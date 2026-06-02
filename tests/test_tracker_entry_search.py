from __future__ import annotations

import unittest

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID
from backend.repositories.in_memory_tracker_entries import InMemoryTrackerEntryRepository


class TrackerEntrySearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryTrackerEntryRepository()

    def test_search_matches_project_name(self) -> None:
        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="smart building",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["project_name"], "Smart Building Upgrade")

    def test_search_uses_effective_project_name_override(self) -> None:
        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="project name a",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["project_name"], "Project Name A")

    def test_search_does_not_match_other_fields(self) -> None:
        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="korea facilities agency",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 0)
        self.assertEqual(rows, [])

    def test_search_can_exclude_auxiliary_service_titles(self) -> None:
        self.repository._entries[next(iter(self.repository._entries))]["project_name_source"] = "서울식물원 식재설계 공모전 운영 대행용역"

        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        titles = [row["project_name"] for row in rows]
        self.assertEqual(total, 2)
        self.assertNotIn("서울식물원 식재설계 공모전 운영 대행용역", titles)
        self.assertIn("Smart Building Upgrade", titles)

    def test_search_filters_by_notice_year_across_supported_date_formats(self) -> None:
        first_id, second_id = list(self.repository._entries.keys())
        self.repository._entries[first_id]["notice_date_source"] = "2023-01-15"
        self.repository._entries[second_id]["notice_date_source"] = "20240116"

        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="",
            region="",
            notice_year="2023",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 1)
        self.assertEqual(rows[0]["notice_date"], "2023-01-15")


    def test_list_entries_preserves_organization_id(self) -> None:
        rows, total = self.repository.list_entries(
            page=1,
            page_size=20,
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 2)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["organization_id"], DEFAULT_PHASE1_ORGANIZATION_ID)

    def test_list_entry_summaries_preserves_organization_id(self) -> None:
        rows, total = self.repository.list_entry_summaries(
            page=1,
            page_size=20,
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        self.assertEqual(total, 2)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["organization_id"], DEFAULT_PHASE1_ORGANIZATION_ID)


if __name__ == "__main__":
    unittest.main()
