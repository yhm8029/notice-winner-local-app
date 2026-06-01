from __future__ import annotations

import re
from typing import Any


SALES_RELEVANT_STAGES = frozenset(
    {
        "DESIGN_SERVICE",
        "MEP_DESIGN",
        "CM_SUPERVISION",
        "CONSTRUCTION_BID",
        "CONSTRUCTION_REBID",
    }
)


def _norm_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


def _contains_any(norm_text: str, patterns: list[str]) -> bool:
    return any(_norm_text(pattern) in norm_text for pattern in patterns)


def _phase_from_title(title: str) -> str:
    norm = _norm_text(title)
    has_rebid = "재공고" in norm
    has_design_competition = _contains_any(norm, ["설계공모", "건축설계공모", "국제설계공모"])
    has_construction = _contains_any(norm, ["공사", "공사입찰", "전기공사", "통신공사", "소방공사", "기계설비공사"])
    has_mep = _contains_any(norm, ["기계", "전기", "통신", "소방", "자동제어", "bems"])

    if has_rebid and has_construction:
        return "CONSTRUCTION_REBID"
    if has_design_competition and _contains_any(norm, ["정정", "변경", "첨부", "재공고", "취소"]):
        return "SELF_OR_CORRECTION"
    if _contains_any(norm, ["정정공고", "변경공고", "첨부파일변경", "취소공고", "질의답변"]):
        return "SELF_OR_CORRECTION"
    if _contains_any(
        norm,
        [
            "제안서평가",
            "평가용역",
            "평가위원",
            "심사위원",
            "심사위원회",
            "심사중계",
            "심사송출",
            "시스템구축",
            "유지보수",
            "홈페이지",
            "시상식",
            "매뉴얼제작",
            "공모전운영",
            "운영용역",
        ],
    ):
        return "ADMIN_NOISE"
    if _contains_any(norm, ["당선", "당선작", "심사결과", "입상작", "선정결과"]):
        return "CONTEST_RESULT"
    if _contains_any(norm, ["건설사업관리", "감리", "감독권한대행"]):
        return "CM_SUPERVISION"
    if has_construction and not has_design_competition:
        return "CONSTRUCTION_BID"
    if has_mep:
        return "MEP_DESIGN"
    if _contains_any(norm, ["실시설계", "기본설계", "설계용역", "건축설계용역", "기본및실시설계"]):
        return "DESIGN_SERVICE"
    return "UNKNOWN_REFERENCE"


def _hard_exclusion_reason(title: str, stage: str) -> str:
    norm = _norm_text(title)
    if stage == "CONSTRUCTION_REBID":
        return ""
    if stage == "SELF_OR_CORRECTION":
        return "HARD_EXCLUDE:self_or_correction"
    if _contains_any(norm, ["제안서평가", "평가용역"]):
        return "HARD_EXCLUDE:proposal_evaluation"
    if stage == "ADMIN_NOISE":
        return "HARD_EXCLUDE:admin_noise"
    return ""


def classify_related_notice_item(project: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    del project
    classified = dict(item)
    title = str(classified.get("project_name") or "")
    stage = _phase_from_title(title)
    exclusion_reason = _hard_exclusion_reason(title, stage)
    if exclusion_reason:
        sales_relevance = "excluded"
        sales_score = 0
    elif stage in SALES_RELEVANT_STAGES:
        sales_relevance = "sales_relevant"
        sales_score = 90 if stage in {"MEP_DESIGN", "CONSTRUCTION_BID", "CONSTRUCTION_REBID"} else 80
    elif stage == "CONTEST_RESULT":
        sales_relevance = "reference"
        sales_score = 55
    else:
        sales_relevance = "reference"
        sales_score = 35

    reason_codes = list(classified.get("reason_codes") or [])
    reason_codes.append(f"PHASE_MATCH:{stage}")
    if exclusion_reason:
        reason_codes.append(exclusion_reason)

    relatedness_score = int(classified.get("match_score") or 0)
    classified.update(
        {
            "notice_stage": stage,
            "sales_relevance": sales_relevance,
            "exclusion_reason": exclusion_reason,
            "relatedness_score": relatedness_score,
            "sales_relevance_score": sales_score,
            "reason_codes": reason_codes,
        }
    )
    return classified


def group_related_notice_items(project: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {"sales_relevant": [], "reference": [], "excluded": []}
    for item in items:
        classified = classify_related_notice_item(project, item)
        bucket = str(classified.get("sales_relevance") or "reference")
        if bucket not in groups:
            bucket = "reference"
        groups[bucket].append(classified)
    return groups
