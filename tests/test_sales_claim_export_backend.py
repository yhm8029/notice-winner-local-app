from __future__ import annotations

import unittest
from uuid import uuid4

from backend.services.sales_claim_export_backend import build_sales_claim_export_rows
from backend.services.sales_claim_export_backend import extract_latest_sales_note_text


class _Claim:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, object]:
        return dict(self._payload)


class _TrackerRepository:
    def __init__(self, tracker_entry: dict[str, object] | None) -> None:
        self.tracker_entry = tracker_entry
        self.requested_entry_id = None

    def get_entry(self, entry_id):  # noqa: ANN001
        self.requested_entry_id = entry_id
        return self.tracker_entry


class SalesClaimExportBackendTests(unittest.TestCase):
    def test_extract_latest_sales_note_text_returns_last_entry_without_timestamp(self) -> None:
        self.assertEqual(
            extract_latest_sales_note_text(
                "\n[2026-03-28 09:00] first note\n\n[2026-03-29 10:30] final note\n",
            ),
            "final note",
        )

    def test_build_sales_claim_export_rows_reads_tracker_entry_and_formats_dates(self) -> None:
        source_entry_id = str(uuid4())
        claim = _Claim(
            {
                "project_name": "Fallback Project",
                "source_entry_id": source_entry_id,
                "owner_display_name": "Kim Manager",
                "owner_email": "kim@example.com",
                "estimated_amount_text": "12억원",
                "sales_note": "[2026-03-29 11:00] talked to client",
                "sales_note_updated_at": "2026-03-30T08:00:00Z",
            }
        )
        tracker_repository = _TrackerRepository(
            {
                "project_name": "Tracker Project",
                "gross_area_scale": "Large",
                "construction_cost": "100억원",
                "demand_org_name": "ACME",
                "demand_contact": "010-1234-5678",
                "client_location": "Seoul",
                "site_location_1": "Gangnam",
                "site_location_2": "Yeoksam",
                "architect_office": "Studio A",
                "construction_start_date": "2026-04-01",
                "last_checked_date": "2026-03-28",
                "progress_note": "tracker memo",
                "notice_date": "2026-03-15",
                "building_automation_estimated_amount": "9억원",
            }
        )

        rows = build_sales_claim_export_rows(
            claims=[claim],
            tracker_repository=tracker_repository,
            format_tracker_export_date=lambda value: f"DATE:{value}",
        )

        self.assertEqual(str(tracker_repository.requested_entry_id), source_entry_id)
        self.assertEqual(
            rows,
            [
                {
                    "project_name": "Fallback Project",
                    "gross_area_scale": "Large",
                    "construction_cost": "100억원",
                    "demand_org_name": "ACME",
                    "demand_contact": "010-1234-5678",
                    "client_location": "Seoul",
                    "site_location_1": "Gangnam",
                    "site_location_2": "Yeoksam",
                    "architect_office": "Studio A",
                    "construction_start_date": "2026-04-01",
                    "last_checked_date": "DATE:2026-03-30T08:00:00Z",
                    "progress_note": "talked to client",
                    "notice_date": "2026-03-15",
                    "manager_name": "Kim Manager",
                    "building_automation_estimated_amount": "12억원",
                }
            ],
        )

    def test_build_sales_claim_export_rows_falls_back_when_tracker_entry_unavailable(self) -> None:
        claim = _Claim(
            {
                "project_name": "Claim Project",
                "source_entry_id": "not-a-uuid",
                "owner_display_name": "",
                "owner_email": "owner@example.com",
                "estimated_amount_text": "",
                "sales_note": "",
                "updated_at": "2026-03-31T00:00:00Z",
            }
        )
        tracker_repository = _TrackerRepository(
            {
                "project_name": "Tracker Project",
                "progress_note": "tracker memo",
                "building_automation_estimated_amount": "7억원",
            }
        )

        rows = build_sales_claim_export_rows(
            claims=[claim],
            tracker_repository=tracker_repository,
            format_tracker_export_date=lambda value: f"DATE:{value}",
        )

        self.assertIsNone(tracker_repository.requested_entry_id)
        self.assertEqual(rows[0]["project_name"], "Claim Project")
        self.assertEqual(rows[0]["progress_note"], "")
        self.assertEqual(rows[0]["manager_name"], "owner@example.com")
        self.assertEqual(rows[0]["building_automation_estimated_amount"], "")
        self.assertEqual(rows[0]["last_checked_date"], "DATE:2026-03-31T00:00:00Z")

    def test_build_sales_claim_export_rows_uses_tracker_fallbacks_when_claim_fields_are_blank(self) -> None:
        source_entry_id = str(uuid4())
        claim = _Claim(
            {
                "project_name": "",
                "source_entry_id": source_entry_id,
                "owner_display_name": "",
                "owner_email": "owner@example.com",
                "estimated_amount_text": "",
                "sales_note": "",
                "updated_at": "",
            }
        )
        tracker_repository = _TrackerRepository(
            {
                "project_name": "Tracker Project",
                "progress_note": "tracker memo",
                "last_checked_date": "2026-04-01",
                "building_automation_estimated_amount": "7억원",
            }
        )

        rows = build_sales_claim_export_rows(
            claims=[claim],
            tracker_repository=tracker_repository,
            format_tracker_export_date=lambda value: f"DATE:{value}",
        )

        self.assertEqual(rows[0]["project_name"], "Tracker Project")
        self.assertEqual(rows[0]["progress_note"], "tracker memo")
        self.assertEqual(rows[0]["building_automation_estimated_amount"], "7억원")
        self.assertEqual(rows[0]["last_checked_date"], "DATE:2026-04-01")
