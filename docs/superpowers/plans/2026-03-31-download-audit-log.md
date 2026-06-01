# Download Audit Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record successful spreadsheet downloads for sales/tracker list exports and expose recent history only in admin mode.

**Architecture:** Add one append-only Supabase audit table, write one row from each successful backend download response path, and expose a small admin-only read API. The frontend consumes that read API and renders a recent download panel in admin mode only.

**Tech Stack:** FastAPI, Supabase repository pattern, frontend `app.js`, existing auth/admin guards, pytest/unittest, Node test runner

---

## File Structure

- Create: `backend/repositories/download_audit_logs.py`
  - Repository protocol and row typing for audit-log persistence
- Create: `backend/repositories/in_memory_download_audit_logs.py`
  - In-memory implementation for tests
- Create: `backend/repositories/supabase_download_audit_logs.py`
  - Supabase implementation
- Modify: `backend/repositories/__init__.py`
  - Export new repository helpers
- Modify: `backend/api/schemas.py`
  - Response model for audit-log rows if needed
- Modify: `backend/api/app.py`
  - Write logs in successful download endpoints and expose admin-only read endpoint
- Create: `supabase/migrations/202603310001_download_audit_logs.sql`
  - Append-only audit table and indexes
- Modify: `frontend/app.js`
  - Admin-only panel rendering, fetch, and state hookup
- Create or modify: `tests/test_download_audit_logs_repository.py`
  - Repository behavior tests
- Modify: `tests/api/test_phase1_api.py`
  - Download logging and admin-only read endpoint tests
- Create or modify: `frontend/tests/org-admin-runtime.test.js` or `frontend/tests/auth-session-runtime.test.js`
  - UI visibility/render tests for admin-only download history panel

### Task 1: Add the Audit Log Persistence Layer

**Files:**
- Create: `backend/repositories/download_audit_logs.py`
- Create: `backend/repositories/in_memory_download_audit_logs.py`
- Create: `backend/repositories/supabase_download_audit_logs.py`
- Modify: `backend/repositories/__init__.py`
- Test: `tests/test_download_audit_logs_repository.py`

- [ ] **Step 1: Write the failing repository test**

```python
def test_in_memory_download_audit_logs_appends_and_lists_newest_first():
    repo = InMemoryDownloadAuditLogRepository()
    repo.create_log(
        organization_id=ORG_ID,
        user_id=USER_ID,
        user_email="user@example.com",
        user_role="org_admin",
        download_scope="global",
        download_format="xlsx",
        source_page="tracker_entries",
        file_name="project_status.xlsx",
    )
    rows = repo.list_logs(organization_id=ORG_ID, limit=10)
    assert len(rows) == 1
    assert rows[0]["download_scope"] == "global"
    assert rows[0]["download_format"] == "xlsx"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_download_audit_logs_repository.py -q
```

Expected: fail because repository does not exist yet.

- [ ] **Step 3: Write minimal repository interfaces and implementations**

Define:

- `DownloadAuditLogRow`
- `DownloadAuditLogRepository`
- `create_log(...)`
- `list_logs(...)`

Keep fields aligned with the spec:

- `organization_id`
- `user_id`
- `user_email`
- `user_role`
- `download_scope`
- `download_format`
- `source_page`
- `file_name`
- `created_at`

- [ ] **Step 4: Run repository test to verify it passes**

Run:

```powershell
python -m pytest tests/test_download_audit_logs_repository.py -q
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/repositories/download_audit_logs.py backend/repositories/in_memory_download_audit_logs.py backend/repositories/supabase_download_audit_logs.py backend/repositories/__init__.py tests/test_download_audit_logs_repository.py
git commit -m "feat: add download audit log repository"
```

### Task 2: Add the Supabase Migration

**Files:**
- Create: `supabase/migrations/202603310001_download_audit_logs.sql`

- [ ] **Step 1: Write the migration**

Create a table:

```sql
create table if not exists public.download_audit_logs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid null,
  user_email text not null,
  user_role text not null,
  download_scope text not null,
  download_format text not null,
  source_page text not null,
  file_name text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_download_audit_logs_org_created
  on public.download_audit_logs (organization_id, created_at desc);

create index if not exists idx_download_audit_logs_org_source_created
  on public.download_audit_logs (organization_id, source_page, created_at desc);
```

- [ ] **Step 2: Add simple constraints**

Use check constraints for:

- `download_scope in ('my', 'company', 'global')`
- `download_format in ('xlsx', 'csv')`
- `source_page in ('my_active_sales', 'company_active_sales', 'tracker_entries')`

- [ ] **Step 3: Commit**

```powershell
git add supabase/migrations/202603310001_download_audit_logs.sql
git commit -m "feat: add download audit log migration"
```

### Task 3: Log Successful Downloads in Backend Endpoints

**Files:**
- Modify: `backend/api/app.py`
- Modify: `backend/api/schemas.py`
- Test: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write failing API tests for successful download logging**

Add tests for:

- `my` sales xlsx download logs one row
- `company` sales xlsx download logs one row
- `global` tracker entries csv/xlsx download logs one row

Sketch:

```python
def test_tracker_entries_download_writes_audit_log(client, auth_headers, app_state):
    response = client.get("/api/tracker-entries/download?format=xlsx", headers=auth_headers)
    assert response.status_code == 200
    rows = app_state.download_audit_logs.list_logs(organization_id=ORG_ID, limit=10)
    assert len(rows) == 1
    assert rows[0]["source_page"] == "tracker_entries"
    assert rows[0]["download_format"] == "xlsx"
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```powershell
python -m pytest tests/api/test_phase1_api.py -q
```

Expected: fail because logging is not implemented yet.

- [ ] **Step 3: Add backend helper for writing download audit rows**

Add one small helper in `backend/api/app.py` that accepts:

- current actor/session
- scope
- format
- source page
- file name

and writes one repository row.

- [ ] **Step 4: Insert logging in successful response paths only**

Apply to:

- sales export endpoint for `my_active_sales.xlsx`
- sales export endpoint for `company_active_sales.xlsx`
- tracker entries download endpoint for csv/xlsx

Do not log validation or authorization failures.

- [ ] **Step 5: Add admin-only read endpoint**

Example shape:

```python
@app.get("/api/admin/download-audit-logs")
def list_download_audit_logs(...):
    ...
```

Requirements:

- admin only
- current organization only
- newest first
- simple `limit` query supported

- [ ] **Step 6: Add read-endpoint tests**

Add tests:

- admin can list rows
- org member cannot list rows

- [ ] **Step 7: Run API tests again**

Run:

```powershell
python -m pytest tests/api/test_phase1_api.py -q
```

Expected: pass for the new audit-log coverage.

- [ ] **Step 8: Commit**

```powershell
git add backend/api/app.py backend/api/schemas.py tests/api/test_phase1_api.py
git commit -m "feat: log successful spreadsheet downloads"
```

### Task 4: Add the Admin-Only Frontend Panel

**Files:**
- Modify: `frontend/app.js`
- Test: `frontend/tests/org-admin-runtime.test.js`

- [ ] **Step 1: Write failing frontend test for admin-only visibility**

Add a test that verifies:

- admin mode renders the download history panel
- user mode does not render it

Sketch:

```javascript
test("download audit panel is hidden outside admin mode", () => {
  const html = buildAdminPanelMarkup({ isAdmin: false, downloadAuditLogs: [] });
  assert.doesNotMatch(html, /다운로드 이력/);
});
```

- [ ] **Step 2: Run frontend test to verify it fails**

Run:

```powershell
node --test frontend/tests/org-admin-runtime.test.js
```

Expected: fail because the panel does not exist yet.

- [ ] **Step 3: Add frontend state, fetch, and render wiring**

In admin mode only:

- fetch `/api/admin/download-audit-logs`
- store recent rows
- render a small panel/table with:
  - time
  - user
  - scope
  - format
  - source page
  - file name

- [ ] **Step 4: Keep user mode hidden**

Do not render the panel or fetch the endpoint in user mode.

- [ ] **Step 5: Run frontend test and syntax check**

Run:

```powershell
node --test frontend/tests/org-admin-runtime.test.js
node --check frontend/app.js
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add frontend/app.js frontend/tests/org-admin-runtime.test.js
git commit -m "feat: show download audit logs in admin mode"
```

### Task 5: Focused Regression Verification

**Files:**
- Modify: none

- [ ] **Step 1: Run the backend-focused verification set**

Run:

```powershell
python -m pytest tests/test_download_audit_logs_repository.py tests/api/test_phase1_api.py -q
```

Expected: pass.

- [ ] **Step 2: Run the frontend-focused verification set**

Run:

```powershell
node --test frontend/tests/org-admin-runtime.test.js
node --check frontend/app.js
```

Expected: pass.

- [ ] **Step 3: Review changed files**

Run:

```powershell
git status --short
git diff -- backend/api/app.py backend/api/schemas.py backend/repositories/download_audit_logs.py backend/repositories/in_memory_download_audit_logs.py backend/repositories/supabase_download_audit_logs.py frontend/app.js tests/api/test_phase1_api.py tests/test_download_audit_logs_repository.py frontend/tests/org-admin-runtime.test.js supabase/migrations/202603310001_download_audit_logs.sql
```

Expected: only audit-log related changes.

- [ ] **Step 4: Commit any final cleanup**

```powershell
git add backend/api/app.py backend/api/schemas.py backend/repositories/download_audit_logs.py backend/repositories/in_memory_download_audit_logs.py backend/repositories/supabase_download_audit_logs.py frontend/app.js tests/api/test_phase1_api.py tests/test_download_audit_logs_repository.py frontend/tests/org-admin-runtime.test.js supabase/migrations/202603310001_download_audit_logs.sql
git commit -m "test: finalize download audit log coverage"
```
