from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID


def build_artifact_item_payload(*, row: dict[str, Any], download_url: str, download_url_expires_in: int = 600) -> dict[str, Any]:
    return {
        "id": UUID(str(row["id"])),
        "artifact_type": str(row["artifact_type"]),
        "file_name": str(row["file_name"]),
        "mime_type": str(row["mime_type"]),
        "size_bytes": int(row.get("size_bytes") or 0),
        "checksum": str(row.get("checksum") or ""),
        "meta": dict(row.get("meta_json") or {}),
        "download_url": str(download_url),
        "download_url_expires_in": int(download_url_expires_in),
        "created_at": row["created_at"],
    }


def build_artifact_preview_payload_for_artifact_row(
    *,
    artifact_row: dict[str, Any],
    limit: int,
    resolve_artifact_path_fn: Any,
    build_artifact_preview_payload_fn: Any,
    unsupported_preview_fn: Any | None = None,
) -> dict[str, Any]:
    file_path = resolve_artifact_path_fn(str(artifact_row["storage_path"]))
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))
    return build_artifact_preview_payload_fn(
        artifact_type=str(artifact_row["artifact_type"]),
        file_path=file_path,
        limit=limit,
        unsupported_preview_fn=unsupported_preview_fn,
    )
