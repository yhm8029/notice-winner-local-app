from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import UUID

from backend.repositories.supabase_tracker_entries import SupabaseTrackerEntryRepository
from backend.repositories.supabase_tracker_entries import SupabaseTrackerEntryRepositoryConfig
from backend.repositories.tracker_entries import TrackerEntryRepositoryError
def _sample_entry() -> dict[str, object]:
    return {
        "entry_key": "20240345166|000|danghangpo-hall",
        "row_no": 1,
        "sheet_name": "Sheet1",
        "section_name": "facility_cost",
        "source_bid_no": "20240345166",
        "source_bid_ord": "000",
        "source_project_name_norm": "danghangpo-hall",
        "project_name": "당항포관광지 다목적홀 건립사업 건축설계 공모",
        "gross_area_scale": "1000㎡",
        "construction_cost": "10억원",
        "demand_org_name": "고성군",
        "demand_contact": "관광과/055-000-0000",
        "client_location": "경상남도 고성군",
        "site_location_1": "경상남도",
        "site_location_2": "고성군",
        "architect_office": "",
        "opening_scheduled_date": "20250328",
        "construction_start_date": "",
        "last_checked_date": "2026-03-16",
        "progress_note": "",
        "notice_date": "2026-03-16",
        "manager_name": "",
        "building_automation_estimated_amount": "",
    }


def _effective_row(source_run_id: UUID, source_tracker_run_id: UUID) -> dict[str, object]:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "source_run_id": str(source_run_id),
        "source_tracker_run_id": str(source_tracker_run_id),
        "entry_key": "20240345166|000|danghangpo-hall",
        "sheet_name": "Sheet1",
        "section_name": "facility_cost",
        "row_no": 1,
        "source_bid_no": "20240345166",
        "source_bid_ord": "000",
        "source_project_name_norm": "danghangpo-hall",
        "project_name": "당항포관광지 다목적홀 건립사업 건축설계 공모",
        "gross_area_scale": "1000㎡",
        "construction_cost": "10억원",
        "demand_org_name": "고성군",
        "demand_contact": "관광과/055-000-0000",
        "client_location": "경상남도 고성군",
        "site_location_1": "경상남도",
        "site_location_2": "고성군",
        "architect_office": "",
        "opening_scheduled_date": "20250328",
        "construction_start_date": "",
        "last_checked_date": "2026-03-16",
        "progress_note": "",
        "notice_date": "2026-03-16",
        "manager_name": "",
        "building_automation_estimated_amount": "",
        "overridden_fields": [],
        "created_at": "2026-03-16T14:33:00Z",
        "updated_at": "2026-03-16T14:33:05Z",
        "last_edited_at": None,
        "last_edited_by": None,
        "last_edited_by_label": "",
    }


class SupabaseTrackerEntryRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        config = SupabaseTrackerEntryRepositoryConfig(
            base_url="https://example.supabase.co",
            api_key="secret",
            organization_id=UUID("7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001"),
            timeout_seconds=10.0,
        )
        self.repository = SupabaseTrackerEntryRepository(config)
        self.source_run_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        self.source_tracker_run_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    def test_upsert_source_entries_bulk_upserts_then_reads_effective_rows(self) -> None:
        returned_row = _effective_row(self.source_run_id, self.source_tracker_run_id)

        with patch.object(
            self.repository,
            "_request_json",
            side_effect=[
                ([], {}),
                ([returned_row], {}),
            ],
        ) as request_json_mock:
            rows = self.repository.upsert_source_entries(
                source_run_id=self.source_run_id,
                source_tracker_run_id=self.source_tracker_run_id,
                entries=[_sample_entry()],
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entry_key"], "20240345166|000|danghangpo-hall")
        self.assertEqual(rows[0]["opening_scheduled_date"], "20250328")
        self.assertEqual(request_json_mock.call_args_list[0].kwargs["method"], "POST")
        self.assertEqual(
            request_json_mock.call_args_list[0].kwargs["query"],
            [("on_conflict", "organization_id,entry_key")],
        )
        self.assertEqual(
            request_json_mock.call_args_list[0].kwargs["headers"],
            {"Prefer": "resolution=merge-duplicates,return=minimal"},
        )
        self.assertTrue(request_json_mock.call_args_list[0].kwargs["allow_retry"])
        self.assertEqual(request_json_mock.call_args_list[1].kwargs["method"], "GET")
        self.assertEqual(
            request_json_mock.call_args_list[0].kwargs["payload"][0]["opening_scheduled_date_source"],
            "20250328",
        )

    def test_upsert_source_entries_preserves_bulk_upsert_error(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            side_effect=RuntimeError("Supabase request failed: timeout"),
        ):
            with self.assertRaisesRegex(RuntimeError, "timeout"):
                self.repository.upsert_source_entries(
                    source_run_id=self.source_run_id,
                    source_tracker_run_id=self.source_tracker_run_id,
                    entries=[_sample_entry()],
                )

    def test_list_entries_searches_project_name_only(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            rows, total = self.repository.list_entries(
                page=1,
                page_size=20,
                q="danghangpo hall",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        query = request_json_mock.call_args.kwargs["query"]
        self.assertIn(("project_name", "ilike.*danghangpo hall*"), query)
        self.assertNotIn(("or", "(project_name.ilike.*danghangpo hall*)"), query)

    def test_list_entry_summaries_uses_summary_select_clause(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            rows, total = self.repository.list_entry_summaries(
                page=1,
                page_size=20,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        query = request_json_mock.call_args.kwargs["query"]
        select_clause = next(value for key, value in query if key == "select")
        self.assertIn("project_name", select_clause)
        self.assertIn("notice_date", select_clause)
        self.assertNotIn("manager_name", select_clause)
        self.assertIn("site_location_2", select_clause)

    def test_list_entries_retries_with_legacy_select_when_contract_date_missing(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            side_effect=[
                TrackerEntryRepositoryError("column tracker_entries_effective.contract_date does not exist"),
                ([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
            ],
        ) as request_json_mock:
            rows, total = self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["contract_date"], "")
        fallback_query = request_json_mock.call_args_list[1].kwargs["query"]
        fallback_select = next(value for key, value in fallback_query if key == "select")
        self.assertNotIn("contract_date", fallback_select)

    def test_list_entries_uses_legacy_select_after_schema_fallback_is_cached(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            side_effect=[
                TrackerEntryRepositoryError("column tracker_entries_effective.contract_date does not exist"),
                ([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
                ([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
            ],
        ) as request_json_mock:
            rows_first, total_first = self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )
            rows_second, total_second = self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total_first, 1)
        self.assertEqual(total_second, 1)
        self.assertEqual(len(rows_first), 1)
        self.assertEqual(len(rows_second), 1)
        self.assertEqual(request_json_mock.call_count, 3)
        second_call_query = request_json_mock.call_args_list[2].kwargs["query"]
        second_call_select = next(value for key, value in second_call_query if key == "select")
        self.assertNotIn("contract_date", second_call_select)

    def test_upsert_source_entries_retries_without_extended_source_fields(self) -> None:
        returned_row = _effective_row(self.source_run_id, self.source_tracker_run_id)

        with patch.object(
            self.repository,
            "_request_json",
            side_effect=[
                TrackerEntryRepositoryError("column tracker_entries.contract_date_source does not exist"),
                ([], {}),
                TrackerEntryRepositoryError("column tracker_entries_effective.contract_date does not exist"),
                ([returned_row], {}),
            ],
        ) as request_json_mock:
            rows = self.repository.upsert_source_entries(
                source_run_id=self.source_run_id,
                source_tracker_run_id=self.source_tracker_run_id,
                entries=[_sample_entry()],
            )

        self.assertEqual(len(rows), 1)
        retry_payload = request_json_mock.call_args_list[1].kwargs["payload"][0]
        self.assertNotIn("contract_date_source", retry_payload)
        fallback_select_query = request_json_mock.call_args_list[3].kwargs["query"]
        fallback_select = next(value for key, value in fallback_select_query if key == "select")
        self.assertNotIn("contract_date", fallback_select)

    def test_get_entry_by_entry_key_uses_cached_legacy_select_after_schema_fallback(self) -> None:
        with patch(
            "backend.repositories.supabase_tracker_entries.request_json",
            side_effect=[
                TrackerEntryRepositoryError("column tracker_entries_effective.contract_date does not exist"),
                ([_effective_row(self.source_run_id, self.source_tracker_run_id)], {}),
                ([_effective_row(self.source_run_id, self.source_tracker_run_id)], {}),
            ],
        ) as request_json_mock:
            first = self.repository.get_entry_by_entry_key("20240345166|000|danghangpo-hall")
            second = self.repository.get_entry_by_entry_key("20240345166|000|danghangpo-hall")

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(request_json_mock.call_count, 3)
        second_call_query = request_json_mock.call_args_list[2].kwargs["query"]
        second_call_select = next(value for key, value in second_call_query if key == "select")
        self.assertNotIn("contract_date", second_call_select)

    def test_list_entries_adds_region_or_filter(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            rows, total = self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="경남",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        query = request_json_mock.call_args.kwargs["query"]
        self.assertIn(
            (
                "or",
                "(demand_org_name.ilike.*경남*,client_location.ilike.*경남*,site_location_1.ilike.*경남*,site_location_2.ilike.*경남*,demand_org_name.ilike.*경상남도*,client_location.ilike.*경상남도*,site_location_1.ilike.*경상남도*,site_location_2.ilike.*경상남도*)",
            ),
            query,
        )

    def test_list_entries_disambiguates_gwangju_from_gyeonggi_gwangju_si(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            rows, total = self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="광주",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        query = request_json_mock.call_args.kwargs["query"]
        region_clause = next(value for key, value in query if key == "or")
        self.assertIn("site_location_1.eq.광주", region_clause)
        self.assertIn("client_location.ilike.광주 *", region_clause)
        self.assertIn("client_location.ilike.*광주광역시*", region_clause)
        self.assertNotIn("client_location.ilike.*광주*", region_clause)

    def test_list_entries_adds_auxiliary_title_exclusion_filter(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            rows, total = self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="",
                exclude_auxiliary_titles=True,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        query = request_json_mock.call_args.kwargs["query"]
        self.assertIn(
            (
                "and",
                "(project_name.not.ilike.*대행용역*,project_name.not.ilike.*관리용역*)",
            ),
            query,
        )

    def test_apply_override_coerces_contract_date_input_for_construction_period(self) -> None:
        before_entry = _effective_row(self.source_run_id, self.source_tracker_run_id)
        before_entry["construction_start_date"] = "착수일로부터 90일"
        updated_entry = dict(before_entry)
        updated_entry["construction_start_date"] = "계약일 2025-01-01 기준 90일 (완료예정 2025-04-01)"
        updated_entry["overridden_fields"] = ["construction_start_date"]

        with patch.object(
            self.repository,
            "get_entry",
            side_effect=[before_entry, updated_entry],
        ), patch.object(
            self.repository,
            "list_audit_logs",
            side_effect=[
                ([], None),
                ([{"id": 1, "field_name": "construction_start_date"}], None),
            ],
        ), patch.object(
            self.repository,
            "_request_json",
            return_value=({}, {}),
        ) as request_json_mock:
            result = self.repository.apply_override(
                entry_id=UUID("11111111-1111-1111-1111-111111111111"),
                field_name="construction_start_date",
                new_value="20250101",
                actor_user_id=None,
                actor_label="tester",
                change_source="web",
            )

        assert result is not None
        self.assertTrue(result.changed)
        self.assertEqual(
            request_json_mock.call_args.kwargs["payload"]["p_new_value"],
            "계약일 2025-01-01 기준 90일 (완료예정 2025-04-01)",
        )


    def test_list_entries_adds_multi_region_or_filter(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            self.repository.list_entries(
                page=1,
                page_size=20,
                q="",
                region="\ubd80\uc0b0,\ub300\uad6c",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        query = request_json_mock.call_args.kwargs["query"]
        region_clause = next(value for key, value in query if key == "or")
        self.assertIn("\ubd80\uc0b0", region_clause)
        self.assertIn("\ub300\uad6c", region_clause)

    def test_list_entries_for_export_uses_export_select_clause(self) -> None:
        with patch.object(
            self.repository,
            "_request_json",
            return_value=([_effective_row(self.source_run_id, self.source_tracker_run_id)], {"content-range": "0-0/1"}),
        ) as request_json_mock:
            rows, total = self.repository.list_entries_for_export(
                page=1,
                page_size=20,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=self.source_tracker_run_id,
                sheet_name="",
                section_name="",
            )

        self.assertEqual(total, 1)
        self.assertEqual(len(rows), 1)
        query = request_json_mock.call_args.kwargs["query"]
        select_clause = next(value for key, value in query if key == "select")
        self.assertIn("manager_name", select_clause)
        self.assertIn("site_location_2", select_clause)


if __name__ == "__main__":
    unittest.main()
