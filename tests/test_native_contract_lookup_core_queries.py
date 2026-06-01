from __future__ import annotations

import unittest

from backend.services.native_contract_lookup import _build_core_project_queries
from backend.services.native_contract_lookup import _build_hub_project_queries
from backend.services.native_contract_lookup import _build_lofin_query_variants


class NativeContractLookupCoreQueryTests(unittest.TestCase):
    def test_core_queries_preserve_specific_prefix(self) -> None:
        queries = _build_core_project_queries(
            "금산인삼약초특화농공단지 복합문화센터 건축설계공모(제안공모)"
        )

        self.assertEqual(
            queries[:2],
            [
                "금산인삼약초특화농공단지 복합문화센터",
                "금산인삼약초특화농공단지",
            ],
        )

    def test_core_queries_simplify_build_project_suffix(self) -> None:
        queries = _build_core_project_queries(
            "당진시 육아종합지원센터 건립사업 설계공모(제안공모)"
        )

        self.assertEqual(
            queries[:2],
            [
                "당진시 육아종합지원센터 건립",
                "당진시 육아종합지원센터",
            ],
        )

    def test_core_queries_add_nospace_variant(self) -> None:
        queries = _build_core_project_queries("원덕 노인복지관 건립사업 설계공모")

        self.assertIn("원덕 노인복지관 건립", queries)
        self.assertIn("원덕 노인복지관", queries)
        self.assertIn("원덕노인복지관건립", queries)

    def test_lofin_variants_reuse_core_queries(self) -> None:
        self.assertEqual(
            _build_lofin_query_variants("망우본동 생활 SOC 건립 설계공모"),
            _build_core_project_queries("망우본동 생활 SOC 건립 설계공모")[:3],
        )

    def test_hub_queries_strip_leading_qualifiers_and_keep_prefix(self) -> None:
        queries = _build_hub_project_queries("(집행대행)(가칭) 구미늘품뜰 거점형 늘봄센터 신축공사 설계공모")

        self.assertIn("구미늘품뜰 거점형 늘봄센터 신축공사", queries)
        self.assertIn("구미늘품뜰", queries)

    def test_hub_queries_shorten_school_names(self) -> None:
        queries = _build_hub_project_queries("(집행대행)진보초등학교 공간재구조화사업 건축 설계공모")

        self.assertIn("진보초 공간재구조화사업", queries)
        self.assertIn("진보초", queries)


class NativeContractLookupHubPrefixFallbackTests(unittest.TestCase):
    def test_hub_queries_add_short_prefix_fallback(self) -> None:
        queries = _build_hub_project_queries(
            "(\uc9d1\ud589\ub300\ud589)(\uac00\uce6d) \uad6c\ubbf8\ub298\ud488\ub738 \uac70\uc810\ud615 \ub298\ubd04\uc13c\ud130 \uc2e0\ucd95\uacf5\uc0ac \uc124\uacc4\uacf5\ubaa8"
        )

        self.assertIn("\uad6c\ubbf8", queries)


if __name__ == "__main__":
    unittest.main()
