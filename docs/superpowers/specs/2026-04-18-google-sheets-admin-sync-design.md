# Google Sheets Admin Sync Design

**Date**

- 2026-04-18

**Goal**

SPMS admin mode should read one private Google Spreadsheet, automatically discover its visible sheets, and render them as SPMS tabs with cached read-only data that refreshes every 5 to 10 minutes.

**Decision Summary**

- Use `backend sync + cached SPMS rendering`.
- Do not embed the Google Sheets UI directly.
- Start with `manual refresh token registration` for one Google account.
- Treat Google Sheets as the edit source of truth and SPMS as a read-only dashboard.
- Keep `프로젝트 현황` as the fixed first admin tab.
- Add all discovered Google Sheets tabs after that first tab, in Google sheet order.
- Preserve the last successful snapshot when Google access fails.

## Background

- The current admin top navigation already exists in [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) and was initially designed around static Google Sheet embed placeholders.
- The current design-list area is not yet backed by real Google Sheets data.
- The target spreadsheet is private and is currently shared to the operator account with comment access.
- The operator does not need to edit data inside SPMS.
- The spreadsheet owner remains the only person who edits sheet content.
- The spreadsheet can gain new sheets over time, such as `경상남도 영업List`, and SPMS should expose those automatically without code changes for each new tab.

## Why This Approach

Three approaches were considered:

1. Cached backend sync and SPMS-native rendering
2. Live Google API fetch on every tab open
3. Direct Google Sheets UI embed

The chosen approach is `1`.

Reasons:

- It works with private sheets through authenticated API access.
- It keeps tab switching fast because the browser reads SPMS data, not Google directly.
- It survives temporary Google API failures by showing the last successful snapshot.
- It supports automatic tab creation from discovered sheet metadata.
- It keeps Google auth, refresh token handling, and rate usage in one backend path.
- It matches the operating model where Google Sheets is edited elsewhere and SPMS is only for viewing.

## Scope

### In Scope

- reading one private spreadsheet through Google Sheets API
- manual one-time refresh token registration for the initial operator account
- periodic background sync every 5 to 10 minutes
- backend snapshot caching of spreadsheet metadata and visible sheet contents
- dynamic admin tab generation from discovered sheet list
- SPMS-native table rendering for synced sheet data
- display of sync status and last successful sync time in admin mode
- automatic inclusion of newly added Google Sheets tabs
- deterministic display-name normalization for selected Korean labels
- future-ready separation so auth can later move from refresh token to service account

### Out of Scope

- editing Google Sheets from SPMS
- preserving full Google Sheets UI features such as comments, formulas UI, filters UI, merged-cell behavior, or exact visual formatting
- multi-account Google connection management
- per-user custom spreadsheet connections
- immediate service account implementation in the first iteration
- replacing the existing `프로젝트 현황` business logic

## Product Behavior

### Admin Tab Model

The admin top navigation will have two categories:

1. Fixed SPMS tab
   - `프로젝트 현황`

2. Dynamic Google-backed tabs
   - one tab per discovered visible sheet in the configured spreadsheet
   - ordered by Google sheet index

Example resulting admin tabs:

- `프로젝트 현황`
- `설계리스트`
- `발주예정`
- `LOST`
- `경상남도 영업 리스트`
- `대리점 리스트`

### Sheet Name Display Rules

Raw Google sheet names are normalized into display labels for SPMS navigation.

Default normalization rules:

- trim leading and trailing whitespace
- remove wrapping `*` characters when they are only decorative
- collapse repeated internal spaces
- preserve Korean and English text otherwise

Explicit display mappings:

- `설계List` -> `설계리스트`
- `*발주예정*` -> `발주예정`
- `LOST` -> `LOST`
- `경상남도 영업List` -> `경상남도 영업 리스트`
- `대리점 리스트` -> `대리점 리스트`

Fallback rule:

- if a sheet name does not match a known mapping, use the normalized source name as-is

This keeps new sheets visible automatically without waiting for code deployment.

### Data Presentation

SPMS will not show an iframe or raw Google Sheets UI.

Each dynamic tab renders:

- sheet display name
- source spreadsheet title
- sync status
- last successful sync time
- read-only table of headers and rows

Expected table behavior:

- first non-empty row is treated as the header row
- subsequent rows are data rows
- trailing empty rows and fully empty columns are trimmed from the rendered snapshot
- rows render in spreadsheet order
- cells render as plain display values, not formulas
- long content may wrap or truncate depending on the eventual frontend styling, but the source text remains available in the cell payload

## Architecture

### Source of Truth

- Google Spreadsheet is the only editing source of truth.
- SPMS stores synchronized read-only snapshots for fast and stable viewing.

### Authentication Strategy

Initial authentication method:

- use Google OAuth user credentials with a manually registered `refresh token`
- request read-only scope only
- store credentials server-side in environment variables or a local secured config file already used by the deployment process

Why manual refresh token first:

- only one operator account is needed initially
- it avoids building OAuth sign-in UI and callback flows inside SPMS
- it can later be replaced with service account credentials without changing the admin tab UI model

Future migration target:

- service account with the spreadsheet shared directly to the service account email

### Backend Sync Service

Add a dedicated backend sync component with four responsibilities:

1. Read configured spreadsheet identity and Google credentials
2. Refresh access tokens when needed
3. Pull spreadsheet metadata plus visible sheet values on a fixed interval
4. Save a complete read snapshot for frontend use

Suggested backend responsibilities by module:

- auth helper for Google token refresh
- Google Sheets client wrapper for metadata and values
- sync scheduler / runner
- snapshot serializer and cache store
- admin API reader endpoints

### Sync Cadence

Default sync interval:

- `5 minutes`

Allowed operational range:

- `5 to 10 minutes`

Design choice:

- implement the interval as configuration
- default production value remains `5 minutes`

### Snapshot Storage

For the current single-EC2 deployment, store snapshots in:

- in-memory hot cache for fast reads
- file-based persisted snapshot on disk for process restart survival

Suggested stored snapshot shape:

- spreadsheet id
- spreadsheet title
- source url
- sync status
- last started sync time
- last successful sync time
- last failed sync time
- last error message
- version or generation number
- discovered sheet list
- per-sheet header cells
- per-sheet row values

Design rationale:

- memory cache serves active requests quickly
- file snapshot preserves the last good state if the service restarts
- this is simpler than introducing a new Supabase table in the first iteration

Future migration path:

- if the system later needs multi-instance consistency, move the snapshot store to Supabase while keeping the same API contract

### Frontend Rendering

The frontend should stop treating these admin tabs as static embed entries.

Instead:

- keep `프로젝트 현황` as the existing fixed admin view
- fetch dynamic Google sheet tab metadata from a backend bootstrap endpoint
- merge the fixed tab with dynamic tabs at runtime
- render dynamic tabs through a common read-only table panel

Suggested admin bootstrap payload fields:

- fixed tabs
- dynamic sheet tabs
- active sync status
- source spreadsheet title
- last successful sync timestamp

Suggested data endpoint fields per sheet:

- sheet id
- raw sheet title
- display title
- sheet order
- headers
- rows
- row count
- column count
- synced at

## Data Flow

1. SPMS starts and loads Google Sheets sync configuration.
2. Background sync job wakes on the configured interval.
3. Backend exchanges refresh token for access token if necessary.
4. Backend fetches spreadsheet metadata and visible sheet list.
5. Backend fetches values for each visible sheet.
6. Backend normalizes names and trims display payload.
7. Backend writes a full snapshot to memory and disk.
8. Admin frontend loads bootstrap metadata from SPMS.
9. Frontend renders `프로젝트 현황` plus all synced sheet tabs.
10. When a Google-backed tab opens, frontend requests the cached sheet payload from SPMS.
11. If the latest sync failed, frontend still renders the last successful snapshot and surfaces sync status.

## API Contract

The exact route names can be finalized during implementation, but the design assumes three admin-only endpoints.

1. Admin Google Sheets bootstrap
   - returns spreadsheet title, sync metadata, and dynamic tab list

2. Admin Google Sheets sheet payload
   - returns the cached header and row payload for one sheet

3. Admin Google Sheets manual sync trigger
   - optional admin-only endpoint to force a refresh outside the normal interval

Manual sync is not required for normal use but is useful during setup and troubleshooting.

## Error Handling

### Google Access Failure

If Google API access fails because of network issues, quota issues, or temporary Google-side errors:

- do not clear the previous good snapshot
- keep existing tabs and data visible
- mark sync status as failed
- display the failure timestamp and short error message to admins

### Refresh Token Failure

If refresh token use fails:

- keep the last successful snapshot
- stop claiming the data is fresh
- show an admin-facing `구글 재연결 필요` state
- do not break `프로젝트 현황`

### New Sheet Added

If the spreadsheet owner adds a new visible sheet:

- the next successful sync automatically includes it
- the next frontend bootstrap automatically exposes it as a new tab

### Sheet Removed or Renamed

If a sheet is removed or renamed:

- the next successful sync updates the dynamic tab list accordingly
- tabs no longer present in the source disappear from the dynamic list
- renamed sheets appear under their new normalized display label

## Operational Rules

### Normal Operation

- operator registers the Google spreadsheet id once
- operator registers the Google refresh token once
- SPMS refreshes access tokens automatically in the backend
- SPMS syncs sheet data every configured interval
- no manual update is needed during normal operation

### When Manual Action Is Required

Manual re-registration is needed only when one of these happens:

- the Google app authorization is revoked
- the refresh token is invalidated or expires
- the OAuth app remains in Google `Testing` state and short-lived refresh token behavior is triggered
- the spreadsheet id changes because the source moved to a different file
- the deployment environment loses the stored credentials

### Production Requirement

The Google OAuth app should be in `Production` state before relying on long-lived refresh token behavior.

### Service Account Migration

Later migration from user refresh token to service account should change only the credential provider:

- create service account
- share the spreadsheet with the service account email
- replace backend credential configuration
- keep the same sync runner, snapshot store, API responses, and frontend UI

## What To Update Later

This section exists so the operator can quickly answer future maintenance questions.

### If Sheet Content Changes

- no code change required
- next sync picks up the new rows and cells

### If a New Sheet Tab Is Added

- no code change required
- next sync picks up the new sheet and SPMS shows a new tab automatically

### If a Sheet Name Changes

- usually no code change required
- only update code later if a prettier custom display label is desired beyond the default normalization rules

### If the Spreadsheet File Changes

- update the configured spreadsheet id
- trigger a sync or wait for the next interval

### If Google Access Stops Working

Check these in order:

1. whether the refresh token is still valid
2. whether the OAuth app is in `Production`
3. whether the spreadsheet is still shared to the authenticated account
4. whether deployment still has the stored Google credentials

### If Moving To Service Account

- add the service account email to the spreadsheet share list
- replace refresh-token-based credential settings with service-account settings
- keep the rest of the design unchanged

## Security Notes

- use read-only Google Sheets scope
- do not expose refresh token to the frontend
- do not return raw credential details in API responses
- treat sync status endpoints as admin-only
- redact credential-related errors before sending them to the browser

## Testing Strategy

1. Verify admin mode still defaults to `프로젝트 현황`.
2. Verify dynamic Google-backed tabs appear after `프로젝트 현황`.
3. Verify sheet order matches the Google spreadsheet order.
4. Verify the configured label mappings render as expected.
5. Verify unknown new sheet names still appear automatically with normalized labels.
6. Verify a newly added sheet appears after the next successful sync without code changes.
7. Verify a renamed sheet updates after the next successful sync.
8. Verify a removed sheet disappears after the next successful sync.
9. Verify a failed sync preserves the last successful snapshot.
10. Verify refresh token failure shows a reconnect-needed state while keeping cached data.
11. Verify backend restart reloads the last persisted snapshot.
12. Verify user mode remains unchanged.

## Risks

- Google sheet formatting will not match the exact native Google Sheets UI.
- Very large sheets may require row limits, paging, or trimmed payloads in a later iteration.
- If the spreadsheet contains unusual merged-header layouts, header detection may need refinement.
- If the spreadsheet owner hides sheets that should remain visible in SPMS, automatic discovery rules may need an explicit allowlist later.

## Success Criteria

- SPMS admin mode shows one fixed tab and dynamic Google-backed tabs from the configured spreadsheet.
- New sheets appear automatically after sync without code deployment.
- SPMS remains readable even when Google temporarily fails.
- Refresh token usually needs one-time registration only, not repeated manual updates.
- Future migration to service account can happen without redesigning the UI or sync model.

## External References

- Google OAuth web server flow: https://developers.google.com/identity/protocols/oauth2/web-server
- Google OAuth policies: https://developers.google.com/identity/protocols/oauth2/policies
- Google Workspace credential setup: https://developers.google.com/workspace/guides/create-credentials
