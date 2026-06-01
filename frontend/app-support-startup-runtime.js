(function attachAppSupportStartupRuntime(global) {
  function normalizeSalesOverviewPayload(payload) {
    return {
      myItems: Array.isArray(payload?.my_items) ? payload.my_items : [],
      companyItems: Array.isArray(payload?.company_items) ? payload.company_items : [],
      organizationUsers: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
    };
  }

  function buildSalesOverviewCachePayloadFallback(payload) {
    const normalized = normalizeSalesOverviewPayload(payload);
    return {
      my_items: normalized.myItems,
      company_items: normalized.companyItems,
      organization_users: normalized.organizationUsers,
    };
  }

  function mergeSalesOverviewIntoHomeBootstrapPayloadFallback(existingPayload, salesPayload) {
    const currentPayload =
      existingPayload && typeof existingPayload === "object" && !Array.isArray(existingPayload)
        ? existingPayload
        : {};
    return {
      ...currentPayload,
      ...buildSalesOverviewCachePayloadFallback(salesPayload),
    };
  }

  function buildHomeBootstrapCachePayloadFallback(payload) {
    return {
      ...buildSalesOverviewCachePayloadFallback(payload),
      tracker_first_page: payload?.tracker_first_page && typeof payload?.tracker_first_page === "object"
        ? payload.tracker_first_page
        : { items: [], page: 1, page_size: 20, total: 0, sort_contract: { mode: "default", order_by: [] } },
      generated_at: payload?.generated_at || "",
      snapshot_version: Number(payload?.snapshot_version || 1) || 1,
    };
  }

  function hasCachedSalesOverviewData(context = {}) {
    return Boolean(
      context?.mySalesClaims?.length
      || context?.companySalesClaims?.length
      || context?.organizationUsers?.length,
    );
  }

  function hasCachedHomeBootstrapData(context = {}) {
    return Boolean(
      context?.homeBootstrapTrackerSnapshotActive
      || context?.mySalesClaims?.length
      || context?.companySalesClaims?.length
      || context?.organizationUsers?.length,
    );
  }

  function isMissingSalesOverviewEndpointError(error) {
    const isOverview404 =
      Number(error?.status || 0) === 404
      && String(error?.path || "").startsWith("/api/sales-claims/overview");
    if (!isOverview404) {
      return false;
    }
    const payload = error?.payload;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return true;
    }
    const errorPayload = payload?.error;
    if (!errorPayload || typeof errorPayload !== "object") {
      return true;
    }
    const errorCode = String(errorPayload.code || "").trim();
    return !errorCode;
  }

  function isMissingHomeBootstrapEndpointError(error) {
    return (
      Number(error?.status || 0) === 404
      && String(error?.path || "").startsWith("/api/home-bootstrap")
    );
  }

  function isOutOfRangePageError(error) {
    const message = String(error && error.message ? error.message : error || "").toLowerCase();
    return message.includes("requested range not satisfiable") || message.includes("offset of");
  }

  function extractOutOfRangeTotalRows(error) {
    const message = String(error && error.message ? error.message : error || "");
    const match = message.match(/there are only\s+(\d+)\s+rows/i);
    return match ? Number(match[1]) || 0 : 0;
  }

  function buildStorageIdentity(authUser) {
    const organizationId = String(authUser?.organization_id || "").trim();
    const userId = String(authUser?.local_user_id || "").trim();
    const email = String(authUser?.email || "").trim().toLowerCase();
    return `${organizationId}|${userId}|${email}`;
  }

  function createBootstrapCacheHelpers(options = {}) {
    const {
      state = {},
      cacheRuntime = null,
      buildStorageIdentity = () => "",
      orgAdminBootstrapStorageKey = "",
    } = options;

    function buildSalesOverviewStorageIdentity() {
      return buildStorageIdentity(state.auth?.user) || "";
    }

    function readConsoleCacheEnvelope(storageKey, { allowStale = false } = {}) {
      if (!cacheRuntime || !state.auth?.user) {
        return null;
      }
      return cacheRuntime.readEnvelope(storageKey, {
        identity: buildSalesOverviewStorageIdentity(),
        maxAgeMs: cacheRuntime.DEFAULT_MAX_AGE_MS,
        allowStale,
      });
    }

    function writeConsoleCacheEnvelope(storageKey, payload) {
      if (!cacheRuntime || !state.auth?.user) {
        return false;
      }
      return cacheRuntime.writeEnvelope(storageKey, {
        identity: buildSalesOverviewStorageIdentity(),
        payload,
        cachedAt: Date.now(),
      });
    }

    function buildOrganizationAdminBootstrapCachePayload(payload) {
      return {
        members: Array.isArray(payload?.members) ? payload.members : [],
        plan_summary: payload?.plan_summary && typeof payload.plan_summary === "object" ? payload.plan_summary : null,
        invitations: Array.isArray(payload?.invitations) ? payload.invitations : [],
        auth_audit_logs: {
          items: Array.isArray(payload?.auth_audit_logs?.items) ? payload.auth_audit_logs.items : [],
          has_more: Boolean(payload?.auth_audit_logs?.has_more),
        },
        download_audit_logs: {
          items: Array.isArray(payload?.download_audit_logs?.items) ? payload.download_audit_logs.items : [],
          has_more: Boolean(payload?.download_audit_logs?.has_more),
        },
        login_audit_logs: {
          items: Array.isArray(payload?.login_audit_logs?.items) ? payload.login_audit_logs.items : [],
          has_more: Boolean(payload?.login_audit_logs?.has_more),
        },
        generated_at: payload?.generated_at || "",
      };
    }

    function readOrganizationAdminBootstrapCache() {
      const parsed = readConsoleCacheEnvelope(orgAdminBootstrapStorageKey, { allowStale: true });
      if (!parsed || typeof parsed.payload !== "object" || !parsed.payload) {
        return null;
      }
      return buildOrganizationAdminBootstrapCachePayload(parsed.payload);
    }

    function persistOrganizationAdminBootstrapCache(payload) {
      return writeConsoleCacheEnvelope(
        orgAdminBootstrapStorageKey,
        buildOrganizationAdminBootstrapCachePayload(payload),
      );
    }

    return {
      buildSalesOverviewStorageIdentity,
      readConsoleCacheEnvelope,
      writeConsoleCacheEnvelope,
      buildOrganizationAdminBootstrapCachePayload,
      readOrganizationAdminBootstrapCache,
      persistOrganizationAdminBootstrapCache,
    };
  }

  function createAppStartupFacade(options = {}) {
    const {
      state = {},
      dom = {},
      windowObject = global,
      documentObject = global?.document || null,
      authSessionHeartbeatMs = 0,
      adminGoogleSheetsRuntime = null,
      canLoadProtectedConsoleData = () => false,
      isAdminGoogleSheetTabKey = () => false,
      isPendingLegacyAdminAlias = () => false,
      mountRuntimeEnhancements = () => {},
      hydrateStateFromUrl = () => {},
      hydrateProjectRelatedPayloadCache = () => {},
      hydratePatchFieldOptions = () => {},
      syncFilterControlsFromState = () => {},
      renderSyncMeta = () => {},
      applyUiMode = () => {},
      bindEvents = () => {},
      renderAuthUi = () => {},
      renderDashboard = () => {},
      renderReport = () => {},
      renderReportJob = () => {},
      importAuthSessionFromLocationHash = async () => {},
      initializeAuthGate = async () => {},
      clearUserModeRunSelection = () => {},
      hydrateHomeBootstrapCache = () => {},
      loadHomeBootstrap = async () => {},
      scheduleTrackerChangeEventsWarmup = () => {},
      hydrateTrackerChangeEventsCache = () => {},
      loadRuns = async () => {},
      loadOrganizationUsers = async () => {},
      loadMySalesClaims = async () => {},
      loadTrackerChangeEventUnreadCount = async () => {},
      loadTrackerChangeEvents = async () => {},
      loadRunPresets = async () => {},
      loadAdminConsoleData = async () => {},
      loadBackfillConflicts = async () => {},
      refreshAuthSessionState = async () => {},
      loadDashboardSummary = async () => {},
      loadReportJobs = async () => {},
      loadPhaseReport = async () => {},
      loadAdminGoogleSheetsBootstrap = async () => {},
    } = options;

    function shouldPollGeneralConsole() {
      if (!state.autoRefresh) return false;
      if (state.uiMode !== "admin") return false;
      const hasRunningRun = (state.runs || []).some((run) => ["queued", "running"].includes(String(run?.status || "")));
      if (hasRunningRun) return true;
      return (state.reportJobs || []).some((job) => ["queued", "running"].includes(String(job?.status || "")));
    }

    function shouldPollAdminGoogleSheets() {
      if (!state.autoRefresh) return false;
      if (state.uiMode !== "admin") return false;
      if (!adminGoogleSheetsRuntime) return false;
      if (!canLoadProtectedConsoleData()) return false;
      return isAdminGoogleSheetTabKey(state.adminTab) || isPendingLegacyAdminAlias();
    }

    function pollGeneralConsoleTick() {
      const shouldPollGeneral = shouldPollGeneralConsole();
      const shouldPollSheets = shouldPollAdminGoogleSheets();
      if (!shouldPollGeneral && !shouldPollSheets) return;
      if (shouldPollGeneral) {
        loadDashboardSummary({ silent: true });
        loadReportJobs({ silent: true });
        loadPhaseReport({ silent: true });
        loadRuns({ silent: true, preservePage: true, source: "interval" });
        loadBackfillConflicts({ silent: true });
      }
      if (shouldPollSheets) {
        void loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
      }
    }

    async function initializeConsole() {
      if (state.uiMode === "user") {
        clearUserModeRunSelection({ sync: true });
        hydrateHomeBootstrapCache();
        void loadHomeBootstrap({ silent: true });
        scheduleTrackerChangeEventsWarmup();
      } else {
        hydrateTrackerChangeEventsCache();
        await loadRuns({ initial: true });
        void loadOrganizationUsers({ silent: true });
        void loadMySalesClaims({ silent: true });
        void loadTrackerChangeEventUnreadCount({ silent: true });
        void loadTrackerChangeEvents({ silent: true });
      }
      void loadRunPresets({ silent: true });
      void loadAdminConsoleData({ silent: true });
      if (state.uiMode === "admin") void loadBackfillConflicts({ silent: true });
      state.runsHandle = windowObject.setInterval(pollGeneralConsoleTick, 60000);
      state.salesClaimsHandle = null;
      if (!state.authSessionHandle) {
        state.authSessionHandle = windowObject.setInterval(() => {
          if (!state.auth?.enabled || !state.auth?.authenticated) return;
          if (documentObject?.visibilityState !== "visible") return;
          void refreshAuthSessionState({ silent: true });
        }, authSessionHeartbeatMs);
      }
    }

    async function ensureConsoleInitialized() {
      if (state.consoleInitialized) return;
      state.consoleInitialized = true;
      await initializeConsole();
    }

    async function boot() {
      mountRuntimeEnhancements();
      hydrateStateFromUrl();
      hydrateProjectRelatedPayloadCache();
      if (dom.apiBaseLabel) {
        dom.apiBaseLabel.textContent = windowObject.location.origin;
      }
      hydratePatchFieldOptions();
      syncFilterControlsFromState();
      renderSyncMeta();
      applyUiMode();
      bindEvents();
      renderAuthUi();
      renderDashboard(null);
      renderReport(null);
      renderReportJob(null);
      await importAuthSessionFromLocationHash();
      await initializeAuthGate();
      if (!state.auth?.enabled || (state.auth?.authenticated && state.auth?.authorized)) {
        await ensureConsoleInitialized();
      }
    }

    return {
      boot,
      ensureConsoleInitialized,
      initializeConsole,
      shouldPollGeneralConsole,
      shouldPollAdminGoogleSheets,
      pollGeneralConsoleTick,
    };
  }

  function createBootstrapRuntimeDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      api = async () => ({}),
      flash = () => {},
      salesStateHelpers = {},
      bootstrapSupport = {},
      canUseAdminMode = () => false,
      mergeOrganizationInvitations = () => {},
      loadTrackerEntries = async () => {},
      renderMySalesClaimsPanel = () => {},
      renderTrackerEntries = () => {},
      renderSalesSummaryPanel = () => {},
      renderOrganizationAdminPanel = () => {},
      applyHomeBootstrapPayload = () => {},
      applySalesOverviewPayload = () => {},
      persistHomeBootstrapCache = () => {},
      persistSalesOverviewCache = () => {},
      resetTrackerBoardEdit = () => {},
      renderEntriesPagination = () => {},
      syncUrlState = () => {},
      useGlobalTrackerEntriesScope = () => true,
      salesOverviewStorageKey = "",
      homeBootstrapStorageKey = "",
      readConsoleCacheEnvelope = () => null,
      writeConsoleCacheEnvelope = () => {},
    } = options;
    const salesStateHelperDeps =
      salesStateHelpers && typeof salesStateHelpers === "object"
        ? salesStateHelpers
        : {};
    const bootstrapSupportDeps =
      bootstrapSupport && typeof bootstrapSupport === "object"
        ? bootstrapSupport
        : {};
    const {
      getVisibleSalesProjectIds = () => [],
      isActiveSalesClaim = () => false,
      isCurrentUserClaimOwner = () => false,
      mergeActiveSalesClaims = () => {},
      replaceVisibleSalesClaims = () => {},
    } = salesStateHelperDeps;
    const {
      normalizeSalesOverviewPayload = (payload) => payload || {},
      buildSalesOverviewCachePayload = (payload) => payload || {},
      mergeSalesOverviewIntoHomeBootstrapPayload = (existingPayload, salesPayload) => ({
        ...(existingPayload && typeof existingPayload === "object" ? existingPayload : {}),
        ...(salesPayload && typeof salesPayload === "object" ? salesPayload : {}),
      }),
      buildHomeBootstrapCachePayload = (payload) => payload || {},
      hasCachedSalesOverviewData = () => false,
      hasCachedHomeBootstrapData = () => false,
      isMissingSalesOverviewEndpointError = () => false,
      isMissingHomeBootstrapEndpointError = () => false,
    } = bootstrapSupportDeps;

    function buildConsoleDataRuntimeDeps() {
      return {
        state,
        api,
        flash,
        canUseAdminMode,
        getVisibleSalesProjectIds,
        isActiveSalesClaim,
        isCurrentUserClaimOwner,
        mergeActiveSalesClaims,
        mergeOrganizationInvitations,
        replaceVisibleSalesClaims,
        loadTrackerEntries,
        renderMySalesClaimsPanel,
        renderTrackerEntries,
        renderSalesSummaryPanel,
        renderOrganizationAdminPanel,
        applyHomeBootstrapPayload,
        applySalesOverviewPayload,
        persistHomeBootstrapCache,
        persistSalesOverviewCache,
        hasCachedHomeBootstrapData,
        hasCachedSalesOverviewData,
        isMissingHomeBootstrapEndpointError,
        isMissingSalesOverviewEndpointError,
      };
    }

    function buildHomeBootstrapRuntimeDeps() {
      return {
        state,
        dom,
        mergeActiveSalesClaims,
        resetTrackerBoardEdit,
        renderEntriesPagination,
        renderMySalesClaimsPanel,
        renderTrackerEntries,
        syncUrlState,
        useGlobalTrackerEntriesScope,
        normalizeSalesOverviewPayload,
        buildSalesOverviewCachePayload,
        mergeSalesOverviewIntoHomeBootstrapPayload,
        buildHomeBootstrapCachePayload,
        salesOverviewStorageKey,
        homeBootstrapStorageKey,
        readConsoleCacheEnvelope,
        writeConsoleCacheEnvelope,
      };
    }

    return {
      buildConsoleDataRuntimeDeps,
      buildHomeBootstrapRuntimeDeps,
    };
  }

  function createAppSupportStartupRuntime(options = {}) {
    const state = options.state || null;
    const bootstrapRuntime = options.bootstrapRuntime || null;

    return {
      buildStorageIdentity(authUser) {
        if (typeof bootstrapRuntime?.buildStorageIdentity === "function") {
          return bootstrapRuntime.buildStorageIdentity(authUser);
        }
        return buildStorageIdentity(authUser);
      },
      normalizeSalesOverviewPayload(payload) {
        if (typeof bootstrapRuntime?.normalizeSalesOverviewPayload === "function") {
          return bootstrapRuntime.normalizeSalesOverviewPayload(payload);
        }
        return normalizeSalesOverviewPayload(payload);
      },
      buildSalesOverviewCachePayload(payload) {
        if (typeof bootstrapRuntime?.buildSalesOverviewCachePayload === "function") {
          return bootstrapRuntime.buildSalesOverviewCachePayload(payload);
        }
        return buildSalesOverviewCachePayloadFallback(payload);
      },
      mergeSalesOverviewIntoHomeBootstrapPayload(existingPayload, salesPayload) {
        if (typeof bootstrapRuntime?.mergeSalesOverviewIntoHomeBootstrapPayload === "function") {
          return bootstrapRuntime.mergeSalesOverviewIntoHomeBootstrapPayload(existingPayload, salesPayload);
        }
        return mergeSalesOverviewIntoHomeBootstrapPayloadFallback(existingPayload, salesPayload);
      },
      buildHomeBootstrapCachePayload(payload) {
        if (typeof bootstrapRuntime?.buildHomeBootstrapCachePayload === "function") {
          return bootstrapRuntime.buildHomeBootstrapCachePayload(payload);
        }
        return buildHomeBootstrapCachePayloadFallback(payload);
      },
      hasCachedSalesOverviewData(context = {}) {
        if (typeof bootstrapRuntime?.hasCachedSalesOverviewData === "function") {
          return bootstrapRuntime.hasCachedSalesOverviewData({
            mySalesClaims: state?.mySalesClaims,
            companySalesClaims: state?.companySalesClaims,
            organizationUsers: state?.organizationUsers,
            ...context,
          });
        }
        return hasCachedSalesOverviewData({
          mySalesClaims: state?.mySalesClaims,
          companySalesClaims: state?.companySalesClaims,
          organizationUsers: state?.organizationUsers,
          ...context,
        });
      },
      hasCachedHomeBootstrapData(context = {}) {
        if (typeof bootstrapRuntime?.hasCachedHomeBootstrapData === "function") {
          return bootstrapRuntime.hasCachedHomeBootstrapData({
            homeBootstrapTrackerSnapshotActive: state?.homeBootstrapTrackerSnapshotActive,
            mySalesClaims: state?.mySalesClaims,
            companySalesClaims: state?.companySalesClaims,
            organizationUsers: state?.organizationUsers,
            ...context,
          });
        }
        return hasCachedHomeBootstrapData({
          homeBootstrapTrackerSnapshotActive: state?.homeBootstrapTrackerSnapshotActive,
          mySalesClaims: state?.mySalesClaims,
          companySalesClaims: state?.companySalesClaims,
          organizationUsers: state?.organizationUsers,
          ...context,
        });
      },
      isMissingSalesOverviewEndpointError(error) {
        if (typeof bootstrapRuntime?.isMissingSalesOverviewEndpointError === "function") {
          return bootstrapRuntime.isMissingSalesOverviewEndpointError(error);
        }
        return isMissingSalesOverviewEndpointError(error);
      },
      isMissingHomeBootstrapEndpointError(error) {
        if (typeof bootstrapRuntime?.isMissingHomeBootstrapEndpointError === "function") {
          return bootstrapRuntime.isMissingHomeBootstrapEndpointError(error);
        }
        return isMissingHomeBootstrapEndpointError(error);
      },
      isOutOfRangePageError,
      extractOutOfRangeTotalRows,
      createBootstrapCacheHelpers,
      createAppStartupFacade,
      createBootstrapRuntimeDepsHelpers,
    };
  }

  global.SPMSAppSupportStartupRuntime = {
    createAppSupportStartupRuntime,
  };
})(window);
