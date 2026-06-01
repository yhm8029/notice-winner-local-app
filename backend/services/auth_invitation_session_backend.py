from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any


def require_invitation_email_match(
    *,
    invite_token: str,
    email: str,
    normalize_email_fn: Any,
    get_invitation_by_token_fn: Any,
    auth_error_cls: Any,
) -> None:
    normalized_token = str(invite_token or "").strip()
    if not normalized_token:
        return
    normalized_email = normalize_email_fn(email)
    invitation = get_invitation_by_token_fn(normalized_token)
    if invitation is None:
        raise auth_error_cls("invitation not found", status_code=404, code="invite_not_found")
    if str(invitation.get("status") or "") == "revoked":
        raise auth_error_cls("invitation has been revoked", status_code=400, code="invite_revoked")
    if str(invitation.get("status") or "") == "expired":
        raise auth_error_cls("invitation has expired", status_code=400, code="invite_expired")
    invited_email = normalize_email_fn(invitation.get("email"))
    if invited_email and invited_email != normalized_email:
        raise auth_error_cls(
            "invitation email does not match the requested email",
            status_code=403,
            code="invite_email_mismatch",
        )


def can_use_invite_password_setup(
    *,
    auth_user_id: str,
    email: str,
    invite_token: str,
    normalize_email_fn: Any,
    get_invitation_by_token_fn: Any,
    parse_datetime_value_fn: Any,
) -> bool:
    normalized_token = str(invite_token or "").strip()
    normalized_email = normalize_email_fn(email)
    if not normalized_token or not auth_user_id or not normalized_email:
        return False
    invitation = get_invitation_by_token_fn(normalized_token)
    if invitation is None:
        return False
    if normalize_email_fn(invitation.get("email")) != normalized_email:
        return False
    if str(invitation.get("status") or "") != "accepted":
        return False
    if str(invitation.get("accepted_user_id") or "").strip() != str(auth_user_id or "").strip():
        return False
    accepted_at = parse_datetime_value_fn(invitation.get("accepted_at"))
    if accepted_at is None:
        return False
    return (datetime.now(timezone.utc) - accepted_at) <= timedelta(hours=24)


def raise_accept_invitation_error(
    *,
    exc: Exception,
    invitation_id: str,
    persist_invitation_status_fn: Any,
    auth_error_cls: Any,
) -> None:
    message = str(getattr(exc, "message", "") or str(exc) or "").strip()
    normalized_message = message.lower()
    if "invitation has expired" in normalized_message:
        if invitation_id:
            try:
                persist_invitation_status_fn(invitation_id=invitation_id, status="expired")
            except Exception:
                pass
        raise auth_error_cls("invitation has expired", status_code=400, code="invite_expired") from exc
    if "invitation has been revoked" in normalized_message:
        raise auth_error_cls("invitation has been revoked", status_code=400, code="invite_revoked") from exc
    if "invitation already belongs to another account" in normalized_message:
        raise auth_error_cls(
            "invitation already belongs to another account",
            status_code=409,
            code="invite_already_claimed",
        ) from exc
    if "invitation has already been accepted" in normalized_message:
        raise auth_error_cls(
            "invitation has already been accepted",
            status_code=409,
            code="invite_already_accepted",
        ) from exc
    if "active user limit reached for this organization" in normalized_message:
        raise auth_error_cls(
            "organization active user limit reached",
            status_code=409,
            code="invite_limit_reached",
        ) from exc
    raise exc


def resolve_session_invitation_token(
    *,
    invite_token: str,
    auth_user_id: str,
    email: str,
    list_pending_invitations_by_email_fn: Any,
    auth_error_cls: Any,
) -> str:
    normalized_token = str(invite_token or "").strip()
    if normalized_token:
        return normalized_token
    pending = list_pending_invitations_by_email_fn(email=email)
    if not pending:
        raise auth_error_cls("pending invitation not found for this account", status_code=404, code="invite_not_found")
    if len(pending) > 1:
        raise auth_error_cls("multiple pending invitations found for this account", status_code=409, code="invite_ambiguous")
    invitation = dict(pending[0])
    token = str(invitation.get("invite_token") or "").strip()
    if not token:
        raise auth_error_cls("pending invitation token is missing", status_code=500, code="invite_invalid")
    accepted_user_id = str(invitation.get("accepted_user_id") or "").strip()
    if accepted_user_id and accepted_user_id != auth_user_id:
        raise auth_error_cls("invitation already belongs to another account", status_code=409, code="invite_already_claimed")
    return token


def resolve_pending_invitation_token_for_email(
    *,
    email: str,
    invite_token: str = "",
    required: bool = False,
    list_pending_invitations_by_email_fn: Any,
    auth_error_cls: Any,
) -> str:
    normalized_token = str(invite_token or "").strip()
    if normalized_token:
        return normalized_token
    pending = list_pending_invitations_by_email_fn(email=email)
    if not pending:
        if required:
            raise auth_error_cls(
                "invitation is required for this account",
                status_code=403,
                code="invite_required",
            )
        return ""
    if len(pending) > 1:
        raise auth_error_cls("multiple pending invitations found for this account", status_code=409, code="invite_ambiguous")
    invitation = dict(pending[0])
    token = str(invitation.get("invite_token") or "").strip()
    if not token:
        if required:
            raise auth_error_cls("pending invitation token is missing", status_code=500, code="invite_invalid")
        return ""
    return token
