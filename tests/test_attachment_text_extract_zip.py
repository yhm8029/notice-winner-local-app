from __future__ import annotations

import zipfile
from io import BytesIO
from unittest.mock import patch

from backend.services.attachment_text_extract import _infer_suffix
from backend.services.attachment_text_extract import extract_attachment_text


def test_infer_suffix_distinguishes_hwpx_zip_from_generic_zip() -> None:
    hwpx_buffer = BytesIO()
    with zipfile.ZipFile(hwpx_buffer, "w") as zf:
        zf.writestr("Preview/PrvText.txt", "preview")
        zf.writestr("Contents/section0.xml", "<root><p>section</p></root>")
    assert _infer_suffix(file_name="", content_type="", data=hwpx_buffer.getvalue()) == ".hwpx"

    generic_buffer = BytesIO()
    with zipfile.ZipFile(generic_buffer, "w") as zf:
        zf.writestr("notice.hwp", b"dummy")
    assert _infer_suffix(file_name="", content_type="", data=generic_buffer.getvalue()) == ".zip"


def test_extract_attachment_text_reads_supported_docs_inside_zip() -> None:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("folder/공고문.hwp", b"dummy-hwp")
        zf.writestr("folder/readme.txt", "plain-text-note".encode("utf-8"))

    with (
        patch(
            "backend.services.attachment_text_extract._extract_hwp_via_hwp5txt",
            return_value="담당부서 055-360-1165",
        ),
        patch(
            "backend.services.attachment_text_extract._extract_hwp_via_hwp5html",
            return_value="",
        ),
    ):
        text = extract_attachment_text(data=buffer.getvalue(), file_name="notice_bundle.zip")

    assert "공고문.hwp" in text
    assert "055-360-1165" in text
    assert "readme.txt" in text
    assert "plain-text-note" in text
