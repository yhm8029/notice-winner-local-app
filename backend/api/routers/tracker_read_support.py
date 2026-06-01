from __future__ import annotations

from typing import Any


def _app_module():
    from backend.api import app as tracker_read_app

    return tracker_read_app


def __getattr__(name: str) -> Any:
    return getattr(_app_module(), name)
