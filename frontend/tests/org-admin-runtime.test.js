const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSOrgAdminRuntime;
}

function formatInvitationStatusLabel(value) {
  return {
    pending: "대기 중",
    accepted: "수락 완료",
    expired: "만료",
    revoked: "철회",
    sent: "발송 시작",
    queued: "발송 대기",
    failed: "발송 실패",
    manual: "수동 전달",
  }[value] || String(value);
}

test("buildInvitationListMarkup renders hidden-pending hint and revoke button", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildInvitationListMarkup(
    {
      planSummary: { pending_invite_count: 2 },
      invitations: [
        {
          id: "invite-1",
          display_name: "홍길동",
          email: "hong@example.com",
          role: "org_member",
          status: "pending",
          team_name: "영업",
          job_title: "담당자",
          expires_at: "2026-03-29T00:00:00Z",
          invite_url: "https://example.com/invite/1",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatDate: (value) => String(value),
      formatInvitationStatusLabel,
    },
  );

  assert.match(html, /일부 pending 초대는 현재 권한으로 관리할 수 없습니다\./);
  assert.match(html, /data-invite-revoke="invite-1"/);
});

test("buildInvitationResultMarkup renders manual fallback details after invite creation", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildInvitationResultMarkup(
    {
      id: "invite-failed",
      display_name: "Fallback User",
      email: "fallback@example.com",
      role: "org_member",
      delivery_status: "failed",
      delivery_message: "메일 발송에 실패했습니다. 링크와 초기 암호를 직접 전달하세요.",
      invite_url: "https://example.com/invite/fallback",
      initial_password: "TempPass123!",
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatInvitationStatusLabel,
    },
  );

  assert.match(html, /Fallback User/);
  assert.match(html, /fallback@example.com/);
  assert.match(html, /status-failed/);
  assert.match(html, />발송 실패</);
  assert.match(html, /메일 발송에 실패했습니다\. 링크와 초기 암호를 직접 전달하세요\./);
  assert.match(html, /초대 링크 https:\/\/example\.com\/invite\/fallback/);
  assert.match(html, /TempPass123!/);
  assert.match(html, /data-invite-copy="https:\/\/example\.com\/invite\/fallback"/);
});

test("buildInvitationResultMarkup localizes the manual delivery fallback state", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildInvitationResultMarkup(
    {
      id: "invite-manual",
      display_name: "Manual User",
      email: "manual@example.com",
      role: "org_member",
      delivery_status: "manual",
      invite_url: "https://example.com/invite/manual",
      initial_password: "Manual123!",
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatInvitationStatusLabel,
    },
  );

  assert.match(html, /Manual User/);
  assert.match(html, /status-manual/);
  assert.match(html, />수동 전달</);
  assert.match(html, /초대 링크 https:\/\/example\.com\/invite\/manual/);
  assert.match(html, /Manual123!/);
});

test("buildInvitationResultMarkup keeps copy fallback even when delivery starts automatically", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildInvitationResultMarkup(
    {
      id: "invite-sent",
      display_name: "Sent User",
      email: "sent@example.com",
      role: "org_admin",
      delivery_status: "sent",
      delivery_message: "초대 메일 발송을 시작했습니다.",
      invite_url: "https://example.com/invite/sent",
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatInvitationStatusLabel,
    },
  );

  assert.match(html, /Sent User/);
  assert.match(html, /status-sent/);
  assert.match(html, />발송 시작</);
  assert.match(html, /초대 메일 발송을 시작했습니다\./);
  assert.match(html, /초대 링크 https:\/\/example\.com\/invite\/sent/);
  assert.match(html, /data-invite-copy="https:\/\/example\.com\/invite\/sent"/);
});

test("buildOrganizationMemberSummaryMarkup renders account and membership counts", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrganizationMemberSummaryMarkup(
    {
      members: [
        { id: "1", account_status: "active", membership_status: "active" },
        { id: "2", account_status: "inactive", membership_status: "deactivated" },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      resolveStatusClass: (value) => String(value),
      formatAccountStatusLabel: (value) => String(value),
      formatMembershipStatusLabel: (value) => String(value),
    },
  );

  assert.match(html, /총 2명/);
  assert.match(html, /계정 active 1명/);
  assert.match(html, /소속 deactivated 1명/);
});

test("buildOrganizationMemberListMarkup locks protected and self members", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrganizationMemberListMarkup(
    {
      members: [
        {
          id: "protected",
          display_name: "보호 계정",
          email: "protected@example.com",
          global_role: "platform_admin",
          account_status: "active",
          membership_status: "active",
          role: "org_admin",
          organization_name: "회사",
          mobile_phone: "010-0000-0000",
          office_phone: "02-0000-0000",
        },
        {
          id: "self",
          display_name: "나",
          email: "me@example.com",
          account_status: "active",
          membership_status: "active",
          role: "org_member",
          organization_name: "회사",
          mobile_phone: "010-1111-1111",
          office_phone: "02-1111-1111",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      resolveStatusClass: (value) => String(value),
      formatAccountStatusLabel: (value) => String(value),
      formatMembershipStatusLabel: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      getRenderableOrgRoleOptions: (value) => [value, "org_admin", "org_member"],
      isProtectedOrganizationMember: (member) => member.id === "protected",
      getCurrentAuthLocalUserId: () => "self",
    },
  );

  assert.match(html, /data-member-id="protected"/);
  assert.match(html, /data-member-id="self"/);
  assert.match(html, /disabled/);
  assert.doesNotMatch(html, /data-member-delete="protected"/);
  assert.doesNotMatch(html, /data-member-delete="self"/);
});

test("buildOrganizationMemberListMarkup exposes the member-field selector contract", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrganizationMemberListMarkup(
    {
      members: [
        {
          id: "member-1",
          display_name: "Member",
          email: "member@example.com",
          account_status: "active",
          membership_status: "active",
          role: "org_member",
          organization_name: "Company",
          mobile_phone: "010-2222-2222",
          office_phone: "02-2222-2222",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      resolveStatusClass: (value) => String(value),
      formatAccountStatusLabel: (value) => String(value),
      formatMembershipStatusLabel: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      getRenderableOrgRoleOptions: (value) => [value, "org_admin", "org_member"],
      membershipStatusOptions: ["active", "paused"],
      isProtectedOrganizationMember: () => false,
      getCurrentAuthLocalUserId: () => "",
    },
  );

  assert.match(html, /data-member-field="role"/);
  assert.match(html, /data-member-field="membership_status"/);
  assert.match(html, /data-member-field="team_name"/);
  assert.match(html, /data-member-field="job_title"/);
  assert.match(html, /value="paused"/);
  assert.doesNotMatch(html, /value="inactive"/);
});

test("buildOrganizationAuditLogMarkup renders event, actor, and target text", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrganizationAuditLogMarkup(
    {
      auditLogs: [
        {
          event_type: "invite_created",
          actor_display_name: "Admin",
          actor_email: "admin@example.com",
          actor_role: "org_admin",
          target_type: "invitation",
          target_id: "invite-9",
          created_at: "2026-03-29T00:00:00Z",
          payload_json: { email: "invitee@example.com", role: "org_member" },
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => String(value),
      formatAuthAuditEventLabel: (value) => {
        if (value === "invite_created") return "Invite Created";
        return String(value);
      },
      formatAuthAuditActorLabel: () => "Admin · admin@example.com · org_admin",
      formatAuthAuditSummary: () => "invitee@example.com · org_member",
    },
  );

  assert.match(html, /Invite Created/);
  assert.match(html, /Admin · admin@example.com · org_admin/);
  assert.match(html, /대상 invitation · invite-9/);
});

test("formatAuthAuditSummary is available from the runtime and matches audit row semantics", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");

  assert.equal(
    runtime.formatAuthAuditSummary(
      {
        event_type: "invite_created",
        payload_json: {
          email: "invitee@example.com",
          role: "org_member",
        },
      },
      {
        formatOrgRoleLabel: (value) => `ROLE:${value}`,
      },
    ),
    "invitee@example.com · ROLE:org_member",
  );
  assert.equal(
    runtime.formatAuthAuditSummary(
      {
        target_type: "invitation",
        target_id: "invite-9",
      },
      {},
    ),
    "invitation · invite-9",
  );
});

test("buildDownloadAuditPanelMarkup stays hidden outside admin mode", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildDownloadAuditPanelMarkup(
    {
      isAdminMode: false,
      downloadAuditLogs: [
        {
          created_at: "2026-03-31T10:20:30Z",
          user_email: "admin@example.com",
          user_role: "org_admin",
          download_scope: "company",
          download_format: "xlsx",
          source_page: "company_active_sales",
          file_name: "company_active_sales.xlsx",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatDownloadScopeLabel: (value) => String(value),
      formatDownloadFormatLabel: (value) => String(value),
      formatDownloadSourcePageLabel: (value) => String(value),
    },
  );

  assert.equal(html, "");
  assert.doesNotMatch(html, /다운로드 이력/);
});

test("buildDownloadAuditPanelMarkup renders loading state in admin mode", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildDownloadAuditPanelMarkup(
    {
      isAdminMode: true,
      loading: true,
      downloadAuditLogs: [],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatDownloadScopeLabel: (value) => String(value),
      formatDownloadFormatLabel: (value) => String(value),
      formatDownloadSourcePageLabel: (value) => String(value),
    },
  );

  assert.match(html, /다운로드 이력/);
  assert.match(html, /다운로드 이력을 불러오는 중입니다\./);
});

test("buildDownloadAuditPanelMarkup renders error and empty states", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const errorHtml = runtime.buildDownloadAuditPanelMarkup(
    {
      isAdminMode: true,
      errorMessage: "다운로드 이력을 불러오지 못했습니다.",
      downloadAuditLogs: [],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatDownloadScopeLabel: (value) => String(value),
      formatDownloadFormatLabel: (value) => String(value),
      formatDownloadSourcePageLabel: (value) => String(value),
    },
  );
  const emptyHtml = runtime.buildDownloadAuditPanelMarkup(
    {
      isAdminMode: true,
      downloadAuditLogs: [],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
      formatDownloadScopeLabel: (value) => String(value),
      formatDownloadFormatLabel: (value) => String(value),
      formatDownloadSourcePageLabel: (value) => String(value),
    },
  );

  assert.match(errorHtml, /다운로드 이력을 불러오지 못했습니다\./);
  assert.match(emptyHtml, /최근 다운로드 이력이 없습니다\./);
});

test("buildDownloadAuditPanelMarkup renders time user scope format source page and file name", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildDownloadAuditPanelMarkup(
    {
      isAdminMode: true,
      downloadAuditLogs: [
        {
          created_at: "2026-03-31T10:20:30Z",
          user_email: "admin@example.com",
          user_role: "org_admin",
          download_scope: "company",
          download_format: "xlsx",
          source_page: "company_active_sales",
          file_name: "company_active_sales.xlsx",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => `DATE:${value}`,
      formatOrgRoleLabel: (value) => `ROLE:${value}`,
      formatDownloadScopeLabel: (value) => `SCOPE:${value}`,
      formatDownloadFormatLabel: (value) => `FORMAT:${value}`,
      formatDownloadSourcePageLabel: (value) => `PAGE:${value}`,
    },
  );

  assert.match(html, /DATE:2026-03-31T10:20:30Z/);
  assert.match(html, /admin@example.com · ROLE:org_admin/);
  assert.match(html, /SCOPE:company · FORMAT:xlsx · PAGE:company_active_sales/);
  assert.match(html, /company_active_sales\.xlsx/);
  assert.match(html, /organization-download-audit-refresh-button/);
});

test("buildLoginAuditPanelMarkup renders login history and load more controls", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildLoginAuditPanelMarkup(
    {
      isAdminMode: true,
      visibleCount: 5,
      hasMore: true,
      loginAuditLogs: [
        {
          created_at: "2026-04-01T10:20:30Z",
          user_email: "member@example.com",
          user_role: "org_member",
          ip_address: "127.0.0.1",
          user_agent: "Mozilla/5.0",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value),
      formatDate: (value) => `DATE:${value}`,
      formatLoginAuditActorLabel: (item) => `ACTOR:${item.user_email}`,
      formatLoginAuditSummary: (item) => `SUMMARY:${item.user_role}`,
    },
  );

  assert.match(html, /ACTOR:member@example.com/);
  assert.match(html, /SUMMARY:org_member/);
  assert.match(html, /IP 127\.0\.0\.1/);
  assert.match(html, /Mozilla\/5\.0/);
  assert.match(html, /organization-login-audit-refresh-button/);
  assert.match(html, /organization-login-audit-load-more-button/);
});
