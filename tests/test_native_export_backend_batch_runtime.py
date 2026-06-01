from __future__ import annotations

import csv
import tempfile
import time
import unittest
from pathlib import Path

from backend.services.native_export_backend_batch_runtime import load_grouped_items
from backend.services.native_export_backend_batch_runtime import process_grouped_items_parallel
from backend.services.native_export_backend_batch_runtime import write_output_rows


class NativeExportBackendBatchRuntimeTests(unittest.TestCase):
    def test_load_grouped_items_groups_rows_by_bid_no_and_bid_ord(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_csv = Path(temp_dir) / "internal_nav.csv"
            with input_csv.open("w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=["bid_no", "bid_ord", "value"])
                writer.writeheader()
                writer.writerows(
                    [
                        {"bid_no": "A", "bid_ord": "", "value": "1"},
                        {"bid_no": "A", "bid_ord": "000", "value": "2"},
                        {"bid_no": "B", "bid_ord": "001", "value": "3"},
                    ]
                )

            grouped_items = load_grouped_items(input_csv)

        self.assertEqual(len(grouped_items), 2)
        self.assertEqual(grouped_items[0][0], ("A", "000"))
        self.assertEqual(len(grouped_items[0][1]), 2)
        self.assertEqual(grouped_items[1][0], ("B", "001"))

    def test_process_grouped_items_parallel_preserves_index_order_and_progress(self) -> None:
        progress_messages: list[str] = []
        grouped_items = [
            (("A", "000"), [{"bid_no": "A"}]),
            (("B", "000"), [{"bid_no": "B"}]),
        ]

        def _build_output_row_fn(*, group_item, llm_config, use_llm, should_stop):
            bid_no = group_item[0][0]
            if bid_no == "A":
                time.sleep(0.05)
            return {"bid_no": bid_no, "rank": "1"}, f"done:{bid_no}", False

        rows = process_grouped_items_parallel(
            grouped_items=grouped_items,
            worker_count=2,
            build_output_row_fn=_build_output_row_fn,
            llm_config=object(),
            progress_cb=progress_messages.append,
            should_stop=None,
            raise_if_stop_requested_fn=lambda _should_stop: None,
        )

        self.assertEqual([row["bid_no"] for row in rows], ["A", "B"])
        self.assertCountEqual(progress_messages, ["done:A", "done:B"])

    def test_write_output_rows_creates_parent_and_writes_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_csv = Path(temp_dir) / "nested" / "winner.csv"
            write_output_rows(output_csv, [{"bid_no": "A", "bid_ord": "000", "rank": "1"}])

            with output_csv.open("r", encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.DictReader(fp))

        self.assertEqual(rows[0]["bid_no"], "A")
        self.assertEqual(rows[0]["rank"], "1")


if __name__ == "__main__":
    unittest.main()
