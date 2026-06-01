from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "http_smoke_test.py"
SPEC = importlib.util.spec_from_file_location("http_smoke_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
http_smoke_test = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(http_smoke_test)


class HttpSmokeTestScriptTests(unittest.TestCase):
    def test_has_supabase_rest_config_requires_url_and_api_key(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(http_smoke_test.has_supabase_rest_config())

        with mock.patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://example.supabase.co"},
            clear=True,
        ):
            self.assertFalse(http_smoke_test.has_supabase_rest_config())

        with mock.patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SECRET_KEY": "secret-key",
            },
            clear=True,
        ):
            self.assertTrue(http_smoke_test.has_supabase_rest_config())

    def test_record_artifact_cleanup_metadata_captures_storage_paths(self) -> None:
        artifact_ids: list[str] = []
        storage_paths: list[str] = []

        http_smoke_test.record_artifact_cleanup_metadata(
            [
                {"id": "artifact-1", "storage_path": "output/artifacts/run-1/winner.csv"},
                {"id": "artifact-2"},
            ],
            artifact_ids,
            storage_paths,
        )

        self.assertEqual(artifact_ids, ["artifact-1", "artifact-2"])
        self.assertEqual(storage_paths, ["output/artifacts/run-1/winner.csv"])


if __name__ == "__main__":
    unittest.main()
