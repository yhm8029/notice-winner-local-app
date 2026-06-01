from __future__ import annotations

import unittest
from uuid import uuid4

from backend.repositories.in_memory_tracker_change_events import InMemoryTrackerChangeEventRepository


class InMemoryTrackerChangeEventRepositoryTests(unittest.TestCase):
    def test_count_unread_excludes_silent_events(self) -> None:
        repository = InMemoryTrackerChangeEventRepository()
        organization_id = uuid4()
        tracker_entry_id = uuid4()
        repository.append_events(
            organization_id=organization_id,
            events=[
                {
                    "tracker_entry_id": tracker_entry_id,
                    "event_type": "field_filled",
                    "field_name": "gross_area_scale",
                    "old_value": "",
                    "new_value": "4,481.1㎡",
                    "old_value_norm": "",
                    "new_value_norm": "4481.1",
                    "source_kind": "tracker_export",
                    "dedupe_key": "non-silent",
                    "is_silent": False,
                },
                {
                    "tracker_entry_id": tracker_entry_id,
                    "event_type": "field_updated_safe",
                    "field_name": "construction_cost",
                    "old_value": "50억원",
                    "new_value": "184.07억원",
                    "old_value_norm": "5000000000",
                    "new_value_norm": "18407000000",
                    "source_kind": "backfill",
                    "dedupe_key": "silent",
                    "is_silent": True,
                },
            ],
        )

        self.assertEqual(repository.count_unread(organization_id=organization_id), 1)


if __name__ == "__main__":
    unittest.main()
