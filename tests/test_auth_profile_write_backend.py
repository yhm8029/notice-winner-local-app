from __future__ import annotations

import unittest

from backend.services.auth_profile_write_backend import ensure_membership
from backend.services.auth_profile_write_backend import ensure_user_profile
from backend.services.auth_profile_write_backend import sync_legacy_user_projection
from backend.services.auth_profile_write_backend import update_local_user_profile


class _AuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "validation_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class AuthProfileWriteBackendTests(unittest.TestCase):
    def test_ensure_user_profile_updates_existing_profile_with_different_id(self) -> None:
        captured: dict[str, object] = {}

        def fake_request_json(**kwargs):
            captured.update(kwargs)
            return [], {}

        ensure_user_profile(
            user_id="new-user",
            email="user@example.com",
            display_name="User",
            account_status="active",
            global_role="org_admin",
            get_user_profile_fn=lambda **_: {"id": "existing-user"},
            request_json_fn=fake_request_json,
            rest_base_url=lambda: "https://example.invalid",
            service_api_key=lambda: "key",
            timeout_seconds=lambda: 5.0,
            rest_upsert_fn=lambda *args, **kwargs: self.fail("rest_upsert should not be used"),
            normalize_account_status_fn=lambda value: f"acct:{value}",
            normalize_global_role_fn=lambda value: f"role:{value}",
            is_missing_relation_error_fn=lambda message, relation: False,
            is_missing_column_error_fn=lambda message, column: False,
            auth_error_cls=_AuthError,
        )

        self.assertEqual(captured["path"], "/user_profiles")
        self.assertEqual(captured["query"], [("id", "eq.existing-user")])
        self.assertEqual(
            captured["payload"],
            {
                "display_name": "User",
                "account_status": "acct:active",
                "global_role": "role:org_admin",
            },
        )

    def test_ensure_user_profile_includes_new_fields_when_explicitly_provided(self) -> None:
        captured: dict[str, object] = {}

        def fake_rest_upsert(table: str, payload: dict[str, object], *, on_conflict: str) -> None:
            captured["table"] = table
            captured["payload"] = dict(payload)
            captured["on_conflict"] = on_conflict

        ensure_user_profile(
            user_id="new-user",
            email="user@example.com",
            display_name="User",
            created_by_user_id="admin-user",
            password_setup_mode="admin_set",
            force_password_change=False,
            get_user_profile_fn=lambda **_: None,
            request_json_fn=lambda **_: self.fail("request_json should not be used"),
            rest_base_url=lambda: "https://example.invalid",
            service_api_key=lambda: "key",
            timeout_seconds=lambda: 5.0,
            rest_upsert_fn=fake_rest_upsert,
            normalize_account_status_fn=lambda value: f"acct:{value}",
            normalize_global_role_fn=lambda value: f"role:{value}",
            is_missing_relation_error_fn=lambda message, relation: False,
            is_missing_column_error_fn=lambda message, column: False,
            auth_error_cls=_AuthError,
        )

        self.assertEqual(captured["table"], "user_profiles")
        self.assertEqual(captured["on_conflict"], "id")
        self.assertEqual(
            captured["payload"],
            {
                "id": "new-user",
                "email": "user@example.com",
                "display_name": "User",
                "account_status": "acct:active",
                "global_role": "role:",
                "created_by_user_id": "admin-user",
                "password_setup_mode": "admin_set",
                "force_password_change": False,
            },
        )

    def test_ensure_user_profile_retries_without_optional_metadata_when_columns_are_missing(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_rest_upsert(table: str, payload: dict[str, object], *, on_conflict: str) -> None:
            calls.append({"table": table, "payload": dict(payload), "on_conflict": on_conflict})
            if len(calls) == 1:
                raise _AuthError("Could not find the 'created_by_user_id' column of 'user_profiles' in the schema cache")

        ensure_user_profile(
            user_id="new-user",
            email="user@example.com",
            display_name="User",
            created_by_user_id="admin-user",
            password_setup_mode="admin_set",
            force_password_change=False,
            get_user_profile_fn=lambda **_: None,
            request_json_fn=lambda **_: self.fail("request_json should not be used"),
            rest_base_url=lambda: "https://example.invalid",
            service_api_key=lambda: "key",
            timeout_seconds=lambda: 5.0,
            rest_upsert_fn=fake_rest_upsert,
            normalize_account_status_fn=lambda value: f"acct:{value}",
            normalize_global_role_fn=lambda value: f"role:{value}",
            is_missing_relation_error_fn=lambda message, relation: relation in message and "schema cache" in message,
            is_missing_column_error_fn=lambda message, column: column in message,
            auth_error_cls=_AuthError,
        )

        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0]["payload"],
            {
                "id": "new-user",
                "email": "user@example.com",
                "display_name": "User",
                "account_status": "acct:active",
                "global_role": "role:",
                "created_by_user_id": "admin-user",
                "password_setup_mode": "admin_set",
                "force_password_change": False,
            },
        )
        self.assertEqual(
            calls[1]["payload"],
            {
                "id": "new-user",
                "email": "user@example.com",
                "display_name": "User",
                "account_status": "acct:active",
                "global_role": "role:",
            },
        )

    def test_ensure_membership_ignores_missing_relation_error(self) -> None:
        def fake_rest_upsert(*args, **kwargs):
            raise _AuthError("organization_memberships relation missing")

        ensure_membership(
            organization_id="org-1",
            user_id="user-1",
            role="org_member",
            membership_status="active",
            team_name="Sales",
            job_title="Lead",
            rest_upsert_fn=fake_rest_upsert,
            normalize_org_role_fn=lambda value: f"role:{value}",
            normalize_membership_status_fn=lambda value: f"status:{value}",
            is_missing_relation_error_fn=lambda message, relation: relation in message,
            auth_error_cls=_AuthError,
        )

    def test_sync_legacy_user_projection_upserts_normalized_legacy_payload(self) -> None:
        captured: dict[str, object] = {}

        def fake_rest_upsert(table: str, payload: dict[str, object], *, on_conflict: str) -> None:
            captured["table"] = table
            captured["payload"] = dict(payload)
            captured["on_conflict"] = on_conflict

        sync_legacy_user_projection(
            user_id="user-1",
            organization_id="org-1",
            email="user@example.com",
            display_name="User",
            membership_role="org_admin",
            membership_status="active",
            rest_upsert_fn=fake_rest_upsert,
            map_membership_role_to_legacy_role_fn=lambda value: f"legacy:{value}",
            normalize_membership_status_fn=lambda value: f"status:{value}",
        )

        self.assertEqual(captured["table"], "users")
        self.assertEqual(captured["on_conflict"], "id")
        self.assertEqual(
            captured["payload"],
            {
                "id": "user-1",
                "organization_id": "org-1",
                "email": "user@example.com",
                "display_name": "User",
                "role": "legacy:org_admin",
                "status": "status:active",
            },
        )

    def test_update_local_user_profile_falls_back_to_legacy_users_patch_and_syncs_projection(self) -> None:
        calls: list[dict[str, object]] = []
        sync_calls: list[dict[str, object]] = []

        def fake_request_json(**kwargs):
            calls.append(dict(kwargs))
            if kwargs["path"] == "/user_profiles":
                raise _AuthError("user_profiles relation missing")
            return [{"id": "user-1"}], {}

        profile = update_local_user_profile(
            user_id="user-1",
            email="user@example.com",
            display_name="Updated User",
            mobile_phone="010-1111-2222",
            office_phone="02-123-4567",
            request_json_fn=fake_request_json,
            rest_base_url=lambda: "https://example.invalid",
            service_api_key=lambda: "key",
            timeout_seconds=lambda: 5.0,
            auth_error_cls=_AuthError,
            is_missing_relation_error_fn=lambda message, relation: relation in message,
            get_local_user_fn=lambda **_: {
                "organization_id": "org-1",
                "role": "org_member",
                "membership_status": "active",
            },
            sync_legacy_user_projection_fn=lambda **kwargs: sync_calls.append(dict(kwargs)),
            get_user_profile_fn=lambda **_: {"id": "user-1", "display_name": "Updated User"},
            default_phase1_org_id="phase1-org",
        )

        self.assertEqual([call["path"] for call in calls], ["/user_profiles", "/users"])
        self.assertEqual(calls[1]["payload"], {"display_name": "Updated User"})
        self.assertEqual(
            sync_calls,
            [
                {
                    "user_id": "user-1",
                    "organization_id": "org-1",
                    "email": "user@example.com",
                    "display_name": "Updated User",
                    "membership_role": "org_member",
                    "membership_status": "active",
                }
            ],
        )
        self.assertEqual(profile, {"id": "user-1", "display_name": "Updated User"})


if __name__ == "__main__":
    unittest.main()
