from __future__ import annotations

import json
import time
from typing import Any

import requests

from backend.perf_runtime import SLOW_SUPABASE_REQUEST_SEC
from backend.perf_runtime import SUPABASE_PERF_LOGGER

_RETRYABLE_METHODS = frozenset({"GET", "PATCH"})
_MAX_REQUEST_ATTEMPTS = 3
_INITIAL_RETRY_DELAY_SECONDS = 0.5
_RETRYABLE_HTTP_STATUSES = frozenset({408, 500, 502, 503, 504})


def extract_error_message(body: str) -> str | None:
    if not body:
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return body
    if isinstance(payload, dict):
        message = payload.get("message")
        details = payload.get("details")
        if message and details:
            return f"{message} ({details})"
        if message:
            return str(message)
    return body


def _is_retryable_request_error(method: str, exc: requests.RequestException) -> bool:
    normalized_method = method.upper()
    if normalized_method not in _RETRYABLE_METHODS:
        return False
    return isinstance(exc, (requests.Timeout, requests.ConnectionError))


def _request_method_allows_retry(method: str, *, allow_retry: bool) -> bool:
    normalized_method = method.upper()
    return normalized_method in _RETRYABLE_METHODS or (
        normalized_method == "POST" and allow_retry
    )


def _is_retryable_http_error(method: str, exc: requests.HTTPError, *, allow_retry: bool) -> bool:
    if not _request_method_allows_retry(method, allow_retry=allow_retry):
        return False
    status_code = int(getattr(exc.response, "status_code", 0) or 0)
    return status_code in _RETRYABLE_HTTP_STATUSES


def request_json(
    *,
    rest_url: str,
    api_key: str,
    timeout_seconds: float,
    method: str,
    path: str,
    query: list[tuple[str, str]] | None = None,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | list[dict[str, Any]] | None = None,
    allow_retry: bool = False,
    error_cls: type[Exception],
) -> tuple[list[dict[str, Any]] | dict[str, Any], dict[str, str]]:
    response_headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if headers:
        response_headers.update(headers)

    response: requests.Response | None = None
    last_request_error: requests.RequestException | None = None
    started = time.perf_counter()
    for attempt in range(_MAX_REQUEST_ATTEMPTS):
        try:
            response = requests.request(
                method=method,
                url=f"{rest_url}{path}",
                params=query or None,
                headers=response_headers,
                json=payload if payload is not None else None,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            last_request_error = None
            break
        except requests.HTTPError as exc:
            duration = time.perf_counter() - started
            body = (exc.response.text if exc.response is not None else "") or ""
            status_code = exc.response.status_code if exc.response is not None else "error"
            if duration >= SLOW_SUPABASE_REQUEST_SEC:
                SUPABASE_PERF_LOGGER.warning(
                    "SUPABASE_HTTP_ERROR method=%s path=%s status=%s duration=%.3f attempt=%s query=%s",
                    method,
                    path,
                    status_code,
                    duration,
                    attempt + 1,
                    query or [],
                )
            if _is_retryable_http_error(method, exc, allow_retry=allow_retry) and attempt < _MAX_REQUEST_ATTEMPTS - 1:
                time.sleep(_INITIAL_RETRY_DELAY_SECONDS * (2**attempt))
                continue
            message = extract_error_message(body.strip()) or f"Supabase request failed: HTTP {status_code}"
            raise error_cls(message) from exc
        except requests.RequestException as exc:
            last_request_error = exc
            if (
                not _request_method_allows_retry(method, allow_retry=allow_retry)
                or not isinstance(exc, (requests.Timeout, requests.ConnectionError))
                or attempt >= _MAX_REQUEST_ATTEMPTS - 1
            ):
                break
            time.sleep(_INITIAL_RETRY_DELAY_SECONDS * (2**attempt))

    if last_request_error is not None:
        duration = time.perf_counter() - started
        if duration >= SLOW_SUPABASE_REQUEST_SEC:
            SUPABASE_PERF_LOGGER.warning(
                "SUPABASE_REQUEST_ERROR method=%s path=%s duration=%.3f attempts=%s query=%s error=%s",
                method,
                path,
                duration,
                _MAX_REQUEST_ATTEMPTS,
                query or [],
                last_request_error,
            )
        raise error_cls(f"Supabase request failed: {last_request_error}") from last_request_error
    if response is None:
        raise error_cls("Supabase request failed without a response")

    duration = time.perf_counter() - started
    if duration >= SLOW_SUPABASE_REQUEST_SEC:
        SUPABASE_PERF_LOGGER.warning(
            "SUPABASE_SLOW method=%s path=%s status=%s duration=%.3f attempts=%s query=%s",
            method,
            path,
            response.status_code,
            duration,
            attempt + 1,
            query or [],
        )

    raw = response.text.strip()
    parsed_headers = dict(response.headers)
    if not raw:
        return [], parsed_headers

    try:
        parsed = response.json()
    except ValueError as exc:
        raise error_cls("Supabase response is not valid JSON") from exc

    if isinstance(parsed, list):
        return parsed, parsed_headers
    if isinstance(parsed, dict):
        return parsed, parsed_headers
    raise error_cls("Supabase response is not a JSON object or array")
