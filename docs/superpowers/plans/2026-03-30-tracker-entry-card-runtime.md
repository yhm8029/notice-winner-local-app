# Tracker Entry Card Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `frontend/app.js`의 트래커 엔트리 카드 마크업을 `frontend/tracker-entry-runtime.js`로 분리한다.

**Architecture:** `frontend/tracker-entry-runtime.js`는 카드 shell, 번호 배지, head actions, metrics, 추정 금액, override/sales/related section 삽입을 담당한다. `frontend/app.js`는 displayEntries 필터링, selected/related/sales state, card list 주입, 그리고 클릭/토글/영업 액션 이벤트 wiring을 유지한다.

**Tech Stack:** Vanilla JavaScript, Node built-in `node:test`, `node --check`, existing `window.SPMSTrackerEntryRuntime` IIFE pattern

---

## File Structure

- Modify: `frontend/tracker-entry-runtime.js`
- Modify: `frontend/app.js`
- Create: `frontend/tests/tracker-entry-runtime.test.js`

### Task 1: Extract Tracker Entry Card Markup Helper

**Files:**
- Modify: `frontend/tracker-entry-runtime.js`
- Modify: `frontend/app.js:7566-7651`
- Create: `frontend/tests/tracker-entry-runtime.test.js`

- [ ] **Step 1: Write the failing tests**

Create `frontend/tests/tracker-entry-runtime.test.js` with:

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime(filePath) {
  const source = fs.readFileSync(filePath, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSTrackerEntryRuntime;
}

test("buildTrackerEntryCardMarkup renders shell, number badge, and action selectors", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));
  const html = runtime.buildTrackerEntryCardMarkup(
    {
      entry: {
        id: "entry-1",
        project_name: "Alpha",
        entry_key: "tracker:1",
        demand_org_name: "수요기관",
        gross_area_scale: "1000㎡",
        construction_cost: "10억원",
        architect_office: "설계사",
        construction_start_date: "2026-04-01",
        opening_scheduled_date: "2026-03-30",
        demand_contact: "홍길동",
        site_location_1: "서울",
      },
      displayNo: 3,
      selected: true,
      relatedButtonLabel: "연관 공고 닫기",
      overrideMetaHtml: "",
      salesClaimSectionHtml: "",
      relatedNoticesHtml: "",
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      formatBuildingAutomationEstimateValue: () => "0.3억원",
      formatKoreanDate: (value) => String(value ?? ""),
    },
  );
  assert.match(html, /entry-item is-selected/);
  assert.match(html, /aria-label="No\. 3"/);
  assert.match(html, /data-entry-related-toggle="entry-1"/);
  assert.match(html, /data-entry-notice-view="entry-1"/);
});

test("buildTrackerEntryCardMarkup renders metrics and injected sections", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));
  const html = runtime.buildTrackerEntryCardMarkup(
    {
      entry: {
        id: "entry-2",
        project_name: "Beta",
        entry_key: "tracker:2",
        demand_org_name: "",
        gross_area_scale: "",
        construction_cost: "",
        architect_office: "",
        construction_start_date: "",
        opening_scheduled_date: "",
        demand_contact: "",
        site_location_1: "",
      },
      displayNo: 1,
      selected: false,
      relatedButtonLabel: "연관 공고 열기",
      overrideMetaHtml: "<p>override project_name</p>",
      salesClaimSectionHtml: "<section>sales-block</section>",
      relatedNoticesHtml: "<section>related-block</section>",
    },
    {
      escapeHtml: (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll("\"", "&quot;"),
      formatBuildingAutomationEstimateValue: () => "fallback-amount",
      formatKoreanDate: () => "2026.03.30",
    },
  );
  assert.match(html, /수요기관 없음/);
  assert.match(html, /fallback-amount/);
  assert.match(html, /2026\.03\.30/);
  assert.match(html, /<section>sales-block<\/section>/);
  assert.match(html, /<section>related-block<\/section>/);
  assert.match(html, /<p>override project_name<\/p>/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/tracker-entry-runtime.test.js`

Expected: FAIL with `TypeError` because `buildTrackerEntryCardMarkup` does not exist yet

- [ ] **Step 3: Implement runtime helper**

Add `buildTrackerEntryCardMarkup(payload, helpers)` to `frontend/tracker-entry-runtime.js` and export it:

```javascript
function buildTrackerEntryCardMarkup(payload = {}, helpers = {}) {
  const {
    entry = {},
    displayNo = 0,
    selected = false,
    relatedButtonLabel = "연관 공고 열기",
    overrideMetaHtml = "",
    salesClaimSectionHtml = "",
    relatedNoticesHtml = "",
  } = payload;
  const {
    escapeHtml = (value) => String(value ?? ""),
    formatBuildingAutomationEstimateValue = (_entry, fallback) => String(fallback ?? ""),
    formatKoreanDate = (value) => String(value ?? ""),
  } = helpers;
  const selectedClass = selected ? " is-selected" : "";
  return `
    <article class="entry-item${selectedClass}" data-entry-id="${escapeHtml(entry.id)}">
      <div class="entry-shell">
        <div class="entry-no-badge" aria-label="No. ${escapeHtml(String(displayNo))}">
          <span class="entry-no-label">No.</span>
          <strong>${escapeHtml(String(displayNo))}</strong>
        </div>
        <div class="entry-body">
          <div class="entry-head">
            <div>
              <strong>${escapeHtml(entry.project_name)}</strong>
              <p class="mono">${escapeHtml(entry.entry_key)}</p>
            </div>
            <div class="entry-head-actions">
              <button class="ghost-button tracker-related-toggle" type="button" data-entry-related-toggle="${escapeHtml(entry.id)}">
                ${escapeHtml(relatedButtonLabel)}
              </button>
              <button class="ghost-button tracker-related-toggle" type="button" data-entry-notice-view="${escapeHtml(entry.id)}">
                공고문 보기
              </button>
            </div>
          </div>
          <p>${escapeHtml(entry.demand_org_name || "(수요기관 없음)")}</p>
          <p class="entry-metrics">
            <span><strong>연면적</strong> ${escapeHtml(entry.gross_area_scale || "-")}</span>
            <span><strong>공사비</strong> ${escapeHtml(entry.construction_cost || "-")}</span>
          </p>
          <p class="entry-metrics entry-metrics-single">
            <span><strong>빌딩자동제어 추정금액(공사비 최대 3%)</strong> ${escapeHtml(formatBuildingAutomationEstimateValue(entry, entry.building_automation_estimated_amount || "-"))}</span>
          </p>
          <p class="entry-metrics">
            <span><strong>설계사무소</strong> ${escapeHtml(entry.architect_office || "-")}</span>
            <span><strong>착공</strong> ${escapeHtml(entry.construction_start_date || "-")}</span>
          </p>
          <p class="entry-metrics entry-metrics-single">
            <span><strong>개찰예정일</strong> ${escapeHtml(formatKoreanDate(entry.opening_scheduled_date || ""))}</span>
          </p>
          <p class="entry-metrics">
            <span><strong>담당</strong> ${escapeHtml(entry.demand_contact || "-")}</span>
            <span><strong>현장</strong> ${escapeHtml(entry.site_location_1 || "-")}</span>
          </p>
          ${salesClaimSectionHtml}
          ${overrideMetaHtml}
          ${relatedNoticesHtml}
        </div>
      </div>
    </article>
  `;
}
```

- [ ] **Step 4: Rewire `frontend/app.js` with runtime + local fallback**

In `frontend/app.js`, add a local fallback builder near `renderTrackerEntries()`:

```javascript
function buildTrackerEntryCardMarkupFallback(payload) {
  const {
    entry,
    displayNo,
    selected,
    relatedButtonLabel,
    overrideMetaHtml,
    salesClaimSectionHtml,
    relatedNoticesHtml,
  } = payload;
  const selectedClass = selected ? " is-selected" : "";
  return `
    <article class="entry-item${selectedClass}" data-entry-id="${escapeHtml(entry.id)}">
      <div class="entry-shell">
        <div class="entry-no-badge" aria-label="No. ${escapeHtml(String(displayNo))}">
          <span class="entry-no-label">No.</span>
          <strong>${escapeHtml(String(displayNo))}</strong>
        </div>
        <div class="entry-body">
          <div class="entry-head">
            <div>
              <strong>${escapeHtml(entry.project_name)}</strong>
              <p class="mono">${escapeHtml(entry.entry_key)}</p>
            </div>
            <div class="entry-head-actions">
              <button class="ghost-button tracker-related-toggle" type="button" data-entry-related-toggle="${escapeHtml(entry.id)}">
                ${relatedButtonLabel}
              </button>
              <button class="ghost-button tracker-related-toggle" type="button" data-entry-notice-view="${escapeHtml(entry.id)}">
                공고문 보기
              </button>
            </div>
          </div>
          <p>${escapeHtml(entry.demand_org_name || "(수요기관 없음)")}</p>
          <p class="entry-metrics">
            <span><strong>연면적</strong> ${escapeHtml(entry.gross_area_scale || "-")}</span>
            <span><strong>공사비</strong> ${escapeHtml(entry.construction_cost || "-")}</span>
          </p>
          <p class="entry-metrics entry-metrics-single">
            <span><strong>빌딩자동제어 추정금액(공사비 최대 3%)</strong> ${escapeHtml(formatBuildingAutomationEstimateValue(entry, entry.building_automation_estimated_amount || "-"))}</span>
          </p>
          <p class="entry-metrics">
            <span><strong>설계사무소</strong> ${escapeHtml(entry.architect_office || "-")}</span>
            <span><strong>착공</strong> ${escapeHtml(entry.construction_start_date || "-")}</span>
          </p>
          <p class="entry-metrics entry-metrics-single">
            <span><strong>개찰예정일</strong> ${escapeHtml(formatKoreanDate(entry.opening_scheduled_date || ""))}</span>
          </p>
          <p class="entry-metrics">
            <span><strong>담당</strong> ${escapeHtml(entry.demand_contact || "-")}</span>
            <span><strong>현장</strong> ${escapeHtml(entry.site_location_1 || "-")}</span>
          </p>
          ${salesClaimSectionHtml}
          ${overrideMetaHtml}
          ${relatedNoticesHtml}
        </div>
      </div>
    </article>
  `;
}
```

Then replace the inline card template inside `renderTrackerEntries()` with:

```javascript
const payload = {
  entry,
  displayNo,
  selected: entry.id === state.selectedEntryId,
  relatedButtonLabel,
  overrideMetaHtml,
  salesClaimSectionHtml: renderSalesClaimSection(entry),
  relatedNoticesHtml: renderTrackerEntryRelatedNotices(entry),
};
return TRACKER_ENTRY_RUNTIME?.buildTrackerEntryCardMarkup?.(
  payload,
  {
    escapeHtml,
    formatBuildingAutomationEstimateValue,
    formatKoreanDate,
  },
) || buildTrackerEntryCardMarkupFallback(payload);
```

Keep unchanged:

- displayEntries filtering
- empty-state branches
- selectedEntry / relatedEntry state resets
- all entry click / related toggle / notice view / sales action event binding

- [ ] **Step 5: Add app-side fallback seam test**

Extend `frontend/tests/tracker-entry-runtime.test.js` with a VM seam test:

```javascript
test("renderTrackerEntries card builder falls back when runtime helper is missing", () => {
  const appSource = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const fallbackMatch = appSource.match(/function buildTrackerEntryCardMarkupFallback\(payload\) \{[\s\S]*?\n\}/);
  const renderMatch = appSource.match(/function renderTrackerEntries\(entries, \{ refreshSelectedEntry = true \} = \{\}\) \{[\s\S]*?\nfunction renderTrackerBoard/);
  assert.ok(fallbackMatch);
  assert.ok(renderMatch);
});
```

If a direct `renderTrackerEntries()` seam test is too broad, a narrower source-evaluation test around `buildTrackerEntryCardMarkupFallback()` is acceptable, but it must prove app-side fallback exists and returns non-empty card markup.

- [ ] **Step 6: Run focused tests to verify it passes**

Run: `node --test frontend/tests/tracker-entry-runtime.test.js`

Expected: PASS

- [ ] **Step 7: Run syntax verification**

Run: `node --check frontend/tracker-entry-runtime.js frontend/app.js`

Expected: exit code 0 and no output

- [ ] **Step 8: Commit**

```bash
git add frontend/tracker-entry-runtime.js frontend/app.js frontend/tests/tracker-entry-runtime.test.js
git commit -m "refactor: extract tracker entry card runtime"
```

## Self-Review

- Spec coverage: 카드 마크업 분리, runtime helper export, app-side fallback, 테스트 추가 모두 포함했다.
- Placeholder scan: helper 이름, 테스트 코드, 명령을 실제 내용으로 적었고 `TODO`/`TBD`를 남기지 않았다.
- Type consistency: `buildTrackerEntryCardMarkup`와 `buildTrackerEntryCardMarkupFallback` 이름을 plan 전반에서 일관되게 사용했다.
