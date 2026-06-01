(function attachAppUiGlueRuntime(global) {
  function requireAppBootstrapBridge(getAppBootstrapBridge) {
    const bridge = typeof getAppBootstrapBridge === "function" ? getAppBootstrapBridge() : null;
    if (!bridge || typeof bridge !== "object") {
      throw new Error("appBootstrapBridge is required before app.js loads");
    }
    return bridge;
  }

  function createAppUiGlueRuntime(options = {}) {
    const state = options.state || {};
    const dom = options.dom || {};
    const salesRuntime = options.salesRuntime || null;
    const runViewRuntime = options.runViewRuntime || null;
    const runTypeLabels = options.runTypeLabels || {};
    const callRuntimeEnhancements = options.callRuntimeEnhancements;
    const callAppEventBindings = options.callAppEventBindings;
    const callProjectRelatedController = options.callProjectRelatedController;
    const callRunPanelsController = options.callRunPanelsController;
    const callTrackerController = options.callTrackerController;
    const callReportPanelsController = options.callReportPanelsController;
    const requireOrganizationAdminRuntime = options.requireOrganizationAdminRuntime;
    const requireAuthSessionRuntime = options.requireAuthSessionRuntime;
    const renderAuthUi = options.renderAuthUi;
    const canUseAdminMode = options.canUseAdminMode;
    const syncUiModeChrome = options.syncUiModeChrome;
    const applyUiModeTransition = options.applyUiModeTransition;
    const getAppBootstrapBridge = options.getAppBootstrapBridge;

    function canUseBootstrapSignUp() {
      const bootstrapEmail = String(state.auth?.bootstrapEmail || "").trim().toLowerCase();
      const typedEmail = String(dom.authEmail?.value || "").trim().toLowerCase();
      return Boolean(bootstrapEmail && typedEmail && typedEmail === bootstrapEmail);
    }

    function isBootstrapEmail(email) {
      const bootstrapEmail = String(state.auth?.bootstrapEmail || "").trim().toLowerCase();
      const normalizedEmail = String(email || "").trim().toLowerCase();
      return Boolean(bootstrapEmail && normalizedEmail && bootstrapEmail === normalizedEmail);
    }

    function shouldShowSignUpMode() {
      return true;
    }

    function mountRuntimeEnhancements() {
      return callRuntimeEnhancements("mountRuntimeEnhancements");
    }

    function formatContractAmountInput(rawValue) {
      return salesRuntime?.formatContractAmountInput?.(rawValue) || "";
    }

    function formatContractAmountDisplay(rawValue, fallback = "-") {
      return salesRuntime?.formatContractAmountDisplay?.(rawValue, fallback) || fallback;
    }

    function renderInvitationStatus(message = "", level = "") {
      requireOrganizationAdminRuntime().renderInvitationStatus({
        dom,
        buildInvitationStatusViewModel: requireAuthSessionRuntime().buildInvitationStatusViewModel,
        message,
        level,
      });
    }

    function handleAuthFindId() {
      state.auth.message =
        "\ub85c\uadf8\uc778 \uc544\uc774\ub514\ub294 \ucd08\ub300 \ubc1b\uc740 \uacc4\uc815 \ub4f1\ub85d\uc5d0 \uc0ac\uc6a9\ud55c \uc774\uba54\uc77c\uc785\ub2c8\ub2e4. "
        + "\uae30\uc5b5\ub098\uc9c0 \uc54a\uc73c\uba74 \ud68c\uc0ac \uad00\ub9ac\uc790\uc5d0\uac8c \ud655\uc778\ud558\uc138\uc694.";
      renderAuthUi();
    }

    function bindEvents() {
      return callAppEventBindings("bindEvents");
    }

    function runTypeLabel(runType) {
      return (
        runViewRuntime?.runTypeLabel(runType, runTypeLabels)
        || runTypeLabels[String(runType || "").trim()]
        || String(runType || "-")
      );
    }

    function isProjectTrackerRun(runType) {
      const raw = String(runType || "").trim();
      return raw === "project_tracker" || raw === "winner_pipeline";
    }

    function hydrateStateFromUrl() {
      return requireAppBootstrapBridge(getAppBootstrapBridge).hydrateStateFromUrl();
    }

    function renderSyncMeta() {
      dom.autoRefreshToggle.checked = state.autoRefresh;
      dom.lastSyncLabel.textContent = state.lastSyncLabel;
    }

    function touchSyncMeta(label) {
      state.lastSyncLabel = label;
      renderSyncMeta();
    }

    function hydrateProjectRelatedPayloadCache() {
      return callProjectRelatedController("hydrateProjectRelatedPayloadCache");
    }

    function persistProjectRelatedPayloadCache() {
      return callProjectRelatedController("persistProjectRelatedPayloadCache");
    }

    function openDrawer() {
      state.drawerOpen = true;
      dom.entryDrawer.classList.remove("hidden");
      dom.entryDrawer.setAttribute("aria-hidden", "false");
    }

    function closeDrawer() {
      state.drawerOpen = false;
      dom.entryDrawer.classList.add("hidden");
      dom.entryDrawer.setAttribute("aria-hidden", "true");
    }

    function syncFilterControlsFromState() {
      callRunPanelsController("syncRunFilterControlsFromState");
      callTrackerController("syncTrackerFilterControlsFromState");
      callReportPanelsController("syncReportSelectFromState");
    }

    function readRunFiltersFromControls() {
      state.runFilters.status = dom.runFilterStatus.value;
      state.runFilters.runType = dom.runFilterType.value;
      state.runFilters.from = dom.runFilterFrom.value;
      state.runFilters.to = dom.runFilterTo.value;
      state.runFilters.pageSize = Number(dom.runPageSize.value || 20);
    }

    function applyUiMode() {
      const adminMode = syncUiModeChrome();
      applyUiModeTransition(adminMode);
    }

    function toggleUiMode() {
      if (!canUseAdminMode()) {
        state.uiMode = "user";
        applyUiMode();
        return;
      }
      state.uiMode = state.uiMode === "admin" ? "user" : "admin";
      applyUiMode();
    }

    function useGlobalTrackerEntriesScope() {
      return true;
    }

    function shouldPollGeneralConsole() {
      return requireAppBootstrapBridge(getAppBootstrapBridge).shouldPollGeneralConsole();
    }

    function clearUserModeRunSelection({ sync = false } = {}) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).clearUserModeRunSelection({ sync });
    }

    return {
      canUseBootstrapSignUp,
      isBootstrapEmail,
      shouldShowSignUpMode,
      mountRuntimeEnhancements,
      formatContractAmountInput,
      formatContractAmountDisplay,
      renderInvitationStatus,
      handleAuthFindId,
      bindEvents,
      runTypeLabel,
      isProjectTrackerRun,
      hydrateStateFromUrl,
      renderSyncMeta,
      touchSyncMeta,
      hydrateProjectRelatedPayloadCache,
      persistProjectRelatedPayloadCache,
      openDrawer,
      closeDrawer,
      syncFilterControlsFromState,
      readRunFiltersFromControls,
      toggleUiMode,
      useGlobalTrackerEntriesScope,
      shouldPollGeneralConsole,
      applyUiMode,
      clearUserModeRunSelection,
    };
  }

  global.SPMSAppUiGlueRuntime = {
    createAppUiGlueRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
