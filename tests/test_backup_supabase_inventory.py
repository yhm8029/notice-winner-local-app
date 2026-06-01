from __future__ import annotations

import json

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
