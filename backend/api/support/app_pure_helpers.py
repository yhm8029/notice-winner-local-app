from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from backend.api.support.run_support import _json_default
from backend.api.support.run_support import resolve_artifact_path
from backend.api.support.tracker_read_support import _parse_iso_datetime
from backend.services.related_notice_query_runtime import RELATED_NOTICE_PRECOMPUTE_STALE_SEC
from backend.services.related_notice_response_backend import is_related_notice_precompute_stale as _is_related_notice_precompute_stale_impl


def load_json_artifact_payload(storage_path: str) -> dict[str, Any] | list[Any] | None:
    artifact_path = resolve_artifact_path(storage_path)
    if not artifact_path.exists():
        return None
    try:
        with artifact_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return None


def _load_json_artifact_payload(storage_path: str) -> dict[str, Any] | list[Any] | None:
    return load_json_artifact_payload(storage_path)


def parse_yyyymmdd(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if len(raw) == 8 and raw.isdigit():
        try:
            return datetime.strptime(raw, "%Y%m%d")
        except ValueError:
            return None
    if len(raw) >= 10 and raw[:10].replace("-", "").isdigit():
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return None


def _parse_yyyymmdd(value: str) -> datetime | None:
    return parse_yyyymmdd(value)


def format_yyyymmdd(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        parsed = parse_yyyymmdd(value)
        return parsed.strftime("%Y%m%d") if parsed else str(value or "").strip()
    try:
        return value.strftime("%Y%m%d")
    except Exception:
        return str(value or "").strip()


def _format_yyyymmdd(value: Any) -> str:
    return format_yyyymmdd(value)


def json_safe_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, default=_json_default))


def _json_safe_copy(value: Any) -> Any:
    return json_safe_copy(value)


def is_related_notice_precompute_stale(
    run_row: dict[str, Any],
    precompute_status: str,
    *,
    updated_at: Any = None,
) -> bool:
    return _is_related_notice_precompute_stale_impl(
        run_row,
        precompute_status,
        updated_at=updated_at,
        parse_iso_datetime_fn=_parse_iso_datetime,
        stale_sec=RELATED_NOTICE_PRECOMPUTE_STALE_SEC,
    )
