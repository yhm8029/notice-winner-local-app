from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Callable

import requests

from .attachment_text_extract import AttachmentTextLoadResult
from .attachment_text_extract import download_attachment_text
from .attachment_text_extract import download_attachment_text_with_timing as _download_attachment_text_with_timing
from .native_contract_lookup import get_last_contract_lookup_meta
from .native_contract_lookup import resolve_contract_by_bid_no
from .native_gui_rules import WinnerExtraction
from .native_gui_rules import decode_html_and_strip
from .native_gui_rules import extract_area_number
from .native_gui_rules import extract_client_location
from .native_gui_rules import extract_completion_expected_date
from .native_gui_rules import extract_construction_start_date
from .native_gui_rules import extract_contact_from_notice_text
from .native_gui_rules import extract_contact_resolution_from_notice_text
from .native_gui_rules import extract_duration_days_from_text
from .native_gui_rules import extract_labeled_cost_text
from .native_gui_rules import extract_notice_area_value
from .native_gui_rules import extract_notice_cost_won
from .native_gui_rules import extract_site_location
from .native_gui_rules import format_won
from .native_gui_rules import get_manual_field_overrides
from .native_gui_rules import has_external_competition_portal_only_contact
from .native_gui_rules import is_auxiliary_service_project
from .native_gui_rules import looks_like_architecture_firm_name
from .native_gui_rules import normalize_contact_candidate
from .native_gui_rules import PHONE_FLEX_PAT
from .native_gui_rules import winner_name_extractor
from ..repositories.tracker_entries import estimate_tracker_building_automation_amount as _estimate_tracker_building_automation_amount
from .native_llm_correction import load_llm_correction_config_from_options
from .native_llm_correction import LlmCorrectionResult
from .native_llm_correction import maybe_correct_notice_fields_with_llm
from .native_export_backend_attachment_runtime import attachment_doc_score as _attachment_doc_score_impl
from .native_export_backend_attachment_runtime import fetch_attachment_texts as _fetch_attachment_texts_impl
from .native_export_backend_attachment_runtime import maybe_rescue_attachment_fields_with_synap as _maybe_rescue_attachment_fields_with_synap_impl
from .native_export_backend_attachment_runtime import merge_synap_note as _merge_synap_note_impl
from .native_export_backend_attachment_runtime import missing_synap_rescue_fields as _missing_synap_rescue_fields_impl
from .native_export_backend_attachment_runtime import select_best_attachment_contact as _select_best_attachment_contact_impl
from .native_export_backend_attachment_runtime import should_continue_attachment_scan as _should_continue_attachment_scan_impl
from .native_export_backend_contract_runtime import build_fallback_notes as _build_fallback_notes_impl
from .native_export_backend_contract_runtime import compute_completion_expected_date as _compute_completion_expected_date_impl
from .native_export_backend_contract_runtime import resolve_building_automation_amount as _resolve_building_automation_amount_impl
from .native_export_backend_contract_runtime import resolve_contract_evidence as _resolve_contract_evidence_impl
from .native_export_backend_contract_runtime import resolve_contract_hit_note as _resolve_contract_hit_note_impl
from .native_export_backend_contract_runtime import resolve_contract_reason_code as _resolve_contract_reason_code_impl
from .native_export_backend_contract_runtime import resolve_contract_score as _resolve_contract_score_impl
from .native_export_backend_contract_runtime import resolve_contract_source_type as _resolve_contract_source_type_impl
from .native_export_backend_contract_runtime import resolve_contract_status as _resolve_contract_status_impl
from .native_export_backend_contract_runtime import resolve_contract_winner_pattern as _resolve_contract_winner_pattern_impl
from .native_export_backend_contract_runtime import select_building_automation_cost_candidate as _select_building_automation_cost_candidate_impl
from .native_export_backend_batch_runtime import load_grouped_items as _load_grouped_items_impl
from .native_export_backend_batch_runtime import process_grouped_items_parallel as _process_grouped_items_parallel_impl
from .native_export_backend_batch_runtime import write_output_rows as _write_output_rows_impl
from .native_export_backend_field_runtime import build_resolved_export_fields as _build_resolved_export_fields_impl
from .native_export_backend_notice_runtime import extract_notice_fields as _extract_notice_fields_impl
from .native_export_backend_notice_runtime import fetch_page_text as _fetch_page_text_impl
from .native_export_backend_notice_runtime import has_attachment_enrichment_fields as _has_attachment_enrichment_fields_impl
from .native_export_backend_notice_runtime import has_attachment_skip_fields as _has_attachment_skip_fields_impl
from .native_export_backend_notice_runtime import has_core_export_fields as _has_core_export_fields_impl
from .native_export_backend_notice_runtime import has_page_enrichment_fields as _has_page_enrichment_fields_impl
from .native_export_backend_notice_runtime import resolve_candidate_winner_name as _resolve_candidate_winner_name_impl
from .native_export_backend_notice_runtime import should_try_attachment as _should_try_attachment_impl
from .native_export_backend_notice_flow_runtime import collect_notice_context as _collect_notice_context_impl
from .native_export_backend_notice_flow_runtime import enrich_with_attachment_documents as _enrich_with_attachment_documents_impl
from .native_export_backend_page_runtime import build_page_fetch_urls as _build_page_fetch_urls_impl
from .native_export_backend_page_runtime import fetch_page_documents as _fetch_page_documents_impl
from .native_export_backend_page_runtime import pick_primary_document as _pick_primary_document_impl
from .native_export_backend_row_runtime import build_output_row as _build_output_row_impl
from .native_export_backend_row_runtime import build_progress_message as _build_progress_message_impl
from ._native_export_backend_runtime_support_helpers import collect_attachment_documents as _collect_attachment_documents_impl
from ._native_export_backend_runtime_support_helpers import load_attachment_text_with_timing as _load_attachment_text_with_timing_impl
from ._native_export_backend_runtime_support_helpers import pick_best_match as _pick_best_match_impl
from ._native_export_backend_runtime_support_helpers import raise_if_stop_requested as _raise_if_stop_requested_impl
from .synap_text_extract import download_notice_attachment_text_via_synap

REQUEST_TIMEOUT_SEC = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
ATTACHMENT_FIELD_COUNT = 10
MAX_ATTACHMENT_DOCS = 3
MIN_ATTACHMENT_SCAN_DOCS = 2


def _default_export_row_max_workers(*, getenv_fn: Callable[[str, str], str] | None = None) -> int:
    getenv = getenv_fn or os.getenv
    raw_value = str(getenv("WINNER_PIPELINE_EXPORT_ROW_WORKERS", "12") or "").strip() or "12"
    try:
        return max(1, int(raw_value))
    except ValueError:
        return 12


EXPORT_ROW_MAX_WORKERS = _default_export_row_max_workers()


def _normalize_export_contact_value(value: str, org_name: str) -> str:
    raw = str(value or "").strip()
    if not raw or not PHONE_FLEX_PAT.search(raw):
        return raw
    normalized = normalize_contact_candidate(raw, org_name)
    return normalized or raw


@dataclass(frozen=True)
class PageDocument:
    url: str
    title: str
    text: str


@dataclass(frozen=True)
class AttachmentDocument:
    url: str
    file_name: str
    score: int
    is_announcement_doc: bool
    text: str = ""


@dataclass(frozen=True)
class ExtractedNoticeFields:
    winner_name: str = ""
    winner_pattern: str = ""
    gross_area_scale: str = ""
    construction_cost: str = ""
    demand_contact: str = ""
    client_location: str = ""
    site_location: str = ""
    architect_office: str = ""
    construction_start_date: str = ""
    construction_duration_days: str = ""
    completion_expected_date_explicit: str = ""
    building_automation_estimated_amount: str = ""
    llm_corrected_fields: tuple[str, ...] = ()
    demand_contact_resolution_status: str = ""
    demand_contact_resolution_reason: str = ""
    demand_contact_resolution_phase: str = ""
    demand_contact_resolution_role: str = ""
    demand_contact_resolution_owner_side: str = ""
    demand_contact_resolution_owner_side_basis: str = ""


@dataclass(frozen=True)
class ResolvedField:
    value: str = ""
    source: str = ""


def _resolve_field(*, confirmed_value: str = "", fallback_value: str = "", fallback_source: str = "") -> ResolvedField:
    confirmed = str(confirmed_value or "").strip()
    if confirmed:
        return ResolvedField(value=confirmed, source="confirmed_extracted")
    fallback = str(fallback_value or "").strip()
    if fallback:
        return ResolvedField(value=fallback, source=str(fallback_source or "").strip())
    return ResolvedField()


def _looks_like_specific_architecture_firm_name(value: str) -> bool:
    return looks_like_architecture_firm_name(value)


@dataclass(frozen=True)
class AttachmentTextPayload:
    all_text: str = ""
    announcement_text: str = ""
    tried_count: int = 0
    parsed_count: int = 0
    download_ms: int = 0
    parse_ms: int = 0


def run_post_collect_native(
    internal_nav_csv: Path,
    out_csv: Path,
    *,
    params: dict[str, object] | None = None,
    progress_cb: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> Path:
    advanced_options = dict((params or {}).get("_advanced_options") or {}) if isinstance(params, dict) else {}
    llm_config = load_llm_correction_config_from_options(advanced_options)
    llm_remaining = int(llm_config.max_rows or 0)
    grouped_items = _load_grouped_items_impl(internal_nav_csv)
    out_rows: list[dict[str, str]] = []
    if llm_config.enabled and llm_remaining > 0:
        for group_item in grouped_items:
            _raise_if_stop_requested(should_stop)
            out_row, progress_message, llm_used = _build_post_collect_output_row(
                group_item=group_item,
                llm_config=llm_config,
                use_llm=llm_remaining > 0,
                should_stop=should_stop,
            )
            out_rows.append(out_row)
            if llm_used:
                llm_remaining -= 1
            if progress_cb is not None and progress_message:
                progress_cb(progress_message)
    else:
        worker_count = _resolve_export_worker_count(
            advanced_options=advanced_options,
            grouped_item_count=len(grouped_items),
        )
        if worker_count <= 1:
            for group_item in grouped_items:
                _raise_if_stop_requested(should_stop)
                out_row, progress_message, _ = _build_post_collect_output_row(
                    group_item=group_item,
                    llm_config=llm_config,
                    use_llm=False,
                    should_stop=should_stop,
                )
                out_rows.append(out_row)
                if progress_cb is not None and progress_message:
                    progress_cb(progress_message)
        else:
            out_rows = _process_grouped_items_parallel_impl(
                grouped_items=grouped_items,
                worker_count=worker_count,
                build_output_row_fn=_build_post_collect_output_row,
                llm_config=llm_config,
                progress_cb=progress_cb,
                should_stop=should_stop,
                raise_if_stop_requested_fn=_raise_if_stop_requested,
            )

    _write_output_rows_impl(out_csv, out_rows)
    return out_csv


def _resolve_export_worker_count(*, advanced_options: dict[str, object], grouped_item_count: int) -> int:
    worker_count = EXPORT_ROW_MAX_WORKERS
    raw_value = str(advanced_options.get("export_row_workers") or "").strip()
    if raw_value:
        try:
            worker_count = int(raw_value)
        except ValueError:
            worker_count = EXPORT_ROW_MAX_WORKERS
    return min(max(1, worker_count), max(1, grouped_item_count))


def _build_post_collect_output_row(
    *,
    group_item: tuple[tuple[str, str], list[dict[str, str]]],
    llm_config: object,
    use_llm: bool,
    should_stop: Callable[[], bool] | None = None,
) -> tuple[dict[str, str], str, bool]:
    _raise_if_stop_requested(should_stop)
    (bid_no, bid_ord), rows = group_item
    best_row = _pick_best_match(rows)
    project_name_norm = str(best_row.get("project_name_norm") or "").strip()
    org_name = str(best_row.get("org_name") or "").strip()
    manual_overrides = get_manual_field_overrides(bid_no)
    search_url = str(best_row.get("internal_search_url") or "").strip()
    base_url = str(best_row.get("base_url") or "").strip()
    notice_url = str(best_row.get("notice_url") or "").strip()
    presmpt_prce = str(best_row.get("presmpt_prce") or "").strip()
    spec_doc_url = str(best_row.get("spec_doc_url") or "").strip()
    spec_doc_file_name = str(best_row.get("spec_doc_file_name") or "").strip()

    timing_ms = {
        "contract_lookup": 0,
        "page_fetch": 0,
        "attachment_download": 0,
        "attachment_parse": 0,
    }
    page_urls = _build_page_fetch_urls(
        notice_url=notice_url,
        base_url=base_url,
        search_url=search_url,
    )
    announce_date = str(best_row.get("announce_date") or "").strip()

    def _timed_contract_lookup() -> tuple[object, int, object]:
        _raise_if_stop_requested(should_stop)
        started = time.perf_counter()
        result = resolve_contract_by_bid_no(
            bid_no=bid_no,
            project_name_norm=project_name_norm,
            announce_date=announce_date,
            org_name=org_name,
        )
        return result, int(round((time.perf_counter() - started) * 1000)), get_last_contract_lookup_meta()

    def _timed_fetch_pages(urls: list[str]) -> tuple[list[PageDocument], int]:
        _raise_if_stop_requested(should_stop)
        started = time.perf_counter()
        result = _fetch_page_documents(urls, should_stop=should_stop)
        return result, int(round((time.perf_counter() - started) * 1000))

    with ThreadPoolExecutor(max_workers=2) as executor:
        contract_future = executor.submit(_timed_contract_lookup)
        first_page_future = executor.submit(_timed_fetch_pages, page_urls[:1])
        contract_hit, timing_ms["contract_lookup"], contract_lookup_meta = contract_future.result()
        first_page_documents, first_page_elapsed = first_page_future.result()
    timing_ms["page_fetch"] += first_page_elapsed
    notice_context = _collect_notice_context_impl(
        page_urls=page_urls,
        project_name_norm=project_name_norm,
        org_name=org_name,
        should_stop=should_stop,
        raise_if_stop_requested_fn=_raise_if_stop_requested,
        fetch_page_documents_fn=_fetch_page_documents,
        pick_primary_document_fn=_pick_primary_document,
        extract_notice_fields_fn=_extract_notice_fields,
        has_page_enrichment_fields_fn=_has_page_enrichment_fields,
        initial_documents=first_page_documents,
    )
    timing_ms["page_fetch"] += notice_context.additional_page_fetch_ms
    documents = notice_context.documents
    preferred_document = notice_context.preferred_document
    title = notice_context.title
    combined_text = notice_context.combined_text
    extracted = notice_context.extracted

    attachment_docs = _collect_attachment_documents(best_row, spec_doc_url=spec_doc_url, spec_doc_file_name=spec_doc_file_name)
    attachment_payload = AttachmentTextPayload()
    attachment_note = ""
    synap_note = ""
    if _should_try_attachment(attachment_docs=attachment_docs, extracted=extracted):
        attachment_enrichment = _enrich_with_attachment_documents_impl(
            attachment_docs=attachment_docs,
            extracted=extracted,
            combined_text=combined_text,
            title=title,
            bid_no=bid_no,
            bid_ord=bid_ord,
            org_name=org_name,
            best_row=best_row,
            should_stop=should_stop,
            timing_ms=timing_ms,
            raise_if_stop_requested_fn=_raise_if_stop_requested,
            load_attachment_text_with_timing_fn=_load_attachment_text_with_timing,
            extract_notice_fields_fn=_extract_notice_fields,
            extract_contact_from_notice_text_fn=extract_contact_from_notice_text,
            select_best_attachment_contact_fn=_select_best_attachment_contact,
            maybe_rescue_attachment_fields_with_synap_fn=_maybe_rescue_attachment_fields_with_synap,
            merge_synap_note_fn=_merge_synap_note,
            should_continue_attachment_scan_fn=_should_continue_attachment_scan,
            replace_fn=replace,
            attachment_text_payload_cls=AttachmentTextPayload,
        )
        extracted = attachment_enrichment.extracted
        attachment_payload = attachment_enrichment.payload
        attachment_note = attachment_enrichment.attachment_note
        synap_note = attachment_enrichment.synap_note
    elif attachment_docs:
        attachment_note = "attachment_skipped:page_core_fields"
    if use_llm:
        _raise_if_stop_requested(should_stop)
        llm_result = maybe_correct_notice_fields_with_llm(
            config=llm_config,
            text=combined_text,
            project_name=title,
            org_name=org_name,
            area=extracted.gross_area_scale,
            cost=extracted.construction_cost,
            contact=extracted.demand_contact,
        )
    else:
        llm_result = LlmCorrectionResult()
    llm_used = bool(llm_result.corrected_fields)
    llm_corrected_fields = tuple(field for field in llm_result.corrected_fields if field != "contact")
    if llm_result.corrected_fields:
        extracted = replace(
            extracted,
            gross_area_scale=llm_result.area or extracted.gross_area_scale,
            construction_cost=llm_result.cost or extracted.construction_cost,
            llm_corrected_fields=llm_corrected_fields,
        )

    resolved_fields = _build_resolved_export_fields_impl(
        extracted=extracted,
        contract_hit=contract_hit,
        best_row=best_row,
        manual_overrides=manual_overrides,
        external_portal_contact_expected_blank=has_external_competition_portal_only_contact(combined_text),
        presmpt_prce=presmpt_prce,
        org_name=org_name,
        resolved_field_cls=ResolvedField,
        format_won_fn=format_won,
        normalize_export_contact_value_fn=_normalize_export_contact_value,
        resolve_field_fn=_resolve_field,
        looks_like_specific_architecture_firm_name_fn=_looks_like_specific_architecture_firm_name,
        resolve_contract_source_type_fn=_resolve_contract_source_type,
        select_building_automation_cost_candidate_fn=_select_building_automation_cost_candidate,
        resolve_building_automation_amount_fn=_resolve_building_automation_amount,
        compute_completion_expected_date_fn=_compute_completion_expected_date,
        resolve_contract_status_fn=_resolve_contract_status,
        resolve_contract_score_fn=_resolve_contract_score,
        resolve_contract_reason_code_fn=_resolve_contract_reason_code,
        resolve_contract_winner_pattern_fn=_resolve_contract_winner_pattern,
        resolve_contract_evidence_fn=_resolve_contract_evidence,
        resolve_contract_hit_note_fn=_resolve_contract_hit_note,
        build_fallback_notes_fn=_build_fallback_notes,
    )

    out_row = _build_output_row_impl(
        bid_no=bid_no,
        bid_ord=bid_ord,
        best_row={**best_row, "source_type": resolved_fields.contract_source_type},
        preferred_document_url=preferred_document.url,
        notice_url=notice_url,
        search_url=search_url,
        base_url=base_url,
        title=title,
        winner_name=resolved_fields.winner_name,
        confidence=resolved_fields.confidence,
        winner_pattern=resolved_fields.winner_pattern,
        score=resolved_fields.score,
        reason_code=resolved_fields.reason_code,
        review_flag=resolved_fields.review_flag,
        contract_name=(contract_hit.contract_name if contract_hit else "") or title or project_name_norm,
        contract_date=str(contract_hit.contract_date or "") if contract_hit else "",
        notice_construction_cost=resolved_fields.notice_construction_cost,
        contract_amount=resolved_fields.contract_amount,
        gross_area_scale=resolved_fields.gross_area_scale,
        demand_contact=resolved_fields.demand_contact,
        client_location=resolved_fields.client_location,
        site_location=resolved_fields.site_location,
        architect_office=resolved_fields.architect_office,
        construction_start_date=resolved_fields.construction_start_date,
        construction_duration_days=resolved_fields.construction_duration_days,
        completion_expected_date_explicit=resolved_fields.completion_expected_date_explicit,
        completion_expected_date_computed=resolved_fields.completion_expected_date_computed,
        building_auto_est=resolved_fields.building_auto_est,
        evidence_source=resolved_fields.evidence_source,
        status=resolved_fields.status,
        spec_doc_file_name=spec_doc_file_name,
        contract_hit_note=resolved_fields.contract_hit_note,
        attachment_note=attachment_note,
        synap_note=synap_note,
        llm_corrected_fields=extracted.llm_corrected_fields,
        extracted_contact_resolution_status=extracted.demand_contact_resolution_status,
        extracted_contact_resolution_reason=extracted.demand_contact_resolution_reason,
        extracted_contact_resolution_phase=extracted.demand_contact_resolution_phase,
        extracted_contact_resolution_role=extracted.demand_contact_resolution_role,
        extracted_contact_resolution_owner_side=extracted.demand_contact_resolution_owner_side,
        extracted_contact_resolution_owner_side_basis=extracted.demand_contact_resolution_owner_side_basis,
        expected_blank_external_portal=resolved_fields.expected_blank_external_portal,
        expected_blank_contact_review=resolved_fields.expected_blank_contact_review,
        fallback_notes=resolved_fields.fallback_notes,
        join_non_empty_fn=_join_non_empty,
    )
    progress_message = _build_progress_message_impl(
        bid_no=bid_no,
        status=resolved_fields.status,
        winner_name=resolved_fields.winner_name,
        gross_area_scale=extracted.gross_area_scale,
        construction_cost=extracted.construction_cost,
        contract_lookup_meta=contract_lookup_meta,
        document_count=len(documents),
        attachment_tried_count=attachment_payload.tried_count,
        attachment_parsed_count=attachment_payload.parsed_count,
        timing_ms=timing_ms,
    )
    return out_row, progress_message, llm_used


def _resolve_contract_source_type(contract_hit: object, winner_name: str) -> str:
    return _resolve_contract_source_type_impl(contract_hit, winner_name)


def _resolve_contract_status(*, contract_hit: object, winner_name: str, g2b_verified: str) -> str:
    return _resolve_contract_status_impl(contract_hit=contract_hit, winner_name=winner_name, g2b_verified=g2b_verified)


def _resolve_contract_score(contract_hit: object, winner_name: str) -> float:
    return _resolve_contract_score_impl(contract_hit, winner_name)


def _resolve_contract_reason_code(*, contract_hit: object, winner_name: str, g2b_verified: str, status: str) -> str:
    return _resolve_contract_reason_code_impl(
        contract_hit=contract_hit,
        winner_name=winner_name,
        g2b_verified=g2b_verified,
        status=status,
    )


def _resolve_contract_winner_pattern(contract_hit: object, winner_name: str, extracted_pattern: str) -> str:
    return _resolve_contract_winner_pattern_impl(contract_hit, winner_name, extracted_pattern)


def _resolve_contract_evidence(contract_hit: object, winner_name: str) -> str:
    return _resolve_contract_evidence_impl(contract_hit, winner_name)


def _resolve_contract_hit_note(contract_hit: object, winner_name: str) -> str:
    return _resolve_contract_hit_note_impl(contract_hit, winner_name)


def _pick_best_match(rows: list[dict[str, str]]) -> dict[str, str]:
    return _pick_best_match_impl(rows)


def _build_page_fetch_urls(*, notice_url: str, base_url: str, search_url: str) -> list[str]:
    return _build_page_fetch_urls_impl(notice_url=notice_url, base_url=base_url, search_url=search_url)


def _fetch_page_documents(
    urls: list[str],
    *,
    should_stop: Callable[[], bool] | None = None,
) -> list[PageDocument]:
    return _fetch_page_documents_impl(
        urls,
        fetch_page_text_fn=_fetch_page_text,
        raise_if_stop_requested_fn=_raise_if_stop_requested,
        page_document_cls=PageDocument,
        should_stop=should_stop,
    )


def _pick_primary_document(documents: list[PageDocument]) -> PageDocument:
    return _pick_primary_document_impl(documents, page_document_cls=PageDocument)


def _collect_attachment_documents(row: dict[str, str], *, spec_doc_url: str, spec_doc_file_name: str) -> list[AttachmentDocument]:
    return _collect_attachment_documents_impl(
        row,
        spec_doc_url=spec_doc_url,
        spec_doc_file_name=spec_doc_file_name,
        attachment_document_cls=AttachmentDocument,
        attachment_doc_score_fn=_attachment_doc_score,
    )


def _attachment_doc_score(file_name: str) -> int:
    return _attachment_doc_score_impl(file_name)

def _fetch_attachment_texts(documents: list[AttachmentDocument]) -> AttachmentTextPayload:
    return _fetch_attachment_texts_impl(
        documents,
        load_attachment_text_with_timing_fn=_load_attachment_text_with_timing,
        payload_cls=AttachmentTextPayload,
    )

def _raise_if_stop_requested(should_stop: Callable[[], bool] | None) -> None:
    return _raise_if_stop_requested_impl(should_stop)


def _load_attachment_text_with_timing(*, url: str, file_name: str) -> AttachmentTextLoadResult:
    return _load_attachment_text_with_timing_impl(
        url=url,
        file_name=file_name,
        download_attachment_text_fn=download_attachment_text,
        download_attachment_text_with_timing_fn=_download_attachment_text_with_timing,
    )


def _fetch_page_text(url: str) -> tuple[str, str]:
    return _fetch_page_text_impl(
        url,
        requests_get_fn=requests.get,
        decode_html_and_strip_fn=decode_html_and_strip,
        user_agent=USER_AGENT,
        request_timeout_sec=REQUEST_TIMEOUT_SEC,
    )


def _extract_notice_fields(*, title: str, text: str, project_name: str, org_name: str) -> ExtractedNoticeFields:
    return _extract_notice_fields_impl(
        title=title,
        text=text,
        project_name=project_name,
        org_name=org_name,
        winner_name_extractor_fn=winner_name_extractor,
        extracted_notice_fields_cls=ExtractedNoticeFields,
        extract_notice_area_value_fn=extract_notice_area_value,
        extract_notice_cost_won_fn=extract_notice_cost_won,
        format_won_fn=format_won,
        is_auxiliary_service_project_fn=is_auxiliary_service_project,
        extract_contact_from_notice_text_fn=extract_contact_from_notice_text,
        extract_contact_resolution_from_notice_text_fn=extract_contact_resolution_from_notice_text,
        extract_client_location_fn=extract_client_location,
        extract_site_location_fn=extract_site_location,
        extract_construction_start_date_fn=extract_construction_start_date,
        extract_duration_days_from_text_fn=extract_duration_days_from_text,
        extract_completion_expected_date_fn=extract_completion_expected_date,
        extract_labeled_cost_text_fn=extract_labeled_cost_text,
    )

def _select_building_automation_cost_candidate(
    *,
    notice_construction_cost: ResolvedField,
    contract_amount: ResolvedField,
    contract_source_type: str,
) -> tuple[str, str]:
    return _select_building_automation_cost_candidate_impl(
        notice_construction_cost=notice_construction_cost,
        contract_amount=contract_amount,
        contract_source_type=contract_source_type,
    )

def _compute_completion_expected_date(*, contract_date: str, duration_days: str, contract_source_type: str) -> str:
    return _compute_completion_expected_date_impl(
        contract_date=contract_date,
        duration_days=duration_days,
        contract_source_type=contract_source_type,
    )

def _resolve_building_automation_amount(
    *,
    explicit_value: str,
    construction_cost_candidate: str,
    candidate_label: str,
) -> ResolvedField:
    return _resolve_building_automation_amount_impl(
        explicit_value=explicit_value,
        construction_cost_candidate=construction_cost_candidate,
        candidate_label=candidate_label,
        resolved_field_cls=ResolvedField,
    )

def _build_fallback_notes(fields: dict[str, ResolvedField]) -> list[str]:
    return _build_fallback_notes_impl(fields)

def _join_non_empty(values: list[str], sep: str) -> str:
    return sep.join(value for value in values if str(value or "").strip())


def _has_page_enrichment_fields(extracted: ExtractedNoticeFields) -> bool:
    area_value = extract_area_number(extracted.gross_area_scale)
    return all(
        [
            extracted.demand_contact,
            50 <= area_value <= 2000000,
        ]
    )


def _has_core_export_fields(extracted: ExtractedNoticeFields, winner_name: str) -> bool:
    return all(
        [
            str(winner_name or "").strip(),
            extracted.gross_area_scale,
            extracted.construction_cost,
        ]
    )


def _has_attachment_enrichment_fields(extracted: ExtractedNoticeFields) -> bool:
    area_value = extract_area_number(extracted.gross_area_scale)
    return all(
        [
            extracted.construction_cost,
            50 <= area_value <= 2000000,
            extracted.demand_contact,
            _has_usable_schedule_period(extracted),
        ]
    )


def _has_attachment_skip_fields(extracted: ExtractedNoticeFields) -> bool:
    return _has_attachment_enrichment_fields(extracted)


def _has_usable_schedule_period(extracted: ExtractedNoticeFields) -> bool:
    duration_value = str(extracted.construction_duration_days or "").strip()
    if duration_value:
        try:
            if int(re.sub(r"[^0-9]", "", duration_value) or "0") >= 30:
                return True
        except Exception:
            pass
    for value in (
        str(extracted.construction_start_date or "").strip(),
    ):
        month_match = re.search(r"(\d{1,3})\s*개월", value)
        if month_match:
            return True
        day_match = re.search(r"(\d{1,4})\s*일", value)
        if day_match:
            try:
                if int(day_match.group(1)) >= 30:
                    return True
            except Exception:
                continue
    return False


def _resolve_candidate_winner_name(
    *,
    contract_hit: object,
    extracted: ExtractedNoticeFields,
    best_row: dict[str, str],
) -> str:
    candidates = [
        getattr(contract_hit, "contract_name", "") if contract_hit else "",
        extracted.winner_name,
        str(best_row.get("winner_name") or "").strip(),
        str(best_row.get("contract_name") or "").strip(),
    ]
    for candidate in candidates:
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _should_try_attachment(
    *,
    attachment_docs: list[AttachmentDocument],
    extracted: ExtractedNoticeFields,
) -> bool:
    if not attachment_docs:
        return False
    return not _has_attachment_skip_fields(extracted)


def _should_continue_attachment_scan(
    *,
    tried_count: int,
    available_count: int,
    extracted: ExtractedNoticeFields,
) -> bool:
    return _should_continue_attachment_scan_impl(
        tried_count=tried_count,
        available_count=available_count,
        extracted=extracted,
        min_attachment_scan_docs=MIN_ATTACHMENT_SCAN_DOCS,
        has_attachment_enrichment_fields_fn=_has_attachment_enrichment_fields,
    )

def _contact_specificity(value: str) -> int:
    contact = str(value or "").strip()
    if not contact:
        return -1
    left = contact.split("/", 1)[0].strip()
    return len(re.sub(r"\s+", "", left))


def _prefer_richer_contact(*, current_contact: str, candidate_contact: str) -> str:
    current = str(current_contact or "").strip()
    candidate = str(candidate_contact or "").strip()
    if not candidate:
        return current
    if not current:
        return candidate
    if _contact_specificity(candidate) > _contact_specificity(current):
        return candidate
    return current


def _select_best_attachment_contact(
    *,
    current_contact: str,
    announcement_contact: str,
    piece_contact: str,
    is_announcement_doc: bool,
) -> str:
    return _select_best_attachment_contact_impl(
        current_contact=current_contact,
        announcement_contact=announcement_contact,
        piece_contact=piece_contact,
        is_announcement_doc=is_announcement_doc,
    )

def _maybe_rescue_attachment_fields_with_synap(
    *,
    extracted: ExtractedNoticeFields,
    attachment_url: str,
    file_name: str,
    bid_no: str,
    bid_ord: str,
    project_name: str,
    org_name: str,
    unty_atch_file_no: str,
) -> tuple[ExtractedNoticeFields, tuple[str, ...]]:
    return _maybe_rescue_attachment_fields_with_synap_impl(
        extracted=extracted,
        attachment_url=attachment_url,
        file_name=file_name,
        bid_no=bid_no,
        bid_ord=bid_ord,
        project_name=project_name,
        org_name=org_name,
        unty_atch_file_no=unty_atch_file_no,
        extract_area_number_fn=extract_area_number,
        extract_notice_fields_fn=_extract_notice_fields,
        download_notice_attachment_text_via_synap_fn=download_notice_attachment_text_via_synap,
        missing_synap_rescue_fields_fn=_missing_synap_rescue_fields,
        replace_fn=replace,
    )

def _missing_synap_rescue_fields(extracted: ExtractedNoticeFields) -> tuple[str, ...]:
    return _missing_synap_rescue_fields_impl(extracted, extract_area_number_fn=extract_area_number)

def _merge_synap_note(current_note: str, rescued_fields: tuple[str, ...]) -> str:
    return _merge_synap_note_impl(current_note, rescued_fields)
