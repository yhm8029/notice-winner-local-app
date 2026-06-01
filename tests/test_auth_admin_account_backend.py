from __future__ import annotations

import unittest

import backend.services.auth_admin_account_backend as backend


class _AuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "auth_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _noop_warn(_message: str) -> None:
    return None


def _raise_auth_error(message: str, *, status_code: int, code: str):
    def _raiser(**_kwargs):
        raise _AuthError(message, status_code=status_code, code=code)

    return _raiser


class PlatformAdminAccountBackendTests(unittest.TestCase):
    def test_create_platform_admin_account_rejects_non_platform_admin_actors(self) -> None:
        with self.assertRaises(_AuthError) as ctx:
            backend.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="org_admin",
                organization_id="org-1",
                email="member@example.com",
                password="TempPass123!",
                display_name="Member",
                role="org_member",
                create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
                get_user_profile_fn=lambda **_kwargs: None,
                list_local_users_fn=lambda **_kwargs: [],
                ensure_user_profile_fn=lambda **_kwargs: None,
                ensure_membership_fn=lambda **_kwargs: None,
                append_audit_log_fn=lambda **_kwargs: None,
                cleanup_local_account_fn=lambda **_kwargs: None,
                delete_auth_user_fn=lambda **_kwargs: None,
                warn_fn=_noop_warn,
                normalize_email_fn=lambda value: str(value).strip().lower(),
                normalize_org_role_fn=lambda value: str(value).strip().lower(),
                auth_error_cls=_AuthError,
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.code, "auth_forbidden")

    def test_create_platform_admin_account_rejects_duplicate_email_for_existing_local_user(self) -> None:
        with self.assertRaises(_AuthError) as ctx:
            backend.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="platform_admin",
                organization_id="org-1",
                email=" member@example.com ",
                password="TempPass123!",
                display_name="Member",
                role="ORG_MEMBER",
                create_auth_user_fn=lambda **_kwargs: self.fail("create_auth_user_fn should not be called"),
                get_user_profile_fn=lambda **_kwargs: None,
                list_local_users_fn=lambda **_kwargs: [{"email": "member@example.com"}],
                ensure_user_profile_fn=lambda **_kwargs: self.fail("ensure_user_profile_fn should not be called"),
                ensure_membership_fn=lambda **_kwargs: self.fail("ensure_membership_fn should not be called"),
                append_audit_log_fn=lambda **_kwargs: self.fail("append_audit_log_fn should not be called"),
                cleanup_local_account_fn=lambda **_kwargs: self.fail("cleanup_local_account_fn should not be called"),
                delete_auth_user_fn=lambda **_kwargs: self.fail("delete_auth_user_fn should not be called"),
                warn_fn=_noop_warn,
                normalize_email_fn=lambda value: str(value).strip().lower(),
                normalize_org_role_fn=lambda value: str(value).strip().lower(),
                auth_error_cls=_AuthError,
            )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.code, "auth_user_exists")

    def test_create_platform_admin_account_creates_auth_user_profile_membership_and_audit_log(self) -> None:
        profile_calls: list[dict[str, object]] = []
        membership_calls: list[dict[str, object]] = []
        audit_calls: list[dict[str, object]] = []

        item = backend.create_platform_admin_account(
            actor_user_id="admin-1",
            actor_role="platform_admin",
            organization_id="org-1",
            email=" Member@Example.com ",
            password="TempPass123!",
            display_name="Member",
            role="ORG_MEMBER",
            create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
            get_user_profile_fn=lambda **_kwargs: None,
            list_local_users_fn=lambda **_kwargs: [],
            ensure_user_profile_fn=lambda **kwargs: profile_calls.append(dict(kwargs)),
            ensure_membership_fn=lambda **kwargs: membership_calls.append(dict(kwargs)),
            append_audit_log_fn=lambda **kwargs: audit_calls.append(dict(kwargs)),
            cleanup_local_account_fn=lambda **_kwargs: self.fail("cleanup_local_account_fn should not be called"),
            delete_auth_user_fn=lambda **_kwargs: self.fail("delete_auth_user_fn should not be called"),
            warn_fn=_noop_warn,
            normalize_email_fn=lambda value: str(value).strip().lower(),
            normalize_org_role_fn=lambda value: str(value).strip().lower(),
            auth_error_cls=_AuthError,
        )

        self.assertEqual(
            item,
            {
                "id": "user-1",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "account_status": "active",
                "membership_status": "active",
                "password_setup_mode": "admin_set",
                "force_password_change": False,
            },
        )
        self.assertEqual(profile_calls[0]["user_id"], "user-1")
        self.assertEqual(profile_calls[0]["account_status"], "active")
        self.assertEqual(profile_calls[0]["global_role"], "")
        self.assertEqual(profile_calls[0]["created_by_user_id"], "admin-1")
        self.assertEqual(profile_calls[0]["password_setup_mode"], "admin_set")
        self.assertFalse(profile_calls[0]["force_password_change"])
        self.assertEqual(membership_calls[0]["organization_id"], "org-1")
        self.assertEqual(membership_calls[0]["user_id"], "user-1")
        self.assertEqual(membership_calls[0]["role"], "org_member")
        self.assertEqual(membership_calls[0]["membership_status"], "active")
        self.assertEqual(audit_calls[0]["event_type"], "account_created")
        self.assertEqual(audit_calls[0]["target_type"], "user_profile")
        self.assertEqual(audit_calls[0]["target_id"], "user-1")

    def test_create_platform_admin_account_rejects_global_same_email_collision_before_auth_creation(self) -> None:
        create_calls: list[dict[str, object]] = []

        with self.assertRaises(_AuthError) as ctx:
            backend.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="platform_admin",
                organization_id="org-1",
                email="member@example.com",
                password="TempPass123!",
                display_name="Member",
                role="org_member",
                create_auth_user_fn=lambda **kwargs: create_calls.append(dict(kwargs)),
                get_user_profile_fn=lambda **_kwargs: {"id": "existing-profile", "email": "member@example.com"},
                list_local_users_fn=lambda **_kwargs: self.fail("list_local_users_fn should not be called"),
                ensure_user_profile_fn=lambda **_kwargs: self.fail("ensure_user_profile_fn should not be called"),
                ensure_membership_fn=lambda **_kwargs: self.fail("ensure_membership_fn should not be called"),
                append_audit_log_fn=lambda **_kwargs: self.fail("append_audit_log_fn should not be called"),
                cleanup_local_account_fn=lambda **_kwargs: self.fail("cleanup_local_account_fn should not be called"),
                delete_auth_user_fn=lambda **_kwargs: self.fail("delete_auth_user_fn should not be called"),
                warn_fn=_noop_warn,
                normalize_email_fn=lambda value: str(value).strip().lower(),
                normalize_org_role_fn=lambda value: str(value).strip().lower(),
                auth_error_cls=_AuthError,
            )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.code, "auth_user_exists")
        self.assertEqual(create_calls, [])

    def test_create_platform_admin_account_cleans_up_auth_and_local_state_on_write_failure(self) -> None:
        cleanup_calls: list[dict[str, object]] = []

        with self.assertRaises(_AuthError) as ctx:
            backend.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="platform_admin",
                organization_id="org-1",
                email="member@example.com",
                password="TempPass123!",
                display_name="Member",
                role="org_member",
                create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
                get_user_profile_fn=lambda **_kwargs: None,
                list_local_users_fn=lambda **_kwargs: [],
                ensure_user_profile_fn=_raise_auth_error("profile write failed", status_code=500, code="profile_write_failed"),
                ensure_membership_fn=lambda **_kwargs: self.fail("ensure_membership_fn should not be called"),
                append_audit_log_fn=lambda **_kwargs: self.fail("append_audit_log_fn should not be called"),
                cleanup_local_account_fn=lambda **kwargs: cleanup_calls.append(dict(kwargs)),
                delete_auth_user_fn=lambda **kwargs: cleanup_calls.append({"auth_user_id": kwargs["auth_user_id"]}),
                warn_fn=_noop_warn,
                normalize_email_fn=lambda value: str(value).strip().lower(),
                normalize_org_role_fn=lambda value: str(value).strip().lower(),
                auth_error_cls=_AuthError,
            )

        self.assertEqual(ctx.exception.code, "profile_write_failed")
        self.assertEqual(
            cleanup_calls,
            [
                {"auth_user_id": "user-1"},
                {"organization_id": "org-1", "user_id": "user-1", "email": "member@example.com"},
            ],
        )

    def test_create_platform_admin_account_raises_cleanup_error_when_rollback_cleanup_fails(self) -> None:
        cleanup_calls: list[str] = []

        def _fail_auth_cleanup(**_kwargs):
            cleanup_calls.append("auth")
            raise _AuthError("auth cleanup failed", status_code=500, code="cleanup_failed")

        def _fail_local_cleanup(**_kwargs):
            cleanup_calls.append("local")
            raise _AuthError("local cleanup failed", status_code=500, code="cleanup_failed")

        with self.assertRaises(_AuthError) as ctx:
            backend.create_platform_admin_account(
                actor_user_id="admin-1",
                actor_role="platform_admin",
                organization_id="org-1",
                email="member@example.com",
                password="TempPass123!",
                display_name="Member",
                role="org_member",
                create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
                get_user_profile_fn=lambda **_kwargs: None,
                list_local_users_fn=lambda **_kwargs: [],
                ensure_user_profile_fn=_raise_auth_error("profile write failed", status_code=500, code="profile_write_failed"),
                ensure_membership_fn=lambda **_kwargs: self.fail("ensure_membership_fn should not be called"),
                append_audit_log_fn=lambda **_kwargs: self.fail("append_audit_log_fn should not be called"),
                cleanup_local_account_fn=_fail_local_cleanup,
                delete_auth_user_fn=_fail_auth_cleanup,
                warn_fn=_noop_warn,
                normalize_email_fn=lambda value: str(value).strip().lower(),
                normalize_org_role_fn=lambda value: str(value).strip().lower(),
                auth_error_cls=_AuthError,
            )

        self.assertEqual(ctx.exception.code, "auth_create_cleanup_failed")
        self.assertIn("rollback cleanup failed", ctx.exception.message)
        self.assertEqual(cleanup_calls, ["auth", "local"])

    def test_create_platform_admin_account_emits_warning_for_audit_failure_and_still_succeeds(self) -> None:
        warn_calls: list[str] = []

        def _warn(message: str) -> None:
            warn_calls.append(message)

        item = backend.create_platform_admin_account(
            actor_user_id="admin-1",
            actor_role="platform_admin",
            organization_id="org-1",
            email="member@example.com",
            password="TempPass123!",
            display_name="Member",
            role="org_member",
            create_auth_user_fn=lambda **_kwargs: {"id": "user-1", "email": "member@example.com"},
            get_user_profile_fn=lambda **_kwargs: None,
            list_local_users_fn=lambda **_kwargs: [],
            ensure_user_profile_fn=lambda **_kwargs: None,
            ensure_membership_fn=lambda **_kwargs: None,
            append_audit_log_fn=_raise_auth_error("audit write failed", status_code=500, code="audit_write_failed"),
            cleanup_local_account_fn=lambda **_kwargs: self.fail("cleanup_local_account_fn should not be called"),
            delete_auth_user_fn=lambda **_kwargs: self.fail("delete_auth_user_fn should not be called"),
            warn_fn=_warn,
            normalize_email_fn=lambda value: str(value).strip().lower(),
            normalize_org_role_fn=lambda value: str(value).strip().lower(),
            auth_error_cls=_AuthError,
        )

        self.assertEqual(item["id"], "user-1")
        self.assertEqual(warn_calls, ["account_created audit log failed (organization_id=org-1, user_id=user-1, email=member@example.com)"])


if __name__ == "__main__":
    unittest.main()
