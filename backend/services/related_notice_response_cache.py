from __future__ import annotations

import threading
import time
from typing import Any
from uuid import UUID

from backend.api.schemas import RelatedNoticeListResponse

_RELATED_NOTICE_RESPONSE_CACHE_LOCK = threading.Lock()
_RELATED_NOTICE_RESPONSE_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
RELATED_NOTICE_RESPONSE_CACHE_TTL_SEC = 90.0
RELATED_NOTICE_PENDING_CACHE_TTL_SEC = 10.0
RELATED_NOTICE_PENDING_PRECOMPUTE_CACHE_TTL_SEC = 30.0
RELATED_NOTICE_SEED_FALLBACK_CACHE_TTL_SEC = 20.0


def related_notice_response_cache_ttl_seconds(response: RelatedNoticeListResponse) -> float:
    if response.status != "ready":
        if response.status == "pending" and response.source == "precompute":
            return RELATED_NOTICE_PENDING_PRECOMPUTE_CACHE_TTL_SEC
        return RELATED_NOTICE_PENDING_CACHE_TTL_SEC
    if response.source == "seed_fallback":
        return RELATED_NOTICE_SEED_FALLBACK_CACHE_TTL_SEC
    return RELATED_NOTICE_RESPONSE_CACHE_TTL_SEC


def _related_notice_response_cache_key(project_id: UUID, snapshot_set_id: str | None) -> tuple[str, str]:
    snapshot_key = str(snapshot_set_id or "legacy").strip() or "legacy"
    return str(project_id), snapshot_key


def get_related_notice_response_cache(
    project_id: UUID,
    snapshot_set_id: str | None = None,
) -> RelatedNoticeListResponse | None:
    cache_key = _related_notice_response_cache_key(project_id, snapshot_set_id)
    now = time.monotonic()
    with _RELATED_NOTICE_RESPONSE_CACHE_LOCK:
        cached = _RELATED_NOTICE_RESPONSE_CACHE.get(cache_key)
        if cached is None:
            return None
        expires_at, payload = cached
        if expires_at <= now:
            _RELATED_NOTICE_RESPONSE_CACHE.pop(cache_key, None)
            return None
    return RelatedNoticeListResponse(**dict(payload))


def set_related_notice_response_cache(
    project_id: UUID,
    response_or_snapshot_set_id: RelatedNoticeListResponse | str,
    response: RelatedNoticeListResponse | None = None,
    snapshot_set_id: str | None = None,
) -> RelatedNoticeListResponse:
    if isinstance(response_or_snapshot_set_id, RelatedNoticeListResponse):
        response_model = response_or_snapshot_set_id
        snapshot_key = snapshot_set_id
        if snapshot_key is None and isinstance(response, str):
            snapshot_key = response
    else:
        snapshot_key = str(response_or_snapshot_set_id or "").strip() or None
        if response is None:
            raise TypeError("response is required when snapshot_set_id is passed positionally")
        response_model = response
    ttl = max(1.0, related_notice_response_cache_ttl_seconds(response_model))
    payload = response_model.model_dump(mode="python")
    cache_key = _related_notice_response_cache_key(project_id, snapshot_key)
    with _RELATED_NOTICE_RESPONSE_CACHE_LOCK:
        _RELATED_NOTICE_RESPONSE_CACHE[cache_key] = (time.monotonic() + ttl, payload)
    return RelatedNoticeListResponse(**dict(payload))


def clear_related_notice_response_cache(project_id: UUID | None = None) -> None:
    with _RELATED_NOTICE_RESPONSE_CACHE_LOCK:
        if project_id is None:
            _RELATED_NOTICE_RESPONSE_CACHE.clear()
            return
        project_key = str(project_id)
        for cache_key in [key for key in _RELATED_NOTICE_RESPONSE_CACHE if key[0] == project_key]:
            _RELATED_NOTICE_RESPONSE_CACHE.pop(cache_key, None)
