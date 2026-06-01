from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from .schemas_auth import AuthOrganizationUserItem
from .schemas_tracker import TrackerEntrySummaryItem


class SalesClaimRequest(BaseModel):
    source_entry_id: UUID | None = None
    source_run_id: UUID | None = None
    project_name: str = ""
    estimated_amount_text: str = ""


class SalesClaimPatchRequest(BaseModel):
    sales_note: str = ""
    force_admin_override: bool = False


class SalesClaimTransferRequest(BaseModel):
    target_user_id: UUID | None = None
    target_email: str = ""
    force: bool = False


class SalesClaimCloseRequest(BaseModel):
    outcome: str
    contract_amount_text: str = ""
    force: bool = False


class SalesClaimReleaseRequest(BaseModel):
    force: bool = False


class SalesClaimItem(BaseModel):
    organization_id: UUID
    project_id: UUID
    source_entry_id: UUID | None = None
    source_run_id: UUID | None = None
    project_name: str = ""
    owner_user_id: UUID | None = None
    owner_email: str = ""
    owner_display_name: str = ""
    claimed_at: datetime
    current_owner_assigned_at: datetime
    released_at: datetime | None = None
    is_active: bool = True
    claim_status: str = "active"
    closed_at: datetime | None = None
    closed_by: UUID | None = None
    sales_note: str = ""
    sales_note_updated_at: datetime | None = None
    sales_note_updated_by: UUID | None = None
    estimated_amount_text: str = ""
    estimated_amount_low_krw: int | None = None
    estimated_amount_high_krw: int | None = None
    created_at: datetime
    updated_at: datetime


class SalesClaimMutationResponse(BaseModel):
    changed: bool = True
    claim: SalesClaimItem


class SalesClaimListResponse(BaseModel):
    items: list[SalesClaimItem] = Field(default_factory=list)


class SalesClaimOverviewResponse(BaseModel):
    my_items: list[SalesClaimItem] = Field(default_factory=list)
    company_items: list[SalesClaimItem] = Field(default_factory=list)
    organization_users: list[AuthOrganizationUserItem] = Field(default_factory=list)


class HomeBootstrapTrackerSortContract(BaseModel):
    mode: str = "default"
    order_by: list[str] = Field(default_factory=list)


class HomeBootstrapTrackerFirstPageResponse(BaseModel):
    items: list[TrackerEntrySummaryItem] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    total: int = 0
    sort_contract: HomeBootstrapTrackerSortContract = Field(default_factory=HomeBootstrapTrackerSortContract)


class HomeBootstrapResponse(BaseModel):
    my_items: list[SalesClaimItem] = Field(default_factory=list)
    company_items: list[SalesClaimItem] = Field(default_factory=list)
    organization_users: list[AuthOrganizationUserItem] = Field(default_factory=list)
    tracker_first_page: HomeBootstrapTrackerFirstPageResponse = Field(default_factory=HomeBootstrapTrackerFirstPageResponse)
    generated_at: datetime | None = None
    snapshot_version: int = 1


class SalesClaimSummaryProjectItem(BaseModel):
    project_id: UUID
    project_name: str = ""
    estimated_amount_text: str = ""
    estimated_amount_low_krw: int | None = None
    estimated_amount_high_krw: int | None = None
    claimed_at: datetime
    current_owner_assigned_at: datetime
    elapsed_days: int = 0
    owner_elapsed_days: int = 0
    sales_note: str = ""


class SalesClaimSummaryUserItem(BaseModel):
    user_id: UUID | None = None
    user_name: str = ""
    user_email: str = ""
    active_project_count: int = 0
    total_low_krw: int = 0
    total_high_krw: int = 0
    projects: list[SalesClaimSummaryProjectItem] = Field(default_factory=list)


class SalesClaimSummaryByUserResponse(BaseModel):
    items: list[SalesClaimSummaryUserItem] = Field(default_factory=list)


class SalesActionRecommendationItem(BaseModel):
    entry_id: str = ""
    project_id: str = ""
    project_name: str = ""
    source_bid_no: str = ""
    source_bid_ord: str = ""
    automation_amount_text: str = ""
    automation_amount_low_krw: int = 0
    primary_label: str = ""
    action_labels: list[str] = Field(default_factory=list)
    latest_meaningful_notice_type: str = ""
    latest_meaningful_notice_date: str = ""
    elapsed_days: int = 0
    reasons: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    tracker_entry: dict[str, Any] = Field(default_factory=dict)
    claim_payload: dict[str, Any] = Field(default_factory=dict)
    internal_sort_score: int | None = None


class SalesActionRecommendationListResponse(BaseModel):
    items: list[SalesActionRecommendationItem] = Field(default_factory=list)
    total: int = 0
    weekly_recheck_summary: dict[str, int] = Field(default_factory=dict)


class RunCreateParams(BaseModel):
    start_date: str
    end_date: str
    contract_date_hint: str = ""
    bid_no: str = ""
    notice_title: str = ""
    demand_org: str = ""
    rows_per_page: int = 100
    max_pages: int = 3
    api_scope: str = "construction"


class RunCreateRequest(BaseModel):
    run_type: str
    params: RunCreateParams
    advanced_options: dict[str, Any] = Field(default_factory=dict)


class RunCreateResponse(BaseModel):
    id: UUID
    status: str
    run_type: str
    parent_run_id: UUID | None = None
    created_at: datetime


class RunCancelResponse(BaseModel):
    id: UUID
    status: str
    cancel_requested: bool


class RunListItem(BaseModel):
    id: UUID
    status: str
    run_type: str
    parent_run_id: UUID | None = None
    progress_stage: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RunListResponse(BaseModel):
    items: list[RunListItem]
    page: int
    page_size: int
    total: int


class DashboardSummaryResponse(BaseModel):
    run_counts: dict[str, int] = Field(default_factory=dict)
    tracker_total: int = 0
    tracker_edited_total: int = 0
    repository_backends: dict[str, str] = Field(default_factory=dict)
    artifact_metadata_persistent: bool = False
    synthetic_debug_enabled: bool = False
    recent_failed_runs: list[RunListItem] = Field(default_factory=list)
    latest_reports: dict[str, Any] = Field(default_factory=dict)
    active_report_jobs: list[dict[str, Any]] = Field(default_factory=list)


class RunDetailResponse(BaseModel):
    id: UUID
    status: str
    run_type: str
    parent_run_id: UUID | None = None
    progress_stage: str
    progress_current: int
    progress_total: int
    cancel_requested: bool
    params: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ArtifactItem(BaseModel):
    id: UUID
    artifact_type: str
    file_name: str
    mime_type: str
    size_bytes: int
    checksum: str
    meta: dict[str, Any] = Field(default_factory=dict)
    download_url: str
    download_url_expires_in: int
    created_at: datetime


class ArtifactListResponse(BaseModel):
    items: list[ArtifactItem]


class RunLogItem(BaseModel):
    id: int
    level: str
    stage: str
    message: str
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class RunLogListResponse(BaseModel):
    items: list[RunLogItem]
    next_cursor: int | None = None


class ReportJobCreateRequest(BaseModel):
    report_name: str
    gui_source_root: str = ""
    seed_csv: str = ""
    seed_limit: int = 3
    start_date: str = "20250101"
    end_date: str = "20250228"
    contract_date_hint: str = ""
    bid_no: str = ""
    notice_title: str = ""
    demand_org: str = ""
    rows_per_page: int = 30
    max_pages: int = 1
    api_scope: str = "construction"


class ReportJobItem(BaseModel):
    id: UUID
    report_name: str
    status: str
    output_path: str
    command: list[str] = Field(default_factory=list)
    seed_limit: int = 0
    seed_csv: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    log_excerpt: str = ""
    error: str = ""


class ReportJobListResponse(BaseModel):
    items: list[ReportJobItem]


class RunPresetCreateRequest(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class RunPresetItem(BaseModel):
    id: UUID
    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class RunPresetListResponse(BaseModel):
    items: list[RunPresetItem]


class RunEventEnvelope(BaseModel):
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ProjectItem(BaseModel):
    id: UUID
    project_name: str
    project_name_norm: str
    project_search_name: str = ""
    issuer_name: str = ""
    latest_notice_date: str = ""
    latest_notice_title: str = ""
    source_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectItem]
    page: int
    page_size: int
    total: int


class NoticeViewDocumentItem(BaseModel):
    source_label: str = ""
    url: str = ""
    title: str = ""
    text: str = ""
    is_primary: bool = False


class NoticeViewResponse(BaseModel):
    project_name: str = ""
    bid_no: str = ""
    bid_ord: str = ""
    requested_urls: list[str] = Field(default_factory=list)
    document_count: int = 0
    title: str = ""
    used_url: str = ""
    text: str = ""
    documents: list[NoticeViewDocumentItem] = Field(default_factory=list)


class RelatedNoticeItem(BaseModel):
    id: str
    project_name: str
    project_search_name: str = ""
    issuer_name: str = ""
    announce_date: str = ""
    bid_no: str = ""
    bid_ord: str = ""
    g2b_verified: str = ""
    notice_url: str = ""
    notice_detail_url: str = ""
    match_score: int = 0
    match_reason: str = ""
    notice_stage: str = ""
    sales_relevance: str = ""
    exclusion_reason: str = ""
    relatedness_score: int = 0
    sales_relevance_score: int = 0
    reason_codes: list[str] = Field(default_factory=list)


class RelatedNoticeListResponse(BaseModel):
    project_id: UUID
    project_name: str
    project_search_name: str = ""
    status: str = "ready"
    source: str = "precomputed"
    message: str = ""
    precomputed: bool = False
    items: list[RelatedNoticeItem]
    groups: dict[str, list[RelatedNoticeItem]] = Field(default_factory=dict)
    stats: dict[str, int] = Field(default_factory=dict)


class RelatedNoticeRecomputeResponse(BaseModel):
    project_id: UUID
    project_name: str = ""
    project_search_name: str = ""
    project_key: str = ""
    run_id: str = ""
    status: str = "queued"
    queued: bool = False
    message: str = ""


class RelatedNoticeProgressResponse(BaseModel):
    project_id: UUID
    project_name: str = ""
    project_search_name: str = ""
    project_key: str = ""
    run_id: str = ""
    status: str = "idle"
    message: str = ""
    item_count: int = 0
    started_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    items: list[RelatedNoticeItem] = Field(default_factory=list)


__all__ = [
    "ArtifactItem",
    "ArtifactListResponse",
    "DashboardSummaryResponse",
    "HomeBootstrapResponse",
    "HomeBootstrapTrackerFirstPageResponse",
    "HomeBootstrapTrackerSortContract",
    "NoticeViewDocumentItem",
    "NoticeViewResponse",
    "ProjectItem",
    "ProjectListResponse",
    "RelatedNoticeItem",
    "RelatedNoticeListResponse",
    "RelatedNoticeProgressResponse",
    "RelatedNoticeRecomputeResponse",
    "ReportJobCreateRequest",
    "ReportJobItem",
    "ReportJobListResponse",
    "RunCancelResponse",
    "RunCreateParams",
    "RunCreateRequest",
    "RunCreateResponse",
    "RunDetailResponse",
    "RunEventEnvelope",
    "RunListItem",
    "RunListResponse",
    "RunLogItem",
    "RunLogListResponse",
    "RunPresetCreateRequest",
    "RunPresetItem",
    "RunPresetListResponse",
    "SalesClaimCloseRequest",
    "SalesActionRecommendationItem",
    "SalesActionRecommendationListResponse",
    "SalesClaimItem",
    "SalesClaimListResponse",
    "SalesClaimMutationResponse",
    "SalesClaimOverviewResponse",
    "SalesClaimPatchRequest",
    "SalesClaimReleaseRequest",
    "SalesClaimRequest",
    "SalesClaimSummaryByUserResponse",
    "SalesClaimSummaryProjectItem",
    "SalesClaimSummaryUserItem",
    "SalesClaimTransferRequest",
]
