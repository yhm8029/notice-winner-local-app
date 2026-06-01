from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.app import ApiError
from backend.repositories.tracker_change_events import TrackerChangeEventRepositoryError
from backend.api.support import tracker_read_support
from tests.api.test_phase1_api import ApiServer
from tests.api.test_phase1_api_behavior import _project_tracker_run_payload


def _auth_context(organization_id):  # type: ignore[no-untyped-def]
    return SimpleNamespace(
        authorized=True,
        organization_id=organization_id,
        local_user_id=uuid4(),
        email="admin@example.com",
        display_name="Admin",
        role="platform_admin",
    )


class TrackerChangeEventsApiTests(unittest.TestCase):
    def test_missing_tracker_change_events_table_degrades_to_empty_payload(self) -> None:
        class _MissingTableRepository:
            def count_unread(self, *, organization_id):
                raise TrackerChangeEventRepositoryError(
                    "Could not find the table 'public.tracker_change_events' in the schema cache"
                )

            def list_events(self, *, organization_id, limit, tracker_entry_id=None, include_silent=False):
                raise TrackerChangeEventRepositoryError(
                    "relation \"tracker_change_events\" does not exist"
                )

        with ApiServer() as server, patch(
            "backend.api.app._get_tracker_change_event_repository",
            return_value=_MissingTableRepository(),
        ):
            unread_status, unread_payload = server.request_json("GET", "/api/tracker-change-events/unread-count")
            self.assertEqual(unread_status, 200)
            self.assertEqual(int(unread_payload["unread_count"]), 0)

            list_status, list_payload = server.request_json("GET", "/api/tracker-change-events?limit=20")
            self.assertEqual(list_status, 200)
            self.assertEqual(list_payload["total"], 0)
            self.assertEqual(list_payload["items"], [])

    def test_repository_config_error_degrades_to_empty_payload(self) -> None:
        with ApiServer() as server, patch(
            "backend.api.app._get_tracker_change_event_repository",
            side_effect=ApiError(status_code=503, code="repository_error", message="tracker change events unavailable"),
        ):
            unread_status, unread_payload = server.request_json("GET", "/api/tracker-change-events/unread-count")
            self.assertEqual(unread_status, 200)
            self.assertEqual(int(unread_payload["unread_count"]), 0)

            list_status, list_payload = server.request_json("GET", "/api/tracker-change-events?limit=20")
            self.assertEqual(list_status, 200)
            self.assertEqual(list_payload["total"], 0)
            self.assertEqual(list_payload["items"], [])

    def test_manual_patch_creates_change_event_and_mark_read_clears_unread(self) -> None:
        with ApiServer(
            env_overrides={
                "PHASE2_AUTH_ENABLED": "0",
                "BOOTSTRAP_PLATFORM_ADMIN_EMAIL": "",
                "SUPABASE_URL": "",
                "SUPABASE_SECRET_KEY": "",
                "SUPABASE_SERVICE_ROLE_KEY": "",
                "SUPABASE_ANON_KEY": "",
            }
        ) as server:
            create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
            self.assertEqual(create_status, 201)
            server.wait_for_run(create_payload["id"], target_statuses={"success"})

            tracker_status, tracker_payload = server.request_json(
                "POST",
                f"/api/runs/{create_payload['id']}/tracker-export",
            )
            self.assertEqual(tracker_status, 202)
            server.wait_for_run(tracker_payload["id"], target_statuses={"success"})

            entries_status, entries_payload = server.request_json(
                "GET",
                f"/api/tracker-entries?source_tracker_run_id={tracker_payload['id']}&page=1&page_size=20",
            )
            self.assertEqual(entries_status, 200)
            entry = entries_payload["items"][0]

            unread_status_before, unread_payload_before = server.request_json("GET", "/api/tracker-change-events/unread-count")
            self.assertEqual(unread_status_before, 200)
            unread_before = int(unread_payload_before["unread_count"])

            patch_status, patch_payload = server.request_json(
                "PATCH",
                f"/api/tracker-entries/{entry['id']}",
                payload={
                    "field_name": "project_name",
                    "value": "Project Name Final",
                    "actor_label": "phase1-tester",
                    "change_source": "web",
                },
            )
            self.assertEqual(patch_status, 200)
            self.assertTrue(patch_payload["changed"])

            list_status, list_payload = server.request_json("GET", "/api/tracker-change-events?limit=10")
            self.assertEqual(list_status, 200)
            self.assertGreaterEqual(list_payload["total"], 1)
            event = list_payload["items"][0]
            self.assertEqual(event["event_type"], "manual_updated")
            self.assertEqual(event["field_name"], "project_name")
            self.assertEqual(event["tracker_entry_id"], entry["id"])
            self.assertTrue(event["project_name"])

            unread_status_after, unread_payload_after = server.request_json("GET", "/api/tracker-change-events/unread-count")
            self.assertEqual(unread_status_after, 200)
            self.assertEqual(int(unread_payload_after["unread_count"]), unread_before + 1)

            mark_status, mark_payload = server.request_json(
                "POST",
                "/api/tracker-change-events/mark-read",
                payload={"tracker_entry_id": entry["id"]},
            )
            self.assertEqual(mark_status, 200)
            self.assertGreaterEqual(int(mark_payload["updated_count"]), 1)

            unread_status_final, unread_payload_final = server.request_json("GET", "/api/tracker-change-events/unread-count")
            self.assertEqual(unread_status_final, 200)
            self.assertEqual(int(unread_payload_final["unread_count"]), unread_before)

    def test_list_tracker_change_events_uses_snapshot_repository_before_entry_fallback(self) -> None:
        organization_id = uuid4()
        tracker_entry_id = uuid4()
        event_id = uuid4()
        target_tracker_entry_id = tracker_entry_id
        tracker_entry_calls: list[UUID] = []

        class _EventRepository:
            def list_events(self, *, organization_id, limit, tracker_entry_id=None, include_silent=False):
                return [
                    {
                        "id": str(event_id),
                        "tracker_entry_id": str(target_tracker_entry_id),
                        "event_type": "manual_updated",
                        "field_name": "project_name",
                        "old_value": "Old",
                        "new_value": "New",
                        "old_value_norm": "old",
                        "new_value_norm": "new",
                        "source_run_id": None,
                        "source_kind": "web",
                        "source_ref": "tester",
                        "extractor_version": "",
                        "reason_code": "",
                        "batch_key": "",
                        "is_silent": False,
                        "created_at": "2026-04-07T00:00:00+00:00",
                        "is_read": False,
                        "read_at": None,
                    }
                ]

        class _SnapshotRepository:
            def get_snapshots(self, *, organization_id, tracker_entry_ids):
                return [
                    {
                        "tracker_entry_id": tracker_entry_id,
                        "organization_id": organization_id,
                        "updated_at": "2026-04-07T00:00:00+00:00",
                        "detail_json": {
                            "id": str(tracker_entry_id),
                            "project_id": str(uuid4()),
                            "project_name": "Snapshot Project",
                            "entry_key": "entry-001",
                        },
                    }
                ]

        class _EntryRepository:
            def get_entry(self, entry_id):
                tracker_entry_calls.append(entry_id)
                return {
                    "id": str(entry_id),
                    "project_id": str(uuid4()),
                    "project_name": "Live Entry Project",
                    "entry_key": "entry-live",
                    "updated_at": "2026-04-06T00:00:00+00:00",
                }

        with TestClient(app) as client, patch(
            "backend.api.app._get_tracker_change_event_repository",
            return_value=_EventRepository(),
        ), patch(
            "backend.api.app.read_auth_context",
            return_value=_auth_context(organization_id),
        ), patch.object(
            tracker_read_support,
            "get_tracker_entry_snapshot_repository",
            return_value=_SnapshotRepository(),
        ), patch(
            "backend.api.app._get_tracker_repository",
            return_value=_EntryRepository(),
        ), patch(
            "backend.api.app._resolve_request_organization_id",
            return_value=organization_id,
        ):
            response = client.get("/api/tracker-change-events?limit=20")
            list_status, list_payload = response.status_code, response.json()

        self.assertEqual(list_status, 200)
        self.assertEqual(list_payload["total"], 1)
        self.assertEqual([str(item) for item in tracker_entry_calls], [str(tracker_entry_id)])
        self.assertEqual(list_payload["items"][0]["project_name"], "Snapshot Project")
        self.assertEqual(list_payload["items"][0]["entry_key"], "entry-001")

    def test_list_tracker_change_events_falls_back_to_entry_repository_when_snapshot_missing(self) -> None:
        organization_id = uuid4()
        tracker_entry_id = uuid4()
        event_id = uuid4()
        target_tracker_entry_id = tracker_entry_id

        class _EventRepository:
            def list_events(self, *, organization_id, limit, tracker_entry_id=None, include_silent=False):
                return [
                    {
                        "id": str(event_id),
                        "tracker_entry_id": str(target_tracker_entry_id),
                        "event_type": "manual_updated",
                        "field_name": "project_name",
                        "old_value": "Old",
                        "new_value": "New",
                        "old_value_norm": "old",
                        "new_value_norm": "new",
                        "source_run_id": None,
                        "source_kind": "web",
                        "source_ref": "tester",
                        "extractor_version": "",
                        "reason_code": "",
                        "batch_key": "",
                        "is_silent": False,
                        "created_at": "2026-04-07T00:00:00+00:00",
                        "is_read": False,
                        "read_at": None,
                    }
                ]

        class _SnapshotRepository:
            def get_snapshots(self, *, organization_id, tracker_entry_ids):
                return []

        class _EntryRepository:
            def get_entry(self, entry_id):
                self.called_with = entry_id
                return {
                    "id": str(entry_id),
                    "project_id": str(uuid4()),
                    "project_name": "Entry Project",
                    "entry_key": "entry-002",
                }

        entry_repository = _EntryRepository()

        with TestClient(app) as client, patch(
            "backend.api.app._get_tracker_change_event_repository",
            return_value=_EventRepository(),
        ), patch(
            "backend.api.app.read_auth_context",
            return_value=_auth_context(organization_id),
        ), patch.object(
            tracker_read_support,
            "get_tracker_entry_snapshot_repository",
            return_value=_SnapshotRepository(),
        ), patch(
            "backend.api.app._get_tracker_repository",
            return_value=entry_repository,
        ), patch(
            "backend.api.app._resolve_request_organization_id",
            return_value=organization_id,
        ):
            response = client.get("/api/tracker-change-events?limit=20")
            list_status, list_payload = response.status_code, response.json()

        self.assertEqual(list_status, 200)
        self.assertEqual(list_payload["items"][0]["project_name"], "Entry Project")
        self.assertEqual(str(entry_repository.called_with), str(tracker_entry_id))


if __name__ == "__main__":
    unittest.main()
