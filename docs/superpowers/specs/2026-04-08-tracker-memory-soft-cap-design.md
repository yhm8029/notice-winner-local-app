# Tracker Memory Soft Cap Design

## Goal

Keep tracker-related cache growth from pushing the `uvicorn` process into sustained high-memory pressure on the `t3.small` EC2 instance.

## Scope

This change only targets process-local tracker/search caches that are safe to rebuild:

- global tracker rows cache
- tracker export workbook cache

This change does not attempt general Python heap compaction, and it does not restart the service.

## Design

Add a soft memory cap check on the global tracker cache path. When the current process RSS is at or above `900 MiB`, clear the tracker/search caches before serving the global tracker request. Protect this with a `5 minute` cooldown so repeated searches do not clear caches on every request.

Use the existing tracker cache invalidation path so both caches are cleared consistently:

- `_TRACKER_GLOBAL_ROWS_CACHE`
- `_TRACKER_EXPORT_WORKBOOK_CACHE`

The soft-cap check should be best-effort and fail-open. If RSS measurement fails for any reason, the request path should continue normally.

## Tradeoffs

### Good

- prevents tracker caches from growing without bound during repeated global searches
- avoids full process restarts
- keeps the change localized to existing tracker cache primitives

### Bad

- the first global tracker search after a clear may be slower
- clearing caches does not guarantee immediate RSS drop because Python may keep heap arenas reserved
- if the threshold is too low, cache churn can hurt search latency

## Thresholds

- RSS soft cap: `900 MiB`
- cooldown after a soft-cap clear: `300 seconds`

## Verification

- unit test that soft-cap clearing happens when RSS is above threshold
- unit test that cooldown suppresses repeated clears
- existing tracker search tests remain green
