# Native Service Private Helper Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce `native_export_backend_runtime.py` and `native_gui_rules_impl.py` by moving implementation detail into private helper/runtime modules while preserving all public import surfaces and behavior.

**Architecture:** Keep `backend/services/native_export_backend.py` and `backend/services/native_gui_rules.py` unchanged. Replace the two large implementation modules with thin delegation layers that re-export the same names from new private modules in `backend/services`. Move the current logic verbatim into the new private modules so callers continue to import the same public modules and tests exercise the same behavior.

**Tech Stack:** Python 3.11, `pytest`, existing backend service modules.

---

### Task 1: Split the export runtime behind a private implementation module

**Files:**
- Create: `backend/services/_native_export_backend_runtime_impl.py`
- Modify: `backend/services/native_export_backend_runtime.py`
- Test: `tests/test_native_export_backend_runtime_helpers.py`

- [ ] **Step 1: Write the failing test**

```python
import backend.services.native_export_backend_runtime as runtime

def test_public_import_surface_still_exposes_export_runtime_symbols():
    assert hasattr(runtime, "run_post_collect_native")
    assert hasattr(runtime, "PageDocument")
    assert hasattr(runtime, "_build_post_collect_output_row")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_native_export_backend_runtime_helpers.py -v`
Expected: PASS before the refactor, then keep passing after the delegation change.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/services/native_export_backend_runtime.py
from ._native_export_backend_runtime_impl import *  # noqa: F401,F403
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_native_export_backend_runtime_helpers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/_native_export_backend_runtime_impl.py backend/services/native_export_backend_runtime.py tests/test_native_export_backend_runtime_helpers.py
git commit -m "리팩터: export runtime private 모듈 분리"
```

### Task 2: Split the GUI rules implementation behind a private implementation module

**Files:**
- Create: `backend/services/_native_gui_rules_impl.py`
- Modify: `backend/services/native_gui_rules_impl.py`
- Test: `tests/test_native_gui_rules.py`

- [ ] **Step 1: Write the failing test**

```python
import backend.services.native_gui_rules_impl as impl

def test_public_import_surface_still_exposes_gui_rule_symbols():
    assert hasattr(impl, "normalize_contact_candidate")
    assert hasattr(impl, "get_manual_field_overrides")
    assert hasattr(impl, "PHONE_FLEX_PAT")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_native_gui_rules.py -v`
Expected: PASS before the refactor, then keep passing after the delegation change.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/services/native_gui_rules_impl.py
from ._native_gui_rules_impl import *  # noqa: F401,F403
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_native_gui_rules.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/_native_gui_rules_impl.py backend/services/native_gui_rules_impl.py tests/test_native_gui_rules.py
git commit -m "리팩터: gui rules private 모듈 분리"
```

### Task 3: Verify no behavior changed

**Files:**
- Modify: none
- Test: `tests/test_native_export_backend_runtime_helpers.py`, `tests/test_native_gui_rules.py`

- [ ] **Step 1: Run the focused tests**

Run: `pytest tests/test_native_export_backend_runtime_helpers.py tests/test_native_gui_rules.py -v`
Expected: PASS

- [ ] **Step 2: Check file sizes**

Run: `wc -l backend/services/native_export_backend_runtime.py backend/services/native_gui_rules_impl.py`
Expected: Both files are materially smaller than before the split, with logic living in private helper/runtime modules.

