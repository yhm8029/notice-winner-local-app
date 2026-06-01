from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from backend.services.artifact_files import WrittenArtifact


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACTS_ROOT = ROOT_DIR / "output" / "artifacts"


def ensure_run_artifact_dir(run_id: UUID) -> Path:
    raw_root = os.getenv("ARTIFACTS_ROOT", "").strip()
    if not raw_root:
        root = DEFAULT_ARTIFACTS_ROOT
    else:
        root = Path(raw_root).expanduser()
    path = root / str(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_artifact_path(storage_path: str) -> Path:
    path = Path(storage_path)
    if path.is_absolute():
        return path
    return ROOT_DIR / storage_path


def build_written_artifact(*, absolute_path: Path, mime_type: str, row_count: int) -> "WrittenArtifact":
    from backend.services.artifact_files import WrittenArtifact

    absolute_path = absolute_path.resolve()
    checksum = _sha256(absolute_path)
    storage_path = _artifact_storage_path(absolute_path)
    return WrittenArtifact(
        storage_path=storage_path,
        absolute_path=absolute_path,
        file_name=absolute_path.name,
        mime_type=mime_type,
        size_bytes=absolute_path.stat().st_size,
        checksum=checksum,
        row_count=row_count,
    )


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return sum(1 for _ in reader)


def _artifact_storage_path(absolute_path: Path) -> str:
    try:
        return str(absolute_path.relative_to(ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return str(absolute_path).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        while True:
            chunk = fp.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
