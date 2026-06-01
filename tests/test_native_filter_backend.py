from __future__ import annotations

import csv
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services import native_filter_backend
from backend.services import native_filter_search_runtime
from backend.services.native_filter_backend import SearchResult
from backend.services.native_filter_backend import build_queries
from backend.services.native_filter_backend import fetch_candidates_from_queries
from backend.services.native_filter_backend import run_collect_native


class NativeFilterBackendTests(unittest.TestCase):
    def test_default_query_search_is_disabled_for_local_app(self) -> None:
        with patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("generic web search must not run in the local app"),
        ):
            rows = native_filter_search_runtime.search_results_without_cache("design winner", 8)

        self.assertEqual(rows, [])

    def test_build_queries_orders_bid_no_then_base_then_base_org(self) -> None:
        queries = build_queries("부산 설계공모", "부산광역시", "R25BK00000001")
        self.assertEqual(len(queries), 6)
        self.assertIn("R25BK00000001", queries[0])
        self.assertIn("R25BK00000001", queries[1])
        self.assertNotIn("부산광역시", queries[2])
        self.assertNotIn("부산광역시", queries[3])
        self.assertIn("부산광역시", queries[4])
        self.assertIn("부산광역시", queries[5])

    def test_run_collect_native_skips_stage_two_when_stage_one_is_sufficient(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00000001",
                        "bid_ord": "000",
                        "project_name": "설계공모 테스트",
                        "org_name": "부산광역시",
                        "announce_date": "20250102",
                        "g2b_verified": "Y",
                    }
                )

            calls: list[list[str]] = []

            def _fake_fetch(**kwargs):
                calls.append(list(kwargs["queries"]))
                return [
                    {
                        "query": kwargs["queries"][0],
                        "url": "https://www.busan.go.kr/board/view",
                        "title": "설계공모 당선 결과",
                        "snippet": "당선 결과",
                        "candidate_score": 0.81,
                        "source_type": "web",
                        "filter_result": "PASS",
                        "filter_reason": "official_domain",
                    }
                ]

            with patch("backend.services.native_filter_backend.fetch_candidates_from_queries", side_effect=_fake_fetch):
                run_collect_native(input_csv, output_csv)

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0]), native_filter_backend.STAGE_1_QUERY_COUNT)

    def test_fetch_candidates_from_queries_logs_early_stop_when_flag_enabled(self) -> None:
        messages: list[str] = []
        with patch.object(native_filter_backend, "EARLY_STOP_ENABLED", True):
            with patch(
                "backend.services.native_filter_backend.search_results_without_cache",
                return_value=[
                    SearchResult(
                        query='"R25BK00554120" "당선"',
                        title="R25BK00554120 설계공모 당선 결과",
                        url="https://www.busan.go.kr/board/view/R25BK00554120",
                        snippet="당선 결과",
                    )
                ],
            ):
                rows = fetch_candidates_from_queries(
                    bid_no="R25BK00554120",
                    queries=['"R25BK00554120" "당선"', '"후속" "심사결과"'],
                    org_name="부산광역시",
                    project_name="설계공모",
                    progress_messages=messages,
                    stage=1,
                    query_start_index=1,
                )

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(messages), 1)
        self.assertIn("early_stop:", messages[0])
        self.assertIn("query_idx=1", messages[0])
        self.assertIn("stage=1", messages[0])

    def test_run_collect_native_uses_direct_notice_url_fast_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            progress_messages: list[str] = []
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                        "bid_ntce_dtl_url",
                        "demand_officer_name",
                        "notice_officer_tel",
                        "presmpt_prce",
                        "spec_doc_url_1",
                        "spec_doc_file_name_1",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name": "design contest test",
                        "org_name": "Seoul Office",
                        "announce_date": "20250102",
                        "g2b_verified": "Y",
                        "bid_ntce_dtl_url": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00554120&bidPbancOrd=000",
                        "demand_officer_name": "Manager Kim",
                        "notice_officer_tel": "02-111-2222",
                        "presmpt_prce": "120000000",
                        "spec_doc_url_1": "https://www.g2b.go.kr/download/spec.hwp",
                        "spec_doc_file_name_1": "notice.hwp",
                    }
                )

            with patch(
                "backend.services.native_filter_backend.search_results_without_cache",
                side_effect=AssertionError("search should not run when direct URL exists"),
            ):
                run_collect_native(input_csv, output_csv, progress_cb=progress_messages.append)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "CANDIDATE_OK")
        self.assertEqual(rows[0]["source_type"], "g2b_api")
        self.assertEqual(
            rows[0]["url"],
            "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00554120&bidPbancOrd=000",
        )
        self.assertEqual(rows[0]["presmpt_prce"], "120000000")
        self.assertEqual(rows[0]["officer_name"], "Manager Kim")
        self.assertEqual(rows[0]["spec_doc_file_name"], "notice.hwp")
        self.assertTrue(
            any(
                message.startswith("filter_summary: ")
                and "direct_url_fast_path_used=1" in message
                and "skipped_queries=" in message
                for message in progress_messages
            )
        )

    def test_run_collect_native_marks_direct_auxiliary_service_titles_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                        "bid_ntce_dtl_url",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "20241104833",
                        "bid_ord": "000",
                        "project_name": "\uc124\uacc4\uacf5\ubaa8 \uc81c\uc548\uc11c \ud3c9\uac00\uc6a9\uc5ed",
                        "org_name": "Seoul Office",
                        "announce_date": "20241106",
                        "g2b_verified": "Y",
                        "bid_ntce_dtl_url": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=20241104833&bidPbancOrd=000",
                    }
                )
                writer.writerow(
                    {
                        "bid_no": "20240321085",
                        "bid_ord": "000",
                        "project_name": "\uc124\uacc4\uacf5\ubaa8 \ud648\ud398\uc774\uc9c0 \uc0c1\uc6a9SW \uc720\uc9c0\ubcf4\uc218\uc6a9\uc5ed",
                        "org_name": "Seoul Office",
                        "announce_date": "20240314",
                        "g2b_verified": "Y",
                        "bid_ntce_dtl_url": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=20240321085&bidPbancOrd=000",
                    }
                )

            with patch(
                "backend.services.native_filter_backend.search_results_without_cache",
                side_effect=AssertionError("search should not run when direct URL exists"),
            ):
                run_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(len(rows), 2)
        self.assertEqual({row["status"] for row in rows}, {"EXCLUDED"})
        self.assertEqual({row["filter_result"] for row in rows}, {"EXCLUDED"})
        self.assertEqual({row["filter_reason"] for row in rows}, {"auxiliary_service_project"})

    def test_run_collect_native_preserves_input_order_when_parallelized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00000001",
                        "bid_ord": "000",
                        "project_name": "first design contest",
                        "org_name": "Seoul",
                        "announce_date": "20250102",
                        "g2b_verified": "Y",
                    }
                )
                writer.writerow(
                    {
                        "bid_no": "R25BK00000002",
                        "bid_ord": "000",
                        "project_name": "second design contest",
                        "org_name": "Busan",
                        "announce_date": "20250103",
                        "g2b_verified": "Y",
                    }
                )

            def _fake_search(query: str, num: int = 10, sleep_sec: float = 0.2) -> list[SearchResult]:
                if "first" in query:
                    time.sleep(0.2)
                    return [
                        SearchResult(
                            query=query,
                            title="first design result",
                            url="https://www.seoul.go.kr/board/1",
                            snippet="design result",
                        )
                    ]
                return [
                    SearchResult(
                        query=query,
                        title="second design result",
                        url="https://www.busan.go.kr/board/2",
                        snippet="design result",
                    )
                ]

            with patch(
                "backend.services.native_filter_backend.search_results_without_cache",
                side_effect=_fake_search,
            ):
                run_collect_native(
                    input_csv,
                    output_csv,
                    advanced_options={"filter_row_workers": 2},
                )

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual([row["bid_no"] for row in rows], ["R25BK00000001", "R25BK00000002"])

    def test_run_collect_native_reuses_query_results_with_run_level_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            progress_messages: list[str] = []
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                    ],
                )
                writer.writeheader()
                for bid_no in ("R25BK00000001", "R25BK00000001"):
                    writer.writerow(
                        {
                            "bid_no": bid_no,
                            "bid_ord": "000",
                            "project_name": "cacheable design contest",
                            "org_name": "Seoul",
                            "announce_date": "20250102",
                            "g2b_verified": "Y",
                        }
                    )

            query_calls: list[str] = []

            def _fake_search(query: str, num: int = 10, sleep_sec: float = 0.2) -> list[SearchResult]:
                query_calls.append(query)
                time.sleep(0.05)
                return []

            with patch.object(native_filter_backend, "EARLY_STOP_ENABLED", False):
                with patch(
                    "backend.services.native_filter_backend.search_results_without_cache",
                    side_effect=_fake_search,
                ):
                    run_collect_native(
                        input_csv,
                        output_csv,
                        advanced_options={"filter_row_workers": 2},
                        progress_cb=progress_messages.append,
                    )

        expected_unique_queries = len(
            build_queries("cacheable design contest", "Seoul", "R25BK00000001")
        )
        self.assertEqual(len(query_calls), expected_unique_queries)
        self.assertTrue(
            any(
                message.startswith("filter_summary: ")
                and "hits=" in message
                and "misses=" in message
                for message in progress_messages
            )
        )

    def test_run_collect_native_accepts_custom_filter_worker_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                    ],
                )
                writer.writeheader()
                for index in range(3):
                    writer.writerow(
                        {
                            "bid_no": f"R25BK0000000{index + 1}",
                            "bid_ord": "000",
                            "project_name": f"design contest {index + 1}",
                            "org_name": "Seoul",
                            "announce_date": "20250102",
                            "g2b_verified": "Y",
                        }
                    )

            with patch(
                "backend.services.native_filter_backend.search_results_without_cache",
                return_value=[
                    SearchResult(
                        query='"design contest" result',
                        title="design contest result",
                        url="https://www.seoul.go.kr/board/view",
                        snippet="design result",
                    )
                ],
            ):
                run_collect_native(
                    input_csv,
                    output_csv,
                    advanced_options={"filter_row_workers": 16},
                )

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(len(rows), 3)

    def test_run_collect_native_raises_interrupted_when_cancel_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "seed.csv"
            output_csv = root / "candidate.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00000001",
                        "bid_ord": "000",
                        "project_name": "cancel design contest",
                        "org_name": "Seoul",
                        "announce_date": "20250102",
                        "g2b_verified": "Y",
                    }
                )

            calls = {"count": 0}

            def _should_stop() -> bool:
                calls["count"] += 1
                return calls["count"] >= 2

            with self.assertRaises(InterruptedError):
                run_collect_native(input_csv, output_csv, should_stop=_should_stop)
