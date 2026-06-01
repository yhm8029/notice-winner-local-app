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
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        session: Any | None = None,
        page_size: int = 1000,
        timeout_sec: int = 30,
    ):
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
