from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .report_job_backend import build_report_job_command as _build_report_job_command_impl
from .report_job_backend import discover_gui_source_root as _discover_gui_source_root_impl
from .report_job_backend import resolve_report_script_path as _resolve_report_script_path_impl
from .report_job_backend import resolve_reports_root as _resolve_reports_root_impl
from .report_job_backend import trim_log_excerpt as _trim_log_excerpt_impl


def _resolve_reports_root(*, frontend_dir: Path) -> Path:
    return _resolve_reports_root_impl(
        raw_root=os.getenv("REPORTS_ROOT", "").strip(),
        app_root=frontend_dir.parents[0],
    )


def _resolve_report_script_path(
    report_name: str,
    *,
    app_root: Path,
    report_script_files: dict[str, str],
    report_script_env_overrides: dict[str, str],
    not_found_fn: Any,
) -> Path:
    return _resolve_report_script_path_impl(
        report_name=report_name,
        app_root=app_root,
        report_script_files=report_script_files,
        report_script_env_overrides=report_script_env_overrides,
        env_get_fn=os.getenv,
        not_found_fn=not_found_fn,
    )


def _discover_gui_source_root(explicit: str, *, app_root: Path) -> Path | None:
    return _discover_gui_source_root_impl(
        explicit=explicit,
        app_root=app_root,
        env_get_fn=os.getenv,
    )


def _trim_log_excerpt(text: str, max_chars: int = 4000) -> str:
    return _trim_log_excerpt_impl(text, max_chars=max_chars)


def _build_report_job_command(
    payload: Any,
    *,
    app_root: Path,
    frontend_dir: Path,
    report_files: dict[str, str],
    report_script_files: dict[str, str],
    report_script_env_overrides: dict[str, str],
    validation_error_fn: Any,
    not_found_fn: Any,
) -> tuple[list[str], Path, Path | None, str]:
    return _build_report_job_command_impl(
        payload,
        sys_executable=sys.executable,
        app_root=app_root,
        report_files=report_files,
        resolve_reports_root_fn=lambda: _resolve_reports_root(frontend_dir=frontend_dir),
        resolve_report_script_path_fn=lambda report_name: _resolve_report_script_path(
            report_name,
            app_root=app_root,
            report_script_files=report_script_files,
            report_script_env_overrides=report_script_env_overrides,
            not_found_fn=not_found_fn,
        ),
        discover_gui_source_root_fn=lambda explicit: _discover_gui_source_root(explicit, app_root=app_root),
        validation_error_fn=validation_error_fn,
    )
