from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

import backend.api.app as app_module


REQUEST_ORG_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OTHER_ORG_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
ENTRY_ID = UUID("11111111-2222-3333-4444-555555555555")


def _auth_context() -> SimpleNamespace:
    return SimpleNamespace(
        authorized=True,
        organization_id=REQUEST_ORG_ID,
        local_user_id=UUID("99999999-9999-9999-9999-999999999999"),
        email="member@example.com",
        display_name="Member",
        role="org_member",
    )


def _tracker_row(*, organization_id: UUID) -> dict[str, object]:
    return {
        "id": ENTRY_ID,
        "organization_id": organization_id,
        "source_run_id": UUID("66666666-6666-6666-6666-666666666666"),
        "source_tracker_run_id": UUID("77777777-7777-7777-7777-777777777777"),
        "project_search_name": "scoped project",
        "entry_key": "bid-1|000|sample",
        "sheet_name": "최근점검현황(15개)",
        "section_name": "default",
        "row_no": 1,
        "source_bid_no": "BID-1",
        "source_bid_ord": "000",
        "source_project_name_norm": "scoped project",
        "project_name": "Scoped Project",
        "gross_area_scale": "1000",
        "construction_cost": "2000",
        "demand_org_name": "Agency",
        "demand_contact": "Contact",
        "client_location": "Seoul",
        "site_location_1": "Seoul",
        "site_location_2": "",
        "architect_office": "Office",
        "opening_scheduled_date": "",
        "construction_start_date": "2026-04-01",
        "contract_date": "",
        "construction_duration_days": "",
        "completion_expected_date_explicit": "",
        "completion_expected_date_computed": "",
        "last_checked_date": "2026-04-02",
        "progress_note": "",
        "notice_date": "2026-04-01",
        "manager_name": "Kim",
        "building_automation_estimated_amount": "1000000",
        "overridden_fields": [],
        "has_overrides": False,
        "created_at": "2026-04-01T00:00:00+00:00",
        "updated_at": "2026-04-01T00:00:00+00:00",
    }


class _FakeTrackerRepository:
    def __init__(self, row: dict[str, object]) -> None:
        self._row = row

    def list_entry_summaries(self, **kwargs):  # type: ignore[no-untyped-def]
        del kwargs
        return [dict(self._row)], 1

    def list_entries(self, **kwargs):  # type: ignore[no-untyped-def]
        del kwargs
        return [dict(self._row)], 1

    def get_entry(self, entry_id):  # type: ignore[no-untyped-def]
        if entry_id == ENTRY_ID:
            return dict(self._row)
        return None

    def list_audit_logs(self, *, entry_id, cursor, limit):  # type: ignore[no-untyped-def]
        del entry_id, cursor, limit
        return [], None


class TrackerAccessScopeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app_module.app)

    def test_tracker_entry_summaries_filter_rows_to_request_organization(self) -> None:
        repository = _FakeTrackerRepository(_tracker_row(organization_id=OTHER_ORG_ID))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context()),
            patch.object(app_module, "_get_tracker_repository", return_value=repository),
            patch.object(app_module, "_resolve_request_organization_id", return_value=REQUEST_ORG_ID),
            patch.object(app_module, "_hydrate_tracker_entry_summary_rows", side_effect=lambda organization_id, rows: rows),
        ):
            response = self.client.get("/api/tracker-entry-summaries?page=1&page_size=20&source_tracker_run_id=77777777-7777-7777-7777-777777777777")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["items"], [])
        self.assertEqual(payload["total"], 0)

    def test_tracker_entry_summaries_include_site_location_2_for_same_organization(self) -> None:
        repository = _FakeTrackerRepository(_tracker_row(organization_id=REQUEST_ORG_ID))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context()),
            patch.object(app_module, "_get_tracker_repository", return_value=repository),
            patch.object(app_module, "_resolve_request_organization_id", return_value=REQUEST_ORG_ID),
            patch.object(app_module, "_hydrate_tracker_entry_summary_rows", side_effect=lambda organization_id, rows: rows),
        ):
            response = self.client.get("/api/tracker-entry-summaries?page=1&page_size=20&source_tracker_run_id=77777777-7777-7777-7777-777777777777")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["items"][0]["site_location_2"], "")

    def test_tracker_entry_detail_returns_not_found_for_other_organization(self) -> None:
        repository = _FakeTrackerRepository(_tracker_row(organization_id=OTHER_ORG_ID))
        with (
            patch.object(app_module, "read_auth_context", return_value=_auth_context()),
            patch.object(app_module, "_get_tracker_repository", return_value=repository),
            patch.object(app_module, "_resolve_request_organization_id", return_value=REQUEST_ORG_ID),
            patch.object(app_module, "_hydrate_tracker_entry_detail_row", side_effect=lambda organization_id, row: row),
        ):
            response = self.client.get(f"/api/tracker-entries/{ENTRY_ID}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "not_found")
