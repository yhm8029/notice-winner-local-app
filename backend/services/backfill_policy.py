from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

SAFE_BACKFILL_FIELDS = ("gross_area_scale", "construction_cost", "demand_contact")
SAFE_BACKFILL_TRUSTED_SOURCE_TYPES = frozenset({"g2b_contract_api", "lofin_api", "eais_web", "hub_result"})
SUSPICIOUS_CONTACT_PLACEHOLDERS = (
    "-",
    "없음",
    "미상",
    "문의",
    "홈페이지참조",
    "공모전kr",
    "공모전.kr",
    "마실와이드",
    "02-6010-1022",
)


@dataclass(frozen=True)
class BackfillDecision:
    action: str
    reason_code: str
    current_norm: str
    candidate_norm: str


def _is_blankish(value: Any) -> bool:
    text = str(value or "").strip()
    return not text or text == "-"


def _normalize_digits(value: str) -> str:
    return re.sub(r"[^0-9]", "", str(value or ""))


def normalize_area_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.search(r"([0-9][0-9,]*(?:\.\d+)?)", text)
    if not match:
        return ""
    try:
        return f"{float(match.group(1).replace(',', '')):.4f}".rstrip("0").rstrip(".")
    except Exception:
        return ""


def normalize_cost_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    eok_match = re.search(r"([0-9][0-9,]*(?:\.\d+)?)\s*억원", text.replace(" ", ""))
    if eok_match:
        try:
            return str(int(round(float(eok_match.group(1).replace(",", "")) * 100000000)))
        except Exception:
            return ""
    digits = _normalize_digits(text)
    if not digits:
        return ""
    try:
        won = int(digits)
    except Exception:
        return ""
    return str(won) if won > 0 else ""


def _normalize_email(value: str) -> str:
    match = re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", str(value or ""), flags=re.IGNORECASE)
    return str(match.group(1) if match else "").strip().lower()


def _normalize_phone(value: str) -> str:
    digits = _normalize_digits(value)
    if len(digits) < 9:
        return ""
    return digits


def normalize_contact_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    email = _normalize_email(text)
    phone = _normalize_phone(text)
    if email:
        return f"email:{email}"
    if phone:
        return f"phone:{phone}"
    return re.sub(r"\s+", " ", text).strip().lower()


def is_valid_contact_candidate(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if _normalize_email(text):
        return True
    if _normalize_phone(text):
        return True
    return bool(re.search(r"(담당|과|팀|실|센터|부서)", text))


def is_suspicious_contact_placeholder(value: Any) -> bool:
    text = re.sub(r"\s+", "", str(value or "").strip()).lower()
    if not text:
        return True
    normalized_phone = _normalize_phone(text)
    if _has_structured_contact(text) and normalized_phone != "0260101022":
        return False
    return any(marker in text for marker in SUSPICIOUS_CONTACT_PLACEHOLDERS)


def _has_structured_contact(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if _normalize_email(text) or _normalize_phone(text):
        return True
    return "/" in text and bool(re.search(r"[가-힣A-Za-z]", text))


def _is_manual(entry: dict[str, Any] | None, field_name: str) -> bool:
    overridden = entry.get("overridden_fields") if isinstance(entry, dict) else []
    return field_name in (overridden or [])


def _candidate_is_trusted(source_type: str, source_ref: str) -> bool:
    source_type_text = str(source_type or "").strip()
    source_ref_text = str(source_ref or "").strip()
    return source_type_text in SAFE_BACKFILL_TRUSTED_SOURCE_TYPES or bool(source_ref_text)


def classify_gross_area_backfill(
    *,
    current_value: str,
    candidate_value: str,
    current_entry: dict[str, Any] | None = None,
    candidate_source_type: str = "",
    candidate_source_ref: str = "",
) -> BackfillDecision:
    current_norm = normalize_area_value(current_value)
    candidate_norm = normalize_area_value(candidate_value)
    candidate_is_trusted = _candidate_is_trusted(candidate_source_type, candidate_source_ref)
    if _is_manual(current_entry, "gross_area_scale"):
        return BackfillDecision("skip", "manual_protected", current_norm, candidate_norm)
    if not candidate_norm:
        return BackfillDecision("skip", "candidate_unusable", current_norm, candidate_norm)
    if _is_blankish(current_value):
        return BackfillDecision("safe_fill_blank", "blank_or_unusable_current", current_norm, candidate_norm)
    if not current_norm:
        if candidate_is_trusted:
            return BackfillDecision("safe_replace_implausible_current", "implausible_current_unparseable", current_norm, candidate_norm)
        return BackfillDecision("review_conflict", "weak_candidate_conflict", current_norm, candidate_norm)
    if current_norm == candidate_norm:
        return BackfillDecision("noop", "semantic_same", current_norm, candidate_norm)
    if candidate_is_trusted:
        return BackfillDecision("review_conflict", "valid_nonblank_conflict", current_norm, candidate_norm)
    return BackfillDecision("review_conflict", "weak_candidate_conflict", current_norm, candidate_norm)


def classify_construction_cost_backfill(
    *,
    current_value: str,
    candidate_value: str,
    current_entry: dict[str, Any] | None = None,
    candidate_source_type: str = "",
    candidate_source_ref: str = "",
) -> BackfillDecision:
    current_norm = normalize_cost_value(current_value)
    candidate_norm = normalize_cost_value(candidate_value)
    candidate_is_trusted = _candidate_is_trusted(candidate_source_type, candidate_source_ref)
    if _is_manual(current_entry, "construction_cost"):
        return BackfillDecision("skip", "manual_protected", current_norm, candidate_norm)
    if not candidate_norm:
        return BackfillDecision("skip", "candidate_unusable", current_norm, candidate_norm)
    if _is_blankish(current_value):
        return BackfillDecision("safe_fill_blank", "blank_or_unusable_current", current_norm, candidate_norm)
    if not current_norm:
        if candidate_is_trusted:
            return BackfillDecision("safe_replace_implausible_current", "implausible_current_unparseable", current_norm, candidate_norm)
        return BackfillDecision("review_conflict", "weak_candidate_conflict", current_norm, candidate_norm)
    if current_norm == candidate_norm:
        return BackfillDecision("noop", "semantic_same", current_norm, candidate_norm)
    if candidate_is_trusted:
        return BackfillDecision("review_conflict", "valid_nonblank_conflict", current_norm, candidate_norm)
    return BackfillDecision("review_conflict", "weak_candidate_conflict", current_norm, candidate_norm)


def classify_demand_contact_backfill(
    *,
    current_value: str,
    candidate_value: str,
    current_entry: dict[str, Any] | None = None,
    candidate_source_type: str = "",
    candidate_source_ref: str = "",
) -> BackfillDecision:
    current_norm = normalize_contact_value(current_value)
    candidate_norm = normalize_contact_value(candidate_value)
    candidate_is_trusted = _candidate_is_trusted(candidate_source_type, candidate_source_ref)
    if _is_manual(current_entry, "demand_contact"):
        return BackfillDecision("skip", "manual_protected", current_norm, candidate_norm)
    if not is_valid_contact_candidate(candidate_value):
        return BackfillDecision("skip", "candidate_unusable", current_norm, candidate_norm)
    if current_norm == candidate_norm and current_norm:
        return BackfillDecision("noop", "semantic_same", current_norm, candidate_norm)
    if _has_structured_contact(current_value) and not is_suspicious_contact_placeholder(current_value):
        return BackfillDecision("review_conflict", "valid_contact_protected", current_norm, candidate_norm)
    if _is_blankish(current_value) or is_suspicious_contact_placeholder(current_value):
        if not candidate_is_trusted:
            return BackfillDecision("review_conflict", "weak_candidate_contact", current_norm, candidate_norm)
        action = "safe_replace_implausible_current" if current_norm else "safe_fill_blank"
        return BackfillDecision(action, "blank_or_placeholder_current", current_norm, candidate_norm)
    return BackfillDecision("review_conflict", "valid_contact_protected", current_norm, candidate_norm)


def classify_safe_backfill(
    field_name: str,
    *,
    current_value: str,
    candidate_value: str,
    current_entry: dict[str, Any] | None = None,
    candidate_source_type: str = "",
    candidate_source_ref: str = "",
) -> BackfillDecision:
    if field_name == "gross_area_scale":
        return classify_gross_area_backfill(
            current_value=current_value,
            candidate_value=candidate_value,
            current_entry=current_entry,
            candidate_source_type=candidate_source_type,
            candidate_source_ref=candidate_source_ref,
        )
    if field_name == "construction_cost":
        return classify_construction_cost_backfill(
            current_value=current_value,
            candidate_value=candidate_value,
            current_entry=current_entry,
            candidate_source_type=candidate_source_type,
            candidate_source_ref=candidate_source_ref,
        )
    if field_name == "demand_contact":
        return classify_demand_contact_backfill(
            current_value=current_value,
            candidate_value=candidate_value,
            current_entry=current_entry,
            candidate_source_type=candidate_source_type,
            candidate_source_ref=candidate_source_ref,
        )
    return BackfillDecision("skip", "field_not_supported", "", "")
