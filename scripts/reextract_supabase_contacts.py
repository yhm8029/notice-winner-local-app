from __future__ import annotations

import argparse
import csv
import json
import os
import re
import requests
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.repositories.factory import get_tracker_entry_repository
from backend.repositories.factory import reset_tracker_entry_repository
from backend.repositories.tracker_entries import TrackerEntryRepository
from backend.repositories.tracker_entries import TrackerEntryRepositoryError
from backend.services.native_export_backend import _build_page_fetch_urls
from backend.services.native_export_backend import _collect_attachment_documents
from backend.services.native_export_backend import _contact_specificity
from backend.services.native_export_backend import _extract_notice_fields
from backend.services.native_export_backend import _fetch_attachment_texts
from backend.services.native_export_backend import _fetch_page_documents
from backend.services.native_export_backend import _pick_primary_document
from backend.services.native_export_backend import _prefer_richer_contact
from backend.services.native_llm_correction import _needs_contact_llm
from backend.services.native_llm_correction import load_llm_correction_config
from backend.services.native_llm_correction import maybe_correct_notice_fields_with_llm
from backend.services.native_seed_backend import fetch_seed_rows_with_diagnostics
from backend.services.native_seed_backend import resolve_service_key
from backend.services.native_seed_backend import API_SCOPE_TO_DIRECT_ENDPOINTS
from backend.services.native_seed_backend import _api_header
from backend.services.native_seed_backend import _derive_notice_status
from backend.services.native_seed_backend import _extract_items
from backend.services.native_seed_backend import _try_xml_items_fallback
from backend.services.native_gui_rules import extract_contact_from_notice_text
from backend.services.native_gui_rules import has_external_competition_portal_only_contact
from backend.services.native_gui_rules import is_auxiliary_service_project
from backend.services.native_gui_rules import normalize_contact_candidate
from backend.services.native_gui_rules import normalize_phone
from backend.services.native_gui_rules import PHONE_FLEX_PAT
from backend.services.backfill_policy import is_suspicious_contact_placeholder

ATTACHMENT_FIELD_COUNT = 10
CONTACT_SENTENCE_FRAGMENT_PAT = re.compile(
    r"(?:토론을\s*통해|공모안을\s*분석|분석하고|공정한|접수\s*사실|수신\s*여부|유선\s*통보|반드시\s*확인)",
    re.I,
)
CURRENT_CONTACT_HARD_NOISE_PAT = re.compile(
    r"(?:등이\s*변경되었을\s*경우에는|신속히\s*우리시|토론을\s*통해|공모안을\s*분석|공정한\s*과|기타\s*공모의\s*진행|공공건축처)",
    re.I,
)
WEAK_CONTACT_DEPT_EXACT = {
    "행정실",
    "접수실",
    "접수사실",
    "공모관리팀",
}
ENGLISH_NOTICE_FILE_PAT = re.compile(
    r"(?:영문|_eng\b|\beng\b|english|notice on the international design competition|announcement_eng|guidelines_eng)",
    re.I,
)
REPORT_FIELDS = (
    "entry_id",
    "bid_no",
    "bid_ord",
    "project_name",
    "demand_org_name",
    "notice_date",
    "current_contact",
    "current_needs_llm",
    "seed_fetch_source",
    "seed_announce_date",
    "seed_officer_name",
    "seed_officer_tel",
    "candidate_contact",
    "candidate_contact_source",
    "llm_requested",
    "llm_contact_corrected",
    "verification_status",
    "safe_to_apply",
    "applied",
    "apply_changed",
    "error",
    "hub_check_note",
    "progress_message",
)


@dataclass(frozen=True)
class SeedLookupResult:
    row: dict[str, str]
    source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re-extract demand_contact for live Supabase tracker entries.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-needs-llm", action="store_true")
    parser.add_argument("--input-csv", default="")
    parser.add_argument("--force-llm-contact", action="store_true")
    parser.add_argument("--apply-safe", action="store_true")
    parser.add_argument("--actor-label", default="")
    parser.add_argument("--output-prefix", default="")
    return parser.parse_args()


def load_env_file(path: str) -> None:
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _month_bounds(date_text: str) -> tuple[str, str]:
    text = str(date_text or "").strip()
    if len(text) != 8 or not text.isdigit():
        return "20250101", "20251231"
    year = int(text[:4])
    month = int(text[4:6])
    start = f"{year:04d}{month:02d}01"
    if month == 12:
        end = f"{year:04d}{month:02d}31"
    else:
        next_month = datetime(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
        last_day = (next_month - datetime.resolution).day
        end = f"{year:04d}{month:02d}{last_day:02d}"
    return start, end


def list_all_tracker_entries(
    *,
    repo: TrackerEntryRepository,
    page_size: int,
) -> list[dict[str, Any]]:
    page = 1
    rows: list[dict[str, Any]] = []
    while True:
        try:
            batch, total = repo.list_entries(
                page=page,
                page_size=page_size,
                q="",
                region="",
                exclude_auxiliary_titles=False,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        except TrackerEntryRepositoryError as exc:
            if "tracker_entries_effective.contract_date does not exist" not in str(exc):
                raise
            batch, total = _list_contact_reextract_entries_minimal(repo=repo, page=page, page_size=page_size)
        rows.extend(batch)
        if len(rows) >= total or not batch:
            break
        page += 1
    return rows


def _list_contact_reextract_entries_minimal(
    *,
    repo: TrackerEntryRepository,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    request_json = getattr(repo, "_request_json", None)
    config = getattr(repo, "_config", None)
    if request_json is None or config is None or not getattr(config, "organization_id", None):
        raise TrackerEntryRepositoryError(
            "minimal tracker entry fallback is unavailable for the current repository backend"
        )
    select_clause = ",".join(
        (
            "id",
            "entry_key",
            "source_bid_no",
            "source_bid_ord",
            "source_project_name_norm",
            "project_name",
            "demand_org_name",
            "notice_date",
            "demand_contact",
            "updated_at",
        )
    )
    rows, headers = request_json(
        method="GET",
        path="/tracker_entries_effective",
        query=[
            ("select", select_clause),
            ("organization_id", f"eq.{config.organization_id}"),
            ("limit", str(page_size)),
            ("offset", str((page - 1) * page_size)),
            ("order", "updated_at.desc"),
            ("order", "id.asc"),
        ],
        headers={"Prefer": "count=planned"},
    )
    total = _parse_total_count(headers, fallback=len(rows))
    return [dict(row) for row in rows], total


def _parse_total_count(headers: dict[str, str], *, fallback: int) -> int:
    content_range = str(headers.get("Content-Range") or "").strip()
    if "/" not in content_range:
        return fallback
    total = content_range.rsplit("/", 1)[-1].strip()
    if not total or total == "*":
        return fallback
    try:
        return int(total)
    except ValueError:
        return fallback


def load_subset_entries(
    *,
    repo_rows: list[dict[str, Any]],
    input_csv: str,
) -> list[dict[str, Any]]:
    entry_index = {str(row.get("id") or ""): row for row in repo_rows}
    selected: list[dict[str, Any]] = []
    with Path(input_csv).expanduser().open("r", encoding="utf-8-sig", newline="") as fp:
        for row in csv.DictReader(fp):
            entry_id = str(row.get("entry_id") or "").strip()
            live_row = entry_index.get(entry_id)
            if live_row is not None:
                selected.append(live_row)
                continue
            selected.append(
                {
                    "id": entry_id,
                    "source_bid_no": str(row.get("bid_no") or "").strip(),
                    "source_bid_ord": str(row.get("bid_ord") or "").strip() or "000",
                    "project_name": str(row.get("project_name") or "").strip(),
                    "demand_org_name": str(row.get("demand_org_name") or "").strip(),
                    "notice_date": str(row.get("notice_date") or "").strip(),
                    "demand_contact": str(row.get("current_contact") or "").strip(),
                }
            )
    return selected


def _row_matches_bid(row: dict[str, str], *, bid_no: str, bid_ord: str) -> bool:
    return (
        str(row.get("bid_no") or "").strip().upper() == bid_no.upper()
        and str(row.get("bid_ord") or "").strip() == bid_ord
    )


def _find_seed_row_in_artifacts(*, bid_no: str, bid_ord: str) -> dict[str, str]:
    for seed_path in sorted((ROOT / "output" / "artifacts").glob("*/project_tracker_seed_input.csv")):
        with seed_path.open("r", encoding="utf-8-sig", newline="") as fp:
            for row in csv.DictReader(fp):
                candidate = {str(key): str(value or "").strip() for key, value in row.items()}
                if _row_matches_bid(candidate, bid_no=bid_no, bid_ord=bid_ord):
                    return candidate
    return {}


def fetch_seed_row(
    *,
    service_key: str,
    bid_no: str,
    bid_ord: str,
    notice_date: str,
) -> SeedLookupResult:
    start_date, end_date = _month_bounds(notice_date)
    result = fetch_seed_rows_with_diagnostics(
        service_key=service_key,
        start_date=start_date,
        end_date=end_date,
        bid_no_filter=bid_no,
        title_filter="",
        demand_org_filter="",
        rows_per_page=20,
        max_pages=1,
        endpoint_mode="all",
        allow_title_broad_retry=False,
    )
    for row in result.rows:
        if _row_matches_bid(row, bid_no=bid_no, bid_ord=bid_ord):
            return SeedLookupResult(row=row, source="g2b_api")
    if result.rows:
        return SeedLookupResult(row=result.rows[0], source="g2b_api")
    artifact_row = _find_seed_row_in_artifacts(bid_no=bid_no, bid_ord=bid_ord)
    if artifact_row:
        return SeedLookupResult(row=artifact_row, source="artifact_seed")
    return SeedLookupResult(row={}, source="")


def detect_bid_notice_status(
    *,
    service_key: str,
    bid_no: str,
    bid_ord: str,
    notice_date: str,
    timeout_sec: int = 15,
) -> str:
    normalized_bid_no = str(bid_no or "").strip().upper()
    normalized_bid_ord = str(bid_ord or "").strip() or "000"
    if not normalized_bid_no:
        return ""
    session = requests.Session()
    exact_statuses: list[str] = []
    fallback_statuses: list[str] = []
    for _, endpoint_url in API_SCOPE_TO_DIRECT_ENDPOINTS["all"]:
        params = {
            "ServiceKey": service_key,
            "pageNo": 1,
            "numOfRows": 20,
            "type": "json",
            "inqryDiv": "2",
            "bidNtceNo": normalized_bid_no,
        }
        try:
            response = session.get(endpoint_url, params=params, timeout=timeout_sec)
        except Exception:
            continue
        if int(getattr(response, "status_code", 0) or 0) != 200:
            continue
        try:
            payload = response.json()
        except Exception:
            payload = {}
        result_code, _ = _api_header(payload) if isinstance(payload, dict) else ("", "")
        if result_code and result_code not in {"00", "03"}:
            continue
        items, _ = _extract_items(payload) if isinstance(payload, dict) else ([], 0)
        if not items:
            xml_items, _ = _try_xml_items_fallback(session, endpoint_url, params, timeout_sec=timeout_sec)
            items = xml_items
        for item in items:
            item_bid_no = str(item.get("bidNtceNo") or "").strip().upper()
            if item_bid_no != normalized_bid_no:
                continue
            status = _derive_notice_status(
                title=str(item.get("bidNtceNm") or "").strip(),
                notice_kind_name=str(item.get("ntceKindNm") or "").strip(),
            )
            item_bid_ord = str(item.get("bidNtceOrd") or "").strip() or "000"
            if item_bid_ord == normalized_bid_ord:
                exact_statuses.append(status)
            else:
                fallback_statuses.append(status)
    if "cancelled" in exact_statuses:
        return "cancelled"
    if exact_statuses:
        return exact_statuses[0]
    if "cancelled" in fallback_statuses:
        return "cancelled"
    if fallback_statuses:
        return fallback_statuses[0]
    return ""


def build_export_row(entry: dict[str, Any], seed_row: dict[str, str]) -> dict[str, str]:
    row = {
        "bid_no": str(entry.get("source_bid_no") or seed_row.get("bid_no") or "").strip(),
        "bid_ord": str(entry.get("source_bid_ord") or seed_row.get("bid_ord") or "000").strip() or "000",
        "project_name_norm": str(entry.get("source_project_name_norm") or entry.get("project_name") or "").strip(),
        "org_name": str(seed_row.get("org_name") or entry.get("demand_org_name") or "").strip(),
        "announce_date": str(seed_row.get("announce_date") or entry.get("notice_date") or "").strip(),
        "g2b_verified": str(seed_row.get("g2b_verified") or "Y").strip() or "Y",
        "internal_search_url": str(seed_row.get("bid_ntce_dtl_url") or seed_row.get("bid_ntce_url") or "").strip(),
        "notice_url": str(seed_row.get("bid_ntce_dtl_url") or seed_row.get("bid_ntce_url") or "").strip(),
        "base_url": str(seed_row.get("bid_ntce_url") or seed_row.get("bid_ntce_dtl_url") or "").strip(),
        "presmpt_prce": str(seed_row.get("presmpt_prce") or "").strip(),
        "officer_name": str(seed_row.get("notice_officer_name") or seed_row.get("demand_officer_name") or "").strip(),
        "officer_tel": str(seed_row.get("notice_officer_tel") or "").strip(),
        "spec_doc_url": str(seed_row.get("spec_doc_url_1") or "").strip(),
        "spec_doc_file_name": str(seed_row.get("spec_doc_file_name_1") or "").strip(),
    }
    for index in range(1, ATTACHMENT_FIELD_COUNT + 1):
        row[f"spec_doc_url_{index}"] = str(seed_row.get(f"spec_doc_url_{index}") or "").strip()
        row[f"spec_doc_file_name_{index}"] = str(seed_row.get(f"spec_doc_file_name_{index}") or "").strip()
    return row


def _fallback_seed_contact(seed_row: dict[str, str]) -> str:
    officer_name = str(
        seed_row.get("officer_name")
        or seed_row.get("notice_officer_name")
        or seed_row.get("demand_officer_name")
        or ""
    ).strip()
    officer_tel = str(seed_row.get("officer_tel") or seed_row.get("notice_officer_tel") or "").strip()
    if officer_name and officer_tel:
        return f"{officer_name} / {officer_tel}"
    if officer_tel:
        return officer_tel
    return ""


def _extract_contact_phone(value: str) -> str:
    match = PHONE_FLEX_PAT.search(str(value or "").strip())
    if not match:
        return ""
    return normalize_phone(match.group(0))


def _extract_contact_dept(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "/" in text:
        return text.split("/", 1)[0].strip()
    phone_match = PHONE_FLEX_PAT.search(text)
    if phone_match:
        return text[: phone_match.start()].strip(" /:-")
    return text


def _replace_contact_dept(value: str, dept: str) -> str:
    text = str(value or "").strip()
    phone = _extract_contact_phone(text)
    clean_dept = str(dept or "").strip()
    if clean_dept and phone:
        return f"{clean_dept}/{phone}"
    return text


def _strip_orphan_admin_prefix(dept: str) -> str:
    value = str(dept or "").strip()
    return re.sub(r"^(?:청|시청|군청|구청|도청|교육청|지원청)\s+", "", value).strip()


def _looks_like_sentence_fragment_contact(value: str) -> bool:
    dept = _extract_contact_dept(value)
    if not dept:
        return True
    compact = re.sub(r"\s+", "", dept)
    if CURRENT_CONTACT_HARD_NOISE_PAT.search(dept):
        return True
    if CONTACT_SENTENCE_FRAGMENT_PAT.search(dept):
        return True
    return any(
        token in compact
        for token in (
            "토론을통해",
            "공모안을분석",
            "분석하고",
            "공정한",
            "접수사실",
            "수신여부",
            "유선통보",
            "반드시확인",
        )
    )


def _looks_like_weak_structured_contact(value: str) -> bool:
    dept = _extract_contact_dept(value)
    if not dept:
        return False
    dept_norm = re.sub(r"\s+", "", str(dept or "").strip())
    return dept_norm in WEAK_CONTACT_DEPT_EXACT


def assess_current_contact_quality(*, current_contact: str, org_name: str) -> tuple[bool, bool]:
    current = str(current_contact or "").strip()
    if not current:
        return True, False
    if is_suspicious_contact_placeholder(current):
        return True, False
    weak_contact = _looks_like_weak_structured_contact(current)
    normalized, _reason = normalize_confirmed_contact_candidate(current, org_name)
    if normalized:
        return False, weak_contact
    if weak_contact:
        return False, True
    return True, False


def normalize_confirmed_contact_candidate(candidate_contact: str, org_name: str) -> tuple[str, str]:
    raw = str(candidate_contact or "").strip()
    if not raw:
        return "", "empty"
    if _looks_like_sentence_fragment_contact(raw):
        return "", "sentence_fragment"
    normalized = normalize_contact_candidate(raw, org_name)
    if not normalized:
        return "", "normalized_blank"
    dept = _extract_contact_dept(normalized)
    cleaned_dept = _strip_orphan_admin_prefix(dept)
    if cleaned_dept != dept:
        normalized = _replace_contact_dept(normalized, cleaned_dept)
    if _looks_like_sentence_fragment_contact(normalized):
        return "", "sentence_fragment"
    return normalized, ""


def should_exclude_contact_target(project_name: str) -> bool:
    return is_auxiliary_service_project(str(project_name or "").strip())


def _filter_contact_attachment_documents(documents: list[Any]) -> list[Any]:
    return [
        document
        for document in documents
        if not ENGLISH_NOTICE_FILE_PAT.search(str(getattr(document, "file_name", "") or ""))
    ]


def extract_contact_via_notice(
    *,
    export_row: dict[str, str],
    llm_enabled: bool,
    force_llm_contact: bool = False,
) -> tuple[str, str, bool, str, str, bool]:
    llm_config = load_llm_correction_config()
    search_url = str(export_row.get("internal_search_url") or "").strip()
    base_url = str(export_row.get("base_url") or "").strip()
    notice_url = str(export_row.get("notice_url") or "").strip()
    spec_doc_url = str(export_row.get("spec_doc_url") or "").strip()
    spec_doc_file_name = str(export_row.get("spec_doc_file_name") or "").strip()
    project_name = str(export_row.get("project_name_norm") or "").strip()
    org_name = str(export_row.get("org_name") or "").strip()
    bid_no = str(export_row.get("bid_no") or "").strip()

    page_urls = _build_page_fetch_urls(
        notice_url=notice_url,
        base_url=base_url,
        search_url=search_url,
    )
    documents = _fetch_page_documents(page_urls)
    preferred_document = _pick_primary_document(documents)
    title = preferred_document.title or project_name
    page_text = "\n".join(doc.text for doc in documents if doc.text)
    combined_text = page_text
    extracted = _extract_notice_fields(
        title=title,
        text=combined_text,
        project_name=title,
        org_name=org_name,
    )

    attachment_docs = _filter_contact_attachment_documents(
        _collect_attachment_documents(
        export_row,
        spec_doc_url=spec_doc_url,
        spec_doc_file_name=spec_doc_file_name,
        )
    )
    attachment_display_name = str(getattr(attachment_docs[0], "file_name", "") or "").strip() if attachment_docs else ""
    attachment_note = ""
    if attachment_docs and _needs_contact_llm(contact=extracted.demand_contact):
        attachment_payload = _fetch_attachment_texts(attachment_docs)
        attachment_note = (
            f"attachment_parsed:{attachment_payload.parsed_count}/{attachment_payload.tried_count}"
            if attachment_payload.parsed_count
            else f"attachment_tried:{attachment_payload.tried_count}/0"
        )
        if attachment_payload.all_text:
            combined_text = "\n\n".join(part for part in [page_text, attachment_payload.all_text] if part).strip()
            extracted = _extract_notice_fields(
                title=title,
                text=combined_text,
                project_name=title,
                org_name=org_name,
            )
            attachment_contact = extract_contact_from_notice_text(
                attachment_payload.announcement_text or attachment_payload.all_text,
                org_name,
            )
            best_contact = _prefer_richer_contact(
                current_contact=extracted.demand_contact,
                candidate_contact=attachment_contact,
            )
            if best_contact:
                extracted = extracted.__class__(
                    winner_name=extracted.winner_name,
                    winner_pattern=extracted.winner_pattern,
                    gross_area_scale=extracted.gross_area_scale,
                    construction_cost=extracted.construction_cost,
                    demand_contact=best_contact,
                    client_location=extracted.client_location,
                    site_location=extracted.site_location,
                    architect_office=extracted.architect_office,
                    construction_start_date=extracted.construction_start_date,
                    construction_duration_days=extracted.construction_duration_days,
                    building_automation_estimated_amount=extracted.building_automation_estimated_amount,
                    llm_corrected_fields=extracted.llm_corrected_fields,
                )

    llm_contact_corrected = False
    llm_contact_input = "" if force_llm_contact else extracted.demand_contact
    should_call_llm = bool(
        llm_enabled
        and llm_config.enabled
        and (force_llm_contact or _needs_contact_llm(contact=extracted.demand_contact))
    )
    if should_call_llm:
        llm_result = maybe_correct_notice_fields_with_llm(
            config=llm_config,
            text=combined_text,
            project_name=title,
            org_name=org_name,
            area=extracted.gross_area_scale or "100㎡",
            cost=extracted.construction_cost or "100,000,000원",
            contact=llm_contact_input,
        )
        llm_contact_corrected = "contact" in llm_result.corrected_fields
        if llm_result.contact:
            extracted = extracted.__class__(
                winner_name=extracted.winner_name,
                winner_pattern=extracted.winner_pattern,
                gross_area_scale=extracted.gross_area_scale,
                construction_cost=extracted.construction_cost,
                demand_contact=llm_result.contact,
                client_location=extracted.client_location,
                site_location=extracted.site_location,
                architect_office=extracted.architect_office,
                construction_start_date=extracted.construction_start_date,
                construction_duration_days=extracted.construction_duration_days,
                building_automation_estimated_amount=extracted.building_automation_estimated_amount,
                llm_corrected_fields=llm_result.corrected_fields,
            )

    candidate_contact = str(extracted.demand_contact or "").strip()
    candidate_source = "confirmed_extracted" if candidate_contact else ""
    expected_blank_external_portal = bool(
        not candidate_contact and has_external_competition_portal_only_contact(combined_text)
    )
    confirmed_reject_reason = ""
    confirmed_normalized = False
    if candidate_source == "confirmed_extracted":
        normalized_candidate, confirmed_reject_reason = normalize_confirmed_contact_candidate(candidate_contact, org_name)
        if normalized_candidate:
            confirmed_normalized = normalized_candidate != candidate_contact
            candidate_contact = normalized_candidate
        else:
            candidate_contact = ""
            candidate_source = ""
    if not candidate_contact and not expected_blank_external_portal:
        candidate_contact = _fallback_seed_contact(export_row)
        candidate_source = "fallback_seed_contact" if candidate_contact else ""

    notes = []
    if attachment_display_name:
        notes.append(attachment_display_name)
    if attachment_note:
        notes.append(attachment_note)
    if confirmed_normalized:
        notes.append("demand_contact=normalized_confirmed")
    if confirmed_reject_reason:
        notes.append(f"demand_contact=rejected_confirmed:{confirmed_reject_reason}")
    if expected_blank_external_portal:
        notes.append("demand_contact=expected_blank_external_portal")
    if llm_contact_corrected:
        notes.append("llm_corrected=contact")
    if candidate_source == "fallback_seed_contact":
        notes.append("demand_contact=fallback_seed_contact")
    hub_check_note = " | ".join(note for note in notes if note)
    progress_message = (
        f"{bid_no}: contact={'Y' if candidate_contact else 'N'} "
        f"source={candidate_source or '-'} "
        f"pages={len(documents)} attachments={len(attachment_docs)} "
        f"llm_contact={'Y' if llm_contact_corrected else 'N'}"
    )
    return (
        candidate_contact,
        candidate_source,
        llm_contact_corrected,
        hub_check_note,
        progress_message,
        expected_blank_external_portal,
    )


def classify_result(
    *,
    current_contact: str,
    current_needs_llm: bool,
    current_implausible: bool = False,
    current_weak: bool = False,
    candidate_contact: str,
    candidate_source: str,
    llm_contact_corrected: bool,
    expected_blank_external_portal: bool = False,
    error: str = "",
) -> tuple[str, bool]:
    if error:
        return "error", False
    current = str(current_contact or "").strip()
    candidate = str(candidate_contact or "").strip()
    current_phone = _extract_contact_phone(current)
    candidate_phone = _extract_contact_phone(candidate)
    current_specificity = _contact_specificity(current)
    candidate_specificity = _contact_specificity(candidate)
    if expected_blank_external_portal:
        return "expected_blank_external_portal", False
    if not candidate_contact:
        if current_needs_llm:
            return "still_blank", False
        return "no_candidate", False
    if candidate_contact == current_contact:
        return "unchanged", False
    if current and not current_needs_llm and not current_implausible and not current_weak:
        return "keep_current", False
    if candidate_source == "fallback_seed_contact":
        if current_needs_llm:
            return "fallback_only", False
        return "review_needed", False
    if current_implausible and candidate_source == "confirmed_extracted" and not llm_contact_corrected:
        return "safe_replace_implausible_current", True
    if not current and candidate_source == "confirmed_extracted":
        return "safe_improvement", True
    if (
        current
        and current_needs_llm
        and candidate_source == "confirmed_extracted"
        and current_phone
        and candidate_phone
        and current_phone == candidate_phone
        and candidate_specificity > current_specificity
    ):
        return "safe_upgrade_same_phone", True
    if current_weak and candidate_source == "confirmed_extracted":
        return "review_needed", False
    if candidate_source == "confirmed_extracted" and current_needs_llm:
        return "review_needed", False
    if candidate_source == "confirmed_extracted" and llm_contact_corrected:
        return "review_needed", False
    if candidate_source == "confirmed_extracted":
        return "review_needed", False
    return "review_needed", False


def process_entry(
    *,
    entry: dict[str, Any],
    service_key: str,
    llm_enabled: bool,
    force_llm_contact: bool = False,
) -> dict[str, Any]:
    entry_id = str(entry.get("id") or "").strip()
    bid_no = str(entry.get("source_bid_no") or "").strip()
    bid_ord = str(entry.get("source_bid_ord") or "").strip() or "000"
    project_name = str(entry.get("project_name") or "").strip()
    demand_org_name = str(entry.get("demand_org_name") or "").strip()
    notice_date = str(entry.get("notice_date") or "").strip()
    current_contact = str(entry.get("demand_contact") or "").strip()
    current_implausible, current_weak = assess_current_contact_quality(
        current_contact=current_contact,
        org_name=demand_org_name,
    )
    current_needs_llm = bool(
        _needs_contact_llm(contact=current_contact)
        or current_implausible
        or current_weak
    )
    report: dict[str, Any] = {
        "entry_id": entry_id,
        "bid_no": bid_no,
        "bid_ord": bid_ord,
        "project_name": project_name,
        "demand_org_name": demand_org_name,
        "notice_date": notice_date,
        "current_contact": current_contact,
        "current_needs_llm": current_needs_llm,
        "seed_fetch_source": "",
        "seed_announce_date": "",
        "seed_officer_name": "",
        "seed_officer_tel": "",
        "candidate_contact": "",
        "candidate_contact_source": "",
        "llm_requested": bool(llm_enabled and (force_llm_contact or current_needs_llm)),
        "llm_contact_corrected": False,
        "verification_status": "",
        "safe_to_apply": False,
        "applied": False,
        "apply_changed": False,
        "error": "",
        "hub_check_note": "",
        "progress_message": "",
    }
    if not bid_no:
        report["error"] = "missing_bid_no"
        report["verification_status"] = "error"
        return report

    try:
        notice_status = detect_bid_notice_status(
            service_key=service_key,
            bid_no=bid_no,
            bid_ord=bid_ord,
            notice_date=notice_date,
        )
        if notice_status == "cancelled":
            report["verification_status"] = "excluded_cancelled"
            report["progress_message"] = f"{bid_no}: excluded cancelled notice"
            return report
        if should_exclude_contact_target(project_name):
            report["verification_status"] = "excluded_auxiliary"
            report["progress_message"] = f"{bid_no}: excluded auxiliary project"
            return report
        seed_lookup = fetch_seed_row(
            service_key=service_key,
            bid_no=bid_no,
            bid_ord=bid_ord,
            notice_date=notice_date,
        )
        seed_row = seed_lookup.row
        report["seed_fetch_source"] = seed_lookup.source
        if not seed_row:
            report["error"] = "seed_row_not_found"
            report["verification_status"] = "error"
            return report
        report["seed_announce_date"] = str(seed_row.get("announce_date") or "").strip()
        report["seed_officer_name"] = str(
            seed_row.get("notice_officer_name") or seed_row.get("demand_officer_name") or ""
        ).strip()
        report["seed_officer_tel"] = str(seed_row.get("notice_officer_tel") or "").strip()

        export_row = build_export_row(entry, seed_row)
        (
            candidate_contact,
            candidate_source,
            llm_contact_corrected,
            hub_check_note,
            progress_message,
            expected_blank_external_portal,
        ) = extract_contact_via_notice(
            export_row=export_row,
            llm_enabled=bool(llm_enabled and (force_llm_contact or current_needs_llm)),
            force_llm_contact=force_llm_contact,
        )

        report["candidate_contact"] = candidate_contact
        report["candidate_contact_source"] = candidate_source
        report["hub_check_note"] = hub_check_note
        report["progress_message"] = progress_message
        report["llm_contact_corrected"] = llm_contact_corrected
        report["verification_status"], report["safe_to_apply"] = classify_result(
            current_contact=current_contact,
            current_needs_llm=current_needs_llm,
            current_implausible=current_implausible,
            current_weak=current_weak,
            candidate_contact=candidate_contact,
            candidate_source=candidate_source,
            llm_contact_corrected=llm_contact_corrected,
            expected_blank_external_portal=expected_blank_external_portal,
            error="",
        )
        return report
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["verification_status"] = "error"
        return report


def apply_safe_updates(
    *,
    repo: TrackerEntryRepository,
    rows: list[dict[str, Any]],
    actor_label: str,
    organization_id: UUID | None = None,
) -> None:
    for row in rows:
        if not row.get("safe_to_apply"):
            continue
        if row.get("applied"):
            continue
        try:
            result = repo.apply_override(
                entry_id=UUID(str(row["entry_id"])),
                field_name="demand_contact",
                new_value=str(row["candidate_contact"] or "").strip(),
                actor_user_id=None,
                actor_label=actor_label,
                change_source="system",
            )
            row["applied"] = True
            row["apply_changed"] = bool(result.changed) if result is not None else False
            if organization_id is not None and result is not None and result.changed:
                try:
                    from backend.api.app import _invalidate_home_bootstrap_snapshot_best_effort
                    from backend.api.app import _upsert_tracker_entry_snapshots_best_effort

                    _upsert_tracker_entry_snapshots_best_effort(
                        organization_id=organization_id,
                        rows=[result.entry],
                    )
                    _invalidate_home_bootstrap_snapshot_best_effort(organization_id=organization_id)
                except Exception:
                    pass
        except Exception as exc:
            row["error"] = f"apply_failed: {type(exc).__name__}: {exc}"
            row["verification_status"] = "error"


def write_report_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(REPORT_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in REPORT_FIELDS})


def write_report_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_output_prefix(raw_prefix: str) -> Path:
    if raw_prefix.strip():
        return Path(raw_prefix).expanduser()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return ROOT / f"tracker_contact_reextract_supabase_{stamp}"


def main() -> int:
    args = parse_args()
    load_env_file(args.env_file)
    service_key = resolve_service_key()
    if not service_key:
        raise SystemExit("missing public data service key")

    reset_tracker_entry_repository()
    repo = get_tracker_entry_repository()
    repo_rows = list_all_tracker_entries(repo=repo, page_size=max(1, int(args.page_size or 500)))
    repo_rows = [row for row in repo_rows if str(row.get("source_bid_no") or "").strip()]
    if str(args.input_csv or "").strip():
        rows = load_subset_entries(repo_rows=repo_rows, input_csv=str(args.input_csv or "").strip())
    else:
        rows = list(repo_rows)
    if args.only_needs_llm:
        rows = [row for row in rows if _needs_contact_llm(contact=str(row.get("demand_contact") or "").strip())]
    if args.limit > 0:
        rows = rows[: int(args.limit)]

    llm_config = load_llm_correction_config()
    llm_enabled = bool(llm_config.enabled)
    total = len(rows)
    print(
        json.dumps(
            {
                "total_targets": total,
                "workers": max(1, int(args.workers or 4)),
                "llm_enabled": llm_enabled,
                "force_llm_contact": bool(args.force_llm_contact),
                "apply_safe": bool(args.apply_safe),
                "only_needs_llm": bool(args.only_needs_llm),
            },
            ensure_ascii=False,
        )
    )

    processed: list[dict[str, Any]] = []
    lock = threading.Lock()
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers or 4))) as executor:
        futures = [
            executor.submit(
                process_entry,
                entry=row,
                service_key=service_key,
                llm_enabled=llm_enabled,
                force_llm_contact=bool(args.force_llm_contact),
            )
            for row in rows
        ]
        for future in as_completed(futures):
            report = future.result()
            processed.append(report)
            with lock:
                completed += 1
                if completed % 25 == 0 or completed == total:
                    print(
                        json.dumps(
                            {
                                "processed": completed,
                                "total": total,
                                "safe_improvement": sum(1 for item in processed if item.get("verification_status") == "safe_improvement"),
                                "still_blank": sum(1 for item in processed if item.get("verification_status") == "still_blank"),
                                "error": sum(1 for item in processed if item.get("verification_status") == "error"),
                            },
                            ensure_ascii=False,
                        )
                    )

    processed.sort(key=lambda item: (str(item.get("verification_status") or ""), str(item.get("bid_no") or "")))

    actor_label = str(args.actor_label or "").strip() or f"contact_reextract_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if args.apply_safe:
        apply_safe_updates(
            repo=repo,
            rows=processed,
            actor_label=actor_label,
            organization_id=organization_id,
        )

    status_counts = Counter(str(row.get("verification_status") or "") for row in processed)
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_targets": total,
        "llm_enabled": llm_enabled,
        "apply_safe": bool(args.apply_safe),
        "actor_label": actor_label if args.apply_safe else "",
        "status_counts": dict(status_counts),
        "safe_to_apply_count": sum(1 for row in processed if row.get("safe_to_apply")),
        "applied_count": sum(1 for row in processed if row.get("applied")),
        "apply_changed_count": sum(1 for row in processed if row.get("apply_changed")),
        "llm_contact_corrected_count": sum(1 for row in processed if row.get("llm_contact_corrected")),
        "seed_fetch_sources": dict(Counter(str(row.get("seed_fetch_source") or "") for row in processed)),
    }

    output_prefix = build_output_prefix(str(args.output_prefix or ""))
    csv_path = output_prefix.with_suffix(".csv")
    json_path = output_prefix.with_suffix(".json")
    payload = {
        "summary": summary,
        "items": [{field: row.get(field, "") for field in REPORT_FIELDS} for row in processed],
    }
    write_report_csv(csv_path, processed)
    write_report_json(json_path, payload)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(str(csv_path))
    print(str(json_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
