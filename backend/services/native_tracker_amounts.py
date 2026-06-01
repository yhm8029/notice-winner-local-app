from __future__ import annotations

import re
from typing import Any

from .native_gui_rules import is_auxiliary_service_project
from .native_gui_rules import is_building_like_project
from ..repositories.tracker_entries import (
    estimate_tracker_building_automation_amount as _estimate_tracker_building_automation_amount,
)


TRACKER_TRUSTED_COST_SOURCE_TYPES = frozenset({"g2b_contract_api", "lofin_api", "eais_web"})
TRACKER_TRUSTED_COMPLETION_SOURCE_TYPES = frozenset({"g2b_contract_api", "lofin_api"})


def parse_tracker_cost_to_won(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    eok_match = re.search(r"([0-9][0-9,]*(?:\.\d+)?)\s*억원", text.replace(" ", ""))
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


def parse_tracker_area_value(value: Any) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    match = re.search(r"([0-9][0-9,]*(?:\.\d+)?)", text)
    if not match:
        return 0.0
    try:
        return float(match.group(1).replace(",", ""))
    except Exception:
        return 0.0


def format_eok_amount(won: int) -> str:
    if int(won or 0) <= 0:
        return ""
    eok = round(float(won) / 100000000.0, 2)
    text = f"{eok:.2f}".rstrip("0").rstrip(".")
    return f"{text}억원"


def format_tracker_cost_value(
    value: Any,
    source: Any,
    *,
    project_name: str = "",
    safe_value_resolver,
) -> str:
    if is_auxiliary_service_project(project_name):
        return ""
    raw = safe_value_resolver(value, source)
    if not raw:
        return ""
    won = parse_tracker_cost_to_won(raw)
    if won <= 0:
        return raw
    return format_eok_amount(won)


def normalize_tracker_gross_area(
    *,
    project_name: str,
    value: Any,
    source: Any,
    safe_value_resolver,
) -> str:
    raw = safe_value_resolver(value, source)
    if not raw:
        return ""
    area_value = parse_tracker_area_value(raw)
    if is_auxiliary_service_project(project_name):
        return ""
    if is_building_like_project(project_name) and 0 < area_value < 50:
        return ""
    return raw


def looks_like_major_capex_project(project_name: str) -> bool:
    text = str(project_name or "")
    return any(
        token in text
        for token in (
            "건립",
            "신축",
            "증축",
            "개축",
            "리모델링",
            "공간재구조화",
            "조성",
            "이전",
            "복합센터",
            "청사",
            "도서관",
            "학교",
            "센터",
            "회관",
        )
    )


def format_tracker_cost_candidate(value: Any, *, project_name: str = "") -> str:
    if is_auxiliary_service_project(project_name):
        return ""
    won = parse_tracker_cost_to_won(value)
    if won <= 0:
        return ""
    return format_eok_amount(won)


def sanitize_tracker_construction_cost(*, project_name: str, cost_value: str, gross_area_scale: str) -> str:
    text = str(cost_value or "").strip()
    if not text:
        return ""
    if is_auxiliary_service_project(project_name):
        return ""
    won = parse_tracker_cost_to_won(text)
    area_value = parse_tracker_area_value(gross_area_scale)
    if looks_like_major_capex_project(project_name) and area_value >= 1000 and 0 < won <= 100000000:
        return ""
    return text


def resolve_tracker_construction_cost(
    *,
    notice_construction_cost: Any,
    notice_construction_cost_source: Any,
    contract_amount: Any,
    contract_amount_source: Any,
    source_type: Any,
    project_name: str,
    safe_value_resolver,
) -> str:
    notice_value = format_tracker_cost_value(
        notice_construction_cost,
        notice_construction_cost_source,
        project_name=project_name,
        safe_value_resolver=safe_value_resolver,
    )
    if notice_value:
        return notice_value
    source_type_text = str(source_type or "").strip()
    contract_source_text = str(contract_amount_source or "").strip()
    if (
        source_type_text in TRACKER_TRUSTED_COST_SOURCE_TYPES
        and contract_source_text.startswith("confirmed")
    ):
        return format_tracker_cost_candidate(contract_amount, project_name=project_name)
    return ""


def estimate_building_automation_amount_from_cost(construction_cost: Any) -> str:
    return _estimate_tracker_building_automation_amount(construction_cost)


def compute_completion_expected_date(*, contract_date: str, duration_days: str, source_type: str) -> str:
    if str(source_type or "").strip() not in TRACKER_TRUSTED_COMPLETION_SOURCE_TYPES:
        return ""
    try:
        days = int(str(duration_days or "").strip() or "0")
    except Exception:
        days = 0
    if days <= 0:
        return ""
    match = re.search(r"(\d{4})[-./]?(\d{2})[-./]?(\d{2})", str(contract_date or "").strip())
    if not match:
        return ""
    try:
        from datetime import datetime
        from datetime import timedelta

        start = datetime(*map(int, match.groups()))
        return (start + timedelta(days=days)).strftime("%Y-%m-%d")
    except Exception:
        return ""
