from __future__ import annotations

import os
import unittest
from unittest import mock

from backend.api import auth_runtime


class AuthRuntimeLocalBootstrapTests(unittest.TestCase):
    def test_local_bootstrap_session_reuses_existing_profile_id_for_same_email(self) -> None:
        existing_id = "11111111-1111-1111-1111-111111111111"
        with mock.patch.object(
            auth_runtime,
            "_get_user_profile",
            return_value={"id": existing_id, "email": "yhm8029@gmail.com"},
        ), mock.patch.object(
            auth_runtime,
            "_get_local_user",
            return_value=None,
        ), mock.patch.object(
            auth_runtime,
            "_ensure_bootstrap_local_user",
            return_value={
                "id": existing_id,
                "organization_id": "22222222-2222-2222-2222-222222222222",
                "organization_name": "Internal Operations",
                "display_name": "운영자",
                "status": "active",
                "account_status": "active",
                "membership_status": "active",
            },
        ) as ensure_bootstrap:
            payload = auth_runtime._build_local_bootstrap_session(email="yhm8029@gmail.com", display_name="운영자")

        self.assertEqual(payload["auth_user_id"], existing_id)
        ensure_bootstrap.assert_called_once()
        self.assertEqual(ensure_bootstrap.call_args.kwargs["auth_user_id"], existing_id)

    def test_sign_in_uses_local_bootstrap_before_upstream_auth(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            with mock.patch.object(auth_runtime, "_auth_request") as auth_request, mock.patch.object(
                auth_runtime,
                "_has_local_bootstrap_password",
                return_value=True,
            ), mock.patch.object(
                auth_runtime,
                "_verify_local_bootstrap_password",
                return_value=True,
            ), mock.patch.object(
                auth_runtime,
                "_build_local_bootstrap_session",
                return_value={"authorized": True, "role": "platform_admin", "email": "yhm8029@gmail.com"},
            ) as build_local:
                payload = auth_runtime.sign_in_with_password(
                    email="yhm8029@gmail.com",
                    password="secret-password",
                    request_host="127.0.0.1",
                )

        self.assertTrue(payload["authorized"])
        auth_request.assert_not_called()
        build_local.assert_called_once()

    def test_sign_up_uses_local_bootstrap_before_upstream_auth(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            with mock.patch.object(auth_runtime, "_auth_request") as auth_request, mock.patch.object(
                auth_runtime,
                "_register_local_bootstrap_password",
            ) as register_local, mock.patch.object(
                auth_runtime,
                "_build_local_bootstrap_session",
                return_value={"authorized": True, "role": "platform_admin", "email": "yhm8029@gmail.com"},
            ) as build_local:
                payload = auth_runtime.sign_up_console_user(
                    email="yhm8029@gmail.com",
                    password="secret-password",
                    display_name="운영자",
                    request_host="127.0.0.1",
                )

        self.assertTrue(payload["authorized"])
        auth_request.assert_not_called()
        register_local.assert_called_once()
        build_local.assert_called_once()

    def test_password_reset_returns_local_bootstrap_guidance_on_localhost(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            result = auth_runtime.send_password_reset_email(
                email="yhm8029@gmail.com",
                request_host="127.0.0.1",
            )

        self.assertIn("최초 운영자 등록", result["message"])
