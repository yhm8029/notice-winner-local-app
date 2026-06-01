from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.api import test_phase1_api


class ApiServerTempPathTests(unittest.TestCase):
    def test_build_test_tmp_path_defaults_under_system_temp_root(self) -> None:
        path = test_phase1_api._build_test_tmp_path("workspace", token="abc123")

        self.assertTrue(str(path).startswith(tempfile.gettempdir()))
        self.assertEqual(path, Path(tempfile.gettempdir()) / "nwpw-tests" / "abc123" / "workspace")

    def test_build_test_tmp_path_is_not_nested_under_repo_root(self) -> None:
        short_path = test_phase1_api._build_test_tmp_path("workspace", token="abc123")

        self.assertNotIn(str(test_phase1_api.ROOT_DIR), str(short_path))


if __name__ == "__main__":
    unittest.main()
