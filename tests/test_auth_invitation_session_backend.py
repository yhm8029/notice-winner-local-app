from __future__ import annotations

import unittest
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from backend.api.auth_runtime import AuthRuntimeError
from backend.services.auth_invitation_session_backend import can_use_invite_password_setup
from backend.services.auth_invitation_session_backend import raise_accept_invitation_error
from backend.services.auth_invitation_session_backend import require_invitation_email_match
from backend.services.auth_invitation_session_backend import resolve_pending_invitation_token_for_email
from backend.services.auth_invitation_session_backend import resolve_session_invitation_token


class AuthInvitationSessionBackendTests(unittest.TestCase):
    def test_require_invitation_email_match_rejects_mismatch(self) -> None:
        with self.assertRaises(AuthRuntimeError) as ctx:
            require_invitation_email_match(
                invite_token="invite-token",
                email="member@example.com",
                normalize_email_fn=lambda value: str(value).strip().lower(),
                get_invitation_by_token_fn=lambda token: {"status": "pending", "email": "other@example.com"},
                auth_error_cls=AuthRuntimeError,
            )

        self.assertEqual(ctx.exception.code, "invite_email_mismatch")

    def test_resolve_pending_invitation_token_for_email_requires_invitation_when_missing(self) -> None:
        with self.assertRaises(AuthRuntimeError) as ctx:
            resolve_pending_invitation_token_for_email(
                email="member@example.com",
                invite_token="",
                required=True,
                list_pending_invitations_by_email_fn=lambda *, email: [],
                auth_error_cls=AuthRuntimeError,
            )

        self.assertEqual(ctx.exception.code, "invite_required")

    def test_resolve_session_invitation_token_rejects_ambiguous_pending_invitations(self) -> None:
        with self.assertRaises(AuthRuntimeError) as ctx:
            resolve_session_invitation_token(
                invite_token="",
                auth_user_id="auth-user-id",
                email="member@example.com",
                list_pending_invitations_by_email_fn=lambda *, email: [
                    {"invite_token": "invite-1", "accepted_user_id": ""},
                    {"invite_token": "invite-2", "accepted_user_id": ""},
                ],
                auth_error_cls=AuthRuntimeError,
            )

        self.assertEqual(ctx.exception.code, "invite_ambiguous")

    def test_raise_accept_invitation_error_persists_expired_status(self) -> None:
        persisted: list[tuple[str, str]] = []

        with self.assertRaises(AuthRuntimeError) as ctx:
            raise_accept_invitation_error(
                exc=AuthRuntimeError("invitation has expired"),
                invitation_id="invitation-id",
                persist_invitation_status_fn=lambda *, invitation_id, status: persisted.append((invitation_id, status)),
                auth_error_cls=AuthRuntimeError,
            )

        self.assertEqual(ctx.exception.code, "invite_expired")
        self.assertEqual(persisted, [("invitation-id", "expired")])

    def test_can_use_invite_password_setup_accepts_recent_accepted_invite_for_same_user(self) -> None:
        accepted_at = datetime.now(timezone.utc) - timedelta(hours=1)

        allowed = can_use_invite_password_setup(
            auth_user_id="auth-user-id",
            email="member@example.com",
            invite_token="invite-token",
            normalize_email_fn=lambda value: str(value).strip().lower(),
            get_invitation_by_token_fn=lambda token: {
                "email": "member@example.com",
                "status": "accepted",
                "accepted_user_id": "auth-user-id",
                "accepted_at": accepted_at.isoformat(),
            },
            parse_datetime_value_fn=lambda value: datetime.fromisoformat(str(value)),
        )

        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
