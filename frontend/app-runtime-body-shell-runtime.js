(function initAppRuntimeBodyShellRuntime(global) {
  const CANONICAL_APP_URL = "/";
  const CANONICAL_URL_STATE_STORAGE_KEY = "notice-winner-pipeline-web.canonicalUrlState.v1";

  function writeCanonicalUrlStateSearch(params) {
    try {
      const next = params instanceof URLSearchParams ? params.toString() : String(params || "");
      if (next) {
        global?.sessionStorage?.setItem?.(CANONICAL_URL_STATE_STORAGE_KEY, next);
      } else {
        global?.sessionStorage?.removeItem?.(CANONICAL_URL_STATE_STORAGE_KEY);
      }
    } catch (_error) {
      // Storage can be unavailable; keeping the visible URL canonical is more important.
    }
  }

  function createBootstrapSalesStateHelpers({
    salesStateHelpers,
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
  } = {}) {
    if (typeof salesStateHelpers !== "undefined" && salesStateHelpers) {
      return salesStateHelpers;
    }
    return {
      getVisibleSalesProjectIds: typeof getVisibleSalesProjectIds === "function" ? getVisibleSalesProjectIds : () => [],
      getSalesClaimForProject: typeof getSalesClaimForProject === "function" ? getSalesClaimForProject : () => null,
      getTrackerProjectSnapshot: typeof getTrackerProjectSnapshot === "function" ? getTrackerProjectSnapshot : () => null,
      renderUserSalesProjectFacts: typeof renderUserSalesProjectFacts === "function" ? renderUserSalesProjectFacts : () => "",
      isCurrentUserClaimOwner: typeof isCurrentUserClaimOwner === "function" ? isCurrentUserClaimOwner : () => true,
      canCurrentUserForceRelease: typeof canCurrentUserForceRelease === "function" ? canCurrentUserForceRelease : () => false,
      canCurrentUserManageClaim: typeof canCurrentUserManageClaim === "function" ? canCurrentUserManageClaim : () => false,
      isActiveSalesClaim: typeof isActiveSalesClaim === "function" ? isActiveSalesClaim : () => false,
      getOrganizationTransferTargets: typeof getOrganizationTransferTargets === "function" ? getOrganizationTransferTargets : () => [],
      getSalesNoteDraft: typeof getSalesNoteDraft === "function" ? getSalesNoteDraft : () => "",
      setSalesNoteDraft: typeof setSalesNoteDraft === "function" ? setSalesNoteDraft : () => {},
      upsertSalesClaim: typeof upsertSalesClaim === "function" ? upsertSalesClaim : () => {},
      replaceVisibleSalesClaims: typeof replaceVisibleSalesClaims === "function" ? replaceVisibleSalesClaims : () => {},
      mergeActiveSalesClaims: typeof mergeActiveSalesClaims === "function" ? mergeActiveSalesClaims : () => {},
      formatShortDateTime: typeof formatShortDateTime === "function" ? formatShortDateTime : () => "",
      formatEstimatedAmountRangeFromKrw: typeof formatEstimatedAmountRangeFromKrw === "function" ? formatEstimatedAmountRangeFromKrw : () => "",
    };
  }

  function buildUrlForState({
    state,
    pathname = null,
    uiMode,
    adminTab,
    defaultAdminTab,
    locationPathname,
    resolveStatePathname,
    persist = false,
  } = {}) {
    const params = new URLSearchParams();
    if (state.runFilters.status) params.set("run_status", state.runFilters.status);
    if (state.runFilters.runType) params.set("run_type", state.runFilters.runType);
    if (state.runFilters.from) params.set("run_from", state.runFilters.from);
    if (state.runFilters.to) params.set("run_to", state.runFilters.to);
    if (state.runFilters.page !== 1) params.set("run_page", String(state.runFilters.page));
    if (state.runFilters.pageSize !== 20) params.set("run_page_size", String(state.runFilters.pageSize));
    if (state.selectedRunId) params.set("run_id", state.selectedRunId);
    if (state.selectedTrackerRunId) params.set("tracker_run_id", state.selectedTrackerRunId);
    if (state.trackerFilters.q) params.set("tracker_q", state.trackerFilters.q);
    if (state.trackerFilters.region) params.set("tracker_region", state.trackerFilters.region);
    if (state.trackerFilters.editedOnly) params.set("tracker_edited", "1");
    if (state.trackerFilters.page !== 1) params.set("tracker_page", String(state.trackerFilters.page));
    if (state.trackerFilters.pageSize !== 20) params.set("tracker_page_size", String(state.trackerFilters.pageSize));
    if (!state.autoRefresh) params.set("auto_refresh", "0");
    if (state.reportKey && state.reportKey !== "phase1-artifact-diff") params.set("report_key", state.reportKey);
    if (state.selectedReportJobId) params.set("report_job_id", state.selectedReportJobId);
    if (uiMode === "admin") params.set("mode", "admin");
    if (adminTab && adminTab !== defaultAdminTab) params.set("admin_tab", adminTab);
    if (persist) {
      writeCanonicalUrlStateSearch(params);
    }
    return CANONICAL_APP_URL;
  }

  function syncUrlState({ state, windowObject, buildUrlForStateFn }, options = {}) {
    const { historyMode = "replace" } = options;
    const nextUrl = buildUrlForStateFn({ ...options, persist: true });
    const canonicalSearch = String(windowObject?.sessionStorage?.getItem?.(CANONICAL_URL_STATE_STORAGE_KEY) || "");
    if (state && typeof state === "object") {
      state.canonicalUrlStateHydrated = true;
      state.canonicalUrlStateSource = canonicalSearch ? "storage" : "";
      state.canonicalLocationPathname = windowObject?.location?.pathname || CANONICAL_APP_URL;
      state.canonicalLocationSearch = canonicalSearch ? `?${canonicalSearch}` : "";
    }
    if (historyMode === "push") {
      windowObject.history.pushState({}, "", nextUrl);
      return;
    }
    windowObject.history.replaceState({}, "", nextUrl);
  }

  function openDrawer({ state, dom }) {
    state.drawerOpen = true;
    dom.entryDrawer.classList.remove("hidden");
    dom.entryDrawer.setAttribute("aria-hidden", "false");
  }

  function closeDrawer({ state, dom }) {
    state.drawerOpen = false;
    dom.entryDrawer.classList.add("hidden");
    dom.entryDrawer.setAttribute("aria-hidden", "true");
  }

  function syncFilterControlsFromState({ state, dom, renderTrackerRegionButtons }) {
    dom.runFilterStatus.value = state.runFilters.status;
    dom.runFilterType.value = state.runFilters.runType;
    dom.runFilterFrom.value = state.runFilters.from;
    dom.runFilterTo.value = state.runFilters.to;
    dom.runPageSize.value = String(state.runFilters.pageSize);
    dom.trackerQuery.value = state.trackerFilters.q;
    renderTrackerRegionButtons();
    dom.trackerPageSize.value = String(state.trackerFilters.pageSize);
    dom.reportSelect.value = state.reportKey;
  }

  function readRunFiltersFromControls({ state, dom }) {
    state.runFilters.status = dom.runFilterStatus.value;
    state.runFilters.runType = dom.runFilterType.value;
    state.runFilters.from = dom.runFilterFrom.value;
    state.runFilters.to = dom.runFilterTo.value;
    state.runFilters.pageSize = Number(dom.runPageSize.value || 20);
  }

  global.SPMSAppRuntimeBodyShellRuntime = {
    createBootstrapSalesStateHelpers,
    buildUrlForState,
    syncUrlState,
    openDrawer,
    closeDrawer,
    syncFilterControlsFromState,
    readRunFiltersFromControls,
  };
})(typeof window !== "undefined" ? window : globalThis);
