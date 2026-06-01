# App Router Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `backend/api/app.py` into focused domain router modules without changing runtime behavior, response contracts, or deployment shape.

**Architecture:** Keep one FastAPI application and one deployment entrypoint, but move route declarations into router modules by domain. Phase 1 only extracts routes and minimal supporting wiring; heavy helper cleanup remains limited to what is necessary to keep imports stable and tests green.

**Tech Stack:** Python, FastAPI, unittest, node test runner

---

### File Structure

**Files to create**
- `backend/api/routers/__init__.py`
- `backend/api/routers/auth.py`
- `backend/api/routers/admin.py`
- `backend/api/routers/artifacts.py`
- `backend/api/routers/related_notice.py`
- `backend/api/routers/tracker.py`
- `tests/test_api_router_registration.py`

**Files to modify**
- `backend/api/app.py`
- `tests/test_app_startup_imports.py`
- `tests/test_auth_runtime.py`
- `tests/api/test_auth_admin_accounts_api.py`

**Responsibility split**
- `backend/api/app.py`: FastAPI app construction, middleware, static/app shell wiring, router inclusion
- `backend/api/routers/auth.py`: auth/session/profile/invitation-adjacent endpoints
- `backend/api/routers/admin.py`: admin account/audit/admin-only endpoints
- `backend/api/routers/artifacts.py`: artifact list/detail/download/preview endpoints
- `backend/api/routers/related_notice.py`: related notice read/view/search endpoints
- `backend/api/routers/tracker.py`: tracker list/detail/update/export/bootstrap-heavy tracker endpoints
- `tests/test_api_router_registration.py`: router inclusion and route reachability smoke checks

---

### Task 1: Add Router Registration Smoke Tests

**Files:**
- Create: `tests/test_api_router_registration.py`
- Test: `tests/test_api_router_registration.py`

- [ ] **Step 1: Write the failing test**

```python
from __future__ import annotations

import unittest


class ApiRouterRegistrationTests(unittest.TestCase):
    def test_app_module_exposes_router_modules(self) -> None:
        from backend.api.routers import auth
        from backend.api.routers import admin
        from backend.api.routers import artifacts
        from backend.api.routers import related_notice
        from backend.api.routers import tracker

        self.assertEqual(auth.router.__class__.__name__, "APIRouter")
        self.assertEqual(admin.router.__class__.__name__, "APIRouter")
        self.assertEqual(artifacts.router.__class__.__name__, "APIRouter")
        self.assertEqual(related_notice.router.__class__.__name__, "APIRouter")
        self.assertEqual(tracker.router.__class__.__name__, "APIRouter")

    def test_composed_app_includes_expected_paths(self) -> None:
        from backend.api.app import app

        paths = {route.path for route in app.routes}

        self.assertIn("/api/auth/sign-in", paths)
        self.assertIn("/api/admin/accounts", paths)
        self.assertIn("/api/artifacts/{artifact_id}", paths)
        self.assertIn("/api/tracker-entry-summaries", paths)
        self.assertIn("/api/projects/{project_id}/notice-view", paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api_router_registration -v`
Expected: FAIL because `backend.api.routers` modules do not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
# backend/api/routers/__init__.py
"""API routers package."""
```

```python
# backend/api/routers/auth.py
from fastapi import APIRouter

router = APIRouter()
```

Repeat the same minimal `router = APIRouter()` module shape for:

- `backend/api/routers/admin.py`
- `backend/api/routers/artifacts.py`
- `backend/api/routers/related_notice.py`
- `backend/api/routers/tracker.py`
```

- [ ] **Step 4: Run test to verify partial progress**

Run: `python -m unittest tests.test_api_router_registration -v`
Expected: first test gets further; second test still fails because routes are not registered yet

- [ ] **Step 5: Commit**

```bash
git add backend/api/routers/__init__.py backend/api/routers/auth.py backend/api/routers/admin.py backend/api/routers/artifacts.py backend/api/routers/related_notice.py backend/api/routers/tracker.py tests/test_api_router_registration.py
git commit -m "test: add API router registration coverage"
```

### Task 2: Extract Auth Routes Into `backend/api/routers/auth.py`

**Files:**
- Modify: `backend/api/app.py`
- Modify: `backend/api/routers/auth.py`
- Test: `tests/test_api_router_registration.py`
- Test: `tests/test_auth_runtime.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api_router_registration.py`:

```python
    def test_auth_router_owns_auth_paths(self) -> None:
        from backend.api.routers import auth

        auth_paths = {route.path for route in auth.router.routes}

        self.assertIn("/api/auth/sign-in", auth_paths)
        self.assertIn("/api/auth/session", auth_paths)
        self.assertIn("/api/auth/profile", auth_paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api_router_registration -v`
Expected: FAIL because `auth.router.routes` is empty

- [ ] **Step 3: Write minimal implementation**

Move auth route decorators and handlers from `backend/api/app.py` to `backend/api/routers/auth.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.post("/api/auth/sign-in")
def sign_in(...):
    ...


@router.get("/api/auth/session")
def get_session(...):
    ...
```

In `backend/api/app.py`, include the router:

```python
from backend.api.routers.auth import router as auth_router

app.include_router(auth_router)
```

Keep the existing helper functions in `backend/api/app.py` for now; import them into the router module as needed instead of rewriting behavior.

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m unittest tests.test_api_router_registration tests.test_auth_runtime -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py backend/api/routers/auth.py tests/test_api_router_registration.py tests/test_auth_runtime.py
git commit -m "refactor: extract auth API router"
```

### Task 3: Extract Admin Routes Into `backend/api/routers/admin.py`

**Files:**
- Modify: `backend/api/app.py`
- Modify: `backend/api/routers/admin.py`
- Test: `tests/test_api_router_registration.py`
- Test: `tests/api/test_auth_admin_accounts_api.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api_router_registration.py`:

```python
    def test_admin_router_owns_admin_paths(self) -> None:
        from backend.api.routers import admin

        admin_paths = {route.path for route in admin.router.routes}

        self.assertIn("/api/admin/accounts", admin_paths)
        self.assertIn("/api/admin/accounts/{user_id}/password-reset", admin_paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api_router_registration tests.api.test_auth_admin_accounts_api -v`
Expected: FAIL because `admin.router.routes` is empty

- [ ] **Step 3: Write minimal implementation**

Move admin account and audit-oriented route handlers into `backend/api/routers/admin.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.post("/api/admin/accounts")
def create_admin_account(...):
    ...


@router.post("/api/admin/accounts/{user_id}/password-reset")
def reset_admin_account_password(...):
    ...
```

Include the router in `backend/api/app.py`:

```python
from backend.api.routers.admin import router as admin_router

app.include_router(admin_router)
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m unittest tests.test_api_router_registration tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py backend/api/routers/admin.py tests/test_api_router_registration.py tests/api/test_auth_admin_accounts_api.py
git commit -m "refactor: extract admin API router"
```

### Task 4: Extract Artifact Routes Into `backend/api/routers/artifacts.py`

**Files:**
- Modify: `backend/api/app.py`
- Modify: `backend/api/routers/artifacts.py`
- Test: `tests/test_api_router_registration.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api_router_registration.py`:

```python
    def test_artifact_router_owns_artifact_paths(self) -> None:
        from backend.api.routers import artifacts

        artifact_paths = {route.path for route in artifacts.router.routes}

        self.assertIn("/api/artifacts", artifact_paths)
        self.assertIn("/api/artifacts/{artifact_id}", artifact_paths)
        self.assertIn("/api/artifacts/{artifact_id}/preview", artifact_paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports -v`
Expected: FAIL because `artifacts.router.routes` is empty

- [ ] **Step 3: Write minimal implementation**

Move artifact list/detail/download/preview handlers into `backend/api/routers/artifacts.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/artifacts")
def list_artifacts(...):
    ...


@router.get("/api/artifacts/{artifact_id}")
def download_artifact(...):
    ...
```

Include the router in `backend/api/app.py`:

```python
from backend.api.routers.artifacts import router as artifacts_router

app.include_router(artifacts_router)
```

Keep the new lazy artifact helper loaders intact; do not reintroduce top-level heavy imports.

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py backend/api/routers/artifacts.py tests/test_api_router_registration.py tests/test_app_startup_imports.py
git commit -m "refactor: extract artifact API router"
```

### Task 5: Extract Related Notice Routes Into `backend/api/routers/related_notice.py`

**Files:**
- Modify: `backend/api/app.py`
- Modify: `backend/api/routers/related_notice.py`
- Test: `tests/test_api_router_registration.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api_router_registration.py`:

```python
    def test_related_notice_router_owns_notice_paths(self) -> None:
        from backend.api.routers import related_notice

        notice_paths = {route.path for route in related_notice.router.routes}

        self.assertIn("/api/notices/view", notice_paths)
        self.assertIn("/api/projects/{project_id}/notice-view", notice_paths)
        self.assertIn("/api/tracker-entries/{entry_id}/notice-view", notice_paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports -v`
Expected: FAIL because `related_notice.router.routes` is empty

- [ ] **Step 3: Write minimal implementation**

Move related notice read/view/search handlers into `backend/api/routers/related_notice.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/notices/view")
def get_notice_view(...):
    ...
```

Include the router in `backend/api/app.py`:

```python
from backend.api.routers.related_notice import router as related_notice_router

app.include_router(related_notice_router)
```

Preserve the lazy notice-view helper loaders already added in `backend/api/app.py`.

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py backend/api/routers/related_notice.py tests/test_api_router_registration.py tests/test_app_startup_imports.py
git commit -m "refactor: extract related notice API router"
```

### Task 6: Extract Tracker Routes Into `backend/api/routers/tracker.py`

**Files:**
- Modify: `backend/api/app.py`
- Modify: `backend/api/routers/tracker.py`
- Test: `tests/test_api_router_registration.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api_router_registration.py`:

```python
    def test_tracker_router_owns_tracker_paths(self) -> None:
        from backend.api.routers import tracker

        tracker_paths = {route.path for route in tracker.router.routes}

        self.assertIn("/api/tracker-entry-summaries", tracker_paths)
        self.assertIn("/api/tracker-entry-summaries/download", tracker_paths)
        self.assertIn("/api/tracker-entries/{entry_id}", tracker_paths)
        self.assertIn("/api/tracker-entries/missing-report/download", tracker_paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports -v`
Expected: FAIL because `tracker.router.routes` is empty

- [ ] **Step 3: Write minimal implementation**

Move tracker list/detail/update/export/template/report handlers into `backend/api/routers/tracker.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/tracker-entry-summaries")
def list_tracker_entry_summaries(...):
    ...


@router.get("/api/tracker-entries/{entry_id}")
def get_tracker_entry(...):
    ...
```

Include the router in `backend/api/app.py`:

```python
from backend.api.routers.tracker import router as tracker_router

app.include_router(tracker_router)
```

Do not rewrite tracker helpers in this task. Reuse existing helpers from the current module graph and preserve the startup lazy-loading work already completed.

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports tests.test_auth_runtime tests.test_auth_runtime_local_bootstrap tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py backend/api/routers/tracker.py tests/test_api_router_registration.py tests/test_app_startup_imports.py tests/test_auth_runtime.py tests/test_auth_runtime_local_bootstrap.py tests/api/test_auth_admin_accounts_api.py
git commit -m "refactor: extract tracker API router"
```

### Task 7: Reduce `backend/api/app.py` To Composition Root

**Files:**
- Modify: `backend/api/app.py`
- Test: `tests/test_api_router_registration.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api_router_registration.py`:

```python
    def test_app_module_keeps_shell_routes_after_router_split(self) -> None:
        from backend.api.app import app

        paths = {route.path for route in app.routes}

        self.assertIn("/", paths)
        self.assertIn("/app", paths)
        self.assertIn("/health", paths)
```

- [ ] **Step 2: Run test to verify it fails if shell routes moved incorrectly**

Run: `python -m unittest tests.test_api_router_registration -v`
Expected: PASS now; keep it as a guard before cleanup

- [ ] **Step 3: Write minimal implementation**

Trim `backend/api/app.py` so it keeps only:

```python
app = FastAPI(...)

app.add_middleware(...)
app.mount(...)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(artifacts_router)
app.include_router(related_notice_router)
app.include_router(tracker_router)


@app.get("/health")
def health_check():
    ...


@app.get("/", include_in_schema=False)
def app_index():
    ...


@app.get("/app", include_in_schema=False)
def app_shell():
    ...
```

Leave only truly app-level helpers in this file. Do not perform broad helper extraction in this task.

- [ ] **Step 4: Run tests to verify it passes**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports tests.test_auth_runtime tests.test_auth_runtime_local_bootstrap tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/app.py tests/test_api_router_registration.py tests/test_app_startup_imports.py tests/test_auth_runtime.py tests/test_auth_runtime_local_bootstrap.py tests/api/test_auth_admin_accounts_api.py
git commit -m "refactor: reduce app module to composition root"
```

### Task 8: Final Verification And Startup Regression Check

**Files:**
- Verify: `backend/api/app.py`
- Verify: `backend/api/routers/auth.py`
- Verify: `backend/api/routers/admin.py`
- Verify: `backend/api/routers/artifacts.py`
- Verify: `backend/api/routers/related_notice.py`
- Verify: `backend/api/routers/tracker.py`
- Verify: `tests/test_api_router_registration.py`

- [ ] **Step 1: Run backend verification**

Run: `python -m unittest tests.test_api_router_registration tests.test_app_startup_imports tests.test_auth_runtime tests.test_auth_runtime_local_bootstrap tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 2: Run frontend verification**

Run: `node --test frontend/tests/auth-session-runtime.test.js frontend/tests/platform-admin-account-runtime.test.js frontend/tests/org-admin-runtime.test.js`
Expected: PASS

- [ ] **Step 3: Run syntax verification**

Run: `node --check frontend/app.js`
Expected: no output

- [ ] **Step 4: Re-run startup import profiling**

Run: `python -X importtime -c "import backend.api.app" 2> importtime_app_after_router_split.log`
Expected: successful import with no regression from the current modularized-memory baseline

- [ ] **Step 5: Review app startup total**

Run: `Get-Content importtime_app_after_router_split.log | Select-Object -Last 120`
Expected: no new heavy eager import chains introduced by router modules

- [ ] **Step 6: Commit any verification-driven cleanup**

```bash
git add backend/api/app.py backend/api/routers tests/test_api_router_registration.py tests/test_app_startup_imports.py
git commit -m "chore: verify API router modularization"
```
