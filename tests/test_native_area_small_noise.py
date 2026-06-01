from __future__ import annotations

import unittest

from backend.services.native_gui_rules import extract_notice_area_value


class NativeAreaSmallNoiseTests(unittest.TestCase):
    def test_extract_notice_area_prefers_school_area_label_over_tiny_noise(self) -> None:
        text = (
            "부지면적 : 15,805.2㎡\n"
            "교사면적 : 16,634㎡\n"
            "연면적 : 1㎡\n"
        )

        value = extract_notice_area_value(text, "신항고등학교 교사 신축 설계공모")

        self.assertEqual(value, "16,634㎡")


if __name__ == "__main__":
    unittest.main()
