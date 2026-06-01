# Main Modularization Organization Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `organization admin`의 `플랜 요약`, `초대`, `멤버 관리` 표시 계산을 [`frontend/organization-admin-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/organization-admin-runtime.js)로 더 분리하고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 상태 읽기, DOM 반영, 이벤트 실행 흐름만 담당하게 만든다.

**Architecture:** `organization admin`은 `view-model + markup` 분리로 정리한다. runtime은 플랜 요약, 초대 목록, 멤버 summary/list를 순수 helper로 계산하고, `app.js`는 `getOrganizationPlanSummaryForDisplay()`, API 호출, 감사 로그 렌더, 저장/삭제/철회 액션과 DOM 연결을 유지한다. 감사 로그는 이번 차수에서 일부러 제외한다.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser global runtime pattern (`window.SPMSOrganizationAdminRuntime`), existing frontend shell in `frontend/app.js`

---

## File Structure

- `frontend/organization-admin-runtime.js`
  - organization admin panel 생성, 상태 메시지, 액션 바인딩을 유지하면서 플랜 요약, 초대 목록, 멤버 summary/list helper를 제공한다.
- `frontend/app.js`
  - organization admin 관련 state를 읽고 runtime에 전달한다.
  - audit log 렌더와 invitation/member action 실행을 유지한다.
- `tests/frontend/test_organization_admin_runtime.mjs`
  - organization admin runtime helper를 node 환경에서 직접 검증한다.
- `tests/frontend/test_organization_admin_app_integration.mjs`
  - `renderOrganizationAdminPanel()`이 runtime helper 경로를 쓰는지 구조적으로 검증한다.

### Task 1: Add Organization Admin Runtime Tests

**Files:**
- Create: `tests/frontend/test_organization_admin_runtime.mjs`

- [ ] **Step 1: Write the failing runtime tests**

```js
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/organization-admin-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSOrganizationAdminRuntime;
}

test("buildOrganizationPlanSummaryView returns disabled submit state when upgrade is required", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildOrganizationPlanSummaryView, "function");

  const view = runtime.buildOrganizationPlanSummaryView({
    planSummary: {
      plan_label: "Starter",
      plan_code: "starter",
      active_user_count: 5,
      active_user_limit: 5,
      pending_invite_count: 2,
      pending_invite_limit: 2,
      remaining_active_user_slots: 0,
      remaining_pending_invite_slots: 0,
      upgrade_required: true,
      upgrade_message: "사용자 한도를 늘리려면 업그레이드가 필요합니다.",
    },
  }, {
    escapeHtml: (value) => String(value),
  });

  assert.match(view.html, /업그레이드 필요/);
  assert.equal(view.invitationSubmitDisabled, true);
  assert.match(view.invitationSubmitTitle, /업그레이드/);
});

test("buildOrganizationInvitationListView renders hidden pending hint", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildOrganizationInvitationListView, "function");

  const view = runtime.buildOrganizationInvitationListView({
    organizationInvitations: [
      { id: "inv-1", email: "one@example.com", status: "pending", role: "org_member" },
    ],
    planSummary: { pending_invite_count: 3 },
  }, {
    escapeHtml: (value) => String(value),
    formatOrgRoleLabel: (value) => value,
    formatInvitationStatusLabel: (value) => value,
    formatDate: (value) => String(value || ""),
  });

  assert.match(view.html, /pending 초대/);
  assert.match(view.html, /inv-1/);
});

test("buildOrganizationMemberViews sorts active members first and locks protected/self accounts", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildOrganizationMemberSummaryView, "function");
  assert.equal(typeof runtime.buildOrganizationMemberListView, "function");

  const members = [
    { id: "self-1", email: "self@example.com", display_name: "나", role: "org_admin", membership_status: "active", account_status: "active" },
    { id: "member-2", email: "inactive@example.com", display_name: "비활성", role: "org_member", membership_status: "inactive", account_status: "active" },
    { id: "member-1", email: "active@example.com", display_name: "활성", role: "org_member", membership_status: "active", account_status: "active" },
  ];

  const summaryView = runtime.buildOrganizationMemberSummaryView({ organizationMembers: members }, {
    escapeHtml: (value) => String(value),
    formatAccountStatusLabel: (value) => value,
    formatMembershipStatusLabel: (value) => value,
    resolveStatusClass: (value) => value,
  });
  assert.match(summaryView.html, /총3명/);

  const listView = runtime.buildOrganizationMemberListView({
    organizationMembers: members,
    memberSaveStateByUserId: {},
    memberDeleteStateByUserId: {},
  }, {
    escapeHtml: (value) => String(value),
    formatAccountStatusLabel: (value) => value,
    formatMembershipStatusLabel: (value) => value,
    formatOrgRoleLabel: (value) => value,
    resolveStatusClass: (value) => value,
    membershipStatusOptions: ["active", "inactive", "deactivated"],
    getRenderableOrgRoleOptions: () => ["org_member", "org_admin"],
    isProtectedOrganizationMember: (member) => member.id === "self-1",
    getCurrentAuthLocalUserId: () => "self-1",
  });

  assert.ok(listView.html.indexOf("active@example.com") < listView.html.indexOf("inactive@example.com"));
  assert.match(listView.html, /disabled/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_organization_admin_runtime.mjs`  
Expected: FAIL with messages like `runtime.buildOrganizationPlanSummaryView is not a function`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/frontend/test_organization_admin_runtime.mjs
git commit -m "test: organization admin runtime helper 기대값 추가"
```

### Task 2: Implement Organization Admin Runtime Helpers

**Files:**
- Modify: `frontend/organization-admin-runtime.js`
- Test: `tests/frontend/test_organization_admin_runtime.mjs`

- [ ] **Step 1: Add plan summary helper**

`frontend/organization-admin-runtime.js`에 플랜 요약 전용 helper를 추가한다.

```js
function buildOrganizationPlanSummaryView({ planSummary, loading = false, error = "" } = {}, helpers = {}) {
  const { escapeHtml = (value) => String(value || "") } = helpers;

  if (loading && !planSummary) {
    return {
      html: '<div class="empty-state">플랜 요약을 불러오는 중입니다.</div>',
      invitationSubmitDisabled: true,
      invitationSubmitTitle: "",
    };
  }
  if (error && !planSummary) {
    return {
      html: `<div class="empty-state">${escapeHtml(error)}</div>`,
      invitationSubmitDisabled: true,
      invitationSubmitTitle: "",
    };
  }
  if (!planSummary) {
    return {
      html: '<div class="empty-state">플랜 요약 정보를 아직 불러오지 못했습니다.</div>',
      invitationSubmitDisabled: false,
      invitationSubmitTitle: "",
    };
  }

  const inviteBlocked = Boolean(planSummary.upgrade_required);
  return {
    html: `
      <div class="org-plan-summary-card${inviteBlocked ? " is-upgrade-required" : ""}">
        <div class="org-admin-list-item-head">
          <div>
            <strong>${escapeHtml(planSummary.plan_label || `플랜 ${planSummary.plan_code || "A"}`)}</strong>
            <p class="mono">가입 ${escapeHtml(String(planSummary.active_user_count))} / ${escapeHtml(String(planSummary.active_user_limit))}명 | 대기 초대 ${escapeHtml(String(planSummary.pending_invite_count))} / ${escapeHtml(String(planSummary.pending_invite_limit))}건</p>
          </div>
          <span class="status-badge status-${escapeHtml(inviteBlocked ? "failed" : "success")}">${escapeHtml(inviteBlocked ? "업그레이드 필요" : "사용 가능")}</span>
        </div>
      </div>
    `,
    invitationSubmitDisabled: inviteBlocked,
    invitationSubmitTitle: inviteBlocked ? String(planSummary.upgrade_message || "") : "",
  };
}
```

- [ ] **Step 2: Add invitation list helper**

```js
function buildOrganizationInvitationListView(options = {}, helpers = {}) {
  const {
    organizationInvitationsLoading = false,
    organizationInvitationsError = "",
    organizationInvitations = [],
    planSummary = null,
  } = options;
  const {
    escapeHtml = (value) => String(value || ""),
    formatDate = (value) => String(value || ""),
    formatOrgRoleLabel = (value) => String(value || ""),
    formatInvitationStatusLabel = (value) => String(value || ""),
  } = helpers;

  if (organizationInvitationsLoading) {
    return { html: '<div class="empty-state">초대 목록을 불러오는 중입니다.</div>' };
  }
  if (organizationInvitationsError) {
    return { html: `<div class="empty-state">${escapeHtml(organizationInvitationsError)}</div>` };
  }
  if (!organizationInvitations.length) {
    const hasHiddenInvitations = Number(planSummary?.pending_invite_count || 0) > 0;
    return {
      html: hasHiddenInvitations
        ? '<div class="empty-state">현재 권한으로 관리할 수 없는 pending 초대가 있습니다.</div>'
        : '<div class="empty-state">아직 생성된 초대가 없습니다.</div>',
    };
  }

  const visiblePendingInviteCount = organizationInvitations.filter((item) => String(item.status || "pending") === "pending").length;
  const hasHiddenInvitations = Number(planSummary?.pending_invite_count || 0) > visiblePendingInviteCount;
  return {
    html: `
      ${hasHiddenInvitations ? '<p class="hint-text">일부 pending 초대는 현재 권한으로 관리할 수 없습니다.</p>' : ""}
      ${organizationInvitations.map((item) => `
        <article class="org-admin-list-item">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(item.display_name || item.email || "-")}</strong>
              <p class="mono">${escapeHtml(item.email || "-")} | ${escapeHtml(formatOrgRoleLabel(item.role || "org_member"))}</p>
            </div>
            <span class="status-badge status-${escapeHtml(String(item.status || "pending"))}">${escapeHtml(formatInvitationStatusLabel(item.status || "pending"))}</span>
          </div>
          <p class="mono">만료 ${escapeHtml(formatDate(item.expires_at))}</p>
          <div class="org-admin-inline-actions">
            <button class="ghost-button" type="button" data-invite-copy="${escapeHtml(item.invite_url || "")}">링크 복사</button>
            ${String(item.status || "pending") === "pending" ? `<button class="ghost-button" type="button" data-invite-revoke="${escapeHtml(item.id)}">철회</button>` : ""}
          </div>
        </article>
      `).join("")}
    `,
  };
}
```

- [ ] **Step 3: Add member summary/list helpers and compose markup**

```js
function buildOrganizationMemberSummaryView({ organizationMembers = [] } = {}, helpers = {}) {
  const {
    escapeHtml = (value) => String(value || ""),
    formatAccountStatusLabel = (value) => String(value || ""),
    formatMembershipStatusLabel = (value) => String(value || ""),
    resolveStatusClass = (value) => String(value || ""),
  } = helpers;

  if (!organizationMembers.length) {
    return { html: '<div class="empty-state">등록된 사용자가 없습니다.</div>' };
  }

  const counts = {
    account: { active: 0, inactive: 0, deactivated: 0 },
    membership: { active: 0, inactive: 0, deactivated: 0 },
  };
  organizationMembers.forEach((member) => {
    const accountStatus = String(member.account_status || "active");
    const membershipStatus = String(member.membership_status || member.status || "active");
    if (Object.prototype.hasOwnProperty.call(counts.account, accountStatus)) counts.account[accountStatus] += 1;
    if (Object.prototype.hasOwnProperty.call(counts.membership, membershipStatus)) counts.membership[membershipStatus] += 1;
  });

  return {
    html: `
      <div class="org-member-summary-card">
        <strong>현재 사용자 현황</strong>
        <div class="org-member-summary-grid">
          <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">총${escapeHtml(String(organizationMembers.length))}명</span>
          <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">계정 ${escapeHtml(formatAccountStatusLabel("active"))} ${escapeHtml(String(counts.account.active))}명</span>
          <span class="status-badge status-${escapeHtml(resolveStatusClass("inactive"))}">소속 ${escapeHtml(formatMembershipStatusLabel("inactive"))} ${escapeHtml(String(counts.membership.inactive))}명</span>
        </div>
      </div>
    `,
  };
}
```

`buildOrganizationMemberListView()`는 기존 정렬 규칙과 protected/self lock 규칙을 유지하고, 마지막에 `buildOrganizationAdminMarkup()`이 위 helper들을 조합하도록 바꾼다.

- [ ] **Step 4: Run runtime tests to verify they pass**

Run: `node --test tests/frontend/test_organization_admin_runtime.mjs`  
Expected: PASS

- [ ] **Step 5: Commit the runtime helper extraction**

```bash
git add frontend/organization-admin-runtime.js tests/frontend/test_organization_admin_runtime.mjs
git commit -m "refactor: organization admin runtime helper 추가"
```

### Task 3: Wire App Rendering To Runtime Helpers

**Files:**
- Modify: `frontend/app.js`
- Create: `tests/frontend/test_organization_admin_app_integration.mjs`
- Test: `tests/frontend/test_organization_admin_runtime.mjs`

- [ ] **Step 1: Add integration test for render path**

```js
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app.js");

test("renderOrganizationAdminPanel uses organization-admin runtime helpers", () => {
  const source = fs.readFileSync(appPath, "utf8");
  assert.match(source, /buildOrganizationAdminMarkup\(\{/);
  assert.match(source, /planSummary: nextPlanSummary/);
  assert.match(source, /dom\.organizationPlanSummary\.innerHTML = markup\.planSummaryHtml/);
  assert.match(source, /dom\.organizationMemberList\.innerHTML = markup\.memberListHtml/);
});
```

- [ ] **Step 2: Run integration test to verify it fails or proves the current gap**

Run: `node --test tests/frontend/test_organization_admin_app_integration.mjs`  
Expected: FAIL if the render path still depends on inline helper output that the spec intends to remove, or PASS once the helper wiring is complete.

- [ ] **Step 3: Trim app-side inline rendering to runtime boundaries**

`frontend/app.js`에서 `renderOrganizationAdminPanel()`을 아래 형태로 유지한다.

```js
function renderOrganizationAdminPanel() {
  if (!dom.panelOrgAdmin || !dom.organizationPlanSummary || !dom.invitationList || !dom.organizationMemberList || !dom.organizationMemberSummary || !dom.organizationAuditLogList) {
    return;
  }

  syncInvitationRoleOptions();
  const nextPlanSummary = getOrganizationPlanSummaryForDisplay();
  const markup = requireOrganizationAdminRuntime().buildOrganizationAdminMarkup({
    canUseAdminMode: canUseAdminMode(),
    uiMode: state.uiMode,
    planSummary: nextPlanSummary,
    organizationInvitationsLoading: state.organizationInvitationsLoading,
    organizationInvitationsError: state.organizationInvitationsError,
    organizationInvitations: state.organizationInvitations,
    invitationSaving: state.invitationSaving,
    organizationAuditLogsLoading: state.organizationAuditLogsLoading,
    organizationAuditLogsError: state.organizationAuditLogsError,
    organizationAuditLogs: state.organizationAuditLogs,
    organizationMembersLoading: state.organizationMembersLoading,
    organizationMembersError: state.organizationMembersError,
    organizationMembers: state.organizationMembers,
    memberSaveStateByUserId: state.memberSaveStateByUserId,
    memberDeleteStateByUserId: state.memberDeleteStateByUserId,
  }, {
    escapeHtml,
    formatDate,
    formatOrgRoleLabel,
    formatInvitationStatusLabel,
    formatAuthAuditEventLabel,
    formatAuthAuditActorLabel,
    formatAuthAuditSummary,
    formatAccountStatusLabel,
    formatMembershipStatusLabel,
    resolveStatusClass,
    getRenderableOrgRoleOptions,
    membershipStatusOptions: MEMBERSHIP_STATUS_OPTIONS,
    isProtectedOrganizationMember,
    getCurrentAuthLocalUserId,
  });

  dom.organizationPlanSummary.innerHTML = markup.planSummaryHtml;
  dom.invitationList.innerHTML = markup.invitationListHtml;
  dom.organizationAuditLogList.innerHTML = markup.auditLogHtml;
  dom.organizationMemberSummary.innerHTML = markup.memberSummaryHtml;
  dom.organizationMemberList.innerHTML = markup.memberListHtml;
}
```

이 단계에서는 감사 로그 출력은 그대로 두고, inline legacy block이 남아 있다면 주석 reference 영역을 더 줄이거나 제거한다.

- [ ] **Step 4: Run integration and syntax checks**

Run:

```bash
node --test tests/frontend/test_organization_admin_runtime.mjs
node --test tests/frontend/test_organization_admin_app_integration.mjs
node --check frontend/app.js
node --check frontend/organization-admin-runtime.js
```

Expected: all PASS

- [ ] **Step 5: Commit the app wiring**

```bash
git add frontend/app.js frontend/organization-admin-runtime.js tests/frontend/test_organization_admin_app_integration.mjs
git commit -m "refactor: organization admin runtime 경계 정리"
```

### Task 4: Run Frontend Modularization Regression Verification

**Files:**
- Verify only: `frontend/app.js`
- Verify only: `frontend/run-view-runtime.js`
- Verify only: `frontend/tracker-diagnostics-runtime.js`
- Verify only: `frontend/selected-entry-runtime.js`
- Verify only: `frontend/tracker-entry-runtime.js`
- Verify only: `frontend/organization-admin-runtime.js`

- [ ] **Step 1: Run organization admin focused tests**

Run:

```bash
node --test tests/frontend/test_organization_admin_runtime.mjs
node --test tests/frontend/test_organization_admin_app_integration.mjs
```

Expected: all PASS

- [ ] **Step 2: Run existing modularization regression tests**

Run:

```bash
node --test tests/frontend/test_run_view_runtime.mjs
node --test tests/frontend/test_tracker_diagnostics_runtime.mjs
node --test tests/frontend/test_selected_entry_runtime.mjs
node --test tests/frontend/test_selected_entry_app_integration.mjs
node --test tests/frontend/test_tracker_entry_runtime.mjs
node --test tests/frontend/test_tracker_entry_app_integration.mjs
node --test tests/frontend/test_tracker_board_runtime.mjs
node --test tests/frontend/test_tracker_board_app_integration.mjs
```

Expected: all PASS

- [ ] **Step 3: Run syntax and worktree checks**

Run:

```bash
node --check frontend/app.js
node --check frontend/run-view-runtime.js
node --check frontend/tracker-diagnostics-runtime.js
node --check frontend/selected-entry-runtime.js
node --check frontend/tracker-entry-runtime.js
node --check frontend/organization-admin-runtime.js
git status --short
```

Expected:
- all `node --check` commands exit 0
- `git status --short` shows only the expected organization admin files plus unrelated pre-existing `related notice` changes

- [ ] **Step 4: Commit the verification checkpoint**

```bash
git add tests/frontend/test_organization_admin_runtime.mjs tests/frontend/test_organization_admin_app_integration.mjs frontend/organization-admin-runtime.js frontend/app.js
git commit -m "test: organization admin 모듈화 회귀 검증"
```
