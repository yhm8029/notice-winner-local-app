from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any


def normalize_local_user_status(value: Any) -> str:
    account_status = normalize_account_status(value)
    if account_status in {"inactive", "deactivated"}:
        return account_status
    return "active"


def normalize_account_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"inactive", "deactivated"}:
        return normalized
    return "active"


def normalize_membership_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"inactive", "deactivated"}:
        return normalized
    return "active"


def normalize_org_role(value: Any, *, valid_org_roles: set[str]) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in valid_org_roles:
        return "org_member"
    return normalized


def normalize_global_role(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "platform_admin":
        return normalized
    return ""


def parse_datetime_value(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


def map_role_label(role: str) -> str:
    normalized = str(role or "").strip().lower()
    if normalized in {"admin", "org_admin"}:
        return "org_admin"
    return "org_member"


def map_membership_role_to_legacy_role(role: str, *, normalize_org_role_fn: Any) -> str:
    normalized = normalize_org_role_fn(role)
    if normalized == "org_admin":
        return "admin"
    return "member"


def is_missing_relation_error(message: str, relation_name: str) -> bool:
    lowered = str(message or "").lower()
    relation = relation_name.lower()
    if relation not in lowered:
        return False
    return any(token in lowered for token in ("relation", "schema cache", "table", "column"))


def is_missing_column_error(message: str, column_name: str) -> bool:
    lowered = str(message or "").lower()
    column = column_name.lower()
    if column not in lowered:
        return False
    return any(token in lowered for token in ("column", "schema cache", "does not exist"))
