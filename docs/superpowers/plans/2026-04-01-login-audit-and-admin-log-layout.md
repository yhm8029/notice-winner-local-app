# Login Audit And Admin Log Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record successful logins in a dedicated audit table, show a new admin-only login history card, and constrain all admin log cards to 5 items with "더 보기" pagination in a `2 x 3` grid.

**Architecture:** Add a new `login_audit_logs` repository path that writes best-effort rows on successful sign-in and exposes a small admin read API. Extend the admin console state to load login logs and maintain per-card visible counts, then render three log cards with shared "더 보기" behavior in a fixed `2 x 3` layout.

**Tech Stack:** FastAPI backend, repository abstraction with in-memory and Supabase implementations, vanilla JS runtime modules, Supabase SQL migration, pytest, Node test runner.

---

## File Structure

### Backend

- Create: `backend/repositories/login_audit_logs.py`
  - Shared repository interface and record helpers for login audit rows.
- Create: `backend/repositories/in_memory_login_audit_logs.py`
  - Test/in-memory implementation for local and pytest flows.
- Create: `backend/repositories/supabase_login_audit_logs.py`
  - Supabase insert/list implementation.
- Modify: `backend/repositories/factory.py`
  - Wire the new repository into repo creation.
- Modify: `backend/api/schemas.py`
  - Add response models for login audit items/list response.
- Modify: `backend/api/auth_runtime.py`
  - Insert login audit rows after successful sign-in, best-effort only.
- Modify: `backend/api/app.py`
  - Add admin-only login audit list endpoint.
- Create: `supabase/migrations/202604010001_login_audit_logs.sql`
  - New table and indexes.

### Frontend

- Modify: `frontend/app.js`
  - Extend admin state, load login logs, manage visible item counts, attach "더 보기" handlers, add login log slot and blank slot to grid.
- Modify: `frontend/console-data-runtime.js`
  - Load login audit logs via admin API.
- Modify: `frontend/org-admin-runtime.js`
  - Render login audit card and add shared 5-item slicing plus "더 보기" buttons for audit/download/login cards.
- Modify: `frontend/styles.css`
  - Enforce `2 x 3` grid, support empty slot, and keep long log text/card content within bounds.

### Tests

- Create: `tests/test_login_audit_logs_repository.py`
  - Repository insert/list behavior.
- Modify: `tests/test_auth_runtime.py`
  - Successful login writes login audit row, failures do not.
- Modify: `tests/api/test_phase1_api.py`
  - Admin login audit API and limit behavior.
- Modify: `frontend/tests/org-admin-runtime.test.js`
  - Login card rendering, 5-item default limit, "더 보기" behavior.
- Modify: `frontend/tests/console-data-runtime.test.js`
  - Login audit loader behavior.

## Task 1: Add Login Audit Repository And Migration

**Files:**
- Create: `backend/repositories/login_audit_logs.py`
- Create: `backend/repositories/in_memory_login_audit_logs.py`
- Create: `backend/repositories/supabase_login_audit_logs.py`
- Modify: `backend/repositories/factory.py`
- Create: `supabase/migrations/202604010001_login_audit_logs.sql`
- Test: `tests/test_login_audit_logs_repository.py`

- [ ] **Step 1: Write the failing repository test**

```python
from backend.repositories.in_memory_login_audit_logs import InMemoryLoginAuditLogsRepository


def test_login_audit_repository_lists_latest_first():
    repo = InMemoryLoginAuditLogsRepository()
    repo.append_log(
        organization_id="org-1",
        user_id="user-1",
        user_email="user1@example.com",
        user_role="org_member",
        ip_address="127.0.0.1",
        user_agent="pytest/one",
    )
    repo.append_log(
        organization_id="org-1",
        user_id="user-2",
        user_email="user2@example.com",
        user_role="org_admin",
        ip_address="127.0.0.2",
        user_agent="pytest/two",
    )

    rows = repo.list_logs("org-1", limit=5)

    assert [row["user_email"] for row in rows] == [
        "user2@example.com",
        "user1@example.com",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_login_audit_logs_repository.py -q`

Expected: FAIL with missing module or missing repository methods.

- [ ] **Step 3: Write minimal repository implementations**

```python
# backend/repositories/login_audit_logs.py
from typing import Protocol


class LoginAuditLogsRepository(Protocol):
    def append_log(
        self,
        *,
        organization_id: str,
        user_id: str,
        user_email: str,
        user_role: str,
        ip_address: str,
        user_agent: str,
    ) -> dict: ...

    def list_logs(self, organization_id: str, limit: int = 5) -> list[dict]: ...
```

```python
# backend/repositories/in_memory_login_audit_logs.py
from datetime import datetime, timezone


class InMemoryLoginAuditLogsRepository:
    def __init__(self):
        self._rows = []

    def append_log(self, **payload):
        row = {
            "id": f"log-{len(self._rows) + 1}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        self._rows.append(row)
        return row

    def list_logs(self, organization_id, limit=5):
        rows = [row for row in self._rows if row["organization_id"] == organization_id]
        return list(reversed(rows))[:limit]
```

```sql
create table if not exists public.login_audit_logs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid references public.users(id) on delete set null,
  user_email text not null,
  user_role text not null,
  ip_address text not null default '',
  user_agent text not null default '',
  created_at timestamptz not null default now()
);

create index if not exists idx_login_audit_logs_org_created
  on public.login_audit_logs (organization_id, created_at desc);
```

- [ ] **Step 4: Run repository tests**

Run: `python -m pytest tests/test_login_audit_logs_repository.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/repositories/login_audit_logs.py backend/repositories/in_memory_login_audit_logs.py backend/repositories/supabase_login_audit_logs.py backend/repositories/factory.py supabase/migrations/202604010001_login_audit_logs.sql tests/test_login_audit_logs_repository.py
git commit -m "feat: add login audit log repository"
```

## Task 2: Record Successful Logins And Expose Admin API

**Files:**
- Modify: `backend/api/auth_runtime.py`
- Modify: `backend/api/app.py`
- Modify: `backend/api/schemas.py`
- Modify: `tests/test_auth_runtime.py`
- Modify: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write the failing auth/runtime test**

```python
def test_sign_in_writes_login_audit_row(client, login_audit_repo, seed_console_user):
    response = client.post(
        "/api/auth/sign-in",
        json={"email": "admin@example.com", "password": "password1234"},
    )

    assert response.status_code == 200
    rows = login_audit_repo.list_logs(seed_console_user["organization_id"], limit=5)
    assert rows[0]["user_email"] == "admin@example.com"
```

- [ ] **Step 2: Run auth test to verify it fails**

Run: `python -m pytest tests/test_auth_runtime.py -q -k login_audit`

Expected: FAIL because no audit row is written.

- [ ] **Step 3: Write minimal auth/runtime implementation**

```python
# backend/api/auth_runtime.py
def _append_login_audit_log(request, session_payload):
    repo = get_login_audit_logs_repository()
    if not repo:
        return
    try:
        repo.append_log(
            organization_id=str(session_payload.get("organization_id") or ""),
            user_id=str(session_payload.get("local_user_id") or ""),
            user_email=str(session_payload.get("email") or ""),
            user_role=str(session_payload.get("role") or ""),
            ip_address=str(request.client.host if request.client else ""),
            user_agent=str(request.headers.get("user-agent") or ""),
        )
    except Exception:
        logger.warning("LOGIN_AUDIT_APPEND_FAILED", exc_info=True)
```

```python
# backend/api/app.py
@app.get("/api/admin/login-audit-logs", response_model=LoginAuditLogListResponse)
def get_admin_login_audit_logs(limit: int = 5, session=Depends(require_org_admin_session)):
    repo = get_login_audit_logs_repository()
    rows = repo.list_logs(str(session.organization_id), limit=max(1, min(limit, 100)))
    return {"items": rows}
```

- [ ] **Step 4: Write the failing admin API test**

```python
def test_admin_login_audit_logs_returns_latest_rows(client, admin_headers, login_audit_repo):
    login_audit_repo.append_log(
        organization_id="org-1",
        user_id="user-1",
        user_email="member@example.com",
        user_role="org_member",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    response = client.get("/api/admin/login-audit-logs?limit=5", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["items"][0]["user_email"] == "member@example.com"
```

- [ ] **Step 5: Run backend tests**

Run: `python -m pytest tests/test_auth_runtime.py tests/api/test_phase1_api.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/api/auth_runtime.py backend/api/app.py backend/api/schemas.py tests/test_auth_runtime.py tests/api/test_phase1_api.py
git commit -m "feat: log successful sign-ins"
```

## Task 3: Add Login Audit Loader And Admin Cards Pagination

**Files:**
- Modify: `frontend/console-data-runtime.js`
- Modify: `frontend/org-admin-runtime.js`
- Modify: `frontend/app.js`
- Modify: `frontend/tests/console-data-runtime.test.js`
- Modify: `frontend/tests/org-admin-runtime.test.js`

- [ ] **Step 1: Write the failing frontend loader test**

```javascript
import test from "node:test";
import assert from "node:assert/strict";
import { loadOrganizationLoginAuditLogs } from "../console-data-runtime.js";

test("loadOrganizationLoginAuditLogs requests admin login audit logs", async () => {
  let requested = "";
  const api = async (path) => {
    requested = path;
    return { items: [] };
  };

  await loadOrganizationLoginAuditLogs({ api, limit: 5 });
  assert.equal(requested, "/api/admin/login-audit-logs?limit=5");
});
```

- [ ] **Step 2: Run loader test to verify it fails**

Run: `node --test frontend/tests/console-data-runtime.test.js`

Expected: FAIL because the loader function does not exist.

- [ ] **Step 3: Add loader and state wiring**

```javascript
// frontend/console-data-runtime.js
export async function loadOrganizationLoginAuditLogs({ api, limit = 5 }) {
  return api(`/api/admin/login-audit-logs?limit=${encodeURIComponent(limit)}`);
}
```

```javascript
// frontend/app.js
state.organizationLoginAuditLogs = [];
state.organizationLoginAuditVisibleCount = 5;

function handleOrganizationLoginAuditMore() {
  state.organizationLoginAuditVisibleCount += 5;
  return loadOrganizationLoginAuditLogs({ limit: state.organizationLoginAuditVisibleCount });
}
```

- [ ] **Step 4: Write the failing runtime rendering test**

```javascript
test("buildLoginAuditPanelMarkup shows five items and more button", () => {
  const html = buildLoginAuditPanelMarkup({
    isAdminMode: true,
    items: Array.from({ length: 6 }, (_, index) => ({
      user_email: `user${index}@example.com`,
      user_role: "org_member",
      created_at: "2026-04-01T00:00:00Z",
      ip_address: "127.0.0.1",
      user_agent: "pytest",
    })),
    visibleCount: 5,
    hasMore: true,
  });

  assert.equal((html.match(/org-admin-list-item/g) || []).length, 5);
  assert.match(html, /더 보기/);
});
```

- [ ] **Step 5: Implement three log cards with shared 5-item slicing**

```javascript
function sliceVisibleItems(items, visibleCount = 5) {
  const normalized = Array.isArray(items) ? items : [];
  return {
    visibleItems: normalized.slice(0, visibleCount),
    hasMore: normalized.length > visibleCount,
  };
}
```

```javascript
// app.js org admin grid shell
<div class="org-admin-grid">
  ...existing four cards...
  <div id="organization-login-audit-panel-slot"></div>
  <div class="org-admin-empty-slot" aria-hidden="true"></div>
</div>
```

- [ ] **Step 6: Run frontend tests**

Run: `node --test frontend/tests/org-admin-runtime.test.js frontend/tests/console-data-runtime.test.js`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/app.js frontend/console-data-runtime.js frontend/org-admin-runtime.js frontend/tests/org-admin-runtime.test.js frontend/tests/console-data-runtime.test.js
git commit -m "feat: show login audit logs in admin panel"
```

## Task 4: Final Layout And Regression Verification

**Files:**
- Modify: `frontend/styles.css`
- Test: `frontend/tests/org-admin-runtime.test.js`
- Test: `tests/api/test_phase1_api.py`
- Test: `tests/test_auth_runtime.py`
- Test: `tests/test_login_audit_logs_repository.py`

- [ ] **Step 1: Update layout styles**

```css
.org-admin-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  align-items: start;
}

.org-admin-empty-slot {
  min-height: 1px;
}
```

- [ ] **Step 2: Run backend regression suite**

Run: `python -m pytest tests/test_login_audit_logs_repository.py tests/test_auth_runtime.py tests/api/test_phase1_api.py -q`

Expected: PASS.

- [ ] **Step 3: Run frontend regression suite**

Run: `node --test frontend/tests/org-admin-runtime.test.js frontend/tests/console-data-runtime.test.js`

Expected: PASS.

- [ ] **Step 4: Run frontend syntax checks**

Run: `node --check frontend/app.js frontend/console-data-runtime.js frontend/org-admin-runtime.js frontend/styles.css`

Expected: `node --check` passes for JS files; use a CSS-aware lint substitute only if already present. If `styles.css` cannot be checked by `node --check`, omit it and verify by browser smoke after deploy.

- [ ] **Step 5: Commit**

```bash
git add frontend/styles.css
git commit -m "fix: tighten admin log card layout"
```

## Task 5: Merge-Result Validation And Deployment Preparation

**Files:**
- No code changes required
- Verify: `supabase/migrations/202604010001_login_audit_logs.sql`

- [ ] **Step 1: Verify merge-result locally**

Run: `git fetch origin && git merge --no-commit --no-ff origin/main`

Expected: no conflicts, or only resolved expected conflicts in admin audit card files.

- [ ] **Step 2: Run final command set**

Run:

```bash
python -m pytest tests/test_login_audit_logs_repository.py tests/test_auth_runtime.py tests/api/test_phase1_api.py -q
node --test frontend/tests/org-admin-runtime.test.js frontend/tests/console-data-runtime.test.js
node --check frontend/app.js frontend/console-data-runtime.js frontend/org-admin-runtime.js
```

Expected: all pass.

- [ ] **Step 3: Prepare migration handoff**

```sql
select to_regclass('public.login_audit_logs');
```

Expected before migration: `null`

Expected after migration: `public.login_audit_logs`

- [ ] **Step 4: Commit plan-complete checkpoint**

```bash
git status --short
git log --oneline -n 5
```

Expected: clean tree except intentional local artifacts such as `test-results/`.
