from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _collapse_tracker_rows_by_project
from backend.api.app import _filter_tracker_rows_for_global_scope
from backend.api.app import _load_all_tracker_entries_for_global_summary
from backend.services.tracker_global_summary_backend import filter_tracker_rows_for_global_scope as filter_tracker_rows_for_global_scope_impl


class TrackerGlobalSummaryTests(unittest.TestCase):
    def test_load_all_tracker_entries_for_global_summary_uses_list_entries_with_row_metadata(self) -> None:
        rows = [
            {
                "id": uuid4(),
                "source_run_id": uuid4(),
                "source_tracker_run_id": None,
                "entry_key": "r25bk1|000|sample",
                "sheet_name": "",
                "section_name": "",
                "row_no": 7,
                "source_bid_no": "r25bk1",
                "source_bid_ord": "000",
                "source_project_name_norm": "sample-project",
                "project_name": "샘플 프로젝트",
                "gross_area_scale": "",
                "construction_cost": "",
                "demand_org_name": "부산광역시교육청",
                "demand_contact": "",
                "client_location": "",
                "site_location_1": "부산광역시",
                "site_location_2": "",
                "architect_office": "",
                "opening_scheduled_date": "",
                "construction_start_date": "",
                "contract_date": "",
                "construction_duration_days": "",
                "completion_expected_date_explicit": "",
                "completion_expected_date_computed": "",
                "last_checked_date": "",
                "progress_note": "",
                "notice_date": "2025-03-27",
                "manager_name": "",
                "building_automation_estimated_amount": "",
                "overridden_fields": [],
                "has_overrides": False,
                "last_edited_at": None,
                "last_edited_by": None,
                "last_edited_by_label": "",
                "created_at": "2026-03-27T00:00:00+00:00",
                "updated_at": "2026-03-27T01:00:00+00:00",
            }
        ]

        class _Repo:
            def list_entries(self, **kwargs):
                return rows, len(rows)

        with patch("backend.api.app._get_tracker_repository", return_value=_Repo()), \
             patch("backend.api.app._annotate_tracker_entries_with_project_refs", side_effect=lambda value: value), \
             patch("backend.api.app._annotate_tracker_entries_with_opening_dates", side_effect=lambda value: value), \
             patch("backend.api.app._normalize_tracker_rows_for_presentation", side_effect=lambda value: value):
            loaded = _load_all_tracker_entries_for_global_summary()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["row_no"], 7)
        self.assertIn("updated_at", loaded[0])
        self.assertIn("overridden_fields", loaded[0])

    def test_collapse_tracker_rows_by_project_merges_duplicate_rows_and_fills_blanks(self) -> None:
        project_id = uuid4()
        rows = [
            {
                "id": uuid4(),
                "project_id": project_id,
                "project_name": "동수영중학교 그린스마트스쿨 리모델링 건축설계 공모",
                "entry_key": "r25bk1|000|dongsuyeong-middle-school",
                "source_project_name_norm": "동수영중학교-그린스마트스쿨-리모델링-건축설계-공모",
                "architect_office": "",
                "demand_contact": "",
                "gross_area_scale": "9362㎡",
                "construction_cost": "",
                "site_location_1": "부산광역시",
                "demand_org_name": "부산광역시교육청 해운대교육지원청",
                "updated_at": "2026-03-27T00:00:00+00:00",
                "created_at": "2026-03-27T00:00:00+00:00",
                "overridden_fields": [],
            },
            {
                "id": uuid4(),
                "project_id": project_id,
                "project_name": "동수영중학교 그린스마트스쿨 리모델링 건축설계 공모 재공고",
                "entry_key": "r25bk2|000|dongsuyeong-middle-school",
                "source_project_name_norm": "동수영중학교-그린스마트스쿨-리모델링-건축설계-공모",
                "architect_office": "도플건축사사무소 주식회사",
                "demand_contact": "동수영중학교 행정실/051-752-3355",
                "gross_area_scale": "",
                "construction_cost": "96.41억원",
                "site_location_1": "",
                "demand_org_name": "",
                "updated_at": "2026-03-27T01:00:00+00:00",
                "created_at": "2026-03-27T01:00:00+00:00",
                "overridden_fields": [],
            },
        ]

        collapsed = _collapse_tracker_rows_by_project(rows)

        self.assertEqual(len(collapsed), 1)
        item = collapsed[0]
        self.assertEqual(item["project_id"], project_id)
        self.assertEqual(item["architect_office"], "도플건축사사무소 주식회사")
        self.assertEqual(item["demand_contact"], "동수영중학교 행정실/051-752-3355")
        self.assertEqual(item["gross_area_scale"], "9362㎡")
        self.assertEqual(item["construction_cost"], "96.41억원")
        self.assertEqual(item["site_location_1"], "부산광역시")
        self.assertEqual(item["demand_org_name"], "부산광역시교육청 해운대교육지원청")

    def test_filter_tracker_rows_for_global_scope_matches_search_from_duplicate_title_variants(self) -> None:
        project_id = uuid4()
        collapsed = _collapse_tracker_rows_by_project(
            [
                {
                    "id": uuid4(),
                    "project_id": project_id,
                    "project_name": "동수영중학교 그린스마트스쿨 리모델링 건축설계 공모",
                    "entry_key": "r25bk1|000|dongsuyeong-middle-school",
                    "source_project_name_norm": "동수영중학교-그린스마트스쿨-리모델링-건축설계-공모",
                    "architect_office": "",
                    "demand_contact": "",
                    "gross_area_scale": "",
                    "construction_cost": "",
                    "site_location_1": "부산광역시",
                    "demand_org_name": "",
                    "updated_at": "2026-03-27T00:00:00+00:00",
                    "created_at": "2026-03-27T00:00:00+00:00",
                    "overridden_fields": [],
                },
                {
                    "id": uuid4(),
                    "project_id": project_id,
                    "project_name": "동수영중학교 그린스마트스쿨 리모델링 건축설계 공모 재공고",
                    "entry_key": "r25bk2|000|dongsuyeong-middle-school",
                    "source_project_name_norm": "동수영중학교-그린스마트스쿨-리모델링-건축설계-공모",
                    "architect_office": "",
                    "demand_contact": "",
                    "gross_area_scale": "",
                    "construction_cost": "",
                    "site_location_1": "부산광역시",
                    "demand_org_name": "",
                    "updated_at": "2026-03-27T01:00:00+00:00",
                    "created_at": "2026-03-27T01:00:00+00:00",
                    "overridden_fields": [],
                },
            ]
        )

        filtered = _filter_tracker_rows_for_global_scope(
            collapsed,
            q="재공고",
            region="부산",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["project_id"], project_id)

    def test_collapse_tracker_rows_by_project_stores_normalized_search_text(self) -> None:
        collapsed = _collapse_tracker_rows_by_project(
            [
                {
                    "id": uuid4(),
                    "project_id": uuid4(),
                    "project_name": "Alpha Community Center",
                    "entry_key": "alpha-center",
                    "source_project_name_norm": "alpha-community-center",
                    "architect_office": "Studio One",
                    "demand_contact": "Planning Team/02-1234-5678",
                    "gross_area_scale": "",
                    "construction_cost": "",
                    "site_location_1": "Seoul",
                    "demand_org_name": "Alpha District Office",
                    "updated_at": "2026-03-27T00:00:00+00:00",
                    "created_at": "2026-03-27T00:00:00+00:00",
                    "overridden_fields": [],
                }
            ]
        )

        self.assertEqual(len(collapsed), 1)
        self.assertIn("_search_text_norm", collapsed[0])
        self.assertIn("alphacommunitycenter", collapsed[0]["_search_text_norm"])
        self.assertIn("alphadistrictoffice", collapsed[0]["_search_text_norm"])

    def test_filter_tracker_rows_for_global_scope_prefers_cached_normalized_search_text(self) -> None:
        norm_calls: list[str] = []

        def _norm_text(value: str) -> str:
            norm_calls.append(value)
            if value == "alpha":
                return "alpha"
            raise AssertionError(f"unexpected normalization request: {value}")

        filtered = filter_tracker_rows_for_global_scope_impl(
            [
                {
                    "project_name": "Alpha Community Center",
                    "demand_org_name": "Alpha District Office",
                    "_search_text_norm": "alphacommunitycenter alphadistrictoffice",
                    "has_overrides": False,
                    "overridden_fields": [],
                }
            ],
            q="alpha",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            norm_text_fn=_norm_text,
            tracker_entry_matches_title_visibility_fn=lambda row, exclude_auxiliary_titles: True,
            tracker_entry_matches_region_fn=lambda row, region: True,
        )

        self.assertEqual(len(filtered), 1)
        self.assertEqual(norm_calls, ["alpha"])

    def test_filter_tracker_rows_for_global_scope_orders_by_opening_scheduled_date_desc_and_pushes_blank_dates_last(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "blank",
                    "project_name": "Blank Date Project",
                    "opening_scheduled_date": "",
                    "updated_at": "2026-04-14T00:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "older-dated",
                    "project_name": "Older Dated Project",
                    "opening_scheduled_date": "2026-03-02",
                    "updated_at": "2026-04-14T00:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "newer-dated",
                    "project_name": "Newer Dated Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T00:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual([row["id"] for row in filtered], ["newer-dated", "older-dated", "blank"])

    def test_filter_tracker_rows_for_global_scope_prefers_newer_opening_date_over_newer_updated_at(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "older-opening-newer-update",
                    "project_name": "Older Opening Newer Update Project",
                    "opening_scheduled_date": "2026-03-02",
                    "updated_at": "2026-04-14T02:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "newer-opening-older-update",
                    "project_name": "Newer Opening Older Update Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T01:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual(
            [row["id"] for row in filtered],
            ["newer-opening-older-update", "older-opening-newer-update"],
        )

    def test_filter_tracker_rows_for_global_scope_normalizes_mixed_opening_scheduled_date_formats_for_sorting(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "compact-date",
                    "project_name": "Compact Date Project",
                    "opening_scheduled_date": "20260328",
                    "updated_at": "2026-04-14T01:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "iso-date",
                    "project_name": "ISO Date Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T01:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual([row["id"] for row in filtered], ["iso-date", "compact-date"])

    def test_filter_tracker_rows_for_global_scope_uses_updated_at_desc_fallback_for_same_opening_scheduled_date(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "alpha-id",
                    "project_name": "Alpha Id Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T01:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "omega-id",
                    "project_name": "Omega Id Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T02:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual([row["id"] for row in filtered], ["omega-id", "alpha-id"])

    def test_filter_tracker_rows_for_global_scope_uses_id_desc_fallback_when_opening_date_and_updated_at_match(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "alpha-id",
                    "project_name": "Alpha Id Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T02:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "omega-id",
                    "project_name": "Omega Id Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T02:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual([row["id"] for row in filtered], ["omega-id", "alpha-id"])

    def test_collapse_tracker_rows_by_project_does_not_mix_fields_from_different_bid_identities(self) -> None:
        project_id = uuid4()
        rows = [
            {
                "id": uuid4(),
                "project_id": project_id,
                "project_name": "꼼지락 이음센터 조성사업 건축설계공모 공고",
                "entry_key": "r25bk00678165|000|꼼지락-이음센터-조성사업-건축설계공모-공고",
                "source_bid_no": "R25BK00678165",
                "source_bid_ord": "000",
                "source_project_name_norm": "꼼지락-이음센터-조성사업-건축설계공모-공고",
                "architect_office": "",
                "demand_contact": "등이 변경되었을 경우에는 신속히 우리시 도시디자인과/055-330-3913",
                "gross_area_scale": "650㎡",
                "construction_cost": "23.5억원",
                "site_location_1": "경상남도",
                "client_location": "경상남도 김해시",
                "demand_org_name": "경상남도 김해시",
                "notice_date": "20250227",
                "updated_at": "2026-03-27T00:00:00+00:00",
                "created_at": "2026-03-27T00:00:00+00:00",
                "overridden_fields": [],
            },
            {
                "id": uuid4(),
                "project_id": project_id,
                "project_name": "기장군 보훈회관 건립 사업 기본 및 실시설계용역[설계공모]",
                "entry_key": "r25bk00683837|000|기장군-보훈회관-건립-사업-기본-및-실시설계용역[설계공모]",
                "source_bid_no": "R25BK00683837",
                "source_bid_ord": "000",
                "source_project_name_norm": "기장군-보훈회관-건립-사업-기본-및-실시설계용역[설계공모]",
                "architect_office": "(주)엠디에이건축사사무소, (주)나무종합건축사사무소",
                "demand_contact": "기타사항과 관련해서는 우리군 건축과 공공건축팀/051-709-8686",
                "gross_area_scale": "",
                "construction_cost": "",
                "site_location_1": "부산광역시",
                "client_location": "부산광역시 기장군",
                "demand_org_name": "부산광역시 기장군",
                "notice_date": "20250304",
                "updated_at": "2026-03-27T01:00:00+00:00",
                "created_at": "2026-03-27T01:00:00+00:00",
                "overridden_fields": [],
            },
        ]

        collapsed = _collapse_tracker_rows_by_project(rows)

        self.assertEqual(len(collapsed), 1)
        item = collapsed[0]
        if item["project_name"] == "꼼지락 이음센터 조성사업 건축설계공모 공고":
            self.assertEqual(item["demand_org_name"], "경상남도 김해시")
            self.assertEqual(item["client_location"], "경상남도 김해시")
            self.assertEqual(item["demand_contact"], "등이 변경되었을 경우에는 신속히 우리시 도시디자인과/055-330-3913")
            self.assertEqual(item["architect_office"], "")
        else:
            self.assertEqual(item["project_name"], "기장군 보훈회관 건립 사업 기본 및 실시설계용역[설계공모]")
            self.assertEqual(item["architect_office"], "(주)엠디에이건축사사무소, (주)나무종합건축사사무소")
            self.assertEqual(item["client_location"], "부산광역시 기장군")
            self.assertEqual(item["demand_org_name"], "부산광역시 기장군")
            self.assertEqual(item["demand_contact"], "기타사항과 관련해서는 우리군 건축과 공공건축팀/051-709-8686")


if __name__ == "__main__":
    unittest.main()
