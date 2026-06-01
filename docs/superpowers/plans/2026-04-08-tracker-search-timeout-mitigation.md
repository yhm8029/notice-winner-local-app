# Tracker Search Timeout Mitigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce tracker search request timeouts by stopping overlapping frontend requests and cutting repeated server-side global-search normalization work.

**Architecture:** Keep the existing tracker search flow, but make it single-flight on the client and lighter on the server. The frontend will abort superseded search requests and stop auto-loading change-event data after every search, while the backend will cache normalized search text on collapsed global rows so each query avoids rebuilding large search strings.

**Tech Stack:** Vanilla JS frontend, FastAPI backend, Python unittest, Node test runner

---

### Task 1: Frontend Search Request Control

**Files:**
- Modify: `frontend/app.js`
- Create: `frontend/tests/tracker-search-runtime.test.js`

- [ ] Add failing tests for `loadTrackerEntries()` aborting superseded searches and skipping automatic change-event follow-up loads.
- [ ] Run `node --test frontend/tests/tracker-search-runtime.test.js` and confirm the new assertions fail for current behavior.
- [ ] Implement a dedicated in-flight tracker search controller in `frontend/app.js`.
- [ ] Update `loadTrackerEntries()` to abort the previous search before starting a new one and to skip automatic `tracker-change-events` refresh after each search.
- [ ] Re-run `node --test frontend/tests/tracker-search-runtime.test.js` and `node --check frontend/app.js`.

### Task 2: Backend Global Search Cache Optimization

**Files:**
- Modify: `backend/services/tracker_global_summary_backend.py`
- Modify: `tests/test_tracker_global_summary.py`

- [ ] Add failing tests that verify collapsed global rows store normalized search text once and filtered search reuses it.
- [ ] Run `python -m unittest tests.test_tracker_global_summary -v` and confirm the new assertions fail for current behavior.
- [ ] Implement `_search_text_norm` caching during collapse and update filtering to use the cached normalized text instead of rebuilding and renormalizing the search bucket every query.
- [ ] Re-run `python -m unittest tests.test_tracker_global_summary -v`.

### Task 3: Verification

**Files:**
- Modify: none

- [ ] Run `node --test frontend/tests/tracker-search-runtime.test.js frontend/tests/tracker-entry-runtime.test.js`.
- [ ] Run `python -m unittest tests.test_tracker_global_summary -v`.
- [ ] Summarize the observed behavior change and any residual risks before PR creation.
