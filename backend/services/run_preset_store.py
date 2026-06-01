from __future__ import annotations

import threading
from typing import Any
from uuid import UUID

from backend.api.schemas import RunPresetItem

_RUN_PRESETS_LOCK = threading.Lock()
_RUN_PRESETS: dict[UUID, dict[str, Any]] = {}
_RUN_PRESET_ORDER: list[UUID] = []


def store_run_preset(row: dict[str, Any]) -> dict[str, Any]:
    with _RUN_PRESETS_LOCK:
        _RUN_PRESETS[row["id"]] = dict(row)
        _RUN_PRESET_ORDER.insert(0, row["id"])
        del _RUN_PRESET_ORDER[50:]
        return dict(_RUN_PRESETS[row["id"]])


def list_run_presets(limit: int = 50) -> list[dict[str, Any]]:
    with _RUN_PRESETS_LOCK:
        items: list[dict[str, Any]] = []
        for preset_id in _RUN_PRESET_ORDER:
            row = _RUN_PRESETS.get(preset_id)
            if row is None:
                continue
            items.append(dict(row))
            if len(items) >= limit:
                break
        return items


def to_run_preset_item(row: dict[str, Any]) -> RunPresetItem:
    return RunPresetItem(
        id=UUID(str(row["id"])),
        name=str(row["name"]),
        params=dict(row.get("params") or {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
