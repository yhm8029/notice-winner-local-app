from __future__ import annotations

import unittest
from datetime import datetime

from backend.services.related_notice_collect_backend import build_related_notice_collect_recipes
from backend.services.related_notice_collect_backend import build_related_notice_search_window


class RelatedNoticeCollectBackendTests(unittest.TestCase):
    def test_build_related_notice_search_window_uses_earliest_run_and_notice_dates(self) -> None:
        project = {
            "first_notice_date": "20240205",
            "latest_notice_date": "20240212",
            "source_json": {"run_ids": ["run-1", "run-2"]},
        }
        runs = [
            {"id": "run-1", "params_json": {"start_date": "20240220"}},
            {"id": "run-2", "params_json": {"start_date": "20240110"}},
        ]

        start_date, end_date = build_related_notice_search_window(
            project,
            collect_all_runs_fn=lambda: runs,
            parse_yyyymmdd_fn=lambda value: datetime.strptime(value, "%Y%m%d"),
            format_yyyymmdd_fn=lambda value: value.strftime("%Y%m%d"),
            now_fn=lambda: datetime(2026, 3, 29),
        )

        self.assertEqual(start_date, "20240110")
        self.assertEqual(end_date, "20260329")

    def test_build_related_notice_collect_recipes_reuses_max_limits_from_source_runs(self) -> None:
        project = {
            "project_name": "demo project construction design competition",
            "project_search_name": "demo project construction",
            "latest_notice_title": "demo project construction design competition",
            "first_notice_date": "20240205",
            "source_json": {"run_ids": ["run-1"]},
        }
        source_runs = [
            {
                "id": "run-1",
                "params_json": {
                    "notice_title": "demo project construction",
                    "rows_per_page": 999,
                    "max_pages": 15,
                },
            }
        ]

        recipes = build_related_notice_collect_recipes(
            project,
            source_runs=source_runs,
            build_related_notice_search_window_fn=lambda project: ("20240205", "20260329"),
            build_related_notice_query_variants_fn=lambda candidate: [candidate],
            norm_text_fn=lambda value: str(value).strip().lower().replace(" ", ""),
            collect_max_queries=5,
            default_rows_per_page=100,
            default_max_pages=3,
        )

        self.assertEqual(len(recipes), 2)
        self.assertEqual(recipes[0]["rows_per_page"], 999)
        self.assertEqual(recipes[0]["max_pages"], 15)
        self.assertEqual(recipes[0]["api_scope"], "all")
        self.assertEqual(
            [recipe["notice_title"] for recipe in recipes],
            [
                "demo project construction",
                "demo project construction design competition",
            ],
        )


if __name__ == "__main__":
    unittest.main()
