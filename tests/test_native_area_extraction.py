from __future__ import annotations

import unittest

from backend.services.native_gui_rules import extract_notice_area_value


class NativeAreaExtractionTests(unittest.TestCase):
    def test_extract_notice_area_ignores_numbered_section_marker_before_real_area(self) -> None:
        text = (
            "마. 사업규모 및 내용\n"
            "1) 대지면적 : 15,805.2㎡\n"
            "2) 교사면적 : 16,634㎡(±5% 이내, 필로티주차장 2,450㎡ 포함)\n"
        )

        value = extract_notice_area_value(text, "신항고등학교 교사 신축 설계공모")

        self.assertEqual(value, "16,634㎡")

    def test_extract_notice_area_prefers_project_area_over_generic_scale_bullets(self) -> None:
        text = (
            "Summary Notice\n"
            "- Area : Approximately 1,316,071㎡\n"
            "2) 토지 및 시설물 등 규모의 확장 가능성을 감안한 미래지향적인 공간체계가 될 수 있는 설계를 하여야 한다.\n"
            "3) 주변 토지이용과 현지여건을 고려하여 유료, 무료구역을 구분하여 공간계획을 수립하여야 한다.\n"
            "사업면적 : 1,316,071㎡\n"
            "- 보문산수목원 조성 : A=약1,316,071㎡(형질변경 면적은 200,000㎡ 미만으로 한다.)\n"
        )

        value = extract_notice_area_value(text, "보문산수목원 조성사업 설계공모")

        self.assertEqual(value, "1,316,071㎡")

    def test_extract_notice_area_ignores_percentage_only_area_phrase(self) -> None:
        text = "1) 건축 연면적은 제시한 면적에서 ±5% 이내로 계획"

        value = extract_notice_area_value(text, "금산인삼약초특화농공단지 복합문화센터 건축설계공모")

        self.assertEqual(value, "")

    def test_extract_notice_area_ignores_site_area_when_only_building_scale_is_present(self) -> None:
        text = (
            "나. 대지면적 : 1,913.90㎡\n"
            "다. 건축규모 : 법정 규모 - 4층\n"
        )

        value = extract_notice_area_value(text, "금산인삼약초특화농공단지 복합문화센터 건축설계공모")

        self.assertEqual(value, "")

    def test_extract_notice_area_ignores_cost_under_project_scale_label(self) -> None:
        text = (
            "2. 사업개요\n"
            "나. 사업 규모\n"
            "표\n"
            "다. 총공사비(예정) : 33,800,000천원(부가세포함)\n"
            "라. 설 계 비(예정) : 1,643,697천원\n"
        )

        value = extract_notice_area_value(text, "디지털항암센터 건립사업 설계공모")

        self.assertEqual(value, "")


    def test_extract_notice_area_converts_pyeong_subtotal_table_to_square_meters(self) -> None:
        text = (
            "\uc0ac\uc5c5\ub0b4\uc6a9\n"
            "\uac74\ubb3c\uba85/\uc704\uce58 \uba74 \uc801(\ud3c9) \uc124\uacc4\ub0b4\uc6a9\n"
            "\ub300\ud559\ubcf8\ubd80 1~3\uce35 1\uce35 184.7 2\uce35 137.3 3\uce35 185.1 \uacc4 507.1\n"
            "C.L.C 2~3\uce35 2\uce35 55.0 3\uce35 55.3 \uacc4 110.3\n"
            "\ud569\uacc4 617.4\n"
        )

        value = extract_notice_area_value(
            text,
            "\ud55c\ub9bc\ub300\ud559\uad50 \ub300\ud559\ubcf8\ubd80 \ub85c\ube44 \ud658\uacbd\uac1c\uc120 \uc124\uacc4\uacf5\ubaa8",
        )

        self.assertEqual(value, "2,041.0\u33a1")

    def test_extract_notice_area_prefers_gross_area_inside_project_scale_over_site_area(self) -> None:
        text = (
            "\uc0ac\uc5c5\uac1c\uc694\n"
            "\ucd5c\uadfc 5\ub144 \uc774\ub0b4 \uc5f0\uba74\uc801 6,000\u33a1 \uc774\uc0c1\uc758 \uc124\uacc4\uc6a9\uc5ed \uc2e4\uc801\uc774 \uc788\ub294 \uc790\n"
            "\uac74\ub9bd\uc704\uce58: \uc591\uc0b0\ubd80\uc0b0\ub300\ud559\uad50\ubcd1\uc6d0 \ubd80\uc9c0\n"
            "\ubd80\uc9c0\uba74\uc801: 236,514\u33a1 \uc911 \uc57d 7,200\u33a1(\uc8fc\ucc28\uc7a5\ubd80\uc9c0 \ubcc4\ub3c4)\n"
            "\uac74\ub9bd\uaddc\ubaa8: \uc5f0\uba74\uc801 12,500.00\u33a1(\u00b15% \ubc94\uc704 \ub0b4 \uc870\uc815\uac00\ub2a5)\n"
            "\uac74\ucd95\uacf5\uc0ac\ube44: \uae08301.18\uc5b5\uc6d0\n"
        )

        value = extract_notice_area_value(text, "\uc591\uc0b0\ubd80\uc0b0\ub300\ud559\uad50\ubcd1\uc6d0 \uc784\uc0c1\uad50\uc721\ud6c8\ub828\uc13c\ud130 \uac74\ub9bd \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "12,500\u33a1")

    def test_extract_notice_area_accepts_estimated_gross_area_label(self) -> None:
        text = (
            "\uc124\uacc4\uac1c\uc694\n"
            "\ub300\uc9c0\uc704\uce58: \uacbd\uc0c1\ubd81\ub3c4 \uad6c\ubbf8\uc2dc \uc625\uacc4\ub3d9 923\ubc88\uc9c0\n"
            "\ubd80\uc9c0\uba74\uc801: 19,896.60\u33a1\n"
            "\ucd94\uc815\uc5f0\uba74\uc801: 8,682.66\u33a1[\u00b13% \ub0b4\uc678]\n"
            "\uc608\uc815\uacf5\uc0ac\ube44: 19,841,392\ucc9c\uc6d0\n"
        )

        value = extract_notice_area_value(text, "\uac00\uce6d)\ud574\ub9c8\ub8e8\uace0\ub4f1\ud559\uad50 \uc2e0\ucd95\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "8,682.7\u33a1")

    def test_extract_notice_area_does_not_sum_site_area_and_estimated_gross_area_table(self) -> None:
        text = (
            "\uc0ac\uc5c5\uaddc\ubaa8 \ubc0f \ub0b4\uc6a9\n"
            "\uad6c \ubd84\n"
            "\ub300\uc9c0\uba74\uc801(\u33a1)\n"
            "\ucd94\uc815\uc5f0\uba74\uc801(\u33a1)\n"
            "\ud559\uae09\uc218\n"
            "\uace0\ub4f1\ud559\uad50\n"
            "19,896.60\u33a1\n"
            "8,682.66\u33a1\n"
            "\uac74\ucd95\uc5f0\uba74\uc801: \u00b13%\uc774\ub0b4 \uc870\uc815\uac00\ub2a5\n"
            "\ucd1d\uacf5\uc0ac\ube44: \uae0819,841,392\ucc9c\uc6d0\n"
        )

        value = extract_notice_area_value(text, "\uac00\uce6d)\ud574\ub9c8\ub8e8\uace0\ub4f1\ud559\uad50 \uc2e0\ucd95\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "8,682.7\u33a1")

    def test_extract_notice_area_prefers_metric_value_inside_sf_parentheses(self) -> None:
        text = (
            "\u25e6\ubd80\uc9c0\uba74\uc801\n"
            "53,282SF(4,950\u33a1)\n"
            "\u25e6\uc5f0\uba74\uc801\n"
            "74,124SF(6,889\u33a1)\n"
            "\u25e6 \ucd94\uc815\uacf5\uc0ac\ube44\n"
            "46,772,000\ubbf8\ubd88\n"
        )

        value = extract_notice_area_value(text, "\uc8fc\ub85c\uc2a4\uc564\uc824\ub808\uc2a4\ucd1d\uc601\uc0ac\uad00 \uccad\uc0ac \uc2e0\ucd95 \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "6,889\u33a1")

    def test_extract_notice_area_accepts_floor_use_table_total_area(self) -> None:
        text = (
            "\uce35\ubcc4\uc6a9\ub3c4\n"
            "(\uacc4\ud68d\uc548)\n"
            "\u203b \ucc38\uace0\uc6a9\n"
            "\uad6c  \ubd84\n"
            "\uba74\uc801(\u33a1)\n"
            "\uc9c0\ud5582\uce35\n"
            "~\n"
            "\uc9c0\uc0c13\uce35\n"
            "6,100\n"
        )

        value = extract_notice_area_value(text, "\uc5ec\uc218\ub3d9 \ubcf4\ud6c8\ud68c\uad00 \uac74\ub9bd\uacf5\uc0ac \uac74\ucd95 \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "6,100\u33a1")

    def test_extract_notice_area_prefers_after_project_subtotal_in_existing_after_delta_table(self) -> None:
        text = (
            "\uc5f0 \uba74 \uc801\n"
            "\uad6c \ubd84 \uae30\uc874(\uc0ac\uc5c5 \uc804) \uc99d\uac1c\ucd95(\uc0ac\uc5c5 \ud6c4) \uc99d \uac10 \ube44 \uace0\n"
            "5\ub3d9\n"
            "5,181\u33a1\n"
            "\uc9c0\uc0c14\uce35\n"
            "6,471\u33a1\n"
            "\uc9c0\uc0c15\uce35\n"
            "1,290\u33a1\n"
            "\uc9c0\uc0c11\uce35\n"
            "6\ub3d9\n"
            "3,107\u33a1\n"
            "\uc9c0\uc0c14\uce35\n"
            "3,852\u33a1\n"
            "\uc9c0\uc0c15\uce35\n"
            "745\u33a1\n"
            "\uc9c0\uc0c11\uce35\n"
            "7\ub3d9\n"
            "4,765\u33a1\n"
            "\uc9c0\uc0c14\uce35\n"
            "5,955\u33a1\n"
            "\uc9c0\uc0c15\uce35\n"
            "1,190\u33a1\n"
            "\uc9c0\uc0c11\uce35\n"
            "\uc18c\uacc4 13,053\u33a1 (\uc9c0\uc0c14\uce35) 16,278\u33a1 (\uc9c0\uc0c15\uce35) 3,225\u33a1 (1\uac1c\uce35)\n"
        )

        value = extract_notice_area_value(text, "\uc11c\uc6b8\ub300\ud559\uad50 \uc778\ubb38\ub300 5,6,7\ub3d9 \uc99d\ucd95\uc0ac\uc5c5 \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "16,278\u33a1")

    def test_extract_notice_area_prefers_after_project_subtotal_when_values_are_on_following_lines(self) -> None:
        text = (
            "\uc5f0 \uba74 \uc801\n"
            "\uad6c \ubd84\n"
            "\uae30\uc874(\uc0ac\uc5c5 \uc804)\n"
            "\uc99d\uac1c\ucd95(\uc0ac\uc5c5 \ud6c4)\n"
            "\uc99d \uac10\n"
            "\uc18c\uacc4\n"
            "13,053\u33a1\n"
            "(\uc9c0\uc0c14\uce35)\n"
            "16,278\u33a1\n"
            "(\uc9c0\uc0c15\uce35)\n"
            "3,225\u33a1\n"
            "(1\uac1c\uce35)\n"
        )

        value = extract_notice_area_value(text, "\uc11c\uc6b8\ub300\ud559\uad50 \uc778\ubb38\ub300 5,6,7\ub3d9 \uc99d\ucd95\uc0ac\uc5c5 \uc124\uacc4\uacf5\ubaa8")

        self.assertEqual(value, "16,278\u33a1")


if __name__ == "__main__":
    unittest.main()
