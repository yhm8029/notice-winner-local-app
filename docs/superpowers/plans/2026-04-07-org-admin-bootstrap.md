# Org Admin Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 운영자 패널 초기 진입을 단일 bootstrap API와 캐시 우선 렌더로 바꿔 카드별 지연과 timeout 체감을 줄인다.

**Architecture:** backend는 기존 개별 조회 helper를 재사용하는 bootstrap endpoint를 추가하고, frontend는 bootstrap payload를 localStorage에 캐시한 뒤 stale-while-revalidate 방식으로 즉시 렌더한다. 개별 더보기/새로고침 경로는 기존 API를 유지한다.

**Tech Stack:** FastAPI, Pydantic, vanilla JS runtime modules, node:test, pytest

---

### Task 1: Backend Bootstrap Endpoint

**Files:**
- Modify: `backend/api/schemas.py`
- Modify: `backend/api/app.py`
- Test: `tests/api/test_phase1_api.py`

- [ ] Add failing API tests for admin bootstrap auth and response shape
- [ ] Run the focused pytest selection and confirm the new tests fail for missing endpoint
- [ ] Add the minimal response models and route
- [ ] Re-run the focused pytest selection and confirm green

### Task 2: Frontend Bootstrap Cache Loader

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/console-data-runtime.js`
- Test: `frontend/tests/console-data-runtime.test.js`

- [ ] Add failing node tests for cached bootstrap hydration and single bootstrap fetch
- [ ] Run the focused node tests and confirm failure
- [ ] Implement bootstrap cache helpers and loader wiring
- [ ] Re-run the focused node tests and confirm green

### Task 3: Integration Verification

**Files:**
- Modify: `frontend/console-data-runtime.js`
- Test: `frontend/tests/org-admin-runtime.test.js`
- Test: `frontend/tests/platform-admin-account-runtime.test.js`
- Test: `frontend/tests/tracker-change-runtime.test.js`

- [ ] Run existing frontend regression tests
- [ ] Run backend regression tests around invitation/admin routes
- [ ] If all green, summarize changed behavior and remaining risks
