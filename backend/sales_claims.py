from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from uuid import UUID


class SalesClaimError(Exception):
    pass


class SalesClaimConflictError(SalesClaimError):
    def __init__(self, claim: "SalesClaimRecord") -> None:
        self.claim = claim
        super().__init__(f"project is already claimed by {claim.owner_display_name or claim.owner_email}")


class SalesClaimPermissionError(SalesClaimError):
    pass


class SalesClaimNotFoundError(SalesClaimError):
    pass


class SalesClaimInvalidTransitionError(SalesClaimError):
    pass


SALES_CLAIM_STATUS_ACTIVE = "active"
SALES_CLAIM_STATUS_WON = "won"
SALES_CLAIM_STATUS_LOST = "lost"
SALES_CLAIM_STATUSES = {
    SALES_CLAIM_STATUS_ACTIVE,
    SALES_CLAIM_STATUS_WON,
    SALES_CLAIM_STATUS_LOST,
}


@dataclass
class SalesClaimRecord:
    organization_id: UUID
    project_id: UUID
    source_entry_id: UUID | None
    source_run_id: UUID | None
    project_name: str
    owner_user_id: UUID | None
    owner_email: str
    owner_display_name: str
    claimed_at: datetime
    current_owner_assigned_at: datetime
    released_at: datetime | None = None
    is_active: bool = True
    claim_status: str = SALES_CLAIM_STATUS_ACTIVE
    closed_at: datetime | None = None
    closed_by: UUID | None = None
    sales_note: str = ""
    sales_note_updated_at: datetime | None = None
    sales_note_updated_by: UUID | None = None
    estimated_amount_text: str = ""
    estimated_amount_low_krw: int | None = None
    estimated_amount_high_krw: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "source_entry_id": self.source_entry_id,
            "source_run_id": self.source_run_id,
            "project_name": self.project_name,
            "owner_user_id": self.owner_user_id,
            "owner_email": self.owner_email,
            "owner_display_name": self.owner_display_name,
            "claimed_at": self.claimed_at,
            "current_owner_assigned_at": self.current_owner_assigned_at,
            "released_at": self.released_at,
            "is_active": self.is_active,
            "claim_status": self.claim_status,
            "closed_at": self.closed_at,
            "closed_by": self.closed_by,
            "sales_note": self.sales_note,
            "sales_note_updated_at": self.sales_note_updated_at,
            "sales_note_updated_by": self.sales_note_updated_by,
            "estimated_amount_text": self.estimated_amount_text,
            "estimated_amount_low_krw": self.estimated_amount_low_krw,
            "estimated_amount_high_krw": self.estimated_amount_high_krw,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class SalesActor:
    organization_id: UUID
    user_id: UUID | None
    email: str
    display_name: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role in {"platform_admin", "org_admin"}


_AMOUNT_RANGE_RE = re.compile(
    r"(?P<low>\d+(?:\.\d+)?)\s*(?:억|억원)?\s*~\s*(?P<high>\d+(?:\.\d+)?)\s*(?:억|억원)?"
)
_AMOUNT_SINGLE_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?:억|억원)?")
_AMOUNT_EOK = Decimal("100000000")
_SALES_NOTE_TIMESTAMP_RE = re.compile(r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*(?P<text>.*)$")


class InMemorySalesClaimStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_claims: dict[tuple[UUID, UUID], SalesClaimRecord] = {}

    def list_claims(
        self,
        *,
        organization_id: UUID,
        project_ids: list[UUID] | None = None,
        lightweight: bool = False,
    ) -> list[SalesClaimRecord]:
        with self._lock:
            visible = [
                claim
                for (org_id, project_id), claim in self._active_claims.items()
                if org_id == organization_id and (project_ids is None or project_id in project_ids)
            ]
            return [self._clone_claim(claim) for claim in sorted(visible, key=lambda item: item.claimed_at)]

    def claim_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        source_entry_id: UUID | None,
        source_run_id: UUID | None,
        project_name: str,
        estimated_amount_text: str,
    ) -> tuple[bool, SalesClaimRecord]:
        key = (actor.organization_id, project_id)
        with self._lock:
            existing = self._active_claims.get(key)
            if existing is not None:
                if actor.user_id is not None and existing.owner_user_id == actor.user_id:
                    return False, self._clone_claim(existing)
                raise SalesClaimConflictError(self._clone_claim(existing))

            low_krw, high_krw = _parse_estimated_amount_range(estimated_amount_text)
            now = datetime.now(timezone.utc)
            claim = SalesClaimRecord(
                organization_id=actor.organization_id,
                project_id=project_id,
                source_entry_id=source_entry_id,
                source_run_id=source_run_id,
                project_name=project_name,
                owner_user_id=actor.user_id,
                owner_email=actor.email,
                owner_display_name=actor.display_name or actor.email,
                claimed_at=now,
                current_owner_assigned_at=now,
                claim_status=SALES_CLAIM_STATUS_ACTIVE,
                sales_note="",
                estimated_amount_text=estimated_amount_text,
                estimated_amount_low_krw=low_krw,
                estimated_amount_high_krw=high_krw,
                created_at=now,
                updated_at=now,
            )
            self._active_claims[key] = claim
            return True, self._clone_claim(claim)

    def update_sales_note(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        sales_note: str,
        force_admin_override: bool = False,
    ) -> SalesClaimRecord:
        key = (actor.organization_id, project_id)
        with self._lock:
            claim = self._active_claims.get(key)
            if claim is None:
                raise SalesClaimNotFoundError("sales claim not found")
            owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
            if not owner_match and not (force_admin_override and actor.is_admin):
                raise SalesClaimPermissionError("only the claim owner can update sales_note")
            if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE and not (force_admin_override and actor.is_admin):
                raise SalesClaimInvalidTransitionError("closed sales claims cannot be updated")
            now = datetime.now(timezone.utc)
            claim.sales_note = str(sales_note or "")
            claim.sales_note_updated_at = now
            claim.sales_note_updated_by = actor.user_id
            claim.updated_at = now
            return self._clone_claim(claim)

    def transfer_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        target_user_id: UUID | None,
        target_email: str,
        target_display_name: str,
        force: bool = False,
    ) -> SalesClaimRecord:
        key = (actor.organization_id, project_id)
        with self._lock:
            claim = self._active_claims.get(key)
            if claim is None:
                raise SalesClaimNotFoundError("sales claim not found")
            owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
            if not owner_match and not (force and actor.is_admin):
                raise SalesClaimPermissionError("you do not have permission to transfer this claim")
            if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE:
                raise SalesClaimInvalidTransitionError("closed sales claims cannot be transferred")
            next_owner_email = str(target_email or "").strip().lower()
            if not next_owner_email:
                raise SalesClaimInvalidTransitionError("target user is required")
            if target_user_id is not None and claim.owner_user_id == target_user_id:
                raise SalesClaimInvalidTransitionError("claim is already assigned to that user")
            if next_owner_email == claim.owner_email.strip().lower():
                raise SalesClaimInvalidTransitionError("claim is already assigned to that user")

            now = datetime.now(timezone.utc)
            transfer_note = append_sales_note_entry(
                claim.sales_note,
                build_system_sales_note_text(
                    f"{claim.owner_display_name or claim.owner_email} -> "
                    f"{target_display_name or next_owner_email} 이관"
                ),
                timestamp=now,
            )
            claim.owner_user_id = target_user_id
            claim.owner_email = next_owner_email
            claim.owner_display_name = str(target_display_name or next_owner_email)
            claim.current_owner_assigned_at = now
            claim.sales_note = transfer_note
            claim.sales_note_updated_at = now
            claim.sales_note_updated_by = actor.user_id
            claim.updated_at = now
            return self._clone_claim(claim)

    def close_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        outcome: str,
        contract_amount_text: str = "",
        force: bool = False,
    ) -> SalesClaimRecord:
        key = (actor.organization_id, project_id)
        normalized_outcome = normalize_sales_claim_status(outcome)
        if normalized_outcome not in {SALES_CLAIM_STATUS_WON, SALES_CLAIM_STATUS_LOST}:
            raise SalesClaimInvalidTransitionError("sales claim close outcome must be won or lost")
        with self._lock:
            claim = self._active_claims.get(key)
            if claim is None:
                raise SalesClaimNotFoundError("sales claim not found")
            owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
            if not owner_match and not (force and actor.is_admin):
                raise SalesClaimPermissionError("you do not have permission to close this claim")
            if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE:
                raise SalesClaimInvalidTransitionError("sales claim is already closed")

            now = datetime.now(timezone.utc)
            claim.claim_status = normalized_outcome
            claim.closed_at = now
            claim.closed_by = actor.user_id
            claim.sales_note = append_sales_note_entry(
                claim.sales_note,
                build_close_sales_note_text(normalized_outcome, contract_amount_text),
                timestamp=now,
            )
            claim.sales_note_updated_at = now
            claim.sales_note_updated_by = actor.user_id
            claim.updated_at = now
            return self._clone_claim(claim)

    def release_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        force: bool = False,
    ) -> SalesClaimRecord:
        key = (actor.organization_id, project_id)
        with self._lock:
            claim = self._active_claims.get(key)
            if claim is None:
                raise SalesClaimNotFoundError("sales claim not found")
            owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
            if not owner_match and not (force and actor.is_admin):
                raise SalesClaimPermissionError("you do not have permission to release this claim")

            released = self._clone_claim(claim)
            now = datetime.now(timezone.utc)
            released.is_active = False
            released.released_at = now
            released.updated_at = now
            self._active_claims.pop(key, None)
            return released

    def summarize_by_user(self, *, organization_id: UUID) -> list[dict[str, Any]]:
        return summarize_sales_claim_records(self.list_claims(organization_id=organization_id))

    @staticmethod
    def _clone_claim(claim: SalesClaimRecord) -> SalesClaimRecord:
        return SalesClaimRecord(
            organization_id=claim.organization_id,
            project_id=claim.project_id,
            source_entry_id=claim.source_entry_id,
            source_run_id=claim.source_run_id,
            project_name=claim.project_name,
            owner_user_id=claim.owner_user_id,
            owner_email=claim.owner_email,
            owner_display_name=claim.owner_display_name,
            claimed_at=claim.claimed_at,
            current_owner_assigned_at=claim.current_owner_assigned_at,
            released_at=claim.released_at,
            is_active=claim.is_active,
            claim_status=claim.claim_status,
            closed_at=claim.closed_at,
            closed_by=claim.closed_by,
            sales_note=claim.sales_note,
            sales_note_updated_at=claim.sales_note_updated_at,
            sales_note_updated_by=claim.sales_note_updated_by,
            estimated_amount_text=claim.estimated_amount_text,
            estimated_amount_low_krw=claim.estimated_amount_low_krw,
            estimated_amount_high_krw=claim.estimated_amount_high_krw,
            created_at=claim.created_at,
            updated_at=claim.updated_at,
        )


_STORE = InMemorySalesClaimStore()


def get_sales_claim_store() -> InMemorySalesClaimStore:
    return _STORE


def summarize_sales_claim_records(claims: list[SalesClaimRecord]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    now = datetime.now(timezone.utc)
    for claim in claims:
        if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE:
            continue
        group_key = str(claim.owner_user_id or claim.owner_email or "")
        group = grouped.setdefault(
            group_key,
            {
                "user_id": claim.owner_user_id,
                "user_name": claim.owner_display_name or claim.owner_email,
                "user_email": claim.owner_email,
                "active_project_count": 0,
                "total_low_krw": 0,
                "total_high_krw": 0,
                "projects": [],
            },
        )
        group["active_project_count"] += 1
        if claim.estimated_amount_low_krw is not None:
            group["total_low_krw"] += int(claim.estimated_amount_low_krw)
        if claim.estimated_amount_high_krw is not None:
            group["total_high_krw"] += int(claim.estimated_amount_high_krw)
        group["projects"].append(
            {
                "project_id": claim.project_id,
                "project_name": claim.project_name,
                "estimated_amount_text": claim.estimated_amount_text,
                "estimated_amount_low_krw": claim.estimated_amount_low_krw,
                "estimated_amount_high_krw": claim.estimated_amount_high_krw,
                "claimed_at": claim.claimed_at,
                "current_owner_assigned_at": claim.current_owner_assigned_at,
                "elapsed_days": max(0, (now - claim.claimed_at).days),
                "owner_elapsed_days": max(0, (now - claim.current_owner_assigned_at).days),
                "sales_note": claim.sales_note,
            }
        )

    items = list(grouped.values())
    for item in items:
        item["projects"] = sorted(item["projects"], key=lambda project: project["claimed_at"])
    items.sort(key=lambda item: (str(item["user_name"]).lower(), str(item["user_email"]).lower()))
    return items


def _parse_estimated_amount_range(raw_text: str) -> tuple[int | None, int | None]:
    text = str(raw_text or "").replace(",", "").strip()
    if not text:
        return None, None

    range_match = _AMOUNT_RANGE_RE.search(text)
    if range_match:
        low = _parse_eok_decimal(range_match.group("low"))
        high = _parse_eok_decimal(range_match.group("high"))
        return low, high

    single_match = _AMOUNT_SINGLE_RE.search(text)
    if single_match:
        value = _parse_eok_decimal(single_match.group("value"))
        return value, value

    return None, None


def _parse_eok_decimal(raw_value: str) -> int | None:
    try:
        decimal_value = Decimal(str(raw_value).strip())
    except (InvalidOperation, ValueError):
        return None
    return int(decimal_value * _AMOUNT_EOK)


def normalize_sales_claim_status(raw_value: str) -> str:
    normalized = str(raw_value or "").strip().lower()
    if normalized not in SALES_CLAIM_STATUSES:
        return SALES_CLAIM_STATUS_ACTIVE
    return normalized


def append_sales_note_entry(raw_sales_note: str, entry_text: str, *, timestamp: datetime | None = None) -> str:
    entry = serialize_sales_note_entry(entry_text, timestamp=timestamp)
    if not entry:
        return str(raw_sales_note or "")
    existing = [item for item in str(raw_sales_note or "").splitlines() if str(item or "").strip()]
    existing.append(entry)
    return "\n".join(existing)


def serialize_sales_note_entry(text: str, *, timestamp: datetime | None = None) -> str:
    trimmed = str(text or "").strip()
    if not trimmed:
        return ""
    entry_timestamp = (timestamp or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return f"[{entry_timestamp.strftime('%Y-%m-%d %H:%M')}] {trimmed}"


def build_system_sales_note_text(text: str) -> str:
    return f"[시스템] {str(text or '').strip()}"


def build_close_sales_note_text(outcome: str, contract_amount_text: str = "") -> str:
    normalized_outcome = normalize_sales_claim_status(outcome)
    if normalized_outcome == SALES_CLAIM_STATUS_WON:
        amount = str(contract_amount_text or "").strip()
        return build_system_sales_note_text(
            f"계약 완료 처리 | 계약금액 {amount}" if amount else "계약 완료 처리"
        )
    return build_system_sales_note_text("영업 종료 처리")


def infer_sales_claim_state_from_note(
    raw_sales_note: str,
    *,
    claimed_at: datetime,
) -> tuple[datetime, str, datetime | None]:
    assigned_at = claimed_at
    claim_status = SALES_CLAIM_STATUS_ACTIVE
    closed_at: datetime | None = None
    for line in str(raw_sales_note or "").splitlines():
        parsed = _parse_sales_note_line(line)
        if parsed is None:
            continue
        timestamp, text = parsed
        if "[시스템]" not in text:
            continue
        if "이관" in text:
            assigned_at = timestamp
        if "계약 완료 처리" in text:
            claim_status = SALES_CLAIM_STATUS_WON
            closed_at = timestamp
        elif "영업 종료 처리" in text:
            claim_status = SALES_CLAIM_STATUS_LOST
            closed_at = timestamp
    return assigned_at, claim_status, closed_at


def _parse_sales_note_line(raw_line: str) -> tuple[datetime, str] | None:
    raw = str(raw_line or "").strip()
    if not raw:
        return None
    matched = _SALES_NOTE_TIMESTAMP_RE.match(raw)
    if matched:
        try:
            timestamp = datetime.strptime(matched.group("timestamp"), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
        return timestamp, str(matched.group("text") or "").strip()
    return None
