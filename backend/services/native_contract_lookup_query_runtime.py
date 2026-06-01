from __future__ import annotations

import re
from datetime import datetime
from datetime import timedelta


def _resolve_date_window(announce_date: str) -> tuple[str, str] | None:
    text = str(announce_date or "").strip()
    match = re.search(r"(\d{4})(\d{2})(\d{2})", text)
    if not match:
        return None
    try:
        start = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except Exception:
        return None
    year_end = datetime(start.year, 12, 31)
    return (start.strftime("%Y%m%d"), year_end.strftime("%Y%m%d"))


def _build_lofin_date_hints(announce_date: str) -> list[str]:
    if not _is_yyyymmdd(announce_date):
        return []
    try:
        base_dt = datetime.strptime(str(announce_date), "%Y%m%d")
    except ValueError:
        return []
    lofin_start = base_dt + timedelta(days=30)
    lofin_end = min(base_dt + timedelta(days=210), datetime.now())
    if lofin_start > lofin_end:
        return []
    return _iter_yyyymmdd_asc(lofin_start.strftime("%Y%m%d"), lofin_end.strftime("%Y%m%d"), max_days=240)


def _iter_yyyymmdd_asc(start_ymd: str, end_ymd: str, *, max_days: int) -> list[str]:
    try:
        start_dt = datetime.strptime(start_ymd, "%Y%m%d")
        end_dt = datetime.strptime(end_ymd, "%Y%m%d")
    except Exception:
        return []
    if start_dt > end_dt:
        return []
    rows: list[str] = []
    current = start_dt
    while current <= end_dt and len(rows) < max_days:
        rows.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return rows


def _iter_yyyymmdd_desc(start_ymd: str, end_ymd: str, *, max_days: int) -> list[str]:
    try:
        start_dt = datetime.strptime(start_ymd, "%Y%m%d")
        end_dt = datetime.strptime(end_ymd, "%Y%m%d")
    except Exception:
        return []
    if start_dt > end_dt:
        return []
    rows: list[str] = []
    current = end_dt
    while current >= start_dt and len(rows) < max_days:
        rows.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)
    return rows


def _is_yyyymmdd(value: str) -> bool:
    return bool(re.fullmatch(r"\d{8}", str(value or "").strip()))


def _is_education_org_name(text: str) -> bool:
    norm = re.sub(r"\s+", "", str(text or ""))
    return "교육청" in norm or "교육지원청" in norm


def _is_local_government_org_name(text: str) -> bool:
    norm = re.sub(r"\s+", "", str(text or ""))
    return any(
        token in norm
        for token in (
            "특별자치시",
            "특별자치도",
            "광역시",
            "시청",
            "군청",
            "구청",
            "도청",
        )
    )


def _should_run_query_sweep(*, enable_query_sweep: bool, org_name: str, project_name_norm: str) -> bool:
    if not enable_query_sweep:
        return False
    if len(re.sub(r"\s+", "", str(project_name_norm or "")).strip().lower()) < 10:
        return False
    return _is_education_org_name(org_name) or _is_local_government_org_name(org_name)


def _is_generic_project_term(value: str) -> bool:
    compact = re.sub(r"\s+", "", str(value or "")).strip().lower()
    return compact in {"", "공고", "설계공모", "공모", "사업"}
