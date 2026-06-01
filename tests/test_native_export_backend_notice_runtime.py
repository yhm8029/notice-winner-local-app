from __future__ import annotations

import unittest

from backend.services.native_export_backend_notice_runtime import _extract_duration_days_from_period_display
from backend.services.native_export_backend_notice_runtime import extract_labeled_value
from backend.services.native_export_backend_notice_runtime import fetch_page_text
from backend.services.native_export_backend_notice_runtime import has_attachment_enrichment_fields
from backend.services.native_export_backend_notice_runtime import resolve_candidate_winner_name
from backend.services.native_export_backend_notice_runtime import should_try_attachment


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class _Extracted:
    def __init__(self, *, gross_area_scale: str = "", construction_cost: str = "", demand_contact: str = "") -> None:
        self.gross_area_scale = gross_area_scale
        self.construction_cost = construction_cost
        self.demand_contact = demand_contact


class NativeExportBackendNoticeRuntimeTests(unittest.TestCase):
    def test_fetch_page_text_strips_markup_and_decodes_title(self) -> None:
        title, text = fetch_page_text(
            "https://example.com/notice",
            requests_get_fn=lambda url, headers, timeout: _FakeResponse(
                "<html><head><title>Demo &amp; Notice</title></head>"
                "<body><script>ignore()</script><div>First</div><p>Second</p></body></html>"
            ),
            decode_html_and_strip_fn=lambda value: " ".join(str(value).split()),
        )

        self.assertEqual(title, "Demo & Notice")
        self.assertIn("First", text)
        self.assertIn("Second", text)
        self.assertNotIn("ignore()", text)

    def test_extract_labeled_value_uses_following_line_when_inline_value_missing(self) -> None:
        self.assertEqual(
            extract_labeled_value("담당부서\n건축과", ["담당부서"]),
            "건축과",
        )

    def test_extract_duration_days_from_period_display_uses_long_display_over_short_notice_window(self) -> None:
        self.assertEqual(_extract_duration_days_from_period_display("착수일로부터180일간"), 180)

    def test_resolve_candidate_winner_name_prefers_contract_hit_then_extracted(self) -> None:
        contract_hit = type("Hit", (), {"contract_name": "Contract Winner"})()
        extracted = type("Extracted", (), {"winner_name": "Extracted Winner"})()

        selected = resolve_candidate_winner_name(
            contract_hit=contract_hit,
            extracted=extracted,
            best_row={"winner_name": "Row Winner", "contract_name": "Row Contract"},
        )

        self.assertEqual(selected, "Contract Winner")

    def test_should_try_attachment_requires_missing_attachment_fields(self) -> None:
        extracted = _Extracted(gross_area_scale="120", construction_cost="1,000", demand_contact="02-111-2222")
        self.assertTrue(has_attachment_enrichment_fields(extracted, extract_area_number_fn=lambda value: int(value)))
        self.assertFalse(
            should_try_attachment(
                attachment_docs=[object()],
                extracted=extracted,
                has_attachment_skip_fields_fn=lambda value: has_attachment_enrichment_fields(
                    value,
                    extract_area_number_fn=lambda area: int(area),
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
