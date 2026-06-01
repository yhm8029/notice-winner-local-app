from __future__ import annotations

from typing import Any


def create_platform_admin_account(
    *,
    actor_user_id: str,
    actor_role: str,
    organization_id: str,
    email: str,
    password: str,
    display_name: str,
    role: str,
    create_auth_user_fn: Any,
    get_user_profile_fn: Any,
    list_local_users_fn: Any,
    ensure_user_profile_fn: Any,
    ensure_membership_fn: Any,
    append_audit_log_fn: Any,
    cleanup_local_account_fn: Any,
    delete_auth_user_fn: Any,
    warn_fn: Any,
    normalize_email_fn: Any,
    normalize_org_role_fn: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any]:
    if str(actor_role or "").strip().lower() != "platform_admin":
        raise auth_error_cls("platform admin only", status_code=403, code="auth_forbidden")

    normalized_email = normalize_email_fn(email)
    normalized_display_name = str(display_name or "").strip()
    if not normalized_email or not str(password or "").strip():
        raise auth_error_cls("email and password are required", status_code=400, code="validation_error")

    existing_profile = get_user_profile_fn(email=normalized_email)
    if existing_profile is not None:
        raise auth_error_cls("account already exists", status_code=409, code="auth_user_exists")

    existing_users = list_local_users_fn(organization_id=organization_id, include_inactive=True)
    if any(str(item.get("email") or "").strip().lower() == normalized_email for item in existing_users):
        raise auth_error_cls("account already exists", status_code=409, code="auth_user_exists")

    created_auth_user = create_auth_user_fn(
        email=normalized_email,
        password=password,
        display_name=normalized_display_name,
    )
    user_id = str((created_auth_user or {}).get("id") or "").strip()
    if not user_id:
        raise auth_error_cls("failed to create auth user", status_code=500, code="auth_create_failed")

    normalized_role = normalize_org_role_fn(role)
    try:
        ensure_user_profile_fn(
            user_id=user_id,
            email=normalized_email,
            display_name=normalized_display_name,
            account_status="active",
            global_role="",
            created_by_user_id=actor_user_id,
            password_setup_mode="admin_set",
            force_password_change=False,
        )
        ensure_membership_fn(
            organization_id=organization_id,
            user_id=user_id,
            role=normalized_role,
            membership_status="active",
        )
    except Exception as write_exc:
        cleanup_failures: list[str] = []
        try:
            delete_auth_user_fn(auth_user_id=user_id)
        except Exception as exc:
            cleanup_failures.append(f"delete_auth_user_fn failed: {exc}")
        try:
            cleanup_local_account_fn(
                organization_id=organization_id,
                user_id=user_id,
                email=normalized_email,
            )
        except Exception as exc:
            cleanup_failures.append(f"cleanup_local_account_fn failed: {exc}")
        if cleanup_failures:
            cleanup_message = "; ".join(cleanup_failures)
            raise auth_error_cls(
                f"account creation failed and rollback cleanup failed: {cleanup_message}",
                status_code=500,
                code="auth_create_cleanup_failed",
            ) from write_exc
        raise
    try:
        append_audit_log_fn(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            event_type="account_created",
            target_type="user_profile",
            target_id=user_id,
            payload={"email": normalized_email, "role": normalized_role},
        )
    except Exception:
        try:
            warn_fn(
                "account_created audit log failed "
                f"(organization_id={organization_id}, user_id={user_id}, email={normalized_email})"
            )
        except Exception:
            pass
    return {
        "id": user_id,
        "email": normalized_email,
        "display_name": normalized_display_name,
        "role": normalized_role,
        "account_status": "active",
        "membership_status": "active",
        "password_setup_mode": "admin_set",
        "force_password_change": False,
    }
