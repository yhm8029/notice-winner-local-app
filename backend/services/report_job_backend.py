from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_reports_root(*, raw_root: str, app_root: Path) -> Path:
    reports_root = Path(raw_root).expanduser() if raw_root else app_root / "output"
    if not reports_root.is_absolute():
        reports_root = app_root / reports_root
    return reports_root


def resolve_report_script_path(
    *,
    report_name: str,
    app_root: Path,
    report_script_files: dict[str, str],
    report_script_env_overrides: dict[str, str],
    env_get_fn: Any,
    not_found_fn: Any,
) -> Path:
    override_name = report_script_env_overrides.get(report_name, "")
    raw_override = str(env_get_fn(override_name) or "").strip() if override_name else ""
    if raw_override:
        script_path = Path(raw_override).expanduser()
        if not script_path.is_absolute():
            script_path = app_root / script_path
        if script_path.exists():
            return script_path
    script_name = report_script_files.get(report_name, "")
    if not script_name:
        not_found_fn(f"report not found: {report_name}")
    script_path = app_root / "scripts" / script_name
    if not script_path.exists():
        not_found_fn(f"report script not found: {report_name}")
    return script_path


def discover_gui_source_root(*, explicit: str, app_root: Path, env_get_fn: Any) -> Path | None:
    candidates: list[Path] = []
    raw_explicit = explicit.strip()
    if raw_explicit:
        candidates.append(Path(raw_explicit).expanduser())
    raw_env = str(env_get_fn("GUI_PARITY_SOURCE_ROOT") or "").strip()
    if raw_env:
        candidates.append(Path(raw_env).expanduser())

    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate if candidate.is_absolute() else app_root / candidate
        resolved = resolved.resolve()
        resolved_key = str(resolved).lower()
        if resolved_key in seen:
            continue
        seen.add(resolved_key)
        if resolved.exists():
            return resolved
    return None


def trim_log_excerpt(text: str, max_chars: int = 4000) -> str:
    normalized = (text or "").strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[-max_chars:]


def build_report_job_command(
    payload: Any,
    *,
    sys_executable: str,
    app_root: Path,
    report_files: dict[str, str],
    resolve_reports_root_fn: Any,
    resolve_report_script_path_fn: Any,
    discover_gui_source_root_fn: Any,
    validation_error_fn: Any,
) -> tuple[list[str], Path, Path | None, str]:
    report_name = str(payload.report_name or "").strip()
    if report_name not in report_files:
        validation_error_fn("report_name must be one of phase1-equivalence, phase1-artifact-diff")

    reports_root = resolve_reports_root_fn()
    reports_root.mkdir(parents=True, exist_ok=True)
    output_path = reports_root / report_files[report_name]
    script_path = resolve_report_script_path_fn(report_name)
    gui_root = discover_gui_source_root_fn(str(payload.gui_source_root or "").strip())

    command = [sys_executable, str(script_path), "--output", str(output_path)]
    if gui_root is not None:
        command.extend(["--gui-source-root", str(gui_root)])

    if report_name == "phase1-artifact-diff":
        seed_csv = str(payload.seed_csv or "").strip()
        if not seed_csv and gui_root is not None:
            default_seed_csv = gui_root / "tests" / "winner_pipeline_seed_input.csv"
            if default_seed_csv.exists():
                seed_csv = str(default_seed_csv)
        if seed_csv:
            command.extend(["--seed-csv", seed_csv])
        if int(payload.seed_limit or 0) > 0:
            command.extend(["--seed-limit", str(payload.seed_limit)])
        command.extend(
            [
                "--start-date",
                str(payload.start_date),
                "--end-date",
                str(payload.end_date),
                "--contract-date-hint",
                str(payload.contract_date_hint),
                "--bid-no",
                str(payload.bid_no),
                "--notice-title",
                str(payload.notice_title),
                "--demand-org",
                str(payload.demand_org),
                "--rows-per-page",
                str(payload.rows_per_page),
                "--max-pages",
                str(payload.max_pages),
                "--api-scope",
                str(payload.api_scope),
            ]
        )
        return command, output_path, gui_root, seed_csv

    return command, output_path, gui_root, ""
