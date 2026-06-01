from __future__ import annotations

from typing import Any


def counts_towards_active_user_limit(
    *,
    item: dict[str, Any],
    normalize_global_role: Any,
    normalize_account_status: Any,
    normalize_membership_status: Any,
) -> bool:
    if normalize_global_role(item.get("global_role")) == "platform_admin":
        return False
    return (
        normalize_account_status(item.get("account_status")) == "active"
        and normalize_membership_status(item.get("membership_status") or item.get("status")) == "active"
    )


def build_plan_upgrade_message(
    *,
    plan_code: str,
    active_user_limit: int,
    pending_invite_limit: int,
    active_user_limit_reached: bool,
    pending_invite_limit_reached: bool,
    resolve_next_plan_code: Any,
    organization_plan_limits: dict[str, dict[str, int]],
) -> str:
    if not active_user_limit_reached and not pending_invite_limit_reached:
        return ""
    if active_user_limit_reached and pending_invite_limit_reached:
        reason = (
            f"?꾩옱 ?뚮옖 {plan_code}??媛???ъ슜???쒕룄({active_user_limit}紐?? "
            f"?湲?以?珥덈? ?쒕룄({pending_invite_limit}嫄???紐⑤몢 ?꾨떖?덉뒿?덈떎."
        )
    elif active_user_limit_reached:
        reason = f"?꾩옱 ?뚮옖 {plan_code}??媛???ъ슜???쒕룄({active_user_limit}紐????꾨떖?덉뒿?덈떎."
    else:
        reason = f"?꾩옱 ?뚮옖 {plan_code}???湲?以?珥덈? ?쒕룄({pending_invite_limit}嫄????꾨떖?덉뒿?덈떎."

    next_plan_code = resolve_next_plan_code(plan_code)
    if not next_plan_code:
        return f"{reason} ?꾩옱 理쒖긽???뚮옖?대?濡??쒕룄 利앹꽕???꾩슂?섎㈃ ?댁쁺?먯뿉寃?臾몄쓽?섏꽭??"

    next_plan_limits = organization_plan_limits[next_plan_code]
    return (
        f"{reason} ?뚮옖 {next_plan_code}濡??낃렇?덉씠?쒗븯硫?"
        f"媛???ъ슜??{next_plan_limits['active_user_limit']}紐? "
        f"?湲?以?珥덈? {next_plan_limits['pending_invite_limit']}嫄닿퉴吏 ?ъ슜?????덉뒿?덈떎."
    )


def build_organization_plan_summary(
    *,
    organization: dict[str, Any],
    members: list[dict[str, Any]],
    pending_invitations: list[dict[str, Any]],
    normalize_plan_code: Any,
    normalize_limit_value: Any,
    counts_towards_active_user_limit: Any,
    build_plan_upgrade_message: Any,
    resolve_next_plan_code: Any,
    organization_plan_limits: dict[str, dict[str, int]],
) -> dict[str, Any]:
    plan_code = normalize_plan_code(organization.get("plan_code"))
    active_user_limit = normalize_limit_value(
        organization.get("active_user_limit"),
        default=organization_plan_limits[plan_code]["active_user_limit"],
        minimum=1,
    )
    pending_invite_limit = normalize_limit_value(
        organization.get("pending_invite_limit"),
        default=organization_plan_limits[plan_code]["pending_invite_limit"],
        minimum=0,
    )
    active_user_count = sum(1 for item in members if counts_towards_active_user_limit(item=item))
    pending_invite_count = sum(1 for item in pending_invitations if str(item.get("status") or "pending") == "pending")
    active_user_limit_reached = active_user_count >= active_user_limit
    pending_invite_limit_reached = pending_invite_count >= pending_invite_limit
    upgrade_message = build_plan_upgrade_message(
        plan_code=plan_code,
        active_user_limit=active_user_limit,
        pending_invite_limit=pending_invite_limit,
        active_user_limit_reached=active_user_limit_reached,
        pending_invite_limit_reached=pending_invite_limit_reached,
    )
    return {
        "organization_id": str(organization.get("id") or ""),
        "organization_name": str(organization.get("name") or ""),
        "plan_code": plan_code,
        "plan_label": str(organization.get("plan_label") or f"?뚮옖 {plan_code}"),
        "active_user_limit": active_user_limit,
        "pending_invite_limit": pending_invite_limit,
        "active_user_count": active_user_count,
        "pending_invite_count": pending_invite_count,
        "remaining_active_user_slots": max(0, active_user_limit - active_user_count),
        "remaining_pending_invite_slots": max(0, pending_invite_limit - pending_invite_count),
        "active_user_limit_reached": active_user_limit_reached,
        "pending_invite_limit_reached": pending_invite_limit_reached,
        "upgrade_required": active_user_limit_reached or pending_invite_limit_reached,
        "upgrade_message": upgrade_message,
        "next_plan_code": resolve_next_plan_code(plan_code),
    }


def get_organization_plan_summary(
    *,
    organization_id: str,
    get_organization: Any,
    list_local_users: Any,
    list_invitations: Any,
    build_organization_plan_summary: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    organization = get_organization(organization_id)
    if organization is None:
        raise auth_error_cls("organization not found", status_code=404, code="organization_not_found")
    members = list_local_users(organization_id=organization_id, include_inactive=True)
    pending_invitations = list_invitations(organization_id=organization_id, include_non_pending=False)
    return build_organization_plan_summary(
        organization=organization,
        members=members,
        pending_invitations=pending_invitations,
    )


def get_organization_invitation_dashboard(
    *,
    organization_id: str,
    actor_role: str,
    get_organization: Any,
    list_local_users: Any,
    list_invitations: Any,
    build_organization_plan_summary: Any,
    filter_manageable_invitations: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    organization = get_organization(organization_id)
    if organization is None:
        raise auth_error_cls("organization not found", status_code=404, code="organization_not_found")
    members = list_local_users(organization_id=organization_id, include_inactive=True)
    pending_invitations = list_invitations(organization_id=organization_id, include_non_pending=False)
    plan_summary = build_organization_plan_summary(
        organization=organization,
        members=members,
        pending_invitations=pending_invitations,
    )
    return {
        "items": filter_manageable_invitations(actor_role=actor_role, invitations=pending_invitations),
        "plan_summary": plan_summary,
    }


def ensure_invitation_capacity(
    *,
    organization_id: str,
    get_organization_plan_summary: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    summary = get_organization_plan_summary(organization_id=organization_id)
    if summary.get("upgrade_required"):
        raise auth_error_cls(
            str(summary.get("upgrade_message") or "?꾩옱 ?뚮옖 ?쒕룄???꾨떖?덉뒿?덈떎."),
            status_code=409,
            code="invite_limit_reached",
        )
    return summary


def ensure_acceptance_capacity(
    *,
    organization_id: str,
    auth_user_id: str,
    email: str,
    get_user_profile: Any,
    get_membership_row: Any,
    counts_towards_active_user_limit: Any,
    get_organization_plan_summary: Any,
    normalize_global_role: Any,
    auth_error_cls: type[Exception],
) -> None:
    profile = get_user_profile(user_id=auth_user_id, email=email)
    if profile is not None and normalize_global_role(profile.get("global_role")) == "platform_admin":
        return

    existing_membership = get_membership_row(organization_id=organization_id, user_id=auth_user_id)
    if existing_membership is not None and counts_towards_active_user_limit(item=existing_membership):
        return

    summary = get_organization_plan_summary(organization_id=organization_id)
    if summary.get("active_user_limit_reached"):
        raise auth_error_cls(
            str(summary.get("upgrade_message") or "?꾩옱 ?뚮옖??媛??媛???ъ슜???쒕룄???꾨떖?덉뒿?덈떎."),
            status_code=409,
            code="invite_limit_reached",
        )
