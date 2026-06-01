from __future__ import annotations

import unittest

from backend.api.app import _build_related_notice_query_variants
from backend.api.app import _project_search_name


class ProjectQueryNormalizationTests(unittest.TestCase):
    def test_strips_design_competition_suffix_and_noise_parenthetical(self) -> None:
        self.assertEqual(
            _project_search_name("목재누리센터 건립사업 기본 및 실시설계 공모(제안)"),
            "목재누리센터 건립사업",
        )

    def test_removes_decorative_quotes(self) -> None:
        self.assertEqual(
            _project_search_name("「여수시 본청사 별관증축 건립사업」 건축 설계 공모"),
            "여수시 본청사 별관증축 건립사업",
        )

    def test_prefers_project_clause_after_brand_phrase(self) -> None:
        self.assertEqual(
            _project_search_name("청년문화 강진, 청년 글로벌 플랫폼 조성사업 설계 공모"),
            "청년 글로벌 플랫폼 조성사업",
        )

    def test_humanizes_slug_like_tracker_norm(self) -> None:
        self.assertEqual(
            _project_search_name("여수시-본청사-별관증축-건립사업-건축-설계-공모"),
            "여수시 본청사 별관증축 건립사업",
        )

    def test_strips_design_noise_from_slug_like_tracker_norm(self) -> None:
        self.assertEqual(
            _project_search_name("목재누리센터-건립사업-기본-및-실시설계-공모"),
            "목재누리센터 건립사업",
        )

    def test_strips_trailing_architecture_noise_from_slug_like_tracker_norm(self) -> None:
        self.assertEqual(
            _project_search_name("고군농공단지-청년문화센터-건립사업-건축"),
            "고군농공단지 청년문화센터 건립사업",
        )

    def test_does_not_collapse_to_short_tail_phrase(self) -> None:
        self.assertEqual(
            _project_search_name("「여수시 본청사 별관증축 건립사업」 건축 설계 공모"),
            "여수시 본청사 별관증축 건립사업",
        )
        self.assertEqual(
            _project_search_name("[삼호 건강증진형 보건지소 전환 증축공사 ] 건축 설계공모"),
            "삼호 건강증진형 보건지소 전환 증축공사",
        )
        self.assertEqual(
            _project_search_name("[영암 낭씽이 생물자원 보전시설 조성사업 ] 건축 설계공모"),
            "영암 낭씽이 생물자원 보전시설 조성사업",
        )

    def test_related_notice_query_variants_include_broader_terms(self) -> None:
        variants = _build_related_notice_query_variants("고군농공단지 청년문화센터 건립사업")
        self.assertIn("고군농공단지 청년문화센터 건립사업", variants)
        self.assertIn("고군농공단지 청년문화센터", variants)
        self.assertIn("청년문화센터 건립사업", variants)

    def test_strips_notice_suffix_from_imsil_foreign_worker_case(self) -> None:
        self.assertEqual(
            _project_search_name("임실군 농촌 외국인 근로자 기숙사 건립사업 설계공모(제안공모)"),
            "임실군 농촌 외국인 근로자 기숙사 건립사업",
        )

    def test_preserves_meaningful_parenthetical_and_drops_leading_year(self) -> None:
        self.assertEqual(
            _project_search_name("2023년 거점형 대형놀이터(덕진)"),
            "거점형 대형놀이터 덕진",
        )


if __name__ == "__main__":
    unittest.main()
