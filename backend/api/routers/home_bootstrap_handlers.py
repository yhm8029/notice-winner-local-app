from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import Request

from backend.api.routers import home_bootstrap_support as support
from backend.api.schemas import AuthOrganizationUserItem
from backend.api.schemas import HomeBootstrapResponse
from backend.api.schemas import OrganizationAdminBootstrapResponse
from backend.api.schemas import SalesClaimItem
from backend.api.schemas import SalesClaimSummaryByUserResponse


def _app_module():
    return support._app_module()


def _read_sales_overview_cache(*, organization_id: UUID) -> dict[str, Any] | None:
    return support._read_sales_overview_cache_impl(organization_id=organization_id)


def _write_sales_overview_cache(
    *,
    organization_id: UUID,
    company_items: list[dict[str, Any]],
    organization_users: list[dict[str, Any]],
) -> None:
    support._write_sales_overview_cache_impl(
        organization_id=organization_id,
        company_items=company_items,
        organization_users=organization_users,
    )


def _invalidate_sales_overview_cache(*, organization_id: UUID | str | None) -> None:
    support._invalidate_sales_overview_cache_impl(
        organization_id=organization_id,
        invalidate_home_bootstrap_snapshot_best_effort=support._invalidate_home_bootstrap_snapshot_best_effort,
    )


def _read_organization_admin_bootstrap_cache(
    *,
    organization_id: UUID | str | None,
) -> OrganizationAdminBootstrapResponse | None:
    app_module = _app_module()
    cached = support._read_ttl_model_cache(
        cache=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE,
        cache_lock=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE_LOCK,
        cache_key=str(organization_id or ""),
    )
    if cached is None:
        return None
    return OrganizationAdminBootstrapResponse.model_validate(cached)


def _write_organization_admin_bootstrap_cache(
    *,
    organization_id: UUID | str | None,
    payload: OrganizationAdminBootstrapResponse,
) -> OrganizationAdminBootstrapResponse:
    app_module = _app_module()
    cached = support._write_ttl_model_cache(
        cache=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE,
        cache_lock=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE_LOCK,
        cache_key=str(organization_id or ""),
        ttl_sec=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE_TTL_SEC,
        payload=payload,
    )
    return OrganizationAdminBootstrapResponse.model_validate(cached)


def _clear_organization_admin_bootstrap_cache(*, organization_id: UUID | str | None = None) -> None:
    app_module = _app_module()
    support._clear_ttl_model_cache(
        cache=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE,
        cache_lock=app_module._ORGANIZATION_ADMIN_BOOTSTRAP_CACHE_LOCK,
        cache_key=str(organization_id or ""),
    )


def _read_sales_claim_summary_by_user_cache(
    *,
    organization_id: UUID | str | None,
) -> SalesClaimSummaryByUserResponse | None:
    app_module = _app_module()
    cached = support._read_ttl_model_cache(
        cache=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE,
        cache_lock=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE_LOCK,
        cache_key=str(organization_id or ""),
    )
    if cached is None:
        return None
    return SalesClaimSummaryByUserResponse.model_validate(cached)


def _write_sales_claim_summary_by_user_cache(
    *,
    organization_id: UUID | str | None,
    payload: SalesClaimSummaryByUserResponse,
) -> SalesClaimSummaryByUserResponse:
    app_module = _app_module()
    cached = support._write_ttl_model_cache(
        cache=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE,
        cache_lock=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE_LOCK,
        cache_key=str(organization_id or ""),
        ttl_sec=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE_TTL_SEC,
        payload=payload,
    )
    return SalesClaimSummaryByUserResponse.model_validate(cached)


def _clear_sales_claim_summary_by_user_cache(*, organization_id: UUID | str | None = None) -> None:
    app_module = _app_module()
    support._clear_ttl_model_cache(
        cache=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE,
        cache_lock=app_module._SALES_CLAIM_SUMMARY_BY_USER_CACHE_LOCK,
        cache_key=str(organization_id or ""),
    )


def _invalidate_sales_claim_view_caches(*, organization_id: UUID | str | None) -> None:
    support._invalidate_sales_overview_cache(organization_id=organization_id)
    support._clear_sales_claim_summary_by_user_cache(organization_id=organization_id)


def _load_home_bootstrap_snapshot_row(*, organization_id: UUID) -> dict[str, Any] | None:
    return support._load_home_bootstrap_snapshot_row_impl(
        organization_id=organization_id,
        get_home_bootstrap_snapshot_repository=support.get_home_bootstrap_snapshot_repository,
    )


def _upsert_home_bootstrap_snapshot_best_effort(
    *,
    organization_id: UUID,
    payload_json: dict[str, Any],
    generated_at: datetime,
) -> dict[str, Any] | None:
    return support._upsert_home_bootstrap_snapshot_best_effort_impl(
        organization_id=organization_id,
        payload_json=payload_json,
        generated_at=generated_at,
        get_home_bootstrap_snapshot_repository=support.get_home_bootstrap_snapshot_repository,
        json_safe_copy=support._json_safe_copy,
        snapshot_version=support._HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        logger=support.HOME_BOOTSTRAP_PERF_LOGGER,
    )


def _invalidate_home_bootstrap_snapshot_best_effort(*, organization_id: UUID | str | None) -> None:
    return support._invalidate_home_bootstrap_snapshot_best_effort_impl(
        organization_id=organization_id,
        clear_global_tracker_rows_cache=support._clear_global_tracker_rows_cache,
        get_home_bootstrap_snapshot_repository=support.get_home_bootstrap_snapshot_repository,
        logger=support.HOME_BOOTSTRAP_PERF_LOGGER,
    )


def _describe_home_bootstrap_snapshot_state(snapshot: dict[str, Any] | None) -> str:
    return support._describe_home_bootstrap_snapshot_state_impl(
        snapshot,
        snapshot_version=support._HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        parse_iso_datetime=support._parse_iso_datetime,
    )


def _is_home_bootstrap_snapshot_fresh(snapshot: dict[str, Any]) -> bool:
    return support._is_home_bootstrap_snapshot_fresh_impl(
        snapshot,
        snapshot_version=support._HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        parse_iso_datetime=support._parse_iso_datetime,
    )


def _is_valid_home_bootstrap_payload_shape(payload: dict[str, Any]) -> bool:
    return support._is_valid_home_bootstrap_payload_shape_impl(
        payload,
        snapshot_version=support._HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        parse_iso_datetime=support._parse_iso_datetime,
    )


def _build_home_bootstrap_tracker_first_page() -> dict[str, Any]:
    return support._build_home_bootstrap_tracker_first_page_impl(
        load_global_tracker_rows=support._load_global_tracker_rows,
        filter_tracker_rows_for_global_scope=support._filter_tracker_rows_for_global_scope,
        page_size=support._HOME_BOOTSTRAP_TRACKER_PAGE_SIZE,
        model_to_json_dict=support._model_to_json_dict,
        to_tracker_entry_summary_model=support._to_tracker_entry_summary_model,
    )


def _build_sales_claim_overview_payload(
    *,
    actor,
    request_id: str = "",
) -> dict[str, Any]:
    return support._build_sales_claim_overview_payload_impl(
        actor=actor,
        request_id=request_id,
        get_sales_claim_repository=support._get_sales_claim_repository,
        auth_is_enabled=support.auth_is_enabled,
        list_local_users_overview=support.list_local_users_overview,
        measure_stage=support.measure_stage,
        model_to_json_dict=support._model_to_json_dict,
        to_sales_claim_model=support._to_sales_claim_model,
        to_auth_org_user_model=support._to_auth_org_user_model,
    )


def _build_home_bootstrap_payload(
    *,
    actor,
    request_id: str = "",
) -> dict[str, Any]:
    return support._build_home_bootstrap_payload_impl(
        actor=actor,
        request_id=request_id,
        load_home_bootstrap_snapshot_row_fn=support._load_home_bootstrap_snapshot_row,
        describe_home_bootstrap_snapshot_state_fn=support._describe_home_bootstrap_snapshot_state,
        build_sales_claim_overview_payload_fn=support._build_sales_claim_overview_payload,
        build_home_bootstrap_tracker_first_page_fn=support._build_home_bootstrap_tracker_first_page,
        utc_now=support._utc_now,
        json_safe_copy=support._json_safe_copy,
        parse_iso_datetime=support._parse_iso_datetime,
        upsert_home_bootstrap_snapshot_best_effort_fn=support._upsert_home_bootstrap_snapshot_best_effort,
        snapshot_version=support._HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        logger=support.HOME_BOOTSTRAP_PERF_LOGGER,
    )


def get_home_bootstrap(request: Request) -> HomeBootstrapResponse:
    actor = support._resolve_sales_actor(request)
    request_id = str(getattr(request.state, "request_id", "") or "")
    try:
        payload = support._build_home_bootstrap_payload(
            actor=actor,
            request_id=request_id,
        )
    except support.SalesClaimRepositoryError as exc:
        support._repository_error(str(exc))
    except support.TrackerEntryRepositoryError as exc:
        support._repository_error(str(exc))
    except support.AuthRuntimeError as exc:
        raise support.ApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    support._dispatch_background(support._warm_default_user_tracker_export_workbook)
    return HomeBootstrapResponse(
        my_items=[SalesClaimItem.model_validate(item) for item in payload.get("my_items") or []],
        company_items=[SalesClaimItem.model_validate(item) for item in payload.get("company_items") or []],
        organization_users=[AuthOrganizationUserItem.model_validate(item) for item in payload.get("organization_users") or []],
        tracker_first_page=payload.get("tracker_first_page") or {},
        generated_at=payload.get("generated_at"),
        snapshot_version=int(payload.get("snapshot_version") or support._HOME_BOOTSTRAP_SNAPSHOT_VERSION),
    )
