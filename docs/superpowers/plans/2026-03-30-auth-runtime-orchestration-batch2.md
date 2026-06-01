# Auth Runtime Orchestration Batch 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract auth session/profile orchestration from `backend/api/auth_runtime.py` into a focused backend service without changing auth behavior.

**Architecture:** Add a new `backend/services/auth_session_orchestration_backend.py` module that owns sign-in, sign-up, password-reset, session-refresh, session-status, and console-profile-update orchestration through dependency injection. Keep `backend/api/auth_runtime.py` as the public facade that wires existing helpers and delegates to the new backend module, while preserving current route contracts and error semantics.

**Tech Stack:** Python, `unittest`, FastAPI request/response objects, dependency-injected backend helpers

---

### File Structure

**Create:**
- `backend/services/auth_session_orchestration_backend.py`
- `tests/test_auth_session_orchestration_backend.py`

**Modify:**
- `backend/api/auth_runtime.py`
- `tests/test_auth_runtime.py`

The new backend file owns orchestration only. `auth_runtime.py` keeps constants, low-level wrappers, and public function exports.

### Task 1: Lock Session/Profile Orchestration Behavior With Tests

**Files:**
- Create: `tests/test_auth_session_orchestration_backend.py`
- Modify: `tests/test_auth_runtime.py`

- [ ] **Step 1: Add failing backend orchestration tests for protected/session refresh behavior**

```python
from backend.services import auth_session_orchestration_backend as orchestration


def test_ensure_fresh_session_payload_clears_cookie_when_refresh_token_missing():
    response = Response()
    with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
        orchestration.ensure_fresh_session_payload(
            payload={"access_expires_at": 1, "refresh_token": ""},
            response=response,
            now=100,
            grace_seconds=auth_runtime.SESSION_REFRESH_GRACE_SECONDS,
            refresh_auth_session_fn=lambda *_args, **_kwargs: None,
            clear_auth_session_cookie_fn=lambda _response: cleared.append(True),
            set_auth_session_cookie_fn=lambda *_args, **_kwargs: None,
            error_cls=auth_runtime.AuthRuntimeError,
            logger=mock.Mock(),
            session_refresh_timeout_seconds_fn=lambda: 30.0,
        )
```

- [ ] **Step 2: Add failing backend orchestration tests for sign-in and profile-update paths**

```python
def test_sign_in_with_password_accepts_resolved_invitation_token():
    payload = orchestration.sign_in_with_password(
        email="member@example.com",
        password="secret",
        invite_token="",
        request_host="example.com",
        ensure_auth_enabled=lambda: None,
        normalize_email_fn=lambda value: str(value).strip().lower(),
        can_use_local_bootstrap_fallback_fn=lambda **_kwargs: False,
        has_local_bootstrap_password_fn=lambda **_kwargs: False,
        verify_local_bootstrap_password_fn=lambda **_kwargs: False,
        build_local_bootstrap_session_fn=lambda **_kwargs: {},
        auth_request_fn=lambda *_args, **_kwargs: {"access_token": "a", "refresh_token": "r", "expires_in": 3600, "user": {"id": "user-1", "email": "member@example.com"}},
        finalize_session_payload_fn=lambda payload: {**payload, "auth_user_id": "user-1", "email": "member@example.com"},
        resolve_pending_invitation_token_for_email_fn=lambda **_kwargs: "invite-1",
        require_invitation_email_match_fn=lambda **_kwargs: None,
        accept_invitation_for_session_payload_fn=lambda **kwargs: {**kwargs["session_payload"], "accepted": kwargs["invite_token"]},
        touch_last_login_fn=lambda **_kwargs: None,
        error_cls=auth_runtime.AuthRuntimeError,
    )

    self.assertEqual(payload["accepted"], "invite-1")
```

- [ ] **Step 3: Run targeted tests to verify the new backend coverage fails first**

Run:
```powershell
python -m unittest tests.test_auth_session_orchestration_backend
```

Expected: `FAIL` because the backend module and delegated orchestration helpers do not exist yet.

- [ ] **Step 4: Commit the red state**

```powershell
git add tests/test_auth_session_orchestration_backend.py tests/test_auth_runtime.py
git commit -m "test: add auth session orchestration coverage"
```

### Task 2: Create `auth_session_orchestration_backend.py` And Move Orchestration There

**Files:**
- Create: `backend/services/auth_session_orchestration_backend.py`
- Test: `tests/test_auth_session_orchestration_backend.py`

- [ ] **Step 1: Add minimal orchestration helpers that mirror the current public flows**

```python
def sign_in_with_password(
    *,
    email: str,
    password: str,
    invite_token: str = "",
    request_host: str = "",
    ensure_auth_enabled: Any,
    normalize_email_fn: Any,
    can_use_local_bootstrap_fallback_fn: Any,
    has_local_bootstrap_password_fn: Any,
    verify_local_bootstrap_password_fn: Any,
    build_local_bootstrap_session_fn: Any,
    auth_request_fn: Any,
    finalize_session_payload_fn: Any,
    resolve_pending_invitation_token_for_email_fn: Any,
    require_invitation_email_match_fn: Any,
    accept_invitation_for_session_payload_fn: Any,
    touch_last_login_fn: Any,
    error_cls: Any,
) -> dict[str, Any]:
    ...
```

- [ ] **Step 2: Implement the matching helpers for**

```python
def sign_up_console_user(...): ...
def send_password_reset_email(...): ...
def ensure_fresh_session_payload(...): ...
def build_session_response(...): ...
def refresh_auth_session(...): ...
def update_console_user_profile(...): ...
```

Keep the new file orchestration-only. Do not move low-level auth transport, cookie codec, invitation read/write, or profile persistence implementations into it.

- [ ] **Step 3: Run focused backend tests**

Run:
```powershell
python -m unittest tests.test_auth_session_orchestration_backend
```

Expected: `OK`

- [ ] **Step 4: Commit**

```powershell
git add backend/services/auth_session_orchestration_backend.py tests/test_auth_session_orchestration_backend.py
git commit -m "refactor: extract auth session orchestration backend"
```

### Task 3: Convert `auth_runtime.py` Into A Thin Facade For The Extracted Flows

**Files:**
- Modify: `backend/api/auth_runtime.py`
- Modify: `tests/test_auth_runtime.py`
- Test: `tests/test_auth_session_orchestration_backend.py`

- [ ] **Step 1: Import the new backend helpers in `backend/api/auth_runtime.py`**

```python
from backend.services.auth_session_orchestration_backend import build_session_response as _build_session_response_impl
from backend.services.auth_session_orchestration_backend import ensure_fresh_session_payload as _ensure_fresh_session_payload_impl
from backend.services.auth_session_orchestration_backend import refresh_auth_session as _refresh_auth_session_impl
from backend.services.auth_session_orchestration_backend import send_password_reset_email as _send_password_reset_email_impl
from backend.services.auth_session_orchestration_backend import sign_in_with_password as _sign_in_with_password_impl
from backend.services.auth_session_orchestration_backend import sign_up_console_user as _sign_up_console_user_impl
from backend.services.auth_session_orchestration_backend import update_console_user_profile as _update_console_user_profile_impl
```

- [ ] **Step 2: Replace the public bodies with thin delegation wrappers**

```python
def sign_in_with_password(*, email: str, password: str, invite_token: str = "", request_host: str = "") -> dict[str, Any]:
    return _sign_in_with_password_impl(
        email=email,
        password=password,
        invite_token=invite_token,
        request_host=request_host,
        ensure_auth_enabled=_ensure_auth_enabled,
        normalize_email_fn=_normalize_email,
        can_use_local_bootstrap_fallback_fn=_can_use_local_bootstrap_fallback,
        has_local_bootstrap_password_fn=_has_local_bootstrap_password,
        verify_local_bootstrap_password_fn=_verify_local_bootstrap_password,
        build_local_bootstrap_session_fn=_build_local_bootstrap_session,
        auth_request_fn=_auth_request,
        finalize_session_payload_fn=_finalize_session_payload,
        resolve_pending_invitation_token_for_email_fn=_resolve_pending_invitation_token_for_email,
        require_invitation_email_match_fn=_require_invitation_email_match,
        accept_invitation_for_session_payload_fn=accept_invitation_for_session_payload,
        touch_last_login_fn=_touch_last_login,
        error_cls=AuthRuntimeError,
    )
```

Mirror the same pattern for sign-up, password reset, session refresh/status, and profile update.

- [ ] **Step 3: Keep thin-facade regression coverage in `tests/test_auth_runtime.py`**

Add assertions that the public functions still call through correctly with the existing facade-level dependencies.

```python
with mock.patch.object(auth_runtime, "_sign_in_with_password_impl", return_value={"authorized": True}) as helper:
    payload = auth_runtime.sign_in_with_password(email="member@example.com", password="secret")

self.assertTrue(payload["authorized"])
helper.assert_called_once()
```

- [ ] **Step 4: Run auth runtime and backend tests**

Run:
```powershell
python -m unittest tests.test_auth_runtime tests.test_auth_session_orchestration_backend
```

Expected: `OK`

- [ ] **Step 5: Commit**

```powershell
git add backend/api/auth_runtime.py tests/test_auth_runtime.py tests/test_auth_session_orchestration_backend.py
git commit -m "refactor: slim auth runtime session facade"
```

### Task 4: Run Broader Auth Verification

**Files:**
- No additional file changes required

- [ ] **Step 1: Run the broader auth-related verification suite**

Run:
```powershell
python -m unittest tests.test_auth_runtime tests.test_auth_invitation_backend tests.test_auth_invitation_read_backend tests.test_auth_invitation_session_backend tests.test_auth_profile_lookup_backend tests.test_auth_profile_write_backend
```

Expected: `OK`

- [ ] **Step 2: Run API coverage that touches auth session behavior**

Run:
```powershell
python -m unittest tests.api.test_phase1_api
```

Expected: `OK`

- [ ] **Step 3: Confirm worktree state**

Run:
```powershell
git status --short
git log --oneline -6
```

Expected: clean worktree and the three new batch commits on top.
