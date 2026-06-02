export function createAppBootstrapBridge(context = {}) {
  const DEFAULT_ADMIN_TAB = "project-status";
  const SALES_RECOMMENDATIONS_ADMIN_TAB = "sales-recommendations";
  const DEFAULT_REPORT_KEY = "phase1-artifact-diff";
  const APP_ROOT_PATH = "/";
  const LEGACY_APP_ROOT_PATH = "/app";
  const LEGACY_PROJECT_STATUS_ROUTE_PATH = "/app/project-status";
  const SALES_RECOMMENDATIONS_ROUTE_PATH = "/app/sales-recommendations";
  const DEFAULT_ADMIN_ROUTE_PATH = APP_ROOT_PATH;
  const CANONICAL_URL_STATE_STORAGE_KEY = "notice-winner-pipeline-web.canonicalUrlState.v1";
  const LEGACY_ADMIN_ROUTE_ALIASES = Object.freeze({
    "/app/design-list": true,
    "/app/planned-orders": true,
    "/app/lost": true,
    "/app/agency-list": true,
  });

  const {
    bootstrapRuntime = null,
    state = null,
    window: runtimeWindow = typeof window !== "undefined" ? window : globalThis,
    document: runtimeDocument = runtimeWindow?.document || null,
    AUTH_SESSION_HEARTBEAT_MS = 0,
    loadHomeBootstrap = null,
    callAuthController = null,
    loadRuns = null,
    loadOrganizationUsers = null,
    loadMySalesClaims = null,
    trackerController = null,
    getTrackerController = () => trackerController,
    loadRunPresets = null,
    loadDashboardSummary = null,
    loadReportJobs = null,
    loadPhaseReport = null,
    refreshAuthSessionState = null,
    loadBackfillConflicts = null,
    loadOrganizationAdminData = null,
    loadTrackerTemplateStatus = null,
    loadProjects = null,
    refreshSalesAdminPanels = null,
    loadTrackerContactResolutionSummary = null,
    loadTrackerCleanupPreview = null,
    dom = null,
    mergeActiveSalesClaims = null,
    resetTrackerBoardEdit = null,
    renderEntriesPagination = null,
    renderMySalesClaimsPanel = null,
    renderTrackerEntries = null,
    syncUrlState = null,
    useGlobalTrackerEntriesScope = () => true,
    salesOverviewStorageKey = "",
    homeBootstrapStorageKey = "",
    clampPage = (value, fallback) => fallback,
    normalizeTrackerRegionFilter = (value) => String(value || "").trim(),
  } = context;

  const adminTabsRuntime = runtimeWindow?.SPMSAdminTabsRuntime || globalThis?.SPMSAdminTabsRuntime || null;

  function readBootstrapRuntimeMethod(methodName) {
    const runtimeMethod = bootstrapRuntime?.[methodName];
    return typeof runtimeMethod === "function" ? runtimeMethod : null;
  }

  function requireBootstrapRuntimeMethod(methodName) {
    const runtimeMethod = readBootstrapRuntimeMethod(methodName);
    if (!runtimeMethod) {
      throw new Error(`BOOTSTRAP_RUNTIME.${methodName} is required before app.js loads`);
    }
    return runtimeMethod;
  }

  function normalizeLocationPath(pathname) {
    const raw = String(pathname || "").trim();
    if (!raw) {
      return APP_ROOT_PATH;
    }
    const normalized = raw.endsWith("/") && raw !== "/" ? raw.replace(/\/+$/, "") : raw;
    return normalized || APP_ROOT_PATH;
  }

  function isAppRootRoutePath(pathname) {
    const normalized = normalizeLocationPath(pathname);
    return normalized === APP_ROOT_PATH || normalized === LEGACY_APP_ROOT_PATH;
  }

  function isLegacyProjectStatusRoutePath(pathname) {
    return normalizeLocationPath(pathname) === LEGACY_PROJECT_STATUS_ROUTE_PATH;
  }

  function isSalesRecommendationsRoutePath(pathname) {
    return normalizeLocationPath(pathname) === SALES_RECOMMENDATIONS_ROUTE_PATH;
  }

  function resolveLegacyAdminRoutePath(pathname) {
    const normalized = normalizeLocationPath(pathname);
    return LEGACY_ADMIN_ROUTE_ALIASES[normalized] ? normalized : "";
  }

  function readCanonicalUrlStateSearch() {
    try {
      return String(runtimeWindow?.sessionStorage?.getItem?.(CANONICAL_URL_STATE_STORAGE_KEY) || "");
    } catch (_error) {
      return "";
    }
  }

  function writeCanonicalUrlStateSearch(searchParams) {
    try {
      const next = searchParams instanceof URLSearchParams ? searchParams.toString() : String(searchParams || "");
      if (next) {
        runtimeWindow?.sessionStorage?.setItem?.(CANONICAL_URL_STATE_STORAGE_KEY, next);
      } else {
        runtimeWindow?.sessionStorage?.removeItem?.(CANONICAL_URL_STATE_STORAGE_KEY);
      }
    } catch (_error) {
      // Storage can be unavailable in private modes. URL canonicalization should still work.
    }
  }

  function canonicalizeBrowserUrl() {
    const pathname = runtimeWindow?.location?.pathname || APP_ROOT_PATH;
    const search = runtimeWindow?.location?.search || "";
    if (normalizeLocationPath(pathname) !== APP_ROOT_PATH || search) {
      runtimeWindow?.history?.replaceState?.({}, "", APP_ROOT_PATH);
    }
  }

  function isProjectStatusRoutePath(pathname = runtimeWindow?.location?.pathname) {
    return isAppRootRoutePath(pathname) || isLegacyProjectStatusRoutePath(pathname);
  }

  function isAdminGoogleSheetTabKey(value) {
    if (typeof adminTabsRuntime?.isAdminGoogleSheetTabKey === "function") {
      return adminTabsRuntime.isAdminGoogleSheetTabKey(value);
    }
    return /^sheet-\d+$/.test(String(value ?? "").trim());
  }

  function normalizeAdminTab(rawValue) {
    if (typeof adminTabsRuntime?.normalizeAdminTab === "function") {
      return adminTabsRuntime.normalizeAdminTab(rawValue, {
        defaultTab: DEFAULT_ADMIN_TAB,
        isAdminGoogleSheetTabKey,
        isBuiltinAdminTabKey: (value) => {
          const key = String(value || "").trim();
          return key === DEFAULT_ADMIN_TAB || key === SALES_RECOMMENDATIONS_ADMIN_TAB;
        },
      });
    }
    const candidate = String(rawValue || "").trim();
    if (!candidate) {
      return DEFAULT_ADMIN_TAB;
    }
    if (candidate === DEFAULT_ADMIN_TAB || candidate === SALES_RECOMMENDATIONS_ADMIN_TAB || isAdminGoogleSheetTabKey(candidate)) {
      return candidate;
    }
    return DEFAULT_ADMIN_TAB;
  }

  function getAdminTabByPathname(pathname) {
    const normalized = normalizeLocationPath(pathname);
    if (isProjectStatusRoutePath(normalized) || resolveLegacyAdminRoutePath(normalized)) {
      return { key: DEFAULT_ADMIN_TAB };
    }
    if (isSalesRecommendationsRoutePath(normalized)) {
      return { key: SALES_RECOMMENDATIONS_ADMIN_TAB };
    }
    return null;
  }

  function resolveUiModeFromLocation(pathname = runtimeWindow?.location?.pathname, search = runtimeWindow?.location?.search) {
    if (typeof adminTabsRuntime?.resolveUiModeFromLocation === "function") {
      return adminTabsRuntime.resolveUiModeFromLocation(pathname, search, {
        canUseAdminMode: () => true,
        isProjectStatusRoutePath,
        isAdminModeRoutePath: (candidate) => isLegacyProjectStatusRoutePath(candidate) || isSalesRecommendationsRoutePath(candidate) || Boolean(resolveLegacyAdminRoutePath(candidate)),
        resolveLegacyAdminRoutePath,
      });
    }
    const params = new URLSearchParams(search || "");
    if (params.get("mode") === "admin") {
      return "admin";
    }
    if (isLegacyProjectStatusRoutePath(pathname) || isSalesRecommendationsRoutePath(pathname) || resolveLegacyAdminRoutePath(pathname)) {
      return "admin";
    }
    return "user";
  }

  function ensureFilterState() {
    if (!state || typeof state !== "object") {
      return;
    }
    if (!state.runFilters || typeof state.runFilters !== "object") {
      state.runFilters = {};
    }
    if (!state.trackerFilters || typeof state.trackerFilters !== "object") {
      state.trackerFilters = {};
    }
    if (!state.auth || typeof state.auth !== "object") {
      state.auth = {};
    }
  }

  function resolveStatePathname({
    pathname = runtimeWindow?.location?.pathname,
    uiMode = state?.uiMode,
    adminTab = state?.adminTab,
  } = {}) {
    if (
      uiMode === "admin"
      || isAdminGoogleSheetTabKey(adminTab)
      || isProjectStatusRoutePath(pathname)
      || resolveLegacyAdminRoutePath(pathname)
    ) {
      return DEFAULT_ADMIN_ROUTE_PATH;
    }
    if (getAdminTabByPathname(pathname)) {
      return APP_ROOT_PATH;
    }
    return pathname || APP_ROOT_PATH;
  }

  function buildUrlForState({
    pathname = null,
    uiMode = state?.uiMode,
    adminTab = state?.adminTab,
    persist = false,
  } = {}) {
    ensureFilterState();
    const params = new URLSearchParams();
    if (state?.runFilters?.status) params.set("run_status", state.runFilters.status);
    if (state?.runFilters?.runType) params.set("run_type", state.runFilters.runType);
    if (state?.runFilters?.from) params.set("run_from", state.runFilters.from);
    if (state?.runFilters?.to) params.set("run_to", state.runFilters.to);
    if (Number(state?.runFilters?.page || 1) !== 1) params.set("run_page", String(state.runFilters.page));
    if (Number(state?.runFilters?.pageSize || 20) !== 20) params.set("run_page_size", String(state.runFilters.pageSize));
    if (state?.selectedRunId) params.set("run_id", state.selectedRunId);
    if (state?.selectedTrackerRunId) params.set("tracker_run_id", state.selectedTrackerRunId);
    if (state?.trackerFilters?.q) params.set("tracker_q", state.trackerFilters.q);
    if (state?.trackerFilters?.region) params.set("tracker_region", state.trackerFilters.region);
    if (state?.trackerFilters?.noticeYear) params.set("tracker_notice_year", state.trackerFilters.noticeYear);
    if (state?.trackerFilters?.editedOnly) params.set("tracker_edited", "1");
    if (Number(state?.trackerFilters?.page || 1) !== 1) params.set("tracker_page", String(state.trackerFilters.page));
    if (Number(state?.trackerFilters?.pageSize || 20) !== 20) params.set("tracker_page_size", String(state.trackerFilters.pageSize));
    if (state?.autoRefresh === false) params.set("auto_refresh", "0");
    if (state?.reportKey && state.reportKey !== DEFAULT_REPORT_KEY) params.set("report_key", state.reportKey);
    if (state?.selectedReportJobId) params.set("report_job_id", state.selectedReportJobId);
    if (uiMode === "admin") {
      params.set("mode", "admin");
    }
    if (adminTab && adminTab !== DEFAULT_ADMIN_TAB) {
      params.set("admin_tab", adminTab);
    }
    if (persist) {
      writeCanonicalUrlStateSearch(params);
    }
    return APP_ROOT_PATH;
  }

  function safeNormalizeTrackerRegionFilter(value) {
    try {
      return normalizeTrackerRegionFilter(value);
    } catch (_error) {
      return String(value || "").trim();
    }
  }

  function safeNormalizeTrackerNoticeYearFilter(value) {
    const text = String(value || "").trim();
    return /^\d{4}$/.test(text) ? text : "";
  }

  function hydrateStateFromUrlFallback() {
    ensureFilterState();
    const urlSearch = runtimeWindow?.location?.search || "";
    const storedSearch = urlSearch ? "" : readCanonicalUrlStateSearch();
    const params = new URLSearchParams(urlSearch || storedSearch || "");
    const pathname = runtimeWindow?.location?.pathname || APP_ROOT_PATH;
    const routeTab = getAdminTabByPathname(pathname);

    state.adminLegacyRoutePath = params.has("admin_tab") ? "" : resolveLegacyAdminRoutePath(pathname);
    state.adminTab = normalizeAdminTab(params.get("admin_tab") || routeTab?.key || DEFAULT_ADMIN_TAB);
    state.uiMode = resolveUiModeFromLocation(pathname, runtimeWindow?.location?.search || "");
    state.runFilters.status = params.get("run_status") || "";
    state.runFilters.runType = params.get("run_type") || "";
    state.runFilters.from = params.get("run_from") || "";
    state.runFilters.to = params.get("run_to") || "";
    state.runFilters.page = clampPage(params.get("run_page"), 1);
    state.runFilters.pageSize = clampPage(params.get("run_page_size"), 20);
    state.selectedRunId = params.get("run_id") || null;
    state.selectedTrackerRunId = params.get("tracker_run_id") || null;
    state.trackerFilters.q = params.get("tracker_q") || "";
    state.trackerFilters.region = safeNormalizeTrackerRegionFilter(params.get("tracker_region") || "");
    state.trackerFilters.noticeYear = safeNormalizeTrackerNoticeYearFilter(params.get("tracker_notice_year") || "");
    state.trackerFilters.editedOnly = params.get("tracker_edited") === "1";
    state.trackerFilters.page = clampPage(params.get("tracker_page"), 1);
    state.trackerFilters.pageSize = clampPage(params.get("tracker_page_size"), 20);
    state.selectedEntryId = params.get("entry_id") || null;
    state.drawerOpen = Boolean(state.selectedEntryId);
    state.autoRefresh = params.get("auto_refresh") !== "0";
    state.reportKey = params.get("report_key") || DEFAULT_REPORT_KEY;
    state.selectedReportJobId = params.get("report_job_id") || null;
    state.auth.inviteToken = params.get("invite_token") || "";
    state.canonicalUrlStateHydrated = true;
    state.canonicalUrlStateSource = urlSearch ? "url" : (storedSearch ? "storage" : "");
    state.canonicalLocationPathname = pathname;
    state.canonicalLocationSearch = urlSearch || (storedSearch ? `?${storedSearch}` : "");

    if (params.has("entry_id")) {
      params.delete("entry_id");
    }
    writeCanonicalUrlStateSearch(params);
    canonicalizeBrowserUrl();
  }

  function syncUrlStateFallback(options = {}) {
    const {
      historyMode = "replace",
      pathname = null,
      uiMode = state?.uiMode,
      adminTab = state?.adminTab,
    } = options || {};
    const nextUrl = buildUrlForState({ pathname, uiMode, adminTab, persist: true });
    const canonicalSearch = readCanonicalUrlStateSearch();
    state.canonicalUrlStateHydrated = true;
    state.canonicalUrlStateSource = canonicalSearch ? "storage" : "";
    state.canonicalLocationPathname = runtimeWindow?.location?.pathname || APP_ROOT_PATH;
    state.canonicalLocationSearch = canonicalSearch ? `?${canonicalSearch}` : "";
    if (historyMode === "push") {
      runtimeWindow?.history?.pushState?.({}, "", nextUrl);
      return;
    }
    runtimeWindow?.history?.replaceState?.({}, "", nextUrl);
  }

  function getConsoleBootstrapRuntimeDeps() {
    return {
      state,
      window: runtimeWindow,
      document: runtimeDocument,
      AUTH_SESSION_HEARTBEAT_MS,
      loadHomeBootstrap,
      callAuthController,
      loadRuns,
      loadOrganizationUsers,
      loadMySalesClaims,
      trackerController: getTrackerController(),
      loadRunPresets,
      loadDashboardSummary,
      loadReportJobs,
      loadPhaseReport,
      refreshAuthSessionState,
      loadBackfillConflicts,
      loadOrganizationAdminData,
      loadTrackerTemplateStatus,
      loadProjects,
      refreshSalesAdminPanels,
      loadTrackerContactResolutionSummary,
      loadTrackerCleanupPreview,
      dom,
      mergeActiveSalesClaims,
      resetTrackerBoardEdit,
      renderEntriesPagination,
      renderMySalesClaimsPanel,
      renderTrackerEntries,
      syncUrlState,
      useGlobalTrackerEntriesScope,
      salesOverviewStorageKey,
      homeBootstrapStorageKey,
    };
  }

  async function ensureConsoleInitialized() {
    return requireBootstrapRuntimeMethod("ensureConsoleInitialized")(getConsoleBootstrapRuntimeDeps());
  }

  async function initializeConsole() {
    return requireBootstrapRuntimeMethod("initializeConsole")(getConsoleBootstrapRuntimeDeps());
  }

  async function loadAdminConsoleData({ silent = false, force = false } = {}) {
    return requireBootstrapRuntimeMethod("loadAdminConsoleData")(getConsoleBootstrapRuntimeDeps(), { silent, force });
  }

  function readConsoleCacheEnvelope(storageKey, { allowStale = false } = {}) {
    return bootstrapRuntime?.readConsoleCacheEnvelope?.({ state }, storageKey, { allowStale }) || null;
  }

  function writeConsoleCacheEnvelope(storageKey, payload) {
    return bootstrapRuntime?.writeConsoleCacheEnvelope?.({ state }, storageKey, payload) || false;
  }

  function applyHomeBootstrapPayload(payload) {
    return bootstrapRuntime?.applyHomeBootstrapPayload?.({
      state,
      dom,
      mergeActiveSalesClaims,
      resetTrackerBoardEdit,
      renderEntriesPagination,
      renderMySalesClaimsPanel,
      renderTrackerEntries,
      syncUrlState,
    }, payload || {});
  }

  function hydrateHomeBootstrapCache() {
    return requireBootstrapRuntimeMethod("hydrateHomeBootstrapCache")(getConsoleBootstrapRuntimeDeps());
  }

  function persistSalesOverviewCache(payload) {
    return requireBootstrapRuntimeMethod("persistSalesOverviewCache")(getConsoleBootstrapRuntimeDeps(), payload);
  }

  function syncHomeBootstrapSalesCache(payload) {
    return requireBootstrapRuntimeMethod("syncHomeBootstrapSalesCache")(getConsoleBootstrapRuntimeDeps(), payload);
  }

  function persistHomeBootstrapCache(payload) {
    return requireBootstrapRuntimeMethod("persistHomeBootstrapCache")(getConsoleBootstrapRuntimeDeps(), payload);
  }

  function shouldUseHomeBootstrapTrackerSnapshot() {
    const runtimeResult = bootstrapRuntime?.shouldUseHomeBootstrapTrackerSnapshot?.(getConsoleBootstrapRuntimeDeps());
    return runtimeResult || bootstrapRuntime?.canUseHomeBootstrapTrackerSnapshot({
      uiMode: state?.uiMode,
      globalScope: useGlobalTrackerEntriesScope(),
      snapshotActive: state?.homeBootstrapTrackerSnapshotActive,
      query: state?.trackerFilters?.q,
      region: state?.trackerFilters?.region,
      noticeYear: state?.trackerFilters?.noticeYear,
      editedOnly: state?.trackerFilters?.editedOnly,
      page: state?.trackerFilters?.page,
    }) || (
      state?.uiMode === "user"
      && useGlobalTrackerEntriesScope()
      && state?.homeBootstrapTrackerSnapshotActive
      && !String(state?.trackerFilters?.q || "").trim()
      && !String(state?.trackerFilters?.region || "").trim()
      && !String(state?.trackerFilters?.noticeYear || "").trim()
      && !state?.trackerFilters?.editedOnly
      && Number(state?.trackerFilters?.page || 1) === 1
    );
  }

  function hydrateStateFromUrl() {
    const runtimeMethod = readBootstrapRuntimeMethod("hydrateStateFromUrl");
    if (runtimeMethod) {
      const result = runtimeMethod({
        state,
        window: runtimeWindow,
        clampPage,
        normalizeTrackerRegionFilter,
      });
      canonicalizeBrowserUrl();
      return result;
    }
    return hydrateStateFromUrlFallback();
  }

  function syncUrlStateBridge(options = {}) {
    const runtimeMethod = readBootstrapRuntimeMethod("syncUrlState");
    if (runtimeMethod) {
      return runtimeMethod({
        state,
        window: runtimeWindow,
      }, options);
    }
    if (typeof syncUrlState === "function") {
      return syncUrlState(options);
    }
    return syncUrlStateFallback(options);
  }

  function shouldPollGeneralConsole() {
    return requireBootstrapRuntimeMethod("shouldPollGeneralConsole")(getConsoleBootstrapRuntimeDeps());
  }

  function clearUserModeRunSelection({ sync = false } = {}) {
    return requireBootstrapRuntimeMethod("clearUserModeRunSelection")(getConsoleBootstrapRuntimeDeps(), { sync });
  }

  return {
    getConsoleBootstrapRuntimeDeps,
    ensureConsoleInitialized,
    initializeConsole,
    loadAdminConsoleData,
    readConsoleCacheEnvelope,
    writeConsoleCacheEnvelope,
    applyHomeBootstrapPayload,
    hydrateHomeBootstrapCache,
    persistSalesOverviewCache,
    syncHomeBootstrapSalesCache,
    persistHomeBootstrapCache,
    shouldUseHomeBootstrapTrackerSnapshot,
    hydrateStateFromUrl,
    syncUrlState: syncUrlStateBridge,
    shouldPollGeneralConsole,
    clearUserModeRunSelection,
  };
}

const appBootstrapBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appBootstrapBridgeRoot.APP_BOOTSTRAP_BRIDGE = appBootstrapBridgeRoot.APP_BOOTSTRAP_BRIDGE || {};
appBootstrapBridgeRoot.APP_BOOTSTRAP_BRIDGE.createAppBootstrapBridge = createAppBootstrapBridge;
