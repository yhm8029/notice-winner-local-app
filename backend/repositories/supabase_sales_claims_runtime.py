from __future__ import annotations

import re
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from backend.sales_claims import SalesClaimRecord
from backend.repositories.sales_claims import SalesClaimRepositoryError


SALES_CLAIM_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "project_id",
        "source_entry_id",
        "source_run_id",
        "project_name",
        "owner_user_id",
        "owner_email",
        "owner_display_name",
        "claimed_at",
        "current_owner_assigned_at",
        "released_at",
        "is_active",
        "claim_status",
        "closed_at",
        "closed_by",
        "sales_note",
        "sales_note_updated_at",
        "sales_note_updated_by",
        "estimated_amount_text",
        "estimated_amount_low_krw",
        "estimated_amount_high_krw",
        "created_at",
        "updated_at",
    )
)

SALES_CLAIM_OVERVIEW_SELECT = ",".join(
    (
        "id",
        "organization_id",
        "project_id",
        "project_name",
        "owner_user_id",
        "owner_email",
        "owner_display_name",
        "claimed_at",
        "current_owner_assigned_at",
        "is_active",
        "claim_status",
        "closed_at",
        "sales_note",
        "estimated_amount_text",
        "created_at",
        "updated_at",
    )
)

SALES_CLAIM_OVERVIEW_SELECT_FALLBACK = ",".join(
    (
        "id",
        "organization_id",
        "project_id",
        "project_name",
        "owner_user_id",
        "owner_email",
        "owner_display_name",
        "claimed_at",
        "is_active",
        "sales_note",
        "estimated_amount_text",
        "created_at",
        "updated_at",
    )
)

SALES_CLAIM_SELECT_FALLBACK = ",".join(
    (
        "id",
        "organization_id",
        "project_id",
        "source_entry_id",
        "source_run_id",
        "project_name",
        "owner_user_id",
        "owner_email",
        "owner_display_name",
        "claimed_at",
        "released_at",
        "is_active",
        "sales_note",
        "sales_note_updated_at",
        "sales_note_updated_by",
        "estimated_amount_text",
        "estimated_amount_low_krw",
        "estimated_amount_high_krw",
        "created_at",
        "updated_at",
    )
)

_ISO_DATETIME_FALLBACK_RE = re.compile(
    r"^(?P<prefix>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?P<fraction>\.\d+)?(?P<offset>Z|[+-]\d{2}:\d{2}|[+-]\d{4})?$"
)


def parse_uuid(value: Any) -> UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return UUID(raw)


def parse_datetime(value: Any) -> datetime:
    parsed = parse_datetime_nullable(value)
    if parsed is None:
        raise SalesClaimRepositoryError("Supabase sales claim row included an invalid datetime")
    return parsed


def parse_datetime_nullable(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        fallback_raw = normalize_iso_datetime_literal(raw)
        if not fallback_raw:
            raise SalesClaimRepositoryError(f"invalid datetime value: {raw}") from exc
        try:
            parsed = datetime.fromisoformat(fallback_raw)
        except ValueError as fallback_exc:
            raise SalesClaimRepositoryError(f"invalid datetime value: {raw}") from fallback_exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_iso_datetime_literal(raw: str) -> str | None:
    match = _ISO_DATETIME_FALLBACK_RE.fullmatch(str(raw or "").strip())
    if match is None:
        return None
    prefix = match.group("prefix")
    fraction = match.group("fraction") or ""
    offset = match.group("offset") or ""
    if fraction:
        digits = fraction[1:]
        fraction = f".{digits.ljust(6, '0')[:6]}"
    if offset == "Z":
        offset = "+00:00"
    elif offset and len(offset) == 5 and offset[0] in "+-":
        offset = f"{offset[:3]}:{offset[3:]}"
    return f"{prefix}{fraction}{offset}"


def parse_int_nullable(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def is_active_claim_conflict_error(message: str) -> bool:
    lowered = str(message or "").lower()
    return "project_sales_claims" in lowered and (
        "duplicate key" in lowered
        or "ux_project_sales_claims_active_project" in lowered
        or "violates unique constraint" in lowered
    )


def is_missing_column_error(message: str, column_name: str) -> bool:
    lowered = str(message or "").lower()
    column = str(column_name or "").strip().lower()
    return column in lowered and any(token in lowered for token in ("column", "schema cache", "does not exist"))


def serialize_claim_snapshot(claim: SalesClaimRecord) -> dict[str, Any]:
    return {
        "organization_id": str(claim.organization_id),
        "project_id": str(claim.project_id),
        "source_entry_id": str(claim.source_entry_id) if claim.source_entry_id else None,
        "source_run_id": str(claim.source_run_id) if claim.source_run_id else None,
        "project_name": claim.project_name,
        "owner_user_id": str(claim.owner_user_id) if claim.owner_user_id else None,
        "owner_email": claim.owner_email,
        "owner_display_name": claim.owner_display_name,
        "claimed_at": claim.claimed_at.isoformat(),
        "current_owner_assigned_at": claim.current_owner_assigned_at.isoformat(),
        "released_at": claim.released_at.isoformat() if claim.released_at else None,
        "is_active": claim.is_active,
        "claim_status": claim.claim_status,
        "closed_at": claim.closed_at.isoformat() if claim.closed_at else None,
        "closed_by": str(claim.closed_by) if claim.closed_by else None,
        "sales_note": claim.sales_note,
        "sales_note_updated_at": claim.sales_note_updated_at.isoformat() if claim.sales_note_updated_at else None,
        "sales_note_updated_by": str(claim.sales_note_updated_by) if claim.sales_note_updated_by else None,
        "estimated_amount_text": claim.estimated_amount_text,
        "estimated_amount_low_krw": claim.estimated_amount_low_krw,
        "estimated_amount_high_krw": claim.estimated_amount_high_krw,
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat(),
    }


def parse_low_krw(raw_text: str) -> int | None:
    record = build_amount_probe(raw_text)
    return record[0]


def parse_high_krw(raw_text: str) -> int | None:
    record = build_amount_probe(raw_text)
    return record[1]


def build_amount_probe(raw_text: str) -> tuple[int | None, int | None]:
    from backend.sales_claims import _parse_estimated_amount_range

    return _parse_estimated_amount_range(raw_text)
