# Sales Estimate Label Copy Plan

## Task

Align the building automation estimate label text across sales/tracker UI surfaces.

## Files

- `frontend/sales-view-runtime.js`
- `frontend/tracker-entry-runtime.js`
- `frontend/app.js`
- `frontend/tests/tracker-entry-runtime.test.js`

## Steps

1. Replace the old `공사비 최대 3%` label text with `공사비의 1.5~2%` in all affected renderers.
2. Update the focused frontend test expectation.
3. Run:
   - `node --test frontend/tests/tracker-entry-runtime.test.js`
   - `node --check frontend/sales-view-runtime.js frontend/tracker-entry-runtime.js frontend/app.js`
