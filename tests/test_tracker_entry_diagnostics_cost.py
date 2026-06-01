from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.api.app import _annotate_tracker_entries_with_field_diagnostics


class TrackerEntryDiagnosticsCostTests(unittest.TestCase):
    def test_annotate_tracker_entries_with_field_diagnostics_includes_construction_cost(self) -> None:
        source_run_id = uuid4()
        entry = {
            "id": str(uuid4()),
            "source_run_id": str(source_run_id),
            "source_tracker_run_id": str(uuid4()),
            "source_bid_no": "R25BK00000077",
            "source_bid_ord": "000",
            "source_project_name_norm": "demo-project",
            "project_name": "Demo Project",
            "construction_cost": "12억원",
            "architect_office": "예시건축사사무소",
            "gross_area_scale": "1,000㎡",
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
                        "notice_construction_cost_source": "confirmed_extracted",
                        "notice_construction_cost": "1,200,000,000원",
                        "demand_contact_source": "fallback_seed_contact",
                        "source_type": "eais_web",
                        "reason_code": "EAIS_CONTRACT_MATCH",
                        "evidence_source": "eais:demo-project|서울특별시",
                        "winner_name": "예시건축사사무소",
                    }
                },
                {},
            ),
        ):
            rows = _annotate_tracker_entries_with_field_diagnostics([entry])

        diagnostics = {item["field_key"]: item for item in rows[0]["field_diagnostics"]}
        self.assertEqual(diagnostics["construction_cost"]["source_label"], "첨부문서 직접 추출")
        self.assertEqual(diagnostics["construction_cost"]["source_type_label"], "EAIS")
        self.assertIn("value=1,200,000,000원", diagnostics["construction_cost"]["evidence_preview"])


if __name__ == "__main__":
    unittest.main()
