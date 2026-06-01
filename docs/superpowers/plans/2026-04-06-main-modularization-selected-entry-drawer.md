# Main Modularization Selected Entry Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `selected entry drawer` 표시 계산을 [`frontend/selected-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/selected-entry-runtime.js) 로 분리하고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 상태 관리와 DOM 반영만 담당하게 만든다.

**Architecture:** `selected entry drawer` 는 `view-model + markup` 분리를 적용한다. runtime 은 loading/empty/patch panel/drawer/diagnostics/field grid 계산을 순수 함수로 제공하고, `app.js` 는 selected entry 상태, API 호출, 이벤트 바인딩, focus/select 같은 DOM 상호작용을 유지한다.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser global runtime pattern (`window.SPMS*Runtime`), existing frontend shell in `frontend/app.js`

---

## File Structure

- `frontend/selected-entry-runtime.js`
  - selected entry 메타, loading/empty view, patch panel view, drawer view, diagnostics markup, field grid markup helper를 가진다.
- `frontend/app.js`
  - selected entry 상태, API 흐름, DOM 반영, 버튼 바인딩, input focus/select, audit/change-events 로딩 연결을 유지한다.
- `tests/frontend/test_selected_entry_runtime.mjs`
  - runtime helper를 node 환경에서 직접 검증한다.

### Task 1: Add Selected Entry Runtime Tests

**Files:**
- Create: `tests/frontend/test_selected_entry_runtime.mjs`

- [ ] **Step 1: Write the failing test file**

```js
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/selected-entry-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSSelectedEntryRuntime;
}

test("buildSelectedEntryLoadingView returns loading copy for summary entry", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSelectedEntryLoadingView, "function");

  const view = runtime.buildSelectedEntryLoadingView(
    { project_name: "테스트 프로젝트" },
    { errorMessage: "" }
  );

  assert.equal(view.title, "테스트 프로젝트");
  assert.match(view.emptyStateText, /상세를 불러오는 중/);
  assert.match(view.auditHtml, /감사 로그/);
  assert.match(view.fieldGridHtml, /필드를 불러오는 중/);
});

test("buildSelectedEntryEmptyView returns disabled patch panel defaults", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSelectedEntryEmptyView, "function");

  const view = runtime.buildSelectedEntryEmptyView();

  assert.match(view.emptyStateText, /Select an entry/);
  assert.equal(view.patchValue, "");
  assert.equal(view.patchCurrentValueText, "-");
  assert.equal(view.patchOverrideMetaText, "no override");
  assert.equal(view.clearDisabled, true);
});

test("buildPatchPanelView reflects override state and current field value", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildPatchPanelView, "function");

  const view = runtime.buildPatchPanelView(
    {
      project_name: "강남 리모델링",
      progress_note: "",
      overridden_fields: ["project_name"],
    },
    { fieldName: "project_name" }
  );

  assert.equal(view.patchValue, "강남 리모델링");
  assert.equal(view.patchCurrentValueText, "강남 리모델링");
  assert.equal(view.patchOverrideMetaText, "override active");
  assert.equal(view.clearDisabled, false);
});

test("buildDrawerView returns drawer metadata and field list markup", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildDrawerView, "function");

  const view = runtime.buildDrawerView(
    {
      project_name: "성수 오피스",
      entry_key: "entry-7",
      row_no: 14,
      demand_org_name: "테스트 발주처",
      overridden_fields: ["progress_note"],
      progress_note: "조정 중",
    },
    {
      editableFields: ["progress_note"],
      escapeHtml: (value) => String(value),
    }
  );

  assert.equal(view.title, "성수 오피스");
  assert.match(view.metaText, /entry-7/);
  assert.match(view.statusLineHtml, /override active/);
  assert.match(view.fieldListHtml, /progress_note/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_selected_entry_runtime.mjs`
Expected: FAIL with messages like `runtime.buildSelectedEntryLoadingView is not a function`

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/frontend/test_selected_entry_runtime.mjs
git commit -m "test: selected entry runtime helper 기대값 추가"
```

### Task 2: Implement Selected Entry Runtime Helpers

**Files:**
- Modify: `frontend/selected-entry-runtime.js`
- Test: `tests/frontend/test_selected_entry_runtime.mjs`

- [ ] **Step 1: Add minimal helpers to satisfy the tests**

`frontend/selected-entry-runtime.js` 에 아래 순수 helper를 추가한다.

```js
function buildSelectedEntryLoadingView(entry, { errorMessage = "" } = {}) {
  const entryName = entry?.project_name || "선택한 프로젝트";
  return {
    title: entryName,
    emptyStateText: errorMessage
      ? `${entryName} 상세를 불러오지 못했습니다. ${errorMessage}`
      : `${entryName} 상세를 불러오는 중입니다.`,
    auditHtml: '<div class="empty-state">상세 정보를 불러오면 감사 로그가 표시됩니다.</div>',
    fieldGridHtml: '<div class="empty-state">상세 필드를 불러오는 중입니다.</div>',
    diagnosticsHtml: '<div class="empty-state">상세 정보를 불러오면 source와 근거가 표시됩니다.</div>',
    changeEventsHtml: '<div class="empty-state">최근 변경을 불러오는 중입니다.</div>',
    saveDisabled: true,
    clearDisabled: true,
  };
}

function buildSelectedEntryEmptyView() {
  return {
    emptyStateText: "Select an entry to browse fields.",
    auditHtml: '<div class="empty-state">No audit logs loaded.</div>',
    fieldGridHtml: '<div class="empty-state">Select an entry to browse fields.</div>',
    diagnosticsHtml: '<div class="empty-state">상세 정보를 불러오면 source와 근거가 표시됩니다.</div>',
    patchValue: "",
    patchCurrentValueText: "-",
    patchOverrideMetaText: "no override",
    clearDisabled: true,
  };
}

function buildPatchPanelView(entry, { fieldName = "" } = {}) {
  if (!entry || typeof entry !== "object") {
    return buildSelectedEntryEmptyView();
  }
  const overriddenFields = Array.isArray(entry.overridden_fields) ? entry.overridden_fields : [];
  const hasOverride = overriddenFields.includes(fieldName);
  const currentValue = entry[fieldName] ?? "";
  return {
    patchValue: currentValue,
    patchCurrentValueText: currentValue || "(empty)",
    patchOverrideMetaText: hasOverride ? "override active" : "source value in effect",
    clearDisabled: !hasOverride,
  };
}

function buildDrawerView(entry, { editableFields = [], escapeHtml = (value) => String(value || "") } = {}) {
  return {
    title: entry?.project_name || "",
    metaText: `${entry?.entry_key || ""} | row ${entry?.row_no || ""}`,
    statusLineHtml: `
      <span class="mono">${escapeHtml((entry?.overridden_fields || []).length ? "override active" : "source values")}</span>
      <span class="mono">${escapeHtml(entry?.demand_org_name || "")}</span>
    `,
    fieldListHtml: buildDrawerFieldListMarkup(entry, { editableFields, escapeHtml }),
  };
}
```

- [ ] **Step 2: Extend runtime with a selected entry display builder**

`buildSelectedEntryDisplayView(entry, options)` 를 추가해서 `renderSelectedEntry` 에 필요한 표시 데이터를 한 번에 조합한다.

```js
function buildSelectedEntryDisplayView(entry, options = {}) {
  const {
    summaryOnly = false,
    editableFields = [],
    activeField = "",
    truncate = (value) => String(value || ""),
    escapeHtml = (value) => String(value || ""),
  } = options;

  return {
    metaText: buildSelectedEntryMeta(entry, { summaryOnly }),
    fieldGridHtml: buildEntryFieldGridMarkup(entry, {
      editableFields,
      activeField,
      truncate,
      escapeHtml,
    }),
    diagnosticsHtml: summaryOnly
      ? '<div class="empty-state">상세 source와 근거를 불러오는 중입니다.</div>'
      : buildEntryDiagnosticsMarkup(entry, { escapeHtml }),
    drawerView: buildDrawerView(entry, { editableFields, escapeHtml }),
  };
}
```

- [ ] **Step 3: Re-run the runtime tests**

Run: `node --test tests/frontend/test_selected_entry_runtime.mjs`
Expected: PASS

- [ ] **Step 4: Run syntax check for the runtime**

Run: `node --check frontend/selected-entry-runtime.js`
Expected: exit `0`

- [ ] **Step 5: Commit the runtime helper implementation**

```bash
git add frontend/selected-entry-runtime.js tests/frontend/test_selected_entry_runtime.mjs
git commit -m "refactor: selected entry runtime helper 추가"
```

### Task 3: Wire App Rendering to the Runtime

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/selected-entry-runtime.js`
- Test: `tests/frontend/test_selected_entry_runtime.mjs`

- [ ] **Step 1: Replace loading rendering with runtime output**

`renderSelectedEntryLoading` 이 직접 문구를 조합하지 않고 runtime helper 결과를 사용하게 바꾼다.

```js
function renderSelectedEntryLoading(entry, errorMessage = "") {
  const view = requireSelectedEntryRuntime().buildSelectedEntryLoadingView(entry, { errorMessage });
  dom.entryEmptyState.classList.remove("hidden");
  dom.entryEditor.classList.add("hidden");
  dom.entryEmptyState.textContent = view.emptyStateText;
  dom.auditLogList.innerHTML = view.auditHtml;
  dom.entryFieldGrid.innerHTML = view.fieldGridHtml;
  if (dom.entryDiagnosticsList) {
    dom.entryDiagnosticsList.innerHTML = view.diagnosticsHtml;
  }
  if (dom.selectedEntryChangeList) {
    dom.selectedEntryChangeList.innerHTML = view.changeEventsHtml;
  }
  dom.saveEntryButton.disabled = view.saveDisabled;
  dom.clearEntryButton.disabled = view.clearDisabled;
}
```

- [ ] **Step 2: Replace empty-state and patch panel calculations**

`renderSelectedEntry(null)` 와 `syncPatchValueFromSelectedEntry()` 에서 runtime helper 결과를 사용하게 바꾼다.

```js
const emptyView = requireSelectedEntryRuntime().buildSelectedEntryEmptyView();
dom.entryEmptyState.textContent = emptyView.emptyStateText;
dom.auditLogList.innerHTML = emptyView.auditHtml;
dom.entryFieldGrid.innerHTML = emptyView.fieldGridHtml;
dom.entryDiagnosticsList.innerHTML = emptyView.diagnosticsHtml;
dom.patchValue.value = emptyView.patchValue;
dom.patchCurrentValue.textContent = emptyView.patchCurrentValueText;
dom.patchOverrideMeta.textContent = emptyView.patchOverrideMetaText;
dom.clearEntryButton.disabled = emptyView.clearDisabled;
```

```js
const patchView = requireSelectedEntryRuntime().buildPatchPanelView(state.selectedEntry, {
  fieldName: dom.patchField.value,
});
dom.patchValue.value = patchView.patchValue;
dom.patchCurrentValue.textContent = patchView.patchCurrentValueText;
dom.patchOverrideMeta.textContent = patchView.patchOverrideMetaText;
dom.clearEntryButton.disabled = patchView.clearDisabled;
```

- [ ] **Step 3: Replace selected entry display rendering**

`renderSelectedEntry`, `renderEntryFieldGrid`, `renderEntryDiagnostics`, `renderDrawer` 내부의 표시 계산을 runtime helper 기반으로 치환한다. 이벤트 바인딩과 focus/select 는 그대로 `app.js` 에 둔다.

```js
const runtime = requireSelectedEntryRuntime();
const displayView = runtime.buildSelectedEntryDisplayView(entry, {
  summaryOnly,
  editableFields: EDITABLE_FIELDS,
  activeField: dom.patchField.value,
  truncate,
  escapeHtml,
});

dom.entryMeta.textContent = displayView.metaText;
dom.entryFieldGrid.innerHTML = displayView.fieldGridHtml;
dom.entryDiagnosticsList.innerHTML = displayView.diagnosticsHtml;
dom.drawerTitle.textContent = displayView.drawerView.title;
dom.drawerMeta.textContent = displayView.drawerView.metaText;
dom.drawerStatusLine.innerHTML = displayView.drawerView.statusLineHtml;
dom.drawerFieldList.innerHTML = displayView.drawerView.fieldListHtml;
```

- [ ] **Step 4: Keep event binding in `app.js` and confirm runtime does not touch DOM**

확인 기준:
- `selected-entry-runtime.js` 안에 `querySelector`, `addEventListener`, `focus`, `select` 가 없어야 한다.
- `app.js` 안에서 `[data-field]`, `[data-drawer-field]` 바인딩은 그대로 유지한다.

Run:
- `rg -n "querySelector|addEventListener|focus\\(|select\\(" frontend/selected-entry-runtime.js`

Expected: no matches

- [ ] **Step 5: Run focused verification**

Run:
- `node --check frontend/app.js`
- `node --check frontend/selected-entry-runtime.js`
- `node --test tests/frontend/test_selected_entry_runtime.mjs`

Expected:
- syntax checks exit `0`
- node test PASS

- [ ] **Step 6: Commit the app integration**

```bash
git add frontend/app.js frontend/selected-entry-runtime.js tests/frontend/test_selected_entry_runtime.mjs
git commit -m "refactor: selected entry drawer runtime 경계 정리"
```

### Task 4: Final Regression Pass

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/selected-entry-runtime.js`
- Test: `tests/frontend/test_run_view_runtime.mjs`
- Test: `tests/frontend/test_tracker_diagnostics_runtime.mjs`
- Test: `tests/frontend/test_selected_entry_runtime.mjs`

- [ ] **Step 1: Run all related frontend runtime tests together**

Run:
- `node --test tests/frontend/test_run_view_runtime.mjs`
- `node --test tests/frontend/test_tracker_diagnostics_runtime.mjs`
- `node --test tests/frontend/test_selected_entry_runtime.mjs`

Expected: all PASS

- [ ] **Step 2: Run final syntax checks**

Run:
- `node --check frontend/app.js`
- `node --check frontend/run-view-runtime.js`
- `node --check frontend/tracker-diagnostics-runtime.js`
- `node --check frontend/selected-entry-runtime.js`

Expected: all exit `0`

- [ ] **Step 3: Confirm worktree contains only intended files**

Run: `git status --short`
Expected: either empty output or only the three files from this plan before the final commit

- [ ] **Step 4: Commit any final regression-only cleanup**

```bash
git add frontend/app.js frontend/selected-entry-runtime.js tests/frontend/test_selected_entry_runtime.mjs
git commit -m "test: selected entry drawer 모듈화 회귀 검증 정리"
```
