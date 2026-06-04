from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Mapping


SQLITE_BACKEND_ENV_KEYS = (
    "TRACKER_REPOSITORY_BACKEND",
    "RUN_REPOSITORY_BACKEND",
    "ARTIFACT_REPOSITORY_BACKEND",
    "RUN_LOG_REPOSITORY_BACKEND",
    "RELATED_NOTICE_CACHE_REPOSITORY_BACKEND",
    "RELATED_NOTICE_PUBLICATION_REPOSITORY_BACKEND",
    "SALES_CLAIM_REPOSITORY_BACKEND",
    "TRACKER_CHANGE_EVENT_REPOSITORY_BACKEND",
    "DOWNLOAD_AUDIT_LOG_REPOSITORY_BACKEND",
    "LOGIN_AUDIT_LOG_REPOSITORY_BACKEND",
    "TRACKER_ENTRY_SNAPSHOT_REPOSITORY_BACKEND",
    "HOME_BOOTSTRAP_SNAPSHOT_REPOSITORY_BACKEND",
    "BACKFILL_CONFLICT_REPOSITORY_BACKEND",
)


def build_app_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/app/"


def ensure_runtime_directories(writable_root: Path) -> None:
    (writable_root / "data").mkdir(parents=True, exist_ok=True)
    (writable_root / "output" / "artifacts").mkdir(parents=True, exist_ok=True)


def build_desktop_environment(
    *,
    bundle_root: Path,
    writable_root: Path,
    current_env: Mapping[str, str],
) -> dict[str, str]:
    env = dict(current_env)
    for key in SQLITE_BACKEND_ENV_KEYS:
        env.setdefault(key, "sqlite")
    env.setdefault("LOCAL_SQLITE_PATH", str(writable_root / "data" / "local.sqlite3"))
    env.setdefault("ARTIFACTS_ROOT", str(writable_root / "output" / "artifacts"))
    env.setdefault(
        "TRACKER_TEMPLATE_PATH",
        str(bundle_root / "assets" / "project_tracker_template.xlsx"),
    )
    return env


def resolve_bundle_root() -> Path:
    frozen_bundle = getattr(sys, "_MEIPASS", None)
    if frozen_bundle:
        return Path(frozen_bundle).resolve()
    return Path(__file__).resolve().parents[1]


def resolve_writable_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, *, timeout_seconds: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status < 500:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.15)
    raise RuntimeError(f"Local server did not start at {url}") from last_error


def configure_desktop_environment() -> tuple[Path, Path]:
    bundle_root = resolve_bundle_root()
    writable_root = resolve_writable_root()
    ensure_runtime_directories(writable_root)
    os.environ.update(
        build_desktop_environment(
            bundle_root=bundle_root,
            writable_root=writable_root,
            current_env=os.environ,
        )
    )
    return bundle_root, writable_root


def start_api_server(host: str, port: int):
    import uvicorn

    config = uvicorn.Config(
        "backend.api.app:app",
        host=host,
        port=port,
        log_level=os.environ.get("DESKTOP_UVICORN_LOG_LEVEL", "warning"),
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="notice-winner-api", daemon=True)
    thread.start()
    return server, thread


def run_desktop_app(*, host: str, port: int | None, debug: bool = False) -> None:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError(
            "pywebview is required for the desktop app. "
            "Install desktop dependencies with: pip install -r requirements-desktop.txt"
        ) from exc

    configure_desktop_environment()
    selected_port = port or find_free_port(host)
    server, _thread = start_api_server(host, selected_port)
    app_url = build_app_url(host, selected_port)
    wait_for_server(app_url)

    window = webview.create_window(
        "공고 추적",
        app_url,
        width=1440,
        height=960,
        min_size=(1180, 760),
    )

    def stop_server() -> None:
        server.should_exit = True

    window.events.closed += stop_server
    webview.start(debug=debug)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the local project tracker desktop app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_desktop_app(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
