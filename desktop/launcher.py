from __future__ import annotations

import argparse
import json
import logging
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


def _load_env_file(env_path: Path, env: dict[str, str]) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip("\"'")
        if key and value and key not in env:
            env[key] = value


def load_desktop_env_files(
    *,
    bundle_root: Path,
    writable_root: Path,
    current_env: Mapping[str, str],
) -> dict[str, str]:
    env = dict(current_env)
    for env_path in (
        writable_root / ".env",
        writable_root / "config" / ".env",
        bundle_root / ".env",
    ):
        _load_env_file(env_path, env)
    return env


def build_app_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/app/"


def build_desktop_return_button_script(app_url: str) -> str:
    app_url_json = json.dumps(str(app_url), ensure_ascii=False)
    return f"""
(function () {{
  var appUrl = {app_url_json};
  var href = String(location.href || "");
  var isLocalApp = appUrl && href.indexOf(appUrl) === 0;
  var isNoticeViewer = href.indexOf("SynapDocViewServer") !== -1;
  if (!isNoticeViewer || isLocalApp) {{
    var localButton = document.getElementById("notice-winner-return-button");
    if (localButton) localButton.remove();
    return;
  }}
  if (document.getElementById("notice-winner-return-button")) return;
  var button = document.createElement("button");
  button.id = "notice-winner-return-button";
  button.type = "button";
  button.textContent = "앱으로 돌아가기";
  button.style.position = "fixed";
  button.style.top = "14px";
  button.style.left = "14px";
  button.style.zIndex = "2147483647";
  button.style.padding = "10px 14px";
  button.style.border = "1px solid #1e3a8a";
  button.style.borderRadius = "8px";
  button.style.background = "#ffffff";
  button.style.color = "#10213f";
  button.style.font = "700 14px Malgun Gothic, Arial, sans-serif";
  button.style.boxShadow = "0 10px 30px rgba(15, 23, 42, 0.24)";
  button.style.cursor = "pointer";
  button.addEventListener("click", function () {{
    if (history.length > 1) {{
      history.back();
      return;
    }}
    location.href = appUrl;
  }});
  document.body.appendChild(button);
}})();
"""


def inject_desktop_return_button(window, app_url: str) -> None:
    try:
        window.evaluate_js(build_desktop_return_button_script(app_url))
    except Exception:
        logging.getLogger("desktop.launcher").exception("Failed to inject desktop return button")


def ensure_runtime_directories(writable_root: Path) -> None:
    (writable_root / "data").mkdir(parents=True, exist_ok=True)
    (writable_root / "output" / "artifacts").mkdir(parents=True, exist_ok=True)
    (writable_root / "logs").mkdir(parents=True, exist_ok=True)


def configure_desktop_logging(writable_root: Path) -> Path:
    log_path = writable_root / "logs" / "server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.touch(exist_ok=True)
    root_logger = logging.getLogger()
    log_path_text = str(log_path)
    if not any(getattr(handler, "_notice_winner_log_path", "") == log_path_text for handler in root_logger.handlers):
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        handler._notice_winner_log_path = log_path_text  # type: ignore[attr-defined]
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    os.environ.setdefault("DESKTOP_SERVER_LOG_PATH", log_path_text)
    return log_path


def build_desktop_environment(
    *,
    bundle_root: Path,
    writable_root: Path,
    current_env: Mapping[str, str],
) -> dict[str, str]:
    env = dict(current_env)
    for key in SQLITE_BACKEND_ENV_KEYS:
        env.setdefault(key, "sqlite")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("LOCAL_APP_EXPOSE_INTERNAL_ERRORS", "1")
    env.setdefault("LOCAL_SQLITE_PATH", str(writable_root / "data" / "local.sqlite3"))
    env.setdefault("NOTICE_VIEWER_CACHE_PATH", str(writable_root / "data" / "notice_viewer_cache.json"))
    env.setdefault("ARTIFACTS_ROOT", str(writable_root / "output" / "artifacts"))
    env.setdefault("RUN_WORKSPACE_ROOT", str(writable_root / "output" / "runs"))
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
    configure_desktop_logging(writable_root)
    desktop_env = load_desktop_env_files(
        bundle_root=bundle_root,
        writable_root=writable_root,
        current_env=os.environ,
    )
    os.environ.update(
        build_desktop_environment(
            bundle_root=bundle_root,
            writable_root=writable_root,
            current_env=desktop_env,
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
    window.events.loaded += lambda: inject_desktop_return_button(window, app_url)
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
