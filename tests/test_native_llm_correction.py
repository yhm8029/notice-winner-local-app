from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.native_export_backend import run_post_collect_native
from backend.services.native_llm_correction import LlmCorrectionConfig
from backend.services.native_llm_correction import LlmCorrectionResult
from backend.services.native_llm_correction import _needs_contact_llm
from backend.services.native_llm_correction import load_llm_correction_config_from_options
from backend.services.native_llm_correction import maybe_correct_notice_fields_with_llm


class _FakeAnthropicResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        '{"area":"2,450\\u33a1","cost":"547,520,000\\uc6d0",'
                        '"contact":"\\uc2dc\\uc124\\uc9c0\\uc6d0\\ub2f4\\ub2f9/055-960-2791"}'
                    ),
                }
            ]
        }


class _SequencedAnthropicResponse:
    def __init__(self, *, status_code: int, payload: dict[str, object]) -> None:
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict[str, object]:
        return self._payload


class NativeLlmCorrectionTests(unittest.TestCase):
    def test_load_llm_correction_config_from_options_prefers_explicit_options(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "TRACKER_LLM_CORRECT": "0",
                "ANTHROPIC_API_KEY": "",
                "TRACKER_LLM_MODEL": "",
                "TRACKER_LLM_MAX_ROWS": "20",
            },
            clear=False,
        ):
            config = load_llm_correction_config_from_options(
                {
                    "llm_correct": True,
                    "anthropic_key": "abc",
                    "llm_model": "claude-3-5-haiku-latest",
                    "llm_max_rows": 7,
                }
            )

        self.assertTrue(config.enabled)
        self.assertEqual(config.api_key, "abc")
        self.assertEqual(config.model, "claude-3-5-haiku-latest")
        self.assertEqual(config.max_rows, 7)

    def test_maybe_correct_notice_fields_with_llm_accepts_valid_values(self) -> None:
        result = maybe_correct_notice_fields_with_llm(
            config=LlmCorrectionConfig(
                enabled=True,
                api_key="test-key",
                model="claude-3-5-haiku-latest",
                max_rows=20,
                max_chars=4000,
            ),
            text=(
                "\ubb38\uc758: \uc2dc\uc124\uc9c0\uc6d0\ub2f4\ub2f9 055-960-2791 "
                "\ucd1d\uc5f0\uba74\uc801 2450\u33a1 \ucd1d\uacf5\uc0ac\ube44 547,520,000\uc6d0"
            ),
            project_name="\ud568\uc591 \ub3c4\uc11c\uad00 \uc774\uc804 \uc2e0\ucd95 \uc124\uacc4\uacf5\ubaa8",
            org_name="\uacbd\uc0c1\ub0a8\ub3c4\uad50\uc721\uccad",
            area="",
            cost="",
            contact="",
            request_fn=lambda *args, **kwargs: _FakeAnthropicResponse(),
        )

        self.assertEqual(result.area, "2,450㎡")
        self.assertEqual(result.cost, "547,520,000원")
        self.assertEqual(result.contact, "시설지원담당/055-960-2791")
        self.assertEqual(result.corrected_fields, ("area", "contact", "cost"))

    def test_needs_contact_llm_flags_generic_contact_labels(self) -> None:
        self.assertTrue(_needs_contact_llm(contact="\uacf5\ubaa8 \ub2f4\ub2f9/055-749-6174"))
        self.assertTrue(_needs_contact_llm(contact="\ubb38\uc758\ucc98/055-749-6174"))
        self.assertFalse(_needs_contact_llm(contact="\uad00\uad11\uacfc/052-226-3044"))

    def test_maybe_correct_notice_fields_with_llm_retries_legacy_model_alias(self) -> None:
        calls: list[str] = []

        def _request(*args, **kwargs):
            model = str(kwargs.get("json", {}).get("model") or "")
            calls.append(model)
            if len(calls) == 1:
                return _SequencedAnthropicResponse(
                    status_code=404,
                    payload={"error": {"type": "not_found_error", "message": "model not found"}},
                )
            return _SequencedAnthropicResponse(
                status_code=200,
                payload={
                    "content": [
                        {
                            "type": "text",
                            "text": '{"contact":"\\uc804\\ub7b5\\uc0ac\\uc5c5\\uacfc/055-123-4567"}',
                        }
                    ]
                },
            )

        result = maybe_correct_notice_fields_with_llm(
            config=LlmCorrectionConfig(
                enabled=True,
                api_key="test-key",
                model="claude-3-5-haiku-latest",
                max_rows=20,
                max_chars=4000,
            ),
            text="\ubb38\uc758\ucc98 055-123-4567",
            project_name="\uc804\ub7b5\uc0ac\uc5c5 \uac74\ub9bd \uc124\uacc4\uacf5\ubaa8",
            org_name="\uac00\uc0c1 \uae30\uad00",
            area="1,250㎡",
            cost="500,000,000원",
            contact="\ubb38\uc758\ucc98/055-123-4567",
            request_fn=_request,
        )

        self.assertEqual(calls, ["claude-3-5-haiku-latest", "claude-haiku-4-5-20251001"])
        self.assertEqual(result.contact, "전략사업과/055-123-4567")
        self.assertEqual(result.corrected_fields, ("contact",))

    def test_run_post_collect_native_applies_llm_correction(self) -> None:
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
                        "internal_search_url",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00554120",
                        "bid_ord": "000",
                        "project_name_norm": "\ud568\uc591 \ub3c4\uc11c\uad00 \uc774\uc804 \uc2e0\ucd95 \uc124\uacc4\uacf5\ubaa8",
                        "org_name": "\uacbd\uc0c1\ub0a8\ub3c4\uad50\uc721\uccad",
                        "internal_search_url": "https://example.com/post",
                        "status": "SEARCH_URL_BUILT",
                    }
                )

            with patch(
                "backend.services.native_export_backend.requests.get",
                return_value=type(
                    "Resp",
                    (),
                    {
                        "text": "<html><title>test</title><body>body</body></html>",
                        "raise_for_status": staticmethod(lambda: None),
                    },
                )(),
            ), patch(
                "backend.services.native_export_backend.load_llm_correction_config_from_options",
                return_value=LlmCorrectionConfig(
                    enabled=True,
                    api_key="test-key",
                    model="claude-haiku-4-5-20251001",
                    max_rows=20,
                    max_chars=4000,
                ),
            ), patch(
                "backend.services.native_export_backend.maybe_correct_notice_fields_with_llm",
                return_value=LlmCorrectionResult(
                    area="2,450㎡",
                    cost="547,520,000원",
                    contact="시설지원담당/055-960-2791",
                    corrected_fields=("area", "contact", "cost"),
                ),
            ):
                run_post_collect_native(input_csv, output_csv)

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["gross_area_scale"], "2,450㎡")
        self.assertEqual(rows[0]["notice_construction_cost"], "547,520,000원")
        self.assertEqual(rows[0]["demand_contact"], "")
        self.assertIn("llm_corrected=area,cost", rows[0]["hub_check_note"])
