const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadApplyHomeBootstrapPayloadContext(overrides = {}) {
  const runtimePath = path.join(__dirname, "..", "home-bootstrap-runtime.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const bootstrapRuntime = {
    normalizeTrackerFirstPagePayload: (payload, fallbackPageSize = 20) => ({
      items: Array.isArray(payload?.items) ? payload.items : [],
      page: Number(payload?.page || 1) || 1,
      page_size: Number(payload?.page_size || fallbackPageSize || 20) || 20,
      total: Number(payload?.total || 0) || 0,
      sort_contract: payload?.sort_contract || { mode: "default", order_by: [] },
    }),
    mergeTrackerEntriesById: (previousEntries, nextEntries) =>
      (Array.isArray(nextEntries) ? nextEntries : []).map((entry) => ({
        ...((Array.isArray(previousEntries) ? previousEntries.find((item) => item.id === entry.id) : null) || {}),
        ...entry,
      })),
    canUseHomeBootstrapTrackerSnapshot: (input) => (
      input?.uiMode === "user"
      && Boolean(input?.globalScope)
      && Boolean(input?.snapshotActive)
      && !String(input?.query || "").trim()
      && !String(input?.region || "").trim()
      && !Boolean(input?.editedOnly)
      && Number(input?.page || 1) === 1
    ),
  };
  const window = { SPMSBootstrapRuntime: bootstrapRuntime };

  const context = {
    window,
    state: {
      uiMode: "user",
      trackerEntries: [{ id: "existing-entry", project_name: "Existing Project" }],
      trackerEntriesTotal: 42,
      trackerEntriesError: "",
      organizationUsersLoading: true,
      organizationUsersError: "stale",
      mySalesClaimsLoading: true,
      mySalesClaimsError: "stale",
      companySalesClaims: [],
      mySalesClaims: [],
      organizationUsers: [],
      homeBootstrapTrackerSnapshotActive: false,
      trackerBoardEdit: { entryId: null },
      trackerRelatedEntryId: null,
      trackerRelatedResolvingEntryId: null,
      selectedEntryId: "existing-entry",
      selectedEntry: { id: "existing-entry" },
      selectedEntryLoadingId: "existing-entry",
      selectedEntryError: "",
      trackerFilters: {
        q: "",
        region: "",
        editedOnly: false,
        page: 3,
        pageSize: 20,
      },
    },
    dom: {
      trackerContext: { textContent: "" },
    },
    APP_SUPPORT: {
      normalizeSalesOverviewPayload(payload) {
        return {
          companyItems: payload.company_items || [],
          myItems: payload.my_items || [],
          organizationUsers: payload.organization_users || [],
        };
      },
      buildSalesOverviewCachePayload(payload) {
        return {
          company_items: payload.company_items || [],
          my_items: payload.my_items || [],
          organization_users: payload.organization_users || [],
        };
      },
      mergeSalesOverviewIntoHomeBootstrapPayload(existingPayload, salesPayload) {
        return {
          ...(existingPayload && typeof existingPayload === "object" && !Array.isArray(existingPayload) ? existingPayload : {}),
          company_items: salesPayload.company_items || [],
          my_items: salesPayload.my_items || [],
          organization_users: salesPayload.organization_users || [],
        };
      },
      buildHomeBootstrapCachePayload(payload) {
        return {
          company_items: payload.company_items || [],
          my_items: payload.my_items || [],
          organization_users: payload.organization_users || [],
          tracker_first_page: payload.tracker_first_page || {
            items: [],
            page: 1,
            page_size: 20,
            total: 0,
            sort_contract: { mode: "default", order_by: [] },
          },
          generated_at: payload.generated_at || "",
          snapshot_version: Number(payload.snapshot_version || 1) || 1,
        };
      },
      hasCachedSalesOverviewData() {
        return false;
      },
      hasCachedHomeBootstrapData() {
        return false;
      },
      isMissingSalesOverviewEndpointError() {
        return false;
      },
      isMissingHomeBootstrapEndpointError() {
        return false;
      },
      buildStorageIdentity() {
        return "";
      },
    },
    normalizeSalesOverviewPayload(payload) {
      return {
        companyItems: payload.company_items || [],
        myItems: payload.my_items || [],
        organizationUsers: payload.organization_users || [],
      };
    },
    mergeActiveSalesClaims(items) {
      context.__mergedSalesClaims = items;
    },
    useGlobalTrackerEntriesScope() {
      return true;
    },
    resetTrackerBoardEdit() {
      context.__resetTrackerBoardEditCalled = true;
    },
    syncUrlState() {
      context.__syncUrlStateCalls = (context.__syncUrlStateCalls || 0) + 1;
    },
    renderMySalesClaimsPanel() {
      context.__renderMySalesClaimsPanelCalls = (context.__renderMySalesClaimsPanelCalls || 0) + 1;
    },
    renderTrackerEntries(entries, options) {
      context.__renderTrackerEntriesCalls = (context.__renderTrackerEntriesCalls || []);
      context.__renderTrackerEntriesCalls.push({ entries, options });
    },
    renderEntriesPagination() {
      context.__renderEntriesPaginationCalls = (context.__renderEntriesPaginationCalls || 0) + 1;
    },
    ...overrides,
  };

  vm.createContext(context);
  vm.runInContext(`${source}\n`, context, { filename: runtimePath });
  const rawHomeRuntime = context.window.SPMSHomeBootstrapRuntime;
  const rawBootstrapRuntime = context.window.SPMSBootstrapRuntime;
  const runtimeDeps = {
    state: context.state,
    dom: context.dom,
    mergeActiveSalesClaims: context.mergeActiveSalesClaims,
    resetTrackerBoardEdit: context.resetTrackerBoardEdit,
    renderEntriesPagination: context.renderEntriesPagination,
    renderMySalesClaimsPanel: context.renderMySalesClaimsPanel,
    renderTrackerEntries: context.renderTrackerEntries,
    syncUrlState: context.syncUrlState,
    useGlobalTrackerEntriesScope: context.useGlobalTrackerEntriesScope,
    normalizeSalesOverviewPayload: context.APP_SUPPORT.normalizeSalesOverviewPayload,
    buildSalesOverviewCachePayload: context.APP_SUPPORT.buildSalesOverviewCachePayload,
    mergeSalesOverviewIntoHomeBootstrapPayload: context.APP_SUPPORT.mergeSalesOverviewIntoHomeBootstrapPayload,
    buildHomeBootstrapCachePayload: context.APP_SUPPORT.buildHomeBootstrapCachePayload,
    salesOverviewStorageKey: "notice-winner-pipeline-web.salesOverview.v1",
    homeBootstrapStorageKey: "notice-winner-pipeline-web.homeBootstrap.v6",
    readConsoleCacheEnvelope: context.readConsoleCacheEnvelope,
    writeConsoleCacheEnvelope: context.writeConsoleCacheEnvelope,
  };
  const boundHomeRuntime = {
    applyHomeBootstrapPayload: (payload) => rawHomeRuntime.applyHomeBootstrapPayload(runtimeDeps, payload),
    hydrateHomeBootstrapCache: () => rawHomeRuntime.hydrateHomeBootstrapCache(runtimeDeps),
    persistSalesOverviewCache: (payload) => rawHomeRuntime.persistSalesOverviewCache(runtimeDeps, payload),
    syncHomeBootstrapSalesCache: (payload) => rawHomeRuntime.syncHomeBootstrapSalesCache(runtimeDeps, payload),
    persistHomeBootstrapCache: (payload) => rawHomeRuntime.persistHomeBootstrapCache(runtimeDeps, payload),
    shouldUseHomeBootstrapTrackerSnapshot: () => rawHomeRuntime.shouldUseHomeBootstrapTrackerSnapshot(runtimeDeps),
  };
  context.window.SPMSHomeBootstrapRuntime = boundHomeRuntime;
  context.window.SPMSBootstrapRuntime = {
    ...(rawBootstrapRuntime || {}),
    ...boundHomeRuntime,
  };
  return context;
}

test("home-bootstrap runtime owns the apply and cache helpers", () => {
  const context = loadApplyHomeBootstrapPayloadContext();

  assert.equal(typeof context.window.SPMSHomeBootstrapRuntime, "object");
  assert.equal(typeof context.window.SPMSBootstrapRuntime.applyHomeBootstrapPayload, "function");
  assert.equal(context.window.SPMSBootstrapRuntime.applyHomeBootstrapPayload, context.window.SPMSHomeBootstrapRuntime.applyHomeBootstrapPayload);
  assert.equal(context.window.SPMSBootstrapRuntime.hydrateHomeBootstrapCache, context.window.SPMSHomeBootstrapRuntime.hydrateHomeBootstrapCache);
  assert.equal(context.window.SPMSBootstrapRuntime.persistSalesOverviewCache, context.window.SPMSHomeBootstrapRuntime.persistSalesOverviewCache);
  assert.equal(context.window.SPMSBootstrapRuntime.syncHomeBootstrapSalesCache, context.window.SPMSHomeBootstrapRuntime.syncHomeBootstrapSalesCache);
  assert.equal(context.window.SPMSBootstrapRuntime.persistHomeBootstrapCache, context.window.SPMSHomeBootstrapRuntime.persistHomeBootstrapCache);
  assert.equal(context.window.SPMSBootstrapRuntime.shouldUseHomeBootstrapTrackerSnapshot, context.window.SPMSHomeBootstrapRuntime.shouldUseHomeBootstrapTrackerSnapshot);
});

test("applyHomeBootstrapPayload preserves tracker page when current view is not first-page snapshot", () => {
  const context = loadApplyHomeBootstrapPayloadContext();

  context.window.SPMSHomeBootstrapRuntime.applyHomeBootstrapPayload({
    tracker_first_page: {
      items: [{ id: "bootstrap-entry", project_name: "Bootstrap Project" }],
      total: 99,
      page: 1,
      page_size: 20,
    },
    company_items: [{ id: "claim-1" }],
    my_items: [{ id: "claim-1" }],
    organization_users: [{ id: "user-1" }],
  });

  assert.equal(context.state.trackerFilters.page, 3);
  assert.equal(context.state.trackerEntries[0].id, "existing-entry");
  assert.equal(context.state.trackerEntriesTotal, 42);
  assert.equal(context.state.homeBootstrapTrackerSnapshotActive, false);
  assert.equal(context.__syncUrlStateCalls || 0, 0);
  assert.equal(context.__renderEntriesPaginationCalls || 0, 0);
  assert.equal(context.__renderMySalesClaimsPanelCalls || 0, 1);
});

test("applyHomeBootstrapPayload applies tracker snapshot on default first-page view", () => {
  const context = loadApplyHomeBootstrapPayloadContext({
    state: {
      uiMode: "user",
      trackerEntries: [],
      trackerEntriesTotal: 0,
      trackerEntriesError: "",
      organizationUsersLoading: true,
      organizationUsersError: "",
      mySalesClaimsLoading: true,
      mySalesClaimsError: "",
      companySalesClaims: [],
      mySalesClaims: [],
      organizationUsers: [],
      homeBootstrapTrackerSnapshotActive: false,
      trackerBoardEdit: { entryId: null },
      trackerRelatedEntryId: null,
      trackerRelatedResolvingEntryId: null,
      selectedEntryId: null,
      selectedEntry: null,
      selectedEntryLoadingId: null,
      selectedEntryError: "",
      trackerFilters: {
        q: "",
        region: "",
        editedOnly: false,
        page: 1,
        pageSize: 20,
      },
    },
  });

  context.window.SPMSHomeBootstrapRuntime.applyHomeBootstrapPayload({
    tracker_first_page: {
      items: [{ id: "bootstrap-entry", project_name: "Bootstrap Project" }],
      total: 99,
      page: 1,
      page_size: 20,
    },
  });

  assert.equal(context.state.trackerFilters.page, 1);
  assert.equal(context.state.trackerEntries[0].id, "bootstrap-entry");
  assert.equal(context.state.trackerEntriesTotal, 99);
  assert.equal(context.state.homeBootstrapTrackerSnapshotActive, true);
  assert.equal(context.__syncUrlStateCalls || 0, 1);
  assert.equal(context.__renderEntriesPaginationCalls || 0, 1);
});
