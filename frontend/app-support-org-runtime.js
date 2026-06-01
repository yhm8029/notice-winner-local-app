(function attachAppSupportOrgRuntime(global) {
  const SHELL_RUNTIME = global.SPMSAppShellRuntime || null;
  const ADMIN_SUPPORT_RUNTIME = global.SPMSAppSupportAdminRuntime || null;
  const ORG_ROLE_LABELS = SHELL_RUNTIME?.ORG_ROLE_LABELS || {
    platform_admin: "platform_admin",
    org_admin: "org_admin",
    org_member: "org_member",
    admin: "admin",
    member: "member",
  };
  const INVITATION_STATUS_LABELS = SHELL_RUNTIME?.INVITATION_STATUS_LABELS || {
    pending: "pending",
    accepted: "accepted",
    expired: "expired",
    revoked: "revoked",
  };
  const CONTACT_RESOLUTION_STATUS_LABELS = SHELL_RUNTIME?.CONTACT_RESOLUTION_STATUS_LABELS || {
    resolved: "resolved",
    review: "review",
    no_owner_candidate: "no_owner_candidate",
    missing: "missing",
  };
  const ACCOUNT_STATUS_LABELS = SHELL_RUNTIME?.ACCOUNT_STATUS_LABELS || {
    active: "active",
    inactive: "inactive",
    deactivated: "deactivated",
  };
  const MEMBERSHIP_STATUS_LABELS = SHELL_RUNTIME?.MEMBERSHIP_STATUS_LABELS || {
    active: "active",
    inactive: "inactive",
    deactivated: "deactivated",
  };

  function formatOrgRoleLabel(role) {
    const raw = String(role || "").trim();
    return ORG_ROLE_LABELS[raw] || raw || "-";
  }

  function formatInvitationStatusLabel(status) {
    const raw = String(status || "").trim();
    return INVITATION_STATUS_LABELS[raw] || raw || "-";
  }

  function formatContactResolutionStatusLabel(status) {
    const raw = String(status || "").trim();
    return CONTACT_RESOLUTION_STATUS_LABELS[raw] || raw || "-";
  }

  function formatContactResolutionReasonLabel(reason) {
    const raw = String(reason || "").trim();
    if (!raw) {
      return "-";
    }
    return raw.replace(/_/g, " ");
  }

  function formatAccountStatusLabel(status) {
    const raw = String(status || "").trim();
    return ACCOUNT_STATUS_LABELS[raw] || raw || "-";
  }

  function formatMembershipStatusLabel(status) {
    const raw = String(status || "").trim();
    return MEMBERSHIP_STATUS_LABELS[raw] || raw || "-";
  }

  function resolveStatusClass(status) {
    const raw = String(status || "").trim().toLowerCase();
    if (raw === "active") {
      return "success";
    }
    if (raw === "inactive") {
      return "queued";
    }
    if (raw === "deactivated") {
      return "failed";
    }
    return raw || "queued";
  }

  function isAdminRole(role) {
    return ["platform_admin", "org_admin"].includes(String(role || "").trim());
  }

  function canUseAdminMode(state) {
    if (!state?.auth?.enabled) {
      return true;
    }
    return isAdminRole(state.auth.user?.role);
  }

  function canLoadProtectedConsoleData(state) {
    if (state?.auth?.checking) {
      return false;
    }
    if (!state?.auth?.enabled) {
      return true;
    }
    return Boolean(state.auth.authenticated && state.auth.authorized);
  }

  function getMissingReportDownloadLimit(state) {
    const summaryCount = Number(state?.trackerMissingReport?.summary?.missing_entries || 0);
    if (summaryCount > 0) {
      return Math.min(summaryCount, 500);
    }
    return 500;
  }

  function createSalesStateHelpers(options = {}) {
    const {
      state = {},
      isAdminRole = () => false,
      buildUserSalesProjectFactsMarkup = () => "",
      formatEokValue = (value) => String(value ?? ""),
    } = options;

    function getVisibleSalesProjectIds(entries = state.trackerEntries) {
      return [...new Set(
        (entries || [])
          .map((entry) => String(entry.project_id || "").trim())
          .filter(Boolean)
      )];
    }

    function getSalesClaimForProject(projectId) {
      if (!projectId) {
        return null;
      }
      const key = String(projectId);
      return (
        state.salesClaimsByProjectId[key]
        || state.mySalesClaims.find((claim) => String(claim?.project_id || "") === key)
        || state.companySalesClaims.find((claim) => String(claim?.project_id || "") === key)
        || null
      );
    }

    function getTrackerProjectSnapshot(projectId) {
      const key = String(projectId || "").trim();
      if (!key) {
        return null;
      }
      const summaryEntry = state.trackerEntries.find((entry) => String(entry.project_id || "").trim() === key);
      if (summaryEntry) {
        return summaryEntry;
      }
      if (state.selectedEntry && String(state.selectedEntry.project_id || "").trim() === key) {
        return state.selectedEntry;
      }
      return null;
    }

    function renderUserSalesProjectFacts(snapshot, estimatedAmountText = "-") {
      return buildUserSalesProjectFactsMarkup(snapshot, estimatedAmountText);
    }

    function isCurrentUserClaimOwner(claim) {
      if (!claim || !state.auth.user) {
        return false;
      }
      const currentUserId = String(state.auth.user.local_user_id || "").trim();
      const currentEmail = String(state.auth.user.email || "").trim().toLowerCase();
      if (currentUserId && String(claim.owner_user_id || "").trim() === currentUserId) {
        return true;
      }
      return Boolean(currentEmail && String(claim.owner_email || "").trim().toLowerCase() === currentEmail);
    }

    function canCurrentUserForceRelease() {
      return isAdminRole(state.auth.user?.role);
    }

    function canCurrentUserManageClaim(claim) {
      return isCurrentUserClaimOwner(claim) || canCurrentUserForceRelease();
    }

    function isActiveSalesClaim(claim) {
      return Boolean(claim && claim.is_active && String(claim.claim_status || "active") === "active");
    }

    function getOrganizationTransferTargets(claim) {
      const currentUserId = String(claim?.owner_user_id || "").trim();
      const currentEmail = String(claim?.owner_email || "").trim().toLowerCase();
      return (state.organizationUsers || []).filter((item) => {
        const itemId = String(item.id || "").trim();
        const itemEmail = String(item.email || "").trim().toLowerCase();
        if (currentUserId && itemId === currentUserId) {
          return false;
        }
        if (currentEmail && itemEmail === currentEmail) {
          return false;
        }
        return String(item.status || "active") === "active";
      });
    }

    function getSalesNoteDraft(projectId) {
      const key = String(projectId || "").trim();
      if (!key) {
        return "";
      }
      if (Object.prototype.hasOwnProperty.call(state.salesClaimDrafts, key)) {
        return state.salesClaimDrafts[key];
      }
      return "";
    }

    function setSalesNoteDraft(projectId, value) {
      const key = String(projectId || "").trim();
      if (!key) {
        return;
      }
      state.salesClaimDrafts[key] = String(value || "");
    }

    function upsertSalesClaim(claim) {
      const key = String(claim?.project_id || "").trim();
      if (!key) {
        return;
      }
      if (!claim.is_active) {
        delete state.salesClaimsByProjectId[key];
        delete state.salesClaimDrafts[key];
        return;
      }
      state.salesClaimsByProjectId[key] = claim;
    }

    function replaceVisibleSalesClaims(items) {
      const previousDrafts = { ...state.salesClaimDrafts };
      const visibleKeys = new Set(getVisibleSalesProjectIds());
      for (const key of visibleKeys) {
        delete state.salesClaimsByProjectId[key];
        delete state.salesClaimDrafts[key];
      }
      for (const item of items || []) {
        upsertSalesClaim(item);
        const key = String(item.project_id || "").trim();
        if (!key) {
          continue;
        }
        if (Object.prototype.hasOwnProperty.call(previousDrafts, key) && isCurrentUserClaimOwner(item)) {
          state.salesClaimDrafts[key] = previousDrafts[key];
        }
      }
    }

    function mergeActiveSalesClaims(items) {
      for (const item of items || []) {
        upsertSalesClaim(item);
      }
    }

    function formatShortDateTime(value) {
      if (!value) {
        return "-";
      }
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) {
        return String(value);
      }
      const year = parsed.getFullYear();
      const month = String(parsed.getMonth() + 1).padStart(2, "0");
      const day = String(parsed.getDate()).padStart(2, "0");
      const hour = String(parsed.getHours()).padStart(2, "0");
      const minute = String(parsed.getMinutes()).padStart(2, "0");
      return `${year}-${month}-${day} ${hour}:${minute}`;
    }

    function formatEstimatedAmountRangeFromKrw(low, high, fallback = "-") {
      const lowValue = Number(low);
      const highValue = Number(high);
      if (!Number.isFinite(lowValue) && !Number.isFinite(highValue)) {
        return fallback;
      }
      const safeLow = Number.isFinite(lowValue) ? lowValue : highValue;
      const safeHigh = Number.isFinite(highValue) ? highValue : lowValue;
      const lowEok = formatEokValue(safeLow / 100000000);
      const highEok = formatEokValue(safeHigh / 100000000);
      if (Math.abs(safeLow - safeHigh) < 1) {
        return `${lowEok}억원`;
      }
      return `${lowEok}~${highEok}억원`;
    }

    return {
      getVisibleSalesProjectIds,
      getSalesClaimForProject,
      getTrackerProjectSnapshot,
      renderUserSalesProjectFacts,
      isCurrentUserClaimOwner,
      canCurrentUserForceRelease,
      canCurrentUserManageClaim,
      isActiveSalesClaim,
      getOrganizationTransferTargets,
      getSalesNoteDraft,
      setSalesNoteDraft,
      upsertSalesClaim,
      replaceVisibleSalesClaims,
      mergeActiveSalesClaims,
      formatShortDateTime,
      formatEstimatedAmountRangeFromKrw,
    };
  }

  function createAdminTabsHelpers(options = {}) {
    const factory = ADMIN_SUPPORT_RUNTIME?.createAdminTabsHelpers;
    if (typeof factory === "function") return factory(options);
    throw new Error("SPMSAppSupportAdminRuntime.createAdminTabsHelpers is required");
  }

  function createOrgAdminHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      windowObject = global,
      ORG_ROLE_OPTIONS: orgRoleOptions = [],
      formatOrgRoleLabel = (value) => String(value ?? ""),
      formatMembershipStatusLabel = (value) => String(value ?? ""),
      escapeHtml = (value) => String(value ?? ""),
      copyInvitationUrl = async () => {},
      loadOrganizationInvitations = async () => {},
      getOrgAdminRuntime = () => null,
    } = options;

    function mergeOrganizationInvitationItem(existingItem, nextItem) {
      const merged = {
        ...(existingItem && typeof existingItem === "object" ? existingItem : {}),
        ...(nextItem && typeof nextItem === "object" ? nextItem : {}),
      };
      const keysToPreserve = ["invite_url", "delivery_status", "delivery_message", "initial_password"];
      for (const key of keysToPreserve) {
        const nextValue = String(nextItem?.[key] || "").trim();
        if (!nextValue) {
          merged[key] = existingItem?.[key] || "";
        }
      }
      return merged;
    }

    function mergeOrganizationInvitations(items, existingItems = state.organizationInvitations) {
      const existingById = new Map(
        (Array.isArray(existingItems) ? existingItems : [])
          .filter((item) => item && item.id)
          .map((item) => [String(item.id), item]),
      );
      return (Array.isArray(items) ? items : []).map((item) => {
        const invitationId = String(item?.id || "");
        const existingItem = existingById.get(invitationId);
        return mergeOrganizationInvitationItem(existingItem, item);
      });
    }

    function upsertOrganizationInvitation(item) {
      if (!item || !item.id) {
        return;
      }
      const invitationId = String(item.id);
      const existingItem = state.organizationInvitations.find((invitation) => String(invitation.id) === invitationId);
      const mergedItem = mergeOrganizationInvitationItem(existingItem, item);
      state.organizationInvitations = [
        mergedItem,
        ...state.organizationInvitations.filter((existing) => String(existing.id) !== invitationId),
      ];
    }

    function removeOrganizationInvitation(invitationId) {
      const targetId = String(invitationId || "");
      if (!targetId) {
        return;
      }
      state.organizationInvitations = state.organizationInvitations.filter((item) => String(item.id) !== targetId);
    }

    function bindInvitationCopyButtons(root) {
      if (!root || typeof root.querySelectorAll !== "function") {
        return;
      }
      for (const button of root.querySelectorAll("[data-invite-copy]")) {
        button.addEventListener("click", () => {
          const inviteUrl = button.getAttribute("data-invite-copy") || "";
          void copyInvitationUrl(inviteUrl, { renderStatusText: false });
        });
      }
    }

    function scheduleOrganizationInvitationSync(delayMs = 1500) {
      if (state.organizationInvitationSyncHandle) {
        windowObject.clearTimeout(state.organizationInvitationSyncHandle);
      }
      state.organizationInvitationSyncHandle = windowObject.setTimeout(() => {
        state.organizationInvitationSyncHandle = 0;
        void loadOrganizationInvitations({ silent: true });
      }, delayMs);
    }

    function getRenderableOrgRoleOptions(currentRole = "") {
      const normalizedCurrentRole = String(currentRole || "").trim();
      if (normalizedCurrentRole && !orgRoleOptions.includes(normalizedCurrentRole)) {
        return [normalizedCurrentRole, ...orgRoleOptions];
      }
      return [...orgRoleOptions];
    }

    function getCurrentAuthLocalUserId() {
      return String(state.auth.user?.local_user_id || state.auth.user?.auth_user_id || "").trim();
    }

    function isProtectedOrganizationMember(member) {
      const globalRole = String(member?.global_role || "").trim().toLowerCase();
      const email = String(member?.email || "").trim().toLowerCase();
      return globalRole === "platform_admin" || (state.auth.bootstrapEmail && email === state.auth.bootstrapEmail);
    }

    function canInviteOrganizationAdmins() {
      return String(state.auth.user?.role || "").trim() === "platform_admin";
    }

    function canManagePlatformAdminAccounts() {
      return canInviteOrganizationAdmins();
    }

    function getAllowedInvitationRoleOptions() {
      return canInviteOrganizationAdmins() ? ["org_member", "org_admin"] : ["org_member"];
    }

    function syncInvitationRoleOptions() {
      if (!dom.invitationRole) {
        return;
      }
      const allowedRoles = getAllowedInvitationRoleOptions();
      const currentValue = String(dom.invitationRole.value || "org_member").trim();
      dom.invitationRole.innerHTML = allowedRoles
        .map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(formatOrgRoleLabel(option))}</option>`)
        .join("");
      dom.invitationRole.value = allowedRoles.includes(currentValue) ? currentValue : allowedRoles[0];
    }

    function getOrganizationPlanSummaryForDisplay() {
      if (!state.organizationPlanSummary || typeof state.organizationPlanSummary !== "object") {
        return null;
      }
      const summary = { ...state.organizationPlanSummary };
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
          ? String(summary.upgrade_message || "현재 플랜 한도에 도달했습니다. 상위 플랜 업그레이드를 검토하세요.").trim()
          : "",
      };
    }

    function formatAuthAuditEventLabel(eventType) {
      switch (String(eventType || "").trim()) {
        case "invite_created":
          return "초대 생성";
        case "invite_accepted":
          return "초대 수락";
        case "invite_revoked":
          return "초대 철회";
        case "membership_role_changed":
          return "역할 변경";
        case "membership_deactivated":
          return "소속 비활성화";
        case "membership_reactivated":
          return "소속 재활성화";
        default:
          return String(eventType || "").trim() || "-";
      }
    }

    function formatAuthAuditActorLabel(item) {
      const displayName = String(item?.actor_display_name || "").trim();
      const email = String(item?.actor_email || "").trim();
      const role = String(item?.actor_role || "").trim();
      const parts = [];
      if (displayName) {
        parts.push(displayName);
      }
      if (email && email !== displayName) {
        parts.push(email);
      }
      if (role) {
        parts.push(formatOrgRoleLabel(role));
      }
      return parts.length ? parts.join(" · ") : "시스템";
    }

    function formatAuthAuditSummary(item) {
      return getOrgAdminRuntime()?.formatAuthAuditSummary?.(item, {
        formatOrgRoleLabel,
        formatMembershipStatusLabel,
      }) || "";
    }

    return {
      mergeOrganizationInvitationItem,
      mergeOrganizationInvitations,
      upsertOrganizationInvitation,
      removeOrganizationInvitation,
      bindInvitationCopyButtons,
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
      formatAuthAuditSummary,
    };
  }

  function createAdminTabsFacade(options = {}) {
    const factory = ADMIN_SUPPORT_RUNTIME?.createAdminTabsFacade;
    if (typeof factory === "function") return factory(options);
    throw new Error("SPMSAppSupportAdminRuntime.createAdminTabsFacade is required");
  }

  function createOrgAdminControllerDepsHelpers(options = {}) {
    const {
      sharedDeps = {},
      formattingDeps = {},
      actionDeps = {},
      runtimeDeps = {},
    } = options;
    let cachedDeps = null;

    function buildOrgAdminControllerDeps() {
      if (cachedDeps) {
        return cachedDeps;
      }
      cachedDeps = {
        ...sharedDeps,
        ...formattingDeps,
        ...actionDeps,
        ...runtimeDeps,
      };
      return cachedDeps;
    }

    return {
      buildOrgAdminControllerDeps,
    };
  }

  function createAppSupportOrgRuntime(options = {}) {
    const state = options.state || null;
    return {
      formatOrgRoleLabel,
      formatInvitationStatusLabel,
      formatContactResolutionStatusLabel,
      formatContactResolutionReasonLabel,
      formatAccountStatusLabel,
      formatMembershipStatusLabel,
      resolveStatusClass,
      isAdminRole,
      canUseAdminMode: () => canUseAdminMode(state),
      canLoadProtectedConsoleData: () => canLoadProtectedConsoleData(state),
      getMissingReportDownloadLimit: () => getMissingReportDownloadLimit(state),
      createSalesStateHelpers,
      createAdminTabsHelpers,
      createAdminTabsFacade,
      createOrgAdminHelpers,
      createOrgAdminControllerDepsHelpers,
    };
  }

  global.SPMSAppSupportOrgRuntime = {
    createAppSupportOrgRuntime,
  };
})(window);
