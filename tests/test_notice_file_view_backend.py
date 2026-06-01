from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _select_project_source_notice_row
from backend.api.app import _select_tracker_entry_source_notice_row
from backend.services.notice_file_view_backend import load_notice_seed_row_by_bid


class _EmptyArtifactRepository:
    def list_artifacts(self, *, run_id):  # type: ignore[no-untyped-def]
        return []


class NoticeFileViewBackendTests(unittest.TestCase):
    @patch("backend.services.notice_file_view_backend.collect_seed_rows_with_params")
    def test_load_notice_seed_row_by_bid_prefers_exact_bid_ord(self, collect_seed_rows_with_params) -> None:
        collect_seed_rows_with_params.return_value = SimpleNamespace(
            rows=[
                {"bid_no": "R26BK01311027", "bid_ord": "001", "spec_doc_url": "https://example.com/other.hwp"},
                {"bid_no": "R26BK01311027", "bid_ord": "000", "spec_doc_url": "https://example.com/notice.hwp"},
            ]
        )

        row = load_notice_seed_row_by_bid(bid_no="R26BK01311027", bid_ord="000")

        self.assertIsNotNone(row)
        self.assertEqual(row["bid_ord"], "000")
        self.assertEqual(row["spec_doc_url"], "https://example.com/notice.hwp")

    @patch("backend.services.notice_file_view_backend.collect_seed_rows_with_params")
    def test_load_notice_seed_row_by_bid_falls_back_to_first_row(self, collect_seed_rows_with_params) -> None:
        collect_seed_rows_with_params.return_value = SimpleNamespace(
            rows=[{"bid_no": "R26BK01311027", "bid_ord": "001", "spec_doc_url": "https://example.com/notice.hwp"}]
        )

        row = load_notice_seed_row_by_bid(bid_no="R26BK01311027", bid_ord="000")

        self.assertIsNotNone(row)
        self.assertEqual(row["bid_ord"], "001")

    @patch("backend.api.app.load_notice_seed_row_by_bid")
    @patch("backend.api.app._get_artifact_repository", return_value=_EmptyArtifactRepository())
    def test_select_tracker_entry_source_notice_row_falls_back_without_local_artifact(
        self,
        _get_artifact_repository,
        load_notice_seed_row_by_bid_mock,
    ) -> None:
        load_notice_seed_row_by_bid_mock.return_value = {"bid_no": "R26BK01311027", "bid_ord": "000"}

        row = _select_tracker_entry_source_notice_row(
            {
                "source_run_id": str(uuid4()),
                "source_bid_no": "R26BK01311027",
                "source_bid_ord": "000",
            }
        )

        self.assertEqual(row, {"bid_no": "R26BK01311027", "bid_ord": "000"})
        load_notice_seed_row_by_bid_mock.assert_called_once_with(bid_no="R26BK01311027", bid_ord="000")

    @patch("backend.api.app.load_notice_seed_row_by_bid")
    @patch("backend.api.app._get_artifact_repository", return_value=_EmptyArtifactRepository())
    def test_select_project_source_notice_row_falls_back_without_local_artifact(
        self,
        _get_artifact_repository,
        load_notice_seed_row_by_bid_mock,
    ) -> None:
        load_notice_seed_row_by_bid_mock.return_value = {"bid_no": "R26BK01311027", "bid_ord": "000"}

        row = _select_project_source_notice_row(
            {
                "issuer_name": "제주특별자치도",
                "source_json": {
                    "run_ids": [str(uuid4())],
                    "source_bid_no": "R26BK01311027",
                    "source_bid_ord": "000",
                },
            }
        )

        self.assertEqual(row, {"bid_no": "R26BK01311027", "bid_ord": "000"})
        load_notice_seed_row_by_bid_mock.assert_called_once_with(bid_no="R26BK01311027", bid_ord="000")


if __name__ == "__main__":
    unittest.main()
