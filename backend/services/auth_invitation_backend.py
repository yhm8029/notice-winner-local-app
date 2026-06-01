from __future__ import annotations

import secrets
import time
from datetime import datetime
from datetime import timezone
from logging import Logger
from typing import Any


def resolve_allowed_invitation_roles(actor_role: str) -> tuple[str, ...]:
    normalized_actor_role = str(actor_role or "").strip().lower()
    if normalized_actor_role == "platform_admin":
        return ("org_member", "org_admin")
    if normalized_actor_role == "org_admin":
        return ("org_member",)
    return ()


def validate_invitation_permissions(
    *,
    actor_role: str,
    role: str,
    normalize_org_role: Any,
    auth_error_cls: type[Exception],
) -> str:
    normalized_role = normalize_org_role(role)
    allowed_roles = resolve_allowed_invitation_roles(actor_role)
    if normalized_role in allowed_roles:
        return normalized_role
    raise auth_error_cls(
        "현재 권한으로는 해당 역할의 초대를 만들 수 없습니다.",
        status_code=403,
        code="invite_role_forbidden",
    )


def can_manage_invitation_role(*, actor_role: str, target_role: str) -> bool:
    normalized_target_role = str(target_role or "").strip().lower()
    return normalized_target_role in resolve_allowed_invitation_roles(actor_role)


def filter_manageable_invitations(*, actor_role: str, invitations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in invitations
        if can_manage_invitation_role(actor_role=actor_role, target_role=item.get("role"))
    ]


def raise_create_invitation_error(
    *,
    exc: Exception,
    organization_id: str,
    get_organization_plan_summary: Any,
    auth_error_cls: type[Exception],
) -> None:
    message = str(getattr(exc, "message", "") or str(exc) or "").strip()
    normalized_message = message.lower()
    if (
        "active user limit reached for this organization" in normalized_message
        or "pending invite limit reached for this organization" in normalized_message
    ):
        summary = get_organization_plan_summary(organization_id=organization_id)
        raise auth_error_cls(
            str(summary.get("upgrade_message") or "현재 플랜 한도에 도달했습니다."),
            status_code=409,
            code="invite_limit_reached",
        ) from exc
    if "organization not found" in normalized_message:
        raise auth_error_cls("organization not found", status_code=404, code="organization_not_found") from exc
    if "idx_invitations_org_email_pending" in normalized_message:
        raise auth_error_cls(
            "이미 대기 중인 초대가 있습니다.",
            status_code=409,
            code="invite_already_exists",
        ) from exc
    raise exc


def create_invitation(
    *,
    organization_id: str,
    created_by: str,
    actor_role: str,
    email: str,
    role: str,
    display_name: str = "",
    team_name: str = "",
    job_title: str = "",
    expires_in_days: int = 7,
    invite_url_base: str = "",
    send_email: bool = True,
    normalize_email: Any,
    normalize_org_role: Any,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    normalize_invitation_row: Any,
    build_invite_url: Any,
    build_invitation_initial_password: Any,
    append_audit_log: Any,
    send_invitation_email: Any,
    format_invitation_delivery_error: Any,
    get_organization_plan_summary: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise auth_error_cls("email is required", status_code=400, code="validation_error")
    normalized_role = validate_invitation_permissions(
        actor_role=actor_role,
        role=role,
        normalize_org_role=normalize_org_role,
        auth_error_cls=auth_error_cls,
    )
    clamped_days = max(1, min(int(expires_in_days or 7), 30))
    token = secrets.token_urlsafe(24)
    expires_at = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ",
        time.gmtime(time.time() + clamped_days * 24 * 60 * 60),
    )
    try:
        result, _headers = request_json(
            rest_url=rest_base_url(),
            api_key=service_api_key(),
            timeout_seconds=timeout_seconds(),
            method="POST",
            path="/rpc/create_invitation",
            payload={
                "p_organization_id": organization_id,
                "p_email": normalized_email,
                "p_role": normalized_role,
                "p_display_name": str(display_name or "").strip(),
                "p_team_name": str(team_name or "").strip(),
                "p_job_title": str(job_title or "").strip(),
                "p_invite_token": token,
                "p_expires_at": expires_at,
                "p_created_by": created_by or None,
            },
            error_cls=auth_error_cls,
        )
    except Exception as exc:
        raise_create_invitation_error(
            exc=exc,
            organization_id=organization_id,
            get_organization_plan_summary=get_organization_plan_summary,
            auth_error_cls=auth_error_cls,
        )
    created = None
    if isinstance(result, list) and result:
        created = dict(result[0])
    elif isinstance(result, dict):
        created = dict(result)
    if created is None:
        raise auth_error_cls("failed to create invitation", status_code=500, code="invite_create_failed")
    item = normalize_invitation_row(created)
    item["invite_url"] = build_invite_url(invite_url_base, item["invite_token"])
    item["initial_password"] = build_invitation_initial_password(str(item.get("invite_token") or ""))
    if not send_email:
        item["delivery_status"] = "queued"
        item["delivery_message"] = "초대 메일 발송을 시작했습니다. 도착하지 않으면 링크 복사로 직접 전달하세요."
        append_audit_log(
            organization_id=organization_id,
            actor_user_id=created_by,
            event_type="invite_created",
            target_type="invitation",
            target_id=str(item.get("id") or ""),
            payload={
                "email": normalized_email,
                "role": item.get("role"),
            },
        )
        return item
    try:
        send_invitation_email(
            email=normalized_email,
            invite_url=item["invite_url"],
            display_name=str(display_name or "").strip(),
        )
        item["delivery_status"] = "sent"
        item["delivery_message"] = "초대 메일을 발송했습니다."
    except Exception as exc:
        item["delivery_status"] = "failed"
        item["delivery_message"] = format_invitation_delivery_error(str(getattr(exc, "message", "") or exc))
    append_audit_log(
        organization_id=organization_id,
        actor_user_id=created_by,
        event_type="invite_created",
        target_type="invitation",
        target_id=str(item.get("id") or ""),
        payload={
            "email": normalized_email,
            "role": item.get("role"),
        },
    )
    return item


def revoke_invitation(
    *,
    organization_id: str,
    invitation_id: str,
    actor_user_id: str,
    actor_role: str,
    get_invitation_by_id: Any,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    normalize_invitation_row: Any,
    append_audit_log: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    invitation = get_invitation_by_id(organization_id=organization_id, invitation_id=invitation_id)
    if invitation is None:
        raise auth_error_cls("invitation not found", status_code=404, code="invite_not_found")
    if not can_manage_invitation_role(actor_role=actor_role, target_role=invitation.get("role")):
        raise auth_error_cls(
            "현재 권한으로는 해당 역할 초대를 철회할 수 없습니다.",
            status_code=403,
            code="invite_role_forbidden",
        )
    rows, _headers = request_json(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="PATCH",
        path="/invitations",
        query=[
            ("id", f"eq.{invitation_id}"),
            ("organization_id", f"eq.{organization_id}"),
        ],
        headers={"Prefer": "return=representation"},
        payload={
            "status": "revoked",
            "revoked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        error_cls=auth_error_cls,
    )
    if not isinstance(rows, list) or not rows:
        raise auth_error_cls("invitation not found", status_code=404, code="invite_not_found")
    item = normalize_invitation_row(dict(rows[0]))
    append_audit_log(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        event_type="invite_revoked",
        target_type="invitation",
        target_id=invitation_id,
        payload={"email": item.get("email", "")},
    )
    return item


def deliver_invitation_email(
    *,
    email: str,
    invite_url: str,
    display_name: str = "",
    invitation_email_delivery_enabled: Any,
    send_invitation_email: Any,
    normalize_email: Any,
    logger: Logger,
) -> None:
    if not invitation_email_delivery_enabled():
        return
    try:
        send_invitation_email(
            email=email,
            invite_url=invite_url,
            display_name=display_name,
        )
    except Exception as exc:
        logger.warning(
            "invitation email delivery failed for %s: %s",
            normalize_email(email),
            str(getattr(exc, "message", "") or exc),
        )


def expire_stale_invitations(
    *,
    organization_id: str,
    email: str = "",
    normalize_email: Any,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    parse_datetime_value: Any,
    persist_invitation_status_fn: Any,
    auth_error_cls: type[Exception],
) -> None:
    query: list[tuple[str, str]] = [
        ("select", "id,status,expires_at"),
        ("organization_id", f"eq.{organization_id}"),
        ("status", "eq.pending"),
        ("limit", "100"),
    ]
    normalized_email = normalize_email(email)
    if normalized_email:
        query.append(("email", f"eq.{normalized_email}"))
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
        return
    for row in rows:
        invitation_id = str(row.get("id") or "").strip()
        expires_at = parse_datetime_value(row.get("expires_at"))
        if not invitation_id or expires_at is None:
            continue
        if expires_at <= datetime.now(timezone.utc):
            persist_invitation_status_fn(invitation_id=invitation_id, status="expired")


def persist_invitation_status(
    *,
    invitation_id: str,
    status: str,
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    auth_error_cls: type[Exception],
) -> None:
    request_json(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="PATCH",
        path="/invitations",
        query=[("id", f"eq.{invitation_id}")],
        headers={"Prefer": "return=minimal"},
        payload={"status": status},
        error_cls=auth_error_cls,
    )
