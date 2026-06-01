from __future__ import annotations

from dataclasses import dataclass
import unittest

import backend.services.native_export_backend_runtime as runtime
from backend.services.native_export_backend_page_runtime import build_page_fetch_urls
from backend.services.native_export_backend_page_runtime import fetch_page_documents
from backend.services.native_export_backend_page_runtime import pick_primary_document
from backend.services.native_export_backend_row_runtime import build_output_row
from backend.services.native_export_backend_row_runtime import build_progress_message


@dataclass(frozen=True)
class PageDocument:
    url: str
    title: str
    text: str


@dataclass(frozen=True)
class ResolvedField:
    value: str = ""
    source: str = ""


class NativeExportBackendRuntimeHelpersTests(unittest.TestCase):
    def test_public_import_surface_still_exposes_runtime_symbols(self) -> None:
        self.assertTrue(hasattr(runtime, "run_post_collect_native"))
        self.assertTrue(hasattr(runtime, "PageDocument"))
        self.assertTrue(hasattr(runtime, "_build_post_collect_output_row"))

    def test_build_page_fetch_urls_preserves_order_and_removes_duplicates(self) -> None:
        self.assertEqual(
            build_page_fetch_urls(
                notice_url=" https://example.com/notice ",
                base_url="https://example.com/base",
                search_url="https://example.com/notice",
            ),
            ["https://example.com/notice", "https://example.com/base"],
        )

    def test_fetch_page_documents_skips_blank_and_duplicate_urls(self) -> None:
        calls: list[str] = []

        def _fake_fetch_page_text(url: str) -> tuple[str, str]:
            calls.append(url)
            return f"title:{url}", f"text:{url}"

        documents = fetch_page_documents(
            ["", "https://example.com/a", "https://example.com/a", "https://example.com/b"],
            fetch_page_text_fn=_fake_fetch_page_text,
            raise_if_stop_requested_fn=lambda _should_stop: None,
            page_document_cls=PageDocument,
        )

        self.assertEqual(calls, ["https://example.com/a", "https://example.com/b"])
        self.assertEqual([document.url for document in documents], calls)

    def test_pick_primary_document_prefers_richest_text(self) -> None:
        selected = pick_primary_document(
            [
                PageDocument(url="https://example.com/a", title="A", text=""),
                PageDocument(url="https://example.com/b", title="B", text="short"),
                PageDocument(url="https://example.com/c", title="C", text="much longer body"),
            ],
            page_document_cls=PageDocument,
        )

        self.assertEqual(selected.url, "https://example.com/c")

    def test_build_output_row_and_progress_message_use_resolved_values(self) -> None:
        out_row = build_output_row(
            bid_no="R25BK0001",
            bid_ord="000",
            best_row={"g2b_verified": "Y"},
            preferred_document_url="https://example.com/post",
            notice_url="",
            search_url="https://example.com/search",
            base_url="https://example.com/base",
            title="Demo title",
            winner_name="Demo winner",
            confidence="high",
            winner_pattern="pattern",
            score="0.95",
            reason_code="MATCH",
            review_flag="N",
            contract_name="Demo contract",
            contract_date="2026-04-25",
            notice_construction_cost=ResolvedField(value="1,000", source="confirmed_extracted"),
            contract_amount=ResolvedField(value="2,000", source="confirmed_contract"),
            gross_area_scale=ResolvedField(value="300", source="confirmed_extracted"),
            demand_contact=ResolvedField(value="demo/02-111-2222", source="confirmed_extracted"),
            client_location=ResolvedField(value="서울", source="confirmed_extracted"),
            site_location=ResolvedField(value="강남", source="confirmed_extracted"),
            architect_office=ResolvedField(value="demo architects", source="confirmed_contract_lookup"),
            construction_start_date=ResolvedField(value="2026-05-01", source="confirmed_extracted"),
            construction_duration_days="30",
            completion_expected_date_explicit="",
            completion_expected_date_computed="2026-05-31",
            building_auto_est=ResolvedField(value="120", source="estimated_contract_amount"),
            evidence_source="g2b_contract:demo",
            status="FOUND",
            spec_doc_file_name="spec.hwp",
            contract_hit_note="g2b_contract_hit",
            attachment_note="attachment_parsed:1/1",
            synap_note="synap_rescued=contact",
            llm_corrected_fields=("area",),
            extracted_contact_resolution_status="resolved",
            extracted_contact_resolution_reason="rule",
            extracted_contact_resolution_phase="page",
            extracted_contact_resolution_role="owner",
            extracted_contact_resolution_owner_side="client",
            extracted_contact_resolution_owner_side_basis="label",
            expected_blank_external_portal=False,
            expected_blank_contact_review=False,
            fallback_notes=["contract_amount=fallback_seed_presmpt_prce"],
            join_non_empty_fn=lambda values, sep: sep.join(value for value in values if str(value or "").strip()),
        )

        progress_message = build_progress_message(
            bid_no="R25BK0001",
            status="FOUND",
            winner_name="Demo winner",
            gross_area_scale="300",
            construction_cost="1,000",
            contract_lookup_meta=type(
                "Meta",
                (),
                {
                    "contract_lookup_path": "g2b",
                    "query_sweep_used": True,
                    "query_sweep_hit": False,
                    "lofin_date_workers": 2,
                    "lofin_global_semaphore_limit": 4,
                    "lofin_max_active_requests": 3,
                    "lofin_dates_examined": 6,
                    "lofin_requests_total": 7,
                    "lofin_pages_fetched_total": 8,
                    "lofin_powershell_used": False,
                    "lofin_ssl_fallback_used": True,
                    "lofin_timeout_count": 1,
                    "lofin_first_nonempty_date": "2026-01-01",
                    "lofin_hit_date": "",
                    "lofin_best_score": 0.87,
                    "lofin_budget_seconds": 12.3,
                    "lofin_budget_exhausted": False,
                },
            )(),
            document_count=2,
            attachment_tried_count=1,
            attachment_parsed_count=1,
            timing_ms={
                "contract_lookup": 11,
                "page_fetch": 22,
                "attachment_download": 33,
                "attachment_parse": 44,
            },
        )

        self.assertEqual(out_row["post_url"], "https://example.com/post")
        self.assertEqual(out_row["winner_name"], "Demo winner")
        self.assertIn("contract_amount=fallback_seed_presmpt_prce", out_row["hub_check_note"])
        self.assertIn("lofin_best=0.870", progress_message)
        self.assertIn("attachments=1/1", progress_message)
