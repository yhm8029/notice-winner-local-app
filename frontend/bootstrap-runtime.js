(function attachBootstrapRuntime(global) {
  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function normalizePlainObject(value) {
    return isPlainObject(value) ? value : {};
  }

  function buildStorageIdentity(authUser) {
    const organizationId = String(authUser?.organization_id || "").trim();
    const userId = String(authUser?.local_user_id || "").trim();
    const email = String(authUser?.email || "").trim().toLowerCase();
    return `${organizationId}|${userId}|${email}`;
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

  function normalizeSalesOverviewPayload(payload) {
    return {
      myItems: Array.isArray(payload?.my_items) ? payload.my_items : [],
      companyItems: Array.isArray(payload?.company_items) ? payload.company_items : [],
      organizationUsers: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
    };
  }

  function buildSalesOverviewCachePayload(payload) {
    const normalized = normalizeSalesOverviewPayload(payload);
    return {
      my_items: normalized.myItems,
      company_items: normalized.companyItems,
      organization_users: normalized.organizationUsers,
    };
  }

  function mergeSalesOverviewIntoHomeBootstrapPayload(existingPayload, salesPayload) {
    const currentPayload = normalizePlainObject(existingPayload);
    return {
      ...currentPayload,
      ...buildSalesOverviewCachePayload(salesPayload),
    };
  }

  function buildHomeBootstrapCachePayload(payload) {
    const trackerFirstPage = normalizeTrackerFirstPagePayload(payload?.tracker_first_page);
    return {
      ...buildSalesOverviewCachePayload(payload),
      tracker_first_page: trackerFirstPage,
      generated_at: payload?.generated_at || "",
      snapshot_version: Number(payload?.snapshot_version || 1) || 1,
    };
  }

  function normalizeTrackerFirstPagePayload(payload, fallbackPageSize = 20) {
    const currentPayload = normalizePlainObject(payload);
    return {
      items: Array.isArray(currentPayload.items) ? currentPayload.items : [],
      page: Number(currentPayload.page || 1) || 1,
      page_size: Number(currentPayload.page_size || fallbackPageSize || 20) || 20,
      total: Number(currentPayload.total || 0) || 0,
      sort_contract:
        isPlainObject(currentPayload.sort_contract)
          ? currentPayload.sort_contract
          : { mode: "default", order_by: [] },
    };
  }

  function mergeTrackerEntriesById(previousEntries, nextEntries) {
    const previousMap = new Map((Array.isArray(previousEntries) ? previousEntries : []).map((entry) => [entry.id, entry]));
    return (Array.isArray(nextEntries) ? nextEntries : []).map((entry) => ({
      ...(previousMap.get(entry.id) || {}),
      ...entry,
    }));
  }

  function canUseHomeBootstrapTrackerSnapshot(input) {
    return (
      input?.uiMode === "user"
      && Boolean(input?.globalScope)
      && Boolean(input?.snapshotActive)
      && !String(input?.query || "").trim()
      && !String(input?.region || "").trim()
      && !String(input?.noticeYear || "").trim()
      && !Boolean(input?.editedOnly)
      && Number(input?.page || 1) === 1
    );
  }

  function hasCachedSalesOverviewData(snapshotState) {
    return Boolean(
      snapshotState?.mySalesClaims?.length
      || snapshotState?.companySalesClaims?.length
      || snapshotState?.organizationUsers?.length
    );
  }

  function hasCachedHomeBootstrapData(snapshotState) {
    return Boolean(
      snapshotState?.homeBootstrapTrackerSnapshotActive
      || hasCachedSalesOverviewData(snapshotState)
    );
  }

  async function callIfFunction(fn, ...args) {
    return typeof fn === "function" ? fn(...args) : undefined;
  }

  async function loadAdminConsoleData(deps = {}, { silent = false, force = false } = {}) {
    if (deps.state?.uiMode !== "admin") {
      return;
    }
    await Promise.allSettled([
      callIfFunction(deps.loadDashboardSummary, { silent }),
      callIfFunction(deps.loadReportJobs, { silent }),
      callIfFunction(deps.loadPhaseReport, { silent }),
      callIfFunction(deps.loadRuns, { silent, preservePage: true }),
      callIfFunction(deps.loadProjects, { silent }),
      callIfFunction(deps.loadOrganizationAdminData, { silent, force }),
      callIfFunction(deps.loadTrackerTemplateStatus, { silent }),
      callIfFunction(deps.loadBackfillConflicts, { silent }),
    ]);
  }

  async function initializeConsole(deps = {}) {
    if (deps.state?.uiMode === "user") {
      await callIfFunction(deps.loadHomeBootstrap, { silent: true });
    } else {
      await callIfFunction(deps.loadRuns, { initial: true });
      void callIfFunction(deps.loadOrganizationUsers, { silent: true });
      void callIfFunction(deps.loadMySalesClaims, { silent: true });
    }
    void callIfFunction(deps.loadRunPresets, { silent: true });
    void loadAdminConsoleData(deps, { silent: true });
    if (deps.state?.uiMode === "admin") {
      void callIfFunction(deps.loadBackfillConflicts, { silent: true });
    }
    if (deps.state) {
      deps.state.consoleInitialized = true;
    }
  }

  async function ensureConsoleInitialized(deps = {}) {
    if (deps.state?.consoleInitialized) {
      return;
    }
    await initializeConsole(deps);
  }

  const bootstrapRuntime = {
    buildStorageIdentity,
    isMissingSalesOverviewEndpointError,
    isMissingHomeBootstrapEndpointError,
    normalizeSalesOverviewPayload,
    buildSalesOverviewCachePayload,
    mergeSalesOverviewIntoHomeBootstrapPayload,
    buildHomeBootstrapCachePayload,
    normalizeTrackerFirstPagePayload,
    mergeTrackerEntriesById,
    canUseHomeBootstrapTrackerSnapshot,
    hasCachedSalesOverviewData,
    hasCachedHomeBootstrapData,
    loadAdminConsoleData,
    initializeConsole,
    ensureConsoleInitialized,
  };
  global.SPMSBootstrapRuntime = Object.freeze(bootstrapRuntime);
})(window);
