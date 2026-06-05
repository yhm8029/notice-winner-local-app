from __future__ import annotations

from uuid import uuid4

from backend.api.routers import tracker_export_handlers


def _tracker_entry_row() -> dict[str, object]:
    entry_id = uuid4()
    now = "2026-01-01T00:00:00+00:00"
    return {
        "id": entry_id,
        "source_run_id": uuid4(),
        "source_tracker_run_id": uuid4(),
        "project_id": uuid4(),
        "project_search_name": "sample-project",
        "entry_key": "sample-entry",
        "sheet_name": "Sheet1",
        "section_name": "facility_cost",
        "row_no": 1,
        "source_bid_no": "R26BK00000001",
        "source_bid_ord": "000",
        "source_project_name_norm": "sample-project",
        "project_name": "Sample Project",
        "gross_area_scale": "",
        "construction_cost": "",
        "demand_org_name": "",
        "demand_contact": "",
        "client_location": "",
        "site_location_1": "",
        "site_location_2": "",
        "architect_office": "",
        "construction_start_date": "",
        "contract_date": "",
        "construction_duration_days": "",
        "completion_expected_date_explicit": "",
        "completion_expected_date_computed": "",
        "last_checked_date": "",
        "progress_note": "",
        "notice_date": "2026-01-01",
        "manager_name": "",
        "building_automation_estimated_amount": "",
        "created_at": now,
        "updated_at": now,
    }


def test_list_tracker_entries_preserves_repository_total_after_page_filter(monkeypatch) -> None:
    class Repository:
        def list_entries(self, **_kwargs):
            return [_tracker_entry_row()], 1520

    monkeypatch.setattr(tracker_export_handlers.support, "_get_tracker_repository", lambda: Repository())
    monkeypatch.setattr(tracker_export_handlers.support, "_resolve_request_organization_id", lambda _request: uuid4())
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_tracker_row_belongs_to_request_organization",
        lambda _row, *, organization_id: True,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_annotate_tracker_entries_with_project_refs",
        lambda rows: rows,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_annotate_tracker_entries_with_opening_dates",
        lambda rows: rows,
    )
    monkeypatch.setattr(
        tracker_export_handlers.support,
        "_normalize_tracker_rows_for_presentation",
        lambda rows: rows,
    )

    response = tracker_export_handlers.list_tracker_entries(
        request=object(),
        page=1,
        page_size=20,
    )

    assert len(response.items) == 1
    assert response.total == 1520
