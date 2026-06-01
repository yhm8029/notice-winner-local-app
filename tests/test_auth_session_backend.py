from __future__ import annotations

import unittest

from backend.services.auth_session_backend import build_session_response_payload


class AuthSessionBackendTests(unittest.TestCase):
    def test_build_session_response_payload_shapes_session_user_defaults(self) -> None:
        def _build_auth_status_response() -> dict[str, object]:
            return {
                "enabled": False,
                "authenticated": False,
                "authorized": False,
                "bootstrap_email": "bootstrap@example.com",
                "public_auth_url": "https://example.supabase.co/auth/v1",
                "public_api_key": "public-key",
                "public_auth_configured": True,
                "message": "ignored",
                "user": None,
            }

        response = build_session_response_payload(
            session_payload={
                "authorized": True,
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "membership_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "organization_id": "c8bfe667-2f4e-4c2a-8e6d-f0a4fba2c5ad",
                "organization_name": "Internal Operations",
                "message": "Session ready",
            },
            build_auth_status_response_fn=_build_auth_status_response,
        )

        self.assertEqual(response["enabled"], True)
        self.assertEqual(response["authenticated"], True)
        self.assertEqual(response["authorized"], True)
        self.assertEqual(response["bootstrap_email"], "bootstrap@example.com")
        self.assertEqual(response["public_auth_configured"], True)
        self.assertEqual(response["message"], "Session ready")
        self.assertEqual(
            response["user"],
            {
                "auth_user_id": "2d3fab62-2ea2-4b4e-95ea-0d2bf9e4b5b7",
                "local_user_id": "fb8d3775-6731-4761-a843-489fcfdb4cdd",
                "membership_id": "7f4b4c45-6d7b-4d95-9f7d-9b6c7e8f1001",
                "email": "member@example.com",
                "display_name": "Member",
                "role": "org_member",
                "status": "active",
                "account_status": "active",
                "membership_status": "active",
                "mobile_phone": "",
                "office_phone": "",
                "organization_id": "c8bfe667-2f4e-4c2a-8e6d-f0a4fba2c5ad",
                "organization_name": "Internal Operations",
            },
        )
