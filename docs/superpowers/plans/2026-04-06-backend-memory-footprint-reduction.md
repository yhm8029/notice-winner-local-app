# Backend Memory Footprint Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce backend idle memory into the 700-900MB range and stop swap thrashing during normal console use by removing unnecessary eager imports from startup and lazy-loading rare heavy features.

**Architecture:** Keep auth/session, home bootstrap, and standard tracker browsing on stable code paths while shifting export, report, related-notice, artifact parsing, and pipeline execution helpers behind local imports. The process should only pay heavy import cost when the matching rare feature is actually called.

**Tech Stack:** Python, FastAPI, unittest, import-time profiling

---

### Task 1: Capture Startup Import Baseline In Tests Or Repro Script

**Files:**
- Create: `tests/test_app_startup_imports.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Write the failing test or assertion script**

```python
def test_backend_services_module_does_not_export_pipeline_execution_helpers():
    import backend.services as services

    assert not hasattr(services, "safely_execute_project_tracker")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: FAIL because `backend.services` still exports heavy helpers

- [ ] **Step 3: Write minimal implementation direction**

```python
# backend/services/__init__.py
# remove pipeline/export execution re-exports from package root
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_app_startup_imports.py backend/services/__init__.py
git commit -m "test: lock down backend services startup imports"
```

### Task 2: Remove Heavy Re-Exports From `backend.services`

**Files:**
- Modify: `backend/services/__init__.py`
- Modify: `backend/api/app.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Add failing coverage for concrete imports**

```python
def test_app_imports_heavy_service_helpers_from_concrete_modules():
    from backend.api import app as app_module

    assert callable(app_module.resolve_artifact_path)
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: FAIL after removing package-root exports and before fixing call sites

- [ ] **Step 3: Implement concrete module imports**

```python
from backend.services.artifact_files import resolve_artifact_path
from backend.services.run_execution import queue_tracker_export_run_for_parent
from backend.services.run_execution import safely_execute_project_tracker
from backend.services.seed_collect import synthetic_debug_enabled
```

- [ ] **Step 4: Run targeted tests**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/__init__.py backend/api/app.py tests/test_app_startup_imports.py
git commit -m "refactor: remove heavy backend services re-exports"
```

### Task 3: Lazy-Load Rare Heavy Dependencies In `app.py`

**Files:**
- Modify: `backend/api/app.py`
- Test: `tests/test_app_startup_imports.py`

- [ ] **Step 1: Add failing tests for lazy helper access points**

```python
def test_lazy_import_helper_loads_openpyxl_only_when_called():
    from backend.api import app as app_module

    workbook_cls = app_module._load_openpyxl_workbook_class()

    assert workbook_cls.__name__ == "Workbook"
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: FAIL because helper function does not exist yet

- [ ] **Step 3: Implement lazy helpers**

```python
def _load_openpyxl_workbook_class():
    from openpyxl import Workbook
    return Workbook
```

- [ ] **Step 4: Replace top-level rare imports with helper calls or local imports**

```python
Workbook = _load_openpyxl_workbook_class()
```

Use the same pattern for other rare heavy helper groups touched by this file.

- [ ] **Step 5: Run targeted tests**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/app.py tests/test_app_startup_imports.py
git commit -m "refactor: lazy load rare backend app dependencies"
```

### Task 4: Keep Hot Auth Paths Green

**Files:**
- Verify: `backend/api/auth_runtime.py`
- Verify: `tests/test_auth_runtime.py`
- Verify: `tests/test_auth_runtime_local_bootstrap.py`
- Verify: `tests/api/test_auth_admin_accounts_api.py`

- [ ] **Step 1: Run backend auth verification**

Run: `python -m unittest tests.test_auth_runtime tests.test_auth_runtime_local_bootstrap tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 2: Run startup import verification**

Run: `python -m unittest tests.test_app_startup_imports -v`
Expected: PASS

- [ ] **Step 3: Re-run import-time profiling manually**

Run: `python -X importtime -c "import backend.api.app" 2> importtime_app.log`
Expected: lower cumulative startup import footprint for heavy modules

- [ ] **Step 4: Review top importtime entries**

Run: `Get-Content importtime_app.log | Select-Object -Last 120`
Expected: reduced `backend.services` and document parsing startup chain

- [ ] **Step 5: Commit if any verification-driven cleanup is needed**

```bash
git add backend/api/app.py backend/services/__init__.py tests/test_app_startup_imports.py importtime_app.log
git commit -m "chore: verify backend startup memory reductions"
```

### Task 5: Verify Branch Health Before Any Deployment Decision

**Files:**
- Verify: `frontend/app.js`
- Verify: `frontend/tests/auth-session-runtime.test.js`
- Verify: `backend/api/app.py`
- Verify: `backend/services/__init__.py`

- [ ] **Step 1: Run frontend auth-session tests**

Run: `node --test frontend/tests/auth-session-runtime.test.js frontend/tests/platform-admin-account-runtime.test.js frontend/tests/org-admin-runtime.test.js`
Expected: PASS

- [ ] **Step 2: Check syntax**

Run: `node --check frontend/app.js`
Expected: no output

- [ ] **Step 3: Check branch status**

Run: `git status --short --branch`
Expected: clean or only intended changes

- [ ] **Step 4: Summarize production follow-up**

```text
- no production deploy yet
- compare import baseline and live RSS after deploy
- only move to phase B if swap remains active during normal use
```

- [ ] **Step 5: Commit final integration changes if needed**

```bash
git add backend/api/app.py backend/services/__init__.py tests/test_app_startup_imports.py
git commit -m "fix: reduce backend startup memory footprint"
```
