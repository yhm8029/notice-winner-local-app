from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class TrackerCleanupPreviewResponse(BaseModel):
    source_tracker_run_id: UUID
    parent_run_id: UUID | None = None
    tracker_entry_count: int = 0
    child_run_count: int = 0
    parent_run_count: int = 0
    log_count: int = 0
    artifact_count: int = 0


class TrackerCleanupApplyRequest(BaseModel):
    source_tracker_run_id: UUID


class TrackerCleanupApplyResponse(BaseModel):
    source_tracker_run_id: UUID
    parent_run_id: UUID | None = None
    deleted_tracker_entry_count: int = 0
    deleted_run_count: int = 0
    deleted_log_count: int = 0
    deleted_artifact_count: int = 0


class TrackerDownloadJobCreateRequest(BaseModel):
    format: str = "xlsx"
    q: str = ""
    region: str = ""
    notice_year: str = ""
    exclude_auxiliary_titles: bool = False
    edited_only: bool = False
    blank_progress_note: bool = False
    source_run_id: UUID | None = None
    source_tracker_run_id: UUID | None = None
    sheet_name: str = ""
    section_name: str = ""


class TrackerDownloadJobItem(BaseModel):
    id: UUID
    status: str
    format: str = "xlsx"
    file_name: str = ""
    download_url: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str = ""
    reused_existing: bool = False
    summary: dict[str, object] = Field(default_factory=dict)


class TrackerTemplateStatusResponse(BaseModel):
    source: str
    source_label: str = ""
    file_name: str = ""
    original_file_name: str = ""
    active_path: str = ""
    size_bytes: int = 0
    updated_at: str = ""


class TrackerEntryFieldDiagnosticItem(BaseModel):
    field_key: str
    field_label: str
    current_value: str = ""
    source_key: str = ""
    source_label: str = ""
    source_type: str = ""
    source_type_label: str = ""
    reason_code: str = ""
    source_reason: str = ""
    evidence_preview: str = ""
    confidence: str = ""
    missing_reason_code: str = ""
    missing_reason: str = ""
    is_missing: bool = False
    is_overridden: bool = False


class TrackerEntryItem(BaseModel):
    id: UUID
    source_run_id: UUID | None = None
    source_tracker_run_id: UUID | None = None
    project_id: UUID | None = None
    project_search_name: str = ""
    entry_key: str
    sheet_name: str
    section_name: str
    row_no: int
    source_bid_no: str
    source_bid_ord: str
    source_project_name_norm: str
    project_name: str
    gross_area_scale: str
    construction_cost: str
    demand_org_name: str
    demand_contact: str
    client_location: str
    site_location_1: str
    site_location_2: str
    architect_office: str
    opening_scheduled_date: str = ""
    construction_start_date: str
    contract_date: str = ""
    construction_duration_days: str = ""
    completion_expected_date_explicit: str = ""
    completion_expected_date_computed: str = ""
    last_checked_date: str
    progress_note: str
    notice_date: str
    manager_name: str
    building_automation_estimated_amount: str
    gross_area_scale_source: str = ""
    demand_contact_source: str = ""
    architect_office_source: str = ""
    source_type: str = ""
    reason_code: str = ""
    evidence_source: str = ""
    field_diagnostics: list[TrackerEntryFieldDiagnosticItem] = Field(default_factory=list)
    overridden_fields: list[str] = Field(default_factory=list)
    last_edited_at: datetime | None = None
    last_edited_by: UUID | None = None
    last_edited_by_label: str = ""
    created_at: datetime
    updated_at: datetime


class TrackerEntrySummaryItem(BaseModel):
    id: UUID
    source_run_id: UUID | None = None
    source_tracker_run_id: UUID | None = None
    project_id: UUID | None = None
    source_bid_no: str = ""
    source_bid_ord: str = ""
    entry_key: str
    row_no: int
    project_name: str
    gross_area_scale: str
    construction_cost: str
    demand_org_name: str
    demand_contact: str
    client_location: str
    site_location_1: str
    site_location_2: str = ""
    architect_office: str
    opening_scheduled_date: str = ""
    construction_start_date: str
    contract_date: str = ""
    construction_duration_days: str = ""
    completion_expected_date_explicit: str = ""
    completion_expected_date_computed: str = ""
    last_checked_date: str
    progress_note: str
    building_automation_estimated_amount: str
    overridden_fields: list[str] = Field(default_factory=list)


class TrackerEntryListResponse(BaseModel):
    items: list[TrackerEntryItem]
    page: int
    page_size: int
    total: int


class TrackerEntrySummaryListResponse(BaseModel):
    items: list[TrackerEntrySummaryItem]
    page: int
    page_size: int
    total: int


class TrackerMissingFieldItem(BaseModel):
    field_key: str
    field_label: str
    source_reason: str = ""
    reason_group: str = ""
    reason_explainer: str = ""


class TrackerMissingReportItem(BaseModel):
    entry_id: UUID
    source_run_id: UUID | None = None
    source_tracker_run_id: UUID | None = None
    project_name: str
    bid_no: str = ""
    bid_ord: str = ""
    demand_org_name: str = ""
    missing_fields: list[TrackerMissingFieldItem] = Field(default_factory=list)
    updated_at: datetime | None = None


class TrackerMissingReportSummary(BaseModel):
    total_entries: int = 0
    missing_entries: int = 0
    contact_missing: int = 0
    architect_missing: int = 0
    area_missing: int = 0


class TrackerMissingReportResponse(BaseModel):
    summary: TrackerMissingReportSummary
    items: list[TrackerMissingReportItem] = Field(default_factory=list)


class TrackerContactResolutionStatusCount(BaseModel):
    status: str
    count: int = 0


class TrackerContactResolutionReasonCount(BaseModel):
    reason: str
    count: int = 0


class TrackerContactResolutionItem(BaseModel):
    entry_id: UUID
    source_run_id: UUID | None = None
    source_tracker_run_id: UUID | None = None
    project_name: str = ""
    demand_org_name: str = ""
    demand_contact: str = ""
    resolution_status: str = ""
    resolution_reason: str = ""
    resolution_phase: str = ""
    resolution_role: str = ""
    resolution_owner_side: str = ""
    resolution_owner_side_basis: str = ""
    updated_at: datetime | None = None


class TrackerContactResolutionSummaryResponse(BaseModel):
    total_entries: int = 0
    status_counts: list[TrackerContactResolutionStatusCount] = Field(default_factory=list)
    reason_counts: list[TrackerContactResolutionReasonCount] = Field(default_factory=list)
    items: list[TrackerContactResolutionItem] = Field(default_factory=list)


class TrackerEntryPatchRequest(BaseModel):
    field_name: str
    value: str | None = None
    actor_user_id: UUID | None = None
    actor_label: str = ""
    change_source: str = "web"


class TrackerEntryAuditLogItem(BaseModel):
    id: int
    field_name: str
    old_value: str
    new_value: str
    actor_user_id: UUID | None = None
    actor_label: str = ""
    change_source: str
    created_at: datetime


class TrackerEntryPatchResponse(BaseModel):
    changed: bool
    entry: TrackerEntryItem
    audit_log: TrackerEntryAuditLogItem | None = None


class TrackerEntryAuditLogListResponse(BaseModel):
    items: list[TrackerEntryAuditLogItem]
    next_cursor: int | None = None


class TrackerChangeEventItem(BaseModel):
    id: UUID
    tracker_entry_id: UUID
    project_id: UUID | None = None
    project_name: str = ""
    entry_key: str = ""
    event_type: str
    field_name: str | None = None
    old_value: str = ""
    new_value: str = ""
    old_value_norm: str | None = None
    new_value_norm: str | None = None
    source_run_id: UUID | None = None
    source_kind: str
    source_ref: str = ""
    extractor_version: str = ""
    reason_code: str = ""
    batch_key: str = ""
    is_silent: bool = False
    created_at: datetime
    is_read: bool = False
    read_at: datetime | None = None


class TrackerChangeEventListResponse(BaseModel):
    items: list[TrackerChangeEventItem] = Field(default_factory=list)
    total: int = 0


class TrackerChangeEventUnreadCountResponse(BaseModel):
    unread_count: int = 0


class TrackerChangeEventMarkReadRequest(BaseModel):
    event_ids: list[UUID] = Field(default_factory=list)
    tracker_entry_id: UUID | None = None


class TrackerChangeEventMarkReadResponse(BaseModel):
    updated_count: int = 0


class BackfillConflictItem(BaseModel):
    id: UUID
    tracker_entry_id: UUID
    project_id: UUID | None = None
    project_name: str = ""
    entry_key: str = ""
    field_name: str
    current_value: str = ""
    candidate_value: str = ""
    current_value_norm: str | None = None
    candidate_value_norm: str | None = None
    reason_code: str = ""
    source_kind: str = ""
    source_ref: str = ""
    source_run_id: UUID | None = None
    extractor_version: str = ""
    detected_at: datetime
    resolved_at: datetime | None = None
    resolution: str | None = None
    conflict_key: str = ""


class BackfillConflictListResponse(BaseModel):
    items: list[BackfillConflictItem] = Field(default_factory=list)
    total: int = 0


class BackfillConflictResolveRequest(BaseModel):
    resolution: str


class BackfillConflictResolveResponse(BaseModel):
    item: BackfillConflictItem


__all__ = [
    "BackfillConflictItem",
    "BackfillConflictListResponse",
    "BackfillConflictResolveRequest",
    "BackfillConflictResolveResponse",
    "TrackerChangeEventItem",
    "TrackerChangeEventListResponse",
    "TrackerChangeEventMarkReadRequest",
    "TrackerChangeEventMarkReadResponse",
    "TrackerChangeEventUnreadCountResponse",
    "TrackerCleanupApplyRequest",
    "TrackerCleanupApplyResponse",
    "TrackerCleanupPreviewResponse",
    "TrackerContactResolutionItem",
    "TrackerContactResolutionReasonCount",
    "TrackerContactResolutionStatusCount",
    "TrackerContactResolutionSummaryResponse",
    "TrackerDownloadJobCreateRequest",
    "TrackerDownloadJobItem",
    "TrackerEntryAuditLogItem",
    "TrackerEntryAuditLogListResponse",
    "TrackerEntryFieldDiagnosticItem",
    "TrackerEntryItem",
    "TrackerEntryListResponse",
    "TrackerEntryPatchRequest",
    "TrackerEntryPatchResponse",
    "TrackerEntrySummaryItem",
    "TrackerEntrySummaryListResponse",
    "TrackerMissingFieldItem",
    "TrackerMissingReportItem",
    "TrackerMissingReportResponse",
    "TrackerMissingReportSummary",
    "TrackerTemplateStatusResponse",
]
