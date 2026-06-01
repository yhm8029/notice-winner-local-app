from __future__ import annotations

import unittest

from backend.api.app import _build_related_notice_query_variants
from backend.api.app import _build_related_notice_primary_queries
from backend.api.app import _score_related_notice_match


class RelatedNoticeStemMatchingTests(unittest.TestCase):
    def test_query_variants_include_stem_and_head(self) -> None:
        variants = _build_related_notice_query_variants("의사숙소 신축공사 설계공모 공고")

        self.assertIn("의사숙소 신축공사", variants)
        self.assertIn("의사숙소 신축", variants)
        self.assertIn("의사숙소", variants)

    def test_score_accepts_discipline_split_same_project(self) -> None:
        project = {
            "project_name": "의사숙소 신축공사 설계공모 공고",
            "project_search_name": "의사숙소 신축공사",
            "_project_match_key": "의사숙소신축공사",
        }
        row = {
            "project_name": "강진의료원 의사 숙소 신축 소방공사",
            "org_name": "전라남도",
            "announce_date": "20250613",
            "bid_no": "R25BK00903695",
            "bid_ord": "000",
        }

        score, candidate_search_name, reason = _score_related_notice_match(project, row)

        self.assertGreaterEqual(score, 20)
        self.assertTrue(candidate_search_name)
        self.assertTrue("same_stem" in reason or "stem_overlap" in reason)

    def test_query_variants_expand_discipline_branch_for_material_followups(self) -> None:
        variants = _build_related_notice_query_variants(
            "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uc124\uacc4\uacf5\ubaa8"
        )

        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5", variants)
        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95", variants)
        self.assertIn("\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uacf5\uc0ac", variants)
        self.assertIn(
            "\uc5ec\ud765 \ub450\ub4dc\ub9bc\uc13c\ud130 \uc870\uc131\uc0ac\uc5c5 \uac74\ucd95\uacf5\uc0ac \uad00\uae09\uc790\uc7ac",
            variants,
        )

    def test_primary_queries_keep_business_anchor_before_international_design_tail(self) -> None:
        project_name = (
            "\uac00\ub355\ub3c4\uc2e0\uacf5\ud56d \uac74\uc124\uc0ac\uc5c5 "
            "\uc5ec\uac1d\ud130\ubbf8\ub110 \uad6d\uc81c\uc124\uacc4\uacf5\ubaa8"
        )
        project = {
            "project_name": project_name,
            "project_search_name": project_name,
            "latest_notice_title": project_name,
        }

        queries = _build_related_notice_primary_queries(project, "service")

        self.assertIn("\uac00\ub355\ub3c4\uc2e0\uacf5\ud56d \uac74\uc124\uc0ac\uc5c5", queries)


if __name__ == "__main__":
    unittest.main()
