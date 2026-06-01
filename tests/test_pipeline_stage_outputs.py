from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from backend.services.pipeline_stage_outputs import run_export_stage_for_run
from backend.services.pipeline_stage_outputs import run_rescan_stage_for_run


class PipelineStageOutputsTests(unittest.TestCase):
    def test_run_rescan_stage_for_run_passes_should_stop_to_native_rescan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "candidate.csv"
            output_csv = root / "internal_nav.csv"
            input_csv.write_text("bid_no,bid_ord\nR25BK00000001,000\n", encoding="utf-8-sig")
            output_csv.write_text("bid_no\nR25BK00000001\n", encoding="utf-8-sig")
            should_stop = lambda: False

            with patch(
                "backend.services.pipeline_stage_outputs.collect_candidates_csv_path_for_run",
                return_value=input_csv,
            ), patch(
                "backend.services.pipeline_stage_outputs.internal_nav_csv_path_for_run",
                return_value=output_csv,
            ), patch(
                "backend.services.pipeline_stage_outputs.run_internal_nav_native",
                return_value=None,
            ) as run_native, patch(
                "backend.services.pipeline_stage_outputs._count_csv_rows",
                return_value=1,
            ):
                output = run_rescan_stage_for_run(
                    run_id=uuid4(),
                    params={},
                    filter_backend="native_filter",
                    should_stop=should_stop,
                )

        self.assertEqual(output.row_count, 1)
        self.assertEqual(output.stage_backend, "native_rescan")
        self.assertIs(run_native.call_args.kwargs["should_stop"], should_stop)

    def test_run_export_stage_for_run_passes_should_stop_to_native_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_csv = root / "internal_nav.csv"
            output_csv = root / "winner.csv"
            input_csv.write_text("bid_no,bid_ord\nR25BK00000001,000\n", encoding="utf-8-sig")
            output_csv.write_text("bid_no\nR25BK00000001\n", encoding="utf-8-sig")
            should_stop = lambda: False

            with patch(
                "backend.services.pipeline_stage_outputs.internal_nav_csv_path_for_run",
                return_value=input_csv,
            ), patch(
                "backend.services.pipeline_stage_outputs.post_collect_csv_path_for_run",
                return_value=output_csv,
            ), patch(
                "backend.services.pipeline_stage_outputs.run_post_collect_native",
                return_value=output_csv,
            ) as run_native, patch(
                "backend.services.pipeline_stage_outputs._count_csv_rows",
                return_value=1,
            ), patch(
                "backend.services.pipeline_stage_outputs._first_csv_value",
                return_value="R25BK00000001",
            ):
                output = run_export_stage_for_run(
                    run_id=uuid4(),
                    params={"_advanced_options": {"export_row_workers": 1}},
                    rescan_backend="native_rescan",
                    should_stop=should_stop,
                )

        self.assertEqual(output.row_count, 1)
        self.assertEqual(output.stage_backend, "native_export")
        self.assertIs(run_native.call_args.kwargs["should_stop"], should_stop)


if __name__ == "__main__":
    unittest.main()
