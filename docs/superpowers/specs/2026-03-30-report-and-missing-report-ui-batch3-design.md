# Report And Missing Report UI Batch 3 Design

## Goal

Continue the frontend modularization pattern by moving report-panel rendering and tracker missing-report rendering out of `frontend/app.js` into focused runtime modules, without changing report behavior or tracker-admin behavior.

This batch is presentation-only. Data loading, URL sync, event wiring, and download actions stay in `frontend/app.js`.

## Scope

Target the remaining report-related and tracker missing-report rendering blocks in `frontend/app.js`.

In scope:

- `renderReport()`
- `renderReportJobs()`
- `renderReportJob()`
- `reportKeyLabel()`
- `renderTrackerMissingReport()`
- `renderMissingReportChip()`

Out of scope:

- `loadPhaseReport()`
- `loadReportJobs()`
- `runReportJob()`
- `refreshReportPanels()`
- missing-report fetch/download actions
- panel DOM creation/query setup
- URL state mutation

## Existing Direction

This branch already uses focused frontend runtime files such as:

- `run-view-runtime.js`
- `tracker-change-runtime.js`
- `related-notice-runtime.js`
- `artifact-runtime.js`

`frontend/app.js` still contains deterministic markup and display shaping for the report panel and the tracker missing-report panel. Those are good candidates for runtime extraction because they are largely pure rendering with app-side state/event orchestration around them.

## Design

### Responsibility split

Create two new frontend runtime modules.

`frontend/report-runtime.js` should own:

- report key labeling
- report summary/status line shaping
- report summary/json display shaping
- report job list markup
- report job detail/status shaping

`frontend/tracker-missing-report-runtime.js` should own:

- missing-report summary chip markup
- missing-report item list markup
- missing-report empty/error display markup

`frontend/app.js` should keep:

- API calls
- state mutation
- selected report-job state updates
- event listener registration
- panel bootstrap and DOM lookup
- CSV/XLSX download actions

### Report panel handling

The report runtime should expose deterministic helpers that accept plain data plus injected formatting helpers.

Expected helper responsibilities:

- resolve report label from report key
- build the status line for the loaded report summary
- build jobs-list markup with selected-item state
- build job-detail status text

`app.js` should continue attaching click handlers to rendered report-job items after inserting the markup.

### Missing report handling

The missing-report runtime should expose deterministic helpers that shape:

- summary chip markup from `report.summary`
- list markup for each missing project and its missing fields
- empty/error-state markup

This should remain tracker-admin presentation only. Fetch timing and admin-mode gating stay in `app.js`.

### File structure

Recommended new modules:

- `frontend/report-runtime.js`
- `frontend/tracker-missing-report-runtime.js`

Do not overload existing runtimes for this batch:

- `run-view-runtime.js` already owns run cards/logs/preset/execution context
- `tracker-change-runtime.js` already owns tracker change/backfill views

Keeping report and missing-report in dedicated files preserves one clear responsibility per runtime.

## Testing Strategy

Keep this batch test-first.

Add focused frontend runtime tests:

- `frontend/tests/report-runtime.test.js`
- `frontend/tests/tracker-missing-report-runtime.test.js`

Coverage should include:

- report label selection for known keys
- loaded-report summary/status text
- report empty/error states
- report job list selected-item markup
- report job detail status text
- missing-report summary chips
- missing-report empty/error states
- missing-report item rendering with nested field reasons

If `app.js` adds fallback paths because a runtime may be missing, include explicit fallback coverage for those seams.

Verification should include:

- targeted `node --test` runtime suites
- `node --check` for touched frontend files

## Risks And Mitigations

- Risk: selected report-job highlighting or click selectors drift
  - Mitigation: keep the same `data-report-job-id` contract and test for it
- Risk: missing-report empty/error copy changes unintentionally
  - Mitigation: lock current copy in runtime tests before extraction
- Risk: runtime boundaries blur into event handling
  - Mitigation: keep all click listeners and selection state mutation in `app.js`

## Success Criteria

- `frontend/app.js` is materially smaller around report and missing-report rendering.
- Two new focused runtime modules clearly own deterministic report UI and missing-report UI shaping.
- Report panel behavior, selected-job behavior, and tracker missing-report behavior remain unchanged.
- Selector contracts and admin gating remain unchanged.
- Focused frontend runtime tests pass cleanly.
