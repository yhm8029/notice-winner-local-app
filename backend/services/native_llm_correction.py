from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from typing import Callable

import requests

from .native_gui_rules import extract_area_number
from .native_gui_rules import extract_cost_won
from .native_gui_rules import format_area_number
from .native_gui_rules import format_won
from .native_gui_rules import is_building_like_project
from .native_gui_rules import normalize_contact_candidate

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MODEL_FALLBACKS = {
    "claude-3-5-haiku-latest": DEFAULT_MODEL,
}
GENERIC_CONTACT_DEPT_EXACT = {
    "\ubb38\uc758",
    "\ubb38\uc758\ucc98",
    "\ubb38\uc758\uc0ac\ud56d",
    "\uae30\ud0c0\ubb38\uc758\uc0ac\ud56d",
    "\uc5f0\ub77d\ucc98",
    "\uc804\ud654",
    "\ubb38\uc758\uc804\ud654",
    "\ub2f4\ub2f9",
    "\ub2f4\ub2f9\uc790",
    "\ub2f4\ub2f9\ubd80\uc11c",
    "\uacf5\ubaa8\ub2f4\ub2f9",
    "\uc124\uacc4\uacf5\ubaa8\ub2f4\ub2f9",
    "\uacf5\ubaa8\ub2f4\ub2f9\uc790",
    "\uc124\uacc4\uacf5\ubaa8\ub2f4\ub2f9\uc790",
}


@dataclass(frozen=True)
class LlmCorrectionConfig:
    enabled: bool
    api_key: str
    model: str
    max_rows: int
    max_chars: int


@dataclass(frozen=True)
class LlmCorrectionResult:
    area: str = ""
    cost: str = ""
    contact: str = ""
    corrected_fields: tuple[str, ...] = ()


def load_llm_correction_config() -> LlmCorrectionConfig:
    return load_llm_correction_config_from_options({})


def load_llm_correction_config_from_options(options: dict[str, Any] | None) -> LlmCorrectionConfig:
    advanced = dict(options or {})
    enabled = str(os.getenv("TRACKER_LLM_CORRECT") or "").strip().lower() in {"1", "true", "y", "yes"}
    if "llm_correct" in advanced:
        enabled = str(advanced.get("llm_correct") or "").strip().lower() in {"1", "true", "y", "yes"}
    api_key = str(os.getenv("ANTHROPIC_API_KEY") or "").strip()
    if str(advanced.get("anthropic_key") or "").strip():
        api_key = str(advanced.get("anthropic_key") or "").strip()
    model = str(os.getenv("TRACKER_LLM_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if str(advanced.get("llm_model") or "").strip():
        model = str(advanced.get("llm_model") or "").strip()
    try:
        max_rows = int(str(os.getenv("TRACKER_LLM_MAX_ROWS") or "20").strip())
    except Exception:
        max_rows = 20
    if str(advanced.get("llm_max_rows") or "").strip():
        try:
            max_rows = int(str(advanced.get("llm_max_rows") or "").strip())
        except Exception:
            pass
    try:
        max_chars = int(str(os.getenv("TRACKER_LLM_MAX_CHARS") or "12000").strip())
    except Exception:
        max_chars = 12000
    if str(advanced.get("llm_max_chars") or "").strip():
        try:
            max_chars = int(str(advanced.get("llm_max_chars") or "").strip())
        except Exception:
            pass
    return LlmCorrectionConfig(
        enabled=bool(enabled and api_key and model),
        api_key=api_key,
        model=model,
        max_rows=max(0, max_rows),
        max_chars=max(2000, min(max_chars, 40000)),
    )


def maybe_correct_notice_fields_with_llm(
    *,
    config: LlmCorrectionConfig,
    text: str,
    project_name: str,
    org_name: str,
    area: str,
    cost: str,
    contact: str,
    request_fn: Callable[..., Any] | None = None,
) -> LlmCorrectionResult:
    if not config.enabled:
        return LlmCorrectionResult()
    normalized_text = _normalize_source_text(text, max_chars=config.max_chars)
    if not normalized_text:
        return LlmCorrectionResult()

    need_area = _needs_area_llm(area=area, project_name=project_name)
    need_cost = not bool(str(cost or "").strip())
    need_contact = _needs_contact_llm(contact=contact)
    if not (need_area or need_cost or need_contact):
        return LlmCorrectionResult()

    payload = _call_anthropic_json(
        api_key=config.api_key,
        model=config.model,
        notice_text=normalized_text,
        project_name=project_name,
        org_name=org_name,
        need_area=need_area,
        need_cost=need_cost,
        need_contact=need_contact,
        request_fn=request_fn or requests.post,
    )
    if not payload:
        return LlmCorrectionResult()

    corrected_fields: list[str] = []
    corrected_area = ""
    corrected_cost = ""
    corrected_contact = ""

    if need_area:
        corrected_area = _validate_area(str(payload.get("area") or "").strip(), project_name=project_name)
        if corrected_area:
            corrected_fields.append("area")
    if need_cost:
        corrected_cost = _validate_cost(str(payload.get("cost") or "").strip())
        if corrected_cost:
            corrected_fields.append("cost")
    if need_contact:
        corrected_contact = _validate_contact(str(payload.get("contact") or "").strip(), org_name=org_name)
        if corrected_contact:
            corrected_fields.append("contact")

    return LlmCorrectionResult(
        area=corrected_area,
        cost=corrected_cost,
        contact=corrected_contact,
        corrected_fields=tuple(sorted(corrected_fields)),
    )


def _call_anthropic_json(
    *,
    api_key: str,
    model: str,
    notice_text: str,
    project_name: str,
    org_name: str,
    need_area: bool,
    need_cost: bool,
    need_contact: bool,
    request_fn: Callable[..., Any],
) -> dict[str, Any]:
    system_prompt = (
        "You extract missing fields from a Korean public architecture notice. "
        "Reply with exactly one JSON object and no extra text."
    )
    user_prompt = (
        "Review the notice text below and fill only the requested fields.\n"
        f"- project_name: {project_name}\n"
        f"- org_name: {org_name}\n"
        f"- need_area: {int(need_area)}\n"
        f"- need_cost: {int(need_cost)}\n"
        f"- need_contact: {int(need_contact)}\n"
        "Use only these JSON keys: area, cost, contact.\n"
        "Rules:\n"
        "1. If the notice does not support a field, return an empty string for that field.\n"
        "2. area format: '2,450㎡'.\n"
        "3. cost format: '547,520,000원'.\n"
        "4. contact format: 'department/phone' or 'organization/phone'. Exclude person names and titles.\n"
        "5. Output JSON only.\n\n"
        f"{notice_text}"
    )
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    for candidate_model in _iter_candidate_models(model):
        body = {
            "model": candidate_model,
            "max_tokens": 300,
            "temperature": 0,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        try:
            response = request_fn(ANTHROPIC_API_URL, headers=headers, json=body, timeout=30)
        except Exception:
            return {}

        try:
            data = response.json()
        except Exception:
            data = {}

        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code >= 400:
            if _is_model_not_found_error(data):
                continue
            try:
                response.raise_for_status()
            except Exception:
                return {}
            return {}

        try:
            response.raise_for_status()
        except Exception:
            return {}

        parts = data.get("content") or []
        text_parts: list[str] = []
        for part in parts:
            if str((part or {}).get("type") or "") == "text":
                text_parts.append(str((part or {}).get("text") or ""))
        raw_text = "\n".join(text_parts).strip()
        payload = _parse_json_object(raw_text)
        if payload:
            return payload
    return {}


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return {}
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _normalize_source_text(text: str, *, max_chars: int) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in str(text or "").splitlines()]
    compact = "\n".join(line for line in lines if line)
    return compact[:max_chars].strip()


def _needs_area_llm(*, area: str, project_name: str) -> bool:
    normalized_area = str(area or "").strip()
    if not normalized_area:
        return True
    if not is_building_like_project(project_name):
        return False
    return 0 < extract_area_number(normalized_area) < 100


def _validate_area(value: str, *, project_name: str) -> str:
    area_num = extract_area_number(value)
    if area_num <= 0:
        return ""
    if is_building_like_project(project_name) and area_num < 100:
        return ""
    return format_area_number(area_num)


def _validate_cost(value: str) -> str:
    won = extract_cost_won(value)
    if won < 100000000:
        return ""
    return format_won(won)


def _validate_contact(value: str, *, org_name: str) -> str:
    return normalize_contact_candidate(value, org_name)


def _needs_contact_llm(*, contact: str) -> bool:
    normalized = str(contact or "").strip()
    if not normalized:
        return True
    if "/" not in normalized:
        return True
    dept = str(normalized.split("/", 1)[0] or "").strip()
    dept_norm = re.sub(r"\s+", "", dept)
    if not dept_norm:
        return True
    if len(dept_norm) <= 2:
        return True
    if _looks_like_generic_contact_dept(dept):
        return True
    return False


def _looks_like_generic_contact_dept(dept: str) -> bool:
    normalized = re.sub(r"[^0-9A-Za-z\uac00-\ud7a3]", "", str(dept or "")).lower()
    if not normalized:
        return True
    if normalized in GENERIC_CONTACT_DEPT_EXACT:
        return True
    if re.fullmatch(r"(?:\uacf5\ubaa8|\uc124\uacc4\uacf5\ubaa8)(?:\ubb38\uc758|\ub2f4\ub2f9|\ub2f4\ub2f9\uc790)", normalized):
        return True
    return False


def _iter_candidate_models(model: str) -> list[str]:
    selected = str(model or "").strip() or DEFAULT_MODEL
    candidates = [selected]
    fallback = str(MODEL_FALLBACKS.get(selected) or "").strip()
    if fallback and fallback not in candidates:
        candidates.append(fallback)
    return candidates


def _is_model_not_found_error(payload: dict[str, Any]) -> bool:
    error = payload.get("error") if isinstance(payload, dict) else {}
    if not isinstance(error, dict):
        return False
    return str(error.get("type") or "").strip() == "not_found_error"
