const ORG_ROLE_OPTIONS = ["org_admin", "org_member"];
const orgAdminControllerRuntimeState = { factory: null, loading: null };

if (typeof document !== "undefined") {
  orgAdminControllerRuntimeState.loading = import("./org-admin-controller-runtime.js")
    .then((mod) => {
      if (typeof mod.createOrgAdminControllerRuntime === "function") {
        orgAdminControllerRuntimeState.factory = mod.createOrgAdminControllerRuntime;
      }
      return mod;
    })
    .catch(() => null);
}

export function createOrgAdminController(deps = {}) {
  let extractedRuntime = null;
  const makeConsoleLoader = (methodName) => async ({ silent = false } = {}) => callConsoleDataRuntime(methodName, { silent });

  function callConsoleDataRuntime(methodName, options) {
    return deps.requireConsoleDataRuntime()[methodName](deps.getConsoleDataRuntimeDeps(), options);
  }

  function canUseAdminMode() {
    if (typeof deps.canUseAdminMode === "function") return deps.canUseAdminMode();
    if (!deps.state.auth.enabled) return true;
    return ["platform_admin", "org_admin"].includes(String(deps.state.auth.user?.role || "").trim());
  }

  function mergeOrganizationInvitationItem(existingItem, nextItem) {
    const merged = {
      ...(existingItem && typeof existingItem === "object" ? existingItem : {}),
      ...(nextItem && typeof nextItem === "object" ? nextItem : {}),
    };
    for (const key of ["invite_url", "delivery_status", "delivery_message", "initial_password"]) {
      if (!String(nextItem?.[key] || "").trim()) merged[key] = existingItem?.[key] || "";
    }
    return merged;
  }

  function mergeOrganizationInvitations(items, existingItems = deps.state.organizationInvitations) {
    const existingById = new Map(
      (Array.isArray(existingItems) ? existingItems : []).filter((item) => item && item.id).map((item) => [String(item.id), item]),
    );
    return (Array.isArray(items) ? items : []).map((item) => mergeOrganizationInvitationItem(existingById.get(String(item?.id || "")), item));
  }

  function upsertOrganizationInvitation(item) {
    if (!item?.id) return;
    const invitationId = String(item.id);
    const existingItem = deps.state.organizationInvitations.find((invitation) => String(invitation.id) === invitationId);
    const mergedItem = mergeOrganizationInvitationItem(existingItem, item);
    deps.state.organizationInvitations = [mergedItem, ...deps.state.organizationInvitations.filter((existing) => String(existing.id) !== invitationId)];
  }

  function removeOrganizationInvitation(invitationId) {
    const targetId = String(invitationId || "");
    if (!targetId) return;
    deps.state.organizationInvitations = deps.state.organizationInvitations.filter((item) => String(item.id) !== targetId);
  }

  function scheduleOrganizationInvitationSync(delayMs = 1500) {
    if (deps.state.organizationInvitationSyncHandle) deps.window.clearTimeout(deps.state.organizationInvitationSyncHandle);
    deps.state.organizationInvitationSyncHandle = deps.window.setTimeout(() => {
      deps.state.organizationInvitationSyncHandle = 0;
      void loadOrganizationInvitations({ silent: true });
    }, delayMs);
  }

  function getRenderableOrgRoleOptions(currentRole = "") {
    const normalizedCurrentRole = String(currentRole || "").trim();
    return normalizedCurrentRole && !ORG_ROLE_OPTIONS.includes(normalizedCurrentRole) ? [normalizedCurrentRole, ...ORG_ROLE_OPTIONS] : [...ORG_ROLE_OPTIONS];
  }

  function getCurrentAuthLocalUserId() {
    return String(deps.state.auth.user?.local_user_id || deps.state.auth.user?.auth_user_id || "").trim();
  }

  function isProtectedOrganizationMember(member) {
    const globalRole = String(member?.global_role || "").trim().toLowerCase();
    const email = String(member?.email || "").trim().toLowerCase();
    return globalRole === "platform_admin" || (deps.state.auth.bootstrapEmail && email === deps.state.auth.bootstrapEmail);
  }

  function canInviteOrganizationAdmins() {
    return String(deps.state.auth.user?.role || "").trim() === "platform_admin";
  }

  function canManagePlatformAdminAccounts() {
    return typeof deps.canManagePlatformAdminAccounts === "function" ? deps.canManagePlatformAdminAccounts() : false;
  }

  function getAllowedInvitationRoleOptions() {
    return canInviteOrganizationAdmins() ? ["org_member", "org_admin"] : ["org_member"];
  }

  function syncInvitationRoleOptions() {
    if (typeof deps.syncInvitationRoleOptions === "function" && deps.syncInvitationRoleOptions !== syncInvitationRoleOptions) {
      return deps.syncInvitationRoleOptions();
    }
    if (!deps.dom.invitationRole) return;
    const allowedRoles = getAllowedInvitationRoleOptions();
    const currentValue = String(deps.dom.invitationRole.value || "org_member").trim();
    deps.dom.invitationRole.innerHTML = deps.requireOrganizationAdminRuntime().buildInvitationRoleOptionsMarkup(allowedRoles, {
      escapeHtml: deps.escapeHtml,
      formatOrgRoleLabel: deps.formatOrgRoleLabel,
    });
    deps.dom.invitationRole.value = allowedRoles.includes(currentValue) ? currentValue : allowedRoles[0];
  }

  function getOrganizationPlanSummaryForDisplay() {
    if (typeof deps.getOrganizationPlanSummaryForDisplay === "function") return deps.getOrganizationPlanSummaryForDisplay();
    if (!deps.state.organizationPlanSummary || typeof deps.state.organizationPlanSummary !== "object") return null;
    const summary = { ...deps.state.organizationPlanSummary };
    const activeUserLimit = Math.max(0, Number(summary.active_user_limit || 0));
    const pendingInviteLimit = Math.max(0, Number(summary.pending_invite_limit || 0));
    const activeUserCount = Math.max(0, Number(summary.active_user_count || 0));
    const pendingInviteCount = Math.max(0, Number(summary.pending_invite_count || 0));
    const activeUserLimitReached = activeUserLimit > 0 && activeUserCount >= activeUserLimit;
    const pendingInviteLimitReached = pendingInviteCount >= pendingInviteLimit;
    return {
      ...summary,
      plan_code: String(summary.plan_code || "A").trim() || "A",
      plan_label: String(summary.plan_label || "").trim() || `플랜 ${String(summary.plan_code || "A").trim() || "A"}`,
      active_user_limit: activeUserLimit,
      pending_invite_limit: pendingInviteLimit,
      active_user_count: activeUserCount,
      pending_invite_count: pendingInviteCount,
      remaining_active_user_slots: Math.max(0, activeUserLimit - activeUserCount),
      remaining_pending_invite_slots: Math.max(0, pendingInviteLimit - pendingInviteCount),
      active_user_limit_reached: activeUserLimitReached,
      pending_invite_limit_reached: pendingInviteLimitReached,
      upgrade_required: activeUserLimitReached || pendingInviteLimitReached,
      upgrade_message: activeUserLimitReached || pendingInviteLimitReached
        ? String(summary.upgrade_message || "현재 플랜 한도에 도달했습니다. 관리자에게 문의해 주세요.").trim()
        : "",
    };
  }

  function formatAuthAuditEventLabel(eventType) {
    switch (String(eventType || "").trim()) {
      case "invite_created": return "초대 생성";
      case "invite_accepted": return "초대 수락";
      case "invite_revoked": return "초대 취소";
      case "membership_role_changed": return "초대 취소";
      case "membership_deactivated": return "소속 비활성화";
      case "membership_reactivated": return "소속 활성화";
      default: return String(eventType || "").trim() || "-";
    }
  }

  function formatAuthAuditActorLabel(item) {
    const displayName = String(item?.actor_display_name || "").trim();
    const email = String(item?.actor_email || "").trim();
    const role = String(item?.actor_role || "").trim();
    const parts = [];
    if (displayName) parts.push(displayName);
    if (email && email !== displayName) parts.push(email);
    if (role) parts.push(deps.formatOrgRoleLabel(role));
    return parts.length ? parts.join(" 쨌 ") : "정보 없음";
  }

  function formatDownloadScopeLabel(value) { return String(value || "").trim() || "-"; }
  function formatDownloadFormatLabel(value) { return String(value || "").trim() || "-"; }
  function formatDownloadSourcePageLabel(value) { return String(value || "").trim() || "-"; }

  const loadOrganizationUsers = makeConsoleLoader("loadOrganizationUsers");
  const loadOrganizationMembers = makeConsoleLoader("loadOrganizationMembers");
  const loadOrganizationInvitations = makeConsoleLoader("loadOrganizationInvitations");
  const loadOrganizationAuditLogs = makeConsoleLoader("loadOrganizationAuditLogs");
  const loadOrganizationDownloadAuditLogs = makeConsoleLoader("loadOrganizationDownloadAuditLogs");
  const loadOrganizationLoginAuditLogs = makeConsoleLoader("loadOrganizationLoginAuditLogs");
  function loadOrganizationAdminData({ silent = false, force = false } = {}) {
    return callConsoleDataRuntime("loadOrganizationAdminData", { silent, force });
  }

  function createEmptyPlatformAdminAccountDraft() {
    return { email: "", display_name: "", role: "org_member", password: "" };
  }

  function normalizePlatformAdminAccountDraft(draft) {
    const source = draft && typeof draft === "object" ? draft : {};
    return {
      email: String(source.email || ""),
      display_name: String(source.display_name || ""),
      role: String(source.role || "org_member").trim() || "org_member",
      password: String(source.password || ""),
    };
  }

  function getAllowedPlatformAdminAccountRoleOptions() {
    return canInviteOrganizationAdmins() ? ["org_member", "org_admin"] : ["org_member"];
  }

  function getExtractedRuntime() {
    if (extractedRuntime) return extractedRuntime;
    const factory = orgAdminControllerRuntimeState.factory;
    if (typeof factory !== "function") return null;
    extractedRuntime = factory({
      deps,
      locals: {
        canUseAdminMode,
        upsertOrganizationInvitation,
        removeOrganizationInvitation,
        scheduleOrganizationInvitationSync,
        getRenderableOrgRoleOptions,
        getCurrentAuthLocalUserId,
        isProtectedOrganizationMember,
        canInviteOrganizationAdmins,
        canManagePlatformAdminAccounts,
        getAllowedInvitationRoleOptions,
        syncInvitationRoleOptions,
        getOrganizationPlanSummaryForDisplay,
        formatAuthAuditEventLabel,
        formatAuthAuditActorLabel,
        formatDownloadScopeLabel,
        formatDownloadFormatLabel,
        formatDownloadSourcePageLabel,
        loadOrganizationUsers,
        loadOrganizationMembers,
        loadOrganizationInvitations,
        loadOrganizationAuditLogs,
        loadOrganizationDownloadAuditLogs,
        loadOrganizationLoginAuditLogs,
        handlePlatformAdminAccountSubmit,
        resetOrganizationMemberPassword,
      },
    });
    return extractedRuntime;
  }

  async function waitForExtractedRuntime() {
    if (getExtractedRuntime()) return extractedRuntime;
    if (!orgAdminControllerRuntimeState.loading) return null;
    await orgAdminControllerRuntimeState.loading;
    return getExtractedRuntime();
  }

  async function handlePlatformAdminAccountSubmit(event) {
    event.preventDefault();
    const {
      state,
      api,
      flash,
      renderOrganizationAdminPanel,
      loadOrganizationMembers: reloadOrganizationMembers,
      loadOrganizationUsers: reloadOrganizationUsers,
      loadOrganizationAuditLogs: reloadOrganizationAuditLogs,
    } = deps;
    if (!state.auth.enabled || !state.auth.authorized || !canManagePlatformAdminAccounts()) return;
    const FormElementCtor = deps.window?.HTMLFormElement || globalThis.HTMLFormElement;
    if (!(event.currentTarget instanceof FormElementCtor)) return;
    const FormDataCtor = deps.window?.FormData || globalThis.FormData;
    const data = new FormDataCtor(event.currentTarget);
    const payload = {
      email: String(data.get("email") || "").trim(),
      display_name: String(data.get("display_name") || "").trim(),
      role: String(data.get("role") || "org_member").trim() || "org_member",
      password: String(data.get("password") || ""),
    };
    state.platformAdminAccount.draft = normalizePlatformAdminAccountDraft(payload);
    if (!getAllowedPlatformAdminAccountRoleOptions().includes(payload.role)) {
      flash("이 화면에서는 해당 역할 계정을 만들 수 없습니다.", "error");
      return;
    }
    state.platformAdminAccount.saving = true;
    renderOrganizationAdminPanel();
    try {
      const item = await api("/api/admin/accounts", {
        method: "POST",
        body: JSON.stringify(payload),
        cacheBust: false,
        timeoutMs: 20000,
      });
      state.platformAdminAccount.result = item;
      state.platformAdminAccount.draft = createEmptyPlatformAdminAccountDraft();
      flash("계정을 생성했습니다.");
      await Promise.all([
        reloadOrganizationMembers({ silent: true }),
        reloadOrganizationUsers({ silent: true }),
        reloadOrganizationAuditLogs({ silent: true }),
      ]);
    } catch (err) {
      flash(err.message, "error");
    } finally {
      state.platformAdminAccount.saving = false;
      renderOrganizationAdminPanel();
    }
  }

  async function handleInvitationSubmit(event) {
    return (await waitForExtractedRuntime())?.handleInvitationSubmit(event);
  }

  async function copyInvitationUrl(inviteUrl, options = {}) {
    return (await waitForExtractedRuntime())?.copyInvitationUrl(inviteUrl, options);
  }

  async function revokeOrganizationInvitation(invitationId) {
    return (await waitForExtractedRuntime())?.revokeOrganizationInvitation(invitationId);
  }

  async function saveOrganizationMember(userId, article) {
    return (await waitForExtractedRuntime())?.saveOrganizationMember(userId, article);
  }

  async function deleteOrganizationMember(userId, article) {
    return (await waitForExtractedRuntime())?.deleteOrganizationMember(userId, article);
  }

  async function resetOrganizationMemberPassword(userId, article) {
    const { state, api, flash, window, renderOrganizationAdminPanel } = deps;
    if (!userId || !(article instanceof window.HTMLElement) || !canManagePlatformAdminAccounts()) return;
    const memberName = String(article.querySelector("strong")?.textContent || "user").trim() || "user";
    const password = window.prompt(`${memberName} 계정의 새 비밀번호를 입력하세요.`, "");
    if (password == null) return;
    const normalizedPassword = String(password).trim();
    if (!normalizedPassword) {
      flash("비밀번호를 입력해야 합니다.", "error");
      return;
    }
    state.platformAdminAccount.resetStateByUserId = { ...state.platformAdminAccount.resetStateByUserId, [userId]: true };
    renderOrganizationAdminPanel();
    try {
      const result = await api(`/api/admin/accounts/${encodeURIComponent(userId)}/password-reset`, {
        method: "POST",
        body: JSON.stringify({ password: normalizedPassword }),
        cacheBust: false,
        timeoutMs: 20000,
      });
      flash(result.message || "비밀번호를 재설정했습니다.");
      await Promise.all([loadOrganizationMembers({ silent: true }), loadOrganizationAuditLogs({ silent: true })]);
    } catch (err) {
      flash(err.message, "error");
    } finally {
      const nextState = { ...state.platformAdminAccount.resetStateByUserId };
      delete nextState[userId];
      state.platformAdminAccount.resetStateByUserId = nextState;
      renderOrganizationAdminPanel();
    }
  }

  function bindOrganizationAdminAuditActions(options = {}) {
    const runtime = getExtractedRuntime();
    if (runtime?.bindOrganizationAdminAuditActions) return runtime.bindOrganizationAdminAuditActions(options);
    if (orgAdminControllerRuntimeState.loading) {
      void orgAdminControllerRuntimeState.loading.then(() => getExtractedRuntime()?.bindOrganizationAdminAuditActions(options));
    }
    return undefined;
  }

  function renderOrganizationAdminPanel() {
    const runtime = getExtractedRuntime();
    if (runtime?.renderOrganizationAdminPanel) return runtime.renderOrganizationAdminPanel();
    if (orgAdminControllerRuntimeState.loading) {
      void orgAdminControllerRuntimeState.loading.then(() => getExtractedRuntime()?.renderOrganizationAdminPanel());
    }
    return undefined;
  }

  return {
    mergeOrganizationInvitationItem,
    mergeOrganizationInvitations,
    upsertOrganizationInvitation,
    removeOrganizationInvitation,
    scheduleOrganizationInvitationSync,
    getRenderableOrgRoleOptions,
    getCurrentAuthLocalUserId,
    isProtectedOrganizationMember,
    canInviteOrganizationAdmins,
    getAllowedInvitationRoleOptions,
    syncInvitationRoleOptions,
    getOrganizationPlanSummaryForDisplay,
    formatAuthAuditEventLabel,
    formatAuthAuditActorLabel,
    formatDownloadScopeLabel,
    formatDownloadFormatLabel,
    formatDownloadSourcePageLabel,
    loadOrganizationUsers,
    loadOrganizationMembers,
    loadOrganizationInvitations,
    loadOrganizationAuditLogs,
    loadOrganizationDownloadAuditLogs,
    loadOrganizationLoginAuditLogs,
    bindOrganizationAdminAuditActions,
    loadOrganizationAdminData,
    handlePlatformAdminAccountSubmit,
    handleInvitationSubmit,
    copyInvitationUrl,
    revokeOrganizationInvitation,
    saveOrganizationMember,
    deleteOrganizationMember,
    resetOrganizationMemberPassword,
    renderOrganizationAdminPanel,
  };
}

if (typeof window !== "undefined") {
  window.ORG_ADMIN_CONTROLLER = window.ORG_ADMIN_CONTROLLER || {};
  window.ORG_ADMIN_CONTROLLER.createOrgAdminController = createOrgAdminController;
} else if (typeof globalThis !== "undefined") {
  globalThis.ORG_ADMIN_CONTROLLER = globalThis.ORG_ADMIN_CONTROLLER || {};
  globalThis.ORG_ADMIN_CONTROLLER.createOrgAdminController = createOrgAdminController;
}
