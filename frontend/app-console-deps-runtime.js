(function attachAppConsoleDepsRuntime(global) {
  function toGetterName(name) {
    return `get${String(name).charAt(0).toUpperCase()}${String(name).slice(1)}`;
  }

  function resolveOption(options, name) {
    const getter = options?.[toGetterName(name)];
    if (typeof getter === "function") {
      return getter();
    }
    return options?.[name];
  }

  function requireRuntime(runtime, message) {
    if (!runtime) {
      throw new Error(message);
    }
    return runtime;
  }

  function requireAppBootstrapBridge(getAppBootstrapBridge) {
    const bridge = typeof getAppBootstrapBridge === "function" ? getAppBootstrapBridge() : null;
    if (!bridge || typeof bridge !== "object") {
      throw new Error("appBootstrapBridge is required before app.js loads");
    }
    return bridge;
  }

  function createAppConsoleDepsRuntime(options = {}) {
    const state = options.state || {};
    const api = options.api;
    const flash = options.flash;
    const getAppBootstrapBridge = options.getAppBootstrapBridge;

    function requireConsoleDataRuntime() {
      return requireRuntime(resolveOption(options, "consoleDataRuntime"), "SPMSConsoleDataRuntime is not available.");
    }

    function requireAuthSessionRuntime() {
      return requireRuntime(resolveOption(options, "authSessionRuntime"), "SPMSAuthSessionRuntime is not available.");
    }

    function requireOrganizationAdminRuntime() {
      return requireRuntime(resolveOption(options, "organizationAdminRuntime"), "SPMSOrgAdminRuntime is not available.");
    }

    function requireTrackerDiagnosticsRuntime() {
      return requireRuntime(resolveOption(options, "trackerDiagnosticsRuntime"), "SPMSTrackerDiagnosticsRuntime is not available.");
    }

    function requireSelectedEntryRuntime() {
      return requireRuntime(resolveOption(options, "selectedEntryRuntime"), "SPMSSelectedEntryRuntime is not available.");
    }

    function readConsoleCacheEnvelope(storageKey, { allowStale = false } = {}) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).readConsoleCacheEnvelope(storageKey, { allowStale });
    }

    function writeConsoleCacheEnvelope(storageKey, payload) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).writeConsoleCacheEnvelope(storageKey, payload);
    }

    function applyHomeBootstrapPayload(payload) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).applyHomeBootstrapPayload(payload);
    }

    function hydrateHomeBootstrapCache() {
      return requireAppBootstrapBridge(getAppBootstrapBridge).hydrateHomeBootstrapCache();
    }

    function persistSalesOverviewCache(payload) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).persistSalesOverviewCache(payload);
    }

    function syncHomeBootstrapSalesCache(payload) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).syncHomeBootstrapSalesCache(payload);
    }

    function persistHomeBootstrapCache(payload) {
      return requireAppBootstrapBridge(getAppBootstrapBridge).persistHomeBootstrapCache(payload);
    }

    function shouldUseHomeBootstrapTrackerSnapshot() {
      return requireAppBootstrapBridge(getAppBootstrapBridge).shouldUseHomeBootstrapTrackerSnapshot();
    }

    function syncUrlState() {
      return requireAppBootstrapBridge(getAppBootstrapBridge).syncUrlState();
    }

    function getConsoleDataRuntimeDeps() {
      return {
        state,
        api,
        flash,
        canUseAdminMode: resolveOption(options, "canUseAdminMode"),
        getVisibleSalesProjectIds: resolveOption(options, "getVisibleSalesProjectIds"),
        isActiveSalesClaim: resolveOption(options, "isActiveSalesClaim"),
        isCurrentUserClaimOwner: resolveOption(options, "isCurrentUserClaimOwner"),
        mergeActiveSalesClaims: resolveOption(options, "mergeActiveSalesClaims"),
        mergeOrganizationInvitations: resolveOption(options, "mergeOrganizationInvitations"),
        replaceVisibleSalesClaims: resolveOption(options, "replaceVisibleSalesClaims"),
        loadTrackerEntries: resolveOption(options, "loadTrackerEntries"),
        renderMySalesClaimsPanel: resolveOption(options, "renderMySalesClaimsPanel"),
        renderTrackerEntries: resolveOption(options, "renderTrackerEntries"),
        renderSalesSummaryPanel: resolveOption(options, "renderSalesSummaryPanel"),
        renderOrganizationAdminPanel: resolveOption(options, "renderOrganizationAdminPanel"),
        applyHomeBootstrapPayload,
        persistHomeBootstrapCache,
        persistSalesOverviewCache,
        hasCachedHomeBootstrapData: resolveOption(options, "hasCachedHomeBootstrapData"),
        hasCachedSalesOverviewData: resolveOption(options, "hasCachedSalesOverviewData"),
        isMissingHomeBootstrapEndpointError: resolveOption(options, "isMissingHomeBootstrapEndpointError"),
        isMissingSalesOverviewEndpointError: resolveOption(options, "isMissingSalesOverviewEndpointError"),
      };
    }

    async function loadVisibleSalesClaims({ silent = false } = {}) {
      return requireConsoleDataRuntime().loadVisibleSalesClaims(getConsoleDataRuntimeDeps(), { silent });
    }

    async function loadHomeBootstrap({ silent = false, force = false } = {}) {
      return requireConsoleDataRuntime().loadHomeBootstrap(getConsoleDataRuntimeDeps(), { silent, force });
    }

    async function loadHomeBootstrapFromLegacy({ silent = false } = {}) {
      return requireConsoleDataRuntime().loadHomeBootstrapFromLegacy(getConsoleDataRuntimeDeps(), { silent });
    }

    async function loadSalesOverview({ silent = false, force = false } = {}) {
      return requireConsoleDataRuntime().loadSalesOverview(getConsoleDataRuntimeDeps(), { silent, force });
    }

    async function loadSalesOverviewFromLegacy({ silent = false, persistCache = false } = {}) {
      return requireConsoleDataRuntime().loadSalesOverviewFromLegacy(getConsoleDataRuntimeDeps(), { silent, persistCache });
    }

    async function loadMySalesClaims({ silent = false } = {}) {
      return requireConsoleDataRuntime().loadMySalesClaims(getConsoleDataRuntimeDeps(), { silent });
    }

    async function loadClosedSalesClaims({ silent = false } = {}) {
      return requireConsoleDataRuntime().loadClosedSalesClaims(getConsoleDataRuntimeDeps(), { silent });
    }

    function refreshSalesAdminPanels({ silent = false } = {}) {
      return requireConsoleDataRuntime().refreshSalesAdminPanels(getConsoleDataRuntimeDeps(), { silent });
    }

    async function loadSalesClaimSummaryByUser({ silent = false } = {}) {
      return requireConsoleDataRuntime().loadSalesClaimSummaryByUser(getConsoleDataRuntimeDeps(), { silent });
    }

    function formatAccountStatusLabel(status) {
      return requireOrganizationAdminRuntime().formatAccountStatusLabel(status);
    }

    function formatMembershipStatusLabel(status) {
      return requireOrganizationAdminRuntime().formatMembershipStatusLabel(status);
    }

    function resolveStatusClass(status) {
      return requireOrganizationAdminRuntime().resolveStatusClass(status);
    }

    return {
      readConsoleCacheEnvelope,
      writeConsoleCacheEnvelope,
      getConsoleDataRuntimeDeps,
      requireConsoleDataRuntime,
      requireAuthSessionRuntime,
      requireOrganizationAdminRuntime,
      requireTrackerDiagnosticsRuntime,
      requireSelectedEntryRuntime,
      applyHomeBootstrapPayload,
      hydrateHomeBootstrapCache,
      persistSalesOverviewCache,
      syncHomeBootstrapSalesCache,
      persistHomeBootstrapCache,
      shouldUseHomeBootstrapTrackerSnapshot,
      syncUrlState,
      loadVisibleSalesClaims,
      loadHomeBootstrap,
      loadHomeBootstrapFromLegacy,
      loadSalesOverview,
      loadSalesOverviewFromLegacy,
      loadMySalesClaims,
      loadClosedSalesClaims,
      refreshSalesAdminPanels,
      loadSalesClaimSummaryByUser,
      formatAccountStatusLabel,
      formatMembershipStatusLabel,
      resolveStatusClass,
    };
  }

  global.SPMSAppConsoleDepsRuntime = {
    createAppConsoleDepsRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
