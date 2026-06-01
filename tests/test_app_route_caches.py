from __future__ import annotations

import unittest
from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.sales_claims import SalesActor


def _auth_context(actor: SalesActor | None = None) -> SimpleNamespace:
    actor = actor or SalesActor(
        organization_id=uuid4(),
        user_id=uuid4(),
        email="admin@example.com",
        display_name="Admin",
        role="platform_admin",
    )
    return SimpleNamespace(
        authorized=True,
        organization_id=actor.organization_id,
        local_user_id=actor.user_id,
        email=actor.email,
        display_name=actor.display_name,
        role=actor.role,
    )


class AppRouteCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        from backend.api import app as app_module

        self.app_module = app_module
        for clear_name in (
            "_clear_organization_admin_bootstrap_cache",
            "_clear_dashboard_summary_cache",
            "_clear_sales_claim_summary_by_user_cache",
            "_clear_tracker_template_status_cache",
        ):
            clear_fn = getattr(app_module, clear_name, None)
            if callable(clear_fn):
                clear_fn()

    def tearDown(self) -> None:
        for clear_name in (
            "_clear_organization_admin_bootstrap_cache",
            "_clear_dashboard_summary_cache",
            "_clear_sales_claim_summary_by_user_cache",
            "_clear_tracker_template_status_cache",
        ):
            clear_fn = getattr(self.app_module, clear_name, None)
            if callable(clear_fn):
                clear_fn()
        if hasattr(self.app_module, "_TRACKER_MEMORY_SOFT_CAP_LAST_CLEAR_MONOTONIC"):
            self.app_module._TRACKER_MEMORY_SOFT_CAP_LAST_CLEAR_MONOTONIC = None

    def _admin_actor(self) -> SalesActor:
        return SalesActor(
            organization_id=uuid4(),
            user_id=uuid4(),
            email="admin@example.com",
            display_name="Admin",
            role="platform_admin",
        )

    def test_organization_panel_bootstrap_reuses_process_cache_and_invalidates_after_invitation_create(self) -> None:
        actor = self._admin_actor()
        calls = {
            "members": 0,
            "invitations": 0,
            "auth_audit": 0,
        }
        created_item = {
            "id": str(uuid4()),
            "organization_id": str(actor.organization_id),
            "email": "invitee@example.com",
            "role": "org_member",
            "display_name": "Invitee",
            "team_name": "Ops",
            "job_title": "Manager",
            "invite_token": "invite-token-123",
            "invite_url": "https://example.com/app/?invite_token=invite-token-123",
            "status": "pending",
            "expires_at": "2026-04-14T00:00:00Z",
            "created_at": "2026-04-07T00:00:00Z",
            "updated_at": "2026-04-07T00:00:00Z",
            "delivery_status": "manual",
            "delivery_message": "manual fallback",
            "initial_password": "Abcdef1!Ghijk2@",
        }

        class EmptyLogRepository:
            def list_logs(self, *, organization_id, limit):  # type: ignore[no-untyped-def]
                return []

        def _list_members(*, organization_id, include_inactive):  # type: ignore[no-untyped-def]
            calls["members"] += 1
            return []

        def _get_dashboard(*, organization_id, actor_role):  # type: ignore[no-untyped-def]
            calls["invitations"] += 1
            return {"items": [], "plan_summary": {}}

        def _list_auth_audit(*, organization_id, limit):  # type: ignore[no-untyped-def]
            calls["auth_audit"] += 1
            return []

        with (
            patch.object(self.app_module, "read_auth_context", return_value=_auth_context(actor)),
            patch.object(self.app_module, "_resolve_sales_actor", return_value=actor),
            patch.object(self.app_module, "list_local_users", side_effect=_list_members),
            patch.object(self.app_module, "get_organization_invitation_dashboard", side_effect=_get_dashboard),
            patch.object(self.app_module, "list_organization_audit_logs", side_effect=_list_auth_audit),
            patch.object(self.app_module, "_get_download_audit_log_repository", return_value=EmptyLogRepository()),
            patch.object(self.app_module, "_get_login_audit_log_repository", return_value=EmptyLogRepository()),
            patch.object(self.app_module, "invitation_email_delivery_enabled", return_value=False),
            patch.object(self.app_module, "create_invitation", return_value=dict(created_item)),
            TestClient(self.app_module.app) as client,
        ):
            first = client.get("/api/admin/organization-panel-bootstrap")
            second = client.get("/api/admin/organization-panel-bootstrap")
            created = client.post(
                "/api/auth/invitations",
                json={
                    "email": "invitee@example.com",
                    "role": "org_member",
                    "display_name": "Invitee",
                    "team_name": "Ops",
                    "job_title": "Manager",
                    "expires_in_days": 7,
                },
            )
            third = client.get("/api/admin/organization-panel-bootstrap")

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(third.status_code, 200, third.text)
        self.assertEqual(calls["members"], 2)
        self.assertEqual(calls["invitations"], 2)
        self.assertEqual(calls["auth_audit"], 2)

    def test_dashboard_summary_reuses_process_cache_within_ttl(self) -> None:
        call_count = 0
        payload = self.app_module.DashboardSummaryResponse(
            run_counts={"success": 1},
            tracker_total=2,
            tracker_edited_total=0,
            repository_backends={"artifacts": "in_memory"},
            artifact_metadata_persistent=False,
            synthetic_debug_enabled=False,
            recent_failed_runs=[],
            latest_reports={},
            active_report_jobs=[],
        )

        def _build() -> object:
            nonlocal call_count
            call_count += 1
            return payload

        with (
            patch.object(self.app_module, "read_auth_context", return_value=_auth_context(self._admin_actor())),
            patch.object(self.app_module, "_build_dashboard_summary", side_effect=_build),
            TestClient(self.app_module.app) as client,
        ):
            first = client.get("/api/dashboard/summary")
            second = client.get("/api/dashboard/summary")

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(call_count, 1)

    def test_sales_claim_summary_by_user_reuses_process_cache_within_ttl(self) -> None:
        actor = self._admin_actor()
        call_count = 0

        class FakeRepository:
            def summarize_by_user(self, *, organization_id):  # type: ignore[no-untyped-def]
                nonlocal call_count
                call_count += 1
                return [
                    {
                        "user_id": actor.user_id,
                        "user_name": "Admin",
                        "user_email": actor.email,
                        "active_project_count": 1,
                        "total_low_krw": 1000,
                        "total_high_krw": 2000,
                        "projects": [],
                    }
                ]

        with (
            patch.object(self.app_module, "read_auth_context", return_value=_auth_context(actor)),
            patch.object(self.app_module, "_resolve_sales_actor", return_value=actor),
            patch.object(self.app_module, "_get_sales_claim_repository", return_value=FakeRepository()),
            TestClient(self.app_module.app) as client,
        ):
            first = client.get("/api/sales-claims/summary-by-user")
            second = client.get("/api/sales-claims/summary-by-user")

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(call_count, 1)

    def test_tracker_template_status_reuses_process_cache_and_invalidates_after_upload(self) -> None:
        describe_call_count = 0
        status_payload = {
            "source": "env_override",
            "source_label": "Env Override",
            "file_name": "template.xlsx",
            "original_file_name": "",
            "active_path": "/tmp/template.xlsx",
            "size_bytes": 128,
            "updated_at": "2026-04-07T00:00:00Z",
        }

        class FakeUploadFile:
            filename = "uploaded.xlsx"

            async def read(self) -> bytes:
                return b"fake-xlsx"

        def _describe() -> dict[str, object]:
            nonlocal describe_call_count
            describe_call_count += 1
            return dict(status_payload)

        with patch.object(
            self.app_module,
            "_load_artifact_file_helpers",
            return_value={
                "describe_active_tracker_template": _describe,
                "save_uploaded_tracker_template": lambda payload, original_file_name: dict(status_payload),
                "clear_uploaded_tracker_template": lambda: dict(status_payload),
            },
        ):
            first = self.app_module.get_tracker_template_status()
            second = self.app_module.get_tracker_template_status()
            uploaded = self.app_module.upload_tracker_template(FakeUploadFile())
            if hasattr(uploaded, "__await__"):
                import asyncio

                asyncio.run(uploaded)
            third = self.app_module.get_tracker_template_status()

        self.assertEqual(first.source, "env_override")
        self.assertEqual(second.source, "env_override")
        self.assertEqual(third.source, "env_override")
        self.assertEqual(describe_call_count, 2)

    def test_tracker_memory_soft_cap_clears_tracker_caches_when_rss_exceeds_threshold(self) -> None:
        threshold_bytes = 900 * 1024 * 1024

        with (
            patch.object(self.app_module, "_get_process_rss_bytes", return_value=threshold_bytes + 1),
            patch.object(self.app_module, "_clear_global_tracker_rows_cache") as clear_cache,
            patch.object(self.app_module.time, "monotonic", return_value=1000.0),
        ):
            did_clear = self.app_module._maybe_clear_tracker_caches_for_memory_soft_cap()

        self.assertTrue(did_clear)
        clear_cache.assert_called_once_with()
        self.assertEqual(self.app_module._TRACKER_MEMORY_SOFT_CAP_LAST_CLEAR_MONOTONIC, 1000.0)

    def test_tracker_memory_soft_cap_respects_cooldown_between_clears(self) -> None:
        threshold_bytes = 900 * 1024 * 1024

        with (
            patch.object(self.app_module, "_get_process_rss_bytes", return_value=threshold_bytes + 1),
            patch.object(self.app_module, "_clear_global_tracker_rows_cache") as clear_cache,
            patch.object(self.app_module.time, "monotonic", side_effect=[1000.0, 1100.0]),
        ):
            first = self.app_module._maybe_clear_tracker_caches_for_memory_soft_cap()
            second = self.app_module._maybe_clear_tracker_caches_for_memory_soft_cap()

        self.assertTrue(first)
        self.assertFalse(second)
        clear_cache.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
