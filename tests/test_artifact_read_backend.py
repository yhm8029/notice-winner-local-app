from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import unittest
from unittest.mock import patch

from backend.api import app as api_app
from backend.api.app import ApiError
from backend.services.artifact_read_backend import build_artifact_item_payload
from backend.services.artifact_read_backend import build_artifact_preview_payload_for_artifact_row


class ArtifactReadBackendTests(unittest.TestCase):
    def test_build_artifact_item_payload_applies_defaults_and_download_url(self) -> None:
        created_at = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)
        row = {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "artifact_type": "winner_csv",
            "file_name": "winner.csv",
            "mime_type": "text/csv",
            "size_bytes": None,
            "checksum": None,
            "meta_json": None,
            "created_at": created_at,
        }

        payload = build_artifact_item_payload(
            row=row,
            download_url="http://example.test/api/artifacts/11111111-1111-1111-1111-111111111111/download",
        )

        self.assertEqual(payload["id"], row["id"])
        self.assertEqual(payload["artifact_type"], "winner_csv")
        self.assertEqual(payload["file_name"], "winner.csv")
        self.assertEqual(payload["mime_type"], "text/csv")
        self.assertEqual(payload["size_bytes"], 0)
        self.assertEqual(payload["checksum"], "")
        self.assertEqual(payload["meta"], {})
        self.assertEqual(
            payload["download_url"],
            "http://example.test/api/artifacts/11111111-1111-1111-1111-111111111111/download",
        )
        self.assertEqual(payload["download_url_expires_in"], 600)
        self.assertEqual(payload["created_at"], created_at)

    def test_build_artifact_preview_payload_for_artifact_row_resolves_storage_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = "runs/abc/winner.csv"
            resolved_path = Path(tmp_dir) / storage_path
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path.write_text("name\nalpha\n", encoding="utf-8")
            resolve_calls: list[str] = []
            preview_calls: list[tuple[str, Path, int, object | None]] = []
            unsupported_preview_fn = object()

            def resolve_artifact_path_fn(value: str) -> Path:
                resolve_calls.append(value)
                return resolved_path

            def build_artifact_preview_payload_fn(
                *,
                artifact_type: str,
                file_path: Path,
                limit: int,
                unsupported_preview_fn: object | None = None,
            ) -> dict[str, object]:
                preview_calls.append((artifact_type, file_path, limit, unsupported_preview_fn))
                return {
                    "artifact_type": artifact_type,
                    "file_path": str(file_path),
                    "limit": limit,
                }

            payload = build_artifact_preview_payload_for_artifact_row(
                artifact_row={
                    "artifact_type": "winner_csv",
                    "storage_path": storage_path,
                },
                limit=4,
                resolve_artifact_path_fn=resolve_artifact_path_fn,
                build_artifact_preview_payload_fn=build_artifact_preview_payload_fn,
                unsupported_preview_fn=unsupported_preview_fn,
            )

            self.assertEqual(resolve_calls, [storage_path])
            self.assertEqual(
                preview_calls,
                [("winner_csv", resolved_path, 4, unsupported_preview_fn)],
            )
            self.assertEqual(
                payload,
                {
                    "artifact_type": "winner_csv",
                    "file_path": str(resolved_path),
                    "limit": 4,
                },
            )

    def test_build_artifact_preview_payload_for_artifact_row_raises_for_missing_file_before_unsupported_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = Path(tmp_dir) / "missing.bin"
            resolve_calls: list[str] = []
            preview_calls: list[tuple[str, Path, int, object | None]] = []

            def resolve_artifact_path_fn(value: str) -> Path:
                resolve_calls.append(value)
                return missing_path

            def build_artifact_preview_payload_fn(
                *,
                artifact_type: str,
                file_path: Path,
                limit: int,
                unsupported_preview_fn: object | None = None,
            ) -> dict[str, object]:
                preview_calls.append((artifact_type, file_path, limit, unsupported_preview_fn))
                raise AssertionError("unsupported preview should not be reached before missing file")

            with self.assertRaises(FileNotFoundError):
                build_artifact_preview_payload_for_artifact_row(
                    artifact_row={
                        "artifact_type": "unsupported_artifact",
                        "storage_path": "runs/abc/missing.bin",
                    },
                    limit=4,
                    resolve_artifact_path_fn=resolve_artifact_path_fn,
                    build_artifact_preview_payload_fn=build_artifact_preview_payload_fn,
                    unsupported_preview_fn=object(),
                )

            self.assertEqual(resolve_calls, ["runs/abc/missing.bin"])
            self.assertEqual(preview_calls, [])

    def test_artifact_download_and_preview_require_visible_owning_run(self) -> None:
        artifact_id = UUID("22222222-2222-2222-2222-222222222222")
        run_id = UUID("33333333-3333-3333-3333-333333333333")
        artifact_row = {
            "id": artifact_id,
            "run_id": run_id,
            "artifact_type": "unsupported_artifact",
            "file_name": "hidden.bin",
            "mime_type": "application/octet-stream",
            "storage_path": "runs/hidden/hidden.bin",
            "created_at": datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc),
        }
        hidden_run_row = {
            "id": run_id,
            "status": "success",
            "run_type": "project_tracker",
            "created_at": datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc),
        }

        class _ArtifactRepository:
            def __init__(self) -> None:
                self.requested_ids: list[UUID] = []

            def get_artifact(self, requested_id: UUID) -> dict[str, object]:
                self.requested_ids.append(requested_id)
                return artifact_row

        class _RunRepository:
            def __init__(self) -> None:
                self.requested_ids: list[UUID] = []

            def get_run(self, requested_id: UUID) -> dict[str, object]:
                self.requested_ids.append(requested_id)
                return hidden_run_row

        artifact_repository = _ArtifactRepository()
        run_repository = _RunRepository()

        with patch("backend.api.app._get_artifact_repository", return_value=artifact_repository), patch(
            "backend.api.app._get_run_repository",
            return_value=run_repository,
        ), patch("backend.api.app._run_visible_in_operational_views", return_value=False), patch(
            "backend.api.app.resolve_artifact_path",
            side_effect=AssertionError("file resolution should not happen before visibility check"),
        ), patch(
            "backend.api.app._build_artifact_preview_payload",
            side_effect=AssertionError("preview shaping should not happen before visibility check"),
        ):
            with self.assertRaises(ApiError) as download_error:
                api_app.download_artifact(artifact_id)
            self.assertEqual(download_error.exception.status_code, 404)

            with self.assertRaises(ApiError) as preview_error:
                api_app.preview_artifact(artifact_id)
            self.assertEqual(preview_error.exception.status_code, 404)

        self.assertEqual(artifact_repository.requested_ids, [artifact_id, artifact_id])
        self.assertEqual(run_repository.requested_ids, [run_id, run_id])


if __name__ == "__main__":
    unittest.main()
