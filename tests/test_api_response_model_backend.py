from __future__ import annotations

import unittest

from backend.api.schemas import AuthInvitationItem
from backend.api.schemas import AuthOrganizationPlanSummary
from backend.api.schemas import AuthOrganizationUserItem
from backend.api.schemas import SalesClaimSummaryProjectItem
from backend.api.schemas import SalesClaimSummaryUserItem
from backend.services import api_response_model_backend


class ApiResponseModelBackendTests(unittest.TestCase):
    class _LegacyModel:
        def dict(self):
            return {"kind": "dict"}

        def json(self):
            return '{"kind":"json"}'

    def test_to_auth_invitation_model_builds_invite_url(self) -> None:
        item = api_response_model_backend.to_auth_invitation_model(
            invite_url_base="https://example.com",
            item={
                "id": "11111111-1111-1111-1111-111111111111",
                "organization_id": "22222222-2222-2222-2222-222222222222",
                "invite_token": "invite-token-123",
                "email": "member@example.com",
                "role": "org_member",
                "expires_at": "2026-03-29T12:00:00Z",
                "created_at": "2026-03-29T12:00:00Z",
                "updated_at": "2026-03-29T12:00:00Z",
            },
            auth_invitation_item_cls=AuthInvitationItem,
        )

        self.assertEqual(item.invite_url, "https://example.com/app/?invite_token=invite-token-123")
        self.assertEqual(item.email, "member@example.com")

    def test_to_sales_claim_summary_user_model_wraps_nested_projects(self) -> None:
        item = api_response_model_backend.to_sales_claim_summary_user_model(
            {
                "user_id": "11111111-1111-1111-1111-111111111111",
                "user_email": "owner@example.com",
                "user_name": "Owner",
                "active_project_count": 1,
                "projects": [
                    {
                        "project_id": "22222222-2222-2222-2222-222222222222",
                        "project_name": "Demo Project",
                        "estimated_amount_text": "1억원",
                        "claimed_at": "2026-03-29T12:00:00Z",
                        "current_owner_assigned_at": "2026-03-29T12:00:00Z",
                    }
                ],
            },
            sales_claim_summary_user_item_cls=SalesClaimSummaryUserItem,
            to_sales_claim_summary_project_model=lambda project: api_response_model_backend.to_sales_claim_summary_project_model(
                project,
                sales_claim_summary_project_item_cls=SalesClaimSummaryProjectItem,
            ),
        )

        self.assertEqual(item.projects[0].project_name, "Demo Project")

    def test_model_to_json_dict_prefers_model_dump_json_mode(self) -> None:
        item = api_response_model_backend.to_auth_org_plan_summary_model(
            {
                "plan_code": "A",
                "active_user_limit": 5,
                "pending_invite_limit": 5,
                "active_user_count": 1,
                "pending_invite_count": 0,
                "next_plan_code": "B",
                "active_user_limit_reached": False,
                "pending_invite_limit_reached": False,
                "upgrade_message": "",
            },
            auth_org_plan_summary_cls=AuthOrganizationPlanSummary,
        )

        payload = api_response_model_backend.model_to_json_dict(item)

        self.assertEqual(payload["plan_code"], "A")
        self.assertEqual(payload["active_user_limit"], 5)

    def test_model_to_dict_falls_back_to_dict_method(self) -> None:
        payload = api_response_model_backend.model_to_dict(self._LegacyModel())

        self.assertEqual(payload, {"kind": "dict"})

    def test_model_to_json_dict_falls_back_to_json_method(self) -> None:
        payload = api_response_model_backend.model_to_json_dict(self._LegacyModel())

        self.assertEqual(payload, {"kind": "json"})

    def test_to_auth_org_user_model_validates_item(self) -> None:
        item = api_response_model_backend.to_auth_org_user_model(
            {
                "membership_id": "11111111-1111-1111-1111-111111111111",
                "organization_id": "22222222-2222-2222-2222-222222222222",
                "id": "33333333-3333-3333-3333-333333333333",
                "user_id": "33333333-3333-3333-3333-333333333333",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "status": "active",
                "account_status": "active",
                "membership_status": "active",
            },
            auth_org_user_item_cls=AuthOrganizationUserItem,
        )

        self.assertEqual(item.email, "member@example.com")


if __name__ == "__main__":
    unittest.main()
