from __future__ import annotations

from unittest import TestCase
from uuid import uuid4

from backend.repositories.in_memory_backfill_conflicts import InMemoryBackfillConflictRepository


class InMemoryBackfillConflictRepositoryTests(TestCase):
    def test_list_open_and_resolve_conflict(self) -> None:
        repository = InMemoryBackfillConflictRepository()
        organization_id = uuid4()
        tracker_entry_id = uuid4()
        rows = repository.upsert_conflicts(
            organization_id=organization_id,
            conflicts=[
                {
                    "tracker_entry_id": tracker_entry_id,
                    "field_name": "demand_contact",
                    "current_value": "portal/02-6010-1022",
                    "candidate_value": "ops-team/02-555-1234",
                    "reason_code": "valid_contact_protected",
                    "source_kind": "backfill",
                    "conflict_key": f"{tracker_entry_id}:demand_contact:test",
                }
            ],
        )

        self.assertEqual(len(rows), 1)
        conflict_id = rows[0]["id"]
        self.assertEqual(len(repository.list_conflicts(organization_id=organization_id, limit=10)), 1)

        resolved = repository.resolve_conflict(
            organization_id=organization_id,
            conflict_id=conflict_id,
            resolution="dismissed",
        )

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["resolution"], "dismissed")
        self.assertIsNotNone(resolved["resolved_at"])
        self.assertEqual(len(repository.list_conflicts(organization_id=organization_id, limit=10)), 0)
        self.assertEqual(
            len(repository.list_conflicts(organization_id=organization_id, limit=10, include_resolved=True)),
            1,
        )
