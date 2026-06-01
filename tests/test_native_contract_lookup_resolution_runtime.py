from __future__ import annotations

import unittest
from unittest.mock import patch

import backend.services.native_contract_lookup_core_runtime as core_runtime
from backend.services.native_contract_lookup_core_runtime_state import ContractLookupMeta
from backend.services.native_contract_lookup_core_runtime_state import ContractLookupResult
from backend.services.native_contract_lookup_resolution_runtime import resolve_ordered_contract_lookup_fallbacks


class NativeContractLookupResolutionRuntimeTests(unittest.TestCase):
    def test_resolve_ordered_contract_lookup_fallbacks_short_circuits_on_eais_hit(self) -> None:
        hit = ContractLookupResult(contract_name="eais", source_type="eais_web")
        base_meta = ContractLookupMeta(contract_lookup_path="query_sweep_hit", query_sweep_used=True)
        captured: list[ContractLookupMeta] = []

        with patch(
            "backend.services.native_contract_lookup_resolution_runtime.get_last_contract_lookup_meta",
            return_value=base_meta,
        ), patch(
            "backend.services.native_contract_lookup_resolution_runtime._set_last_contract_lookup_meta",
            side_effect=captured.append,
        ):
            result = resolve_ordered_contract_lookup_fallbacks(
                project_name_norm="project",
                announce_date="20250101",
                timeout_sec=10.0,
                org_name="org",
                resolve_eais_contract_hit_fn=lambda **_: hit,
                resolve_hub_result_hit_fn=lambda **_: self.fail("hub should not run after eais hit"),
                resolve_lofin_contract_hit_fn=lambda **_: self.fail("lofin should not run after eais hit"),
                is_education_org_name_fn=lambda _value: False,
            )

        self.assertIs(result, hit)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].contract_lookup_path, "eais_hit")
        self.assertTrue(captured[0].query_sweep_used)

    def test_core_runtime_delegates_to_ordered_fallback_helper_when_g2b_is_skipped(self) -> None:
        sentinel = ContractLookupResult(contract_name="delegated", source_type="delegated")

        with patch(
            "backend.services.native_contract_lookup_core_runtime.resolve_service_key",
            return_value="",
        ), patch(
            "backend.services.native_contract_lookup_core_runtime.resolve_ordered_contract_lookup_fallbacks",
            return_value=sentinel,
        ) as fallback_helper:
            result = core_runtime.resolve_contract_by_bid_no(
                bid_no="",
                project_name_norm="project",
                announce_date="20250101",
                org_name="org",
            )

        self.assertIs(result, sentinel)
        fallback_helper.assert_called_once()

    def test_resolve_ordered_contract_lookup_fallbacks_merges_previous_meta_into_lofin_hit(self) -> None:
        hit = ContractLookupResult(contract_name="lofin", source_type="lofin_api")
        base_meta = ContractLookupMeta(
            contract_lookup_path="query_sweep_no_hit",
            query_sweep_used=True,
            lofin_best_score=0.1,
        )
        lofin_meta = ContractLookupMeta(
            contract_lookup_path="lofin_stage",
            lofin_date_workers=3,
            lofin_hit_date="20250324",
            lofin_best_score=0.8,
        )
        captured: list[ContractLookupMeta] = []
        meta_values = iter([base_meta, base_meta, base_meta, lofin_meta])

        def _fake_get_last_contract_lookup_meta() -> ContractLookupMeta:
            return next(meta_values)

        with patch(
            "backend.services.native_contract_lookup_resolution_runtime.get_last_contract_lookup_meta",
            side_effect=_fake_get_last_contract_lookup_meta,
        ), patch(
            "backend.services.native_contract_lookup_resolution_runtime._set_last_contract_lookup_meta",
            side_effect=captured.append,
        ):
            result = resolve_ordered_contract_lookup_fallbacks(
                project_name_norm="project",
                announce_date="20250101",
                timeout_sec=10.0,
                org_name="org",
                resolve_eais_contract_hit_fn=lambda **_: None,
                resolve_hub_result_hit_fn=lambda **_: None,
                resolve_lofin_contract_hit_fn=lambda **_: hit,
                is_education_org_name_fn=lambda _value: False,
            )

        self.assertIs(result, hit)
        self.assertEqual(len(captured), 1)
        merged = captured[0]
        self.assertEqual(merged.contract_lookup_path, "lofin_hit")
        self.assertTrue(merged.query_sweep_used)
        self.assertEqual(merged.lofin_date_workers, 3)
        self.assertEqual(merged.lofin_hit_date, "20250324")
        self.assertEqual(merged.lofin_best_score, 0.8)


if __name__ == "__main__":
    unittest.main()
