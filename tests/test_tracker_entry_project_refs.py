from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid5

from backend.api.app import PROJECT_NAMESPACE
from backend.api.app import _annotate_tracker_entries_with_project_refs
from backend.api.app import _project_match_key
from backend.api.app import _select_project_search_name


class TrackerEntryProjectRefTests(unittest.TestCase):
    def test_annotate_tracker_entries_with_project_refs_adds_project_id(self) -> None:
        project_name = "청량119안전센터 신축공사"
        source_project_name_norm = "청량119안전센터-신축공사"
        project_search_name = _select_project_search_name(project_name, source_project_name_norm)
        project_key = _project_match_key(project_search_name or project_name or source_project_name_norm)
        project_id = uuid5(PROJECT_NAMESPACE, f"project:{project_key}")

        items = _annotate_tracker_entries_with_project_refs(
            [
                {
                    "project_name": project_name,
                    "source_project_name_norm": source_project_name_norm,
                }
            ]
        )

        self.assertEqual(items[0]["project_id"], project_id)
        self.assertEqual(items[0]["project_search_name"], project_search_name)

    def test_annotate_tracker_entries_with_project_refs_assigns_fallback_project_id(self) -> None:
        with patch("backend.api.app._build_project_aggregates", side_effect=AssertionError("aggregate rebuild should not run")):
            items = _annotate_tracker_entries_with_project_refs(
                [
                    {
                        "project_name": "demo project",
                        "source_project_name_norm": "demo-project",
                    }
                ]
            )

        self.assertIsNotNone(items[0]["project_id"])
        self.assertTrue(items[0]["project_search_name"])


if __name__ == "__main__":
    unittest.main()
