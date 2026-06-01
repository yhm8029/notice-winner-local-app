from __future__ import annotations

import asyncio
import calendar
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Request

from backend.api.schemas import ArtifactItem
from backend.api.schemas import ReportJobCreateRequest
from backend.api.schemas import RunCreateRequest
from backend.api.schemas import RunCreateResponse
from backend.api.schemas import RunDetailResponse
from backend.api.schemas import RunListItem
from backend.api.schemas import RunLogItem
from backend.api.support.runtime_common import ApiError
from backend.api.support.runtime_common import _conflict_error
from backend.api.support.runtime_common import _dispatch_background
from backend.api.support.runtime_common import _get_artifact_repository
from backend.api.support.runtime_common import _get_run_log_repository
from backend.api.support.runtime_common import _get_run_repository
from backend.api.support.runtime_common import _not_found
from backend.api.support.runtime_common import _repository_error
from backend.api.support.runtime_common import _validation_error
from backend.phase1_defaults import build_phase1_run_row
from backend.phase1_defaults import PROJECT_TRACKER_RUN_TYPE
from backend.phase1_defaults import VALID_RUN_TYPES
from backend.repositories import ArtifactRepositoryError
from backend.repositories import RunLogRepositoryError
from backend.repositories import RunRepositoryError
from backend.services.api_response_model_backend import model_to_dict as _model_to_dict_impl
from backend.services.related_notice_query_runtime import _filter_visible_runs
from backend.services.related_notice_query_runtime import _is_project_tracker_run_type
from backend.services.related_notice_query_runtime import _run_visible_in_operational_views
from backend.services.report_job_backend import build_report_job_command as _build_report_job_command_impl
from backend.services.report_job_backend import discover_gui_source_root as _discover_gui_source_root_impl
from backend.services.report_job_backend import resolve_report_script_path as _resolve_report_script_path_impl
from backend.services.report_job_backend import resolve_reports_root as _resolve_reports_root_impl
from backend.services.report_job_backend import trim_log_excerpt as _trim_log_excerpt_impl
from backend.services.report_job_store import get_report_job as get_stored_report_job
from backend.services.report_job_store import update_report_job
from backend.services.seed_collect import synthetic_debug_enabled

VALID_API_SCOPES = frozenset({"construction", "service", "goods", "all"})
VALID_RUN_STATUSES = frozenset({"queued", "running", "success", "failed", "cancelled"})
RUN_TERMINAL_STATUSES = frozenset({"success", "failed", "cancelled"})
DEMAND_ORG_INPUT_SPLIT_RE = re.compile(r"[,·ㄛ\n;|/ㄞ﹞王]+")
APP_ROOT = Path(__file__).resolve().parents[3]
REPORT_FILES = {
    "phase1-equivalence": "phase1-equivalence-report.json",
    "phase1-artifact-diff": "phase1-artifact-diff-report.json",
}
REPORT_SCRIPT_FILES = {
    "phase1-equivalence": "phase1_equivalence_runner.py",
    "phase1-artifact-diff": "phase1_artifact_diff_runner.py",
}
REPORT_SCRIPT_ENV_OVERRIDES = {
    "phase1-equivalence": "REPORT_SCRIPT_PHASE1_EQUIVALENCE",
    "phase1-artifact-diff": "REPORT_SCRIPT_PHASE1_ARTIFACT_DIFF",
}


def _load_run_execution_helpers():
    from backend.services.run_execution import queue_tracker_export_run_for_parent
    from backend.services.run_execution import safely_execute_project_tracker

    return queue_tracker_export_run_for_parent, safely_execute_project_tracker


def _load_artifact_file_helpers():
    from backend.services.artifact_files import resolve_artifact_path as resolve_artifact_path_impl

    return {
        "resolve_artifact_path": resolve_artifact_path_impl,
    }


def resolve_artifact_path(storage_path: str) -> Path:
    return _load_artifact_file_helpers()["resolve_artifact_path"](storage_path)


def _load_artifact_preview_helpers():
    from backend.services.artifact_preview_backend import build_artifact_preview_payload
    from backend.services.artifact_read_backend import build_artifact_item_payload
    from backend.services.artifact_read_backend import build_artifact_preview_payload_for_artifact_row

    return {
        "build_artifact_item_payload": build_artifact_item_payload,
        "build_artifact_preview_payload_for_artifact_row": build_artifact_preview_payload_for_artifact_row,
        "build_artifact_preview_payload": build_artifact_preview_payload,
    }


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


def _synthetic_debug_mode_enabled() -> bool:
    return synthetic_debug_enabled()


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


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"unsupported json type: {type(value)!r}")


def _encode_sse(*, event: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload, ensure_ascii=False, default=_json_default)
    return f"event: {event}\ndata: {body}\n\n"


def _to_uuid_or_none(value: Any) -> UUID | None:
    if value in (None, ""):
        return None
    return UUID(str(value))


def _to_run_create_response(row: dict[str, Any]) -> RunCreateResponse:
    return RunCreateResponse(
        id=UUID(str(row["id"])),
        status=str(row["status"]),
        run_type=str(row["run_type"]),
        parent_run_id=_to_uuid_or_none(row.get("parent_run_id")),
        created_at=row["created_at"],
    )


def _to_run_list_item(row: dict[str, Any]) -> RunListItem:
    return RunListItem(
        id=UUID(str(row["id"])),
        status=str(row["status"]),
        run_type=str(row["run_type"]),
        parent_run_id=_to_uuid_or_none(row.get("parent_run_id")),
        progress_stage=str(row.get("progress_stage") or ""),
        created_at=row["created_at"],
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
    )


def _to_run_detail(row: dict[str, Any]) -> RunDetailResponse:
    return RunDetailResponse(
        id=UUID(str(row["id"])),
        status=str(row["status"]),
        run_type=str(row["run_type"]),
        parent_run_id=_to_uuid_or_none(row.get("parent_run_id")),
        progress_stage=str(row.get("progress_stage") or ""),
        progress_current=int(row.get("progress_current") or 0),
        progress_total=int(row.get("progress_total") or 0),
        cancel_requested=bool(row.get("cancel_requested")),
        params=dict(row.get("params_json") or {}),
        summary=dict(row.get("summary_json") or {}),
        error=dict(row.get("error_json") or {}),
        created_at=row["created_at"],
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
    )


def _to_artifact_item(request: Request, row: dict[str, Any]) -> ArtifactItem:
    artifact_preview_helpers = _load_artifact_preview_helpers()
    return ArtifactItem.model_validate(
        artifact_preview_helpers["build_artifact_item_payload"](
            row=row,
            download_url=str(request.url_for("download_artifact", artifact_id=str(row["id"]))),
        )
    )


def _to_run_log_item(row: dict[str, Any]) -> RunLogItem:
    return RunLogItem(
        id=int(row["id"]),
        level=str(row["level"]),
        stage=str(row.get("stage") or ""),
        message=str(row["message"]),
        meta=dict(row.get("meta_json") or {}),
        created_at=row["created_at"],
    )


async def _stream_run_events(run_id: UUID, poll_interval_ms: int) -> Any:
    run_repository = _get_run_repository()
    log_repository = _get_run_log_repository()
    last_run_signature = ""
    seen_log_ids: set[int] = set()

    while True:
        try:
            run_row = run_repository.get_run(run_id)
        except RunRepositoryError as exc:
            yield _encode_sse(event="error", payload={"message": str(exc)})
            return

        if run_row is None:
            yield _encode_sse(event="error", payload={"message": f"run not found: {run_id}"})
            return

        run_payload = _to_run_detail(run_row).model_dump(mode="json")
        run_signature = json.dumps(run_payload, sort_keys=True, ensure_ascii=False)
        if run_signature != last_run_signature:
            yield _encode_sse(event="run", payload=run_payload)
            last_run_signature = run_signature

        try:
            log_rows, _next_cursor = log_repository.list_logs(run_id=run_id, cursor=None, limit=200)
        except RunLogRepositoryError as exc:
            yield _encode_sse(event="error", payload={"message": str(exc)})
            return

        new_logs = []
        for row in sorted(log_rows, key=lambda item: int(item["id"])):
            log_id = int(row["id"])
            if log_id in seen_log_ids:
                continue
            seen_log_ids.add(log_id)
            new_logs.append(_to_run_log_item(row).model_dump(mode="json"))
        for log_payload in new_logs:
            yield _encode_sse(event="log", payload=log_payload)

        if str(run_row.get("status") or "") in RUN_TERMINAL_STATUSES:
            yield _encode_sse(
                event="complete",
                payload={
                    "run_id": str(run_id),
                    "status": str(run_row.get("status") or ""),
                    "progress_stage": str(run_row.get("progress_stage") or ""),
                },
            )
            return

        await asyncio.sleep(max(0.25, poll_interval_ms / 1000.0))


def _get_visible_artifact(artifact_id: UUID) -> dict[str, Any]:
    artifact_repository = _get_artifact_repository()
    try:
        artifact = artifact_repository.get_artifact(artifact_id)
    except ArtifactRepositoryError as exc:
        _repository_error(str(exc))

    if artifact is None:
        _not_found(f"artifact not found: {artifact_id}")

    run_repository = _get_run_repository()
    try:
        run_row = run_repository.get_run(UUID(str(artifact["run_id"])))
    except RunRepositoryError as exc:
        _repository_error(str(exc))

    if run_row is None or not _run_visible_in_operational_views(run_row):
        _not_found(f"artifact not found: {artifact_id}")

    return artifact


def _build_artifact_preview_payload(*, artifact_row: dict[str, Any], limit: int) -> dict[str, Any]:
    artifact_preview_helpers = _load_artifact_preview_helpers()
    return artifact_preview_helpers["build_artifact_preview_payload_for_artifact_row"](
        artifact_row=artifact_row,
        limit=limit,
        resolve_artifact_path_fn=resolve_artifact_path,
        build_artifact_preview_payload_fn=artifact_preview_helpers["build_artifact_preview_payload"],
        unsupported_preview_fn=_conflict_error,
    )


def _normalize_demand_org_input(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parts = [
        re.sub(r"\s+", " ", part).strip()
        for part in DEMAND_ORG_INPUT_SPLIT_RE.split(raw)
        if str(part or "").strip()
    ]
    if not parts:
        return ""
    normalized_parts: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized_parts.append(part)
    return ", ".join(normalized_parts)


def _dump_request_params(payload: RunCreateRequest) -> dict[str, Any]:
    params_dict = _model_to_dict_impl(payload.params)
    params_dict["demand_org"] = _normalize_demand_org_input(params_dict.get("demand_org"))
    if payload.advanced_options:
        params_dict["_advanced_options"] = payload.advanced_options
    return params_dict


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


def _resolve_reports_root() -> Path:
    raw_root = os.getenv("REPORTS_ROOT", "").strip()
    return _resolve_reports_root_impl(raw_root=raw_root, app_root=APP_ROOT)


def _resolve_report_script_path(report_name: str) -> Path:
    return _resolve_report_script_path_impl(
        report_name=report_name,
        app_root=APP_ROOT,
        report_script_files=REPORT_SCRIPT_FILES,
        report_script_env_overrides=REPORT_SCRIPT_ENV_OVERRIDES,
        env_get_fn=os.getenv,
        not_found_fn=_not_found,
    )


def _discover_gui_source_root(explicit: str = "") -> Path | None:
    return _discover_gui_source_root_impl(explicit=explicit, app_root=APP_ROOT, env_get_fn=os.getenv)


def _trim_log_excerpt(text: str, max_chars: int = 4000) -> str:
    return _trim_log_excerpt_impl(text, max_chars=max_chars)


def _build_report_job_command(payload: ReportJobCreateRequest) -> tuple[list[str], Path, Path | None, str]:
    return _build_report_job_command_impl(
        payload,
        sys_executable=sys.executable,
        app_root=APP_ROOT,
        report_files=REPORT_FILES,
        resolve_reports_root_fn=_resolve_reports_root,
        resolve_report_script_path_fn=_resolve_report_script_path,
        discover_gui_source_root_fn=_discover_gui_source_root,
        validation_error_fn=_validation_error,
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
                "error": ""
                if completed.returncode == 0
                else _trim_log_excerpt(combined_output.splitlines()[-1] if combined_output else "report job failed"),
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
