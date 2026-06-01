# Admin Google Sheets Instant Open Design

**Goal**

Make Google Sheets admin tabs open immediately by rendering the last saved snapshot before auth/session refresh completes, then keep that snapshot visible until a newer server snapshot is ready.

## Background

- The current admin Google Sheets path already has:
  - a backend snapshot exposed through `/api/admin/google-sheets/bootstrap`
  - per-sheet payload reads through `/api/admin/google-sheets/sheets/{sheet_key}`
  - a browser cache runtime for bootstrap and sheet payloads
- The current perceived slowdown is still high because the app waits for auth/session confirmation before showing the protected console shell and then waits for the Google Sheets path to settle.
- The user explicitly wants:
  - Google Sheets admin tabs only, not the full SPMS console
  - the last snapshot shown immediately when the page opens
  - the old snapshot to remain visible until a newer snapshot is available
  - periodic refresh every 10 minutes rather than aggressive frequent refresh
- The user explicitly accepts the trade-off that a previously saved Google Sheets admin snapshot may appear briefly before the session re-check finishes, as long as an expired session is then handled politely and the user is returned to the login flow.

## Scope

### In Scope

- immediate snapshot-first rendering for Google Sheets admin tabs only
- showing the last saved Google Sheets admin snapshot before auth/session refresh completes
- keeping the cached snapshot visible while the app checks auth and server freshness
- re-validating auth in the background and switching to the login screen if the session is no longer valid
- reusing the backend snapshot model rather than re-reading Google directly on every open
- limiting automatic live refresh for Google Sheets admin tabs to a 10-minute cadence
- continuing to use the previous snapshot while live refresh is pending or fails
- preserving existing manual sync behavior

### Out of Scope

- changing non-Google-Sheets admin screens to render before auth completes
- changing normal user-mode pages
- changing backend snapshot schema
- reading Google Sheets directly from the frontend
- introducing websockets or push-based real-time updates
- changing organization, dashboard, runs, or tracker panel load behavior outside the Google Sheets admin tab path

## User-Approved Requirements

### Functional

1. If the current route points to a Google Sheets admin tab and a valid browser snapshot exists, the app should render that snapshot immediately on page open.
2. This immediate render should happen even before `/api/auth/session` finishes, but only for Google Sheets admin tabs.
3. After the page opens, the app must still re-check auth/session in the background.
4. If the session is valid, the app should continue using the console and refresh the Google Sheets tab from the backend snapshot path.
5. If the session is expired or unauthorized, the app should replace the cached tab with the login screen and a polite session-expired message.
6. The app should not replace the visible snapshot with a loading state while checking for fresher data.
7. Automatic Google Sheets admin refresh should happen at most once every 10 minutes while the user remains on a Google Sheets admin tab.
8. If the backend snapshot is refreshed successfully, the visible tab should update in place and the browser cache should be replaced.
9. If the refresh fails, the old snapshot should remain visible and the UI should show a non-blocking warning.
10. Manual Google Sheets sync/refresh remains available and can still force an earlier update.

### Non-Functional

- do not increase Google Sheets backend cost materially
- do not add direct Google API reads on page open
- do not increase Supabase usage materially
- do not expand the optimistic pre-auth behavior to the rest of the protected console
- keep the implementation modular and localized to the Google Sheets admin path
- maintain polite Korean auth/session copy

## Approaches Considered

1. Browser snapshot first, backend snapshot refresh after auth
   - Render the last browser snapshot immediately for Google Sheets admin tabs.
   - Re-check session in the background.
   - After session passes, refresh from the backend snapshot endpoints and only trigger a backend sync if the snapshot is older than 10 minutes.
   - Pros: fastest perceived open, low backend cost, keeps Google out of the critical path.
   - Cons: briefly shows last-known protected content before session confirmation.
   - Recommended.

2. Wait for auth, then show cached snapshot
   - Keep the current auth gate, but once auth passes, render browser-cached snapshot before live refresh.
   - Pros: stronger auth-first posture.
   - Cons: does not solve the user's main complaint because first paint is still blocked on the session request.

3. Always fetch a fresh backend snapshot on open
   - Do not use browser snapshot for immediate rendering; only show content after live backend responses.
   - Pros: simpler trust model.
   - Cons: too slow for the user goal and still dependent on auth + backend latency on every open.

## Recommended Design

Use a Google-Sheets-tab-only optimistic display mode backed by the existing browser snapshot runtime and the existing backend snapshot endpoints.

The open flow becomes:

1. Detect whether the current route is a Google Sheets admin tab route or a legacy alias that resolves to a Google Sheets tab.
2. If yes, read the browser snapshot immediately.
3. If the snapshot is valid, render the cached Google Sheets tab shell and rows immediately.
4. Start auth/session refresh in parallel.
5. If auth fails, hide the cached console content and return to the login shell with a polite expired-session message.
6. If auth passes, fetch the backend bootstrap snapshot.
7. If the backend snapshot is newer or different, update the visible tab and browser cache.
8. If the backend snapshot is stale by the configured threshold, request the existing backend sync path and keep the current snapshot visible until newer backend data appears.

The user should never see:

- a blank protected page while the browser already has a usable Google Sheets snapshot
- a loading-only state replacing a previously visible snapshot
- frequent one-minute Google Sheets refreshes when a 10-minute cadence is enough

## Architecture

### Frontend Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)

- allow a limited Google-Sheets-only optimistic render path before auth completes
- keep the existing auth gate for the rest of the console
- if the route is a Google Sheets admin tab and a valid cached snapshot exists:
  - render the cached tab panel immediately
  - mark the view as `pending_auth_validation`
  - avoid hiding the visible snapshot while auth/bootstrap refresh is underway
- when auth refresh completes:
  - if unauthorized, clear the optimistic Google Sheets view from the DOM and show the login shell
  - if authorized, continue with live bootstrap refresh and cache replacement
- track the last successful live Google Sheets refresh time so automatic refresh happens on a 10-minute cadence instead of every minute for that path

[`frontend/admin-google-sheets-cache-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/admin-google-sheets-cache-runtime.js)

- remains the low-level browser snapshot reader/writer
- may need small helper expansion only if the app needs more explicit metadata access, but the core storage contract should stay versioned and bounded

### Backend Responsibilities

No new backend endpoints are needed.

Use the existing endpoints:

- `/api/auth/session`
- `/api/admin/google-sheets/bootstrap`
- `/api/admin/google-sheets/sheets/{sheet_key}`
- `/api/admin/google-sheets/sync`

The backend remains the source of truth for the latest synchronized snapshot. The browser snapshot is only the instant-open fallback.

## Data Flow

### Page Open With Cached Snapshot

1. User opens a Google Sheets admin tab URL.
2. Frontend reads the browser snapshot.
3. Cached Google Sheets tab renders immediately.
4. Frontend starts `/api/auth/session`.
5. If auth passes:
   - fetch `/api/admin/google-sheets/bootstrap`
   - fetch only the active sheet payload if needed
   - compare refresh timestamps
   - update the tab and cache if fresher data exists
6. If auth fails:
   - remove optimistic protected content from view
   - show login shell with polite expired-session messaging

### Page Open Without Cached Snapshot

1. User opens a Google Sheets admin tab URL.
2. No valid browser snapshot exists.
3. App behaves like today:
   - auth gate first
   - then live bootstrap/payload path

### Ongoing Refresh While User Stays On Tab

1. While the user stays on a Google Sheets admin tab, the app checks whether 10 minutes have elapsed since the last live Google Sheets refresh.
2. If not, keep showing current content with no extra fetch.
3. If yes:
   - fetch backend bootstrap
   - if backend snapshot is stale or sync status indicates refresh is needed, trigger the existing sync endpoint
   - continue showing the current snapshot until a newer backend snapshot is available
4. Replace the visible snapshot only after a newer successful response arrives.

## Auth and Security Behavior

This design intentionally accepts a narrow optimistic display trade-off for Google Sheets admin tabs only.

Guardrails:

- only the Google Sheets admin tab panel can render before auth completes
- do not expose the rest of the admin console before auth completes
- do not enable editing or privileged mutations from the optimistic pre-auth state
- if auth returns unauthorized, immediately switch to the login shell and show:
  - `세션이 만료되었습니다. 다시 로그인해 주세요.`
- the optimistic snapshot should be treated as temporary display state, not as proof of access

This is acceptable because:

- the user explicitly approved this trade-off
- it solves the main latency complaint
- it does not add new server-side exposure or bypass backend authorization

## Refresh Cadence

Current behavior is too eager for this path if it checks Google Sheets-related state every minute.

Change the Google Sheets automatic refresh policy to:

- `10 minutes` for passive automatic refresh while the user remains on a Google Sheets admin tab
- immediate refresh when the user manually presses the sync/refresh button
- immediate live bootstrap refresh right after optimistic snapshot render finishes auth validation

This means:

- first open is fast because it uses the snapshot
- background freshness checks are much less chatty
- users still get regular updates without feeling blocked

## Error Handling

- invalid browser snapshot: ignore it and fall back to the normal auth/live flow
- auth request failure:
  - if cached snapshot is visible, keep it visible briefly with a soft warning until the auth failure outcome is known
  - if the failure resolves to unauthorized or expired session, switch to login
- backend bootstrap failure after auth success: keep the current visible snapshot and show a non-blocking warning
- backend payload failure after auth success: keep the current visible sheet and show a non-blocking warning
- backend sync timeout/failure: retain the old snapshot and try again on the next 10-minute cadence or manual refresh

## Testing

Add or extend frontend integration coverage for:

1. opening a Google Sheets admin tab with a valid snapshot while auth is still pending
2. keeping the snapshot visible while `/api/auth/session` is in flight
3. replacing the optimistic tab with the login shell when auth returns expired/unauthorized
4. continuing from optimistic snapshot to authorized live refresh when auth passes
5. ensuring the rest of the protected console is not rendered optimistically
6. ensuring automatic Google Sheets refresh does not run more often than every 10 minutes
7. ensuring existing snapshot remains visible during refresh and on refresh failure

## Risks

- protected content may be visible briefly before auth confirms the session
- the current `app.js` auth shell and console shell toggling may need a new intermediate display state
- if the optimistic path is not tightly scoped, it could accidentally expose non-Google-Sheets admin panels before auth
- if the 10-minute cadence is wired on top of the existing one-minute poll without proper gating, duplicate refreshes could still occur

## Success Criteria

- opening a Google Sheets admin tab feels immediate when a snapshot exists
- the user continues seeing the old snapshot until a newer backend snapshot is ready
- expired sessions are still handled politely and switched back to login
- only Google Sheets admin tabs get this optimistic behavior
- automatic Google Sheets refresh cadence is reduced to 10 minutes
- backend and Google-facing cost does not materially increase
