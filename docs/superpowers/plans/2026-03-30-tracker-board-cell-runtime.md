# Tracker Board Cell Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `frontend/app.js`의 트래커 보드 셀 마크업과 편집 셀 마크업을 `frontend/tracker-board-runtime.js`로 분리한다.

**Architecture:** `frontend/app.js`는 정렬, 편집 상태 판단, 테이블 조립, 이벤트 wiring을 유지하고, `frontend/tracker-board-runtime.js`는 순수 마크업 helper만 추가한다. 셀 단위 HTML과 편집 셀 HTML은 runtime이 만들고, `app.js`는 현재 state를 payload/helpers로 전달해 호출한다.

**Tech Stack:** Vanilla JavaScript, Node built-in `node:test`, `node --check`, existing `window.SPMSTrackerBoardRuntime` IIFE pattern

---

## File Structure

- Modify: `frontend/tracker-board-runtime.js`
- Modify: `frontend/app.js`
- Modify: `frontend/tests/tracker-board-runtime.test.js`

### Task 1: Extract Tracker Board Cell Markup Helpers

**Files:**
- Modify: `frontend/tracker-board-runtime.js`
- Modify: `frontend/app.js:8127-8204`
- Modify: `frontend/tests/tracker-board-runtime.test.js`

- [ ] **Step 1: Write the failing tests**

Add these tests to `frontend/tests/tracker-board-runtime.test.js`:

```javascript
test("buildTrackerBoardCellMarkup renders display number cell", () => {
  const runtime = loadRuntime("frontend/tracker-board-runtime.js");
  const html = runtime.buildTrackerBoardCellMarkup(
    {
      entry: { id: "entry-1", overridden_fields: [] },
      column: { key: "display_no", label: "번호", editable: false },
      displayNo: 7,
      value: "",
      isEditing: false,
      isOverridden: false,
    },
    { escapeHtml: (value) => String(value) },
  );
  assert.equal(html, "<td>7</td>");
});

test("buildTrackerBoardCellMarkup renders editable override cell with selector contract", () => {
  const runtime = loadRuntime("frontend/tracker-board-runtime.js");
  const html = runtime.buildTrackerBoardCellMarkup(
    {
      entry: { id: "entry-1", overridden_fields: ["demand_contact"] },
      column: { key: "demand_contact", label: "담당", editable: true },
      displayNo: 1,
      value: "홍길동",
      isEditing: false,
      isOverridden: true,
    },
    { escapeHtml: (value) => String(value) },
  );
  assert.match(html, /tracker-board-cell is-overridden/);
  assert.match(html, /data-board-edit-trigger="true"/);
  assert.match(html, /data-board-edit-entry-id="entry-1"/);
  assert.match(html, /data-board-edit-field="demand_contact"/);
  assert.match(html, /override/);
});

test("buildTrackerBoardEditingCellMarkup renders textarea editing state with error", () => {
  const runtime = loadRuntime("frontend/tracker-board-runtime.js");
  const html = runtime.buildTrackerBoardEditingCellMarkup(
    {
      entryId: "entry-1",
      fieldName: "progress_note",
      label: "진행 메모",
      value: "메모",
      saving: false,
      errorMessage: "저장 실패",
      textarea: true,
      rows: 4,
    },
    { escapeHtml: (value) => String(value) },
  );
  assert.match(html, /<textarea/);
  assert.match(html, /rows="4"/);
  assert.match(html, /data-board-edit-form="true"/);
  assert.match(html, /저장 실패/);
});

test("buildTrackerBoardEditingCellMarkup renders text input with disabled controls", () => {
  const runtime = loadRuntime("frontend/tracker-board-runtime.js");
  const html = runtime.buildTrackerBoardEditingCellMarkup(
    {
      entryId: "entry-2",
      fieldName: "project_name",
      label: "프로젝트명",
      value: "Alpha",
      saving: true,
      errorMessage: "",
      textarea: false,
      rows: 1,
    },
    { escapeHtml: (value) => String(value) },
  );
  assert.match(html, /<input/);
  assert.match(html, /data-board-edit-input="true"/);
  assert.match(html, /disabled/);
  assert.match(html, /data-board-edit-cancel="true"/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/tracker-board-runtime.test.js`

Expected: FAIL with `TypeError` because the new runtime helpers do not exist yet

- [ ] **Step 3: Write minimal runtime implementation**

Add these helpers to `frontend/tracker-board-runtime.js` and export them from `window.SPMSTrackerBoardRuntime`:

```javascript
function buildTrackerBoardCellMarkup(payload = {}, helpers = {}) {
  const {
    entry = {},
    column = {},
    displayNo = 0,
    value = "",
    isEditing = false,
    isOverridden = false,
    editingCellMarkup = "",
  } = payload;
  const { escapeHtml = (raw) => String(raw ?? "") } = helpers;
  if (column.key === "display_no") {
    return `<td>${escapeHtml(String(displayNo))}</td>`;
  }
  if (!column.editable) {
    return `<td>${escapeHtml(value || "-")}</td>`;
  }
  if (isEditing) {
    return editingCellMarkup;
  }
  return `
    <td class="tracker-board-cell${isOverridden ? " is-overridden" : ""}">
      <button
        class="tracker-board-edit-trigger"
        type="button"
        data-board-edit-trigger="true"
        data-board-edit-entry-id="${escapeHtml(entry.id)}"
        data-board-edit-field="${escapeHtml(column.key)}"
      >
        <span class="tracker-board-cell-value">${escapeHtml(value || "-")}</span>
        <span class="tracker-board-cell-meta mono">${isOverridden ? "override" : "클릭해 수정"}</span>
      </button>
    </td>
  `;
}

function buildTrackerBoardEditingCellMarkup(payload = {}, helpers = {}) {
  const {
    entryId = "",
    fieldName = "",
    label = "",
    value = "",
    saving = false,
    errorMessage = "",
    textarea = false,
    rows = 3,
  } = payload;
  const { escapeHtml = (raw) => String(raw ?? "") } = helpers;
  const inputMarkup = textarea
    ? `<textarea
        class="tracker-board-edit-input tracker-board-edit-input-textarea"
        rows="${escapeHtml(String(rows))}"
        data-board-edit-input="true"
        data-board-edit-entry-id="${escapeHtml(entryId)}"
        data-board-edit-field="${escapeHtml(fieldName)}"
        data-board-edit-active="true"
        ${saving ? "disabled" : ""}
      >${escapeHtml(value || "")}</textarea>`
    : `<input
        class="tracker-board-edit-input"
        type="text"
        value="${escapeHtml(value || "")}"
        data-board-edit-input="true"
        data-board-edit-entry-id="${escapeHtml(entryId)}"
        data-board-edit-field="${escapeHtml(fieldName)}"
        data-board-edit-active="true"
        ${saving ? "disabled" : ""}
      />`;
  return `
    <td class="tracker-board-cell tracker-board-cell-editing">
      <form
        class="tracker-board-edit-form"
        data-board-edit-form="true"
        data-board-edit-entry-id="${escapeHtml(entryId)}"
        data-board-edit-field="${escapeHtml(fieldName)}"
      >
        <span class="tracker-board-edit-label">${escapeHtml(label)}</span>
        ${inputMarkup}
        <div class="tracker-board-edit-actions">
          <button class="primary-button tracker-board-edit-save" type="submit" ${saving ? "disabled" : ""}>저장</button>
          <button class="ghost-button tracker-board-edit-cancel" type="button" data-board-edit-cancel="true" ${saving ? "disabled" : ""}>취소</button>
        </div>
        <p class="tracker-board-edit-hint mono">${textarea ? "Enter 저장 · Shift+Enter 줄바꿈 · Esc 취소" : "Enter 저장 · Esc 취소"}</p>
        ${errorMessage ? `<p class="tracker-board-edit-error">${escapeHtml(errorMessage)}</p>` : ""}
      </form>
    </td>
  `;
}
```

- [ ] **Step 4: Rewire `frontend/app.js`**

Replace the bodies of `renderTrackerBoardCell()` and `renderTrackerBoardEditingCell()` with runtime helper calls:

```javascript
function renderTrackerBoardCell({ entry, column, displayNo }) {
  const value = entry[column.key] || "";
  const isEditing = state.trackerBoardEdit.entryId === entry.id && state.trackerBoardEdit.fieldName === column.key;
  const isOverridden = entry.overridden_fields.includes(column.key);
  return TRACKER_BOARD_RUNTIME?.buildTrackerBoardCellMarkup?.(
    {
      entry,
      column,
      displayNo,
      value,
      isEditing,
      isOverridden,
      editingCellMarkup: isEditing
        ? renderTrackerBoardEditingCell({
          entry,
          fieldName: column.key,
          label: column.label,
          value: state.trackerBoardEdit.draftValue,
          saving: state.trackerBoardEdit.saving,
          errorMessage: state.trackerBoardEdit.errorMessage,
        })
        : "",
    },
    { escapeHtml },
  ) || `<td>${escapeHtml(value || "-")}</td>`;
}

function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {
  const textarea = TRACKER_BOARD_TEXTAREA_FIELDS.has(fieldName);
  return TRACKER_BOARD_RUNTIME?.buildTrackerBoardEditingCellMarkup?.(
    {
      entryId: entry.id,
      fieldName,
      label,
      value,
      saving,
      errorMessage,
      textarea,
      rows: fieldName === "progress_note" ? 4 : 3,
    },
    { escapeHtml },
  ) || "";
}
```

Keep unchanged:

- `renderTrackerBoard()` table shell
- `toggleTrackerBoardBlankPriority()`
- all row/edit/save/cancel/input event binding
- `beginTrackerBoardEdit()` and `resetTrackerBoardEdit()`

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `node --test frontend/tests/tracker-board-runtime.test.js`

Expected: PASS

- [ ] **Step 6: Run syntax verification**

Run: `node --check frontend/tracker-board-runtime.js frontend/app.js`

Expected: exit code 0 and no output

- [ ] **Step 7: Commit**

```bash
git add frontend/tracker-board-runtime.js frontend/app.js frontend/tests/tracker-board-runtime.test.js
git commit -m "refactor: extract tracker board cell helpers"
```

## Self-Review

- Spec coverage: 셀 마크업 분리, 편집 셀 마크업 분리, selector contract 유지, 테스트 추가 모두 포함했다.
- Placeholder scan: `TODO`, `TBD`, 추상 표현 없이 helper 이름, 테스트 코드, 명령을 모두 적었다.
- Type consistency: helper 이름은 `buildTrackerBoardCellMarkup`와 `buildTrackerBoardEditingCellMarkup`으로 plan 전반에서 일관되게 사용했다.
