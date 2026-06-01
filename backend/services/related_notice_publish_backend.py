from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from backend.phase1_defaults import load_phase1_identity
from backend.repositories import get_related_notice_cache_repository
from backend.repositories import get_related_notice_publication_repository
from backend.services.related_notice_response_cache import clear_related_notice_response_cache


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_datetime(value: Any, *, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return fallback
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _candidate_snapshot_set_id(run_id: UUID, snapshot_set_id: str | None) -> str:
    candidate = str(snapshot_set_id or "").strip()
    if candidate:
        return candidate
    return str(run_id)


def _publication_matches_candidate(
    publication: dict[str, Any] | None,
    *,
    candidate_snapshot_set_id: str,
    run_id: UUID,
    payload_generated_at: datetime,
    updated_at: datetime | None = None,
) -> bool:
    if publication is None:
        return False
    matches_candidate = (
        str(publication.get("published_snapshot_set_id") or "") == candidate_snapshot_set_id
        and str(publication.get("source_run_id") or "") == str(run_id)
        and _coerce_datetime(publication.get("generated_at"), fallback=payload_generated_at) == payload_generated_at
    )
    if not matches_candidate:
        return False
    if updated_at is None:
        return True
    return _coerce_datetime(publication.get("updated_at"), fallback=updated_at) == updated_at


def _publication_is_same_or_newer_than_candidate(
    publication: dict[str, Any] | None,
    *,
    candidate_snapshot_set_id: str,
    run_id: UUID,
    payload_generated_at: datetime,
) -> bool:
    if publication is None:
        return False
    current_generated_at = _coerce_datetime(publication.get("generated_at"), fallback=payload_generated_at)
    if current_generated_at > payload_generated_at:
        return True
    if current_generated_at < payload_generated_at:
        return False
    return _publication_matches_candidate(
        publication,
        candidate_snapshot_set_id=candidate_snapshot_set_id,
        run_id=run_id,
        payload_generated_at=payload_generated_at,
    )


def _build_candidate_cache_row(
    *,
    organization_id: Any,
    snapshot_set_id: str,
    run_id: UUID,
    generated_at: datetime,
    project_entry: dict[str, Any],
) -> dict[str, Any]:
    items = list(project_entry.get("items") or [])
    return {
        "organization_id": str(organization_id),
        "project_key": str(project_entry.get("project_key") or "").strip(),
        "snapshot_set_id": snapshot_set_id,
        "project_name": str(project_entry.get("project_name") or "").strip(),
        "project_search_name": str(project_entry.get("project_search_name") or "").strip(),
        "issuer_name": str(project_entry.get("issuer_name") or "").strip(),
        "status": "success",
        "source": str(project_entry.get("source") or "").strip(),
        "algorithm_version": int(project_entry.get("algorithm_version") or 0),
        "item_count": len(items),
        "error": "",
        "payload_json": dict(project_entry),
        "source_run_id": str(run_id),
        "generated_at": generated_at.isoformat(),
    }


def publish_related_notice_snapshot_set_for_run(
    *,
    run_id: UUID,
    related_notice_payload: dict[str, Any],
    snapshot_set_id: str | None = None,
    get_related_notice_cache_repository_fn: Any | None = None,
    get_related_notice_publication_repository_fn: Any | None = None,
    load_phase1_identity_fn: Any | None = None,
    utc_now_fn: Any | None = None,
) -> dict[str, Any]:
    if get_related_notice_cache_repository_fn is None:
        get_related_notice_cache_repository_fn = get_related_notice_cache_repository
    if get_related_notice_publication_repository_fn is None:
        get_related_notice_publication_repository_fn = get_related_notice_publication_repository
    if load_phase1_identity_fn is None:
        load_phase1_identity_fn = load_phase1_identity
    if utc_now_fn is None:
        utc_now_fn = _utcnow

    identity = load_phase1_identity_fn()
    candidate_snapshot_set_id = _candidate_snapshot_set_id(run_id, snapshot_set_id)
    payload_generated_at = _coerce_datetime(related_notice_payload.get("generated_at"), fallback=utc_now_fn())
    project_entries = [dict(item) for item in (related_notice_payload.get("projects") or []) if isinstance(item, dict)]

    cache_repository = get_related_notice_cache_repository_fn()
    previous_publication = get_related_notice_publication_repository_fn().get_publication(
        organization_id=identity.organization_id
    )
    for project_entry in project_entries:
        project_key = str(project_entry.get("project_key") or "").strip()
        if not project_key:
            continue
        cache_repository.upsert_cache(
            _build_candidate_cache_row(
                organization_id=identity.organization_id,
                snapshot_set_id=candidate_snapshot_set_id,
                run_id=run_id,
                generated_at=payload_generated_at,
                project_entry=project_entry,
            )
        )

    publication_repository = get_related_notice_publication_repository_fn()
    published_at = utc_now_fn()
    published_publication: dict[str, Any] | None = None
    if previous_publication is not None:
        previous_generated_at = _coerce_datetime(
            previous_publication.get("generated_at"),
            fallback=payload_generated_at,
        )
        if previous_generated_at > payload_generated_at:
            return dict(previous_publication)
    try:
        if previous_publication is not None:
            published_publication = publication_repository.upsert_publication_if_current(
                organization_id=identity.organization_id,
                expected_updated_at=previous_publication.get("updated_at"),
                published_snapshot_set_id=candidate_snapshot_set_id,
                source_run_id=run_id,
                generated_at=payload_generated_at,
                published_at=published_at,
            )
            if _publication_is_same_or_newer_than_candidate(
                published_publication,
                candidate_snapshot_set_id=candidate_snapshot_set_id,
                run_id=run_id,
                payload_generated_at=payload_generated_at,
            ):
                clear_related_notice_response_cache()
                return published_publication
            published_publication = publication_repository.upsert_publication_if_current(
                organization_id=identity.organization_id,
                expected_updated_at=published_publication.get("updated_at"),
                published_snapshot_set_id=candidate_snapshot_set_id,
                source_run_id=run_id,
                generated_at=payload_generated_at,
                published_at=published_at,
            )
            if _publication_is_same_or_newer_than_candidate(
                published_publication,
                candidate_snapshot_set_id=candidate_snapshot_set_id,
                run_id=run_id,
                payload_generated_at=payload_generated_at,
            ):
                clear_related_notice_response_cache()
                return published_publication
            raise RuntimeError("related notice publication CAS miss did not advance candidate")
        published_publication = publication_repository.upsert_publication(
            organization_id=identity.organization_id,
            published_snapshot_set_id=candidate_snapshot_set_id,
            source_run_id=run_id,
            generated_at=payload_generated_at,
            published_at=published_at,
        )
        clear_related_notice_response_cache()
        return published_publication
    except Exception:
        if previous_publication is not None:
            current_publication = publication_repository.get_publication(
                organization_id=identity.organization_id,
            )
            attempt_updated_at = _coerce_datetime(
                (published_publication or {}).get("updated_at"),
                fallback=published_at,
            )
            if current_publication is not None and not _publication_matches_candidate(
                current_publication,
                candidate_snapshot_set_id=candidate_snapshot_set_id,
                run_id=run_id,
                payload_generated_at=payload_generated_at,
                updated_at=attempt_updated_at,
            ):
                raise
            publication_repository.upsert_publication_if_current(
                organization_id=identity.organization_id,
                expected_updated_at=(
                    current_publication.get("updated_at") if current_publication is not None else previous_publication.get("updated_at")
                ),
                published_snapshot_set_id=str(previous_publication.get("published_snapshot_set_id") or ""),
                source_run_id=UUID(str(previous_publication.get("source_run_id") or run_id)),
                generated_at=previous_publication.get("generated_at") or payload_generated_at,
                published_at=previous_publication.get("published_at") or payload_generated_at,
            )
        raise
