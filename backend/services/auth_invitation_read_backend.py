from __future__ import annotations

import time
from typing import Any


def list_pending_invitations_by_email(
    *,
    email: str,
    normalize_email: Any,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    normalize_invitation_row: Any,
    auth_error_cls: type[Exception],
) -> list[dict[str, Any]]:
    normalized_email = normalize_email(email)
    if not normalized_email:
        return []
    rows, _headers = request_json(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="GET",
        path="/invitations",
        query=[
            (
                "select",
                "id,organization_id,email,role,display_name,team_name,job_title,invite_token,status,"
                "expires_at,accepted_at,revoked_at,accepted_user_id,created_by,created_at,updated_at",
            ),
            ("email", f"eq.{normalized_email}"),
            ("status", "eq.pending"),
            ("order", "created_at.desc"),
            ("limit", "3"),
        ],
        error_cls=auth_error_cls,
    )
    if not isinstance(rows, list):
        return []
    return [normalize_invitation_row(dict(item)) for item in rows]


def list_invitations(
    *,
    organization_id: str,
    include_non_pending: bool = True,
    expire_stale_invitations: Any,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    normalize_invitation_row: Any,
    auth_error_cls: type[Exception],
) -> list[dict[str, Any]]:
    expire_stale_invitations(organization_id=organization_id)
    query: list[tuple[str, str]] = [
        (
            "select",
            "id,organization_id,email,role,display_name,team_name,job_title,invite_token,status,"
            "expires_at,accepted_at,revoked_at,accepted_user_id,created_by,created_at,updated_at",
        ),
        ("organization_id", f"eq.{organization_id}"),
        ("order", "created_at.desc"),
    ]
    if not include_non_pending:
        query.append(("status", "eq.pending"))
    rows, _headers = request_json(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="GET",
        path="/invitations",
        query=query,
        error_cls=auth_error_cls,
    )
    if not isinstance(rows, list):
        return []
    return [normalize_invitation_row(dict(item)) for item in rows]


def get_invitation_preview(
    *,
    invite_token: str,
    get_invitation_by_token: Any,
    get_organization: Any,
    build_invitation_initial_password: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    invitation = get_invitation_by_token(invite_token)
    if invitation is None:
        raise auth_error_cls("invitation not found", status_code=404, code="invite_not_found")
    organization = get_organization(str(invitation.get("organization_id") or ""))
    preview = dict(invitation)
    preview["organization_name"] = str(organization.get("name") or "") if organization else ""
    if str(preview.get("status") or "") == "pending":
        preview["initial_password"] = build_invitation_initial_password(str(preview.get("invite_token") or ""))
    return preview


def get_invitation_preview_by_email(
    *,
    email: str,
    list_pending_invitations_by_email: Any,
    get_organization: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    pending = list_pending_invitations_by_email(email=email)
    if not pending:
        raise auth_error_cls("invitation not found", status_code=404, code="invite_not_found")
    if len(pending) > 1:
        raise auth_error_cls("multiple pending invitations found for this account", status_code=409, code="invite_ambiguous")
    invitation = dict(pending[0])
    organization = get_organization(str(invitation.get("organization_id") or ""))
    preview = dict(invitation)
    preview["organization_name"] = str(organization.get("name") or "") if organization else ""
    return preview


def get_invitation_by_token(
    invite_token: str,
    *,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    normalize_invitation_row: Any,
    persist_invitation_status: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any] | None:
    normalized_token = str(invite_token or "").strip()
    if not normalized_token:
        return None
    rows, _headers = request_json(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="GET",
        path="/invitations",
        query=[
            (
                "select",
                "id,organization_id,email,role,display_name,team_name,job_title,invite_token,status,"
                "expires_at,accepted_at,revoked_at,accepted_user_id,created_by,created_at,updated_at",
            ),
            ("invite_token", f"eq.{normalized_token}"),
            ("limit", "1"),
        ],
        error_cls=auth_error_cls,
    )
    if not isinstance(rows, list) or not rows:
        return None
    raw = dict(rows[0])
    item = normalize_invitation_row(raw)
    if str(raw.get("status") or "").strip().lower() == "pending" and str(item.get("status") or "") == "expired":
        invitation_id = str(item.get("id") or "").strip()
        if invitation_id:
            persist_invitation_status(invitation_id=invitation_id, status="expired")
    return item


def get_invitation_by_id(
    *,
    organization_id: str,
    invitation_id: str,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    normalize_invitation_row: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any] | None:
    normalized_invitation_id = str(invitation_id or "").strip()
    normalized_organization_id = str(organization_id or "").strip()
    if not normalized_invitation_id or not normalized_organization_id:
        return None
    rows, _headers = request_json(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="GET",
        path="/invitations",
        query=[
            (
                "select",
                "id,organization_id,email,role,display_name,team_name,job_title,invite_token,status,expires_at,"
                "accepted_at,revoked_at,accepted_user_id,created_by,created_at,updated_at",
            ),
            ("id", f"eq.{normalized_invitation_id}"),
            ("organization_id", f"eq.{normalized_organization_id}"),
            ("limit", "1"),
        ],
        error_cls=auth_error_cls,
    )
    if not isinstance(rows, list) or not rows:
        return None
    return normalize_invitation_row(dict(rows[0]))


def normalize_invitation_row(
    row: dict[str, Any],
    *,
    normalize_email: Any,
    normalize_org_role: Any,
) -> dict[str, Any]:
    item = dict(row)
    item["email"] = normalize_email(item.get("email"))
    item["role"] = normalize_org_role(item.get("role"))
    status = str(item.get("status") or "pending").strip().lower()
    if status not in {"pending", "accepted", "expired", "revoked"}:
        status = "pending"
    if status == "pending":
        expires_at = str(item.get("expires_at") or "").strip()
        if expires_at:
            try:
                if expires_at.endswith("Z"):
                    expires_dt = time.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ")
                    if time.mktime(expires_dt) < time.time():
                        status = "expired"
            except ValueError:
                pass
    item["status"] = status
    item.setdefault("invite_url", "")
    item.setdefault("delivery_status", "")
    item.setdefault("delivery_message", "")
    return item
