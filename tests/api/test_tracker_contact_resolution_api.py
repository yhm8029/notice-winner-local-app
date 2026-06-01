from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

import backend.api.app as app_module
from backend.sales_claims import SalesActor


ORGANIZATION_ID = UUID("5d2aa9d7-9486-4af1-a8f1-8e8f8f120001")


def _admin_actor() -> SalesActor:
    return SalesActor(
        organization_id=ORGANIZATION_ID,
        user_id=None,
        email="admin@example.com",
        display_name="Admin",
        role="org_admin",
    )


def _auth_context(actor: SalesActor) -> SimpleNamespace:
    return SimpleNamespace(
        authorized=True,
        organization_id=actor.organization_id,
        local_user_id=actor.user_id,
        email=actor.email,
        display_name=actor.display_name,
        role=actor.role,
    )


class TrackerContactResolutionApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app_module.app)

    def test_summary_returns_payload_for_admin(self) -> None:
        payload = {
            "total_entries": 2,
            "status_counts": [{"status": "resolved", "count": 1}, {"status": "review", "count": 1}],
            "reason_counts": [{"reason": "explicit_owner_org_match", "count": 1}],
            "items": [
                {
                    "entry_id": "11111111-1111-1111-1111-111111111111",
                    "source_run_id": None,
                    "source_tracker_run_id": None,
                    "project_name": "Example Project",
                    "demand_org_name": "Org A",
                    "demand_contact": "시설과/02-1111-1111",
                    "resolution_status": "resolved",
                    "resolution_reason": "explicit_owner_org_match",
                    "resolution_phase": "notice",
                    "resolution_role": "owner_contact",
                    "resolution_owner_side": "yes",
                    "resolution_owner_side_basis": "explicit_owner_org_match",
                    "updated_at": None,
                }
            ],
        }
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "_build_tracker_contact_resolution_summary", return_value=payload),
        ):
            response = self.client.get("/api/admin/tracker-contact-resolution-summary?limit=5")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_entries"], 2)
        self.assertEqual(body["status_counts"][0]["status"], "resolved")
        self.assertEqual(body["items"][0]["project_name"], "Example Project")

    def test_summary_requires_admin(self) -> None:
        member = SalesActor(
            organization_id=ORGANIZATION_ID,
            user_id=None,
            email="member@example.com",
            display_name="Member",
            role="org_member",
        )
        with patch.object(app_module, "_resolve_sales_actor", return_value=member):
            with patch.object(app_module, "read_auth_context", return_value=_auth_context(member)):
                response = self.client.get("/api/admin/tracker-contact-resolution-summary?limit=5")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "auth_forbidden")
