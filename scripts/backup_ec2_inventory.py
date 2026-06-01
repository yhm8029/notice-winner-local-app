from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_backup_common import create_backup_dir
from scripts.local_backup_common import load_env_file
from scripts.local_backup_common import write_json
from scripts.local_backup_common import write_jsonl


DEFAULT_EC2_PATHS = (
    "/home/ubuntu/notice-winner-pipeline-web/output",
    "/home/ubuntu/notice-winner-pipeline-web/input",
    "/home/ubuntu/notice-winner-pipeline-web/logs",
    "/home/ubuntu/notice-winner-pipeline-web/.tmp-runs",
)


def _single_quote_remote_path(path: str) -> str:
    return "'" + path.replace("'", "'\"'\"'") + "'"


def build_find_command(paths: list[str]) -> str:
    quoted_paths = " ".join(_single_quote_remote_path(path) for path in paths)
    return (
        "find "
        + quoted_paths
        + " -type f -printf '%p\\t%s\\t%TY-%Tm-%TdT%TH:%TM:%TS%Tz\\n' 2>/dev/null"
        + " || true"
    )


def build_tar_command(paths: list[str]) -> str:
    relative_paths = [path.strip().lstrip("/") for path in paths if path.strip()]
    quoted_paths = " ".join(_single_quote_remote_path(path) for path in relative_paths)
    return "tar -C / --ignore-failed-read -czf - " + quoted_paths + " 2>/dev/null"


def build_ssh_args(ssh_target: str, command: str, *, identity_file: str = "") -> list[str]:
    args = ["ssh"]
    if identity_file:
        args.extend(["-i", identity_file])
    args.extend([ssh_target, command])
    return args


def parse_find_output(output: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            rows.append({"path": line, "size_bytes": 0, "modified_at": "", "parse_error": "expected 3 tab-separated fields"})
            continue
        rows.append({"path": parts[0], "size_bytes": int(parts[1]), "modified_at": parts[2]})
    return rows


def run_ssh_find(
    ssh_target: str,
    paths: list[str],
    *,
    identity_file: str = "",
    timeout_sec: int = 120,
) -> list[dict[str, Any]]:
    command = build_find_command(paths)
    result = subprocess.run(
        build_ssh_args(ssh_target, command, identity_file=identity_file),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_sec,
    )
    return parse_find_output(result.stdout)


def _safe_extract_tarball(tarball_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with tarfile.open(tarball_path, "r:gz") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if not str(target).startswith(str(destination_root)):
                raise RuntimeError(f"Refusing to extract unsafe tar member: {member.name}")
        archive.extractall(destination)


def download_ec2_archive(
    backup_dir: Path,
    *,
    ssh_target: str,
    paths: list[str],
    identity_file: str = "",
    timeout_sec: int = 600,
    extract: bool = True,
) -> Path:
    archive_path = backup_dir / "ec2-files.tar.gz"
    command = build_tar_command(paths)
    with archive_path.open("wb") as handle:
        subprocess.run(
            build_ssh_args(ssh_target, command, identity_file=identity_file),
            check=True,
            stdout=handle,
            stderr=subprocess.PIPE,
            timeout=timeout_sec,
        )
    if extract:
        _safe_extract_tarball(archive_path, backup_dir / "files")
    return archive_path


def write_ec2_inventory(
    backup_dir: Path,
    *,
    ssh_target: str,
    paths: list[str],
    files: list[dict[str, Any]],
    timestamp: str,
    archive_path: Path | None = None,
) -> dict[str, Any]:
    files_path = backup_dir / "files.jsonl"
    write_jsonl(files_path, files)
    manifest = {
        "kind": "ec2_file_inventory",
        "timestamp": timestamp,
        "ssh_target": ssh_target,
        "paths": paths,
        "file_count": len(files),
        "total_size_bytes": sum(int(item.get("size_bytes") or 0) for item in files),
        "files_path": str(files_path),
    }
    if archive_path is not None:
        manifest["archive_path"] = str(archive_path)
    write_json(backup_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory EC2 app-owned files before local migration.")
    parser.add_argument("--env-file", default=".env.local-backup")
    parser.add_argument("--backup-root", default="backups")
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--ssh-target", default="")
    parser.add_argument("--ssh-key-path", default="")
    parser.add_argument("--paths", default="")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--no-extract", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    ssh_target = args.ssh_target or os.environ.get("EC2_SSH_TARGET", "").strip()
    if not ssh_target:
        raise SystemExit("EC2_SSH_TARGET or --ssh-target is required")
    paths = [item.strip() for item in (args.paths or os.environ.get("EC2_BACKUP_PATHS", "")).split(",") if item.strip()]
    if not paths:
        paths = list(DEFAULT_EC2_PATHS)
    identity_file = args.ssh_key_path or os.environ.get("EC2_SSH_KEY_PATH", "").strip()
    backup_dir = create_backup_dir(Path(args.backup_root), "ec2", timestamp=args.timestamp or None)
    if args.dry_run:
        files: list[dict[str, Any]] = []
        write_json(backup_dir / "dry-run-command.json", {"ssh_target": ssh_target, "command": build_find_command(paths)})
        archive_path = None
    else:
        files = run_ssh_find(ssh_target, paths, identity_file=identity_file)
        archive_path = (
            download_ec2_archive(
                backup_dir,
                ssh_target=ssh_target,
                paths=paths,
                identity_file=identity_file,
                extract=not args.no_extract,
            )
            if args.download
            else None
        )
    manifest = write_ec2_inventory(
        backup_dir,
        ssh_target=ssh_target,
        paths=paths,
        files=files,
        timestamp=backup_dir.name,
        archive_path=archive_path,
    )
    print(f"EC2 inventory written: {backup_dir}")
    print(f"Files inventoried: {manifest['file_count']}")
    if archive_path is not None:
        print(f"EC2 archive written: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
