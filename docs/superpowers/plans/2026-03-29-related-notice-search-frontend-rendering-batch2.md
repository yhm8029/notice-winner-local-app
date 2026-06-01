# Related Notice Search Frontend Rendering Batch 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `frontend/app.js`에 남아 있는 조직 관리자 패널 잔여 마크업과 영업 종료 아카이브 렌더링을 기존 runtime 패턴으로 분리한다.

**Architecture:** `frontend/app.js`는 loading/error/admin gating과 이벤트 wiring을 유지하고, 순수 마크업 생성과 집계 계산은 `frontend/org-admin-runtime.js`와 `frontend/sales-view-runtime.js`로 이동한다. 새 helper는 DOM 접근 없이 collaborator를 주입받아 HTML 문자열만 반환한다.

**Tech Stack:** Vanilla JavaScript, Node built-in `node:test`, `node --check`, existing `window.SPMS*Runtime` IIFE pattern

---

## File Structure

- Modify: `frontend/org-admin-runtime.js`
- Modify: `frontend/sales-view-runtime.js`
- Modify: `frontend/app.js`
- Modify: `frontend/tests/org-admin-runtime.test.js`
- Modify: `frontend/tests/sales-view-runtime.test.js`

### Task 1: Extend Organization Admin Runtime

**Files:**
- Modify: `frontend/org-admin-runtime.js`
- Modify: `frontend/app.js:1235-1480`
- Modify: `frontend/tests/org-admin-runtime.test.js`

- [ ] **Step 1: Write the failing tests**

Add these tests to `frontend/tests/org-admin-runtime.test.js`:

```javascript
test("buildInvitationListMarkup renders hidden-pending hint and revoke button", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildInvitationListMarkup(
    {
      invitations: [
        {
          id: "invite-1",
          display_name: "홍길동",
          email: "hong@example.com",
          role: "org_member",
          status: "pending",
          team_name: "영업",
          job_title: "매니저",
          delivery_message: "메일 발송 완료",
          initial_password: "temp-1234",
          expires_at: "2026-04-05T00:00:00Z",
          invite_url: "https://example.com/invite/1",
        },
      ],
      pendingInviteCount: 2,
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      formatOrgRoleLabel: (value) => String(value ?? ""),
      formatInvitationStatusLabel: (value) => String(value ?? ""),
      formatDate: (value) => String(value ?? ""),
    },
  );
  assert.match(html, /일부 pending 초대는 현재 권한으로 관리할 수 없습니다/);
  assert.match(html, /data-invite-revoke="invite-1"/);
});

test("buildOrganizationMemberSummaryMarkup renders account and membership counts", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrganizationMemberSummaryMarkup(
    {
      members: [
        { account_status: "active", membership_status: "active" },
        { account_status: "inactive", membership_status: "inactive" },
        { account_status: "deactivated", membership_status: "deactivated" },
      ],
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      resolveStatusClass: (value) => String(value ?? ""),
      formatAccountStatusLabel: (value) => String(value ?? ""),
      formatMembershipStatusLabel: (value) => String(value ?? ""),
    },
  );
  assert.match(html, /총 3명/);
  assert.match(html, /계정 active 1명/);
  assert.match(html, /소속 inactive 1명/);
});

test("buildOrganizationMemberListMarkup locks protected and self members", () => {
  const runtime = loadRuntime("frontend/org-admin-runtime.js");
  const html = runtime.buildOrganizationMemberListMarkup(
    {
      members: [
        {
          id: "member-1",
          display_name: "플랫폼 관리자",
          email: "platform@example.com",
          role: "org_admin",
          account_status: "active",
          membership_status: "active",
          organization_name: "SPMS",
          mobile_phone: "",
          office_phone: "",
          team_name: "",
          job_title: "",
        },
      ],
      memberSaveStateByUserId: {},
      memberDeleteStateByUserId: {},
      currentAuthLocalUserId: "member-1",
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      resolveStatusClass: (value) => String(value ?? ""),
      formatAccountStatusLabel: (value) => String(value ?? ""),
      formatMembershipStatusLabel: (value) => String(value ?? ""),
      formatOrgRoleLabel: (value) => String(value ?? ""),
      getRenderableOrgRoleOptions: () => ["org_member", "org_admin"],
      membershipStatusOptions: ["active", "inactive", "deactivated"],
      isProtectedOrganizationMember: () => true,
    },
  );
  assert.match(html, /disabled/);
  assert.doesNotMatch(html, /data-member-delete="member-1"/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/org-admin-runtime.test.js`

Expected: FAIL with `TypeError` because the new runtime helpers do not exist yet

- [ ] **Step 3: Write minimal runtime implementation**

Add these helpers to `frontend/org-admin-runtime.js` and export them from `window.SPMSOrgAdminRuntime`:

```javascript
function buildInvitationListMarkup(payload = {}, helpers = {}) {
  const {
    invitations = [],
    pendingInviteCount = 0,
  } = payload;
  const {
    escapeHtml = (value) => String(value ?? ""),
    formatOrgRoleLabel = (value) => String(value ?? ""),
    formatInvitationStatusLabel = (value) => String(value ?? ""),
    formatDate = (value) => String(value ?? ""),
  } = helpers;
  const visiblePendingInviteCount = invitations.filter((item) => String(item?.status || "pending") === "pending").length;
  const hasHiddenInvitations = Number(pendingInviteCount || 0) > visiblePendingInviteCount;
  return `
    ${hasHiddenInvitations ? '<p class="hint-text">일부 pending 초대는 현재 권한으로 관리할 수 없습니다.</p>' : ""}
    ${invitations.map((item) => {
      const status = String(item?.status || "pending");
      const isPending = status === "pending";
      return `
        <article class="org-admin-list-item">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(item?.display_name || item?.email || "-")}</strong>
              <p class="mono">${escapeHtml(item?.email || "-")} | ${escapeHtml(formatOrgRoleLabel(item?.role || "org_member"))}</p>
            </div>
            <span class="status-badge status-${escapeHtml(status)}">${escapeHtml(formatInvitationStatusLabel(status))}</span>
          </div>
          <p>팀 ${escapeHtml(item?.team_name || "-")} · 직책 ${escapeHtml(item?.job_title || "-")}</p>
          ${item?.delivery_message ? `<p class="mono">${escapeHtml(item.delivery_message)}</p>` : ""}
          ${item?.initial_password ? `<p class="mono">초기 암호 ${escapeHtml(item.initial_password)}</p>` : ""}
          <p class="mono">만료 ${escapeHtml(formatDate(item?.expires_at))}</p>
          <div class="org-admin-inline-actions">
            <button class="ghost-button" type="button" data-invite-copy="${escapeHtml(item?.invite_url || "")}">링크 복사</button>
            ${isPending ? `<button class="ghost-button" type="button" data-invite-revoke="${escapeHtml(item?.id || "")}">철회</button>` : ""}
          </div>
        </article>
      `;
    }).join("")}
  `;
}

function buildOrganizationAuditLogMarkup(payload = {}, helpers = {}) {
  const { auditLogs = [] } = payload;
  const {
    escapeHtml = (value) => String(value ?? ""),
    formatAuthAuditEventLabel = (value) => String(value ?? ""),
    formatAuthAuditActorLabel = (value) => String(value ?? ""),
    formatAuthAuditSummary = (value) => String(value ?? ""),
    formatDate = (value) => String(value ?? ""),
  } = helpers;
  return auditLogs.map((item) => `
    <article class="org-admin-list-item">
      <div class="org-admin-list-item-head">
        <div>
          <strong>${escapeHtml(formatAuthAuditEventLabel(item?.event_type))}</strong>
          <p class="mono">${escapeHtml(formatAuthAuditActorLabel(item))}</p>
        </div>
        <span class="status-badge status-success">${escapeHtml(formatDate(item?.created_at))}</span>
      </div>
      <p>${escapeHtml(formatAuthAuditSummary(item))}</p>
      <p class="mono">대상 ${escapeHtml(String(item?.target_type || "-"))}${item?.target_id ? ` · ${escapeHtml(String(item.target_id || ""))}` : ""}</p>
    </article>
  `).join("");
}

function buildOrganizationMemberSummaryMarkup(payload = {}, helpers = {}) {
  const { members = [] } = payload;
  const {
    escapeHtml = (value) => String(value ?? ""),
    resolveStatusClass = (value) => String(value ?? ""),
    formatAccountStatusLabel = (value) => String(value ?? ""),
    formatMembershipStatusLabel = (value) => String(value ?? ""),
  } = helpers;
  const accountCounts = { active: 0, inactive: 0, deactivated: 0 };
  const membershipCounts = { active: 0, inactive: 0, deactivated: 0 };
  members.forEach((member) => {
    const accountStatus = String(member?.account_status || "active");
    const membershipStatus = String(member?.membership_status || member?.status || "active");
    if (Object.prototype.hasOwnProperty.call(accountCounts, accountStatus)) {
      accountCounts[accountStatus] += 1;
    }
    if (Object.prototype.hasOwnProperty.call(membershipCounts, membershipStatus)) {
      membershipCounts[membershipStatus] += 1;
    }
  });
  return `
    <div class="org-member-summary-card">
      <strong>현재 사용자 현황</strong>
      <div class="org-member-summary-grid">
        <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">총 ${escapeHtml(String(members.length))}명</span>
        <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">계정 ${escapeHtml(formatAccountStatusLabel("active"))} ${escapeHtml(String(accountCounts.active))}명</span>
        <span class="status-badge status-${escapeHtml(resolveStatusClass("inactive"))}">계정 ${escapeHtml(formatAccountStatusLabel("inactive"))} ${escapeHtml(String(accountCounts.inactive))}명</span>
        <span class="status-badge status-${escapeHtml(resolveStatusClass("deactivated"))}">계정 ${escapeHtml(formatAccountStatusLabel("deactivated"))} ${escapeHtml(String(accountCounts.deactivated))}명</span>
        <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">소속 ${escapeHtml(formatMembershipStatusLabel("active"))} ${escapeHtml(String(membershipCounts.active))}명</span>
        <span class="status-badge status-${escapeHtml(resolveStatusClass("inactive"))}">소속 ${escapeHtml(formatMembershipStatusLabel("inactive"))} ${escapeHtml(String(membershipCounts.inactive))}명</span>
        <span class="status-badge status-${escapeHtml(resolveStatusClass("deactivated"))}">소속 ${escapeHtml(formatMembershipStatusLabel("deactivated"))} ${escapeHtml(String(membershipCounts.deactivated))}명</span>
      </div>
      <p class="hint-text">계정 상태는 로그인 가능 여부, 소속 상태는 회사 내 사용 가능 여부를 뜻합니다.</p>
    </div>
  `;
}

function buildOrganizationMemberListMarkup(payload = {}, helpers = {}) {
  const {
    members = [],
    memberSaveStateByUserId = {},
    memberDeleteStateByUserId = {},
    currentAuthLocalUserId = "",
  } = payload;
  const {
    escapeHtml = (value) => String(value ?? ""),
    resolveStatusClass = (value) => String(value ?? ""),
    formatAccountStatusLabel = (value) => String(value ?? ""),
    formatMembershipStatusLabel = (value) => String(value ?? ""),
    formatOrgRoleLabel = (value) => String(value ?? ""),
    getRenderableOrgRoleOptions = () => [],
    membershipStatusOptions = [],
    isProtectedOrganizationMember = () => false,
  } = helpers;
  return members.map((member) => {
    const memberId = String(member?.id || "");
    const isSaving = Boolean(memberSaveStateByUserId[memberId]);
    const isDeleting = Boolean(memberDeleteStateByUserId[memberId]);
    const isProtected = Boolean(isProtectedOrganizationMember(member));
    const isSelf = Boolean(memberId && memberId === currentAuthLocalUserId);
    const roleStatusLocked = isProtected || isSelf;
    const deleteLocked = isProtected || isSelf || isDeleting;
    const hint = isProtected
      ? "부트스트랩/플랫폼 운영자 계정의 권한과 상태는 수정할 수 없습니다."
      : isSelf
        ? "자기 계정의 역할/상태는 이 화면에서 수정할 수 없습니다."
        : "";
    return `
      <article class="org-admin-list-item org-member-card" data-member-id="${escapeHtml(memberId)}">
        <div class="org-admin-list-item-head">
          <div>
            <strong>${escapeHtml(member?.display_name || member?.email || "-")}</strong>
            <p class="mono">${escapeHtml(member?.email || "-")}</p>
          </div>
          <div class="org-admin-badge-stack">
            <span class="status-badge status-${escapeHtml(resolveStatusClass(String(member?.account_status || "active")))}">계정 ${escapeHtml(formatAccountStatusLabel(member?.account_status || "active"))}</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass(String(member?.membership_status || member?.status || "active")))}">소속 ${escapeHtml(formatMembershipStatusLabel(member?.membership_status || member?.status || "active"))}</span>
          </div>
        </div>
        <p class="mono">회사 ${escapeHtml(member?.organization_name || "-")} · 현재 역할 ${escapeHtml(formatOrgRoleLabel(member?.role || "-"))}</p>
        <p>휴대폰 ${escapeHtml(member?.mobile_phone || "-")} · 회사 전화 ${escapeHtml(member?.office_phone || "-")}</p>
        <div class="org-member-form-grid">
          <label>
            <span>역할</span>
            <select data-member-field="role" ${roleStatusLocked ? "disabled" : ""}>
              ${getRenderableOrgRoleOptions(member?.role || "org_member").map((option) => `<option value="${escapeHtml(option)}" ${String(member?.role || "org_member") === option ? "selected" : ""}>${escapeHtml(formatOrgRoleLabel(option))}</option>`).join("")}
            </select>
          </label>
          <label>
            <span>소속 상태</span>
            <select data-member-field="membership_status" ${roleStatusLocked ? "disabled" : ""}>
              ${membershipStatusOptions.map((option) => `<option value="${escapeHtml(option)}" ${String(member?.membership_status || member?.status || "active") === option ? "selected" : ""}>${escapeHtml(formatMembershipStatusLabel(option))}</option>`).join("")}
            </select>
          </label>
          <label>
            <span>팀명</span>
            <input data-member-field="team_name" type="text" value="${escapeHtml(member?.team_name || "")}" />
          </label>
          <label>
            <span>직책</span>
            <input data-member-field="job_title" type="text" value="${escapeHtml(member?.job_title || "")}" />
          </label>
        </div>
        <div class="org-admin-inline-actions">
          ${hint ? `<span class="hint-text">${escapeHtml(hint)}</span>` : '<span class="hint-text">역할/상태/팀/직책 변경 후 저장할 수 있습니다.</span>'}
          <div class="org-admin-inline-button-row">
            ${!deleteLocked ? `<button class="ghost-button" type="button" data-member-delete="${escapeHtml(memberId)}">${isDeleting ? "삭제 중..." : "계정 삭제"}</button>` : ""}
            <button class="primary-button" type="button" data-member-save="${escapeHtml(memberId)}">${isSaving ? "저장 중..." : "저장"}</button>
          </div>
        </div>
      </article>
    `;
  }).join("");
}
```

- [ ] **Step 4: Rewire `frontend/app.js` to use the runtime helpers**

Replace the inline HTML assembly inside `renderOrganizationAdminPanel()` with these calls:

```javascript
dom.invitationList.innerHTML = ORG_ADMIN_RUNTIME?.buildInvitationListMarkup?.(
  {
    invitations: state.organizationInvitations,
    pendingInviteCount: Number(planSummary?.pending_invite_count || 0),
  },
  {
    escapeHtml,
    formatOrgRoleLabel,
    formatInvitationStatusLabel,
    formatDate,
  },
) || "";

dom.organizationAuditLogList.innerHTML = ORG_ADMIN_RUNTIME?.buildOrganizationAuditLogMarkup?.(
  { auditLogs: state.organizationAuditLogs },
  {
    escapeHtml,
    formatAuthAuditEventLabel,
    formatAuthAuditActorLabel,
    formatAuthAuditSummary,
    formatDate,
  },
) || "";

dom.organizationMemberSummary.innerHTML = ORG_ADMIN_RUNTIME?.buildOrganizationMemberSummaryMarkup?.(
  { members: sortedMembers },
  {
    escapeHtml,
    resolveStatusClass,
    formatAccountStatusLabel,
    formatMembershipStatusLabel,
  },
) || "";

dom.organizationMemberList.innerHTML = ORG_ADMIN_RUNTIME?.buildOrganizationMemberListMarkup?.(
  {
    members: sortedMembers,
    memberSaveStateByUserId: state.memberSaveStateByUserId,
    memberDeleteStateByUserId: state.memberDeleteStateByUserId,
    currentAuthLocalUserId: getCurrentAuthLocalUserId(),
  },
  {
    escapeHtml,
    resolveStatusClass,
    formatAccountStatusLabel,
    formatMembershipStatusLabel,
    formatOrgRoleLabel,
    getRenderableOrgRoleOptions,
    membershipStatusOptions: MEMBERSHIP_STATUS_OPTIONS,
    isProtectedOrganizationMember,
  },
) || "";
```

Keep these branches in `app.js` unchanged:

- admin mode gating
- loading/error/empty fallback messages
- invitation submit button disabled/title logic
- event binding for copy/revoke/save/delete buttons

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `node --test frontend/tests/org-admin-runtime.test.js`

Expected: PASS

- [ ] **Step 6: Run syntax verification**

Run: `node --check frontend/org-admin-runtime.js frontend/app.js`

Expected: exit code 0 and no output

- [ ] **Step 7: Commit**

```bash
git add frontend/org-admin-runtime.js frontend/app.js frontend/tests/org-admin-runtime.test.js
git commit -m "refactor: extract org admin markup helpers"
```

### Task 2: Extend Sales View Runtime For Closed Archive Rendering

**Files:**
- Modify: `frontend/sales-view-runtime.js`
- Modify: `frontend/app.js:6532-6720`
- Modify: `frontend/tests/sales-view-runtime.test.js`

- [ ] **Step 1: Write the failing tests**

Add these tests to `frontend/tests/sales-view-runtime.test.js`:

```javascript
test("buildClosedSalesArchiveSectionMarkup groups claims by year and month", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const html = runtime.buildClosedSalesArchiveSectionMarkup(
    {
      title: "계약 완료",
      claims: [
        {
          project_name: "Alpha",
          claim_status: "won",
          closed_at: "2026-03-10T00:00:00Z",
          owner_display_name: "김담당",
          sales_note: "[2026-03-09] 계약 확정",
        },
        {
          project_name: "Beta",
          claim_status: "won",
          closed_at: "2026-02-11T00:00:00Z",
          owner_display_name: "이담당",
          sales_note: "[2026-02-10] 계약 완료",
        },
      ],
      showContractAmount: true,
      currentYear: 2026,
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      getSalesYearMonthBucket: (value) => {
        if (String(value).includes("-03-")) return { year: 2026, month: 3 };
        if (String(value).includes("-02-")) return { year: 2026, month: 2 };
        return null;
      },
      formatContractAmountDisplay: (value) => String(value ?? ""),
      extractContractAmountTextFromSalesNote: () => "10억원",
      formatSalesDateLabel: (value) => String(value ?? ""),
      truncate: (value) => String(value ?? ""),
      formatSalesNoteTextForDisplay: (value) => String(value ?? ""),
      getLatestSalesNoteItem: () => ({ timestamp: "2026-03-09", text: "계약 확정" }),
      salesClaimStatusLabel: (value) => String(value ?? ""),
      formatSalesClaimEstimateLabel: () => "-",
    },
  );
  assert.match(html, /2026년/);
  assert.match(html, /3월/);
  assert.match(html, /2월/);
});

test("buildClosedSalesArchiveSectionMarkup renders empty state when no claims exist", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const html = runtime.buildClosedSalesArchiveSectionMarkup(
    {
      title: "영업 종료",
      claims: [],
      showContractAmount: false,
      currentYear: 2026,
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      getSalesYearMonthBucket: () => null,
      formatContractAmountDisplay: (value) => String(value ?? ""),
      extractContractAmountTextFromSalesNote: () => "",
      formatSalesDateLabel: (value) => String(value ?? ""),
      truncate: (value) => String(value ?? ""),
      formatSalesNoteTextForDisplay: (value) => String(value ?? ""),
      getLatestSalesNoteItem: () => null,
      salesClaimStatusLabel: (value) => String(value ?? ""),
      formatSalesClaimEstimateLabel: () => "-",
    },
  );
  assert.match(html, /영업 종료된 영업 프로젝트가 없습니다/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/sales-view-runtime.test.js`

Expected: FAIL with `TypeError` because `buildClosedSalesArchiveSectionMarkup` does not exist yet

- [ ] **Step 3: Extend `frontend/sales-view-runtime.js`**

Add this helper and export it from `window.SPMSSalesViewRuntime`:

```javascript
function buildClosedSalesArchiveSectionMarkup(payload = {}, helpers = {}) {
  const {
    title = "",
    claims = [],
    showContractAmount = false,
    currentYear = Number(new Date().getFullYear()),
  } = payload;
  const {
    escapeHtml = (value) => String(value ?? ""),
    getSalesYearMonthBucket = () => null,
    formatContractAmountDisplay = (value) => String(value ?? ""),
    extractContractAmountTextFromSalesNote = () => "",
    formatSalesDateLabel = (value) => String(value ?? ""),
    truncate = (value) => String(value ?? ""),
    formatSalesNoteTextForDisplay = (value) => String(value ?? ""),
    getLatestSalesNoteItem = () => null,
    salesClaimStatusLabel = (value) => String(value ?? ""),
    formatSalesClaimEstimateLabel = () => "-",
  } = helpers;

  const yearGroups = new Map();
  for (const claim of claims) {
    const bucket = getSalesYearMonthBucket(claim?.closed_at || claim?.updated_at || claim?.created_at);
    if (!bucket || !bucket.year || bucket.year > currentYear) {
      continue;
    }
    if (!yearGroups.has(bucket.year)) {
      yearGroups.set(bucket.year, new Map());
    }
    const monthGroups = yearGroups.get(bucket.year);
    if (!monthGroups.has(bucket.month)) {
      monthGroups.set(bucket.month, []);
    }
    monthGroups.get(bucket.month).push(claim);
  }

  const itemsMarkup = yearGroups.size
    ? [...yearGroups.entries()]
      .sort((left, right) => left[0] - right[0])
      .map(([year, monthGroups]) => {
        const monthMarkup = [...monthGroups.entries()]
          .sort((left, right) => left[0] - right[0])
          .map(([month, monthClaims]) => {
            const claimsMarkup = monthClaims.map((claim, index) => {
              const contractAmountText = showContractAmount ? formatContractAmountDisplay(extractContractAmountTextFromSalesNote(claim?.sales_note)) : "";
              const closedDateLabel = formatSalesDateLabel(claim?.closed_at || claim?.updated_at || claim?.created_at);
              const ownerLabel = claim?.owner_display_name || claim?.owner_email || "-";
              const latestNote = getLatestSalesNoteItem(claim?.sales_note, claim?.claimed_at);
              const latestNoteLabel = latestNote
                ? `${latestNote.timestamp ? `${latestNote.timestamp} · ` : ""}${truncate(formatSalesNoteTextForDisplay(latestNote.text), 120)}`
                : "";
              return `
                <article class="sales-summary-archive-item">
                  <div class="sales-summary-archive-head">
                    <strong>${escapeHtml(String(index + 1))}. ${escapeHtml(claim?.project_name || "-")}</strong>
                    <span class="entry-sales-status-badge${showContractAmount ? " is-closed" : ""}">${escapeHtml(salesClaimStatusLabel(claim?.claim_status))}</span>
                  </div>
                  <p class="mono">${escapeHtml(ownerLabel)} | ${escapeHtml(closedDateLabel)} 처리</p>
                  <p class="mono">${showContractAmount ? `계약금액 ${escapeHtml(contractAmountText || "-")}` : escapeHtml(formatSalesClaimEstimateLabel(claim))}</p>
                  ${latestNoteLabel ? `<p>${escapeHtml(latestNoteLabel)}</p>` : ""}
                </article>
              `;
            }).join("");
            return `
              <section class="sales-summary-archive-month">
                <div class="sales-summary-archive-month-head">
                  <strong>${escapeHtml(`${month}월`)}</strong>
                  <span class="mono">${escapeHtml(String(monthClaims.length))}건</span>
                </div>
                <div class="sales-summary-archive-list">${claimsMarkup}</div>
              </section>
            `;
          })
          .join("");
        return `
          <section class="sales-summary-archive-year">
            <div class="sales-summary-archive-year-head">
              <strong>${escapeHtml(`${year}년`)}</strong>
              <span class="mono">${escapeHtml(String([...monthGroups.values()].reduce((count, monthClaims) => count + monthClaims.length, 0)))}건</span>
            </div>
            <div class="sales-summary-archive-year-list">${monthMarkup}</div>
          </section>
        `;
      })
      .join("")
    : `<div class="empty-state">${escapeHtml(`${title}된 영업 프로젝트가 없습니다.`)}</div>`;

  return `
    <section class="sales-summary-archive-group">
      <div class="sales-summary-archive-group-head">
        <strong>${escapeHtml(title)}</strong>
        <span class="mono">${escapeHtml(String(claims.length))}건</span>
      </div>
      <div class="sales-summary-archive-list">${itemsMarkup}</div>
    </section>
  `;
}
```

- [ ] **Step 4: Rewire `frontend/app.js`**

Replace the body of `renderClosedSalesArchiveSection()` with a runtime call:

```javascript
function renderClosedSalesArchiveSection(title, claims, { showContractAmount = false } = {}) {
  const currentYear = getSalesYearMonthBucket(new Date())?.year || Number(new Date().getFullYear());
  return SALES_VIEW_RUNTIME?.buildClosedSalesArchiveSectionMarkup?.(
    {
      title,
      claims,
      showContractAmount,
      currentYear,
    },
    {
      escapeHtml,
      getSalesYearMonthBucket,
      formatContractAmountDisplay,
      extractContractAmountTextFromSalesNote,
      formatSalesDateLabel,
      truncate,
      formatSalesNoteTextForDisplay,
      getLatestSalesNoteItem,
      salesClaimStatusLabel,
      formatSalesClaimEstimateLabel,
    },
  ) || "";
}
```

Keep `renderSalesSummaryPanel()` 그대로 유지하고, `activeMarkup` / `closedMarkup` 조합과 force-release event binding은 바꾸지 않는다.

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `node --test frontend/tests/sales-view-runtime.test.js`

Expected: PASS

- [ ] **Step 6: Run syntax verification**

Run: `node --check frontend/sales-view-runtime.js frontend/app.js`

Expected: exit code 0 and no output

- [ ] **Step 7: Commit**

```bash
git add frontend/sales-view-runtime.js frontend/app.js frontend/tests/sales-view-runtime.test.js
git commit -m "refactor: extract sales archive runtime"
```

## Self-Review

- Spec coverage: 조직 관리자 패널 잔여 마크업과 영업 종료 아카이브 렌더링 모두 task로 포함했다.
- Placeholder scan: `TODO`, `TBD`, 추상적인 “적절히 처리” 표현 없이 실제 helper 이름, 테스트 코드, 명령을 모두 적었다.
- Type consistency: runtime helper 이름은 `buildInvitationListMarkup`, `buildOrganizationAuditLogMarkup`, `buildOrganizationMemberSummaryMarkup`, `buildOrganizationMemberListMarkup`, `buildClosedSalesArchiveSectionMarkup`으로 plan 전반에서 일관되게 사용했다.
