from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.native_contract_lookup import ContractLookupMeta
from backend.services.native_contract_lookup import ContractLookupResult
from backend.services.native_export_backend import run_post_collect_native


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class NativeExportContractLookupLoggingTests(unittest.TestCase):
    def test_run_post_collect_native_emits_contract_lookup_meta_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            progress_messages: list[str] = []
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "org_name",
                        "announce_date",
                        "g2b_verified",
                        "base_url",
                        "internal_search_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00555555",
                        "bid_ord": "000",
                        "project_name_norm": "테스트프로젝트",
                        "org_name": "경상남도 양산시",
                        "announce_date": "20250115",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/view",
                        "internal_search_url": "https://www.example.com/view?q=test",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            with patch(
                "backend.services.native_export_backend.resolve_contract_by_bid_no",
                return_value=ContractLookupResult(contract_name="테스트건축사사무소"),
            ), patch(
                "backend.services.native_export_backend.get_last_contract_lookup_meta",
                return_value=ContractLookupMeta(
                    contract_lookup_path="lofin_hit",
                    query_sweep_used=False,
                    query_sweep_hit=False,
                    lofin_date_workers=3,
                    lofin_global_semaphore_limit=4,
                    lofin_dates_examined=18,
                    lofin_requests_total=36,
                    lofin_pages_fetched_total=12,
                    lofin_timeout_count=1,
                    lofin_first_nonempty_date="20250324",
                    lofin_hit_date="20250324",
                    lofin_best_score=0.91,
                    lofin_max_active_requests=3,
                ),
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>공고</title><body>내용 없음</body></html>"),
            ):
                run_post_collect_native(input_csv, output_csv, progress_cb=progress_messages.append)

        self.assertEqual(len(progress_messages), 1)
        self.assertIn("contract_lookup_path=lofin_hit", progress_messages[0])
        self.assertIn("query_sweep_used=N", progress_messages[0])
        self.assertIn("query_sweep_hit=N", progress_messages[0])
        self.assertIn("lofin_workers=3", progress_messages[0])
        self.assertIn("lofin_sem=4", progress_messages[0])
        self.assertIn("lofin_req=36", progress_messages[0])
        self.assertIn("lofin_first_nonempty=20250324", progress_messages[0])
        self.assertIn("lofin_hit_date=20250324", progress_messages[0])
        self.assertIn("lofin_best=0.910", progress_messages[0])
