from __future__ import annotations

import unittest

from backend.services import auth_profile_lookup_backend


class DummyAuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "auth_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class AuthProfileLookupBackendTests(unittest.TestCase):
    def test_get_local_user_builds_filters_and_normalizes_first_row(self) -> None:
        captured: dict[str, Any] = {}

        item = auth_profile_lookup_backend.get_local_user(
            user_id="user-1",
            email="member@example.com",
            organization_id="org-1",
            query_local_user_rows=lambda **kwargs: captured.update({"filters": list(kwargs["filters"])}) or [
                {"id": "user-1", "email": "member@example.com"}
            ],
            normalize_local_user_row=lambda raw: {**raw, "status": "active"},
        )

        self.assertEqual(
            captured["filters"],
            [
                ("user_id", "eq.user-1"),
                ("email", "eq.member@example.com"),
                ("organization_id", "eq.org-1"),
                ("limit", "1"),
            ],
        )
        assert item is not None
        self.assertEqual(item["status"], "active")

    def test_get_user_profile_falls_back_only_for_missing_user_profiles_relation(self) -> None:
        def _request_json(**kwargs):
            raise DummyAuthError("relation user_profiles does not exist")

        item = auth_profile_lookup_backend.get_user_profile(
            user_id="user-1",
            email="member@example.com",
            request_json=_request_json,
            rest_base_url=lambda: "https://example.supabase.co/rest/v1",
            service_api_key=lambda: "service-key",
            timeout_seconds=lambda: 5.0,
            user_profile_select_columns="id,email,account_status,global_role",
            is_missing_relation_error=lambda message, relation_name: relation_name == "user_profiles",
            build_profile_from_legacy_user=lambda **kwargs: {"id": kwargs["user_id"], "email": kwargs["email"]},
            normalize_account_status=lambda value: str(value or "").strip().lower() or "active",
            normalize_global_role=lambda value: str(value or "").strip().lower(),
            auth_error_cls=DummyAuthError,
        )

        self.assertEqual(item, {"id": "user-1", "email": "member@example.com"})

    def test_get_user_profile_normalizes_account_status_and_global_role(self) -> None:
        item = auth_profile_lookup_backend.get_user_profile(
            user_id="user-1",
            email="member@example.com",
            request_json=lambda **kwargs: (
                [{"id": "user-1", "email": "member@example.com", "account_status": "INACTIVE", "global_role": "PLATFORM_ADMIN"}],
                {},
            ),
            rest_base_url=lambda: "https://example.supabase.co/rest/v1",
            service_api_key=lambda: "service-key",
            timeout_seconds=lambda: 5.0,
            user_profile_select_columns="id,email,account_status,global_role",
            is_missing_relation_error=lambda message, relation_name: False,
            build_profile_from_legacy_user=lambda **kwargs: None,
            normalize_account_status=lambda value: str(value or "").strip().lower() or "active",
            normalize_global_role=lambda value: str(value or "").strip().lower(),
            auth_error_cls=DummyAuthError,
        )

        assert item is not None
        self.assertEqual(item["account_status"], "inactive")
        self.assertEqual(item["global_role"], "platform_admin")

    def test_get_user_profile_re_raises_non_missing_relation_errors(self) -> None:
        def _request_json(**kwargs):
            raise DummyAuthError("timeout", status_code=503, code="upstream_error")

        with self.assertRaises(DummyAuthError) as ctx:
            auth_profile_lookup_backend.get_user_profile(
                user_id="user-1",
                email="member@example.com",
                request_json=_request_json,
                rest_base_url=lambda: "https://example.supabase.co/rest/v1",
                service_api_key=lambda: "service-key",
                timeout_seconds=lambda: 5.0,
                user_profile_select_columns="id,email,account_status,global_role",
                is_missing_relation_error=lambda message, relation_name: False,
                build_profile_from_legacy_user=lambda **kwargs: {"id": kwargs["user_id"], "email": kwargs["email"]},
                normalize_account_status=lambda value: str(value or "").strip().lower() or "active",
                normalize_global_role=lambda value: str(value or "").strip().lower(),
                auth_error_cls=DummyAuthError,
            )

        self.assertEqual(ctx.exception.code, "upstream_error")

    def test_build_profile_from_legacy_user_retries_without_status_column(self) -> None:
        calls: list[str] = []

        def _request_json(**kwargs):
            query = dict(kwargs.get("query") or [])
            select_value = query.get("select")
            calls.append(str(select_value))
            if select_value == "id,email,display_name,status":
                raise DummyAuthError('column "status" does not exist')
            return ([{"id": "user-1", "email": "member@example.com", "display_name": "Member"}], {})

        item = auth_profile_lookup_backend.build_profile_from_legacy_user(
            user_id="user-1",
            email="member@example.com",
            request_json=_request_json,
            rest_base_url=lambda: "https://example.supabase.co/rest/v1",
            service_api_key=lambda: "service-key",
            timeout_seconds=lambda: 5.0,
            local_user_select_columns="id,email,display_name,status",
            local_user_fallback_select_columns="id,email,display_name",
            is_missing_column_error=lambda message, column_name: column_name == "status",
            normalize_account_status=lambda value: "active",
            normalize_global_role=lambda value: "",
            auth_error_cls=DummyAuthError,
        )

        self.assertEqual(calls, ["id,email,display_name,status", "id,email,display_name"])
        assert item is not None
        self.assertEqual(item["id"], "user-1")
        self.assertEqual(item["account_status"], "active")
        self.assertEqual(item["global_role"], "")

    def test_get_membership_row_preserves_org_scoping_and_normalizes_row(self) -> None:
        captured: dict[str, object] = {}

        item = auth_profile_lookup_backend.get_membership_row(
            organization_id="org-1",
            user_id="user-1",
            membership_id="membership-1",
            email="member@example.com",
            query_local_user_rows=lambda **kwargs: captured.update({"filters": list(kwargs["filters"])}) or [
                {
                    "membership_id": "membership-1",
                    "organization_id": "org-1",
                    "user_id": "user-1",
                    "email": "member@example.com",
                }
            ],
            normalize_local_user_row=lambda raw: {**raw, "status": "active"},
        )

        self.assertEqual(
            captured["filters"],
            [
                ("organization_id", "eq.org-1"),
                ("user_id", "eq.user-1"),
                ("membership_id", "eq.membership-1"),
                ("email", "eq.member@example.com"),
                ("limit", "1"),
            ],
        )
        assert item is not None
        self.assertEqual(item["status"], "active")


if __name__ == "__main__":
    unittest.main()
