from __future__ import annotations

import unittest

from backend.services.related_notice_classification import classify_related_notice_item
from backend.services.related_notice_classification import group_related_notice_items
from backend.services.run_execution_related_notice_runtime import build_related_notice_project_entry
from backend.services.related_notice_query_runtime import RELATED_NOTICE_COLLECT_MAX_QUERIES
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_DEADLINE_SEC
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_MAX_PAGES
from backend.services.related_notice_query_runtime import RELATED_NOTICE_LIVE_REQUEST_TIMEOUT_SEC
from backend.services.related_notice_query_runtime import _build_related_notice_query_variants


class RelatedNoticeClassificationTests(unittest.TestCase):
    def test_live_related_notice_search_uses_fast_interactive_budget(self) -> None:
        self.assertLessEqual(RELATED_NOTICE_LIVE_DEADLINE_SEC, 35)
        self.assertLessEqual(RELATED_NOTICE_LIVE_REQUEST_TIMEOUT_SEC, 6)
        self.assertLessEqual(RELATED_NOTICE_COLLECT_MAX_QUERIES, 6)
        self.assertLessEqual(RELATED_NOTICE_LIVE_MAX_PAGES, 1)

    def test_detailed_design_notice_is_sales_relevant(self) -> None:
        item = {
            "project_name": "OO복합문화센터 건립사업 기본 및 실시설계 용역",
            "match_score": 120,
        }

        classified = classify_related_notice_item({}, item)

        self.assertEqual(classified["notice_stage"], "DESIGN_SERVICE")
        self.assertEqual(classified["sales_relevance"], "sales_relevant")
        self.assertIn("PHASE_MATCH:DESIGN_SERVICE", classified["reason_codes"])

    def test_proposal_evaluation_service_is_excluded(self) -> None:
        item = {
            "project_name": "OO학교 건축설계공모 제안서 평가용역",
            "match_score": 140,
        }

        classified = classify_related_notice_item({}, item)

        self.assertEqual(classified["notice_stage"], "ADMIN_NOISE")
        self.assertEqual(classified["sales_relevance"], "excluded")
        self.assertEqual(classified["exclusion_reason"], "HARD_EXCLUDE:proposal_evaluation")

    def test_design_competition_system_and_event_operation_are_excluded(self) -> None:
        titles = [
            "인천광역시교육청 설계공모 심사시스템 구축 용역",
            "제6회 서울식물원 식재설계공모전 시상식 운영",
        ]

        classified_items = [classify_related_notice_item({}, {"project_name": title, "match_score": 100}) for title in titles]

        self.assertEqual([item["sales_relevance"] for item in classified_items], ["excluded", "excluded"])
        self.assertEqual([item["notice_stage"] for item in classified_items], ["ADMIN_NOISE", "ADMIN_NOISE"])

    def test_construction_rebid_is_preserved_as_sales_relevant(self) -> None:
        item = {
            "project_name": "OO복합문화센터 전기공사 입찰 재공고",
            "match_score": 95,
        }

        classified = classify_related_notice_item({}, item)

        self.assertEqual(classified["notice_stage"], "CONSTRUCTION_REBID")
        self.assertEqual(classified["sales_relevance"], "sales_relevant")
        self.assertEqual(classified["exclusion_reason"], "")

    def test_design_competition_rebid_is_excluded(self) -> None:
        item = {
            "project_name": "OO복합문화센터 건축 설계공모 재공고",
            "match_score": 95,
        }

        classified = classify_related_notice_item({}, item)

        self.assertEqual(classified["notice_stage"], "SELF_OR_CORRECTION")
        self.assertEqual(classified["sales_relevance"], "excluded")
        self.assertEqual(classified["exclusion_reason"], "HARD_EXCLUDE:self_or_correction")

    def test_group_related_notice_items_separates_sales_reference_and_excluded(self) -> None:
        items = [
            {"project_name": "OO복합문화센터 실시설계 용역", "match_score": 120},
            {"project_name": "OO복합문화센터 심사결과 공고", "match_score": 90},
            {"project_name": "OO복합문화센터 심사위원 운영 용역", "match_score": 80},
        ]

        grouped = group_related_notice_items({}, items)

        self.assertEqual([item["notice_stage"] for item in grouped["sales_relevant"]], ["DESIGN_SERVICE"])
        self.assertEqual([item["notice_stage"] for item in grouped["reference"]], ["CONTEST_RESULT"])
        self.assertEqual([item["notice_stage"] for item in grouped["excluded"]], ["ADMIN_NOISE"])

    def test_query_variants_include_phase_lane_terms_for_business_anchor(self) -> None:
        variants = _build_related_notice_query_variants("가덕도신공항 건설사업 여객터미널 국제설계공모")

        self.assertIn("가덕도신공항 여객터미널 실시설계", variants)
        self.assertIn("가덕도신공항 여객터미널 설계용역", variants)
        self.assertIn("가덕도신공항 여객터미널 감리", variants)
        self.assertIn("가덕도신공항 여객터미널 공사", variants)

    def test_project_entry_stores_grouped_related_notices(self) -> None:
        entry = build_related_notice_project_entry(
            project={"project_key": "demo", "project_name": "Demo", "project_search_name": "Demo"},
            run_id="00000000-0000-0000-0000-000000000001",
            items=[
                classify_related_notice_item({}, {"project_name": "Demo 실시설계 용역", "match_score": 120}),
                classify_related_notice_item({}, {"project_name": "Demo 심사위원 운영 용역", "match_score": 80}),
            ],
            source="live",
            error_message="",
            search_debug={},
            algorithm_version=99,
        )

        self.assertEqual(len(entry["groups"]["sales_relevant"]), 1)
        self.assertEqual(len(entry["groups"]["excluded"]), 1)
        self.assertEqual(entry["stats"]["sales_relevant_count"], 1)
        self.assertEqual(entry["stats"]["excluded_count"], 1)


if __name__ == "__main__":
    unittest.main()
