from __future__ import annotations

import unittest

from backend.services.native_gui_rules_location_runtime import extract_completion_expected_date
from backend.services.native_gui_rules_location_runtime import extract_site_location
from backend.services.native_gui_rules_location_runtime import infer_city_from_org_or_project


class NativeGuiRulesLocationRuntimeTests(unittest.TestCase):
    def test_extract_completion_expected_date_normalizes_explicit_label(self) -> None:
        text = "준공예정일 : 2026. 02. 28"
        self.assertEqual(extract_completion_expected_date(text), "2026-02-28")

    def test_extract_site_location_falls_back_to_inferred_location(self) -> None:
        value = extract_site_location(
            "사업위치 : 대지면적",
            "경상남도교육청 경상남도진주교육지원청",
            "진주기계공업고등학교 실습장 및 청소원 직업체험관 증축 설계공모",
        )
        self.assertEqual(value, "경상남도 진주시")

    def test_infer_city_from_org_or_project_ignores_119gu_noise(self) -> None:
        value = infer_city_from_org_or_project("경상남도", "양산소방서 119구조대 신축사업 설계공모")
        self.assertEqual(value, "")


if __name__ == "__main__":
    unittest.main()
