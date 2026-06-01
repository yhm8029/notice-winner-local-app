from __future__ import annotations

import threading
from datetime import datetime
from datetime import timezone
from typing import Any


_PROGRESS_LOCK = threading.Lock()
_PROGRESS_BY_PROJECT_KEY: dict[str, dict[str, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _item_key(item: dict[str, Any]) -> str:
    return "::".join(
        (
            str(item.get("bid_no") or "").strip(),
            str(item.get("bid_ord") or "").strip(),
            str(item.get("project_name") or "").strip(),
        )
    )


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        key = _item_key(item)
        if not key.strip(":"):
            key = str(item.get("id") or "").strip()
        if not key:
            continue
        current = deduped.get(key)
        if current is None or int(item.get("match_score") or 0) > int(current.get("match_score") or 0):
            deduped[key] = dict(item)
    return list(deduped.values())


def start_related_notice_progress(
    *,
    project_key: str,
    project_name: str = "",
    project_search_name: str = "",
    run_id: str = "",
    status: str = "running",
    message: str = "연관 공고 검색을 시작했습니다.",
) -> dict[str, Any]:
    key = str(project_key or "").strip()
    if not key:
        return {}
    now = _utc_now_iso()
    payload = {
        "project_key": key,
        "project_name": str(project_name or ""),
        "project_search_name": str(project_search_name or ""),
        "run_id": str(run_id or ""),
        "status": str(status or "running"),
        "message": message,
        "items": [],
        "item_count": 0,
        "started_at": now,
        "updated_at": now,
        "completed_at": "",
    }
    with _PROGRESS_LOCK:
        _PROGRESS_BY_PROJECT_KEY[key] = dict(payload)
    return dict(payload)


def update_related_notice_progress(
    *,
    project_key: str,
    items: list[dict[str, Any]] | None = None,
    project_name: str = "",
    project_search_name: str = "",
    run_id: str = "",
    status: str = "running",
    message: str = "",
) -> dict[str, Any]:
    key = str(project_key or "").strip()
    if not key:
        return {}
    now = _utc_now_iso()
    with _PROGRESS_LOCK:
        current = dict(_PROGRESS_BY_PROJECT_KEY.get(key) or {})
        if not current:
            current = {
                "project_key": key,
                "project_name": "",
                "project_search_name": "",
                "run_id": "",
                "status": "running",
                "message": "연관 공고 검색을 시작했습니다.",
                "items": [],
                "item_count": 0,
                "started_at": now,
                "updated_at": now,
                "completed_at": "",
            }
        merged_items = _dedupe_items([*list(current.get("items") or []), *list(items or [])])
        current.update(
            {
                "project_key": key,
                "project_name": str(project_name or current.get("project_name") or ""),
                "project_search_name": str(project_search_name or current.get("project_search_name") or ""),
                "run_id": str(run_id or current.get("run_id") or ""),
                "status": str(status or current.get("status") or "running"),
                "message": message or str(current.get("message") or ""),
                "items": merged_items,
                "item_count": len(merged_items),
                "started_at": str(current.get("started_at") or now),
                "updated_at": now,
                "completed_at": str(current.get("completed_at") or ""),
            }
        )
        _PROGRESS_BY_PROJECT_KEY[key] = dict(current)
        return dict(current)


def finish_related_notice_progress(
    *,
    project_key: str,
    status: str,
    items: list[dict[str, Any]] | None = None,
    message: str = "",
) -> dict[str, Any]:
    final_status = str(status or "ready").strip() or "ready"
    payload = update_related_notice_progress(
        project_key=project_key,
        items=items,
        status=final_status,
        message=message,
    )
    if not payload:
        return {}
    payload["completed_at"] = _utc_now_iso()
    with _PROGRESS_LOCK:
        _PROGRESS_BY_PROJECT_KEY[str(project_key or "").strip()] = dict(payload)
    return dict(payload)


def get_related_notice_progress(*, project_key: str) -> dict[str, Any]:
    key = str(project_key or "").strip()
    if not key:
        return {}
    with _PROGRESS_LOCK:
        return dict(_PROGRESS_BY_PROJECT_KEY.get(key) or {})


def clear_related_notice_progress(project_key: str = "") -> None:
    key = str(project_key or "").strip()
    with _PROGRESS_LOCK:
        if key:
            _PROGRESS_BY_PROJECT_KEY.pop(key, None)
            return
        _PROGRESS_BY_PROJECT_KEY.clear()
