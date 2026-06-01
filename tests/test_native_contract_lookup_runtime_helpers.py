from __future__ import annotations

import unittest

from backend.services.native_contract_lookup_eais_runtime import _extract_duration_days
from backend.services.native_contract_lookup_eais_runtime import _normalize_eais_amount
from backend.services.native_contract_lookup_eais_runtime import _parse_corp_list_company
from backend.services.native_contract_lookup_eais_runtime import _parse_ymd_flexible
from backend.services.native_contract_lookup_query_helpers_runtime import _build_core_project_queries
from backend.services.native_contract_lookup_query_helpers_runtime import _build_hub_project_queries


class NativeContractLookupRuntimeHelperTests(unittest.TestCase):
    def test_parse_corp_list_company_prefers_primary_role(self) -> None:
        company = _parse_corp_list_company(
            "[0^공동^x^보조업체^x^x^90][1^주계약업체^x^대표업체^x^x^10]"
        )

        self.assertEqual(company, "대표업체")

    def test_extract_duration_days_supports_months(self) -> None:
        self.assertEqual(_extract_duration_days("착수일로부터 6개월"), 180)

    def test_normalize_eais_amount_keeps_digits_only(self) -> None:
        self.assertEqual(_normalize_eais_amount("금1,234,500원"), "1234500")

    def test_parse_ymd_flexible_accepts_dashed_date(self) -> None:
        parsed = _parse_ymd_flexible("2025-04-03")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.strftime("%Y%m%d"), "20250403")

    def test_build_core_project_queries_adds_nospace_variant(self) -> None:
        queries = _build_core_project_queries("원덕 노인복지관 건립사업 설계공모")

        self.assertIn("원덕 노인복지관 건립", queries)
        self.assertIn("원덕 노인복지관", queries)
        self.assertIn("원덕노인복지관건립", queries)

    def test_build_hub_project_queries_adds_short_prefix_fallback(self) -> None:
        queries = _build_hub_project_queries("(집행대행)(가칭) 구미늘품뜰 거점형 늘봄센터 신축공사 설계공모")

        self.assertIn("구미", queries)


if __name__ == "__main__":
    unittest.main()
