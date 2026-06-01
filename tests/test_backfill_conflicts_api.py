from __future__ import annotations

from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from fastapi.testclient import TestClient

import backend.api.app as app_module
from backend.repositories.in_memory_backfill_conflicts import InMemoryBackfillConflictRepository
from backend.sales_claims import SalesActor


ORGANIZATION_ID = UUID("5d2aa9d7-9486-4af1-a8f1-8e8f8f120001")
TRACKER_ENTRY_ID = UUID("b8aa3b59-d1cf-4c0d-ae2d-0c1fcb960001")
OTHER_TRACKER_ENTRY_ID = UUID("b8aa3b59-d1cf-4c0d-ae2d-0c1fcb960002")
PROJECT_ID = UUID("1a1d2699-bdeb-41f9-8a31-08169f090001")
SOURCE_RUN_ID = UUID("8ea18a2f-d77d-49c6-a5cb-3aa76f890001")
OTHER_SOURCE_RUN_ID = UUID("8ea18a2f-d77d-49c6-a5cb-3aa76f890002")


def _tracker_entry(*, entry_id: UUID = TRACKER_ENTRY_ID) -> dict[str, object]:
    return {
        "id": entry_id,
        "organization_id": ORGANIZATION_ID,
        "project_id": PROJECT_ID,
        "project_name": "Example Project",
        "entry_key": f"BID123|001|{entry_id}",
    }


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


class BackfillConflictsApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app_module.app)
        self.repository = InMemoryBackfillConflictRepository()
        self.conflict_id = uuid4()
        detected_at = datetime(2026, 3, 27, 10, 0, tzinfo=timezone.utc)
        self.repository._rows_by_id[self.conflict_id] = {  # type: ignore[attr-defined]
            "id": self.conflict_id,
            "organization_id": ORGANIZATION_ID,
            "tracker_entry_id": TRACKER_ENTRY_ID,
            "field_name": "demand_contact",
            "current_value": "portal/02-6010-1022",
            "candidate_value": "tourism-team/054-420-6136",
            "current_value_norm": "0260101022",
            "candidate_value_norm": "0544206136",
            "reason_code": "valid_contact_protected",
            "source_kind": "backfill",
            "source_ref": "dry_run_row_1",
            "source_run_id": SOURCE_RUN_ID,
            "extractor_version": "safe_backfill_mvp_v1",
            "detected_at": detected_at,
            "resolved_at": None,
            "resolution": None,
            "conflict_key": "entry:demand_contact:test",
        }
        other_id = uuid4()
        self.repository._rows_by_id[other_id] = {  # type: ignore[attr-defined]
            "id": other_id,
            "organization_id": ORGANIZATION_ID,
            "tracker_entry_id": OTHER_TRACKER_ENTRY_ID,
            "field_name": "demand_contact",
            "current_value": "portal/02-6010-1022",
            "candidate_value": "tourism-team/054-420-6136",
            "current_value_norm": "0260101022",
            "candidate_value_norm": "0544206136",
            "reason_code": "valid_contact_protected",
            "source_kind": "backfill",
            "source_ref": "dry_run_row_2",
            "source_run_id": OTHER_SOURCE_RUN_ID,
            "extractor_version": "safe_backfill_mvp_v1",
            "detected_at": detected_at,
            "resolved_at": None,
            "resolution": None,
            "conflict_key": "entry:demand_contact:test-2",
        }

    def test_list_backfill_conflicts_returns_open_items(self) -> None:
        fake_tracker_repository = SimpleNamespace(get_entry=lambda entry_id: _tracker_entry(entry_id=entry_id))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_request_organization_id", return_value=ORGANIZATION_ID),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "get_backfill_conflict_repository", return_value=self.repository),
            patch.object(app_module, "_get_tracker_repository", return_value=fake_tracker_repository),
        ):
            response = self.client.get("/api/backfill-conflicts?limit=10")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 2)
        self.assertTrue(payload["items"])
        self.assertEqual(
            {item["tracker_entry_id"] for item in payload["items"]},
            {str(TRACKER_ENTRY_ID), str(OTHER_TRACKER_ENTRY_ID)},
        )
        self.assertTrue(all(item["project_name"] == "Example Project" for item in payload["items"]))

    def test_list_backfill_conflicts_filters_by_tracker_entry_id(self) -> None:
        fake_tracker_repository = SimpleNamespace(get_entry=lambda entry_id: _tracker_entry(entry_id=entry_id))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_request_organization_id", return_value=ORGANIZATION_ID),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "get_backfill_conflict_repository", return_value=self.repository),
            patch.object(app_module, "_get_tracker_repository", return_value=fake_tracker_repository),
        ):
            response = self.client.get(f"/api/backfill-conflicts?limit=10&tracker_entry_id={TRACKER_ENTRY_ID}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["tracker_entry_id"], str(TRACKER_ENTRY_ID))

    def test_resolve_backfill_conflict_sets_resolution(self) -> None:
        fake_tracker_repository = SimpleNamespace(get_entry=lambda entry_id: _tracker_entry(entry_id=entry_id))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_request_organization_id", return_value=ORGANIZATION_ID),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "get_backfill_conflict_repository", return_value=self.repository),
            patch.object(app_module, "_get_tracker_repository", return_value=fake_tracker_repository),
        ):
            response = self.client.post(
                f"/api/backfill-conflicts/{self.conflict_id}/resolve",
                json={"resolution": "keep_current"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["resolution"], "keep_current")
        self.assertIsNotNone(payload["resolved_at"])

    def test_resolve_backfill_conflict_rejects_unknown_resolution(self) -> None:
        fake_tracker_repository = SimpleNamespace(get_entry=lambda entry_id: _tracker_entry(entry_id=entry_id))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(_admin_actor())),
            patch.object(app_module, "_resolve_request_organization_id", return_value=ORGANIZATION_ID),
            patch.object(app_module, "_resolve_sales_actor", return_value=_admin_actor()),
            patch.object(app_module, "get_backfill_conflict_repository", return_value=self.repository),
            patch.object(app_module, "_get_tracker_repository", return_value=fake_tracker_repository),
        ):
            response = self.client.post(
                f"/api/backfill-conflicts/{self.conflict_id}/resolve",
                json={"resolution": "bad_value"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_list_backfill_conflicts_requires_admin(self) -> None:
        non_admin = SalesActor(
            organization_id=ORGANIZATION_ID,
            user_id=None,
            email="member@example.com",
            display_name="Member",
            role="org_member",
        )
        fake_tracker_repository = SimpleNamespace(get_entry=lambda entry_id: _tracker_entry(entry_id=entry_id))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context(non_admin)),
            patch.object(app_module, "_resolve_request_organization_id", return_value=ORGANIZATION_ID),
            patch.object(app_module, "_resolve_sales_actor", return_value=non_admin),
            patch.object(app_module, "get_backfill_conflict_repository", return_value=self.repository),
            patch.object(app_module, "_get_tracker_repository", return_value=fake_tracker_repository),
        ):
            response = self.client.get("/api/backfill-conflicts?limit=10")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "auth_forbidden")
