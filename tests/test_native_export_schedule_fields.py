from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.services.native_contract_lookup import ContractLookupResult
from backend.services.native_export_backend import _build_post_collect_output_row
from backend.services.native_export_backend import ExtractedNoticeFields
from backend.services.native_export_backend import PageDocument


class NativeExportScheduleFieldTests(unittest.TestCase):
    def test_build_post_collect_output_row_uses_trusted_contract_amount_for_building_automation_fallback(self) -> None:
        group_item = (
            ("R25BK00970325", "000"),
            [
                {
                    "bid_no": "R25BK00970325",
                    "bid_ord": "000",
                    "project_name_norm": "haeundae-school-remodeling",
                    "org_name": "부산광역시해운대교육지원청",
                    "internal_search_url": "",
                    "base_url": "https://example.com/notice",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=ContractLookupResult(
                contract_name="해운대여자중학교 공간재구조화 리모델링 건축설계 공모",
                contract_date="2025-10-31",
                contract_amount="9354723000",
                contract_duration_days=120,
                source_type="g2b_contract_api",
            ),
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            return_value=ExtractedNoticeFields(),
        ):
            out_row, _progress_message, _llm_used = _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(out_row["contract_amount"], "9,354,723,000원")
        self.assertEqual(out_row["building_automation_estimated_amount"], "1.40억원~1.87억원")
        self.assertEqual(out_row["building_automation_estimated_amount_source"], "estimated_contract_amount")

    def test_build_post_collect_output_row_splits_explicit_and_computed_completion(self) -> None:
        group_item = (
            ("R25BK00970325", "000"),
            [
                {
                    "bid_no": "R25BK00970325",
                    "bid_ord": "000",
                    "project_name_norm": "haeundae-school-remodeling",
                    "org_name": "부산광역시해운대교육지원청",
                    "internal_search_url": "",
                    "base_url": "https://example.com/notice",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=ContractLookupResult(
                contract_name="해운대여자중학교 공간재구조화 리모델링 건축설계 공모",
                contract_date="2025-10-31",
                contract_amount="9354723000",
                contract_duration_days=120,
                source_type="g2b_contract_api",
            ),
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            return_value=ExtractedNoticeFields(
                construction_duration_days="120",
                completion_expected_date_explicit="2026-03-05",
            ),
        ):
            out_row, _progress_message, _llm_used = _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(out_row["construction_duration_days"], "120")
        self.assertEqual(out_row["completion_expected_date_explicit"], "2026-03-05")
        self.assertEqual(out_row["completion_expected_date_computed"], "")


if __name__ == "__main__":
    unittest.main()
