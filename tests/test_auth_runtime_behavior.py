from __future__ import annotations

import os
import time
import unittest
from types import SimpleNamespace
from unittest import mock
from uuid import UUID

from starlette.background import BackgroundTasks
from starlette.responses import Response
from starlette.requests import Request

from backend.api import auth_runtime
from backend.api import app as auth_app


class AuthRuntimeFacadeTests(unittest.TestCase):
    def test_auth_runtime_does_not_export_legacy_orchestration_symbols(self) -> None:
        for name in (
            "_legacy_sign_in_with_password_inline",
            "_legacy_sign_up_console_user_inline",
            "_legacy_send_password_reset_email_inline",
            "_legacy_ensure_fresh_session_payload_inline",
            "_legacy_update_console_user_profile_inline",
            "_legacy_build_session_response_inline",
            "_legacy_refresh_auth_session_inline",
        ):
            self.assertFalse(hasattr(auth_runtime, name), name)

    def test_sign_in_with_password_delegates_to_orchestration_backend(self) -> None:
        with (
            mock.patch.object(auth_runtime, "_sign_in_with_password_impl", return_value={"authorized": True}, create=True) as helper,
            mock.patch.object(auth_runtime, "_ensure_auth_enabled") as ensure_auth_enabled,
        ):
            payload = auth_runtime.sign_in_with_password(email="member@example.com", password="password-123")

        self.assertTrue(payload["authorized"])
        ensure_auth_enabled.assert_not_called()
        helper.assert_called_once()
        self.assertEqual(helper.call_args.kwargs["email"], "member@example.com")
        self.assertIs(helper.call_args.kwargs["ensure_auth_enabled"], ensure_auth_enabled)
        self.assertIs(helper.call_args.kwargs["normalize_email_fn"], auth_runtime._normalize_email)

    def test_build_session_response_delegates_to_orchestration_backend(self) -> None:
        request = Request({"type": "http", "method": "GET", "path": "/api/auth/session", "headers": []})
        response = Response()

        with (
            mock.patch.object(auth_runtime, "read_signed_session_payload", return_value={"authorized": True}) as read_payload,
            mock.patch.object(
                auth_runtime,
                "_build_session_response_impl",
                return_value={"authenticated": True},
                create=True,
            ) as helper,
        ):
            session = auth_runtime.build_session_response(request, response)

        self.assertTrue(session["authenticated"])
        read_payload.assert_called_once_with(request)
        helper.assert_called_once()
        self.assertEqual(helper.call_args.kwargs["payload"], {"authorized": True})
        self.assertIs(helper.call_args.kwargs["build_auth_status_response_fn"], auth_runtime.build_auth_status_response)

    def test_build_session_response_payload_does_not_expose_platform_admin_account_creation_flag(self) -> None:
        payload = auth_runtime.build_session_response_payload(
            {
                "authorized": True,
                "authenticated": True,
                "role": "platform_admin",
                "email": "ops@example.com",
            }
        )

        self.assertNotIn("platform_admin_account_creation_enabled", payload)

    def test_create_platform_admin_account_delegates_to_backend_helper(self) -> None:
        with mock.patch.object(
            auth_runtime,
            "_create_platform_admin_account_impl",
            return_value={"id": "user-1", "email": "member@example.com"},
            create=True,
        ) as helper:
            item = auth_runtime.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="platform_admin",
                organization_id="org-1",
                email="member@example.com",
                password="TempPass123!",
                display_name="Member",
                role="org_member",
            )

        self.assertEqual(item, {"id": "user-1", "email": "member@example.com"})
        helper.assert_called_once()
        self.assertEqual(helper.call_args.kwargs["actor_user_id"], "admin-1")
        self.assertEqual(helper.call_args.kwargs["actor_role"], "platform_admin")
        self.assertIs(helper.call_args.kwargs["create_auth_user_fn"], auth_runtime._create_supabase_auth_user)
        self.assertIs(helper.call_args.kwargs["list_local_users_fn"], auth_runtime.list_local_users)
        self.assertIs(helper.call_args.kwargs["ensure_user_profile_fn"], auth_runtime._ensure_user_profile)
        self.assertIs(helper.call_args.kwargs["ensure_membership_fn"], auth_runtime._ensure_membership)
        self.assertIs(helper.call_args.kwargs["append_audit_log_fn"], auth_runtime._append_audit_log)

    def test_cleanup_local_account_is_noop_when_local_row_is_missing(self) -> None:
        with (
            mock.patch.object(auth_runtime, "_get_local_user", return_value=None),
            mock.patch.object(auth_runtime, "_rest_delete_rows") as delete_rows_mock,
        ):
            auth_runtime._cleanup_local_account(organization_id="org-1", user_id="user-1", email="member@example.com")

        delete_rows_mock.assert_not_called()

    def test_create_platform_admin_account_preserves_root_error_when_cleanup_is_noop(self) -> None:
        with (
            mock.patch.object(auth_runtime, "_get_local_user", return_value=None),
            mock.patch.object(auth_runtime, "_get_user_profile", return_value=None),
            mock.patch.object(auth_runtime, "_create_supabase_auth_user", return_value={"id": "user-1"}),
            mock.patch.object(auth_runtime, "list_local_users", return_value=[]),
            mock.patch.object(auth_runtime, "_delete_supabase_auth_user"),
            mock.patch.object(
                auth_runtime,
                "_ensure_user_profile",
                side_effect=auth_runtime.AuthRuntimeError("profile write failed", status_code=500, code="profile_write_failed"),
            ),
            mock.patch.object(auth_runtime, "_ensure_membership"),
            mock.patch.object(auth_runtime, "_append_audit_log"),
        ):
            with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                auth_runtime.create_platform_admin_account(
                    actor_user_id="admin-1",
                    actor_role="platform_admin",
                    organization_id="org-1",
                    email="member@example.com",
                    password="TempPass123!",
                    display_name="Member",
                    role="org_member",
                )

        self.assertEqual(ctx.exception.code, "profile_write_failed")

    def test_ensure_user_profile_accepts_platform_admin_account_metadata(self) -> None:
        with mock.patch.object(auth_runtime, "_ensure_user_profile_impl") as helper:
            auth_runtime._ensure_user_profile(
                user_id="user-1",
                email="member@example.com",
                display_name="Member",
                account_status="active",
                global_role="",
                created_by_user_id="admin-1",
                password_setup_mode="admin_set",
                force_password_change=False,
            )

        helper.assert_called_once()
        self.assertEqual(helper.call_args.kwargs["created_by_user_id"], "admin-1")
        self.assertEqual(helper.call_args.kwargs["password_setup_mode"], "admin_set")
        self.assertFalse(helper.call_args.kwargs["force_password_change"])

    def test_reset_platform_admin_account_password_records_audit_log(self) -> None:
        with (
            mock.patch.object(auth_runtime, "_auth_request", return_value={}) as auth_request_mock,
            mock.patch.object(auth_runtime, "_append_audit_log") as append_audit_log_mock,
        ):
            payload = auth_runtime.reset_platform_admin_account_password(
                actor_user_id="admin-1",
                actor_role="platform_admin",
                organization_id="org-1",
                user_id="user-1",
                email="member@example.com",
                password="TempPass123!",
            )

        self.assertEqual(payload["message"], "password reset scheduled")
        auth_request_mock.assert_called_once_with(
            "PUT",
            "/admin/users/user-1",
            payload={"password": "TempPass123!"},
            use_service_authorization=True,
        )
        append_audit_log_mock.assert_called_once()
        self.assertEqual(append_audit_log_mock.call_args.kwargs["event_type"], "account_password_reset")
        self.assertEqual(append_audit_log_mock.call_args.kwargs["target_type"], "user_profile")
        self.assertEqual(append_audit_log_mock.call_args.kwargs["target_id"], "user-1")

    def test_update_console_user_profile_delegates_to_orchestration_backend(self) -> None:
        session_payload = {
            "auth_user_id": "auth-user-id",
            "email": "member@example.com",
            "access_token": "access-token",
            "access_expires_at": int(time.time()) + 3600,
        }

        with mock.patch.object(
            auth_runtime,
            "_update_console_user_profile_impl",
            return_value={"display_name": "New Name"},
            create=True,
        ) as helper:
            updated = auth_runtime.update_console_user_profile(
                session_payload=session_payload,
                display_name="New Name",
                current_password="current-password",
                password="new-password-123",
            )

        self.assertEqual(updated["display_name"], "New Name")
        helper.assert_called_once()
        self.assertEqual(helper.call_args.kwargs["session_payload"], session_payload)
        self.assertIs(helper.call_args.kwargs["verify_password_fn"], auth_runtime._verify_password)
        self.assertIs(helper.call_args.kwargs["build_local_bootstrap_session_fn"], auth_runtime._build_local_bootstrap_session)

    def test_record_login_audit_log_uses_request_metadata(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/sign-in",
                "headers": [
                    (b"host", b"example.test"),
                    (b"user-agent", b"pytest-agent/1.0"),
                    (b"x-forwarded-for", b"203.0.113.9, 198.51.100.7"),
                ],
                "client": ("127.0.0.1", 4321),
            }
        )
        session_payload = {
            "authorized": True,
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "local_user_id": "33333333-3333-3333-3333-333333333333",
            "auth_user_id": "22222222-2222-2222-2222-222222222222",
            "email": "member@example.com",
            "role": "org_admin",
        }

        with mock.patch.object(auth_runtime, "get_login_audit_log_repository", create=True) as get_repo_mock:
            repository = mock.Mock()
            repository.create_log.return_value = {
                "id": "33333333-3333-3333-3333-333333333333",
                "organization_id": "11111111-1111-1111-1111-111111111111",
                "user_id": "22222222-2222-2222-2222-222222222222",
                "user_email": "member@example.com",
                "user_role": "org_admin",
                "ip_address": "203.0.113.9",
                "user_agent": "pytest-agent/1.0",
                "created_at": "2026-04-01T00:00:00Z",
            }
            get_repo_mock.return_value = repository

            auth_runtime.record_login_audit_log(request=request, session_payload=session_payload)

        get_repo_mock.assert_called_once()
        repository.create_log.assert_called_once_with(
            organization_id=UUID("11111111-1111-1111-1111-111111111111"),
            user_id=UUID("33333333-3333-3333-3333-333333333333"),
            user_email="member@example.com",
            user_role="org_admin",
            ip_address="203.0.113.9",
            user_agent="pytest-agent/1.0",
        )

    def test_record_login_audit_log_ignores_repository_failures(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/sign-in",
                "headers": [],
                "client": ("127.0.0.1", 1234),
            }
        )
        session_payload = {
            "authorized": True,
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "local_user_id": "33333333-3333-3333-3333-333333333333",
            "auth_user_id": "22222222-2222-2222-2222-222222222222",
            "email": "member@example.com",
            "role": "org_admin",
        }

        with (
            mock.patch.object(auth_runtime, "get_login_audit_log_repository", create=True) as get_repo_mock,
            mock.patch.object(auth_runtime.logger, "warning") as warning_mock,
        ):
            repository = mock.Mock()
            repository.create_log.side_effect = RuntimeError("audit failed")
            get_repo_mock.return_value = repository

            auth_runtime.record_login_audit_log(request=request, session_payload=session_payload)

        warning_mock.assert_called_once()


class AuthRuntimeTests(unittest.TestCase):
    def test_list_local_users_overview_pushes_active_filters_into_query(self) -> None:
        captured: dict[str, object] = {}

        def _fake_request_json(**kwargs):
            captured["query"] = list(kwargs.get("query") or [])
            return ([
                {
                    "membership_id": "11111111-1111-1111-1111-111111111111",
                    "organization_id": "22222222-2222-2222-2222-222222222222",
                    "user_id": "33333333-3333-3333-3333-333333333333",
                    "email": "member@example.com",
                    "display_name": "Member",
                    "mobile_phone": "010-1234-5678",
                    "office_phone": "02-1234-5678",
                    "account_status": "active",
                    "membership_role": "org_member",
                    "membership_status": "active",
                    "team_name": "Sales",
                    "job_title": "Lead",
                }
            ], {})

        with mock.patch.object(auth_runtime, "request_json", side_effect=_fake_request_json), mock.patch.object(
            auth_runtime,
            "_rest_base_url",
            return_value="https://example.supabase.co/rest/v1",
        ), mock.patch.object(auth_runtime, "_service_api_key", return_value="service-key"), mock.patch.object(
            auth_runtime, "_timeout_seconds", return_value=5.0
        ):
            rows = auth_runtime.list_local_users_overview(
                organization_id="22222222-2222-2222-2222-222222222222"
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "active")
        query = dict(captured.get("query") or [])
        self.assertEqual(query.get("organization_id"), "eq.22222222-2222-2222-2222-222222222222")
        self.assertEqual(query.get("membership_status"), "eq.active")
        self.assertEqual(query.get("account_status"), "eq.active")

    def test_list_local_users_overview_falls_back_to_legacy_users_when_relation_missing(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "request_json",
                side_effect=auth_runtime.AuthRuntimeError("relation organization_member_profiles does not exist"),
            ) as request_json_mock,
            mock.patch.object(auth_runtime, "_rest_base_url", return_value="https://example.supabase.co/rest/v1"),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=5.0),
            mock.patch.object(auth_runtime, "_is_missing_relation_error", return_value=True),
            mock.patch.object(
                auth_runtime,
                "list_local_users",
                return_value=[{"id": "legacy-user", "status": "active"}],
            ) as list_local_users_mock,
        ):
            rows = auth_runtime.list_local_users_overview(
                organization_id="22222222-2222-2222-2222-222222222222"
            )

        self.assertEqual(rows, [{"id": "legacy-user", "status": "active"}])
        self.assertEqual(request_json_mock.call_count, 1)
        list_local_users_mock.assert_called_once_with(
            organization_id="22222222-2222-2222-2222-222222222222",
            include_inactive=False,
        )

    def test_query_local_user_rows_retries_legacy_users_without_status_column(self) -> None:
        def _fake_request_json(**kwargs):
            path = kwargs["path"]
            query = list(kwargs.get("query") or [])
            select_columns = dict(query).get("select")
            if path == "/organization_member_profiles":
                raise auth_runtime.AuthRuntimeError("relation organization_member_profiles does not exist")
            if path == "/users" and select_columns == auth_runtime.LOCAL_USER_SELECT_COLUMNS:
                raise auth_runtime.AuthRuntimeError('column "status" does not exist')
            return (
                [
                    {
                        "id": "legacy-user",
                        "organization_id": "org-123",
                        "email": "member@example.com",
                        "display_name": "Member",
                        "role": "admin",
                    }
                ],
                {},
            )

        with (
            mock.patch.object(auth_runtime, "request_json", side_effect=_fake_request_json),
            mock.patch.object(auth_runtime, "_rest_base_url", return_value="https://example.supabase.co/rest/v1"),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=5.0),
            mock.patch.object(auth_runtime, "_is_missing_relation_error", return_value=True),
            mock.patch.object(auth_runtime, "_get_organization", return_value={"name": "Internal Operations"}),
        ):
            rows = auth_runtime._query_local_user_rows(
                filters=[("organization_id", "eq.org-123"), ("order", "display_name.asc")]
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["organization_name"], "Internal Operations")
        self.assertEqual(rows[0]["membership_status"], "active")

    def test_normalize_local_user_row_prefers_account_inactive_over_membership_active(self) -> None:
        item = auth_runtime._normalize_local_user_row(
            {
                "membership_id": "membership-1",
                "organization_id": "org-123",
                "user_id": "user-123",
                "email": "member@example.com",
                "display_name": "Member",
                "account_status": "inactive",
                "global_role": "",
                "membership_role": "org_member",
                "membership_status": "active",
            }
        )

        self.assertEqual(item["status"], "inactive")
        self.assertEqual(item["account_status"], "inactive")
        self.assertEqual(item["membership_status"], "active")

    def test_get_organization_retries_legacy_select_when_plan_columns_are_missing(self) -> None:
        def _fake_request_json(**kwargs):
            query = dict(kwargs.get("query") or [])
            if query.get("select") == auth_runtime.ORGANIZATION_SELECT_COLUMNS:
                raise auth_runtime.AuthRuntimeError('column "plan_code" does not exist')
            return (
                [
                    {
                        "id": "org-123",
                        "name": "Internal Operations",
                        "slug": "internal-ops",
                    }
                ],
                {},
            )

        with (
            mock.patch.object(auth_runtime, "request_json", side_effect=_fake_request_json),
            mock.patch.object(auth_runtime, "_rest_base_url", return_value="https://example.supabase.co/rest/v1"),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=5.0),
        ):
            item = auth_runtime._get_organization("org-123")

        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item["plan_code"], auth_runtime.DEFAULT_ORGANIZATION_PLAN_CODE)
        self.assertEqual(
            item["active_user_limit"],
            auth_runtime.ORGANIZATION_PLAN_LIMITS[auth_runtime.DEFAULT_ORGANIZATION_PLAN_CODE]["active_user_limit"],
        )

    def test_auth_disabled_without_supabase_configuration(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "",
                "LOCAL_APP_DISABLE_LOGIN": "",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "",
                "SUPABASE_URL": "",
                "SUPABASE_SECRET_KEY": "",
                "SUPABASE_SERVICE_ROLE_KEY": "",
                "SUPABASE_SECRET": "",
            },
            clear=False,
        ):
            self.assertFalse(auth_runtime.auth_is_enabled())

    def test_local_app_disable_login_overrides_supabase_auth_configuration(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LOCAL_APP_DISABLE_LOGIN": "1",
                "PHASE2_AUTH_ENABLED": "1",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "admin@example.com",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            self.assertFalse(auth_runtime.auth_is_enabled())

    def test_explicit_phase2_auth_disabled_overrides_bootstrap_email(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LOCAL_APP_DISABLE_LOGIN": "",
                "PHASE2_AUTH_ENABLED": "0",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "admin@example.com",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            self.assertFalse(auth_runtime.auth_is_enabled())

    def test_explicit_phase2_auth_enabled_still_requires_supabase_configuration(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LOCAL_APP_DISABLE_LOGIN": "",
                "PHASE2_AUTH_ENABLED": "1",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "admin@example.com",
                "SUPABASE_URL": "",
                "SUPABASE_SECRET_KEY": "",
                "SUPABASE_SERVICE_ROLE_KEY": "",
                "SUPABASE_SECRET": "",
            },
            clear=False,
        ):
            self.assertFalse(auth_runtime.auth_is_enabled())

    def test_public_api_key_requires_anon_or_publishable_key(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "SUPABASE_ANON_KEY": "",
                "SUPABASE_PUBLISHABLE_KEY": "",
                "SUPABASE_SECRET_KEY": "sb_secret_example",
            },
            clear=False,
        ):
            with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                auth_runtime._public_api_key()

        self.assertEqual(ctx.exception.code, "auth_config_error")

    def test_sign_in_uses_local_bootstrap_fallback_when_auth_upstream_times_out(self) -> None:
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
            with mock.patch.object(
                auth_runtime,
                "_auth_request",
                side_effect=auth_runtime.AuthRuntimeError("timeout", status_code=503, code="auth_upstream_error"),
            ), mock.patch.object(
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
            ) as build_local, mock.patch.object(
                auth_runtime,
                "_list_pending_invitations_by_email",
                return_value=[],
            ):
                payload = auth_runtime.sign_in_with_password(
                    email="yhm8029@gmail.com",
                    password="secret-password",
                    request_host="127.0.0.1",
                )

        self.assertTrue(payload["authorized"])
        build_local.assert_called_once()

    def test_bootstrap_sign_up_uses_local_fallback_when_auth_upstream_times_out(self) -> None:
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
            with mock.patch.object(
                auth_runtime,
                "_auth_request",
                side_effect=auth_runtime.AuthRuntimeError("timeout", status_code=503, code="auth_upstream_error"),
            ), mock.patch.object(
                auth_runtime,
                "_register_local_bootstrap_password",
            ) as register_local, mock.patch.object(
                auth_runtime,
                "_build_local_bootstrap_session",
                return_value={"authorized": True, "role": "platform_admin", "email": "yhm8029@gmail.com"},
            ) as build_local, mock.patch.object(
                auth_runtime,
                "_list_pending_invitations_by_email",
                return_value=[],
            ):
                payload = auth_runtime.sign_up_console_user(
                    email="yhm8029@gmail.com",
                    password="secret-password",
                    display_name="운영자",
                    request_host="127.0.0.1",
                )

        self.assertTrue(payload["authorized"])
        register_local.assert_called_once()
        build_local.assert_called_once()

    def test_read_access_token_expires_in_uses_backend_helper(self) -> None:
        with mock.patch.object(auth_runtime, "_read_access_token_expires_in_impl", return_value=321) as helper:
            expires_in = auth_runtime._read_access_token_expires_in("header.payload.signature")

        self.assertEqual(expires_in, 321)
        helper.assert_called_once_with(
            "header.payload.signature",
            urlsafe_b64decode=auth_runtime._urlsafe_b64decode,
        )

    def test_finalize_session_payload_sets_profile_checked_at(self) -> None:
        token_payload = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "user": {
                "id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "email": "member@example.com",
                "user_metadata": {"display_name": "Member"},
            },
        }

        with (
            mock.patch.object(auth_runtime, "_resolve_display_name", return_value="Member"),
            mock.patch.object(
                auth_runtime,
                "_resolve_application_profile",
                return_value={
                    "role": "org_member",
                    "authorized": True,
                    "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    "organization_name": "Internal Operations",
                    "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                    "membership_id": "28e7fe7b-f72e-44e5-afed-a4630f26e68d",
                    "status": "active",
                    "account_status": "active",
                    "membership_status": "active",
                    "mobile_phone": "",
                    "office_phone": "",
                    "message": "",
                },
            ),
            mock.patch.object(auth_runtime.time, "time", return_value=1_700_000_000),
        ):
            payload = auth_runtime._finalize_session_payload(token_payload)

        self.assertEqual(payload["profile_checked_at"], 1_700_000_000)

    def test_decode_signed_payload_maps_backend_value_error_to_auth_invalid(self) -> None:
        with mock.patch.object(
            auth_runtime,
            "_decode_signed_payload_impl",
            side_effect=ValueError("Invalid auth session signature"),
        ):
            with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                auth_runtime._decode_signed_payload("broken")

        self.assertEqual(ctx.exception.code, "auth_invalid")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.message, "Invalid auth session signature")

    def test_signed_cookie_round_trip_builds_auth_context(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "yhm8029@gmail.com",
                "display_name": "HYUNMO",
                "role": "platform_admin",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 4102444800,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/dashboard/summary",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )

            with mock.patch.object(
                auth_runtime,
                "_get_local_user",
                return_value={
                    "id": payload["local_user_id"],
                    "organization_id": payload["organization_id"],
                    "email": payload["email"],
                    "display_name": payload["display_name"],
                    "role": "admin",
                    "status": "active",
                    "organization_name": payload["organization_name"],
                },
            ):
                context = auth_runtime.read_auth_context(request)

            self.assertIsNotNone(context)
            assert context is not None
            self.assertEqual(str(context.auth_user_id), payload["auth_user_id"])
            self.assertEqual(str(context.local_user_id), payload["local_user_id"])
            self.assertEqual(context.email, "yhm8029@gmail.com")
            self.assertEqual(context.role, "platform_admin")
            self.assertTrue(context.authorized)

    def test_read_auth_context_rejects_inactive_local_user(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 4102444800,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/dashboard/summary",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )

            with mock.patch.object(
                auth_runtime,
                "_get_local_user",
                return_value={
                    "id": payload["local_user_id"],
                    "organization_id": payload["organization_id"],
                    "email": payload["email"],
                    "display_name": payload["display_name"],
                    "role": "member",
                    "status": "inactive",
                    "organization_name": payload["organization_name"],
                },
            ):
                context = auth_runtime.read_auth_context(request)

        self.assertIsNone(context)

    def test_read_auth_context_uses_signed_payload_without_local_lookup_when_profile_check_is_fresh(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "account_status": "active",
                "membership_status": "active",
                "profile_checked_at": int(time.time()),
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 4102444800,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/dashboard/summary",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )

            with mock.patch.object(auth_runtime, "_get_local_user", side_effect=AssertionError("local lookup should be skipped")):
                context = auth_runtime.read_auth_context(request)

        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.email, "member@example.com")
        self.assertEqual(context.role, "org_member")
        self.assertTrue(context.authorized)

    def test_read_auth_context_revalidates_local_user_when_profile_check_is_stale(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "account_status": "active",
                "membership_status": "active",
                "profile_checked_at": int(time.time()) - 3600,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 4102444800,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/dashboard/summary",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )

            with mock.patch.object(
                auth_runtime,
                "_get_local_user",
                return_value={
                    "id": payload["local_user_id"],
                    "organization_id": payload["organization_id"],
                    "email": payload["email"],
                    "display_name": payload["display_name"],
                    "role": "org_admin",
                    "status": "active",
                    "account_status": "active",
                    "membership_status": "active",
                    "organization_name": payload["organization_name"],
                },
            ) as get_local_user_mock:
                context = auth_runtime.read_auth_context(request)

        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.role, "org_admin")
        get_local_user_mock.assert_called_once()

    def test_read_auth_context_uses_authorization_bearer_when_cookie_is_missing(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/dashboard/summary",
                "headers": [(b"authorization", b"Bearer access-token")],
            }
        )

        with mock.patch.object(
            auth_runtime,
            "_auth_request",
            return_value={
                "id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "email": "member@example.com",
                "user_metadata": {"display_name": "Member"},
            },
        ) as auth_request_mock, mock.patch.object(
            auth_runtime,
            "_resolve_application_profile",
            return_value={
                "role": "org_admin",
                "authorized": True,
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "membership_id": "2c1d15d6-394f-42fc-a2d0-a263967f0cc1",
                "status": "active",
                "account_status": "active",
                "membership_status": "active",
                "message": "",
                "mobile_phone": "",
                "office_phone": "",
            },
        ), mock.patch.object(
            auth_runtime,
            "_read_access_token_expires_in",
            return_value=3600,
        ):
            context = auth_runtime.read_auth_context(request)

        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.email, "member@example.com")
        self.assertEqual(context.role, "org_admin")
        self.assertTrue(context.authorized)
        auth_request_mock.assert_called_once()

    def test_build_session_response_refreshes_expiring_cookie(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "yhm8029@gmail.com",
                "display_name": "HYUNMO",
                "role": "platform_admin",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 1,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/auth/session",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )
            response = Response()
            refreshed_payload = dict(payload)
            refreshed_payload["access_token"] = "refreshed-access-token"
            refreshed_payload["refresh_token"] = "refreshed-refresh-token"
            refreshed_payload["access_expires_at"] = 4102444800

            with mock.patch.object(auth_runtime, "_get_local_user", return_value=None), mock.patch.object(
                auth_runtime,
                "refresh_auth_session",
                return_value=refreshed_payload,
            ):
                session = auth_runtime.build_session_response(request, response)

            self.assertTrue(session["authenticated"])
            self.assertEqual(session["user"]["email"], "yhm8029@gmail.com")
            self.assertGreaterEqual(int(response.headers["set-cookie"].split("Max-Age=")[1].split(";", 1)[0]), 60 * 60 * 24 * 30 - 5)

    def test_build_session_response_clears_cookie_when_refresh_fails(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "yhm8029@gmail.com",
                "display_name": "HYUNMO",
                "role": "platform_admin",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 1,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/auth/session",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )
            response = Response()

            with mock.patch.object(
                auth_runtime,
                "refresh_auth_session",
                side_effect=auth_runtime.AuthRuntimeError("timeout", status_code=503, code="auth_upstream_error"),
            ):
                session = auth_runtime.build_session_response(request, response)

            self.assertFalse(session["authenticated"])
            self.assertEqual(session["message"], "세션이 만료되었습니다. 다시 로그인해 주세요.")
            self.assertIn("set-cookie", response.headers)
            self.assertIn("Max-Age=0", response.headers["set-cookie"])

    def test_ensure_fresh_session_payload_refreshes_expiring_cookie(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "yhm8029@gmail.com",
                "display_name": "HYUNMO",
                "role": "platform_admin",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 1,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/auth/profile",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )
            response = Response()
            refreshed_payload = dict(payload)
            refreshed_payload["access_token"] = "refreshed-access-token"
            refreshed_payload["refresh_token"] = "refreshed-refresh-token"
            refreshed_payload["access_expires_at"] = 4102444800

            with mock.patch.object(auth_runtime, "refresh_auth_session", return_value=refreshed_payload):
                resolved = auth_runtime.ensure_fresh_session_payload(request, response)

            self.assertEqual(resolved["access_token"], "refreshed-access-token")
            self.assertIn("set-cookie", response.headers)

    def test_ensure_fresh_session_payload_clears_cookie_when_refresh_fails(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "yhm8029@gmail.com",
            },
            clear=False,
        ):
            payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "yhm8029@gmail.com",
                "display_name": "HYUNMO",
                "role": "platform_admin",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": 1,
            }
            signed = auth_runtime._encode_signed_payload(payload)
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/auth/profile",
                    "headers": [(b"cookie", f"{auth_runtime.SESSION_COOKIE_NAME}={signed}".encode("utf-8"))],
                }
            )
            response = Response()

            with mock.patch.object(
                auth_runtime,
                "refresh_auth_session",
                side_effect=auth_runtime.AuthRuntimeError("timeout", status_code=503, code="auth_upstream_error"),
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.ensure_fresh_session_payload(request, response)

            self.assertEqual(ctx.exception.code, "auth_required")
            self.assertIn("set-cookie", response.headers)
            self.assertIn("Max-Age=0", response.headers["set-cookie"])

    def test_update_console_user_profile_updates_supabase_user_and_local_user(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
            },
            clear=False,
        ):
            session_payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "member@example.com",
                "display_name": "Old Name",
                "role": "org_member",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": int(time.time()) + 3600,
            }

            with (
                mock.patch.object(auth_runtime, "_require_invitation_email_match") as require_match_mock,
                mock.patch.object(
                    auth_runtime,
                    "_auth_request",
                    return_value={
                        "id": session_payload["auth_user_id"],
                        "email": session_payload["email"],
                        "user_metadata": {"display_name": "New Name"},
                    },
                ) as auth_request_mock,
                mock.patch.object(auth_runtime, "_verify_password") as verify_password_mock,
                mock.patch.object(auth_runtime, "_update_local_user_profile") as update_local_user_mock,
                mock.patch.object(
                    auth_runtime,
                    "_finalize_session_payload",
                    return_value={**session_payload, "display_name": "New Name"},
                ) as finalize_mock,
            ):
                updated = auth_runtime.update_console_user_profile(
                    session_payload=session_payload,
                    display_name="New Name",
                    current_password="current-password-123",
                    password="new-password-123",
                )

            self.assertEqual(updated["display_name"], "New Name")
            verify_password_mock.assert_called_once_with(
                email=session_payload["email"],
                password="current-password-123",
            )
            auth_request_mock.assert_called_once_with(
                "PUT",
                "/user",
                payload={"password": "new-password-123", "data": {"display_name": "New Name"}},
                access_token="access-token",
                use_service_authorization=False,
            )
            update_local_user_mock.assert_called_once_with(
                user_id=session_payload["auth_user_id"],
                email=session_payload["email"],
                display_name="New Name",
                mobile_phone="",
                office_phone="",
            )
            finalize_mock.assert_called_once()

    def test_sign_in_with_password_accepts_invitation_token(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "SUPABASE_ANON_KEY": "anon-key",
            },
            clear=False,
        ):
            with (
                mock.patch.object(auth_runtime, "_require_invitation_email_match") as require_match_mock,
                mock.patch.object(
                    auth_runtime,
                    "_auth_request",
                    return_value={
                        "access_token": "access",
                        "refresh_token": "refresh",
                        "expires_in": 3600,
                        "user": {
                            "id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                            "email": "member@example.com",
                            "user_metadata": {"display_name": "Member"},
                        },
                    },
                ),
                mock.patch.object(
                    auth_runtime,
                    "_finalize_session_payload",
                    return_value={
                        "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                        "email": "member@example.com",
                        "display_name": "Member",
                        "authorized": False,
                        "access_token": "access",
                        "refresh_token": "refresh",
                        "access_expires_at": int(time.time()) + 3600,
                    },
                ),
                mock.patch.object(
                    auth_runtime,
                    "accept_invitation_for_session_payload",
                    return_value={"authorized": True},
                ) as accept_mock,
            ):
                payload = auth_runtime.sign_in_with_password(
                    email="member@example.com",
                    password="password-123",
                    invite_token="invite-token-123",
                )

        self.assertEqual(payload, {"authorized": True})
        require_match_mock.assert_called_once_with(
            invite_token="invite-token-123",
            email="member@example.com",
        )
        accept_mock.assert_called_once()

    def test_accept_invitation_for_session_payload_resolves_pending_invitation_by_email(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            session_payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "email": "member@example.com",
                "display_name": "Member",
                "access_token": "access",
                "refresh_token": "refresh",
                "access_expires_at": int(time.time()) + 3600,
            }
            with (
                mock.patch.object(auth_runtime, "_ensure_user_profile") as ensure_profile_mock,
                mock.patch.object(
                    auth_runtime,
                    "_list_pending_invitations_by_email",
                    return_value=[
                        {
                            "invite_token": "invite-token-123",
                            "accepted_user_id": "",
                        }
                    ],
                ) as list_pending_mock,
                mock.patch.object(
                    auth_runtime,
                    "_get_invitation_by_token",
                    return_value={
                        "invite_token": "invite-token-123",
                        "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                        "email": "member@example.com",
                        "status": "pending",
                        "accepted_user_id": "",
                    },
                ),
                mock.patch.object(auth_runtime, "_get_user_profile", return_value={"global_role": ""}),
                mock.patch.object(auth_runtime, "_get_membership_row", return_value=None),
                mock.patch.object(
                    auth_runtime,
                    "get_organization_plan_summary",
                    return_value={"active_user_limit_reached": False},
                ),
                mock.patch.object(
                    auth_runtime,
                    "request_json",
                    return_value=(
                        {
                            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                            "membership_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                            "invitation_id": "11111111-1111-1111-1111-111111111111",
                            "organization_name": "Internal Operations",
                        },
                        {},
                    ),
                ) as request_json_mock,
                mock.patch.object(auth_runtime, "_append_audit_log") as append_audit_mock,
                mock.patch.object(auth_runtime, "_touch_last_login") as touch_last_login_mock,
                mock.patch.object(
                    auth_runtime,
                    "_finalize_session_payload",
                    return_value={"authorized": True},
                ) as finalize_mock,
            ):
                resolved = auth_runtime.accept_invitation_for_session_payload(
                    session_payload=session_payload,
                    invite_token="",
                )

        self.assertEqual(resolved, {"authorized": True})
        ensure_profile_mock.assert_called_once()
        list_pending_mock.assert_called_once_with(email="member@example.com")
        request_json_mock.assert_called_once()
        self.assertEqual(request_json_mock.call_args.kwargs["payload"]["p_invite_token"], "invite-token-123")
        append_audit_mock.assert_called_once()
        touch_last_login_mock.assert_called_once_with(auth_user_id=session_payload["auth_user_id"])
        finalize_mock.assert_called_once()

    def test_accept_invitation_for_session_payload_rejects_ambiguous_pending_invitations(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            session_payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "email": "member@example.com",
                "display_name": "Member",
                "access_token": "access",
                "refresh_token": "refresh",
                "access_expires_at": int(time.time()) + 3600,
            }
            with mock.patch.object(
                auth_runtime,
                "_list_pending_invitations_by_email",
                return_value=[
                    {"invite_token": "invite-1", "accepted_user_id": ""},
                    {"invite_token": "invite-2", "accepted_user_id": ""},
                ],
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.accept_invitation_for_session_payload(
                        session_payload=session_payload,
                        invite_token="",
                    )

        self.assertEqual(ctx.exception.code, "invite_ambiguous")

    def test_accept_invitation_for_session_payload_persists_expired_status_when_rpc_reports_expired(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            session_payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "email": "member@example.com",
                "display_name": "Member",
                "access_token": "access",
                "refresh_token": "refresh",
                "access_expires_at": int(time.time()) + 3600,
            }
            invitation = {
                "id": "11111111-1111-1111-1111-111111111111",
                "invite_token": "invite-token-123",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "email": "member@example.com",
                "status": "pending",
                "accepted_user_id": "",
            }
            with (
                mock.patch.object(auth_runtime, "_ensure_user_profile"),
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=invitation),
                mock.patch.object(auth_runtime, "_get_user_profile", return_value={"global_role": ""}),
                mock.patch.object(auth_runtime, "_get_membership_row", return_value=None),
                mock.patch.object(
                    auth_runtime,
                    "get_organization_plan_summary",
                    return_value={"active_user_limit_reached": False},
                ),
                mock.patch.object(
                    auth_runtime,
                    "request_json",
                    side_effect=auth_runtime.AuthRuntimeError("invitation has expired"),
                ),
                mock.patch.object(auth_runtime, "_persist_invitation_status") as persist_status_mock,
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.accept_invitation_for_session_payload(
                        session_payload=session_payload,
                        invite_token="invite-token-123",
                    )

        self.assertEqual(ctx.exception.code, "invite_expired")
        persist_status_mock.assert_called_once_with(
            invitation_id=invitation["id"],
            status="expired",
        )

    def test_accept_invitation_for_session_payload_rejects_replayed_accepted_invitation(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            session_payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "email": "member@example.com",
                "display_name": "Member",
                "access_token": "access",
                "refresh_token": "refresh",
                "access_expires_at": int(time.time()) + 3600,
            }
            invitation = {
                "id": "11111111-1111-1111-1111-111111111111",
                "invite_token": "invite-token-123",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "email": "member@example.com",
                "status": "accepted",
                "accepted_user_id": session_payload["auth_user_id"],
            }
            with (
                mock.patch.object(auth_runtime, "_ensure_user_profile"),
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=invitation),
                mock.patch.object(auth_runtime, "_get_user_profile", return_value={"global_role": ""}),
                mock.patch.object(auth_runtime, "_get_membership_row", return_value=None),
                mock.patch.object(
                    auth_runtime,
                    "get_organization_plan_summary",
                    return_value={"active_user_limit_reached": False},
                ),
                mock.patch.object(
                    auth_runtime,
                    "request_json",
                    side_effect=auth_runtime.AuthRuntimeError("invitation has already been accepted"),
                ),
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.accept_invitation_for_session_payload(
                        session_payload=session_payload,
                        invite_token="invite-token-123",
                    )

        self.assertEqual(ctx.exception.code, "invite_already_accepted")

    def test_sign_up_rejects_invite_email_mismatch_before_creating_user(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            with (
                mock.patch.object(
                    auth_runtime,
                    "_get_invitation_by_token",
                    return_value={
                        "invite_token": "invite-token-123",
                        "email": "invited@example.com",
                        "status": "pending",
                    },
                ),
                mock.patch.object(auth_runtime, "_auth_request") as auth_request_mock,
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.sign_up_console_user(
                        email="other@example.com",
                        password="password-123",
                        invite_token="invite-token-123",
                    )

        self.assertEqual(ctx.exception.code, "invite_email_mismatch")
        auth_request_mock.assert_not_called()

    def test_sign_up_requires_invite_for_non_bootstrap_email(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "bootstrap@example.com",
            },
            clear=False,
        ):
            with mock.patch.object(auth_runtime, "_auth_request") as auth_request_mock, mock.patch.object(
                auth_runtime,
                "_list_pending_invitations_by_email",
                return_value=[],
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.sign_up_console_user(
                        email="member@example.com",
                        password="password-123",
                    )

        self.assertEqual(ctx.exception.code, "invite_required")
        auth_request_mock.assert_not_called()

    def test_sign_up_resolves_pending_invitation_by_email_without_token(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "bootstrap@example.com",
            },
            clear=False,
        ):
            pending_invitation = {
                "invite_token": "invite-token-123",
                "email": "member@example.com",
                "status": "pending",
            }
            with (
                mock.patch.object(auth_runtime, "_list_pending_invitations_by_email", return_value=[pending_invitation]),
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=pending_invitation),
                mock.patch.object(auth_runtime, "_auth_request", return_value={"id": "auth-user-id"}),
                mock.patch.object(auth_runtime, "sign_in_with_password", return_value={"authorized": True}) as sign_in_mock,
                mock.patch.object(auth_runtime, "_ensure_member_local_user"),
                mock.patch.object(auth_runtime, "_finalize_session_payload", return_value={"authorized": True}) as finalize_mock,
            ):
                payload = auth_runtime.sign_up_console_user(
                    email="member@example.com",
                    password="password-123",
                )

        self.assertTrue(payload["authorized"])
        sign_in_mock.assert_called_once()
        self.assertEqual(sign_in_mock.call_args.kwargs["invite_token"], "invite-token-123")
        finalize_mock.assert_called_once()

    def test_sign_up_continues_when_auth_user_already_exists_with_duplicate_key_error(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "bootstrap@example.com",
            },
            clear=False,
        ):
            pending_invitation = {
                "invite_token": "invite-token-123",
                "email": "member@example.com",
                "status": "pending",
            }
            with (
                mock.patch.object(auth_runtime, "_list_pending_invitations_by_email", return_value=[pending_invitation]),
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=pending_invitation),
                mock.patch.object(
                    auth_runtime,
                    "_auth_request",
                    side_effect=auth_runtime.AuthRuntimeError(
                        'duplicate key value violates unique constraint "users_email_partial_key"',
                        status_code=500,
                        code="auth_upstream_error",
                    ),
                ),
                mock.patch.object(auth_runtime, "sign_in_with_password", return_value={"authorized": True}) as sign_in_mock,
                mock.patch.object(auth_runtime, "_ensure_member_local_user"),
                mock.patch.object(auth_runtime, "_finalize_session_payload", return_value={"authorized": True}) as finalize_mock,
            ):
                payload = auth_runtime.sign_up_console_user(
                    email="member@example.com",
                    password="password-123",
                )

        self.assertTrue(payload["authorized"])
        sign_in_mock.assert_called_once()
        self.assertEqual(sign_in_mock.call_args.kwargs["invite_token"], "invite-token-123")
        finalize_mock.assert_called_once()

    def test_sign_up_does_not_treat_unrelated_duplicate_key_error_as_existing_user(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "bootstrap@example.com",
            },
            clear=False,
        ):
            pending_invitation = {
                "invite_token": "invite-token-123",
                "email": "member@example.com",
                "status": "pending",
            }
            with (
                mock.patch.object(auth_runtime, "_list_pending_invitations_by_email", return_value=[pending_invitation]),
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=pending_invitation),
                mock.patch.object(
                    auth_runtime,
                    "_auth_request",
                    side_effect=auth_runtime.AuthRuntimeError(
                        'duplicate key value violates unique constraint "some_other_unique_key"',
                        status_code=500,
                        code="auth_upstream_error",
                    ),
                ),
            ):
                with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                    auth_runtime.sign_up_console_user(
                        email="member@example.com",
                        password="password-123",
                    )

        self.assertEqual(ctx.exception.code, "auth_upstream_error")

    def test_sign_in_resolves_pending_invitation_by_email_without_token(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "bootstrap@example.com",
            },
            clear=False,
        ):
            pending_invitation = {
                "invite_token": "invite-token-123",
                "email": "member@example.com",
                "status": "pending",
            }
            token_payload = {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "user": {"id": "auth-user-id", "email": "member@example.com"},
                "expires_in": 3600,
            }
            with (
                mock.patch.object(auth_runtime, "_list_pending_invitations_by_email", return_value=[pending_invitation]),
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=pending_invitation),
                mock.patch.object(auth_runtime, "_auth_request", return_value=token_payload),
                mock.patch.object(auth_runtime, "_finalize_session_payload", return_value={"auth_user_id": "auth-user-id", "authorized": False}),
                mock.patch.object(auth_runtime, "accept_invitation_for_session_payload", return_value={"authorized": True}) as accept_mock,
            ):
                payload = auth_runtime.sign_in_with_password(
                    email="member@example.com",
                    password="password-123",
                )

        self.assertTrue(payload["authorized"])
        accept_mock.assert_called_once()
        self.assertEqual(accept_mock.call_args.kwargs["invite_token"], "invite-token-123")

    def test_update_profile_allows_recent_accepted_invite_without_current_password(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
                "PHASE2_AUTH_SESSION_SECRET": "phase2-session-secret",
            },
            clear=False,
        ):
            session_payload = {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "email": "member@example.com",
                "display_name": "Old Name",
                "role": "org_member",
                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "organization_name": "Internal Operations",
                "authorized": True,
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "access_expires_at": int(time.time()) + 3600,
            }
            invitation = {
                "invite_token": "invite-token-123",
                "email": "member@example.com",
                "status": "accepted",
                "accepted_user_id": session_payload["auth_user_id"],
                "accepted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            with (
                mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=invitation),
                mock.patch.object(
                    auth_runtime,
                    "_auth_request",
                    return_value={
                        "id": session_payload["auth_user_id"],
                        "email": session_payload["email"],
                        "user_metadata": {"display_name": "New Name"},
                    },
                ) as auth_request_mock,
                mock.patch.object(auth_runtime, "_verify_password") as verify_password_mock,
                mock.patch.object(auth_runtime, "_update_local_user_profile") as update_local_user_mock,
                mock.patch.object(
                    auth_runtime,
                    "_finalize_session_payload",
                    return_value={**session_payload, "display_name": "New Name"},
                ) as finalize_mock,
            ):
                updated = auth_runtime.update_console_user_profile(
                    session_payload=session_payload,
                    display_name="New Name",
                    current_password="",
                    password="new-password-123",
                    invite_token="invite-token-123",
                )

        self.assertEqual(updated["display_name"], "New Name")
        verify_password_mock.assert_not_called()
        auth_request_mock.assert_called_once_with(
            "PUT",
            "/user",
            payload={"password": "new-password-123", "data": {"display_name": "New Name"}},
            access_token="access-token",
            use_service_authorization=False,
        )
        update_local_user_mock.assert_called_once()
        finalize_mock.assert_called_once()

    def test_get_invitation_preview_includes_organization_name(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            with (
                mock.patch.object(
                    auth_runtime,
                    "_get_invitation_by_token",
                    return_value={
                        "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                        "email": "member@example.com",
                        "role": "org_member",
                        "display_name": "Member",
                        "invite_token": "invite-token-123",
                        "status": "pending",
                    },
                ),
                mock.patch.object(
                    auth_runtime,
                    "_get_organization",
                    return_value={"name": "Internal Operations"},
                ),
            ):
                preview = auth_runtime.get_invitation_preview(invite_token="invite-token-123")

        self.assertEqual(preview["organization_name"], "Internal Operations")
        self.assertEqual(preview["email"], "member@example.com")
        self.assertEqual(len(preview["initial_password"]), 16)

    def test_create_invitation_marks_manual_delivery_when_email_delivery_is_disabled(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            with (
                mock.patch.object(
                    auth_runtime,
                    "request_json",
                    return_value=(
                        [
                            {
                                "id": "0f7f7c62-6fef-4d13-a3d6-b8bb7d85a111",
                                "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                                "email": "member@example.com",
                                "role": "org_member",
                                "display_name": "Member",
                                "team_name": "Operations",
                                "job_title": "Manager",
                                "invite_token": "invite-token-123",
                                "status": "pending",
                                "expires_at": "2026-03-30T00:00:00Z",
                                "created_at": "2026-03-23T00:00:00Z",
                                "updated_at": "2026-03-23T00:00:00Z",
                            }
                        ],
                        {},
                    ),
                ) as request_json_mock,
                mock.patch.object(auth_runtime, "_append_audit_log"),
                mock.patch.object(auth_runtime, "_send_invitation_email") as send_invite_mock,
            ):
                item = auth_runtime.create_invitation(
                    organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    created_by="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                    actor_role="org_admin",
                    email="member@example.com",
                    role="org_member",
                    display_name="Member",
                    team_name="Operations",
                    job_title="Manager",
                    expires_in_days=7,
                    invite_url_base="http://127.0.0.1:8019",
                    send_email=False,
                )

        self.assertEqual(item["delivery_status"], "manual")
        self.assertEqual(
            item["delivery_message"],
            "자동 초대 메일 발송은 현재 비활성화되어 있습니다. 초대 링크와 초기 암호를 복사해 직접 전달하세요.",
        )
        self.assertEqual(len(item["initial_password"]), 16)
        self.assertTrue(any(character.isupper() for character in item["initial_password"]))
        self.assertTrue(any(character.islower() for character in item["initial_password"]))
        self.assertTrue(any(character.isdigit() for character in item["initial_password"]))
        self.assertTrue(any(not character.isalnum() for character in item["initial_password"]))
        self.assertEqual(request_json_mock.call_args.kwargs["path"], "/rpc/create_invitation")
        send_invite_mock.assert_not_called()

    def test_post_auth_invitation_preserves_backend_delivery_payload_when_email_delivery_is_disabled(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/invitations",
                "scheme": "http",
                "server": ("testserver", 80),
                "root_path": "",
                "headers": [],
                "client": ("testclient", 12345),
                "query_string": b"",
            }
        )

        backend_item = {
            "id": "0f7f7c62-6fef-4d13-a3d6-b8bb7d85a111",
            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            "email": "member@example.com",
            "role": "org_member",
            "display_name": "Member",
            "team_name": "Operations",
            "job_title": "Manager",
            "invite_token": "invite-token-123",
            "invite_url": "http://127.0.0.1:8019/app/?invite_token=invite-token-123",
            "status": "pending",
            "expires_at": "2026-03-30T00:00:00Z",
            "created_at": "2026-03-23T00:00:00Z",
            "updated_at": "2026-03-23T00:00:00Z",
            "delivery_status": "failed",
            "delivery_message": "Delivery failed: SMTP is unavailable.",
            "initial_password": "Abcdef1!Ghijk2@",
        }

        background_tasks = BackgroundTasks()
        with (
            mock.patch.object(
                auth_app,
                "_resolve_sales_actor",
                return_value=SimpleNamespace(
                    is_admin=True,
                    organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    user_id="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                    role="org_admin",
                    email="admin@example.com",
                ),
            ),
            mock.patch.object(auth_app, "invitation_email_delivery_enabled", return_value=False),
            mock.patch.object(auth_app, "create_invitation", return_value=dict(backend_item)) as create_invitation_mock,
            mock.patch.object(auth_app, "_to_auth_invitation_model", side_effect=lambda request, item: item),
        ):
            result = auth_app.post_auth_invitation(
                background_tasks,
                request,
                auth_app.AuthInvitationCreateRequest(
                    email="member@example.com",
                    role="org_member",
                    display_name="Member",
                    team_name="Operations",
                    job_title="Manager",
                    expires_in_days=7,
                ),
            )

        self.assertEqual(result["delivery_status"], "failed")
        self.assertEqual(result["delivery_message"], "Delivery failed: SMTP is unavailable.")
        self.assertEqual(result["invite_url"], backend_item["invite_url"])
        self.assertEqual(result["initial_password"], backend_item["initial_password"])
        create_invitation_mock.assert_called_once()
        self.assertFalse(create_invitation_mock.call_args.kwargs["send_email"])

    def test_post_auth_invitation_queues_background_email_delivery_when_enabled(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/invitations",
                "scheme": "http",
                "server": ("testserver", 80),
                "root_path": "",
                "headers": [],
                "client": ("testclient", 12345),
                "query_string": b"",
            }
        )
        background_tasks = BackgroundTasks()

        backend_item = {
            "id": "0f7f7c62-6fef-4d13-a3d6-b8bb7d85a111",
            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            "email": "member@example.com",
            "role": "org_member",
            "display_name": "Member",
            "team_name": "Operations",
            "job_title": "Manager",
            "invite_token": "invite-token-123",
            "invite_url": "http://127.0.0.1:8019/app/?invite_token=invite-token-123",
            "status": "pending",
            "expires_at": "2026-03-30T00:00:00Z",
            "created_at": "2026-03-23T00:00:00Z",
            "updated_at": "2026-03-23T00:00:00Z",
            "delivery_status": "manual",
            "delivery_message": "manual fallback",
            "initial_password": "Abcdef1!Ghijk2@",
        }

        with (
            mock.patch.object(
                auth_app,
                "_resolve_sales_actor",
                return_value=SimpleNamespace(
                    is_admin=True,
                    organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    user_id="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                    role="org_admin",
                    email="admin@example.com",
                ),
            ),
            mock.patch.object(auth_app, "invitation_email_delivery_enabled", return_value=True),
            mock.patch.object(auth_app, "create_invitation", return_value=dict(backend_item)) as create_invitation_mock,
            mock.patch.object(auth_app, "_to_auth_invitation_model", side_effect=lambda request, item: item),
        ):
            result = auth_app.post_auth_invitation(
                background_tasks,
                request,
                auth_app.AuthInvitationCreateRequest(
                    email="member@example.com",
                    role="org_member",
                    display_name="Member",
                    team_name="Operations",
                    job_title="Manager",
                    expires_in_days=7,
                ),
            )

        self.assertEqual(result["delivery_status"], "queued")
        self.assertIn("초대 메일 발송을 시작했습니다", result["delivery_message"])
        create_invitation_mock.assert_called_once()
        self.assertFalse(create_invitation_mock.call_args.kwargs["send_email"])
        self.assertEqual(len(background_tasks.tasks), 1)
        task = background_tasks.tasks[0]
        self.assertIs(task.func, auth_app.deliver_invitation_email)
        self.assertEqual(task.kwargs["email"], "member@example.com")
        self.assertEqual(task.kwargs["invite_url"], backend_item["invite_url"])
        self.assertEqual(task.kwargs["display_name"], "Member")

    def test_resolve_public_app_base_url_prefers_forwarded_host(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/invitations",
                "scheme": "http",
                "server": ("13.125.219.119", 8000),
                "root_path": "",
                "headers": [
                    (b"x-forwarded-host", b"notice-winner-pipeline-web-related-notice-search.vercel.app"),
                    (b"x-forwarded-proto", b"https"),
                ],
                "client": ("testclient", 12345),
                "query_string": b"",
            }
        )

        self.assertEqual(
            auth_app._resolve_public_app_base_url(request),
            "https://notice-winner-pipeline-web-related-notice-search.vercel.app",
        )

    def test_resolve_public_app_base_url_prefers_public_app_url_env(self) -> None:
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/auth/invitations",
                "scheme": "http",
                "server": ("13.125.219.119", 8000),
                "root_path": "",
                "headers": [],
                "client": ("testclient", 12345),
                "query_string": b"",
            }
        )

        with mock.patch.dict(os.environ, {"PUBLIC_APP_URL": "https://custom.example.com"}, clear=False):
            self.assertEqual(auth_app._resolve_public_app_base_url(request), "https://custom.example.com")

    def test_create_invitation_preserves_service_delivery_payload_when_email_delivery_is_disabled(self) -> None:
        backend_item = {
            "id": "0f7f7c62-6fef-4d13-a3d6-b8bb7d85a111",
            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            "email": "member@example.com",
            "role": "org_member",
            "display_name": "Member",
            "team_name": "Operations",
            "job_title": "Manager",
            "invite_token": "invite-token-123",
            "invite_url": "http://127.0.0.1:8019/app/?invite_token=invite-token-123",
            "status": "pending",
            "expires_at": "2026-03-30T00:00:00Z",
            "created_at": "2026-03-23T00:00:00Z",
            "updated_at": "2026-03-23T00:00:00Z",
            "delivery_status": "failed",
            "delivery_message": "Delivery failed: SMTP is unavailable.",
            "initial_password": "Abcdef1!Ghijk2@",
        }

        with (
            mock.patch.object(auth_runtime, "_create_invitation_impl", return_value=dict(backend_item)) as create_invitation_impl_mock,
            mock.patch.object(auth_runtime, "_append_audit_log"),
            mock.patch.object(auth_runtime, "_send_invitation_email"),
        ):
            item = auth_runtime.create_invitation(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                created_by="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                actor_role="org_admin",
                email="member@example.com",
                role="org_member",
                display_name="Member",
                team_name="Operations",
                job_title="Manager",
                expires_in_days=7,
                invite_url_base="http://127.0.0.1:8019",
                send_email=False,
            )

        self.assertEqual(item["invite_url"], backend_item["invite_url"])
        self.assertEqual(item["initial_password"], backend_item["initial_password"])
        self.assertEqual(item["delivery_status"], "failed")
        self.assertEqual(item["delivery_message"], "Delivery failed: SMTP is unavailable.")
        create_invitation_impl_mock.assert_called_once()

    def test_deliver_invitation_email_is_disabled_without_delivery_prerequisites(self) -> None:
        with (
            mock.patch.dict(
                os.environ,
                {
                    "PHASE2_AUTH_DELIVER_INVITE_EMAILS": "",
                },
                clear=False,
            ),
            mock.patch.object(auth_runtime, "_has_invitation_email_delivery_prerequisites", return_value=False),
            mock.patch.object(auth_runtime, "_send_invitation_email") as send_invite_mock,
        ):
            auth_runtime.deliver_invitation_email(
                email="member@example.com",
                invite_url="http://127.0.0.1:8019/app/?invite_token=invite-token-123",
                display_name="Member",
            )

        send_invite_mock.assert_not_called()

    def test_deliver_invitation_email_is_enabled_by_default_when_delivery_prerequisites_exist(self) -> None:
        with (
            mock.patch.dict(
                os.environ,
                {
                    "PHASE2_AUTH_DELIVER_INVITE_EMAILS": "",
                },
                clear=False,
            ),
            mock.patch.object(auth_runtime, "_has_invitation_email_delivery_prerequisites", return_value=True),
            mock.patch.object(auth_runtime, "_send_invitation_email") as send_invite_mock,
        ):
            auth_runtime.deliver_invitation_email(
                email="member@example.com",
                invite_url="http://127.0.0.1:8019/app/?invite_token=invite-token-123",
                display_name="Member",
            )

        send_invite_mock.assert_called_once_with(
            email="member@example.com",
            invite_url="http://127.0.0.1:8019/app/?invite_token=invite-token-123",
            display_name="Member",
        )

    def test_deliver_invitation_email_can_be_enabled_explicitly(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_DELIVER_INVITE_EMAILS": "1",
            },
            clear=False,
        ):
            with mock.patch.object(auth_runtime, "_send_invitation_email") as send_invite_mock:
                auth_runtime.deliver_invitation_email(
                    email="member@example.com",
                    invite_url="http://127.0.0.1:8019/app/?invite_token=invite-token-123",
                    display_name="Member",
                )

        send_invite_mock.assert_called_once_with(
            email="member@example.com",
            invite_url="http://127.0.0.1:8019/app/?invite_token=invite-token-123",
            display_name="Member",
        )

    def test_get_organization_plan_summary_counts_only_active_non_platform_users(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_get_organization",
                return_value={
                    "id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    "name": "Internal Operations",
                    "plan_code": "B",
                    "plan_label": "플랜 B",
                    "active_user_limit": 10,
                    "pending_invite_limit": 10,
                },
            ),
            mock.patch.object(
                auth_runtime,
                "list_local_users",
                return_value=[
                    {"account_status": "active", "membership_status": "active", "global_role": "", "email": "a@example.com"},
                    {"account_status": "active", "membership_status": "inactive", "global_role": "", "email": "b@example.com"},
                    {"account_status": "active", "membership_status": "active", "global_role": "platform_admin", "email": "ops@example.com"},
                    {"account_status": "active", "membership_status": "active", "global_role": "", "email": "c@example.com"},
                ],
            ),
            mock.patch.object(
                auth_runtime,
                "list_invitations",
                return_value=[
                    {"status": "pending", "email": "pending1@example.com"},
                    {"status": "pending", "email": "pending2@example.com"},
                ],
            ),
        ):
            summary = auth_runtime.get_organization_plan_summary(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            )

        self.assertEqual(summary["plan_code"], "B")
        self.assertEqual(summary["active_user_count"], 2)
        self.assertEqual(summary["pending_invite_count"], 2)
        self.assertEqual(summary["remaining_active_user_slots"], 8)
        self.assertEqual(summary["remaining_pending_invite_slots"], 8)
        self.assertFalse(summary["upgrade_required"])

    def test_get_organization_invitation_dashboard_hides_org_admin_invites_from_org_admin_actor(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_get_organization",
                return_value={
                    "id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    "name": "Internal Operations",
                    "plan_code": "A",
                    "active_user_limit": 5,
                    "pending_invite_limit": 5,
                },
            ),
            mock.patch.object(auth_runtime, "list_local_users", return_value=[]),
            mock.patch.object(
                auth_runtime,
                "list_invitations",
                return_value=[
                    {"id": "member-invite", "email": "member@example.com", "role": "org_member", "status": "pending"},
                    {"id": "admin-invite", "email": "admin@example.com", "role": "org_admin", "status": "pending"},
                ],
            ),
        ):
            dashboard = auth_runtime.get_organization_invitation_dashboard(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                actor_role="org_admin",
            )

        self.assertEqual([item["id"] for item in dashboard["items"]], ["member-invite"])
        self.assertEqual(dashboard["plan_summary"]["pending_invite_count"], 2)

    def test_list_organization_audit_logs_enriches_actor_metadata(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_get_organization",
                return_value={"id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001", "name": "Internal Operations"},
            ),
            mock.patch.object(auth_runtime, "_rest_base_url", return_value="https://example.supabase.co/rest/v1"),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-role-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=10.0),
            mock.patch.object(
                auth_runtime,
                "request_json",
                return_value=(
                    [
                        {
                            "id": 101,
                            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                            "actor_user_id": "user-profile-1",
                            "actor_membership_id": "membership-1",
                            "event_type": "invite_created",
                            "target_type": "invitation",
                            "target_id": "invite-1",
                            "payload_json": {"email": "member@example.com", "role": "org_member"},
                            "created_at": "2026-03-25T01:00:00Z",
                        }
                    ],
                    {},
                ),
            ),
            mock.patch.object(
                auth_runtime,
                "list_local_users",
                return_value=[
                    {
                        "id": "user-profile-1",
                        "membership_id": "membership-1",
                        "email": "admin@example.com",
                        "display_name": "관리자",
                        "role": "org_admin",
                        "global_role": "",
                    }
                ],
            ),
        ):
            items = auth_runtime.list_organization_audit_logs(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                limit=20,
            )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["actor_email"], "admin@example.com")
        self.assertEqual(items[0]["actor_display_name"], "관리자")
        self.assertEqual(items[0]["actor_role"], "org_admin")
        self.assertEqual(items[0]["event_type"], "invite_created")

    def test_list_organization_audit_logs_clamps_limit_to_100(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_get_organization",
                return_value={"id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001", "name": "Internal Operations"},
            ),
            mock.patch.object(auth_runtime, "_rest_base_url", return_value="https://example.supabase.co/rest/v1"),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-role-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=10.0),
            mock.patch.object(
                auth_runtime,
                "request_json",
                return_value=([], {}),
            ) as request_json_mock,
        ):
            items = auth_runtime.list_organization_audit_logs(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                limit=999,
            )

        self.assertEqual(items, [])
        self.assertIn(("limit", "100"), request_json_mock.call_args.kwargs["query"])

    def test_list_organization_audit_logs_coerces_non_dict_payload_json(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_get_organization",
                return_value={"id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001", "name": "Internal Operations"},
            ),
            mock.patch.object(auth_runtime, "_rest_base_url", return_value="https://example.supabase.co/rest/v1"),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-role-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=10.0),
            mock.patch.object(
                auth_runtime,
                "request_json",
                return_value=(
                    [
                        {
                            "id": 102,
                            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                            "actor_user_id": "",
                            "actor_membership_id": "",
                            "event_type": "invite_created",
                            "target_type": "invitation",
                            "target_id": "invite-2",
                            "payload_json": "not-a-dict",
                            "created_at": "2026-03-25T02:00:00Z",
                        }
                    ],
                    {},
                ),
            ),
            mock.patch.object(auth_runtime, "list_local_users", return_value=[]),
        ):
            items = auth_runtime.list_organization_audit_logs(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                limit=20,
            )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["payload_json"], {})

    def test_resolve_allowed_invitation_roles_permission_matrix(self) -> None:
        self.assertEqual(
            auth_runtime._resolve_allowed_invitation_roles("platform_admin"),
            ("org_member", "org_admin"),
        )
        self.assertEqual(
            auth_runtime._resolve_allowed_invitation_roles("org_admin"),
            ("org_member",),
        )
        self.assertEqual(auth_runtime._resolve_allowed_invitation_roles("org_member"), ())

    def test_filter_manageable_invitations_permission_matrix(self) -> None:
        invitations = [
            {"id": "member-invite", "role": "org_member"},
            {"id": "admin-invite", "role": "org_admin"},
            {"id": "unknown-invite", "role": "unknown"},
        ]

        platform_items = auth_runtime._filter_manageable_invitations(
            actor_role="platform_admin",
            invitations=invitations,
        )
        org_admin_items = auth_runtime._filter_manageable_invitations(
            actor_role="org_admin",
            invitations=invitations,
        )

        self.assertEqual([item["id"] for item in platform_items], ["member-invite", "admin-invite"])
        self.assertEqual([item["id"] for item in org_admin_items], ["member-invite"])

    def test_create_invitation_rejects_org_admin_target_for_org_admin_actor(self) -> None:
        with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
            auth_runtime.create_invitation(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                created_by="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                actor_role="org_admin",
                email="admin@example.com",
                role="org_admin",
                send_email=False,
            )

        self.assertEqual(ctx.exception.code, "invite_role_forbidden")

    def test_create_invitation_allows_platform_admin_to_invite_org_admin(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_rest_base_url",
                return_value="https://example.supabase.co/rest/v1",
            ),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-role-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=10.0),
            mock.patch.object(
                auth_runtime,
                "request_json",
                return_value=(
                    [
                        {
                            "id": "0f7f7c62-6fef-4d13-a3d6-b8bb7d85a111",
                            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                            "email": "admin@example.com",
                            "role": "org_admin",
                            "display_name": "Admin",
                            "team_name": "",
                            "job_title": "",
                            "invite_token": "invite-token-123",
                            "status": "pending",
                            "expires_at": "2026-03-30T00:00:00Z",
                            "created_at": "2026-03-23T00:00:00Z",
                            "updated_at": "2026-03-23T00:00:00Z",
                        }
                    ],
                    {},
                ),
            ) as request_json_mock,
            mock.patch.object(auth_runtime, "_append_audit_log"),
        ):
            auth_runtime.create_invitation(
                organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                created_by="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                actor_role="platform_admin",
                email="admin@example.com",
                role="org_admin",
                display_name="Admin",
                send_email=False,
            )

        self.assertEqual(request_json_mock.call_args.kwargs["path"], "/rpc/create_invitation")
        self.assertEqual(request_json_mock.call_args.kwargs["payload"]["p_role"], "org_admin")

    def test_create_invitation_rejects_when_plan_limit_is_reached(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_rest_base_url",
                return_value="https://example.supabase.co/rest/v1",
            ),
            mock.patch.object(auth_runtime, "_service_api_key", return_value="service-role-key"),
            mock.patch.object(auth_runtime, "_timeout_seconds", return_value=10.0),
            mock.patch.object(
                auth_runtime,
                "get_organization_plan_summary",
                return_value={
                    "upgrade_message": "Plan limit reached.",
                },
            ),
            mock.patch.object(
                auth_runtime,
                "request_json",
                side_effect=auth_runtime.AuthRuntimeError("pending invite limit reached for this organization"),
            ) as request_json_mock,
        ):
            with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                auth_runtime.create_invitation(
                    organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    created_by="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                    actor_role="org_admin",
                    email="member@example.com",
                    role="org_member",
                    send_email=False,
                )

        self.assertEqual(ctx.exception.code, "invite_limit_reached")
        self.assertEqual(ctx.exception.status_code, 409)
        request_json_mock.assert_called_once()

    def test_delete_local_user_account_removes_local_rows_and_auth_user(self) -> None:
        deleted_paths: list[tuple[str, list[tuple[str, str]]]] = []

        def _record_delete(path: str, query: list[tuple[str, str]]) -> None:
            deleted_paths.append((path, list(query)))

        with (
            mock.patch.object(
                auth_runtime,
                "_get_local_user",
                return_value={
                    "id": "user-123",
                    "email": "member@example.com",
                    "membership_id": "membership-123",
                },
            ),
            mock.patch.object(
                auth_runtime,
                "_get_user_profile",
                return_value={"id": "profile-123"},
            ),
            mock.patch.object(auth_runtime, "_rest_delete_rows", side_effect=_record_delete) as delete_mock,
            mock.patch.object(auth_runtime, "_delete_supabase_auth_user") as delete_auth_mock,
        ):
            current = auth_runtime.delete_local_user_account(
                organization_id="org-123",
                user_id="user-123",
            )

        self.assertEqual(current["id"], "user-123")
        self.assertTrue(delete_mock.called)
        self.assertEqual(
            [path for path, _query in deleted_paths],
            [
                "project_sales_claims",
                "project_sales_claim_events",
                "saved_run_presets",
                "pipeline_runs",
                "tracker_entry_audit_logs",
                "audit_logs",
                "audit_logs",
                "invitations",
                "invitations",
                "invitations",
                "organization_memberships",
                "user_profiles",
                "users",
            ],
        )
        delete_auth_mock.assert_called_once_with(auth_user_id="user-123")

    def test_delete_local_user_account_handles_missing_profile_and_blank_email(self) -> None:
        deleted_paths: list[str] = []

        def _record_delete(path: str, query: list[tuple[str, str]]) -> None:
            del query
            deleted_paths.append(path)

        with (
            mock.patch.object(
                auth_runtime,
                "_get_local_user",
                return_value={
                    "id": "user-789",
                    "email": "",
                    "membership_id": "",
                },
            ),
            mock.patch.object(auth_runtime, "_get_user_profile", return_value=None),
            mock.patch.object(auth_runtime, "_rest_delete_rows", side_effect=_record_delete),
            mock.patch.object(auth_runtime, "_delete_supabase_auth_user") as delete_auth_mock,
        ):
            auth_runtime.delete_local_user_account(
                organization_id="org-789",
                user_id="user-789",
            )

        self.assertEqual(
            deleted_paths,
            [
                "project_sales_claims",
                "project_sales_claim_events",
                "saved_run_presets",
                "pipeline_runs",
                "tracker_entry_audit_logs",
                "audit_logs",
                "invitations",
                "invitations",
                "organization_memberships",
                "user_profiles",
                "users",
            ],
        )
        delete_auth_mock.assert_called_once_with(auth_user_id="user-789")

    def test_revoke_invitation_rejects_org_admin_invite_for_org_admin_actor(self) -> None:
        with (
            mock.patch.object(
                auth_runtime,
                "_get_invitation_by_id",
                return_value={"id": "admin-invite", "role": "org_admin"},
            ),
            mock.patch.object(auth_runtime, "request_json") as request_json_mock,
        ):
            with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                auth_runtime.revoke_invitation(
                    organization_id="7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                    invitation_id="admin-invite",
                    actor_user_id="2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                    actor_role="org_admin",
                )

        self.assertEqual(ctx.exception.code, "invite_role_forbidden")
        request_json_mock.assert_not_called()

    def test_accept_invitation_for_session_payload_rejects_when_active_user_limit_is_reached(self) -> None:
        session_payload = {
            "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
            "email": "member@example.com",
            "display_name": "Member",
            "access_token": "access",
            "refresh_token": "refresh",
            "access_expires_at": int(time.time()) + 3600,
        }
        invitation = {
            "invite_token": "invite-token-123",
            "organization_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
            "email": "member@example.com",
            "status": "pending",
            "accepted_user_id": "",
        }
        with (
            mock.patch.object(auth_runtime, "_ensure_user_profile"),
            mock.patch.object(auth_runtime, "_get_invitation_by_token", return_value=invitation),
            mock.patch.object(auth_runtime, "_get_user_profile", return_value={"global_role": ""}),
            mock.patch.object(auth_runtime, "_get_membership_row", return_value=None),
            mock.patch.object(
                auth_runtime,
                "get_organization_plan_summary",
                return_value={
                    "active_user_limit_reached": True,
                    "upgrade_message": "Seat limit reached.",
                },
            ),
            mock.patch.object(auth_runtime, "request_json") as request_json_mock,
        ):
            with self.assertRaises(auth_runtime.AuthRuntimeError) as ctx:
                auth_runtime.accept_invitation_for_session_payload(
                    session_payload=session_payload,
                    invite_token="invite-token-123",
                )

        self.assertEqual(ctx.exception.code, "invite_limit_reached")
        request_json_mock.assert_not_called()

    def test_import_auth_session_builds_session_from_tokens(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "PHASE2_AUTH_ENABLED": "1",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "phase2-secret",
            },
            clear=False,
        ):
            with (
                mock.patch.object(
                    auth_runtime,
                    "_auth_request",
                    return_value={
                        "id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                        "email": "member@example.com",
                        "user_metadata": {"display_name": "Member"},
                    },
                ) as auth_request_mock,
                mock.patch.object(
                    auth_runtime,
                    "_finalize_session_payload",
                    return_value={"authorized": True, "access_token": "access", "refresh_token": "refresh"},
                ) as finalize_mock,
                mock.patch.object(auth_runtime, "_read_access_token_expires_in", return_value=3600),
            ):
                payload = auth_runtime.import_auth_session(
                    access_token="access",
                    refresh_token="refresh",
                )

        self.assertEqual(payload["authorized"], True)
        auth_request_mock.assert_called_once_with(
            "GET",
            "/user",
            access_token="access",
            use_service_authorization=False,
        )
        finalize_mock.assert_called_once()
