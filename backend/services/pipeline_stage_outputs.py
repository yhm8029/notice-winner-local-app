from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from uuid import UUID

from .native_export_backend import run_post_collect_native
from .native_filter_backend import run_collect_native
from .native_rescan_backend import run_internal_nav_native
from .run_workspace import collect_candidates_csv_path_for_run
from .run_workspace import internal_nav_csv_path_for_run
from .run_workspace import post_collect_csv_path_for_run
from .seed_collect import load_seed_rows_for_run
from .seed_collect import synthetic_debug_enabled


@dataclass(frozen=True)
class FilterStageOutput:
    candidate_csv_path: Path
    row_count: int
    stage_backend: str


@dataclass(frozen=True)
class RescanStageOutput:
    internal_nav_csv_path: Path
    row_count: int
    stage_backend: str


@dataclass(frozen=True)
class ExportStageOutput:
    post_collect_csv_path: Path
    row_count: int
    stage_backend: str
    primary_bid_no: str


def run_filter_stage_for_run(
    *,
    run_id: UUID,
    params: dict[str, Any],
    collect_backend: str,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> FilterStageOutput:
    candidate_csv_path = collect_candidates_csv_path_for_run(run_id)

    if collect_backend == "synthetic":
        if not synthetic_debug_enabled():
            raise RuntimeError("synthetic filter stage is disabled")
        rows = _build_synthetic_candidate_rows(seed_rows=load_seed_rows_for_run(run_id))
        _write_csv(candidate_csv_path, rows=rows, fieldnames=_candidate_fieldnames())
        return FilterStageOutput(
            candidate_csv_path=candidate_csv_path,
            row_count=len(rows),
            stage_backend="synthetic",
        )
    try:
        run_collect_native(
            _seed_csv_path(run_id),
            candidate_csv_path,
            advanced_options=dict(params.get("_advanced_options") or {}),
            progress_cb=_prefix_progress(progress_cb, "filter(native)"),
            should_stop=should_stop,
        )
        row_count = _count_csv_rows(candidate_csv_path)
        return FilterStageOutput(
            candidate_csv_path=candidate_csv_path,
            row_count=row_count,
            stage_backend="native_filter",
        )
    except Exception as exc:
        if not synthetic_debug_enabled():
            raise
        if progress_cb is not None:
            progress_cb(f"filter(native) unavailable; fallback to synthetic ({exc})")
        rows = _build_synthetic_candidate_rows(seed_rows=load_seed_rows_for_run(run_id))
        _write_csv(candidate_csv_path, rows=rows, fieldnames=_candidate_fieldnames())
        return FilterStageOutput(
            candidate_csv_path=candidate_csv_path,
            row_count=len(rows),
            stage_backend="synthetic",
        )


def run_rescan_stage_for_run(
    *,
    run_id: UUID,
    params: dict[str, Any],
    filter_backend: str,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> RescanStageOutput:
    internal_nav_csv_path = internal_nav_csv_path_for_run(run_id)

    if filter_backend == "synthetic":
        if not synthetic_debug_enabled():
            raise RuntimeError("synthetic rescan stage is disabled")
        rows = _build_synthetic_internal_nav_rows(candidate_csv_path=collect_candidates_csv_path_for_run(run_id))
        _write_csv(internal_nav_csv_path, rows=rows, fieldnames=_internal_nav_fieldnames())
        return RescanStageOutput(
            internal_nav_csv_path=internal_nav_csv_path,
            row_count=len(rows),
            stage_backend="synthetic",
        )
    try:
        run_internal_nav_native(
            collect_candidates_csv_path_for_run(run_id),
            internal_nav_csv_path,
            progress_cb=_prefix_progress(progress_cb, "rescan(native)"),
            should_stop=should_stop,
        )
        row_count = _count_csv_rows(internal_nav_csv_path)
        return RescanStageOutput(
            internal_nav_csv_path=internal_nav_csv_path,
            row_count=row_count,
            stage_backend="native_rescan",
        )
    except Exception as exc:
        if not synthetic_debug_enabled():
            raise
        if progress_cb is not None:
            progress_cb(f"rescan(native) unavailable; fallback to synthetic ({exc})")
        rows = _build_synthetic_internal_nav_rows(candidate_csv_path=collect_candidates_csv_path_for_run(run_id))
        _write_csv(internal_nav_csv_path, rows=rows, fieldnames=_internal_nav_fieldnames())
        return RescanStageOutput(
            internal_nav_csv_path=internal_nav_csv_path,
            row_count=len(rows),
            stage_backend="synthetic",
        )


def run_export_stage_for_run(
    *,
    run_id: UUID,
    params: dict[str, Any],
    rescan_backend: str,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> ExportStageOutput:
    post_collect_csv_path = post_collect_csv_path_for_run(run_id)

    if rescan_backend == "synthetic":
        if not synthetic_debug_enabled():
            raise RuntimeError("synthetic export stage is disabled")
        rows = _build_synthetic_post_collect_rows(internal_nav_csv_path=internal_nav_csv_path_for_run(run_id))
        _write_csv(post_collect_csv_path, rows=rows, fieldnames=_post_collect_fieldnames())
        return ExportStageOutput(
            post_collect_csv_path=post_collect_csv_path,
            row_count=len(rows),
            stage_backend="synthetic",
            primary_bid_no=str(rows[0]["bid_no"]) if rows else "",
        )
    try:
        actual_path = run_post_collect_native(
            internal_nav_csv_path_for_run(run_id),
            post_collect_csv_path,
            params=params,
            progress_cb=_prefix_progress(progress_cb, "export(native)"),
            should_stop=should_stop,
        )
        row_count = _count_csv_rows(actual_path)
        primary_bid_no = _first_csv_value(actual_path, "bid_no")
        return ExportStageOutput(
            post_collect_csv_path=Path(actual_path),
            row_count=row_count,
            stage_backend="native_export",
            primary_bid_no=primary_bid_no,
        )
    except Exception as exc:
        if not synthetic_debug_enabled():
            raise
        if progress_cb is not None:
            progress_cb(f"export(native) unavailable; fallback to synthetic ({exc})")
        rows = _build_synthetic_post_collect_rows(internal_nav_csv_path=internal_nav_csv_path_for_run(run_id))
        _write_csv(post_collect_csv_path, rows=rows, fieldnames=_post_collect_fieldnames())
        return ExportStageOutput(
            post_collect_csv_path=post_collect_csv_path,
            row_count=len(rows),
            stage_backend="synthetic",
            primary_bid_no=str(rows[0]["bid_no"]) if rows else "",
        )


def _seed_csv_path(run_id: UUID) -> Path:
    from .run_workspace import seed_csv_path_for_run

    return seed_csv_path_for_run(run_id)


def _build_synthetic_candidate_rows(*, seed_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, seed_row in enumerate(seed_rows, start=1):
        bid_no = str(seed_row.get("bid_no") or "").strip()
        bid_ord = str(seed_row.get("bid_ord") or "").strip() or "000"
        project_name = str(seed_row.get("project_name") or "").strip()
        project_name_norm = _slugify(project_name)
        url = f"https://example.internal/{project_name_norm or 'notice'}/{index}"
        rows.append(
            {
                "bid_no": bid_no,
                "bid_ord": bid_ord,
                "project_name_norm": project_name_norm,
                "g2b_verified": str(seed_row.get("g2b_verified") or "N").strip().upper() or "N",
                "query": "synthetic-seed",
                "source_type": "synthetic",
                "candidate_rank": 1,
                "candidate_score": 0.95,
                "url": url,
                "title": f"{project_name} synthetic candidate",
                "snippet": project_name,
                "parser_version": "web-v0.1",
                "run_mode": "synthetic",
                "status": "CANDIDATE_OK",
                "search_fail": "N",
                "parse_fail": "N",
                "date_anomaly": "N",
                "fallback_flag": "Y",
                "filter_result": "PASS",
                "filter_reason": "synthetic_seed",
                "notice_url": "",
                "spec_doc_url": "",
                "spec_doc_file_name": "",
                "presmpt_prce": "",
                "officer_name": "",
                "officer_tel": "",
            }
        )
    return rows


def _build_synthetic_internal_nav_rows(*, candidate_csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with candidate_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            url = str(row.get("url") or "").strip()
            if not url:
                continue
            rows.append(
                {
                    "bid_no": str(row.get("bid_no") or "").strip(),
                    "bid_ord": str(row.get("bid_ord") or "").strip() or "000",
                    "project_name_norm": str(row.get("project_name_norm") or "").strip(),
                    "g2b_verified": str(row.get("g2b_verified") or "N").strip().upper() or "N",
                    "base_url": url,
                    "base_query": str(row.get("query") or "").strip(),
                    "base_source_type": str(row.get("source_type") or "").strip(),
                    "search_link": url,
                    "internal_search_url": f"{url}?synthetic_search=1",
                    "notice_url": str(row.get("notice_url") or "").strip(),
                    "spec_doc_url": str(row.get("spec_doc_url") or "").strip(),
                    "spec_doc_file_name": str(row.get("spec_doc_file_name") or "").strip(),
                    "presmpt_prce": str(row.get("presmpt_prce") or "").strip(),
                    "officer_name": str(row.get("officer_name") or "").strip(),
                    "officer_tel": str(row.get("officer_tel") or "").strip(),
                    "parser_version": "web-v0.1",
                    "run_mode": "synthetic",
                    "status": "SEARCH_URL_BUILT",
                }
            )
    return rows


def _build_synthetic_post_collect_rows(*, internal_nav_csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with internal_nav_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for index, row in enumerate(reader, start=1):
            bid_no = str(row.get("bid_no") or "").strip()
            bid_ord = str(row.get("bid_ord") or "").strip() or "000"
            project_name_norm = str(row.get("project_name_norm") or "").strip()
            search_url = str(row.get("internal_search_url") or "").strip()
            rows.append(
                {
                    "bid_no": bid_no,
                    "bid_ord": bid_ord,
                    "rank": str(index),
                    "project_name_norm": project_name_norm,
                    "g2b_verified": str(row.get("g2b_verified") or "N").strip().upper() or "N",
                    "source_type": "synthetic",
                    "internal_search_url": search_url,
                    "post_url": search_url,
                    "post_title": f"{project_name_norm} synthetic winner",
                    "winner_name": "Synthetic Winner",
                    "winner_confidence": "high",
                    "winner_pattern": "SYNTHETIC",
                    "post_score": "0.95",
                    "file_url": "",
                    "file_name": "",
                    "confidence_score": "0.95",
                    "reason_code": "SYNTHETIC_EXPORT",
                    "review_flag": "N",
                    "escalate": "N",
                    "contract_name": project_name_norm,
                    "contract_date": "",
                    "contract_amount": "",
                    "gross_area_scale": "",
                    "demand_contact": "",
                    "client_location": "",
                    "site_location": "",
                    "architect_office": "Synthetic Winner",
                    "construction_start_date": "",
                    "building_automation_estimated_amount": "",
                    "evidence_source": "synthetic",
                    "parser_version": "web-v0.1",
                    "run_mode": "synthetic",
                    "status": "FOUND",
                    "hub_check_note": "",
                }
            )
    return rows


def _candidate_fieldnames() -> list[str]:
    return [
        "bid_no",
        "bid_ord",
        "project_name_norm",
        "g2b_verified",
        "query",
        "source_type",
        "candidate_rank",
        "candidate_score",
        "url",
        "title",
        "snippet",
        "parser_version",
        "run_mode",
        "status",
        "search_fail",
        "parse_fail",
        "date_anomaly",
        "fallback_flag",
        "filter_result",
        "filter_reason",
        "notice_url",
        "spec_doc_url",
        "spec_doc_file_name",
        "presmpt_prce",
        "officer_name",
        "officer_tel",
    ]


def _internal_nav_fieldnames() -> list[str]:
    return [
        "bid_no",
        "bid_ord",
        "project_name_norm",
        "g2b_verified",
        "base_url",
        "base_query",
        "base_source_type",
        "search_link",
        "internal_search_url",
        "notice_url",
        "spec_doc_url",
        "spec_doc_file_name",
        "presmpt_prce",
        "officer_name",
        "officer_tel",
        "parser_version",
        "run_mode",
        "status",
    ]


def _post_collect_fieldnames() -> list[str]:
    return [
        "bid_no",
        "bid_ord",
        "rank",
        "project_name_norm",
        "g2b_verified",
        "source_type",
        "internal_search_url",
        "post_url",
        "post_title",
        "winner_name",
        "winner_confidence",
        "winner_pattern",
        "post_score",
        "file_url",
        "file_name",
        "confidence_score",
        "reason_code",
        "review_flag",
        "escalate",
        "contract_name",
        "contract_date",
        "notice_construction_cost",
        "contract_amount",
        "gross_area_scale",
        "demand_contact",
        "client_location",
        "site_location",
        "architect_office",
        "construction_start_date",
        "construction_duration_days",
        "completion_expected_date_explicit",
        "completion_expected_date_computed",
        "building_automation_estimated_amount",
        "evidence_source",
        "parser_version",
        "run_mode",
        "status",
        "hub_check_note",
    ]


def _write_csv(path: Path, *, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        return sum(1 for _ in reader)


def _first_csv_value(path: Path, field_name: str) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        first_row = next(reader, None)
    if first_row is None:
        return ""
    return str(first_row.get(field_name) or "").strip()


def _slugify(value: str) -> str:
    compact = "-".join(part for part in value.strip().lower().replace("/", " ").split() if part)
    return compact or "notice"


def _prefix_progress(progress_cb: Callable[[str], None] | None, prefix: str):
    if progress_cb is None:
        return None

    def _inner(message: str) -> None:
        progress_cb(f"{prefix}: {message}")

    return _inner
