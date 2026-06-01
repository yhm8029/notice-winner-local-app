from __future__ import annotations

from typing import Any


def build_application_profile(
    *,
    auth_user: dict[str, Any],
    email: str,
    display_name: str,
    bootstrap_platform_admin_email_fn,
    ensure_bootstrap_local_user_fn,
    get_local_user_fn,
    get_user_profile_fn,
    normalize_local_user_status_fn,
    normalize_account_status_fn,
    normalize_membership_status_fn,
    default_bootstrap_org_name: str,
) -> dict[str, Any]:
    auth_user_id = str(auth_user.get("id") or "").strip()
    bootstrap_email = bootstrap_platform_admin_email_fn()
    if bootstrap_email and email == bootstrap_email:
        local_user = ensure_bootstrap_local_user_fn(
            auth_user_id=auth_user_id,
            email=email,
            display_name=display_name,
        )
        return {
            "authorized": True,
            "role": "platform_admin",
            "organization_id": str(local_user.get("organization_id") or ""),
            "organization_name": str(local_user.get("organization_name") or default_bootstrap_org_name),
            "local_user_id": str(local_user.get("id") or ""),
            "membership_id": str(local_user.get("membership_id") or ""),
            "message": "",
            "status": normalize_local_user_status_fn(local_user.get("status")),
            "account_status": normalize_account_status_fn(local_user.get("account_status")),
            "membership_status": normalize_membership_status_fn(local_user.get("membership_status")),
            "mobile_phone": str(local_user.get("mobile_phone") or ""),
            "office_phone": str(local_user.get("office_phone") or ""),
        }

    local_user = get_local_user_fn(user_id=auth_user_id)
    if local_user is None:
        profile = get_user_profile_fn(user_id=auth_user_id, email=email)
        account_status = normalize_account_status_fn(profile.get("account_status")) if profile else "inactive"
        return {
            "authorized": False,
            "role": "unauthorized",
            "organization_id": None,
            "organization_name": "",
            "local_user_id": str(profile.get("id") or "") if profile else None,
            "membership_id": None,
            "message": "This account is authenticated but not invited to any organization.",
            "status": account_status,
            "account_status": account_status,
            "membership_status": "inactive",
            "mobile_phone": str(profile.get("mobile_phone") or "") if profile else "",
            "office_phone": str(profile.get("office_phone") or "") if profile else "",
        }

    account_status = normalize_account_status_fn(local_user.get("account_status"))
    membership_status = normalize_membership_status_fn(local_user.get("membership_status"))
    local_status = normalize_local_user_status_fn(local_user.get("status"))
    if local_status != "active":
        return {
            "authorized": False,
            "role": str(local_user.get("role") or "org_member"),
            "organization_id": str(local_user.get("organization_id") or ""),
            "organization_name": str(local_user.get("organization_name") or ""),
            "local_user_id": str(local_user.get("id") or ""),
            "membership_id": str(local_user.get("membership_id") or ""),
            "message": "계정이 비활성화되었습니다.",
            "status": local_status,
            "account_status": account_status,
            "membership_status": membership_status,
            "mobile_phone": str(local_user.get("mobile_phone") or ""),
            "office_phone": str(local_user.get("office_phone") or ""),
        }

    return {
        "authorized": True,
        "role": str(local_user.get("role") or "org_member"),
        "organization_id": str(local_user.get("organization_id") or ""),
        "organization_name": str(local_user.get("organization_name") or ""),
        "local_user_id": str(local_user.get("id") or ""),
        "membership_id": str(local_user.get("membership_id") or ""),
        "message": "",
        "status": local_status,
        "account_status": account_status,
        "membership_status": membership_status,
        "mobile_phone": str(local_user.get("mobile_phone") or ""),
        "office_phone": str(local_user.get("office_phone") or ""),
    }


def ensure_bootstrap_local_user(
    *,
    auth_user_id: str,
    email: str,
    display_name: str,
    rest_upsert_fn,
    ensure_user_profile_fn,
    ensure_membership_fn,
    sync_legacy_user_projection_fn,
    get_local_user_fn,
    default_phase1_organization_id,
    default_bootstrap_org_name: str,
    default_bootstrap_org_slug: str,
    error_cls,
) -> dict[str, Any]:
    if not auth_user_id:
        raise error_cls("Supabase auth user id is required", status_code=500, code="auth_invalid")

    resolved_display_name = display_name or email.split("@", 1)[0]
    organization_id = str(default_phase1_organization_id)
    rest_upsert_fn(
        "organizations",
        {
            "id": organization_id,
            "name": default_bootstrap_org_name,
            "slug": default_bootstrap_org_slug,
        },
        on_conflict="id",
    )
    ensure_user_profile_fn(
        user_id=auth_user_id,
        email=email,
        display_name=resolved_display_name,
        account_status="active",
        global_role="platform_admin",
    )
    ensure_membership_fn(
        organization_id=organization_id,
        user_id=auth_user_id,
        role="org_admin",
        membership_status="active",
    )
    sync_legacy_user_projection_fn(
        user_id=auth_user_id,
        organization_id=organization_id,
        email=email,
        display_name=resolved_display_name,
        membership_role="org_admin",
        membership_status="active",
    )
    local_user = get_local_user_fn(user_id=auth_user_id, organization_id=organization_id)
    if local_user is None:
        raise error_cls("Failed to create bootstrap application user", status_code=500, code="bootstrap_failed")
    return local_user


def ensure_member_local_user(
    *,
    auth_user_id: str,
    email: str,
    display_name: str,
    ensure_user_profile_fn,
    get_user_profile_fn,
    error_cls,
) -> dict[str, Any]:
    if not auth_user_id:
        raise error_cls("Supabase auth user id is required", status_code=500, code="auth_invalid")

    ensure_user_profile_fn(
        user_id=auth_user_id,
        email=email,
        display_name=display_name or email.split("@", 1)[0],
        account_status="active",
    )
    profile = get_user_profile_fn(user_id=auth_user_id, email=email)
    if profile is None:
        raise error_cls("Failed to create application profile", status_code=500, code="bootstrap_failed")
    return profile
