from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MessageResponse(BaseModel):
    message: str


class AuthCredentialRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    invite_token: str = ""


class AuthPasswordResetRequest(BaseModel):
    email: str


class AuthAdminAccountCreateRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    role: str = "org_member"


class AuthAdminAccountPasswordResetRequest(BaseModel):
    password: str


class AuthAdminAccountItem(BaseModel):
    id: UUID
    email: str
    display_name: str = ""
    role: str = ""
    account_status: str = "active"
    membership_status: str = "active"
    password_setup_mode: str = "admin_set"
    force_password_change: bool = False
    platform_admin_managed: bool = True


class AuthAdminAccountPasswordResetResponse(BaseModel):
    message: str


class AuthUserItem(BaseModel):
    auth_user_id: UUID
    local_user_id: UUID | None = None
    membership_id: UUID | None = None
    email: str
    display_name: str = ""
    role: str = ""
    status: str = "active"
    account_status: str = "active"
    membership_status: str = "active"
    organization_id: UUID | None = None
    organization_name: str = ""
    mobile_phone: str = ""
    office_phone: str = ""


class AuthSessionResponse(BaseModel):
    enabled: bool = False
    authenticated: bool = False
    authorized: bool = False
    access_token: str = ""
    bootstrap_email: str = ""
    public_auth_url: str = ""
    public_api_key: str = ""
    public_auth_configured: bool = False
    message: str = ""
    user: AuthUserItem | None = None


class AuthOrganizationUserItem(BaseModel):
    id: UUID
    membership_id: UUID | None = None
    organization_id: UUID
    email: str
    display_name: str = ""
    role: str = ""
    status: str = "active"
    account_status: str = "active"
    membership_status: str = "active"
    organization_name: str = ""
    team_name: str = ""
    job_title: str = ""
    mobile_phone: str = ""
    office_phone: str = ""


class AuthOrganizationUserListResponse(BaseModel):
    items: list[AuthOrganizationUserItem] = Field(default_factory=list)


class AuthOrganizationUserStatusUpdateRequest(BaseModel):
    status: str


class AuthProfileUpdateRequest(BaseModel):
    display_name: str
    mobile_phone: str = ""
    office_phone: str = ""
    current_password: str = ""
    password: str = ""
    invite_token: str = ""


class AuthOrganizationUserUpdateRequest(BaseModel):
    role: str = ""
    membership_status: str = ""
    team_name: str = ""
    job_title: str = ""


class AuthInvitationCreateRequest(BaseModel):
    email: str
    role: str = "org_member"
    display_name: str = ""
    team_name: str = ""
    job_title: str = ""
    expires_in_days: int = 7


class AuthInvitationAcceptRequest(BaseModel):
    invite_token: str


class AuthSessionImportRequest(BaseModel):
    access_token: str
    refresh_token: str = ""


class AuthInvitationItem(BaseModel):
    id: UUID
    organization_id: UUID
    email: str
    role: str = "org_member"
    display_name: str = ""
    team_name: str = ""
    job_title: str = ""
    invite_token: str
    invite_url: str = ""
    status: str = "pending"
    expires_at: datetime
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    accepted_user_id: UUID | None = None
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    delivery_status: str = ""
    delivery_message: str = ""
    initial_password: str = ""


class AuthOrganizationPlanSummary(BaseModel):
    organization_id: UUID | None = None
    organization_name: str = ""
    plan_code: str = "A"
    plan_label: str = ""
    active_user_limit: int = 5
    pending_invite_limit: int = 5
    active_user_count: int = 0
    pending_invite_count: int = 0
    remaining_active_user_slots: int = 0
    remaining_pending_invite_slots: int = 0
    active_user_limit_reached: bool = False
    pending_invite_limit_reached: bool = False
    upgrade_required: bool = False
    upgrade_message: str = ""
    next_plan_code: str = ""


class AuthInvitationListResponse(BaseModel):
    items: list[AuthInvitationItem] = Field(default_factory=list)
    plan_summary: AuthOrganizationPlanSummary | None = None


class AuthAuditLogItem(BaseModel):
    id: int
    organization_id: UUID | None = None
    actor_user_id: UUID | None = None
    actor_membership_id: UUID | None = None
    actor_email: str = ""
    actor_display_name: str = ""
    actor_role: str = ""
    event_type: str
    target_type: str = ""
    target_id: str = ""
    payload_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AuthAuditLogListResponse(BaseModel):
    items: list[AuthAuditLogItem] = Field(default_factory=list)


class AuthAuditLogSliceResponse(BaseModel):
    items: list[AuthAuditLogItem] = Field(default_factory=list)
    has_more: bool = False


class DownloadAuditLogItem(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    user_email: str = ""
    user_role: str = ""
    download_scope: str
    download_format: str
    source_page: str
    file_name: str = ""
    created_at: datetime


class DownloadAuditLogListResponse(BaseModel):
    items: list[DownloadAuditLogItem] = Field(default_factory=list)


class DownloadAuditLogSliceResponse(BaseModel):
    items: list[DownloadAuditLogItem] = Field(default_factory=list)
    has_more: bool = False


class LoginAuditLogItem(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    user_email: str = ""
    user_role: str = ""
    ip_address: str = ""
    user_agent: str = ""
    created_at: datetime


class LoginAuditLogListResponse(BaseModel):
    items: list[LoginAuditLogItem] = Field(default_factory=list)


class LoginAuditLogSliceResponse(BaseModel):
    items: list[LoginAuditLogItem] = Field(default_factory=list)
    has_more: bool = False


class OrganizationAdminBootstrapResponse(BaseModel):
    members: list[AuthOrganizationUserItem] = Field(default_factory=list)
    plan_summary: AuthOrganizationPlanSummary | None = None
    invitations: list[AuthInvitationItem] = Field(default_factory=list)
    auth_audit_logs: AuthAuditLogSliceResponse = Field(default_factory=AuthAuditLogSliceResponse)
    download_audit_logs: DownloadAuditLogSliceResponse = Field(default_factory=DownloadAuditLogSliceResponse)
    login_audit_logs: LoginAuditLogSliceResponse = Field(default_factory=LoginAuditLogSliceResponse)
    generated_at: datetime


class AuthInvitationPreviewResponse(BaseModel):
    organization_id: UUID | None = None
    organization_name: str = ""
    email: str
    role: str = "org_member"
    display_name: str = ""
    team_name: str = ""
    job_title: str = ""
    status: str = "pending"
    expires_at: datetime | None = None
    accepted_at: datetime | None = None
    initial_password: str = ""


__all__ = [
    "AuthAdminAccountCreateRequest",
    "AuthAdminAccountItem",
    "AuthAdminAccountPasswordResetRequest",
    "AuthAdminAccountPasswordResetResponse",
    "AuthAuditLogItem",
    "AuthAuditLogListResponse",
    "AuthAuditLogSliceResponse",
    "AuthCredentialRequest",
    "AuthInvitationAcceptRequest",
    "AuthInvitationCreateRequest",
    "AuthInvitationItem",
    "AuthInvitationListResponse",
    "AuthInvitationPreviewResponse",
    "AuthOrganizationPlanSummary",
    "AuthOrganizationUserItem",
    "AuthOrganizationUserListResponse",
    "AuthOrganizationUserStatusUpdateRequest",
    "AuthOrganizationUserUpdateRequest",
    "AuthPasswordResetRequest",
    "AuthProfileUpdateRequest",
    "AuthSessionImportRequest",
    "AuthSessionResponse",
    "AuthUserItem",
    "DownloadAuditLogItem",
    "DownloadAuditLogListResponse",
    "DownloadAuditLogSliceResponse",
    "ErrorDetail",
    "ErrorResponse",
    "LoginAuditLogItem",
    "LoginAuditLogListResponse",
    "LoginAuditLogSliceResponse",
    "MessageResponse",
    "OrganizationAdminBootstrapResponse",
]
