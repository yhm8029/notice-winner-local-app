from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.services import artifact_files


class ArtifactFilePathTests(unittest.TestCase):
    def test_build_written_artifact_keeps_absolute_storage_path_outside_repo(self) -> None:
        temp_dir = Path(tempfile.gettempdir()) / "nwpw-tests-artifacts"
        temp_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = temp_dir / "outside-repo.json"
        artifact_path.write_text("{}", encoding="utf-8")
        try:
            written = artifact_files.build_written_artifact(
                absolute_path=artifact_path,
                mime_type="application/json",
                row_count=0,
            )

            self.assertEqual(written.storage_path, str(artifact_path).replace("\\", "/"))
        finally:
            artifact_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
