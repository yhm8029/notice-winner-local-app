from __future__ import annotations

from typing import Any


TRACKER_SOURCE_REASON_LABELS: dict[str, str] = {
    "confirmed_extracted": "첨부문서 직접 추출",
    "confirmed_contract_lookup": "계약조회 당선사 확정",
    "fallback_seed_contact": "seed 연락처 fallback",
    "fallback_winner_name": "당선사명 fallback",
    "fallback_contract_date": "계약일 fallback",
    "estimated_notice_construction_cost": "공사비 기반 추정",
    "fallback_notice_cost": "공고문 공사비 fallback",
}

TRACKER_CONTRACT_SOURCE_LABELS: dict[str, str] = {
    "g2b_contract_api": "G2B 계약",
    "lofin_api": "LOFIN",
    "eais_web": "EAIS",
    "hub_result": "HUB",
    "native_web": "native_web",
}

TRACKER_MISSING_REASON_EXPLAINERS: dict[str, str] = {
    "구버전 run": "현재 코드로 다시 처리하면 채워질 가능성이 있는 예전 결과입니다.",
    "정상 빈값": "이 공고 유형에서는 해당 필드가 없어도 정상입니다.",
    "source 없음": "허용 source(EAIS/LOFIN/HUB/G2B)에서 해당 필드 후보를 찾지 못했습니다.",
    "query miss": "허용 source 결과 흔적은 있지만 현재 규칙으로는 해당 필드를 확정하지 못했습니다.",
}

TRACKER_EXPECTED_BLANK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "architect_office": (
        "관리용역",
        "관리 용역",
        "통합관리용역",
        "운영 대행용역",
        "운영대행용역",
        "평가용역",
        "공모전 운영",
        "제안서평가용역",
        "심사용역",
    ),
    "gross_area_scale": (
        "관리용역",
        "관리 용역",
        "통합관리용역",
        "운영 대행용역",
        "운영대행용역",
        "평가용역",
        "공모전 운영",
        "제안서평가용역",
        "심사용역",
    ),
}

TRACKER_TRUSTED_SOURCE_TYPES = frozenset({"g2b_contract_api", "lofin_api", "eais_web", "hub_result"})


def _is_blank(value: Any) -> bool:
    text = str(value or "").strip()
    return not text or text == "-"


def _winner_row_has_allowed_source_signal(winner_row: dict[str, str] | None) -> bool:
    if winner_row is None:
        return False
    raw_source_type = str(winner_row.get("source_type") or "").strip()
    if raw_source_type in TRACKER_TRUSTED_SOURCE_TYPES:
        return True
    raw_reason_code = str(winner_row.get("reason_code") or "").strip().upper()
    if raw_reason_code.startswith(("G2B_", "LOFIN_", "EAIS_", "HUB_")):
        return True
    return bool(str(winner_row.get("evidence_source") or "").strip())


def _is_expected_blank_tracker_field(field_key: str, project_name: str) -> bool:
    title = str(project_name or "").strip()
    if not title:
        return False
    keywords = TRACKER_EXPECTED_BLANK_KEYWORDS.get(field_key, ())
    return any(keyword in title for keyword in keywords)


def _humanize_tracker_source_label(source_key: str) -> str:
    raw = str(source_key or "").strip()
    if not raw:
        return "source 없음"
    if raw == "manual_override":
        return "수동 보정"
    return TRACKER_SOURCE_REASON_LABELS.get(raw, raw)


def _humanize_contract_source_type(source_type: str) -> str:
    raw = str(source_type or "").strip()
    if not raw:
        return ""
    return TRACKER_CONTRACT_SOURCE_LABELS.get(raw, raw)


def _humanize_tracker_source_reason(
    *,
    field_key: str,
    winner_row: dict[str, str] | None,
    source_field_name: str,
) -> str:
    if winner_row is None:
        return "winner_csv 없음"

    raw_source = str(winner_row.get(source_field_name) or "").strip()
    raw_reason_code = str(winner_row.get("reason_code") or "").strip()
    raw_source_type = str(winner_row.get("source_type") or "").strip()
    parts: list[str] = []

    if raw_source:
        parts.append(TRACKER_SOURCE_REASON_LABELS.get(raw_source, raw_source))
    else:
        parts.append(f"{source_field_name} 없음")

    if field_key == "architect_office":
        winner_name = str(winner_row.get("winner_name") or "").strip()
        if winner_name:
            parts.append(f"winner_name={winner_name}")
    if raw_reason_code:
        parts.append(f"reason={raw_reason_code}")
    if raw_source_type:
        parts.append(f"source_type={raw_source_type}")
    return " | ".join(parts)


def classify_tracker_field_missing(
    *,
    field_key: str,
    project_name: str,
    winner_row: dict[str, str] | None,
    source_field_name: str,
) -> tuple[str, str]:
    if _is_expected_blank_tracker_field(field_key, project_name):
        return "정상 빈값", TRACKER_MISSING_REASON_EXPLAINERS["정상 빈값"]

    if winner_row is None:
        return "source 없음", TRACKER_MISSING_REASON_EXPLAINERS["source 없음"]

    raw_source = str(winner_row.get(source_field_name) or "").strip()
    raw_value_field = "notice_construction_cost" if field_key == "construction_cost" else field_key
    raw_value = str(winner_row.get(raw_value_field) or "").strip()
    if raw_source and raw_value and not raw_source.startswith("fallback_winner_name"):
        return "구버전 run", TRACKER_MISSING_REASON_EXPLAINERS["구버전 run"]

    if _winner_row_has_allowed_source_signal(winner_row):
        return "query miss", TRACKER_MISSING_REASON_EXPLAINERS["query miss"]

    return "source 없음", TRACKER_MISSING_REASON_EXPLAINERS["source 없음"]


def _derive_confidence(
    *,
    source_key: str,
    source_type: str,
    evidence_source: str,
    is_missing: bool,
    missing_reason_code: str,
    is_overridden: bool,
) -> str:
    if is_overridden:
        return "manual"
    if is_missing:
        if missing_reason_code == "정상 빈값":
            return "expected_blank"
        return "low"
    if source_key.startswith("confirmed"):
        return "high"
    if source_key.startswith("estimated"):
        return "medium"
    if source_key.startswith("fallback"):
        return "low"
    if source_type in TRACKER_TRUSTED_SOURCE_TYPES and evidence_source:
        return "medium"
    return "low"


def build_tracker_field_diagnostic(
    *,
    entry: dict[str, Any],
    winner_row: dict[str, str] | None,
    field_key: str,
    field_label: str,
    source_field_name: str,
) -> dict[str, Any]:
    overridden_fields = set(entry.get("overridden_fields") or [])
    is_overridden = field_key in overridden_fields
    current_value = str(entry.get(field_key) or "").strip()
    is_missing = _is_blank(current_value)
    raw_source_type = str((winner_row or {}).get("source_type") or "").strip()
    raw_reason_code = str((winner_row or {}).get("reason_code") or "").strip()
    raw_evidence_source = str((winner_row or {}).get("evidence_source") or "").strip()

    source_key = (
        "manual_override"
        if is_overridden
        else str((winner_row or {}).get(source_field_name) or "").strip()
    )
    source_reason = (
        "수동 보정이 현재 적용 중입니다."
        if source_key == "manual_override"
        else _humanize_tracker_source_reason(
            field_key=field_key,
            winner_row=winner_row,
            source_field_name=source_field_name,
        )
    )

    evidence_parts: list[str] = []
    if raw_evidence_source:
        evidence_parts.append(raw_evidence_source)
    raw_field_name = "notice_construction_cost" if field_key == "construction_cost" else field_key
    raw_field_value = str((winner_row or {}).get(raw_field_name) or "").strip()
    if raw_field_value:
        evidence_parts.append(f"value={raw_field_value}")
    if field_key == "architect_office":
        winner_name = str((winner_row or {}).get("winner_name") or "").strip()
        if winner_name:
            evidence_parts.append(f"winner_name={winner_name}")

    missing_reason_code = ""
    missing_reason = ""
    if is_missing:
        missing_reason_code, missing_reason = classify_tracker_field_missing(
            field_key=field_key,
            project_name=str(entry.get("project_name") or "").strip(),
            winner_row=winner_row,
            source_field_name=source_field_name,
        )

    return {
        "field_key": field_key,
        "field_label": field_label,
        "current_value": current_value,
        "source_key": source_key,
        "source_label": _humanize_tracker_source_label(source_key),
        "source_type": raw_source_type,
        "source_type_label": _humanize_contract_source_type(raw_source_type),
        "reason_code": raw_reason_code,
        "source_reason": source_reason,
        "evidence_preview": " | ".join(part for part in evidence_parts if part),
        "confidence": _derive_confidence(
            source_key=source_key,
            source_type=raw_source_type,
            evidence_source=raw_evidence_source,
            is_missing=is_missing,
            missing_reason_code=missing_reason_code,
            is_overridden=is_overridden,
        ),
        "missing_reason_code": missing_reason_code,
        "missing_reason": missing_reason,
        "is_missing": is_missing,
        "is_overridden": is_overridden,
    }
