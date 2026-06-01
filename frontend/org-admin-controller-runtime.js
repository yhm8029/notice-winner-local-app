export function createOrgAdminControllerRuntime(context = {}) {
  const { deps = {}, locals = {} } = context;

  function formatAuthAuditSummary(item) {
    return deps.requireOrganizationAdminRuntime()?.formatAuthAuditSummary?.(item, {
      formatOrgRoleLabel: deps.formatOrgRoleLabel,
      formatMembershipStatusLabel: deps.formatMembershipStatusLabel,
    }) || "";
  }

  function formatLoginAuditActorLabel(item) {
    const formatRole = deps.formatOrgRoleLabel || ((value) => String(value || "").trim() || "-");
    const displayName = String(item?.display_name || "").trim();
    const email = String(item?.user_email || item?.email || "").trim();
    const role = String(item?.user_role || item?.role || "").trim();
    const parts = [];
    if (displayName) parts.push(displayName);
    if (email && email !== displayName) parts.push(email);
    if (role) parts.push(formatRole(role));
    return parts.length ? parts.join(" 쨌 ") : "정보 없음";
  }

  function formatLoginAuditSummary(item) {
    const formatRole = deps.formatOrgRoleLabel || ((value) => String(value || "").trim() || "-");
    const bits = [];
    const email = String(item?.user_email || item?.email || "").trim();
    const role = String(item?.user_role || item?.role || "").trim();
    const ipAddress = String(item?.ip_address || "").trim();
    const userAgent = String(item?.user_agent || "").trim();
    if (email) bits.push(email);
    if (role) bits.push(formatRole(role));
    if (ipAddress) bits.push(`IP ${ipAddress}`);
    if (userAgent) bits.push(userAgent);
    return bits.length ? bits.join(" 쨌 ") : "로그 기록 없음";
  }

  async function handleInvitationSubmit(event) {
    event.preventDefault();
    const { state, dom, api, flash, setBusy, renderOrganizationAdminPanel, renderInvitationStatus } = deps;
    if (!state.auth.enabled || !state.auth.authorized || !locals.canUseAdminMode() || !dom.invitationForm) return;
    const payload = {
      email: String(dom.invitationEmail?.value || "").trim(),
      display_name: String(dom.invitationDisplayName?.value || "").trim(),
      role: String(dom.invitationRole?.value || "org_member").trim() || "org_member",
      team_name: String(dom.invitationTeamName?.value || "").trim(),
      job_title: String(dom.invitationJobTitle?.value || "").trim(),
      expires_in_days: Number(dom.invitationExpiresInDays?.value || 7) || 7,
    };
    const allowedRoles = locals.getAllowedInvitationRoleOptions();
    const planSummary = locals.getOrganizationPlanSummaryForDisplay();
    const currentEmail = String(state.auth.user?.email || "").trim().toLowerCase();
    if (!allowedRoles.includes(payload.role)) {
      renderInvitationStatus("현재 권한으로는 해당 역할 초대를 만들 수 없습니다.", "error");
      flash("초대 가능한 역할만 선택할 수 있습니다.", "error");
      return;
    }
    if (payload.email && currentEmail && payload.email.toLowerCase() === currentEmail) {
      renderInvitationStatus("현재 로그인한 이메일로는 초대장을 만들 수 없습니다.", "error");
      flash("내 이메일로는 초대할 수 없습니다.", "error");
      dom.invitationEmail?.focus();
      return;
    }
    if (planSummary?.upgrade_required) {
      renderInvitationStatus(planSummary.upgrade_message || "현재 플랜 한도에 도달했습니다.", "error");
      flash(planSummary.upgrade_message || "플랜 한도에 도달했습니다.", "error");
      return;
    }
    state.invitationSaving = true;
    setBusy(dom.invitationSubmitButton, true, "생성 중...");
    try {
      const item = await api("/api/auth/invitations", {
        method: "POST",
        body: JSON.stringify(payload),
        cacheBust: false,
        timeoutMs: 45000,
      });
      dom.invitationForm.reset();
      if (dom.invitationRole) dom.invitationRole.value = "org_member";
      if (dom.invitationExpiresInDays) dom.invitationExpiresInDays.value = "7";
      const deliveryStatus = String(item.delivery_status || "");
      const deliveryStarted = deliveryStatus === "sent" || deliveryStatus === "queued";
      if (typeof deps.upsertOrganizationInvitation === "function") deps.upsertOrganizationInvitation(item);
      else locals.upsertOrganizationInvitation(item);
      renderOrganizationAdminPanel();
      if (!deliveryStarted) await copyInvitationUrl(String(item.invite_url || ""), { renderStatusText: false });
      renderInvitationStatus(
        [
          item.delivery_message || (deliveryStarted
            ? "초대 메일 발송이 시작됐습니다. 메일이 오지 않으면 목록의 링크 복사 버튼으로 직접 전달해 주세요."
            : "초대 메일 발송이 실패했습니다. 링크를 복사해서 직접 전달해 주세요."),
          item.initial_password ? `초기 비밀번호 ${String(item.initial_password || "").trim()}` : "",
        ].filter(Boolean).join(" 쨌 "),
        deliveryStarted ? "" : "error",
      );
      if (typeof deps.scheduleOrganizationInvitationSync === "function") deps.scheduleOrganizationInvitationSync(deliveryStarted ? 2500 : 800);
      else locals.scheduleOrganizationInvitationSync(deliveryStarted ? 2500 : 800);
      flash(deliveryStarted ? "초대를 생성했습니다." : "초대 메일 발송이 실패해서 링크 복사 방식으로 전환했습니다.", deliveryStarted ? "" : "warn");
    } catch (err) {
      renderInvitationStatus(err.message || "초대 링크를 만들지 못했습니다.", "error");
      flash(err.message, "error");
    } finally {
      state.invitationSaving = false;
      setBusy(dom.invitationSubmitButton, false, "초대 링크 생성");
      renderOrganizationAdminPanel();
    }
  }

  async function copyInvitationUrl(inviteUrl, options = {}) {
    const { renderStatusText = false } = options;
    const { flash, navigator, document, window, renderInvitationStatus } = deps;
    const trimmed = String(inviteUrl || "").trim();
    if (!trimmed) {
      flash("복사할 초대 링크가 없습니다.", "warn");
      return;
    }
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(trimmed);
        flash("초대 링크를 복사했습니다.");
        return;
      }
    } catch (_err) {
      // fall through
    }
    try {
      const textarea = document.createElement("textarea");
      textarea.value = trimmed;
      textarea.setAttribute("readonly", "true");
      textarea.style.position = "fixed";
      textarea.style.top = "-1000px";
      textarea.style.left = "-1000px";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      const copied = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (copied) {
        flash("초대 링크를 복사했습니다.");
        return;
      }
    } catch (_err) {
      // fall through
    }
    window.prompt("아래 초대 링크를 복사해 주세요.", trimmed);
    if (renderStatusText) renderInvitationStatus(`초대 링크: ${trimmed}`, "");
    flash("자동 복사가 되지 않아 초대 링크를 직접 복사하도록 표시했습니다.", "warn");
  }

  async function revokeOrganizationInvitation(invitationId) {
    const { api, flash, renderOrganizationAdminPanel } = deps;
    if (!invitationId) return;
    try {
      await api(`/api/auth/invitations/${encodeURIComponent(invitationId)}/revoke`, {
        method: "POST",
        body: JSON.stringify({}),
        cacheBust: false,
        timeoutMs: 15000,
      });
      if (typeof deps.removeOrganizationInvitation === "function") deps.removeOrganizationInvitation(invitationId);
      else locals.removeOrganizationInvitation(invitationId);
      renderOrganizationAdminPanel();
      flash("초대를 취소했습니다.");
      if (typeof deps.scheduleOrganizationInvitationSync === "function") deps.scheduleOrganizationInvitationSync(800);
      else locals.scheduleOrganizationInvitationSync(800);
    } catch (err) {
      flash(err.message, "error");
    }
  }

  async function saveOrganizationMember(userId, article) {
    const { state, api, flash, window, renderOrganizationAdminPanel } = deps;
    if (!userId || !(article instanceof window.HTMLElement)) return;
    const role = String(article.querySelector('[data-member-field="role"]')?.value || "").trim();
    const membershipStatus = String(article.querySelector('[data-member-field="membership_status"]')?.value || "").trim();
    const teamName = String(article.querySelector('[data-member-field="team_name"]')?.value || "").trim();
    const jobTitle = String(article.querySelector('[data-member-field="job_title"]')?.value || "").trim();
    state.memberSaveStateByUserId = { ...state.memberSaveStateByUserId, [userId]: true };
    renderOrganizationAdminPanel();
    try {
      await api(`/api/auth/users/${encodeURIComponent(userId)}`, {
        method: "PATCH",
        body: JSON.stringify({ role, membership_status: membershipStatus, team_name: teamName, job_title: jobTitle }),
        cacheBust: false,
        timeoutMs: 20000,
      });
      flash("사용자 정보를 저장했습니다.");
      await Promise.all([locals.loadOrganizationMembers({ silent: true }), locals.loadOrganizationUsers({ silent: true })]);
    } catch (err) {
      flash(err.message, "error");
    } finally {
      const nextState = { ...state.memberSaveStateByUserId };
      delete nextState[userId];
      state.memberSaveStateByUserId = nextState;
      renderOrganizationAdminPanel();
    }
  }

  async function deleteOrganizationMember(userId, article) {
    const { state, api, flash, window, renderOrganizationAdminPanel } = deps;
    if (!userId || !(article instanceof window.HTMLElement)) return;
    const memberName = String(article.querySelector("strong")?.textContent || "user").trim() || "user";
    if (!window.confirm(`${memberName} 계정을 삭제하면 조직 사용자 정보와 초대, 실행 이력, 영업 담당 흔적까지 함께 제거됩니다. 계속하시겠습니까?`)) return;
    state.memberDeleteStateByUserId = { ...state.memberDeleteStateByUserId, [userId]: true };
    renderOrganizationAdminPanel();
    try {
      await api(`/api/auth/users/${encodeURIComponent(userId)}`, {
        method: "DELETE",
        body: JSON.stringify({}),
        cacheBust: false,
        timeoutMs: 30000,
      });
      flash("계정을 삭제했습니다.");
      await Promise.all([
        locals.loadOrganizationMembers({ silent: true }),
        locals.loadOrganizationUsers({ silent: true }),
        locals.loadOrganizationInvitations({ silent: true }),
        deps.loadSalesClaimSummaryByUser({ silent: true }),
        deps.loadClosedSalesClaims({ silent: true }),
      ]);
    } catch (err) {
      flash(err.message, "error");
    } finally {
      const nextState = { ...state.memberDeleteStateByUserId };
      delete nextState[userId];
      state.memberDeleteStateByUserId = nextState;
      renderOrganizationAdminPanel();
    }
  }

  function bindOrganizationAdminAuditActions(options = {}) {
    const { dom, onDownloadAuditRefresh, onDownloadAuditLoadMore, onLoginAuditRefresh, onLoginAuditLoadMore } = options;
    const panel = dom?.panelOrgAdmin;
    const ElementCtor = deps.window?.Element || globalThis.Element;
    if (!ElementCtor || !panel || panel.__spmsOrganizationAdminAuditActionsBound) return;
    panel.addEventListener("click", (event) => {
      if (!(event.target instanceof ElementCtor)) return;
      const buttonConfigs = [
        ["#organization-download-audit-refresh-button", onDownloadAuditRefresh],
        ["#organization-download-audit-load-more-button", onDownloadAuditLoadMore],
        ["#organization-login-audit-refresh-button", onLoginAuditRefresh],
        ["#organization-login-audit-load-more-button", onLoginAuditLoadMore],
      ];
      for (const [selector, handler] of buttonConfigs) {
        const button = event.target.closest(selector);
        if (button instanceof ElementCtor && panel.contains(button)) {
          handler?.();
          return;
        }
      }
    });
    panel.__spmsOrganizationAdminAuditActionsBound = true;
  }

  function bindListClick(container, selector, resolver) {
    if (!container) return;
    for (const element of container.querySelectorAll(selector)) resolver(element);
  }

  function renderOrganizationAdminPanel() {
    const {
      state,
      dom,
      window,
      document,
      escapeHtml,
      formatDate,
      formatOrgRoleLabel,
      formatInvitationStatusLabel,
      formatAccountStatusLabel,
      formatMembershipStatusLabel,
      resolveStatusClass,
      requireOrganizationAdminRuntime,
      platformAdminAccountRuntime,
      syncPlatformAdminAccountDraftFromForm,
      renderOrgAdminRuntimeReloadFallback,
      membershipStatusOptions,
    } = deps;
    if (
      !dom.panelOrgAdmin
      || !dom.platformAdminAccountPanelSlot
      || !dom.organizationPlanSummary
      || !dom.invitationList
      || !dom.organizationMemberList
      || !dom.organizationMemberSummary
      || !dom.organizationAuditPanelSlot
      || !dom.organizationDownloadAuditPanelSlot
      || !dom.organizationLoginAuditPanelSlot
    ) return;

    if (!locals.canUseAdminMode() || state.uiMode !== "admin") {
      dom.platformAdminAccountPanelSlot.innerHTML = "";
      dom.organizationPlanSummary.innerHTML = '<div class="empty-state">관리자 모드에서 플랜 현황을 확인할 수 있습니다.</div>';
      dom.invitationList.innerHTML = '<div class="empty-state">관리자 모드에서 초대 목록을 확인할 수 있습니다.</div>';
      dom.organizationMemberSummary.innerHTML = '<div class="empty-state">관리자 모드에서 사용자 상태를 확인할 수 있습니다.</div>';
      dom.organizationMemberList.innerHTML = '<div class="empty-state">관리자 모드에서 사용자 관리를 사용할 수 있습니다.</div>';
      dom.organizationAuditPanelSlot.innerHTML = '<div class="empty-state">관리자 모드에서 조직 감사 로그를 확인할 수 있습니다.</div>';
      dom.organizationDownloadAuditPanelSlot.innerHTML = "";
      dom.organizationLoginAuditPanelSlot.innerHTML = "";
      dom.organizationAuditRefreshButton = null;
      dom.organizationAuditLoadMoreButton = null;
      dom.organizationDownloadAuditRefreshButton = null;
      dom.organizationDownloadAuditLoadMoreButton = null;
      dom.organizationLoginAuditRefreshButton = null;
      dom.organizationLoginAuditLoadMoreButton = null;
      state.organizationAuditLogsHasMore = false;
      state.organizationDownloadAuditLogsHasMore = false;
      state.organizationLoginAuditLogsHasMore = false;
      return;
    }

    const existingPlatformAdminAccountForm = dom.platformAdminAccountPanelSlot.querySelector("#platform-admin-account-form");
    if (existingPlatformAdminAccountForm instanceof window.HTMLFormElement && !state.platformAdminAccount.saving) {
      syncPlatformAdminAccountDraftFromForm(existingPlatformAdminAccountForm);
    }

    const orgAdminRuntime = requireOrganizationAdminRuntime();
    if (platformAdminAccountRuntime?.buildPlatformAdminAccountCardMarkup) {
      dom.platformAdminAccountPanelSlot.innerHTML = platformAdminAccountRuntime.buildPlatformAdminAccountCardMarkup(
        {
          enabled: locals.canInviteOrganizationAdmins(),
          currentUserRole: String(state.auth.user?.role || ""),
          saving: state.platformAdminAccount.saving,
          result: state.platformAdminAccount.result,
          draft: state.platformAdminAccount.draft,
        },
        { escapeHtml, formatOrgRoleLabel },
      );
    } else {
      dom.platformAdminAccountPanelSlot.innerHTML = "";
    }

    const platformAdminAccountForm = dom.platformAdminAccountPanelSlot.querySelector("#platform-admin-account-form");
    if (platformAdminAccountForm) {
      platformAdminAccountForm.addEventListener("submit", deps.handlePlatformAdminAccountSubmit || locals.handlePlatformAdminAccountSubmit);
      for (const field of platformAdminAccountForm.querySelectorAll("input, select")) {
        field.addEventListener("input", () => syncPlatformAdminAccountDraftFromForm(platformAdminAccountForm));
        field.addEventListener("change", () => syncPlatformAdminAccountDraftFromForm(platformAdminAccountForm));
      }
    }

    locals.syncInvitationRoleOptions();
    const planSummary = locals.getOrganizationPlanSummaryForDisplay();
    if (state.organizationInvitationsLoading && !planSummary) {
      dom.organizationPlanSummary.innerHTML = '<div class="empty-state">플랜 요약을 불러오는 중입니다.</div>';
    } else if (planSummary) {
      if (orgAdminRuntime?.buildOrgPlanSummaryMarkup) dom.organizationPlanSummary.innerHTML = orgAdminRuntime.buildOrgPlanSummaryMarkup(planSummary, { escapeHtml });
      else renderOrgAdminRuntimeReloadFallback(dom.organizationPlanSummary);
    } else if (state.organizationInvitationsError) {
      dom.organizationPlanSummary.innerHTML = `<div class="empty-state">${escapeHtml(state.organizationInvitationsError)}</div>`;
    } else {
      dom.organizationPlanSummary.innerHTML = '<div class="empty-state">플랜 요약 정보를 아직 불러오지 못했습니다.</div>';
    }

    if (state.organizationInvitationsLoading) {
      dom.invitationList.innerHTML = '<div class="empty-state">초대 목록을 불러오는 중입니다.</div>';
    } else if (state.organizationInvitationsError) {
      dom.invitationList.innerHTML = `<div class="empty-state">${escapeHtml(state.organizationInvitationsError)}</div>`;
    } else if (!state.organizationInvitations.length) {
      dom.invitationList.innerHTML = Number(planSummary?.pending_invite_count || 0) > 0
        ? '<div class="empty-state">현재 권한으로 관리할 수 있는 pending 초대가 없습니다.</div>'
        : '<div class="empty-state">아직 생성된 초대가 없습니다.</div>';
    } else if (orgAdminRuntime?.buildInvitationListMarkup) {
      dom.invitationList.innerHTML = orgAdminRuntime.buildInvitationListMarkup(
        { invitations: state.organizationInvitations, planSummary },
        { escapeHtml, formatOrgRoleLabel, formatDate, formatInvitationStatusLabel },
      );
    } else {
      renderOrgAdminRuntimeReloadFallback(dom.invitationList);
    }

    if (dom.invitationSubmitButton) {
      const inviteBlocked = Boolean(planSummary?.upgrade_required);
      dom.invitationSubmitButton.disabled = state.invitationSaving || inviteBlocked;
      dom.invitationSubmitButton.title = inviteBlocked ? String(planSummary?.upgrade_message || "") : "";
    }

    const auditLimit = Math.max(1, Number(state.organizationAuditLogsLimit || 5) || 5);
    if (orgAdminRuntime?.buildOrganizationAuditLogMarkup) {
      dom.organizationAuditPanelSlot.innerHTML = orgAdminRuntime.buildOrganizationAuditLogMarkup(
        {
          auditLogs: state.organizationAuditLogs,
          loading: state.organizationAuditLogsLoading,
          errorMessage: state.organizationAuditLogsError,
          visibleCount: auditLimit,
          hasMore: state.organizationAuditLogsHasMore,
        },
        { escapeHtml, formatDate, formatAuthAuditEventLabel: locals.formatAuthAuditEventLabel, formatAuthAuditActorLabel: locals.formatAuthAuditActorLabel },
      );
    } else {
      renderOrgAdminRuntimeReloadFallback(dom.organizationAuditPanelSlot);
    }
    dom.organizationAuditRefreshButton = dom.panelOrgAdmin.querySelector("#organization-audit-refresh-button");
    if (dom.organizationAuditRefreshButton) dom.organizationAuditRefreshButton.onclick = () => { void locals.loadOrganizationAuditLogs({}); };
    dom.organizationAuditLoadMoreButton = dom.panelOrgAdmin.querySelector("#organization-audit-load-more-button");
    if (dom.organizationAuditLoadMoreButton) dom.organizationAuditLoadMoreButton.onclick = () => {
      state.organizationAuditLogsLimit = Math.max(5, auditLimit + 5);
      void locals.loadOrganizationAuditLogs({});
    };

    const downloadLimit = Math.max(1, Number(state.organizationDownloadAuditLogsLimit || 5) || 5);
    if (orgAdminRuntime?.buildDownloadAuditPanelMarkup) {
      dom.organizationDownloadAuditPanelSlot.innerHTML = orgAdminRuntime.buildDownloadAuditPanelMarkup(
        {
          isAdminMode: true,
          loading: state.organizationDownloadAuditLogsLoading,
          errorMessage: state.organizationDownloadAuditLogsError,
          downloadAuditLogs: state.organizationDownloadAuditLogs,
          visibleCount: downloadLimit,
          hasMore: state.organizationDownloadAuditLogsHasMore,
        },
        {
          escapeHtml,
          formatDate,
          formatOrgRoleLabel,
          formatDownloadScopeLabel: locals.formatDownloadScopeLabel,
          formatDownloadFormatLabel: locals.formatDownloadFormatLabel,
          formatDownloadSourcePageLabel: locals.formatDownloadSourcePageLabel,
        },
      );
    } else {
      renderOrgAdminRuntimeReloadFallback(dom.organizationDownloadAuditPanelSlot);
    }
    dom.organizationDownloadAuditRefreshButton = dom.panelOrgAdmin.querySelector("#organization-download-audit-refresh-button");
    if (dom.organizationDownloadAuditRefreshButton) dom.organizationDownloadAuditRefreshButton.onclick = () => { void locals.loadOrganizationDownloadAuditLogs({}); };
    dom.organizationDownloadAuditLoadMoreButton = dom.panelOrgAdmin.querySelector("#organization-download-audit-load-more-button");
    if (dom.organizationDownloadAuditLoadMoreButton) dom.organizationDownloadAuditLoadMoreButton.onclick = () => {
      state.organizationDownloadAuditLogsLimit = Math.max(5, downloadLimit + 5);
      void locals.loadOrganizationDownloadAuditLogs({});
    };

    const loginLimit = Math.max(1, Number(state.organizationLoginAuditLogsLimit || 5) || 5);
    if (orgAdminRuntime?.buildLoginAuditPanelMarkup) {
      dom.organizationLoginAuditPanelSlot.innerHTML = orgAdminRuntime.buildLoginAuditPanelMarkup(
        {
          isAdminMode: true,
          loading: state.organizationLoginAuditLogsLoading,
          errorMessage: state.organizationLoginAuditLogsError,
          loginAuditLogs: state.organizationLoginAuditLogs,
          visibleCount: loginLimit,
          hasMore: state.organizationLoginAuditLogsHasMore,
        },
        { escapeHtml, formatDate },
      );
    } else {
      renderOrgAdminRuntimeReloadFallback(dom.organizationLoginAuditPanelSlot);
    }
    dom.organizationLoginAuditRefreshButton = dom.panelOrgAdmin.querySelector("#organization-login-audit-refresh-button");
    if (dom.organizationLoginAuditRefreshButton) dom.organizationLoginAuditRefreshButton.onclick = () => { void locals.loadOrganizationLoginAuditLogs({}); };
    dom.organizationLoginAuditLoadMoreButton = dom.panelOrgAdmin.querySelector("#organization-login-audit-load-more-button");
    if (dom.organizationLoginAuditLoadMoreButton) dom.organizationLoginAuditLoadMoreButton.onclick = () => {
      state.organizationLoginAuditLogsLimit = Math.max(5, loginLimit + 5);
      void locals.loadOrganizationLoginAuditLogs({});
    };

    if (state.organizationMembersLoading) {
      dom.organizationMemberSummary.innerHTML = '<div class="empty-state">사용자 상태 요약을 불러오는 중입니다.</div>';
      dom.organizationMemberList.innerHTML = '<div class="empty-state">사용자 목록을 불러오는 중입니다.</div>';
    } else if (state.organizationMembersError) {
      dom.organizationMemberSummary.innerHTML = `<div class="empty-state">${escapeHtml(state.organizationMembersError)}</div>`;
      dom.organizationMemberList.innerHTML = `<div class="empty-state">${escapeHtml(state.organizationMembersError)}</div>`;
    } else if (!state.organizationMembers.length) {
      dom.organizationMemberSummary.innerHTML = '<div class="empty-state">등록된 사용자가 없습니다.</div>';
      dom.organizationMemberList.innerHTML = '<div class="empty-state">등록된 사용자가 없습니다.</div>';
    } else {
      const sortedMembers = [...state.organizationMembers].sort((left, right) => {
        const leftActive = String(left.membership_status || left.status || "active") === "active" ? 0 : 1;
        const rightActive = String(right.membership_status || right.status || "active") === "active" ? 0 : 1;
        if (leftActive !== rightActive) return leftActive - rightActive;
        return String(left.display_name || left.email || "").localeCompare(String(right.display_name || right.email || ""), "ko");
      });
      if (orgAdminRuntime?.buildOrganizationMemberSummaryMarkup) {
        dom.organizationMemberSummary.innerHTML = orgAdminRuntime.buildOrganizationMemberSummaryMarkup(
          { members: sortedMembers },
          { escapeHtml, resolveStatusClass, formatAccountStatusLabel, formatMembershipStatusLabel },
        );
      } else {
        renderOrgAdminRuntimeReloadFallback(dom.organizationMemberSummary);
      }
      if (orgAdminRuntime?.buildOrganizationMemberListMarkup) {
        dom.organizationMemberList.innerHTML = orgAdminRuntime.buildOrganizationMemberListMarkup(
          { members: sortedMembers, memberSaveStateByUserId: state.memberSaveStateByUserId, memberDeleteStateByUserId: state.memberDeleteStateByUserId },
          {
            escapeHtml,
            resolveStatusClass,
            formatAccountStatusLabel,
            formatMembershipStatusLabel,
            formatOrgRoleLabel,
            getRenderableOrgRoleOptions: locals.getRenderableOrgRoleOptions,
            membershipStatusOptions,
            isProtectedOrganizationMember: locals.isProtectedOrganizationMember,
            getCurrentAuthLocalUserId: locals.getCurrentAuthLocalUserId,
          },
        );
      } else {
        renderOrgAdminRuntimeReloadFallback(dom.organizationMemberList);
      }
    }

    bindListClick(dom.invitationList, "[data-invite-copy]", (button) => {
      button.addEventListener("click", () => void copyInvitationUrl(button.getAttribute("data-invite-copy") || "", { renderStatusText: true }));
    });
    bindListClick(dom.invitationList, "[data-invite-revoke]", (button) => {
      button.addEventListener("click", () => {
        const invitationId = button.getAttribute("data-invite-revoke") || "";
        if (invitationId) void revokeOrganizationInvitation(invitationId);
      });
    });
    bindListClick(dom.organizationMemberList, "[data-member-save]", (button) => {
      button.addEventListener("click", () => {
        const article = button.closest("[data-member-id]");
        const userId = button.getAttribute("data-member-save") || "";
        if (article instanceof window.HTMLElement && userId) void saveOrganizationMember(userId, article);
      });
    });
    bindListClick(dom.organizationMemberList, "[data-member-delete]", (button) => {
      button.addEventListener("click", () => {
        const article = button.closest("[data-member-id]");
        const userId = button.getAttribute("data-member-delete") || "";
        if (article instanceof window.HTMLElement && userId) void deleteOrganizationMember(userId, article);
      });
    });

    if (locals.canManagePlatformAdminAccounts()) {
      for (const article of dom.organizationMemberList.querySelectorAll("[data-member-id]")) {
        if (!(article instanceof window.HTMLElement)) continue;
        const userId = String(article.getAttribute("data-member-id") || "").trim();
        if (!userId) continue;
        const member = state.organizationMembers.find((item) => String(item?.id || "").trim() === userId);
        if (!member || locals.isProtectedOrganizationMember(member) || userId === locals.getCurrentAuthLocalUserId()) continue;
        const buttonRow = article.querySelector(".org-admin-inline-button-row");
        if (!(buttonRow instanceof window.HTMLElement)) continue;
        const resetButton = document.createElement("button");
        resetButton.type = "button";
        resetButton.className = "ghost-button";
        resetButton.dataset.memberPasswordReset = userId;
        resetButton.textContent = state.platformAdminAccount.resetStateByUserId[userId] ? "재설정 중..." : "비밀번호 재설정";
        resetButton.disabled = Boolean(state.platformAdminAccount.resetStateByUserId[userId]);
        resetButton.addEventListener("click", () => { void locals.resetOrganizationMemberPassword(userId, article); });
        buttonRow.insertBefore(resetButton, buttonRow.firstChild);
      }
    }
  }

  return {
    handleInvitationSubmit,
    copyInvitationUrl,
    revokeOrganizationInvitation,
    saveOrganizationMember,
    deleteOrganizationMember,
    bindOrganizationAdminAuditActions,
    renderOrganizationAdminPanel,
  };
}
