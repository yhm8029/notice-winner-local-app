from __future__ import annotations

import time
import unittest
from typing import Any

from backend.services import auth_invitation_read_backend


class DummyAuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "auth_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class AuthInvitationReadBackendTests(unittest.TestCase):
    def test_list_invitations_expires_stale_rows_and_can_filter_pending_only(self) -> None:
        captured: dict[str, Any] = {}
        expired: dict[str, Any] = {}

        rows = auth_invitation_read_backend.list_invitations(
            organization_id="org-1",
            include_non_pending=False,
            expire_stale_invitations=lambda **kwargs: expired.update(kwargs),
            request_json=lambda **kwargs: (
                captured.update({"query": list(kwargs.get("query") or [])}) or [
                    {
                        "id": "invite-1",
                        "organization_id": "org-1",
                        "email": "member@example.com",
                        "role": "org_member",
                        "status": "pending",
                    }
                ],
                {},
            ),
            rest_base_url=lambda: "https://example.supabase.co/rest/v1",
            service_api_key=lambda: "service-key",
            timeout_seconds=lambda: 5.0,
            normalize_invitation_row=lambda row: auth_invitation_read_backend.normalize_invitation_row(
                row,
                normalize_email=lambda value: str(value or "").strip().lower(),
                normalize_org_role=lambda value: str(value or "").strip().lower(),
            ),
            auth_error_cls=DummyAuthError,
        )

        self.assertEqual(expired, {"organization_id": "org-1"})
        self.assertEqual(rows[0]["status"], "pending")
        self.assertEqual(dict(captured["query"])["status"], "eq.pending")

    def test_normalize_invitation_row_marks_expired_pending_invitation(self) -> None:
        expired = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 60))

        item = auth_invitation_read_backend.normalize_invitation_row(
            {
                "email": "Member@Example.com",
                "role": "ORG_MEMBER",
                "status": "pending",
                "expires_at": expired,
            },
            normalize_email=lambda value: str(value or "").strip().lower(),
            normalize_org_role=lambda value: str(value or "").strip().lower(),
        )

        self.assertEqual(item["email"], "member@example.com")
        self.assertEqual(item["role"], "org_member")
        self.assertEqual(item["status"], "expired")
        self.assertEqual(item["invite_url"], "")
        self.assertEqual(item["delivery_status"], "")
        self.assertEqual(item["delivery_message"], "")

    def test_get_invitation_by_token_persists_expired_pending_status(self) -> None:
        expired = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 60))
        captured: dict[str, Any] = {}

        item = auth_invitation_read_backend.get_invitation_by_token(
            "invite-token-123",
            request_json=lambda **kwargs: (
                [
                    {
                        "id": "invite-1",
                        "email": "member@example.com",
                        "role": "org_member",
                        "status": "pending",
                        "expires_at": expired,
                    }
                ],
                {},
            ),
            rest_base_url=lambda: "https://example.supabase.co/rest/v1",
            service_api_key=lambda: "service-key",
            timeout_seconds=lambda: 5.0,
            normalize_invitation_row=lambda row: auth_invitation_read_backend.normalize_invitation_row(
                row,
                normalize_email=lambda value: str(value or "").strip().lower(),
                normalize_org_role=lambda value: str(value or "").strip().lower(),
            ),
            persist_invitation_status=lambda **kwargs: captured.update(kwargs),
            auth_error_cls=DummyAuthError,
        )

        assert item is not None
        self.assertEqual(item["status"], "expired")
        self.assertEqual(captured, {"invitation_id": "invite-1", "status": "expired"})

    def test_get_invitation_preview_adds_org_name_and_initial_password(self) -> None:
        preview = auth_invitation_read_backend.get_invitation_preview(
            invite_token="invite-token-123",
            get_invitation_by_token=lambda token: {
                "organization_id": "org-1",
                "email": "member@example.com",
                "invite_token": token,
                "status": "pending",
            },
            get_organization=lambda organization_id: {"name": "Internal Operations"} if organization_id == "org-1" else {},
            build_invitation_initial_password=lambda token: f"pw-{token}",
            auth_error_cls=DummyAuthError,
        )

        self.assertEqual(preview["organization_name"], "Internal Operations")
        self.assertEqual(preview["initial_password"], "pw-invite-token-123")

    def test_get_invitation_preview_by_email_rejects_ambiguous_pending_invites(self) -> None:
        with self.assertRaises(DummyAuthError) as ctx:
            auth_invitation_read_backend.get_invitation_preview_by_email(
                email="member@example.com",
                list_pending_invitations_by_email=lambda **kwargs: [
                    {"organization_id": "org-1"},
                    {"organization_id": "org-2"},
                ],
                get_organization=lambda organization_id: {"name": organization_id},
                auth_error_cls=DummyAuthError,
            )

        self.assertEqual(ctx.exception.code, "invite_ambiguous")

    def test_get_invitation_preview_by_email_adds_organization_name(self) -> None:
        preview = auth_invitation_read_backend.get_invitation_preview_by_email(
            email="member@example.com",
            list_pending_invitations_by_email=lambda **kwargs: [
                {
                    "organization_id": "org-1",
                    "email": "member@example.com",
                    "status": "pending",
                }
            ],
            get_organization=lambda organization_id: {"name": "Internal Operations"} if organization_id == "org-1" else {},
            auth_error_cls=DummyAuthError,
        )

        self.assertEqual(preview["organization_name"], "Internal Operations")
        self.assertEqual(preview["email"], "member@example.com")

    def test_get_invitation_by_id_normalizes_matching_row(self) -> None:
        item = auth_invitation_read_backend.get_invitation_by_id(
            organization_id="org-1",
            invitation_id="invite-1",
            request_json=lambda **kwargs: (
                [
                    {
                        "id": "invite-1",
                        "organization_id": "org-1",
                        "email": "Member@Example.com",
                        "role": "ORG_MEMBER",
                        "status": "pending",
                    }
                ],
                {},
            ),
            rest_base_url=lambda: "https://example.supabase.co/rest/v1",
            service_api_key=lambda: "service-key",
            timeout_seconds=lambda: 5.0,
            normalize_invitation_row=lambda row: auth_invitation_read_backend.normalize_invitation_row(
                row,
                normalize_email=lambda value: str(value or "").strip().lower(),
                normalize_org_role=lambda value: str(value or "").strip().lower(),
            ),
            auth_error_cls=DummyAuthError,
        )

        assert item is not None
        self.assertEqual(item["email"], "member@example.com")
        self.assertEqual(item["role"], "org_member")


if __name__ == "__main__":
    unittest.main()
