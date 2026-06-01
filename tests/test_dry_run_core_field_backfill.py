from __future__ import annotations

import unittest

from scripts.dry_run_core_field_backfill import _resolve_apply_mode


class DryRunCoreFieldBackfillTests(unittest.TestCase):
    def test_resolve_apply_mode_marks_safe_fill_as_override(self) -> None:
        self.assertEqual(_resolve_apply_mode("gross_area_scale", "safe_fill_blank"), "override")

    def test_resolve_apply_mode_marks_safe_replace_as_override(self) -> None:
        self.assertEqual(_resolve_apply_mode("construction_cost", "safe_replace_implausible_current"), "override")

    def test_resolve_apply_mode_marks_conflict_as_conflict(self) -> None:
        self.assertEqual(_resolve_apply_mode("demand_contact", "review_conflict"), "conflict")

    def test_resolve_apply_mode_skips_unsupported_fields(self) -> None:
        self.assertEqual(_resolve_apply_mode("architect_office", "safe_fill_blank"), "skip")


if __name__ == "__main__":
    unittest.main()
