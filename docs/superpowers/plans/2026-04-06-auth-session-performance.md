# Auth Session Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로그인 및 보호 API 인증 경로의 반복 Supabase 조회를 줄여 로그인 타임아웃과 일반 API 지연을 완화한다.

**Architecture:** 로그인 시에는 기존처럼 프로필을 1회 조회해 signed session payload 를 구성하고, 일반 보호 API 요청에서는 payload 기반 auth context 를 우선 사용한다. 다만 권한 회수 반영을 위해 `profile_checked_at` TTL 이 지난 경우에만 재검증한다. 프론트는 세션 재호출을 singleflight + throttle 로 줄인다.

**Tech Stack:** Python, FastAPI, requests, Node test runner

---

### Task 1: Add Backend Failing Tests For Auth Context TTL Behavior

**Files:**
- Modify: `tests/test_auth_runtime.py`
- Test: `tests/test_auth_runtime.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_read_auth_context_uses_signed_payload_without_local_lookup_when_profile_check_is_fresh():
    ...

def test_read_auth_context_revalidates_local_user_when_profile_check_is_stale():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_auth_runtime -v`
Expected: FAIL in the new TTL assertions

- [ ] **Step 3: Write minimal implementation**

```python
profile_checked_at = int(payload.get("profile_checked_at") or 0)
if profile_checked_at and int(time.time()) - profile_checked_at < PROFILE_RECHECK_TTL_SECONDS:
    return AuthContext(...)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_auth_runtime -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_auth_runtime.py backend/api/auth_runtime.py
git commit -m "test: cover auth context ttl behavior"
```

### Task 2: Make Session Payload Carry Revalidation Metadata And Reduce Read Path Lookups

**Files:**
- Modify: `backend/api/auth_runtime.py`
- Test: `tests/test_auth_runtime.py`

- [ ] **Step 1: Add failing assertion for session payload metadata**

```python
def test_finalize_session_payload_sets_profile_checked_at():
    ...
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run: `python -m unittest tests.test_auth_runtime -v`
Expected: FAIL in the new payload metadata assertion

- [ ] **Step 3: Implement payload metadata and lookup reduction**

```python
payload["profile_checked_at"] = int(time.time())
local_user = _get_local_user(user_id=auth_user_id)
```

- [ ] **Step 4: Run backend auth tests**

Run: `python -m unittest tests.test_auth_runtime tests.test_auth_runtime_local_bootstrap tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/api/auth_runtime.py tests/test_auth_runtime.py
git commit -m "feat: reduce repeated auth profile lookups"
```

### Task 3: Add Frontend Session Refresh Dedupe And Throttle

**Files:**
- Modify: `frontend/app.js`
- Test: `frontend/tests/auth-session-runtime.test.js`

- [ ] **Step 1: Add failing tests for duplicate refresh suppression**

```javascript
test("refreshAuthSessionState dedupes concurrent calls", async () => {
  ...
});

test("refreshAuthSessionState skips repeated calls inside cooldown", async () => {
  ...
});
```

- [ ] **Step 2: Run frontend tests to verify they fail**

Run: `node --test frontend/tests/auth-session-runtime.test.js`
Expected: FAIL in the new dedupe/throttle assertions

- [ ] **Step 3: Implement singleflight + cooldown**

```javascript
let authRefreshPromise = null;
let lastAuthRefreshAt = 0;
```

- [ ] **Step 4: Run frontend tests to verify they pass**

Run: `node --test frontend/tests/auth-session-runtime.test.js frontend/tests/platform-admin-account-runtime.test.js frontend/tests/org-admin-runtime.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js frontend/tests/auth-session-runtime.test.js
git commit -m "feat: throttle auth session refresh requests"
```

### Task 4: Run End-To-End Verification For The Isolated Branch

**Files:**
- Verify: `backend/api/auth_runtime.py`
- Verify: `frontend/app.js`
- Verify: `tests/test_auth_runtime.py`
- Verify: `frontend/tests/auth-session-runtime.test.js`

- [ ] **Step 1: Run backend verification suite**

Run: `python -m unittest tests.test_auth_runtime tests.test_auth_runtime_local_bootstrap tests.api.test_auth_admin_accounts_api -v`
Expected: PASS

- [ ] **Step 2: Run frontend verification suite**

Run: `node --test frontend/tests/auth-session-runtime.test.js frontend/tests/platform-admin-account-runtime.test.js frontend/tests/org-admin-runtime.test.js`
Expected: PASS

- [ ] **Step 3: Check branch status**

Run: `git status --short --branch`
Expected: clean or only intended changes

- [ ] **Step 4: Summarize runtime-only next steps**

```text
- no production deploy yet
- review branch diff
- merge only after approval
```

- [ ] **Step 5: Commit final integration changes if needed**

```bash
git add backend/api/auth_runtime.py frontend/app.js tests/test_auth_runtime.py frontend/tests/auth-session-runtime.test.js
git commit -m "fix: reduce auth session performance bottlenecks"
```
