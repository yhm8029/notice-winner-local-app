from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
from unittest import mock
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.api import app as app_module


class AuthAdminAccountsApiTests(TestCase):
    def test_password_reset_route_uses_flow_specific_response_model(self) -> None:
        route = next(
            route
            for route in app_module.app.routes
            if getattr(route, "path", "") == "/api/admin/accounts/{user_id}/password-reset"
            and "POST" in getattr(route, "methods", set())
        )

        self.assertEqual(getattr(route, "response_model", None).__name__, "AuthAdminAccountPasswordResetResponse")

    def test_post_admin_accounts_ignores_feature_flag_for_platform_admin(self) -> None:
        actor = SimpleNamespace(
            is_admin=True,
            role="platform_admin",
            organization_id=uuid4(),
            user_id=uuid4(),
            email="ops@example.com",
        )
        created_item = {
            "id": str(uuid4()),
            "email": "member@example.com",
            "display_name": "Member",
            "role": "org_member",
            "account_status": "active",
            "membership_status": "active",
            "password_setup_mode": "admin_set",
            "force_password_change": False,
        }

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=False, create=True),
            mock.patch.object(app_module, "create_platform_admin_account", return_value=created_item, create=True),
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                "/api/admin/accounts",
                json={
                    "email": "member@example.com",
                    "display_name": "Member",
                    "role": "org_member",
                    "password": "TempPass123!",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["email"], "member@example.com")

    def test_post_admin_accounts_rejects_non_platform_admin_actor(self) -> None:
        actor = SimpleNamespace(
            is_admin=True,
            role="org_admin",
            organization_id=uuid4(),
            user_id=uuid4(),
            email="admin@example.com",
        )

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=True, create=True),
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                "/api/admin/accounts",
                json={
                    "email": "member@example.com",
                    "display_name": "Member",
                    "role": "org_member",
                    "password": "TempPass123!",
                },
            )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["error"]["code"], "auth_forbidden")

    def test_post_admin_accounts_returns_created_item_for_platform_admin(self) -> None:
        actor = SimpleNamespace(
            is_admin=True,
            role="platform_admin",
            organization_id=uuid4(),
            user_id=uuid4(),
            email="ops@example.com",
        )
        created_item = {
            "id": str(uuid4()),
            "email": "member@example.com",
            "display_name": "Member",
            "role": "org_member",
            "account_status": "active",
            "membership_status": "active",
            "password_setup_mode": "admin_set",
            "force_password_change": False,
        }

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=True, create=True),
            mock.patch.object(app_module, "create_platform_admin_account", return_value=created_item, create=True) as create_mock,
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                "/api/admin/accounts",
                json={
                    "email": "member@example.com",
                    "display_name": "Member",
                    "role": "org_member",
                    "password": "TempPass123!",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["email"], "member@example.com")
        self.assertEqual(payload["role"], "org_member")
        create_mock.assert_called_once()

    def test_post_admin_account_password_reset_ignores_feature_flag_for_platform_admin(self) -> None:
        actor = SimpleNamespace(
            is_admin=True,
            role="platform_admin",
            organization_id=uuid4(),
            user_id=uuid4(),
            email="ops@example.com",
        )
        target_user_id = uuid4()

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=False, create=True),
            mock.patch.object(
                app_module,
                "list_local_users",
                return_value=[{"id": str(target_user_id), "email": "member@example.com"}],
            ),
            mock.patch.object(
                app_module,
                "reset_platform_admin_account_password",
                return_value={"message": "password reset scheduled"},
                create=True,
            ),
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                f"/api/admin/accounts/{target_user_id}/password-reset",
                json={"password": "TempPass123!"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["message"], "password reset scheduled")

    def test_post_admin_account_password_reset_rejects_bootstrap_platform_admin_target(self) -> None:
        actor = SimpleNamespace(
            is_admin=True,
            role="platform_admin",
            organization_id=uuid4(),
            user_id=uuid4(),
            email="ops@example.com",
        )
        target_user_id = uuid4()

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=True, create=True),
            mock.patch.object(app_module, "bootstrap_platform_admin_email", return_value="bootstrap@example.com"),
            mock.patch.object(
                app_module,
                "list_local_users",
                return_value=[{"id": str(target_user_id), "email": "bootstrap@example.com"}],
            ),
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                f"/api/admin/accounts/{target_user_id}/password-reset",
                json={"password": "TempPass123!"},
            )

        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["error"]["code"], "auth_user_protected")

    def test_post_admin_account_password_reset_rejects_self_target(self) -> None:
        actor_user_id = uuid4()
        actor = SimpleNamespace(
            is_admin=True,
            role="platform_admin",
            organization_id=uuid4(),
            user_id=actor_user_id,
            email="ops@example.com",
        )

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=True, create=True),
            mock.patch.object(
                app_module,
                "list_local_users",
                return_value=[{"id": str(actor_user_id), "email": "ops@example.com"}],
            ),
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                f"/api/admin/accounts/{actor_user_id}/password-reset",
                json={"password": "TempPass123!"},
            )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["error"]["code"], "auth_user_self_password_reset_forbidden")

    def test_post_admin_account_password_reset_returns_message_for_platform_admin(self) -> None:
        target_user_id = uuid4()
        actor = SimpleNamespace(
            is_admin=True,
            role="platform_admin",
            organization_id=uuid4(),
            user_id=uuid4(),
            email="ops@example.com",
        )

        with (
            mock.patch.object(app_module, "auth_is_enabled", return_value=False),
            mock.patch.object(app_module, "_resolve_sales_actor", return_value=actor),
            mock.patch.object(app_module, "platform_admin_account_creation_enabled", return_value=True, create=True),
            mock.patch.object(
                app_module,
                "list_local_users",
                return_value=[{"id": str(target_user_id), "email": "member@example.com"}],
            ),
            mock.patch.object(
                app_module,
                "reset_platform_admin_account_password",
                return_value={"message": "password reset scheduled"},
                create=True,
            ) as reset_mock,
            TestClient(app_module.app) as client,
        ):
            response = client.post(
                f"/api/admin/accounts/{target_user_id}/password-reset",
                json={"password": "TempPass123!"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["message"], "password reset scheduled")
        reset_mock.assert_called_once()
        self.assertEqual(reset_mock.call_args.kwargs["actor_user_id"], str(actor.user_id))
        self.assertEqual(reset_mock.call_args.kwargs["actor_role"], "platform_admin")
        self.assertEqual(reset_mock.call_args.kwargs["organization_id"], str(actor.organization_id))
        self.assertEqual(reset_mock.call_args.kwargs["user_id"], str(target_user_id))
