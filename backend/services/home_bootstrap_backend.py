from __future__ import annotations

import time
from datetime import datetime
import threading
from typing import Any
from uuid import UUID

from backend.repositories import HomeBootstrapSnapshotRepositoryConfigError
from backend.repositories import HomeBootstrapSnapshotRepositoryError

_SALES_OVERVIEW_CACHE_TTL_SEC = 30.0
_sales_overview_cache_lock = threading.Lock()
_sales_overview_cache_by_org: dict[str, dict[str, Any]] = {}
_HOME_BOOTSTRAP_TRACKER_DEFAULT_SORT_ORDER_BY = [
    "opening_scheduled_date_desc",
    "updated_at_desc",
    "id_desc",
]


def sales_overview_cache_key(*, organization_id: UUID) -> str:
    return str(organization_id)


def read_sales_overview_cache(*, organization_id: UUID) -> dict[str, Any] | None:
    cache_key = sales_overview_cache_key(organization_id=organization_id)
    with _sales_overview_cache_lock:
        cached = _sales_overview_cache_by_org.get(cache_key)
        if not cached:
            return None
        if (time.perf_counter() - float(cached.get("cached_at_monotonic") or 0.0)) > _SALES_OVERVIEW_CACHE_TTL_SEC:
            _sales_overview_cache_by_org.pop(cache_key, None)
            return None
        return {
            "company_items": [dict(item) for item in list(cached.get("company_items") or [])],
            "organization_users": [dict(item) for item in list(cached.get("organization_users") or [])],
        }


def write_sales_overview_cache(
    *,
    organization_id: UUID,
    company_items: list[dict[str, Any]],
    organization_users: list[dict[str, Any]],
) -> None:
    cache_key = sales_overview_cache_key(organization_id=organization_id)
    with _sales_overview_cache_lock:
        _sales_overview_cache_by_org[cache_key] = {
            "cached_at_monotonic": time.perf_counter(),
            "company_items": [dict(item) for item in list(company_items or [])],
            "organization_users": [dict(item) for item in list(organization_users or [])],
        }


def invalidate_sales_overview_cache(
    *,
    organization_id: UUID | str | None,
    invalidate_home_bootstrap_snapshot_best_effort: Any,
) -> None:
    cache_key = str(organization_id or "").strip()
    if not cache_key:
        return
    with _sales_overview_cache_lock:
        _sales_overview_cache_by_org.pop(cache_key, None)
    invalidate_home_bootstrap_snapshot_best_effort(organization_id=organization_id)


def load_home_bootstrap_snapshot_row(
    *,
    organization_id: UUID,
    get_home_bootstrap_snapshot_repository: Any,
) -> dict[str, Any] | None:
    try:
        repository = get_home_bootstrap_snapshot_repository()
    except HomeBootstrapSnapshotRepositoryConfigError:
        return None
    try:
        snapshot = repository.get_snapshot(organization_id=organization_id)
    except HomeBootstrapSnapshotRepositoryError:
        return None
    if not snapshot:
        return None
    return dict(snapshot)


def upsert_home_bootstrap_snapshot_best_effort(
    *,
    organization_id: UUID,
    payload_json: dict[str, Any],
    generated_at: datetime,
    get_home_bootstrap_snapshot_repository: Any,
    json_safe_copy: Any,
    snapshot_version: int,
    logger: Any,
) -> dict[str, Any] | None:
    try:
        repository = get_home_bootstrap_snapshot_repository()
    except HomeBootstrapSnapshotRepositoryConfigError:
        return None
    try:
        safe_payload_json = json_safe_copy(payload_json)
        snapshot = repository.upsert_snapshot(
            organization_id=organization_id,
            snapshot_version=snapshot_version,
            payload_json=safe_payload_json,
            generated_at=generated_at,
        )
    except HomeBootstrapSnapshotRepositoryError:
        return None
    except Exception:
        logger.exception(
            "HOME_BOOTSTRAP event=upsert_failed meta=%s",
            {"organization_id": str(organization_id)},
        )
        return None
    if not snapshot:
        return None
    return dict(snapshot)


def invalidate_home_bootstrap_snapshot_best_effort(
    *,
    organization_id: UUID | str | None,
    clear_global_tracker_rows_cache: Any,
    get_home_bootstrap_snapshot_repository: Any,
    logger: Any,
) -> None:
    cache_key = str(organization_id or "").strip()
    if not cache_key:
        return
    clear_global_tracker_rows_cache()
    try:
        normalized_org_id = UUID(cache_key)
    except (ValueError, TypeError):
        return
    try:
        repository = get_home_bootstrap_snapshot_repository()
    except HomeBootstrapSnapshotRepositoryConfigError:
        return
    try:
        repository.invalidate_snapshot(organization_id=normalized_org_id)
    except HomeBootstrapSnapshotRepositoryError:
        return
    logger.info(
        "HOME_BOOTSTRAP event=invalidate meta=%s",
        {"organization_id": str(normalized_org_id)},
    )


def is_valid_home_bootstrap_payload_shape(
    payload: dict[str, Any],
    *,
    snapshot_version: int,
    parse_iso_datetime: Any,
) -> bool:
    if int(payload.get("snapshot_version") or 0) != snapshot_version:
        return False
    if parse_iso_datetime(payload.get("generated_at")) is None:
        return False

    company_items = payload.get("company_items")
    if not isinstance(company_items, list):
        return False
    for item in company_items:
        if not isinstance(item, dict):
            return False
        if item and (not item.get("project_id") or not item.get("project_name")):
            return False

    organization_users = payload.get("organization_users")
    if not isinstance(organization_users, list):
        return False
    for item in organization_users:
        if not isinstance(item, dict):
            return False
        if item and not (item.get("user_id") or item.get("membership_id") or item.get("email")):
            return False

    tracker_first_page = payload.get("tracker_first_page")
    if not isinstance(tracker_first_page, dict):
        return False
    items = tracker_first_page.get("items")
    if not isinstance(items, list):
        return False
    for item in items:
        if not isinstance(item, dict):
            return False
        if item and (not item.get("id") or not item.get("project_name")):
            return False
    if not isinstance(tracker_first_page.get("sort_contract"), dict):
        return False
    sort_contract = tracker_first_page.get("sort_contract")
    if sort_contract.get("mode") != "default":
        return False
    if list(sort_contract.get("order_by") or []) != _HOME_BOOTSTRAP_TRACKER_DEFAULT_SORT_ORDER_BY:
        return False
    try:
        if int(tracker_first_page.get("page") or 0) < 1:
            return False
        if int(tracker_first_page.get("page_size") or 0) < 1:
            return False
        if int(tracker_first_page.get("total") or 0) < 0:
            return False
    except (TypeError, ValueError):
        return False
    return True


def describe_home_bootstrap_snapshot_state(
    snapshot: dict[str, Any] | None,
    *,
    snapshot_version: int,
    parse_iso_datetime: Any,
) -> str:
    if not snapshot:
        return "missing"
    if int(snapshot.get("snapshot_version") or 0) != snapshot_version:
        return "version_mismatch"
    payload = snapshot.get("payload_json")
    if not isinstance(payload, dict):
        return "payload_missing"
    if not is_valid_home_bootstrap_payload_shape(
        payload,
        snapshot_version=snapshot_version,
        parse_iso_datetime=parse_iso_datetime,
    ):
        return "payload_invalid"
    tracker_first_page = payload.get("tracker_first_page")
    if not isinstance(tracker_first_page, dict):
        return "tracker_page_missing"
    generated_at = parse_iso_datetime(snapshot.get("generated_at") or payload.get("generated_at"))
    if generated_at is None:
        return "generated_at_missing"
    invalidated_at = parse_iso_datetime(snapshot.get("invalidated_at"))
    if invalidated_at is not None and invalidated_at > generated_at:
        return "invalidated"
    return "fresh"


def is_home_bootstrap_snapshot_fresh(
    snapshot: dict[str, Any],
    *,
    snapshot_version: int,
    parse_iso_datetime: Any,
) -> bool:
    if not snapshot:
        return False
    if int(snapshot.get("snapshot_version") or 0) != snapshot_version:
        return False
    payload = snapshot.get("payload_json")
    if not isinstance(payload, dict):
        return False
    if not is_valid_home_bootstrap_payload_shape(
        payload,
        snapshot_version=snapshot_version,
        parse_iso_datetime=parse_iso_datetime,
    ):
        return False
    tracker_first_page = payload.get("tracker_first_page")
    if not isinstance(tracker_first_page, dict):
        return False
    generated_at = parse_iso_datetime(snapshot.get("generated_at") or payload.get("generated_at"))
    if generated_at is None:
        return False
    invalidated_at = parse_iso_datetime(snapshot.get("invalidated_at"))
    if invalidated_at is not None and invalidated_at > generated_at:
        return False
    return True


def build_home_bootstrap_tracker_first_page(
    *,
    load_global_tracker_rows: Any,
    filter_tracker_rows_for_global_scope: Any,
    page_size: int,
    model_to_json_dict: Any,
    to_tracker_entry_summary_model: Any,
) -> dict[str, Any]:
    all_rows = load_global_tracker_rows()
    filtered = filter_tracker_rows_for_global_scope(
        all_rows,
        q="",
        region="",
        exclude_auxiliary_titles=True,
        edited_only=False,
    )
    total = len(filtered)
    items = filtered[:page_size]
    return {
        "items": [model_to_json_dict(to_tracker_entry_summary_model(item)) for item in items],
        "page": 1,
        "page_size": page_size,
        "total": total,
        "sort_contract": {
            "mode": "default",
            "order_by": ["opening_scheduled_date_desc", "updated_at_desc", "id_desc"],
        },
    }


def sales_claim_belongs_to_actor(item: Any, actor: Any) -> bool:
    payload = item.to_dict() if hasattr(item, "to_dict") else dict(item or {})
    actor_user_id = str(actor.user_id or "").strip()
    claim_user_id = str(payload.get("owner_user_id") or "").strip()
    if actor_user_id and claim_user_id and actor_user_id == claim_user_id:
        return True
    actor_email = str(actor.email or "").strip().lower()
    claim_email = str(payload.get("owner_email") or "").strip().lower()
    return bool(actor_email and claim_email and actor_email == claim_email)


def build_sales_claim_overview_payload(
    *,
    actor: Any,
    request_id: str = "",
    get_sales_claim_repository: Any,
    auth_is_enabled: Any,
    list_local_users_overview: Any,
    measure_stage: Any,
    model_to_json_dict: Any,
    to_sales_claim_model: Any,
    to_auth_org_user_model: Any,
) -> dict[str, Any]:
    cached = read_sales_overview_cache(organization_id=actor.organization_id)
    if cached is None:
        repository = get_sales_claim_repository()
        with measure_stage("sales_overview.list_claims", request_id=request_id, organization_id=str(actor.organization_id)):
            company_claims = repository.list_claims(
                organization_id=actor.organization_id,
                project_ids=None,
                lightweight=True,
            )
        company_items = [model_to_json_dict(to_sales_claim_model(item)) for item in company_claims]
        organization_users: list[dict[str, Any]] = []
        if auth_is_enabled():
            with measure_stage("sales_overview.list_users", request_id=request_id, organization_id=str(actor.organization_id)):
                organization_users = [
                    model_to_json_dict(to_auth_org_user_model(item))
                    for item in list_local_users_overview(organization_id=str(actor.organization_id))
                ]
        write_sales_overview_cache(
            organization_id=actor.organization_id,
            company_items=company_items,
            organization_users=organization_users,
        )
        cached = {
            "company_items": company_items,
            "organization_users": organization_users,
        }

    company_items = [dict(item) for item in list(cached.get("company_items") or [])]
    my_items = [dict(item) for item in company_items if sales_claim_belongs_to_actor(item, actor)]
    return {
        "my_items": my_items,
        "company_items": company_items,
        "organization_users": [dict(item) for item in list(cached.get("organization_users") or [])],
    }


def build_home_bootstrap_payload(
    *,
    actor: Any,
    request_id: str = "",
    load_home_bootstrap_snapshot_row_fn: Any,
    describe_home_bootstrap_snapshot_state_fn: Any,
    build_sales_claim_overview_payload_fn: Any,
    build_home_bootstrap_tracker_first_page_fn: Any,
    utc_now: Any,
    json_safe_copy: Any,
    parse_iso_datetime: Any,
    upsert_home_bootstrap_snapshot_best_effort_fn: Any,
    snapshot_version: int,
    logger: Any,
) -> dict[str, Any]:
    snapshot_row = load_home_bootstrap_snapshot_row_fn(organization_id=actor.organization_id)
    snapshot_state = describe_home_bootstrap_snapshot_state_fn(snapshot_row)
    if snapshot_state == "fresh" and snapshot_row:
        payload_json = dict(snapshot_row.get("payload_json") or {})
        generated_at = parse_iso_datetime(payload_json.get("generated_at") or snapshot_row.get("generated_at"))
        age_sec = None
        if generated_at is not None:
            age_sec = round((utc_now() - generated_at).total_seconds(), 3)
        logger.info(
            "HOME_BOOTSTRAP event=snapshot_hit meta=%s",
            {
                "request_id": request_id,
                "organization_id": str(actor.organization_id),
                "age_sec": age_sec,
                "company_items": len(list(payload_json.get("company_items") or [])),
                "tracker_items": len(list((payload_json.get("tracker_first_page") or {}).get("items") or [])),
            },
        )
    else:
        logger.info(
            "HOME_BOOTSTRAP event=regenerate meta=%s",
            {
                "request_id": request_id,
                "organization_id": str(actor.organization_id),
                "snapshot_state": snapshot_state,
            },
        )
        sales_payload = build_sales_claim_overview_payload_fn(actor=actor, request_id=request_id)
        tracker_first_page = build_home_bootstrap_tracker_first_page_fn()
        generated_at = utc_now()
        payload_json = json_safe_copy(
            {
                "snapshot_version": snapshot_version,
                "generated_at": generated_at.isoformat(),
                "company_items": [dict(item) for item in list(sales_payload.get("company_items") or [])],
                "organization_users": [dict(item) for item in list(sales_payload.get("organization_users") or [])],
                "tracker_first_page": dict(tracker_first_page or {}),
            }
        )
        upsert_home_bootstrap_snapshot_best_effort_fn(
            organization_id=actor.organization_id,
            payload_json=payload_json,
            generated_at=generated_at,
        )
        logger.info(
            "HOME_BOOTSTRAP event=regenerated meta=%s",
            {
                "request_id": request_id,
                "organization_id": str(actor.organization_id),
                "company_items": len(list(payload_json.get("company_items") or [])),
                "tracker_items": len(list((payload_json.get("tracker_first_page") or {}).get("items") or [])),
            },
        )
    company_items = [dict(item) for item in list(payload_json.get("company_items") or [])]
    generated_at = payload_json.get("generated_at")
    if not generated_at and snapshot_row:
        generated_at = snapshot_row.get("generated_at")
    return {
        "my_items": [dict(item) for item in company_items if sales_claim_belongs_to_actor(item, actor)],
        "company_items": company_items,
        "organization_users": [dict(item) for item in list(payload_json.get("organization_users") or [])],
        "tracker_first_page": dict(payload_json.get("tracker_first_page") or {}),
        "generated_at": generated_at,
        "snapshot_version": int(payload_json.get("snapshot_version") or snapshot_version),
    }
