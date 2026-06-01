from __future__ import annotations

import unittest
from unittest.mock import Mock
from uuid import uuid4

from backend.services.tracker_contact_resolution_backend import build_tracker_contact_resolution_summary


class TrackerContactResolutionBackendTests(unittest.TestCase):
    def test_build_summary_counts_statuses_and_reasons(self) -> None:
        source_run_id = uuid4()
        tracker_run_id = uuid4()
        entries = [
            {
                "id": uuid4(),
                "source_run_id": source_run_id,
                "source_tracker_run_id": tracker_run_id,
                "project_name": "Resolved Project",
                "demand_org_name": "Org A",
                "demand_contact": "시설과/02-1111-1111",
                "updated_at": "2026-04-05T00:00:00Z",
            },
            {
                "id": uuid4(),
                "source_run_id": source_run_id,
                "source_tracker_run_id": tracker_run_id,
                "project_name": "Review Project",
                "demand_org_name": "Org B",
                "demand_contact": "",
                "updated_at": "2026-04-05T00:01:00Z",
            },
            {
                "id": uuid4(),
                "source_run_id": source_run_id,
                "source_tracker_run_id": tracker_run_id,
                "project_name": "No Owner Project",
                "demand_org_name": "Org C",
                "demand_contact": "",
                "updated_at": "2026-04-05T00:02:00Z",
            },
            {
                "id": uuid4(),
                "source_run_id": source_run_id,
                "source_tracker_run_id": tracker_run_id,
                "project_name": "Missing Project",
                "demand_org_name": "Org D",
                "demand_contact": "",
                "updated_at": "2026-04-05T00:03:00Z",
            },
        ]
        lookup = Mock(
            side_effect=[
                {
                    "demand_contact_resolution_status": "resolved",
                    "demand_contact_resolution_reason": "explicit_owner_org_match",
                    "demand_contact_resolution_phase": "notice",
                    "demand_contact_resolution_role": "owner_contact",
                    "demand_contact_resolution_owner_side": "yes",
                    "demand_contact_resolution_owner_side_basis": "explicit_owner_org_match",
                },
                {
                    "demand_contact_resolution_status": "review",
                    "demand_contact_resolution_reason": "multiple_owner_candidates",
                },
                {
                    "demand_contact_resolution_status": "no_owner_candidate",
                    "demand_contact_resolution_reason": "management_only",
                },
                None,
            ]
        )

        payload = build_tracker_contact_resolution_summary(
            entries=entries,
            limit=10,
            load_winner_index_by_run_fn=lambda run_id: ({}, {}),
            lookup_winner_row_for_entry_fn=lookup,
            coerce_uuid_or_none_fn=lambda value: value,
            source_run_id=source_run_id,
        )

        self.assertEqual(payload["total_entries"], 4)
        self.assertEqual(
            payload["status_counts"],
            [
                {"status": "resolved", "count": 1},
                {"status": "review", "count": 1},
                {"status": "no_owner_candidate", "count": 1},
                {"status": "missing", "count": 1},
            ],
        )
        self.assertEqual(
            payload["reason_counts"],
            [
                {"reason": "explicit_owner_org_match", "count": 1},
                {"reason": "management_only", "count": 1},
                {"reason": "multiple_owner_candidates", "count": 1},
            ],
        )
        self.assertEqual(payload["items"][0]["resolution_status"], "resolved")
        self.assertEqual(payload["items"][1]["resolution_reason"], "multiple_owner_candidates")
        self.assertEqual(payload["items"][3]["resolution_status"], "missing")

    def test_build_summary_filters_by_tracker_run_id(self) -> None:
        included_tracker_run_id = uuid4()
        other_tracker_run_id = uuid4()
        lookup = Mock(return_value={"demand_contact_resolution_status": "resolved"})

        payload = build_tracker_contact_resolution_summary(
            entries=[
                {"id": uuid4(), "source_run_id": uuid4(), "source_tracker_run_id": included_tracker_run_id, "project_name": "Included"},
                {"id": uuid4(), "source_run_id": uuid4(), "source_tracker_run_id": other_tracker_run_id, "project_name": "Excluded"},
            ],
            limit=10,
            load_winner_index_by_run_fn=lambda run_id: ({}, {}),
            lookup_winner_row_for_entry_fn=lookup,
            coerce_uuid_or_none_fn=lambda value: value,
            source_tracker_run_id=included_tracker_run_id,
        )

        self.assertEqual(payload["total_entries"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["project_name"], "Included")


if __name__ == "__main__":
    unittest.main()
