from __future__ import annotations

from dataclasses import dataclass
import unittest

from backend.services.native_export_backend_notice_flow_runtime import collect_notice_context
from backend.services.native_export_backend_notice_flow_runtime import enrich_with_attachment_documents


@dataclass(frozen=True)
class PageDocument:
    url: str
    title: str
    text: str


@dataclass(frozen=True)
class AttachmentDocument:
    url: str
    file_name: str
    score: int
    is_announcement_doc: bool
    text: str = ""


@dataclass(frozen=True)
class ExtractedFields:
    winner_name: str = ""
    winner_pattern: str = ""
    gross_area_scale: str = ""
    construction_cost: str = ""
    demand_contact: str = ""
    client_location: str = ""
    site_location: str = ""
    architect_office: str = ""
    construction_start_date: str = ""
    construction_duration_days: str = ""
    completion_expected_date_explicit: str = ""
    building_automation_estimated_amount: str = ""
    llm_corrected_fields: tuple[str, ...] = ()
    demand_contact_resolution_status: str = ""
    demand_contact_resolution_reason: str = ""
    demand_contact_resolution_phase: str = ""
    demand_contact_resolution_role: str = ""
    demand_contact_resolution_owner_side: str = ""
    demand_contact_resolution_owner_side_basis: str = ""


class NativeExportBackendNoticeFlowRuntimeTests(unittest.TestCase):
    def test_collect_notice_context_fetches_extra_pages_when_first_pass_is_sparse(self) -> None:
        page_fetch_calls: list[list[str]] = []

        def _fake_fetch_page_documents(urls, should_stop):
            page_fetch_calls.append(list(urls))
            return [
                PageDocument(url=url, title=f"title:{url}", text=f"text:{url}")
                for url in urls
            ]

        extraction_calls: list[str] = []

        def _fake_extract_notice_fields(*, title, text, project_name, org_name):
            extraction_calls.append(text)
            if len(extraction_calls) == 1:
                return ExtractedFields(demand_contact="", gross_area_scale="10")
            return ExtractedFields(demand_contact="02-111-2222", gross_area_scale="300")

        result = collect_notice_context(
            page_urls=["https://example.com/1", "https://example.com/2"],
            project_name_norm="demo",
            org_name="demo org",
            should_stop=None,
            raise_if_stop_requested_fn=lambda _should_stop: None,
            fetch_page_documents_fn=_fake_fetch_page_documents,
            pick_primary_document_fn=lambda documents: documents[-1],
            extract_notice_fields_fn=_fake_extract_notice_fields,
            has_page_enrichment_fields_fn=lambda extracted: bool(extracted.demand_contact),
        )

        self.assertEqual(page_fetch_calls, [["https://example.com/1"], ["https://example.com/2"]])
        self.assertEqual(result.title, "title:https://example.com/2")
        self.assertEqual(result.preferred_document.url, "https://example.com/2")
        self.assertEqual(result.combined_text, "text:https://example.com/1\ntext:https://example.com/2")
        self.assertEqual(result.extracted.demand_contact, "02-111-2222")

    def test_enrich_with_attachment_documents_merges_contact_and_synap_notes(self) -> None:
        load_calls: list[str] = []

        def _fake_load_attachment_text_with_timing(*, url, file_name):
            load_calls.append(file_name)
            return type(
                "AttachmentLoadResult",
                (),
                {
                    "text": f"contact:{file_name}",
                    "download_ms": 7,
                    "parse_ms": 3,
                },
            )()

        replace_calls: list[tuple[str, str]] = []

        def _fake_replace(extracted, **changes):
            replace_calls.append((extracted.demand_contact, changes["demand_contact"]))
            return ExtractedFields(**{**extracted.__dict__, **changes})

        extracted = ExtractedFields(demand_contact="")
        result = enrich_with_attachment_documents(
            attachment_docs=[
                AttachmentDocument(
                    url="https://example.com/a",
                    file_name="notice-a.hwp",
                    score=10,
                    is_announcement_doc=True,
                )
            ],
            extracted=extracted,
            combined_text="page-body",
            title="demo title",
            bid_no="BID-1",
            bid_ord="000",
            org_name="demo org",
            best_row={"item_pbanc_unty_atch_file_no": "123"},
            should_stop=None,
            timing_ms={"attachment_download": 0, "attachment_parse": 0},
            raise_if_stop_requested_fn=lambda _should_stop: None,
            load_attachment_text_with_timing_fn=_fake_load_attachment_text_with_timing,
            extract_notice_fields_fn=lambda **_kwargs: ExtractedFields(demand_contact="page-contact"),
            extract_contact_from_notice_text_fn=lambda text, _org_name: f"picked:{text.split(':', 1)[-1]}",
            select_best_attachment_contact_fn=lambda **kwargs: kwargs["announcement_contact"],
            maybe_rescue_attachment_fields_with_synap_fn=lambda **kwargs: (
                kwargs["extracted"],
                ("contact",),
            ),
            merge_synap_note_fn=lambda current_note, rescued_fields: ",".join(filter(None, [current_note, *rescued_fields])),
            should_continue_attachment_scan_fn=lambda **_kwargs: False,
            replace_fn=_fake_replace,
            attachment_text_payload_cls=lambda **kwargs: type("Payload", (), kwargs)(),
        )

        self.assertEqual(load_calls, ["notice-a.hwp"])
        self.assertEqual(replace_calls, [("page-contact", "picked:notice-a.hwp")])
        self.assertEqual(result.extracted.demand_contact, "picked:notice-a.hwp")
        self.assertEqual(result.payload.tried_count, 1)
        self.assertEqual(result.payload.parsed_count, 1)
        self.assertEqual(result.payload.download_ms, 7)
        self.assertEqual(result.payload.parse_ms, 3)
        self.assertEqual(result.attachment_note, "attachment_parsed:1/1")
        self.assertEqual(result.synap_note, "contact")
        self.assertEqual(result.attachment_text, "notice-a.hwp\ncontact:notice-a.hwp")


if __name__ == "__main__":
    unittest.main()
