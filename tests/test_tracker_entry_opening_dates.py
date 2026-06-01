from __future__ import annotations

import unittest
from unittest.mock import Mock
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _annotate_tracker_entries_with_opening_dates


class TrackerEntryOpeningDateTests(unittest.TestCase):
    def test_annotate_tracker_entries_with_opening_dates_keeps_persisted_value(self) -> None:
        items = _annotate_tracker_entries_with_opening_dates(
            [
                {
                    "source_run_id": str(uuid4()),
                    "source_bid_no": "R25BK00624372",
                    "source_bid_ord": "000",
                    "opening_scheduled_date": "20250328",
                }
            ]
        )

        self.assertEqual(items[0]["opening_scheduled_date"], "20250328")

    def test_annotate_tracker_entries_with_opening_dates_reads_seed_artifact(self) -> None:
        source_run_id = uuid4()
        artifact_repository = Mock()
        artifact_repository.list_artifacts.return_value = [
            {
                "artifact_type": "seed_csv",
                "storage_path": "output/artifacts/demo/project_tracker_seed_input.csv",
            }
        ]

        with patch("backend.api.app._get_artifact_repository", return_value=artifact_repository), patch(
            "backend.api.app._load_seed_rows_from_artifact_path",
            return_value=[
                {
                    "bid_no": "R25BK00624372",
                    "bid_ord": "000",
                    "opening_scheduled_date": "20250328",
                }
            ],
        ):
            items = _annotate_tracker_entries_with_opening_dates(
                [
                    {
                        "source_run_id": str(source_run_id),
                        "source_bid_no": "R25BK00624372",
                        "source_bid_ord": "0",
                    }
                ]
            )

        self.assertEqual(items[0]["opening_scheduled_date"], "20250328")

    def test_annotate_tracker_entries_with_opening_dates_keeps_blank_when_missing(self) -> None:
        artifact_repository = Mock()
        artifact_repository.list_artifacts.return_value = []

        with patch("backend.api.app._get_artifact_repository", return_value=artifact_repository):
            items = _annotate_tracker_entries_with_opening_dates(
                [
                    {
                        "source_run_id": str(uuid4()),
                        "source_bid_no": "R25BK00624372",
                        "source_bid_ord": "000",
                    }
                ]
            )

        self.assertEqual(items[0]["opening_scheduled_date"], "")


if __name__ == "__main__":
    unittest.main()
