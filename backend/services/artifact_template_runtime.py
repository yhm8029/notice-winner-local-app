from __future__ import annotations

import json
import os
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TRACKER_TEMPLATE_PATH = ROOT_DIR / "프로젝트 트래커 양식.xlsx"
LEGACY_TRACKER_TEMPLATE_PATH = ROOT_DIR / "assets" / "project_tracker_template.xlsx"
UPLOADED_TRACKER_TEMPLATE_PATH = ROOT_DIR / "input" / "uploaded_project_tracker_template.xlsx"
UPLOADED_TRACKER_TEMPLATE_META_PATH = ROOT_DIR / "input" / "uploaded_project_tracker_template.json"


def resolve_tracker_template_path() -> Path:
    candidate, _ = _resolve_tracker_template_candidate()
    return candidate


def describe_active_tracker_template() -> dict[str, Any]:
    candidate, source = _resolve_tracker_template_candidate()
    payload = {
        "source": source,
        "source_label": _tracker_template_source_label(source),
        "file_name": candidate.name,
        "original_file_name": candidate.name,
        "active_path": str(candidate),
        "size_bytes": int(candidate.stat().st_size),
        "updated_at": datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc).isoformat(),
    }
    meta_path = resolve_uploaded_tracker_template_meta_path()
    if source == "uploaded_override" and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        if isinstance(meta, dict):
            payload["original_file_name"] = str(meta.get("original_file_name") or candidate.name)
            if meta.get("uploaded_at"):
                payload["updated_at"] = str(meta["uploaded_at"])
    return payload


def clear_uploaded_tracker_template() -> dict[str, Any]:
    for path in (resolve_uploaded_tracker_template_path(), resolve_uploaded_tracker_template_meta_path()):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return describe_active_tracker_template()


def resolve_uploaded_tracker_template_path() -> Path:
    raw = os.getenv("TRACKER_TEMPLATE_UPLOAD_PATH", "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = ROOT_DIR / candidate
        return candidate
    return UPLOADED_TRACKER_TEMPLATE_PATH


def resolve_uploaded_tracker_template_meta_path(template_path: Path | None = None) -> Path:
    raw = os.getenv("TRACKER_TEMPLATE_UPLOAD_META_PATH", "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = ROOT_DIR / candidate
        return candidate
    candidate = template_path or resolve_uploaded_tracker_template_path()
    if candidate == UPLOADED_TRACKER_TEMPLATE_PATH:
        return UPLOADED_TRACKER_TEMPLATE_META_PATH
    return candidate.with_suffix(".json")


def _resolve_tracker_template_candidate() -> tuple[Path, str]:
    upload_path = resolve_uploaded_tracker_template_path()
    if upload_path.exists():
        return upload_path, "uploaded_override"

    raw = os.getenv("TRACKER_TEMPLATE_PATH", "").strip()
    if raw:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = ROOT_DIR / candidate
        if not candidate.exists():
            raise FileNotFoundError(f"tracker template not found: {candidate}")
        return candidate, "env_override"

    for candidate in (DEFAULT_TRACKER_TEMPLATE_PATH, LEGACY_TRACKER_TEMPLATE_PATH):
        if candidate.exists():
            source = "repo_default" if candidate == DEFAULT_TRACKER_TEMPLATE_PATH else "legacy_default"
            return candidate, source
    raise FileNotFoundError(f"tracker template not found: {DEFAULT_TRACKER_TEMPLATE_PATH}")


def _tracker_template_source_label(source: str) -> str:
    mapping = {
        "uploaded_override": "업로드한 서버 양식",
        "env_override": "TRACKER_TEMPLATE_PATH 설정값",
        "repo_default": "repo 루트 기본 양식",
        "legacy_default": "legacy assets 양식",
    }
    return mapping.get(source, source)
