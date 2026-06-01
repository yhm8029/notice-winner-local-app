# Admin Google Sheets Column Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add frontend-only per-column text and select filters to the admin Google Sheets table without increasing backend request load.

**Architecture:** Extend the existing admin Google Sheets runtime so it normalizes cell text, computes per-column distinct options, and renders a second sticky header row containing a text input and a select for each column. Keep filter state in `frontend/app.js`, keyed by sheet tab, so the runtime stays reusable and sheet switches preserve only that sheet’s own filters.

**Tech Stack:** Vanilla JavaScript, existing admin Google Sheets runtime, existing frontend node tests, CSS

---

## File Map

- Modify: `frontend/admin-google-sheets-runtime.js`
  - add row normalization, distinct option derivation, filter application, and filter row rendering
- Modify: `frontend/app.js`
  - keep per-sheet admin Google Sheets filter state and re-render when filters change
- Modify: `frontend/styles.css`
  - style filter controls inside the Google Sheets table header region
- Modify: `tests/frontend/test_admin_google_sheets_runtime.mjs`
  - cover runtime filtering behavior and no-match rendering
- Modify: `tests/frontend/test_admin_tabs_app_integration.mjs`
  - cover sheet-keyed filter state retention in app wiring

### Task 1: Add failing runtime tests for column filtering

**Files:**
- Modify: `tests/frontend/test_admin_google_sheets_runtime.mjs`
- Test: `tests/frontend/test_admin_google_sheets_runtime.mjs`

- [ ] **Step 1: Write failing tests for text, select, and empty-state filtering**

```js
test("buildAdminGoogleSheetTableView renders filter controls and filters rows by query and selected value", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView({
    headers: ["지역", "기관"],
    rows: [
      ["서울", "서울교육청"],
      ["경남", "경남교육청"],
      ["경남", "창원시"],
    ],
    filters: [
      { query: "경남", selected: "" },
      { query: "", selected: "경남교육청" },
    ],
  });

  assert.match(view.html, /admin-google-sheet-filter-row/);
  assert.match(view.html, /value=\"경남\"/);
  assert.match(view.html, /<td>경남<\/td>/);
  assert.match(view.html, /경남교육청/);
  assert.doesNotMatch(view.html, /서울교육청/);
  assert.doesNotMatch(view.html, /창원시/);
});

test("buildAdminGoogleSheetTableView renders no-match state when filters remove all rows", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView({
    headers: ["지역"],
    rows: [["서울"], ["경남"]],
    filters: [{ query: "부산", selected: "" }],
  });

  assert.match(view.html, /조건에 맞는 데이터가 없습니다/);
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs`
Expected: FAIL because the runtime does not render a filter row or apply any `filters` input yet

- [ ] **Step 3: Implement the minimal runtime filtering helpers**

```js
function normalizeFilterText(value) {
  return String(value ?? "").trim().toLowerCase();
}

function buildColumnOptions(rows, columnIndex) {
  return Array.from(
    new Set(
      rows
        .map((row) => normalizeCellEntry(row[columnIndex]).text)
        .filter(Boolean),
    ),
  ).sort((left, right) => left.localeCompare(right, "ko"));
}

function rowMatchesFilters(row, filters) {
  return filters.every((filter, index) => {
    const cellText = normalizeFilterText(normalizeCellEntry(row[index]).text);
    const query = normalizeFilterText(filter?.query);
    const selected = String(filter?.selected ?? "").trim();
    if (query && !cellText.includes(query)) return false;
    if (selected && normalizeCellEntry(row[index]).text !== selected) return false;
    return true;
  });
}
```

- [ ] **Step 4: Re-run the runtime tests**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/admin-google-sheets-runtime.js tests/frontend/test_admin_google_sheets_runtime.mjs
git commit -m "feat: add admin google sheets column filter runtime"
```

### Task 2: Preserve filter state per admin Google Sheets tab in app wiring

**Files:**
- Modify: `frontend/app.js`
- Modify: `tests/frontend/test_admin_tabs_app_integration.mjs`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Write the failing app integration test**

```js
test("admin google sheets keeps filter state isolated per sheet key", async () => {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/admin",
    search: "?mode=project-status&admin_tab=sheet-1",
  });
  authorizeHarness(harness);

  const state = harness.hooks.state;
  state.adminGoogleSheetsBootstrap = {
    sync_status: "ready",
    tabs: [
      { key: "sheet-1", display_title: "설계리스트", raw_title: "설계리스트", sheet_id: 1, sheet_order: 1 },
      { key: "sheet-2", display_title: "발주예정", raw_title: "발주예정", sheet_id: 2, sheet_order: 2 },
    ],
  };
  state.adminGoogleSheetsSheetPayloads["sheet-1"] = {
    headers: ["지역"],
    rows: [["서울"], ["경남"]],
  };
  state.adminGoogleSheetsSheetPayloads["sheet-2"] = {
    headers: ["지역"],
    rows: [["부산"], ["대구"]],
  };

  harness.hooks.setAdminGoogleSheetsFilters("sheet-1", [{ query: "경남", selected: "" }]);
  assert.deepEqual(
    JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetsFilters("sheet-1"))),
    [{ query: "경남", selected: "" }],
  );
  assert.deepEqual(
    JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetsFilters("sheet-2"))),
    [],
  );
});
```

- [ ] **Step 2: Run the integration test to verify it fails**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: FAIL because the app does not expose or maintain per-sheet admin Google Sheets filter state

- [ ] **Step 3: Implement minimal app state wiring**

```js
state.adminGoogleSheetsFiltersBySheet = {};

function getAdminGoogleSheetsFilters(sheetKey) {
  return Array.isArray(state.adminGoogleSheetsFiltersBySheet[sheetKey])
    ? state.adminGoogleSheetsFiltersBySheet[sheetKey]
    : [];
}

function setAdminGoogleSheetsFilters(sheetKey, filters) {
  state.adminGoogleSheetsFiltersBySheet[sheetKey] = Array.isArray(filters)
    ? filters.map((item) => ({
        query: String(item?.query ?? ""),
        selected: String(item?.selected ?? ""),
      }))
    : [];
  renderAdminTabPanel();
}
```

- [ ] **Step 4: Re-run the integration test**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "feat: preserve admin google sheets filters per sheet"
```

### Task 3: Add filter-row styles and run focused frontend verification

**Files:**
- Modify: `frontend/styles.css`
- Test: `tests/frontend/test_admin_google_sheets_runtime.mjs`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Add a style assertion**

```js
test("admin google sheet filter styles exist", () => {
  const styles = fs.readFileSync(stylesPath, "utf8");

  assert.match(styles, /\.admin-google-sheet-filter-row/);
  assert.match(styles, /\.admin-google-sheet-filter-input/);
  assert.match(styles, /\.admin-google-sheet-filter-select/);
});
```

- [ ] **Step 2: Run focused frontend tests and verify the new assertion fails first**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: FAIL because the filter style selectors do not exist yet

- [ ] **Step 3: Add minimal styles**

```css
.admin-google-sheet-filter-row th {
  padding: 8px 10px;
  background: rgba(255, 246, 237, 0.98);
}

.admin-google-sheet-filter-input,
.admin-google-sheet-filter-select {
  width: 100%;
  min-width: 110px;
  border: 1px solid rgba(92, 66, 44, 0.16);
  border-radius: 10px;
  background: #fffdf9;
}
```

- [ ] **Step 4: Re-run focused frontend tests**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/styles.css tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "style: add admin google sheets filter controls"
```
