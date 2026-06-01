from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.reextract_supabase_contacts import assess_current_contact_quality
from scripts.reextract_supabase_contacts import classify_result
from scripts.reextract_supabase_contacts import detect_bid_notice_status
from scripts.reextract_supabase_contacts import normalize_confirmed_contact_candidate
from scripts.reextract_supabase_contacts import should_exclude_contact_target


class ReextractSupabaseContactsTests(unittest.TestCase):
    def test_should_exclude_contact_target_for_auxiliary_project(self) -> None:
        self.assertTrue(should_exclude_contact_target("대구유아교육진흥원 분원 설립공사 설계공모(건축+전시) 제안서 평가용역"))
        self.assertFalse(should_exclude_contact_target("정부대전지방합동청사 건립사업 국제설계공모"))

    def test_detect_bid_notice_status_marks_exact_cancelled_notice(self) -> None:
        class _FakeResponse:
            status_code = 200

            def json(self) -> dict:
                return {
                    "response": {
                        "header": {"resultCode": "00", "resultMsg": "OK"},
                        "body": {
                            "totalCount": 2,
                            "items": {
                                "item": [
                                    {
                                        "bidNtceNo": "R25BK00664465",
                                        "bidNtceOrd": "000",
                                        "bidNtceNm": "테스트 공고",
                                        "ntceKindNm": "등록공고",
                                    },
                                    {
                                        "bidNtceNo": "R25BK00664465",
                                        "bidNtceOrd": "001",
                                        "bidNtceNm": "테스트 공고",
                                        "ntceKindNm": "취소공고",
                                    },
                                ]
                            },
                        },
                    }
                }

        class _FakeSession:
            def get(self, endpoint_url: str, params: dict, timeout: int) -> _FakeResponse:
                return _FakeResponse()

        with patch("scripts.reextract_supabase_contacts.requests.Session", return_value=_FakeSession()):
            status = detect_bid_notice_status(
                service_key="fake-key",
                bid_no="R25BK00664465",
                bid_ord="001",
                notice_date="20250221",
            )

        self.assertEqual(status, "cancelled")

    def test_normalize_confirmed_contact_candidate_rejects_sentence_fragment(self) -> None:
        normalized, reason = normalize_confirmed_contact_candidate(
            "토론을 통해 공모안을 분석하고 공정한 과/055-940-3703",
            "경상남도 거창군",
        )

        self.assertEqual(normalized, "")
        self.assertEqual(reason, "sentence_fragment")

    def test_normalize_confirmed_contact_candidate_keeps_structured_department_phone(self) -> None:
        normalized, reason = normalize_confirmed_contact_candidate(
            "청주시청 공공시설과/043-201-2582",
            "청주시",
        )

        self.assertEqual(normalized, "공공시설과/043-201-2582")
        self.assertEqual(reason, "")

    def test_normalize_confirmed_contact_candidate_keeps_exact_org_name_contact(self) -> None:
        org = "\uad6d\ub9bd\uacf5\uc6d0\uacf5\ub2e8 \ub3d9\ubd80\uc9c0\uc5ed\ubcf8\ubd80"
        normalized, reason = normalize_confirmed_contact_candidate(
            f"{org}/055-771-8615",
            org,
        )

        self.assertEqual(normalized, f"{org}/055-771-8615")
        self.assertEqual(reason, "")

    def test_classify_result_keeps_existing_normal_contact(self) -> None:
        status, safe = classify_result(
            current_contact="시설지원과/052-204-2615",
            current_needs_llm=False,
            candidate_contact="교육체육과/052-204-1152",
            candidate_source="confirmed_extracted",
            llm_contact_corrected=True,
            error="",
        )

        self.assertEqual(status, "keep_current")
        self.assertFalse(safe)

    def test_classify_result_allows_blank_to_confirmed_fill(self) -> None:
        status, safe = classify_result(
            current_contact="",
            current_needs_llm=True,
            candidate_contact="동수영중학교 행정실/051-752-3355",
            candidate_source="confirmed_extracted",
            llm_contact_corrected=True,
            error="",
        )

        self.assertEqual(status, "safe_improvement")
        self.assertTrue(safe)

    def test_classify_result_allows_same_phone_specificity_upgrade(self) -> None:
        status, safe = classify_result(
            current_contact="접수사실/043-201-2582",
            current_needs_llm=True,
            candidate_contact="청주시청 공공시설과/043-201-2582",
            candidate_source="confirmed_extracted",
            llm_contact_corrected=True,
            error="",
        )

        self.assertEqual(status, "safe_upgrade_same_phone")
        self.assertTrue(safe)

    def test_classify_result_blocks_generic_to_different_phone_auto_apply(self) -> None:
        status, safe = classify_result(
            current_contact="접수사실/043-201-2582",
            current_needs_llm=True,
            candidate_contact="김원/043-201-1733",
            candidate_source="confirmed_extracted",
            llm_contact_corrected=True,
            error="",
        )

        self.assertEqual(status, "review_needed")
        self.assertFalse(safe)

    def test_assess_current_contact_quality_marks_sentence_fragment_implausible(self) -> None:
        implausible, weak = assess_current_contact_quality(
            current_contact="토론을 통해 공모안을 분석하고 공정한 과/055-940-3379",
            org_name="경상남도 거창군",
        )

        self.assertTrue(implausible)
        self.assertFalse(weak)

    def test_assess_current_contact_quality_marks_admin_office_as_weak(self) -> None:
        implausible, weak = assess_current_contact_quality(
            current_contact="행정실/051-518-7923",
            org_name="부산광역시교육청 부산정보관광고등학교",
        )

        self.assertFalse(implausible)
        self.assertTrue(weak)

    def test_classify_result_allows_safe_replace_for_implausible_current(self) -> None:
        status, safe = classify_result(
            current_contact="토론을 통해 공모안을 분석하고 공정한 과/055-940-3379",
            current_needs_llm=True,
            current_implausible=True,
            current_weak=False,
            candidate_contact="건축주택과/055-665-2975",
            candidate_source="confirmed_extracted",
            llm_contact_corrected=False,
            expected_blank_external_portal=False,
            error="",
        )

        self.assertEqual(status, "safe_replace_implausible_current")
        self.assertTrue(safe)

    def test_classify_result_keeps_weak_current_contact_as_review(self) -> None:
        status, safe = classify_result(
            current_contact="행정실/051-518-7923",
            current_needs_llm=True,
            current_implausible=False,
            current_weak=True,
            candidate_contact="시설과/051-518-7924",
            candidate_source="confirmed_extracted",
            llm_contact_corrected=False,
            expected_blank_external_portal=False,
            error="",
        )

        self.assertEqual(status, "review_needed")
        self.assertFalse(safe)


if __name__ == "__main__":
    unittest.main()
