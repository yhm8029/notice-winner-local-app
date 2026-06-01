from __future__ import annotations

from typing import Any
from uuid import UUID


def build_related_notice_artifact_payload(
    deps: Any,
    *,
    run_id: UUID,
    params: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    target_project_keys: set[str] | None = None,
    limit_projects: bool = True,
    prefer_seed_fallback_on_cache_miss: bool = False,
) -> dict[str, Any]:
    from backend.api.app import _better_project_label
    from backend.api.app import _dedupe_related_notice_payload_items
    from backend.api.app import _is_generic_project_term
    from backend.api.app import _live_related_notice_search
    from backend.api.app import _project_match_key
    from backend.api.app import _project_search_name
    from backend.api.app import _score_related_notice_match

    projects_by_key: dict[str, dict[str, Any]] = {}

    def _register_project(project_name: str, issuer_name: str, latest_notice_date: str, *, source: str) -> None:
        cleaned_name = str(project_name or "").strip()
        if not cleaned_name:
            return
        project_search_name = _project_search_name(cleaned_name)
        if source == "query" and _is_generic_project_term(project_search_name or cleaned_name):
            return
        project_key = _project_match_key(project_search_name or cleaned_name)
        if not project_key:
            return
        if target_project_keys and project_key not in target_project_keys:
            return
        item = projects_by_key.setdefault(
            project_key,
            {
                "project_key": project_key,
                "_project_match_key": project_key,
                "project_name": cleaned_name,
                "project_search_name": project_search_name,
                "issuer_name": str(issuer_name or "").strip(),
                "latest_notice_date": str(latest_notice_date or "").strip(),
                "source_json": {"run_ids": [str(run_id)]},
                "_source_priority": 1 if source == "query" else 0,
                "_seed_row_count": 0,
            },
        )
        item["project_name"] = _better_project_label(str(item.get("project_name") or ""), cleaned_name)
        if project_search_name:
            item["project_search_name"] = project_search_name
        if source == "query":
            item["_source_priority"] = 1
        if issuer_name and not item.get("issuer_name"):
            item["issuer_name"] = str(issuer_name or "").strip()
        if str(latest_notice_date or "").strip() >= str(item.get("latest_notice_date") or ""):
            item["latest_notice_date"] = str(latest_notice_date or "").strip()
        if source == "seed":
            item["_seed_row_count"] = int(item.get("_seed_row_count") or 0) + 1

    _register_project(
        str(params.get("notice_title") or params.get("bid_no") or "").strip(),
        str(params.get("demand_org") or "").strip(),
        str(params.get("end_date") or "").strip(),
        source="query",
    )
    for row in seed_rows:
        _register_project(
            str(row.get("project_name") or "").strip(),
            str(row.get("org_name") or "").strip(),
            str(row.get("announce_date") or "").strip(),
            source="seed",
        )

    projects = sorted(
        projects_by_key.values(),
        key=lambda item: (
            int(item.get("_source_priority") or 0),
            int(item.get("_seed_row_count") or 0),
            str(item.get("latest_notice_date") or ""),
            len(str(item.get("project_search_name") or item.get("project_name") or "")),
        ),
        reverse=True,
    )
    if not target_project_keys and limit_projects:
        projects = projects[: deps.RELATED_NOTICE_PRECOMPUTE_MAX_PROJECTS]

    payload_projects: list[dict[str, Any]] = []
    total_items = 0
    reuse_snapshot_keys = deps._related_notice_reuse_snapshot_keys()
    for project in projects:
        project_key = str(project.get("project_key") or project.get("_project_match_key") or "").strip()
        reusable_project_entry = deps._reusable_related_notice_project_entry(
            project=project,
            run_id=run_id,
            reuse_snapshot_keys=reuse_snapshot_keys,
        )
        if reusable_project_entry is not None:
            if project_key:
                deps.update_related_notice_progress(
                    project_key=project_key,
                    project_name=str(reusable_project_entry.get("project_name") or project.get("project_name") or ""),
                    project_search_name=str(reusable_project_entry.get("project_search_name") or project.get("project_search_name") or ""),
                    run_id=str(run_id),
                    items=[dict(item) for item in (reusable_project_entry.get("items") or []) if isinstance(item, dict)],
                    status="running",
                    message=f"{len(list(reusable_project_entry.get('items') or []))}건의 연관 공고를 확인했습니다.",
                )
            total_items += len(list(reusable_project_entry.get("items") or []))
            payload_projects.append(reusable_project_entry)
            continue
        if prefer_seed_fallback_on_cache_miss:
            seed_items = deps._seed_fallback_related_notice_items(
                project=project,
                seed_rows=seed_rows,
                score_related_notice_match_fn=_score_related_notice_match,
                project_search_name_fn=_project_search_name,
                dedupe_related_notice_payload_items_fn=_dedupe_related_notice_payload_items,
            )
            search_debug = {
                "seed_fallback": {
                    "used": True,
                    "item_count": len(seed_items),
                    "bid_nos": [
                        str(item.get("bid_no") or "").strip()
                        for item in seed_items
                        if str(item.get("bid_no") or "").strip()
                    ],
                },
                "cache_reused": False,
                "live_search_skipped": True,
            }
            if project_key:
                deps.update_related_notice_progress(
                    project_key=project_key,
                    project_name=str(project.get("project_name") or ""),
                    project_search_name=str(project.get("project_search_name") or ""),
                    run_id=str(run_id),
                    items=seed_items,
                    status="running",
                    message=f"{len(seed_items)}건의 연관 공고를 확인했습니다.",
                )
            total_items += len(seed_items)
            payload_projects.append(
                deps._build_related_notice_project_entry(
                    project=project,
                    run_id=run_id,
                    items=seed_items,
                    source="seed_fallback",
                    error_message="",
                    search_debug=search_debug,
                )
            )
            continue
        live_items: list[dict[str, Any]] = []
        search_debug: dict[str, Any] = {}
        source = "seed_fallback"
        error_message = ""
        try:
            def _emit_live_progress(items: list[Any], _debug: dict[str, Any]) -> None:
                if not project_key:
                    return
                item_dicts = [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else dict(item)
                    for item in items
                    if isinstance(item, dict) or hasattr(item, "model_dump")
                ]
                deps.update_related_notice_progress(
                    project_key=project_key,
                    project_name=str(project.get("project_name") or ""),
                    project_search_name=str(project.get("project_search_name") or ""),
                    run_id=str(run_id),
                    items=item_dicts,
                    status="running",
                    message=f"{len(item_dicts)}건의 연관 공고를 확인했습니다.",
                )

            live_result_items, search_debug = _live_related_notice_search(
                project,
                progress_cb=_emit_live_progress if project_key else None,
            )
            live_items = [item.model_dump(mode="json") for item in live_result_items]
            if live_items:
                source = "live"
        except Exception as exc:
            error_message = str(exc)
            search_debug = {
                "project_name": str(project.get("project_name") or ""),
                "project_search_name": str(project.get("project_search_name") or ""),
                "error": error_message,
                "attempts": [],
                "deduped_row_count": 0,
                "scored_candidate_count": 0,
                "final_item_count": 0,
            }
            live_items = []

        if not live_items:
            seed_related = deps._seed_fallback_related_notice_items(
                project=project,
                seed_rows=seed_rows,
                score_related_notice_match_fn=_score_related_notice_match,
                project_search_name_fn=_project_search_name,
                dedupe_related_notice_payload_items_fn=_dedupe_related_notice_payload_items,
            )
            live_items = seed_related
            search_debug["seed_fallback"] = {
                "used": True,
                "item_count": len(seed_related),
                "bid_nos": [
                    str(item.get("bid_no") or "").strip()
                    for item in seed_related
                    if str(item.get("bid_no") or "").strip()
                ],
            }
        else:
            search_debug["seed_fallback"] = {"used": False, "item_count": 0, "bid_nos": []}
        live_items = _dedupe_related_notice_payload_items(live_items)
        if project_key:
            deps.update_related_notice_progress(
                project_key=project_key,
                project_name=str(project.get("project_name") or ""),
                project_search_name=str(project.get("project_search_name") or ""),
                run_id=str(run_id),
                items=live_items,
                status="running",
                message=f"{len(live_items)}건의 연관 공고를 확인했습니다.",
            )

        total_items += len(live_items)
        payload_projects.append(
            deps._build_related_notice_project_entry(
                project=project,
                run_id=run_id,
                items=live_items,
                source=source,
                error_message=error_message,
                search_debug=search_debug,
            )
        )

    return {
        "run_id": str(run_id),
        "generated_at": deps._utcnow().isoformat(),
        "project_count": len(payload_projects),
        "item_count": total_items,
        "projects": payload_projects,
    }


def precompute_related_notices_for_run(
    deps: Any,
    run_id: UUID,
    *,
    project_key: str = "",
    backfill_remaining: bool = True,
    force_recompute: bool = False,
    snapshot_set_id: str = "",
) -> None:
    run_repository = deps.get_run_repository()
    artifact_repository = deps.get_artifact_repository()
    run = run_repository.get_run(run_id)
    if run is None:
        raise deps.RunRepositoryError(f"run not found: {run_id}")
    if str(run.get("run_type") or "").strip() not in {"project_tracker", "winner_pipeline"}:
        raise deps.RunRepositoryError(f"related notice precompute requires a project_tracker run: {run_id}")
    if str(run.get("status") or "").strip() != "success":
        raise deps.RunRepositoryError(f"related notice precompute requires a successful run: {run_id}")

    try:
        artifacts = artifact_repository.list_artifacts(run_id=run_id)
    except deps.ArtifactRepositoryError as exc:
        raise deps.RunRepositoryError(str(exc)) from exc
    existing_related_artifact = next(
        (item for item in artifacts if str(item.get("artifact_type") or "").strip() == deps.RELATED_NOTICE_ARTIFACT_TYPE),
        None,
    )
    existing_payload = None
    if existing_related_artifact is not None:
        existing_payload = deps._load_existing_related_notice_payload(str(existing_related_artifact.get("storage_path") or "").strip())
    if existing_related_artifact is not None and project_key and deps._should_skip_related_notice_project_recompute(
        existing_payload=existing_payload,
        project_key=project_key,
        force_recompute=force_recompute,
    ):
        deps._update_related_notice_summary(
            run_id=run_id,
            summary_patch={
                "related_notice_precompute_status": "success",
                "related_notice_project_statuses": deps._build_related_notice_project_status_patch(
                    [project_key] if project_key else [],
                    status="success",
                ),
            },
        )
        return

    params = dict(run.get("params_json") or {})
    seed_rows = deps.load_seed_rows_for_run(run_id)
    deps._update_related_notice_summary(
        run_id=run_id,
        summary_patch={
            "related_notice_precompute_status": "running",
            "related_notice_project_statuses": deps._build_related_notice_project_status_patch(
                [project_key] if project_key else [],
                status="running",
            ),
        },
    )
    if project_key:
        deps._upsert_related_notice_cache_entry(
            project_entry={
                "project_key": project_key,
                "project_name": "",
                "project_search_name": "",
                "issuer_name": "",
                "source": "",
                "algorithm_version": deps.RELATED_NOTICE_ALGORITHM_VERSION,
                "items": [],
            },
            status="running",
            source_run_id=run_id,
        )
    deps._log_info(
        run_id=run_id,
        stage="finalize",
        message="related notice precompute started",
        meta={"seed_rows": len(seed_rows)},
    )

    try:
        related_notice_payload = deps._build_related_notice_artifact_payload(
            run_id=run_id,
            params=params,
            seed_rows=seed_rows,
            target_project_keys={project_key} if project_key else None,
            limit_projects=bool(project_key),
            prefer_seed_fallback_on_cache_miss=not bool(project_key),
        )
        if project_key:
            related_notice_payload = deps._merge_related_notice_payload(existing_payload, related_notice_payload)
        payload_project_keys = [
            str(item.get("project_key") or "").strip()
            for item in (related_notice_payload.get("projects") or [])
            if str(item.get("project_key") or "").strip()
        ]
        for project_entry in (related_notice_payload.get("projects") or []):
            deps._upsert_related_notice_cache_entry(
                project_entry=dict(project_entry),
                status="success",
                source_run_id=run_id,
            )
        if project_key:
            updated_project_entry = next(
                (
                    dict(item)
                    for item in (related_notice_payload.get("projects") or [])
                    if str(item.get("project_key") or "").strip() == project_key
                ),
                None,
            )
            if updated_project_entry is not None:
                deps._upsert_related_notice_snapshot_project_entry(
                    run_id=run_id,
                    project_entry=updated_project_entry,
                    snapshot_set_id=snapshot_set_id,
                )
                deps.finish_related_notice_progress(
                    project_key=project_key,
                    status="ready",
                    items=[dict(item) for item in (updated_project_entry.get("items") or []) if isinstance(item, dict)],
                    message=f"{len(list(updated_project_entry.get('items') or []))}건의 연관 공고 검색이 완료되었습니다.",
                )
            else:
                deps.finish_related_notice_progress(
                    project_key=project_key,
                    status="missing",
                    items=[],
                    message="연관 공고 검색 결과가 없습니다.",
                )
        related_notice_artifact = deps.write_json_artifact(
            run_id=run_id,
            file_name=deps.RELATED_NOTICE_ARTIFACT_FILE_NAME,
            payload=related_notice_payload,
        )
        if existing_related_artifact is None:
            deps._create_artifact_record(
                artifact_repository=artifact_repository,
                run_id=run_id,
                artifact_type=deps.RELATED_NOTICE_ARTIFACT_TYPE,
                written_artifact=related_notice_artifact,
                meta={
                    "stage": "finalize",
                    "project_count": int(related_notice_payload.get("project_count") or 0),
                    "item_count": int(related_notice_payload.get("item_count") or 0),
                    "backend": "precomputed",
                },
            )
        deps._update_related_notice_summary(
            run_id=run_id,
            summary_patch={
                "related_notice_file_name": related_notice_artifact.file_name,
                "related_notice_projects": int(related_notice_payload.get("project_count") or 0),
                "related_notice_items": int(related_notice_payload.get("item_count") or 0),
                "related_notice_precomputed": True,
                "related_notice_precompute_status": "success",
                "related_notice_precompute_error": "",
                "related_notice_project_statuses": deps._build_related_notice_project_status_patch(
                    payload_project_keys,
                    status="success",
                ),
            },
        )
        deps._log_info(
            run_id=run_id,
            stage="finalize",
            message="related notices precomputed",
            meta={
                "project_count": int(related_notice_payload.get("project_count") or 0),
                "item_count": int(related_notice_payload.get("item_count") or 0),
                "artifact_file_name": related_notice_artifact.file_name,
            },
        )
        if not project_key:
            try:
                published_snapshot = deps.publish_related_notice_snapshot_set_for_run(
                    run_id=run_id,
                    related_notice_payload=related_notice_payload,
                )
                published_snapshot_set_id = str(
                    published_snapshot.get("published_snapshot_set_id") or ""
                ).strip()
                deps._update_related_notice_summary(
                    run_id=run_id,
                    summary_patch={
                        "related_notice_snapshot_set_id": published_snapshot_set_id,
                    },
                )
                deps._queue_related_notice_incremental_recompute(
                    run_id=run_id,
                    payload=related_notice_payload,
                    published_snapshot_set_id=published_snapshot_set_id,
                )
            except Exception as exc:
                deps._log_warning(
                    run_id=run_id,
                    stage="finalize",
                    message="related notice publish failed",
                    meta={"error": str(exc)},
                )
        if project_key and backfill_remaining:
            all_project_payload = deps._build_related_notice_artifact_payload(
                run_id=run_id,
                params=params,
                seed_rows=seed_rows,
                target_project_keys=None,
                limit_projects=False,
                prefer_seed_fallback_on_cache_miss=True,
            )
            existing_keys = set(deps._related_notice_payload_project_keys(related_notice_payload))
            remaining_keys = [
                str(item.get("project_key") or "").strip()
                for item in (all_project_payload.get("projects") or [])
                if str(item.get("project_key") or "").strip() and str(item.get("project_key") or "").strip() not in existing_keys
            ]
            if remaining_keys:
                deps._update_related_notice_summary(
                    run_id=run_id,
                    summary_patch={
                        "related_notice_project_statuses": deps._build_related_notice_project_status_patch(
                            remaining_keys,
                            status="queued",
                        ),
                    },
                )
                for remaining_key in remaining_keys:
                    try:
                        deps.precompute_related_notices_for_run(
                            run_id,
                            project_key=remaining_key,
                            backfill_remaining=False,
                        )
                    except Exception:
                        continue
    except Exception as exc:
        if project_key:
            deps.finish_related_notice_progress(
                project_key=project_key,
                status="failed",
                items=[],
                message=f"연관 공고 검색 중 오류가 발생했습니다: {exc}",
            )
            deps._upsert_related_notice_cache_entry(
                project_entry={
                    "project_key": project_key,
                    "project_name": "",
                    "project_search_name": "",
                    "issuer_name": "",
                    "source": "",
                    "algorithm_version": deps.RELATED_NOTICE_ALGORITHM_VERSION,
                    "items": [],
                },
                status="failed",
                source_run_id=run_id,
                error=str(exc),
            )
        deps._update_related_notice_summary(
            run_id=run_id,
            summary_patch={
                "related_notice_precomputed": False,
                "related_notice_precompute_status": "failed",
                "related_notice_precompute_error": str(exc),
                "related_notice_project_statuses": deps._build_related_notice_project_status_patch(
                    [project_key] if project_key else [],
                    status="failed",
                    error=str(exc),
                ),
            },
        )
        deps._log_warning(
            run_id=run_id,
            stage="finalize",
            message="related notice precompute failed",
            meta={"error": str(exc)},
        )
