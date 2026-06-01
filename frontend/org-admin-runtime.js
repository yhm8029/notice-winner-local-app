(function attachSPMSOrgAdminRuntime(globalObject) {
  function buildOrgPlanSummaryMarkup(planSummary, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    const inviteBlocked = Boolean(planSummary?.upgrade_required);
    return `
      <div class="org-plan-summary-card${inviteBlocked ? " is-upgrade-required" : ""}">
        <div class="org-admin-list-item-head">
          <div>
            <strong>${escapeHtml(planSummary?.plan_label || `플랜 ${planSummary?.plan_code || "A"}`)}</strong>
            <p class="mono">가입 ${escapeHtml(String(planSummary?.active_user_count || 0))} / ${escapeHtml(String(planSummary?.active_user_limit || 0))}명 · 대기 초대 ${escapeHtml(String(planSummary?.pending_invite_count || 0))} / ${escapeHtml(String(planSummary?.pending_invite_limit || 0))}건</p>
          </div>
          <span class="status-badge status-${escapeHtml(inviteBlocked ? "failed" : "success")}">${escapeHtml(inviteBlocked ? "업그레이드 필요" : "사용 가능")}</span>
        </div>
        <div class="org-plan-summary-grid">
          <div class="org-plan-summary-metric">
            <span>현재 가입 수</span>
            <strong>${escapeHtml(String(planSummary?.active_user_count || 0))} / ${escapeHtml(String(planSummary?.active_user_limit || 0))}명</strong>
          </div>
          <div class="org-plan-summary-metric">
            <span>남은 가입 수</span>
            <strong>${escapeHtml(String(planSummary?.remaining_active_user_slots || 0))}명</strong>
          </div>
          <div class="org-plan-summary-metric">
            <span>현재 pending 초대</span>
            <strong>${escapeHtml(String(planSummary?.pending_invite_count || 0))} / ${escapeHtml(String(planSummary?.pending_invite_limit || 0))}건</strong>
          </div>
          <div class="org-plan-summary-metric">
            <span>남은 초대 가능 수</span>
            <strong>${escapeHtml(String(planSummary?.remaining_pending_invite_slots || 0))}건</strong>
          </div>
        </div>
        ${planSummary?.upgrade_message ? `<p class="org-plan-summary-upgrade">${escapeHtml(planSummary.upgrade_message)}</p>` : '<p class="hint-text">현재 플랜 한도 안에서 사용자 초대와 가입을 운영할 수 있습니다.</p>'}
      </div>
    `;
  }

  function buildInvitationRoleOptionsMarkup(roles = [], helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
    } = helpers;
    const roleOptions = Array.isArray(roles) && roles.length ? roles : ["org_member"];
    return roleOptions.map((role) => {
      const value = String(role || "org_member").trim() || "org_member";
      return `<option value="${escapeHtml(value)}">${escapeHtml(formatOrgRoleLabel(value))}</option>`;
    }).join("");
  }

  function resolveItems(payload, keys) {
    for (const key of keys) {
      const value = payload?.[key];
      if (Array.isArray(value)) {
        return value;
      }
    }
    return [];
  }

  function sliceVisibleItems(items, visibleCount = 5) {
    const normalizedItems = Array.isArray(items) ? items : [];
    const limit = Math.max(1, Number(visibleCount || 5) || 5);
    return {
      visibleItems: normalizedItems.slice(0, limit),
      hasMore: normalizedItems.length >= limit,
      limit,
    };
  }

  function buildOrgAdminLogCardMarkup({
    title,
    kicker,
    refreshButtonId,
    loadMoreButtonId,
    loadingMessage,
    emptyMessage,
    errorMessage,
    loading,
    items,
    visibleCount,
    canLoadMore,
    bodyMarkup,
  }, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
    } = helpers;
    const isLoading = Boolean(loading);
    const { visibleItems, hasMore, limit } = sliceVisibleItems(items, visibleCount);
    const resolvedBodyMarkup = typeof bodyMarkup === "function"
      ? bodyMarkup(visibleItems, helpers)
      : String(bodyMarkup || "");
    let contentMarkup = "";
    if (isLoading && !visibleItems.length) {
      contentMarkup = `<div class="empty-state">${escapeHtml(loadingMessage)}</div>`;
    } else if (errorMessage && !visibleItems.length) {
      contentMarkup = `<div class="empty-state">${escapeHtml(errorMessage)}</div>`;
    } else if (!visibleItems.length) {
      contentMarkup = `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
    } else {
      contentMarkup = resolvedBodyMarkup;
    }
    const showLoadMore = Boolean(canLoadMore ?? hasMore);
    const loadMoreButtonMarkup = showLoadMore
      ? `<button id="${escapeHtml(loadMoreButtonId)}" class="ghost-button" type="button" ${isLoading ? "disabled" : ""}>${escapeHtml(isLoading ? "더 불러오는 중..." : "더 보기")}</button>`
      : "";
    return `
      <article class="runtime-card org-admin-card">
        <div class="runtime-card-head">
          <div>
            <strong>${escapeHtml(title)}</strong>
            <p class="kicker">${escapeHtml(kicker)}</p>
          </div>
          <button id="${escapeHtml(refreshButtonId)}" class="ghost-button" type="button">새로고침</button>
        </div>
        <div class="runtime-list">${contentMarkup}</div>
        <div class="org-admin-card-actions">
          ${loadMoreButtonMarkup}
          <span class="hint-text">${escapeHtml(`현재 ${limit}개까지 확인 중입니다.`)}</span>
        </div>
      </article>
    `;
  }
  function buildInvitationListMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      formatInvitationStatusLabel = (value) => String(value ?? ""),
    } = helpers;
    const invitations = resolveItems(payload, ["invitations", "items", "invites"]);
    if (!invitations.length) {
      return "";
    }
    const planSummary = payload?.planSummary || payload?.organizationPlanSummary || null;
    const visiblePendingInviteCount = invitations.filter((item) => String(item?.status || "pending") === "pending").length;
    const hasHiddenInvitations = Number(planSummary?.pending_invite_count || 0) > visiblePendingInviteCount;
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
            ${item?.invite_url ? `<p class="mono">초대 링크 ${escapeHtml(item.invite_url)}</p>` : ""}
            ${item?.initial_password ? `<p class="mono">초기 암호 ${escapeHtml(item.initial_password)}</p>` : ""}
            <p class="mono">만료 ${escapeHtml(formatDate(item?.expires_at))}</p>
            <div class="org-admin-inline-actions">
              <button class="ghost-button" type="button" data-invite-copy="${escapeHtml(item?.invite_url || "")}">링크 복사</button>
              ${
                isPending
                  ? `<button class="ghost-button" type="button" data-invite-revoke="${escapeHtml(item?.id || "")}">철회</button>`
                  : ""
              }
            </div>
          </article>
        `;
      }).join("")}
    `;
  }

  function resolveInvitationDeliveryMessage(item = {}) {
    const explicitMessage = String(item?.delivery_message || "").trim();
    if (explicitMessage) {
      return explicitMessage;
    }
    const deliveryStatus = String(item?.delivery_status || "").trim();
    if (deliveryStatus === "sent" || deliveryStatus === "queued") {
      return "초대 메일 발송을 시작했습니다. 메일이 도착하지 않으면 링크 복사로 직접 전달하세요.";
    }
    return "초대 메일 자동 발송에 실패했습니다. 링크와 초기 암호를 직접 전달하세요.";
  }

  function buildInvitationResultMarkup(item, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
      formatInvitationStatusLabel = (value) => String(value ?? ""),
    } = helpers;
    if (!item || typeof item !== "object") {
      return "";
    }
    const displayName = String(item?.display_name || item?.email || "-");
    const email = String(item?.email || "-");
    const role = String(item?.role || "org_member");
    const deliveryStatus = String(item?.delivery_status || "").trim();
    const deliveryMessage = resolveInvitationDeliveryMessage(item);
    const badgeStatus = deliveryStatus || "pending";
    return `
      <article class="org-admin-list-item">
        <div class="org-admin-list-item-head">
          <div>
            <strong>${escapeHtml(displayName)}</strong>
            <p class="mono">${escapeHtml(email)} | ${escapeHtml(formatOrgRoleLabel(role))}</p>
          </div>
          <span class="status-badge status-${escapeHtml(badgeStatus)}">${escapeHtml(formatInvitationStatusLabel(badgeStatus) || badgeStatus)}</span>
        </div>
        <p class="mono">${escapeHtml(deliveryMessage)}</p>
        ${item?.invite_url ? `<p class="mono">초대 링크 ${escapeHtml(item.invite_url)}</p>` : ""}
        ${item?.initial_password ? `<p class="mono">초기 암호 ${escapeHtml(item.initial_password)}</p>` : ""}
        <div class="org-admin-inline-actions">
          <button class="ghost-button" type="button" data-invite-copy="${escapeHtml(item?.invite_url || "")}">링크 복사</button>
        </div>
      </article>
    `;
  }

  function formatAuthAuditSummary(item = {}, helpers = {}) {
    const formatRole = helpers.formatOrgRoleLabel || ((value) => String(value || "").trim() || "-");
    const formatMembershipStatus = helpers.formatMembershipStatusLabel || ((value) => String(value || "").trim() || "-");
    const payload = item && typeof item.payload_json === "object" ? item.payload_json : {};
    const targetType = String(item?.target_type || "").trim();
    const targetId = String(item?.target_id || "").trim();
    switch (String(item?.event_type || "").trim()) {
      case "invite_created":
      case "invite_accepted":
      case "invite_revoked": {
        const bits = [];
        if (payload.email) {
          bits.push(String(payload.email));
        }
        if (payload.role) {
          bits.push(formatRole(payload.role));
        }
        return bits.length ? bits.join(" · ") : "초대 대상 정보 없음";
      }
      case "membership_role_changed":
        if (payload.before_role || payload.after_role) {
          return `${formatRole(payload.before_role || "-")} -> ${formatRole(payload.after_role || "-")}`;
        }
        return "권한 변경";
      case "membership_deactivated":
      case "membership_reactivated":
        if (payload.before_status || payload.after_status) {
          return `${formatMembershipStatus(payload.before_status || "-")} -> ${formatMembershipStatus(payload.after_status || "-")}`;
        }
        return "소속 상태 변경";
      default:
        if (targetType || targetId) {
          return [targetType || "target", targetId || "-"].join(" · ");
        }
        return "세부 정보 없음";
    }
  }

  function buildOrganizationAuditLogMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      formatAuthAuditEventLabel = (value) => String(value ?? ""),
      formatAuthAuditActorLabel = (value) => String(value ?? ""),
    } = helpers;
    const auditLogs = resolveItems(payload, ["auditLogs", "items", "logs"]);
    return buildOrgAdminLogCardMarkup({
      title: "조직 감사 로그",
      kicker: "초대, 수락, 철회, 역할/상태 변경 이력을 최근 순으로 확인합니다.",
      refreshButtonId: "organization-audit-refresh-button",
      loadMoreButtonId: "organization-audit-load-more-button",
      loadingMessage: "조직 감사 로그를 불러오는 중입니다.",
      emptyMessage: "최근 조직 감사 로그가 없습니다.",
      errorMessage: String(payload?.errorMessage || ""),
      loading: Boolean(payload?.loading),
      items: auditLogs,
      visibleCount: payload?.visibleCount,
      canLoadMore: payload?.hasMore,
      bodyMarkup: (visibleItems) => visibleItems.map((item) => `
        <article class="org-admin-list-item">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(formatAuthAuditEventLabel(item?.event_type))}</strong>
              <p class="mono">${escapeHtml(formatAuthAuditActorLabel(item))}</p>
            </div>
            <span class="status-badge status-success">${escapeHtml(formatDate(item?.created_at))}</span>
          </div>
          <p>${escapeHtml(formatAuthAuditSummary(item, helpers))}</p>
          <p class="mono">대상 ${escapeHtml(String(item?.target_type || "-"))}${item?.target_id ? ` · ${escapeHtml(String(item.target_id || ""))}` : ""}</p>
        </article>
      `).join(""),
    }, helpers);
  }

  function formatLoginAuditActorLabel(item = {}) {
    const displayName = String(item?.display_name || "").trim();
    const email = String(item?.user_email || item?.email || "").trim();
    const role = String(item?.user_role || item?.role || "").trim();
    const bits = [];
    if (displayName) {
      bits.push(displayName);
    }
    if (email && email !== displayName) {
      bits.push(email);
    }
    if (role) {
      bits.push(role);
    }
    return bits.length ? bits.join(" · ") : "로그인";
  }

  function formatLoginAuditSummary(item = {}) {
    const bits = [];
    const email = String(item?.user_email || item?.email || "").trim();
    const role = String(item?.user_role || item?.role || "").trim();
    const ipAddress = String(item?.ip_address || "").trim();
    const userAgent = String(item?.user_agent || "").trim();
    if (email) {
      bits.push(email);
    }
    if (role) {
      bits.push(role);
    }
    if (ipAddress) {
      bits.push(`IP ${ipAddress}`);
    }
    if (userAgent) {
      bits.push(userAgent);
    }
    return bits.length ? bits.join(" · ") : "로그인 기록";
  }
  function buildOrganizationMemberSummaryMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      resolveStatusClass = (value) => String(value ?? ""),
      formatAccountStatusLabel = (value) => String(value ?? ""),
      formatMembershipStatusLabel = (value) => String(value ?? ""),
    } = helpers;
    const members = resolveItems(payload, ["members", "items", "organizationMembers"]);
    if (!members.length) {
      return "";
    }
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

  function buildOrganizationMemberListMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      resolveStatusClass = (value) => String(value ?? ""),
      formatAccountStatusLabel = (value) => String(value ?? ""),
      formatMembershipStatusLabel = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
      getRenderableOrgRoleOptions = (currentRole = "") => [currentRole],
      membershipStatusOptions = [],
      isProtectedOrganizationMember = () => false,
      getCurrentAuthLocalUserId = () => "",
    } = helpers;
    const members = resolveItems(payload, ["members", "items", "organizationMembers"]);
    if (!members.length) {
      return "";
    }
    return members.map((member) => {
      const memberId = String(member?.id || "");
      const isSaving = Boolean(payload?.saveStateByUserId?.[memberId] ?? payload?.memberSaveStateByUserId?.[memberId]);
      const isDeleting = Boolean(payload?.deleteStateByUserId?.[memberId] ?? payload?.memberDeleteStateByUserId?.[memberId]);
      const isProtected = Boolean(isProtectedOrganizationMember(member));
      const isSelf = memberId && memberId === getCurrentAuthLocalUserId();
      const roleStatusLocked = isProtected || isSelf;
      const deleteLocked = isProtected || isSelf || isDeleting;
      const hint = isProtected
        ? "부트스트랩/플랫폼 운영자 계정의 권한과 상태는 수정할 수 없습니다."
        : isSelf
        ? "자기 계정의 역할/상태는 이 화면에서 수정할 수 없습니다."
        : "";
      const currentRole = String(member?.role || "org_member");
      const currentMembershipStatus = String(member?.membership_status || member?.status || "active");
      return `
        <article class="org-admin-list-item org-member-card" data-member-id="${escapeHtml(memberId)}">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(member?.display_name || member?.email || "-")}</strong>
              <p class="mono">${escapeHtml(member?.email || "-")}</p>
            </div>
            <div class="org-admin-badge-stack">
              <span class="status-badge status-${escapeHtml(resolveStatusClass(String(member?.account_status || "active")))}">계정 ${escapeHtml(formatAccountStatusLabel(member?.account_status || "active"))}</span>
              <span class="status-badge status-${escapeHtml(resolveStatusClass(String(currentMembershipStatus)))}">소속 ${escapeHtml(formatMembershipStatusLabel(currentMembershipStatus))}</span>
            </div>
          </div>
          <p class="mono">회사 ${escapeHtml(member?.organization_name || "-")} · 현재 역할 ${escapeHtml(formatOrgRoleLabel(member?.role || "-"))}</p>
          <p>휴대폰 ${escapeHtml(member?.mobile_phone || "-")} · 회사 전화 ${escapeHtml(member?.office_phone || "-")}</p>
          <div class="org-member-form-grid">
            <label>
              <span>역할</span>
              <select data-member-field="role" ${roleStatusLocked ? "disabled" : ""}>
                ${getRenderableOrgRoleOptions(currentRole).map((option) => `<option value="${escapeHtml(option)}" ${String(currentRole) === option ? "selected" : ""}>${escapeHtml(formatOrgRoleLabel(option))}</option>`).join("")}
              </select>
            </label>
            <label>
              <span>소속 상태</span>
              <select data-member-field="membership_status" ${roleStatusLocked ? "disabled" : ""}>
                ${membershipStatusOptions.map((option) => `<option value="${escapeHtml(option)}" ${String(currentMembershipStatus) === option ? "selected" : ""}>${escapeHtml(formatMembershipStatusLabel(option))}</option>`).join("")}
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

  function buildDownloadAuditPanelMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
      formatDownloadScopeLabel = (value) => String(value ?? ""),
      formatDownloadFormatLabel = (value) => String(value ?? ""),
      formatDownloadSourcePageLabel = (value) => String(value ?? ""),
    } = helpers;
    const downloadAuditLogs = resolveItems(payload, ["downloadAuditLogs", "items", "logs"]);
    if (!payload?.isAdminMode) {
      return "";
    }
    return buildOrgAdminLogCardMarkup({
      title: "다운로드 이력",
      kicker: "최근 다운로드 파일 이력을 최신 순으로 확인합니다.",
      refreshButtonId: "organization-download-audit-refresh-button",
      loadMoreButtonId: "organization-download-audit-load-more-button",
      loadingMessage: "다운로드 이력을 불러오는 중입니다.",
      emptyMessage: "최근 다운로드 이력이 없습니다.",
      errorMessage: String(payload?.errorMessage || ""),
      loading: Boolean(payload?.loading),
      items: downloadAuditLogs,
      visibleCount: payload?.visibleCount,
      canLoadMore: payload?.hasMore,
      bodyMarkup: (visibleItems) => visibleItems.map((item) => `
        <article class="org-admin-list-item">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(item?.file_name || "-")}</strong>
              <p class="mono">${escapeHtml(item?.user_email || "-")} · ${escapeHtml(formatOrgRoleLabel(item?.user_role || "-"))}</p>
            </div>
            <span class="status-badge status-success">${escapeHtml(formatDate(item?.created_at))}</span>
          </div>
          <p>${escapeHtml(formatDownloadScopeLabel(item?.download_scope || "-"))} · ${escapeHtml(formatDownloadFormatLabel(item?.download_format || "-"))} · ${escapeHtml(formatDownloadSourcePageLabel(item?.source_page || "-"))}</p>
          <p class="mono">${escapeHtml(item?.file_name || "-")}</p>
        </article>
      `).join(""),
    }, helpers);
  }

  function buildLoginAuditPanelMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
    } = helpers;
    const loginAuditLogs = resolveItems(payload, ["loginAuditLogs", "items", "logs"]);
    const actorLabel = helpers.formatLoginAuditActorLabel || formatLoginAuditActorLabel;
    const summaryLabel = helpers.formatLoginAuditSummary || formatLoginAuditSummary;
    if (!payload?.isAdminMode) {
      return "";
    }
    return buildOrgAdminLogCardMarkup({
      title: "로그인 이력",
      kicker: "최근 로그인 성공 기록을 최신 순으로 확인합니다.",
      refreshButtonId: "organization-login-audit-refresh-button",
      loadMoreButtonId: "organization-login-audit-load-more-button",
      loadingMessage: "로그인 이력을 불러오는 중입니다.",
      emptyMessage: "최근 로그인 이력이 없습니다.",
      errorMessage: String(payload?.errorMessage || ""),
      loading: Boolean(payload?.loading),
      items: loginAuditLogs,
      visibleCount: payload?.visibleCount,
      canLoadMore: payload?.hasMore,
      bodyMarkup: (visibleItems) => visibleItems.map((item) => `
        <article class="org-admin-list-item">
          <div class="org-admin-list-item-head">
            <div>
              <strong>${escapeHtml(actorLabel(item))}</strong>
              <p class="mono">${escapeHtml(summaryLabel(item))}</p>
            </div>
            <span class="status-badge status-success">${escapeHtml(formatDate(item?.created_at))}</span>
          </div>
          <p>IP ${escapeHtml(String(item?.ip_address || "-"))}</p>
          <p class="mono">${escapeHtml(String(item?.user_agent || "-"))}</p>
        </article>
      `).join(""),
    }, helpers);
  }
  globalObject.SPMSOrgAdminRuntime = {
    buildOrgPlanSummaryMarkup,
    buildInvitationRoleOptionsMarkup,
    buildInvitationListMarkup,
    buildInvitationResultMarkup,
    formatAuthAuditSummary,
    buildOrganizationAuditLogMarkup,
    buildLoginAuditPanelMarkup,
    buildOrganizationMemberSummaryMarkup,
    buildOrganizationMemberListMarkup,
    buildDownloadAuditPanelMarkup,
  };
})(window);
