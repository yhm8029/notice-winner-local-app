from __future__ import annotations

import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

from backend.services.attachment_text_extract import _is_good_enough_hwp_text
from backend.services.attachment_text_extract import extract_attachment_text


SAMPLE_HWP_PATH = Path(__file__).resolve().parents[1] / "output" / "_tmp_attach_probe" / "sample_hwp.hwp"
MANUAL_PROBE_DIR = Path(__file__).resolve().parents[1] / "output" / "debug" / "manual_4298_6626"


class AttachmentTextExtractTests(unittest.TestCase):
    def test_extract_attachment_text_reads_hwpx_preview(self) -> None:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("Preview/PrvText.txt", "당선자: 테스트건축사사무소\n연면적: 1,234㎡\n예정공사비: 9,999원")
            zf.writestr("Contents/section0.xml", "<root><p>현장위치 서울시 중구</p></root>")
        text = extract_attachment_text(data=buffer.getvalue(), file_name="sample.hwpx")
        self.assertIn("당선자: 테스트건축사사무소", text)
        self.assertIn("연면적: 1,234㎡", text)
        self.assertIn("현장위치 서울시 중구", text)

    def test_extract_attachment_text_reads_hwp_preview_stream(self) -> None:
        if not SAMPLE_HWP_PATH.exists():
            self.skipTest("sample HWP probe file not found")
        data = SAMPLE_HWP_PATH.read_bytes()
        text = extract_attachment_text(data=data, file_name="sample.hwp")
        self.assertIn("경상남도교육청 함양도서관 이전 신축 설계공모", text)
        self.assertIn("예정공사비", text)

    def test_is_good_enough_hwp_text_uses_category_hits(self) -> None:
        weak_text = "참조 문서\n페이지 1\n예시 내용"
        self.assertFalse(_is_good_enough_hwp_text(weak_text))

        category_text = "\n".join(
            [
                "당선자 청명건축",
                "연면적 2,450㎡",
                "공사비 123,000,000원",
            ]
        )
        self.assertTrue(_is_good_enough_hwp_text(category_text * 20))

    def test_extract_attachment_text_reads_hwp_bodytext_beyond_preview(self) -> None:
        hwp_path = MANUAL_PROBE_DIR / "R25BK00806626_000_seq3.hwp"
        if not hwp_path.exists():
            self.skipTest("manual HWP probe file not found")

        text = extract_attachment_text(data=hwp_path.read_bytes(), file_name=hwp_path.name)

        self.assertIn("\ucd94\uc815\uc5f0\uba74\uc801", text)
        self.assertIn("8,682.66", text)
        self.assertIn("\uc608\uc815\uacf5\uc0ac\ube44", text)
        self.assertIn("19,841,392", text)

    def test_extract_attachment_text_reads_hwp_members_inside_zip(self) -> None:
        zip_path = MANUAL_PROBE_DIR / "R25BK00794298_001_seq1.zip"
        if not zip_path.exists():
            self.skipTest("manual ZIP probe file not found")

        text = extract_attachment_text(data=zip_path.read_bytes(), file_name=zip_path.name)

        self.assertIn("\uac74\ucd95\uc5f0\uba74\uc801", text)
        self.assertIn("12,500", text)
        self.assertIn("\uac74\ucd95\uacf5\uc0ac\ube44", text)
        self.assertIn("301.18", text)
