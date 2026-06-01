# Invite Delivery Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 조직 관리자 초대 생성 시 자동 메일 발송을 복구하고, 발송 실패 시에도 초대 링크와 초기 암호를 관리자 UI에서 즉시 복사할 수 있게 만든다.

**Architecture:** 백엔드는 기존 `Supabase Auth + Custom SMTP` 흐름을 유지하면서 `send_email` 활성화와 실패 payload 보존을 검증한다. 프론트는 초대 생성 직후 응답의 `invite_url`, `initial_password`, `delivery_message`를 상태/UI에 남겨, 메일 실패나 수동 전달 경로에서도 빈 패널이 아니라 복사 가능한 fallback을 보여준다.

**Tech Stack:** FastAPI, Supabase Auth REST, vanilla JS runtime UI, Python `unittest`, Node test

---

### Task 1: Backend Invite Delivery Activation

**Files:**
- Modify: `backend/api/auth_runtime.py`
- Modify: `backend/api/app.py`
- Modify: `backend/services/auth_invitation_backend.py`
- Test: `tests/test_auth_runtime.py`

- [ ] **Step 1: Add/adjust failing backend tests for delivery gating and fallback payload**

Add tests in `tests/test_auth_runtime.py` covering:

```python
def test_invitation_email_delivery_enabled_defaults_true_when_auth_enabled(self) -> None:
    with mock.patch.dict(os.environ, {"PHASE2_AUTH_ENABLED": "1"}, clear=False):
        self.assertTrue(auth_runtime.invitation_email_delivery_enabled())


def test_create_invitation_preserves_manual_fallback_payload_when_delivery_fails(self) -> None:
    with (
        mock.patch.object(auth_runtime, "_create_invitation_impl") as helper,
        mock.patch.object(auth_runtime, "_ensure_auth_enabled"),
    ):
        helper.return_value = {
            "id": "invite-1",
            "email": "member@example.com",
            "invite_token": "invite-token-123",
            "invite_url": "http://127.0.0.1:8019/app/?invite_token=invite-token-123",
            "initial_password": "pw-123",
            "delivery_status": "failed",
            "delivery_message": "smtp failed",
        }
        item = auth_runtime.create_invitation(
            organization_id="org-1",
            created_by="user-1",
            actor_role="org_admin",
            email="member@example.com",
            role="org_member",
            invite_url_base="http://127.0.0.1:8019",
            send_email=True,
        )

    self.assertEqual(item["delivery_status"], "failed")
    self.assertEqual(item["invite_url"], "http://127.0.0.1:8019/app/?invite_token=invite-token-123")
    self.assertEqual(item["initial_password"], "pw-123")
```

- [ ] **Step 2: Run the targeted backend tests and confirm the current gap**

Run:

```bash
python -m unittest tests.test_auth_runtime
```

Expected: at least one failure tied to invite delivery gating or fallback assumptions if the current implementation still diverges.

- [ ] **Step 3: Implement the backend delivery fix**

Update these paths:

- `backend/api/auth_runtime.py`
  - Keep `invitation_email_delivery_enabled()` aligned with actual auth-enabled operation.
  - If `PHASE2_AUTH_DELIVER_INVITE_EMAILS` is explicitly set, honor it.
  - Otherwise default to enabled when auth is enabled.
- `backend/api/app.py`
  - Keep `send_email = invitation_email_delivery_enabled()` and preserve `invite_url`, `initial_password`, `delivery_status`, `delivery_message` on the response path.
  - Do not overwrite a service-produced failure payload with a blank manual state.
- `backend/services/auth_invitation_backend.py`
  - Preserve `invite_url` and `initial_password` regardless of `sent` / `failed` / `manual`.
  - Keep `delivery_message` human-readable for failed/manual paths.

- [ ] **Step 4: Re-run the targeted backend tests**

Run:

```bash
python -m unittest tests.test_auth_runtime
```

Expected: PASS

- [ ] **Step 5: Commit the backend invite delivery fix**

```bash
git add backend/api/auth_runtime.py backend/api/app.py backend/services/auth_invitation_backend.py tests/test_auth_runtime.py
git commit -m "fix: restore invite delivery fallback payloads"
```

### Task 2: Frontend Invite Fallback Visibility

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/org-admin-runtime.js`
- Test: `frontend/tests/org-admin-runtime.test.js`

- [ ] **Step 1: Add failing frontend tests for invite fallback rendering**

Extend `frontend/tests/org-admin-runtime.test.js` with a case like:

```javascript
test("invitation list keeps invite link actions and initial password for failed delivery", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildInvitationListMarkup(
    {
      invitations: [
        {
          id: "invite-1",
          email: "member@example.com",
          role: "org_member",
          status: "pending",
          invite_url: "https://example.com/app/?invite_token=invite-1",
          initial_password: "pw-123",
          delivery_status: "failed",
          delivery_message: "smtp failed",
        },
      ],
    },
    helpers,
  );

  assert.match(html, /smtp failed/);
  assert.match(html, /초기 암호 pw-123/);
  assert.match(html, /data-invite-copy=\"https:\/\/example.com\/app\/\?invite_token=invite-1\"/);
});
```

Add a small `app.js`-level behavior test if needed to lock that `handleInvitationSubmit()` keeps showing fallback text even when delivery fails.

- [ ] **Step 2: Run the targeted frontend tests and confirm the current gap**

Run:

```bash
node --test frontend/tests/org-admin-runtime.test.js
```

Expected: FAIL if the current UI still drops the fallback data or renders an empty result region.

- [ ] **Step 3: Implement the frontend fallback visibility fix**

Update:

- `frontend/org-admin-runtime.js`
  - Ensure invitation cards always render `delivery_message`, `initial_password`, and `링크 복사` when `invite_url` exists.
  - Do not gate the copy action behind `sent` status only.
- `frontend/app.js`
  - In `handleInvitationSubmit()`, preserve the returned invitation payload through `upsertOrganizationInvitation(item)` and `renderOrganizationAdminPanel()`.
  - Keep `copyInvitationUrl()` fallback on non-started delivery states and ensure `renderInvitationStatus()` includes `delivery_message` plus `initial_password`.
  - If there is a dedicated result/status region for newly created invites, ensure it is populated instead of left blank.

- [ ] **Step 4: Re-run the targeted frontend tests**

Run:

```bash
node --test frontend/tests/org-admin-runtime.test.js
node --check frontend/app.js frontend/org-admin-runtime.js
```

Expected: PASS

- [ ] **Step 5: Commit the frontend invite fallback fix**

```bash
git add frontend/app.js frontend/org-admin-runtime.js frontend/tests/org-admin-runtime.test.js
git commit -m "fix: show invite fallback details in admin ui"
```

### Task 3: End-to-End Invite Recovery Verification

**Files:**
- Verify only: `backend/api/app.py`
- Verify only: `backend/api/auth_runtime.py`
- Verify only: `frontend/app.js`
- Verify only: `frontend/org-admin-runtime.js`

- [ ] **Step 1: Run focused backend and frontend verification**

Run:

```bash
python -m unittest tests.test_auth_runtime
node --test frontend/tests/org-admin-runtime.test.js
node --check frontend/app.js frontend/org-admin-runtime.js
```

Expected: all pass

- [ ] **Step 2: Smoke the invite creation path locally**

Run the app with the auth environment used in local testing, then create an invitation from the admin UI.

Expected:

- `delivery_status` is `sent` when Gmail SMTP / Supabase Auth delivery succeeds
- if delivery fails, the UI still shows `delivery_message`, `invite_url` copy action, and `initial_password`

- [ ] **Step 3: Commit any final verification-only adjustments**

```bash
git status --short
```

Expected: no unexpected files beyond intended code/test changes.

