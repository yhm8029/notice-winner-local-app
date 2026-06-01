from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _build_tracker_missing_report


class TrackerMissingReportTests(unittest.TestCase):
    def test_build_tracker_missing_report_summarizes_blank_fields_and_reasons(self) -> None:
        source_run_a = uuid4()
        source_run_b = uuid4()
        deduped_entry_id = uuid4()
        architect_missing_entry_id = uuid4()

        entries = [
            {
                "id": str(deduped_entry_id),
                "source_run_id": str(source_run_a),
                "source_tracker_run_id": str(uuid4()),
                "source_bid_no": "R25BK00000001",
                "source_bid_ord": "0",
                "source_project_name_norm": "demo-project-a",
                "project_name": "Demo Project A",
                "demand_org_name": "서울특별시",
                "demand_contact": "",
                "architect_office": "건축사사무소 A",
                "gross_area_scale": "",
                "created_at": "2026-03-18T09:00:00Z",
                "updated_at": "2026-03-18T10:00:00Z",
            },
            {
                "id": str(uuid4()),
                "source_run_id": str(source_run_a),
                "source_tracker_run_id": str(uuid4()),
                "source_bid_no": "R25BK00000001",
                "source_bid_ord": "000",
                "source_project_name_norm": "demo-project-a",
                "project_name": "Demo Project A old",
                "demand_org_name": "서울특별시",
                "demand_contact": "",
                "architect_office": "건축사사무소 A",
                "gross_area_scale": "",
                "created_at": "2026-03-18T08:00:00Z",
                "updated_at": "2026-03-18T08:30:00Z",
            },
            {
                "id": str(architect_missing_entry_id),
                "source_run_id": str(source_run_b),
                "source_tracker_run_id": str(uuid4()),
                "source_bid_no": "R25BK00000002",
                "source_bid_ord": "000",
                "source_project_name_norm": "demo-project-b",
                "project_name": "Demo Project B",
                "demand_org_name": "부산광역시",
                "demand_contact": "시설과/051-000-0000",
                "architect_office": "",
                "gross_area_scale": "1000㎡",
                "created_at": "2026-03-18T11:00:00Z",
                "updated_at": "2026-03-18T11:30:00Z",
            },
        ]

        def load_winner_index(run_id):
            if run_id == source_run_a:
                return (
                    {
                        ("R25BK00000001", "000", "demo-project-a"): {
                            "demand_contact": "총무과/02-0000-0000",
                            "demand_contact_source": "fallback_seed_contact",
                            "gross_area_scale": "1200㎡",
                            "gross_area_scale_source": "confirmed_extracted",
                            "reason_code": "EAIS_CONTRACT_MATCH",
                            "source_type": "eais_openapi",
                        }
                    },
                    {},
                )
            if run_id == source_run_b:
                return (
                    {
                        ("R25BK00000002", "000", "demo-project-b"): {
                            "architect_office_source": "",
                            "winner_name": "주식회사 데모건축",
                            "reason_code": "LOFIN_CONTRACT_STRONG_MATCH",
                            "source_type": "lofin_openapi",
                        }
                    },
                    {},
                )
            return {}, {}

        with patch("backend.api.app._collect_all_tracker_entries", return_value=entries), patch(
            "backend.api.app._load_winner_index_by_run",
            side_effect=load_winner_index,
        ):
            summary, items = _build_tracker_missing_report(limit=10)

        self.assertEqual(summary.total_entries, 2)
        self.assertEqual(summary.missing_entries, 2)
        self.assertEqual(summary.contact_missing, 1)
        self.assertEqual(summary.architect_missing, 1)
        self.assertEqual(summary.area_missing, 1)

        by_entry_id = {str(item.entry_id): item for item in items}
        self.assertIn(str(deduped_entry_id), by_entry_id)
        self.assertIn(str(architect_missing_entry_id), by_entry_id)

        first_item = by_entry_id[str(deduped_entry_id)]
        self.assertEqual([field.field_key for field in first_item.missing_fields], ["demand_contact", "gross_area_scale"])
        self.assertIn("seed 연락처 fallback", first_item.missing_fields[0].source_reason)
        self.assertIn("reason=EAIS_CONTRACT_MATCH", first_item.missing_fields[0].source_reason)
        self.assertEqual(first_item.missing_fields[0].reason_group, "구버전 run")
        self.assertIn("첨부문서 직접 추출", first_item.missing_fields[1].source_reason)
        self.assertEqual(first_item.missing_fields[1].reason_group, "구버전 run")

        second_item = by_entry_id[str(architect_missing_entry_id)]
        self.assertEqual([field.field_key for field in second_item.missing_fields], ["architect_office"])
        self.assertIn("winner_name=주식회사 데모건축", second_item.missing_fields[0].source_reason)
        self.assertIn("reason=LOFIN_CONTRACT_STRONG_MATCH", second_item.missing_fields[0].source_reason)
        self.assertEqual(second_item.missing_fields[0].reason_group, "query miss")

    def test_build_tracker_missing_report_marks_missing_winner_csv_reason(self) -> None:
        entry_id = uuid4()
        entries = [
            {
                "id": str(entry_id),
                "source_run_id": str(uuid4()),
                "source_tracker_run_id": str(uuid4()),
                "source_bid_no": "R25BK00000003",
                "source_bid_ord": "000",
                "source_project_name_norm": "demo-project-c",
                "project_name": "Demo Project C",
                "demand_org_name": "대전광역시",
                "demand_contact": "",
                "architect_office": "건축사사무소 C",
                "gross_area_scale": "500㎡",
                "created_at": "2026-03-18T12:00:00Z",
                "updated_at": "2026-03-18T12:05:00Z",
            }
        ]

        with patch("backend.api.app._collect_all_tracker_entries", return_value=entries), patch(
            "backend.api.app._load_winner_index_by_run",
            return_value=({}, {}),
        ):
            summary, items = _build_tracker_missing_report(limit=10)

        self.assertEqual(summary.total_entries, 1)
        self.assertEqual(summary.missing_entries, 1)
        self.assertEqual(items[0].missing_fields[0].source_reason, "winner_csv 없음")
        self.assertEqual(items[0].missing_fields[0].reason_group, "source 없음")


if __name__ == "__main__":
    unittest.main()
