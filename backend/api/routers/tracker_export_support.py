from __future__ import annotations

from typing import Any


def _app_module():
    from backend.api import app as tracker_export_app

    return tracker_export_app


def __getattr__(name: str) -> Any:
    return getattr(_app_module(), name)
