from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from uuid import UUID

from .artifact_files import read_tracking_workbook_rows
from .native_tracker_backend import build_tracker_entries_from_winner_csv
from .run_workspace import seed_csv_path_for_run


@dataclass(frozen=True)
class TrackerExportPreparedOutput:
    entries: list[dict[str, Any]]
    workbook_path: Path | None
    stage_backend: str


def prepare_tracker_export_for_run(
    *,
    parent_run_id: UUID,
    params: dict[str, Any],
    winner_csv_path: Path | None,
    progress_cb: Callable[[str], None] | None = None,
) -> TrackerExportPreparedOutput | None:
    export_backend = str(((params.get("_export_summary") or {}) or {}).get("export_backend") or "").strip()
    if export_backend.startswith("native"):
        if winner_csv_path is None:
            raise RuntimeError("winner_csv artifact not found for native tracker_export")
        entries = build_tracker_entries_from_winner_csv(
            winner_csv_path=winner_csv_path,
            seed_csv_path=seed_csv_path_for_run(parent_run_id),
        )
        return TrackerExportPreparedOutput(
            entries=entries,
            workbook_path=None,
            stage_backend="native_tracker_export",
        )
    if export_backend == "synthetic":
        return None
    return None


def _load_seed_candidates(seed_csv_path: Path) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if not seed_csv_path.exists():
        return candidates
    with seed_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            project_name = str((row or {}).get("project_name") or "").strip()
            if not project_name:
                continue
            candidates.append(
                {
                    "project_name": project_name,
                    "project_name_norm": _norm_text(project_name),
                    "project_name_slug": _slugify(project_name),
                    "bid_no": str((row or {}).get("bid_no") or "").strip().upper(),
                    "bid_ord": _normalize_bid_ord((row or {}).get("bid_ord") or "000"),
                    "opening_scheduled_date": str((row or {}).get("opening_scheduled_date") or "").strip(),
                    "source_project_name_norm": _slugify(project_name),
                }
            )
    return candidates


def _resolve_seed_meta(project_name: str, seed_candidates: list[dict[str, str]]) -> dict[str, str]:
    if not seed_candidates:
        return {}

    project_name_norm = _norm_text(project_name)
    project_name_slug = _slugify(project_name)

    for candidate in seed_candidates:
        if candidate["project_name_norm"] == project_name_norm:
            return candidate
        if candidate["project_name_slug"] == project_name_slug:
            return candidate

    best_candidate: dict[str, str] | None = None
    best_score: tuple[int, int] | None = None
    for candidate in seed_candidates:
        candidate_norm = candidate["project_name_norm"]
        candidate_slug = candidate["project_name_slug"]
        if not candidate_norm:
            continue
        matches = (
            project_name_norm in candidate_norm
            or candidate_norm in project_name_norm
            or project_name_slug in candidate_slug
            or candidate_slug in project_name_slug
        )
        if not matches:
            continue
        score = (
            abs(len(candidate_norm) - len(project_name_norm)),
            abs(len(candidate_slug) - len(project_name_slug)),
        )
        if best_score is None or score < best_score:
            best_score = score
            best_candidate = candidate

    if best_candidate is not None:
        return best_candidate

    if len(seed_candidates) == 1:
        return seed_candidates[0]

    return {}


def _build_entries_from_workbook_rows(
    *,
    workbook_rows: list[dict[str, str]],
    seed_candidates: list[dict[str, str]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for index, row in enumerate(workbook_rows, start=1):
        project_name = str(row.get("project_name") or "").strip()
        seed_meta = _resolve_seed_meta(project_name, seed_candidates)
        source_bid_no = str(seed_meta.get("bid_no") or "").strip()
        source_bid_ord = str(seed_meta.get("bid_ord") or "000").strip() or "000"
        source_project_name_norm = str(
            seed_meta.get("source_project_name_norm") or _slugify(project_name)
        ).strip()
        entry_key = "|".join(
            (
                source_bid_no.lower(),
                source_bid_ord.lower(),
                source_project_name_norm.lower(),
            )
        )
        entries.append(
            {
                "entry_key": entry_key,
                "row_no": index,
                "sheet_name": "Sheet1",
                "section_name": "facility_cost",
                "source_bid_no": source_bid_no,
                "source_bid_ord": source_bid_ord,
                "source_project_name_norm": source_project_name_norm,
                "project_name": project_name,
                "gross_area_scale": str(row.get("gross_area_scale") or "").strip(),
                "construction_cost": str(row.get("construction_cost") or "").strip(),
                "demand_org_name": str(row.get("demand_org_name") or "").strip(),
                "demand_contact": str(row.get("demand_contact") or "").strip(),
                "client_location": str(row.get("client_location") or "").strip(),
                "site_location_1": str(row.get("site_location_1") or "").strip(),
                "site_location_2": str(row.get("site_location_2") or "").strip(),
                "architect_office": str(row.get("architect_office") or "").strip(),
                "opening_scheduled_date": str(seed_meta.get("opening_scheduled_date") or "").strip(),
                "construction_start_date": str(row.get("construction_start_date") or "").strip(),
                "last_checked_date": str(row.get("last_checked_date") or "").strip(),
                "progress_note": str(row.get("progress_note") or "").strip(),
                "notice_date": str(row.get("notice_date") or "").strip(),
                "manager_name": str(row.get("manager_name") or "").strip(),
                "building_automation_estimated_amount": str(
                    row.get("building_automation_estimated_amount") or ""
                ).strip(),
            }
        )
    return entries


def _normalize_bid_ord(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def _slugify(value: str) -> str:
    compact = "-".join(part for part in value.strip().lower().replace("/", " ").split() if part)
    return compact or "notice"


def _norm_text(value: str) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if not ch.isspace())


def _prefix_progress(progress_cb: Callable[[str], None] | None, prefix: str):
    if progress_cb is None:
        return None

    def _inner(message: str) -> None:
        progress_cb(f"{prefix}: {message}")

    return _inner
