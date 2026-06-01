# Excel Dropdown Sheet Filters Design

**Date**

- 2026-04-19

**Goal**

Replace the current second-row Google Sheets table filters with an Excel-like header dropdown filter experience in SPMS, using frontend-only sorting and checkbox filtering without adding backend, Supabase, or Google Sheets traffic.

**Decision Summary**

- Remove the current inline second-row filter controls from the Google Sheets table.
- Add one dropdown trigger to each visible header cell, matching the Excel-style header-arrow interaction the user requested.
- Support ascending and descending sort actions, option-list search, select-all behavior, and checkbox-based multi-select filtering.
- Keep filtering fully client-side against the already loaded sheet payload.
- Preserve filter state per sheet key so different sheet tabs do not leak state into each other.
- Use the same filter UI in both user mode and admin mode because both now share the same Google Sheets table shell.

## Background

- The merged Google Sheets experience now shows the same sheet-backed tabs in both user mode and admin mode through [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js).
- The current filter implementation renders a second header row with inline text/select controls from [`frontend/admin-google-sheets-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/admin-google-sheets-runtime.js).
- The user clarified that this is not the desired UX. They want the Excel-style pattern shown in the reference screenshot:
  - header-level dropdown trigger
  - popup menu from the header
  - sort actions
  - search inside the popup
  - checkbox list with a select-all row
- The user explicitly chose the standard implementation level:
  - not a minimal text-only dropdown
  - not a full Excel clone with advanced condition builders
  - exactly the middle ground with sorting plus checkbox-based list filtering

## Scope

### In Scope

- replacing the current second-row filter UI in the Google Sheets table
- rendering one filter dropdown trigger per header cell
- popup-driven sorting:
  - ascending
  - descending
- popup-driven filtering:
  - search within available option values
  - select-all behavior
  - checkbox multi-select of distinct visible values
- explicit confirm and cancel behavior inside the popup
- per-sheet persistence of current filter and sort state in frontend memory
- showing active-filter visual state on the header trigger
- supporting the same behavior in both user mode and admin mode
- frontend runtime and integration regression coverage

### Out of Scope

- backend query filtering
- server-side sorting
- extra snapshot requests for filtering
- Google Sheets API query changes
- full Excel advanced conditions such as:
  - text conditions
  - numeric ranges
  - date ranges
  - blank/non-blank operators
  - custom formulas
- persistent filter storage across hard reloads or across devices
- editing sheet values inside SPMS

## Approaches Considered

1. Replace the current second-row controls with Excel-style header popovers
   - Keep filtering local to the loaded payload.
   - Preserve the table markup and state ownership in the current frontend.
   - Pros: matches the requested UX most closely, no backend cost, fits the current architecture.
   - Cons: requires more runtime state and event binding than the current filter row.
   - Recommended.

2. Keep the current second-row controls and only restyle them
   - Pros: smallest implementation.
   - Cons: does not satisfy the requested Excel-like interaction model.

3. Introduce a heavy third-party data-grid library
   - Pros: lots of ready-made table features.
   - Cons: high integration cost, styling drift, larger bundle, and unnecessary complexity for the current sheet tables.

## Recommended Design

Replace the current filter row with per-column header dropdown filters that feel like Excel's automatic filter menu while staying within the current SPMS runtime.

### Core Interaction Model

Each header cell gets a compact trigger icon on the right edge.

When the user clicks that trigger:

- open a single popup anchored to that header
- close any previously open popup
- show controls for only that column

The popup contains:

1. sort ascending action
2. sort descending action
3. searchable option list
4. a select-all checkbox row
5. per-value checkboxes
6. confirm
7. cancel

### Filtering Rules

- A column with no active selection behaves as unfiltered.
- If all values are selected, that column behaves as unfiltered.
- If a subset of values is selected, only rows matching those visible values remain.
- Popup search narrows only the option list inside the popup. It does not directly filter table rows until the user confirms the checkbox selection.
- Filtering uses the visible display text of each cell.
- Linked cells continue using their rendered text label for filtering, not the raw URL.

### Sorting Rules

- Only one effective sort column is needed at a time.
- Sort direction can be:
  - none
  - ascending
  - descending
- Sorting applies after filtering.
- Sorting uses the same visible cell text basis as filtering.
- If the user changes the active sheet tab, sort state remains isolated to that sheet key.

### Confirm / Cancel Behavior

The popup uses a staged edit model:

- opening the popup copies the currently applied column state into a draft state
- changing checkboxes or popup search edits only the draft
- clicking confirm commits the draft into the applied table state
- clicking cancel, outside-click, or `Esc` discards unconfirmed draft changes

This is the closest low-complexity match to Excel behavior and avoids accidental table reshaping while the user is still browsing values.

## Data Model

The current `filters[]` shape is not sufficient for Excel-style popovers. Replace it with sheet-keyed column filter state.

Suggested frontend state shape:

```js
{
  "sheet-1664606955": {
    sort: { columnIndex: 3, direction: "asc" },
    columns: {
      "0": { selectedValues: [] },
      "1": { selectedValues: ["Project A", "Project B"] },
      "2": { selectedValues: [] },
      "3": { selectedValues: ["255.43", "175.57"] }
    }
  }
}
```

Separate popup UI draft state should exist outside the persisted sheet state:

```js
{
  open: true,
  sheetKey: "sheet-1664606955",
  columnIndex: 3,
  searchDraft: "175",
  pendingSelectedValues: ["255.43", "175.57"]
}
```

Key rules:

- `selectedValues: []` means no filter applied
- sheet state persists per tab key
- popup draft state exists only while one popup is open

## UI Behavior

### Header Rendering

- remove the second filter row entirely
- render one header row only
- add a compact dropdown trigger button to each header cell
- visually highlight a trigger when:
  - the column has an active filter
  - the column is the active sort column

### Popup Rendering

- popup opens beneath or near the active header trigger
- only one popup may be open at once
- popup width should be fixed and scroll its option list rather than expanding the table
- long values may truncate visually, but the full value should still be usable as the filter key

### Option List Semantics

- available option values come from the currently loaded payload rows for that sheet
- deduplicate by normalized visible text
- keep displayed labels stable and human-readable
- the select-all row toggles the full current option set
- if the search box narrows the visible option list, select-all operates on the visible option set, not hidden results

### Keyboard / Dismissal Behavior

- `Esc` closes the popup without applying draft edits
- clicking outside closes the popup without applying draft edits
- reopening the same column restores the last applied state, not the abandoned draft

## Architecture Changes

### Runtime

[`frontend/admin-google-sheets-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/admin-google-sheets-runtime.js)

- remove the current second-row filter model and row rendering
- add helpers to:
  - derive distinct visible option values per column
  - apply checkbox-value filtering
  - apply one active sort definition
  - render header trigger state
  - render popup markup for the active column
- continue to expose one table view builder entrypoint so app wiring stays centralized

### App State And Controller Logic

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)

- replace the existing sheet filter state memory with sheet-keyed Excel-style filter state
- add popup UI state for:
  - open/closed
  - active sheet key
  - active column
  - search draft
  - pending selected values
- bind click handlers for:
  - opening a header popup
  - sort actions
  - checkbox toggles
  - confirm
  - cancel
  - outside-click dismissal
- keep user-mode and admin-mode behavior identical for table filtering
- keep admin-only sync controls and diagnostics untouched

### Styles

[`frontend/styles.css`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/styles.css)

- remove or deprecate second-row filter styles
- add styles for:
  - header trigger buttons
  - active trigger state
  - popup shell
  - popup option list
  - checkbox rows
  - popup footer actions
- ensure the popup remains usable on narrow laptop widths without breaking the sheet table scroll layout

## Error Handling And Edge Cases

### Empty / Missing Data

- If a sheet has no rows, still render the header and no popup options.
- If a column has no distinct values, show an empty disabled list state inside the popup.

### Refresh Behavior

- If sheet payload refreshes and some previously selected values no longer exist, drop only invalid selections for that column.
- If all selected values become invalid, the column returns to the unfiltered state.
- Keep valid sort state unless the sorted column index no longer exists.

### Mixed Cell Types

- normalize all cell values to visible text before deduping or sorting
- for link cells, use link text
- for blank cells, treat them consistently as one visible blank bucket if they need to appear in options

## Risks And Mitigations

### Risk: popup logic becomes brittle in the existing large `app.js`

Mitigation:

- keep popup state transitions explicit and centralized
- prefer a small set of named helpers instead of scattering inline DOM logic

### Risk: filter behavior becomes inconsistent between user mode and admin mode

Mitigation:

- keep filtering entirely inside the shared table rendering path
- avoid any mode-specific branches in the filter logic itself

### Risk: large distinct-value lists become hard to use

Mitigation:

- searchable option list inside the popup
- scrollable list container with fixed max height

### Risk: users lose confidence if draft edits apply too early

Mitigation:

- use explicit confirm and cancel actions
- do not mutate applied table state while the user is still exploring the list

## Test Plan

Add or update frontend tests to verify:

1. the old second-row filter controls no longer render
2. each header renders a dropdown trigger
3. opening a trigger renders the expected popup shell
4. ascending and descending sort reorder rows correctly
5. checkbox multi-select filters rows correctly
6. select-all resets or reapplies the visible option set correctly
7. popup search narrows the option list without applying row filtering before confirm
8. cancel restores the prior applied state
9. outside-click and `Esc` close the popup without committing draft edits
10. filter and sort state remain isolated per sheet key
11. the same behavior works in both user mode and admin mode shared Google Sheets tables
12. existing admin sync/status behavior remains unchanged

## Success Criteria

- SPMS Google Sheets tables no longer show the second filter row
- every column header exposes an Excel-like dropdown trigger
- users can sort and multi-filter rows from the popup menu without extra network requests
- popup filtering feels meaningfully closer to Excel than the current inline filter row
- filter state stays isolated by sheet tab
- user mode and admin mode share the same filtering behavior
- current Google Sheets loading, sync, and snapshot performance behavior does not regress
