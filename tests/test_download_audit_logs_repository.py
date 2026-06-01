from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from uuid import UUID

from backend.repositories import DownloadAuditLogRepository
from backend.repositories import DownloadAuditLogRow
from backend.repositories import InMemoryDownloadAuditLogRepository
from backend.repositories import SupabaseDownloadAuditLogRepository
from backend.repositories import SupabaseDownloadAuditLogRepositoryConfig
from backend.repositories.supabase_download_audit_logs import DOWNLOAD_AUDIT_LOG_SELECT

ORG_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_ID = UUID("33333333-3333-3333-3333-333333333333")


def test_in_memory_download_audit_logs_appends_and_lists_newest_first() -> None:
    repo: DownloadAuditLogRepository = InMemoryDownloadAuditLogRepository()

    first = repo.create_log(
        organization_id=ORG_ID,
        user_id=USER_ID,
        user_email="user@example.com",
        user_role="org_admin",
        download_scope="my",
        download_format="csv",
        source_page="my_active_sales",
        file_name="my-sales.csv",
    )
    repo.create_log(
        organization_id=OTHER_ORG_ID,
        user_id=None,
        user_email="other@example.com",
        user_role="org_member",
        download_scope="company",
        download_format="xlsx",
        source_page="company_active_sales",
        file_name="company-sales.xlsx",
    )
    second = repo.create_log(
        organization_id=ORG_ID,
        user_id=USER_ID,
        user_email="user@example.com",
        user_role="org_admin",
        download_scope="global",
        download_format="xlsx",
        source_page="tracker_entries",
        file_name="project-status.xlsx",
    )

    rows = repo.list_logs(organization_id=ORG_ID, limit=10)

    assert len(rows) == 2
    assert rows[0]["id"] == second["id"]
    assert rows[1]["id"] == first["id"]
    assert rows[0]["download_scope"] == "global"
    assert rows[0]["download_format"] == "xlsx"
    assert rows[0]["source_page"] == "tracker_entries"
    assert rows[0]["organization_id"] == ORG_ID
    assert rows[0]["user_id"] == USER_ID
    assert isinstance(rows[0]["created_at"], datetime)
    assert rows[0]["created_at"] >= rows[1]["created_at"]


def test_supabase_download_audit_logs_create_and_list_match_repository_contract() -> None:
    config = SupabaseDownloadAuditLogRepositoryConfig(
        base_url="https://example.supabase.co",
        api_key="secret",
        timeout_seconds=10.0,
    )
    repo = SupabaseDownloadAuditLogRepository(config)
    created_row: DownloadAuditLogRow = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "organization_id": str(ORG_ID),
        "user_id": str(USER_ID),
        "user_email": "user@example.com",
        "user_role": "org_admin",
        "download_scope": "global",
        "download_format": "xlsx",
        "source_page": "tracker_entries",
        "file_name": "project-status.xlsx",
        "created_at": "2026-03-31T09:00:00Z",
    }

    with patch.object(repo, "_request_json", return_value=([created_row], {})) as request_json_mock:
        row = repo.create_log(
            organization_id=ORG_ID,
            user_id=USER_ID,
            user_email="user@example.com",
            user_role="org_admin",
            download_scope="global",
            download_format="xlsx",
            source_page="tracker_entries",
            file_name="project-status.xlsx",
        )

    assert row == created_row
    assert request_json_mock.call_args.kwargs["method"] == "POST"
    assert request_json_mock.call_args.kwargs["path"] == "/download_audit_logs"
    assert request_json_mock.call_args.kwargs["headers"] == {"Prefer": "return=representation"}
    assert request_json_mock.call_args.kwargs["payload"] == {
        "organization_id": str(ORG_ID),
        "user_id": str(USER_ID),
        "user_email": "user@example.com",
        "user_role": "org_admin",
        "download_scope": "global",
        "download_format": "xlsx",
        "source_page": "tracker_entries",
        "file_name": "project-status.xlsx",
    }

    with patch.object(repo, "_request_json", return_value=([created_row], {})) as request_json_mock:
        rows = repo.list_logs(organization_id=ORG_ID, limit=5)

    assert rows == [created_row]
    assert request_json_mock.call_args.kwargs["method"] == "GET"
    assert request_json_mock.call_args.kwargs["path"] == "/download_audit_logs"
    assert request_json_mock.call_args.kwargs["query"] == [
        ("select", DOWNLOAD_AUDIT_LOG_SELECT),
        ("organization_id", f"eq.{ORG_ID}"),
        ("order", "created_at.desc"),
        ("limit", "5"),
    ]
