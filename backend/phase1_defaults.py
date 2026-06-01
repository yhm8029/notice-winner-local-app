from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import UUID

DEFAULT_PHASE1_ORGANIZATION_ID = UUID("7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001")
DEFAULT_PHASE1_INTERNAL_USER_ID = UUID("8e9d2b94-4c95-4e2b-9be8-2be1d96e1001")
DEFAULT_SOURCE_MODE = "web_native"
PROJECT_TRACKER_RUN_TYPE = "project_tracker"
LEGACY_PROJECT_TRACKER_RUN_TYPE = "winner_pipeline"
TRACKER_EXPORT_RUN_TYPE = "tracker_export"
PROJECT_TRACKER_RUN_TYPES = frozenset({PROJECT_TRACKER_RUN_TYPE, LEGACY_PROJECT_TRACKER_RUN_TYPE})
VALID_RUN_TYPES = frozenset({PROJECT_TRACKER_RUN_TYPE, LEGACY_PROJECT_TRACKER_RUN_TYPE, TRACKER_EXPORT_RUN_TYPE})


@dataclass(frozen=True)
class Phase1Identity:
    organization_id: UUID
    internal_user_id: UUID


def _load_uuid(env_name: str, default_value: UUID) -> UUID:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default_value
    try:
        return UUID(raw)
    except ValueError as exc:
        raise RuntimeError(f"{env_name} must be a valid UUID") from exc


def load_phase1_identity() -> Phase1Identity:
    return Phase1Identity(
        organization_id=_load_uuid("PHASE1_ORGANIZATION_ID", DEFAULT_PHASE1_ORGANIZATION_ID),
        internal_user_id=_load_uuid("PHASE1_INTERNAL_USER_ID", DEFAULT_PHASE1_INTERNAL_USER_ID),
    )


def build_phase1_run_row(
    *,
    run_type: str,
    params: dict[str, Any],
    parent_run_id: UUID | str | None = None,
    progress_stage: str = "",
) -> dict[str, Any]:
    if run_type not in VALID_RUN_TYPES:
        raise ValueError(f"unsupported run_type: {run_type}")

    identity = load_phase1_identity()
    parent_value = str(parent_run_id) if parent_run_id else None

    return {
        "organization_id": str(identity.organization_id),
        "requested_by": str(identity.internal_user_id),
        "parent_run_id": parent_value,
        "status": "queued",
        "run_type": run_type,
        "source_mode": DEFAULT_SOURCE_MODE,
        "params_json": params,
        "summary_json": {},
        "error_json": {},
        "progress_stage": progress_stage,
        "progress_current": 0,
        "progress_total": 0,
        "cancel_requested": False,
    }


def build_phase1_preset_row(*, name: str, params: dict[str, Any]) -> dict[str, Any]:
    identity = load_phase1_identity()

    return {
        "organization_id": str(identity.organization_id),
        "created_by": str(identity.internal_user_id),
        "name": name,
        "params_json": params,
    }
