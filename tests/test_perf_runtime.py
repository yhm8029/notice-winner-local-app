from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.perf_runtime import ensure_request_id
from backend.perf_runtime import measure_stage


class PerfRuntimeTests(unittest.TestCase):
    def test_ensure_request_id_sets_and_reuses_value(self) -> None:
        request = SimpleNamespace(state=SimpleNamespace())

        first = ensure_request_id(request)
        second = ensure_request_id(request)

        self.assertTrue(first)
        self.assertEqual(first, second)

    def test_measure_stage_logs_info_for_fast_stage(self) -> None:
        with patch("backend.perf_runtime.time.perf_counter", side_effect=[10.0, 10.05]), patch(
            "backend.perf_runtime.STAGE_PERF_LOGGER.info"
        ) as info_mock, patch("backend.perf_runtime.STAGE_PERF_LOGGER.warning") as warning_mock:
            with measure_stage("tracker_entry_detail.load_entry", entry_id="entry-1"):
                pass

        info_mock.assert_called_once()
        warning_mock.assert_not_called()

    def test_measure_stage_logs_warning_for_slow_stage(self) -> None:
        with patch("backend.perf_runtime.time.perf_counter", side_effect=[10.0, 10.5]), patch(
            "backend.perf_runtime.STAGE_PERF_LOGGER.info"
        ) as info_mock, patch("backend.perf_runtime.STAGE_PERF_LOGGER.warning") as warning_mock:
            with measure_stage("tracker_entry_detail.normalize_presentation", entry_id="entry-1"):
                pass

        warning_mock.assert_called_once()
        info_mock.assert_not_called()

if __name__ == "__main__":
    unittest.main()
