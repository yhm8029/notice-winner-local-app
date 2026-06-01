# Related Notice Read Path Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/api/projects/{project_id}/related-notices` return quickly by removing heavy artifact scans from the request path.

**Architecture:** Keep Supabase cache lookup and background precompute intact, but add an explicit switch so request handling can skip artifact fallback work. The route will use cache-only precomputed lookup and then defer to the existing non-live fallback path.

**Tech Stack:** Python, FastAPI, unittest, production log verification

---

### Task 1: Lock Down Cache-Only Precomputed Lookup

**Files:**
- Modify: `backend/services/related_notice_read_model_backend.py`
- Test: `tests/test_related_notice_read_model_backend.py`

- [ ] Add a failing test that proves precomputed lookup can skip artifact scans on request paths.
- [ ] Run the targeted test and verify it fails for the expected reason.
- [ ] Add an `allow_artifact_scan` switch to `precomputed_related_notice_items()`.
- [ ] Re-run the targeted test and verify it passes.

### Task 2: Move Project Route To Cache-Only Precomputed Reads

**Files:**
- Modify: `backend/api/app.py`
- Test: `tests/test_related_notice_helpers.py`
- Test: `tests/api/test_phase1_api.py`

- [ ] Add coverage showing the project related notice route still returns fallback data without requiring artifact fallback on the read path.
- [ ] Run the targeted tests and verify failure if behavior is not yet wired.
- [ ] Update `_precomputed_related_notice_items()` call sites in `app.py` so request handling passes `allow_artifact_scan=False`.
- [ ] Re-run targeted related notice tests and verify they pass.

### Task 3: Verify End-to-End Behavior

**Files:**
- Verify: `tests/test_related_notice_read_model_backend.py`
- Verify: `tests/test_related_notice_helpers.py`
- Verify: `tests/test_related_notice_response_backend.py`
- Verify: `tests/api/test_phase1_api.py`

- [ ] Run the focused pytest selection for related notice read-path coverage.
- [ ] Confirm branch is clean except intended changes.
- [ ] If production deploy is repeated, compare `/api/projects/.../related-notices` timing and memory again.
