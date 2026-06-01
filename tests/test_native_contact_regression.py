from __future__ import annotations

import unittest

from backend.services.native_export_backend import _select_best_attachment_contact
from backend.services.native_gui_rules import extract_contact_from_notice_text


class NativeContactRegressionTests(unittest.TestCase):
    def test_extract_contact_from_notice_text_supports_parenthesized_office_phone(self) -> None:
        text = "\n".join(
            [
                "라. 문의처",
                "○ 주소 : 대구광역시 북구 옥산로 65(침산동) 북구청 건축주택과",
                "○ 전화 : 053)665-2975",
            ]
        )

        self.assertEqual(
            extract_contact_from_notice_text(text, "대구광역시 북구"),
            "건축주택과/053-665-2975",
        )

    def test_select_best_attachment_contact_prefers_announcement_contact_over_guideline_contact(self) -> None:
        self.assertEqual(
            _select_best_attachment_contact(
                current_contact="",
                announcement_contact="건축주택과/053-665-2975",
                piece_contact="공원녹지과/053-665-4304",
                is_announcement_doc=False,
            ),
            "건축주택과/053-665-2975",
        )


if __name__ == "__main__":
    unittest.main()
