from __future__ import annotations

import unittest
from datetime import timezone

from backend.repositories.supabase_sales_claims import _normalize_iso_datetime_literal
from backend.repositories.supabase_sales_claims import _parse_datetime_nullable


class SupabaseSalesClaimDatetimeTests(unittest.TestCase):
    def test_normalize_iso_datetime_literal_pads_fractional_seconds(self) -> None:
        self.assertEqual(
            _normalize_iso_datetime_literal("2026-03-20T22:59:05.74814+00:00"),
            "2026-03-20T22:59:05.748140+00:00",
        )

    def test_parse_datetime_nullable_accepts_short_fractional_offset_timestamp(self) -> None:
        parsed = _parse_datetime_nullable("2026-03-20T22:59:05.74814+00:00")

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.isoformat(), "2026-03-20T22:59:05.748140+00:00")


if __name__ == "__main__":
    unittest.main()
