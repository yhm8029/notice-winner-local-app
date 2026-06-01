from __future__ import annotations

import unittest

import backend.services.native_gui_rules_impl as impl
from backend.services.native_gui_rules import extract_completion_expected_date
from backend.services.native_gui_rules import extract_construction_start_date
from backend.services.native_gui_rules import extract_duration_days_from_text
from backend.services.native_gui_rules import extract_notice_area_value
from backend.services.native_gui_rules import extract_notice_cost_won
from backend.services.native_gui_rules import extract_site_location
from backend.services.native_gui_rules import infer_city_from_org_or_project


class NativeGuiRulesTests(unittest.TestCase):
    def test_public_import_surface_still_exposes_gui_rule_symbols(self) -> None:
        self.assertTrue(hasattr(impl, "normalize_contact_candidate"))
        self.assertTrue(hasattr(impl, "get_manual_field_overrides"))
        self.assertTrue(hasattr(impl, "PHONE_FLEX_PAT"))

    def test_extract_notice_area_value_accepts_subtotal_after_yeonmyeon_header(self) -> None:
        text = """
        기존건축물규모 : 건축면적 1,966.08㎡, 연면적 6,569.89㎡
        구분 구조 건축년도 경과년수 연면적(㎡)
        본관동 철근콘크리트 1971 54 5,616.25
        특별교실동 철근콘크리트 2003 22 953.64
        계 6,569.89
        """
        self.assertEqual(
            extract_notice_area_value(text, "해운대여자중학교 공간재구조화 리모델링 건축설계 공모"),
            "6,569.9㎡",
        )

    def test_extract_notice_cost_won_accepts_spaced_strong_label(self) -> None:
        text = "예정 공사비 : 9,354,723,000원 (부가가치세 포함)"
        self.assertEqual(extract_notice_cost_won(text), 9354723000)

    def test_extract_duration_days_from_text_supports_contract_based_months(self) -> None:
        text = "예정 공사기간 : 계약일로부터 4개월"
        self.assertEqual(extract_duration_days_from_text(text), 120)

    def test_extract_duration_days_from_text_supports_task_order_period_with_holiday_phrase(self) -> None:
        text = """
3. 설계기간
가. 본 과업은 착수일로부터 공.휴일을 포함하여 210일로 한다.
"""
        self.assertEqual(extract_duration_days_from_text(text), 210)

    def test_extract_duration_days_from_text_supports_service_design_period_tilde_days(self) -> None:
        text = "9) 용역설계기간 : 착수일 ~ 210일(BF예비인증 기간 포함)"
        self.assertEqual(extract_duration_days_from_text(text), 210)

    def test_extract_construction_start_date_supports_contract_execution_period_end_date(self) -> None:
        text = "ㅇ 수행기간 : 계약체결일 ~ 2025. 12. 31."
        self.assertEqual(extract_construction_start_date(text), "계약체결일~2025-12-31")

    def test_extract_construction_start_date_supports_until_date_service_period(self) -> None:
        text = "본 과업의 설계용역기간은 2025년 1월 30일까지로, 인허가 완료시까지로 한다."
        self.assertEqual(extract_construction_start_date(text), "2025-01-30까지")

    def test_extract_completion_expected_date_normalizes_explicit_label(self) -> None:
        text = "완공예정일 : 2026. 02. 28"
        self.assertEqual(extract_completion_expected_date(text), "2026-02-28")

    def test_extract_construction_start_date_prefers_anchored_duration_phrase(self) -> None:
        text = """
예정 공사기간
4개월(준공목표: 2025.09.)
예정기간
착수일로부터 180일간
"""
        self.assertEqual(extract_construction_start_date(text), "착수일로부터180일간")

    def test_extract_construction_start_date_does_not_return_bare_month_count(self) -> None:
        text = "예정 공사기간 4개월(준공목표: 2025.09.)"
        self.assertEqual(extract_construction_start_date(text), "")

    def test_extract_site_location_rejects_duration_like_text(self) -> None:
        text = "사업위치 : 공사(용역)기간 : 20  .  ~ 20  ."
        value = extract_site_location(
            text,
            "경상남도교육청 경상남도함양교육지원청",
            "경상남도교육청 함양 도서관 이전 신축 설계공모",
        )
        self.assertEqual(value, "경상남도 함양군")

    def test_extract_site_location_rejects_area_label_text(self) -> None:
        text = "현장위치 : 대지면적"
        value = extract_site_location(
            text,
            "경상남도교육청 경상남도진주교육지원청",
            "진주기계공업고등학교 실습장 및 청소년 직업체험관 증축 설계공모",
        )
        self.assertEqual(value, "경상남도 진주시")

    def test_infer_city_from_org_or_project_ignores_119gu_noise(self) -> None:
        value = infer_city_from_org_or_project("경상남도", "양산소방서 119구조대 신축사업 설계공모")
        self.assertEqual(value, "")


    def test_infer_city_from_org_or_project_supports_metro_education_office_district(self) -> None:
        value = infer_city_from_org_or_project("부산광역시해운대교육지원청", "")
        self.assertEqual(value, "해운대구")

    def test_infer_city_from_org_or_project_supports_jeju_city_name(self) -> None:
        value = infer_city_from_org_or_project("제주특별자치도 제주시", "")
        self.assertEqual(value, "제주시")

    def test_infer_city_from_org_or_project_blanks_ambiguous_education_office_regions(self) -> None:
        self.assertEqual(infer_city_from_org_or_project("서울특별시교육청 서울특별시북부교육지원청", ""), "")
        self.assertEqual(infer_city_from_org_or_project("서울특별시교육청 서울특별시강서양천교육지원청", ""), "")
        self.assertEqual(infer_city_from_org_or_project("충청남도교육청 충청남도논산계룡교육지원청", ""), "")

    def test_infer_city_from_org_or_project_ignores_non_admin_org_suffixes(self) -> None:
        self.assertEqual(infer_city_from_org_or_project("당진도시공사", ""), "")
        self.assertEqual(infer_city_from_org_or_project("울산광역시 울산경제자유구역청", ""), "")
        self.assertEqual(infer_city_from_org_or_project("문화재청 국립해양문화재연구소", ""), "")


if __name__ == "__main__":
    unittest.main()
