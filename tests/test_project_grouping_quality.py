from __future__ import annotations

import unittest

from backend.services.project_grouping_quality import GroupingAssignment
from backend.services.project_grouping_quality import evaluate_project_grouping
from scripts.evaluate_project_grouping import _build_assignments


class ProjectGroupingQualityTests(unittest.TestCase):
    def test_pairwise_metrics_are_perfect_when_groups_match(self) -> None:
        assignments = [
            GroupingAssignment("A", "g1", "g1"),
            GroupingAssignment("B", "g1", "g1"),
            GroupingAssignment("C", "g2", "g2"),
        ]

        summary = evaluate_project_grouping(assignments)

        self.assertEqual(summary["pairwise_precision"], 1.0)
        self.assertEqual(summary["pairwise_recall"], 1.0)
        self.assertEqual(summary["pairwise_f1"], 1.0)
        self.assertEqual(summary["overmerged_group_count"], 0)
        self.assertEqual(summary["oversplit_group_count"], 0)

    def test_detects_overmerge_and_oversplit(self) -> None:
        assignments = [
            GroupingAssignment("A", "g1", "p1"),
            GroupingAssignment("B", "g1", "p2"),
            GroupingAssignment("C", "g2", "p2"),
        ]

        summary = evaluate_project_grouping(assignments)

        self.assertEqual(summary["pairwise_precision"], 0.0)
        self.assertEqual(summary["pairwise_recall"], 0.0)
        self.assertEqual(summary["overmerged_group_count"], 1)
        self.assertEqual(summary["oversplit_group_count"], 1)

    def test_build_assignments_uses_tracker_group_prediction(self) -> None:
        golden_rows = [
            {
                "expected_group_id": "group-a",
                "bid_no": "R25BK00000001",
                "bid_ord": "000",
            },
            {
                "expected_group_id": "group-a",
                "bid_no": "R25BK00000002",
                "bid_ord": "000",
            },
        ]
        tracker_rows = [
            {
                "source_bid_no": "R25BK00000001",
                "source_bid_ord": "000",
                "project_name": "여수시 본청사 별관증축 건립사업",
                "source_project_name_norm": "여수시-본청사-별관증축-건립사업",
            },
            {
                "source_bid_no": "R25BK00000002",
                "source_bid_ord": "000",
                "project_name": "여수시 본청사 별관증축 건립사업 기본 및 실시설계",
                "source_project_name_norm": "여수시-본청사-별관증축-건립사업",
            },
        ]

        assignments = _build_assignments(golden_rows, tracker_rows)

        self.assertEqual(len(assignments), 2)
        self.assertEqual(assignments[0].expected_group_id, "group-a")
        self.assertTrue(assignments[0].predicted_group_id)
        self.assertEqual(assignments[0].predicted_group_id, assignments[1].predicted_group_id)


if __name__ == "__main__":
    unittest.main()
