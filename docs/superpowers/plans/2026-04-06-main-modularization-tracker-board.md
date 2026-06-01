# Main Modularization Tracker Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `tracker board`의 렌더링과 edit markup/view-model 계산을 [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 로 분리하고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 상태와 이벤트 흐름만 담당하게 만든다.

**Architecture:** `tracker board` 는 `view-model + markup` 분리를 적용한다. runtime 은 empty state, blank-priority sorting, header/cell/edit-form markup, table markup 을 순수 helper 로 제공하고, `app.js` 는 `trackerBoardSort`, `trackerBoardEdit`, row/cell 이벤트, save/cancel, keydown/input, selected state 연계를 유지한다.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser global runtime pattern (`window.SPMS*Runtime`), existing frontend shell in `frontend/app.js`

---

## File Structure

- `frontend/tracker-entry-runtime.js`
  - tracker entry summary/list helper와 함께 board rendering helper를 가진다.
- `frontend/app.js`
  - `renderTrackerBoard()` 호출, state 갱신, 이벤트 바인딩, `saveTrackerBoardEdit()` 연결을 유지한다.
- `tests/frontend/test_tracker_board_runtime.mjs`
  - board runtime helper를 node 환경에서 직접 검증한다.
- `tests/frontend/test_tracker_board_app_integration.mjs`
  - `renderTrackerBoard()` 가 runtime helper 경로를 사용하는지 구조적으로 검증한다.

### Task 1: Add Tracker Board Runtime Tests

**Files:**
- Create: `tests/frontend/test_tracker_board_runtime.mjs`

- [ ] **Step 1: Write the failing runtime tests**

```js
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/tracker-entry-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSTrackerEntryRuntime;
}

test("buildTrackerBoardEmptyStateView returns empty-state markup", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerBoardEmptyStateView, "function");

  const view = runtime.buildTrackerBoardEmptyStateView({
    emptyHtml: '<div class="empty-state">No board rows.</div>',
  });

  assert.match(view.html, /No board rows/);
  assert.equal(view.className, "tracker-board-content empty-state");
});

test("buildSortedTrackerBoardEntries applies blank-priority ordering", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSortedTrackerBoardEntries, "function");

  const sorted = runtime.buildSortedTrackerBoardEntries(
    [
      { id: "a", demand_contact: "홍길동" },
      { id: "b", demand_contact: "" },
      { id: "c", demand_contact: "김철수" },
    ],
    {
      fieldName: "demand_contact",
      blankPriorityFields: ["demand_contact"],
    }
  );

  assert.deepEqual(sorted.map((item) => item.id), ["b", "a", "c"]);
});

test("buildTrackerBoardCellMarkup returns edit trigger for editable cells", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerBoardCellMarkup, "function");

  const html = runtime.buildTrackerBoardCellMarkup(
    {
      entry: {
        id: "entry-1",
        project_name: "테스트 프로젝트",
        overridden_fields: ["project_name"],
      },
      column: { key: "project_name", label: "프로젝트명", editable: true },
      displayNo: 1,
      trackerBoardEdit: { entryId: null, fieldName: "", draftValue: "", saving: false, errorMessage: "" },
      textareaFields: ["progress_note"],
    },
    { escapeHtml: (value) => String(value) }
  );

  assert.match(html, /data-board-edit-trigger/);
  assert.match(html, /is-overridden/);
});

test("buildTrackerBoardEditingCellMarkup renders textarea form for progress_note", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerBoardEditingCellMarkup, "function");

  const html = runtime.buildTrackerBoardEditingCellMarkup(
    {
      entry: { id: "entry-1" },
      fieldName: "progress_note",
      label: "주요진행사항",
      value: "작성 중",
      saving: false,
      errorMessage: "",
      textareaFields: ["progress_note"],
    },
    { escapeHtml: (value) => String(value) }
  );

  assert.match(html, /textarea/);
  assert.match(html, /data-board-edit-form/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_tracker_board_runtime.mjs`
Expected: FAIL with messages like `runtime.buildTrackerBoardEmptyStateView is not a function`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/frontend/test_tracker_board_runtime.mjs
git commit -m "test: tracker board runtime helper 기대값 추가"
```

### Task 2: Implement Tracker Board Runtime Helpers

**Files:**
- Modify: `frontend/tracker-entry-runtime.js`
- Test: `tests/frontend/test_tracker_board_runtime.mjs`

- [ ] **Step 1: Add empty-state and sorting helpers**

`frontend/tracker-entry-runtime.js` 에 아래 helper 를 추가한다.

```js
function buildTrackerBoardEmptyStateView({
  emptyHtml = '<div class="empty-state">No board rows loaded.</div>',
} = {}) {
  return {
    html: emptyHtml,
    className: "tracker-board-content empty-state",
  };
}

function buildSortedTrackerBoardEntries(entries, {
  fieldName = "",
  blankPriorityFields = [],
} = {}) {
  if (!blankPriorityFields.includes(fieldName)) {
    return entries;
  }
  return entries
    .map((entry, index) => ({ entry, index }))
    .sort((left, right) => {
      const leftBlank = !String(left.entry[fieldName] ?? "").trim();
      const rightBlank = !String(right.entry[fieldName] ?? "").trim();
      if (leftBlank !== rightBlank) {
        return leftBlank ? -1 : 1;
      }
      return left.index - right.index;
    })
    .map(({ entry }) => entry);
}
```

- [ ] **Step 2: Add header, cell, edit-form, and table markup helpers**

```js
function buildTrackerBoardHeaderCellMarkup(column, {
  active = false,
  escapeHtml = (value) => String(value || ""),
} = {}) {
  if (!column?.blankPriority) {
    return `<th>${escapeHtml(column?.label || "")}</th>`;
  }
  return `
    <th class="tracker-board-head-cell">
      <button
        class="tracker-board-sort-trigger${active ? " is-active" : ""}"
        type="button"
        data-board-sort-field="${escapeHtml(column.key)}"
      >
        <span>${escapeHtml(column.label)}</span>
        <span class="tracker-board-sort-meta mono">${active ? "빈 값 우선" : "클릭 시 빈 값 우선"}</span>
      </button>
    </th>
  `;
}

function buildTrackerBoardEditingCellMarkup(options, { escapeHtml = (value) => String(value || "") } = {}) {
  const { entry, fieldName, label, value, saving, errorMessage, textareaFields = [] } = options;
  const textarea = textareaFields.includes(fieldName);
  const inputMarkup = textarea
    ? `<textarea class="tracker-board-edit-input tracker-board-edit-input-textarea" rows="${fieldName === "progress_note" ? "4" : "3"}" data-board-edit-input="true" data-board-edit-entry-id="${escapeHtml(entry.id)}" data-board-edit-field="${escapeHtml(fieldName)}" data-board-edit-active="true" ${saving ? "disabled" : ""}>${escapeHtml(value || "")}</textarea>`
    : `<input class="tracker-board-edit-input" type="text" value="${escapeHtml(value || "")}" data-board-edit-input="true" data-board-edit-entry-id="${escapeHtml(entry.id)}" data-board-edit-field="${escapeHtml(fieldName)}" data-board-edit-active="true" ${saving ? "disabled" : ""} />`;
  return `
    <td class="tracker-board-cell tracker-board-cell-editing">
      <form class="tracker-board-edit-form" data-board-edit-form="true" data-board-edit-entry-id="${escapeHtml(entry.id)}" data-board-edit-field="${escapeHtml(fieldName)}">
        <span class="tracker-board-edit-label">${escapeHtml(label)}</span>
        ${inputMarkup}
        <div class="tracker-board-edit-actions">
          <button class="primary-button tracker-board-edit-save" type="submit" ${saving ? "disabled" : ""}>저장</button>
          <button class="ghost-button tracker-board-edit-cancel" type="button" data-board-edit-cancel="true" ${saving ? "disabled" : ""}>취소</button>
        </div>
        <p class="tracker-board-edit-hint mono">${textarea ? "Enter 저장 / Shift+Enter 줄바꿈 / Esc 취소" : "Enter 저장 / Esc 취소"}</p>
        ${errorMessage ? `<p class="tracker-board-edit-error">${escapeHtml(errorMessage)}</p>` : ""}
      </form>
    </td>
  `;
}
```

- [ ] **Step 3: Add board cell/row/table helper**

```js
function buildTrackerBoardCellMarkup(options, helpers = {}) {
  const {
    entry,
    column,
    displayNo,
    trackerBoardEdit,
    textareaFields = [],
  } = options;
  const { escapeHtml = (value) => String(value || "") } = helpers;

  if (column.key === "display_no") {
    return `<td>${displayNo}</td>`;
  }
  const value = entry[column.key] || "";
  const isEditing = trackerBoardEdit.entryId === entry.id && trackerBoardEdit.fieldName === column.key;
  const overrideClass = (entry.overridden_fields || []).includes(column.key) ? " is-overridden" : "";
  if (!column.editable) {
    return `<td>${escapeHtml(value || "-")}</td>`;
  }
  if (isEditing) {
    return buildTrackerBoardEditingCellMarkup({
      entry,
      fieldName: column.key,
      label: column.label,
      value: trackerBoardEdit.draftValue,
      saving: trackerBoardEdit.saving,
      errorMessage: trackerBoardEdit.errorMessage,
      textareaFields,
    }, helpers);
  }
  return `
    <td class="tracker-board-cell${overrideClass}">
      <button class="tracker-board-edit-trigger" type="button" data-board-edit-trigger="true" data-board-edit-entry-id="${escapeHtml(entry.id)}" data-board-edit-field="${escapeHtml(column.key)}">
        <span class="tracker-board-cell-value">${escapeHtml(value || "-")}</span>
        <span class="tracker-board-cell-meta mono">${(entry.overridden_fields || []).includes(column.key) ? "override" : "클릭해 수정"}</span>
      </button>
    </td>
  `;
}

function buildTrackerBoardMarkup(entries, options = {}, helpers = {}) {
  const {
    columns = [],
    currentSortField = "",
    trackerBoardEdit = { entryId: null, fieldName: "", draftValue: "", saving: false, errorMessage: "" },
    textareaFields = [],
    blankPriorityFields = [],
    page = 1,
    pageSize = 20,
    selectedEntryId = "",
  } = options;
  const { escapeHtml = (value) => String(value || "") } = helpers;
  const boardEntries = buildSortedTrackerBoardEntries(entries, {
    fieldName: currentSortField,
    blankPriorityFields,
  });
  return `
    <table class="tracker-board-table">
      <thead>
        <tr>
          ${columns.map((column) => buildTrackerBoardHeaderCellMarkup(
            { ...column, blankPriority: blankPriorityFields.includes(column.key) },
            { active: currentSortField === column.key, escapeHtml }
          )).join("")}
        </tr>
      </thead>
      <tbody>
        ${boardEntries.map((entry, index) => {
          const displayNo = (page - 1) * pageSize + index + 1;
          const cells = columns.map((column) => buildTrackerBoardCellMarkup({
            entry,
            column,
            displayNo,
            trackerBoardEdit,
            textareaFields,
          }, { escapeHtml })).join("");
          return `<tr data-board-entry-id="${escapeHtml(entry.id)}" class="${entry.id === selectedEntryId ? "is-selected" : ""}">${cells}</tr>`;
        }).join("")}
      </tbody>
    </table>
  `;
}
```

- [ ] **Step 4: Re-run runtime tests**

Run: `node --test tests/frontend/test_tracker_board_runtime.mjs`
Expected: PASS

- [ ] **Step 5: Run syntax check**

Run: `node --check frontend/tracker-entry-runtime.js`
Expected: exit `0`

- [ ] **Step 6: Commit the runtime helper implementation**

```bash
git add frontend/tracker-entry-runtime.js tests/frontend/test_tracker_board_runtime.mjs
git commit -m "refactor: tracker board runtime helper 추가"
```

### Task 3: Wire `renderTrackerBoard()` to the Runtime

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/tracker-entry-runtime.js`
- Create: `tests/frontend/test_tracker_board_app_integration.mjs`

- [ ] **Step 1: Add an integration guard test**

```js
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

test("renderTrackerBoard uses tracker-entry runtime helpers", () => {
  const source = readAppSource();
  const start = source.indexOf("function renderTrackerBoard");
  const end = source.indexOf("function renderTrackerBoardHeaderCell", start);
  const block = source.slice(start, end);

  assert.match(block, /buildTrackerBoardEmptyStateView/);
  assert.match(block, /buildTrackerBoardMarkup/);
  assert.doesNotMatch(block, /dom\\.trackerBoard\\.innerHTML\\s*=\\s*`/);
});
```

- [ ] **Step 2: Run the integration test to verify it fails**

Run: `node --test tests/frontend/test_tracker_board_app_integration.mjs`
Expected: FAIL because `renderTrackerBoard()` still builds inline table markup

- [ ] **Step 3: Replace inline board rendering with runtime helpers**

```js
function renderTrackerBoard(entries) {
  if (!dom.trackerBoard) {
    return;
  }
  if (!entries.length) {
    const emptyView = buildTrackerBoardEmptyStateView({
      emptyHtml: '<div class="empty-state">트래커 행을 불러오면 여기에 보드가 표시됩니다.</div>',
    }) || { html: '<div class="empty-state">트래커 행을 불러오면 여기에 보드가 표시됩니다.</div>', className: "tracker-board-content empty-state" };
    dom.trackerBoard.innerHTML = emptyView.html;
    dom.trackerBoard.className = emptyView.className;
    return;
  }
  dom.trackerBoard.className = "tracker-board-content";
  dom.trackerBoard.innerHTML = buildTrackerBoardMarkup(entries, {
    columns: TRACKER_BOARD_COLUMNS,
    currentSortField: state.trackerBoardSort.fieldName,
    trackerBoardEdit: state.trackerBoardEdit,
    textareaFields: [...TRACKER_BOARD_TEXTAREA_FIELDS],
    blankPriorityFields: [...TRACKER_BOARD_BLANK_PRIORITY_FIELDS],
    page: state.trackerFilters.page,
    pageSize: state.trackerFilters.pageSize,
    selectedEntryId: state.selectedEntryId,
  }, { escapeHtml });
  // existing event binding loops remain below
}
```

- [ ] **Step 4: Replace sorting/header/cell helper calls in `app.js`**

Remove inline-only board helpers from `app.js` after `renderTrackerBoard()` switches to runtime:
- `renderTrackerBoardHeaderCell`
- `isTrackerBoardBlankValue`
- `getSortedTrackerBoardEntries`
- `renderTrackerBoardCell`
- `renderTrackerBoardEditingCell`

Expected end state:
- board markup generation lives in runtime
- `app.js` keeps only binding/state helpers like `toggleTrackerBoardBlankPriority`, `beginTrackerBoardEdit`, `resetTrackerBoardEdit`, `saveTrackerBoardEdit`

- [ ] **Step 5: Keep event binding in `app.js` and confirm runtime stays pure**

Run:
- `rg -n "querySelector|addEventListener|focus\\(|select\\(" frontend/tracker-entry-runtime.js`

Expected: no matches

- [ ] **Step 6: Run focused verification**

Run:
- `node --test tests/frontend/test_tracker_board_runtime.mjs`
- `node --test tests/frontend/test_tracker_board_app_integration.mjs`
- `node --check frontend/app.js`
- `node --check frontend/tracker-entry-runtime.js`

Expected: all PASS / exit `0`

- [ ] **Step 7: Commit the app integration**

```bash
git add frontend/app.js frontend/tracker-entry-runtime.js tests/frontend/test_tracker_board_runtime.mjs tests/frontend/test_tracker_board_app_integration.mjs
git commit -m "refactor: tracker board runtime 경계 정리"
```

### Task 4: Final Frontend Regression Pass

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/tracker-entry-runtime.js`
- Test: `tests/frontend/test_run_view_runtime.mjs`
- Test: `tests/frontend/test_tracker_diagnostics_runtime.mjs`
- Test: `tests/frontend/test_selected_entry_runtime.mjs`
- Test: `tests/frontend/test_selected_entry_app_integration.mjs`
- Test: `tests/frontend/test_tracker_entry_runtime.mjs`
- Test: `tests/frontend/test_tracker_entry_app_integration.mjs`
- Test: `tests/frontend/test_tracker_board_runtime.mjs`
- Test: `tests/frontend/test_tracker_board_app_integration.mjs`

- [ ] **Step 1: Run all related frontend runtime tests**

Run:
- `node --test tests/frontend/test_run_view_runtime.mjs`
- `node --test tests/frontend/test_tracker_diagnostics_runtime.mjs`
- `node --test tests/frontend/test_selected_entry_runtime.mjs`
- `node --test tests/frontend/test_selected_entry_app_integration.mjs`
- `node --test tests/frontend/test_tracker_entry_runtime.mjs`
- `node --test tests/frontend/test_tracker_entry_app_integration.mjs`
- `node --test tests/frontend/test_tracker_board_runtime.mjs`
- `node --test tests/frontend/test_tracker_board_app_integration.mjs`

Expected: all PASS

- [ ] **Step 2: Run final syntax checks**

Run:
- `node --check frontend/app.js`
- `node --check frontend/run-view-runtime.js`
- `node --check frontend/tracker-diagnostics-runtime.js`
- `node --check frontend/selected-entry-runtime.js`
- `node --check frontend/tracker-entry-runtime.js`

Expected: all exit `0`

- [ ] **Step 3: Confirm worktree contains only intended files**

Run: `git status --short`
Expected: either empty output or only the files from this plan before the final commit

- [ ] **Step 4: Commit any final regression-only cleanup**

```bash
git add frontend/app.js frontend/tracker-entry-runtime.js tests/frontend/test_tracker_board_runtime.mjs tests/frontend/test_tracker_board_app_integration.mjs
git commit -m "test: tracker board 모듈화 회귀 검증 정리"
```
