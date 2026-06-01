from __future__ import annotations

import contextlib
import copy
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from backend.perf_runtime import log_google_sheets_admin_duration

from backend.services.google_sheets_admin_backend import (
    build_google_sheet_admin_tab_key,
    fetch_google_sheet_grid_data,
    fetch_google_sheets_admin_metadata,
    normalize_google_sheet_display_title,
    refresh_google_sheets_admin_access_token,
    trim_google_sheet_cell_rows,
)

_GOOGLE_SHEETS_ADMIN_STATE_LOCK = threading.Lock()
_GOOGLE_SHEETS_ADMIN_FILE_LOCKS: dict[str, threading.Lock] = {}
_GOOGLE_SHEETS_ADMIN_SYNC_LOCKS: dict[str, threading.Lock] = {}
_GOOGLE_SHEETS_ADMIN_SNAPSHOTS: dict[str, dict] = {}
_GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATHS: dict[str, Path] = {}
_GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE: dict[str, tuple[int, int] | None] = {}
_GOOGLE_SHEETS_ADMIN_WORKERS: dict[str, threading.Thread] = {}
_GOOGLE_SHEETS_ADMIN_WORKER_STARTING: set[str] = set()
_GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT: set[str] = set()
_GOOGLE_SHEETS_ADMIN_STOP = threading.Event()

_GOOGLE_SHEETS_ADMIN_SYNC_FAILURE_MESSAGE = "Google Sheets sync failed."
_GOOGLE_SHEETS_ADMIN_PERSISTENCE_FAILURE_MESSAGE = "Snapshot persistence failed."
_GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET = object()


class GoogleSheetsAdminSnapshotConflictError(RuntimeError):
    pass


def _google_sheets_admin_snapshot_input_key(*, snapshot_path) -> str:
    return os.path.normcase(os.path.normpath(str(Path(snapshot_path).expanduser())))


def _google_sheets_admin_file_lock(*, path) -> threading.Lock:
    path_key = str(Path(path))
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        lock = _GOOGLE_SHEETS_ADMIN_FILE_LOCKS.get(path_key)
        if lock is None:
            lock = threading.Lock()
            _GOOGLE_SHEETS_ADMIN_FILE_LOCKS[path_key] = lock
        return lock


def _acquire_google_sheets_admin_os_lock(handle) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def _release_google_sheets_admin_os_lock(handle) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def _google_sheets_admin_snapshot_io_lock(*, path):
    path = Path(path)
    thread_lock = _google_sheets_admin_file_lock(path=path)
    lock_path = path.with_name(f"{path.name}.lock")
    thread_lock.acquire()
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as handle:
            _acquire_google_sheets_admin_os_lock(handle)
            try:
                yield
            finally:
                _release_google_sheets_admin_os_lock(handle)
    finally:
        thread_lock.release()


def _google_sheets_admin_snapshot_path(*, config) -> Path:
    input_key = _google_sheets_admin_snapshot_input_key(snapshot_path=config.snapshot_path)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        normalized_path = _GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATHS.get(input_key)
        if normalized_path is not None:
            return normalized_path

    raw_path = Path(config.snapshot_path).expanduser()
    normalized_path = (Path.cwd() / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()

    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        existing_path = _GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATHS.get(input_key)
        if existing_path is not None:
            return existing_path
        _GOOGLE_SHEETS_ADMIN_SNAPSHOT_PATHS[input_key] = normalized_path
        return normalized_path


def _google_sheets_admin_state_key(*, config) -> str:
    return str(_google_sheets_admin_snapshot_path(config=config))


def _google_sheets_admin_sync_lock(*, config) -> threading.Lock:
    state_key = _google_sheets_admin_state_key(config=config)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        lock = _GOOGLE_SHEETS_ADMIN_SYNC_LOCKS.get(state_key)
        if lock is None:
            lock = threading.Lock()
            _GOOGLE_SHEETS_ADMIN_SYNC_LOCKS[state_key] = lock
        return lock


def _sanitize_google_sheets_admin_sync_error(*, error: Exception) -> str:
    return _GOOGLE_SHEETS_ADMIN_SYNC_FAILURE_MESSAGE


def _sanitize_google_sheets_admin_persistence_error(*, error: Exception) -> str:
    return _GOOGLE_SHEETS_ADMIN_PERSISTENCE_FAILURE_MESSAGE


def _copy_google_sheets_admin_cached_snapshot(*, state_key: str) -> dict | None:
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        snapshot = _GOOGLE_SHEETS_ADMIN_SNAPSHOTS.get(state_key)
        return copy.deepcopy(snapshot) if snapshot is not None else None


def _cache_google_sheets_admin_snapshot(*, state_key: str, snapshot: dict, file_state) -> None:
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        _GOOGLE_SHEETS_ADMIN_SNAPSHOTS[state_key] = copy.deepcopy(snapshot)
        if file_state is None:
            _GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE.pop(state_key, None)
        else:
            _GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE[state_key] = file_state


def _google_sheets_admin_snapshot_is_missing(*, path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return False


def _google_sheets_admin_snapshot_file_state(*, path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def _load_google_sheets_admin_snapshot_and_state(
    *, config
) -> tuple[dict | None, tuple[int, int] | None]:
    state_key = _google_sheets_admin_state_key(config=config)
    snapshot_path = _google_sheets_admin_snapshot_path(config=config)
    with _google_sheets_admin_snapshot_io_lock(path=snapshot_path):
        snapshot_is_missing = _google_sheets_admin_snapshot_is_missing(path=snapshot_path)
        current_file_state = _google_sheets_admin_snapshot_file_state(path=snapshot_path)
        snapshot = load_google_sheets_admin_snapshot(path=snapshot_path)
        if snapshot is not None:
            _cache_google_sheets_admin_snapshot(
                state_key=state_key,
                snapshot=snapshot,
                file_state=current_file_state,
            )
            return copy.deepcopy(snapshot), current_file_state
        cached = _copy_google_sheets_admin_cached_snapshot(state_key=state_key)
        if cached is not None and not snapshot_is_missing:
            _cache_google_sheets_admin_snapshot(
                state_key=state_key,
                snapshot=cached,
                file_state=current_file_state,
            )
            return cached, current_file_state
        if snapshot_is_missing:
            with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
                _GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE.pop(state_key, None)
        return None, current_file_state


def _persist_google_sheets_admin_snapshot_unlocked(
    *, path, snapshot: dict, expected_existing_state=_GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        prefix=f"{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot, ensure_ascii=False, indent=2))
            handle.flush()
            os.fsync(handle.fileno())
        if (
            expected_existing_state is not _GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET
            and expected_existing_state != _google_sheets_admin_snapshot_file_state(path=path)
        ):
            raise GoogleSheetsAdminSnapshotConflictError("snapshot changed on disk")
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def persist_google_sheets_admin_snapshot(
    *,
    path,
    snapshot: dict,
    expected_existing_state=_GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET,
) -> None:
    path = Path(path)
    with _google_sheets_admin_snapshot_io_lock(path=path):
        _persist_google_sheets_admin_snapshot_unlocked(
            path=path,
            snapshot=snapshot,
            expected_existing_state=expected_existing_state,
        )


def load_google_sheets_admin_snapshot(*, path) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def sync_google_sheets_admin_snapshot_once(
    *, config, request_post_fn, request_get_fn, now_fn=datetime.now
) -> dict:
    state_key = _google_sheets_admin_state_key(config=config)
    _, base_file_state = _load_google_sheets_admin_snapshot_and_state(config=config)
    access_token = refresh_google_sheets_admin_access_token(
        config=config, request_post_fn=request_post_fn
    )
    metadata = fetch_google_sheets_admin_metadata(
        config=config, access_token=access_token, request_get_fn=request_get_fn
    )
    tabs = []
    sheets = {}
    for item in metadata.get("sheets") or []:
        props = dict(item.get("properties") or {})
        if props.get("hidden"):
            continue
        sheet_id = int(props.get("sheetId") or 0)
        raw_title = str(props.get("title") or "")
        key = build_google_sheet_admin_tab_key(sheet_id)
        header_cells, row_cells = trim_google_sheet_cell_rows(
            fetch_google_sheet_grid_data(
                config=config,
                access_token=access_token,
                sheet_title=raw_title,
                request_get_fn=request_get_fn,
            )
        )
        headers = [cell.get("text") or "" for cell in header_cells]
        rows = [[cell.get("text") or "" for cell in row] for row in row_cells]
        sheets[key] = {
            "sheet_id": sheet_id,
            "raw_title": raw_title,
            "display_title": normalize_google_sheet_display_title(raw_title),
            "headers": headers,
            "rows": rows,
            "header_cells": header_cells,
            "row_cells": row_cells,
            "row_count": len(rows),
            "column_count": len(headers),
        }
        tabs.append(
            {
                "key": key,
                "sheet_id": sheet_id,
                "raw_title": raw_title,
                "display_title": normalize_google_sheet_display_title(raw_title),
                "sheet_order": int(props.get("index") or 0),
            }
        )
    synced_at = now_fn(timezone.utc).isoformat()
    snapshot = {
        "enabled": True,
        "source_title": str((metadata.get("properties") or {}).get("title") or ""),
        "source_url": f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}/edit",
        "sync_status": "ready",
        "last_sync_attempt_at": synced_at,
        "last_successful_sync_at": synced_at,
        "tabs": sorted(tabs, key=lambda item: item["sheet_order"]),
        "sheets": sheets,
    }
    return _store_google_sheets_admin_snapshot_safely(
        config=config,
        state_key=state_key,
        snapshot=snapshot,
        expected_existing_state=base_file_state,
    )


def _build_google_sheets_admin_failure_snapshot(*, config, error: Exception, now_fn=datetime.now) -> dict:
    state_key = _google_sheets_admin_state_key(config=config)
    attempted_at = now_fn(timezone.utc).isoformat()
    try:
        snapshot, base_file_state = _load_google_sheets_admin_snapshot_and_state(config=config)
    except OSError as persistence_error:
        fallback_snapshot = copy.deepcopy(
            _copy_google_sheets_admin_cached_snapshot(state_key=state_key) or {}
        )
        fallback_snapshot.setdefault("enabled", True)
        fallback_snapshot.setdefault(
            "source_url", f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}/edit"
        )
        fallback_snapshot.setdefault("source_title", "")
        fallback_snapshot.setdefault("tabs", [])
        fallback_snapshot.setdefault("sheets", {})
        fallback_snapshot.pop("persistence_error", None)
        fallback_snapshot["sync_status"] = "failed"
        fallback_snapshot["last_sync_attempt_at"] = attempted_at
        fallback_snapshot["last_failed_sync_at"] = attempted_at
        fallback_snapshot["last_error"] = _sanitize_google_sheets_admin_sync_error(error=error)
        fallback_snapshot["persistence_error"] = _sanitize_google_sheets_admin_persistence_error(
            error=persistence_error
        )
        _cache_google_sheets_admin_snapshot(
            state_key=state_key,
            snapshot=fallback_snapshot,
            file_state=None,
        )
        return copy.deepcopy(fallback_snapshot)
    snapshot = copy.deepcopy(snapshot or {})
    snapshot.setdefault("enabled", True)
    snapshot.setdefault(
        "source_url", f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}/edit"
    )
    snapshot.setdefault("source_title", "")
    snapshot.setdefault("tabs", [])
    snapshot.setdefault("sheets", {})
    snapshot.pop("persistence_error", None)
    snapshot["sync_status"] = "failed"
    snapshot["last_sync_attempt_at"] = attempted_at
    snapshot["last_failed_sync_at"] = attempted_at
    snapshot["last_error"] = _sanitize_google_sheets_admin_sync_error(error=error)
    return _store_google_sheets_admin_snapshot_safely(
        config=config,
        state_key=state_key,
        snapshot=snapshot,
        expected_existing_state=base_file_state,
    )


def _store_google_sheets_admin_snapshot_safely(
    *,
    config,
    state_key: str,
    snapshot: dict,
    expected_existing_state=_GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET,
) -> dict:
    snapshot_path = _google_sheets_admin_snapshot_path(config=config)
    safe_snapshot = copy.deepcopy(snapshot)
    safe_snapshot.pop("persistence_error", None)
    try:
        persist_kwargs = {"path": snapshot_path, "snapshot": safe_snapshot}
        if expected_existing_state is not _GOOGLE_SHEETS_ADMIN_EXPECTED_STATE_UNSET:
            persist_kwargs["expected_existing_state"] = expected_existing_state
        persist_google_sheets_admin_snapshot(**persist_kwargs)
    except GoogleSheetsAdminSnapshotConflictError as error:
        current_snapshot = read_google_sheets_admin_snapshot(config=config)
        if current_snapshot is not None:
            return current_snapshot
        cached_snapshot = _copy_google_sheets_admin_cached_snapshot(state_key=state_key)
        if cached_snapshot is not None:
            return cached_snapshot
        return {
            "enabled": True,
            "source_url": f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}/edit",
            "source_title": "",
            "sync_status": "failed",
            "last_sync_attempt_at": safe_snapshot.get("last_sync_attempt_at"),
            "last_failed_sync_at": safe_snapshot.get("last_sync_attempt_at"),
            "last_error": safe_snapshot.get("last_error")
            or _sanitize_google_sheets_admin_persistence_error(error=error),
            "tabs": [],
            "sheets": {},
            "persistence_error": _sanitize_google_sheets_admin_persistence_error(error=error),
        }
    except OSError as error:
        fallback_snapshot = copy.deepcopy(read_google_sheets_admin_snapshot(config=config) or {})
        fallback_snapshot.pop("persistence_error", None)
        if safe_snapshot.get("last_error"):
            fallback_snapshot.update(
                {
                    "sync_status": safe_snapshot.get("sync_status", "failed"),
                    "last_sync_attempt_at": safe_snapshot.get("last_sync_attempt_at"),
                    "last_failed_sync_at": safe_snapshot.get("last_failed_sync_at"),
                    "last_error": safe_snapshot.get("last_error"),
                }
            )
        else:
            fallback_snapshot.setdefault("enabled", True)
            fallback_snapshot.setdefault(
                "source_url", f"https://docs.google.com/spreadsheets/d/{config.spreadsheet_id}/edit"
            )
            fallback_snapshot.setdefault("source_title", "")
            fallback_snapshot.setdefault("tabs", [])
            fallback_snapshot.setdefault("sheets", {})
            fallback_snapshot["sync_status"] = "failed"
            fallback_snapshot["last_sync_attempt_at"] = safe_snapshot.get("last_sync_attempt_at")
            fallback_snapshot["last_failed_sync_at"] = safe_snapshot.get(
                "last_sync_attempt_at"
            )
            fallback_snapshot["last_error"] = _sanitize_google_sheets_admin_persistence_error(
                error=error
            )
        fallback_snapshot["persistence_error"] = _sanitize_google_sheets_admin_persistence_error(
            error=error
        )
        _cache_google_sheets_admin_snapshot(
            state_key=state_key,
            snapshot=fallback_snapshot,
            file_state=_google_sheets_admin_snapshot_file_state(path=snapshot_path),
        )
        return copy.deepcopy(fallback_snapshot)
    _cache_google_sheets_admin_snapshot(
        state_key=state_key,
        snapshot=safe_snapshot,
        file_state=_google_sheets_admin_snapshot_file_state(path=snapshot_path),
    )
    return copy.deepcopy(safe_snapshot)


def run_google_sheets_admin_sync(
    *, config, request_post_fn=requests.post, request_get_fn=requests.get, now_fn=datetime.now
) -> dict:
    with _google_sheets_admin_sync_lock(config=config):
        try:
            return sync_google_sheets_admin_snapshot_once(
                config=config,
                request_post_fn=request_post_fn,
                request_get_fn=request_get_fn,
                now_fn=now_fn,
            )
        except Exception as error:
            return _build_google_sheets_admin_failure_snapshot(
                config=config, error=error, now_fn=now_fn
            )


def read_google_sheets_admin_snapshot(*, config) -> dict | None:
    started = time.perf_counter()
    state_key = _google_sheets_admin_state_key(config=config)
    snapshot_path = _google_sheets_admin_snapshot_path(config=config)
    current_file_state = _google_sheets_admin_snapshot_file_state(path=snapshot_path)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        cached = _GOOGLE_SHEETS_ADMIN_SNAPSHOTS.get(state_key)
        cached_file_state = _GOOGLE_SHEETS_ADMIN_SNAPSHOT_FILE_STATE.get(state_key)
        if (
            cached is not None
            and current_file_state is not None
            and cached_file_state == current_file_state
        ):
            log_google_sheets_admin_duration(
                event="snapshot_read",
                duration=time.perf_counter() - started,
                cache_hit=True,
                path=str(snapshot_path),
                file_missing=False,
                mtime_ns=current_file_state[0],
                size=current_file_state[1],
            )
            return copy.deepcopy(cached)
    try:
        reload_started = time.perf_counter()
        snapshot, _ = _load_google_sheets_admin_snapshot_and_state(config=config)
        reload_duration = time.perf_counter() - reload_started
    except OSError as error:
        log_google_sheets_admin_duration(
            event="snapshot_read",
            duration=time.perf_counter() - started,
            cache_hit=False,
            path=str(snapshot_path),
            file_missing=current_file_state is None,
            error=str(error),
        )
        return _copy_google_sheets_admin_cached_snapshot(state_key=state_key)
    log_google_sheets_admin_duration(
        event="snapshot_read",
        duration=time.perf_counter() - started,
        cache_hit=False,
        path=str(snapshot_path),
        file_missing=current_file_state is None,
        load_duration=reload_duration,
        mtime_ns=current_file_state[0] if current_file_state else None,
        size=current_file_state[1] if current_file_state else None,
    )
    return copy.deepcopy(snapshot) if snapshot is not None else None


def queue_google_sheets_admin_sync_now(*, config) -> bool:
    state_key = _google_sheets_admin_state_key(config=config)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        if state_key in _GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT:
            return False
        _GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT.add(state_key)

    def _run() -> None:
        try:
            run_google_sheets_admin_sync(
                config=config, request_post_fn=requests.post, request_get_fn=requests.get
            )
        finally:
            with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
                _GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT.discard(state_key)

    try:
        worker = threading.Thread(target=_run, daemon=True)
        worker.start()
    except Exception:
        with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
            _GOOGLE_SHEETS_ADMIN_MANUAL_SYNC_IN_FLIGHT.discard(state_key)
        raise
    return True


def ensure_google_sheets_admin_sync_worker_started(*, config) -> None:
    state_key = _google_sheets_admin_state_key(config=config)
    with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
        if state_key in _GOOGLE_SHEETS_ADMIN_WORKER_STARTING:
            return
        worker = _GOOGLE_SHEETS_ADMIN_WORKERS.get(state_key)
        if worker is not None and worker.is_alive():
            return
        _GOOGLE_SHEETS_ADMIN_WORKER_STARTING.add(state_key)

    def _loop() -> None:
        # Worker ownership is process-local; other processes coordinate through the persisted snapshot.
        run_google_sheets_admin_sync(
            config=config, request_post_fn=requests.post, request_get_fn=requests.get
        )
        while not _GOOGLE_SHEETS_ADMIN_STOP.wait(config.sync_interval_seconds):
            run_google_sheets_admin_sync(
                config=config, request_post_fn=requests.post, request_get_fn=requests.get
            )

    try:
        worker = threading.Thread(target=_loop, daemon=True)
        with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
            _GOOGLE_SHEETS_ADMIN_WORKERS[state_key] = worker
        worker.start()
    except Exception:
        with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
            _GOOGLE_SHEETS_ADMIN_WORKER_STARTING.discard(state_key)
            _GOOGLE_SHEETS_ADMIN_WORKERS.pop(state_key, None)
        raise
    else:
        with _GOOGLE_SHEETS_ADMIN_STATE_LOCK:
            _GOOGLE_SHEETS_ADMIN_WORKER_STARTING.discard(state_key)
