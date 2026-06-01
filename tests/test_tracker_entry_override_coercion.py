from __future__ import annotations

import unittest

from backend.repositories.in_memory_tracker_entries import InMemoryTrackerEntryRepository
from backend.repositories.tracker_entries import coerce_tracker_override_value


class TrackerEntryOverrideCoercionTests(unittest.TestCase):
    def test_coerce_construction_start_date_from_contract_date_input(self) -> None:
        value = coerce_tracker_override_value(
            field_name="construction_start_date",
            new_value="20250101",
            source_value="착수일로부터 90일",
            current_effective_value="착수일로부터 90일",
        )

        self.assertEqual(
            value,
            "계약일 2025-01-01 기준 90일 (완료예정 2025-04-01)",
        )

    def test_coerce_construction_start_date_preserves_non_date_override(self) -> None:
        value = coerce_tracker_override_value(
            field_name="construction_start_date",
            new_value="계약 확인 필요",
            source_value="착수일로부터 90일",
            current_effective_value="착수일로부터 90일",
        )

        self.assertEqual(value, "계약 확인 필요")

    def test_coerce_construction_start_date_uses_month_duration_when_present(self) -> None:
        value = coerce_tracker_override_value(
            field_name="construction_start_date",
            new_value="2025-01-01",
            source_value="착수일로부터 6개월",
            current_effective_value="착수일로부터 6개월",
        )

        self.assertEqual(
            value,
            "계약일 2025-01-01 기준 180일 (완료예정 2025-06-30)",
        )

    def test_in_memory_repository_applies_contract_date_override_to_construction_period(self) -> None:
        repository = InMemoryTrackerEntryRepository()
        entry_id = next(iter(repository._entries))
        repository._entries[entry_id]["construction_start_date_source"] = "착수일로부터 90일"

        result = repository.apply_override(
            entry_id=entry_id,
            field_name="construction_start_date",
            new_value="20250101",
            actor_user_id=None,
            actor_label="tester",
            change_source="web",
        )

        assert result is not None
        self.assertTrue(result.changed)
        self.assertEqual(
            result.entry["construction_start_date"],
            "계약일 2025-01-01 기준 90일 (완료예정 2025-04-01)",
        )


if __name__ == "__main__":
    unittest.main()
