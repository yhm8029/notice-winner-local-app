from __future__ import annotations

from typing import Any


def list_local_users(
    *,
    organization_id: str,
    include_inactive: bool = False,
    query_local_user_rows: Any,
    normalize_local_user_row: Any,
) -> list[dict[str, Any]]:
    filters: list[tuple[str, str]] = [
        ("organization_id", f"eq.{organization_id}"),
        ("order", "display_name.asc"),
    ]
    rows = query_local_user_rows(filters=filters)
    items: list[dict[str, Any]] = []
    for row in rows:
        item = normalize_local_user_row(row)
        if not include_inactive and str(item.get("status") or "active") != "active":
            continue
        items.append(item)
    return items


def list_local_users_overview(
    *,
    organization_id: str,
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    error_cls: type[Exception],
    membership_overview_select_columns: str,
    is_missing_relation_error: Any,
    normalize_local_user_row: Any,
    list_local_users: Any,
) -> list[dict[str, Any]]:
    filters: list[tuple[str, str]] = [
        ("organization_id", f"eq.{organization_id}"),
        ("membership_status", "eq.active"),
        ("account_status", "eq.active"),
        ("order", "display_name.asc"),
    ]
    try:
        rows, _headers = request_json_fn(
            rest_url=rest_base_url(),
            api_key=service_api_key(),
            timeout_seconds=timeout_seconds(),
            method="GET",
            path="/organization_member_profiles",
            query=[("select", membership_overview_select_columns), *filters],
            error_cls=error_cls,
        )
        if not isinstance(rows, list):
            return []
        return [normalize_local_user_row(dict(item)) for item in rows]
    except error_cls as exc:
        if not is_missing_relation_error(str(getattr(exc, "message", exc)), "organization_member_profiles"):
            raise
    return list_local_users(organization_id=organization_id, include_inactive=False)


def query_local_user_rows(
    *,
    filters: list[tuple[str, str]],
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    error_cls: type[Exception],
    membership_view_select_columns: str,
    local_user_select_columns: str,
    local_user_fallback_select_columns: str,
    is_missing_relation_error: Any,
    build_legacy_local_user_row: Any,
) -> list[dict[str, Any]]:
    try:
        rows, _headers = request_json_fn(
            rest_url=rest_base_url(),
            api_key=service_api_key(),
            timeout_seconds=timeout_seconds(),
            method="GET",
            path="/organization_member_profiles",
            query=[("select", membership_view_select_columns), *filters],
            error_cls=error_cls,
        )
        if not isinstance(rows, list):
            return []
        return [dict(item) for item in rows]
    except error_cls as exc:
        if not is_missing_relation_error(str(getattr(exc, "message", exc)), "organization_member_profiles"):
            raise

    for select_columns in (local_user_select_columns, local_user_fallback_select_columns):
        legacy_filters = [("id", value) if key == "user_id" else (key, value) for key, value in filters]
        query = [("select", select_columns), *legacy_filters]
        try:
            rows, _headers = request_json_fn(
                rest_url=rest_base_url(),
                api_key=service_api_key(),
                timeout_seconds=timeout_seconds(),
                method="GET",
                path="/users",
                query=query,
                error_cls=error_cls,
            )
            if not isinstance(rows, list):
                return []
            return [build_legacy_local_user_row(item) for item in rows]
        except error_cls as exc:
            lowered = str(getattr(exc, "message", exc) or "").lower()
            if select_columns == local_user_select_columns and "status" in lowered and "column" in lowered:
                continue
            raise
    return []


def normalize_local_user_row(
    *,
    raw: dict[str, Any],
    normalize_account_status: Any,
    normalize_membership_status: Any,
    normalize_global_role: Any,
    build_legacy_local_user_row: Any,
) -> dict[str, Any]:
    row = dict(raw)
    if "membership_role" in row:
        role = str(row.get("membership_role") or "org_member")
        account_status = normalize_account_status(row.get("account_status"))
        membership_status = normalize_membership_status(row.get("membership_status"))
        effective_status = membership_status if account_status == "active" else account_status
        return {
            "id": str(row.get("user_id") or ""),
            "membership_id": str(row.get("membership_id") or ""),
            "organization_id": str(row.get("organization_id") or ""),
            "organization_name": str(row.get("organization_name") or ""),
            "email": str(row.get("email") or ""),
            "display_name": str(row.get("display_name") or ""),
            "role": role,
            "status": effective_status,
            "account_status": account_status,
            "membership_status": membership_status,
            "global_role": normalize_global_role(row.get("global_role")),
            "team_name": str(row.get("team_name") or ""),
            "job_title": str(row.get("job_title") or ""),
            "mobile_phone": str(row.get("mobile_phone") or ""),
            "office_phone": str(row.get("office_phone") or ""),
        }
    return build_legacy_local_user_row(raw=row)


def build_legacy_local_user_row(
    *,
    raw: dict[str, Any],
    map_role_label: Any,
    normalize_local_user_status: Any,
    get_organization: Any,
) -> dict[str, Any]:
    row = dict(raw)
    role = map_role_label(str(row.get("role") or "member"))
    status = normalize_local_user_status(row.get("status"))
    organization_id = str(row.get("organization_id") or "")
    organization = get_organization(organization_id)
    return {
        "id": str(row.get("id") or ""),
        "membership_id": "",
        "organization_id": organization_id,
        "organization_name": str(organization.get("name") or "") if organization else "",
        "email": str(row.get("email") or ""),
        "display_name": str(row.get("display_name") or ""),
        "role": role,
        "status": status,
        "account_status": status,
        "membership_status": status,
        "global_role": "",
        "team_name": "",
        "job_title": "",
        "mobile_phone": "",
        "office_phone": "",
    }


def list_organization_audit_logs(
    *,
    organization_id: str,
    limit: int = 20,
    get_organization: Any,
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    error_cls: type[Exception],
    audit_log_select_columns: str,
    list_local_users: Any,
) -> list[dict[str, Any]]:
    organization = get_organization(organization_id)
    if organization is None:
        raise error_cls("organization not found", status_code=404, code="organization_not_found")
    clamped_limit = max(1, min(int(limit or 20), 100))
    rows, _headers = request_json_fn(
        rest_url=rest_base_url(),
        api_key=service_api_key(),
        timeout_seconds=timeout_seconds(),
        method="GET",
        path="/audit_logs",
        query=[
            ("select", audit_log_select_columns),
            ("organization_id", f"eq.{organization_id}"),
            ("order", "created_at.desc"),
            ("limit", str(clamped_limit)),
        ],
        error_cls=error_cls,
    )
    if not isinstance(rows, list) or not rows:
        return []

    members = list_local_users(organization_id=organization_id, include_inactive=True)
    actor_by_user_id = {
        str(item.get("id") or "").strip(): dict(item)
        for item in members
        if str(item.get("id") or "").strip()
    }
    actor_by_membership_id = {
        str(item.get("membership_id") or "").strip(): dict(item)
        for item in members
        if str(item.get("membership_id") or "").strip()
    }

    items: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw or {})
        actor_user_id = str(row.get("actor_user_id") or "").strip()
        actor_membership_id = str(row.get("actor_membership_id") or "").strip()
        actor = actor_by_user_id.get(actor_user_id) or actor_by_membership_id.get(actor_membership_id) or {}
        payload_json = row.get("payload_json")
        items.append(
            {
                "id": int(row.get("id") or 0),
                "organization_id": str(row.get("organization_id") or organization_id),
                "actor_user_id": actor_user_id or None,
                "actor_membership_id": actor_membership_id or None,
                "actor_email": str(actor.get("email") or ""),
                "actor_display_name": str(actor.get("display_name") or ""),
                "actor_role": str(actor.get("global_role") or actor.get("role") or ""),
                "event_type": str(row.get("event_type") or ""),
                "target_type": str(row.get("target_type") or ""),
                "target_id": str(row.get("target_id") or ""),
                "payload_json": dict(payload_json) if isinstance(payload_json, dict) else {},
                "created_at": row.get("created_at"),
            }
        )
    return items
