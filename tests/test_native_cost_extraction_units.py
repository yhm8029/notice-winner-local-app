from __future__ import annotations

import unittest

from backend.services.native_export_backend import _extract_notice_fields
from backend.services.native_gui_rules import extract_cost_won
from backend.services.native_gui_rules import extract_labeled_cost_text
from backend.services.native_gui_rules import extract_notice_cost_won


class NativeCostExtractionUnitTests(unittest.TestCase):
    def test_extract_notice_cost_won_keeps_total_budget_when_only_budget_exists(self) -> None:
        text = "\n".join(
            [
                "총 사업비 6,890백만 원",
                "설계용역비 261백만 원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 6_890_000_000)

    def test_extract_cost_won_supports_cheonwon_units(self) -> None:
        self.assertEqual(extract_cost_won("52,485,954천원"), 52_485_954_000)

    def test_extract_notice_cost_won_supports_cheonwon_units(self) -> None:
        text = "\n".join(
            [
                "예정공사비: 52,485,954천원(부가가치세 포함)",
                "설계용역비: 1,594,521천원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 52_485_954_000)

    def test_extract_notice_cost_won_prefers_construction_cost_over_total_budget(self) -> None:
        text = "\n".join(
            [
                "총 사업비 6,890백만 원",
                "예정공사비 5,901백만 원",
                "설계용역비 261백만 원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 5_901_000_000)

    def test_extract_labeled_cost_text_supports_spaced_units(self) -> None:
        text = "빌딩자동제어 추정 금액: 261백만 원"
        self.assertEqual(extract_labeled_cost_text(text, ("빌딩자동제어 추정 금액",)), "261,000,000원")

    def test_extract_notice_cost_won_prefers_repeated_amount_over_single_outlier(self) -> None:
        text = "\n".join(
            [
                "예정 공사비 : 3,004,140천원",
                "예정공사비(VAT포함) : 3,004,140천원",
                "예정공사비(VAT포함) : 3,004,140,000천원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 3_004_140_000)

    def test_extract_notice_cost_won_keeps_same_amount_when_budget_and_construction_match(self) -> None:
        text = "\n".join(
            [
                "총사업비 50억원",
                "예정공사비 50억원",
                "설계용역비 2억원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 5_000_000_000)

    def test_extract_notice_cost_won_prefers_construction_cost_over_budget_variant(self) -> None:
        text = "\n".join(
            [
                "예정사업비 121억원",
                "예정공사비 117억원",
                "설계용역비 6억원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 11_700_000_000)


    def test_extract_notice_cost_won_prefers_total_expected_construction_cost_when_labeled(self) -> None:
        text = "\n".join(
            [
                "예정공사비 8,092,000,000원",
                "예정공사비 10,315,000,000원",
                "총 예상공사비 : 금18,407,000,000원",
                "예정 용역금액 : 금867,900,000원",
            ]
        )
        self.assertEqual(extract_notice_cost_won(text), 18_407_000_000)


    def test_extract_notice_cost_won_supports_spaced_eok_won_label(self) -> None:
        text = "\n".join(
            [
                "\ucd94\uc815\uacf5\uc0ac\ube44: 49.8 \uc5b5 \uc6d0",
                "\uc124\uacc4\ube44: \uc11c\uc6b8\ub300\ud559\uad50 \uc608\uc0b0 \ubc94\uc704 \ub0b4 \uc785\ucc30 \uae08\uc561",
            ]
        )

        self.assertEqual(extract_notice_cost_won(text), 4_980_000_000)


class NativeExportCostExtractionTests(unittest.TestCase):
    def test_extract_notice_fields_handles_spaced_million_units(self) -> None:
        text = "\n".join(
            [
                "영남알프스를 찾는 등산객 및 라이딩 관광객을 위한 편익시설 건립을 위한",
                "총 사업비 6,890백만 원",
                "예정공사비 5,901백만 원",
                "설계용역비 261백만 원",
            ]
        )

        fields = _extract_notice_fields(
            title="이천분교 베이스캠프 건립 건축 설계공모 공고",
            text=text,
            project_name="이천분교 베이스캠프 건립",
            org_name="울산광역시 울주군",
        )

        self.assertEqual(fields.construction_cost, "5,901,000,000원")

    def test_extract_notice_fields_handles_cheonwon_units(self) -> None:
        text = "\n".join(
            [
                "건 명: 가칭 제3공립 특수학교 설립공사 건축설계공모",
                "예정공사비: 52,485,954천원(부가가치세 포함)",
                "설계용역비: 1,594,521천원",
            ]
        )

        fields = _extract_notice_fields(
            title="가칭 제3공립 특수학교 설립공사 건축설계공모",
            text=text,
            project_name="가칭 제3공립 특수학교 설립공사 건축설계공모",
            org_name="울산광역시교육청",
        )

        self.assertEqual(fields.construction_cost, "52,485,954,000원")

    def test_extract_notice_fields_ignores_single_cheonwon_outlier_when_consensus_exists(self) -> None:
        text = "\n".join(
            [
                "예정 공사비 : 3,004,140천원(부가세 포함)",
                "예정공사비(VAT포함) : 3,004,140천원",
                "예정공사비(VAT포함) : 3,004,140,000천원",
            ]
        )

        fields = _extract_notice_fields(
            title="이반성면 종합복지회관 건립사업 설계공모 공고",
            text=text,
            project_name="이반성면 종합복지회관 건립사업 설계공모 공고",
            org_name="경상남도 진주시",
        )

        self.assertEqual(fields.construction_cost, "3,004,140,000원")

    def test_extract_notice_fields_keeps_total_budget_when_no_construction_cost_exists(self) -> None:
        text = "\n".join(
            [
                "총 사업비 6,890백만 원",
                "설계용역비 261백만 원",
            ]
        )

        fields = _extract_notice_fields(
            title="테스트 공고",
            text=text,
            project_name="테스트 공고",
            org_name="테스트 기관",
        )

        self.assertEqual(fields.construction_cost, "6,890,000,000원")
