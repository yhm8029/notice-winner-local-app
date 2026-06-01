from __future__ import annotations

import base64
import json
import unittest
from unittest import mock

from backend.services.auth_session_cookie_backend import decode_signed_payload
from backend.services.auth_session_cookie_backend import encode_signed_payload
from backend.services.auth_session_cookie_backend import read_access_token_expires_in


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


class AuthSessionCookieBackendTests(unittest.TestCase):
    def test_encode_decode_round_trip(self) -> None:
        signed = encode_signed_payload(
            {"auth_user_id": "user-1", "authorized": True},
            session_secret=lambda: "secret",
            urlsafe_b64encode=_urlsafe_b64encode,
        )

        decoded = decode_signed_payload(
            signed,
            session_secret=lambda: "secret",
            urlsafe_b64decode=_urlsafe_b64decode,
        )

        self.assertEqual(decoded, {"auth_user_id": "user-1", "authorized": True})

    def test_decode_signed_payload_rejects_invalid_signature(self) -> None:
        signed = encode_signed_payload(
            {"auth_user_id": "user-1"},
            session_secret=lambda: "secret",
            urlsafe_b64encode=_urlsafe_b64encode,
        )

        with self.assertRaisesRegex(ValueError, "Invalid auth session signature"):
            decode_signed_payload(
                signed[:-1] + ("0" if signed[-1] != "0" else "1"),
                session_secret=lambda: "secret",
                urlsafe_b64decode=_urlsafe_b64decode,
            )

    def test_invalid_access_token_uses_default(self) -> None:
        self.assertEqual(
            read_access_token_expires_in(
                "bad-token",
                urlsafe_b64decode=_urlsafe_b64decode,
            ),
            3600,
        )

    def test_read_access_token_expires_in_uses_jwt_exp_with_minimum_floor(self) -> None:
        payload = _urlsafe_b64encode(json.dumps({"exp": 1030}).encode("utf-8"))

        with mock.patch("backend.services.auth_session_cookie_backend.time.time", return_value=1000):
            expires_in = read_access_token_expires_in(
                f"header.{payload}.signature",
                urlsafe_b64decode=_urlsafe_b64decode,
            )

        self.assertEqual(expires_in, 60)
