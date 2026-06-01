from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.phase1_defaults import load_phase1_identity
from backend.repositories.in_memory_backfill_conflicts import InMemoryBackfillConflictRepository
from backend.repositories.in_memory_tracker_change_events import InMemoryTrackerChangeEventRepository
from backend.repositories.in_memory_tracker_entries import InMemoryTrackerEntryRepository
from scripts.apply_core_field_backfill import _execute_plan
from scripts.apply_core_field_backfill import _plan_row


def _seed_tracker_entry(repository: InMemoryTrackerEntryRepository) -> dict[str, object]:
    source_run_id = uuid4()
    source_tracker_run_id = uuid4()
    return repository.upsert_source_entries(
        source_run_id=source_run_id,
        source_tracker_run_id=source_tracker_run_id,
        entries=[
            {
                "entry_key": "r25bk00000001|000|sample-project",
                "sheet_name": "tracker",
                "section_name": "main",
                "row_no": 1,
                "source_bid_no": "R25BK00000001",
                "source_bid_ord": "000",
                "source_project_name_norm": "sample-project",
                "project_name": "Sample Project",
                "gross_area_scale": "",
                "construction_cost": "",
                "demand_org_name": "Sample Org",
                "demand_contact": "",
                "client_location": "부산광역시",
                "site_location_1": "부산광역시",
                "site_location_2": "",
                "architect_office": "",
                "opening_scheduled_date": "",
                "contract_date": "",
                "construction_duration_days": "",
                "completion_expected_date_explicit": "",
                "completion_expected_date_computed": "",
                "construction_start_date": "",
                "last_checked_date": "",
                "progress_note": "",
                "notice_date": "",
                "manager_name": "",
                "building_automation_estimated_amount": "",
            }
        ],
    )[0]


class ApplyCoreFieldBackfillTests(unittest.TestCase):
    def test_plan_row_marks_safe_fill_as_override(self) -> None:
        planned = _plan_row(
            {"field_name": "construction_cost", "action": "safe_fill_blank"},
            allowed_actions={"safe_fill_blank"},
        )
        self.assertEqual(planned["apply_mode"], "override")
        self.assertEqual(planned["plan_status"], "planned")

    def test_plan_row_marks_conflict_for_review_conflict(self) -> None:
        planned = _plan_row(
            {"field_name": "gross_area_scale", "action": "review_conflict"},
            allowed_actions={"review_conflict"},
        )
        self.assertEqual(planned["apply_mode"], "conflict")
        self.assertEqual(planned["plan_status"], "planned")

    def test_execute_plan_records_conflict_without_overwrite(self) -> None:
        tracker_repository = InMemoryTrackerEntryRepository()
        conflict_repository = InMemoryBackfillConflictRepository()
        change_event_repository = InMemoryTrackerChangeEventRepository()
        entry = _seed_tracker_entry(tracker_repository)
        entry_id = str(entry["id"])
        tracker_repository.apply_override(
            entry_id=entry["id"],
            field_name="construction_cost",
            new_value="120,000,000원",
            actor_user_id=None,
            actor_label="tester",
            change_source="system",
        )
        row = {
            "entry_id": entry_id,
            "field_name": "construction_cost",
            "candidate_value": "240,000,000원",
            "action": "review_conflict",
            "plan_status": "planned",
            "apply_mode": "conflict",
            "current_value": "120,000,000원",
            "current_value_norm": "120000000",
            "candidate_value_norm": "240000000",
            "reason_code": "valid_nonblank_conflict",
            "candidate_source_kind": "tracker_export",
            "candidate_source_ref": "run-1",
            "run_id": str(uuid4()),
        }

        with (
            patch("scripts.apply_core_field_backfill.get_tracker_entry_repository", return_value=tracker_repository),
            patch("scripts.apply_core_field_backfill.get_backfill_conflict_repository", return_value=conflict_repository),
            patch("scripts.apply_core_field_backfill.get_tracker_change_event_repository", return_value=change_event_repository),
        ):
            results = _execute_plan([row], actor_label="safe_backfill_test", change_source="system")

        self.assertEqual(results[0]["execute_status"], "conflict_recorded")
        conflict_rows = conflict_repository.upsert_conflicts(
            organization_id=load_phase1_identity().organization_id,
            conflicts=[],
        )
        self.assertEqual(conflict_rows, [])
        listed_conflicts = list(conflict_repository._rows_by_id.values())  # type: ignore[attr-defined]
        self.assertEqual(len(listed_conflicts), 1)
        self.assertEqual(str(listed_conflicts[0]["tracker_entry_id"]), entry_id)
        self.assertEqual(change_event_repository.count_unread(organization_id=load_phase1_identity().organization_id), 0)


if __name__ == "__main__":
    unittest.main()
