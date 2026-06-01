from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_GUI_SOURCE_ROOT = ROOT_DIR.parent / "notice-winner-pipeline-project"

_MODULE_CACHE: dict[str, ModuleType] = {}


def resolve_gui_source_root() -> Path:
    raw = os.getenv("GUI_PARITY_SOURCE_ROOT", "").strip()
    candidate = Path(raw).expanduser() if raw else DEFAULT_GUI_SOURCE_ROOT
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    if not candidate.exists():
        raise FileNotFoundError(f"GUI source root not found: {candidate}")
    return candidate


def load_gui_backend_module() -> ModuleType:
    return _load_module("notice_winner_gui_backend_runtime", "run_gui_backend.py")


def load_search_collect_module() -> ModuleType:
    return _load_module("notice_winner_search_collect_runtime", "pipeline_search_collect_v1.py")


def load_internal_nav_module() -> ModuleType:
    return _load_module("notice_winner_internal_nav_runtime", "pipeline_internal_nav_v1.py")


def load_post_collect_module() -> ModuleType:
    return _load_module("notice_winner_post_collect_runtime", "pipeline_post_collect_v1.py")


def load_tracker_service_module() -> ModuleType:
    return _load_module("notice_winner_tracker_service_runtime", "app/services/tracker_service.py")


def _load_module(module_name: str, relative_path: str) -> ModuleType:
    cached = _MODULE_CACHE.get(module_name)
    if cached is not None:
        return cached

    source_root = resolve_gui_source_root()
    module_path = source_root / relative_path
    if not module_path.exists():
        raise FileNotFoundError(f"GUI parity module not found: {module_path}")

    source_root_str = str(source_root)
    if source_root_str not in sys.path:
        sys.path.insert(0, source_root_str)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load GUI parity module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _MODULE_CACHE[module_name] = module
    return module
