from __future__ import annotations

import unittest

from backend.services.native_gui_rules import _looks_like_attachment_filename_line
from backend.services.native_gui_rules import extract_contact_from_notice_text


class NativeContactFilenameLineTests(unittest.TestCase):
    def test_looks_like_attachment_filename_line_detects_attachment_names(self) -> None:
        self.assertTrue(_looks_like_attachment_filename_line("20240223277-00_1708306587270_notice_file.hwp"))
        self.assertTrue(_looks_like_attachment_filename_line("20240119558-00_1705580373537_notice_file.pdf"))
        self.assertTrue(_looks_like_attachment_filename_line("20240128767-00_1706177388504_notice_file.hwpx"))

    def test_looks_like_attachment_filename_line_does_not_mask_real_contact_line(self) -> None:
        self.assertFalse(
            _looks_like_attachment_filename_line(
                "\ubb38\uc758\ucc98 : \ub0a8\uc6b8\uc8fc\uc18c\ubc29\uc11c \uc18c\ubc29\ud589\uc815\uacfc \uc608\uc0b0\uc7a5\ube44\ud300 \uc1a1\uc6d0\uc7ac(052-241-6631)"
            )
        )

    def test_extract_contact_from_notice_text_ignores_attachment_filename_lines(self) -> None:
        text = "\n".join(
            [
                "20240223277-00_1708306587270_\uc124\uacc4\uacf5\ubaa8_\uacf5\uace0\ubb38(\uccad\ub7c9119\uc548\uc804\uc13c\ud130_\uc2e0\ucd95).hwp",
                "20240223277-00_1708306587276_\uc124\uacc4\uc6a9\uc5ed_\uacfc\uc5c5\uc9c0\uc2dc\uc11c(\uccad\ub7c9119\uc548\uc804\uc13c\ud130_\uc2e0\ucd95).hwp",
                "10. \ubb38\uc758\ucc98 : \ub0a8\uc6b8\uc8fc\uc18c\ubc29\uc11c \uc18c\ubc29\ud589\uc815\uacfc \uc608\uc0b0\uc7a5\ube44\ud300 \uc1a1\uc6d0\uc7ac(052-241-6631)",
            ]
        )

        self.assertEqual(
            extract_contact_from_notice_text(text, "\uc6b8\uc0b0\uad11\uc5ed\uc2dc \ub0a8\uc6b8\uc8fc\uc18c\ubc29\uc11c"),
            "\uc18c\ubc29\ud589\uc815\uacfc \uc608\uc0b0\uc7a5\ube44\ud300/052-241-6631",
        )


if __name__ == "__main__":
    unittest.main()
