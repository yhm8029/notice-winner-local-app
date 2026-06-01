from __future__ import annotations

from unittest.mock import patch

from backend.services.attachment_text_extract import _extract_hwp_text


def test_extract_hwp_text_merges_hwp5txt_and_hwp5html_when_html_has_table_values() -> None:
    with (
        patch(
            "backend.services.attachment_text_extract._extract_hwp_via_hwp5txt",
            return_value="개요\n본문이 충분히 길어서 기존에는 여기서 종료되던 텍스트\n" * 30,
        ),
        patch(
            "backend.services.attachment_text_extract._extract_hwp_via_hwp5html",
            return_value="사업개요\n연면적\n1,967.16㎡\n2,513.91㎡",
        ),
    ):
        text = _extract_hwp_text(b"dummy")

    assert "1,967.16㎡" in text
    assert "2,513.91㎡" in text
