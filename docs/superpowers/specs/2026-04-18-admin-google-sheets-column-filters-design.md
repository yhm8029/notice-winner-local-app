# Admin Google Sheets Column Filters Design

**Date**

- 2026-04-18

**Goal**

Add Excel-like per-column filtering to the SPMS admin Google Sheets table so admins can narrow visible rows immediately after the snapshot loads, without adding extra backend, Supabase, or Google Sheets traffic.

**Decision Summary**

- Keep filtering entirely on the frontend.
- Add one filter row directly under the table header.
- Support both free-text partial matching and per-column value selection.
- Apply text and select filters together for the same column.
- Store filter state per sheet key so switching tabs does not leak filters across different sheets.

## Background

- The admin Google Sheets view already renders snapshot-backed sheet data through [`frontend/admin-google-sheets-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/admin-google-sheets-runtime.js).
- The current table is read-only and shows all rows at once after the payload loads.
- The user wants an Excel-like filtering experience inside the SPMS web UI, not only in downloaded Excel files.
- The user explicitly wants both:
  - text search per column
  - drop-down style value selection per column
- The user also wants to avoid extra server cost or slower page loads.

## Scope

### In Scope

- adding a second header row for filters in the admin Google Sheets table
- per-column text filtering with partial match behavior
- per-column option filtering based on distinct values from the loaded sheet rows
- combining text and option filters for the same column
- preserving separate filter state for each Google Sheets admin tab
- frontend runtime tests for filter behavior and styles

### Out of Scope

- backend query filtering
- server-side pagination
- Google Sheets API query changes
- multi-select checkbox menus
- saving filter state to backend or browser storage across full page reloads
- changing the current snapshot schema

## Approaches Considered

1. Frontend-only inline filters under the header
   - Render filter controls as part of the existing table view.
   - Filter only the already-loaded payload rows in memory.
   - Pros: zero backend cost, instant response after payload load, smallest change set.
   - Cons: still limited by whatever rows are already present in the snapshot payload.
   - Recommended.

2. Backend-driven filter API
   - Send filter state back to the server and ask the backend to shape filtered rows.
   - Pros: central logic, possible future support for very large datasets.
   - Cons: extra requests, more complexity, more cost, slower interaction.

3. Separate filter sidebar
   - Keep the table clean and render filters outside the table grid.
   - Pros: visually tidy for wide tables.
   - Cons: weaker column association and slower scanning during use.

## Recommended Design

Keep the current table markup but insert a filter row below the title header row.

Each column gets two controls:

- a text input for partial matching
- a select box for distinct column values

The table body is re-derived from the loaded row data whenever any filter changes. Filtering rules:

1. If a text input is empty, it does not restrict rows.
2. If a select box is empty, it does not restrict rows.
3. If both are set for the same column, both must match.
4. A row is visible only if it passes every active column filter.

Matching policy:

- text matching is case-insensitive substring matching
- select matching compares the displayed cell text exactly after normalization
- linked cells use visible text for filtering, not the raw URL

## Data Model

The runtime should derive a lightweight filter model from the payload:

- `headers`
- normalized `rows`
- per-column distinct `options`
- current filter state

Suggested shape:

```js
{
  sheetKey: "sheet-1664606955",
  filters: [
    { query: "", selected: "" },
    { query: "창원", selected: "경상남도" },
  ],
}
```

State should be keyed by sheet key so `설계리스트` and `발주예정` filters remain independent.

## UI Behavior

### Filter Row

- show one filter cell below each header cell
- text input placeholder: `검색`
- select default option: `전체`
- long select lists should remain usable without expanding the whole layout

### Filtered Results

- update rows immediately on input and select change
- if no rows match, keep the table frame visible and show a single empty-state row such as `조건에 맞는 데이터가 없습니다.`
- do not mutate the original payload rows; always filter from the normalized source rows

### Tab Switching

- when switching sheet tabs, restore that tab’s own last-used filter state if it exists
- when a sheet payload is refreshed, keep the current filters for that sheet and recompute the visible rows
- if a selected option no longer exists after refresh, clear only that invalid option and keep other filters intact

## Architecture Changes

### Runtime

[`frontend/admin-google-sheets-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/admin-google-sheets-runtime.js)

- add helpers to normalize cell text for filtering
- derive distinct values per column
- render a filter row and filtered body rows
- expose enough output for existing app wiring to keep using the same runtime entrypoint

### App State

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)

- add sheet-keyed memory for active admin Google Sheets filters
- pass current filter state into the runtime builder
- accept filter change callbacks from the rendered table

### Styles

[`frontend/styles.css`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/styles.css)

- style the filter row so it remains usable within the sticky table header region
- keep controls compact enough for wide admin sheets

## Risks And Mitigations

### Risk: wide tables become visually crowded

Mitigation:

- compact inputs
- compact selects
- keep filters inside the sticky header area instead of adding another external panel

### Risk: filter state leaks across different sheets

Mitigation:

- store state per `sheetKey`
- rehydrate filters from that key only

### Risk: dropdown options become too large

Mitigation:

- derive options only from the currently loaded payload
- use the native select element rather than a custom popup component

## Test Plan

Add or update frontend runtime tests to verify:

1. filter controls render for each column
2. text query filters rows by visible cell text
3. select option filters rows by exact visible value
4. combined text + select filters apply together
5. no-match state renders without breaking the table
6. sheet-specific filter state stays isolated when tabs change

## Success Criteria

- admins can filter any loaded Google Sheets admin table directly in SPMS
- filtering happens without extra backend or Google requests
- filters support both text search and select-by-value
- switching sheets does not mix filter state between tabs
- existing admin Google Sheets rendering tests continue to pass
