from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NoticeContextResult:
    documents: list[Any]
    preferred_document: Any
    title: str
    combined_text: str
    extracted: Any
    additional_page_fetch_ms: int = 0


@dataclass(frozen=True)
class AttachmentEnrichmentResult:
    extracted: Any
    payload: Any
    attachment_text: str
    attachment_note: str
    synap_note: str


def collect_notice_context(
    *,
    page_urls: list[str],
    project_name_norm: str,
    org_name: str,
    should_stop,
    raise_if_stop_requested_fn,
    fetch_page_documents_fn,
    pick_primary_document_fn,
    extract_notice_fields_fn,
    has_page_enrichment_fields_fn,
    initial_documents: list[Any] | None = None,
    perf_counter_fn=time.perf_counter,
) -> NoticeContextResult:
    documents = list(initial_documents or [])
    if documents:
        remaining_page_urls = list(page_urls[1:])
    else:
        raise_if_stop_requested_fn(should_stop)
        documents = list(fetch_page_documents_fn(page_urls[:1], should_stop=should_stop))
        remaining_page_urls = list(page_urls[1:])

    preferred_document = pick_primary_document_fn(documents)
    title = str(getattr(preferred_document, "title", "") or "").strip() or project_name_norm
    combined_text = "\n".join(str(getattr(doc, "text", "") or "") for doc in documents if str(getattr(doc, "text", "") or "").strip())
    extracted = extract_notice_fields_fn(
        title=title,
        text=combined_text,
        project_name=title,
        org_name=org_name,
    )

    additional_page_fetch_ms = 0
    if remaining_page_urls and not has_page_enrichment_fields_fn(extracted):
        raise_if_stop_requested_fn(should_stop)
        started = perf_counter_fn()
        documents.extend(fetch_page_documents_fn(remaining_page_urls, should_stop=should_stop))
        additional_page_fetch_ms = int(round((perf_counter_fn() - started) * 1000))
        preferred_document = pick_primary_document_fn(documents)
        title = str(getattr(preferred_document, "title", "") or "").strip() or project_name_norm
        combined_text = "\n".join(
            str(getattr(doc, "text", "") or "") for doc in documents if str(getattr(doc, "text", "") or "").strip()
        )
        extracted = extract_notice_fields_fn(
            title=title,
            text=combined_text,
            project_name=title,
            org_name=org_name,
        )

    return NoticeContextResult(
        documents=documents,
        preferred_document=preferred_document,
        title=title,
        combined_text=combined_text,
        extracted=extracted,
        additional_page_fetch_ms=additional_page_fetch_ms,
    )


def enrich_with_attachment_documents(
    *,
    attachment_docs: list[Any],
    extracted: Any,
    combined_text: str,
    title: str,
    bid_no: str,
    bid_ord: str,
    org_name: str,
    best_row: dict[str, str],
    should_stop,
    timing_ms: dict[str, int],
    raise_if_stop_requested_fn,
    load_attachment_text_with_timing_fn,
    extract_notice_fields_fn,
    extract_contact_from_notice_text_fn,
    select_best_attachment_contact_fn,
    maybe_rescue_attachment_fields_with_synap_fn,
    merge_synap_note_fn,
    should_continue_attachment_scan_fn,
    replace_fn,
    attachment_text_payload_cls,
) -> AttachmentEnrichmentResult:
    page_text = combined_text
    attachment_chunks: list[str] = []
    announcement_chunks: list[str] = []
    tried_count = 0
    parsed_count = 0
    synap_note = ""

    for document in attachment_docs:
        raise_if_stop_requested_fn(should_stop)
        tried_count += 1
        result = load_attachment_text_with_timing_fn(url=document.url, file_name=document.file_name)
        timing_ms["attachment_download"] += int(getattr(result, "download_ms", 0) or 0)
        timing_ms["attachment_parse"] += int(getattr(result, "parse_ms", 0) or 0)
        attachment_piece = str(getattr(result, "text", "") or "")
        if not attachment_piece:
            continue
        chunk = "\n".join(part for part in [document.file_name, attachment_piece] if str(part or "").strip()).strip()
        if not chunk:
            continue
        parsed_count += 1
        attachment_chunks.append(chunk)
        if document.is_announcement_doc:
            announcement_chunks.append(chunk)

        combined_text = "\n\n".join(part for part in [page_text, *attachment_chunks] if str(part or "").strip())
        extracted = extract_notice_fields_fn(
            title=title,
            text=combined_text,
            project_name=title,
            org_name=org_name,
        )
        piece_contact = extract_contact_from_notice_text_fn(attachment_piece, org_name)
        announcement_contact = extract_contact_from_notice_text_fn(
            "\n\n".join(announcement_chunks).strip() or attachment_piece,
            org_name,
        )
        best_contact = select_best_attachment_contact_fn(
            current_contact=extracted.demand_contact,
            announcement_contact=announcement_contact,
            piece_contact=piece_contact,
            is_announcement_doc=document.is_announcement_doc,
        )
        if best_contact:
            extracted = replace_fn(extracted, demand_contact=best_contact)
        extracted, rescued_fields = maybe_rescue_attachment_fields_with_synap_fn(
            extracted=extracted,
            attachment_url=document.url,
            file_name=document.file_name,
            bid_no=bid_no,
            bid_ord=bid_ord,
            project_name=title,
            org_name=org_name,
            unty_atch_file_no=str(
                best_row.get("item_pbanc_unty_atch_file_no")
                or best_row.get("itemPbancUntyAtchFileNo")
                or ""
            ).strip(),
        )
        if rescued_fields:
            synap_note = merge_synap_note_fn(synap_note, rescued_fields)
        if not should_continue_attachment_scan_fn(
            tried_count=tried_count,
            available_count=len(attachment_docs),
            extracted=extracted,
        ):
            break

    payload = attachment_text_payload_cls(
        all_text="\n\n".join(attachment_chunks).strip(),
        announcement_text="\n\n".join(announcement_chunks).strip(),
        tried_count=tried_count,
        parsed_count=parsed_count,
        download_ms=timing_ms["attachment_download"],
        parse_ms=timing_ms["attachment_parse"],
    )
    attachment_text = str(getattr(payload, "all_text", "") or "")
    attachment_note = (
        f"attachment_parsed:{payload.parsed_count}/{payload.tried_count}"
        if payload.parsed_count
        else f"attachment_tried:{payload.tried_count}/0"
    )
    return AttachmentEnrichmentResult(
        extracted=extracted,
        payload=payload,
        attachment_text=attachment_text,
        attachment_note=attachment_note,
        synap_note=synap_note,
    )
