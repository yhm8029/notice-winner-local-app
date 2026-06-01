# Main Modularization Run View Tracker Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `run view`와 `tracker diagnostics`를 기능 변경 없이 더 분리하고, 그 결과를 `main`으로 작은 단위로 머지할 수 있게 만든다.

**Architecture:** `frontend/app.js`는 상태, API 호출, runtime 호출 지점만 유지하고, 순수 렌더링과 view model 계산은 `run-view-runtime.js`와 `tracker-diagnostics-runtime.js`로 이동한다. 통합 변경은 마지막 태스크에서 `index.html`, `vercel.json`, node 기반 runtime 테스트로 묶어 검증한다.

**Tech Stack:** Vanilla JavaScript, FastAPI-backed frontend shell, Node test runner, existing runtime pattern in `frontend/*.js`

---

## File Structure

- `frontend/app.js`
  - 상태, DOM 참조, API 호출, runtime 호출, 이벤트 bind orchestration만 남긴다.
- `frontend/run-view-runtime.js`
  - run list/detail용 순수 렌더링 helper와 view model helper를 모은다.
- `frontend/tracker-diagnostics-runtime.js`
  - diagnostics 패널, summary, cleanup preview, backfill conflict view helper를 모은다.
- `frontend/index.html`
  - runtime 스크립트 로딩 순서와 버전 query를 맞춘다.
- `frontend/vercel.json`
  - `run-view-runtime.js`, `tracker-diagnostics-runtime.js` 경로가 브랜치 배포와 main 머지 후에도 깨지지 않게 유지한다.
- `tests/frontend/test_run_view_runtime.mjs`
  - 새 run view runtime 회귀 테스트를 만든다.
- `tests/frontend/test_tracker_diagnostics_runtime.mjs`
  - diagnostics runtime 보강 테스트를 유지/확장한다.

### Task 1: Run View Runtime Boundary

**Files:**
- Create: `tests/frontend/test_run_view_runtime.mjs`
- Modify: `frontend/run-view-runtime.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: Write the failing test**

```js
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/run-view-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSRunViewRuntime;
}

test("buildRunDetailViewModel returns stable display values", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildRunDetailViewModel, "function");

  const view = runtime.buildRunDetailViewModel(
    {
      id: "run-1",
      status: "success",
      run_type: "tracker_export",
      progress_current: 2,
      progress_total: 4,
      progress_stage: "finalize",
      created_at: "2026-04-06T00:00:00Z",
      started_at: null,
      finished_at: null,
      parent_run_id: "parent-1",
      params: "{a:1}",
      summary: "{b:2}",
      error: "",
    },
    {
      runTypeLabel: (value) => `type:${value}`,
      formatDate: (value) => String(value ?? "-"),
      progressPercent: () => 50,
    }
  );

  assert.equal(view.runTypeLabel, "type:tracker_export");
  assert.equal(view.progressText, "2 / 4");
  assert.equal(view.parentRunId, "parent-1");
  assert.equal(view.progressPercent, 50);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_run_view_runtime.mjs`
Expected: FAIL with `runtime.buildRunDetailViewModel is not a function`

- [ ] **Step 3: Write minimal implementation**

`frontend/run-view-runtime.js`에 순수 helper를 추가한다.

```js
function buildRunDetailViewModel(run, helpers = {}) {
  const {
    runTypeLabel = (value) => String(value || ""),
    formatDate = (value) => String(value || "-"),
    progressPercent = () => 0,
  } = helpers;

  if (!run) {
    return null;
  }

  return {
    id: String(run.id || ""),
    status: String(run.status || ""),
    runTypeLabel: runTypeLabel(run.run_type),
    progressText: `${Number(run.progress_current || 0)} / ${Number(run.progress_total || 0)}`,
    progressStage: String(run.progress_stage || "waiting"),
    progressPercent: Number(progressPercent(run) || 0),
    paramsText: String(run.params || ""),
    summaryText: String(run.summary || ""),
    errorText: String(run.error || ""),
    createdAtText: formatDate(run.created_at),
    startedAtText: formatDate(run.started_at),
    finishedAtText: formatDate(run.finished_at),
    parentRunId: String(run.parent_run_id || "-"),
  };
}

global.SPMSRunViewRuntime = {
  ...global.SPMSRunViewRuntime,
  buildRunDetailViewModel,
};
```

`frontend/app.js`에서는 `renderRunDetail` 내부의 순수 표시값 계산을 runtime으로 위임한다.

```js
const view = RUN_VIEW_RUNTIME?.buildRunDetailViewModel(run, {
  runTypeLabel,
  formatDate,
  progressPercent,
});

dom.runType.textContent = view?.runTypeLabel || runTypeLabel(run.run_type);
dom.runProgressMeta.textContent = view?.progressText || `${run.progress_current} / ${run.progress_total}`;
dom.runParentId.textContent = view?.parentRunId || run.parent_run_id || "-";
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/test_run_view_runtime.mjs`
Expected: PASS

- [ ] **Step 5: Refactor run list fallback to use runtime helpers consistently**

`frontend/app.js`의 `renderRuns`, `renderRunsPagination`, `renderRunDetail`에서 fallback inline markup를 줄이고 runtime helper 우선 호출로 맞춘다.

```js
dom.runsList.innerHTML = RUN_VIEW_RUNTIME?.buildRunsListMarkup(...) || fallbackHtml;
dom.runsPageMeta.textContent = RUN_VIEW_RUNTIME?.buildRunsPageMeta(...) || fallbackText;
const detailView = RUN_VIEW_RUNTIME?.buildRunDetailViewModel(...);
```

- [ ] **Step 6: Run focused syntax checks**

Run:
- `node --check frontend/app.js`
- `node --check frontend/run-view-runtime.js`

Expected: both exit `0`

- [ ] **Step 7: Commit**

```bash
git add frontend/app.js frontend/run-view-runtime.js tests/frontend/test_run_view_runtime.mjs
git commit -m "refactor: run view runtime 경계 정리"
```

### Task 2: Tracker Diagnostics Runtime Boundary

**Files:**
- Modify: `frontend/tracker-diagnostics-runtime.js`
- Modify: `frontend/app.js`
- Modify: `tests/frontend/test_tracker_diagnostics_runtime.mjs`

- [ ] **Step 1: Write the failing test**

`tests/frontend/test_tracker_diagnostics_runtime.mjs`에 backfill conflict view helper 테스트를 추가한다.

```js
test("buildBackfillConflictsView returns scoped empty state copy", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildBackfillConflictsView, "function");

  const view = runtime.buildBackfillConflictsView(
    {
      items: [],
      loading: false,
      sourceRunId: "source-1",
    },
    {
      buildMarkup: () => "unused",
    }
  );

  assert.equal(view.mode, "empty");
  assert.match(view.html, /선택한 source run 기준 열린 충돌 항목이 없습니다/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_tracker_diagnostics_runtime.mjs`
Expected: FAIL with `runtime.buildBackfillConflictsView is not a function`

- [ ] **Step 3: Write minimal implementation**

`frontend/tracker-diagnostics-runtime.js`에 순수 view builder를 추가한다.

```js
function buildBackfillConflictsView(options = {}, helpers = {}) {
  const {
    items = [],
    loading = false,
    sourceRunId = "",
  } = options;
  const {
    buildMarkup = () => "",
  } = helpers;

  if (loading && !items.length) {
    return { mode: "loading", html: "검토 필요 항목을 불러오는 중입니다." };
  }
  if (!items.length) {
    return {
      mode: "empty",
      html: sourceRunId ? "선택한 source run 기준 열린 충돌 항목이 없습니다." : "열린 충돌 항목이 없습니다.",
    };
  }
  return { mode: "ready", html: buildMarkup(items) };
}

global.SPMSTrackerDiagnosticsRuntime = {
  ...global.SPMSTrackerDiagnosticsRuntime,
  buildBackfillConflictsView,
};
```

- [ ] **Step 4: Wire `app.js` to the new helper**

`renderBackfillConflictsPanel`에서 상태 판단을 runtime helper로 위임한다.

```js
const scope = getTrackerDiagnosticsScope();
const view = requireTrackerDiagnosticsRuntime().buildBackfillConflictsView(
  {
    items: state.backfillConflicts,
    loading: state.backfillConflictsLoading,
    sourceRunId: scope?.sourceRunId || "",
  },
  {
    buildMarkup: buildBackfillConflictsMarkup,
  }
);

dom.backfillConflictList.classList.toggle("empty-state", view.mode !== "ready");
dom.backfillConflictList.innerHTML = view.html;
if (view.mode === "ready") {
  bindBackfillConflictActions(dom.backfillConflictList);
}
```

- [ ] **Step 5: Keep diagnostics scope and API logic in `app.js`**

`loadTrackerContactResolutionSummary`, `loadTrackerCleanupPreview`, `loadBackfillConflicts`는 그대로 `app.js`에 둔다. runtime으로 옮기는 것은 렌더링/view helper뿐이다.

```js
// keep in app.js
const scope = getTrackerDiagnosticsScope();
const response = await api(`/api/backfill-conflicts?${query.toString()}`);
```

- [ ] **Step 6: Run runtime tests and syntax checks**

Run:
- `node --test tests/frontend/test_tracker_diagnostics_runtime.mjs`
- `node --check frontend/tracker-diagnostics-runtime.js`
- `node --check frontend/app.js`

Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add frontend/app.js frontend/tracker-diagnostics-runtime.js tests/frontend/test_tracker_diagnostics_runtime.mjs
git commit -m "refactor: tracker diagnostics runtime 경계 정리"
```

### Task 3: Integration and Main Merge Prep

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/vercel.json`
- Modify: `docs/superpowers/specs/2026-04-06-main-modularization-run-view-tracker-diagnostics-design.md`
- Modify: `README.md` (only if runtime loading contract needs a short note)

- [ ] **Step 1: Write the failing smoke expectation as a checklist comment in plan execution notes**

Use this expected loading order as the contract:

```html
<script defer src="/app/tracker-diagnostics-runtime.js?..."></script>
<script defer src="/app/run-view-runtime.js?..."></script>
<script defer src="/app/app.js?..."></script>
```

The failure condition is: `app.js` executes before either runtime is available.

- [ ] **Step 2: Normalize runtime script order**

`frontend/index.html`에서 runtime script가 `app.js`보다 먼저 오도록 유지하고, 이번 태스크에서 추가된 `run-view`/`tracker-diagnostics` 경계를 기준으로 주석 없이 명확한 순서를 맞춘다.

```html
<script defer src="/app/tracker-diagnostics-runtime.js?v=..."></script>
<script defer src="/app/run-view-runtime.js?v=..."></script>
<script defer src="/app/app.js?v=..."></script>
```

- [ ] **Step 3: Verify Vercel rewrites**

`frontend/vercel.json`에서 runtime 파일이 모두 `/app/<runtime>.js -> /<runtime>.js`로 매핑되는지 확인하고 누락이 있으면 추가한다.

```json
{
  "source": "/app/run-view-runtime.js",
  "destination": "/run-view-runtime.js"
}
```

- [ ] **Step 4: Run full frontend verification**

Run:
- `node --check frontend/app.js`
- `node --check frontend/run-view-runtime.js`
- `node --check frontend/tracker-diagnostics-runtime.js`
- `node --test tests/frontend/test_run_view_runtime.mjs`
- `node --test tests/frontend/test_tracker_diagnostics_runtime.mjs`

Expected: all pass

- [ ] **Step 5: Record main merge order in the spec**

`docs/superpowers/specs/2026-04-06-main-modularization-run-view-tracker-diagnostics-design.md`에 실제 구현 후 기준 main merge 순서를 다시 적는다.

```md
- main merge 1: run view runtime refactor only
- main merge 2: tracker diagnostics runtime refactor only
- main merge 3: script/rewrite/test integration only
```

- [ ] **Step 6: Commit**

```bash
git add frontend/index.html frontend/vercel.json tests/frontend/test_run_view_runtime.mjs tests/frontend/test_tracker_diagnostics_runtime.mjs docs/superpowers/specs/2026-04-06-main-modularization-run-view-tracker-diagnostics-design.md
git commit -m "chore: main 머지용 프런트 모듈화 통합 정리"
```

## Self-Review

- Spec coverage
  - `run view` 모듈화: Task 1에서 다룸
  - `tracker diagnostics` 모듈화: Task 2에서 다룸
  - `main` 순차 머지 준비: Task 3에서 다룸
- Placeholder scan
  - `TODO`, `TBD`, `적절히` 같은 표현 없음
- Type consistency
  - 새 helper 이름은 `buildRunDetailViewModel`, `buildBackfillConflictsView`로 고정
  - `app.js`에서는 기존 runtime accessor `RUN_VIEW_RUNTIME`, `requireTrackerDiagnosticsRuntime()`를 그대로 사용
