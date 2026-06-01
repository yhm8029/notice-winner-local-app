from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ResolvedExportFields:
    winner_name: str
    notice_construction_cost: object
    contract_amount: object
    gross_area_scale: object
    demand_contact: object
    client_location: object
    site_location: object
    architect_office: object
    construction_start_date: object
    construction_duration_days: str
    completion_expected_date_explicit: str
    completion_expected_date_computed: str
    building_auto_est: object
    contract_source_type: str
    status: str
    confidence: str
    score: str
    review_flag: str
    reason_code: str
    winner_pattern: str
    evidence_source: str
    contract_hit_note: str
    fallback_notes: list[str]
    expected_blank_external_portal: bool
    expected_blank_contact_review: bool


def build_resolved_export_fields(
    *,
    extracted,
    contract_hit: object,
    best_row: dict[str, str],
    manual_overrides: dict[str, str],
    external_portal_contact_expected_blank: bool,
    presmpt_prce: str,
    org_name: str,
    resolved_field_cls,
    format_won_fn: Callable[[object], str],
    normalize_export_contact_value_fn: Callable[[str, str], str],
    resolve_field_fn: Callable[..., object],
    looks_like_specific_architecture_firm_name_fn: Callable[[str], bool],
    resolve_contract_source_type_fn: Callable[[object, str], str],
    select_building_automation_cost_candidate_fn: Callable[..., tuple[str, str]],
    resolve_building_automation_amount_fn: Callable[..., object],
    compute_completion_expected_date_fn: Callable[..., str],
    resolve_contract_status_fn: Callable[..., str],
    resolve_contract_score_fn: Callable[[object, str], float],
    resolve_contract_reason_code_fn: Callable[..., str],
    resolve_contract_winner_pattern_fn: Callable[[object, str, str], str],
    resolve_contract_evidence_fn: Callable[[object, str], str],
    resolve_contract_hit_note_fn: Callable[[object, str], str],
    build_fallback_notes_fn: Callable[[dict[str, object]], list[str]],
) -> ResolvedExportFields:
    winner_name = str((getattr(contract_hit, "contract_name", "") if contract_hit else "") or extracted.winner_name or "").strip()
    notice_construction_cost = resolve_field_fn(confirmed_value=extracted.construction_cost)
    contract_amount = resolve_field_fn(
        confirmed_value=(
            format_won_fn(getattr(contract_hit, "contract_amount", ""))
            if contract_hit and str(getattr(contract_hit, "contract_amount", "") or "").strip()
            else extracted.construction_cost
        ),
        fallback_value=format_won_fn(presmpt_prce),
        fallback_source="fallback_seed_presmpt_prce",
    )
    gross_area_scale = resolve_field_fn(confirmed_value=extracted.gross_area_scale)
    expected_blank_external_portal = bool(
        external_portal_contact_expected_blank
        and not str(manual_overrides.get("contact") or "").strip()
        and not str(extracted.demand_contact or "").strip()
    )
    expected_blank_contact_review = bool(
        not str(manual_overrides.get("contact") or "").strip()
        and not str(extracted.demand_contact or "").strip()
        and str(extracted.demand_contact_resolution_status or "").strip() == "review"
    )
    normalized_contact_override = normalize_export_contact_value_fn(str(manual_overrides.get("contact") or "").strip(), org_name)
    normalized_extracted_contact = normalize_export_contact_value_fn(extracted.demand_contact, org_name)
    demand_contact = resolve_field_fn(
        confirmed_value=normalized_contact_override or normalized_extracted_contact,
        fallback_value="",
        fallback_source="",
    )
    client_location = resolve_field_fn(confirmed_value=extracted.client_location)
    site_location = resolve_field_fn(
        confirmed_value=extracted.site_location or (str(getattr(contract_hit, "site_name", "") or "").strip() if contract_hit else ""),
    )
    if contract_hit and looks_like_specific_architecture_firm_name_fn(winner_name):
        architect_office = resolved_field_cls(value=winner_name, source="confirmed_contract_lookup")
    else:
        architect_office = resolved_field_cls()
    contract_source_type = resolve_contract_source_type_fn(contract_hit, winner_name)
    construction_start_date = resolve_field_fn(confirmed_value=extracted.construction_start_date)
    construction_duration_days = str(
        extracted.construction_duration_days or (getattr(contract_hit, "contract_duration_days", "") if contract_hit else "") or ""
    ).strip()
    cost_candidate_value, cost_candidate_label = select_building_automation_cost_candidate_fn(
        notice_construction_cost=notice_construction_cost,
        contract_amount=contract_amount,
        contract_source_type=contract_source_type,
    )
    building_auto_est = resolve_building_automation_amount_fn(
        explicit_value=extracted.building_automation_estimated_amount,
        construction_cost_candidate=cost_candidate_value,
        candidate_label=cost_candidate_label,
    )
    completion_expected_date_explicit = str(extracted.completion_expected_date_explicit or "").strip()
    completion_expected_date_computed = compute_completion_expected_date_fn(
        contract_date=str(getattr(contract_hit, "contract_date", "") or "") if contract_hit else "",
        duration_days=construction_duration_days,
        contract_source_type=contract_source_type,
    )
    if completion_expected_date_explicit:
        completion_expected_date_computed = ""
    g2b_verified = str(best_row.get("g2b_verified") or "N").strip().upper() or "N"
    status = resolve_contract_status_fn(
        contract_hit=contract_hit,
        winner_name=winner_name,
        g2b_verified=g2b_verified,
    )
    confidence = "high" if status == "FOUND" else ("medium" if winner_name else "low")
    score = f"{resolve_contract_score_fn(contract_hit, winner_name):.2f}"
    review_flag = "N" if status == "FOUND" else "Y"
    reason_code = resolve_contract_reason_code_fn(
        contract_hit=contract_hit,
        winner_name=winner_name,
        g2b_verified=g2b_verified,
        status=status,
    )
    winner_pattern = resolve_contract_winner_pattern_fn(contract_hit, winner_name, extracted.winner_pattern)
    evidence_source = resolve_contract_evidence_fn(contract_hit, winner_name)
    contract_hit_note = resolve_contract_hit_note_fn(contract_hit, winner_name)
    fallback_notes = build_fallback_notes_fn(
        {
            "contract_amount": contract_amount,
            "demand_contact": demand_contact,
            "architect_office": architect_office,
            "building_automation_estimated_amount": building_auto_est,
        }
    )
    return ResolvedExportFields(
        winner_name=winner_name,
        notice_construction_cost=notice_construction_cost,
        contract_amount=contract_amount,
        gross_area_scale=gross_area_scale,
        demand_contact=demand_contact,
        client_location=client_location,
        site_location=site_location,
        architect_office=architect_office,
        construction_start_date=construction_start_date,
        construction_duration_days=construction_duration_days,
        completion_expected_date_explicit=completion_expected_date_explicit,
        completion_expected_date_computed=completion_expected_date_computed,
        building_auto_est=building_auto_est,
        contract_source_type=contract_source_type,
        status=status,
        confidence=confidence,
        score=score,
        review_flag=review_flag,
        reason_code=reason_code,
        winner_pattern=winner_pattern,
        evidence_source=evidence_source,
        contract_hit_note=contract_hit_note,
        fallback_notes=fallback_notes,
        expected_blank_external_portal=expected_blank_external_portal,
        expected_blank_contact_review=expected_blank_contact_review,
    )
