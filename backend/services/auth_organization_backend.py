from __future__ import annotations

from typing import Any


def normalize_plan_code(
    value: Any,
    *,
    default_organization_plan_code: str,
    organization_plan_limits: dict[str, dict[str, int]],
) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in organization_plan_limits:
        return normalized
    return default_organization_plan_code


def normalize_limit_value(value: Any, *, default: int, minimum: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def resolve_next_plan_code(
    plan_code: str,
    *,
    organization_plan_order: tuple[str, ...],
) -> str:
    try:
        index = organization_plan_order.index(plan_code)
    except ValueError:
        return ""
    if index >= len(organization_plan_order) - 1:
        return ""
    return organization_plan_order[index + 1]


def normalize_organization_row(
    *,
    raw: dict[str, Any],
    normalize_plan_code: Any,
    normalize_limit_value: Any,
    organization_plan_limits: dict[str, dict[str, int]],
) -> dict[str, Any]:
    row = dict(raw or {})
    plan_code = normalize_plan_code(row.get("plan_code"))
    defaults = organization_plan_limits[plan_code]
    return {
        "id": str(row.get("id") or ""),
        "name": str(row.get("name") or ""),
        "slug": str(row.get("slug") or ""),
        "plan_code": plan_code,
        "plan_label": f"Plan {plan_code}",
        "active_user_limit": normalize_limit_value(
            row.get("active_user_limit"),
            default=defaults["active_user_limit"],
            minimum=1,
        ),
        "pending_invite_limit": normalize_limit_value(
            row.get("pending_invite_limit"),
            default=defaults["pending_invite_limit"],
            minimum=0,
        ),
    }


def get_organization(
    organization_id: str,
    *,
    request_json_fn: Any,
    rest_base_url: Any,
    service_api_key: Any,
    timeout_seconds: Any,
    error_cls: type[Exception],
    organization_select_columns: str,
    organization_legacy_select_columns: str,
    is_missing_column_error: Any,
    normalize_organization_row: Any,
) -> dict[str, Any] | None:
    if not organization_id:
        return None
    for select_columns in (organization_select_columns, organization_legacy_select_columns):
        try:
            rows, _headers = request_json_fn(
                rest_url=rest_base_url(),
                api_key=service_api_key(),
                timeout_seconds=timeout_seconds(),
                method="GET",
                path="/organizations",
                query=[
                    ("select", select_columns),
                    ("id", f"eq.{organization_id}"),
                    ("limit", "1"),
                ],
                error_cls=error_cls,
            )
        except error_cls as exc:
            if select_columns == organization_select_columns and any(
                is_missing_column_error(str(getattr(exc, "message", exc)), column_name)
                for column_name in ("plan_code", "active_user_limit", "pending_invite_limit")
            ):
                continue
            raise
        if not isinstance(rows, list) or not rows:
            return None
        return normalize_organization_row(raw=dict(rows[0]))
    return None
