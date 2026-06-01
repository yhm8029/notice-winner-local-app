from __future__ import annotations

from datetime import datetime
from unittest.mock import patch
from uuid import UUID

from backend.repositories.in_memory_login_audit_logs import InMemoryLoginAuditLogRepository
from backend.repositories.login_audit_logs import LoginAuditLogRepository
from backend.repositories.login_audit_logs import LoginAuditLogRow
from backend.repositories.supabase_login_audit_logs import SupabaseLoginAuditLogRepository
from backend.repositories.supabase_login_audit_logs import SupabaseLoginAuditLogRepositoryConfig
from backend.repositories.supabase_login_audit_logs import LOGIN_AUDIT_LOG_SELECT

ORG_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_ID = UUID("33333333-3333-3333-3333-333333333333")


def test_in_memory_login_audit_logs_appends_and_lists_newest_first() -> None:
    repo: LoginAuditLogRepository = InMemoryLoginAuditLogRepository()

    first = repo.create_log(
        organization_id=ORG_ID,
        user_id=USER_ID,
        user_email="user@example.com",
        user_role="org_admin",
        ip_address="203.0.113.9",
        user_agent="pytest-agent/1.0",
    )
    repo.create_log(
        organization_id=OTHER_ORG_ID,
        user_id=USER_ID,
        user_email="other@example.com",
        user_role="org_member",
        ip_address="198.51.100.7",
        user_agent="browser/2.0",
    )
    second = repo.create_log(
        organization_id=ORG_ID,
        user_id=USER_ID,
        user_email="user@example.com",
        user_role="org_admin",
        ip_address="203.0.113.10",
        user_agent="pytest-agent/1.0",
    )

    rows = repo.list_logs(organization_id=ORG_ID, limit=10)

    assert len(rows) == 2
    assert rows[0]["id"] == second["id"]
    assert rows[1]["id"] == first["id"]
    assert rows[0]["organization_id"] == ORG_ID
    assert rows[0]["user_id"] == USER_ID
    assert rows[0]["user_email"] == "user@example.com"
    assert rows[0]["user_role"] == "org_admin"
    assert rows[0]["ip_address"] == "203.0.113.10"
    assert rows[0]["user_agent"] == "pytest-agent/1.0"
    assert isinstance(rows[0]["created_at"], datetime)
    assert rows[0]["created_at"] >= rows[1]["created_at"]


def test_supabase_login_audit_logs_create_and_list_match_repository_contract() -> None:
    config = SupabaseLoginAuditLogRepositoryConfig(
        base_url="https://example.supabase.co",
        api_key="secret",
        timeout_seconds=10.0,
    )
    repo = SupabaseLoginAuditLogRepository(config)
    created_row: LoginAuditLogRow = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "organization_id": str(ORG_ID),
        "user_id": str(USER_ID),
        "user_email": "user@example.com",
        "user_role": "org_admin",
        "ip_address": "203.0.113.10",
        "user_agent": "pytest-agent/1.0",
        "created_at": "2026-03-31T09:00:00Z",
    }

    with patch.object(repo, "_request_json", return_value=([created_row], {})) as request_json_mock:
        row = repo.create_log(
            organization_id=ORG_ID,
            user_id=USER_ID,
            user_email="user@example.com",
            user_role="org_admin",
            ip_address="203.0.113.10",
            user_agent="pytest-agent/1.0",
        )

    assert row == created_row
    assert request_json_mock.call_args.kwargs["method"] == "POST"
    assert request_json_mock.call_args.kwargs["path"] == "/login_audit_logs"
    assert request_json_mock.call_args.kwargs["headers"] == {"Prefer": "return=representation"}
    assert request_json_mock.call_args.kwargs["payload"] == {
        "organization_id": str(ORG_ID),
        "user_id": str(USER_ID),
        "user_email": "user@example.com",
        "user_role": "org_admin",
        "ip_address": "203.0.113.10",
        "user_agent": "pytest-agent/1.0",
    }

    with patch.object(repo, "_request_json", return_value=([created_row], {})) as request_json_mock:
        rows = repo.list_logs(organization_id=ORG_ID, limit=5)

    assert rows == [created_row]
    assert request_json_mock.call_args.kwargs["method"] == "GET"
    assert request_json_mock.call_args.kwargs["path"] == "/login_audit_logs"
    assert request_json_mock.call_args.kwargs["query"] == [
        ("select", LOGIN_AUDIT_LOG_SELECT),
        ("organization_id", f"eq.{ORG_ID}"),
        ("order", "created_at.desc"),
        ("limit", "5"),
    ]
