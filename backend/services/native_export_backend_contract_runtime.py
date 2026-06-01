from __future__ import annotations

import re

from ..repositories.tracker_entries import estimate_tracker_building_automation_amount as _estimate_tracker_building_automation_amount

_TRUSTED_CONSTRUCTION_COST_SOURCE_TYPES = frozenset({"g2b_contract_api", "lofin_api", "eais_web"})
_TRUSTED_COMPLETION_SOURCE_TYPES = frozenset({"g2b_contract_api", "lofin_api"})


def resolve_contract_source_type(contract_hit: object, winner_name: str) -> str:
    if not contract_hit or not str(winner_name or "").strip():
        return "native_web"
    return str(getattr(contract_hit, "source_type", "") or "").strip() or "g2b_contract_api"


def resolve_contract_status(*, contract_hit: object, winner_name: str, g2b_verified: str) -> str:
    if not str(winner_name or "").strip():
        return "REVIEW"
    if not contract_hit:
        return "FOUND"
    source_type = str(getattr(contract_hit, "source_type", "") or "").strip()
    match_score = float(getattr(contract_hit, "match_score", 0.0) or 0.0)
    is_verified = str(g2b_verified or "").strip().upper() == "Y"
    if source_type == "lofin_api":
        return "FOUND" if is_verified and match_score >= 0.80 else "REVIEW"
    if source_type == "eais_web":
        return "FOUND" if is_verified and match_score >= 0.75 else "REVIEW"
    if source_type == "hub_result":
        return "FOUND" if match_score >= 0.70 else "REVIEW"
    return "FOUND"


def resolve_contract_score(contract_hit: object, winner_name: str) -> float:
    if not str(winner_name or "").strip():
        return 0.55
    if not contract_hit:
        return 0.90
    match_score = float(getattr(contract_hit, "match_score", 0.0) or 0.0)
    if match_score > 0:
        return min(1.0, max(0.55, match_score))
    return 0.95


def resolve_contract_reason_code(*, contract_hit: object, winner_name: str, g2b_verified: str, status: str) -> str:
    if not str(winner_name or "").strip():
        return "NATIVE_REVIEW_REQUIRED"
    if not contract_hit:
        return "NATIVE_WEB_MATCH"
    source_type = str(getattr(contract_hit, "source_type", "") or "").strip()
    if source_type == "g2b_contract_api":
        return "G2B_CONTRACT_CONFIRMED"
    if source_type == "lofin_api":
        return "LOFIN_CONTRACT_STRONG_MATCH" if status == "FOUND" else "LOFIN_CONTRACT_MATCH_NEEDS_RECHECK"
    if source_type == "eais_web":
        return "EAIS_CONTRACT_MATCH" if status == "FOUND" else "EAIS_CONTRACT_MATCH_NEEDS_RECHECK"
    if source_type == "hub_result":
        return "HUB_RESULT_MATCH" if status == "FOUND" else "HUB_RESULT_MATCH_NEEDS_RECHECK"
    return "NATIVE_WEB_MATCH" if str(g2b_verified or "").strip().upper() == "Y" else "NATIVE_REVIEW_REQUIRED"


def resolve_contract_winner_pattern(contract_hit: object, winner_name: str, extracted_pattern: str) -> str:
    if contract_hit and str(winner_name or "").strip():
        source_type = str(getattr(contract_hit, "source_type", "") or "").strip()
        if source_type == "lofin_api":
            return "LOFIN_API:cltNm"
        if source_type == "eais_web":
            return "EAIS_API:list+detail"
        if source_type == "hub_result":
            return "HUB_RESULT:prwinPdtList"
        return "G2B_CONTRACT_API:corpList"
    return str(extracted_pattern or "").strip()


def resolve_contract_evidence(contract_hit: object, winner_name: str) -> str:
    if not contract_hit or not str(winner_name or "").strip():
        return "native_web"
    source_type = str(getattr(contract_hit, "source_type", "") or "").strip()
    target_name = str(getattr(contract_hit, "target_name", "") or "").strip()
    inst_name = str(getattr(contract_hit, "inst_name", "") or "").strip()
    if source_type == "lofin_api":
        return f"lofin:{target_name}|{inst_name}"[:200]
    if source_type == "eais_web":
        return f"eais:{target_name}|{inst_name}"[:200]
    if source_type == "hub_result":
        return f"hub:{target_name}|{inst_name}"[:200]
    return f"g2b_contract:{target_name}|{inst_name}"[:200]


def resolve_contract_hit_note(contract_hit: object, winner_name: str) -> str:
    if not contract_hit or not str(winner_name or "").strip():
        return ""
    source_type = str(getattr(contract_hit, "source_type", "") or "").strip()
    if source_type == "lofin_api":
        return "lofin_contract_hit"
    if source_type == "eais_web":
        return "eais_contract_hit"
    if source_type == "hub_result":
        return "hub_result_hit"
    return "g2b_contract_hit"


def format_eok_amount(won: int) -> str:
    if int(won or 0) <= 0:
        return ""
    eok = round(float(won) / 100000000.0, 2)
    return f"{eok:.2f}".rstrip("0").rstrip(".") + "?듭썝"


def select_building_automation_cost_candidate(*, notice_construction_cost, contract_amount, contract_source_type: str) -> tuple[str, str]:
    notice_value = str(notice_construction_cost.value or "").strip()
    if notice_value:
        return notice_value, "notice_construction_cost"
    contract_value = str(contract_amount.value or "").strip()
    contract_source = str(contract_amount.source or "").strip()
    if (
        contract_value
        and contract_source.startswith("confirmed")
        and str(contract_source_type or "").strip() in _TRUSTED_CONSTRUCTION_COST_SOURCE_TYPES
    ):
        return contract_value, "contract_amount"
    return "", ""


def compute_completion_expected_date(*, contract_date: str, duration_days: str, contract_source_type: str) -> str:
    if str(contract_source_type or "").strip() not in _TRUSTED_COMPLETION_SOURCE_TYPES:
        return ""
    try:
        days = int(str(duration_days or "").strip() or "0")
    except Exception:
        days = 0
    if days <= 0:
        return ""
    date_text = str(contract_date or "").strip()
    match = re.search(r"(\d{4})[-./]?(\d{2})[-./]?(\d{2})", date_text)
    if not match:
        return ""
    try:
        from datetime import datetime
        from datetime import timedelta

        start = datetime(*map(int, match.groups()))
        return (start + timedelta(days=days)).strftime("%Y-%m-%d")
    except Exception:
        return ""


def resolve_building_automation_amount(*, explicit_value: str, construction_cost_candidate: str, candidate_label: str, resolved_field_cls):
    explicit = str(explicit_value or "").strip()
    if explicit:
        return resolved_field_cls(value=explicit, source="confirmed_extracted")
    if construction_cost_candidate:
        estimated = _estimate_tracker_building_automation_amount(construction_cost_candidate)
        if estimated:
            suffix = str(candidate_label or "construction_cost").strip()
            return resolved_field_cls(value=estimated, source=f"estimated_{suffix}")
    return resolved_field_cls()


def build_fallback_notes(fields: dict[str, object]) -> list[str]:
    notes: list[str] = []
    for field_name, field in fields.items():
        value = str(getattr(field, "value", "") or "").strip()
        source = str(getattr(field, "source", "") or "").strip()
        if value and source.startswith("fallback"):
            notes.append(f"{field_name}={source}")
    return notes
