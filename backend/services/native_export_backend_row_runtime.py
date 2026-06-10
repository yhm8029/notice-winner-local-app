from __future__ import annotations


def build_output_row(
    *,
    bid_no: str,
    bid_ord: str,
    best_row: dict[str, str],
    preferred_document_url: str,
    notice_url: str,
    search_url: str,
    base_url: str,
    title: str,
    winner_name: str,
    confidence: str,
    winner_pattern: str,
    score: str,
    reason_code: str,
    review_flag: str,
    contract_name: str,
    contract_date: str,
    notice_construction_cost,
    contract_amount,
    gross_area_scale,
    demand_contact,
    client_location,
    site_location,
    architect_office,
    construction_start_date,
    construction_duration_days: str,
    completion_expected_date_explicit: str,
    completion_expected_date_computed: str,
    building_auto_est,
    evidence_source: str,
    status: str,
    spec_doc_file_name: str,
    contract_hit_note: str,
    attachment_note: str,
    synap_note: str,
    llm_corrected_fields: tuple[str, ...],
    extracted_contact_resolution_status: str,
    extracted_contact_resolution_reason: str,
    extracted_contact_resolution_phase: str,
    extracted_contact_resolution_role: str,
    extracted_contact_resolution_owner_side: str,
    extracted_contact_resolution_owner_side_basis: str,
    expected_blank_external_portal: bool,
    expected_blank_contact_review: bool,
    fallback_notes: list[str],
    join_non_empty_fn,
) -> dict[str, str]:
    return {
        "bid_no": bid_no,
        "bid_ord": bid_ord,
        "rank": "1",
        "project_name_norm": str(best_row.get("project_name_norm") or "").strip(),
        "g2b_verified": str(best_row.get("g2b_verified") or "N").strip().upper() or "N",
        "source_type": str(best_row.get("source_type") or ""),
        "internal_search_url": search_url,
        "post_url": preferred_document_url or notice_url or search_url or base_url,
        "post_title": title,
        "winner_name": winner_name,
        "winner_confidence": confidence,
        "winner_pattern": winner_pattern,
        "post_score": score,
        "file_url": "",
        "file_name": "",
        "confidence_score": score,
        "reason_code": reason_code,
        "review_flag": review_flag,
        "escalate": "Y" if review_flag == "Y" else "N",
        "contract_name": contract_name,
        "contract_date": contract_date,
        "notice_construction_cost": notice_construction_cost.value,
        "notice_construction_cost_source": notice_construction_cost.source,
        "contract_amount": contract_amount.value,
        "contract_amount_source": contract_amount.source,
        "gross_area_scale": gross_area_scale.value,
        "gross_area_scale_source": gross_area_scale.source,
        "demand_contact": demand_contact.value,
        "demand_contact_source": demand_contact.source,
        "client_location": client_location.value,
        "client_location_source": client_location.source,
        "site_location": site_location.value,
        "site_location_source": site_location.source,
        "architect_office": architect_office.value,
        "architect_office_source": architect_office.source,
        "construction_start_date": construction_start_date.value,
        "construction_start_date_source": construction_start_date.source,
        "construction_duration_days": construction_duration_days,
        "completion_expected_date_explicit": completion_expected_date_explicit,
        "completion_expected_date_computed": completion_expected_date_computed,
        "building_automation_estimated_amount": building_auto_est.value,
        "building_automation_estimated_amount_source": building_auto_est.source,
        "evidence_source": evidence_source,
        "parser_version": "web-native-v1",
        "run_mode": "native",
        "status": status,
        "hub_check_note": join_non_empty_fn(
            [
                spec_doc_file_name,
                contract_hit_note,
                attachment_note,
                synap_note,
                (
                    join_non_empty_fn(
                        [
                            f"contact_resolution={extracted_contact_resolution_status}",
                            extracted_contact_resolution_reason,
                            extracted_contact_resolution_phase,
                            extracted_contact_resolution_role,
                            extracted_contact_resolution_owner_side,
                            extracted_contact_resolution_owner_side_basis,
                        ],
                        ":",
                    )
                    if extracted_contact_resolution_status
                    else ""
                ),
                "demand_contact=expected_blank_external_portal" if expected_blank_external_portal else "",
                "demand_contact=expected_blank_contact_review" if expected_blank_contact_review else "",
                join_non_empty_fn(fallback_notes, ", ") if fallback_notes else "",
            ],
            " | ",
        ),
    }


def build_progress_message(
    *,
    bid_no: str,
    status: str,
    winner_name: str,
    gross_area_scale: str,
    construction_cost: str,
    contract_lookup_meta: object,
    document_count: int,
    attachment_tried_count: int,
    attachment_parsed_count: int,
    timing_ms: dict[str, int],
) -> str:
    return (
        f"{bid_no}: export_status={status} "
        f"winner={'Y' if winner_name else 'N'} "
        f"area={'Y' if gross_area_scale else 'N'} "
        f"cost={'Y' if construction_cost else 'N'} "
        f"contract_lookup_path={getattr(contract_lookup_meta, 'contract_lookup_path', 'no_hit')} "
        f"query_sweep_used={'Y' if getattr(contract_lookup_meta, 'query_sweep_used', False) else 'N'} "
        f"query_sweep_hit={'Y' if getattr(contract_lookup_meta, 'query_sweep_hit', False) else 'N'} "
        f"lofin_workers={getattr(contract_lookup_meta, 'lofin_date_workers', 0)} "
        f"lofin_sem={getattr(contract_lookup_meta, 'lofin_global_semaphore_limit', 0)} "
        f"lofin_active={getattr(contract_lookup_meta, 'lofin_max_active_requests', 0)} "
        f"lofin_dates={getattr(contract_lookup_meta, 'lofin_dates_examined', 0)} "
        f"lofin_req={getattr(contract_lookup_meta, 'lofin_requests_total', 0)} "
        f"lofin_pages={getattr(contract_lookup_meta, 'lofin_pages_fetched_total', 0)} "
        f"lofin_ps={'Y' if getattr(contract_lookup_meta, 'lofin_powershell_used', False) else 'N'} "
        f"lofin_ssl={'Y' if getattr(contract_lookup_meta, 'lofin_ssl_fallback_used', False) else 'N'} "
        f"lofin_timeouts={getattr(contract_lookup_meta, 'lofin_timeout_count', 0)} "
        f"lofin_first_nonempty={getattr(contract_lookup_meta, 'lofin_first_nonempty_date', '') or '-'} "
        f"lofin_hit_date={getattr(contract_lookup_meta, 'lofin_hit_date', '') or '-'} "
        f"lofin_best={float(getattr(contract_lookup_meta, 'lofin_best_score', 0.0) or 0.0):.3f} "
        f"lofin_budget={float(getattr(contract_lookup_meta, 'lofin_budget_seconds', 0.0) or 0.0):.1f}s "
        f"lofin_budget_exhausted={'Y' if getattr(contract_lookup_meta, 'lofin_budget_exhausted', False) else 'N'} "
        f"pages={document_count} attachments={attachment_tried_count}/{attachment_parsed_count} "
        f"timing_ms(contract_lookup={timing_ms['contract_lookup']},"
        f"page_fetch={timing_ms['page_fetch']},"
        f"attachment_download={timing_ms['attachment_download']},"
        f"attachment_parse={timing_ms['attachment_parse']})"
    )
