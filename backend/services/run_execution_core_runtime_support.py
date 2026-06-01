from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from typing import Any
from typing import Callable
from uuid import UUID

from datetime import datetime
from datetime import timezone

from .run_execution_seed_runtime import stage_delay_seconds as _stage_delay_seconds_impl
from .run_execution_seed_runtime import to_storage_path as _to_storage_path_impl


RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC = 300
_PRECOMPUTE_ACTIVE: dict[str, tuple[float, str]] = {}
_PRECOMPUTE_ACTIVE_LOCK = threading.Lock()


def _to_uuid_or_none(value: Any) -> UUID | None:
    if value in (None, ""):
        return None
    try:
        return UUID(str(value))
    except Exception:
        return None


def _build_run_execution_runtime_deps(module_globals: dict[str, Any]) -> Any:
    return SimpleNamespace(**module_globals)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_storage_path(path: Any) -> str:
    return _to_storage_path_impl(path)


def _stage_delay_seconds(*, params: dict[str, Any], fallback_ms: int) -> float:
    return _stage_delay_seconds_impl(params=params, fallback_ms=fallback_ms)


def related_notice_precompute_dedup_key(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
) -> str:
    normalized_project_key = str(project_key or "").strip()
    normalized_snapshot_set_id = str(snapshot_set_id or "").strip()
    if backfill_remaining and not force_recompute and not normalized_snapshot_set_id:
        return f"{run_id}:{normalized_project_key}"
    return "::".join(
        (
            str(run_id),
            normalized_project_key,
            "backfill" if backfill_remaining else "single",
            "force" if force_recompute else "normal",
            normalized_snapshot_set_id,
        )
    )


def queue_related_notice_precompute_for_run(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
    safely_precompute_related_notices_for_run_fn: Callable[..., None],
) -> bool:
    dedup_key = related_notice_precompute_dedup_key(
        run_id,
        project_key=project_key,
        backfill_remaining=backfill_remaining,
        force_recompute=force_recompute,
        snapshot_set_id=snapshot_set_id,
    )
    token = f"{time.monotonic():.9f}:{threading.get_ident()}"
    now = time.monotonic()

    with _PRECOMPUTE_ACTIVE_LOCK:
        active_entry = _PRECOMPUTE_ACTIVE.get(dedup_key)
        if active_entry is not None:
            started_at, _active_token = active_entry
            if (now - started_at) < RELATED_NOTICE_PRECOMPUTE_ACTIVE_STALE_SEC:
                return False
        _PRECOMPUTE_ACTIVE[dedup_key] = (now, token)

    def _run() -> None:
        try:
            safely_precompute_related_notices_for_run_fn(
                run_id,
                project_key=project_key,
                backfill_remaining=backfill_remaining,
                force_recompute=force_recompute,
                snapshot_set_id=snapshot_set_id,
            )
        finally:
            with _PRECOMPUTE_ACTIVE_LOCK:
                active_entry = _PRECOMPUTE_ACTIVE.get(dedup_key)
                if active_entry is not None and active_entry[1] == token:
                    _PRECOMPUTE_ACTIVE.pop(dedup_key, None)

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    return True


def safely_precompute_related_notices_for_run(
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
    precompute_related_notices_for_run_fn: Callable[..., None],
    log_task_duration_fn: Callable[..., None],
) -> None:
    started = time.perf_counter()
    try:
        precompute_related_notices_for_run_fn(
            run_id,
            project_key=project_key,
            backfill_remaining=backfill_remaining,
            force_recompute=force_recompute,
            snapshot_set_id=snapshot_set_id,
        )
        log_task_duration_fn(
            task_name="related_notice_precompute",
            duration=time.perf_counter() - started,
            status="ok",
            run_id=str(run_id),
            project_key=project_key,
        )
    except Exception:
        log_task_duration_fn(
            task_name="related_notice_precompute",
            duration=time.perf_counter() - started,
            status="error",
            run_id=str(run_id),
            project_key=project_key,
        )
        return
