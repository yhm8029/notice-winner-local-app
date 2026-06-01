from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from backend.services.native_tracker_backend import build_tracker_entries_from_winner_csv


class NativeTrackerAuxiliaryCostTests(unittest.TestCase):
    def test_build_tracker_entries_blanks_cost_for_auxiliary_service_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "winner.csv"
            with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "bid_no",
                        "bid_ord",
                        "title",
                        "notice_construction_cost",
                        "notice_construction_cost_source",
                        "demand_contact",
                        "demand_contact_source",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "bid_no": "R25BK00000001",
                        "bid_ord": "000",
                        "title": "제6회 서울식물원 식재설계 공모전 운영 대행용역",
                        "notice_construction_cost": "100,000,000원",
                        "notice_construction_cost_source": "confirmed_extracted",
                        "demand_contact": "",
                        "demand_contact_source": "",
                    }
                )

            rows = build_tracker_entries_from_winner_csv(
                winner_csv_path=csv_path,
                seed_csv_path=None,
            )

        self.assertEqual(rows[0]["construction_cost"], "")


if __name__ == "__main__":
    unittest.main()
