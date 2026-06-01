# Tracker Opening Date Default Sort Design

## Goal

Make the current tracker notice list default to `opening_scheduled_date` descending so users see the nearest known opening schedules first.

## Scope

This change applies to the default ordering used by the current tracker notice list across the existing global/snapshot-backed list flow.

This change does not add a new user-facing sort toggle or a separate admin-only sort mode.

## Design

Change the default tracker list ordering to:

1. nonblank `opening_scheduled_date` first
2. `opening_scheduled_date` descending
3. existing stable fallback ordering for ties and blank-date rows

Blank `opening_scheduled_date` rows must be pushed to the bottom of the list. If two rows share the same `opening_scheduled_date`, preserve deterministic fallback ordering with the existing recency/id tie-breakers so pagination and snapshot payloads stay stable.

Apply the ordering at the backend/default-data level instead of only in the browser. This keeps `/api/tracker-entry-summaries`, the global tracker list cache, and home bootstrap first-page payloads aligned under one default ordering rule.

## Constraints

- Manual edits to `opening_scheduled_date` must naturally affect row position on the next reload/render.
- Existing filters, pagination, and snapshot hydration behavior must remain unchanged apart from the new default ordering.
- The change should stay localized to tracker ordering code and related tests.

## Tradeoffs

### Good

- users see actionable dated notices first
- blank-date notices still remain visible but do not crowd the top of the list
- one backend rule keeps bootstrap and paginated list behavior consistent

### Bad

- operators looking specifically for missing dates will need to scroll lower
- older assumptions/tests that expect `updated_at`-first ordering need to be updated

## Verification

- unit test for global tracker ordering with later `opening_scheduled_date` first
- unit test for blank `opening_scheduled_date` rows being pushed below dated rows
- unit test that tie rows remain deterministic under fallback ordering
- targeted bootstrap/list tests remain green after updating expected sort metadata where needed
