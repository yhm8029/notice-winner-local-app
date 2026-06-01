from __future__ import annotations

import unittest

from backend.services.native_gui_rules import extract_notice_area_value


class NativeAreaPatternRegressionTests(unittest.TestCase):
    def test_extract_notice_area_sums_multiple_values_on_same_area_line(self) -> None:
        text = (
            "1. 공모개요\n"
            "가. 공모명: 영덕 U&I 수산복합/주거 플랫폼 조성사업 건축설계 제안공모\n"
            "다. 사업개요\n"
            "연면적 1,967.16㎡ 2,513.91㎡\n"
            "라. 예정 총공사비 : 금18,407,000,000원\n"
        )

        value = extract_notice_area_value(text, "영덕 U&I 수산복합/주거 플랫폼 조성사업 건축설계 제안공모")

        self.assertEqual(value, "4,481.1㎡")


if __name__ == "__main__":
    unittest.main()
