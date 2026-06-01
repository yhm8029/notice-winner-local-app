from __future__ import annotations

import unittest

from backend.services.native_contract_lookup_match_runtime import _contract_target_match_score
from backend.services.native_contract_lookup_match_runtime import _pick_best_g2b_contract_hit_by_bid_no
from backend.services.native_contract_lookup_match_runtime import _repair_utf8_mojibake


class NativeContractLookupMatchRuntimeTests(unittest.TestCase):
    def test_repair_utf8_mojibake_prefers_hangul_decoding(self) -> None:
        self.assertEqual(_repair_utf8_mojibake("ëíë¯¼êµ­"), "대한민국")

    def test_contract_target_match_score_adds_bonus_for_large_contract_and_suffix_stripped_match(self) -> None:
        score = _contract_target_match_score(
            "서울시립미술관 건립사업 설계용역",
            "서울시립미술관",
            row={"totCntrctAmt": "600000000"},
            strip_project_suffix_noise_fn=lambda value: value.replace(" 건립사업 설계용역", ""),
            extract_contract_amount_int_fn=lambda row: int(row.get("totCntrctAmt") or 0),
        )

        self.assertGreaterEqual(score, 0.96)

    def test_pick_best_g2b_contract_hit_by_bid_no_prefers_exact_bid_token_match(self) -> None:
        rows = [
            {"ntceNo": "2025-0002", "cntrctNm": "후보 B"},
            {"ntceNo": "2025-0001-00", "cntrctNm": "후보 A"},
        ]

        picked = _pick_best_g2b_contract_hit_by_bid_no(
            rows,
            bid_no="2025-0001",
            project_name_norm="프로젝트 A",
            pick_best_g2b_contract_hit_fn=lambda candidates, project_name_norm: candidates[0],
        )

        self.assertEqual(picked["cntrctNm"], "후보 A")


if __name__ == "__main__":
    unittest.main()
