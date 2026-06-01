# Main Modularization Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `home bootstrap + sales overview cache/snapshot` 관련 data-shape/helper 책임을 [`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js)로 더 밀어 넣고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 API 호출, state mutation, cache envelope read/write 호출, DOM render 중심으로 유지한다.

**Architecture:** 이번 차수는 `helper/data-shape 우선`으로 진행한다. 먼저 bootstrap runtime에 normalize/merge/cache/snapshot helper 계약을 테스트와 함께 고정하고, 그 다음 `app.js`에서 `applyHomeBootstrapPayload`, `persistHomeBootstrapCache`, `syncHomeBootstrapSalesCache`, `shouldUseHomeBootstrapTrackerSnapshot` 같은 경로가 runtime helper를 일관되게 쓰도록 정리한다. 마지막으로 app integration test를 추가해 state 반영과 cache payload contract를 고정한다.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser global runtime pattern (`window.SPMSBootstrapRuntime`), existing frontend shell in `frontend/app.js`

---

## File Structure

- `frontend/bootstrap-runtime.js`
  - bootstrap payload normalize/merge/cache/snapshot helper를 제공한다.
- `frontend/app.js`
  - home bootstrap / sales overview API 호출, state mutation, cache envelope read/write, render 호출을 담당한다.
- `tests/frontend/test_bootstrap_runtime.mjs`
  - bootstrap runtime helper를 node 환경에서 직접 검증한다.
- `tests/frontend/test_bootstrap_app_integration.mjs`
  - `app.js`의 bootstrap 적용/캐시 경로가 runtime helper 계약을 통해 동작하는지 behavioral integration으로 검증한다.

### Task 1: Add Bootstrap Runtime Tests

**Files:**
- Create: `tests/frontend/test_bootstrap_runtime.mjs`

- [ ] **Step 1: Write failing runtime tests**

테스트는 아래 계약을 먼저 고정해야 한다.

- `normalizeSalesOverviewPayload()`가 잘못된 payload shape를 안전한 기본값으로 정규화한다.
- `buildSalesOverviewCachePayload()`가 cache 저장 shape를 만든다.
- `mergeSalesOverviewIntoHomeBootstrapPayload()`가 기존 home bootstrap payload에 sales overview 결과를 합친다.
- `normalizeTrackerFirstPagePayload()`가 pagination/sort 기본값을 보장한다.
- `buildHomeBootstrapCachePayload()`가 `tracker_first_page`, `generated_at`, `snapshot_version`을 포함하는 cache payload를 만든다.
- `canUseHomeBootstrapTrackerSnapshot()`이 query/region/editedOnly/page 조건에 따라 snapshot 재사용 여부를 반환한다.
- `hasCachedSalesOverviewData()`와 `hasCachedHomeBootstrapData()`가 state snapshot 존재 여부를 올바르게 판단한다.
- `isMissingSalesOverviewEndpointError()`와 `isMissingHomeBootstrapEndpointError()`가 404 fallback 조건을 올바르게 판단한다.

- [ ] **Step 2: Run runtime tests to verify red state**

Run: `node --test tests/frontend/test_bootstrap_runtime.mjs`  
Expected: FAIL until missing helpers or stricter contracts are implemented.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/frontend/test_bootstrap_runtime.mjs
git commit -m "test: bootstrap runtime helper 기대값 추가"
```

### Task 2: Expand Bootstrap Runtime Helpers

**Files:**
- Modify: `frontend/bootstrap-runtime.js`
- Test: `tests/frontend/test_bootstrap_runtime.mjs`

- [ ] **Step 1: Align and expand helper contracts**

`frontend/bootstrap-runtime.js`에서 아래 helper 계약을 명확히 유지/보강한다.

```js
buildStorageIdentity(authUser)
normalizeSalesOverviewPayload(payload)
buildSalesOverviewCachePayload(payload)
mergeSalesOverviewIntoHomeBootstrapPayload(existingPayload, salesPayload)
normalizeTrackerFirstPagePayload(payload, fallbackPageSize = 20)
buildHomeBootstrapCachePayload(payload)
mergeTrackerEntriesById(previousEntries, nextEntries)
canUseHomeBootstrapTrackerSnapshot(input)
hasCachedSalesOverviewData(snapshotState)
hasCachedHomeBootstrapData(snapshotState)
isMissingSalesOverviewEndpointError(error)
isMissingHomeBootstrapEndpointError(error)
```

필요하면 pure helper를 추가해도 되지만, `state`, `dom`, `localStorage`, `api()`를 직접 다루면 안 된다.

- [ ] **Step 2: Make runtime tests pass**

Run: `node --test tests/frontend/test_bootstrap_runtime.mjs`  
Expected: PASS

- [ ] **Step 3: Commit runtime helper extraction**

```bash
git add frontend/bootstrap-runtime.js tests/frontend/test_bootstrap_runtime.mjs
git commit -m "refactor: bootstrap runtime helper 정리"
```

### Task 3: Wire Bootstrap Cache/Apply Paths Through Runtime Helpers

**Files:**
- Modify: `frontend/app.js`
- Create: `tests/frontend/test_bootstrap_app_integration.mjs`
- Test: `tests/frontend/test_bootstrap_runtime.mjs`

- [ ] **Step 1: Add app integration test for bootstrap apply/cache paths**

`tests/frontend/test_bootstrap_app_integration.mjs`는 `frontend/app.js`에서 필요한 함수만 추출해 VM에서 평가하고, runtime과 cache layer를 stub해서 아래를 검증한다.

- `applyHomeBootstrapPayload()`가 runtime의 normalized tracker page payload를 통해 state를 반영한다.
- `persistSalesOverviewCache()` / `syncHomeBootstrapSalesCache()`가 runtime helper가 만든 cache payload shape를 사용한다.
- `shouldUseHomeBootstrapTrackerSnapshot()`이 runtime predicate를 사용한다.
- 기존 state merge 규칙이 깨지지 않는다.

- [ ] **Step 2: Refactor `app.js` to use runtime helpers consistently**

정리 대상은 아래 경로다.

- `applyHomeBootstrapPayload()`
- `hydrateHomeBootstrapCache()`
- `persistSalesOverviewCache()`
- `syncHomeBootstrapSalesCache()`
- `persistHomeBootstrapCache()`
- `shouldUseHomeBootstrapTrackerSnapshot()`

원칙:

- API 호출과 `state.*` mutation은 `app.js`에 남긴다.
- normalize/fallback/merge/cache payload 계산은 runtime helper를 우선 사용한다.
- `auth.bootstrapEmail` 관련 로직은 건드리지 않는다.

- [ ] **Step 3: Run focused bootstrap tests**

Run:

```bash
node --test tests/frontend/test_bootstrap_runtime.mjs
node --test tests/frontend/test_bootstrap_app_integration.mjs
node --check frontend/bootstrap-runtime.js
node --check frontend/app.js
```

Expected: PASS

- [ ] **Step 4: Commit bootstrap app wiring**

```bash
git add frontend/app.js frontend/bootstrap-runtime.js tests/frontend/test_bootstrap_runtime.mjs tests/frontend/test_bootstrap_app_integration.mjs
git commit -m "refactor: bootstrap cache runtime 경계 정리"
```

### Task 4: Run Frontend Modularization Regression Verification

**Files:**
- Verify current frontend modularization test matrix only

- [ ] **Step 1: Run bootstrap tests**

```bash
node --test tests/frontend/test_bootstrap_runtime.mjs
node --test tests/frontend/test_bootstrap_app_integration.mjs
```

- [ ] **Step 2: Run existing modularization regression tests**

```bash
node --test tests/frontend/test_auth_session_runtime.mjs
node --test tests/frontend/test_auth_session_app_integration.mjs
node --test tests/frontend/test_organization_admin_runtime.mjs
node --test tests/frontend/test_organization_admin_app_integration.mjs
node --test tests/frontend/test_run_view_runtime.mjs
node --test tests/frontend/test_tracker_diagnostics_runtime.mjs
node --test tests/frontend/test_selected_entry_runtime.mjs
node --test tests/frontend/test_selected_entry_app_integration.mjs
node --test tests/frontend/test_tracker_entry_runtime.mjs
node --test tests/frontend/test_tracker_entry_app_integration.mjs
node --test tests/frontend/test_tracker_board_runtime.mjs
node --test tests/frontend/test_tracker_board_app_integration.mjs
```

- [ ] **Step 3: Run syntax checks and inspect worktree**

```bash
node --check frontend/app.js
node --check frontend/bootstrap-runtime.js
node --check frontend/auth-session-runtime.js
node --check frontend/run-view-runtime.js
node --check frontend/tracker-diagnostics-runtime.js
node --check frontend/selected-entry-runtime.js
node --check frontend/tracker-entry-runtime.js
node --check frontend/organization-admin-runtime.js
git status --short
```

- [ ] **Step 4: Confirm only expected changes remain**

Expected:

- bootstrap modularization files are modified/committed
- unrelated dirty files remain only in the known `related notice` paths

## Review Checklist

- [ ] `auth.bootstrapEmail` / auth bootstrap UX가 이번 차수에 섞이지 않았는가
- [ ] bootstrap helper가 pure function 경계를 지키는가
- [ ] `app.js`가 normalize/fallback/merge 계산을 직접 소유하지 않도록 줄었는가
- [ ] `applyHomeBootstrapPayload()`의 tracker entry merge 규칙이 유지되는가
- [ ] sales overview cache payload와 home bootstrap cache payload shape가 테스트로 고정됐는가
- [ ] snapshot reuse predicate가 기존 의미를 유지하는가

## Commit Strategy

이 차수는 아래 순서로 분리한다.

1. `test: bootstrap runtime helper 기대값 추가`
2. `refactor: bootstrap runtime helper 정리`
3. `refactor: bootstrap cache runtime 경계 정리`

필요하면 마지막에 test-only 보정 커밋을 허용한다. `main`으로 가져갈 때는 같은 순서를 유지한다.
