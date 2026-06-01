from __future__ import annotations

import unittest

from backend.services.backfill_policy import classify_construction_cost_backfill
from backend.services.backfill_policy import classify_demand_contact_backfill


class BackfillPolicyTests(unittest.TestCase):
    def test_manual_value_is_protected_from_backfill(self) -> None:
        decision = classify_construction_cost_backfill(
            current_value="120,000,000원",
            candidate_value="240,000,000원",
            current_entry={"overridden_fields": ["construction_cost"]},
            candidate_source_type="tracker_export",
            candidate_source_ref="run-1",
        )
        self.assertEqual(decision.action, "skip")
        self.assertEqual(decision.reason_code, "manual_protected")

    def test_valid_nonblank_contact_is_not_overwritten(self) -> None:
        decision = classify_demand_contact_backfill(
            current_value="행정실/051-123-4567",
            candidate_value="시설팀/051-222-3333",
            current_entry={"overridden_fields": []},
            candidate_source_type="tracker_export",
            candidate_source_ref="run-1",
        )
        self.assertEqual(decision.action, "review_conflict")
        self.assertEqual(decision.reason_code, "valid_contact_protected")


if __name__ == "__main__":
    unittest.main()
