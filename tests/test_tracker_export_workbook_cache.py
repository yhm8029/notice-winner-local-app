from __future__ import annotations

import json
import unittest

from backend.api.app import _build_tracker_download_job_cache_key
from backend.services.tracker_export_workbook_backend import build_tracker_export_workbook_cache_key


class TrackerExportWorkbookCacheTests(unittest.TestCase):
    def test_cache_key_separates_filters_auxiliary_and_blank_progress_modes(self) -> None:
        base_key = build_tracker_export_workbook_cache_key(
            q="",
            region="",
            edited_only=False,
            exclude_auxiliary_titles=True,
            blank_progress_note=False,
        )
        user_key = build_tracker_export_workbook_cache_key(
            q="",
            region="",
            edited_only=False,
            exclude_auxiliary_titles=True,
            blank_progress_note=True,
        )
        filtered_key = build_tracker_export_workbook_cache_key(
            q="seoul",
            region="seoul",
            edited_only=True,
            exclude_auxiliary_titles=True,
            blank_progress_note=True,
        )
        changed_query_key = build_tracker_export_workbook_cache_key(
            q="busan",
            region="seoul",
            edited_only=True,
            exclude_auxiliary_titles=True,
            blank_progress_note=True,
        )
        self.assertNotEqual(base_key, user_key)
        self.assertNotEqual(user_key, filtered_key)
        self.assertNotEqual(filtered_key, changed_query_key)

    def test_workbook_cache_key_includes_layout_version(self) -> None:
        cache_key = build_tracker_export_workbook_cache_key(
            q="",
            region="",
            edited_only=False,
            exclude_auxiliary_titles=True,
            blank_progress_note=False,
        )

        payload = json.loads(cache_key)

        self.assertEqual(payload["workbook_layout_version"], 3)

    def test_download_job_cache_key_includes_layout_version(self) -> None:
        cache_key = _build_tracker_download_job_cache_key(
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
            blank_progress_note=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )

        payload = json.loads(cache_key)

        self.assertEqual(payload["workbook_layout_version"], 3)

    def test_download_job_cache_key_includes_data_version(self) -> None:
        first_key = _build_tracker_download_job_cache_key(
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
            blank_progress_note=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
            data_version="count=10;updated_at=2026-05-01T00:00:00Z",
        )
        second_key = _build_tracker_download_job_cache_key(
            q="",
            region="",
            exclude_auxiliary_titles=True,
            edited_only=False,
            blank_progress_note=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
            data_version="count=11;updated_at=2026-05-01T00:00:00Z",
        )

        self.assertNotEqual(first_key, second_key)
        self.assertEqual(
            json.loads(first_key)["data_version"],
            "count=10;updated_at=2026-05-01T00:00:00Z",
        )
