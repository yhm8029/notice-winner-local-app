from __future__ import annotations

from typing import Any


def _app_module():
    from backend.api import app as tracker_cache_app

    return tracker_cache_app


def __getattr__(name: str) -> Any:
    return getattr(_app_module(), name)
