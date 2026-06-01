from __future__ import annotations

import unittest

from backend.services.native_gui_rules import normalize_contact_candidate
from backend.services.native_tracker_backend import _normalize_tracker_contact


class NativeContactCleanupRegressionTests(unittest.TestCase):
    def test_normalize_contact_candidate_strips_person_tail_from_department(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "균형개발사업처 최주영 과/070-4217-8323",
                "충북개발공사",
            ),
            "균형개발사업처/070-4217-8323",
        )

    def test_normalize_contact_candidate_rejects_vendor_company_name(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "마실와이드 주식회사/055-940-3377",
                "건축군",
            ),
            "",
        )

    def test_tracker_contact_cleanup_uses_common_normalizer(self) -> None:
        self.assertEqual(
            _normalize_tracker_contact("균형개발사업처 최주영 과/070-4217-8323"),
            "균형개발사업처/070-4217-8323",
        )

    def test_tracker_contact_cleanup_rejects_short_noise_suffix(self) -> None:
        self.assertEqual(
            _normalize_tracker_contact("마실/055-940-3377"),
            "",
        )

    def test_normalize_contact_candidate_rejects_sentence_noise_tail(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "자료 전송 및 접수 사실/051-752-3355",
                "부산광역시해운대교육지원청 해운대여자중학교",
            ),
            "",
        )

    def test_normalize_contact_candidate_rejects_person_name_plus_suffix_only(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "김민선 과/033-259-6317",
                "강원개발공사",
            ),
            "",
        )

    def test_normalize_contact_candidate_rejects_management_agency_phrase(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "공모관리기관/02-6010-1022",
                "거창군",
            ),
            "",
        )

    def test_normalize_contact_candidate_rejects_discussion_sentence_fragment(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "토론을 통해 공모안을 분석하고 공정한 과/02-6010-1022",
                "거창군",
            ),
            "",
        )

    def test_normalize_contact_candidate_strips_leading_sentence_before_department(self) -> None:
        self.assertEqual(
            normalize_contact_candidate(
                "구체적인 실적 인정 여부는 문화기반조성과/062-613-3482",
                "광주광역시",
            ),
            "문화기반조성과/062-613-3482",
        )

    def test_tracker_contact_cleanup_strips_leading_sentence_from_fallback_person_only_contact(self) -> None:
        self.assertEqual(
            _normalize_tracker_contact(
                "문의는 조성일/053-233-0162",
                allow_person_only=True,
            ),
            "조성일/053-233-0162",
        )

    def test_tracker_contact_cleanup_rejects_sentence_fragment_when_fallback_person_only_is_enabled(self) -> None:
        self.assertEqual(
            _normalize_tracker_contact(
                "자료 전송 및 접수 사실/051-752-3355",
                allow_person_only=True,
            ),
            "",
        )


if __name__ == "__main__":
    unittest.main()
