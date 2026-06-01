from __future__ import annotations

import os
from pathlib import Path

_LOADED = False


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip("\"'")
        # Respect explicitly provided process env values, including blank
        # overrides used by tests to disable external integrations.
        if key and value and key not in os.environ:
            os.environ[key] = value


def load_local_env() -> None:
    global _LOADED
    if _LOADED:
        return

    repo_root = Path(__file__).resolve().parent.parent
    candidate_env_paths = [
        repo_root / ".env",
        repo_root.parent / "notice-winner-pipeline-project" / ".env",
    ]
    for env_path in candidate_env_paths:
        _load_env_file(env_path)

    _LOADED = True
