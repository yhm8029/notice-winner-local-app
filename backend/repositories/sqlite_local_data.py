from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID
from uuid import uuid4

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID
from backend.sales_claims import SALES_CLAIM_STATUS_ACTIVE
from backend.sales_claims import SALES_CLAIM_STATUS_LOST
from backend.sales_claims import SALES_CLAIM_STATUS_WON
from backend.sales_claims import SalesActor
from backend.sales_claims import SalesClaimConflictError
from backend.sales_claims import SalesClaimInvalidTransitionError
from backend.sales_claims import SalesClaimNotFoundError
from backend.sales_claims import SalesClaimPermissionError
from backend.sales_claims import SalesClaimRecord
from backend.sales_claims import append_sales_note_entry
from backend.sales_claims import build_close_sales_note_text
from backend.sales_claims import build_system_sales_note_text
from backend.sales_claims import normalize_sales_claim_status
from backend.sales_claims import summarize_sales_claim_records

from .backfill_conflicts import BackfillConflictRepository
from .backfill_conflicts import BackfillConflictRepositoryConfigError
from .backfill_conflicts import BackfillConflictRow
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepository
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRepositoryConfigError
from .home_bootstrap_snapshots import HomeBootstrapSnapshotRow
from .related_notice_cache import RelatedNoticeCacheRepository
from .related_notice_cache import RelatedNoticeCacheRepositoryConfigError
from .related_notice_cache import RelatedNoticeCacheRow
from .related_notice_publications import RelatedNoticePublicationRepository
from .related_notice_publications import RelatedNoticePublicationRepositoryConfigError
from .related_notice_publications import RelatedNoticePublicationRow
from .sales_claims import SalesClaimRepository
from .sales_claims import SalesClaimRepositoryConfigError
from .sqlite_common import LocalRowsStore
from .sqlite_common import SqliteRepositoryConfig
from .sqlite_common import row_sort_text
from .sqlite_common import utc_now_text
from .supabase_sales_claims_runtime import parse_datetime
from .supabase_sales_claims_runtime import parse_datetime_nullable
from .supabase_sales_claims_runtime import parse_high_krw
from .supabase_sales_claims_runtime import parse_int_nullable
from .supabase_sales_claims_runtime import parse_low_krw
from .supabase_sales_claims_runtime import parse_uuid
from .supabase_sales_claims_runtime import serialize_claim_snapshot
from .tracker_change_events import TrackerChangeEventRepository
from .tracker_change_events import TrackerChangeEventRepositoryConfigError
from .tracker_change_events import TrackerChangeEventRow
from .tracker_entries import TRACKER_CHANGE_SOURCES
from .tracker_entries import TRACKER_EDITABLE_FIELDS
from .tracker_entries import TrackerEntryAuditLogRow
from .tracker_entries import TrackerEntryPatchResult
from .tracker_entries import TrackerEntryRepository
from .tracker_entries import TrackerEntryRepositoryConfigError
from .tracker_entries import TrackerEntryRow
from .tracker_entries import coerce_tracker_override_value
from .tracker_entries import tracker_entry_matches_region
from .tracker_entries import tracker_entry_matches_title_visibility
from .tracker_entry_snapshots import TrackerEntrySnapshotRepository
from .tracker_entry_snapshots import TrackerEntrySnapshotRepositoryConfigError
from .tracker_entry_snapshots import TrackerEntrySnapshotRow


TRACKER_ENTRIES_TABLE = "tracker_entries"
TRACKER_AUDIT_LOGS_TABLE = "tracker_entry_audit_logs"
RELATED_NOTICE_CACHE_TABLE = "project_related_notice_cache"
RELATED_NOTICE_PUBLICATIONS_TABLE = "related_notice_publications"
SALES_CLAIMS_TABLE = "project_sales_claims"
TRACKER_CHANGE_EVENTS_TABLE = "tracker_change_events"
TRACKER_ENTRY_SNAPSHOTS_TABLE = "tracker_entry_snapshots"
HOME_BOOTSTRAP_SNAPSHOTS_TABLE = "home_bootstrap_snapshots"
BACKFILL_CONFLICTS_TABLE = "backfill_conflicts"


def _store(config: SqliteRepositoryConfig | None, error_cls: type[Exception]) -> LocalRowsStore:
    return LocalRowsStore(config or SqliteRepositoryConfig.from_env(error_cls=error_cls))


def _same_uuid(left: Any, right: Any) -> bool:
    return str(left or "") == str(right or "")


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _row_id(row: dict[str, Any], *keys: str, fallback: str | None = None) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback or str(uuid4())


def _claim_row_id(organization_id: UUID | str, project_id: UUID | str) -> str:
    return f"{organization_id}:{project_id}"


def _page(rows: list[dict[str, Any]], *, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = len(rows)
    start = max(int(page or 1) - 1, 0) * max(int(page_size or 1), 1)
    end = start + max(int(page_size or 1), 1)
    return rows[start:end], total


class SqliteTrackerEntryRepository(TrackerEntryRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, TrackerEntryRepositoryConfigError)
        self._organization_id = str(DEFAULT_PHASE1_ORGANIZATION_ID)

    def list_entry_summaries(self, **kwargs: Any) -> tuple[list[TrackerEntryRow], int]:
        rows, total = self.list_entries(**kwargs)
        return [self._to_summary_entry(row) for row in rows], total

    def list_entries(
        self,
        *,
        page: int,
        page_size: int,
        q: str,
        region: str,
        exclude_auxiliary_titles: bool,
        edited_only: bool,
        source_run_id: UUID | None,
        source_tracker_run_id: UUID | None,
        sheet_name: str,
        section_name: str,
    ) -> tuple[list[TrackerEntryRow], int]:
        query = q.strip().lower()
        sheet_filter = sheet_name.strip().lower()
        section_filter = section_name.strip().lower()
        source_run_text = str(source_run_id) if source_run_id is not None else None
        source_tracker_text = str(source_tracker_run_id) if source_tracker_run_id is not None else None
        rows: list[TrackerEntryRow] = []
        for raw_row in self._raw_rows():
            if source_run_text is not None and str(raw_row.get("source_run_id")) != source_run_text:
                continue
            if source_tracker_text is not None and str(raw_row.get("source_tracker_run_id")) != source_tracker_text:
                continue
            if sheet_filter and str(raw_row.get("sheet_name") or "").lower() != sheet_filter:
                continue
            if section_filter and str(raw_row.get("section_name") or "").lower() != section_filter:
                continue
            effective = self._to_effective_entry(raw_row)
            if edited_only and not effective["overridden_fields"]:
                continue
            if query and not self._matches_query(effective, query):
                continue
            if not tracker_entry_matches_region(effective, region):
                continue
            if not tracker_entry_matches_title_visibility(
                effective,
                exclude_auxiliary_titles=exclude_auxiliary_titles,
            ):
                continue
            rows.append(effective)
        rows.sort(key=lambda item: (int(item.get("row_no") or 0), str(item.get("id") or "")))
        return _page(rows, page=page, page_size=page_size)

    def list_entries_for_export(self, **kwargs: Any) -> tuple[list[TrackerEntryRow], int]:
        return self.list_entries(**kwargs)

    def get_entries_data_version(self) -> str:
        rows = self._raw_rows()
        if not rows:
            return "count=0;updated_at="
        latest_updated_at = max(row_sort_text(row.get("updated_at")) for row in rows)
        return f"count={len(rows)};updated_at={latest_updated_at}"

    def get_entry(self, entry_id: UUID) -> TrackerEntryRow | None:
        row = self._store.get_row(TRACKER_ENTRIES_TABLE, str(entry_id))
        if row is None or not self._is_local_organization(row):
            return None
        return self._to_effective_entry(row)

    def get_entry_by_entry_key(self, entry_key: str) -> TrackerEntryRow | None:
        row = self._find_by_entry_key(str(entry_key or "").strip())
        if row is None:
            return None
        return self._to_effective_entry(row)

    def apply_override(
        self,
        *,
        entry_id: UUID,
        field_name: str,
        new_value: str | None,
        actor_user_id: UUID | None,
        actor_label: str,
        change_source: str,
    ) -> TrackerEntryPatchResult | None:
        row = self._store.get_row(TRACKER_ENTRIES_TABLE, str(entry_id))
        if row is None or not self._is_local_organization(row):
            return None
        if field_name not in TRACKER_EDITABLE_FIELDS:
            raise ValueError(f"unsupported field_name: {field_name}")
        if actor_user_id is None and not actor_label:
            raise ValueError("actor_user_id or actor_label is required")
        if change_source not in TRACKER_CHANGE_SOURCES:
            raise ValueError(f"unsupported change_source: {change_source}")

        source_key = f"{field_name}_source"
        override_key = f"{field_name}_override"
        source_value = str(row.get(source_key) or "")
        current_override = row.get(override_key)
        old_effective = current_override if current_override is not None else source_value
        next_override = coerce_tracker_override_value(
            field_name=field_name,
            new_value=new_value,
            source_value=source_value,
            current_effective_value=str(old_effective or ""),
        )
        if next_override == source_value:
            next_override = None
        new_effective = next_override if next_override is not None else source_value
        if current_override == next_override:
            return TrackerEntryPatchResult(changed=False, entry=self._to_effective_entry(row), audit_log=None)

        now = utc_now_text()
        row[override_key] = next_override
        row["last_edited_at"] = now
        row["last_edited_by"] = str(actor_user_id) if actor_user_id is not None else None
        row["last_edited_by_label"] = actor_label
        row["updated_at"] = now
        self._store.upsert_row(TRACKER_ENTRIES_TABLE, str(entry_id), row, created_at=row.get("created_at"), updated_at=now)

        audit_log = None
        if old_effective != new_effective:
            audit_log = self._append_audit_log(
                entry_id=entry_id,
                field_name=field_name,
                old_value=str(old_effective or ""),
                new_value=str(new_effective or ""),
                actor_user_id=actor_user_id,
                actor_label=actor_label,
                change_source=change_source,
                created_at=now,
            )
        return TrackerEntryPatchResult(changed=audit_log is not None, entry=self._to_effective_entry(row), audit_log=audit_log)

    def upsert_source_entries(
        self,
        *,
        source_run_id: UUID,
        source_tracker_run_id: UUID,
        entries: list[dict[str, Any]],
    ) -> list[TrackerEntryRow]:
        now = utc_now_text()
        upserted: list[TrackerEntryRow] = []
        for entry in entries:
            entry_key = str(entry["entry_key"])
            row = self._find_by_entry_key(entry_key)
            if row is None:
                entry_id = uuid4()
                row = self._build_entry(
                    entry_id=entry_id,
                    source_run_id=source_run_id,
                    source_tracker_run_id=source_tracker_run_id,
                    entry=entry,
                    created_at=now,
                )
            else:
                row["source_run_id"] = str(source_run_id)
                row["source_tracker_run_id"] = str(source_tracker_run_id)
                row["sheet_name"] = str(entry.get("sheet_name", row.get("sheet_name") or "Sheet1"))
                row["section_name"] = str(entry.get("section_name", row.get("section_name") or "facility_cost"))
                row["row_no"] = int(entry["row_no"])
                row["source_bid_no"] = str(entry["source_bid_no"])
                row["source_bid_ord"] = str(entry["source_bid_ord"])
                row["source_project_name_norm"] = str(entry["source_project_name_norm"])
                for field_name in TRACKER_EDITABLE_FIELDS:
                    row[f"{field_name}_source"] = str(entry.get(field_name, "") or "")
                for field_name in (
                    "opening_scheduled_date",
                    "contract_date",
                    "construction_duration_days",
                    "completion_expected_date_explicit",
                    "completion_expected_date_computed",
                ):
                    row[f"{field_name}_source"] = str(entry.get(field_name) or "")
                row["updated_at"] = now
            self._store.upsert_row(
                TRACKER_ENTRIES_TABLE,
                str(row["id"]),
                row,
                created_at=row.get("created_at"),
                updated_at=row.get("updated_at"),
            )
            upserted.append(self._to_effective_entry(row))
        upserted.sort(key=lambda item: (int(item.get("row_no") or 0), str(item.get("id") or "")))
        return upserted

    def delete_entries_by_source_tracker_run_id(self, *, source_tracker_run_id: UUID) -> int:
        matching_ids = [
            str(row.get("id"))
            for row in self._raw_rows()
            if str(row.get("source_tracker_run_id")) == str(source_tracker_run_id)
        ]
        for entry_id in matching_ids:
            self._store.delete_row(TRACKER_ENTRIES_TABLE, entry_id)
        self._store.delete_matching(
            TRACKER_AUDIT_LOGS_TABLE,
            lambda row: str(row.get("tracker_entry_id")) in set(matching_ids),
        )
        return len(matching_ids)

    def list_audit_logs(
        self,
        *,
        entry_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[TrackerEntryAuditLogRow], int | None]:
        items = [
            dict(row)
            for row in self._store.list_rows(TRACKER_AUDIT_LOGS_TABLE)
            if str(row.get("tracker_entry_id")) == str(entry_id)
        ]
        items.sort(key=lambda item: int(item.get("id") or 0), reverse=True)
        if cursor is not None:
            items = [item for item in items if int(item.get("id") or 0) < cursor]
        page_items = items[:limit]
        next_cursor = int(page_items[-1]["id"]) if len(items) > limit and page_items else None
        return page_items, next_cursor

    def _raw_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._store.list_rows(TRACKER_ENTRIES_TABLE) if self._is_local_organization(row)]

    def _is_local_organization(self, row: dict[str, Any]) -> bool:
        return str(row.get("organization_id")) == self._organization_id

    def _find_by_entry_key(self, entry_key: str) -> dict[str, Any] | None:
        if not entry_key:
            return None
        for row in self._raw_rows():
            if str(row.get("entry_key") or "") == entry_key:
                return row
        return None

    def _build_entry(
        self,
        *,
        entry_id: UUID,
        source_run_id: UUID,
        source_tracker_run_id: UUID,
        entry: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        row: dict[str, Any] = {
            "id": str(entry_id),
            "organization_id": self._organization_id,
            "source_run_id": str(source_run_id),
            "source_tracker_run_id": str(source_tracker_run_id),
            "entry_key": str(entry["entry_key"]),
            "sheet_name": str(entry.get("sheet_name") or "Sheet1"),
            "section_name": str(entry.get("section_name") or "facility_cost"),
            "row_no": int(entry["row_no"]),
            "source_bid_no": str(entry["source_bid_no"]),
            "source_bid_ord": str(entry["source_bid_ord"]),
            "source_project_name_norm": str(entry["source_project_name_norm"]),
            "last_edited_at": None,
            "last_edited_by": None,
            "last_edited_by_label": "",
            "created_at": created_at,
            "updated_at": created_at,
        }
        for field_name in TRACKER_EDITABLE_FIELDS:
            row[f"{field_name}_source"] = str(entry.get(field_name, "") or "")
            row[f"{field_name}_override"] = None
        for field_name in (
            "opening_scheduled_date",
            "contract_date",
            "construction_duration_days",
            "completion_expected_date_explicit",
            "completion_expected_date_computed",
        ):
            row[f"{field_name}_source"] = str(entry.get(field_name) or "")
        return row

    def _append_audit_log(
        self,
        *,
        entry_id: UUID,
        field_name: str,
        old_value: str,
        new_value: str,
        actor_user_id: UUID | None,
        actor_label: str,
        change_source: str,
        created_at: str,
    ) -> TrackerEntryAuditLogRow:
        row: TrackerEntryAuditLogRow = {
            "tracker_entry_id": str(entry_id),
            "field_name": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "actor_user_id": str(actor_user_id) if actor_user_id is not None else None,
            "actor_label": actor_label,
            "change_source": change_source,
            "created_at": created_at,
        }
        return self._store.insert_with_next_integer_id(TRACKER_AUDIT_LOGS_TABLE, row, created_at=created_at)

    def _to_effective_entry(self, row: dict[str, Any]) -> TrackerEntryRow:
        effective: TrackerEntryRow = {
            "id": row.get("id"),
            "organization_id": row.get("organization_id"),
            "source_run_id": row.get("source_run_id"),
            "source_tracker_run_id": row.get("source_tracker_run_id"),
            "entry_key": row.get("entry_key"),
            "sheet_name": row.get("sheet_name") or "Sheet1",
            "section_name": row.get("section_name") or "facility_cost",
            "row_no": int(row.get("row_no") or 0),
            "source_bid_no": row.get("source_bid_no") or "",
            "source_bid_ord": row.get("source_bid_ord") or "",
            "source_project_name_norm": row.get("source_project_name_norm") or "",
            "opening_scheduled_date": row.get("opening_scheduled_date_source", ""),
            "contract_date": row.get("contract_date_source", ""),
            "construction_duration_days": row.get("construction_duration_days_source", ""),
            "completion_expected_date_explicit": row.get("completion_expected_date_explicit_source", ""),
            "completion_expected_date_computed": row.get("completion_expected_date_computed_source", ""),
            "last_edited_at": row.get("last_edited_at"),
            "last_edited_by": row.get("last_edited_by"),
            "last_edited_by_label": row.get("last_edited_by_label") or "",
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        overridden_fields: list[str] = []
        for field_name in TRACKER_EDITABLE_FIELDS:
            override_value = row.get(f"{field_name}_override")
            effective[field_name] = override_value if override_value is not None else row.get(f"{field_name}_source", "")
            if override_value is not None:
                overridden_fields.append(field_name)
        effective["overridden_fields"] = overridden_fields
        return effective

    def _to_summary_entry(self, row: TrackerEntryRow) -> TrackerEntryRow:
        return {
            "id": row["id"],
            "organization_id": row["organization_id"],
            "source_run_id": row["source_run_id"],
            "source_tracker_run_id": row["source_tracker_run_id"],
            "entry_key": row["entry_key"],
            "row_no": row["row_no"],
            "project_name": row["project_name"],
            "gross_area_scale": row["gross_area_scale"],
            "construction_cost": row["construction_cost"],
            "demand_org_name": row["demand_org_name"],
            "demand_contact": row["demand_contact"],
            "client_location": row["client_location"],
            "site_location_1": row["site_location_1"],
            "architect_office": row["architect_office"],
            "opening_scheduled_date": row.get("opening_scheduled_date", ""),
            "construction_start_date": row["construction_start_date"],
            "contract_date": row.get("contract_date", ""),
            "construction_duration_days": row.get("construction_duration_days", ""),
            "completion_expected_date_explicit": row.get("completion_expected_date_explicit", ""),
            "completion_expected_date_computed": row.get("completion_expected_date_computed", ""),
            "last_checked_date": row["last_checked_date"],
            "progress_note": row["progress_note"],
            "building_automation_estimated_amount": row["building_automation_estimated_amount"],
            "overridden_fields": list(row.get("overridden_fields") or []),
        }

    @staticmethod
    def _matches_query(row: TrackerEntryRow, query: str) -> bool:
        project_name = str(row.get("project_name") or "").lower()
        return bool(project_name) and query in project_name


class SqliteRelatedNoticeCacheRepository(RelatedNoticeCacheRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, RelatedNoticeCacheRepositoryConfigError)

    def get_cache(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        key = str(project_key or "").strip()
        snapshot_key = str(snapshot_set_id or "legacy").strip() or "legacy"
        for row in self._store.list_rows(RELATED_NOTICE_CACHE_TABLE):
            if str(row.get("project_key") or "").strip() == key and str(row.get("snapshot_set_id") or "legacy").strip() == snapshot_key:
                return dict(row)
        return None

    def upsert_cache(self, row: RelatedNoticeCacheRow) -> RelatedNoticeCacheRow:
        project_key = str(row.get("project_key") or "").strip()
        snapshot_set_id = str(row.get("snapshot_set_id") or "legacy").strip() or "legacy"
        now = utc_now_text()
        existing = self.get_cache(project_key=project_key, snapshot_set_id=snapshot_set_id) or {}
        merged = {
            "id": existing.get("id") or str(uuid4()),
            "organization_id": existing.get("organization_id") or str(DEFAULT_PHASE1_ORGANIZATION_ID),
            "project_key": project_key,
            "snapshot_set_id": snapshot_set_id,
            "project_name": "",
            "project_search_name": "",
            "issuer_name": "",
            "status": "queued",
            "source": "",
            "algorithm_version": 0,
            "item_count": 0,
            "error": "",
            "payload_json": {},
            "source_run_id": None,
            "generated_at": None,
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
        }
        merged.update(existing)
        merged.update(dict(row))
        merged["project_key"] = project_key
        merged["snapshot_set_id"] = snapshot_set_id
        merged["updated_at"] = now
        return self._store.upsert_row(
            RELATED_NOTICE_CACHE_TABLE,
            _row_id(merged, "id", fallback=f"{snapshot_set_id}:{project_key}"),
            merged,
            created_at=merged.get("created_at"),
            updated_at=now,
        )

    def list_queued(self, *, limit: int = 5) -> list[RelatedNoticeCacheRow]:
        rows = [dict(row) for row in self._store.list_rows(RELATED_NOTICE_CACHE_TABLE) if str(row.get("status") or "").strip() == "queued"]
        rows.sort(key=lambda row: row_sort_text(row.get("updated_at") or row.get("created_at")))
        return rows[: max(0, int(limit or 0))]

    def claim_queued(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        row = self.get_cache(project_key=project_key, snapshot_set_id=snapshot_set_id)
        if row is None or str(row.get("status") or "").strip() != "queued":
            return None
        row["status"] = "running"
        row["updated_at"] = utc_now_text()
        return self._store.upsert_row(
            RELATED_NOTICE_CACHE_TABLE,
            _row_id(row, "id"),
            row,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


class SqliteRelatedNoticePublicationRepository(RelatedNoticePublicationRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, RelatedNoticePublicationRepositoryConfigError)

    def get_publication(self, *, organization_id: UUID) -> RelatedNoticePublicationRow | None:
        for row in self._store.list_rows(RELATED_NOTICE_PUBLICATIONS_TABLE):
            if _same_uuid(row.get("organization_id"), organization_id):
                return deepcopy(row)
        return None

    def upsert_publication(
        self,
        *,
        organization_id: UUID,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: Any,
        published_at: Any,
    ) -> RelatedNoticePublicationRow:
        existing = self.get_publication(organization_id=organization_id) or {}
        generated_at_value = _coerce_datetime(generated_at).isoformat()
        published_at_value = _coerce_datetime(published_at).isoformat()
        row = {
            "organization_id": str(organization_id),
            "published_snapshot_set_id": str(published_snapshot_set_id or ""),
            "source_run_id": str(source_run_id),
            "generated_at": generated_at_value,
            "published_at": published_at_value,
            "created_at": existing.get("created_at") or generated_at_value,
            "updated_at": published_at_value,
        }
        return self._store.upsert_row(RELATED_NOTICE_PUBLICATIONS_TABLE, str(organization_id), row, created_at=row["created_at"], updated_at=row["updated_at"])

    def upsert_publication_if_current(
        self,
        *,
        organization_id: UUID,
        expected_updated_at: Any,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: Any,
        published_at: Any,
    ) -> RelatedNoticePublicationRow:
        existing = self.get_publication(organization_id=organization_id)
        if existing and _coerce_datetime(existing["updated_at"]) != _coerce_datetime(expected_updated_at):
            return existing
        return self.upsert_publication(
            organization_id=organization_id,
            published_snapshot_set_id=published_snapshot_set_id,
            source_run_id=source_run_id,
            generated_at=generated_at,
            published_at=published_at,
        )


class SqliteTrackerEntrySnapshotRepository(TrackerEntrySnapshotRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, TrackerEntrySnapshotRepositoryConfigError)

    def upsert_snapshots(self, *, organization_id: UUID, snapshots: list[dict[str, Any]]) -> list[TrackerEntrySnapshotRow]:
        rows: list[TrackerEntrySnapshotRow] = []
        now = utc_now_text()
        for payload in snapshots:
            tracker_entry_id = payload.get("tracker_entry_id")
            if tracker_entry_id is None:
                continue
            row = {
                "tracker_entry_id": str(tracker_entry_id),
                "organization_id": str(organization_id),
                "summary_json": deepcopy(dict(payload.get("summary_json") or {})),
                "detail_json": deepcopy(dict(payload.get("detail_json") or {})),
                "export_json": deepcopy(dict(payload.get("export_json") or {})),
                "updated_at": row_sort_text(payload.get("updated_at") or now),
            }
            rows.append(
                self._store.upsert_row(
                    TRACKER_ENTRY_SNAPSHOTS_TABLE,
                    str(tracker_entry_id),
                    row,
                    updated_at=row["updated_at"],
                )
            )
        return rows

    def get_snapshots(self, *, organization_id: UUID, tracker_entry_ids: list[UUID]) -> list[TrackerEntrySnapshotRow]:
        wanted = {str(item) for item in tracker_entry_ids}
        rows: list[TrackerEntrySnapshotRow] = []
        for row in self._store.list_rows(TRACKER_ENTRY_SNAPSHOTS_TABLE):
            if str(row.get("tracker_entry_id")) in wanted and _same_uuid(row.get("organization_id"), organization_id):
                rows.append(deepcopy(row))
        return rows


class SqliteHomeBootstrapSnapshotRepository(HomeBootstrapSnapshotRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, HomeBootstrapSnapshotRepositoryConfigError)

    def get_snapshot(self, *, organization_id: UUID) -> HomeBootstrapSnapshotRow | None:
        for row in self._store.list_rows(HOME_BOOTSTRAP_SNAPSHOTS_TABLE):
            if _same_uuid(row.get("organization_id"), organization_id):
                return deepcopy(row)
        return None

    def upsert_snapshot(
        self,
        *,
        organization_id: UUID,
        snapshot_version: int,
        payload_json: dict[str, Any],
        generated_at: Any,
    ) -> HomeBootstrapSnapshotRow | None:
        now = utc_now_text()
        previous = self.get_snapshot(organization_id=organization_id) or {}
        row = {
            "organization_id": str(organization_id),
            "snapshot_version": int(snapshot_version or 0),
            "payload_json": deepcopy(dict(payload_json or {})),
            "generated_at": row_sort_text(generated_at or now),
            "invalidated_at": None,
            "created_at": previous.get("created_at") or now,
            "updated_at": now,
        }
        return self._store.upsert_row(HOME_BOOTSTRAP_SNAPSHOTS_TABLE, str(organization_id), row, created_at=row["created_at"], updated_at=now)

    def invalidate_snapshot(self, *, organization_id: UUID) -> None:
        row = self.get_snapshot(organization_id=organization_id)
        if row is None:
            return
        now = utc_now_text()
        row["invalidated_at"] = now
        row["updated_at"] = now
        self._store.upsert_row(HOME_BOOTSTRAP_SNAPSHOTS_TABLE, str(organization_id), row, created_at=row.get("created_at"), updated_at=now)


class SqliteBackfillConflictRepository(BackfillConflictRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, BackfillConflictRepositoryConfigError)

    def upsert_conflicts(self, *, organization_id: UUID, conflicts: list[dict[str, Any]]) -> list[BackfillConflictRow]:
        rows: list[BackfillConflictRow] = []
        for payload in conflicts:
            conflict_key = str(payload.get("conflict_key") or "").strip()
            existing = self._find_by_conflict_key(conflict_key) if conflict_key else None
            if existing:
                row = dict(existing)
                row.update(
                    {
                        "current_value": str(payload.get("current_value") or row.get("current_value") or ""),
                        "candidate_value": str(payload.get("candidate_value") or row.get("candidate_value") or ""),
                        "current_value_norm": str(payload.get("current_value_norm") or row.get("current_value_norm") or ""),
                        "candidate_value_norm": str(payload.get("candidate_value_norm") or row.get("candidate_value_norm") or ""),
                        "reason_code": str(payload.get("reason_code") or row.get("reason_code") or ""),
                        "source_kind": str(payload.get("source_kind") or row.get("source_kind") or ""),
                        "source_ref": str(payload.get("source_ref") or row.get("source_ref") or ""),
                        "source_run_id": payload.get("source_run_id") or row.get("source_run_id"),
                        "extractor_version": str(payload.get("extractor_version") or row.get("extractor_version") or ""),
                    }
                )
            else:
                row = {
                    "id": str(uuid4()),
                    "organization_id": str(organization_id),
                    "tracker_entry_id": str(payload.get("tracker_entry_id")) if payload.get("tracker_entry_id") is not None else None,
                    "field_name": str(payload.get("field_name") or "").strip(),
                    "current_value": str(payload.get("current_value") or ""),
                    "candidate_value": str(payload.get("candidate_value") or ""),
                    "current_value_norm": str(payload.get("current_value_norm") or "").strip(),
                    "candidate_value_norm": str(payload.get("candidate_value_norm") or "").strip(),
                    "reason_code": str(payload.get("reason_code") or "").strip(),
                    "source_kind": str(payload.get("source_kind") or "").strip(),
                    "source_ref": str(payload.get("source_ref") or "").strip(),
                    "source_run_id": str(payload.get("source_run_id")) if payload.get("source_run_id") is not None else None,
                    "extractor_version": str(payload.get("extractor_version") or "").strip(),
                    "detected_at": row_sort_text(payload.get("detected_at") or utc_now_text()),
                    "resolved_at": row_sort_text(payload.get("resolved_at")) or None,
                    "resolution": str(payload.get("resolution") or "").strip() or None,
                    "conflict_key": conflict_key,
                }
            rows.append(self._store.upsert_row(BACKFILL_CONFLICTS_TABLE, str(row["id"]), row, created_at=row.get("detected_at"), updated_at=row.get("resolved_at")))
        return rows

    def list_conflicts(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        source_run_id: UUID | None = None,
        include_resolved: bool = False,
    ) -> list[BackfillConflictRow]:
        rows = [
            dict(row)
            for row in self._store.list_rows(BACKFILL_CONFLICTS_TABLE)
            if _same_uuid(row.get("organization_id"), organization_id)
            and (tracker_entry_id is None or _same_uuid(row.get("tracker_entry_id"), tracker_entry_id))
            and (source_run_id is None or _same_uuid(row.get("source_run_id"), source_run_id))
            and (include_resolved or row.get("resolved_at") is None)
        ]
        rows.sort(key=lambda item: (row_sort_text(item.get("detected_at")), str(item.get("id") or "")), reverse=True)
        return rows[:limit]

    def resolve_conflict(self, *, organization_id: UUID, conflict_id: UUID, resolution: str) -> BackfillConflictRow | None:
        row = self._store.get_row(BACKFILL_CONFLICTS_TABLE, str(conflict_id))
        if row is None or not _same_uuid(row.get("organization_id"), organization_id):
            return None
        row["resolution"] = str(resolution or "").strip() or None
        row["resolved_at"] = utc_now_text()
        return self._store.upsert_row(BACKFILL_CONFLICTS_TABLE, str(conflict_id), row, created_at=row.get("detected_at"), updated_at=row["resolved_at"])

    def _find_by_conflict_key(self, conflict_key: str) -> BackfillConflictRow | None:
        for row in self._store.list_rows(BACKFILL_CONFLICTS_TABLE):
            if str(row.get("conflict_key") or "").strip() == conflict_key:
                return dict(row)
        return None


class SqliteTrackerChangeEventRepository(TrackerChangeEventRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, TrackerChangeEventRepositoryConfigError)

    def append_events(self, *, organization_id: UUID, events: list[dict[str, Any]]) -> list[TrackerChangeEventRow]:
        rows: list[TrackerChangeEventRow] = []
        for payload in events:
            dedupe_key = str(payload.get("dedupe_key") or "").strip()
            existing = self._find_by_dedupe_key(dedupe_key) if dedupe_key else None
            if existing:
                rows.append(existing)
                continue
            now = utc_now_text()
            row = {
                "id": str(uuid4()),
                "organization_id": str(organization_id),
                "tracker_entry_id": str(payload.get("tracker_entry_id")) if payload.get("tracker_entry_id") is not None else None,
                "event_type": str(payload.get("event_type") or "").strip(),
                "field_name": str(payload.get("field_name") or "").strip(),
                "old_value": str(payload.get("old_value") or ""),
                "new_value": str(payload.get("new_value") or ""),
                "old_value_norm": str(payload.get("old_value_norm") or "").strip(),
                "new_value_norm": str(payload.get("new_value_norm") or "").strip(),
                "source_run_id": str(payload.get("source_run_id")) if payload.get("source_run_id") is not None else None,
                "source_kind": str(payload.get("source_kind") or "").strip(),
                "source_ref": str(payload.get("source_ref") or "").strip(),
                "extractor_version": str(payload.get("extractor_version") or "").strip(),
                "reason_code": str(payload.get("reason_code") or "").strip(),
                "batch_key": str(payload.get("batch_key") or "").strip(),
                "dedupe_key": dedupe_key,
                "is_silent": bool(payload.get("is_silent")),
                "created_at": row_sort_text(payload.get("created_at") or now),
                "is_read": bool(payload.get("is_read")),
                "read_at": row_sort_text(payload.get("read_at")) or None,
            }
            rows.append(self._store.upsert_row(TRACKER_CHANGE_EVENTS_TABLE, str(row["id"]), row, created_at=row["created_at"], updated_at=row.get("read_at")))
        return rows

    def list_events(
        self,
        *,
        organization_id: UUID,
        limit: int,
        tracker_entry_id: UUID | None = None,
        include_silent: bool = False,
    ) -> list[TrackerChangeEventRow]:
        rows = [
            dict(row)
            for row in self._store.list_rows(TRACKER_CHANGE_EVENTS_TABLE)
            if _same_uuid(row.get("organization_id"), organization_id)
            and (tracker_entry_id is None or _same_uuid(row.get("tracker_entry_id"), tracker_entry_id))
            and (include_silent or not bool(row.get("is_silent")))
        ]
        rows.sort(key=lambda item: (row_sort_text(item.get("created_at")), str(item.get("id") or "")), reverse=True)
        return rows[:limit]

    def count_unread(self, *, organization_id: UUID) -> int:
        return sum(
            1
            for row in self._store.list_rows(TRACKER_CHANGE_EVENTS_TABLE)
            if _same_uuid(row.get("organization_id"), organization_id)
            and not bool(row.get("is_read"))
            and not bool(row.get("is_silent"))
        )

    def mark_read(
        self,
        *,
        organization_id: UUID,
        event_ids: list[UUID] | None = None,
        tracker_entry_id: UUID | None = None,
    ) -> int:
        targets = {str(item) for item in event_ids or []}
        updated = 0
        now = utc_now_text()
        for row in self._store.list_rows(TRACKER_CHANGE_EVENTS_TABLE):
            if not _same_uuid(row.get("organization_id"), organization_id):
                continue
            if targets and str(row.get("id")) not in targets:
                continue
            if not targets and tracker_entry_id is not None and not _same_uuid(row.get("tracker_entry_id"), tracker_entry_id):
                continue
            if bool(row.get("is_read")):
                continue
            row["is_read"] = True
            row["read_at"] = now
            self._store.upsert_row(TRACKER_CHANGE_EVENTS_TABLE, str(row["id"]), row, created_at=row.get("created_at"), updated_at=now)
            updated += 1
        return updated

    def _find_by_dedupe_key(self, dedupe_key: str) -> TrackerChangeEventRow | None:
        for row in self._store.list_rows(TRACKER_CHANGE_EVENTS_TABLE):
            if str(row.get("dedupe_key") or "").strip() == dedupe_key:
                return dict(row)
        return None


class SqliteSalesClaimRepository(SalesClaimRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = _store(config, SalesClaimRepositoryConfigError)

    def list_claims(
        self,
        *,
        organization_id: UUID,
        project_ids: list[UUID] | None = None,
        lightweight: bool = False,
    ) -> list[SalesClaimRecord]:
        wanted = {str(item) for item in project_ids or []}
        rows = [
            self._normalize_claim_row(row)
            for row in self._store.list_rows(SALES_CLAIMS_TABLE)
            if _same_uuid(row.get("organization_id"), organization_id)
            and bool(row.get("is_active", True))
            and (not wanted or str(row.get("project_id")) in wanted)
        ]
        return sorted(rows, key=lambda item: item.claimed_at)

    def claim_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        source_entry_id: UUID | None,
        source_run_id: UUID | None,
        project_name: str,
        estimated_amount_text: str,
    ) -> tuple[bool, SalesClaimRecord]:
        existing = self._get_active_claim(organization_id=actor.organization_id, project_id=project_id)
        if existing is not None:
            if actor.user_id is not None and existing.owner_user_id == actor.user_id:
                return False, existing
            raise SalesClaimConflictError(existing)
        now = datetime.now(timezone.utc).isoformat()
        low_krw = parse_low_krw(estimated_amount_text)
        high_krw = parse_high_krw(estimated_amount_text)
        row = {
            "id": str(uuid4()),
            "organization_id": str(actor.organization_id),
            "project_id": str(project_id),
            "source_entry_id": str(source_entry_id) if source_entry_id else None,
            "source_run_id": str(source_run_id) if source_run_id else None,
            "project_name": str(project_name or ""),
            "owner_user_id": str(actor.user_id) if actor.user_id else None,
            "owner_email": str(actor.email or ""),
            "owner_display_name": str(actor.display_name or actor.email or ""),
            "claimed_at": now,
            "current_owner_assigned_at": now,
            "released_at": None,
            "is_active": True,
            "claim_status": SALES_CLAIM_STATUS_ACTIVE,
            "closed_at": None,
            "closed_by": None,
            "sales_note": "",
            "sales_note_updated_at": None,
            "sales_note_updated_by": None,
            "estimated_amount_text": str(estimated_amount_text or ""),
            "estimated_amount_low_krw": low_krw,
            "estimated_amount_high_krw": high_krw,
            "created_at": now,
            "updated_at": now,
        }
        stored = self._upsert_claim_row(row)
        return True, self._normalize_claim_row(stored)

    def update_sales_note(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        sales_note: str,
        force_admin_override: bool = False,
    ) -> SalesClaimRecord:
        claim = self._require_active_claim(actor.organization_id, project_id)
        owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
        if not owner_match and not (force_admin_override and actor.is_admin):
            raise SalesClaimPermissionError("only the claim owner can update sales_note")
        if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE and not (force_admin_override and actor.is_admin):
            raise SalesClaimInvalidTransitionError("closed sales claims cannot be updated")
        row = serialize_claim_snapshot(claim)
        now = datetime.now(timezone.utc).isoformat()
        row["sales_note"] = str(sales_note or "")
        row["sales_note_updated_at"] = now
        row["sales_note_updated_by"] = str(actor.user_id) if actor.user_id else None
        row["updated_at"] = now
        return self._normalize_claim_row(self._upsert_claim_row(row))

    def transfer_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        target_user_id: UUID | None,
        target_email: str,
        target_display_name: str,
        force: bool = False,
    ) -> SalesClaimRecord:
        claim = self._require_active_claim(actor.organization_id, project_id)
        owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
        if not owner_match and not (force and actor.is_admin):
            raise SalesClaimPermissionError("you do not have permission to transfer this claim")
        if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE:
            raise SalesClaimInvalidTransitionError("closed sales claims cannot be transferred")
        next_owner_email = str(target_email or "").strip().lower()
        if not next_owner_email:
            raise SalesClaimInvalidTransitionError("target user is required")
        if target_user_id is not None and claim.owner_user_id == target_user_id:
            raise SalesClaimInvalidTransitionError("claim is already assigned to that user")
        if next_owner_email == claim.owner_email.strip().lower():
            raise SalesClaimInvalidTransitionError("claim is already assigned to that user")
        now_dt = datetime.now(timezone.utc)
        row = serialize_claim_snapshot(claim)
        row["owner_user_id"] = str(target_user_id) if target_user_id is not None else None
        row["owner_email"] = next_owner_email
        row["owner_display_name"] = str(target_display_name or next_owner_email)
        row["current_owner_assigned_at"] = now_dt.isoformat()
        row["sales_note"] = append_sales_note_entry(
            claim.sales_note,
            build_system_sales_note_text(
                f"{claim.owner_display_name or claim.owner_email} -> {target_display_name or next_owner_email} ?닿?"
            ),
            timestamp=now_dt,
        )
        row["sales_note_updated_at"] = now_dt.isoformat()
        row["sales_note_updated_by"] = str(actor.user_id) if actor.user_id else None
        row["updated_at"] = now_dt.isoformat()
        return self._normalize_claim_row(self._upsert_claim_row(row))

    def close_project(
        self,
        *,
        actor: SalesActor,
        project_id: UUID,
        outcome: str,
        contract_amount_text: str = "",
        force: bool = False,
    ) -> SalesClaimRecord:
        normalized_outcome = normalize_sales_claim_status(outcome)
        if normalized_outcome not in {SALES_CLAIM_STATUS_WON, SALES_CLAIM_STATUS_LOST}:
            raise SalesClaimInvalidTransitionError("sales claim close outcome must be won or lost")
        claim = self._require_active_claim(actor.organization_id, project_id)
        owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
        if not owner_match and not (force and actor.is_admin):
            raise SalesClaimPermissionError("you do not have permission to close this claim")
        if claim.claim_status != SALES_CLAIM_STATUS_ACTIVE:
            raise SalesClaimInvalidTransitionError("sales claim is already closed")
        now_dt = datetime.now(timezone.utc)
        row = serialize_claim_snapshot(claim)
        row["claim_status"] = normalized_outcome
        row["closed_at"] = now_dt.isoformat()
        row["closed_by"] = str(actor.user_id) if actor.user_id else None
        row["sales_note"] = append_sales_note_entry(
            claim.sales_note,
            build_close_sales_note_text(normalized_outcome, contract_amount_text),
            timestamp=now_dt,
        )
        row["sales_note_updated_at"] = now_dt.isoformat()
        row["sales_note_updated_by"] = str(actor.user_id) if actor.user_id else None
        row["updated_at"] = now_dt.isoformat()
        return self._normalize_claim_row(self._upsert_claim_row(row))

    def release_project(self, *, actor: SalesActor, project_id: UUID, force: bool = False) -> SalesClaimRecord:
        claim = self._require_active_claim(actor.organization_id, project_id)
        owner_match = actor.user_id is not None and claim.owner_user_id == actor.user_id
        if not owner_match and not (force and actor.is_admin):
            raise SalesClaimPermissionError("you do not have permission to release this claim")
        row = serialize_claim_snapshot(claim)
        now = datetime.now(timezone.utc).isoformat()
        row["is_active"] = False
        row["released_at"] = now
        row["updated_at"] = now
        return self._normalize_claim_row(self._upsert_claim_row(row))

    def summarize_by_user(self, *, organization_id: UUID) -> list[dict[str, Any]]:
        return summarize_sales_claim_records(self.list_claims(organization_id=organization_id))

    def _get_active_claim(self, *, organization_id: UUID, project_id: UUID) -> SalesClaimRecord | None:
        rows = self.list_claims(organization_id=organization_id, project_ids=[project_id])
        return rows[0] if rows else None

    def _require_active_claim(self, organization_id: UUID, project_id: UUID) -> SalesClaimRecord:
        claim = self._get_active_claim(organization_id=organization_id, project_id=project_id)
        if claim is None:
            raise SalesClaimNotFoundError("sales claim not found")
        return claim

    def _upsert_claim_row(self, row: dict[str, Any]) -> dict[str, Any]:
        row_id = _claim_row_id(row["organization_id"], row["project_id"])
        return self._store.upsert_row(SALES_CLAIMS_TABLE, row_id, row, created_at=row.get("created_at"), updated_at=row.get("updated_at"))

    @staticmethod
    def _normalize_claim_row(row: dict[str, Any]) -> SalesClaimRecord:
        claimed_at = parse_datetime(row.get("claimed_at") or row.get("created_at"))
        current_owner_assigned_at = parse_datetime(row.get("current_owner_assigned_at") or row.get("claimed_at") or row.get("created_at"))
        return SalesClaimRecord(
            organization_id=_coerce_uuid(row["organization_id"]),
            project_id=_coerce_uuid(row["project_id"]),
            source_entry_id=parse_uuid(row.get("source_entry_id")),
            source_run_id=parse_uuid(row.get("source_run_id")),
            project_name=str(row.get("project_name") or ""),
            owner_user_id=parse_uuid(row.get("owner_user_id")),
            owner_email=str(row.get("owner_email") or ""),
            owner_display_name=str(row.get("owner_display_name") or row.get("owner_email") or ""),
            claimed_at=claimed_at,
            current_owner_assigned_at=current_owner_assigned_at,
            released_at=parse_datetime_nullable(row.get("released_at")),
            is_active=bool(row.get("is_active", True)),
            claim_status=normalize_sales_claim_status(str(row.get("claim_status") or SALES_CLAIM_STATUS_ACTIVE)),
            closed_at=parse_datetime_nullable(row.get("closed_at")),
            closed_by=parse_uuid(row.get("closed_by")),
            sales_note=str(row.get("sales_note") or ""),
            sales_note_updated_at=parse_datetime_nullable(row.get("sales_note_updated_at")),
            sales_note_updated_by=parse_uuid(row.get("sales_note_updated_by")),
            estimated_amount_text=str(row.get("estimated_amount_text") or ""),
            estimated_amount_low_krw=parse_int_nullable(row.get("estimated_amount_low_krw")),
            estimated_amount_high_krw=parse_int_nullable(row.get("estimated_amount_high_krw")),
            created_at=parse_datetime(row.get("created_at") or claimed_at),
            updated_at=parse_datetime(row.get("updated_at") or row.get("created_at") or claimed_at),
        )
