# Admin Google Sheets Local Cache Design

**Goal**

Make the admin Google Sheets views feel immediate after the first successful load by rendering a previously saved local snapshot first, then refreshing in the background with the latest server snapshot.

## Background

- The current Google Sheets admin integration already persists a server-side snapshot and exposes it through `/api/admin/google-sheets/bootstrap` and `/api/admin/google-sheets/sheets/{sheet_key}`.
- The frontend currently waits for live bootstrap and payload responses before rendering meaningful content for the Google Sheets tabs.
- This causes slow perceived load even when the user has already visited the same tabs recently and the previously rendered content would still be useful while a refresh is happening.
- The user wants the app to behave like a cached admin console:
  - show the last known content immediately
  - refresh in the background
  - replace stale content with fresh content once available
- Additional user constraints:
  - do not increase backend or Supabase cost
  - do not increase backend CPU or memory usage materially
  - keep the implementation modular

## Scope

### In Scope

- frontend-first cached rendering for admin Google Sheets tabs
- storing the last successful Google Sheets bootstrap response in `localStorage`
- storing the last successful per-sheet payload response in `localStorage`
- restoring cached Google Sheets content during app initialization before the network refresh finishes
- showing a small stale-data status message while background refresh is in progress
- keeping cached data visible if the refresh fails
- implementing the cache path without increasing the current backend or Supabase request volume
- moving cache-specific logic into a dedicated frontend runtime/module
- tests covering cache restore, refresh replacement, and stale fallback behavior

### Out of Scope

- changing the current server-side Google Sheets snapshot model
- reducing the backend sync interval as part of this change
- caching Google Sheets data for normal user-mode pages
- cross-user shared browser cache invalidation beyond the authenticated admin browser session
- schema migrations or new backend storage layers

## Requirements

### Functional

1. After the first successful Google Sheets admin load, the frontend stores the bootstrap payload and loaded sheet payloads locally in the browser.
2. When the admin opens SPMS again, the frontend restores the cached Google Sheets bootstrap and the active cached sheet payload immediately if available.
3. The restored cached content must render without waiting for a new network response.
4. After rendering cached content, the frontend must still request the latest bootstrap and sheet payload from the server.
5. When the latest server response arrives, the UI must replace the cached content and update the cache.
6. If the background refresh fails, the most recent successful cached content must remain visible.
7. If no cache exists, the page should behave as it does today.
8. If the cache is malformed, unreadable, or belongs to an incompatible schema version, the frontend should ignore it safely and continue with the normal live load.

### Non-Functional

- keep the diff focused on the admin Google Sheets frontend path
- do not change user-mode behavior
- keep browser storage bounded and versioned
- do not block UI rendering on local cache reads
- preserve existing backend auth and authorization checks
- do not introduce additional Supabase calls for Google Sheets cache restore
- do not fan out live requests to every sheet tab during startup
- keep cache logic modular rather than expanding unrelated `app.js` responsibilities

## Approaches Considered

1. Frontend `localStorage` restore plus background refresh
   - Save successful bootstrap and sheet payloads locally.
   - Restore them during startup and then refresh from the backend.
   - Pros: biggest improvement to perceived speed, no backend contract changes, safe fallback when refresh fails.
   - Cons: requires client-side cache invalidation and versioning.
   - Recommended.

2. Backend-only optimization
   - Try to make `/bootstrap` and `/sheets/{key}` faster without a client cache.
   - Pros: simpler mental model, no local browser storage.
   - Cons: still leaves users waiting on network and auth round-trips; weaker perceived improvement.

3. Server-rendered HTML snapshot
   - Pre-render or inline the latest Google Sheets snapshot in the page shell.
   - Pros: can be very fast on first paint.
   - Cons: much larger architectural change, couples page bootstrap to admin sheet state, unnecessary for the current single-page app.

## Recommended Design

Use a versioned frontend cache in `localStorage` for admin Google Sheets bootstrap and per-sheet payloads.

The cache restore must improve perceived speed without increasing infrastructure cost. That means:

- no extra Supabase reads or writes
- no extra backend polling beyond the existing Google Sheets bootstrap and active-sheet payload refresh path
- no eager loading of all sheet payloads just because cached data exists

### Cache Model

Store one top-level browser object under a dedicated versioned key, for example:

- `notice-winner-pipeline-web.adminGoogleSheetsCache.v1`

Suggested shape:

```json
{
  "saved_at": "2026-04-18T10:00:00.000Z",
  "bootstrap": {},
  "payloads_by_key": {
    "sheet-123": {}
  }
}
```

Rules:

- write only after successful bootstrap or sheet payload responses
- overwrite older cache atomically
- ignore any cache that is not a plain object with the expected shape
- allow a future version bump to invalidate old browser data cleanly

### Restore Flow

During admin app initialization:

1. Read the browser cache.
2. If valid cached bootstrap exists, hydrate:
   - `state.adminGoogleSheetsBootstrap`
   - `state.adminGoogleSheetTabs`
3. If valid cached payloads exist, hydrate:
   - `state.adminGoogleSheetPayloadByKey`
   - matching payload epochs for those entries
4. Render immediately using that cached state.
5. Trigger the normal live bootstrap and sheet payload fetch in the background.

This means the user sees the last known Google Sheets content immediately instead of an empty or initializing panel.

The background refresh must stay bounded:

- refresh bootstrap once through the existing endpoint
- refresh only the currently active Google Sheets tab payload
- do not automatically fetch every cached payload on startup

### Refresh Flow

After cache restore:

- always request live bootstrap from the backend
- if the active tab is a Google Sheet tab, also request the live payload for that tab
- replace state with the live response once it arrives
- save the fresh response back to `localStorage`

This preserves correctness while prioritizing fast perceived load.

### UI Messaging

When cached data is being shown before refresh completes, the admin panel should show a concise status such as:

- `Showing the most recently saved data first. Checking for the latest content.`

When the live refresh succeeds:

- remove the stale-data notice

When the live refresh fails but cached data exists:

- keep showing cached data
- show a concise warning such as:
  - `Showing the most recently saved data. Could not load the latest content.`

When no cached data exists and the live request fails:

- preserve the existing error path

## Architecture

### Frontend Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)

- restore cached bootstrap and payloads into in-memory state before live fetch completion
- track whether the current Google Sheets UI is rendering cached data
- update messaging when cached content is being displayed during refresh
- consume a dedicated cache runtime instead of holding low-level cache parsing logic inline

`frontend/admin-google-sheets-cache-runtime.js` (new)

- expose cache helpers for:
  - reading a versioned admin Google Sheets cache object
  - validating bootstrap and payload cache shape
  - writing successful bootstrap and payload snapshots
  - clearing invalid cache safely
- isolate browser storage access and shape validation from the main app controller
- make the cache behavior independently testable

[`frontend/index.html`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/index.html)

- load the new cache runtime before `app.js`

### State Additions

The frontend should add minimal state for cache awareness, for example:

- `adminGoogleSheetsHydratedFromCache`
- `adminGoogleSheetsShowingCachedData`
- `adminGoogleSheetsCacheSavedAt`

These flags should drive only admin Google Sheets rendering and messaging.

### Isolation

- Do not change the backend response contracts.
- Do not change non-Google-Sheets admin panels.
- Keep all cache logic contained to the Google Sheets admin path so it can be removed or replaced later without touching unrelated app behavior.
- Keep request behavior aligned with today's live path so backend CPU, memory, and Supabase usage do not increase materially.

## Data Flow

### First Successful Visit

1. User opens a Google Sheets admin tab.
2. Frontend loads live bootstrap and live payload.
3. Frontend renders live data.
4. Frontend stores the successful responses in `localStorage`.

### Later Visit

1. User opens SPMS admin mode again.
2. Frontend restores cached bootstrap and cached payload immediately.
3. UI renders cached content.
4. Frontend requests live bootstrap and live payload.
5. Live response replaces cached content.
6. Cache is updated with the fresh response.

### Refresh Failure After Cache Restore

1. Cached content is restored.
2. Live refresh fails.
3. Cached content stays visible.
4. UI shows a non-blocking stale-data warning.

## Error Handling

- malformed cache: ignore and proceed with live fetch
- storage access denied or quota errors: fail silently and proceed without cache persistence
- bootstrap refresh failure with cache present: keep cached tabs and show warning
- sheet payload refresh failure with cached payload present: keep cached sheet and show warning
- bootstrap success but active sheet payload failure: update tab metadata while retaining cached sheet rows if available
- missing cached payload for a non-active sheet: do not prefetch it until the user opens that tab

## Testing

Add frontend integration coverage for:

1. restoring cached Google Sheets bootstrap before live fetch resolves
2. restoring cached sheet payload before live payload resolves
3. replacing cached content with live content after a successful refresh
4. retaining cached content when live bootstrap fails
5. ignoring malformed cache safely
6. not affecting behavior when no cache exists
7. not issuing extra startup sheet payload calls beyond the active tab
8. verifying cache helpers in isolation if the cache runtime is split into its own file

Likely test targets:

- [`tests/frontend/test_admin_tabs_app_integration.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_admin_tabs_app_integration.mjs)
- a new focused frontend integration test for cache hydrate and refresh behavior if the existing file becomes too large

## Risks

- stale content may briefly appear before the fresh refresh replaces it
- cached payloads could drift from live tab metadata if only part of the refresh succeeds
- `localStorage` can throw in restricted browser contexts, so reads and writes must be defensive
- if cache boundaries are too broad, unrelated admin state could leak into this feature
- if the cache logic is left inside `app.js`, future maintenance cost will rise quickly, so modularization is part of the design rather than an optional cleanup

## Success Criteria

- after one successful Google Sheets visit, later visits render admin sheet content immediately from cache
- the UI still refreshes to the newest backend snapshot automatically
- users can continue using the previous snapshot even if a later refresh fails
- the change does not alter user-mode behavior or backend auth requirements
- backend and Supabase request patterns remain effectively the same as today's live path
