# Report And Missing Report UI Batch 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract report-panel rendering and tracker missing-report rendering from `frontend/app.js` into focused runtime modules without changing UI behavior.

**Architecture:** Add `frontend/report-runtime.js` for report label/status/job rendering and `frontend/tracker-missing-report-runtime.js` for missing-report summary/item/empty-state rendering. Keep `frontend/app.js` responsible for state mutation, API calls, click handlers, downloads, DOM lookup, and admin-mode gating.

**Tech Stack:** Vanilla JavaScript, browser runtime helpers on `window.*`, Node test runner

---

### File Structure

**Create:**
- `frontend/report-runtime.js`
- `frontend/tracker-missing-report-runtime.js`
- `frontend/tests/report-runtime.test.js`
- `frontend/tests/tracker-missing-report-runtime.test.js`

**Modify:**
- `frontend/app.js`

The new runtime files own deterministic markup and text shaping only. `app.js` keeps orchestration.

### Task 1: Lock Report UI Behavior With Runtime Tests

**Files:**
- Create: `frontend/tests/report-runtime.test.js`
- Create: `frontend/report-runtime.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: Write failing tests for report label, summary text, and empty/error states**

```js
test("report runtime labels known report keys and builds summary status text", () => {
  const runtime = loadReportRuntime();
  assert.equal(runtime.reportKeyLabel("phase1-equivalence"), "동등성 검증");
  assert.equal(runtime.reportKeyLabel("phase1-artifact-diff"), "산출물 비교 검증");

  const status = runtime.buildReportStatusText(
    { summary: { matched_count: 10, mismatched_count: 2, all_match: false } },
    { reportKey: "phase1-artifact-diff" },
  );
  assert.match(status, /산출물 비교 검증/);
  assert.match(status, /일치 10/);
  assert.match(status, /불일치 2/);
});
```

- [ ] **Step 2: Add failing tests for report job list/detail rendering**

```js
test("report runtime builds selected job markup with stable selectors", () => {
  const runtime = loadReportRuntime();
  const html = runtime.buildReportJobsMarkup(
    [
      { id: "job-1", report_name: "phase1-artifact-diff", status: "success", created_at: "2026-03-30T00:00:00Z" },
    ],
    { selectedReportJobId: "job-1" },
    {
      escapeHtml: (value) => String(value ?? ""),
      statusBadge: (value) => `<span>${value}</span>`,
      formatDate: (value) => `date:${value}`,
      reportKeyLabel: (value) => String(value),
    },
  );
  assert.match(html, /data-report-job-id=\"job-1\"/);
  assert.match(html, /is-selected/);
});
```

- [ ] **Step 3: Run the focused suite to verify it fails**

Run:
```powershell
node --test frontend/tests/report-runtime.test.js
```

Expected: `FAIL` because `frontend/report-runtime.js` does not exist yet.

### Task 2: Implement `report-runtime.js` And Rewire `app.js`

**Files:**
- Create: `frontend/report-runtime.js`
- Modify: `frontend/app.js`
- Test: `frontend/tests/report-runtime.test.js`

- [ ] **Step 1: Add deterministic report helpers**

```js
function reportKeyLabel(reportKey) { ... }
function buildReportStatusText(report, options = {}) { ... }
function buildReportJobsMarkup(items, options = {}, helpers = {}) { ... }
function buildReportJobStatusText(job, helpers = {}) { ... }
```

- [ ] **Step 2: Rewire `frontend/app.js` so runtime owns rendering only**

```js
function renderReport(report, errorMessage = "") {
  const runtime = requireReportRuntime();
  ...
}

function renderReportJobs(items) {
  const runtime = requireReportRuntime();
  ...
}

function renderReportJob(job, errorMessage = "") {
  const runtime = requireReportRuntime();
  ...
}
```

Keep click listener registration and `state.selectedReportJobId` updates in `app.js`.

- [ ] **Step 3: Run report runtime verification**

Run:
```powershell
node --test frontend/tests/report-runtime.test.js
node --check frontend/report-runtime.js frontend/app.js
```

Expected: `PASS`

### Task 3: Lock Missing Report UI Behavior With Runtime Tests

**Files:**
- Create: `frontend/tests/tracker-missing-report-runtime.test.js`
- Create: `frontend/tracker-missing-report-runtime.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: Write failing tests for missing-report summary chips and empty/error states**

```js
test("missing report runtime builds summary chips from report totals", () => {
  const runtime = loadMissingReportRuntime();
  const html = runtime.buildMissingReportSummaryMarkup(
    { total_entries: 10, missing_entries: 3, contact_missing: 2, architect_missing: 1, area_missing: 4 },
    { escapeHtml: (value) => String(value ?? "") },
  );
  assert.match(html, /전체 공고/);
  assert.match(html, />10</);
  assert.match(html, /누락 공고/);
});
```

- [ ] **Step 2: Add failing tests for nested missing-field list rendering**

```js
test("missing report runtime renders project items and field reasons", () => {
  const runtime = loadMissingReportRuntime();
  const html = runtime.buildMissingReportItemsMarkup(
    [
      {
        project_name: "Alpha",
        bid_no: "BID-1",
        bid_ord: "001",
        demand_org_name: "Seoul",
        updated_at: "2026-03-30T00:00:00Z",
        missing_fields: [
          { field_label: "담당 연락처", reason_group: "source_gap", reason_explainer: "없음", source_reason: "source 비어 있음" },
        ],
      },
    ],
    { escapeHtml: (value) => String(value ?? ""), formatDate: (value) => `date:${value}` },
  );
  assert.match(html, /Alpha/);
  assert.match(html, /담당 연락처/);
  assert.match(html, /source_gap/);
});
```

- [ ] **Step 3: Run the focused suite to verify it fails**

Run:
```powershell
node --test frontend/tests/tracker-missing-report-runtime.test.js
```

Expected: `FAIL` because `frontend/tracker-missing-report-runtime.js` does not exist yet.

### Task 4: Implement `tracker-missing-report-runtime.js` And Rewire `app.js`

**Files:**
- Create: `frontend/tracker-missing-report-runtime.js`
- Modify: `frontend/app.js`
- Test: `frontend/tests/tracker-missing-report-runtime.test.js`

- [ ] **Step 1: Add deterministic missing-report helpers**

```js
function buildMissingReportChipMarkup(label, count, helpers = {}) { ... }
function buildMissingReportSummaryMarkup(summary = {}, helpers = {}) { ... }
function buildMissingReportItemsMarkup(items = [], helpers = {}) { ... }
function buildMissingReportEmptyMarkup(message, helpers = {}) { ... }
```

- [ ] **Step 2: Rewire `renderTrackerMissingReport()` to use the runtime**

```js
function renderTrackerMissingReport(errorMessage = "") {
  const runtime = requireTrackerMissingReportRuntime();
  ...
}
```

Keep admin-mode gating, fetch timing, and download button behavior in `app.js`.

- [ ] **Step 3: Run missing-report runtime verification**

Run:
```powershell
node --test frontend/tests/tracker-missing-report-runtime.test.js
node --check frontend/tracker-missing-report-runtime.js frontend/app.js
```

Expected: `PASS`

### Task 5: Run Combined Frontend Verification

**Files:**
- No additional file changes required

- [ ] **Step 1: Run both new runtime suites together**

Run:
```powershell
node --test frontend/tests/report-runtime.test.js frontend/tests/tracker-missing-report-runtime.test.js
```

Expected: `PASS`

- [ ] **Step 2: Run the existing runtime suites that neighbor this area**

Run:
```powershell
node --test frontend/tests/artifact-runtime.test.js frontend/tests/tracker-board-runtime.test.js frontend/tests/tracker-entry-runtime.test.js frontend/tests/org-admin-runtime.test.js frontend/tests/sales-view-runtime.test.js frontend/tests/auth-session-runtime.test.js
```

Expected: `PASS`

- [ ] **Step 3: Run syntax verification**

Run:
```powershell
node --check frontend/report-runtime.js frontend/tracker-missing-report-runtime.js frontend/app.js
```

Expected: no output

- [ ] **Step 4: Confirm worktree state**

Run:
```powershell
git status --short
git log --oneline -8
```

Expected: clean worktree and the new batch commits on top.
