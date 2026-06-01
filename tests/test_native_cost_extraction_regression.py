from __future__ import annotations

import unittest

from backend.services.native_export_backend import _extract_notice_fields
from backend.services.native_gui_rules import extract_notice_cost_won


class NativeCostExtractionRegressionTests(unittest.TestCase):
    def test_extract_notice_cost_won_prefers_labeled_construction_cost_over_generic_one_eok(self) -> None:
        text = "\n".join(
            [
                "이천분교 베이스캠프 건립",
                "총 사업비 6,890백만 원",
                "예정공사비 5,901백만 원",
                "설계용역비 261백만 원",
                "하자보수보증금 100,000,000원",
            ]
        )

        self.assertEqual(extract_notice_cost_won(text), 5_901_000_000)

    def test_extract_notice_fields_ignores_generic_one_eok_when_labeled_cost_exists(self) -> None:
        text = "\n".join(
            [
                "이천분교 베이스캠프 건립 건축 설계공모 공고",
                "총 사업비 6,890백만 원",
                "예정공사비 5,901백만 원",
                "설계용역비 261백만 원",
                "하자보수보증금 100,000,000원",
            ]
        )

        fields = _extract_notice_fields(
            title="이천분교 베이스캠프 건립 건축 설계공모 공고",
            text=text,
            project_name="이천분교 베이스캠프 건립",
            org_name="울산광역시 울주군",
        )

        self.assertEqual(fields.construction_cost, "5,901,000,000원")
