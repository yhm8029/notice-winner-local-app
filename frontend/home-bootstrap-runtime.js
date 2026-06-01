(function attachHomeBootstrapRuntime(global) {
  const baseBootstrapRuntime = global.SPMSBootstrapRuntime || null;

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function getBootstrapRuntimeMethod(methodName) {
    const runtimeMethod = baseBootstrapRuntime?.[methodName];
    if (typeof runtimeMethod !== "function") {
      throw new Error(`SPMSBootstrapRuntime.${methodName} is required before home-bootstrap-runtime.js loads`);
    }
    return runtimeMethod;
  }

  function getSupportRuntimeMethod(deps, methodName) {
    const runtimeMethod = deps?.[methodName] || global.APP_SUPPORT?.[methodName];
    if (typeof runtimeMethod !== "function") {
      throw new Error(`home-bootstrap runtime requires ${methodName}`);
    }
    return runtimeMethod;
  }

  function normalizeHomeBootstrapDeps(deps) {
    return deps && typeof deps === "object" ? deps : {};
  }

  function normalizeSalesOverviewPayload(payload) {
    return {
      myItems: Array.isArray(payload?.my_items) ? payload.my_items : [],
      companyItems: Array.isArray(payload?.company_items) ? payload.company_items : [],
      organizationUsers: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
    };
  }

  function applySalesOverviewPayload(deps, payload) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    const state = runtimeDeps.state || {};
    const normalized = getSupportRuntimeMethod(runtimeDeps, "normalizeSalesOverviewPayload")(payload || {});
    state.companySalesClaims = normalized.companyItems || [];
    state.mySalesClaims = normalized.myItems || [];
    state.organizationUsers = normalized.organizationUsers || [];
    state.organizationUsersLoading = false;
    state.organizationUsersError = "";
    state.mySalesClaimsLoading = false;
    state.mySalesClaimsError = "";
    state.salesClaimsByProjectId = {};
    runtimeDeps.mergeActiveSalesClaims?.(normalized.companyItems || []);
  }

  function shouldApplyHomeBootstrapTrackerSnapshot(deps) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    const state = runtimeDeps.state || {};
    return baseBootstrapRuntime?.canUseHomeBootstrapTrackerSnapshot?.({
      uiMode: state.uiMode,
      globalScope: runtimeDeps.useGlobalTrackerEntriesScope?.() ?? true,
      snapshotActive: true,
      query: state.trackerFilters?.q,
      region: state.trackerFilters?.region,
      editedOnly: state.trackerFilters?.editedOnly,
      page: state.trackerFilters?.page,
    }) || (
      state.uiMode === "user"
      && (runtimeDeps.useGlobalTrackerEntriesScope?.() ?? true)
      && !String(state.trackerFilters?.q || "").trim()
      && !String(state.trackerFilters?.region || "").trim()
      && !state.trackerFilters?.editedOnly
      && Number(state.trackerFilters?.page || 1) === 1
    );
  }

  function shouldUseHomeBootstrapTrackerSnapshot(deps) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    const state = runtimeDeps.state || {};
    const runtimeResult = baseBootstrapRuntime?.canUseHomeBootstrapTrackerSnapshot?.({
      uiMode: state.uiMode,
      globalScope: runtimeDeps.useGlobalTrackerEntriesScope?.() ?? true,
      snapshotActive: state.homeBootstrapTrackerSnapshotActive,
      query: state.trackerFilters?.q,
      region: state.trackerFilters?.region,
      editedOnly: state.trackerFilters?.editedOnly,
      page: state.trackerFilters?.page,
    });
    if (typeof runtimeResult === "boolean") {
      return runtimeResult;
    }
    return state.uiMode === "user"
      && (runtimeDeps.useGlobalTrackerEntriesScope?.() ?? true)
      && state.homeBootstrapTrackerSnapshotActive
      && !String(state.trackerFilters?.q || "").trim()
      && !String(state.trackerFilters?.region || "").trim()
      && !state.trackerFilters?.editedOnly
      && Number(state.trackerFilters?.page || 1) === 1;
  }

  function applyHomeBootstrapPayload(deps, payload) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    const state = runtimeDeps.state || {};

    applySalesOverviewPayload(runtimeDeps, payload || {});
    if (!shouldApplyHomeBootstrapTrackerSnapshot(runtimeDeps)) {
      state.homeBootstrapTrackerSnapshotActive = false;
      runtimeDeps.renderMySalesClaimsPanel?.();
      return;
    }

    const normalizeTrackerFirstPagePayload = getBootstrapRuntimeMethod("normalizeTrackerFirstPagePayload");
    const trackerFirstPage = normalizeTrackerFirstPagePayload(
      payload?.tracker_first_page,
      state.trackerFilters?.pageSize,
    ) || (
      payload?.tracker_first_page && typeof payload.tracker_first_page === "object"
        ? payload.tracker_first_page
        : {}
    );
    const items = Array.isArray(trackerFirstPage.items) ? trackerFirstPage.items : [];
    const previousEntries = Array.isArray(state.trackerEntries) ? state.trackerEntries : [];
    const mergeTrackerEntriesById = baseBootstrapRuntime?.mergeTrackerEntriesById;
    state.trackerEntries = typeof mergeTrackerEntriesById === "function"
      ? mergeTrackerEntriesById(state.trackerEntries, items)
      : items.map((entry) => ({
        ...((Array.isArray(previousEntries) ? previousEntries.find((item) => item.id === entry.id) : null) || {}),
        ...entry,
      }));
    state.trackerEntriesTotal = Number(trackerFirstPage.total || items.length || 0);
    state.trackerEntriesError = "";
    state.organizationUsersLoading = false;
    state.organizationUsersError = "";
    state.mySalesClaimsLoading = false;
    state.mySalesClaimsError = "";
    state.homeBootstrapTrackerSnapshotActive = true;
    state.trackerFilters.page = Number(trackerFirstPage.page || 1) || 1;
    state.trackerFilters.pageSize = Number(trackerFirstPage.page_size || state.trackerFilters.pageSize || 20) || 20;
    if (!state.trackerEntries.some((entry) => entry.id === state.trackerBoardEdit?.entryId)) {
      runtimeDeps.resetTrackerBoardEdit?.();
    }
    if (!state.trackerEntries.some((entry) => entry.id === state.trackerRelatedEntryId)) {
      state.trackerRelatedEntryId = null;
      state.trackerRelatedResolvingEntryId = null;
    }
    if (!state.trackerEntries.some((entry) => entry.id === state.selectedEntryId)) {
      state.selectedEntry = null;
      state.selectedEntryLoadingId = null;
      state.selectedEntryError = "";
    }
    if (runtimeDeps.dom?.trackerContext) {
      runtimeDeps.dom.trackerContext.textContent = `전체 프로젝트 현황 | ${state.trackerEntriesTotal} row(s)`;
    }
    runtimeDeps.syncUrlState?.();
    runtimeDeps.renderMySalesClaimsPanel?.();
    runtimeDeps.renderTrackerEntries?.(state.trackerEntries, { refreshSelectedEntry: false });
    runtimeDeps.renderEntriesPagination?.();
  }

  function hydrateHomeBootstrapCache(deps) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    const parsed = runtimeDeps.readConsoleCacheEnvelope?.(runtimeDeps.homeBootstrapStorageKey);
    if (!parsed) {
      return false;
    }
    applyHomeBootstrapPayload(runtimeDeps, parsed.payload || {});
    return true;
  }

  function persistSalesOverviewCache(deps, payload) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    runtimeDeps.writeConsoleCacheEnvelope?.(
      runtimeDeps.salesOverviewStorageKey,
      getSupportRuntimeMethod(runtimeDeps, "buildSalesOverviewCachePayload")(payload),
    );
    syncHomeBootstrapSalesCache(runtimeDeps, payload);
  }

  function syncHomeBootstrapSalesCache(deps, payload) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    const parsed = runtimeDeps.readConsoleCacheEnvelope?.(runtimeDeps.homeBootstrapStorageKey, { allowStale: true });
    if (!parsed) {
      return;
    }
    const existingPayload = isPlainObject(parsed.payload) ? parsed.payload : {};
    runtimeDeps.writeConsoleCacheEnvelope?.(
      runtimeDeps.homeBootstrapStorageKey,
      getSupportRuntimeMethod(runtimeDeps, "mergeSalesOverviewIntoHomeBootstrapPayload")(existingPayload, payload),
    );
  }

  function persistHomeBootstrapCache(deps, payload) {
    const runtimeDeps = normalizeHomeBootstrapDeps(deps);
    runtimeDeps.writeConsoleCacheEnvelope?.(
      runtimeDeps.homeBootstrapStorageKey,
      getSupportRuntimeMethod(runtimeDeps, "buildHomeBootstrapCachePayload")(payload),
    );
  }

  const homeBootstrapRuntime = {
    applyHomeBootstrapPayload,
    hydrateHomeBootstrapCache,
    persistSalesOverviewCache,
    syncHomeBootstrapSalesCache,
    persistHomeBootstrapCache,
    shouldUseHomeBootstrapTrackerSnapshot,
  };

  global.SPMSHomeBootstrapRuntime = Object.freeze(homeBootstrapRuntime);
  global.SPMSBootstrapRuntime = Object.freeze({
    ...(baseBootstrapRuntime || {}),
    ...homeBootstrapRuntime,
  });
})(window);
