from __future__ import annotations

import os
import threading
import time
from typing import Any
from uuid import UUID

_WORKER_LOCK = threading.Lock()
_WORKER_THREAD: threading.Thread | None = None
_WAKE_EVENT = threading.Event()


def _worker_enabled() -> bool:
    return str(os.getenv("RELATED_NOTICE_REFRESH_WORKER_ENABLED", "1")).strip().lower() not in {"0", "false", "no"}


def _poll_interval_sec() -> float:
    raw = str(os.getenv("RELATED_NOTICE_REFRESH_WORKER_INTERVAL_SEC", "10")).strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 10.0


def wake_related_notice_refresh_worker() -> None:
    _WAKE_EVENT.set()


def ensure_related_notice_refresh_worker_started(
    *,
    get_related_notice_cache_repository_fn: Any,
    safely_precompute_related_notices_for_run_fn: Any,
) -> None:
    global _WORKER_THREAD
    if not _worker_enabled():
        return
    with _WORKER_LOCK:
        if _WORKER_THREAD is not None and _WORKER_THREAD.is_alive():
            return
        _WORKER_THREAD = threading.Thread(
            target=_worker_loop,
            kwargs={
                "get_related_notice_cache_repository_fn": get_related_notice_cache_repository_fn,
                "safely_precompute_related_notices_for_run_fn": safely_precompute_related_notices_for_run_fn,
            },
            name="related-notice-refresh-worker",
            daemon=True,
        )
        _WORKER_THREAD.start()


def _worker_loop(
    *,
    get_related_notice_cache_repository_fn: Any,
    safely_precompute_related_notices_for_run_fn: Any,
) -> None:
    while True:
        try:
            _drain_once(
                get_related_notice_cache_repository_fn=get_related_notice_cache_repository_fn,
                safely_precompute_related_notices_for_run_fn=safely_precompute_related_notices_for_run_fn,
            )
        except Exception:
            pass
        _WAKE_EVENT.wait(_poll_interval_sec())
        _WAKE_EVENT.clear()


def _drain_once(
    *,
    get_related_notice_cache_repository_fn: Any,
    safely_precompute_related_notices_for_run_fn: Any,
    limit: int = 3,
) -> int:
    repository = get_related_notice_cache_repository_fn()
    processed = 0
    for row in repository.list_queued(limit=limit):
        project_key = str(row.get("project_key") or "").strip()
        snapshot_set_id = str(row.get("snapshot_set_id") or "legacy").strip() or "legacy"
        source_run_id = str(row.get("source_run_id") or "").strip()
        if not project_key or not source_run_id:
            continue
        claimed = repository.claim_queued(project_key=project_key, snapshot_set_id=snapshot_set_id)
        if claimed is None:
            continue
        try:
            run_id = UUID(source_run_id)
        except ValueError:
            continue
        safely_precompute_related_notices_for_run_fn(
            run_id,
            project_key=project_key,
            backfill_remaining=False,
            force_recompute=True,
            snapshot_set_id=snapshot_set_id,
        )
        processed += 1
    return processed

