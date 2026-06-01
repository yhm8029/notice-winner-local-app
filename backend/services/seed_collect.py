from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from uuid import UUID

from .native_seed_backend import AllEndpointsQuotaExceededError as NativeQuotaError
from .native_seed_backend import ATTACHMENT_FIELD_COUNT
from .native_seed_backend import fetch_seed_rows_with_diagnostics
from .native_seed_backend import resolve_service_key as resolve_native_service_key
from .native_seed_backend import SeedFetchDiagnostics
from .native_seed_backend import write_seed_csv as write_seed_csv_native
from .run_workspace import seed_csv_path_for_run

ATTACHMENT_SEED_HEADERS = tuple(
    field_name
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1)
    for field_name in (f"spec_doc_url_{index}", f"spec_doc_file_name_{index}")
)

SEED_HEADERS = (
    "bid_no",
    "bid_ord",
    "project_name",
    "org_name",
    "announce_date",
    "g2b_verified",
    "bid_ntce_url",
    "bid_ntce_dtl_url",
    "notice_officer_name",
    "notice_officer_tel",
    "notice_officer_email",
    "demand_officer_name",
    "demand_officer_email",
    "presmpt_prce",
    "service_name",
    "sucsfbid_method_name",
) + ATTACHMENT_SEED_HEADERS
VALID_COLLECT_MODES = frozenset({"auto", "native", "synthetic"})
SYNTHETIC_DEBUG_ENV_NAMES = (
    "PROJECT_TRACKER_ENABLE_SYNTHETIC_DEBUG",
    "WINNER_PIPELINE_ENABLE_SYNTHETIC_DEBUG",
    "ENABLE_SYNTHETIC_DEBUG",
)


@dataclass(frozen=True)
class CollectedSeedOutput:
    rows: list[dict[str, str]]
    seed_csv_path: Path | None
    collect_backend: str
    quota_fallback_used: bool = False
    diagnostics: SeedFetchDiagnostics | None = None


def resolve_collect_mode(params: dict[str, Any]) -> str:
    advanced_options = dict(params.get("_advanced_options") or {})
    raw_collect_mode = (
        advanced_options.get("collect_mode")
        or os.getenv("PROJECT_TRACKER_COLLECT_MODE", "").strip()
        or os.getenv("WINNER_PIPELINE_COLLECT_MODE", "auto")
    )
    raw_value = str(raw_collect_mode).strip().lower()
    if raw_value == "synthetic" and not synthetic_debug_enabled():
        return "auto"
    if raw_value not in VALID_COLLECT_MODES:
        return "auto"
    return raw_value


def synthetic_debug_enabled() -> bool:
    for env_name in SYNTHETIC_DEBUG_ENV_NAMES:
        raw_value = str(os.getenv(env_name, "")).strip().lower()
        if raw_value in {"1", "true", "yes", "on"}:
            return True
    return False


def collect_seed_rows_for_run(
    *,
    run_id: UUID,
    params: dict[str, Any],
    progress_cb: Callable[[str], None] | None = None,
) -> CollectedSeedOutput:
    return collect_seed_rows_with_params(
        params=params,
        progress_cb=progress_cb,
        persist_run_id=run_id,
    )


def collect_seed_rows_with_params(
    *,
    params: dict[str, Any],
    progress_cb: Callable[[str], None] | None = None,
    persist_run_id: UUID | None = None,
) -> CollectedSeedOutput:
    mode = resolve_collect_mode(params)
    if mode == "synthetic":
        if not synthetic_debug_enabled():
            raise RuntimeError("synthetic collect mode is disabled")
        return _collect_synthetic_seed_rows(run_id=persist_run_id, params=params)

    try:
        return _collect_native_seed_rows(run_id=persist_run_id, params=params, progress_cb=progress_cb)
    except Exception as exc:
        if mode == "native" or not synthetic_debug_enabled():
            raise
        if progress_cb is not None:
            progress_cb(f"collect(native) unavailable; fallback to synthetic ({exc})")
        return _collect_synthetic_seed_rows(run_id=persist_run_id, params=params)


def load_seed_rows_for_run(run_id: UUID) -> list[dict[str, str]]:
    seed_csv_path = seed_csv_path_for_run(run_id)
    if not seed_csv_path.exists():
        return []
    with seed_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return [{key: str(row.get(key, "") or "") for key in SEED_HEADERS} for row in reader]


def _collect_native_seed_rows(
    *,
    run_id: UUID | None,
    params: dict[str, Any],
    progress_cb: Callable[[str], None] | None,
) -> CollectedSeedOutput:
    service_key = resolve_native_service_key("")
    if not service_key:
        raise RuntimeError("G2B service key not found in local env")

    start_date = str(params.get("start_date") or "").strip()
    end_date = str(params.get("end_date") or "").strip()
    bid_no_filter = str(params.get("bid_no") or "").strip()
    title_filter = str(params.get("notice_title") or "").strip()
    demand_org_filter = str(params.get("demand_org") or "").strip()
    rows_per_page = int(params.get("rows_per_page") or 100)
    max_pages = int(params.get("max_pages") or 3)
    endpoint_mode = str(params.get("api_scope") or "construction").strip() or "construction"

    prefixed_progress = _prefix_progress(progress_cb, "collect(native)")
    try:
        result = fetch_seed_rows_with_diagnostics(
            service_key=service_key,
            start_date=start_date,
            end_date=end_date,
            bid_no_filter=bid_no_filter,
            title_filter=title_filter,
            demand_org_filter=demand_org_filter,
            rows_per_page=rows_per_page,
            max_pages=max_pages,
            endpoint_mode=endpoint_mode,
            progress_cb=prefixed_progress,
        )
    except NativeQuotaError:
        raise RuntimeError("collect(native) quota exceeded on all attempted endpoints")

    rows = result.rows
    if not rows:
        raise RuntimeError("collect(native) returned no seed rows")

    seed_csv_path: Path | None = None
    if run_id is not None:
        seed_csv_path = seed_csv_path_for_run(run_id)
        write_seed_csv_native(rows, seed_csv_path)
    return CollectedSeedOutput(
        rows=[_normalize_seed_row(row) for row in rows],
        seed_csv_path=seed_csv_path,
        collect_backend="native_api",
        quota_fallback_used=False,
        diagnostics=result.diagnostics,
    )


def _collect_synthetic_seed_rows(*, run_id: UUID | None, params: dict[str, Any]) -> CollectedSeedOutput:
    default_run_key = str(run_id).replace("-", "")[:12].upper() if run_id is not None else "ADHOCSEED"
    bid_no = str(params.get("bid_no") or f"WNP{default_run_key}").strip()
    notice_title = str(params.get("notice_title") or "Project Tracker").strip()
    demand_org = str(params.get("demand_org") or "Internal Demand Organization").strip()
    announce_date = str(params.get("end_date") or params.get("start_date") or "20250101").strip()

    rows = [
        {
            "bid_no": bid_no,
            "bid_ord": "000",
            "project_name": notice_title,
            "org_name": demand_org,
            "announce_date": announce_date,
            "g2b_verified": "N",
            "bid_ntce_url": "",
            "bid_ntce_dtl_url": "",
            "notice_officer_name": "",
            "notice_officer_tel": "",
            "notice_officer_email": "",
            "demand_officer_name": "",
            "demand_officer_email": "",
            "presmpt_prce": "",
            "service_name": "",
            "sucsfbid_method_name": "",
        },
        {
            "bid_no": bid_no,
            "bid_ord": "001",
            "project_name": f"{notice_title} Follow-up",
            "org_name": demand_org,
            "announce_date": announce_date,
            "g2b_verified": "N",
            "bid_ntce_url": "",
            "bid_ntce_dtl_url": "",
            "notice_officer_name": "",
            "notice_officer_tel": "",
            "notice_officer_email": "",
            "demand_officer_name": "",
            "demand_officer_email": "",
            "presmpt_prce": "",
            "service_name": "",
            "sucsfbid_method_name": "",
        },
    ]
    for row in rows:
        for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
            row[f"spec_doc_url_{index}"] = ""
            row[f"spec_doc_file_name_{index}"] = ""

    seed_csv_path: Path | None = None
    if run_id is not None:
        seed_csv_path = seed_csv_path_for_run(run_id)
        _write_seed_csv(rows=rows, seed_csv_path=seed_csv_path)
    return CollectedSeedOutput(
        rows=rows,
        seed_csv_path=seed_csv_path,
        collect_backend="synthetic",
        quota_fallback_used=False,
        diagnostics=None,
    )


def _write_seed_csv(*, rows: list[dict[str, str]], seed_csv_path: Path) -> None:
    seed_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with seed_csv_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(SEED_HEADERS))
        writer.writeheader()
        writer.writerows(rows)


def _normalize_seed_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: str(row.get(key, "") or "") for key in SEED_HEADERS}


def _prefix_progress(progress_cb: Callable[[str], None] | None, prefix: str):
    if progress_cb is None:
        return None

    def _inner(message: str) -> None:
        progress_cb(f"{prefix}: {message}")

    return _inner
