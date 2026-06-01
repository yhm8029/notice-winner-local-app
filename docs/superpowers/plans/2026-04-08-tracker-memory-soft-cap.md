# Tracker Memory Soft Cap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear rebuildable tracker/search caches when the API process RSS crosses a soft memory cap, without restarting the service.

**Architecture:** Measure process RSS on the global tracker cache path, gate cache clearing behind a soft threshold and cooldown, and reuse the existing tracker cache invalidation helper so the behavior stays localized. Tests cover threshold crossing and cooldown suppression.

**Tech Stack:** Python, FastAPI, process-local cache state, unittest

---

### Task 1: Add failing tests for soft-cap clearing

**Files:**
- Modify: `tests/test_app_route_caches.py`
- Modify: `backend/api/app.py`

- [ ] **Step 1: Write a failing test**
- [ ] **Step 2: Run `python -m unittest tests.test_app_route_caches -v` and confirm the new test fails for the missing soft-cap behavior**
- [ ] **Step 3: Implement the minimal soft-cap check and cooldown**
- [ ] **Step 4: Run `python -m unittest tests.test_app_route_caches -v` and confirm green**

### Task 2: Verify tracker regressions stay green

**Files:**
- Verify: `tests/test_tracker_global_summary.py`

- [ ] **Step 1: Run `python -m unittest tests.test_tracker_global_summary -v`**
- [ ] **Step 2: Run `node --test frontend/tests/tracker-search-runtime.test.js frontend/tests/tracker-entry-runtime.test.js`**
- [ ] **Step 3: Run `node --check frontend/app.js`**
