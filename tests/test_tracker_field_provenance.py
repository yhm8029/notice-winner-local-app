from __future__ import annotations

import unittest

from backend.services.tracker_field_provenance import build_tracker_field_diagnostic
from backend.services.tracker_field_provenance import classify_tracker_field_missing


class TrackerFieldProvenanceTests(unittest.TestCase):
    def test_build_tracker_field_diagnostic_marks_confirmed_source_as_high_confidence(self) -> None:
        entry = {
            "project_name": "Demo Project",
            "architect_office": "Demo Architect",
            "overridden_fields": [],
        }
        winner_row = {
            "architect_office_source": "confirmed_contract_lookup",
            "source_type": "eais_web",
            "reason_code": "EAIS_CONTRACT_MATCH",
            "evidence_source": "eais:demo",
            "winner_name": "Demo Architect",
            "architect_office": "Demo Architect",
        }

        item = build_tracker_field_diagnostic(
            entry=entry,
            winner_row=winner_row,
            field_key="architect_office",
            field_label="설계사무소",
            source_field_name="architect_office_source",
        )

        self.assertEqual(item["source_key"], "confirmed_contract_lookup")
        self.assertEqual(item["confidence"], "high")
        self.assertFalse(item["is_missing"])
        self.assertFalse(item["is_overridden"])
        self.assertEqual(item["missing_reason_code"], "")

    def test_build_tracker_field_diagnostic_marks_manual_override(self) -> None:
        entry = {
            "project_name": "Demo Project",
            "construction_cost": "12억원",
            "overridden_fields": ["construction_cost"],
        }

        item = build_tracker_field_diagnostic(
            entry=entry,
            winner_row=None,
            field_key="construction_cost",
            field_label="공사비",
            source_field_name="notice_construction_cost_source",
        )

        self.assertEqual(item["source_key"], "manual_override")
        self.assertEqual(item["confidence"], "manual")
        self.assertFalse(item["is_missing"])
        self.assertTrue(item["is_overridden"])

    def test_classify_tracker_field_missing_returns_expected_blank(self) -> None:
        code, message = classify_tracker_field_missing(
            field_key="gross_area_scale",
            project_name="OO 제안서평가용역",
            winner_row=None,
            source_field_name="gross_area_scale_source",
        )

        self.assertEqual(code, "정상 빈값")
        self.assertTrue(message)


if __name__ == "__main__":
    unittest.main()
