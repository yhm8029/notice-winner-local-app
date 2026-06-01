# Platform Admin Account Creation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a platform-admin-only direct account creation flow with admin-entered initial passwords, admin-triggered password reset, audit logging, and a feature-gated UI that stays dark in production until enabled.

**Architecture:** Extend the existing auth/admin seams instead of building a parallel subsystem. Store the new lifecycle metadata on `user_profiles`, add one focused backend helper for direct account creation and password reset, expose the feature through platform-admin-only API routes, and add one small frontend runtime module plus minimal `app.js` wiring.

**Tech Stack:** FastAPI, Supabase REST/admin auth APIs, SQL migrations, vanilla frontend runtime modules, Python `unittest`, Node `node:test`

---

## Planned File Structure

- Create: `backend/services/auth_admin_account_backend.py`
  - Owns direct account creation and admin password reset orchestration.
- Create: `tests/test_auth_admin_account_backend.py`
  - Locks the new backend helper behavior before the API layer is wired.
- Create: `tests/api/test_auth_admin_accounts_api.py`
  - Verifies feature flag, authorization, success, and error responses for the new endpoints.
- Create: `frontend/platform-admin-account-runtime.js`
  - Renders deterministic markup for the platform-admin account creation card and result state.
- Create: `frontend/tests/platform-admin-account-runtime.test.js`
  - Locks runtime markup and result rendering for the new admin card.
- Create: `supabase/migrations/202604010002_platform_admin_account_creation.sql`
  - Extends `user_profiles` for admin provenance and forward-compatible password policy state.
- Modify: `backend/api/app.py`
  - Adds the new platform-admin-only routes.
- Modify: `backend/api/auth_runtime.py`
  - Exposes the feature flag, wraps the new backend helper, and reuses existing auth/admin transport helpers.
- Modify: `backend/api/schemas.py`
  - Adds request/response models for create and password-reset flows plus the session flag field.
- Modify: `backend/services/auth_profile_write_backend.py`
  - Extends user profile upsert helpers for new lifecycle fields without changing current callers.
- Modify: `frontend/app.js`
  - Inserts the new admin card, binds submit/reset actions, and refreshes existing member/audit data after writes.
- Modify: `frontend/index.html`
  - Loads the new frontend runtime module.
- Modify: `frontend/vercel.json`
  - Rewrites `/app/platform-admin-account-runtime.js` for the Vercel deployment path.
- Modify: `frontend/tests/org-admin-runtime.test.js`
  - Covers coexistence with the existing admin panel layout if shared card markup changes.
- Modify: `tests/test_auth_runtime.py`
  - Covers session-response feature flag exposure and thin facade wiring in `auth_runtime.py`.

## Task 1: Persistence And Backend Helper

**Files:**
- Create: `supabase/migrations/202604010002_platform_admin_account_creation.sql`
- Create: `backend/services/auth_admin_account_backend.py`
- Create: `tests/test_auth_admin_account_backend.py`
- Modify: `backend/services/auth_profile_write_backend.py`

- [ ] **Step 1: Write the failing backend helper tests**

```python
import unittest

from backend.services import auth_admin_account_backend as backend


class PlatformAdminAccountBackendTests(unittest.TestCase):
    def test_create_account_requires_platform_admin(self) -> None:
        with self.assertRaises(RuntimeError):
            backend.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="org_admin",
                organization_id="org-1",
                email="member@example.com",
                password="TempPass123!",
                display_name="Member",
                role="org_member",
                create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
                list_local_users_fn=lambda **_kwargs: [],
                ensure_user_profile_fn=lambda **_kwargs: None,
                ensure_membership_fn=lambda **_kwargs: None,
                append_audit_log_fn=lambda **_kwargs: None,
                normalize_email_fn=lambda value: str(value).strip().lower(),
                normalize_org_role_fn=lambda value: str(value).strip().lower(),
                auth_error_cls=RuntimeError,
            )

    def test_create_account_creates_profile_membership_and_audit(self) -> None:
        profile_calls = []
        membership_calls = []
        audit_calls = []

        item = backend.create_platform_admin_account(
            actor_user_id="admin-1",
            actor_role="platform_admin",
            organization_id="org-1",
            email="member@example.com",
            password="TempPass123!",
            display_name="Member",
            role="org_member",
            create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
            list_local_users_fn=lambda **_kwargs: [],
            ensure_user_profile_fn=lambda **kwargs: profile_calls.append(kwargs),
            ensure_membership_fn=lambda **kwargs: membership_calls.append(kwargs),
            append_audit_log_fn=lambda **kwargs: audit_calls.append(kwargs),
            normalize_email_fn=lambda value: str(value).strip().lower(),
            normalize_org_role_fn=lambda value: str(value).strip().lower(),
            auth_error_cls=RuntimeError,
        )

        self.assertEqual(item["email"], "member@example.com")
        self.assertEqual(profile_calls[0]["account_status"], "active")
        self.assertEqual(profile_calls[0]["password_setup_mode"], "admin_set")
        self.assertFalse(profile_calls[0]["force_password_change"])
        self.assertEqual(membership_calls[0]["organization_id"], "org-1")
        self.assertEqual(audit_calls[0]["event_type"], "account_created")
```

- [ ] **Step 2: Run the backend helper tests to verify they fail**

Run: `python -m unittest tests.test_auth_admin_account_backend -v`

Expected: FAIL with `ModuleNotFoundError` for `backend.services.auth_admin_account_backend`.

- [ ] **Step 3: Implement the migration and backend helper**

```sql
alter table public.user_profiles
  add column if not exists created_by_user_id uuid references public.user_profiles(id) on delete set null,
  add column if not exists password_setup_mode text not null default 'admin_set',
  add column if not exists force_password_change boolean not null default false;

alter table public.user_profiles
  drop constraint if exists user_profiles_password_setup_mode_check;

alter table public.user_profiles
  add constraint user_profiles_password_setup_mode_check
  check (password_setup_mode in ('admin_set', 'system_generated'));

create or replace view public.organization_member_profiles as
select
  m.id as membership_id,
  m.organization_id,
  o.name as organization_name,
  o.slug as organization_slug,
  m.user_profile_id as user_id,
  p.email,
  p.display_name,
  p.mobile_phone,
  p.office_phone,
  p.account_status,
  p.global_role,
  p.created_by_user_id,
  p.password_setup_mode,
  p.force_password_change,
  m.role as membership_role,
  m.membership_status,
  m.team_name,
  m.job_title,
  p.last_login_at,
  p.created_at as profile_created_at,
  p.updated_at as profile_updated_at,
  m.created_at as membership_created_at,
  m.updated_at as membership_updated_at
from public.organization_memberships m
join public.user_profiles p on p.id = m.user_profile_id
join public.organizations o on o.id = m.organization_id;
```

```python
def create_platform_admin_account(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    email: str,
    password: str,
    display_name: str,
    role: str,
    create_auth_user_fn: Any,
    list_local_users_fn: Any,
    ensure_user_profile_fn: Any,
    ensure_membership_fn: Any,
    append_audit_log_fn: Any,
    normalize_email_fn: Any,
    normalize_org_role_fn: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    if str(actor_role or "").strip().lower() != "platform_admin":
        raise auth_error_cls("platform admin only", status_code=403, code="auth_forbidden")
    normalized_email = normalize_email_fn(email)
    if not normalized_email or not password:
        raise auth_error_cls("email and password are required", status_code=400, code="validation_error")
    existing_items = list_local_users_fn(organization_id=organization_id, include_inactive=True)
    if any(str(item.get("email") or "").strip().lower() == normalized_email for item in existing_items):
        raise auth_error_cls("account already exists", status_code=409, code="auth_user_exists")

    created_auth_user = create_auth_user_fn(
        email=normalized_email,
        password=password,
        display_name=display_name,
    )
    user_id = str(created_auth_user.get("id") or "").strip()
    normalized_role = normalize_org_role_fn(role)
    ensure_user_profile_fn(
        user_id=user_id,
        email=normalized_email,
        display_name=display_name.strip(),
        account_status="active",
        global_role="",
        created_by_user_id=actor_user_id,
        password_setup_mode="admin_set",
        force_password_change=False,
    )
    ensure_membership_fn(
        organization_id=organization_id,
        user_id=user_id,
        role=normalized_role,
        membership_status="active",
    )
    append_audit_log_fn(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        event_type="account_created",
        target_type="user_profile",
        target_id=user_id,
        payload={"email": normalized_email, "role": normalized_role},
    )
    return {
        "id": user_id,
        "email": normalized_email,
        "display_name": display_name.strip(),
        "role": normalized_role,
        "account_status": "active",
        "membership_status": "active",
        "password_setup_mode": "admin_set",
        "force_password_change": False,
    }
```

```python
def ensure_user_profile(
    *,
    user_id: str,
    email: str,
    display_name: str,
    account_status: str = "active",
    global_role: str = "",
    created_by_user_id: str = "",
    password_setup_mode: str = "admin_set",
    force_password_change: bool = False,
    get_user_profile_fn: Any,
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    rest_upsert_fn: Any,
    normalize_account_status_fn: Any,
    normalize_global_role_fn: Any,
    is_missing_relation_error_fn: Any,
    auth_error_cls: type[Exception],
) -> None:
    payload = {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "account_status": normalize_account_status_fn(account_status),
        "global_role": normalize_global_role_fn(global_role),
        "created_by_user_id": created_by_user_id or None,
        "password_setup_mode": str(password_setup_mode or "admin_set").strip(),
        "force_password_change": bool(force_password_change),
    }
    rest_upsert_fn("user_profiles", payload, on_conflict="id")
```

- [ ] **Step 4: Run the backend helper tests to verify they pass**

Run: `python -m unittest tests.test_auth_admin_account_backend -v`

Expected: PASS with create-account authorization and persistence assertions green.

- [ ] **Step 5: Commit the persistence/helper work**

```bash
git add supabase/migrations/202604010002_platform_admin_account_creation.sql backend/services/auth_admin_account_backend.py backend/services/auth_profile_write_backend.py tests/test_auth_admin_account_backend.py
git commit -m "feat: add platform admin account backend"
```

## Task 2: API Surface And Auth Session Wiring

**Files:**
- Create: `tests/api/test_auth_admin_accounts_api.py`
- Modify: `backend/api/schemas.py`
- Modify: `backend/api/auth_runtime.py`
- Modify: `backend/api/app.py`
- Modify: `tests/test_auth_runtime.py`

- [ ] **Step 1: Write the failing API and facade tests**

```python
from unittest import TestCase, mock
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api import app as app_module


class AuthAdminAccountApiTests(TestCase):
    def test_post_admin_accounts_rejects_when_feature_is_disabled(self) -> None:
        client = TestClient(app_module.app)
        actor = mock.Mock(is_admin=True, role="platform_admin", organization_id=uuid4(), user_id=uuid4(), email="ops@example.com")
        with (
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=False),
        ):
            response = client.post(
                "/api/admin/accounts",
                json={
                    "email": "member@example.com",
                    "display_name": "Member",
                    "role": "org_member",
                    "password": "TempPass123!",
                },
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "auth_forbidden")

    def test_post_admin_accounts_returns_created_item_for_platform_admin(self) -> None:
        client = TestClient(app_module.app)
        actor = mock.Mock(is_admin=True, role="platform_admin", organization_id=uuid4(), user_id=uuid4(), email="ops@example.com")
        with (
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=True),
            mock.patch.object(
                app_module,
                "create_platform_admin_account",
                return_value={
                    "id": str(uuid4()),
                    "email": "member@example.com",
                    "display_name": "Member",
                    "role": "org_member",
                    "account_status": "active",
                    "membership_status": "active",
                    "password_setup_mode": "admin_set",
                    "force_password_change": False,
                },
            ),
        ):
            response = client.post(
                "/api/admin/accounts",
                json={
                    "email": "member@example.com",
                    "display_name": "Member",
                    "role": "org_member",
                    "password": "TempPass123!",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["platform_admin_managed"])
```

```python
class AuthRuntimeTests(unittest.TestCase):
    def test_build_session_response_payload_exposes_platform_admin_account_creation_flag(self) -> None:
        with mock.patch.dict(os.environ, {"ENABLE_PLATFORM_ADMIN_ACCOUNT_CREATION": "1"}, clear=False):
            payload = auth_runtime.build_session_response_payload(
                {"authorized": True, "authenticated": True, "role": "platform_admin", "email": "ops@example.com"}
            )

        self.assertTrue(payload["platform_admin_account_creation_enabled"])
```

- [ ] **Step 2: Run the API and facade tests to verify they fail**

Run: `python -m unittest tests.api.test_auth_admin_accounts_api tests.test_auth_runtime -v`

Expected: FAIL because `/api/admin/accounts` does not exist, the request/response schemas are missing, and the session payload does not expose the feature flag.

- [ ] **Step 3: Implement schemas, runtime wrappers, and routes**

```python
class AuthAdminAccountCreateRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    role: str = "org_member"


class AuthAdminAccountPasswordResetRequest(BaseModel):
    password: str


class AuthAdminAccountItem(BaseModel):
    id: UUID
    email: str
    display_name: str = ""
    role: str = ""
    account_status: str = "active"
    membership_status: str = "active"
    password_setup_mode: str = "admin_set"
    force_password_change: bool = False
    platform_admin_managed: bool = True
```

```python
def platform_admin_account_creation_enabled() -> bool:
    return str(os.getenv("ENABLE_PLATFORM_ADMIN_ACCOUNT_CREATION", "")).strip().lower() in {"1", "true", "yes", "on"}


def create_platform_admin_account(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    email: str,
    password: str,
    display_name: str,
    role: str,
) -> dict[str, Any]:
    return _create_platform_admin_account_impl(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        organization_id=organization_id,
        email=email,
        password=password,
        display_name=display_name,
        role=role,
        create_auth_user_fn=_create_supabase_auth_user,
        list_local_users_fn=list_local_users,
        ensure_user_profile_fn=_ensure_user_profile,
        ensure_membership_fn=_ensure_membership,
        append_audit_log_fn=_append_audit_log,
        normalize_email_fn=_normalize_email,
        normalize_org_role_fn=_normalize_org_role,
        auth_error_cls=AuthRuntimeError,
    )
```

```python
@app.post("/api/admin/accounts", response_model=AuthAdminAccountItem)
def post_admin_account(request: Request, payload: AuthAdminAccountCreateRequest) -> AuthAdminAccountItem:
    actor = _resolve_sales_actor(request)
    if not platform_admin_account_creation_enabled() or str(actor.role or "") != "platform_admin":
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="플랫폼 운영자만 계정을 생성할 수 있습니다.",
        )
    try:
        item = create_platform_admin_account(
            actor_user_id=str(actor.user_id or ""),
            actor_role=str(actor.role or ""),
            organization_id=str(actor.organization_id),
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
            role=payload.role,
        )
    except AuthRuntimeError as exc:
        raise ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return AuthAdminAccountItem.model_validate({**item, "platform_admin_managed": True})
```

```python
@app.post("/api/admin/accounts/{user_id}/password-reset", response_model=MessageResponse)
def post_admin_account_password_reset(
    request: Request,
    user_id: UUID,
    payload: AuthAdminAccountPasswordResetRequest,
) -> MessageResponse:
    actor = _resolve_sales_actor(request)
    if not platform_admin_account_creation_enabled() or str(actor.role or "") != "platform_admin":
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="auth_forbidden",
            message="플랫폼 운영자만 비밀번호를 재설정할 수 있습니다.",
        )
    reset_platform_admin_account_password(
        actor_user_id=str(actor.user_id or ""),
        actor_role=str(actor.role or ""),
        organization_id=str(actor.organization_id),
        user_id=str(user_id),
        password=payload.password,
    )
    return MessageResponse(message="비밀번호를 재설정했습니다.")
```

- [ ] **Step 4: Run the API and facade tests to verify they pass**

Run: `python -m unittest tests.api.test_auth_admin_accounts_api tests.test_auth_runtime -v`

Expected: PASS with the feature-flag, authorization, create success, and session-payload assertions green.

- [ ] **Step 5: Commit the API surface work**

```bash
git add backend/api/schemas.py backend/api/auth_runtime.py backend/api/app.py tests/api/test_auth_admin_accounts_api.py tests/test_auth_runtime.py
git commit -m "feat: add platform admin account APIs"
```

## Task 3: Frontend Admin Card And Wiring

**Files:**
- Create: `frontend/platform-admin-account-runtime.js`
- Create: `frontend/tests/platform-admin-account-runtime.test.js`
- Modify: `frontend/app.js`
- Modify: `frontend/index.html`
- Modify: `frontend/vercel.json`
- Modify: `frontend/tests/org-admin-runtime.test.js`

- [ ] **Step 1: Write the failing frontend runtime tests**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path, key) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window[key];
}

test("buildPlatformAdminAccountCardMarkup renders password field and create button", () => {
  const runtime = loadRuntime("frontend/platform-admin-account-runtime.js", "SPMSPlatformAdminAccountRuntime");
  const html = runtime.buildPlatformAdminAccountCardMarkup(
    {
      enabled: true,
      currentUserRole: "platform_admin",
      saving: false,
      result: null,
    },
    {
      escapeHtml: (value) => String(value),
    },
  );

  assert.match(html, /platform-admin-account-form/);
  assert.match(html, /name="password"/);
  assert.match(html, /계정 생성/);
});

test("buildPlatformAdminAccountResultMarkup renders active status without echoing the password", () => {
  const runtime = loadRuntime("frontend/platform-admin-account-runtime.js", "SPMSPlatformAdminAccountRuntime");
  const html = runtime.buildPlatformAdminAccountResultMarkup(
    {
      email: "member@example.com",
      display_name: "Member",
      role: "org_member",
      account_status: "active",
      membership_status: "active",
      password_setup_mode: "admin_set",
      force_password_change: false,
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
    },
  );

  assert.match(html, /member@example.com/);
  assert.match(html, /active/);
  assert.doesNotMatch(html, /TempPass123!/);
});
```

- [ ] **Step 2: Run the frontend runtime tests to verify they fail**

Run: `node --test frontend/tests/platform-admin-account-runtime.test.js`

Expected: FAIL because `frontend/platform-admin-account-runtime.js` does not exist yet.

- [ ] **Step 3: Implement the new runtime module and wire it into the admin panel**

```javascript
(function initPlatformAdminAccountRuntime(global) {
  function buildPlatformAdminAccountCardMarkup(state, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? ""), formatOrgRoleLabel = (value) => String(value ?? "") } = helpers;
    if (!state.enabled || state.currentUserRole !== "platform_admin") {
      return '<div class="empty-state">플랫폼 운영자 전용 기능입니다.</div>';
    }
    return `
      <article class="runtime-card org-admin-card">
        <div class="runtime-card-head">
          <div>
            <strong>직접 계정 생성</strong>
            <p class="kicker">플랫폼 운영자가 로그인 가능한 계정을 바로 생성합니다.</p>
          </div>
        </div>
        <form id="platform-admin-account-form" class="org-admin-form">
          <input name="email" type="email" placeholder="이메일" required />
          <input name="display_name" type="text" placeholder="표시 이름" />
          <select name="role">
            <option value="org_member">사용자</option>
            <option value="org_admin">관리자</option>
          </select>
          <input name="password" type="password" placeholder="초기 비밀번호" required />
          <button id="platform-admin-account-submit-button" class="primary-button" type="submit">계정 생성</button>
        </form>
        <div id="platform-admin-account-result">${state.result ? buildPlatformAdminAccountResultMarkup(state.result, helpers) : ""}</div>
      </article>
    `;
  }

  function buildPlatformAdminAccountResultMarkup(item, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? ""), formatOrgRoleLabel = (value) => String(value ?? "") } = helpers;
    return `
      <article class="org-admin-list-item">
        <div class="org-admin-list-item-head">
          <strong>${escapeHtml(item.display_name || item.email)}</strong>
          <span class="status-badge status-${escapeHtml(item.account_status || "active")}">${escapeHtml(item.account_status || "active")}</span>
        </div>
        <p class="mono">${escapeHtml(item.email)}</p>
        <p>${escapeHtml(formatOrgRoleLabel(item.role || ""))}</p>
      </article>
    `;
  }

  global.SPMSPlatformAdminAccountRuntime = {
    buildPlatformAdminAccountCardMarkup,
    buildPlatformAdminAccountResultMarkup,
  };
})(window);
```

```html
<script defer src="/app/platform-admin-account-runtime.js?v=20260401a"></script>
```

```json
{
  "source": "/app/platform-admin-account-runtime.js",
  "destination": "/platform-admin-account-runtime.js"
}
```

```javascript
state.platformAdminAccount = {
  saving: false,
  result: null,
};

orgAdminPanel.innerHTML = `
  <div class="panel-heading">
    <div>
      <p class="kicker">Admin</p>
      <h2>User Admin</h2>
    </div>
    <button id="org-admin-refresh-button" class="ghost-button" type="button">Refresh</button>
  </div>
  <div class="org-admin-grid">
    <div id="platform-admin-account-panel-slot"></div>
    <article class="runtime-card org-admin-card">
      <div id="organization-plan-summary"></div>
      <form id="invitation-form" class="org-admin-form"></form>
      <div id="invitation-status-message"></div>
      <div id="invitation-list"></div>
    </article>
    <article class="runtime-card org-admin-card">
      <div id="organization-member-summary"></div>
      <div id="organization-member-list"></div>
    </article>
    <div id="organization-audit-panel-slot"></div>
    <div id="organization-download-audit-panel-slot"></div>
    <div id="organization-login-audit-panel-slot"></div>
    <div class="org-admin-empty-slot" aria-hidden="true"></div>
  </div>
`;
dom.platformAdminAccountPanelSlot = orgAdminPanel.querySelector("#platform-admin-account-panel-slot");

function renderOrganizationAdminPanel() {
  const cardHtml = window.SPMSPlatformAdminAccountRuntime?.buildPlatformAdminAccountCardMarkup(
    {
      enabled: Boolean(state.auth.platform_admin_account_creation_enabled),
      currentUserRole: String(state.auth.user?.role || ""),
      saving: state.platformAdminAccount.saving,
      result: state.platformAdminAccount.result,
    },
    {
      escapeHtml,
      formatOrgRoleLabel,
    },
  ) || "";
  dom.platformAdminAccountPanelSlot.innerHTML = cardHtml;
  const form = dom.platformAdminAccountPanelSlot.querySelector("#platform-admin-account-form");
  if (form) {
    form.addEventListener("submit", submitPlatformAdminAccountForm);
  }
}

async function submitPlatformAdminAccountForm(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  state.platformAdminAccount.saving = true;
  renderOrganizationAdminPanel();
  try {
    const item = await api("/api/admin/accounts", {
      method: "POST",
      body: JSON.stringify({
        email: String(form.get("email") || "").trim(),
        display_name: String(form.get("display_name") || "").trim(),
        role: String(form.get("role") || "org_member").trim(),
        password: String(form.get("password") || ""),
      }),
    });
    state.platformAdminAccount.result = item;
    await Promise.all([
      loadOrganizationMembers({ silent: true }),
      loadOrganizationAuditLogs({ silent: true }),
    ]);
  } finally {
    state.platformAdminAccount.saving = false;
    renderOrganizationAdminPanel();
  }
}
```

- [ ] **Step 4: Run the frontend tests and static checks**

Run: `node --test frontend/tests/platform-admin-account-runtime.test.js frontend/tests/org-admin-runtime.test.js`

Expected: PASS with the new runtime card and existing admin panel tests green.

Run: `node --check frontend/platform-admin-account-runtime.js`

Expected: no output

Run: `node --check frontend/app.js`

Expected: no output

- [ ] **Step 5: Commit the frontend work**

```bash
git add frontend/platform-admin-account-runtime.js frontend/tests/platform-admin-account-runtime.test.js frontend/app.js frontend/index.html frontend/vercel.json frontend/tests/org-admin-runtime.test.js
git commit -m "feat: add platform admin account creation UI"
```

## Final Verification Pass

- [ ] Run: `python -m unittest tests.test_auth_admin_account_backend tests.api.test_auth_admin_accounts_api tests.test_auth_runtime -v`
- [ ] Run: `node --test frontend/tests/platform-admin-account-runtime.test.js frontend/tests/org-admin-runtime.test.js`
- [ ] Run: `node --check frontend/platform-admin-account-runtime.js`
- [ ] Run: `node --check frontend/app.js`
- [ ] Run: `git status --short`

Expected final state:

- all targeted Python tests pass
- all targeted frontend tests pass
- frontend files parse cleanly
- working tree only contains the intended feature changes
