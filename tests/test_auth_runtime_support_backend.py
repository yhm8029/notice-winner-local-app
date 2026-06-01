from __future__ import annotations

import unittest
from datetime import timezone

from backend.services.auth_runtime_support_backend import is_missing_column_error
from backend.services.auth_runtime_support_backend import is_missing_relation_error
from backend.services.auth_runtime_support_backend import map_membership_role_to_legacy_role
from backend.services.auth_runtime_support_backend import normalize_email
from backend.services.auth_runtime_support_backend import normalize_global_role
from backend.services.auth_runtime_support_backend import normalize_local_user_status
from backend.services.auth_runtime_support_backend import normalize_membership_status
from backend.services.auth_runtime_support_backend import normalize_org_role
from backend.services.auth_runtime_support_backend import parse_datetime_value


class AuthRuntimeSupportBackendTests(unittest.TestCase):
    def test_normalize_local_user_status_prefers_inactive(self) -> None:
        self.assertEqual(normalize_local_user_status("inactive"), "inactive")
        self.assertEqual(normalize_local_user_status("active"), "active")

    def test_parse_datetime_value_handles_z_suffix(self) -> None:
        parsed = parse_datetime_value("2026-03-29T12:34:56Z")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.isoformat(), "2026-03-29T12:34:56+00:00")

    def test_normalize_org_role_and_global_role_keep_only_allowed_values(self) -> None:
        self.assertEqual(normalize_org_role("ORG_ADMIN", valid_org_roles={"org_admin", "org_member"}), "org_admin")
        self.assertEqual(normalize_org_role("weird", valid_org_roles={"org_admin", "org_member"}), "org_member")
        self.assertEqual(normalize_global_role("platform_admin"), "platform_admin")
        self.assertEqual(normalize_global_role("org_admin"), "")
        self.assertEqual(normalize_membership_status("deactivated"), "deactivated")

    def test_error_classifiers_detect_relation_and_column_messages(self) -> None:
        self.assertTrue(is_missing_relation_error("relation user_profiles does not exist", "user_profiles"))
        self.assertTrue(is_missing_column_error("column status does not exist", "status"))
        self.assertFalse(is_missing_relation_error("timeout", "user_profiles"))

    def test_map_membership_role_to_legacy_role_and_normalize_email(self) -> None:
        self.assertEqual(
            map_membership_role_to_legacy_role(
                "ORG_ADMIN",
                normalize_org_role_fn=lambda value: normalize_org_role(value, valid_org_roles={"org_admin", "org_member"}),
            ),
            "admin",
        )
        self.assertEqual(
            map_membership_role_to_legacy_role(
                "unknown",
                normalize_org_role_fn=lambda value: normalize_org_role(value, valid_org_roles={"org_admin", "org_member"}),
            ),
            "member",
        )
        self.assertEqual(normalize_email("  USER@Example.COM "), "user@example.com")


if __name__ == "__main__":
    unittest.main()
