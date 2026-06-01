from __future__ import annotations

import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from uuid import UUID

from fastapi import Request
from fastapi import status

from backend.api.auth_runtime import auth_is_enabled
from backend.api.auth_runtime import bootstrap_platform_admin_email
from backend.api.auth_runtime import list_local_users
from backend.api.auth_runtime import list_local_users_overview
from backend.api.schemas import AuthOrganizationUserItem
from backend.api.schemas import SalesClaimItem
from backend.api.schemas import SalesClaimSummaryProjectItem
from backend.api.schemas import SalesClaimSummaryUserItem
from backend.api.support.runtime_common import ApiError
from backend.api.support.runtime_common import _get_download_audit_log_repository
from backend.api.support.runtime_common import _get_sales_claim_repository
from backend.api.support.runtime_common import _get_tracker_repository
from backend.perf_runtime import measure_stage
from backend.phase1_defaults import load_phase1_identity
from backend.repositories.download_audit_logs import DownloadAuditLogRepositoryError
from backend.repositories.factory import get_home_bootstrap_snapshot_repository as _get_home_bootstrap_snapshot_repository_impl
from backend.repositories.tracker_entries import format_tracker_display_date
from backend.sales_claims import SalesActor
from backend.services.api_response_model_backend import model_to_json_dict as _model_to_json_dict_impl
from backend.services.api_response_model_backend import to_auth_org_user_model as _to_auth_org_user_model_impl
from backend.services.api_response_model_backend import to_sales_claim_summary_project_model as _to_sales_claim_summary_project_model_impl
from backend.services.api_response_model_backend import to_sales_claim_summary_user_model as _to_sales_claim_summary_user_model_impl
from backend.services.home_bootstrap_backend import build_home_bootstrap_payload as _build_home_bootstrap_payload_impl
from backend.services.home_bootstrap_backend import build_home_bootstrap_tracker_first_page as _build_home_bootstrap_tracker_first_page_impl
from backend.services.home_bootstrap_backend import build_sales_claim_overview_payload as _build_sales_claim_overview_payload_impl
from backend.services.home_bootstrap_backend import describe_home_bootstrap_snapshot_state as _describe_home_bootstrap_snapshot_state_impl
from backend.services.home_bootstrap_backend import invalidate_home_bootstrap_snapshot_best_effort as _invalidate_home_bootstrap_snapshot_best_effort_impl
from backend.services.home_bootstrap_backend import invalidate_sales_overview_cache as _invalidate_sales_overview_cache_impl
from backend.services.home_bootstrap_backend import is_home_bootstrap_snapshot_fresh as _is_home_bootstrap_snapshot_fresh_impl
from backend.services.home_bootstrap_backend import is_valid_home_bootstrap_payload_shape as _is_valid_home_bootstrap_payload_shape_impl
from backend.services.home_bootstrap_backend import load_home_bootstrap_snapshot_row as _load_home_bootstrap_snapshot_row_impl
from backend.services.home_bootstrap_backend import read_sales_overview_cache as _read_sales_overview_cache_impl
from backend.services.home_bootstrap_backend import sales_claim_belongs_to_actor as _sales_claim_belongs_to_actor_impl
from backend.services.home_bootstrap_backend import write_sales_overview_cache as _write_sales_overview_cache_impl
from backend.services.home_bootstrap_backend import upsert_home_bootstrap_snapshot_best_effort as _upsert_home_bootstrap_snapshot_best_effort_impl
from backend.services.sales_claim_export_backend import build_sales_claim_export_rows as _build_sales_claim_export_rows_impl

_HOME_BOOTSTRAP_SNAPSHOT_VERSION = 3


def _app_module():
    from backend.api import app as app_module

    return app_module


def _get_home_bootstrap_snapshot_version() -> int:
    return _HOME_BOOTSTRAP_SNAPSHOT_VERSION


def _get_home_bootstrap_snapshot_repository():
    return _get_home_bootstrap_snapshot_repository_impl()


def _read_sales_overview_cache(*, organization_id: UUID) -> dict[str, Any] | None:
    return _read_sales_overview_cache_impl(organization_id=organization_id)


def _write_sales_overview_cache(
    *,
    organization_id: UUID,
    company_items: list[dict[str, Any]],
    organization_users: list[dict[str, Any]],
) -> None:
    _write_sales_overview_cache_impl(
        organization_id=organization_id,
        company_items=company_items,
        organization_users=organization_users,
    )


def _load_home_bootstrap_snapshot_row(*, organization_id: UUID) -> dict[str, Any] | None:
    return _load_home_bootstrap_snapshot_row_impl(
        organization_id=organization_id,
        get_home_bootstrap_snapshot_repository=_get_home_bootstrap_snapshot_repository,
    )


def _upsert_home_bootstrap_snapshot_best_effort(
    *,
    organization_id: UUID,
    payload_json: dict[str, Any],
    generated_at: datetime,
) -> dict[str, Any] | None:
    return _upsert_home_bootstrap_snapshot_best_effort_impl(
        organization_id=organization_id,
        payload_json=payload_json,
        generated_at=generated_at,
        get_home_bootstrap_snapshot_repository=_get_home_bootstrap_snapshot_repository,
        json_safe_copy=_app_module()._json_safe_copy,
        snapshot_version=_HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        logger=_app_module().HOME_BOOTSTRAP_PERF_LOGGER,
    )


def _invalidate_home_bootstrap_snapshot_best_effort(*, organization_id: UUID | str | None) -> None:
    _invalidate_home_bootstrap_snapshot_best_effort_impl(
        organization_id=organization_id,
        clear_global_tracker_rows_cache=_app_module()._clear_global_tracker_rows_cache,
        get_home_bootstrap_snapshot_repository=_get_home_bootstrap_snapshot_repository,
        logger=_app_module().HOME_BOOTSTRAP_PERF_LOGGER,
    )


def _describe_home_bootstrap_snapshot_state(snapshot: dict[str, Any] | None) -> str:
    return _describe_home_bootstrap_snapshot_state_impl(
        snapshot,
        snapshot_version=_HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        parse_iso_datetime=_app_module()._parse_iso_datetime,
    )


def _is_home_bootstrap_snapshot_fresh(snapshot: dict[str, Any]) -> bool:
    return _is_home_bootstrap_snapshot_fresh_impl(
        snapshot,
        snapshot_version=_HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        parse_iso_datetime=_app_module()._parse_iso_datetime,
    )


def _is_valid_home_bootstrap_payload_shape(payload: dict[str, Any]) -> bool:
    return _is_valid_home_bootstrap_payload_shape_impl(
        payload,
        snapshot_version=_HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        parse_iso_datetime=_app_module()._parse_iso_datetime,
    )


def _build_home_bootstrap_tracker_first_page() -> dict[str, Any]:
    return _build_home_bootstrap_tracker_first_page_impl(
        load_global_tracker_rows=_app_module()._load_global_tracker_rows,
        filter_tracker_rows_for_global_scope=_app_module()._filter_tracker_rows_for_global_scope,
        page_size=_app_module()._HOME_BOOTSTRAP_TRACKER_PAGE_SIZE,
        model_to_json_dict=_model_to_json_dict_impl,
        to_tracker_entry_summary_model=_app_module()._to_tracker_entry_summary_model,
    )


def _build_home_bootstrap_payload(
    *,
    actor: SalesActor,
    request_id: str = "",
) -> dict[str, Any]:
    return _build_home_bootstrap_payload_impl(
        actor=actor,
        request_id=request_id,
        load_home_bootstrap_snapshot_row_fn=_load_home_bootstrap_snapshot_row,
        describe_home_bootstrap_snapshot_state_fn=_describe_home_bootstrap_snapshot_state,
        build_sales_claim_overview_payload_fn=_build_sales_claim_overview_payload,
        build_home_bootstrap_tracker_first_page_fn=_build_home_bootstrap_tracker_first_page,
        utc_now=_app_module()._utc_now,
        json_safe_copy=_app_module()._json_safe_copy,
        parse_iso_datetime=_app_module()._parse_iso_datetime,
        upsert_home_bootstrap_snapshot_best_effort_fn=_upsert_home_bootstrap_snapshot_best_effort,
        snapshot_version=_HOME_BOOTSTRAP_SNAPSHOT_VERSION,
        logger=_app_module().HOME_BOOTSTRAP_PERF_LOGGER,
    )


def _resolve_sales_actor(request: Request) -> SalesActor:
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None and auth_context.organization_id is not None:
        return SalesActor(
            organization_id=auth_context.organization_id,
            user_id=auth_context.local_user_id,
            email=str(auth_context.email or ""),
            display_name=str(auth_context.display_name or auth_context.email or "Console User"),
            role=str(auth_context.role or "org_member"),
        )

    identity = load_phase1_identity()
    return SalesActor(
        organization_id=identity.organization_id,
        user_id=identity.internal_user_id,
        email=bootstrap_platform_admin_email() or "phase1-internal-user@example.local",
        display_name="Internal Operations",
        role="platform_admin",
    )


def _resolve_transfer_target_user(
    actor: SalesActor,
    *,
    target_user_id: UUID | None = None,
    target_email: str = "",
) -> dict[str, Any]:
    active_users = list_local_users(organization_id=str(actor.organization_id), include_inactive=False)
    normalized_email = str(target_email or "").strip().lower()
    for item in active_users:
        if target_user_id is not None and str(item.get("id") or "").strip() == str(target_user_id):
            return item
        if normalized_email and str(item.get("email") or "").strip().lower() == normalized_email:
            return item
    raise ApiError(
        status_code=status.HTTP_404_NOT_FOUND,
        code="sales_claim_transfer_target_not_found",
        message="이관 대상 사용자를 찾을 수 없습니다.",
    )


def _to_sales_claim_model(item: Any) -> SalesClaimItem:
    payload = item.to_dict() if hasattr(item, "to_dict") else dict(item or {})
    return SalesClaimItem.model_validate(payload)


def _to_sales_claim_summary_project_model(item: dict[str, Any]) -> SalesClaimSummaryProjectItem:
    return _to_sales_claim_summary_project_model_impl(
        item,
        sales_claim_summary_project_item_cls=SalesClaimSummaryProjectItem,
    )


def _to_sales_claim_summary_user_model(item: dict[str, Any]) -> SalesClaimSummaryUserItem:
    return _to_sales_claim_summary_user_model_impl(
        item,
        sales_claim_summary_user_item_cls=SalesClaimSummaryUserItem,
        to_sales_claim_summary_project_model=_to_sales_claim_summary_project_model,
    )


def _to_auth_org_user_model(item: dict[str, Any]) -> AuthOrganizationUserItem:
    return _to_auth_org_user_model_impl(item, auth_org_user_item_cls=AuthOrganizationUserItem)


def _build_sales_claim_overview_payload(
    *,
    actor: SalesActor,
    request_id: str = "",
) -> dict[str, Any]:
    return _build_sales_claim_overview_payload_impl(
        actor=actor,
        request_id=request_id,
        get_sales_claim_repository=_get_sales_claim_repository,
        auth_is_enabled=auth_is_enabled,
        list_local_users_overview=list_local_users_overview,
        measure_stage=measure_stage,
        model_to_json_dict=_model_to_json_dict_impl,
        to_sales_claim_model=_to_sales_claim_model,
        to_auth_org_user_model=_to_auth_org_user_model,
    )


def _invalidate_sales_overview_cache(*, organization_id: UUID | str | None) -> None:
    from backend.api import app as app_module

    _invalidate_sales_overview_cache_impl(
        organization_id=organization_id,
        invalidate_home_bootstrap_snapshot_best_effort=app_module._invalidate_home_bootstrap_snapshot_best_effort,
    )


def _sales_claim_belongs_to_actor(item: Any, actor: SalesActor) -> bool:
    return _sales_claim_belongs_to_actor_impl(item, actor)


def _format_tracker_export_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = format_tracker_display_date(raw)
    if normalized != raw or len(normalized) == 10:
        return normalized
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return parsed.astimezone(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")


def _build_sales_claim_export_rows(*, claims: list[Any], tracker_repository: Any) -> list[dict[str, Any]]:
    return _build_sales_claim_export_rows_impl(
        claims=claims,
        tracker_repository=tracker_repository,
        format_tracker_export_date=_format_tracker_export_date,
    )


def _load_artifact_file_helpers() -> dict[str, Any]:
    from backend.services.artifact_files import build_tracking_download_workbook_bytes

    return {
        "build_tracking_download_workbook_bytes": build_tracking_download_workbook_bytes,
    }


def _record_download_audit_log(
    *,
    actor: SalesActor,
    download_scope: str,
    download_format: str,
    source_page: str,
    file_name: str,
) -> None:
    repository = _get_download_audit_log_repository()
    try:
        repository.create_log(
            organization_id=actor.organization_id,
            user_id=actor.user_id,
            user_email=actor.email,
            user_role=actor.role,
            download_scope=download_scope,
            download_format=download_format,
            source_page=source_page,
            file_name=file_name,
        )
    except DownloadAuditLogRepositoryError as exc:
        logging.getLogger("perf.download").warning(
            "download_audit_log_write_failed organization_id=%s user_id=%s user_email=%s scope=%s format=%s source_page=%s file_name=%s error=%s",
            str(actor.organization_id),
            str(actor.user_id or ""),
            str(actor.email or ""),
            download_scope,
            download_format,
            source_page,
            file_name,
            str(exc),
        )
