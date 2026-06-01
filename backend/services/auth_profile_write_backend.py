from __future__ import annotations

from typing import Any


def update_local_user_profile(
    *,
    user_id: str,
    email: str,
    display_name: str,
    mobile_phone: str = "",
    office_phone: str = "",
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    auth_error_cls: type[Exception],
    is_missing_relation_error_fn: Any,
    get_local_user_fn: Any,
    sync_legacy_user_projection_fn: Any,
    get_user_profile_fn: Any,
    default_phase1_org_id: str,
) -> dict[str, Any]:
    normalized_display_name = str(display_name or "").strip()
    if not user_id:
        raise auth_error_cls("user_id is required", status_code=400, code="validation_error")
    if not normalized_display_name:
        raise auth_error_cls("display_name is required", status_code=400, code="validation_error")
    profile_payload = {
        "display_name": normalized_display_name,
        "mobile_phone": str(mobile_phone or "").strip(),
        "office_phone": str(office_phone or "").strip(),
    }
    try:
        rows, _headers = request_json_fn(
            rest_url=rest_base_url(),
            api_key=service_api_key(),
            timeout_seconds=timeout_seconds(),
            method="PATCH",
            path="/user_profiles",
            query=[
                ("id", f"eq.{user_id}"),
                ("email", f"eq.{email}"),
            ],
            headers={"Prefer": "return=representation"},
            payload=profile_payload,
            error_cls=auth_error_cls,
        )
    except auth_error_cls as exc:
        if is_missing_relation_error_fn(exc.message, "user_profiles"):
            rows, _headers = request_json_fn(
                rest_url=rest_base_url(),
                api_key=service_api_key(),
                timeout_seconds=timeout_seconds(),
                method="PATCH",
                path="/users",
                query=[
                    ("id", f"eq.{user_id}"),
                    ("email", f"eq.{email}"),
                ],
                headers={"Prefer": "return=representation"},
                payload={"display_name": normalized_display_name},
                error_cls=auth_error_cls,
            )
        else:
            raise
    if not isinstance(rows, list) or not rows:
        raise auth_error_cls("application user not found", status_code=404, code="user_not_found")
    current = get_local_user_fn(user_id=user_id, email=email)
    if current is not None:
        sync_legacy_user_projection_fn(
            user_id=user_id,
            organization_id=str(current.get("organization_id") or default_phase1_org_id),
            email=email,
            display_name=normalized_display_name,
            membership_role=str(current.get("role") or "org_member"),
            membership_status=str(current.get("membership_status") or current.get("status") or "active"),
        )
    profile = get_user_profile_fn(user_id=user_id, email=email)
    if profile is None:
        raise auth_error_cls("application profile not found", status_code=404, code="user_not_found")
    return profile


def ensure_user_profile(
    *,
    user_id: str,
    email: str,
    display_name: str,
    account_status: str = "active",
    global_role: str = "",
    created_by_user_id: str | None = None,
    password_setup_mode: str | None = None,
    force_password_change: bool | None = None,
    get_user_profile_fn: Any,
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    rest_upsert_fn: Any,
    normalize_account_status_fn: Any,
    normalize_global_role_fn: Any,
    is_missing_relation_error_fn: Any,
    is_missing_column_error_fn: Any,
    auth_error_cls: type[Exception],
) -> None:
    base_profile_payload = {
        "display_name": display_name,
        "account_status": normalize_account_status_fn(account_status),
        "global_role": normalize_global_role_fn(global_role),
    }
    profile_payload = dict(base_profile_payload)
    if created_by_user_id is not None:
        profile_payload["created_by_user_id"] = created_by_user_id or None
    if password_setup_mode is not None:
        profile_payload["password_setup_mode"] = str(password_setup_mode or "admin_set").strip()
    if force_password_change is not None:
        profile_payload["force_password_change"] = bool(force_password_change)

    existing = get_user_profile_fn(email=email)
    if existing is not None:
        existing_id = str(existing.get("id") or "").strip()
        if existing_id and existing_id != str(user_id):
            request_json_fn(
                rest_url=rest_base_url(),
                api_key=service_api_key(),
                timeout_seconds=timeout_seconds(),
                method="PATCH",
                path="/user_profiles",
                query=[("id", f"eq.{existing_id}")],
                headers={"Prefer": "return=minimal"},
                payload=profile_payload,
                error_cls=auth_error_cls,
            )
            return
    try:
        rest_upsert_payload = {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            **profile_payload,
        }
        rest_upsert_fn("user_profiles", rest_upsert_payload, on_conflict="id")
    except auth_error_cls as exc:
        if any(
            is_missing_column_error_fn(exc.message, column_name)
            for column_name in ("created_by_user_id", "password_setup_mode", "force_password_change")
        ):
            rest_upsert_fn(
                "user_profiles",
                {
                    "id": user_id,
                    "email": email,
                    "display_name": display_name,
                    **base_profile_payload,
                },
                on_conflict="id",
            )
            return
        if is_missing_relation_error_fn(exc.message, "user_profiles"):
            return
        raise


def ensure_membership(
    *,
    organization_id: str,
    user_id: str,
    role: str,
    membership_status: str = "active",
    team_name: str = "",
    job_title: str = "",
    rest_upsert_fn: Any,
    normalize_org_role_fn: Any,
    normalize_membership_status_fn: Any,
    is_missing_relation_error_fn: Any,
    auth_error_cls: type[Exception],
) -> None:
    try:
        rest_upsert_fn(
            "organization_memberships",
            {
                "organization_id": organization_id,
                "user_profile_id": user_id,
                "role": normalize_org_role_fn(role),
                "membership_status": normalize_membership_status_fn(membership_status),
                "team_name": str(team_name or "").strip(),
                "job_title": str(job_title or "").strip(),
            },
            on_conflict="organization_id,user_profile_id",
        )
    except auth_error_cls as exc:
        if is_missing_relation_error_fn(exc.message, "organization_memberships"):
            return
        raise


def sync_legacy_user_projection(
    *,
    user_id: str,
    organization_id: str,
    email: str,
    display_name: str,
    membership_role: str,
    membership_status: str,
    rest_upsert_fn: Any,
    map_membership_role_to_legacy_role_fn: Any,
    normalize_membership_status_fn: Any,
) -> None:
    legacy_role = map_membership_role_to_legacy_role_fn(membership_role)
    rest_upsert_fn(
        "users",
        {
            "id": user_id,
            "organization_id": organization_id,
            "email": email,
            "display_name": display_name,
            "role": legacy_role,
            "status": normalize_membership_status_fn(membership_status),
        },
        on_conflict="id",
    )
