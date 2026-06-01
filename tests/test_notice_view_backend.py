from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.services.native_export_backend import PageDocument
from backend.services.notice_view_backend import build_notice_view_payload
from backend.services.notice_view_backend import is_allowed_notice_view_url


class NoticeViewBackendTests(unittest.TestCase):
    def test_is_allowed_notice_view_url_accepts_g2b_hosts_only(self) -> None:
        self.assertTrue(
            is_allowed_notice_view_url(
                "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00554120&bidPbancOrd=000"
            )
        )
        self.assertTrue(is_allowed_notice_view_url("https://bid.g2b.go.kr/example"))
        self.assertFalse(is_allowed_notice_view_url("https://example.com/notice"))
        self.assertFalse(is_allowed_notice_view_url("file:///tmp/notice.html"))

    @patch("backend.services.notice_view_backend._build_attachment_notice_document", return_value=None)
    @patch("backend.services.notice_view_backend._fetch_page_documents")
    def test_build_notice_view_payload_dedupes_same_content_and_marks_primary(
        self,
        fetch_documents,
        _build_attachment_notice_document,
    ) -> None:
        detail_url = "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00554120&bidPbancOrd=000"
        base_url = "https://www.g2b.go.kr/link/PNPE027_01/list?bidPbancNo=R25BK00554120"
        fetch_documents.return_value = [
            PageDocument(url=detail_url, title="상세 공고", text="첫 줄\n둘째 줄" * 80),
            PageDocument(url=base_url, title="상세 공고", text="첫 줄\n둘째 줄" * 80),
        ]

        payload = build_notice_view_payload(
            notice_detail_url=detail_url,
            notice_url=base_url,
            project_name="테스트 공고",
            bid_no="R25BK00554120",
            bid_ord="000",
        )

        self.assertEqual(payload["document_count"], 1)
        self.assertEqual(payload["title"], "상세 공고")
        self.assertEqual(payload["used_url"], detail_url)
        self.assertEqual(payload["text"], "첫 줄\n둘째 줄" * 80)
        self.assertEqual(payload["requested_urls"], [detail_url, base_url])
        self.assertEqual(payload["documents"][0]["source_label"], "detail")
        self.assertTrue(payload["documents"][0]["is_primary"])

    def test_build_notice_view_payload_rejects_non_g2b_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "g2b.go.kr"):
            build_notice_view_payload(
                notice_detail_url="https://example.com/notices/1",
                notice_url="",
                project_name="테스트 공고",
                bid_no="R25BK00000001",
                bid_ord="000",
            )

    @patch(
        "backend.services.notice_view_backend._build_attachment_notice_document",
        return_value={
            "source_label": "attachment",
            "url": "https://www.g2b.go.kr/download/spec.hwp",
            "title": "공고문.hwp",
            "text": "첨부 공고문 전체 본문",
            "is_primary": False,
        },
    )
    @patch("backend.services.notice_view_backend._fetch_page_documents")
    def test_build_notice_view_payload_adds_attachment_when_page_text_is_too_short(
        self,
        fetch_documents,
        _build_attachment_notice_document,
    ) -> None:
        detail_url = "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R25BK00554120&bidPbancOrd=000"
        fetch_documents.return_value = [
            PageDocument(url=detail_url, title="나라장터", text="나라장터"),
        ]

        payload = build_notice_view_payload(
            notice_detail_url=detail_url,
            notice_url="",
            project_name="테스트 공고",
            bid_no="R25BK00554120",
            bid_ord="000",
        )

        self.assertEqual(payload["document_count"], 2)
        self.assertEqual(payload["title"], "테스트 공고")
        self.assertEqual(payload["text"], "첨부 공고문 전체 본문")
        self.assertEqual(payload["documents"][1]["source_label"], "attachment")
        self.assertTrue(payload["documents"][1]["is_primary"])

    @patch(
        "backend.services.notice_view_backend._build_attachment_notice_document",
        return_value={
            "source_label": "attachment",
            "url": "https://www.g2b.go.kr/download/original_notice.hwp",
            "title": "원공고.hwp",
            "text": "원공고 첨부 본문",
            "is_primary": False,
        },
    )
    @patch("backend.services.notice_view_backend._fetch_page_documents")
    def test_build_notice_view_payload_allows_bid_only_attachment_fallback(
        self,
        fetch_documents,
        _build_attachment_notice_document,
    ) -> None:
        fetch_documents.return_value = []

        payload = build_notice_view_payload(
            notice_detail_url="",
            notice_url="",
            project_name="테스트 원공고",
            bid_no="R26BK01360454",
            bid_ord="000",
        )

        self.assertEqual(payload["document_count"], 1)
        self.assertEqual(payload["title"], "테스트 원공고")
        self.assertEqual(payload["text"], "원공고 첨부 본문")
        self.assertEqual(payload["documents"][0]["source_label"], "attachment")
        self.assertTrue(payload["documents"][0]["is_primary"])


if __name__ == "__main__":
    unittest.main()
