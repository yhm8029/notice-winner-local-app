from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from decimal import ROUND_HALF_UP
import re
from typing import Any
from typing import Protocol
from uuid import UUID

TRACKER_EDITABLE_FIELDS = (
    "project_name",
    "gross_area_scale",
    "construction_cost",
    "demand_org_name",
    "demand_contact",
    "client_location",
    "site_location_1",
    "site_location_2",
    "architect_office",
    "construction_start_date",
    "last_checked_date",
    "progress_note",
    "notice_date",
    "manager_name",
    "building_automation_estimated_amount",
)
TRACKER_CHANGE_SOURCES = frozenset({"web", "system", "import"})

TrackerEntryRow = dict[str, Any]
TrackerEntryAuditLogRow = dict[str, Any]

TRACKER_REGION_FIELD_NAMES = (
    "demand_org_name",
    "client_location",
    "site_location_1",
    "site_location_2",
)
TRACKER_REGION_ALIASES: dict[str, tuple[str, ...]] = {
    "서울": ("서울", "서울특별시"),
    "부산": ("부산", "부산광역시"),
    "대구": ("대구", "대구광역시"),
    "인천": ("인천", "인천광역시"),
    "광주": ("광주", "광주광역시"),
    "대전": ("대전", "대전광역시"),
    "울산": ("울산", "울산광역시"),
    "세종": ("세종", "세종특별자치시"),
    "경기": ("경기", "경기도"),
    "강원": ("강원", "강원도", "강원특별자치도"),
    "충북": ("충북", "충청북도"),
    "충남": ("충남", "충청남도"),
    "전북": ("전북", "전라북도", "전북특별자치도"),
    "전남": ("전남", "전라남도"),
    "경북": ("경북", "경상북도"),
    "경남": ("경남", "경상남도"),
    "제주": ("제주", "제주도", "제주특별자치도"),
}
TRACKER_REGION_TOKEN_ONLY_CANONICALS = frozenset({"광주", "대구"})
TRACKER_USER_HIDDEN_TITLE_KEYWORDS = (
    "\ub300\ud589\uc6a9\uc5ed",
    "\uad00\ub9ac\uc6a9\uc5ed",
)


def _normalize_tracker_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\uac00-\ud7a3]", "", str(value or "")).lower()


def normalize_tracker_region(region: str) -> str:
    raw = str(region or "").strip()
    if not raw:
        return ""
    if raw in TRACKER_REGION_ALIASES:
        return raw
    for canonical, aliases in TRACKER_REGION_ALIASES.items():
        if raw == canonical or raw in aliases:
            return canonical
    return ""


def parse_tracker_regions(region: Any) -> tuple[str, ...]:
    if region is None:
        return ()
    if isinstance(region, (list, tuple, set, frozenset)):
        raw_values = [str(item or "").strip() for item in region]
    else:
        raw_values = re.split(r"[\n,;|/]+", str(region or ""))
    seen: set[str] = set()
    normalized_values: list[str] = []
    for raw in raw_values:
        canonical = normalize_tracker_region(raw)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        normalized_values.append(canonical)
    return tuple(normalized_values)


def get_tracker_region_aliases(region: str) -> tuple[str, ...]:
    canonical = normalize_tracker_region(region)
    if not canonical:
        return ()
    return TRACKER_REGION_ALIASES[canonical]


def _tracker_region_alias_matches_haystack(*, haystack: str, canonical: str, alias: str) -> bool:
    text = str(haystack or "").strip()
    if not text or not alias:
        return False
    if alias != canonical or canonical not in TRACKER_REGION_TOKEN_ONLY_CANONICALS:
        return alias in text
    return bool(re.search(rf"(?<![0-9A-Za-z가-힣]){re.escape(alias)}(?![0-9A-Za-z가-힣])", text))


def tracker_entry_matches_region(row: TrackerEntryRow, region: str) -> bool:
    selected_regions = parse_tracker_regions(region)
    if not selected_regions:
        return True
    haystacks = [
        str(row.get(field_name, "") or "").strip()
        for field_name in TRACKER_REGION_FIELD_NAMES
    ]
    return any(
        _tracker_region_alias_matches_haystack(
            haystack=haystack,
            canonical=canonical,
            alias=alias,
        )
        for canonical in selected_regions
        for alias in get_tracker_region_aliases(canonical)
        for haystack in haystacks
        if haystack
    )


def tracker_entry_matches_title_visibility(
    row: TrackerEntryRow,
    *,
    exclude_auxiliary_titles: bool,
) -> bool:
    if not exclude_auxiliary_titles:
        return True
    title_norm = _normalize_tracker_text(str(row.get("project_name", "") or ""))
    if not title_norm:
        return True
    return not any(_normalize_tracker_text(keyword) in title_norm for keyword in TRACKER_USER_HIDDEN_TITLE_KEYWORDS)


def normalize_tracker_notice_year(notice_year: Any) -> str:
    text = str(notice_year or "").strip()
    return text if re.fullmatch(r"\d{4}", text) else ""


def tracker_entry_matches_notice_year(row: TrackerEntryRow, notice_year: Any) -> bool:
    normalized_year = normalize_tracker_notice_year(notice_year)
    if not normalized_year:
        return True
    raw_date = str(row.get("notice_date") or row.get("notice_date_source") or "").strip()
    digits = re.sub(r"[^0-9]", "", raw_date)
    return len(digits) >= 4 and digits[:4] == normalized_year


_TRACKER_OVERRIDE_DATE_RE = re.compile(r"^\s*(\d{4})[-./]?(\d{2})[-./]?(\d{2})\s*$")
_TRACKER_COST_EOK_RE = re.compile(r"([0-9][0-9,]*(?:\.\d+)?)\s*억원")
_TRACKER_RELATIVE_START_PREFIXES = ("착수일로부터", "착공일로부터", "계약일로부터", "계약일기준")


def _normalize_tracker_override_date(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = _TRACKER_OVERRIDE_DATE_RE.fullmatch(text)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{year}-{month}-{day}"


def format_tracker_display_date(value: Any) -> str:
    raw = str(value or "").strip()
    normalized = _normalize_tracker_override_date(raw)
    if normalized:
        return normalized
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return parsed.strftime("%Y-%m-%d")


def _looks_like_relative_construction_period(value: str | None) -> bool:
    text = re.sub(r"\s+", "", str(value or "").strip())
    if not text:
        return False
    return text.startswith(_TRACKER_RELATIVE_START_PREFIXES)


def parse_tracker_cost_to_won(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    eok_match = _TRACKER_COST_EOK_RE.search(text.replace(" ", ""))
    if eok_match:
        try:
            return int(round(float(eok_match.group(1).replace(",", "")) * 100000000))
        except Exception:
            return 0
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return 0
    try:
        return int(digits)
    except Exception:
        return 0


def format_tracker_cost_display(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    won = parse_tracker_cost_to_won(text)
    if won <= 0:
        return text
    eok = round(float(won) / 100000000.0, 2)
    return f"{eok:.2f}".rstrip("0").rstrip(".") + "억원"


def estimate_tracker_building_automation_amount(construction_cost: Any) -> str:
    won = parse_tracker_cost_to_won(construction_cost)
    if won <= 0:
        return ""
    eok = Decimal(str(won)) / Decimal("100000000")
    low = (eok * Decimal("0.015")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    high = (eok * Decimal("0.020")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{low:.2f}억원~{high:.2f}억원"


def is_legacy_tracker_building_automation_estimate(value: Any) -> bool:
    return bool(
        re.fullmatch(
            r"\s*\d+(?:\.\d+)?\s*~\s*\d+(?:\.\d+)?\s*(?:억|억원)\s*",
            str(value or "").strip(),
        )
    )


def _extract_tracker_duration_days(value: str | None) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    month_match = re.search(r"(\d{1,3})\s*개월", text)
    if month_match:
        try:
            return int(month_match.group(1)) * 30
        except Exception:
            return 0
    day_match = re.search(r"(\d{1,4})\s*일", text)
    if day_match:
        try:
            return int(day_match.group(1))
        except Exception:
            return 0
    return 0


def _format_tracker_construction_period(
    *,
    contract_date: str,
    duration_days: int,
    fallback_value: str,
) -> str:
    if duration_days <= 0:
        return str(fallback_value or "").strip()
    date_text = str(contract_date or "").strip()
    if not date_text:
        return f"착수일로부터 {duration_days}일"
    match = re.search(r"(\d{4})[-./]?(\d{2})[-./]?(\d{2})", date_text)
    if not match:
        return f"계약일 {date_text} 기준 {duration_days}일"
    year, month, day = map(int, match.groups())
    try:
        from datetime import datetime, timedelta

        start = datetime(year, month, day)
        due = start + timedelta(days=duration_days)
        return (
            f"계약일 {start.strftime('%Y-%m-%d')} 기준 {duration_days}일 "
            f"(완료예정 {due.strftime('%Y-%m-%d')})"
        )
    except Exception:
        return f"계약일 {date_text} 기준 {duration_days}일"


def coerce_tracker_override_value(
    *,
    field_name: str,
    new_value: str | None,
    source_value: str | None = None,
    current_effective_value: str | None = None,
) -> str | None:
    if field_name == "construction_cost" and new_value is not None:
        normalized_cost = format_tracker_cost_display(new_value)
        return normalized_cost or new_value
    if field_name != "construction_start_date" or new_value is None:
        return new_value
    if (
        _normalize_tracker_override_date(current_effective_value)
        and not _normalize_tracker_override_date(new_value)
        and _looks_like_relative_construction_period(new_value)
    ):
        return current_effective_value
    normalized_contract_date = _normalize_tracker_override_date(new_value)
    if not normalized_contract_date:
        return new_value
    duration_days = _extract_tracker_duration_days(current_effective_value)
    if duration_days <= 0:
        duration_days = _extract_tracker_duration_days(source_value)
    if duration_days <= 0:
        return new_value
    return _format_tracker_construction_period(
        contract_date=normalized_contract_date,
        duration_days=duration_days,
        fallback_value=new_value,
    )


class TrackerEntryRepositoryError(RuntimeError):
    pass


class TrackerEntryRepositoryConfigError(TrackerEntryRepositoryError):
    pass


@dataclass(frozen=True)
class TrackerEntryPatchResult:
    changed: bool
    entry: TrackerEntryRow
    audit_log: TrackerEntryAuditLogRow | None = None


class TrackerEntryRepository(Protocol):
    def list_entry_summaries(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
        notice_year: str = "",
    ) -> tuple[list[TrackerEntryRow], int]: ...

    def list_entries(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
        notice_year: str = "",
    ) -> tuple[list[TrackerEntryRow], int]: ...

    def list_entries_for_export(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
        notice_year: str = "",
    ) -> tuple[list[TrackerEntryRow], int]: ...

    def get_entries_data_version(self) -> str: ...

    def get_entry(self, entry_id: UUID) -> TrackerEntryRow | None: ...

    def get_entry_by_entry_key(self, entry_key: str) -> TrackerEntryRow | None: ...

    def apply_override(
        self,
        *,
        entry_id: UUID,
        field_name: str,
        new_value: str | None,
        actor_user_id: UUID | None,
        actor_label: str,
        change_source: str,
    ) -> TrackerEntryPatchResult | None: ...

    def upsert_source_entries(
        self,
        *,
        source_run_id: UUID,
        source_tracker_run_id: UUID,
        entries: list[dict[str, Any]],
    ) -> list[TrackerEntryRow]: ...

    def delete_entries_by_source_tracker_run_id(self, *, source_tracker_run_id: UUID) -> int: ...

    def list_audit_logs(
        self,
        *,
        entry_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[TrackerEntryAuditLogRow], int | None]: ...
