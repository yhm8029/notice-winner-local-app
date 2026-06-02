export function createAuthController(deps = {}) {
  const AUTH_MODE_SIGN_IN = deps.AUTH_MODE_SIGN_IN || "sign_in";
  const AUTH_MODE_SIGN_UP = deps.AUTH_MODE_SIGN_UP || "sign_up";

  function requireFunction(name) {
    const fn = deps[name];
    if (typeof fn !== "function") {
      throw new Error(`auth controller dependency is missing: ${name}`);
    }
    return fn;
  }

  function getWindow() {
    const currentWindow = deps.window || (typeof window !== "undefined" ? window : null);
    if (!currentWindow) {
      throw new Error("auth controller dependency is missing: window");
    }
    return currentWindow;
  }

  function renderAuthUi() {
    return requireFunction("renderAuthUi")();
  }

  function requireAuthSessionRuntime() {
    return requireFunction("requireAuthSessionRuntime")();
  }

  function shouldShowSignUpMode() {
    if (typeof deps.shouldShowSignUpMode === "function") {
      return deps.shouldShowSignUpMode();
    }
    return true;
  }

  function isBootstrapEmail(email) {
    if (typeof deps.isBootstrapEmail === "function") {
      return deps.isBootstrapEmail(email);
    }
    const bootstrapEmail = String(deps.state?.auth?.bootstrapEmail || "").trim().toLowerCase();
    const normalizedEmail = String(email || "").trim().toLowerCase();
    return Boolean(bootstrapEmail && normalizedEmail && bootstrapEmail === normalizedEmail);
  }

  function normalizeAuthErrorMessage(rawMessage, { isSignUp = false, email = "" } = {}) {
    const message = String(rawMessage || "").trim();
    const lowered = message.toLowerCase();
    if (lowered.includes("invalid_credentials")) {
      if (isSignUp && isBootstrapEmail(email)) {
        return "이미 생성된 운영자 계정입니다. 비밀번호 재설정을 사용하거나 기존 비밀번호로 로그인하세요.";
      }
      return "이메일 또는 비밀번호가 올바르지 않습니다.";
    }
    return message || "인증에 실패했습니다.";
  }

  function canUseAdminMode() {
    if (typeof deps.canUseAdminMode === "function") {
      return deps.canUseAdminMode();
    }
    if (!deps.state?.auth?.enabled) {
      return true;
    }
    const role = String(deps.state?.auth?.user?.role || "").trim();
    return ["platform_admin", "org_admin"].includes(role);
  }

  function canLoadProtectedConsoleData() {
    if (typeof deps.canLoadProtectedConsoleData === "function") {
      return deps.canLoadProtectedConsoleData();
    }
    if (deps.state?.auth?.checking) {
      return false;
    }
    if (!deps.state?.auth?.enabled) {
      return true;
    }
    return Boolean(deps.state?.auth?.authenticated && deps.state?.auth?.authorized);
  }

  function syncTrackerChangeEventsWarmup() {
    if (deps.state?.uiMode !== "user") {
      return;
    }
    deps.state.trackerChangeEventsLoading = false;
    deps.renderTrackerChangeEventsPanel?.();
    deps.trackerController?.renderTrackerChangeEventUnreadCount?.();
    const currentWindow = getWindow();
    if (deps.state.trackerChangeEventsWarmupHandle) {
      currentWindow.clearTimeout(deps.state.trackerChangeEventsWarmupHandle);
    }
    deps.state.trackerChangeEventsWarmupHandle = currentWindow.setTimeout(() => {
      deps.state.trackerChangeEventsWarmupHandle = null;
      void deps.trackerController?.loadTrackerChangeEventUnreadCount?.({ silent: true });
      void deps.trackerController?.loadTrackerChangeEvents?.({ silent: true });
    }, 1500);
  }

  function syncUiModeChrome() {
    if (!canUseAdminMode()) {
      deps.state.uiMode = "user";
    }
    const adminMode = deps.state.uiMode === "admin";
    const currentWindow = getWindow();
    if (adminMode && deps.state.trackerChangeEventsWarmupHandle) {
      currentWindow.clearTimeout(deps.state.trackerChangeEventsWarmupHandle);
      deps.state.trackerChangeEventsWarmupHandle = null;
    }
    if (deps.dom?.uiModeLabel) {
      deps.dom.uiModeLabel.textContent = adminMode ? "운영자 모드" : "실사용자 모드";
    }
    if (deps.dom?.modeToggleButton) {
      deps.dom.modeToggleButton.textContent = adminMode ? "사용자 모드" : "운영자 모드";
      deps.dom.modeToggleButton.classList.add("hidden");
    }
    if (deps.dom?.authSessionModeToggleButton) {
      deps.dom.authSessionModeToggleButton.textContent = adminMode ? "사용자 모드" : "운영자 모드";
      deps.dom.authSessionModeToggleButton.classList.add("hidden");
    }
    deps.dom?.apiMetaCard?.classList.toggle("hidden", !adminMode);
    deps.dom?.syncMetaCard?.classList.toggle("hidden", !adminMode);

    const adminOnlyPanels = [
      deps.dom?.panelOrgAdmin,
      deps.dom?.panelDashboard,
      deps.dom?.panelStatus,
      deps.dom?.panelForm,
      deps.dom?.panelRuns,
      deps.dom?.panelLogs,
      deps.dom?.panelReport,
      deps.dom?.panelArtifacts,
      deps.dom?.projectPanel,
      deps.dom?.panelSalesSummary,
      deps.dom?.trackerContactResolutionPanel,
      deps.dom?.trackerCleanupPanel,
      deps.dom?.backfillConflictPanel,
    ];
    for (const panel of adminOnlyPanels) {
      panel?.classList.toggle("hidden", !adminMode);
    }

    deps.dom?.panelEditor?.classList.add("hidden");
    deps.dom?.panelMissingReport?.classList.toggle("hidden", !adminMode);
    deps.dom?.trackerInlineEditor?.classList.add("hidden");
    deps.dom?.trackerEntriesList?.classList.remove("hidden");
    deps.dom?.entriesPrevButton?.closest(".pagination-row")?.classList.remove("hidden");
    deps.dom?.trackerBoard?.closest(".tracker-board")?.classList.add("hidden");
    deps.dom?.trackerTemplateUploadButton?.classList.toggle("hidden", !adminMode);
    deps.dom?.trackerTemplateResetButton?.classList.toggle("hidden", !adminMode);
    deps.dom?.trackerTemplateStatus?.classList.toggle("hidden", !adminMode);

    deps.dom?.trackerExportButton?.classList.add("hidden");
    deps.dom?.trackerContext?.classList.add("hidden");
    deps.dom?.presetPanel?.classList.add("hidden");
    deps.dom?.runExecutionContext?.classList.add("hidden");

    const advancedBox = deps.dom?.runForm?.querySelector(".advanced-box");
    advancedBox?.classList.add("hidden");
    return adminMode;
  }

  function applyUiModeTransition(adminMode, { renderAuth = true } = {}) {
    deps.renderTrackerTemplateStatus?.();
    if (!adminMode) {
      deps.state.backfillConflicts = [];
      deps.state.backfillConflictsLoading = false;
      deps.renderBackfillConflictsPanel?.();
      deps.state.trackerContactResolutionSummary = null;
      deps.state.trackerContactResolutionLoading = false;
      deps.renderTrackerContactResolutionSummary?.();
      deps.state.trackerCleanupPreview = null;
      deps.state.trackerCleanupLoading = false;
      deps.state.trackerCleanupApplying = false;
      deps.renderTrackerCleanupPreview?.();
      deps.closeDrawer?.();
    } else if (canLoadProtectedConsoleData()) {
      void deps.loadAdminConsoleData?.({ silent: true });
      void deps.loadBackfillConflicts?.({ silent: true });
    }
    if (renderAuth) {
      renderAuthUi();
    }
    deps.renderOrganizationAdminPanel?.();
    deps.renderMySalesClaimsPanel?.();
    deps.renderSalesSummaryPanel?.();
    deps.renderRunDetail?.(deps.state.selectedRun);
    deps.renderTrackerEntries?.(deps.state.trackerEntries, { refreshSelectedEntry: adminMode });
    if (canLoadProtectedConsoleData()) {
      if (adminMode) {
        void deps.loadOrganizationUsers?.({ silent: true });
        void deps.loadTrackerEntries?.({ silent: true });
        void deps.trackerController?.loadTrackerChangeEventUnreadCount?.({ silent: true });
        void deps.trackerController?.loadTrackerChangeEvents?.({ silent: true });
      } else {
        deps.clearUserModeRunSelection?.({ sync: true });
        deps.hydrateHomeBootstrapCache?.();
        void deps.loadHomeBootstrap?.({ silent: true });
        syncTrackerChangeEventsWarmup();
      }
    }
  }

  async function initializeAuthGate(options = {}) {
    void options;
    if (deps.state.auth.localSession) {
      deps.state.auth.enabled = true;
      deps.state.auth.checked = true;
      deps.state.auth.checking = false;
      deps.state.auth.authenticated = true;
      deps.state.auth.authorized = true;
      renderAuthUi();
      if (typeof deps.syncUiModeFromLocation === "function") {
        deps.syncUiModeFromLocation();
      }
      requireFunction("syncUiModeChrome")();
      return true;
    }
    deps.state.auth.checking = true;
    renderAuthUi();
    try {
      const response = await deps.api("/api/auth/session", { cacheBust: false, timeoutMs: 10000 });
      applyAuthSession(response);
      if (deps.state.auth.enabled && deps.state.auth.inviteToken) {
        await loadInvitationPreview({ silent: true });
      }
      if (deps.state.auth.enabled && deps.state.auth.authenticated && !deps.state.auth.authorized) {
        await acceptPendingInvitationToken({ silent: true });
      }
      return true;
    } catch (err) {
      deps.state.auth.enabled = true;
      deps.state.auth.checked = true;
      deps.state.auth.checking = false;
      deps.state.auth.authenticated = false;
      deps.state.auth.authorized = false;
      deps.state.auth.user = null;
      deps.state.auth.message = err.message || "인증 상태를 확인하지 못했습니다. 다시 시도해라.";
      renderAuthUi();
      deps.flash(deps.state.auth.message, "error");
      return false;
    }
  }

  async function loadInvitationPreview({ silent = false } = {}) {
    const inviteToken = String(deps.state.auth.inviteToken || "").trim();
    if (!inviteToken) {
      deps.state.auth.invitationPreview = null;
      deps.state.auth.invitationPreviewError = "";
      deps.state.auth.invitationPreviewLoading = false;
      renderAuthUi();
      return null;
    }
    deps.state.auth.invitationPreviewLoading = true;
    deps.state.auth.invitationPreviewError = "";
    renderAuthUi();
    try {
      const preview = await deps.api(`/api/auth/invitations/preview?invite_token=${encodeURIComponent(inviteToken)}`, {
        cacheBust: false,
        timeoutMs: 10000,
      });
      deps.state.auth.invitationPreview = preview || null;
      deps.state.auth.invitationPreviewError = "";
      return preview;
    } catch (err) {
      deps.state.auth.invitationPreview = null;
      deps.state.auth.invitationPreviewError = err.message || "초대 정보를 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(deps.state.auth.invitationPreviewError, "error");
      }
      return null;
    } finally {
      deps.state.auth.invitationPreviewLoading = false;
      renderAuthUi();
    }
  }

  async function loadInvitationPreviewByEmail(email, { silent = false } = {}) {
    const normalizedEmail = String(email || "").trim();
    if (deps.state.auth.inviteToken || !normalizedEmail) {
      if (!deps.state.auth.inviteToken) {
        deps.state.auth.invitationPreview = null;
        deps.state.auth.invitationPreviewError = "";
        deps.state.auth.invitationPreviewLoading = false;
        renderAuthUi();
      }
      return null;
    }
    deps.state.auth.invitationPreviewLoading = true;
    deps.state.auth.invitationPreviewError = "";
    renderAuthUi();
    try {
      const preview = await deps.api(`/api/auth/invitations/preview-by-email?email=${encodeURIComponent(normalizedEmail)}`, {
        cacheBust: false,
        timeoutMs: 8000,
      });
      deps.state.auth.invitationPreview = preview || null;
      deps.state.auth.invitationPreviewError = "";
      return preview;
    } catch (err) {
      deps.state.auth.invitationPreview = null;
      if (String(err.code || "") === "invite_not_found") {
        deps.state.auth.invitationPreviewError = "";
      } else {
        deps.state.auth.invitationPreviewError = err.message || "초대 정보를 불러오지 못했습니다.";
        if (!silent) {
          deps.flash(deps.state.auth.invitationPreviewError, "error");
        }
      }
      return null;
    } finally {
      deps.state.auth.invitationPreviewLoading = false;
      renderAuthUi();
    }
  }

  function scheduleInvitationPreviewLookup(email) {
    const currentWindow = getWindow();
    if (deps.state.auth.previewLookupHandle) {
      currentWindow.clearTimeout(deps.state.auth.previewLookupHandle);
      deps.state.auth.previewLookupHandle = 0;
    }
    if (deps.state.auth.mode !== AUTH_MODE_SIGN_UP || deps.state.auth.inviteToken) {
      return;
    }
    const normalizedEmail = String(email || "").trim();
    if (!normalizedEmail) {
      deps.state.auth.invitationPreview = null;
      deps.state.auth.invitationPreviewError = "";
      renderAuthUi();
      return;
    }
    deps.state.auth.previewLookupHandle = currentWindow.setTimeout(() => {
      deps.state.auth.previewLookupHandle = 0;
      void loadInvitationPreviewByEmail(normalizedEmail, { silent: true });
    }, 250);
  }

  async function importAuthSessionFromLocationHash() {
    if (deps.state.auth.localSession) {
      return;
    }
    const currentWindow = getWindow();
    const rawHash = String(currentWindow.location.hash || "").replace(/^#/, "").trim();
    if (!rawHash) {
      return;
    }
    const hashParams = new URLSearchParams(rawHash);
    const accessToken = String(hashParams.get("access_token") || "").trim();
    const refreshToken = String(hashParams.get("refresh_token") || "").trim();
    const errorDescription = String(hashParams.get("error_description") || hashParams.get("error") || "").trim();
    if (errorDescription) {
      currentWindow.history.replaceState({}, "", `${currentWindow.location.pathname}${currentWindow.location.search}`);
      deps.flash(decodeURIComponent(errorDescription), "error");
      return;
    }
    if (!accessToken) {
      return;
    }
    try {
      const session = await deps.api("/api/auth/session/import", {
        method: "POST",
        body: JSON.stringify({
          access_token: accessToken,
          refresh_token: refreshToken,
        }),
        cacheBust: false,
        timeoutMs: 20000,
      });
      applyAuthSession(session);
    } catch (err) {
      deps.flash(err.message || "초대 메일 로그인 정보를 가져오지 못했습니다.", "error");
    } finally {
      currentWindow.history.replaceState({}, "", `${currentWindow.location.pathname}${currentWindow.location.search}`);
    }
  }

  async function acceptPendingInvitationToken({ silent = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authenticated || deps.state.auth.authorized) {
      return null;
    }
    try {
      const session = await deps.api("/api/auth/invitations/accept", {
        method: "POST",
        body: JSON.stringify({ invite_token: deps.state.auth.inviteToken }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      applyAuthSession(session);
      if (!silent) {
        deps.flash("초대를 수락했다.", "ok");
      }
      return session;
    } catch (err) {
      deps.state.auth.message = err.message || "초대를 수락하지 못했습니다.";
      renderAuthUi();
      if (!silent) {
        deps.flash(deps.state.auth.message, "error");
      }
      return null;
    }
  }

  function applyAuthSession(session) {
    const previousUiMode = deps.state.uiMode;
    const normalized = requireAuthSessionRuntime().normalizeAuthSession(session);
    deps.state.auth.enabled = normalized.enabled;
    deps.state.auth.checked = normalized.checked;
    deps.state.auth.checking = normalized.checking;
    deps.state.auth.authenticated = normalized.authenticated;
    deps.state.auth.authorized = normalized.authorized;
    deps.state.auth.accessToken = normalized.accessToken;
    deps.state.auth.bootstrapEmail = normalized.bootstrapEmail;
    deps.state.auth.message = normalized.message;
    deps.state.auth.user = normalized.user;
    if (deps.state.auth.user && deps.state.auth.user.display_name && deps.dom.patchActorLabel) {
      deps.dom.patchActorLabel.value = deps.state.auth.user.display_name;
    }
    if (typeof deps.syncUiModeFromLocation === "function") {
      deps.syncUiModeFromLocation();
    }
    renderAuthUi();
    const adminMode = requireFunction("syncUiModeChrome")();
    if (previousUiMode !== deps.state.uiMode) {
      requireFunction("applyUiModeTransition")(adminMode, { renderAuth: false });
    }
  }

  async function refreshAuthSessionState({ silent = false } = {}) {
    if (deps.state.auth.localSession) {
      deps.state.auth.enabled = true;
      deps.state.auth.checked = true;
      deps.state.auth.checking = false;
      deps.state.auth.authenticated = true;
      deps.state.auth.authorized = true;
      renderAuthUi();
      return null;
    }
    if (!deps.state.auth.enabled) {
      return null;
    }
    try {
      let session = await deps.api("/api/auth/session", {
        cacheBust: false,
        timeoutMs: 10000,
        __skipAuthRetry: true,
      });
      applyAuthSession(session);
      if (deps.state.auth.authenticated && !deps.state.auth.authorized) {
        const accepted = await acceptPendingInvitationToken({ silent: true });
        if (accepted) {
          session = accepted;
        }
      }
      if (deps.state.auth.authenticated && deps.state.auth.authorized && deps.state.consoleInitialized) {
        if (deps.state.uiMode === "user") {
          void requireFunction("loadSalesOverview")({ silent: true, force: true });
        } else {
          void requireFunction("loadMySalesClaims")({ silent: true });
        }
      }
      return session;
    } catch (err) {
      if (!silent) {
        deps.flash(err.message || "세션을 새로고침하지 못했습니다.", "error");
      }
      return null;
    }
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    if (deps.state.auth.mode === AUTH_MODE_SIGN_UP && !shouldShowSignUpMode()) {
      deps.state.auth.message = "초대 링크가 있거나 초기 운영자 계정일 때만 계정 등록할 수 있습니다.";
      renderAuthUi();
      return;
    }
    const payload = {
      email: String(deps.dom.authEmail.value || "").trim(),
      password: String(deps.dom.authPassword.value || "").trim(),
      display_name: String(deps.dom.authDisplayName.value || "").trim(),
      invite_token: deps.state.auth.inviteToken || "",
    };
    const isSignUp = deps.state.auth.mode === AUTH_MODE_SIGN_UP;
    const endpoint = isSignUp ? "/api/auth/sign-up" : "/api/auth/sign-in";
    const originalLabel = deps.dom.authSubmitButton.textContent || "로그인";
    deps.setBusy(deps.dom.authSubmitButton, true, isSignUp ? "등록 중..." : "로그인 중...");
    try {
      const session = await deps.api(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
        cacheBust: false,
        timeoutMs: 20000,
      });
      applyAuthSession(session);
      if (deps.state.auth.authenticated && deps.state.auth.authorized) {
        await requireFunction("ensureConsoleInitialized")();
      }
    } catch (err) {
      const errorMessage = normalizeAuthErrorMessage(err.message, {
        isSignUp,
        email: payload.email,
      });
      if (!isSignUp && isBootstrapEmail(payload.email) && errorMessage.includes("bootstrap")) {
        deps.state.auth.message = "초기 운영자 계정 비밀번호가 맞지 않습니다. '계정 등록' 탭에서 같은 이메일로 새 비밀번호를 다시 설정하세요.";
      } else {
        deps.state.auth.message = errorMessage;
      }
      renderAuthUi();
    } finally {
      deps.setBusy(deps.dom.authSubmitButton, false, originalLabel);
    }
  }

  async function handleAuthPasswordReset() {
    const email = String(deps.dom.authEmail?.value || "").trim();
    if (!email) {
      deps.state.auth.message = "비밀번호 재설정 메일을 받을 이메일을 먼저 입력하세요.";
      renderAuthUi();
      return;
    }
    const originalLabel = deps.dom.authResetPasswordButton?.textContent || "비밀번호 재설정";
    if (deps.dom.authResetPasswordButton) {
      deps.setBusy(deps.dom.authResetPasswordButton, true, "전송 중...");
    }
    try {
      const result = await deps.api("/api/auth/password-reset", {
        method: "POST",
        body: JSON.stringify({ email }),
        cacheBust: false,
        timeoutMs: 20000,
      });
      deps.state.auth.message = result.message || "비밀번호 재설정 안내를 전송했습니다.";
    } catch (err) {
      deps.state.auth.message = err.message || "비밀번호 재설정을 시작하지 못했습니다.";
    } finally {
      if (deps.dom.authResetPasswordButton) {
        deps.setBusy(deps.dom.authResetPasswordButton, false, originalLabel);
      }
      renderAuthUi();
    }
  }

  async function handleAuthSignOut() {
    requireFunction("closeProfileDialog")();
    try {
      await deps.api("/api/auth/sign-out", {
        method: "POST",
        body: JSON.stringify({}),
        cacheBust: false,
        timeoutMs: 10000,
      });
    } catch (_err) {
      // Ignore logout failures and reset the local shell anyway.
    }
    deps.state.auth.authenticated = false;
    deps.state.auth.authorized = false;
    deps.state.auth.user = null;
    deps.state.auth.message = "";
    deps.state.organizationUsers = [];
    deps.state.organizationUsersError = "";
    deps.state.organizationMembers = [];
    deps.state.organizationMembersError = "";
    deps.state.organizationPlanSummary = null;
    deps.state.organizationInvitations = [];
    deps.state.organizationInvitationsError = "";
    deps.state.organizationAuditLogs = [];
    deps.state.organizationAuditLogsLoading = false;
    deps.state.organizationAuditLogsError = "";
    deps.state.organizationDownloadAuditLogs = [];
    deps.state.organizationDownloadAuditLogsLoading = false;
    deps.state.organizationDownloadAuditLogsError = "";
    deps.state.organizationDownloadAuditLogsLimit = 5;
    deps.state.organizationDownloadAuditLogsHasMore = false;
    deps.state.organizationDownloadAuditLogsLoaded = false;
    deps.state.organizationLoginAuditLogs = [];
    deps.state.organizationLoginAuditLogsLoading = false;
    deps.state.organizationLoginAuditLogsError = "";
    deps.state.organizationLoginAuditLogsLimit = 5;
    deps.state.organizationLoginAuditLogsHasMore = false;
    deps.state.organizationLoginAuditLogsLoaded = false;
    deps.state.memberSaveStateByUserId = {};
    deps.state.mySalesClaims = [];
    deps.state.companySalesClaims = [];
    deps.state.mySalesClaimsError = "";
    deps.state.salesSummaryByUser = [];
    deps.state.salesSummaryError = "";
    deps.state.salesClosedClaims = [];
    deps.state.salesClosedError = "";
    deps.state.consoleInitialized = false;
    const currentWindow = getWindow();
    if (deps.state.runsHandle) {
      currentWindow.clearInterval(deps.state.runsHandle);
      deps.state.runsHandle = null;
    }
    if (deps.state.authSessionHandle) {
      currentWindow.clearInterval(deps.state.authSessionHandle);
      deps.state.authSessionHandle = null;
    }
    currentWindow.location.reload();
  }

  function setAuthMode(mode) {
    deps.state.auth.mode = mode === AUTH_MODE_SIGN_UP ? AUTH_MODE_SIGN_UP : AUTH_MODE_SIGN_IN;
    deps.state.auth.message = "";
    if (deps.state.auth.mode === AUTH_MODE_SIGN_UP) {
      scheduleInvitationPreviewLookup(String(deps.dom.authEmail?.value || "").trim());
    } else if (!deps.state.auth.inviteToken) {
      deps.state.auth.invitationPreview = null;
      deps.state.auth.invitationPreviewError = "";
    }
    renderAuthUi();
  }

  return {
    initializeAuthGate,
    loadInvitationPreview,
    loadInvitationPreviewByEmail,
    scheduleInvitationPreviewLookup,
    importAuthSessionFromLocationHash,
    applyAuthSession,
    applyUiModeTransition,
    refreshAuthSessionState,
    acceptPendingInvitationToken,
    handleAuthSubmit,
    handleAuthPasswordReset,
    handleAuthSignOut,
    scheduleTrackerChangeEventsWarmup: syncTrackerChangeEventsWarmup,
    syncUiModeChrome,
    setAuthMode,
  };
}

if (typeof window !== "undefined") {
  window.AUTH_CONTROLLER = window.AUTH_CONTROLLER || {};
  window.AUTH_CONTROLLER.createAuthController = createAuthController;
} else if (typeof globalThis !== "undefined") {
  globalThis.AUTH_CONTROLLER = globalThis.AUTH_CONTROLLER || {};
  globalThis.AUTH_CONTROLLER.createAuthController = createAuthController;
}
