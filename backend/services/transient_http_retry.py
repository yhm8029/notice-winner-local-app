from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import requests

T = TypeVar("T")

TRANSIENT_HTTP_STATUSES = frozenset({408, 500, 502, 503, 504})


def is_transient_http_status(status_code: int) -> bool:
    return int(status_code or 0) in TRANSIENT_HTTP_STATUSES


def is_transient_request_error(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ),
    )


def run_with_transient_http_retries(
    action: Callable[[], T],
    *,
    should_retry_result: Callable[[T], bool],
    attempts: int = 3,
    delays_sec: tuple[float, ...] = (1.0, 3.0),
) -> T:
    max_attempts = max(1, int(attempts or 1))
    for attempt_index in range(max_attempts):
        try:
            result = action()
        except Exception as exc:
            if not is_transient_request_error(exc) or attempt_index >= max_attempts - 1:
                raise
            _sleep_before_retry(delays_sec=delays_sec, attempt_index=attempt_index)
            continue
        if not should_retry_result(result) or attempt_index >= max_attempts - 1:
            return result
        _sleep_before_retry(delays_sec=delays_sec, attempt_index=attempt_index)
    raise RuntimeError("transient HTTP retry exhausted without a result")


def _sleep_before_retry(*, delays_sec: tuple[float, ...], attempt_index: int) -> None:
    if not delays_sec:
        return
    delay = float(delays_sec[min(attempt_index, len(delays_sec) - 1)] or 0.0)
    if delay > 0:
        time.sleep(delay)
