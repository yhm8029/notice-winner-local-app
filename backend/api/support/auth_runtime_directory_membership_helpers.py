from __future__ import annotations

from typing import Any


def update_local_user_status(
    *,
    organization_id: str,
    user_id: str,
    status: str,
    normalize_requested_membership_status_fn,
    get_membership_row_fn,
    request_json_fn,
    rest_base_url_fn,
    service_api_key_fn,
    timeout_seconds_fn,
    sync_legacy_user_projection_fn,
    get_local_user_fn,
    error_cls,
) -> dict[str, Any]:
    normalized_status = normalize_requested_membership_status_fn(status)
    if not organization_id or not user_id:
        raise error_cls("organization_id and user_id are required", status_code=400, code="validation_error")

    membership = get_membership_row_fn(organization_id=organization_id, user_id=user_id)
    if membership is None:
        raise error_cls("application user not found", status_code=404, code="user_not_found")

    membership_id = str(membership.get("membership_id") or "").strip()
    if not membership_id:
        raise error_cls("membership id is missing", status_code=500, code="membership_invalid")

    rows, _headers = request_json_fn(
        rest_url=rest_base_url_fn(),
        api_key=service_api_key_fn(),
        timeout_seconds=timeout_seconds_fn(),
        method="PATCH",
        path="/organization_memberships",
        query=[("id", f"eq.{membership_id}")],
        headers={"Prefer": "return=representation"},
        payload={"membership_status": normalized_status},
        error_cls=error_cls,
    )
    if not isinstance(rows, list) or not rows:
        raise error_cls("organization membership not found", status_code=404, code="membership_not_found")

    sync_legacy_user_projection_fn(
        user_id=user_id,
        organization_id=organization_id,
        email=str(membership.get("email") or ""),
        display_name=str(membership.get("display_name") or ""),
        membership_role=str(membership.get("role") or membership.get("membership_role") or "org_member"),
        membership_status=normalized_status,
    )

    refreshed = get_local_user_fn(user_id=user_id, organization_id=organization_id)
    if refreshed is None:
        raise error_cls("application user not found", status_code=404, code="user_not_found")
    return refreshed


def update_organization_membership(
    *,
    organization_id: str,
    user_id: str,
    role: str = "",
    membership_status: str = "",
    team_name: str = "",
    job_title: str = "",
    actor_user_id: str = "",
    get_membership_row_fn,
    normalize_org_role_fn,
    normalize_requested_membership_status_fn,
    request_json_fn,
    rest_base_url_fn,
    service_api_key_fn,
    timeout_seconds_fn,
    get_local_user_fn,
    sync_legacy_user_projection_fn,
    append_audit_log_fn,
    error_cls,
) -> dict[str, Any]:
    current = get_membership_row_fn(organization_id=organization_id, user_id=user_id)
    if current is None:
        raise error_cls("application user not found", status_code=404, code="user_not_found")

    payload: dict[str, Any] = {}
    if role:
        payload["role"] = normalize_org_role_fn(role)
    if membership_status:
        payload["membership_status"] = normalize_requested_membership_status_fn(membership_status)
    if team_name is not None:
        payload["team_name"] = str(team_name or "").strip()
    if job_title is not None:
        payload["job_title"] = str(job_title or "").strip()
    if not payload:
        return current

    rows, _headers = request_json_fn(
        rest_url=rest_base_url_fn(),
        api_key=service_api_key_fn(),
        timeout_seconds=timeout_seconds_fn(),
        method="PATCH",
        path="/organization_memberships",
        query=[("id", f"eq.{current.get('membership_id')}")],
        headers={"Prefer": "return=representation"},
        payload=payload,
        error_cls=error_cls,
    )
    if not isinstance(rows, list) or not rows:
        raise error_cls("organization membership not found", status_code=404, code="membership_not_found")

    refreshed = get_local_user_fn(user_id=user_id, organization_id=organization_id)
    if refreshed is None:
        raise error_cls("application user not found", status_code=404, code="user_not_found")

    sync_legacy_user_projection_fn(
        user_id=user_id,
        organization_id=organization_id,
        email=str(refreshed.get("email") or ""),
        display_name=str(refreshed.get("display_name") or ""),
        membership_role=str(refreshed.get("role") or "org_member"),
        membership_status=str(refreshed.get("membership_status") or refreshed.get("status") or "active"),
    )

    membership_id = str(refreshed.get("membership_id") or "")
    if role and str(current.get("role") or "") != str(refreshed.get("role") or ""):
        append_audit_log_fn(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_membership_id=membership_id,
            event_type="membership_role_changed",
            target_type="membership",
            target_id=membership_id,
            payload={"before_role": current.get("role"), "after_role": refreshed.get("role")},
        )
    if membership_status and str(current.get("membership_status") or "active") != str(refreshed.get("membership_status") or "active"):
        append_audit_log_fn(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            actor_membership_id=membership_id,
            event_type="membership_deactivated"
            if str(refreshed.get("membership_status") or "") != "active"
            else "membership_reactivated",
            target_type="membership",
            target_id=membership_id,
            payload={
                "before_status": current.get("membership_status"),
                "after_status": refreshed.get("membership_status"),
            },
        )
    return refreshed


def delete_local_user_account(
    *,
    organization_id: str,
    user_id: str,
    get_local_user_fn,
    normalize_email_fn,
    get_user_profile_fn,
    rest_delete_rows_fn,
    delete_supabase_auth_user_fn,
    error_cls,
) -> dict[str, Any]:
    if not organization_id or not user_id:
        raise error_cls("organization_id and user_id are required", status_code=400, code="validation_error")

    current = get_local_user_fn(user_id=user_id, organization_id=organization_id)
    if current is None:
        raise error_cls("application user not found", status_code=404, code="user_not_found")

    _delete_local_account_rows(
        organization_id=organization_id,
        user_id=user_id,
        email=str(current.get("email") or ""),
        current=current,
        normalize_email_fn=normalize_email_fn,
        get_user_profile_fn=get_user_profile_fn,
        rest_delete_rows_fn=rest_delete_rows_fn,
    )
    delete_supabase_auth_user_fn(auth_user_id=user_id)
    return current


def cleanup_local_account(
    *,
    organization_id: str,
    user_id: str,
    email: str,
    get_local_user_fn,
    normalize_email_fn,
    get_user_profile_fn,
    rest_delete_rows_fn,
) -> None:
    current = get_local_user_fn(user_id=user_id, organization_id=organization_id)
    if current is None:
        return

    _delete_local_account_rows(
        organization_id=organization_id,
        user_id=user_id,
        email=email or str(current.get("email") or ""),
        current=current,
        normalize_email_fn=normalize_email_fn,
        get_user_profile_fn=get_user_profile_fn,
        rest_delete_rows_fn=rest_delete_rows_fn,
    )


def _delete_local_account_rows(
    *,
    organization_id: str,
    user_id: str,
    email: str,
    current: dict[str, Any],
    normalize_email_fn,
    get_user_profile_fn,
    rest_delete_rows_fn,
) -> None:
    normalized_email = normalize_email_fn(email)
    profile = get_user_profile_fn(user_id=user_id, email=normalized_email)
    profile_id = str((profile or {}).get("id") or user_id).strip()
    membership_id = str(current.get("membership_id") or "").strip()

    for path, query in (
        ("project_sales_claims", [("organization_id", f"eq.{organization_id}"), ("owner_user_id", f"eq.{user_id}")]),
        ("project_sales_claim_events", [("organization_id", f"eq.{organization_id}"), ("actor_user_id", f"eq.{user_id}")]),
        ("saved_run_presets", [("organization_id", f"eq.{organization_id}"), ("created_by", f"eq.{user_id}")]),
        ("pipeline_runs", [("organization_id", f"eq.{organization_id}"), ("requested_by", f"eq.{user_id}")]),
        ("tracker_entry_audit_logs", [("organization_id", f"eq.{organization_id}"), ("actor_user_id", f"eq.{user_id}")]),
        ("audit_logs", [("organization_id", f"eq.{organization_id}"), ("actor_user_id", f"eq.{profile_id}")]),
    ):
        rest_delete_rows_fn(path, query)

    if membership_id:
        rest_delete_rows_fn(
            "audit_logs",
            [("organization_id", f"eq.{organization_id}"), ("actor_membership_id", f"eq.{membership_id}")],
        )
    if normalized_email:
        rest_delete_rows_fn(
            "invitations",
            [("organization_id", f"eq.{organization_id}"), ("email", f"eq.{normalized_email}")],
        )
    if profile_id:
        for path, query in (
            ("invitations", [("organization_id", f"eq.{organization_id}"), ("created_by", f"eq.{profile_id}")]),
            ("invitations", [("organization_id", f"eq.{organization_id}"), ("accepted_user_id", f"eq.{profile_id}")]),
            ("organization_memberships", [("organization_id", f"eq.{organization_id}"), ("user_profile_id", f"eq.{profile_id}")]),
            ("user_profiles", [("id", f"eq.{profile_id}")]),
        ):
            rest_delete_rows_fn(path, query)

    rest_delete_rows_fn(
        "users",
        [("organization_id", f"eq.{organization_id}"), ("id", f"eq.{user_id}")],
    )
