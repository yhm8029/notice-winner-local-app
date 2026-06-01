from __future__ import annotations

import unittest

from backend.services.native_gui_rules import extract_contact_from_notice_text
from backend.services.native_gui_rules import extract_contact_observations_from_notice_text
from backend.services.native_gui_rules import has_external_competition_portal_only_contact
from backend.services.native_gui_rules import normalize_contact_candidate
from backend.services.native_llm_correction import LlmCorrectionConfig
from backend.services.native_llm_correction import maybe_correct_notice_fields_with_llm
from backend.services.native_tracker_backend import _normalize_tracker_contact


class _FakeAnthropicResponse:
    def __init__(self, text: str) -> None:
        self._text = text

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {"content": [{"type": "text", "text": self._text}]}


class NativeContactExtractionTests(unittest.TestCase):
    def test_extract_contact_observations_from_notice_text_returns_block_metadata(self) -> None:
        text = "\n".join(
            [
                "3) 기타 문의사항은 세연고등학교 행정실 설계공모 담당자",
                "(☎051-630-0293)으로 문의 바랍니다.",
            ]
        )

        observations = extract_contact_observations_from_notice_text(text, "부산광역시남부교육지원청")

        self.assertGreaterEqual(len(observations), 1)
        self.assertEqual(observations[0].contact, "행정실/051-630-0293")
        self.assertEqual(observations[0].evidence_block_type, "line_cluster")
        self.assertIn("세연고등학교 행정실", observations[0].evidence_block_text)
        self.assertEqual(observations[0].phase_hint, "notice")
        self.assertEqual(observations[0].role_hint, "owner_contact")
        self.assertEqual(observations[0].owner_side_hint, "yes")

    def test_extract_contact_observations_from_notice_text_dedupes_same_contact(self) -> None:
        text = "\n".join(
            [
                "문의처 : 경제과 기업지원팀(☎041-750-3032)",
                "전화 : 경제과 기업지원팀(041-750-3032)",
            ]
        )

        observations = extract_contact_observations_from_notice_text(text, "충청남도 금산군")

        self.assertEqual([item.contact for item in observations], ["경제과 기업지원팀/041-750-3032"])

    def test_extract_contact_from_notice_text_supports_education_office_contact(self) -> None:
        text = "\n".join(
            [
                "※ 질의접수 담당자 연락처 : 055-740-2172",
                ": 경상남도진주교육지원청 강경녀 (055-740-2172)",
                ": 조달청 건설기술계약과 박은자 (070-4056-7566)",
            ]
        )

        self.assertEqual(
            extract_contact_from_notice_text(text, "경상남도교육청 경상남도진주교육지원청"),
            "경상남도진주교육지원청/055-740-2172",
        )

    def test_extract_contact_from_notice_text_supports_task_force_suffix(self) -> None:
        text = "기타 자세한 사항은 창녕군청 미래전략추진단(☎055-530-2105)으로 문의"

        self.assertEqual(
            extract_contact_from_notice_text(text, "경상남도 창녕군"),
            "미래전략추진단/055-530-2105",
        )

    def test_extract_contact_from_notice_text_prefers_department_from_person_title_line(self) -> None:
        text = "설계공모 관련 문의 : 관광과 하태욱 주무관(☎052-226-3044)"

        self.assertEqual(
            extract_contact_from_notice_text(text, "울산광역시 남구"),
            "관광과/052-226-3044",
        )

    def test_extract_contact_from_notice_text_handles_labeled_person_line(self) -> None:
        text = "시행·주관기관 : 진주시 우주항공산업과 담당자 : 강은진 주무관 ☎055-749-8128"

        self.assertEqual(
            extract_contact_from_notice_text(text, "경상남도 진주시"),
            "우주항공산업과/055-749-8128",
        )

    def test_extract_contact_from_notice_text_handles_multiline_school_contact(self) -> None:
        text = "\n".join(
            [
                "3) 기타 문의사항은 세연고등학교 행정실 설계공모 담당자",
                "(☎051-630-0293)으로 문의 바랍니다.",
            ]
        )

        self.assertEqual(
            extract_contact_from_notice_text(text, "부산광역시남부교육지원청"),
            "행정실/051-630-0293",
        )

    def test_normalize_contact_candidate_keeps_org_style_department(self) -> None:
        self.assertEqual(
            normalize_contact_candidate("경상남도진주교육지원청/055-740-2172", "경상남도교육청 경상남도진주교육지원청"),
            "경상남도진주교육지원청/055-740-2172",
        )

    def test_normalize_contact_candidate_keeps_exact_org_name_contact(self) -> None:
        org = "\uad6d\ub9bd\uacf5\uc6d0\uacf5\ub2e8 \ub3d9\ubd80\uc9c0\uc5ed\ubcf8\ubd80"
        self.assertEqual(
            normalize_contact_candidate(f"{org}/055-771-8615", org),
            f"{org}/055-771-8615",
        )

    def test_extract_contact_from_notice_text_keeps_explicit_org_level_contact(self) -> None:
        org = "\uad6d\ub9bd\uacf5\uc6d0\uacf5\ub2e8 \ub3d9\ubd80\uc9c0\uc5ed\ubcf8\ubd80"
        text = (
            "\ub098. \uae30\ud0c0 \uc790\uc138\ud55c \ub0b4\uc6a9\uc740 \uc124\uacc4\uacf5\ubaa8 \uc9c0\uce68\uc11c\ub97c "
            "\ucc38\uace0\ud558\uace0, \ubcc4\ub3c4 \ubb38\uc758\uc0ac\ud56d\uc740 "
            "\uad6d\ub9bd\uacf5\uc6d0\uacf5\ub2e8 \ub3d9\ubd80\uc9c0\uc5ed\ubcf8\ubd80(055-771-8615)\uc73c\ub85c "
            "\ubb38\uc758 \ubc14\ub78c."
        )
        self.assertEqual(
            extract_contact_from_notice_text(text, org),
            f"{org}/055-771-8615",
        )

    def test_normalize_tracker_contact_accepts_new_department_suffixes(self) -> None:
        self.assertEqual(_normalize_tracker_contact("미래전략추진단/055-530-2105"), "미래전략추진단/055-530-2105")
        self.assertEqual(
            _normalize_tracker_contact("경상남도진주교육지원청/055-740-2172"),
            "경상남도진주교육지원청/055-740-2172",
        )

    def test_extract_contact_from_notice_text_discards_noisy_labeled_fallback(self) -> None:
        text = "\n".join(
            [
                "문의처 : (052-226-3044)에 유선으로 사전 통보한 후 전송하고 수신여부를 반드시 확인하여야 한다.",
                "문의 : 경우 출자비율은 탈퇴자의 출자비율을 잔존구성원의 출자비율에 따라 분할한다.",
            ]
        )

        self.assertEqual(extract_contact_from_notice_text(text, "울산광역시 남구"), "")


    def test_extract_contact_from_notice_text_rejects_management_agency_and_sentence_fragment(self) -> None:
        text = "\n".join(
            [
                "가. 설계공모 주최: 경상남도 거창군 전략담당관",
                "담당자: 김승우 (전화번호: 055-940-3377, 전자우편: tree0328@korea.kr)",
                "나. 공모관리기관 : 마실와이드",
                "(전화번호: 02-6010-1022 [내선번호2] / 전자우편: competition@masilwide.com)",
                "나. 심사위원회: 토론을 통해 공모안을 분석하고 공정한 과정을 거쳐 당선작을 선정한다.",
            ]
        )

        self.assertEqual(extract_contact_from_notice_text(text, "경상남도 거창군"), "")

    def test_extract_contact_from_notice_text_prefers_owner_contact_over_eval_vendor(self) -> None:
        text = "\n".join(
            [
                "* 평가 용역업체 담당자 : 김재민 실장, 010-8601-0209",
                "다. 기타 문의사항은 경상남도함양교육지원청 행정지원과 시설지원담당(☎055-960-2791) 또는 교육재정담당(☎055-960-2781)으로 문의하시기 바랍니다.",
            ]
        )

        self.assertEqual(
            extract_contact_from_notice_text(text, "경상남도교육청 경상남도함양교육지원청"),
            "행정지원과/055-960-2791",
        )

    def test_extract_contact_from_notice_text_prefers_department_after_colon(self) -> None:
        text = "가. 용역 과업사항 : 경제과 기업지원팀(☎041-750-3032)"

        self.assertEqual(
            extract_contact_from_notice_text(text, "충청남도 금산군"),
            "경제과 기업지원팀/041-750-3032",
        )


    def test_has_external_competition_portal_only_contact_detects_competition_portal(self) -> None:
        text = "\n".join(
            [
                "공모관리기관 : 마실와이드(주)",
                "질의접수 : 2025. 6. 18. ~ 6. 20.",
                "질의답변 : 설계공모 홈페이지(https://공모전.kr)",
                "전자우편 및 전화를 통한 개별 질의 불가",
            ]
        )
        self.assertTrue(has_external_competition_portal_only_contact(text))

    def test_has_external_competition_portal_only_contact_does_not_flag_internal_management_team(self) -> None:
        text = "\n".join(
            [
                "문의처 : 공모관리팀(053-767-1109)",
                "붙임1) 공고문 참조",
            ]
        )
        self.assertFalse(has_external_competition_portal_only_contact(text))

    def test_extract_contact_from_notice_text_rejects_external_portal_noise_phone(self) -> None:
        text = "\n".join(
            [
                "관광진흥과(02-6010-1022)",
                "공모관리기관 : 마실와이드(주)",
                "질의답변 : 설계공모 홈페이지(https://공모전.kr)",
                "전자우편 및 전화를 통한 개별 질의 불가",
            ]
        )
        self.assertEqual(extract_contact_from_notice_text(text, "예시군"), "")

    def test_extract_contact_from_notice_text_keeps_non_portal_phone_even_with_management_team(self) -> None:
        text = "\n".join(
            [
                "공모관리팀(053-767-1109)",
                "질의답변은 공고문 참조",
            ]
        )
        self.assertEqual(
            extract_contact_from_notice_text(text, "예시군"),
            "공모관리팀/053-767-1109",
        )


class NativeContactLlmTests(unittest.TestCase):
    def test_maybe_correct_notice_fields_with_llm_runs_for_generic_contact(self) -> None:
        result = maybe_correct_notice_fields_with_llm(
            config=LlmCorrectionConfig(
                enabled=True,
                api_key="test-key",
                model="claude-3-5-haiku-latest",
                max_rows=20,
                max_chars=4000,
            ),
            text="문의 : 미래전략추진단(055-530-2105)",
            project_name="장마면 기초생활 거점조성",
            org_name="경상남도 창녕군",
            area="1,174㎡",
            cost="5,745,000,000원",
            contact="팀/055-530-2105",
            request_fn=lambda *args, **kwargs: _FakeAnthropicResponse(
                '{"contact":"미래전략추진단/055-530-2105"}'
            ),
        )

        self.assertEqual(result.contact, "미래전략추진단/055-530-2105")
        self.assertEqual(result.corrected_fields, ("contact",))

    def test_maybe_correct_notice_fields_with_llm_skips_valid_contact(self) -> None:
        called = {"value": False}

        def _request(*args, **kwargs):
            called["value"] = True
            return _FakeAnthropicResponse("{}")

        result = maybe_correct_notice_fields_with_llm(
            config=LlmCorrectionConfig(
                enabled=True,
                api_key="test-key",
                model="claude-3-5-haiku-latest",
                max_rows=20,
                max_chars=4000,
            ),
            text="설계공모 관련 문의 : 관광과 하태욱 주무관(☎052-226-3044)",
            project_name="장생 아트플렉스 건립사업 건축설계공모",
            org_name="울산광역시 남구",
            area="1,250㎡",
            cost="5,000,000,000원",
            contact="관광과/052-226-3044",
            request_fn=_request,
        )

        self.assertFalse(called["value"])
        self.assertEqual(result.contact, "")
        self.assertEqual(result.corrected_fields, ())
