from __future__ import annotations

import unittest

from backend.services.native_gui_rules_area_runtime import extract_notice_area_value


class NativeGuiRulesAreaRuntimeTests(unittest.TestCase):
    def test_extract_notice_area_sums_multiple_values_on_same_area_line(self) -> None:
        text = (
            "1. 공모개요\n"
            "가. 공모명 상동 U&I 부산복합/주거 플랫폼 조성사업 건축설계 제안공모\n"
            "연면적 1,967.16㎡ 2,513.91㎡\n"
            "예정 총공사비 : 금 8,407,000,000원\n"
        )

        value = extract_notice_area_value(text, "상동 U&I 부산복합/주거 플랫폼 조성사업 건축설계 제안공모")

        self.assertEqual(value, "4,481.1㎡")

    def test_extract_notice_area_ignores_cost_under_project_scale_label(self) -> None:
        text = (
            "2. 사업개요\n"
            "사업 규모\n"
            "총공사비(예정) : 33,800,000천원(부가세포함)\n"
            "용역비 예정 : 1,643,697천원\n"
        )

        value = extract_notice_area_value(text, "부산항북항 재개발사업 건축공모")

        self.assertEqual(value, "")


if __name__ == "__main__":
    unittest.main()
