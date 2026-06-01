# Main Modularization Tracker Entry List Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `tracker entry list/detail 카드 렌더`의 표시 계산을 [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 로 분리하고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 상태 결정과 이벤트 바인딩만 담당하게 만든다.

**Architecture:** `tracker entry list` 는 `view-model + markup` 분리를 적용한다. runtime 은 empty state, entry card view-model, entry card markup, entry list markup 을 순수 함수로 제공하고, `app.js` 는 `displayEntries` 결정, selected state 갱신, related notice/sales claim slot 생성, 클릭/입력 이벤트 바인딩, selected entry preload 를 유지한다.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser global runtime pattern (`window.SPMS*Runtime`), existing frontend shell in `frontend/app.js`

---

## File Structure

- `frontend/tracker-entry-runtime.js`
  - tracker entry summary/detail helper와 함께 list/card 표시 helper를 가진다.
- `frontend/app.js`
  - `displayEntries` 계산, list DOM 반영, event binding, selected entry/detail preload, board 연계를 유지한다.
- `tests/frontend/test_tracker_entry_runtime.mjs`
  - tracker entry runtime helper를 node 환경에서 직접 검증한다.
- `tests/frontend/test_tracker_entry_app_integration.mjs`
  - `renderTrackerEntries` 가 runtime 경로를 사용하는지 구조적으로 검증한다.

### Task 1: Add Tracker Entry Runtime Tests

**Files:**
- Create: `tests/frontend/test_tracker_entry_runtime.mjs`

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

test("buildTrackerEntriesEmptyStateView returns admin and user empty copy", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntriesEmptyStateView, "function");

  const adminView = runtime.buildTrackerEntriesEmptyStateView({
    trackerEntriesError: "",
    uiMode: "admin",
  });
  const userView = runtime.buildTrackerEntriesEmptyStateView({
    trackerEntriesError: "",
    uiMode: "user",
  });

  assert.match(adminView.html, /No tracker rows loaded/);
  assert.match(userView.html, /프로젝트/);
});

test("buildTrackerEntryCardView returns selected state, override text, and metrics", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntryCardView, "function");

  const view = runtime.buildTrackerEntryCardView(
    {
      id: "entry-1",
      project_name: "테스트 프로젝트",
      entry_key: "key-1",
      demand_org_name: "발주처",
      gross_area_scale: "1만㎡",
      construction_cost: "100억원",
      architect_office: "설계사",
      construction_start_date: "2026-05-01",
      opening_scheduled_date: "2027-01-01",
      demand_contact: "홍길동",
      site_location_1: "서울",
      building_automation_estimated_amount: "3억원",
      overridden_fields: ["project_name"],
    },
    {
      displayNo: 7,
      selectedEntryId: "entry-1",
      uiMode: "admin",
      formatOpeningScheduledDate: (value) => `open:${value}`,
      formatEstimateValue: (entry) => `estimate:${entry.building_automation_estimated_amount}`,
    }
  );

  assert.equal(view.selectedClass, " is-selected");
  assert.equal(view.displayNoText, "7");
  assert.equal(view.relatedButtonLabel.length > 0, true);
  assert.match(view.overrideMetaText, /override/);
  assert.equal(view.openingScheduledDateText, "open:2027-01-01");
  assert.equal(view.estimateValueText, "estimate:3억원");
});

test("buildTrackerEntryCardMarkup injects slot html", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntryCardMarkup, "function");

  const html = runtime.buildTrackerEntryCardMarkup(
    {
      id: "entry-1",
      project_name: "테스트 프로젝트",
      entry_key: "key-1",
      demand_org_name: "발주처",
      grossAreaScaleText: "1만㎡",
      constructionCostText: "100억원",
      estimateValueText: "3억원",
      architectOfficeText: "설계사",
      constructionStartDateText: "2026-05-01",
      openingScheduledDateText: "2027-01-01",
      demandContactText: "홍길동",
      siteLocationText: "서울",
      selectedClass: " is-selected",
      displayNoText: "2",
      relatedButtonLabel: "연관 공고 닫기",
      overrideMetaHtml: "<p>override project_name</p>",
      salesSectionHtml: "<section>sales</section>",
      relatedNoticeHtml: "<section>related</section>",
    },
    { escapeHtml: (value) => String(value) }
  );

  assert.match(html, /<section>sales<\/section>/);
  assert.match(html, /<section>related<\/section>/);
  assert.match(html, /entry-item is-selected/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_tracker_entry_runtime.mjs`
Expected: FAIL with messages like `runtime.buildTrackerEntriesEmptyStateView is not a function`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/frontend/test_tracker_entry_runtime.mjs
git commit -m "test: tracker entry runtime helper 기대값 추가"
```

### Task 2: Implement Tracker Entry Runtime Helpers

**Files:**
- Modify: `frontend/tracker-entry-runtime.js`
- Test: `tests/frontend/test_tracker_entry_runtime.mjs`

- [ ] **Step 1: Add empty-state and card view helpers**

`frontend/tracker-entry-runtime.js` 에 아래 순수 helper 를 추가한다.

```js
function buildTrackerEntriesEmptyStateView({ trackerEntriesError = "", uiMode = "admin", escapeHtml = (value) => String(value || "") } = {}) {
  if (trackerEntriesError) {
    return {
      html: `<div class="empty-state">프로젝트 현황을 불러오지 못했습니다. ${escapeHtml(trackerEntriesError)}</div>`,
    };
  }
  return {
    html: uiMode === "user"
      ? '<div class="empty-state">현재 영업 대상으로 바로 가져올 수 있는 프로젝트가 없습니다.</div>'
      : '<div class="empty-state">No tracker rows loaded.</div>',
  };
}

function buildTrackerEntryCardView(entry, options = {}) {
  const {
    displayNo = 0,
    selectedEntryId = "",
    trackerRelatedEntryId = "",
    uiMode = "admin",
    formatOpeningScheduledDate = (value) => String(value || "-"),
    formatEstimateValue = () => "-",
  } = options;

  const overriddenFields = Array.isArray(entry?.overridden_fields) ? entry.overridden_fields : [];
  return {
    id: String(entry?.id || ""),
    selectedClass: String(entry?.id || "") === String(selectedEntryId || "") ? " is-selected" : "",
    displayNoText: String(displayNo),
    projectNameText: String(entry?.project_name || ""),
    entryKeyText: String(entry?.entry_key || ""),
    demandOrgNameText: String(entry?.demand_org_name || "(수요기관 없음)"),
    grossAreaScaleText: String(entry?.gross_area_scale || "-"),
    constructionCostText: String(entry?.construction_cost || "-"),
    estimateValueText: String(formatEstimateValue(entry)),
    architectOfficeText: String(entry?.architect_office || "-"),
    constructionStartDateText: String(entry?.construction_start_date || "-"),
    openingScheduledDateText: String(formatOpeningScheduledDate(entry?.opening_scheduled_date || "")),
    demandContactText: String(entry?.demand_contact || "-"),
    siteLocationText: String(entry?.site_location_1 || "-"),
    relatedButtonLabel: String(entry?.id || "") === String(trackerRelatedEntryId || "") ? "연관 공고 닫기" : "연관 공고 열기",
    overrideMetaHtml: uiMode === "admin"
      ? `<p>${overriddenFields.length ? `override ${overriddenFields.join(", ")}` : "no overrides"}</p>`
      : "",
  };
}
```

- [ ] **Step 2: Add card and list markup builders**

```js
function buildTrackerEntryCardMarkup(view, { escapeHtml = (value) => String(value || "") } = {}) {
  return `
    <article class="entry-item${view.selectedClass}" data-entry-id="${escapeHtml(view.id)}">
      <div class="entry-shell">
        <div class="entry-no-badge" aria-label="No. ${escapeHtml(view.displayNoText)}">
          <span class="entry-no-label">No.</span>
          <strong>${escapeHtml(view.displayNoText)}</strong>
        </div>
        <div class="entry-body">
          <div class="entry-head">
            <div>
              <strong>${escapeHtml(view.projectNameText)}</strong>
              <p class="mono">${escapeHtml(view.entryKeyText)}</p>
            </div>
            <div class="entry-head-actions">
              <button class="ghost-button tracker-related-toggle" type="button" data-entry-related-toggle="${escapeHtml(view.id)}">
                ${escapeHtml(view.relatedButtonLabel)}
              </button>
              <button class="ghost-button tracker-related-toggle" type="button" data-entry-notice-view="${escapeHtml(view.id)}">
                공고문 보기
              </button>
            </div>
          </div>
          <p>${escapeHtml(view.demandOrgNameText)}</p>
          <p class="entry-metrics">
            <span><strong>연면적</strong> ${escapeHtml(view.grossAreaScaleText)}</span>
            <span><strong>공사비</strong> ${escapeHtml(view.constructionCostText)}</span>
          </p>
          <p class="entry-metrics entry-metrics-single">
            <span><strong>빌딩자동제어 추정금액(공사비 최대 3%)</strong> ${escapeHtml(view.estimateValueText)}</span>
          </p>
          <p class="entry-metrics">
            <span><strong>설계사무소</strong> ${escapeHtml(view.architectOfficeText)}</span>
            <span><strong>착공</strong> ${escapeHtml(view.constructionStartDateText)}</span>
          </p>
          <p class="entry-metrics entry-metrics-single">
            <span><strong>개찰예정일</strong> ${escapeHtml(view.openingScheduledDateText)}</span>
          </p>
          <p class="entry-metrics">
            <span><strong>담당</strong> ${escapeHtml(view.demandContactText)}</span>
            <span><strong>현장</strong> ${escapeHtml(view.siteLocationText)}</span>
          </p>
          ${view.salesSectionHtml || ""}
          ${view.overrideMetaHtml || ""}
          ${view.relatedNoticeHtml || ""}
        </div>
      </div>
    </article>
  `;
}

function buildTrackerEntriesListMarkup(views, { escapeHtml = (value) => String(value || "") } = {}) {
  return (views || []).map((view) => buildTrackerEntryCardMarkup(view, { escapeHtml })).join("");
}
```

- [ ] **Step 3: Re-run the runtime tests**

Run: `node --test tests/frontend/test_tracker_entry_runtime.mjs`
Expected: PASS

- [ ] **Step 4: Run syntax check for the runtime**

Run: `node --check frontend/tracker-entry-runtime.js`
Expected: exit `0`

- [ ] **Step 5: Commit the runtime helper implementation**

```bash
git add frontend/tracker-entry-runtime.js tests/frontend/test_tracker_entry_runtime.mjs
git commit -m "refactor: tracker entry runtime helper 추가"
```

### Task 3: Wire `renderTrackerEntries` to the Runtime

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/tracker-entry-runtime.js`
- Create: `tests/frontend/test_tracker_entry_app_integration.mjs`

- [ ] **Step 1: Add an integration guard test**

Create `tests/frontend/test_tracker_entry_app_integration.mjs` that checks the active `renderTrackerEntries()` block uses runtime helper calls instead of inline `.map(...` card markup composition.

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

test("renderTrackerEntries uses tracker-entry runtime helpers", () => {
  const source = readAppSource();
  const start = source.indexOf("function renderTrackerEntries");
  const end = source.indexOf("function renderTrackerBoard", start);
  const block = source.slice(start, end);

  assert.match(block, /buildTrackerEntryCardView/);
  assert.match(block, /buildTrackerEntriesListMarkup/);
  assert.doesNotMatch(block, /dom\\.trackerEntriesList\\.innerHTML\\s*=\\s*displayEntries\\s*\\.map/);
});
```

- [ ] **Step 2: Run the integration test to verify it fails**

Run: `node --test tests/frontend/test_tracker_entry_app_integration.mjs`
Expected: FAIL because `renderTrackerEntries` still uses inline `.map(...).join("")`

- [ ] **Step 3: Replace inline card composition in `renderTrackerEntries`**

Move the inline card markup generation in `renderTrackerEntries` to runtime helpers while leaving event binding in `app.js`.

```js
const entryViews = displayEntries.map((entry, index) => {
  const displayNo = (state.trackerFilters.page - 1) * state.trackerFilters.pageSize + index + 1;
  return buildTrackerEntryCardView(entry, {
    displayNo,
    selectedEntryId: state.selectedEntryId,
    trackerRelatedEntryId: state.trackerRelatedEntryId,
    uiMode: state.uiMode,
    formatOpeningScheduledDate: formatKoreanDate,
    formatEstimateValue: (item) => formatBuildingAutomationEstimateValue(item, item.building_automation_estimated_amount || "-"),
    salesSectionHtml: renderSalesClaimSection(entry),
    relatedNoticeHtml: renderTrackerEntryRelatedNotices(entry),
  });
});

dom.trackerEntriesList.innerHTML = buildTrackerEntriesListMarkup(entryViews, { escapeHtml });
```

- [ ] **Step 4: Replace the empty-state branch with runtime output**

```js
const emptyView = buildTrackerEntriesEmptyStateView({
  trackerEntriesError: state.trackerEntriesError,
  uiMode: state.uiMode,
  escapeHtml,
});
dom.trackerEntriesList.innerHTML = emptyView.html;
```

- [ ] **Step 5: Keep event binding in `app.js` and confirm runtime stays pure**

Run:
- `rg -n "querySelector|addEventListener|focus\\(|select\\(" frontend/tracker-entry-runtime.js`

Expected: no matches

- [ ] **Step 6: Run focused verification**

Run:
- `node --test tests/frontend/test_tracker_entry_runtime.mjs`
- `node --test tests/frontend/test_tracker_entry_app_integration.mjs`
- `node --check frontend/app.js`
- `node --check frontend/tracker-entry-runtime.js`

Expected: all PASS / exit `0`

- [ ] **Step 7: Commit the app integration**

```bash
git add frontend/app.js frontend/tracker-entry-runtime.js tests/frontend/test_tracker_entry_app_integration.mjs tests/frontend/test_tracker_entry_runtime.mjs
git commit -m "refactor: tracker entry list runtime 경계 정리"
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

- [ ] **Step 1: Run all related frontend runtime tests**

Run:
- `node --test tests/frontend/test_run_view_runtime.mjs`
- `node --test tests/frontend/test_tracker_diagnostics_runtime.mjs`
- `node --test tests/frontend/test_selected_entry_runtime.mjs`
- `node --test tests/frontend/test_selected_entry_app_integration.mjs`
- `node --test tests/frontend/test_tracker_entry_runtime.mjs`
- `node --test tests/frontend/test_tracker_entry_app_integration.mjs`

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
git add frontend/app.js frontend/tracker-entry-runtime.js tests/frontend/test_tracker_entry_runtime.mjs tests/frontend/test_tracker_entry_app_integration.mjs
git commit -m "test: tracker entry list 모듈화 회귀 검증 정리"
```
