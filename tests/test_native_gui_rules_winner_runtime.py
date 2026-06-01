from __future__ import annotations

import unittest

from backend.services.native_gui_rules import WinnerExtraction
from backend.services.native_gui_rules import winner_name_extractor


class NativeGuiRulesWinnerRuntimeTests(unittest.TestCase):
    def test_winner_name_extractor_reads_strong_tag_winner(self) -> None:
        extracted = winner_name_extractor("<strong>\ud14c\uc2a4\ud2b8\uac74\ucd95\uc0ac\uc0ac\ubb34\uc18c</strong>", "")

        self.assertEqual(
            extracted,
            WinnerExtraction(
                winner_name="\ud14c\uc2a4\ud2b8\uac74\ucd95\uc0ac\uc0ac\ubb34\uc18c",
                confidence=0.95,
                pattern="strong_tag:snippet",
            ),
        )

    def test_winner_name_extractor_strips_trailing_notice_fields(self) -> None:
        extracted = winner_name_extractor(
            "\ub2f9\uc120\uc790 \uccad\uba85\uac74\ucd95\uc0ac\uc0ac\ubb34\uc18c \uc5f0\uba74\uc801 2,450\u33a1 \uacf5\uc0ac\ube44 123,000,000\uc6d0",
            "",
        )

        self.assertEqual(extracted.winner_name, "\uccad\uba85\uac74\ucd95\uc0ac\uc0ac\ubb34\uc18c")
        self.assertEqual(extracted.pattern, "winner_colon:snippet")


if __name__ == "__main__":
    unittest.main()
