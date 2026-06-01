from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _annotate_tracker_entries_with_field_diagnostics


class TrackerEntryDiagnosticsTests(unittest.TestCase):
    def test_annotate_tracker_entries_with_field_diagnostics_uses_winner_row_metadata(self) -> None:
        source_run_id = uuid4()
        source_tracker_run_id = uuid4()
        entry = {
            "id": str(uuid4()),
            "source_run_id": str(source_run_id),
            "source_tracker_run_id": str(source_tracker_run_id),
            "source_bid_no": "R25BK00000077",
            "source_bid_ord": "000",
            "source_project_name_norm": "demo-project",
            "project_name": "Demo Project",
            "architect_office": "아이디어스건축사사무소",
            "gross_area_scale": "1000㎡",
            "demand_contact": "총무과/02-0000-0000",
            "overridden_fields": [],
        }

        with patch(
            "backend.api.app._load_winner_index_by_run",
            return_value=(
                {
                    ("R25BK00000077", "000", "demo-project"): {
                        "architect_office_source": "confirmed_contract_lookup",
                        "gross_area_scale_source": "confirmed_extracted",
                        "demand_contact_source": "fallback_seed_contact",
                        "source_type": "eais_web",
                        "reason_code": "EAIS_CONTRACT_MATCH",
                        "evidence_source": "eais:demo-project|서울특별시",
                        "winner_name": "아이디어스건축사사무소",
                    }
                },
                {},
            ),
        ):
            rows = _annotate_tracker_entries_with_field_diagnostics([entry])

        self.assertEqual(rows[0]["source_type"], "eais_web")
        self.assertEqual(rows[0]["architect_office_source"], "confirmed_contract_lookup")
        diagnostics = {item["field_key"]: item for item in rows[0]["field_diagnostics"]}
        self.assertEqual(diagnostics["architect_office"]["source_label"], "계약조회 당선사 확정")
        self.assertEqual(diagnostics["architect_office"]["source_type_label"], "EAIS")
        self.assertIn("winner_name=아이디어스건축사사무소", diagnostics["architect_office"]["evidence_preview"])


if __name__ == "__main__":
    unittest.main()
