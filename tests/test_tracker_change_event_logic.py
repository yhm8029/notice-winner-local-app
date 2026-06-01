from __future__ import annotations

import unittest
from uuid import uuid4

from backend.services.tracker_change_event_logic import build_tracker_change_event
from backend.services.tracker_change_event_logic import build_tracker_change_event_dedupe_key
from backend.services.tracker_change_event_logic import TrackerEventBuildInput


class TrackerChangeEventLogicTests(unittest.TestCase):
    def test_build_tracker_change_event_skips_semantic_same_cost(self) -> None:
        event = build_tracker_change_event(
            TrackerEventBuildInput(
                organization_id=uuid4(),
                tracker_entry_id=uuid4(),
                event_type="field_updated_safe",
                field_name="construction_cost",
                old_value="1.2억원",
                new_value="120,000,000원",
                source_kind="tracker_export",
            )
        )
        self.assertIsNone(event)

    def test_dedupe_key_is_stable_for_same_inputs(self) -> None:
        tracker_entry_id = uuid4()
        source_run_id = uuid4()
        first = build_tracker_change_event_dedupe_key(
            tracker_entry_id=tracker_entry_id,
            event_type="field_filled",
            field_name="gross_area_scale",
            old_value_norm="",
            new_value_norm="4481.1",
            source_kind="tracker_export",
            source_run_id=source_run_id,
            source_ref="run-1",
            batch_key="tracker_export:run-1",
        )
        second = build_tracker_change_event_dedupe_key(
            tracker_entry_id=tracker_entry_id,
            event_type="field_filled",
            field_name="gross_area_scale",
            old_value_norm="",
            new_value_norm="4481.1",
            source_kind="tracker_export",
            source_run_id=source_run_id,
            source_ref="run-1",
            batch_key="tracker_export:run-1",
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
