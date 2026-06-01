from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

from .native_gui_rules import infer_city_from_org_or_project
from .native_gui_rules import infer_region_from_org
from .native_gui_rules import CONTACT_DEPT_SENTENCE_NOISE_PAT
from .native_gui_rules import CONTACT_OTHER_SENTENCE_FRAGMENT_PAT
from .native_gui_rules import INVALID_CITY_LOCATION_TOKENS
from .native_gui_rules import is_auxiliary_service_project
from .native_gui_rules import is_building_like_project
from .native_gui_rules import looks_like_architecture_firm_name
from .native_gui_rules import normalize_contact_candidate
from .native_gui_rules import OFFICIAL_REGION_PATTERN
from .native_tracker_amounts import compute_completion_expected_date
from .native_tracker_amounts import estimate_building_automation_amount_from_cost
from .native_tracker_amounts import format_eok_amount
from .native_tracker_amounts import format_tracker_cost_value
from .native_tracker_amounts import normalize_tracker_gross_area
from .native_tracker_amounts import parse_tracker_area_value
from .native_tracker_amounts import parse_tracker_cost_to_won
from .native_tracker_amounts import looks_like_major_capex_project
from .native_tracker_amounts import resolve_tracker_construction_cost
from .native_tracker_amounts import sanitize_tracker_construction_cost
from .native_tracker_amounts import TRACKER_TRUSTED_COMPLETION_SOURCE_TYPES
from .native_tracker_contacts import extract_tracker_contact_dept
from .native_tracker_contacts import normalize_phone
from .native_tracker_contacts import normalize_tracker_contact
from .native_tracker_contacts import normalize_tracker_contact_person_only
from .native_tracker_regions import infer_tracker_region_from_text
from .native_tracker_regions import normalize_tracker_region_value
from .native_tracker_regions import normalize_tracker_site_city_candidate
from .native_tracker_regions import split_region_city_from_address
from .native_tracker_regions import tracker_region_official_name
from .native_tracker_regions import tracker_site_city_rank
from .korean_admin_districts import match_official_sigungu
from ..repositories.tracker_entries import TRACKER_REGION_ALIASES
from ..repositories.tracker_entries import TRACKER_REGION_TOKEN_ONLY_CANONICALS


TRACKER_CONTACT_DEPT_SUFFIXES = (
    "과",
    "팀",
    "담당",
    "실",
    "센터",
    "본부",
    "국",
    "처",
    "기획실",
    "행정실",
    "관리실",
    "민원실",
    "홍보실",
    "재무실",
    "지원청",
    "추진단",
)
TRACKER_SITE_CITY_NOISE_EXACT = frozenset(
    {
        "과업지시",
        "과업지시서",
        "입면",
        "요구",
        "안내",
    }
)
TRACKER_SITE_CITY_NOISE_PARTS = (
    "재구",
    "재구조",
    "개발지구",
    "지구",
)


def build_tracker_entries_from_winner_csv(
    *,
    winner_csv_path: Path,
    seed_csv_path: Path | None,
) -> list[dict[str, Any]]:
    from .native_tracker_materialization_backend import (
        build_tracker_entries_from_winner_csv as _build_tracker_entries_from_winner_csv,
    )

    return _build_tracker_entries_from_winner_csv(
        winner_csv_path=winner_csv_path,
        seed_csv_path=seed_csv_path,
    )


def _load_seed_index(seed_csv_path: Path | None) -> dict[tuple[str, str], dict[str, str]]:
    if seed_csv_path is None or not seed_csv_path.exists():
        return {}
    rows: dict[tuple[str, str], dict[str, str]] = {}
    with seed_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            bid_no = str((row or {}).get("bid_no") or "").strip().upper()
            bid_ord = _normalize_bid_ord((row or {}).get("bid_ord") or "000")
            if not bid_no:
                continue
            rows[(bid_no, bid_ord)] = {
                "project_name": str((row or {}).get("project_name") or "").strip(),
                "org_name": str((row or {}).get("org_name") or "").strip(),
                "announce_date": str((row or {}).get("announce_date") or "").strip(),
                "opening_scheduled_date": str((row or {}).get("opening_scheduled_date") or "").strip(),
                "notice_officer_name": str((row or {}).get("notice_officer_name") or "").strip(),
                "notice_officer_tel": str((row or {}).get("notice_officer_tel") or "").strip(),
                "demand_officer_name": str((row or {}).get("demand_officer_name") or "").strip(),
                "presmpt_prce": str((row or {}).get("presmpt_prce") or "").strip(),
                "service_name": str((row or {}).get("service_name") or "").strip(),
                "spec_doc_file_name_1": str((row or {}).get("spec_doc_file_name_1") or "").strip(),
            }
    return rows


def _normalize_bid_ord(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "000"
    if raw.isdigit():
        return f"{int(raw):03d}"
    return raw


def _slugify(value: str) -> str:
    compact = "-".join(part for part in str(value or "").strip().lower().replace("/", " ").split() if part)
    return compact or "notice"


def _norm_text(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", str(value or "").lower())


def _resolve_project_name(*, row: dict[str, Any], seed_meta: dict[str, str], bid_no: str) -> str:
    candidates = [
        str(seed_meta.get("project_name") or "").strip(),
        str(row.get("contract_name") or "").strip(),
        str(row.get("post_title") or "").strip(),
        str(row.get("project_name_norm") or "").strip(),
        bid_no,
    ]
    for candidate in candidates:
        if not candidate or _is_generic_project_name(candidate):
            continue
        if looks_like_architecture_firm_name(candidate):
            continue
        if candidate:
            return candidate
    return candidates[-1]


def _is_generic_project_name(value: str) -> bool:
    normalized = "".join(str(value or "").strip().split()).lower()
    generic_tokens = (
        "\ub098\ub77c\uc7a5\ud130",
        "\uad6d\uac00\uc885\ud569\uc804\uc790\uc870\ub2ec",
        "\uc811\uadfc\uac00\ub2a5\ube0c\ub77c\uc6b0\uc800\uc548\ub0b4",
        "\ube0c\ub77c\uc6b0\uc800\uc548\ub0b4",
        "g2b",
    )
    return any(token in normalized for token in generic_tokens)


def _join_non_empty(values: list[str], sep: str) -> str:
    return sep.join(value for value in values if str(value or "").strip())


def _tracker_safe_value(value: Any, source: Any, allowed_prefixes: tuple[str, ...] = ("confirmed",)) -> str:
    source_text = str(source or "").strip()
    if not any(source_text.startswith(prefix) for prefix in allowed_prefixes):
        return ""
    return str(value or "").strip()


def _format_tracker_cost_value(value: Any, source: Any, *, project_name: str = "") -> str:
    if is_auxiliary_service_project(project_name):
        return ""
    raw = _tracker_safe_value(value, source)
    if not raw:
        return ""
    won = _parse_tracker_cost_to_won(raw)
    if won <= 0:
        return raw
    return _format_eok_amount(won)


def _derive_site_locations(*, current_site_location: str, demand_org_name: str, project_name: str) -> tuple[str, str]:
    return normalize_tracker_site_locations(
        current_site_region="",
        current_site_city=current_site_location,
        current_client_location="",
        demand_org_name=demand_org_name,
        project_name=project_name,
        trusted_current_site=True,
    )


def normalize_tracker_site_locations(
    *,
    current_site_region: str,
    current_site_city: str,
    current_client_location: str,
    demand_org_name: str,
    project_name: str,
    trusted_current_site: bool = False,
) -> tuple[str, str]:
    org_region, org_city = _split_region_city_from_address(demand_org_name)
    region = org_region or _normalize_tracker_region_value(current_site_region)
    parsed_region, parsed_city = _split_region_city_from_address(current_site_city)
    if not region and parsed_region:
        region = parsed_region
    client_region, client_city = _split_region_city_from_address(current_client_location)
    if not region and client_region:
        region = client_region
    if not region:
        region = _infer_tracker_region_from_text(current_site_city, current_client_location, demand_org_name)

    normalized_org_city = _normalize_tracker_site_city_candidate(
        org_city,
        region=region,
        demand_org_name=demand_org_name,
        project_name="",
    )
    if not normalized_org_city and str(demand_org_name or "").strip():
        normalized_org_city = _normalize_tracker_site_city_candidate(
            infer_city_from_org_or_project(demand_org_name, ""),
            region=region,
            demand_org_name=demand_org_name,
            project_name="",
        )
    if str(demand_org_name or "").strip() and normalized_org_city:
        return region, normalized_org_city

    if str(demand_org_name or "").strip():
        candidate_values = []
        if trusted_current_site:
            candidate_values.extend(
                [
                    (parsed_city, 2),
                    (current_site_city, 1),
                ]
            )
    else:
        candidate_values = [
            (parsed_city, 2),
            (current_site_city, 1),
            (client_city, 2),
            (infer_city_from_org_or_project(current_site_city, ""), 0),
            (infer_city_from_org_or_project(current_client_location, ""), 0),
        ]

    best_city = ""
    best_score = (-1, -1)
    for candidate, source_rank in candidate_values:
        normalized_city = _normalize_tracker_site_city_candidate(
            candidate,
            region=region,
            demand_org_name=demand_org_name,
            project_name=project_name,
        )
        if normalized_city:
            score = (_tracker_site_city_rank(normalized_city), int(source_rank))
            if score > best_score:
                best_city = normalized_city
                best_score = score
    return region, best_city


def _resolve_tracker_client_location(
    *,
    current_client_location: str,
    demand_org_name: str,
    project_name: str,
    site_region: str,
    site_city: str,
) -> str:
    demand_org = str(demand_org_name or "").strip()
    if demand_org:
        return demand_org
    current = str(current_client_location or "").strip()
    if current:
        return current
    region = infer_region_from_org(demand_org_name) or str(site_region or "").strip()
    city = infer_city_from_org_or_project(demand_org_name, project_name) or str(site_city or "").strip()
    if region and city:
        return f"{region} {city}"
    return city or region


def _format_construction_period(
    *,
    contract_date: str,
    duration_days: str,
    fallback_value: str,
    completion_expected_date_explicit: str = "",
    completion_expected_date_computed: str = "",
    source_type: str = "",
) -> str:
    try:
        days = int(str(duration_days or "").strip() or "0")
    except Exception:
        days = 0
    completion_value = str(completion_expected_date_explicit or completion_expected_date_computed or "").strip()
    base_value = str(fallback_value or "").strip()
    trusted_completion_source = str(source_type or "").strip() in TRACKER_TRUSTED_COMPLETION_SOURCE_TYPES
    duration_only_period = _format_notice_duration_period(days)
    if duration_only_period and not str(contract_date or "").strip() and (
        not base_value or _base_period_conflicts_with_duration(base_value=base_value, duration_days=days)
    ):
        period = duration_only_period
        if completion_value and "완료예정" not in period:
            return f"{period} (완료예정 {completion_value})"
        return period
    if days <= 0 or not trusted_completion_source:
        if base_value and completion_value and "완료예정" not in base_value:
            return f"{base_value} (완료예정 {completion_value})"
        return base_value
    date_text = str(contract_date or "").strip()
    if not date_text:
        period = base_value or f"\ucc29\uc218\uc77c\ub85c\ubd80\ud130 {days}\uc77c"
        if completion_value and "완료예정" not in period:
            return f"{period} (완료예정 {completion_value})"
        return period
    match = re.search(r"(\d{4})[-./]?(\d{2})[-./]?(\d{2})", date_text)
    if not match:
        period = f"\uacc4\uc57d\uc77c {date_text} \uae30\uc900 {days}\uc77c"
        if completion_value and "완료예정" not in period:
            return f"{period} (완료예정 {completion_value})"
        return period
    year, month, day = map(int, match.groups())
    try:
        from datetime import datetime, timedelta

        start = datetime(year, month, day)
        due = start + timedelta(days=days)
        completion_display = completion_value or due.strftime("%Y-%m-%d")
        return (
            f"\uacc4\uc57d\uc77c {start.strftime('%Y-%m-%d')} \uae30\uc900 {days}\uc77c "
            f"(\uc644\ub8cc\uc608\uc815 {completion_display})"
        )
    except Exception:
        period = f"\uacc4\uc57d\uc77c {date_text} \uae30\uc900 {days}\uc77c"
        if completion_value and "완료예정" not in period:
            return f"{period} (완료예정 {completion_value})"
        return period


def _format_notice_duration_period(days: int) -> str:
    if days < 30:
        return ""
    return f"\ucc29\uc218\uc77c\ub85c\ubd80\ud130{days}\uc77c"


def _base_period_conflicts_with_duration(*, base_value: str, duration_days: int) -> bool:
    if duration_days < 30:
        return False
    match = re.search(r"(\d{1,4})\s*일", str(base_value or ""))
    if not match:
        return False
    try:
        base_days = int(match.group(1))
    except Exception:
        return False
    return base_days != duration_days


def _is_region_only_org_name(org_name: str) -> bool:
    org = str(org_name or "").strip()
    if not org:
        return False
    if any(token in org for token in INVALID_CITY_LOCATION_TOKENS):
        return False
    region = infer_region_from_org(org)
    if not region:
        return False
    org_compact = _norm_text(org)
    region_compact = _norm_text(region)
    idx = org_compact.find(region_compact)
    if idx < 0:
        return False
    tail = org_compact[idx + len(region_compact) :]
    tail = re.sub(r"(교육청|도청|시청|군청|구청|소방본부|소방서|교육지원청)$", "", tail)
    if not tail:
        return True
    if re.search(r"[가-힣a-z0-9]{2,20}(?:시|군|구)", tail):
        return False
    return True



def _build_progress_note(
    *,
    reason_code: str,
    seed_meta: dict[str, str],
    fallback_values: list[tuple[str, str, str]],
) -> str:
    parts: list[str] = []
    if reason_code:
        parts.append(reason_code)
    for field_name, value, source in fallback_values:
        normalized_value = str(value or "").strip()
        normalized_source = str(source or "").strip()
        if not normalized_value or not normalized_source.startswith("fallback"):
            continue
        parts.append(f"{field_name}<{normalized_source}>={normalized_value}")
    spec_doc = str(seed_meta.get("spec_doc_file_name_1") or "").strip()
    if spec_doc:
        parts.append(spec_doc)
    return _join_non_empty(parts, " | ")

def _load_existing_tracker_defaults() -> dict[str, dict[str, str]]:
    if str(os.getenv("TRACKER_MERGE_EXISTING_DEFAULTS", "1")).strip().lower() in {"0", "false", "n", "no"}:
        return {}
    from .artifact_files import read_tracking_workbook_rows

    merged: dict[str, dict[str, str]] = {}
    for path in _iter_default_workbook_candidates():
        try:
            rows = read_tracking_workbook_rows(path)
        except Exception:
            continue
        for row in rows:
            project_key = _norm_text(str(row.get("project_name") or "").strip())
            if not project_key:
                continue
            slot = merged.setdefault(project_key, {})
            for field in (
                "gross_area_scale",
                "demand_org_name",
                "demand_contact",
                "client_location",
                "site_location_1",
                "site_location_2",
                "architect_office",
                "manager_name",
            ):
                slot[field] = _pick_best_text(slot.get(field), row.get(field))
    return merged


def _iter_default_workbook_candidates() -> list[Path]:
    raw = str(os.getenv("TRACKER_DEFAULT_WORKBOOK_PATHS", "")).strip()
    candidates: list[Path] = []
    seen: set[str] = set()

    def _push(path: Path) -> None:
        try:
            resolved = str(path.resolve())
        except Exception:
            resolved = str(path)
        if resolved in seen:
            return
        seen.add(resolved)
        if path.exists() and path.is_file() and not path.name.startswith("~$"):
            candidates.append(path)

    if raw:
        for chunk in raw.split(os.pathsep):
            value = str(chunk or "").strip()
            if not value:
                continue
            _push(Path(value).expanduser())
        return candidates

    repo_root = Path(__file__).resolve().parents[2]
    gui_root = repo_root.parent / "notice-winner-pipeline-project"
    for path in sorted((gui_root / "output").glob("프로젝트_트랙커_*.xlsx"), key=lambda item: item.stat().st_mtime, reverse=True):
        _push(path)
    for path in (
        gui_root / "프로젝트 트랙커 양식.xlsx",
        gui_root / "프로젝트_트랙커_채움.xlsx",
    ):
        _push(path)
    return candidates


def _pick_best_text(*values: Any) -> str:
    best = ""
    best_score = -1
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        score = 0
        if not _looks_corrupted_text(text):
            score += 5
        if re.search(r"[가-힣]", text):
            score += 3
        score += min(len(text), 60) // 20
        if score > best_score:
            best = text
            best_score = score
    return best


def _looks_corrupted_text(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if "�" in text:
        return True
    if text.count("?") >= 2 and not re.search(r"[가-힣]", text):
        return True
    return False


def _native_tracker_amounts_safe_value(value: Any, source: Any) -> str:
    return _tracker_safe_value(value, source)


def _normalize_tracker_gross_area(*, project_name: str, value: Any, source: Any) -> str:
    return normalize_tracker_gross_area(
        project_name=project_name,
        value=value,
        source=source,
        safe_value_resolver=_native_tracker_amounts_safe_value,
    )


def _resolve_tracker_construction_cost(
    *,
    notice_construction_cost: Any,
    notice_construction_cost_source: Any,
    contract_amount: Any,
    contract_amount_source: Any,
    source_type: Any,
    project_name: str,
) -> str:
    return resolve_tracker_construction_cost(
        notice_construction_cost=notice_construction_cost,
        notice_construction_cost_source=notice_construction_cost_source,
        contract_amount=contract_amount,
        contract_amount_source=contract_amount_source,
        source_type=source_type,
        project_name=project_name,
        safe_value_resolver=_native_tracker_amounts_safe_value,
    )


def _format_tracker_cost_value(value: Any, source: Any, *, project_name: str = "") -> str:
    return format_tracker_cost_value(
        value,
        source,
        project_name=project_name,
        safe_value_resolver=_native_tracker_amounts_safe_value,
    )


_parse_tracker_cost_to_won = parse_tracker_cost_to_won
_parse_tracker_area_value = parse_tracker_area_value
_looks_like_major_capex_project = looks_like_major_capex_project
_sanitize_tracker_construction_cost = sanitize_tracker_construction_cost
_estimate_building_automation_amount_from_cost = estimate_building_automation_amount_from_cost
_compute_completion_expected_date = compute_completion_expected_date
_format_eok_amount = format_eok_amount


def _split_region_city_from_address(value: str) -> tuple[str, str]:
    return split_region_city_from_address(
        value,
        official_region_pattern=OFFICIAL_REGION_PATTERN,
        match_official_sigungu=match_official_sigungu,
    )


def _normalize_tracker_region_value(value: str) -> str:
    return normalize_tracker_region_value(
        value,
        official_region_pattern=OFFICIAL_REGION_PATTERN,
        tracker_region_aliases=TRACKER_REGION_ALIASES,
        tracker_region_token_only_canonicals=TRACKER_REGION_TOKEN_ONLY_CANONICALS,
    )


def _infer_tracker_region_from_text(*values: str) -> str:
    return infer_tracker_region_from_text(
        *values,
        official_region_pattern=OFFICIAL_REGION_PATTERN,
        tracker_region_aliases=TRACKER_REGION_ALIASES,
        tracker_region_token_only_canonicals=TRACKER_REGION_TOKEN_ONLY_CANONICALS,
    )


def _tracker_region_official_name(canonical: str) -> str:
    return tracker_region_official_name(
        canonical,
        tracker_region_aliases=TRACKER_REGION_ALIASES,
    )


def _normalize_tracker_site_city_candidate(
    candidate: str,
    *,
    region: str,
    demand_org_name: str,
    project_name: str,
) -> str:
    return normalize_tracker_site_city_candidate(
        candidate,
        region=region,
        tracker_region_aliases=TRACKER_REGION_ALIASES,
        tracker_site_city_noise_exact=TRACKER_SITE_CITY_NOISE_EXACT,
        tracker_site_city_noise_parts=TRACKER_SITE_CITY_NOISE_PARTS,
        invalid_city_location_tokens=INVALID_CITY_LOCATION_TOKENS,
        match_official_sigungu=match_official_sigungu,
    )


_tracker_site_city_rank = tracker_site_city_rank


def _normalize_tracker_contact(value: str, *, allow_person_only: bool = False) -> str:
    return normalize_tracker_contact(
        value,
        allow_person_only=allow_person_only,
        normalize_contact_candidate_fn=normalize_contact_candidate,
        dept_suffixes=TRACKER_CONTACT_DEPT_SUFFIXES,
        dept_sentence_noise_pat=CONTACT_DEPT_SENTENCE_NOISE_PAT,
        other_sentence_fragment_pat=CONTACT_OTHER_SENTENCE_FRAGMENT_PAT,
    )


def _normalize_tracker_contact_person_only(value: str) -> str:
    return normalize_tracker_contact_person_only(
        value,
        dept_sentence_noise_pat=CONTACT_DEPT_SENTENCE_NOISE_PAT,
        other_sentence_fragment_pat=CONTACT_OTHER_SENTENCE_FRAGMENT_PAT,
    )


def _extract_tracker_contact_dept(value: str) -> str:
    return extract_tracker_contact_dept(
        value,
        dept_suffixes=TRACKER_CONTACT_DEPT_SUFFIXES,
    )


_normalize_phone = normalize_phone
