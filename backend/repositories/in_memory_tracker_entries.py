from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID

from .tracker_entries import TRACKER_CHANGE_SOURCES
from .tracker_entries import TRACKER_EDITABLE_FIELDS
from .tracker_entries import TrackerEntryAuditLogRow
from .tracker_entries import TrackerEntryPatchResult
from .tracker_entries import TrackerEntryRepository
from .tracker_entries import TrackerEntryRow
from .tracker_entries import coerce_tracker_override_value
from .tracker_entries import tracker_entry_matches_region
from .tracker_entries import tracker_entry_matches_title_visibility


class InMemoryTrackerEntryRepository(TrackerEntryRepository):
    def __init__(self) -> None:
        self._entries: dict[UUID, dict[str, object]] = {}
        self._audit_logs_by_entry: dict[UUID, list[TrackerEntryAuditLogRow]] = {}
        self._next_audit_log_id = 1
        self._seed_entries()

    def list_entry_summaries(
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
        rows, total = self.list_entries(
            page=page,
            page_size=page_size,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
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

        rows: list[TrackerEntryRow] = []
        for row in self._entries.values():
            if source_run_id is not None and row["source_run_id"] != source_run_id:
                continue
            if source_tracker_run_id is not None and row["source_tracker_run_id"] != source_tracker_run_id:
                continue
            if sheet_filter and str(row["sheet_name"]).lower() != sheet_filter:
                continue
            if section_filter and str(row["section_name"]).lower() != section_filter:
                continue

            effective = self._to_effective_entry(row)
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

        rows.sort(key=lambda item: (item["row_no"], str(item["id"])))
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return rows[start:end], total

    def list_entries_for_export(
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
        return self.list_entries(
            page=page,
            page_size=page_size,
            q=q,
            region=region,
            exclude_auxiliary_titles=exclude_auxiliary_titles,
            edited_only=edited_only,
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )

    def get_entries_data_version(self) -> str:
        rows = [self._to_effective_entry(row) for row in self._entries.values()]
        if not rows:
            return "count=0;updated_at="
        latest_updated_at = max(str(row.get("updated_at") or "") for row in rows)
        return f"count={len(rows)};updated_at={latest_updated_at}"

    def get_entry(self, entry_id: UUID) -> TrackerEntryRow | None:
        row = self._entries.get(entry_id)
        if row is None:
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
        row = self._entries.get(entry_id)
        if row is None:
            return None

        if field_name not in TRACKER_EDITABLE_FIELDS:
            raise ValueError(f"unsupported field_name: {field_name}")
        if actor_user_id is None and not actor_label:
            raise ValueError("actor_user_id or actor_label is required")
        if change_source not in TRACKER_CHANGE_SOURCES:
            raise ValueError(f"unsupported change_source: {change_source}")

        source_key = f"{field_name}_source"
        override_key = f"{field_name}_override"
        source_value = str(row[source_key])
        current_override = row[override_key]
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
            return TrackerEntryPatchResult(
                changed=False,
                entry=self._to_effective_entry(row),
                audit_log=None,
            )

        now = datetime.now(timezone.utc)
        row[override_key] = next_override
        row["last_edited_at"] = now
        row["last_edited_by"] = actor_user_id
        row["last_edited_by_label"] = actor_label
        row["updated_at"] = now

        audit_log = None
        if old_effective != new_effective:
            audit_log = self._append_audit_log(
                entry_id=entry_id,
                field_name=field_name,
                old_value=old_effective,
                new_value=new_effective,
                actor_user_id=actor_user_id,
                actor_label=actor_label,
                change_source=change_source,
                created_at=now,
            )

        return TrackerEntryPatchResult(
            changed=audit_log is not None,
            entry=self._to_effective_entry(row),
            audit_log=audit_log,
        )

    def upsert_source_entries(
        self,
        *,
        source_run_id: UUID,
        source_tracker_run_id: UUID,
        entries: list[dict[str, object]],
    ) -> list[TrackerEntryRow]:
        now = datetime.now(timezone.utc)
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
                    entry_key=entry_key,
                    row_no=int(entry["row_no"]),
                    source_bid_no=str(entry["source_bid_no"]),
                    source_bid_ord=str(entry["source_bid_ord"]),
                    source_project_name_norm=str(entry["source_project_name_norm"]),
                    project_name=str(entry["project_name"]),
                    gross_area_scale=str(entry["gross_area_scale"]),
                    construction_cost=str(entry["construction_cost"]),
                    demand_org_name=str(entry["demand_org_name"]),
                    demand_contact=str(entry["demand_contact"]),
                    client_location=str(entry["client_location"]),
                    site_location_1=str(entry["site_location_1"]),
                    site_location_2=str(entry["site_location_2"]),
                    architect_office=str(entry["architect_office"]),
                    opening_scheduled_date=str(entry.get("opening_scheduled_date") or ""),
                    contract_date=str(entry.get("contract_date") or ""),
                    construction_duration_days=str(entry.get("construction_duration_days") or ""),
                    completion_expected_date_explicit=str(entry.get("completion_expected_date_explicit") or ""),
                    completion_expected_date_computed=str(entry.get("completion_expected_date_computed") or ""),
                    construction_start_date=str(entry["construction_start_date"]),
                    last_checked_date=str(entry["last_checked_date"]),
                    progress_note=str(entry["progress_note"]),
                    notice_date=str(entry["notice_date"]),
                    manager_name=str(entry["manager_name"]),
                    building_automation_estimated_amount=str(
                        entry["building_automation_estimated_amount"]
                    ),
                    created_at=now,
                )
                self._entries[entry_id] = row
            else:
                row["source_run_id"] = source_run_id
                row["source_tracker_run_id"] = source_tracker_run_id
                row["sheet_name"] = str(entry.get("sheet_name", row["sheet_name"]))
                row["section_name"] = str(entry.get("section_name", row["section_name"]))
                row["row_no"] = int(entry["row_no"])
                row["source_bid_no"] = str(entry["source_bid_no"])
                row["source_bid_ord"] = str(entry["source_bid_ord"])
                row["source_project_name_norm"] = str(entry["source_project_name_norm"])
                for field_name in TRACKER_EDITABLE_FIELDS:
                    row[f"{field_name}_source"] = str(entry.get(field_name, "") or "")
                row["opening_scheduled_date_source"] = str(entry.get("opening_scheduled_date") or "")
                row["contract_date_source"] = str(entry.get("contract_date") or "")
                row["construction_duration_days_source"] = str(entry.get("construction_duration_days") or "")
                row["completion_expected_date_explicit_source"] = str(
                    entry.get("completion_expected_date_explicit") or ""
                )
                row["completion_expected_date_computed_source"] = str(
                    entry.get("completion_expected_date_computed") or ""
                )
                row["updated_at"] = now
            upserted.append(self._to_effective_entry(row))

        upserted.sort(key=lambda item: (item["row_no"], str(item["id"])))
        return upserted

    def delete_entries_by_source_tracker_run_id(self, *, source_tracker_run_id: UUID) -> int:
        matching_ids = [
            entry_id
            for entry_id, row in self._entries.items()
            if row["source_tracker_run_id"] == source_tracker_run_id
        ]
        for entry_id in matching_ids:
            self._entries.pop(entry_id, None)
            self._audit_logs_by_entry.pop(entry_id, None)
        return len(matching_ids)

    def list_audit_logs(
        self,
        *,
        entry_id: UUID,
        cursor: int | None,
        limit: int,
    ) -> tuple[list[TrackerEntryAuditLogRow], int | None]:
        items = sorted(
            self._audit_logs_by_entry.get(entry_id, []),
            key=lambda item: int(item["id"]),
            reverse=True,
        )
        if cursor is not None:
            items = [item for item in items if int(item["id"]) < cursor]

        page_items = items[:limit]
        next_cursor = int(page_items[-1]["id"]) if len(items) > limit and page_items else None
        return page_items, next_cursor

    def _seed_entries(self) -> None:
        now = datetime(2026, 3, 12, 5, 0, tzinfo=timezone.utc)
        parent_run_id = uuid4()
        tracker_run_id = uuid4()

        first_id = uuid4()
        first_row = self._build_entry(
            entry_id=first_id,
            source_run_id=parent_run_id,
            source_tracker_run_id=tracker_run_id,
            entry_key="r25bk00555367|000|project-name",
            row_no=12,
            source_bid_no="R25BK00555367",
            source_bid_ord="000",
            source_project_name_norm="project-name",
            project_name="Project Name Alpha",
            gross_area_scale="12 floors / 14200 sqm",
            construction_cost="18500000000",
            demand_org_name="Korea Facilities Agency",
            demand_contact="Architecture Team Kim",
            client_location="Seoul Jung-gu",
            site_location_1="Seoul Jung-gu Eulji-ro",
            site_location_2="Seoul Jung-gu Supyo-dong",
            architect_office="Garam Architects",
            opening_scheduled_date="20260328",
            construction_start_date="2026-05-01",
            last_checked_date="2026-03-12",
            progress_note="",
            notice_date="2026-03-11",
            manager_name="Kim Younghee",
            building_automation_estimated_amount="350000000",
            created_at=now,
        )
        first_row["project_name_override"] = "Project Name A"
        first_row["progress_note_override"] = "Phone verification complete"
        first_row["last_edited_at"] = datetime(2026, 3, 12, 5, 5, tzinfo=timezone.utc)
        first_row["last_edited_by"] = None
        first_row["last_edited_by_label"] = "hyunmo"
        first_row["updated_at"] = datetime(2026, 3, 12, 5, 5, tzinfo=timezone.utc)
        self._entries[first_id] = first_row

        second_id = uuid4()
        self._entries[second_id] = self._build_entry(
            entry_id=second_id,
            source_run_id=parent_run_id,
            source_tracker_run_id=tracker_run_id,
            entry_key="r25bk00555368|000|smart-building",
            row_no=13,
            source_bid_no="R25BK00555368",
            source_bid_ord="000",
            source_project_name_norm="smart-building",
            project_name="Smart Building Upgrade",
            gross_area_scale="8 floors / 8100 sqm",
            construction_cost="9700000000",
            demand_org_name="Seoul Urban Development",
            demand_contact="Planning Team Park",
            client_location="Seongnam",
            site_location_1="Seongnam Bundang-gu",
            site_location_2="Seongnam Jeongja-dong",
            architect_office="Hanul Architects",
            opening_scheduled_date="20260411",
            construction_start_date="2026-06-15",
            last_checked_date="2026-03-12",
            progress_note="Initial review",
            notice_date="2026-03-10",
            manager_name="Park Minsu",
            building_automation_estimated_amount="210000000",
            created_at=now,
        )

        self._append_audit_log(
            entry_id=first_id,
            field_name="project_name",
            old_value="Project Name Alpha",
            new_value="Project Name A",
            actor_user_id=None,
            actor_label="hyunmo",
            change_source="web",
            created_at=datetime(2026, 3, 12, 5, 3, tzinfo=timezone.utc),
        )
        self._append_audit_log(
            entry_id=first_id,
            field_name="progress_note",
            old_value="",
            new_value="Phone verification complete",
            actor_user_id=None,
            actor_label="hyunmo",
            change_source="web",
            created_at=datetime(2026, 3, 12, 5, 5, tzinfo=timezone.utc),
        )

    def _build_entry(
        self,
        *,
        entry_id: UUID,
        source_run_id: UUID,
        source_tracker_run_id: UUID,
        entry_key: str,
        row_no: int,
        source_bid_no: str,
        source_bid_ord: str,
        source_project_name_norm: str,
        project_name: str,
        gross_area_scale: str,
        construction_cost: str,
        demand_org_name: str,
        demand_contact: str,
        client_location: str,
        site_location_1: str,
        site_location_2: str,
        architect_office: str,
        construction_start_date: str,
        last_checked_date: str,
        progress_note: str,
        notice_date: str,
        manager_name: str,
        building_automation_estimated_amount: str,
        created_at: datetime,
        opening_scheduled_date: str = "",
        contract_date: str = "",
        construction_duration_days: str = "",
        completion_expected_date_explicit: str = "",
        completion_expected_date_computed: str = "",
    ) -> dict[str, object]:
        return {
            "id": entry_id,
            "organization_id": DEFAULT_PHASE1_ORGANIZATION_ID,
            "source_run_id": source_run_id,
            "source_tracker_run_id": source_tracker_run_id,
            "entry_key": entry_key,
            "sheet_name": "Sheet1",
            "section_name": "facility_cost",
            "row_no": row_no,
            "source_bid_no": source_bid_no,
            "source_bid_ord": source_bid_ord,
            "source_project_name_norm": source_project_name_norm,
            "project_name_source": project_name,
            "project_name_override": None,
            "gross_area_scale_source": gross_area_scale,
            "gross_area_scale_override": None,
            "construction_cost_source": construction_cost,
            "construction_cost_override": None,
            "demand_org_name_source": demand_org_name,
            "demand_org_name_override": None,
            "demand_contact_source": demand_contact,
            "demand_contact_override": None,
            "client_location_source": client_location,
            "client_location_override": None,
            "site_location_1_source": site_location_1,
            "site_location_1_override": None,
            "site_location_2_source": site_location_2,
            "site_location_2_override": None,
            "architect_office_source": architect_office,
            "architect_office_override": None,
            "opening_scheduled_date_source": opening_scheduled_date,
            "contract_date_source": contract_date,
            "construction_duration_days_source": construction_duration_days,
            "completion_expected_date_explicit_source": completion_expected_date_explicit,
            "completion_expected_date_computed_source": completion_expected_date_computed,
            "construction_start_date_source": construction_start_date,
            "construction_start_date_override": None,
            "last_checked_date_source": last_checked_date,
            "last_checked_date_override": None,
            "progress_note_source": progress_note,
            "progress_note_override": None,
            "notice_date_source": notice_date,
            "notice_date_override": None,
            "manager_name_source": manager_name,
            "manager_name_override": None,
            "building_automation_estimated_amount_source": building_automation_estimated_amount,
            "building_automation_estimated_amount_override": None,
            "last_edited_at": None,
            "last_edited_by": None,
            "last_edited_by_label": "",
            "created_at": created_at,
            "updated_at": created_at,
        }

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
        created_at: datetime,
    ) -> TrackerEntryAuditLogRow:
        audit_log: TrackerEntryAuditLogRow = {
            "id": self._next_audit_log_id,
            "field_name": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "actor_user_id": actor_user_id,
            "actor_label": actor_label,
            "change_source": change_source,
            "created_at": created_at,
        }
        self._next_audit_log_id += 1
        self._audit_logs_by_entry.setdefault(entry_id, []).append(audit_log)
        return audit_log

    def _find_by_entry_key(self, entry_key: str) -> dict[str, object] | None:
        for row in self._entries.values():
            if row["organization_id"] == DEFAULT_PHASE1_ORGANIZATION_ID and row["entry_key"] == entry_key:
                return row
        return None

    def _to_effective_entry(self, row: dict[str, object]) -> TrackerEntryRow:
        effective: TrackerEntryRow = {
            "id": row["id"],
            "organization_id": row["organization_id"],
            "source_run_id": row["source_run_id"],
            "source_tracker_run_id": row["source_tracker_run_id"],
            "entry_key": row["entry_key"],
            "sheet_name": row["sheet_name"],
            "section_name": row["section_name"],
            "row_no": row["row_no"],
            "source_bid_no": row["source_bid_no"],
            "source_bid_ord": row["source_bid_ord"],
            "source_project_name_norm": row["source_project_name_norm"],
            "opening_scheduled_date": row.get("opening_scheduled_date_source", ""),
            "contract_date": row.get("contract_date_source", ""),
            "construction_duration_days": row.get("construction_duration_days_source", ""),
            "completion_expected_date_explicit": row.get("completion_expected_date_explicit_source", ""),
            "completion_expected_date_computed": row.get("completion_expected_date_computed_source", ""),
            "last_edited_at": row["last_edited_at"],
            "last_edited_by": row["last_edited_by"],
            "last_edited_by_label": row["last_edited_by_label"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        overridden_fields: list[str] = []
        for field_name in TRACKER_EDITABLE_FIELDS:
            override_value = row[f"{field_name}_override"]
            effective[field_name] = (
                override_value if override_value is not None else row[f"{field_name}_source"]
            )
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

    def _matches_query(self, row: TrackerEntryRow, query: str) -> bool:
        project_name = str(row["project_name"] or "").lower()
        return bool(project_name) and query in project_name
