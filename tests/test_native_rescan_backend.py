from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from backend.services.native_rescan_backend import run_internal_nav_native


class NativeRescanBackendTests(unittest.TestCase):
    def test_run_internal_nav_native_writes_search_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "candidate.csv"
            output_csv = root / "internal_nav.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "query",
                        "source_type",
                        "candidate_score",
                        "url",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "query": "design-project 당선",
                        "source_type": "web",
                        "candidate_score": "0.95",
                        "url": "https://www.seoul.go.kr/board/view",
                    }
                )

            run_internal_nav_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "SEARCH_URL_BUILT")
        self.assertTrue(rows[0]["internal_search_url"].startswith("https://www.seoul.go.kr/board/view"))

    def test_run_internal_nav_native_skips_excluded_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "candidate.csv"
            output_csv = root / "internal_nav.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "query",
                        "source_type",
                        "candidate_score",
                        "url",
                        "status",
                        "filter_result",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "20241104833",
                        "bid_ord": "000",
                        "project_name_norm": "\uc81c\uc548\uc11c \ud3c9\uac00\uc6a9\uc5ed",
                        "g2b_verified": "Y",
                        "query": "20241104833",
                        "source_type": "g2b_api",
                        "candidate_score": "0",
                        "url": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=20241104833&bidPbancOrd=000",
                        "status": "EXCLUDED",
                        "filter_result": "EXCLUDED",
                    }
                )

            run_internal_nav_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows, [])

    def test_run_internal_nav_native_raises_interrupted_when_cancel_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "candidate.csv"
            output_csv = root / "internal_nav.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "query",
                        "source_type",
                        "candidate_score",
                        "url",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "query": "design-project",
                        "source_type": "web",
                        "candidate_score": "0.95",
                        "url": "https://www.seoul.go.kr/board/view",
                    }
                )

            checks = {"count": 0}

            def _should_stop() -> bool:
                checks["count"] += 1
                return checks["count"] >= 1

            with self.assertRaises(InterruptedError):
                run_internal_nav_native(input_csv, output_csv, should_stop=_should_stop)
