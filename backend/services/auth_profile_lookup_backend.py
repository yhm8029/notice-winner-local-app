from __future__ import annotations

from typing import Any


def get_local_user(
    *,
    user_id: str = "",
    email: str = "",
    organization_id: str = "",
    query_local_user_rows: Any,
    normalize_local_user_row: Any,
) -> dict[str, Any] | None:
    filters: list[tuple[str, str]] = []
    if user_id:
        filters.append(("user_id", f"eq.{user_id}"))
    if email:
        filters.append(("email", f"eq.{email}"))
    if organization_id:
        filters.append(("organization_id", f"eq.{organization_id}"))
    filters.append(("limit", "1"))
    rows = query_local_user_rows(filters=filters)
    if not isinstance(rows, list) or not rows:
        return None
    return normalize_local_user_row(rows[0])


def get_membership_row(
    *,
    organization_id: str = "",
    user_id: str = "",
    membership_id: str = "",
    email: str = "",
    query_local_user_rows: Any,
    normalize_local_user_row: Any,
) -> dict[str, Any] | None:
    filters: list[tuple[str, str]] = []
    if organization_id:
        filters.append(("organization_id", f"eq.{organization_id}"))
    if user_id:
        filters.append(("user_id", f"eq.{user_id}"))
    if membership_id:
        filters.append(("membership_id", f"eq.{membership_id}"))
    if email:
        filters.append(("email", f"eq.{email}"))
    filters.append(("limit", "1"))
    rows = query_local_user_rows(filters=filters)
    if not rows:
        return None
    return normalize_local_user_row(rows[0])


def get_user_profile(
    *,
    user_id: str = "",
    email: str = "",
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    user_profile_select_columns: str,
    is_missing_relation_error: Any,
    build_profile_from_legacy_user: Any,
    normalize_account_status: Any,
    normalize_global_role: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any] | None:
    filters: list[tuple[str, str]] = []
    if user_id:
        filters.append(("id", f"eq.{user_id}"))
    if email:
        filters.append(("email", f"eq.{email}"))
    filters.append(("limit", "1"))
    try:
        rows, _headers = request_json(
            rest_url=rest_base_url(),
            api_key=service_api_key(),
            timeout_seconds=timeout_seconds(),
            method="GET",
            path="/user_profiles",
            query=[("select", user_profile_select_columns), *filters],
            error_cls=auth_error_cls,
        )
    except auth_error_cls as exc:
        if is_missing_relation_error(exc.message, "user_profiles"):
            return build_profile_from_legacy_user(user_id=user_id, email=email)
        raise
    if not isinstance(rows, list) or not rows:
        return None
    row = dict(rows[0])
    row["account_status"] = normalize_account_status(row.get("account_status"))
    row["global_role"] = normalize_global_role(row.get("global_role"))
    return row


def build_profile_from_legacy_user(
    *,
    user_id: str = "",
    email: str = "",
    request_json: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    local_user_select_columns: str,
    local_user_fallback_select_columns: str,
    is_missing_column_error: Any,
    normalize_account_status: Any,
    normalize_global_role: Any,
    auth_error_cls: type[Exception],
) -> dict[str, Any] | None:
    filters: list[tuple[str, str]] = []
    if user_id:
        filters.append(("id", f"eq.{user_id}"))
    if email:
        filters.append(("email", f"eq.{email}"))
    filters.append(("limit", "1"))
    rows = []
    for select_columns in (local_user_select_columns, local_user_fallback_select_columns):
        try:
            rows, _headers = request_json(
                rest_url=rest_base_url(),
                api_key=service_api_key(),
                timeout_seconds=timeout_seconds(),
                method="GET",
                path="/users",
                query=[("select", select_columns), *filters],
                error_cls=auth_error_cls,
            )
            break
        except auth_error_cls as exc:
            if select_columns == local_user_select_columns and is_missing_column_error(exc.message, "status"):
                continue
            raise
    if not isinstance(rows, list) or not rows:
        return None
    row = dict(rows[0])
    return {
        "id": str(row.get("id") or ""),
        "email": str(row.get("email") or ""),
        "display_name": str(row.get("display_name") or ""),
        "mobile_phone": "",
        "office_phone": "",
        "account_status": normalize_account_status(row.get("status")),
        "global_role": normalize_global_role(""),
    }
