from __future__ import annotations

import csv
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.attachment_text_extract import AttachmentTextLoadResult
from backend.services.native_contract_lookup import ContractLookupResult
from backend.services.native_export_backend import _build_post_collect_output_row
from backend.services.native_export_backend import _collect_attachment_documents
from backend.services.native_export_backend import _default_export_row_max_workers
from backend.services.native_export_backend import _maybe_rescue_attachment_fields_with_synap
from backend.services.native_export_backend import _should_continue_attachment_scan
from backend.services.native_export_backend import _resolve_export_worker_count
from backend.services.native_export_backend import AttachmentDocument
from backend.services.native_export_backend import ExtractedNoticeFields
from backend.services.native_export_backend import PageDocument
from backend.services.native_export_backend import run_post_collect_native


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class NativeExportBackendTests(unittest.TestCase):
    def test_default_export_row_worker_count_uses_faster_fallback(self) -> None:
        self.assertEqual(_default_export_row_max_workers(getenv_fn=lambda _name, _default="": ""), 12)

    def test_resolve_export_worker_count_uses_higher_default_parallelism(self) -> None:
        self.assertEqual(_resolve_export_worker_count(advanced_options={}, grouped_item_count=20), 12)

    def test_synap_rescue_fills_only_missing_fields(self) -> None:
        initial = ExtractedNoticeFields()

        with patch(
            "backend.services.native_export_backend.download_notice_attachment_text_via_synap",
            return_value=type("Result", (), {"text": "synap text"})(),
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            return_value=ExtractedNoticeFields(
                gross_area_scale="765㎡",
                construction_cost="3,000,000,000원",
                demand_contact="질의접수처/054-370-6334",
            ),
        ):
            rescued, rescued_fields = _maybe_rescue_attachment_fields_with_synap(
                extracted=initial,
                attachment_url="https://www.g2b.go.kr/download/spec.hwp",
                file_name="공고문.hwp",
                bid_no="R25BK01030497",
                bid_ord="000",
                project_name="풍각 힐링센터 건립공사 제안설계공모",
                org_name="청도군",
                unty_atch_file_no="",
            )

        self.assertEqual(rescued.gross_area_scale, "765㎡")
        self.assertEqual(rescued.construction_cost, "3,000,000,000원")
        self.assertEqual(rescued.demand_contact, "질의접수처/054-370-6334")
        self.assertEqual(rescued_fields, ("area", "cost", "contact"))

    def test_synap_rescue_skips_when_existing_fields_are_already_present(self) -> None:
        initial = ExtractedNoticeFields(
            gross_area_scale="8,415.48㎡",
            construction_cost="27,256,779,000원",
            demand_contact="건축과/02-1234-5678",
        )

        with patch(
            "backend.services.native_export_backend.download_notice_attachment_text_via_synap",
            side_effect=AssertionError("synap should not run when no rescue field is missing"),
        ):
            rescued, rescued_fields = _maybe_rescue_attachment_fields_with_synap(
                extracted=initial,
                attachment_url="https://www.g2b.go.kr/download/spec.hwp",
                file_name="공고문.hwp",
                bid_no="R25BK01254382",
                bid_ord="000",
                project_name="강릉시 농업기술센터 청사 신축 설계공모",
                org_name="강릉시",
                unty_atch_file_no="",
            )

        self.assertEqual(rescued, initial)
        self.assertEqual(rescued_fields, ())

    def test_synap_rescue_does_not_override_existing_area_or_cost(self) -> None:
        initial = ExtractedNoticeFields(
            gross_area_scale="8,415.48㎡",
            construction_cost="27,256,779,000원",
            demand_contact="",
        )

        with patch(
            "backend.services.native_export_backend.download_notice_attachment_text_via_synap",
            return_value=type("Result", (), {"text": "synap text"})(),
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            return_value=ExtractedNoticeFields(
                gross_area_scale="999㎡",
                construction_cost="100,000,000원",
                demand_contact="건축과/02-9999-9999",
            ),
        ):
            rescued, rescued_fields = _maybe_rescue_attachment_fields_with_synap(
                extracted=initial,
                attachment_url="https://www.g2b.go.kr/download/spec.hwp",
                file_name="공고문.hwp",
                bid_no="R25BK01254382",
                bid_ord="000",
                project_name="강릉시 농업기술센터 청사 신축 설계공모",
                org_name="강릉시",
                unty_atch_file_no="",
            )

        self.assertEqual(rescued.gross_area_scale, "8,415.48㎡")
        self.assertEqual(rescued.construction_cost, "27,256,779,000원")
        self.assertEqual(rescued.demand_contact, "건축과/02-9999-9999")
        self.assertEqual(rescued_fields, ("contact",))

    def test_run_post_collect_native_preserves_bid_order_with_parallel_workers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00000001",
                        "bid_ord": "000",
                        "project_name_norm": "project-one",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/one",
                        "base_query": "",
                        "base_source_type": "web",
                        "search_link": "https://www.example.com/one",
                        "internal_search_url": "https://www.example.com/one?q=project-one",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )
                writer.writerow(
                    {
                        "bid_no": "R25BK00000002",
                        "bid_ord": "000",
                        "project_name_norm": "project-two",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/two",
                        "base_query": "",
                        "base_source_type": "web",
                        "search_link": "https://www.example.com/two",
                        "internal_search_url": "https://www.example.com/two?q=project-two",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            def _fake_contract_lookup(*, bid_no: str, project_name_norm: str, announce_date: str, org_name: str):
                if bid_no == "R25BK00000001":
                    time.sleep(0.1)
                return ContractLookupResult(contract_name=f"{project_name_norm}-winner")

            with patch(
                "backend.services.native_export_backend.resolve_contract_by_bid_no",
                side_effect=_fake_contract_lookup,
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>Notice</title><body>body</body></html>"),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual([row["bid_no"] for row in rows], ["R25BK00000001", "R25BK00000002"])

    def test_run_post_collect_native_emits_completed_progress_without_head_of_line_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "bid_no": "R25BK00000001",
                            "bid_ord": "000",
                            "project_name_norm": "project-one",
                            "g2b_verified": "Y",
                            "base_url": "",
                            "base_query": "",
                            "base_source_type": "web",
                            "search_link": "",
                            "internal_search_url": "",
                            "parser_version": "web-native-v1",
                            "run_mode": "native",
                            "status": "SEARCH_URL_BUILT",
                        },
                        {
                            "bid_no": "R25BK00000002",
                            "bid_ord": "000",
                            "project_name_norm": "project-two",
                            "g2b_verified": "Y",
                            "base_url": "",
                            "base_query": "",
                            "base_source_type": "web",
                            "search_link": "",
                            "internal_search_url": "",
                            "parser_version": "web-native-v1",
                            "run_mode": "native",
                            "status": "SEARCH_URL_BUILT",
                        },
                    ]
                )

            progress_messages: list[str] = []

            def _fake_build_row(*, group_item, llm_config, use_llm, should_stop=None):
                (bid_no, _bid_ord), _rows = group_item
                del should_stop
                if bid_no == "R25BK00000001":
                    time.sleep(0.5)
                else:
                    time.sleep(0.0)
                return (
                    {
                        "bid_no": bid_no,
                        "bid_ord": "000",
                        "rank": "1",
                        "project_name_norm": bid_no,
                        "g2b_verified": "Y",
                        "source_type": "native_web",
                        "internal_search_url": "",
                        "post_url": "",
                        "post_title": "",
                        "winner_name": "",
                        "winner_confidence": "",
                        "winner_pattern": "",
                        "post_score": "",
                        "file_url": "",
                        "file_name": "",
                        "confidence_score": "",
                        "reason_code": "",
                        "review_flag": "",
                        "escalate": "",
                        "contract_name": "",
                        "contract_date": "",
                        "notice_construction_cost": "",
                        "notice_construction_cost_source": "",
                        "contract_amount": "",
                        "contract_amount_source": "",
                        "gross_area_scale": "",
                        "gross_area_scale_source": "",
                        "demand_contact": "",
                        "demand_contact_source": "",
                        "client_location": "",
                        "client_location_source": "",
                        "site_location": "",
                        "site_location_source": "",
                        "architect_office": "",
                        "architect_office_source": "",
                        "construction_start_date": "",
                        "construction_start_date_source": "",
                        "construction_duration_days": "",
                        "building_automation_estimated_amount": "",
                        "building_automation_estimated_amount_source": "",
                        "evidence_source": "",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "FOUND",
                        "hub_check_note": "",
                    },
                    f"export(native): {bid_no}: done",
                    False,
                )

            with patch(
                "backend.services.native_export_backend._build_post_collect_output_row",
                side_effect=_fake_build_row,
            ):
                run_post_collect_native(
                    input_csv,
                    output_csv,
                    params={"_advanced_options": {"export_row_workers": 2, "llm_correct": 0}},
                    progress_cb=progress_messages.append,
                )

        self.assertEqual(progress_messages[0], "export(native): R25BK00000002: done")
        self.assertEqual(progress_messages[1], "export(native): R25BK00000001: done")

    def test_run_post_collect_native_raises_interrupted_when_cancel_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "bid_no": "R25BK00000001",
                            "bid_ord": "000",
                            "project_name_norm": "project-one",
                            "g2b_verified": "Y",
                            "base_url": "",
                            "base_query": "",
                            "base_source_type": "web",
                            "search_link": "",
                            "internal_search_url": "",
                            "parser_version": "web-native-v1",
                            "run_mode": "native",
                            "status": "SEARCH_URL_BUILT",
                        },
                        {
                            "bid_no": "R25BK00000002",
                            "bid_ord": "000",
                            "project_name_norm": "project-two",
                            "g2b_verified": "Y",
                            "base_url": "",
                            "base_query": "",
                            "base_source_type": "web",
                            "search_link": "",
                            "internal_search_url": "",
                            "parser_version": "web-native-v1",
                            "run_mode": "native",
                            "status": "SEARCH_URL_BUILT",
                        },
                    ]
                )

            checks = {"count": 0}

            def _should_stop() -> bool:
                checks["count"] += 1
                return checks["count"] >= 2

            def _fake_build_row(*, group_item, llm_config, use_llm, should_stop=None):
                (bid_no, _bid_ord), _rows = group_item
                del llm_config, use_llm, should_stop
                return (
                    {
                        "bid_no": bid_no,
                        "bid_ord": "000",
                        "rank": "1",
                        "project_name_norm": bid_no,
                        "g2b_verified": "Y",
                        "source_type": "native_web",
                        "internal_search_url": "",
                        "post_url": "",
                        "post_title": "",
                        "winner_name": "",
                        "winner_confidence": "",
                        "winner_pattern": "",
                        "post_score": "",
                        "file_url": "",
                        "file_name": "",
                        "confidence_score": "",
                        "reason_code": "",
                        "review_flag": "",
                        "escalate": "",
                        "contract_name": "",
                        "contract_date": "",
                        "notice_construction_cost": "",
                        "notice_construction_cost_source": "",
                        "contract_amount": "",
                        "contract_amount_source": "",
                        "gross_area_scale": "",
                        "gross_area_scale_source": "",
                        "demand_contact": "",
                        "demand_contact_source": "",
                        "client_location": "",
                        "client_location_source": "",
                        "site_location": "",
                        "site_location_source": "",
                        "architect_office": "",
                        "architect_office_source": "",
                        "construction_start_date": "",
                        "construction_start_date_source": "",
                        "construction_duration_days": "",
                        "completion_expected_date_explicit": "",
                        "completion_expected_date_computed": "",
                        "building_automation_estimated_amount": "",
                        "building_automation_estimated_amount_source": "",
                        "evidence_source": "",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "FOUND",
                        "hub_check_note": "",
                    },
                    f"export(native): {bid_no}: done",
                    False,
                )

            with patch(
                "backend.services.native_export_backend._build_post_collect_output_row",
                side_effect=_fake_build_row,
            ):
                with self.assertRaises(InterruptedError):
                    run_post_collect_native(
                        input_csv,
                        output_csv,
                        params={"_advanced_options": {"export_row_workers": 1, "llm_correct": 0}},
                        should_stop=_should_stop,
                    )

        self.assertFalse(output_csv.exists())

    def test_run_post_collect_native_writes_structured_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.seoul.go.kr/board/view",
                        "base_query": "",
                        "base_source_type": "web",
                        "search_link": "https://www.seoul.go.kr/board/view",
                        "internal_search_url": "https://www.seoul.go.kr/board/view?q=design-project",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            fake_html = """
            <html>
              <title>설계공모 결과</title>
              <body>
                <table>
                  <tr><th>당선작</th><td>테스트건축사사무소</td></tr>
                  <tr><th>연면적</th><td>12,345㎡</td></tr>
                  <tr><th>공사비</th><td>123,000,000원</td></tr>
                  <tr><th>담당부서</th><td>시설과</td></tr>
                  <tr><th>담당자</th><td>김담당</td></tr>
                  <tr><th>발주처 위치</th><td>서울특별시 중구 세종대로 110</td></tr>
                  <tr><th>현장위치</th><td>서울특별시 중구 세종로</td></tr>
                  <tr><th>착공일</th><td>2025-04-01</td></tr>
                  <tr><th>빌딩자동제어 추정 금액</th><td>12,000,000원</td></tr>
                </table>
              </body>
            </html>
            """

            with patch("backend.services.native_export_backend.requests.get", return_value=_FakeResponse(fake_html)):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "FOUND")
        self.assertEqual(rows[0]["winner_name"], "테스트건축사사무소")
        self.assertEqual(rows[0]["source_type"], "native_web")
        self.assertEqual(rows[0]["gross_area_scale"], "12,345㎡")
        self.assertEqual(rows[0]["notice_construction_cost"], "123,000,000원")
        self.assertEqual(rows[0]["notice_construction_cost_source"], "confirmed_extracted")
        self.assertEqual(rows[0]["contract_amount"], "123,000,000원")
        self.assertEqual(rows[0]["demand_contact"], "시설과/김담당")
        self.assertEqual(rows[0]["client_location"], "서울특별시 중구 세종대로 110")
        self.assertEqual(rows[0]["site_location"], "서울특별시 중구 세종로")
        self.assertEqual(rows[0]["architect_office"], "")
        self.assertEqual(rows[0]["construction_start_date"], "2025-04-01")
        self.assertEqual(rows[0]["building_automation_estimated_amount"], "12,000,000원")
        self.assertEqual(rows[0]["contract_amount_source"], "confirmed_extracted")
        self.assertEqual(rows[0]["demand_contact_source"], "confirmed_extracted")
        self.assertEqual(rows[0]["architect_office_source"], "")
        self.assertEqual(rows[0]["building_automation_estimated_amount_source"], "confirmed_extracted")

    def test_run_post_collect_native_keeps_contact_blank_without_notice_contact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "notice_url",
                        "spec_doc_url",
                        "spec_doc_file_name",
                        "presmpt_prce",
                        "officer_name",
                        "officer_tel",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.seoul.go.kr/board/view",
                        "base_query": "",
                        "base_source_type": "g2b_api",
                        "search_link": "https://www.seoul.go.kr/board/view",
                        "internal_search_url": "https://www.seoul.go.kr/board/view?q=design-project",
                        "notice_url": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00554120&bidPbancOrd=000",
                        "spec_doc_url": "https://www.g2b.go.kr/download/spec.hwp",
                        "spec_doc_file_name": "공고문.hwp",
                        "presmpt_prce": "123000000",
                        "officer_name": "김담당",
                        "officer_tel": "02-111-2222",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            with patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>설계공모 결과</title><body>접근 가능 브라우저 안내</body></html>"),
            ), patch(
                "backend.services.native_export_backend.download_attachment_text",
                return_value="당선작 청명건축\n연면적 2,450㎡\n위치: 서울시 중구\n예정공사비 금123,000,000원",
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["winner_name"], "청명건축")
        self.assertEqual(rows[0]["gross_area_scale"], "2,450㎡")
        self.assertEqual(rows[0]["notice_construction_cost"], "123,000,000원")
        self.assertEqual(rows[0]["contract_amount"], "123,000,000원")
        self.assertEqual(rows[0]["contract_amount_source"], "confirmed_extracted")
        self.assertEqual(rows[0]["demand_contact"], "")
        self.assertEqual(rows[0]["demand_contact_source"], "")
        self.assertIn("공고문.hwp", rows[0]["hub_check_note"])
        self.assertIn("attachment_parsed", rows[0]["hub_check_note"])
        self.assertNotIn("demand_contact=fallback_seed_contact", rows[0]["hub_check_note"])

    def test_run_post_collect_native_keeps_contact_blank_when_resolution_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "notice_url",
                        "presmpt_prce",
                        "officer_name",
                        "officer_tel",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R26BK09999999",
                        "bid_ord": "000",
                        "project_name_norm": "review-contact-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/review",
                        "base_query": "",
                        "base_source_type": "g2b_api",
                        "search_link": "https://www.example.com/review",
                        "internal_search_url": "https://www.example.com/review?q=review-contact-project",
                        "notice_url": "https://www.example.com/review",
                        "presmpt_prce": "123000000",
                        "officer_name": "???",
                        "officer_tel": "02-111-2222",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            with patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>????</title><body>body</body></html>"),
            ), patch(
                "backend.services.native_export_backend._extract_notice_fields",
                return_value=ExtractedNoticeFields(
                    demand_contact="",
                    demand_contact_resolution_status="review",
                    demand_contact_resolution_reason="owner_candidate_needs_review",
                    demand_contact_resolution_phase="notice",
                    demand_contact_resolution_role="owner_contact",
                    demand_contact_resolution_owner_side="uncertain",
                    demand_contact_resolution_owner_side_basis="unknown",
                ),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["demand_contact"], "")
        self.assertEqual(rows[0]["demand_contact_source"], "")
        self.assertIn("contact_resolution=review", rows[0]["hub_check_note"])
        self.assertIn("demand_contact=expected_blank_contact_review", rows[0]["hub_check_note"])

    def test_run_post_collect_native_normalizes_confirmed_contact_before_writing_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "notice_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R26BK01111111",
                        "bid_ord": "000",
                        "project_name_norm": "contact-cleanup-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/notice",
                        "base_query": "",
                        "base_source_type": "g2b_api",
                        "search_link": "https://www.example.com/notice",
                        "internal_search_url": "https://www.example.com/notice?q=contact-cleanup-project",
                        "notice_url": "https://www.example.com/notice",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            with patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>공고</title><body>body</body></html>"),
            ), patch(
                "backend.services.native_export_backend._extract_notice_fields",
                return_value=ExtractedNoticeFields(
                    demand_contact="구체적인 실적 인정 여부는 문화기반조성과/062-613-3482",
                ),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["demand_contact"], "문화기반조성과/062-613-3482")
        self.assertEqual(rows[0]["demand_contact_source"], "confirmed_extracted")

    def test_run_post_collect_native_does_not_use_generic_architect_office_notice_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "notice_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00712759",
                        "bid_ord": "000",
                        "project_name_norm": "school-remodeling",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/notice",
                        "base_query": "",
                        "base_source_type": "g2b_api",
                        "search_link": "https://www.example.com/notice",
                        "internal_search_url": "https://www.example.com/notice?q=school-remodeling",
                        "notice_url": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00712759&bidPbancOrd=000",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            fake_html = """
            <html>
              <title>\uac74\ucd95\uc124\uacc4\uacf5\ubaa8</title>
              <body>
                <table>
                  <tr><th>\uc124\uacc4\uc0ac\ubb34\uc18c</th><td>\uac1c\uc124\uc790\uc640 \uacf5\ub3d9\uc5c5\ubb34 \uc218\ud589\uc744 \ud55c \uc790\ub2e4, \uad6d\ub0b4 \uac74\ucd95\uc0ac\uc0ac\ubb34\uc18c \uac1c\uc124\uc790\ub97c \ub300\ud45c\uc790\ub85c \uc120\uc784\ud558\uc5ec\uc57c \ud558\uba70, \ubaa8\ub4e0 \ubc95\uc801\uad8c\ub9ac\uc640 \uc758\ubb34\uc0ac\ud56d\uc740 \ub300\ud45c\uc790\uc5d0\uac8c \uadc0\uc18d\ub41c\ub2e4.</td></tr>
                </table>
              </body>
            </html>
            """

            with patch(
                "backend.services.native_export_backend.resolve_contract_by_bid_no",
                return_value=None,
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse(fake_html),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["architect_office"], "")
        self.assertEqual(rows[0]["architect_office_source"], "")

    def test_run_post_collect_native_skips_attachment_when_page_fields_are_sufficient(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "notice_url",
                        "spec_doc_url",
                        "spec_doc_file_name",
                        "presmpt_prce",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/base",
                        "base_query": "",
                        "base_source_type": "g2b_api",
                        "search_link": "https://www.example.com/search",
                        "internal_search_url": "https://www.example.com/search?q=design-project",
                        "notice_url": "https://www.example.com/notice",
                        "spec_doc_url": "https://www.example.com/doc1.hwp",
                        "spec_doc_file_name": "???.hwp",
                        "presmpt_prce": "123000000",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            progress_messages: list[str] = []
            with patch(
                "backend.services.native_export_backend.resolve_contract_by_bid_no",
                return_value=ContractLookupResult(contract_name="?????????"),
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>???? ??</title><body>body</body></html>"),
            ) as mock_get, patch(
                "backend.services.native_export_backend._extract_notice_fields",
                return_value=ExtractedNoticeFields(
                    winner_name="?????????",
                    gross_area_scale="2,450?",
                    construction_cost="123,000,000?",
                    demand_contact="???/02-111-2222",
                    construction_duration_days="120",
                ),
            ), patch(
                "backend.services.native_export_backend.download_attachment_text",
                side_effect=AssertionError("attachment path should be skipped"),
            ):
                run_post_collect_native(input_csv, output_csv, progress_cb=progress_messages.append)

        self.assertEqual(mock_get.call_count, 1)
        self.assertTrue(any("timing_ms(" in message for message in progress_messages))
        self.assertTrue(any("attachments=0/0" in message for message in progress_messages))

    def test_build_post_collect_output_row_continues_until_contact_is_filled(self) -> None:
        group_item = (
            ("R25BK00010000", "000"),
            [
                {
                    "bid_no": "R25BK00010000",
                    "bid_ord": "000",
                    "project_name_norm": "demo-project",
                    "org_name": "서울시",
                    "internal_search_url": "",
                    "base_url": "",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )
        extracted_texts: list[str] = []
        attachment_calls: list[str] = []

        def _fake_extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str):
            extracted_texts.append(text)
            if len(extracted_texts) == 1:
                return ExtractedNoticeFields()
            if len(extracted_texts) == 2:
                return ExtractedNoticeFields(
                    winner_name="청명건축",
                    gross_area_scale="2,450㎡",
                    construction_cost="123,000,000원",
                )
            return ExtractedNoticeFields(
                winner_name="청명건축",
                gross_area_scale="2,450㎡",
                construction_cost="123,000,000원",
                demand_contact="시설과/02-111-2222",
            )

        def _fake_attachment_loader(*, url: str, file_name: str):
            attachment_calls.append(file_name)
            if len(attachment_calls) > 2:
                raise AssertionError("attachment loop should stop once enriched fields are complete")
            return AttachmentTextLoadResult(
                text=(
                    "당선자 청명건축\n연면적 2,450㎡\n공사비 123,000,000원"
                    if len(attachment_calls) == 1
                    else "문의처 시설과/02-111-2222"
                ),
                download_ms=5,
                parse_ms=7,
            )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=None,
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[
                AttachmentDocument(url="https://example.com/a.hwp", file_name="공고문.hwp", score=10, is_announcement_doc=True),
                AttachmentDocument(url="https://example.com/b.hwp", file_name="과업지시서.hwp", score=9, is_announcement_doc=False),
            ],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            side_effect=_fake_extract_notice_fields,
        ), patch(
            "backend.services.native_export_backend._load_attachment_text_with_timing",
            side_effect=_fake_attachment_loader,
        ):
            out_row, progress_message, llm_used = _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(out_row["winner_name"], "청명건축")
        self.assertEqual(attachment_calls, ["공고문.hwp", "과업지시서.hwp"])
        self.assertEqual(extracted_texts[0], "page text")
        self.assertTrue(extracted_texts[1].endswith("공고문.hwp\n당선자 청명건축\n연면적 2,450㎡\n공사비 123,000,000원"))
        self.assertIn("attachments=2/2", progress_message)
        self.assertFalse(llm_used)

    def test_build_post_collect_output_row_continues_past_invalid_huge_area(self) -> None:
        group_item = (
            ("R25BK00652851", "000"),
            [
                {
                    "bid_no": "R25BK00652851",
                    "bid_ord": "000",
                    "project_name_norm": "digital-cancer-center",
                    "org_name": "화순전남대학교병원",
                    "internal_search_url": "",
                    "base_url": "",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )
        attachment_calls: list[str] = []
        extract_calls = {"count": 0}

        def _fake_extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str):
            extract_calls["count"] += 1
            if extract_calls["count"] == 1:
                return ExtractedNoticeFields()
            if extract_calls["count"] == 2:
                return ExtractedNoticeFields(
                    gross_area_scale="33,800,000㎡",
                    construction_cost="33,800,000,000원",
                    demand_contact="시설과/061-379-7502",
                )
            return ExtractedNoticeFields(
                gross_area_scale="10,600㎡",
                construction_cost="33,800,000,000원",
                demand_contact="시설과/061-379-7502",
            )

        def _fake_attachment_loader(*, url: str, file_name: str):
            attachment_calls.append(file_name)
            if len(attachment_calls) > 2:
                raise AssertionError("attachment loop should continue only until valid area is found")
            return AttachmentTextLoadResult(
                text=(
                    "사업 규모\n총공사비(예정) : 33,800,000천원\n"
                    if len(attachment_calls) == 1
                    else "연 면 적 : 10,600㎡\n문의처 시설과/061-379-7502"
                ),
                download_ms=3,
                parse_ms=4,
            )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=None,
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[
                AttachmentDocument(url="https://example.com/a.hwp", file_name="공고문.hwp", score=10, is_announcement_doc=True),
                AttachmentDocument(url="https://example.com/b.hwp", file_name="과업내용서.hwp", score=9, is_announcement_doc=False),
            ],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            side_effect=_fake_extract_notice_fields,
        ), patch(
            "backend.services.native_export_backend._load_attachment_text_with_timing",
            side_effect=_fake_attachment_loader,
        ):
            out_row, progress_message, llm_used = _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(attachment_calls, ["공고문.hwp", "과업내용서.hwp"])
        self.assertEqual(out_row["gross_area_scale"], "10,600㎡")
        self.assertIn("attachments=2/2", progress_message)
        self.assertFalse(llm_used)

    def test_collect_attachment_documents_limits_to_top_three(self) -> None:
        row = {
            "spec_doc_url_1": "https://example.com/a.hwp",
            "spec_doc_file_name_1": "공고문.hwp",
            "spec_doc_url_2": "https://example.com/b.pdf",
            "spec_doc_file_name_2": "과업지시서.pdf",
            "spec_doc_url_3": "https://example.com/c.hwpx",
            "spec_doc_file_name_3": "설계지침.hwpx",
            "spec_doc_url_4": "https://example.com/d.hwp",
            "spec_doc_file_name_4": "참고자료.hwp",
        }

        documents = _collect_attachment_documents(
            row,
            spec_doc_url="",
            spec_doc_file_name="",
        )

        self.assertEqual(len(documents), 3)
        self.assertEqual(
            [document.file_name for document in documents],
            ["공고문.hwp", "설계지침.hwpx", "과업지시서.pdf"],
        )

    def test_collect_attachment_documents_builds_g2b_download_fallbacks(self) -> None:
        row = {
            "bid_no": "R26BK01318924",
            "bid_ord": "001",
            "g2b_verified": "Y",
            "notice_url": (
                "https://www.g2b.go.kr/link/PNPE027_01/single/"
                "?bidPbancNo=R26BK01318924&bidPbancOrd=001&prcmBsneSeCd=05&pbancType=pbanc"
            ),
        }

        documents = _collect_attachment_documents(
            row,
            spec_doc_url="",
            spec_doc_file_name="",
        )

        self.assertEqual(len(documents), 3)
        self.assertEqual(
            [document.url for document in documents],
            [
                (
                    "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
                    "?bidPbancNo=R26BK01318924&bidPbancOrd=001&fileSeq=1&fileType=&prcmBsneSeCd=05"
                ),
                (
                    "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
                    "?bidPbancNo=R26BK01318924&bidPbancOrd=001&fileSeq=2&fileType=&prcmBsneSeCd=05"
                ),
                (
                    "https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do"
                    "?bidPbancNo=R26BK01318924&bidPbancOrd=001&fileSeq=3&fileType=&prcmBsneSeCd=05"
                ),
            ],
        )
        self.assertEqual([document.file_name for document in documents], ["", "", ""])

    def test_should_continue_attachment_scan_reads_two_documents_before_stopping(self) -> None:
        extracted = ExtractedNoticeFields(
            gross_area_scale="2,450sqm",
            construction_cost="12,172,404,000won",
            demand_contact="admin-office/055-960-2791",
            construction_duration_days="120",
        )

        self.assertTrue(
            _should_continue_attachment_scan(
                tried_count=1,
                available_count=3,
                extracted=extracted,
            )
        )
        self.assertFalse(
            _should_continue_attachment_scan(
                tried_count=2,
                available_count=3,
                extracted=extracted,
            )
        )

    def test_should_continue_attachment_scan_uses_third_document_when_core_fields_missing(self) -> None:
        extracted = ExtractedNoticeFields(
            gross_area_scale="2,450sqm",
            construction_cost="12,172,404,000won",
            demand_contact="",
        )

        self.assertTrue(
            _should_continue_attachment_scan(
                tried_count=2,
                available_count=3,
                extracted=extracted,
            )
        )
        self.assertFalse(
            _should_continue_attachment_scan(
                tried_count=3,
                available_count=3,
                extracted=extracted,
            )
        )

    def test_build_post_collect_output_row_reads_second_attachment_even_when_first_is_complete(self) -> None:
        group_item = (
            ("R25BK00554120", "000"),
            [
                {
                    "bid_no": "R25BK00554120",
                    "bid_ord": "000",
                    "project_name_norm": "hamyang-library",
                    "org_name": "hamyang-office",
                    "internal_search_url": "",
                    "base_url": "",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )
        attachment_calls: list[str] = []
        extract_calls = {"count": 0}

        def _fake_extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str):
            extract_calls["count"] += 1
            if extract_calls["count"] == 1:
                return ExtractedNoticeFields()
            return ExtractedNoticeFields(
                gross_area_scale="2,450sqm",
                construction_cost="12,172,404,000won",
                demand_contact="admin-office/055-960-2791",
                construction_duration_days="120",
            )

        def _fake_attachment_loader(*, url: str, file_name: str):
            attachment_calls.append(file_name)
            return AttachmentTextLoadResult(
                text=f"{file_name} attachment text",
                download_ms=1,
                parse_ms=1,
            )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=None,
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[
                AttachmentDocument(url="https://example.com/a.hwp", file_name="notice-1.hwp", score=10, is_announcement_doc=True),
                AttachmentDocument(url="https://example.com/b.hwp", file_name="notice-2.hwp", score=9, is_announcement_doc=False),
                AttachmentDocument(url="https://example.com/c.hwp", file_name="notice-3.hwp", score=8, is_announcement_doc=False),
            ],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            side_effect=_fake_extract_notice_fields,
        ), patch(
            "backend.services.native_export_backend._load_attachment_text_with_timing",
            side_effect=_fake_attachment_loader,
        ):
            _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(attachment_calls, ["notice-1.hwp", "notice-2.hwp"])

    def test_build_post_collect_output_row_reads_third_attachment_only_when_second_is_still_missing_core_fields(self) -> None:
        group_item = (
            ("R25BK01096486", "000"),
            [
                {
                    "bid_no": "R25BK01096486",
                    "bid_ord": "000",
                    "project_name_norm": "yeongbuk-center",
                    "org_name": "pocheon-corp",
                    "internal_search_url": "",
                    "base_url": "",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )
        attachment_calls: list[str] = []
        extract_calls = {"count": 0}

        def _fake_extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str):
            extract_calls["count"] += 1
            if extract_calls["count"] == 1:
                return ExtractedNoticeFields()
            if extract_calls["count"] in (2, 3):
                return ExtractedNoticeFields(
                    gross_area_scale="657sqm",
                    construction_cost="1,982,881,000won",
                    demand_contact="",
                )
            return ExtractedNoticeFields(
                gross_area_scale="657sqm",
                construction_cost="1,982,881,000won",
                demand_contact="pocheon-corp/031-000-0000",
            )

        def _fake_attachment_loader(*, url: str, file_name: str):
            attachment_calls.append(file_name)
            return AttachmentTextLoadResult(
                text=f"{file_name} attachment text",
                download_ms=1,
                parse_ms=1,
            )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=None,
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[
                AttachmentDocument(url="https://example.com/a.hwp", file_name="notice-1.hwp", score=10, is_announcement_doc=True),
                AttachmentDocument(url="https://example.com/b.hwp", file_name="notice-2.hwp", score=9, is_announcement_doc=False),
                AttachmentDocument(url="https://example.com/c.hwp", file_name="notice-3.hwp", score=8, is_announcement_doc=False),
            ],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            side_effect=_fake_extract_notice_fields,
        ), patch(
            "backend.services.native_export_backend._load_attachment_text_with_timing",
            side_effect=_fake_attachment_loader,
        ):
            _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(attachment_calls, ["notice-1.hwp", "notice-2.hwp", "notice-3.hwp"])

    def test_build_post_collect_output_row_reads_third_attachment_when_period_is_missing(self) -> None:
        group_item = (
            ("R26BK01339486", "002"),
            [
                {
                    "bid_no": "R26BK01339486",
                    "bid_ord": "002",
                    "project_name_norm": "changwon-library",
                    "org_name": "gyeongnam-office",
                    "internal_search_url": "",
                    "base_url": "",
                    "notice_url": "https://example.com/notice",
                    "g2b_verified": "Y",
                    "spec_doc_url": "",
                    "spec_doc_file_name": "",
                }
            ],
        )
        attachment_calls: list[str] = []
        extract_calls = {"count": 0}

        def _fake_extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str):
            extract_calls["count"] += 1
            if extract_calls["count"] == 1:
                return ExtractedNoticeFields()
            if extract_calls["count"] in (2, 3):
                return ExtractedNoticeFields(
                    gross_area_scale="3,000sqm",
                    construction_cost="1,000,000,000won",
                    demand_contact="admin-office/055-000-0000",
                    construction_duration_days="",
                )
            return ExtractedNoticeFields(
                gross_area_scale="3,000sqm",
                construction_cost="1,000,000,000won",
                demand_contact="admin-office/055-000-0000",
                construction_duration_days="240",
                construction_start_date="착수일로부터240일간",
            )

        def _fake_attachment_loader(*, url: str, file_name: str):
            attachment_calls.append(file_name)
            return AttachmentTextLoadResult(
                text=f"{file_name} attachment text",
                download_ms=1,
                parse_ms=1,
            )

        with patch(
            "backend.services.native_export_backend.resolve_contract_by_bid_no",
            return_value=None,
        ), patch(
            "backend.services.native_export_backend._fetch_page_documents",
            return_value=[PageDocument(url="https://example.com/notice", title="Demo", text="page text")],
        ), patch(
            "backend.services.native_export_backend._collect_attachment_documents",
            return_value=[
                AttachmentDocument(url="https://example.com/a.hwp", file_name="notice-1.hwp", score=10, is_announcement_doc=True),
                AttachmentDocument(url="https://example.com/b.hwp", file_name="notice-2.hwp", score=9, is_announcement_doc=False),
                AttachmentDocument(url="https://example.com/c.hwp", file_name="task-order.hwp", score=8, is_announcement_doc=False),
            ],
        ), patch(
            "backend.services.native_export_backend._extract_notice_fields",
            side_effect=_fake_extract_notice_fields,
        ), patch(
            "backend.services.native_export_backend._load_attachment_text_with_timing",
            side_effect=_fake_attachment_loader,
        ):
            out_row, _progress_message, _llm_used = _build_post_collect_output_row(
                group_item=group_item,
                llm_config=object(),
                use_llm=False,
            )

        self.assertEqual(attachment_calls, ["notice-1.hwp", "notice-2.hwp", "task-order.hwp"])
        self.assertEqual(out_row["construction_duration_days"], "240")

    def test_run_post_collect_native_prefers_announcement_contact_and_multi_doc_area_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "notice_url",
                        "spec_doc_url",
                        "spec_doc_file_name",
                        "spec_doc_url_1",
                        "spec_doc_file_name_1",
                        "spec_doc_url_2",
                        "spec_doc_file_name_2",
                        "spec_doc_url_3",
                        "spec_doc_file_name_3",
                        "presmpt_prce",
                        "officer_name",
                        "officer_tel",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00999999",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.example.com/view",
                        "base_query": "",
                        "base_source_type": "g2b_api",
                        "search_link": "https://www.example.com/view",
                        "internal_search_url": "https://www.example.com/view?q=design-project",
                        "notice_url": "https://www.g2b.go.kr/link/notice",
                        "spec_doc_url": "https://www.g2b.go.kr/download/doc1.hwp",
                        "spec_doc_file_name": "???? ???.hwp",
                        "spec_doc_url_1": "https://www.g2b.go.kr/download/doc1.hwp",
                        "spec_doc_file_name_1": "???? ???.hwp",
                        "spec_doc_url_2": "https://www.g2b.go.kr/download/doc2.hwp",
                        "spec_doc_file_name_2": "?????.hwp",
                        "spec_doc_url_3": "https://www.g2b.go.kr/download/doc3.hwp",
                        "spec_doc_file_name_3": "???? ???.hwp",
                        "presmpt_prce": "688336364",
                        "officer_name": "???",
                        "officer_tel": "070-4056-7566",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            def _fake_download_attachment_text(*, url: str, file_name: str = "", session=None) -> str:
                if url.endswith("doc1.hwp"):
                    return "??? ??????? 055-960-2791"
                if url.endswith("doc2.hwp"):
                    return "????? 3,600?\n????? 15,043,000,000?"
                if url.endswith("doc3.hwp"):
                    return "???? 180?"
                return ""

            def _fake_extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str):
                return ExtractedNoticeFields(
                    gross_area_scale="3,600?" if "3,600?" in text else "",
                    construction_cost="15,043,000,000?" if "15,043,000,000?" in text else "",
                    demand_contact="??????/055-960-2791" if "055-960-2791" in text else "",
                    construction_duration_days="180" if "180?" in text else "",
                )

            with patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>??</title><body>???? ??</body></html>"),
            ), patch(
                "backend.services.native_export_backend.download_attachment_text",
                side_effect=_fake_download_attachment_text,
            ), patch(
                "backend.services.native_export_backend._extract_notice_fields",
                side_effect=_fake_extract_notice_fields,
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["gross_area_scale"], "3,600?")
        self.assertEqual(rows[0]["notice_construction_cost"], "15,043,000,000?")
        self.assertEqual(rows[0]["demand_contact"], "??????/055-960-2791")
        self.assertEqual(rows[0]["construction_duration_days"], "180")

    def test_run_post_collect_native_estimates_building_automation_amount_from_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "project_name_norm",
                        "g2b_verified",
                        "base_url",
                        "base_query",
                        "base_source_type",
                        "search_link",
                        "internal_search_url",
                        "parser_version",
                        "run_mode",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "design-project",
                        "g2b_verified": "Y",
                        "base_url": "https://www.seoul.go.kr/board/view",
                        "base_query": "",
                        "base_source_type": "web",
                        "search_link": "https://www.seoul.go.kr/board/view",
                        "internal_search_url": "https://www.seoul.go.kr/board/view?q=design-project",
                        "parser_version": "web-native-v1",
                        "run_mode": "native",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            fake_html = """
            <html>
              <title>설계공모 결과</title>
              <body>
                <table>
                  <tr><th>당선자</th><td>테스트건축사사무소</td></tr>
                  <tr><th>공사비</th><td>12,172,404,000원</td></tr>
                </table>
              </body>
            </html>
            """

            with patch("backend.services.native_export_backend.requests.get", return_value=_FakeResponse(fake_html)):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["building_automation_estimated_amount"], "1.83억원~2.43억원")
        self.assertEqual(rows[0]["building_automation_estimated_amount_source"], "estimated_notice_construction_cost")

    def test_run_post_collect_native_marks_lofin_contract_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
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
                        "bid_no": "R25BK00570000",
                        "bid_ord": "000",
                        "project_name_norm": "함양소방서 산악구조대 신축사업 설계공모",
                        "org_name": "경상남도",
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
                return_value=ContractLookupResult(
                    contract_name="핀건축사사무소",
                    contract_date="20250407",
                    contract_amount="3988000000",
                    target_name="함양소방서 산악구조대 신축사업 설계공모",
                    inst_name="경상남도",
                    match_score=0.88,
                    source_type="lofin_api",
                ),
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>공고</title><body>내용 없음</body></html>"),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["source_type"], "lofin_api")
        self.assertEqual(rows[0]["reason_code"], "LOFIN_CONTRACT_STRONG_MATCH")
        self.assertEqual(rows[0]["winner_pattern"], "LOFIN_API:cltNm")
        self.assertEqual(rows[0]["evidence_source"], "lofin:함양소방서 산악구조대 신축사업 설계공모|경상남도")

    def test_run_post_collect_native_marks_eais_contract_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
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
                        "project_name_norm": "양산소방서 119구조대 신축사업 설계공모",
                        "org_name": "경상남도",
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
                return_value=ContractLookupResult(
                    contract_name="어반차건축사사무소&에스에이건축사사무소",
                    contract_date="2025-03-25",
                    contract_amount="3838000000",
                    target_name="양산소방서 119구조대 신축사업 설계공모",
                    inst_name="경상남도",
                    match_score=0.81,
                    source_type="eais_web",
                ),
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>공고</title><body>내용 없음</body></html>"),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["source_type"], "eais_web")
        self.assertEqual(rows[0]["reason_code"], "EAIS_CONTRACT_MATCH")
        self.assertEqual(rows[0]["winner_pattern"], "EAIS_API:list+detail")
        self.assertEqual(rows[0]["evidence_source"], "eais:양산소방서 119구조대 신축사업 설계공모|경상남도")

    def test_run_post_collect_native_marks_hub_contract_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
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
                        "bid_no": "R25BK00937321",
                        "bid_ord": "000",
                        "project_name_norm": "(집행대행)(가칭) 구미늘품뜰 거점형 늘봄센터 신축공사 설계공모",
                        "org_name": "경상북도교육청",
                        "announce_date": "20250702",
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
                return_value=ContractLookupResult(
                    contract_name="와이원건축사사무소",
                    target_name="(가칭)구미늘품뜰 거점형 늘봄센터 신축공사",
                    inst_name="경상북도교육청",
                    match_score=0.91,
                    source_type="hub_result",
                ),
            ), patch(
                "backend.services.native_export_backend.requests.get",
                return_value=_FakeResponse("<html><title>공고</title><body>내용 없음</body></html>"),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["source_type"], "hub_result")
        self.assertEqual(rows[0]["reason_code"], "HUB_RESULT_MATCH")
        self.assertEqual(rows[0]["winner_pattern"], "HUB_RESULT:prwinPdtList")
        self.assertEqual(rows[0]["evidence_source"], "hub:(가칭)구미늘품뜰 거점형 늘봄센터 신축공사|경상북도교육청")
