from __future__ import annotations

from pathlib import Path
from typing import Any


def attachment_doc_score(file_name: str) -> int:
    score = 0
    value = str(file_name or "").strip()
    lowered = value.lower()
    if "공고" in value:
        score += 10
    if "지침" in value or "과업" in value:
        score += 6
    if "제안" in value:
        score += 3
    if lowered.endswith(".hwpx"):
        score += 5
    elif lowered.endswith(".pdf"):
        score += 4
    elif lowered.endswith(".hwp"):
        score += 2
    return score

def fetch_attachment_texts(documents: list[Any], *, load_attachment_text_with_timing_fn, payload_cls) -> Any:
    all_chunks: list[str] = []
    announcement_chunks: list[str] = []
    tried_count = 0
    parsed_count = 0
    download_ms = 0
    parse_ms = 0
    for document in documents:
        tried_count += 1
        result = load_attachment_text_with_timing_fn(url=document.url, file_name=document.file_name)
        download_ms += result.download_ms
        parse_ms += result.parse_ms
        text = result.text
        if not text:
            continue
        chunk = "\n".join(part for part in [document.file_name, text] if part).strip()
        if not chunk:
            continue
        parsed_count += 1
        all_chunks.append(chunk)
        if document.is_announcement_doc:
            announcement_chunks.append(chunk)
    return payload_cls(
        all_text="\n\n".join(all_chunks).strip(),
        announcement_text="\n\n".join(announcement_chunks).strip(),
        tried_count=tried_count,
        parsed_count=parsed_count,
        download_ms=download_ms,
        parse_ms=parse_ms,
    )


def should_continue_attachment_scan(
    *,
    tried_count: int,
    available_count: int,
    extracted: Any,
    min_attachment_scan_docs: int,
    has_attachment_enrichment_fields_fn,
) -> bool:
    if tried_count >= available_count:
        return False
    if tried_count < min(min_attachment_scan_docs, available_count):
        return True
    return not has_attachment_enrichment_fields_fn(extracted)


def contact_specificity(value: str) -> int:
    import re

    contact = str(value or "").strip()
    if not contact:
        return -1
    left = contact.split("/", 1)[0].strip()
    return len(re.sub(r"\s+", "", left))


def prefer_richer_contact(*, current_contact: str, candidate_contact: str) -> str:
    current = str(current_contact or "").strip()
    candidate = str(candidate_contact or "").strip()
    if not candidate:
        return current
    if not current:
        return candidate
    if contact_specificity(candidate) > contact_specificity(current):
        return candidate
    return current


def select_best_attachment_contact(
    *,
    current_contact: str,
    announcement_contact: str,
    piece_contact: str,
    is_announcement_doc: bool,
) -> str:
    best_contact = prefer_richer_contact(
        current_contact=current_contact,
        candidate_contact=announcement_contact,
    )
    if is_announcement_doc or not str(announcement_contact or "").strip():
        best_contact = prefer_richer_contact(
            current_contact=best_contact,
            candidate_contact=piece_contact,
        )
    return best_contact


def maybe_rescue_attachment_fields_with_synap(
    *,
    extracted: Any,
    attachment_url: str,
    file_name: str,
    bid_no: str,
    bid_ord: str,
    project_name: str,
    org_name: str,
    unty_atch_file_no: str,
    extract_area_number_fn,
    extract_notice_fields_fn,
    download_notice_attachment_text_via_synap_fn,
    missing_synap_rescue_fields_fn,
    replace_fn,
) -> tuple[Any, tuple[str, ...]]:
    missing_fields = missing_synap_rescue_fields_fn(extracted)
    if not missing_fields:
        return extracted, ()
    suffix = Path(str(file_name or "").strip()).suffix.lower()
    if suffix not in {".hwp", ".hwpx"}:
        return extracted, ()
    if not str(attachment_url or "").strip() or not str(bid_no or "").strip():
        return extracted, ()
    synap_result = download_notice_attachment_text_via_synap_fn(
        bid_no=bid_no,
        bid_ord=bid_ord,
        attachment_url=attachment_url,
        unty_atch_file_no=unty_atch_file_no,
        max_pages=30,
    )
    synap_text = str(synap_result.text or "").strip()
    if not synap_text:
        return extracted, ()
    synap_fields = extract_notice_fields_fn(
        title=str(file_name or "").strip() or project_name,
        text=synap_text,
        project_name=project_name,
        org_name=org_name,
    )

    rescued: list[str] = []
    area_value = extract_area_number_fn(synap_fields.gross_area_scale)
    gross_area_scale = extracted.gross_area_scale
    if not gross_area_scale and "area" in missing_fields and 50 <= area_value <= 2000000:
        gross_area_scale = synap_fields.gross_area_scale
        rescued.append("area")

    construction_cost = extracted.construction_cost
    if not construction_cost and "cost" in missing_fields and str(synap_fields.construction_cost or "").strip():
        construction_cost = synap_fields.construction_cost
        rescued.append("cost")

    demand_contact = extracted.demand_contact
    if not demand_contact and "contact" in missing_fields and str(synap_fields.demand_contact or "").strip():
        demand_contact = synap_fields.demand_contact
        rescued.append("contact")

    if not rescued:
        return extracted, ()

    contact_resolution_kwargs: dict[str, str] = {}
    if "contact" in rescued:
        contact_resolution_kwargs = {
            "demand_contact_resolution_status": synap_fields.demand_contact_resolution_status,
            "demand_contact_resolution_reason": synap_fields.demand_contact_resolution_reason,
            "demand_contact_resolution_phase": synap_fields.demand_contact_resolution_phase,
            "demand_contact_resolution_role": synap_fields.demand_contact_resolution_role,
            "demand_contact_resolution_owner_side": synap_fields.demand_contact_resolution_owner_side,
            "demand_contact_resolution_owner_side_basis": synap_fields.demand_contact_resolution_owner_side_basis,
        }
    return (
        replace_fn(
            extracted,
            gross_area_scale=gross_area_scale,
            construction_cost=construction_cost,
            demand_contact=demand_contact,
            **contact_resolution_kwargs,
        ),
        tuple(rescued),
    )


def missing_synap_rescue_fields(extracted: Any, *, extract_area_number_fn) -> tuple[str, ...]:
    missing: list[str] = []
    area_value = extract_area_number_fn(extracted.gross_area_scale)
    if not (50 <= area_value <= 2000000):
        missing.append("area")
    if not str(extracted.construction_cost or "").strip():
        missing.append("cost")
    if not str(extracted.demand_contact or "").strip():
        missing.append("contact")
    return tuple(missing)


def merge_synap_note(current_note: str, rescued_fields: tuple[str, ...]) -> str:
    fields = [field for field in rescued_fields if str(field or "").strip()]
    if not fields:
        return current_note
    current = str(current_note or "").strip()
    if not current:
        return f"synap_rescued={','.join(fields)}"
    prefix = "synap_rescued="
    if current.startswith(prefix):
        existing = [part.strip() for part in current[len(prefix):].split(",") if part.strip()]
        merged: list[str] = []
        for part in [*existing, *fields]:
            if part not in merged:
                merged.append(part)
        return prefix + ",".join(merged)
    return current
