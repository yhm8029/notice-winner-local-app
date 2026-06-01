# Local Backup Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local-conversion deliverable: repeatable Supabase and EC2 backup/inventory tools that prove which cloud data exists before any app behavior is changed.

**Architecture:** Add standalone Python scripts under `scripts/` plus focused unit tests under `tests/`. The scripts write timestamped backup folders under a caller-provided output root, produce JSON manifests, export Supabase table data as JSONL, inventory EC2 file paths through SSH, and reconcile `run_artifacts.storage_path` rows against EC2 file manifests.

**Tech Stack:** Python standard library, `requests`, existing pytest/unittest test style, PowerShell wrapper for Windows local operation.

---

## Scope

This plan intentionally does not change the app runtime, auth behavior, repository backends, frontend UI, or Google integrations. It only creates the backup and inventory foundation required before SQLite migration and local-app conversion.

## Files

- Create: `scripts/local_backup_common.py`
  - Shared helpers for env loading, backup directory creation, JSON writing, JSONL writing, SHA-256 hashing, and file manifests.
- Create: `scripts/backup_supabase_inventory.py`
  - Exports expected Supabase tables through PostgREST, writes per-table JSONL files, row counts, and a manifest.
- Create: `scripts/backup_ec2_inventory.py`
  - Uses local `ssh` to list EC2 directories and writes a remote file manifest. It supports a dry-run mode so command construction can be validated without touching EC2.
- Create: `scripts/reconcile_backup_artifacts.py`
  - Compares exported `run_artifacts` rows with the EC2 file manifest and writes a missing/present artifact report.
- Create: `scripts/local_backup_inventory.ps1`
  - Windows wrapper that runs the Supabase export, EC2 inventory, and reconciliation in order.
- Create: `tests/test_local_backup_common.py`
- Create: `tests/test_backup_supabase_inventory.py`
- Create: `tests/test_backup_ec2_inventory.py`
- Create: `tests/test_reconcile_backup_artifacts.py`
- Modify: `.gitignore`
  - Ignore `backups/` and local backup secret files.
- Modify: `README.md`
  - Add a short local-conversion backup section with required env vars and commands.

## Task 1: Shared Backup Helpers

**Files:**
- Create: `scripts/local_backup_common.py`
- Test: `tests/test_local_backup_common.py`

- [ ] **Step 1: Write shared-helper tests**

Create `tests/test_local_backup_common.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from scripts.local_backup_common import create_backup_dir
from scripts.local_backup_common import load_env_file
from scripts.local_backup_common import sha256_file
from scripts.local_backup_common import summarize_file
from scripts.local_backup_common import write_json
from scripts.local_backup_common import write_jsonl


def test_load_env_file_sets_missing_values_without_overwriting(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local-backup"
    env_file.write_text(
        "SUPABASE_URL=https://example.supabase.co\n"
        "SUPABASE_SECRET_KEY='secret-value'\n"
        "EXISTING=from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EXISTING", "from-env")

    loaded = load_env_file(env_file)

    assert loaded == {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SECRET_KEY": "secret-value",
        "EXISTING": "from-file",
    }
    assert loaded["SUPABASE_SECRET_KEY"] == "secret-value"
    assert loaded["EXISTING"] == "from-file"


def test_write_json_and_jsonl_create_utf8_files(tmp_path):
    json_path = tmp_path / "manifest.json"
    jsonl_path = tmp_path / "rows.jsonl"

    write_json(json_path, {"status": "ok", "count": 2})
    write_jsonl(jsonl_path, [{"id": 1}, {"id": 2}])

    assert json.loads(json_path.read_text(encoding="utf-8")) == {"status": "ok", "count": 2}
    assert jsonl_path.read_text(encoding="utf-8").splitlines() == ['{"id":1}', '{"id":2}']


def test_sha256_and_summarize_file(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("abc", encoding="utf-8")

    summary = summarize_file(target)

    assert sha256_file(target) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert summary["path"] == str(target)
    assert summary["size_bytes"] == 3
    assert summary["sha256"] == sha256_file(target)


def test_create_backup_dir_uses_prefix_and_timestamp(tmp_path):
    backup_dir = create_backup_dir(tmp_path, "supabase", timestamp="20260601_120000")

    assert backup_dir == tmp_path / "supabase" / "20260601_120000"
    assert backup_dir.is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_local_backup_common.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.local_backup_common'`.

- [ ] **Step 3: Implement shared helpers**

Create `scripts/local_backup_common.py`:

```python
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def load_env_file(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        name = key.strip()
        parsed = value.strip().strip("\"'")
        loaded[name] = parsed
        os.environ.setdefault(name, parsed)
    return loaded


def create_backup_dir(root: Path, category: str, *, timestamp: str | None = None) -> Path:
    run_id = timestamp or utc_timestamp()
    backup_dir = root / category / run_id
    backup_dir.mkdir(parents=True, exist_ok=False)
    return backup_dir


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_file(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_local_backup_common.py -q
```

Expected: PASS, `4 passed`.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts/local_backup_common.py tests/test_local_backup_common.py
git commit -m "feat: add local backup helpers"
```

Expected: commit succeeds after local git identity is configured.

## Task 2: Supabase Inventory Export

**Files:**
- Create: `scripts/backup_supabase_inventory.py`
- Test: `tests/test_backup_supabase_inventory.py`

- [ ] **Step 1: Write Supabase exporter tests**

Create `tests/test_backup_supabase_inventory.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from scripts.backup_supabase_inventory import DEFAULT_TABLES
from scripts.backup_supabase_inventory import SupabaseRestClient
from scripts.backup_supabase_inventory import build_table_url
from scripts.backup_supabase_inventory import export_supabase_tables


class FakeResponse:
    def __init__(self, rows, status_code=200, content_range="0-0/1"):
        self._rows = rows
        self.status_code = status_code
        self.headers = {"content-range": content_range}
        self.text = json.dumps(rows)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._rows


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, headers, timeout):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        if "run_artifacts" in url:
            return FakeResponse([{"id": "a1", "storage_path": "output/a.xlsx"}], content_range="0-0/1")
        return FakeResponse([], content_range="*/0")


def test_default_tables_include_required_domain_and_audit_tables():
    required = {
        "organizations",
        "users",
        "user_profiles",
        "pipeline_runs",
        "pipeline_logs",
        "run_artifacts",
        "tracker_entries",
        "download_audit_logs",
        "login_audit_logs",
        "project_sales_claims",
        "project_related_notice_cache",
    }

    assert required.issubset(set(DEFAULT_TABLES))


def test_build_table_url_encodes_select_and_order():
    url = build_table_url("https://example.supabase.co", "tracker_entries", offset=100, limit=50)

    assert url == "https://example.supabase.co/rest/v1/tracker_entries?select=*&offset=100&limit=50"


def test_export_supabase_tables_writes_jsonl_and_manifest(tmp_path):
    session = FakeSession()
    client = SupabaseRestClient(
        base_url="https://example.supabase.co",
        api_key="secret",
        session=session,
        page_size=500,
        timeout_sec=5,
    )

    manifest = export_supabase_tables(
        client,
        tmp_path,
        tables=["run_artifacts", "pipeline_runs"],
        timestamp="20260601_120000",
    )

    assert manifest["tables"]["run_artifacts"]["row_count"] == 1
    assert manifest["tables"]["pipeline_runs"]["row_count"] == 0
    assert (tmp_path / "tables" / "run_artifacts.jsonl").read_text(encoding="utf-8").strip() == (
        '{"id":"a1","storage_path":"output/a.xlsx"}'
    )
    assert (tmp_path / "manifest.json").exists()
    assert session.calls[0]["headers"]["apikey"] == "secret"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_backup_supabase_inventory.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.backup_supabase_inventory'`.

- [ ] **Step 3: Implement Supabase exporter**

Create `scripts/backup_supabase_inventory.py`:

```python
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_backup_common import create_backup_dir
from scripts.local_backup_common import load_env_file
from scripts.local_backup_common import summarize_file
from scripts.local_backup_common import write_json
from scripts.local_backup_common import write_jsonl


DEFAULT_TABLES = (
    "organizations",
    "users",
    "user_profiles",
    "organization_memberships",
    "invitations",
    "audit_logs",
    "pipeline_runs",
    "pipeline_logs",
    "run_artifacts",
    "saved_run_presets",
    "tracker_entries",
    "tracker_entry_audit_logs",
    "tracker_change_events",
    "tracker_entry_snapshots",
    "home_bootstrap_snapshots",
    "backfill_conflicts",
    "download_audit_logs",
    "login_audit_logs",
    "project_sales_claims",
    "project_sales_claim_events",
    "project_related_notice_cache",
    "related_notice_publications",
)


def build_table_url(base_url: str, table: str, *, offset: int, limit: int) -> str:
    query = urlencode({"select": "*", "offset": str(offset), "limit": str(limit)}, safe="*")
    return f"{base_url.rstrip('/')}/rest/v1/{table}?{query}"


class SupabaseRestClient:
    def __init__(self, *, base_url: str, api_key: str, session: Any | None = None, page_size: int = 1000, timeout_sec: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = session or requests.Session()
        self.page_size = page_size
        self.timeout_sec = timeout_sec

    def fetch_table(self, table: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            url = build_table_url(self.base_url, table, offset=offset, limit=self.page_size)
            response = self.session.get(
                url,
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                    "Prefer": "count=exact",
                },
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise RuntimeError(f"Supabase table {table} returned non-list payload")
            rows.extend(page)
            if len(page) < self.page_size:
                return rows
            offset += self.page_size


def export_supabase_tables(
    client: SupabaseRestClient,
    backup_dir: Path,
    *,
    tables: list[str],
    timestamp: str,
) -> dict[str, Any]:
    tables_dir = backup_dir / "tables"
    manifest: dict[str, Any] = {
        "kind": "supabase_inventory",
        "timestamp": timestamp,
        "source_url": client.base_url,
        "tables": {},
        "files": [],
    }
    for table in tables:
        table_path = tables_dir / f"{table}.jsonl"
        try:
            rows = client.fetch_table(table)
            write_jsonl(table_path, rows)
            table_summary = summarize_file(table_path)
            manifest["tables"][table] = {
                "status": "exported",
                "row_count": len(rows),
                "path": str(table_path),
                "size_bytes": table_summary["size_bytes"],
                "sha256": table_summary["sha256"],
            }
            manifest["files"].append(table_summary)
        except Exception as exc:
            manifest["tables"][table] = {
                "status": "failed",
                "row_count": 0,
                "error": str(exc),
            }
    write_json(backup_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Supabase table inventory for local app migration.")
    parser.add_argument("--env-file", default=".env.local-backup")
    parser.add_argument("--backup-root", default="backups")
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--tables", default="")
    parser.add_argument("--page-size", type=int, default=1000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    base_url = os.environ.get("SUPABASE_URL", "").strip()
    api_key = (
        os.environ.get("SUPABASE_SECRET_KEY", "").strip()
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ.get("SUPABASE_SECRET", "").strip()
    )
    if not base_url or not api_key:
        raise SystemExit("SUPABASE_URL and a service key are required")
    tables = [item.strip() for item in args.tables.split(",") if item.strip()] or list(DEFAULT_TABLES)
    backup_dir = create_backup_dir(Path(args.backup_root), "supabase", timestamp=args.timestamp or None)
    client = SupabaseRestClient(base_url=base_url, api_key=api_key, page_size=args.page_size)
    manifest = export_supabase_tables(client, backup_dir, tables=tables, timestamp=backup_dir.name)
    failed = [name for name, item in manifest["tables"].items() if item["status"] != "exported"]
    print(f"Supabase backup written: {backup_dir}")
    print(f"Tables exported: {len(tables) - len(failed)} / {len(tables)}")
    if failed:
        print("Failed tables: " + ", ".join(failed))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_backup_supabase_inventory.py tests/test_local_backup_common.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts/backup_supabase_inventory.py tests/test_backup_supabase_inventory.py
git commit -m "feat: add supabase backup inventory export"
```

Expected: commit succeeds.

## Task 3: EC2 File Inventory

**Files:**
- Create: `scripts/backup_ec2_inventory.py`
- Test: `tests/test_backup_ec2_inventory.py`

- [ ] **Step 1: Write EC2 inventory tests**

Create `tests/test_backup_ec2_inventory.py`:

```python
from __future__ import annotations

import json

from scripts.backup_ec2_inventory import build_find_command
from scripts.backup_ec2_inventory import parse_find_output
from scripts.backup_ec2_inventory import write_ec2_inventory


def test_build_find_command_quotes_paths_for_remote_shell():
    command = build_find_command(["/home/ubuntu/app/output", "/home/ubuntu/app/logs"])

    assert "find" in command
    assert "'/home/ubuntu/app/output'" in command
    assert "'/home/ubuntu/app/logs'" in command
    assert "%p\\t%s\\t%TY-%Tm-%TdT%TH:%TM:%TS%Tz\\n" in command


def test_parse_find_output_returns_file_records():
    output = "/app/output/a.xlsx\t123\t2026-06-01T12:30:00.000000000+0900\n"

    rows = parse_find_output(output)

    assert rows == [
        {
            "path": "/app/output/a.xlsx",
            "size_bytes": 123,
            "modified_at": "2026-06-01T12:30:00.000000000+0900",
        }
    ]


def test_write_ec2_inventory_writes_manifest(tmp_path):
    manifest = write_ec2_inventory(
        tmp_path,
        ssh_target="ubuntu@example",
        paths=["/app/output"],
        files=[{"path": "/app/output/a.xlsx", "size_bytes": 123, "modified_at": "2026"}],
        timestamp="20260601_120000",
    )

    assert manifest["ssh_target"] == "ubuntu@example"
    assert manifest["file_count"] == 1
    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["file_count"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_backup_ec2_inventory.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.backup_ec2_inventory'`.

- [ ] **Step 3: Implement EC2 inventory script**

Create `scripts/backup_ec2_inventory.py`:

```python
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
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


def build_find_command(paths: list[str]) -> str:
    quoted_paths = " ".join(shlex.quote(path) for path in paths)
    return (
        "find "
        + quoted_paths
        + " -type f -printf '%p\\t%s\\t%TY-%Tm-%TdT%TH:%TM:%TS%Tz\\n' 2>/dev/null"
    )


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


def run_ssh_find(ssh_target: str, paths: list[str], *, timeout_sec: int = 120) -> list[dict[str, Any]]:
    command = build_find_command(paths)
    result = subprocess.run(
        ["ssh", ssh_target, command],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_sec,
    )
    return parse_find_output(result.stdout)


def write_ec2_inventory(
    backup_dir: Path,
    *,
    ssh_target: str,
    paths: list[str],
    files: list[dict[str, Any]],
    timestamp: str,
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
    write_json(backup_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory EC2 app-owned files before local migration.")
    parser.add_argument("--env-file", default=".env.local-backup")
    parser.add_argument("--backup-root", default="backups")
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--ssh-target", default="")
    parser.add_argument("--paths", default="")
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
    backup_dir = create_backup_dir(Path(args.backup_root), "ec2", timestamp=args.timestamp or None)
    if args.dry_run:
        files: list[dict[str, Any]] = []
        write_json(backup_dir / "dry-run-command.json", {"ssh_target": ssh_target, "command": build_find_command(paths)})
    else:
        files = run_ssh_find(ssh_target, paths)
    manifest = write_ec2_inventory(backup_dir, ssh_target=ssh_target, paths=paths, files=files, timestamp=backup_dir.name)
    print(f"EC2 inventory written: {backup_dir}")
    print(f"Files inventoried: {manifest['file_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_backup_ec2_inventory.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts/backup_ec2_inventory.py tests/test_backup_ec2_inventory.py
git commit -m "feat: add ec2 file inventory export"
```

Expected: commit succeeds.

## Task 4: Artifact Reconciliation

**Files:**
- Create: `scripts/reconcile_backup_artifacts.py`
- Test: `tests/test_reconcile_backup_artifacts.py`

- [ ] **Step 1: Write reconciliation tests**

Create `tests/test_reconcile_backup_artifacts.py`:

```python
from __future__ import annotations

import json

from scripts.reconcile_backup_artifacts import normalize_path_for_match
from scripts.reconcile_backup_artifacts import reconcile_artifacts
from scripts.reconcile_backup_artifacts import write_reconciliation_report


def test_normalize_path_for_match_handles_slashes_and_relative_prefixes():
    assert normalize_path_for_match("\\output\\artifacts\\a.xlsx") == "output/artifacts/a.xlsx"
    assert normalize_path_for_match("/home/ubuntu/app/output/artifacts/a.xlsx").endswith("output/artifacts/a.xlsx")


def test_reconcile_artifacts_matches_suffix_paths():
    artifacts = [
        {"id": "a1", "storage_path": "output/artifacts/a.xlsx"},
        {"id": "a2", "storage_path": "output/artifacts/missing.xlsx"},
    ]
    ec2_files = [
        {"path": "/home/ubuntu/app/output/artifacts/a.xlsx", "size_bytes": 12, "modified_at": "2026"},
    ]

    report = reconcile_artifacts(artifacts, ec2_files)

    assert report["artifact_count"] == 2
    assert report["matched_count"] == 1
    assert report["missing_count"] == 1
    assert report["missing"][0]["id"] == "a2"


def test_write_reconciliation_report_writes_json(tmp_path):
    report = {"artifact_count": 1, "matched_count": 1, "missing_count": 0, "matched": [], "missing": []}

    write_reconciliation_report(tmp_path, report)

    assert json.loads((tmp_path / "artifact_reconciliation.json").read_text(encoding="utf-8"))["artifact_count"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_reconcile_backup_artifacts.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.reconcile_backup_artifacts'`.

- [ ] **Step 3: Implement artifact reconciliation**

Create `scripts/reconcile_backup_artifacts.py`:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_backup_common import write_json


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def normalize_path_for_match(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    while normalized.startswith("./") or normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def reconcile_artifacts(artifacts: list[dict[str, Any]], ec2_files: list[dict[str, Any]]) -> dict[str, Any]:
    file_paths = [(item, normalize_path_for_match(str(item.get("path") or ""))) for item in ec2_files]
    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for artifact in artifacts:
        storage_path = normalize_path_for_match(str(artifact.get("storage_path") or ""))
        if not storage_path:
            missing.append({**artifact, "missing_reason": "empty storage_path"})
            continue
        match = next((item for item, path in file_paths if path.endswith(storage_path) or storage_path.endswith(path)), None)
        if match is None:
            missing.append({**artifact, "missing_reason": "no matching EC2 file path"})
        else:
            matched.append({"artifact": artifact, "file": match})
    return {
        "artifact_count": len(artifacts),
        "ec2_file_count": len(ec2_files),
        "matched_count": len(matched),
        "missing_count": len(missing),
        "matched": matched,
        "missing": missing,
    }


def write_reconciliation_report(output_dir: Path, report: dict[str, Any]) -> None:
    write_json(output_dir / "artifact_reconciliation.json", report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile Supabase run_artifacts rows with EC2 file inventory.")
    parser.add_argument("--supabase-dir", required=True)
    parser.add_argument("--ec2-dir", required=True)
    parser.add_argument("--output-dir", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    supabase_dir = Path(args.supabase_dir)
    ec2_dir = Path(args.ec2_dir)
    output_dir = Path(args.output_dir) if args.output_dir else supabase_dir
    artifacts = read_jsonl(supabase_dir / "tables" / "run_artifacts.jsonl")
    ec2_files = read_jsonl(ec2_dir / "files.jsonl")
    report = reconcile_artifacts(artifacts, ec2_files)
    write_reconciliation_report(output_dir, report)
    print(f"Artifacts matched: {report['matched_count']} / {report['artifact_count']}")
    if report["missing_count"]:
        print(f"Missing artifacts: {report['missing_count']}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_reconcile_backup_artifacts.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts/reconcile_backup_artifacts.py tests/test_reconcile_backup_artifacts.py
git commit -m "feat: reconcile backup artifacts"
```

Expected: commit succeeds.

## Task 5: Windows Backup Wrapper

**Files:**
- Create: `scripts/local_backup_inventory.ps1`
- Test: manual dry-run command

- [ ] **Step 1: Create PowerShell wrapper**

Create `scripts/local_backup_inventory.ps1`:

```powershell
param(
  [string]$EnvFile = ".env.local-backup",
  [string]$BackupRoot = "backups",
  [string]$Timestamp = "",
  [switch]$DryRunEc2
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Timestamp)) {
  $Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

python scripts/backup_supabase_inventory.py `
  --env-file $EnvFile `
  --backup-root $BackupRoot `
  --timestamp $Timestamp

$ec2Args = @(
  "scripts/backup_ec2_inventory.py",
  "--env-file", $EnvFile,
  "--backup-root", $BackupRoot,
  "--timestamp", $Timestamp
)
if ($DryRunEc2) {
  $ec2Args += "--dry-run"
}
python @ec2Args

$supabaseDir = Join-Path $BackupRoot "supabase\$Timestamp"
$ec2Dir = Join-Path $BackupRoot "ec2\$Timestamp"
python scripts/reconcile_backup_artifacts.py `
  --supabase-dir $supabaseDir `
  --ec2-dir $ec2Dir `
  --output-dir $supabaseDir

Write-Host "Local backup inventory complete: $Timestamp"
```

- [ ] **Step 2: Run dry-run wrapper**

Create a local `.env.local-backup` with non-production test values:

```text
SUPABASE_URL=https://example.supabase.co
SUPABASE_SECRET_KEY=test-key
EC2_SSH_TARGET=ubuntu@example
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_backup_inventory.ps1 -Timestamp 20260601_120000 -DryRunEc2
```

Expected: Supabase step fails against `example.supabase.co` with an HTTP/network error, and no EC2 connection is attempted because EC2 is in dry-run mode. This verifies the wrapper wiring without using real credentials.

- [ ] **Step 3: Commit**

Run:

```powershell
git add scripts/local_backup_inventory.ps1
git commit -m "feat: add local backup inventory wrapper"
```

Expected: commit succeeds.

## Task 6: Ignore Local Backups And Document Commands

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Update `.gitignore`**

Append:

```gitignore
backups/
.env.local-backup
.env.local-backup.*
```

- [ ] **Step 2: Add README backup section**

Add this section near the existing local run instructions in `README.md`:

```markdown
## Local conversion backup inventory

Before converting the hosted app to local SQLite/storage, create a cloud data inventory.

Create `.env.local-backup` locally. Do not commit it.

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
EC2_SSH_TARGET=ubuntu@your-ec2-host
EC2_BACKUP_PATHS=/home/ubuntu/notice-winner-pipeline-web/output,/home/ubuntu/notice-winner-pipeline-web/input,/home/ubuntu/notice-winner-pipeline-web/logs
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_backup_inventory.ps1 -Timestamp 20260601_120000
```

Outputs are written under timestamped directories such as `backups/supabase/20260601_120000/` and `backups/ec2/20260601_120000/`. The Supabase manifest contains table row counts and checksums. The EC2 manifest contains app-owned file paths, sizes, and modified timestamps. `artifact_reconciliation.json` reports whether `run_artifacts.storage_path` rows have matching EC2 files.
```

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest tests/test_local_backup_common.py tests/test_backup_supabase_inventory.py tests/test_backup_ec2_inventory.py tests/test_reconcile_backup_artifacts.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

Run:

```powershell
git add .gitignore README.md
git commit -m "docs: document local backup inventory"
```

Expected: commit succeeds.

## Task 7: Real Backup Execution Checklist

**Files:**
- No code change.
- Output: `backups/supabase/20260601_120000/manifest.json`
- Output: `backups/ec2/20260601_120000/manifest.json`
- Output: `backups/supabase/20260601_120000/artifact_reconciliation.json`

- [ ] **Step 1: Configure git identity before commits if needed**

Run with the correct user identity:

```powershell
git config user.name "local-migration-worker"
git config user.email "local-migration-worker@example.invalid"
```

Expected: `git commit` works for future implementation commits.

- [ ] **Step 2: Create real backup env file outside git**

Create `.env.local-backup` with real values from the operator's credential store. The file must define these keys exactly:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
EC2_SSH_TARGET
EC2_BACKUP_PATHS
```

Run this validation command after creating the file:

```powershell
Select-String -Path .env.local-backup -Pattern "^(SUPABASE_URL|SUPABASE_SERVICE_ROLE_KEY|EC2_SSH_TARGET|EC2_BACKUP_PATHS)="
```

Expected: four matching lines are printed. Do not print the file contents in shared logs because it contains a service key.

Expected: `.env.local-backup` is ignored by git.

- [ ] **Step 3: Run real inventory**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_backup_inventory.ps1
```

Expected:

- `backups/supabase/20260601_120000/manifest.json` exists.
- `backups/ec2/20260601_120000/manifest.json` exists.
- `backups/supabase/20260601_120000/artifact_reconciliation.json` exists.
- The command exits `0` if every expected table exports and every artifact is matched.
- The command exits `2` if a table export fails or artifact files are missing; inspect the manifest before proceeding.

- [ ] **Step 4: Review row counts before local DB work**

Open:

```powershell
Get-Content backups/supabase/20260601_120000/manifest.json
```

Expected: row counts are visible for every exported table. If any table has `"status": "failed"`, do not start SQLite migration until the failure is explained.

- [ ] **Step 5: Commit implementation branch after successful dry-run tests**

Run:

```powershell
git status --short
git add scripts/local_backup_common.py scripts/backup_supabase_inventory.py scripts/backup_ec2_inventory.py scripts/reconcile_backup_artifacts.py scripts/local_backup_inventory.ps1 tests/test_local_backup_common.py tests/test_backup_supabase_inventory.py tests/test_backup_ec2_inventory.py tests/test_reconcile_backup_artifacts.py .gitignore README.md
git commit -m "feat: add local migration backup inventory"
```

Expected: implementation commit exists and backup output files remain untracked because `backups/` is ignored.

## Self-Review

Spec coverage:

- Supabase backup before migration: covered by Tasks 2, 5, and 7.
- EC2 backup/inventory before migration: covered by Tasks 3, 5, and 7.
- Artifact reconciliation: covered by Task 4.
- Secrets not committed: covered by Tasks 6 and 7.
- No app behavior changes before backup: enforced by this plan scope.

Placeholder scan:

- This plan contains no unfinished code slots and no deferred implementation phrases.

Type consistency:

- `timestamp`, `backup_dir`, `manifest`, `storage_path`, and `files.jsonl` names are used consistently across scripts.
