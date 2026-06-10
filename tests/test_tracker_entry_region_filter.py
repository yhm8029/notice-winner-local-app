from __future__ import annotations

import unittest
from uuid import uuid4

from backend.repositories.in_memory_tracker_entries import InMemoryTrackerEntryRepository
from backend.repositories.tracker_entries import get_tracker_region_aliases
from backend.repositories.tracker_entries import normalize_tracker_region
from backend.repositories.tracker_entries import parse_tracker_regions
from backend.repositories.tracker_entries import tracker_entry_matches_region


class TrackerEntryRegionFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryTrackerEntryRepository()

    def test_normalize_tracker_region_accepts_official_name(self) -> None:
        self.assertEqual(normalize_tracker_region("경상남도"), "경남")
        self.assertEqual(normalize_tracker_region("전북특별자치도"), "전북")

    def test_region_aliases_include_short_and_official_names(self) -> None:
        self.assertEqual(get_tracker_region_aliases("강원"), ("강원", "강원도", "강원특별자치도"))

    def test_tracker_entry_matches_region_uses_org_and_location_fields(self) -> None:
        entry = {
            "demand_org_name": "경상남도교육청",
            "client_location": "경상남도 창원시",
            "site_location_1": "경상남도",
            "site_location_2": "창원시",
        }
        self.assertTrue(tracker_entry_matches_region(entry, "경남"))
        self.assertFalse(tracker_entry_matches_region(entry, "전남"))

    def test_tracker_entry_matches_region_does_not_mix_gwangju_metro_with_gwangju_si(self) -> None:
        metro_entry = {
            "demand_org_name": "광주광역시 광산구",
            "client_location": "광주광역시 광산구",
            "site_location_1": "광주광역시",
            "site_location_2": "광산구",
        }
        city_entry = {
            "demand_org_name": "경기도 광주시",
            "client_location": "경기도 광주시",
            "site_location_1": "경기도",
            "site_location_2": "광주시",
        }
        self.assertTrue(tracker_entry_matches_region(metro_entry, "광주"))
        self.assertFalse(tracker_entry_matches_region(city_entry, "광주"))
        self.assertTrue(tracker_entry_matches_region(city_entry, "경기"))

    def test_tracker_entry_matches_region_does_not_match_short_region_inside_office_name(self) -> None:
        self.assertFalse(
            tracker_entry_matches_region(
                {
                    "site_location_1": "울산광역시",
                    "client_location": "울산광역시 서울주소방서",
                    "demand_org_name": "울산광역시 서울주소방서",
                    "site_location_2": "",
                },
                "서울",
            )
        )
        self.assertTrue(
            tracker_entry_matches_region(
                {
                    "site_location_1": "서울특별시",
                    "client_location": "서울특별시교육청",
                    "demand_org_name": "서울특별시교육청",
                    "site_location_2": "",
                },
                "서울",
            )
        )

    def test_parse_tracker_regions_accepts_multiple_values(self) -> None:
        self.assertEqual(
            parse_tracker_regions("서울, 부산;대구/인천"),
            ("서울", "부산", "대구", "인천"),
        )

    def test_tracker_entry_matches_region_accepts_multiple_selected_regions(self) -> None:
        entry = {
            "demand_org_name": "대구광역시 북구청",
            "client_location": "대구광역시 북구",
            "site_location_1": "대구광역시",
            "site_location_2": "북구",
        }
        self.assertTrue(tracker_entry_matches_region(entry, "서울,대구,부산"))
        self.assertFalse(tracker_entry_matches_region(entry, "서울,부산,인천"))

    def test_list_entries_filters_by_region(self) -> None:
        tracker_run_id = uuid4()
        parent_run_id = uuid4()
        entry_id = uuid4()
        self.repository._entries[entry_id] = self.repository._build_entry(
            entry_id=entry_id,
            source_run_id=parent_run_id,
            source_tracker_run_id=tracker_run_id,
            entry_key="r25bk99999999|000|gyeongnam-project",
            row_no=99,
            source_bid_no="R25BK99999999",
            source_bid_ord="000",
            source_project_name_norm="gyeongnam-project",
            project_name="경남 프로젝트",
            gross_area_scale="1000㎡",
            construction_cost="50억원",
            demand_org_name="경상남도교육청",
            demand_contact="시설과/055-000-0000",
            client_location="경상남도 창원시",
            site_location_1="경상남도",
            site_location_2="창원시 성산구",
            architect_office="가람건축사사무소",
            construction_start_date="2026-05-01",
            last_checked_date="2026-03-17",
            progress_note="",
            notice_date="2026-03-17",
            manager_name="",
            building_automation_estimated_amount="1억원",
            created_at=self.repository._entries[next(iter(self.repository._entries))]["created_at"],
        )

        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="",
            region="경남",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["project_name"], "경남 프로젝트")


    def test_list_entries_filters_by_notice_year_and_region_together(self) -> None:
        tracker_run_id = uuid4()
        parent_run_id = uuid4()
        seoul_id = uuid4()
        busan_id = uuid4()
        self.repository._entries.clear()
        created_at = "2026-01-01T00:00:00+00:00"
        self.repository._entries[seoul_id] = self.repository._build_entry(
            entry_id=seoul_id,
            source_run_id=parent_run_id,
            source_tracker_run_id=tracker_run_id,
            entry_key="r25bk00000001|000|seoul-2025",
            row_no=1,
            source_bid_no="R25BK00000001",
            source_bid_ord="000",
            source_project_name_norm="seoul-2025",
            project_name="Seoul 2025 Project",
            gross_area_scale="",
            construction_cost="",
            demand_org_name="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc\uad50\uc721\uccad",
            demand_contact="",
            client_location="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
            site_location_1="\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
            site_location_2="",
            architect_office="",
            construction_start_date="",
            last_checked_date="2025-02-01",
            progress_note="",
            notice_date="2025-02-01",
            manager_name="",
            building_automation_estimated_amount="",
            created_at=created_at,
        )
        self.repository._entries[busan_id] = self.repository._build_entry(
            entry_id=busan_id,
            source_run_id=parent_run_id,
            source_tracker_run_id=tracker_run_id,
            entry_key="r25bk00000002|000|busan-2025",
            row_no=2,
            source_bid_no="R25BK00000002",
            source_bid_ord="000",
            source_project_name_norm="busan-2025",
            project_name="Busan 2025 Project",
            gross_area_scale="",
            construction_cost="",
            demand_org_name="\ubd80\uc0b0\uad11\uc5ed\uc2dc",
            demand_contact="",
            client_location="\ubd80\uc0b0\uad11\uc5ed\uc2dc",
            site_location_1="\ubd80\uc0b0\uad11\uc5ed\uc2dc",
            site_location_2="",
            architect_office="",
            construction_start_date="",
            last_checked_date="2025-03-01",
            progress_note="",
            notice_date="2025-03-01",
            manager_name="",
            building_automation_estimated_amount="",
            created_at=created_at,
        )

        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="",
            region="\uc11c\uc6b8",
            notice_year="2025",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["project_name"], "Seoul 2025 Project")


if __name__ == "__main__":
    unittest.main()
