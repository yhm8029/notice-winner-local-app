from __future__ import annotations

import unittest

from backend.api.app import _format_tracker_export_date
from backend.api.app import _normalize_tracker_entry_presentation
from backend.repositories.tracker_entries import format_tracker_display_date


class TrackerDisplayDateTests(unittest.TestCase):
    def test_format_tracker_display_date_normalizes_compact_date(self) -> None:
        self.assertEqual(format_tracker_display_date("20251022"), "2025-10-22")

    def test_format_tracker_export_date_returns_iso_date(self) -> None:
        self.assertEqual(_format_tracker_export_date("20251022"), "2025-10-22")

    def test_normalize_tracker_entry_presentation_formats_last_checked_date(self) -> None:
        normalized = _normalize_tracker_entry_presentation(
            {
                "project_name": "테스트 프로젝트",
                "construction_cost": "12.5억원",
                "building_automation_estimated_amount": "",
                "last_checked_date": "20251022",
                "construction_start_date": "",
                "demand_org_name": "",
                "site_location_1": "",
            },
            winner_row=None,
        )

        self.assertEqual(normalized["last_checked_date"], "2025-10-22")


if __name__ == "__main__":
    unittest.main()
