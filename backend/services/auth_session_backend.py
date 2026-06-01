from __future__ import annotations

from typing import Any


def build_session_response_payload(
    *,
    session_payload: dict[str, Any],
    build_auth_status_response_fn: Any,
) -> dict[str, Any]:
    response = build_auth_status_response_fn()
    response.update(
        {
            "enabled": True,
            "authenticated": True,
            "authorized": bool(session_payload.get("authorized")),
            "access_token": str(session_payload.get("access_token") or ""),
            "message": str(session_payload.get("message") or ""),
            "user": _build_session_user_payload(session_payload),
        }
    )
    return response


def _build_session_user_payload(session_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "auth_user_id": session_payload.get("auth_user_id"),
        "local_user_id": session_payload.get("local_user_id"),
        "membership_id": session_payload.get("membership_id"),
        "email": session_payload.get("email"),
        "display_name": session_payload.get("display_name"),
        "role": session_payload.get("role"),
        "status": session_payload.get("status") or "active",
        "account_status": session_payload.get("account_status") or "active",
        "membership_status": session_payload.get("membership_status") or "active",
        "mobile_phone": session_payload.get("mobile_phone") or "",
        "office_phone": session_payload.get("office_phone") or "",
        "organization_id": session_payload.get("organization_id"),
        "organization_name": session_payload.get("organization_name"),
    }
