from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.api.app import _build_related_notice_collect_recipes
from backend.api.app import _build_related_notice_query_variants


class RelatedNoticeCollectRecipeTests(unittest.TestCase):
    def test_related_notice_query_variants_drop_overly_generic_two_token_query(self) -> None:
        queries = _build_related_notice_query_variants("장평고등학교 교사 신축")

        self.assertIn("장평고등학교 교사 신축", queries)
        self.assertIn("장평고등학교 교사", queries)
        self.assertNotIn("교사 신축", queries)

    def test_collect_recipes_reuse_source_run_collect_params(self) -> None:
        project = {
            "project_name": "Iksan disability center construction design competition",
            "project_search_name": "Iksan disability center construction",
            "latest_notice_title": "Iksan disability center construction design competition",
            "issuer_name": "Iksan City",
            "first_notice_date": "20240205",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000001"]},
        }
        source_run = {
            "id": "00000000-0000-0000-0000-000000000001",
            "params_json": {
                "notice_title": "Iksan disability center construction",
                "demand_org": "Iksan",
                "api_scope": "construction",
                "rows_per_page": 999,
                "max_pages": 15,
                "start_date": "20240205",
            },
        }

        with patch("backend.api.app._project_source_runs", return_value=[source_run]), patch(
            "backend.api.app._build_related_notice_search_window",
            return_value=("20240205", "20260314"),
        ):
            recipes = _build_related_notice_collect_recipes(project)

        self.assertGreaterEqual(len(recipes), 1)
        self.assertEqual(recipes[0]["api_scope"], "all")
        self.assertEqual(recipes[0]["demand_org"], "")
        self.assertEqual(recipes[0]["rows_per_page"], 999)
        self.assertEqual(recipes[0]["max_pages"], 15)
        self.assertEqual(recipes[0]["notice_title"], "Iksan disability center construction")

    def test_collect_recipes_include_discipline_branch_queries(self) -> None:
        project = {
            "project_name": "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uc124\uacc4\uacf5\ubaa8",
            "project_search_name": "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5",
            "latest_notice_title": "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uc124\uacc4\uacf5\ubaa8",
            "issuer_name": "\uc804\ub77c\ub0a8\ub3c4 \uc7a5\ud765\uad70",
            "first_notice_date": "20240321",
            "source_json": {"run_ids": ["00000000-0000-0000-0000-000000000001"]},
        }
        source_run = {
            "id": "00000000-0000-0000-0000-000000000001",
            "params_json": {
                "notice_title": "\uc124\uacc4\uacf5\ubaa8",
                "demand_org": "\uc804\ub0a8",
                "api_scope": "service",
                "rows_per_page": 999,
                "max_pages": 15,
                "start_date": "20240101",
            },
        }

        with patch("backend.api.app._project_source_runs", return_value=[source_run]), patch(
            "backend.api.app._build_related_notice_search_window",
            return_value=("20240321", "20260315"),
        ):
            recipes = _build_related_notice_collect_recipes(project)

        self.assertGreaterEqual(len(recipes), 1)
        queries = [recipe["notice_title"] for recipe in recipes]
        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95", queries)
        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uacf5\uc0ac", queries)
        self.assertIn(
            "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uacf5\uc0ac \uad00\uae09\uc790\uc7ac",
            queries,
        )


if __name__ == "__main__":
    unittest.main()
