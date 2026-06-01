from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

import backend.api.app as app_module
from backend.sales_claims import SalesActor


ORGANIZATION_ID = UUID("7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001")
TRACKER_RUN_ID = UUID("22222222-2222-2222-2222-222222222222")


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


class TrackerCleanupApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app_module.app)

    def test_cleanup_preview_requires_admin_auth(self) -> None:
        actor = SalesActor(
            organization_id=ORGANIZATION_ID,
            user_id=None,
            email="member@example.com",
            display_name="Member",
            role="org_member",
        )
        with patch.object(app_module, "_resolve_sales_actor", return_value=actor):
            with patch.object(app_module, "read_auth_context", return_value=_auth_context(actor)):
                response = self.client.get(f"/api/admin/tracker-cleanup/preview?source_tracker_run_id={TRACKER_RUN_ID}")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "auth_forbidden")

    def test_cleanup_preview_returns_affected_counts(self) -> None:
        preview_payload = {
            "source_tracker_run_id": str(TRACKER_RUN_ID),
            "parent_run_id": "11111111-1111-1111-1111-111111111111",
            "tracker_entry_count": 1,
            "child_run_count": 1,
            "parent_run_count": 1,
            "log_count": 2,
            "artifact_count": 2,
        }
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "_preview_tracker_cleanup", return_value=preview_payload),
        ):
            response = self.client.get(f"/api/admin/tracker-cleanup/preview?source_tracker_run_id={TRACKER_RUN_ID}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tracker_entry_count"], 1)

    def test_cleanup_apply_executes_cleanup(self) -> None:
        apply_payload = {
            "source_tracker_run_id": str(TRACKER_RUN_ID),
            "parent_run_id": "11111111-1111-1111-1111-111111111111",
            "deleted_tracker_entry_count": 1,
            "deleted_run_count": 2,
            "deleted_log_count": 2,
            "deleted_artifact_count": 2,
        }
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "_apply_tracker_cleanup", return_value=apply_payload),
        ):
            response = self.client.post(
                "/api/admin/tracker-cleanup/apply",
                json={"source_tracker_run_id": str(TRACKER_RUN_ID)},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_run_count"], 2)
