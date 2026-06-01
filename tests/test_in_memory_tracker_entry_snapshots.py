from __future__ import annotations

import unittest
from uuid import uuid4

from backend.repositories.in_memory_tracker_entry_snapshots import InMemoryTrackerEntrySnapshotRepository


class InMemoryTrackerEntrySnapshotRepositoryTests(unittest.TestCase):
    def test_upsert_and_get_snapshots_roundtrip(self) -> None:
        repository = InMemoryTrackerEntrySnapshotRepository()
        organization_id = uuid4()
        tracker_entry_id = uuid4()

        repository.upsert_snapshots(
            organization_id=organization_id,
            snapshots=[
                {
                    "tracker_entry_id": tracker_entry_id,
                    "summary_json": {"id": str(tracker_entry_id), "project_name": "테스트 프로젝트"},
                    "detail_json": {"id": str(tracker_entry_id), "project_name": "테스트 프로젝트", "field_diagnostics": []},
                    "export_json": {"project_name": "테스트 프로젝트"},
                }
            ],
        )

        rows = repository.get_snapshots(
            organization_id=organization_id,
            tracker_entry_ids=[tracker_entry_id],
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["summary_json"]["project_name"], "테스트 프로젝트")
        self.assertEqual(rows[0]["detail_json"]["id"], str(tracker_entry_id))


if __name__ == "__main__":
    unittest.main()
