from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RUN_WORKSPACE_ROOT = ROOT_DIR / "output" / "runs"


def _prefer_existing(primary_path: Path, legacy_name: str) -> Path:
    if primary_path.exists():
        return primary_path
    legacy_path = primary_path.parent / legacy_name
    if legacy_path.exists():
        return legacy_path
    return primary_path


def ensure_run_workspace_dir(run_id: UUID) -> Path:
    raw_root = os.getenv("RUN_WORKSPACE_ROOT", "").strip()
    root = Path(raw_root).expanduser() if raw_root else DEFAULT_RUN_WORKSPACE_ROOT
    if not root.is_absolute():
        root = ROOT_DIR / root
    path = root / str(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def seed_csv_path_for_run(run_id: UUID) -> Path:
    return _prefer_existing(
        ensure_run_workspace_dir(run_id) / "project_tracker_seed_input.csv",
        "winner_pipeline_seed_input.csv",
    )


def collect_candidates_csv_path_for_run(run_id: UUID) -> Path:
    return _prefer_existing(
        ensure_run_workspace_dir(run_id) / "project_tracker_candidate_collection_v1_1.csv",
        "winner_pipeline_candidate_collection_v1_1.csv",
    )


def internal_nav_csv_path_for_run(run_id: UUID) -> Path:
    return _prefer_existing(
        ensure_run_workspace_dir(run_id) / "project_tracker_internal_search_urls_v1_1.csv",
        "winner_pipeline_internal_search_urls_v1_1.csv",
    )


def post_collect_csv_path_for_run(run_id: UUID) -> Path:
    return _prefer_existing(
        ensure_run_workspace_dir(run_id) / "project_tracker_posts_files_v1_1.csv",
        "winner_pipeline_posts_files_v1_1.csv",
    )
