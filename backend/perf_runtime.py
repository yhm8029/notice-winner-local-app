from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

from fastapi import Request

HTTP_PERF_LOGGER = logging.getLogger("perf.http")
STAGE_PERF_LOGGER = logging.getLogger("perf.stage")
TASK_PERF_LOGGER = logging.getLogger("perf.task")
SUPABASE_PERF_LOGGER = logging.getLogger("perf.supabase")
GOOGLE_SHEETS_ADMIN_PERF_LOGGER = logging.getLogger("perf.google_sheets_admin")


def _env_float(name: str, default: float) -> float:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_flag(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


SLOW_HTTP_REQUEST_SEC = _env_float("PERF_HTTP_SLOW_REQUEST_SEC", 1.0)
SLOW_STAGE_SEC = _env_float("PERF_STAGE_SLOW_SEC", 0.2)
SLOW_TASK_SEC = _env_float("PERF_TASK_SLOW_SEC", 2.0)
SLOW_SUPABASE_REQUEST_SEC = _env_float("PERF_SUPABASE_SLOW_SEC", 0.3)
SLOW_GOOGLE_SHEETS_ADMIN_SEC = _env_float("PERF_GOOGLE_SHEETS_ADMIN_SLOW_SEC", 0.25)


def ensure_request_id(request: Request) -> str:
    existing = getattr(request.state, "request_id", "")
    if existing:
        return str(existing)
    request_id = uuid4().hex
    request.state.request_id = request_id
    return request_id


@contextmanager
def measure_stage(name: str, **meta: Any):
    started = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - started
        logger = STAGE_PERF_LOGGER.warning if duration >= SLOW_STAGE_SEC else STAGE_PERF_LOGGER.info
        logger("STAGE name=%s duration=%.3f meta=%s", name, duration, meta)


def log_task_duration(
    *,
    task_name: str,
    duration: float,
    status: str,
    **meta: Any,
) -> None:
    logger = TASK_PERF_LOGGER.warning if duration >= SLOW_TASK_SEC else TASK_PERF_LOGGER.info
    logger("TASK_%s task=%s duration=%.3f meta=%s", status.upper(), task_name, duration, meta)


def log_google_sheets_admin_duration(
    *,
    event: str,
    duration: float,
    slow_threshold: float | None = None,
    debug_enabled: bool | None = None,
    **meta: Any,
) -> None:
    threshold = SLOW_GOOGLE_SHEETS_ADMIN_SEC if slow_threshold is None else float(slow_threshold)
    debug = _env_flag("GOOGLE_SHEETS_ADMIN_DEBUG_TIMING") if debug_enabled is None else bool(debug_enabled)
    event_name = str(event or "").upper()
    if duration >= threshold:
        GOOGLE_SHEETS_ADMIN_PERF_LOGGER.warning(
            "GOOGLE_SHEETS_ADMIN_%s duration=%.3f meta=%s",
            event_name,
            duration,
            meta,
        )
        return
    if debug:
        GOOGLE_SHEETS_ADMIN_PERF_LOGGER.info(
            "GOOGLE_SHEETS_ADMIN_%s duration=%.3f meta=%s",
            event_name,
            duration,
            meta,
        )
