from __future__ import annotations

import unittest
from unittest import mock

from starlette.responses import Response

from backend.api.auth_runtime import AuthRuntimeError
from backend.services import auth_session_orchestration_backend as orchestration


class AuthSessionOrchestrationBackendTests(unittest.TestCase):
    def test_sign_in_with_password_accepts_resolved_invitation_token(self) -> None:
        touched: list[str] = []

        payload = orchestration.sign_in_with_password(
            email="Member@Example.com",
            password="password-123",
            invite_token="",
            request_host="example.com",
            ensure_auth_enabled=lambda: None,
            normalize_email_fn=lambda value: str(value).strip().lower(),
            can_use_local_bootstrap_fallback_fn=lambda **_kwargs: False,
            has_local_bootstrap_password_fn=lambda **_kwargs: False,
            verify_local_bootstrap_password_fn=lambda **_kwargs: False,
            build_local_bootstrap_session_fn=lambda **_kwargs: {},
            auth_request_fn=lambda *_args, **_kwargs: {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "user": {"id": "auth-user-id", "email": "member@example.com"},
            },
            finalize_session_payload_fn=lambda payload: {
                "auth_user_id": str(payload["user"]["id"]),
                "email": str(payload["user"]["email"]),
                "authorized": False,
            },
            resolve_pending_invitation_token_for_email_fn=lambda **_kwargs: "invite-token-123",
            require_invitation_email_match_fn=lambda **_kwargs: None,
            accept_invitation_for_session_payload_fn=lambda **kwargs: {
                **kwargs["session_payload"],
                "accepted_invite_token": kwargs["invite_token"],
            },
            touch_last_login_fn=lambda **kwargs: touched.append(kwargs["auth_user_id"]),
            error_cls=AuthRuntimeError,
        )

        self.assertEqual(payload["accepted_invite_token"], "invite-token-123")
        self.assertEqual(touched, [])

    def test_sign_up_console_user_registers_bootstrap_locally_when_fallback_enabled(self) -> None:
        registered: list[tuple[str, str]] = []

        payload = orchestration.sign_up_console_user(
            email="bootstrap@example.com",
            password="password-123",
            display_name="Bootstrap User",
            invite_token="",
            request_host="127.0.0.1",
            ensure_auth_enabled=lambda: None,
            normalize_email_fn=lambda value: str(value).strip().lower(),
            bootstrap_platform_admin_email_fn=lambda: "bootstrap@example.com",
            resolve_pending_invitation_token_for_email_fn=lambda **_kwargs: "",
            require_invitation_email_match_fn=lambda **_kwargs: None,
            can_use_local_bootstrap_fallback_fn=lambda **_kwargs: True,
            register_local_bootstrap_password_fn=lambda **kwargs: registered.append((kwargs["email"], kwargs["password"])),
            build_local_bootstrap_session_fn=lambda **kwargs: {
                "authorized": True,
                "email": kwargs["email"],
                "display_name": kwargs["display_name"],
                "message": kwargs["message"],
            },
            auth_request_fn=lambda *_args, **_kwargs: None,
            is_existing_auth_user_error_fn=lambda _message: False,
            sign_in_with_password_fn=lambda **_kwargs: {},
            ensure_bootstrap_local_user_fn=lambda **_kwargs: None,
            ensure_member_local_user_fn=lambda **_kwargs: None,
            finalize_session_payload_fn=lambda payload: payload,
            current_time_fn=lambda: 100,
            error_cls=AuthRuntimeError,
            local_bootstrap_sign_up_message="bootstrap registered",
        )

        self.assertTrue(payload["authorized"])
        self.assertEqual(registered, [("bootstrap@example.com", "password-123")])
        self.assertEqual(payload["message"], "bootstrap registered")

    def test_send_password_reset_email_returns_local_bootstrap_message_for_local_fallback(self) -> None:
        auth_request = mock.Mock()

        payload = orchestration.send_password_reset_email(
            email="bootstrap@example.com",
            request_host="127.0.0.1",
            ensure_auth_enabled=lambda: None,
            normalize_email_fn=lambda value: str(value).strip().lower(),
            can_use_local_bootstrap_fallback_fn=lambda **_kwargs: True,
            auth_request_fn=auth_request,
            error_cls=AuthRuntimeError,
            local_bootstrap_reset_message="reset locally",
            password_reset_sent_message="unused",
        )

        self.assertEqual(payload, {"message": "reset locally"})
        auth_request.assert_not_called()

    def test_ensure_fresh_session_payload_clears_cookie_when_refresh_token_missing(self) -> None:
        cleared: list[bool] = []
        response = Response()

        with self.assertRaises(AuthRuntimeError) as ctx:
            orchestration.ensure_fresh_session_payload(
                payload={"access_expires_at": 1, "refresh_token": ""},
                response=response,
                ensure_auth_enabled=lambda: None,
                now=100,
                grace_seconds=60,
                refresh_auth_session_fn=lambda *_args, **_kwargs: None,
                clear_auth_session_cookie_fn=lambda _response: cleared.append(True),
                set_auth_session_cookie_fn=lambda *_args, **_kwargs: None,
                error_cls=AuthRuntimeError,
                logger=mock.Mock(),
                session_refresh_timeout_seconds_fn=lambda: 30.0,
            )

        self.assertEqual(ctx.exception.code, "auth_required")
        self.assertEqual(cleared, [True])

    def test_build_session_response_returns_logged_out_payload_when_refresh_fails(self) -> None:
        cleared: list[bool] = []
        response = Response()

        session = orchestration.build_session_response(
            payload={
                "authorized": True,
                "email": "member@example.com",
                "refresh_token": "refresh-token",
                "access_expires_at": 1,
            },
            response=response,
            now=100,
            grace_seconds=60,
            refresh_auth_session_fn=mock.Mock(
                side_effect=AuthRuntimeError("timeout", status_code=503, code="auth_upstream_error")
            ),
            clear_auth_session_cookie_fn=lambda _response: cleared.append(True),
            set_auth_session_cookie_fn=lambda *_args, **_kwargs: None,
            build_auth_status_response_fn=lambda: {
                "enabled": True,
                "authenticated": False,
                "authorized": False,
                "message": "",
                "user": None,
            },
            build_session_response_payload_fn=lambda payload: {
                "authenticated": True,
                "authorized": bool(payload.get("authorized")),
                "message": str(payload.get("message") or ""),
                "user": {"email": payload.get("email")},
            },
            error_cls=AuthRuntimeError,
            logger=mock.Mock(),
            session_refresh_timeout_seconds_fn=lambda: 5.0,
            refresh_failure_message="session expired",
        )

        self.assertFalse(session["authenticated"])
        self.assertEqual(session["message"], "session expired")
        self.assertEqual(cleared, [True])

    def test_refresh_auth_session_finalizes_refreshed_tokens(self) -> None:
        finalized = orchestration.refresh_auth_session(
            "refresh-token",
            timeout_seconds=12.0,
            auth_request_fn=lambda *args, **kwargs: {
                "args": args,
                "kwargs": kwargs,
                "user": {"id": "auth-user-id", "email": "member@example.com"},
            },
            finalize_session_payload_fn=lambda payload: {
                "called_with": payload,
                "authorized": True,
            },
        )

        self.assertTrue(finalized["authorized"])
        self.assertEqual(finalized["called_with"]["kwargs"]["payload"], {"refresh_token": "refresh-token"})
        self.assertEqual(finalized["called_with"]["kwargs"]["timeout_seconds"], 12.0)

    def test_update_console_user_profile_uses_local_bootstrap_update_path(self) -> None:
        registered: list[str] = []
        updated_profiles: list[str] = []
        verified_passwords: list[str] = []
        auth_request = mock.Mock()

        updated = orchestration.update_console_user_profile(
            session_payload={
                "auth_user_id": "auth-user-id",
                "email": "bootstrap@example.com",
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 600,
                "auth_provider": "local_bootstrap",
            },
            display_name="Bootstrap User",
            mobile_phone="010-1234-5678",
            office_phone="02-1234-5678",
            current_password="current-password",
            password="new-password-123",
            invite_token="",
            ensure_auth_enabled=lambda: None,
            normalize_email_fn=lambda value: str(value).strip().lower(),
            verify_local_bootstrap_password_fn=lambda **kwargs: verified_passwords.append(kwargs["password"]) or True,
            can_use_invite_password_setup_fn=lambda **_kwargs: False,
            register_local_bootstrap_password_fn=lambda **kwargs: registered.append(kwargs["password"]),
            update_local_user_profile_fn=lambda **kwargs: updated_profiles.append(kwargs["display_name"]) or kwargs,
            build_local_bootstrap_session_fn=lambda **kwargs: {
                "display_name": kwargs["display_name"],
                "auth_provider": "local_bootstrap",
            },
            verify_password_fn=lambda **_kwargs: None,
            auth_request_fn=auth_request,
            finalize_session_payload_fn=lambda payload: payload,
            current_time_fn=lambda: 100,
            error_cls=AuthRuntimeError,
        )

        self.assertEqual(updated["display_name"], "Bootstrap User")
        self.assertEqual(verified_passwords, ["current-password"])
        self.assertEqual(registered, ["new-password-123"])
        self.assertEqual(updated_profiles, ["Bootstrap User"])
        auth_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
