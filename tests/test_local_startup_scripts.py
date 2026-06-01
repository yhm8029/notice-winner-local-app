from __future__ import annotations

from pathlib import Path


def test_start_local_api_forces_login_disabled_environment() -> None:
    script = Path("scripts/start_local_api.ps1").read_text(encoding="utf-8")

    assert '$env:LOCAL_APP_DISABLE_LOGIN = "1"' in script
    assert '$env:PHASE2_AUTH_ENABLED = "0"' in script
