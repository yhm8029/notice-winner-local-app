# Google Sheets Admin Snapshot Read Performance Design

**Date**

- 2026-04-18

**Goal**

Reduce Google Sheets admin tab timeout incidents by making backend snapshot reads cheaper and by adding low-noise timing logs that explain where time is being spent when the admin bootstrap path is slow.

**Decision Summary**

- Keep the existing admin Google Sheets API surface.
- Optimize the backend snapshot read path instead of changing the frontend request flow first.
- Replace the current `stat + full-file SHA-256` cache validation on every read with a cheaper `mtime_ns + size` based fast path.
- Add targeted performance logging for Google Sheets admin snapshot reads and payload delivery.
- Keep the current auth and authorization model unchanged.

## Background

- The frontend currently times out `/api/admin/google-sheets/bootstrap` after `12s` and `/api/admin/google-sheets/sheets/{sheet_key}` after `20s` in [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js).
- The admin Google Sheets backend does not fetch Google directly during normal page open. It reads the persisted snapshot through [`read_google_sheets_admin_snapshot`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/backend/services/google_sheets_admin_store.py).
- The current snapshot read path computes file state by reading the entire snapshot file and hashing it with SHA-256 on every read in [`_google_sheets_admin_snapshot_file_state`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/backend/services/google_sheets_admin_store.py).
- When the snapshot grows large, repeated full-file reads can dominate the request path even when the file has not changed.
- The user wants both:
  - fewer `Request timed out` failures
  - enough logging to understand whether slowness comes from snapshot reads, payload shaping, or later Google sync work

## Scope

### In Scope

- optimizing backend Google Sheets snapshot cache validation
- preserving existing snapshot semantics for external file mutation detection
- adding lightweight timing logs around snapshot reads and admin bootstrap/payload routes
- keeping the current API responses and frontend behavior intact
- adding regression tests for fast-path cache hits and mutation detection

### Out of Scope

- changing the Google Sheets snapshot schema
- adding new API endpoints
- redesigning the frontend timeout UX
- embedding Google Sheets directly
- changing Google sync cadence or auth behavior as part of this task
- introducing external caches such as Redis

## Root Cause Hypothesis

The most likely root cause of intermittent admin Google Sheets timeout behavior is expensive snapshot validation on the hot read path.

Today, a normal admin read can do all of the following even when nothing changed:

1. `stat()` the snapshot file
2. read the full snapshot bytes
3. compute SHA-256 over the full file
4. compare the resulting tuple against the in-memory cached file state
5. then decide whether to reuse the cached snapshot

That means stable reads still pay for a full-file scan. This is especially wasteful for:

- `/api/admin/google-sheets/bootstrap`
- `/api/admin/google-sheets/sheets/{sheet_key}`

The proposed change removes that cost from the common case.

## Approaches Considered

1. Fast-path snapshot validation plus targeted timing logs
   - Use `mtime_ns + size` for the common cache-hit path.
   - Reload the JSON file only when those cheap file properties change.
   - Add performance logging around snapshot reads and admin routes.
   - Pros: high impact with limited change scope, keeps the existing storage model, gives immediate operational visibility.
   - Cons: relies on filesystem metadata rather than content hashing for the common path.
   - Recommended.

2. Snapshot validation optimization only
   - Remove per-read hashing but add no new logging.
   - Pros: smallest code delta.
   - Cons: if slowness remains elsewhere, operators still cannot tell where time is going.

3. Add a separate sidecar metadata file
   - Persist snapshot metadata separately so the app can validate freshness without touching the large JSON body.
   - Pros: potentially the cheapest read path long-term.
   - Cons: more moving parts, more consistency edges, unnecessary for the current issue.

## Recommended Design

Use a cheaper snapshot state model for the hot read path and supplement it with focused timing logs.

### Snapshot State Model

Replace the current cached file-state tuple:

- `(mtime_ns, size, digest)`

with a cheaper persisted/cached tuple:

- `(mtime_ns, size)`

Behavior:

1. On read, `stat()` the snapshot file.
2. If the cached file state exists and matches `(mtime_ns, size)`, return the cached snapshot immediately.
3. If the file state differs, acquire the existing IO lock, reload the JSON snapshot from disk, and refresh the in-memory cache.
4. If the file is missing, clear the cached file-state marker and return `None` or the existing fallback according to current behavior.
5. If the file is corrupted, preserve the current fallback behavior that reuses the previously cached good snapshot when available.

This keeps external mutation detection while removing repeated full-file hashing from the stable read path.

### Logging Policy

Add a dedicated backend logger:

- `perf.google_sheets_admin`

Default logging behavior:

- only log `warning` lines for slow or failed operations
- avoid chatty per-request info logs in normal operation

Debug logging behavior:

- gated by `GOOGLE_SHEETS_ADMIN_DEBUG_TIMING=1`
- when enabled, emit info-level timing breakdowns for every admin snapshot read and route response

Tracked operations:

- `snapshot_read`
- `snapshot_reload`
- `admin_bootstrap_route`
- `admin_sheet_payload_route`

Suggested metadata fields:

- `path`
- `sheet_key` when applicable
- `cache_hit`
- `file_missing`
- `mtime_ns`
- `size`
- `duration`
- `load_duration`
- `route_duration`
- `tab_count`
- `row_count`
- `error`

Logging should be short, single-line, and machine-searchable.

### Route Timing

Wrap the Google Sheets admin bootstrap and sheet payload route bodies with route-level timers so operators can distinguish:

- snapshot read latency
- payload assembly latency
- total route latency

This does not change the API contract. It only emits timing evidence.

## Architecture Changes

### Backend Store

[`backend/services/google_sheets_admin_store.py`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/backend/services/google_sheets_admin_store.py)

- replace full-file digest state tracking with `mtime_ns + size`
- keep the existing lock-based disk read/write safety
- add small helper(s) to log slow snapshot reads and reloads
- preserve deep-copy semantics for returned cached snapshots

### Backend Router

[`backend/api/routers/admin.py`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/backend/api/routers/admin.py)

- add route-level timers around:
  - `get_admin_google_sheets_bootstrap`
  - `get_admin_google_sheets_sheet_payload`
- log slow and failed route reads through `perf.google_sheets_admin`

### Frontend

No required frontend behavior changes in this task.

The current timeout thresholds remain as-is so we can verify whether the backend change alone reduces timeout incidence.

## Data Flow

### Stable Snapshot Read

1. Request hits admin bootstrap or sheet payload route.
2. Backend computes cheap file state from `stat()`.
3. Cached state matches.
4. Backend returns the in-memory snapshot copy immediately.
5. If the route is still slow, logs will show that the bottleneck is not snapshot reload.

### Changed Snapshot Read

1. Request hits admin bootstrap or sheet payload route.
2. Cheap file state differs from the cached state.
3. Backend acquires the existing snapshot IO lock.
4. Backend reloads JSON from disk, refreshes cache, and returns the new snapshot.
5. If reload is slow, logs capture the reload duration.

### Corrupted Snapshot Read

1. Cheap file state differs, so reload is attempted.
2. JSON decode fails.
3. Backend preserves current fallback behavior:
   - return the cached good snapshot if one exists
   - otherwise return `None`
4. Failure is logged with timing and error metadata.

## Risks And Mitigations

### Risk: false cache hit if file content changes without `mtime_ns` or `size` changing

Mitigation:

- This is rare on the target filesystem and acceptable for this performance fix.
- External changes that do alter either value are still detected immediately.
- The existing sync writer uses atomic replace, which naturally changes file metadata.

### Risk: noisy production logs

Mitigation:

- log only slow or failed operations by default
- reserve per-request detail for `GOOGLE_SHEETS_ADMIN_DEBUG_TIMING=1`

### Risk: hidden bottleneck elsewhere

Mitigation:

- route-level timers and snapshot read timers are added together so we can distinguish store cost from other route cost

## Test Plan

Add or update tests in [`tests/test_google_sheets_admin_store.py`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/test_google_sheets_admin_store.py) to verify:

1. unchanged snapshot file returns cached data without reloading the JSON body
2. changed `mtime_ns` or size forces a reload
3. external mutation detection still works
4. corrupted file still falls back to the last cached good snapshot when available

Add route-level tests if needed to verify:

1. bootstrap route behavior is unchanged
2. sheet payload route behavior is unchanged
3. timing instrumentation does not alter response shapes

## Success Criteria

- stable admin Google Sheets reads no longer scan and hash the full snapshot file on every request
- existing admin Google Sheets tests continue to pass
- new tests prove the fast-path cache hit behavior
- operators can inspect slow-read evidence from `perf.google_sheets_admin` logs without enabling noisy default logging
