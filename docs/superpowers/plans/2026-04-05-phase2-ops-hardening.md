# Phase 2 Ops Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 문서상 남아 있는 1, 2, 3순위 작업 중 실제 코드 갭인 오염 run 정리, tracker org 접근 경계, 조직 운영 UI 모듈 분리를 구현한다.

**Architecture:** 백엔드는 cleanup 서비스와 access 정책 서비스로 나누고, 저장소 프로토콜에 필요한 delete 기능만 최소 추가한다. 프런트는 기존 데이터 로더를 유지하면서 조직 관리자 렌더링/이벤트만 별도 runtime으로 분리한다.

**Tech Stack:** FastAPI, plain JavaScript, Supabase REST repositories, unittest/pytest

---

### Task 1: Tracker Cleanup Backend and Repository Deletes

**Files:**
- Create: `backend/services/tracker_cleanup_backend.py`
- Modify: `backend/repositories/runs.py`
- Modify: `backend/repositories/logs.py`
- Modify: `backend/repositories/artifacts.py`
- Modify: `backend/repositories/in_memory_runs.py`
- Modify: `backend/repositories/in_memory_logs.py`
- Modify: `backend/repositories/in_memory_artifacts.py`
- Modify: `backend/repositories/supabase_runs.py`
- Modify: `backend/repositories/supabase_logs.py`
- Modify: `backend/repositories/supabase_artifacts.py`
- Test: `tests/test_tracker_cleanup_backend.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cleanup_preview_collects_parent_child_logs_and_artifacts():
    ...

def test_apply_cleanup_deletes_children_before_parent():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tracker_cleanup_backend.py -v`
Expected: FAIL because `tracker_cleanup_backend` and delete methods do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def preview_tracker_cleanup(...): ...
def apply_tracker_cleanup(...): ...
```

Add repository delete methods:

```python
def delete_run(self, run_id: UUID) -> bool: ...
def delete_logs_for_run(self, run_id: UUID) -> int: ...
def delete_artifacts_for_run(self, run_id: UUID) -> int: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tracker_cleanup_backend.py -v`
Expected: PASS

### Task 2: Tracker Cleanup API

**Files:**
- Modify: `backend/api/app.py`
- Test: `tests/api/test_tracker_cleanup_api.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cleanup_preview_requires_admin_auth(): ...
def test_cleanup_preview_returns_affected_counts(): ...
def test_cleanup_apply_executes_cleanup(): ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_tracker_cleanup_api.py -v`
Expected: FAIL because cleanup endpoints do not exist.

- [ ] **Step 3: Write minimal implementation**

Add admin-only routes:

```python
@app.get("/api/admin/tracker-cleanup/preview")
@app.post("/api/admin/tracker-cleanup/apply")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_tracker_cleanup_api.py -v`
Expected: PASS

### Task 3: Tracker Read Access Guard

**Files:**
- Create: `backend/services/tracker_access_backend.py`
- Modify: `backend/api/app.py`
- Test: `tests/api/test_tracker_access_scope.py`

- [ ] **Step 1: Write the failing test**

```python
def test_tracker_entries_require_auth_context_when_phase2_auth_enabled(): ...
def test_tracker_entry_export_requires_auth_context_when_phase2_auth_enabled(): ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_tracker_access_scope.py -v`
Expected: FAIL because tracker read endpoints still bypass auth scope.

- [ ] **Step 3: Write minimal implementation**

```python
def require_tracker_read_access(request: Request) -> UUID | None: ...
```

Wire it into tracker read/export endpoints without breaking phase1 fallback when auth is disabled.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_tracker_access_scope.py -v`
Expected: PASS

### Task 4: Organization Admin UI Runtime Split

**Files:**
- Create: `frontend/organization-admin-runtime.js`
- Modify: `frontend/app.js`
- Modify: `frontend/index.html`
- Test: `tests/test_home_bootstrap_backend.py`
- Test: existing frontend smoke path via local app load

- [ ] **Step 1: Write the failing test or smoke expectation**

Document runtime contract in code and add at least one unit-level assertion for exported runtime shape if testable.

- [ ] **Step 2: Run targeted verification before refactor**

Run: `pytest tests/test_auth_runtime.py tests/api/test_sales_claim_api.py -v`
Expected: PASS baseline before JS refactor.

- [ ] **Step 3: Write minimal implementation**

Move organization admin rendering/binding helpers out of `app.js` into `organization-admin-runtime.js`, keeping `console-data-runtime.js` as the data loader.

- [ ] **Step 4: Run verification**

Run: `pytest tests/test_auth_runtime.py tests/api/test_sales_claim_api.py -v`
Run: local browser smoke on `/app/`
Expected: tests PASS and organization admin section still renders/loads.

### Task 5: Final Verification

**Files:**
- Modify as needed based on failures

- [ ] **Step 1: Run focused backend suite**

Run: `pytest tests/test_tracker_cleanup_backend.py tests/api/test_tracker_cleanup_api.py tests/api/test_tracker_access_scope.py -v`

- [ ] **Step 2: Run regression suite around auth and sales claims**

Run: `pytest tests/test_auth_runtime.py tests/api/test_sales_claim_api.py tests/test_sales_claims.py -v`

- [ ] **Step 3: Run app smoke**

Run local server and verify `/app/` loads and organization admin actions do not throw console-breaking errors.

- [ ] **Step 4: Review diff for modular boundaries**

Check that cleanup logic is not embedded directly into `app.py` and organization admin UI is not re-expanded inside `app.js`.
