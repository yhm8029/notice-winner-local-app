# Related Notice Search Frontend Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `frontend/app.js`에 남아 있는 큰 렌더링 블록을 현재 `*-runtime.js` 패턴으로 분리한다.

**Architecture:** `frontend/app.js`는 상태와 이벤트 wiring을 유지하고, tracker board, org admin, sales summary의 markup/view-model helper만 새 runtime 또는 기존 runtime 확장으로 이동한다. 모든 runtime은 기존과 같은 IIFE + `window.SPMS*Runtime` 패턴을 유지한다.

**Tech Stack:** Vanilla JavaScript, Node built-in `node:test`, `node --check`, existing runtime file loading in `frontend/index.html`

---

## File Structure

- Create: `frontend/tracker-board-runtime.js`
- Create: `frontend/org-admin-runtime.js`
- Create: `frontend/tests/tracker-board-runtime.test.js`
- Create: `frontend/tests/org-admin-runtime.test.js`
- Create: `frontend/tests/sales-view-runtime.test.js`
- Modify: `frontend/sales-view-runtime.js`
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`

### Task 1: Extract Tracker Board Runtime

**Files:**
- Create: `frontend/tracker-board-runtime.js`
- Create: `frontend/tests/tracker-board-runtime.test.js`
- Modify: `frontend/index.html`
- Modify: `frontend/app.js:7758-8275`

- [ ] **Step 1: Write the failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSTrackerBoardRuntime;
}

test("buildTrackerBoardHeaderCell renders active blank-priority header", () => {
  const runtime = loadRuntime("frontend/tracker-board-runtime.js");
  const html = runtime.buildTrackerBoardHeaderCell(
    { key: "demand_contact", label: "담당" },
    {
      trackerBoardBlankPriorityFields: new Set(["demand_contact"]),
      trackerBoardSort: { fieldName: "demand_contact" },
      escapeHtml: (value) => String(value),
    }
  );
  assert.match(html, /빈 값 우선/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/tracker-board-runtime.test.js`

Expected: FAIL with `ENOENT` because `frontend/tracker-board-runtime.js` does not exist

- [ ] **Step 3: Write minimal implementation**

Create `frontend/tracker-board-runtime.js`:

```javascript
(function attachSPMSTrackerBoardRuntime(globalObject) {
  function buildTrackerBoardHeaderCell(column, options = {}) {
    const {
      trackerBoardBlankPriorityFields = new Set(),
      trackerBoardSort = { fieldName: "" },
      escapeHtml = (value) => String(value ?? ""),
    } = options;
    if (!trackerBoardBlankPriorityFields.has(column.key)) {
      return `<th>${escapeHtml(column.label)}</th>`;
    }
    const active = trackerBoardSort.fieldName === column.key;
    return `
      <th class="tracker-board-head-cell">
        <button class="tracker-board-sort-trigger${active ? " is-active" : ""}" type="button" data-board-sort-field="${escapeHtml(column.key)}">
          <span>${escapeHtml(column.label)}</span>
          <span class="tracker-board-sort-meta mono">${active ? "빈 값 우선" : "클릭 시 빈 값 우선"}</span>
        </button>
      </th>
    `;
  }

  function isTrackerBoardBlankValue(value) {
    return !String(value ?? "").trim();
  }

  globalObject.SPMSTrackerBoardRuntime = {
    buildTrackerBoardHeaderCell,
    isTrackerBoardBlankValue,
  };
})(window);
```

- [ ] **Step 4: Wire `index.html` and `app.js`**

In `frontend/index.html` add:

```html
<script defer src="/app/tracker-board-runtime.js?v=20260329aa"></script>
```

In `frontend/app.js` add:

```javascript
const TRACKER_BOARD_RUNTIME = window.SPMSTrackerBoardRuntime || null;
```

Replace inline helper body:

```javascript
function renderTrackerBoardHeaderCell(column) {
  return TRACKER_BOARD_RUNTIME.buildTrackerBoardHeaderCell(column, {
    trackerBoardBlankPriorityFields: TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    trackerBoardSort: state.trackerBoardSort,
    escapeHtml,
  });
}
```

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `node --test frontend/tests/tracker-board-runtime.test.js`

Expected: PASS

- [ ] **Step 6: Run syntax verification**

Run: `node --check frontend/tracker-board-runtime.js`

Expected: exit code 0 and no output

- [ ] **Step 7: Commit**

```bash
git add frontend/tracker-board-runtime.js frontend/tests/tracker-board-runtime.test.js frontend/index.html frontend/app.js
git commit -m "refactor: extract tracker board runtime"
```

### Task 2: Extract Organization Admin Runtime

**Files:**
- Create: `frontend/org-admin-runtime.js`
- Create: `frontend/tests/org-admin-runtime.test.js`
- Modify: `frontend/index.html`
- Modify: `frontend/app.js:1233-1545`

- [ ] **Step 1: Write the failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSOrgAdminRuntime;
}

test("buildOrgPlanSummaryMarkup renders upgrade message", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrgPlanSummaryMarkup(
    { plan_label: "플랜 A", active_user_count: 1, active_user_limit: 5, pending_invite_count: 1, pending_invite_limit: 5, upgrade_required: true, upgrade_message: "업그레이드 필요" },
    { escapeHtml: (value) => String(value) }
  );
  assert.match(html, /업그레이드 필요/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/org-admin-runtime.test.js`

Expected: FAIL with `ENOENT` because `frontend/org-admin-runtime.js` does not exist

- [ ] **Step 3: Write minimal implementation**

Create `frontend/org-admin-runtime.js`:

```javascript
(function attachSPMSOrgAdminRuntime(globalObject) {
  function buildOrgPlanSummaryMarkup(planSummary, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    const inviteBlocked = Boolean(planSummary?.upgrade_required);
    return `
      <div class="org-plan-summary-card${inviteBlocked ? " is-upgrade-required" : ""}">
        <strong>${escapeHtml(planSummary?.plan_label || "-")}</strong>
        <p class="mono">가입 ${escapeHtml(String(planSummary?.active_user_count || 0))} / ${escapeHtml(String(planSummary?.active_user_limit || 0))}명</p>
        ${planSummary?.upgrade_message ? `<p class="org-plan-summary-upgrade">${escapeHtml(planSummary.upgrade_message)}</p>` : ""}
      </div>
    `;
  }

  globalObject.SPMSOrgAdminRuntime = {
    buildOrgPlanSummaryMarkup,
  };
})(window);
```

- [ ] **Step 4: Wire `index.html` and `app.js`**

In `frontend/index.html` add:

```html
<script defer src="/app/org-admin-runtime.js?v=20260329aa"></script>
```

In `frontend/app.js` add:

```javascript
const ORG_ADMIN_RUNTIME = window.SPMSOrgAdminRuntime || null;
```

Replace the plan summary HTML build with:

```javascript
dom.organizationPlanSummary.innerHTML = ORG_ADMIN_RUNTIME.buildOrgPlanSummaryMarkup(planSummary, { escapeHtml });
```

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `node --test frontend/tests/org-admin-runtime.test.js`

Expected: PASS

- [ ] **Step 6: Run syntax verification**

Run: `node --check frontend/org-admin-runtime.js`

Expected: exit code 0 and no output

- [ ] **Step 7: Commit**

```bash
git add frontend/org-admin-runtime.js frontend/tests/org-admin-runtime.test.js frontend/index.html frontend/app.js
git commit -m "refactor: extract org admin runtime"
```

### Task 3: Extend Sales View Runtime for Summary Rendering

**Files:**
- Create: `frontend/tests/sales-view-runtime.test.js`
- Modify: `frontend/sales-view-runtime.js`
- Modify: `frontend/app.js:6560-6765`

- [ ] **Step 1: Write the failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSSalesViewRuntime;
}

test("buildSalesSummaryPanelMarkup renders empty-state for admin mode", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const html = runtime.buildSalesSummaryPanelMarkup(
    { uiMode: "admin", salesSummaryLoading: false, salesClosedLoading: false, salesSummaryError: "", salesClosedError: "", salesSummaryByUser: [], salesClosedByUser: [], activeMarkup: "", closedMarkup: "" },
    { escapeHtml: (value) => String(value) }
  );
  assert.match(html, /empty-state|없습니다/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/sales-view-runtime.test.js`

Expected: FAIL with `TypeError` because `buildSalesSummaryPanelMarkup` is not exported yet

- [ ] **Step 3: Extend `frontend/sales-view-runtime.js`**

Add:

```javascript
function buildSalesSummaryPanelMarkup(viewModel = {}, helpers = {}) {
  const { escapeHtml = (value) => String(value ?? "") } = helpers;
  if (viewModel.uiMode !== "admin") {
    return '<div class="empty-state">관리자 모드에서 영업 현황 집계를 확인할 수 있습니다.</div>';
  }
  if (viewModel.salesSummaryLoading || viewModel.salesClosedLoading) {
    return '<div class="empty-state">영업 집계를 불러오는 중입니다.</div>';
  }
  if (viewModel.salesSummaryError || viewModel.salesClosedError) {
    return `<div class="empty-state">${escapeHtml(viewModel.salesSummaryError || viewModel.salesClosedError)}</div>`;
  }
  if (!(viewModel.salesSummaryByUser || []).length && !(viewModel.salesClosedByUser || []).length) {
    return '<div class="empty-state">최근 영업 집계가 없습니다.</div>';
  }
  return `${viewModel.activeMarkup || ""}${viewModel.closedMarkup || ""}`;
}
```

Expose it through `window.SPMSSalesViewRuntime`.

- [ ] **Step 4: Wire `app.js`**

Use:

```javascript
dom.salesSummaryList.innerHTML = SALES_VIEW_RUNTIME.buildSalesSummaryPanelMarkup(
  {
    uiMode: state.uiMode,
    salesSummaryLoading: state.salesSummaryLoading,
    salesClosedLoading: state.salesClosedLoading,
    salesSummaryError: state.salesSummaryError,
    salesClosedError: state.salesClosedError,
    salesSummaryByUser: state.salesSummaryByUser,
    salesClosedByUser: state.salesClosedByUser,
    activeMarkup,
    closedMarkup,
  },
  { escapeHtml }
);
```

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `node --test frontend/tests/sales-view-runtime.test.js`

Expected: PASS

- [ ] **Step 6: Run syntax verification**

Run: `node --check frontend/sales-view-runtime.js`

Expected: exit code 0 and no output

- [ ] **Step 7: Commit**

```bash
git add frontend/sales-view-runtime.js frontend/tests/sales-view-runtime.test.js frontend/app.js
git commit -m "refactor: extract sales summary runtime"
```

## Self-Review

- Spec coverage: tracker board, organization admin, sales summary rendering 모두 포함
- Placeholder scan: 미완성 표식 없음
- Type consistency: 모든 runtime은 `window.SPMS*Runtime` export 패턴 유지
