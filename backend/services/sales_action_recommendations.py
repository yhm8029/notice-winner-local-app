from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from typing import Any

ACTION_LABEL_STAGE_CHANGE = "단계 변화 감지"
ACTION_LABEL_NEW_TRACKING = "신규 추적 대상"
ACTION_LABEL_RECHECK = "재확인 필요"
ACTION_LABEL_BID_RENOTICE = "유찰/재공고 확인"
ACTION_LABEL_HIGH_VALUE = "고액 모니터링"
ACTION_LABEL_LATE_REFERENCE = "늦은 단계 / 참고"
ACTION_LABEL_HOLD = "보류/제외"

ACTION_LABEL_PRIORITY = (
    ACTION_LABEL_STAGE_CHANGE,
    ACTION_LABEL_BID_RENOTICE,
    ACTION_LABEL_NEW_TRACKING,
    ACTION_LABEL_RECHECK,
    ACTION_LABEL_HIGH_VALUE,
    ACTION_LABEL_LATE_REFERENCE,
    ACTION_LABEL_HOLD,
)

STAGE_IMPORTANCE = {
    "설계사무소 확인": 1,
    "실시설계 / 설계용역": 2,
    "당선작 / 심사결과": 3,
    "기계 / 전기 관련 공고": 4,
    "공사입찰": 5,
    "감리 / 건설사업관리": 6,
    "설계공모": 7,
}

RECHECK_DAYS_BY_NOTICE_TYPE = {
    "설계공모": 90,
    "당선작 / 심사결과": 60,
    "실시설계 / 설계용역": 180,
    "공사입찰": 30,
}

MINIMUM_RECOMMENDATION_AMOUNT_KRW = 50_000_000
NEW_TRACKING_AMOUNT_KRW = 200_000_000
RECHECK_PRIORITY_AMOUNT_KRW = 300_000_000
HIGH_VALUE_AMOUNT_KRW = 500_000_000
ONE_EOK_KRW = 100_000_000

TRACKER_ENTRY_RECOMMENDATION_FIELDS = (
    "id",
    "project_id",
    "project_name",
    "demand_org_name",
    "gross_area_scale",
    "construction_cost",
    "building_automation_estimated_amount",
    "architect_office",
    "construction_start_date",
    "opening_scheduled_date",
    "demand_contact",
    "site_location_1",
    "site_location_2",
    "source_bid_no",
    "source_bid_ord",
)


@dataclass(frozen=True)
class SalesNoticeClassification:
    notice_type: str
    stage_importance: int = 99
    is_meaningful: bool = False
    is_stage_change: bool = False
    is_minor_change: bool = False
    is_renotice: bool = False
    is_construction_bid_renotice: bool = False
    is_excluded: bool = False


def _norm_text(value: Any) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


def _compact_text(*values: Any) -> str:
    return _norm_text(" ".join(str(value or "") for value in values))


def _today_seoul() -> date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Asia/Seoul")).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def _parse_date(value: Any) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    compact = re.sub(r"[^0-9]", "", raw)
    if len(compact) >= 8:
        try:
            return date(int(compact[:4]), int(compact[4:6]), int(compact[6:8]))
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def parse_building_automation_amount_low_krw(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    normalized = text.replace(",", "").replace(" ", "")
    range_match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)(억|억원|원)?~([0-9]+(?:\.[0-9]+)?)(억|억원|원)?",
        normalized,
    )
    if range_match:
        unit = range_match.group(2) or range_match.group(4) or ""
        return _amount_number_to_krw(range_match.group(1), unit)
    eok_match = re.search(r"([0-9]+(?:\.[0-9]+)?)(억|억원)", normalized)
    if eok_match:
        return _amount_number_to_krw(eok_match.group(1), "억")
    won_match = re.search(r"([0-9]{5,})원?", normalized)
    if won_match:
        return _amount_number_to_krw(won_match.group(1), "원")
    plain_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", normalized)
    if not plain_match:
        return 0
    number = Decimal(plain_match.group(1))
    if number < Decimal("1000"):
        return int(number * Decimal(ONE_EOK_KRW))
    return int(number)


def _amount_number_to_krw(raw_number: str, unit: str) -> int:
    try:
        number = Decimal(str(raw_number or "0"))
    except Exception:
        return 0
    if unit in {"억", "억원"}:
        return int(number * Decimal(ONE_EOK_KRW))
    return int(number)


def format_amount_krw_as_eok(value: int) -> str:
    if value <= 0:
        return ""
    eok = Decimal(value) / Decimal(ONE_EOK_KRW)
    return f"{eok:.2f}".rstrip("0").rstrip(".") + "억"


def classify_sales_notice(
    title: Any,
    *,
    reason_code: Any = "",
    source_type: Any = "",
    progress_note: Any = "",
) -> SalesNoticeClassification:
    text = _compact_text(title, reason_code, source_type, progress_note)
    if any(token in text for token in ("취소", "철회", "중지")):
        return SalesNoticeClassification(ACTION_LABEL_HOLD, is_excluded=True)

    is_minor_change = any(token in text for token in ("정정", "변경", "첨부파일변경", "첨부변경", "수정"))
    is_renotice = "재공고" in text or "재입찰" in text
    has_construction_bid = any(token in text for token in ("공사입찰", "시설공사", "공사재공고"))
    if is_renotice and has_construction_bid:
        return SalesNoticeClassification(
            "공사입찰 재공고",
            stage_importance=STAGE_IMPORTANCE["공사입찰"],
            is_meaningful=True,
            is_renotice=True,
            is_construction_bid_renotice=True,
        )
    if is_minor_change:
        return SalesNoticeClassification("정정 / 변경", is_minor_change=True, is_renotice=is_renotice)

    if any(token in text for token in ("설계사무소", "건축사사무소", "당선업체", "선정업체")):
        return SalesNoticeClassification(
            "설계사무소 확인",
            stage_importance=STAGE_IMPORTANCE["설계사무소 확인"],
            is_meaningful=True,
            is_stage_change=True,
        )
    if any(token in text for token in ("실시설계", "기본설계", "설계용역")):
        return SalesNoticeClassification(
            "실시설계 / 설계용역",
            stage_importance=STAGE_IMPORTANCE["실시설계 / 설계용역"],
            is_meaningful=True,
            is_stage_change=True,
        )
    if any(token in text for token in ("당선", "심사결과", "당선작", "입상작")):
        return SalesNoticeClassification(
            "당선작 / 심사결과",
            stage_importance=STAGE_IMPORTANCE["당선작 / 심사결과"],
            is_meaningful=True,
            is_stage_change=True,
        )
    if any(token in text for token in ("기계", "전기", "통신", "소방")):
        return SalesNoticeClassification(
            "기계 / 전기 관련 공고",
            stage_importance=STAGE_IMPORTANCE["기계 / 전기 관련 공고"],
            is_meaningful=True,
            is_stage_change=True,
        )
    if has_construction_bid:
        return SalesNoticeClassification(
            "공사입찰",
            stage_importance=STAGE_IMPORTANCE["공사입찰"],
            is_meaningful=True,
            is_stage_change=True,
        )
    if any(token in text for token in ("감리", "건설사업관리", "cm용역")):
        return SalesNoticeClassification(
            "감리 / 건설사업관리",
            stage_importance=STAGE_IMPORTANCE["감리 / 건설사업관리"],
            is_meaningful=True,
            is_stage_change=True,
        )
    if "설계공모" in text or "설계공모전" in text or "건축설계공모" in text:
        return SalesNoticeClassification(
            "설계공모",
            stage_importance=STAGE_IMPORTANCE["설계공모"],
            is_meaningful=True,
        )
    return SalesNoticeClassification("기타", is_renotice=is_renotice)


def build_sales_action_recommendations(
    tracker_rows: list[dict[str, Any]],
    *,
    today: date | None = None,
    recent_label_exposures: dict[tuple[str, str], date] | None = None,
    max_stage_change_items: int = 5,
    expose_internal_score: bool = False,
) -> list[dict[str, Any]]:
    base_today = today or _today_seoul()
    exposures = recent_label_exposures or {}
    candidates: list[dict[str, Any]] = []
    for row in _select_latest_meaningful_rows_by_project(tracker_rows):
        candidate = _build_recommendation_candidate(row, today=base_today)
        if candidate is None:
            continue
        project_key = str(candidate.get("project_id") or candidate.get("entry_id") or "").strip()
        labels = [
            label
            for label in list(candidate.get("action_labels") or [])
            if not _was_recently_exposed(project_key, label, base_today, exposures)
        ]
        if not labels:
            continue
        candidate["action_labels"] = labels
        candidate["primary_label"] = _primary_label(labels)
        candidate["_sort_score"] = _sort_score(candidate)
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            0 if item.get("primary_label") == ACTION_LABEL_STAGE_CHANGE else 1,
            -int(item.get("automation_amount_low_krw") or 0),
            int(item.get("stage_importance") or 99),
            -int(item.get("elapsed_days") or 0),
            str(item.get("latest_meaningful_notice_date") or ""),
        )
    )

    limited: list[dict[str, Any]] = []
    stage_count = 0
    for candidate in candidates:
        if candidate.get("primary_label") == ACTION_LABEL_STAGE_CHANGE:
            if stage_count >= max_stage_change_items:
                continue
            stage_count += 1
        public_candidate = {key: value for key, value in candidate.items() if not key.startswith("_")}
        if expose_internal_score:
            public_candidate["internal_sort_score"] = int(candidate.get("_sort_score") or 0)
        limited.append(public_candidate)
    return limited


def _select_latest_meaningful_rows_by_project(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    passthrough: list[dict[str, Any]] = []
    for row in rows:
        key = _project_group_key(row)
        if not key:
            passthrough.append(row)
            continue
        grouped.setdefault(key, []).append(row)

    selected: list[dict[str, Any]] = list(passthrough)
    for group_rows in grouped.values():
        latest_excluded = _latest_row(group_rows)
        if latest_excluded is not None:
            latest_classification = classify_sales_notice(
                latest_excluded.get("project_name"),
                reason_code=latest_excluded.get("reason_code"),
                source_type=latest_excluded.get("source_type"),
                progress_note=latest_excluded.get("progress_note"),
            )
            if latest_classification.is_excluded:
                continue
        meaningful_rows = [
            row
            for row in group_rows
            if _row_is_meaningful_for_project_group(row)
        ]
        selected_row = _latest_row(meaningful_rows) or _latest_row(group_rows)
        if selected_row is not None:
            selected.append(selected_row)
    return selected


def _project_group_key(row: dict[str, Any]) -> str:
    project_id = str(row.get("project_id") or "").strip()
    if project_id:
        return f"project:{project_id}"
    project_name = _norm_text(str(row.get("source_project_name_norm") or row.get("project_name") or ""))
    org_name = _norm_text(str(row.get("demand_org_name") or ""))
    if project_name:
        return f"name:{project_name}:{org_name}"
    return ""


def _row_is_meaningful_for_project_group(row: dict[str, Any]) -> bool:
    classification = classify_sales_notice(
        row.get("project_name"),
        reason_code=row.get("reason_code"),
        source_type=row.get("source_type"),
        progress_note=row.get("progress_note"),
    )
    return classification.is_meaningful and not classification.is_minor_change and not classification.is_excluded


def _latest_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return max(
        rows,
        key=lambda row: (
            _parse_date(row.get("notice_date") or row.get("last_checked_date") or row.get("updated_at")) or date.min,
            str(row.get("updated_at") or ""),
            str(row.get("id") or ""),
        ),
    )


def _build_recommendation_candidate(row: dict[str, Any], *, today: date) -> dict[str, Any] | None:
    amount_text = str(row.get("building_automation_estimated_amount") or "").strip()
    amount_low = parse_building_automation_amount_low_krw(amount_text)
    if amount_low < MINIMUM_RECOMMENDATION_AMOUNT_KRW:
        return None

    project_name = str(row.get("project_name") or "").strip()
    notice_date = _parse_date(row.get("notice_date") or row.get("last_checked_date") or row.get("updated_at"))
    classification = classify_sales_notice(
        project_name,
        reason_code=row.get("reason_code"),
        source_type=row.get("source_type"),
        progress_note=row.get("progress_note"),
    )
    if classification.is_excluded:
        return None
    if notice_date is None:
        return None

    elapsed_days = max(0, (today - notice_date).days)
    labels: list[str] = []
    reasons: list[str] = []
    actions: list[str] = []

    if classification.is_construction_bid_renotice:
        labels.append(ACTION_LABEL_BID_RENOTICE)
        reasons.extend(
            [
                "공사입찰 재공고가 확인되었습니다.",
                "유찰 또는 조건 변경 가능성이 있어 확인이 필요합니다.",
                "가격, 조건, 참여 업체 상황을 확인해볼 수 있습니다.",
            ]
        )
        actions.extend(["재공고 사유 확인", "입찰 조건 변경 여부 확인", "시공사/협력사 접촉 가능성 검토"])

    if classification.is_stage_change and elapsed_days <= 30 and amount_low >= MINIMUM_RECOMMENDATION_AMOUNT_KRW:
        labels.append(ACTION_LABEL_STAGE_CHANGE)
        reasons.extend(
            [
                _stage_change_reason(classification.notice_type),
                "스펙 반영 가능성이 있는 시점일 수 있습니다.",
                "설계사무소 또는 기계/전기 담당자 확인이 필요합니다.",
            ]
        )
        actions.extend(["설계사무소 확인", "기계/전기 담당자 확인", "설계 착수 여부 확인", "자동제어 스펙 반영 가능성 검토", "관련 자료 전달"])

    if (
        classification.notice_type == "설계공모"
        and elapsed_days <= 30
        and amount_low >= NEW_TRACKING_AMOUNT_KRW
        and not str(row.get("architect_office") or "").strip()
    ):
        labels.append(ACTION_LABEL_NEW_TRACKING)
        reasons.extend(
            [
                "최근 등록된 고액 설계공모입니다.",
                "아직 설계사무소나 후속공고가 확인되지 않았습니다.",
                "바로 영업하기보다는 관심 프로젝트로 등록하고, 당선작/설계사무소/실시설계 공고 발생 시 다시 확인하는 것이 좋습니다.",
            ]
        )
        actions.extend(["관심 등록", "담당자 배정", "후속공고 알림 대기"])

    recheck_threshold = RECHECK_DAYS_BY_NOTICE_TYPE.get(classification.notice_type)
    if recheck_threshold is not None and elapsed_days > recheck_threshold and amount_low >= ONE_EOK_KRW:
        labels.append(ACTION_LABEL_RECHECK)
        amount_label = format_amount_krw_as_eok(amount_low)
        if amount_label:
            reasons.append(f"자동제어 추정금액 {amount_label} 프로젝트입니다.")
        reasons.extend(
            [
                f"{classification.notice_type} 이후 {recheck_threshold}일 이상 후속공고가 없습니다.",
                "나라장터 외 경로로 진행됐을 가능성이 있어 확인이 필요합니다.",
                "금액 규모가 있어 다시 확인할 가치가 있습니다.",
            ]
        )
        actions.extend(["발주처에 당선자 선정 여부 확인", "설계용역 착수 예정일 확인", "설계사무소 선정 여부 확인", "향후 발주 일정 확인"])

    if not labels and classification.notice_type == "감리 / 건설사업관리" and amount_low >= MINIMUM_RECOMMENDATION_AMOUNT_KRW:
        labels.append(ACTION_LABEL_LATE_REFERENCE)
        reasons.extend(
            [
                "감리 또는 건설사업관리 단계로 보이는 공고입니다.",
                "자동제어 스펙 반영 시점은 늦었을 수 있어 참고용으로 확인하세요.",
            ]
        )
        actions.extend(["진행 단계 확인", "기존 스펙 반영 여부 확인", "참고 프로젝트로 보류"])

    if amount_low >= HIGH_VALUE_AMOUNT_KRW and labels:
        labels.append(ACTION_LABEL_HIGH_VALUE)

    labels = _dedupe_preserve_order(labels)
    if not labels:
        return None
    tracker_entry = {field: str(row.get(field) or "") for field in TRACKER_ENTRY_RECOMMENDATION_FIELDS}
    tracker_entry["project_name"] = project_name
    tracker_entry["building_automation_estimated_amount"] = amount_text

    return {
        "entry_id": str(row.get("id") or ""),
        "project_id": str(row.get("project_id") or ""),
        "project_name": project_name,
        "source_bid_no": str(row.get("source_bid_no") or ""),
        "source_bid_ord": str(row.get("source_bid_ord") or ""),
        "automation_amount_text": amount_text,
        "automation_amount_low_krw": amount_low,
        "primary_label": _primary_label(labels),
        "action_labels": labels,
        "latest_meaningful_notice_type": classification.notice_type,
        "latest_meaningful_notice_date": notice_date.isoformat(),
        "elapsed_days": elapsed_days,
        "reasons": _dedupe_preserve_order(reasons),
        "recommended_actions": _dedupe_preserve_order(actions),
        "stage_importance": classification.stage_importance,
        "tracker_entry": tracker_entry,
        "claim_payload": {
            "id": str(row.get("id") or ""),
            "project_id": str(row.get("project_id") or ""),
            "source_tracker_run_id": str(row.get("source_tracker_run_id") or ""),
            "source_run_id": str(row.get("source_run_id") or ""),
            "project_name": project_name,
            "building_automation_estimated_amount": amount_text,
            "construction_cost": str(row.get("construction_cost") or ""),
        },
    }


def _stage_change_reason(notice_type: str) -> str:
    if notice_type == "실시설계 / 설계용역":
        return "최근 실시설계 관련 공고가 확인되었습니다."
    if notice_type == "당선작 / 심사결과":
        return "최근 당선작 또는 심사결과 공고가 확인되었습니다."
    if notice_type == "기계 / 전기 관련 공고":
        return "최근 기계/전기 관련 공고가 확인되었습니다."
    if notice_type == "공사입찰":
        return "최근 공사입찰 공고가 확인되었습니다."
    if notice_type == "설계사무소 확인":
        return "최근 설계사무소 확인 단서가 확인되었습니다."
    return f"최근 {notice_type} 공고가 확인되었습니다."


def _primary_label(labels: list[str]) -> str:
    label_set = set(labels)
    for label in ACTION_LABEL_PRIORITY:
        if label in label_set:
            return label
    return labels[0] if labels else ACTION_LABEL_HOLD


def _was_recently_exposed(
    project_key: str,
    label: str,
    today: date,
    exposures: dict[tuple[str, str], date],
) -> bool:
    if not project_key:
        return False
    exposed_at = exposures.get((project_key, label))
    if exposed_at is None:
        return False
    return 0 <= (today - exposed_at).days < 7


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _sort_score(item: dict[str, Any]) -> int:
    amount = int(item.get("automation_amount_low_krw") or 0)
    primary_priority = ACTION_LABEL_PRIORITY.index(str(item.get("primary_label") or ACTION_LABEL_HOLD))
    stage_importance = int(item.get("stage_importance") or 99)
    return max(0, 10_000 - primary_priority * 1000 - stage_importance * 20) + amount // 10_000_000
