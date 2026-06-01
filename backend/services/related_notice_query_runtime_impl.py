from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from backend.phase1_defaults import PROJECT_TRACKER_RUN_TYPE
from backend.phase1_defaults import PROJECT_TRACKER_RUN_TYPES
from backend.phase1_defaults import TRACKER_EXPORT_RUN_TYPE
from backend.services.seed_collect import synthetic_debug_enabled
from .related_notice_query_runtime_query_helpers import *  # noqa: F403
from . import related_notice_query_runtime_report_helpers as _report_helpers


def _synthetic_debug_mode_enabled() -> bool:
    return synthetic_debug_enabled()


def _requested_collect_mode_from_row(row: dict[str, Any]) -> str:
    params = dict(row.get("params_json") or {})
    advanced_options = dict(params.get("_advanced_options") or {})
    return str(advanced_options.get("collect_mode") or "").strip().lower()


def _is_project_tracker_run_type(run_type: str) -> bool:
    return str(run_type or "").strip() in PROJECT_TRACKER_RUN_TYPES


def _run_type_matches_filter(actual_run_type: str, requested_run_type: str) -> bool:
    actual = str(actual_run_type or "").strip()
    requested = str(requested_run_type or "").strip()
    if not requested:
        return True
    if requested == PROJECT_TRACKER_RUN_TYPE:
        return actual in PROJECT_TRACKER_RUN_TYPES
    return actual == requested


def _run_uses_synthetic_backend(row: dict[str, Any]) -> bool:
    run_type = str(row.get("run_type") or "").strip()
    requested_collect_mode = _requested_collect_mode_from_row(row)
    summary = dict((row.get("summary_json") or {}).get("output") or {})

    if requested_collect_mode == "synthetic":
        return True

    if _is_project_tracker_run_type(run_type):
        if str(summary.get("requested_collect_mode") or "").strip().lower() == "synthetic":
            return True
        stage_backends = dict(summary.get("stage_backends") or {})
        if any(str(value or "").strip().lower() == "synthetic" for value in stage_backends.values()):
            return True
        return any(
            str(summary.get(field_name) or "").strip().lower() == "synthetic"
            for field_name in ("collect_backend", "filter_backend", "rescan_backend", "export_backend")
        )

    if run_type == TRACKER_EXPORT_RUN_TYPE:
        return str(summary.get("tracker_export_backend") or "").strip().lower() == "synthetic"

    return False


def _run_visible_in_operational_views(row: dict[str, Any]) -> bool:
    return _synthetic_debug_mode_enabled() or not _run_uses_synthetic_backend(row)


def _filter_visible_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if _synthetic_debug_mode_enabled():
        return [dict(row) for row in rows]
    return [dict(row) for row in rows if _run_visible_in_operational_views(row)]


def _matches_run_filters(
    row: dict[str, Any],
    *,
    status_value: str,
    run_type: str,
    parent_run_id: UUID | None,
    date_from: str,
    date_to: str,
) -> bool:
    if status_value and str(row.get("status") or "") != status_value:
        return False
    if not _run_type_matches_filter(str(row.get("run_type") or ""), run_type):
        return False
    if parent_run_id is not None and str(row.get("parent_run_id") or "") != str(parent_run_id):
        return False

    created_at = row.get("created_at")
    if isinstance(created_at, datetime):
        created_date = created_at.strftime("%Y-%m-%d")
    else:
        created_date = str(created_at or "")[:10]
    if date_from and created_date < date_from:
        return False
    if date_to and created_date > date_to:
        return False
    return True


class ApiError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def _is_yyyymmdd(value: str) -> bool:
    return len(value) == 8 and value.isdigit()


def _normalize_yyyymmdd(value: str) -> str | None:
    raw = str(value or "").strip()
    if not _is_yyyymmdd(raw):
        return None
    year = int(raw[:4])
    month = int(raw[4:6])
    day = int(raw[6:8])
    if month < 1 or month > 12 or day < 1:
        return None
    last_day = calendar.monthrange(year, month)[1]
    if day > last_day:
        day = last_day
    return f"{year:04d}{month:02d}{day:02d}"


def _is_iso_date(value: str) -> bool:
    return len(value) == 10 and value[4] == "-" and value[7] == "-" and value.replace("-", "").isdigit()


def _validate_run_create_request(payload: RunCreateRequest) -> None:
    params = payload.params
    requested_collect_mode = str((payload.advanced_options or {}).get("collect_mode") or "").strip().lower()

    if payload.run_type != PROJECT_TRACKER_RUN_TYPE:
        _validation_error(f"run_type must be {PROJECT_TRACKER_RUN_TYPE}")

    normalized_start_date = _normalize_yyyymmdd(params.start_date)
    if normalized_start_date is None:
        _validation_error("start_date must be YYYYMMDD")
    params.start_date = normalized_start_date

    normalized_end_date = _normalize_yyyymmdd(params.end_date)
    if normalized_end_date is None:
        _validation_error("end_date must be YYYYMMDD")
    params.end_date = normalized_end_date

    if params.contract_date_hint:
        normalized_contract_date_hint = _normalize_yyyymmdd(params.contract_date_hint)
        if normalized_contract_date_hint is None:
            _validation_error("contract_date_hint must be YYYYMMDD")
        params.contract_date_hint = normalized_contract_date_hint

    if params.start_date > params.end_date:
        _validation_error("start_date must be less than or equal to end_date")

    if not (params.bid_no.strip() or params.notice_title.strip() or params.demand_org.strip()):
        _validation_error("at least one of bid_no, notice_title, demand_org is required")

    if params.rows_per_page < 1:
        _validation_error("rows_per_page must be greater than or equal to 1")

    if params.max_pages < 1:
        _validation_error("max_pages must be greater than or equal to 1")

    if params.api_scope not in VALID_API_SCOPES:
        _validation_error("api_scope must be one of construction, service, goods, all")

    if requested_collect_mode == "synthetic" and not _synthetic_debug_mode_enabled():
        _validation_error("collect_mode synthetic is only available in debug mode")


def _validate_tracker_patch_request(payload: TrackerEntryPatchRequest) -> None:
    if payload.field_name not in TRACKER_EDITABLE_FIELDS:
        allowed = ", ".join(TRACKER_EDITABLE_FIELDS)
        _validation_error(f"field_name must be one of {allowed}")

    if payload.change_source not in TRACKER_CHANGE_SOURCES:
        allowed = ", ".join(sorted(TRACKER_CHANGE_SOURCES))
        _validation_error(f"change_source must be one of {allowed}")


def _validate_run_list_filters(*, status_value: str, run_type: str, date_from: str, date_to: str) -> None:
    if status_value and status_value not in VALID_RUN_STATUSES:
        allowed = ", ".join(sorted(VALID_RUN_STATUSES))
        _validation_error(f"status must be one of {allowed}")

    if run_type and run_type not in VALID_RUN_TYPES:
        allowed = ", ".join(sorted(VALID_RUN_TYPES))
        _validation_error(f"run_type must be one of {allowed}")

    if date_from and not _is_iso_date(date_from):
        _validation_error("from must be YYYY-MM-DD")

    if date_to and not _is_iso_date(date_to):
        _validation_error("to must be YYYY-MM-DD")

    if date_from and date_to and date_from > date_to:
        _validation_error("from must be less than or equal to to")


def _validation_error(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="validation_error",
        message=message,
    )


def _not_found(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_404_NOT_FOUND,
        code="not_found",
        message=message,
    )


def _repository_error(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="repository_error",
        message=message,
    )


def _resolve_tracker_patch_actor(
    request: Request,
    payload: TrackerEntryPatchRequest,
) -> tuple[UUID | None, str]:
    actor_user_id = payload.actor_user_id
    actor_label = payload.actor_label.strip()
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None:
        if actor_user_id is None and auth_context.local_user_id is not None:
            actor_user_id = auth_context.local_user_id
        if not actor_label:
            actor_label = auth_context.display_name or auth_context.email
    if actor_user_id is None and not actor_label:
        _validation_error("actor_user_id or actor_label is required")
    return actor_user_id, actor_label


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


def _resolve_request_organization_id(request: Request) -> UUID:
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is not None and auth_context.organization_id is not None:
        return auth_context.organization_id
    return load_phase1_identity().organization_id


def _to_auth_audit_log_model(item: dict[str, Any]) -> AuthAuditLogItem:
    return AuthAuditLogItem.model_validate(item)


def _to_sales_claim_summary_project_model(item: dict[str, Any]) -> SalesClaimSummaryProjectItem:
    return SalesClaimSummaryProjectItem.model_validate(item)


def _to_sales_claim_summary_user_model(item: dict[str, Any]) -> SalesClaimSummaryUserItem:
    payload = dict(item or {})
    payload["projects"] = [
        _to_sales_claim_summary_project_model(project)
        for project in list(payload.get("projects") or [])
    ]
    return SalesClaimSummaryUserItem.model_validate(payload)


def _is_missing_related_notice_cache_table_error(message: str) -> bool:
    lowered = str(message or "").lower()
    if "project_related_notice_cache" not in lowered:
        return False
    return any(
        token in lowered
        for token in (
            "could not find the table",
            "schema cache",
            "relation",
            "does not exist",
        )
    )


def _is_missing_tracker_change_events_table_error(message: str) -> bool:
    lowered = str(message or "").lower()
    if "tracker_change_events" not in lowered:
        return False
    return any(
        token in lowered
        for token in (
            "could not find the table",
            "schema cache",
            "relation",
            "does not exist",
        )
    )


def _conflict_error(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_409_CONFLICT,
        code="conflict",
        message=message,
    )


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _model_to_json_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if hasattr(model, "json"):
        return json.loads(model.json())
    return _model_to_dict(model)


def _resolve_reports_root() -> Path:
    return _report_helpers._resolve_reports_root(frontend_dir=FRONTEND_DIR)


def _load_report_payload(report_name: str) -> dict[str, Any]:
    file_name = REPORT_FILES.get(report_name)
    if not file_name:
        _not_found(f"report not found: {report_name}")
    report_path = _resolve_reports_root() / str(file_name)
    if not report_path.exists():
        _not_found(f"report file not found: {report_name}")
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _repository_error(f"report is not valid json: {report_name} ({exc})")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_report_script_path(report_name: str) -> Path:
    return _report_helpers._resolve_report_script_path(
        report_name,
        app_root=APP_ROOT,
        report_script_files=REPORT_SCRIPT_FILES,
        report_script_env_overrides=REPORT_SCRIPT_ENV_OVERRIDES,
        not_found_fn=_not_found,
    )


def _discover_gui_source_root(explicit: str = "") -> Path | None:
    return _report_helpers._discover_gui_source_root(explicit, app_root=APP_ROOT)


def _trim_log_excerpt(text: str, max_chars: int = 4000) -> str:
    return _report_helpers._trim_log_excerpt(text, max_chars=max_chars)


def _build_report_job_command(payload: ReportJobCreateRequest) -> tuple[list[str], Path, Path | None, str]:
    return _report_helpers._build_report_job_command(
        payload,
        app_root=APP_ROOT,
        frontend_dir=FRONTEND_DIR,
        report_files=REPORT_FILES,
        report_script_files=REPORT_SCRIPT_FILES,
        report_script_env_overrides=REPORT_SCRIPT_ENV_OVERRIDES,
        validation_error_fn=_validation_error,
        not_found_fn=_not_found,
    )


def _run_report_job(job_id: UUID) -> None:
    row = get_stored_report_job(job_id)
    if row is None:
        return
    update_report_job(job_id, {"status": "running", "started_at": _utc_now()})
    try:
        completed = subprocess.run(
            list(row["command"]),
            cwd=str(APP_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        combined_output = "\n".join(
            part.strip() for part in ((completed.stdout or ""), (completed.stderr or "")) if part.strip()
        )
        summary: dict[str, Any] = {}
        output_path = Path(str(row.get("output_path") or ""))
        if output_path.exists():
            try:
                summary = dict(_load_report_payload(str(row["report_name"])).get("summary") or {})
            except ApiError:
                summary = {}
        status_value = "success" if completed.returncode == 0 else "failed"
        update_report_job(
            job_id,
            {
                "status": status_value,
                "finished_at": _utc_now(),
                "exit_code": completed.returncode,
                "summary": summary,
                "log_excerpt": _trim_log_excerpt(combined_output),
                "error": "" if completed.returncode == 0 else _trim_log_excerpt(combined_output.splitlines()[-1] if combined_output else "report job failed"),
            },
        )
    except Exception as exc:
        update_report_job(
            job_id,
            {
                "status": "failed",
                "finished_at": _utc_now(),
                "exit_code": -1,
                "summary": {},
                "log_excerpt": _trim_log_excerpt(str(exc)),
                "error": str(exc),
            },
        )

def _collect_all_runs() -> list[dict[str, Any]]:
    run_repository = _get_run_repository()
    page = 1
    page_size = 200
    items: list[dict[str, Any]] = []
    total = 0
    while True:
        try:
            batch, total = run_repository.list_runs(
                page=page,
                page_size=page_size,
                status="",
                run_type="",
                parent_run_id=None,
                date_from="",
                date_to="",
            )
        except RunRepositoryError as exc:
            if page > 1 and _is_range_not_satisfiable_error(str(exc)):
                return _filter_visible_runs(items)
            raise
        items.extend(batch)
        if not batch or len(items) >= total:
            return _filter_visible_runs(items)
        page += 1


def _collect_all_tracker_entries() -> list[dict[str, Any]]:
    tracker_repository = _get_tracker_repository()
    visible_run_ids = {str(row.get("id") or "") for row in _collect_all_runs()}
    page = 1
    page_size = 1000
    items: list[dict[str, Any]] = []
    total = 0
    while True:
        try:
            batch, total = tracker_repository.list_entries(
                page=page,
                page_size=page_size,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        except TrackerEntryRepositoryError as exc:
            if page > 1 and _is_range_not_satisfiable_error(str(exc)):
                return items
            raise
        if _synthetic_debug_mode_enabled():
            items.extend(batch)
        else:
            for entry in batch:
                source_run_id = str(entry.get("source_run_id") or "").strip()
                source_tracker_run_id = str(entry.get("source_tracker_run_id") or "").strip()
                if source_run_id and source_run_id not in visible_run_ids:
                    continue
                if source_tracker_run_id and source_tracker_run_id not in visible_run_ids:
                    continue
                items.append(entry)
        if not batch or len(items) >= total:
            return items
        page += 1


def _is_range_not_satisfiable_error(message: str) -> bool:
    normalized = str(message or "").strip().lower()
    return "requested range not satisfiable" in normalized or "offset of" in normalized


def _project_source_notice_keys(project: dict[str, Any]) -> set[tuple[str, str]]:
    cached = project.get("_source_notice_keys")
    if isinstance(cached, set):
        return cached

    target_key = str(project.get("_project_match_key") or "").strip()
    keys: set[tuple[str, str]] = set()
    artifact_repository = _get_artifact_repository()
    for run_row in _project_source_runs(project):
        try:
            run_id = UUID(str(run_row["id"]))
        except Exception:
            continue
        try:
            artifacts = artifact_repository.list_artifacts(run_id=run_id)
        except ArtifactRepositoryError as exc:
            _repository_error(str(exc))
        for artifact in artifacts:
            if str(artifact.get("artifact_type") or "").strip() != "seed_csv":
                continue
            storage_path = str(artifact.get("storage_path") or "").strip()
            if not storage_path:
                continue
            for row in _load_seed_rows_from_artifact_path(storage_path):
                bid_no = str(row.get("bid_no") or "").strip()
                bid_ord = str(row.get("bid_ord") or "").strip()
                if not bid_no:
                    continue
                project_name = str(row.get("project_name") or "").strip()
                candidate_search_name = _project_search_name(project_name)
                candidate_key = _project_match_key(candidate_search_name or project_name)
                if target_key and candidate_key != target_key:
                    continue
                keys.add((bid_no, bid_ord))
    project["_source_notice_keys"] = keys
    return keys
