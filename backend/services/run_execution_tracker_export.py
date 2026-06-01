from __future__ import annotations

from typing import Any
from uuid import UUID


def build_related_notice_added_events(
    deps: Any,
    *,
    organization_id: UUID,
    source_run_id: UUID,
    upserted_entries: list[dict[str, Any]],
    before_entries_by_key: dict[str, dict[str, Any] | None],
) -> list[dict[str, Any]]:
    if not upserted_entries:
        return []

    from backend.api.app import _annotate_tracker_entries_with_project_refs
    from backend.api.app import _build_project_aggregates
    from backend.api.app import _clear_project_aggregates_cache

    _clear_project_aggregates_cache()
    project_aggregates = {
        str(item.get("id") or ""): item
        for item in _build_project_aggregates().values()
        if str(item.get("id") or "").strip()
    }
    annotated_entries = _annotate_tracker_entries_with_project_refs(upserted_entries)
    events: list[dict[str, Any]] = []
    for entry in annotated_entries:
        entry_key = str(entry.get("entry_key") or "").strip()
        if not entry_key:
            continue
        if before_entries_by_key.get(entry_key) is not None:
            continue
        project_id = str(entry.get("project_id") or "").strip()
        if not project_id:
            continue
        aggregate = project_aggregates.get(project_id) or {}
        aggregate_source = dict(aggregate.get("source_json") or {})
        if int(aggregate_source.get("tracker_entry_rows") or 0) <= 1:
            continue
        bid_no = str(entry.get("source_bid_no") or "").strip().upper()
        bid_ord = str(entry.get("source_bid_ord") or "").strip()
        new_value = ""
        if bid_no:
            new_value = f"{bid_no}/{bid_ord}" if bid_ord else bid_no
        if not new_value:
            new_value = entry_key
        event = deps.build_tracker_change_event(
            deps.TrackerEventBuildInput(
                organization_id=organization_id,
                tracker_entry_id=UUID(str(entry["id"])),
                event_type="related_notice_added",
                field_name="",
                old_value="",
                new_value=new_value,
                source_kind="tracker_export",
                source_run_id=source_run_id,
                source_ref=entry_key,
                batch_key=f"tracker_export:{source_run_id}",
            )
        )
        if event is not None:
            events.append(event)
    return events


def execute_tracker_export(deps: Any, parent_run_id: UUID, child_run_id: UUID) -> None:
    run_repository = deps.get_run_repository()
    tracker_repository = deps.get_tracker_entry_repository()
    artifact_repository = deps.get_artifact_repository()

    parent_run = run_repository.get_run(parent_run_id)
    if parent_run is None:
        raise deps.RunRepositoryError(f"parent run not found: {parent_run_id}")

    if run_repository.get_run(child_run_id) is None:
        raise deps.RunRepositoryError(f"tracker_export run not found: {child_run_id}")

    params = dict(parent_run.get("params_json") or {})
    export_summary = dict((parent_run.get("summary_json") or {}).get("output") or {})
    params["_export_summary"] = export_summary
    parent_artifacts = artifact_repository.list_artifacts(run_id=parent_run_id)
    winner_csv_artifact = next(
        (artifact for artifact in parent_artifacts if str(artifact.get("artifact_type")) == "winner_csv"),
        None,
    )
    winner_csv_path = None
    if winner_csv_artifact is not None:
        winner_csv_path = deps.resolve_artifact_path(str(winner_csv_artifact.get("storage_path") or ""))

    prepared_tracker = deps.prepare_tracker_export_for_run(
        parent_run_id=parent_run_id,
        params=params,
        winner_csv_path=winner_csv_path,
        progress_cb=lambda message: deps._log_info(
            run_id=child_run_id,
            stage="tracker_export",
            message=message,
            meta={},
        ),
    )
    if prepared_tracker is None:
        if not deps.synthetic_debug_enabled():
            raise RuntimeError("synthetic tracker_export is disabled")
        seed_rows = deps.load_seed_rows_for_run(parent_run_id)
        entries = deps.build_tracker_seed_entries(run_id=parent_run_id, params=params, seed_rows=seed_rows or None)
        tracker_export_backend = "synthetic"
        workbook_source_path = None
    else:
        entries = prepared_tracker.entries
        tracker_export_backend = prepared_tracker.stage_backend
        workbook_source_path = prepared_tracker.workbook_path
    estimated_rows = len(entries)
    stage_total = len(deps.TRACKER_EXPORT_STAGES)
    delay_seconds = deps._stage_delay_seconds(params=params, fallback_ms=20)
    started_at = deps._utcnow()

    run_repository.update_run(
        child_run_id,
        {
            "status": "running",
            "started_at": started_at.isoformat(),
            "progress_stage": deps.TRACKER_EXPORT_STAGES[0],
            "progress_current": 0,
            "progress_total": stage_total,
        },
    )
    deps._merge_run_summary_output(
        run_id=child_run_id,
        summary_patch={
            "source_run_id": str(parent_run_id),
            "estimated_tracker_entry_rows": estimated_rows,
            "tracker_entry_rows": 0,
            "tracking_excel_generated": False,
            "tracking_excel_file_name": "",
            "tracker_export_backend": tracker_export_backend,
        },
        context="tracker_export_child_started",
    )
    deps._update_tracker_export_parent_summary(
        parent_run_id=parent_run_id,
        summary_patch={
            "auto_tracker_export_enabled": True,
            "auto_tracker_export_run_id": str(child_run_id),
            "auto_tracker_export_status": "running",
            "auto_tracker_export_progress_stage": deps.TRACKER_EXPORT_STAGES[0],
            "auto_tracker_export_progress_current": 0,
            "auto_tracker_export_progress_total": stage_total,
            "auto_tracker_export_estimated_rows": estimated_rows,
            "auto_tracker_export_tracker_entry_rows": 0,
            "auto_tracker_export_tracking_excel_generated": False,
            "auto_tracker_export_tracking_excel_file_name": "",
            "auto_tracker_export_backend": tracker_export_backend,
            "auto_tracker_export_error": "",
        },
        context="tracker_export_parent_started",
    )
    deps._log_info(
        run_id=child_run_id,
        stage=deps.TRACKER_EXPORT_STAGES[0],
        message="tracker_export started",
        meta={"parent_run_id": str(parent_run_id)},
    )
    run_repository.update_run(
        child_run_id,
        {
            "progress_stage": deps.TRACKER_EXPORT_STAGES[0],
            "progress_current": 1,
            "progress_total": stage_total,
        },
    )
    deps._merge_run_summary_output(
        run_id=child_run_id,
        summary_patch={
            "estimated_tracker_entry_rows": estimated_rows,
            "tracker_entry_rows": 0,
            "tracking_excel_generated": False,
            "tracker_export_backend": tracker_export_backend,
        },
        context="tracker_export_child_rows_prepared",
    )
    deps._update_tracker_export_parent_summary(
        parent_run_id=parent_run_id,
        summary_patch={
            "auto_tracker_export_status": "running",
            "auto_tracker_export_progress_stage": deps.TRACKER_EXPORT_STAGES[0],
            "auto_tracker_export_progress_current": 1,
            "auto_tracker_export_progress_total": stage_total,
            "auto_tracker_export_estimated_rows": estimated_rows,
            "auto_tracker_export_tracker_entry_rows": 0,
            "auto_tracker_export_tracking_excel_generated": False,
            "auto_tracker_export_backend": tracker_export_backend,
            "auto_tracker_export_error": "",
        },
        context="tracker_export_parent_rows_prepared",
    )
    deps._log_info(
        run_id=child_run_id,
        stage=deps.TRACKER_EXPORT_STAGES[0],
        message="tracker rows prepared",
        meta={"candidate_rows": len(entries), "tracker_export_backend": tracker_export_backend},
    )
    deps.time.sleep(delay_seconds)

    if deps._cancel_run_if_requested(run_id=child_run_id, current_stage=deps.TRACKER_EXPORT_STAGES[0]):
        deps._log_warning(
            run_id=child_run_id,
            stage=deps.TRACKER_EXPORT_STAGES[0],
            message="tracker_export cancelled before upsert",
            meta={},
        )
        return

    before_entries_by_key: dict[str, dict[str, Any] | None] = {}
    for entry in entries:
        entry_key = str(entry.get("entry_key") or "").strip()
        if not entry_key or entry_key in before_entries_by_key:
            continue
        before_entries_by_key[entry_key] = tracker_repository.get_entry_by_entry_key(entry_key)

    upserted_entries = tracker_repository.upsert_source_entries(
        source_run_id=parent_run_id,
        source_tracker_run_id=child_run_id,
        entries=entries,
    )
    organization_id = deps.load_phase1_identity().organization_id
    try:
        from backend.api.app import _invalidate_home_bootstrap_snapshot_best_effort
        from backend.api.app import _upsert_tracker_entry_snapshots_best_effort

        _upsert_tracker_entry_snapshots_best_effort(
            organization_id=organization_id,
            rows=upserted_entries,
        )
        _invalidate_home_bootstrap_snapshot_best_effort(organization_id=organization_id)
    except Exception:
        pass
    tracker_change_events: list[dict[str, Any]] = []
    for upserted_entry in upserted_entries:
        before_entry = before_entries_by_key.get(str(upserted_entry.get("entry_key") or "").strip())
        if before_entry is None:
            continue
        for field_name in deps.TRACKER_EVENT_FIELDS:
            old_value = str(before_entry.get(field_name) or "")
            new_value = str(upserted_entry.get(field_name) or "")
            event_type = "field_filled" if not str(old_value).strip() and str(new_value).strip() else "field_updated_safe"
            event = deps.build_tracker_change_event(
                deps.TrackerEventBuildInput(
                    organization_id=organization_id,
                    tracker_entry_id=UUID(str(upserted_entry["id"])),
                    event_type=event_type,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    source_kind="tracker_export",
                    source_run_id=child_run_id,
                    source_ref=str(upserted_entry.get("entry_key") or ""),
                    batch_key=f"tracker_export:{child_run_id}",
                )
            )
            if event is not None:
                tracker_change_events.append(event)
    tracker_change_events.extend(
        build_related_notice_added_events(
            deps,
            organization_id=organization_id,
            source_run_id=child_run_id,
            upserted_entries=upserted_entries,
            before_entries_by_key=before_entries_by_key,
        )
    )
    if tracker_change_events:
        try:
            deps.get_tracker_change_event_repository().append_events(
                organization_id=organization_id,
                events=tracker_change_events,
            )
        except deps.TrackerChangeEventRepositoryError as exc:
            deps._log_warning(
                run_id=child_run_id,
                stage=deps.TRACKER_EXPORT_STAGES[0],
                message="tracker change event append failed",
                meta={"error": str(exc), "event_count": len(tracker_change_events)},
            )
    deps._merge_run_summary_output(
        run_id=child_run_id,
        summary_patch={
            "estimated_tracker_entry_rows": estimated_rows,
            "tracker_entry_rows": len(upserted_entries),
            "tracking_excel_generated": False,
            "tracker_export_backend": tracker_export_backend,
        },
        context="tracker_export_child_upserted",
    )
    deps._update_tracker_export_parent_summary(
        parent_run_id=parent_run_id,
        summary_patch={
            "auto_tracker_export_status": "running",
            "auto_tracker_export_progress_stage": deps.TRACKER_EXPORT_STAGES[0],
            "auto_tracker_export_progress_current": 1,
            "auto_tracker_export_progress_total": stage_total,
            "auto_tracker_export_estimated_rows": estimated_rows,
            "auto_tracker_export_tracker_entry_rows": len(upserted_entries),
            "auto_tracker_export_tracking_excel_generated": False,
            "auto_tracker_export_backend": tracker_export_backend,
            "auto_tracker_export_error": "",
        },
        context="tracker_export_parent_upserted",
    )
    deps._log_info(
        run_id=child_run_id,
        stage=deps.TRACKER_EXPORT_STAGES[0],
        message="tracker_entries upsert completed",
        meta={"upserted_rows": len(upserted_entries)},
    )

    if deps._cancel_run_if_requested(run_id=child_run_id, current_stage="finalize"):
        deps._log_warning(
            run_id=child_run_id,
            stage="finalize",
            message="tracker_export cancelled before workbook generation",
            meta={},
        )
        return
    if workbook_source_path is None:
        written_workbook = deps.write_tracking_workbook(run_id=child_run_id, rows=upserted_entries)
    else:
        written_workbook = deps.copy_file_artifact(
            run_id=child_run_id,
            source_path=workbook_source_path,
            artifact_file_name="project_tracking.xlsx",
            mime_type=deps.XLSX_MIME_TYPE,
            row_count=len(upserted_entries),
        )
    deps._create_artifact_record(
        artifact_repository=artifact_repository,
        run_id=child_run_id,
        artifact_type="tracking_excel",
        written_artifact=written_workbook,
        meta={
            "rows": written_workbook.row_count,
            "stage": "finalize",
            "backend": tracker_export_backend,
        },
    )
    deps._merge_run_summary_output(
        run_id=child_run_id,
        summary_patch={
            "estimated_tracker_entry_rows": estimated_rows,
            "tracker_entry_rows": len(upserted_entries),
            "tracking_excel_generated": True,
            "tracking_excel_file_name": written_workbook.file_name,
            "tracker_export_backend": tracker_export_backend,
        },
        context="tracker_export_child_workbook_created",
    )
    deps._update_tracker_export_parent_summary(
        parent_run_id=parent_run_id,
        summary_patch={
            "auto_tracker_export_status": "running",
            "auto_tracker_export_progress_stage": "finalize",
            "auto_tracker_export_progress_current": 1,
            "auto_tracker_export_progress_total": stage_total,
            "auto_tracker_export_estimated_rows": estimated_rows,
            "auto_tracker_export_tracker_entry_rows": len(upserted_entries),
            "auto_tracker_export_tracking_excel_generated": True,
            "auto_tracker_export_tracking_excel_file_name": written_workbook.file_name,
            "auto_tracker_export_backend": tracker_export_backend,
            "auto_tracker_export_error": "",
        },
        context="tracker_export_parent_workbook_created",
    )
    deps._log_info(
        run_id=child_run_id,
        stage="finalize",
        message="tracking_excel artifact created",
        meta={
            "file_name": written_workbook.file_name,
            "rows": written_workbook.row_count,
            "tracker_export_backend": tracker_export_backend,
        },
    )

    finished_at = deps._utcnow()
    run_repository.update_run(
        child_run_id,
        {
            "status": "success",
            "progress_stage": deps.TRACKER_EXPORT_STAGES[-1],
            "progress_current": stage_total,
            "progress_total": stage_total,
            "summary_json": {
                "output": {
                    "source_run_id": str(parent_run_id),
                    "estimated_tracker_entry_rows": estimated_rows,
                    "tracker_entry_rows": len(upserted_entries),
                    "entry_keys": [entry["entry_key"] for entry in upserted_entries],
                    "tracking_excel_generated": True,
                    "tracking_excel_file_name": written_workbook.file_name,
                    "tracker_export_backend": tracker_export_backend,
                }
            },
            "error_json": {},
            "finished_at": finished_at.isoformat(),
        },
    )
    deps._update_tracker_export_parent_summary(
        parent_run_id=parent_run_id,
        summary_patch={
            "auto_tracker_export_enabled": True,
            "auto_tracker_export_run_id": str(child_run_id),
            "auto_tracker_export_status": "success",
            "auto_tracker_export_progress_stage": deps.TRACKER_EXPORT_STAGES[-1],
            "auto_tracker_export_progress_current": stage_total,
            "auto_tracker_export_progress_total": stage_total,
            "auto_tracker_export_estimated_rows": estimated_rows,
            "auto_tracker_export_tracker_entry_rows": len(upserted_entries),
            "auto_tracker_export_tracking_excel_generated": True,
            "auto_tracker_export_tracking_excel_file_name": written_workbook.file_name,
            "auto_tracker_export_backend": tracker_export_backend,
            "auto_tracker_export_error": "",
        },
        context="tracker_export_parent_success",
    )
    deps._log_info(
        run_id=child_run_id,
        stage="finalize",
        message="tracker_export finished successfully",
        meta={
            "tracker_entry_rows": len(upserted_entries),
            "tracker_export_backend": tracker_export_backend,
        },
    )


def build_tracker_seed_entries(
    deps: Any,
    *,
    run_id: UUID,
    params: dict[str, Any],
    seed_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    bid_no = str(params.get("bid_no") or f"WNP{str(run_id).replace('-', '')[:12].upper()}")
    notice_title = str(params.get("notice_title") or "Project Tracker")
    demand_org = str(params.get("demand_org") or "Internal Demand Organization")
    start_date = str(params.get("start_date") or "20250101")
    end_date = str(params.get("end_date") or start_date)
    contract_date_hint = str(params.get("contract_date_hint") or end_date or start_date)
    max_pages = int(params.get("max_pages") or 1)
    rows_per_page = int(params.get("rows_per_page") or 100)
    api_scope = str(params.get("api_scope") or "construction")
    title_slug = deps._slugify(notice_title)
    demand_slug = deps._slugify(demand_org)

    if seed_rows:
        entries: list[dict[str, Any]] = []
        for index, seed_row in enumerate(seed_rows, start=1):
            source_bid_no = str(seed_row.get("bid_no") or bid_no).strip() or bid_no
            source_bid_ord = deps._normalize_bid_ord(seed_row.get("bid_ord"))
            project_name = str(seed_row.get("project_name") or notice_title).strip() or notice_title
            org_name = str(seed_row.get("org_name") or demand_org).strip() or demand_org
            announce_date = str(seed_row.get("announce_date") or end_date).strip() or end_date
            g2b_verified = str(seed_row.get("g2b_verified") or "N").strip().upper() or "N"
            project_name_norm = deps._slugify(project_name)
            entry_key = "|".join(
                (
                    source_bid_no.strip().lower(),
                    source_bid_ord.strip().lower(),
                    project_name_norm.strip().lower(),
                )
            )
            entries.append(
                {
                    "entry_key": entry_key,
                    "row_no": index,
                    "sheet_name": "Sheet1",
                    "section_name": "facility_cost",
                    "source_bid_no": source_bid_no,
                    "source_bid_ord": source_bid_ord,
                    "source_project_name_norm": project_name_norm,
                    "project_name": project_name,
                    "gross_area_scale": f"{api_scope} / pages={max_pages} / rows={rows_per_page}",
                    "construction_cost": str(max(1, rows_per_page) * 1000000 * index),
                    "demand_org_name": org_name,
                    "demand_contact": "Internal Ops",
                    "client_location": "Seoul",
                    "site_location_1": org_name,
                    "site_location_2": api_scope,
                    "architect_office": "GUI Parity Architects",
                    "construction_start_date": deps._to_iso_date(start_date),
                    "last_checked_date": deps._to_iso_date(contract_date_hint or end_date),
                    "progress_note": f"Collected seed ({g2b_verified}) from project_tracker {run_id}",
                    "notice_date": deps._to_iso_date(announce_date),
                    "manager_name": "Phase1 Internal User",
                    "building_automation_estimated_amount": str(max_pages * 5000000 * index),
                }
            )
        return entries

    base_entry = {
        "sheet_name": "Sheet1",
        "section_name": "facility_cost",
        "source_bid_no": bid_no,
        "source_bid_ord": "000",
        "source_project_name_norm": title_slug,
        "project_name": notice_title,
        "gross_area_scale": f"{max_pages} pages / {rows_per_page} rows",
        "construction_cost": str(max(1, rows_per_page) * 1000000),
        "demand_org_name": demand_org,
        "demand_contact": "Internal Ops",
        "client_location": "Seoul",
        "site_location_1": "Seoul Headquarters",
        "site_location_2": api_scope,
        "architect_office": "GUI Parity Architects",
        "construction_start_date": deps._to_iso_date(start_date),
        "last_checked_date": deps._to_iso_date(contract_date_hint or end_date),
        "progress_note": f"Generated from project_tracker {run_id}",
        "notice_date": deps._to_iso_date(end_date),
        "manager_name": "Phase1 Internal User",
        "building_automation_estimated_amount": str(max_pages * 5000000),
    }
    second_bid_ord = "001"
    secondary_title = f"{notice_title} Follow-up"

    entries: list[dict[str, Any]] = []
    for index, source in enumerate(
        (
            base_entry,
            {
                **base_entry,
                "source_bid_ord": second_bid_ord,
                "source_project_name_norm": f"{title_slug}-follow-up",
                "project_name": secondary_title,
                "construction_cost": str(max(1, rows_per_page) * 800000),
                "demand_org_name": f"{demand_org} - {api_scope}",
                "progress_note": f"Generated from {demand_slug}",
                "building_automation_estimated_amount": str(max_pages * 3500000),
            },
        ),
        start=1,
    ):
        entry_key = "|".join(
            (
                str(source["source_bid_no"]).strip().lower(),
                str(source["source_bid_ord"]).strip().lower(),
                str(source["source_project_name_norm"]).strip().lower(),
            )
        )
        row = {
            "entry_key": entry_key,
            "row_no": index,
        }
        row.update(source)
        entries.append(row)

    return entries
