(function attachAppSupportAuthRuntime(global) {
  function createAuthControllerDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      document: documentFallback = null,
      window: windowFallback = null,
      documentObject = documentFallback,
      windowObject = windowFallback,
      api = async () => ({}),
      flash = () => {},
      setBusy = () => {},
      escapeHtml = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
      formatInvitationStatusLabel = (value) => String(value ?? ""),
      formatSalesDateLabel = (value) => String(value ?? ""),
      formatMembershipStatusLabel = (value) => String(value ?? ""),
      requireAuthSessionRuntime = () => null,
      loadOrganizationUsers = async () => {},
      loadOrganizationMembers = async () => {},
      loadSalesOverview = async () => {},
      loadMySalesClaims = async () => {},
      refreshSalesAdminPanels = async () => {},
      ensureConsoleInitialized = async () => {},
      shouldShowSignUpMode = () => false,
      AUTH_MODE_SIGN_IN = "sign_in",
      AUTH_MODE_SIGN_UP = "sign_up",
      syncUiModeChrome = () => {},
      syncUiModeFromLocation = () => {},
      applyUiModeTransition = () => {},
      renderAuthUi = () => {},
      canUseAdminMode = () => false,
      canLoadProtectedConsoleData = () => false,
      loadAdminConsoleData = async () => {},
      loadBackfillConflicts = async () => {},
      renderBackfillConflictsPanel = () => {},
      renderTrackerContactResolutionSummary = () => {},
      renderTrackerCleanupPreview = () => {},
      closeDrawer = () => {},
      hydrateHomeBootstrapCache = () => false,
      clearUserModeRunSelection = () => {},
      loadHomeBootstrap = async () => {},
      loadTrackerEntries = async () => {},
      getTrackerController = () => null,
      renderOrganizationAdminPanel = () => {},
      renderMySalesClaimsPanel = () => {},
      renderSalesSummaryPanel = () => {},
      renderRunDetail = () => {},
      renderTrackerEntries = () => {},
    } = options;

    function buildAuthControllerBaseDeps() {
      return {
        state,
        dom,
        document: documentObject,
        window: windowObject,
        api,
        flash,
        setBusy,
        escapeHtml,
        formatOrgRoleLabel,
        formatInvitationStatusLabel,
        formatSalesDateLabel,
        formatMembershipStatusLabel,
        requireAuthSessionRuntime,
        loadOrganizationUsers,
        loadOrganizationMembers,
        loadSalesOverview,
        loadMySalesClaims,
        refreshSalesAdminPanels,
        ensureConsoleInitialized,
        shouldShowSignUpMode,
        AUTH_MODE_SIGN_IN,
        AUTH_MODE_SIGN_UP,
        syncUiModeChrome,
        syncUiModeFromLocation,
        applyUiModeTransition,
      };
    }

    function buildAuthControllerDeps() {
      return {
        ...buildAuthControllerBaseDeps(),
        renderAuthUi,
        canUseAdminMode,
        canLoadProtectedConsoleData,
        loadAdminConsoleData,
        loadBackfillConflicts,
        renderBackfillConflictsPanel,
        renderTrackerContactResolutionSummary,
        renderTrackerCleanupPreview,
        closeDrawer,
        hydrateHomeBootstrapCache,
        clearUserModeRunSelection,
        loadHomeBootstrap,
        loadTrackerEntries,
        trackerController: getTrackerController(),
        renderOrganizationAdminPanel,
        renderMySalesClaimsPanel,
        renderSalesSummaryPanel,
        renderRunDetail,
        renderTrackerEntries,
      };
    }

    function buildAuthUiControllerDeps() {
      return buildAuthControllerBaseDeps();
    }

    return {
      buildAuthControllerBaseDeps,
      buildAuthControllerDeps,
      buildAuthUiControllerDeps,
    };
  }

  function createAuthControllerDepsHelpersFromApp(options = {}) {
    const {
      core = {},
      authUi = {},
      uiMode = {},
      authState = {},
      adminData = {},
      trackerPanels = {},
      salesPanels = {},
      tracker = {},
    } = options;
    return createAuthControllerDepsHelpers({
      state: core.state,
      dom: core.dom,
      documentObject: core.documentObject,
      windowObject: core.windowObject,
      api: core.api,
      flash: core.flash,
      setBusy: core.setBusy,
      escapeHtml: core.escapeHtml,
      formatOrgRoleLabel: core.formatOrgRoleLabel,
      formatInvitationStatusLabel: core.formatInvitationStatusLabel,
      formatSalesDateLabel: core.formatSalesDateLabel,
      formatMembershipStatusLabel: core.formatMembershipStatusLabel,
      requireAuthSessionRuntime: authState.requireAuthSessionRuntime,
      loadOrganizationUsers: adminData.loadOrganizationUsers,
      loadOrganizationMembers: adminData.loadOrganizationMembers,
      loadSalesOverview: salesPanels.loadSalesOverview,
      loadMySalesClaims: salesPanels.loadMySalesClaims,
      refreshSalesAdminPanels: salesPanels.refreshSalesAdminPanels,
      ensureConsoleInitialized: authState.ensureConsoleInitialized,
      shouldShowSignUpMode: authUi.shouldShowSignUpMode,
      AUTH_MODE_SIGN_IN: authUi.AUTH_MODE_SIGN_IN,
      AUTH_MODE_SIGN_UP: authUi.AUTH_MODE_SIGN_UP,
      syncUiModeChrome: uiMode.syncUiModeChrome,
      syncUiModeFromLocation: uiMode.syncUiModeFromLocation,
      applyUiModeTransition: uiMode.applyUiModeTransition,
      renderAuthUi: authUi.renderAuthUi,
      canUseAdminMode: authState.canUseAdminMode,
      canLoadProtectedConsoleData: authState.canLoadProtectedConsoleData,
      loadAdminConsoleData: adminData.loadAdminConsoleData,
      loadBackfillConflicts: trackerPanels.loadBackfillConflicts,
      renderBackfillConflictsPanel: trackerPanels.renderBackfillConflictsPanel,
      renderTrackerContactResolutionSummary: trackerPanels.renderTrackerContactResolutionSummary,
      renderTrackerCleanupPreview: trackerPanels.renderTrackerCleanupPreview,
      closeDrawer: tracker.closeDrawer,
      hydrateHomeBootstrapCache: authState.hydrateHomeBootstrapCache,
      clearUserModeRunSelection: authState.clearUserModeRunSelection,
      loadHomeBootstrap: authState.loadHomeBootstrap,
      loadTrackerEntries: tracker.loadTrackerEntries,
      getTrackerController: tracker.getTrackerController,
      renderOrganizationAdminPanel: adminData.renderOrganizationAdminPanel,
      renderMySalesClaimsPanel: salesPanels.renderMySalesClaimsPanel,
      renderSalesSummaryPanel: salesPanels.renderSalesSummaryPanel,
      renderRunDetail: trackerPanels.renderRunDetail,
      renderTrackerEntries: tracker.renderTrackerEntries,
    });
  }

  function createAppSupportAuthRuntime() {
    return {
      createAuthControllerDepsHelpers,
      createAuthControllerDepsHelpersFromApp,
    };
  }

  global.SPMSAppSupportAuthRuntime = {
    createAppSupportAuthRuntime,
  };
})(window);
