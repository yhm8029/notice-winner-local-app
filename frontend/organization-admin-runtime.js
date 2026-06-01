(function attachOrganizationAdminRuntime(global) {
  function ensureOrganizationAdminPanel(options = {}) {
    const { dom, document } = options;
    if (!dom || !document || dom.panelOrgAdmin) {
      return;
    }

    const panel = document.createElement("section");
    panel.id = "panel-org-admin";
    panel.className = "panel panel-org-admin hidden";
    panel.innerHTML = `
      <div class="panel-heading">
        <div>
          <p class="kicker">조직 운영</p>
          <h2>조직 관리자</h2>
        </div>
        <div class="inline-actions">
          <button id="org-admin-refresh-button" class="ghost-button" type="button">새로고침</button>
          <button id="organization-audit-refresh-button" class="ghost-button" type="button">감사 로그 새로고침</button>
        </div>
      </div>
      <div class="org-admin-grid">
        <section class="runtime-card org-admin-card">
          <div class="runtime-card-head">
            <div>
              <strong>플랜 및 좌석 현황</strong>
              <p class="kicker">현재 조직의 사용자/초대 한도</p>
            </div>
          </div>
          <div id="organization-plan-summary" class="org-plan-summary empty-state">플랜 요약을 불러오는 중입니다.</div>
        </section>

        <section class="runtime-card org-admin-card">
          <div class="runtime-card-head">
            <div>
              <strong>초대 관리</strong>
              <p class="kicker">조직 사용자를 초대하고 링크를 관리합니다.</p>
            </div>
          </div>
          <form id="invitation-form" class="org-admin-form">
            <label>
              <span>이메일</span>
              <input id="invitation-email" type="email" required />
            </label>
            <label>
              <span>표시 이름</span>
              <input id="invitation-display-name" type="text" />
            </label>
            <label>
              <span>역할</span>
              <select id="invitation-role"></select>
            </label>
            <label>
              <span>팀명</span>
              <input id="invitation-team-name" type="text" />
            </label>
            <label>
              <span>직책</span>
              <input id="invitation-job-title" type="text" />
            </label>
            <label>
              <span>만료일</span>
              <select id="invitation-expires-in-days">
                <option value="3">3일</option>
                <option value="7" selected>7일</option>
                <option value="14">14일</option>
                <option value="30">30일</option>
              </select>
            </label>
          </form>
          <div class="inline-actions">
            <button id="invitation-submit-button" class="primary-button" type="button">초대 링크 생성</button>
          </div>
          <div id="invitation-status-message" class="flash-message hidden" role="status" aria-live="polite"></div>
          <div id="invitation-list" class="runtime-list empty-state">초대 목록을 불러오는 중입니다.</div>
        </section>

        <section class="runtime-card org-admin-card">
          <div class="runtime-card-head">
            <div>
              <strong>사용자 관리</strong>
              <p class="kicker">사용자 상태와 역할을 관리합니다.</p>
            </div>
          </div>
          <div id="organization-member-summary" class="org-member-summary empty-state">사용자 상태 요약을 불러오는 중입니다.</div>
          <div id="organization-member-list" class="runtime-list empty-state">사용자 목록을 불러오는 중입니다.</div>
        </section>

        <section class="runtime-card org-admin-card">
          <div class="runtime-card-head">
            <div>
              <strong>조직 감사 로그</strong>
              <p class="kicker">최근 초대/권한/상태 변경 이력을 확인합니다.</p>
            </div>
          </div>
          <div id="organization-audit-log-list" class="runtime-list empty-state">조직 감사 로그를 불러오는 중입니다.</div>
        </section>
      </div>
    `;

    const insertionTarget = dom.panelDashboard || dom.panelForm;
    if (insertionTarget?.parentElement) {
      insertionTarget.parentElement.insertBefore(panel, insertionTarget);
    }

    dom.panelOrgAdmin = panel;
    dom.orgAdminRefreshButton = panel.querySelector("#org-admin-refresh-button");
    dom.organizationAuditRefreshButton = panel.querySelector("#organization-audit-refresh-button");
    dom.invitationForm = panel.querySelector("#invitation-form");
    dom.invitationEmail = panel.querySelector("#invitation-email");
    dom.invitationDisplayName = panel.querySelector("#invitation-display-name");
    dom.invitationRole = panel.querySelector("#invitation-role");
    dom.invitationTeamName = panel.querySelector("#invitation-team-name");
    dom.invitationJobTitle = panel.querySelector("#invitation-job-title");
    dom.invitationExpiresInDays = panel.querySelector("#invitation-expires-in-days");
    dom.invitationSubmitButton = panel.querySelector("#invitation-submit-button");
    dom.invitationStatusMessage = panel.querySelector("#invitation-status-message");
    dom.organizationPlanSummary = panel.querySelector("#organization-plan-summary");
    dom.invitationList = panel.querySelector("#invitation-list");
    dom.organizationMemberSummary = panel.querySelector("#organization-member-summary");
    dom.organizationMemberList = panel.querySelector("#organization-member-list");
    dom.organizationAuditLogList = panel.querySelector("#organization-audit-log-list");
  }

  function renderInvitationStatus(options = {}) {
    const {
      dom,
      buildInvitationStatusViewModel = (message = "", level = "") => ({
        text: String(message || "").trim(),
        hasMessage: Boolean(String(message || "").trim()),
        isError: level === "error",
      }),
      message = "",
      level = "",
    } = options;

    if (!dom?.invitationStatusMessage) {
      return;
    }

    const viewModel = buildInvitationStatusViewModel(message, level);
    dom.invitationStatusMessage.textContent = viewModel.text || "";
    dom.invitationStatusMessage.classList.toggle("hidden", !viewModel.hasMessage);
    dom.invitationStatusMessage.classList.toggle("error", Boolean(viewModel.isError));
  }

  function buildOrganizationPlanSummaryView(options = {}, helpers = {}) {
    const {
      planSummary = null,
      loading = false,
      error = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;

    let html = '<div class="empty-state">플랜 요약 정보를 아직 불러오지 못했습니다.</div>';
    if (loading && !planSummary) {
      html = '<div class="empty-state">플랜 요약을 불러오는 중입니다.</div>';
    } else if (planSummary) {
      const inviteBlocked = Boolean(planSummary.upgrade_required);
      html = `
        <div class="org-plan-summary-card${inviteBlocked ? " is-upgrade-required" : ""}">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(planSummary.plan_label || `플랜 ${planSummary.plan_code || "A"}`)}</strong>
              <p class="mono">가용 ${escapeHtml(String(planSummary.active_user_count))} / ${escapeHtml(String(planSummary.active_user_limit))}명 | 대기 초대 ${escapeHtml(String(planSummary.pending_invite_count))} / ${escapeHtml(String(planSummary.pending_invite_limit))}건</p>
            </div>
            <span class="status-badge status-${escapeHtml(inviteBlocked ? "failed" : "success")}">${escapeHtml(inviteBlocked ? "업그레이드 필요" : "사용 가능")}</span>
          </div>
          <div class="org-plan-summary-grid">
            <div class="org-plan-summary-metric">
              <span>현재 가용 사용자</span>
              <strong>${escapeHtml(String(planSummary.active_user_count))} / ${escapeHtml(String(planSummary.active_user_limit))}명</strong>
            </div>
            <div class="org-plan-summary-metric">
              <span>남은 사용자 슬롯</span>
              <strong>${escapeHtml(String(planSummary.remaining_active_user_slots))}명</strong>
            </div>
            <div class="org-plan-summary-metric">
              <span>현재 pending 초대</span>
              <strong>${escapeHtml(String(planSummary.pending_invite_count))} / ${escapeHtml(String(planSummary.pending_invite_limit))}건</strong>
            </div>
            <div class="org-plan-summary-metric">
              <span>남은 초대 슬롯</span>
              <strong>${escapeHtml(String(planSummary.remaining_pending_invite_slots))}건</strong>
            </div>
          </div>
          ${planSummary.upgrade_message ? `<p class="org-plan-summary-upgrade">${escapeHtml(planSummary.upgrade_message)}</p>` : '<p class="hint-text">현재 플랜 한도 안에서 사용자 초대와 가입을 운영 중입니다.</p>'}
        </div>
      `;
    } else if (error) {
      html = `<div class="empty-state">${escapeHtml(error)}</div>`;
    }

    return {
      html,
      invitationSubmitDisabled: Boolean(planSummary?.upgrade_required),
      invitationSubmitTitle: Boolean(planSummary?.upgrade_required) ? String(planSummary?.upgrade_message || "") : "",
    };
  }

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

    let html = "";
    if (organizationInvitationsLoading) {
      html = '<div class="empty-state">초대 목록을 불러오는 중입니다.</div>';
    } else if (organizationInvitationsError) {
      html = `<div class="empty-state">${escapeHtml(organizationInvitationsError)}</div>`;
    } else if (!organizationInvitations.length) {
      const hasHiddenInvitations = Number(planSummary?.pending_invite_count || 0) > 0;
      html = hasHiddenInvitations
        ? '<div class="empty-state">현재 권한으로 관리할 수 없는 pending 초대가 있습니다.</div>'
        : '<div class="empty-state">아직 생성된 초대가 없습니다.</div>';
    } else {
      const visiblePendingInviteCount = organizationInvitations.filter((item) => String(item.status || "pending") === "pending").length;
      const hasHiddenInvitations = Number(planSummary?.pending_invite_count || 0) > visiblePendingInviteCount;
      html = `
        ${hasHiddenInvitations ? '<p class="hint-text">현재 권한으로 관리할 수 없는 pending 초대가 있습니다.</p>' : ""}
        ${organizationInvitations.map((item) => {
          const status = String(item.status || "pending");
          const isPending = status === "pending";
          return `
            <article class="org-admin-list-item">
              <div class="org-admin-list-item-head">
                <div>
                  <strong>${escapeHtml(item.display_name || item.email || "-")}</strong>
                  <p class="mono">${escapeHtml(item.email || "-")} | ${escapeHtml(formatOrgRoleLabel(item.role || "org_member"))}</p>
                </div>
                <span class="status-badge status-${escapeHtml(status)}">${escapeHtml(formatInvitationStatusLabel(status))}</span>
              </div>
              <p>팀 ${escapeHtml(item.team_name || "-")} | 직책 ${escapeHtml(item.job_title || "-")}</p>
              ${item.delivery_message ? `<p class="mono">${escapeHtml(item.delivery_message)}</p>` : ""}
              ${item.initial_password ? `<p class="mono">초기 암호 ${escapeHtml(item.initial_password)}</p>` : ""}
              <p class="mono">만료 ${escapeHtml(formatDate(item.expires_at))}</p>
              <div class="org-admin-inline-actions">
                <button class="ghost-button" type="button" data-invite-copy="${escapeHtml(item.invite_url || "")}">링크 복사</button>
                ${isPending ? `<button class="ghost-button" type="button" data-invite-revoke="${escapeHtml(item.id)}">철회</button>` : ""}
              </div>
            </article>
          `;
        }).join("")}
      `;
    }

    return { html };
  }

  function buildOrganizationMemberSummaryView(options = {}, helpers = {}) {
    const {
      organizationMembers = [],
      loading = false,
      error = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      formatAccountStatusLabel = (value) => String(value || ""),
      formatMembershipStatusLabel = (value) => String(value || ""),
      resolveStatusClass = (value) => String(value || ""),
    } = helpers;

    if (loading) {
      return {
        html: '<div class="empty-state">사용자 상태 요약을 불러오는 중입니다.</div>',
      };
    }

    if (error) {
      return {
        html: `<div class="empty-state">${escapeHtml(error)}</div>`,
      };
    }

    if (!organizationMembers.length) {
      return {
        html: '<div class="empty-state">등록된 사용자가 없습니다.</div>',
      };
    }

    const accountCounts = { active: 0, inactive: 0, deactivated: 0 };
    const membershipCounts = { active: 0, inactive: 0, deactivated: 0 };
    organizationMembers.forEach((member) => {
      const accountStatus = String(member.account_status || "active");
      const membershipStatus = String(member.membership_status || member.status || "active");
      if (Object.prototype.hasOwnProperty.call(accountCounts, accountStatus)) {
        accountCounts[accountStatus] += 1;
      }
      if (Object.prototype.hasOwnProperty.call(membershipCounts, membershipStatus)) {
        membershipCounts[membershipStatus] += 1;
      }
    });

    return {
      html: `
        <div class="org-member-summary-card">
          <strong>현재 사용자 현황</strong>
          <div class="org-member-summary-grid">
            <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}" aria-label="총${escapeHtml(String(organizationMembers.length))}명">총 ${escapeHtml(String(organizationMembers.length))}명</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">계정 ${escapeHtml(formatAccountStatusLabel("active"))} ${escapeHtml(String(accountCounts.active))}명</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass("inactive"))}">계정 ${escapeHtml(formatAccountStatusLabel("inactive"))} ${escapeHtml(String(accountCounts.inactive))}명</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass("deactivated"))}">계정 ${escapeHtml(formatAccountStatusLabel("deactivated"))} ${escapeHtml(String(accountCounts.deactivated))}명</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass("active"))}">소속 ${escapeHtml(formatMembershipStatusLabel("active"))} ${escapeHtml(String(membershipCounts.active))}명</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass("inactive"))}">소속 ${escapeHtml(formatMembershipStatusLabel("inactive"))} ${escapeHtml(String(membershipCounts.inactive))}명</span>
            <span class="status-badge status-${escapeHtml(resolveStatusClass("deactivated"))}">소속 ${escapeHtml(formatMembershipStatusLabel("deactivated"))} ${escapeHtml(String(membershipCounts.deactivated))}명</span>
          </div>
          <p class="hint-text">계정 상태는 로그인 가능 여부, 소속 상태는 회사 내 사용 가능 여부를 뜻합니다.</p>
        </div>
      `,
    };
  }

  function buildOrganizationMemberListView(options = {}, helpers = {}) {
    const {
      organizationMembers = [],
      memberSaveStateByUserId = {},
      memberDeleteStateByUserId = {},
      loading = false,
      error = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      formatAccountStatusLabel = (value) => String(value || ""),
      formatMembershipStatusLabel = (value) => String(value || ""),
      formatOrgRoleLabel = (value) => String(value || ""),
      resolveStatusClass = (value) => String(value || ""),
      getRenderableOrgRoleOptions = (value) => [String(value || "org_member")],
      membershipStatusOptions = [],
      isProtectedOrganizationMember = () => false,
      getCurrentAuthLocalUserId = () => "",
    } = helpers;

    if (loading) {
      return {
        html: '<div class="empty-state">사용자 목록을 불러오는 중입니다.</div>',
      };
    }

    if (error) {
      return {
        html: `<div class="empty-state">${escapeHtml(error)}</div>`,
      };
    }

    if (!organizationMembers.length) {
      return {
        html: '<div class="empty-state">등록된 사용자가 없습니다.</div>',
      };
    }

    const sortedMembers = [...organizationMembers].sort((left, right) => {
      const leftActive = String(left.membership_status || left.status || "active") === "active" ? 0 : 1;
      const rightActive = String(right.membership_status || right.status || "active") === "active" ? 0 : 1;
      if (leftActive !== rightActive) {
        return leftActive - rightActive;
      }
      return String(left.display_name || left.email || "").localeCompare(String(right.display_name || right.email || ""), "ko");
    });

    return {
      html: sortedMembers.map((member) => {
        const memberId = String(member.id || "");
        const isSaving = Boolean(memberSaveStateByUserId[memberId]);
        const isDeleting = Boolean(memberDeleteStateByUserId[memberId]);
        const isProtected = isProtectedOrganizationMember(member);
        const isSelf = memberId && memberId === getCurrentAuthLocalUserId();
        const roleStatusLocked = isProtected || isSelf;
        const deleteLocked = isProtected || isSelf || isDeleting;
        const hint = isProtected
          ? "부트스트랩 또는 플랫폼 운영 계정은 권한과 상태를 수정할 수 없습니다."
          : isSelf
          ? "내 계정의 역할과 상태는 여기에서 수정할 수 없습니다."
          : "";
        return `
          <article class="org-admin-list-item org-member-card" data-member-id="${escapeHtml(memberId)}">
            <div class="org-admin-list-item-head">
              <div>
                <strong>${escapeHtml(member.display_name || member.email || "-")}</strong>
                <p class="mono">${escapeHtml(member.email || "-")}</p>
              </div>
              <div class="org-admin-badge-stack">
                <span class="status-badge status-${escapeHtml(resolveStatusClass(String(member.account_status || "active")))}">계정 ${escapeHtml(formatAccountStatusLabel(member.account_status || "active"))}</span>
                <span class="status-badge status-${escapeHtml(resolveStatusClass(String(member.membership_status || member.status || "active")))}">소속 ${escapeHtml(formatMembershipStatusLabel(member.membership_status || member.status || "active"))}</span>
              </div>
            </div>
            <p class="mono">회사 ${escapeHtml(member.organization_name || "-")} | 현재 역할 ${escapeHtml(formatOrgRoleLabel(member.role || "-"))}</p>
            <p>휴대폰 ${escapeHtml(member.mobile_phone || "-")} | 회사 전화 ${escapeHtml(member.office_phone || "-")}</p>
            <div class="org-member-form-grid">
              <label>
                <span>역할</span>
                <select data-member-field="role" ${roleStatusLocked ? "disabled" : ""}>
                  ${getRenderableOrgRoleOptions(member.role || "org_member").map((option) => `<option value="${escapeHtml(option)}" ${String(member.role || "org_member") === option ? "selected" : ""}>${escapeHtml(formatOrgRoleLabel(option))}</option>`).join("")}
                </select>
              </label>
              <label>
                <span>소속 상태</span>
                <select data-member-field="membership_status" ${roleStatusLocked ? "disabled" : ""}>
                  ${membershipStatusOptions.map((option) => `<option value="${escapeHtml(option)}" ${String(member.membership_status || member.status || "active") === option ? "selected" : ""}>${escapeHtml(formatMembershipStatusLabel(option))}</option>`).join("")}
                </select>
              </label>
              <label>
                <span>팀명</span>
                <input data-member-field="team_name" type="text" value="${escapeHtml(member.team_name || "")}" />
              </label>
              <label>
                <span>직책</span>
                <input data-member-field="job_title" type="text" value="${escapeHtml(member.job_title || "")}" />
              </label>
            </div>
            <div class="org-admin-inline-actions">
              ${hint ? `<span class="hint-text">${escapeHtml(hint)}</span>` : '<span class="hint-text">역할, 상태, 팀명, 직책 변경 후 저장할 수 있습니다.</span>'}
              <div class="org-admin-inline-button-row">
                ${!deleteLocked ? `<button class="ghost-button" type="button" data-member-delete="${escapeHtml(memberId)}">${isDeleting ? "삭제 중.." : "계정 삭제"}</button>` : ""}
                <button class="primary-button" type="button" data-member-save="${escapeHtml(memberId)}">${isSaving ? "저장 중.." : "저장"}</button>
              </div>
            </div>
          </article>
        `;
      }).join(""),
    };
  }

  function buildOrganizationAdminMarkup(options = {}, helpers = {}) {
    const {
      canUseAdminMode = false,
      uiMode = "",
      planSummary = null,
      organizationInvitationsLoading = false,
      organizationInvitationsError = "",
      organizationInvitations = [],
      invitationSaving = false,
      organizationAuditLogsLoading = false,
      organizationAuditLogsError = "",
      organizationAuditLogs = [],
      organizationMembersLoading = false,
      organizationMembersError = "",
      organizationMembers = [],
      memberSaveStateByUserId = {},
      memberDeleteStateByUserId = {},
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
      formatOrgRoleLabel = (value) => String(value || ""),
      formatInvitationStatusLabel = (value) => String(value || ""),
      formatAuthAuditEventLabel = (value) => String(value || ""),
      formatAuthAuditActorLabel = (value) => String(value || ""),
      formatAuthAuditSummary = (value) => String(value || ""),
      formatAccountStatusLabel = (value) => String(value || ""),
      formatMembershipStatusLabel = (value) => String(value || ""),
      resolveStatusClass = (value) => String(value || ""),
      getRenderableOrgRoleOptions = (value) => [String(value || "org_member")],
      membershipStatusOptions = [],
      isProtectedOrganizationMember = () => false,
      getCurrentAuthLocalUserId = () => "",
    } = helpers;

    if (!canUseAdminMode || uiMode !== "admin") {
      return {
        planSummaryHtml: '<div class="empty-state">관리자 모드에서 플랜 현황을 확인할 수 있습니다.</div>',
        invitationListHtml: '<div class="empty-state">관리자 모드에서 초대 목록을 확인할 수 있습니다.</div>',
        invitationSubmitDisabled: true,
        invitationSubmitTitle: "",
        auditLogHtml: '<div class="empty-state">관리자 모드에서 조직 감사 로그를 확인할 수 있습니다.</div>',
        memberSummaryHtml: '<div class="empty-state">관리자 모드에서 사용자 상태를 확인할 수 있습니다.</div>',
        memberListHtml: '<div class="empty-state">관리자 모드에서 사용자 관리를 사용할 수 있습니다.</div>',
      };
    }

    const planSummaryView = buildOrganizationPlanSummaryView(
      {
        planSummary,
        loading: organizationInvitationsLoading,
        error: organizationInvitationsError,
      },
      {
        escapeHtml,
      },
    );

    const invitationListView = buildOrganizationInvitationListView(
      {
        organizationInvitationsLoading,
        organizationInvitationsError,
        organizationInvitations,
        planSummary,
      },
      {
        escapeHtml,
        formatDate,
        formatOrgRoleLabel,
        formatInvitationStatusLabel,
      },
    );

    let auditLogHtml = "";
    if (organizationAuditLogsLoading) {
      auditLogHtml = '<div class="empty-state">조직 감사 로그를 불러오는 중입니다.</div>';
    } else if (organizationAuditLogsError) {
      auditLogHtml = `<div class="empty-state">${escapeHtml(organizationAuditLogsError)}</div>`;
    } else if (!organizationAuditLogs.length) {
      auditLogHtml = '<div class="empty-state">최근 조직 감사 로그가 없습니다.</div>';
    } else {
      auditLogHtml = organizationAuditLogs.map((item) => `
        <article class="org-admin-list-item">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(formatAuthAuditEventLabel(item.event_type))}</strong>
              <p class="mono">${escapeHtml(formatAuthAuditActorLabel(item))}</p>
            </div>
            <span class="status-badge status-success">${escapeHtml(formatDate(item.created_at))}</span>
          </div>
          <p>${escapeHtml(formatAuthAuditSummary(item))}</p>
          <p class="mono">대상 ${escapeHtml(String(item.target_type || "-"))}${item.target_id ? ` | ${escapeHtml(String(item.target_id || ""))}` : ""}</p>
        </article>
      `).join("");
    }

    const memberSummaryHtml = buildOrganizationMemberSummaryView(
      {
        organizationMembers,
        loading: organizationMembersLoading,
        error: organizationMembersError,
      },
      {
        escapeHtml,
        formatAccountStatusLabel,
        formatMembershipStatusLabel,
        resolveStatusClass,
      },
    ).html;
    const memberListHtml = buildOrganizationMemberListView(
      {
        organizationMembers,
        memberSaveStateByUserId,
        memberDeleteStateByUserId,
        loading: organizationMembersLoading,
        error: organizationMembersError,
      },
      {
        escapeHtml,
        formatAccountStatusLabel,
        formatMembershipStatusLabel,
        formatOrgRoleLabel,
        resolveStatusClass,
        getRenderableOrgRoleOptions,
        membershipStatusOptions,
        isProtectedOrganizationMember,
        getCurrentAuthLocalUserId,
      },
    ).html;

    return {
      planSummaryHtml: planSummaryView.html,
      invitationListHtml: invitationListView.html,
      invitationSubmitDisabled: Boolean(invitationSaving || planSummaryView.invitationSubmitDisabled),
      invitationSubmitTitle: planSummaryView.invitationSubmitTitle,
      auditLogHtml,
      memberSummaryHtml,
      memberListHtml,
    };
  }

  function bindOrganizationAdminActions(options = {}) {
    const {
      dom,
      onInviteCopy,
      onInviteRevoke,
      onMemberSave,
      onMemberDelete,
    } = options;

    bindInvitationActions(dom?.invitationList, {
      onInviteCopy,
      onInviteRevoke,
    });
    bindMemberActions(dom?.organizationMemberList, {
      onMemberSave,
      onMemberDelete,
    });
  }

  function bindInvitationActions(list, handlers = {}) {
    if (!list) {
      return;
    }
    list.__spmsInviteHandlers = handlers;
    if (list.__spmsInviteHandlersBound) {
      return;
    }
    list.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) {
        return;
      }

      const copyButton = target.closest("[data-invite-copy]");
      if (copyButton instanceof global.HTMLElement && list.contains(copyButton)) {
        const inviteUrl = copyButton.getAttribute("data-invite-copy") || "";
        void list.__spmsInviteHandlers?.onInviteCopy?.(inviteUrl);
        return;
      }

      const revokeButton = target.closest("[data-invite-revoke]");
      if (revokeButton instanceof global.HTMLElement && list.contains(revokeButton)) {
        const invitationId = revokeButton.getAttribute("data-invite-revoke") || "";
        if (!invitationId) {
          return;
        }
        void list.__spmsInviteHandlers?.onInviteRevoke?.(invitationId);
      }
    });
    list.__spmsInviteHandlersBound = true;
  }

  function bindMemberActions(list, handlers = {}) {
    if (!list) {
      return;
    }
    list.__spmsMemberHandlers = handlers;
    if (list.__spmsMemberHandlersBound) {
      return;
    }
    list.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof global.HTMLElement)) {
        return;
      }

      const saveButton = target.closest("[data-member-save]");
      if (saveButton instanceof global.HTMLElement && list.contains(saveButton)) {
        const article = saveButton.closest("[data-member-id]");
        const userId = saveButton.getAttribute("data-member-save") || "";
        if (!(article instanceof global.HTMLElement) || !userId) {
          return;
        }
        void list.__spmsMemberHandlers?.onMemberSave?.(userId, article);
        return;
      }

      const deleteButton = target.closest("[data-member-delete]");
      if (deleteButton instanceof global.HTMLElement && list.contains(deleteButton)) {
        const article = deleteButton.closest("[data-member-id]");
        const userId = deleteButton.getAttribute("data-member-delete") || "";
        if (!(article instanceof global.HTMLElement) || !userId) {
          return;
        }
        void list.__spmsMemberHandlers?.onMemberDelete?.(userId, article);
      }
    });
    list.__spmsMemberHandlersBound = true;
  }

  global.SPMSOrganizationAdminRuntime = {
    ensureOrganizationAdminPanel,
    renderInvitationStatus,
    buildOrganizationPlanSummaryView,
    buildOrganizationInvitationListView,
    buildOrganizationMemberSummaryView,
    buildOrganizationMemberListView,
    buildOrganizationAdminMarkup,
    bindOrganizationAdminActions,
  };
})(window);
