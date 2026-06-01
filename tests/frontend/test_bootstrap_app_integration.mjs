import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const homeBootstrapRuntimePath = path.resolve(__dirname, "../../frontend/home-bootstrap-runtime.js");

const SALES_OVERVIEW_STORAGE_KEY = "notice-winner-pipeline-web.salesOverview.v1";
const HOME_BOOTSTRAP_STORAGE_KEY = "notice-winner-pipeline-web.homeBootstrap.v6";

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function findSourceIndex(source, patterns, fromIndex = 0) {
  for (const pattern of patterns) {
    const index = source.indexOf(pattern, fromIndex);
    if (index >= 0) {
      return index;
    }
  }
  return -1;
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

function readHomeBootstrapRuntimeSource() {
  return fs.readFileSync(homeBootstrapRuntimePath, "utf8");
}

function normalizeWhitespace(source) {
  return source.replace(/\s+/g, " ").trim();
}

function extractAppHomeBootstrapDelegates() {
  const source = readAppSource();
  const start = findSourceIndex(source, [
    "function applyHomeBootstrapPayload(payload) {",
    "function applyHomeBootstrapPayload(payload){",
  ]);
  const end = findSourceIndex(source, [
    "function buildUrlForState(",
    "function buildUrlForState (",
  ], start);
  assert.ok(start >= 0, "home bootstrap helper block should exist in app.js");
  assert.ok(end > start, "home bootstrap helper block should end before buildUrlForState");
  return source.slice(start, end).trim();
}

function extractConsoleDataRuntimeSources() {
  const source = readAppSource();
  const start = findSourceIndex(source, [
    "function getConsoleDataRuntimeDeps() {",
    "function getConsoleDataRuntimeDeps()",
  ]);
  const end = findSourceIndex(source, [
    "async function handleInvitationSubmit(event) {",
    "async function handleInvitationSubmit(event)",
  ], start);
  assert.ok(start >= 0, "console data runtime helper block should exist");
  assert.ok(end > start, "console data runtime helper block should end before handleInvitationSubmit");
  return source.slice(start, end).trim();
}

function createRuntime(overrides = {}) {
  return {
    normalizeSalesOverviewPayload: (payload) => ({
      myItems: Array.isArray(payload?.my_items) ? payload.my_items : [],
      companyItems: Array.isArray(payload?.company_items) ? payload.company_items : [],
      organizationUsers: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
    }),
    buildSalesOverviewCachePayload: (payload) => ({
      my_items: Array.isArray(payload?.my_items) ? payload.my_items : [],
      company_items: Array.isArray(payload?.company_items) ? payload.company_items : [],
      organization_users: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
    }),
    mergeSalesOverviewIntoHomeBootstrapPayload: (existingPayload, salesPayload) => ({
      ...(existingPayload && typeof existingPayload === "object" && !Array.isArray(existingPayload) ? existingPayload : {}),
      my_items: Array.isArray(salesPayload?.my_items) ? salesPayload.my_items : [],
      company_items: Array.isArray(salesPayload?.company_items) ? salesPayload.company_items : [],
      organization_users: Array.isArray(salesPayload?.organization_users) ? salesPayload.organization_users : [],
    }),
    buildHomeBootstrapCachePayload: (payload) => ({
      my_items: Array.isArray(payload?.my_items) ? payload.my_items : [],
      company_items: Array.isArray(payload?.company_items) ? payload.company_items : [],
      organization_users: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
      tracker_first_page: {
        items: Array.isArray(payload?.tracker_first_page?.items) ? payload.tracker_first_page.items : [],
        page: Number(payload?.tracker_first_page?.page || 1) || 1,
        page_size: Number(payload?.tracker_first_page?.page_size || 20) || 20,
        total: Number(payload?.tracker_first_page?.total || 0) || 0,
        sort_contract: payload?.tracker_first_page?.sort_contract || { mode: "default", order_by: [] },
      },
      generated_at: payload?.generated_at || "",
      snapshot_version: Number(payload?.snapshot_version || 1) || 1,
    }),
    hasCachedSalesOverviewData: (snapshotState) => Boolean(
      snapshotState?.mySalesClaims?.length
      || snapshotState?.companySalesClaims?.length
      || snapshotState?.organizationUsers?.length
    ),
    hasCachedHomeBootstrapData: (snapshotState) => Boolean(
      snapshotState?.homeBootstrapTrackerSnapshotActive
      || snapshotState?.mySalesClaims?.length
      || snapshotState?.companySalesClaims?.length
      || snapshotState?.organizationUsers?.length
    ),
    isMissingSalesOverviewEndpointError: () => false,
    isMissingHomeBootstrapEndpointError: () => false,
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
    canUseHomeBootstrapTrackerSnapshot: () => true,
    ...overrides,
  };
}

function loadBootstrapAppHelpers({ runtimeOverrides = {}, globals = {} } = {}) {
  const functionSource = readHomeBootstrapRuntimeSource();
  const runtime = createRuntime(runtimeOverrides);
  const window = { SPMSBootstrapRuntime: runtime };
  const state = {
    uiMode: "user",
    auth: { enabled: true, authenticated: true, authorized: true, user: { role: "org_admin" } },
    trackerFilters: { q: "", region: "", editedOnly: false, page: 1, pageSize: 20 },
    trackerEntries: [],
    trackerEntriesTotal: 0,
    trackerEntriesError: "old error",
    trackerEntriesRequest: null,
    trackerEntriesRequestKey: "",
    trackerBoardEdit: { entryId: null },
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    selectedEntryId: null,
    selectedEntry: null,
    selectedEntryLoadingId: null,
    selectedEntryError: "",
    organizationUsersLoading: true,
    organizationUsersError: "old org error",
    mySalesClaimsLoading: true,
    mySalesClaimsError: "old sales error",
    homeBootstrapTrackerSnapshotActive: false,
    mySalesClaims: [],
    companySalesClaims: [],
    organizationUsers: [],
    salesClaimsByProjectId: {},
    salesClaimDrafts: {},
  };
  const context = vm.createContext({
    window,
    console,
    SALES_OVERVIEW_STORAGE_KEY,
    HOME_BOOTSTRAP_STORAGE_KEY,
    APP_SUPPORT: runtime,
    state,
    dom: {
      trackerContext: { textContent: "" },
    },
    readConsoleCacheEnvelope: () => null,
    writeConsoleCacheEnvelope: () => {},
    renderMySalesClaimsPanel: () => {},
    renderTrackerEntries: () => {},
    renderEntriesPagination: () => {},
    resetTrackerBoardEdit: () => {},
    syncUrlState: () => {},
    mergeActiveSalesClaims: () => {},
    useGlobalTrackerEntriesScope: () => true,
    ...globals,
  });
  vm.runInContext(functionSource, context, { filename: homeBootstrapRuntimePath });
  const homeRuntime = window.SPMSHomeBootstrapRuntime;
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
    normalizeSalesOverviewPayload: runtime.normalizeSalesOverviewPayload,
    buildSalesOverviewCachePayload: runtime.buildSalesOverviewCachePayload,
    mergeSalesOverviewIntoHomeBootstrapPayload: runtime.mergeSalesOverviewIntoHomeBootstrapPayload,
    buildHomeBootstrapCachePayload: runtime.buildHomeBootstrapCachePayload,
    salesOverviewStorageKey: SALES_OVERVIEW_STORAGE_KEY,
    homeBootstrapStorageKey: HOME_BOOTSTRAP_STORAGE_KEY,
    readConsoleCacheEnvelope: context.readConsoleCacheEnvelope,
    writeConsoleCacheEnvelope: context.writeConsoleCacheEnvelope,
  };
  return {
    context,
    applyHomeBootstrapPayload: (payload) => homeRuntime.applyHomeBootstrapPayload(runtimeDeps, payload),
    hydrateHomeBootstrapCache: () => homeRuntime.hydrateHomeBootstrapCache(runtimeDeps),
    persistSalesOverviewCache: (payload) => homeRuntime.persistSalesOverviewCache(runtimeDeps, payload),
    syncHomeBootstrapSalesCache: (payload) => homeRuntime.syncHomeBootstrapSalesCache(runtimeDeps, payload),
    persistHomeBootstrapCache: (payload) => homeRuntime.persistHomeBootstrapCache(runtimeDeps, payload),
    shouldUseHomeBootstrapTrackerSnapshot: () => homeRuntime.shouldUseHomeBootstrapTrackerSnapshot(runtimeDeps),
  };
}

function loadConsoleDataRuntimeWrappers({ runtime = {}, globals = {}, stateOverrides = {} } = {}) {
  const functionSource = extractConsoleDataRuntimeSources();
  const loadTrackerEntries = async () => {};
  const state = {
    uiMode: "user",
    auth: { enabled: true, authenticated: true, authorized: true, user: { role: "org_admin" } },
    homeBootstrapAvailability: "available",
    homeBootstrapRequest: null,
    salesOverviewAvailability: "available",
    salesOverviewRequest: null,
    trackerFilters: { q: "", region: "", editedOnly: false, page: 1, pageSize: 20 },
    homeBootstrapTrackerSnapshotActive: false,
    mySalesClaims: [],
    companySalesClaims: [],
    organizationUsers: [],
    trackerEntries: [],
    ...stateOverrides,
  };
  const salesStateHelpers = {
    getVisibleSalesProjectIds: globals.getVisibleSalesProjectIds || (() => []),
    getSalesClaimForProject: () => null,
    getTrackerProjectSnapshot: () => null,
    renderUserSalesProjectFacts: () => "",
    isCurrentUserClaimOwner: globals.isCurrentUserClaimOwner || (() => true),
    canCurrentUserForceRelease: () => false,
    canCurrentUserManageClaim: () => false,
    isActiveSalesClaim: globals.isActiveSalesClaim || (() => true),
    getOrganizationTransferTargets: () => [],
    getSalesNoteDraft: () => "",
    setSalesNoteDraft: () => {},
    upsertSalesClaim: () => {},
    replaceVisibleSalesClaims: globals.replaceVisibleSalesClaims || (() => {}),
    mergeActiveSalesClaims: globals.mergeActiveSalesClaims || (() => {}),
    formatShortDateTime: () => "",
    formatEstimatedAmountRangeFromKrw: () => "",
  };
  const bootstrapSupport = {
    normalizeSalesOverviewPayload: globals.normalizeSalesOverviewPayload || ((payload) => payload || {}),
    buildSalesOverviewCachePayload: globals.buildSalesOverviewCachePayload || ((payload) => payload || {}),
    mergeSalesOverviewIntoHomeBootstrapPayload: globals.mergeSalesOverviewIntoHomeBootstrapPayload || ((existingPayload, salesPayload) => ({
      ...(existingPayload && typeof existingPayload === "object" ? existingPayload : {}),
      ...(salesPayload && typeof salesPayload === "object" ? salesPayload : {}),
    })),
    buildHomeBootstrapCachePayload: globals.buildHomeBootstrapCachePayload || ((payload) => payload || {}),
    hasCachedSalesOverviewData: globals.hasCachedSalesOverviewData || (() => false),
    hasCachedHomeBootstrapData: globals.hasCachedHomeBootstrapData || (() => false),
    isMissingSalesOverviewEndpointError: globals.isMissingSalesOverviewEndpointError || (() => false),
    isMissingHomeBootstrapEndpointError: globals.isMissingHomeBootstrapEndpointError || (() => false),
  };
  const context = vm.createContext({
    console,
    CONSOLE_DATA_RUNTIME: runtime,
    SALES_OVERVIEW_STORAGE_KEY,
    HOME_BOOTSTRAP_STORAGE_KEY,
    APP_SUPPORT: {
      createSalesStateHelpers: () => salesStateHelpers,
      createBootstrapRuntimeDepsHelpers: (options = {}) => ({
        buildConsoleDataRuntimeDeps: () => ({
          state: options.state,
          api: options.api,
          flash: options.flash,
          canUseAdminMode: options.canUseAdminMode,
          getVisibleSalesProjectIds: options.salesStateHelpers.getVisibleSalesProjectIds,
          isActiveSalesClaim: options.salesStateHelpers.isActiveSalesClaim,
          isCurrentUserClaimOwner: options.salesStateHelpers.isCurrentUserClaimOwner,
          mergeActiveSalesClaims: options.salesStateHelpers.mergeActiveSalesClaims,
          mergeOrganizationInvitations: options.mergeOrganizationInvitations,
          replaceVisibleSalesClaims: options.salesStateHelpers.replaceVisibleSalesClaims,
          loadTrackerEntries: options.loadTrackerEntries,
          renderMySalesClaimsPanel: options.renderMySalesClaimsPanel,
          renderTrackerEntries: options.renderTrackerEntries,
          renderSalesSummaryPanel: options.renderSalesSummaryPanel,
          renderOrganizationAdminPanel: options.renderOrganizationAdminPanel,
          applyHomeBootstrapPayload: options.applyHomeBootstrapPayload,
          applySalesOverviewPayload: options.applySalesOverviewPayload,
          persistHomeBootstrapCache: options.persistHomeBootstrapCache,
          persistSalesOverviewCache: options.persistSalesOverviewCache,
          hasCachedHomeBootstrapData: options.bootstrapSupport.hasCachedHomeBootstrapData,
          hasCachedSalesOverviewData: options.bootstrapSupport.hasCachedSalesOverviewData,
          isMissingHomeBootstrapEndpointError: options.bootstrapSupport.isMissingHomeBootstrapEndpointError,
          isMissingSalesOverviewEndpointError: options.bootstrapSupport.isMissingSalesOverviewEndpointError,
        }),
        buildHomeBootstrapRuntimeDeps: () => ({
          state: options.state,
          dom: options.dom,
          mergeActiveSalesClaims: options.salesStateHelpers.mergeActiveSalesClaims,
          resetTrackerBoardEdit: options.resetTrackerBoardEdit,
          renderEntriesPagination: options.renderEntriesPagination,
          renderMySalesClaimsPanel: options.renderMySalesClaimsPanel,
          renderTrackerEntries: options.renderTrackerEntries,
          syncUrlState: options.syncUrlState,
          useGlobalTrackerEntriesScope: options.useGlobalTrackerEntriesScope,
          normalizeSalesOverviewPayload: options.bootstrapSupport.normalizeSalesOverviewPayload,
          buildSalesOverviewCachePayload: options.bootstrapSupport.buildSalesOverviewCachePayload,
          mergeSalesOverviewIntoHomeBootstrapPayload: options.bootstrapSupport.mergeSalesOverviewIntoHomeBootstrapPayload,
          buildHomeBootstrapCachePayload: options.bootstrapSupport.buildHomeBootstrapCachePayload,
          salesOverviewStorageKey: options.salesOverviewStorageKey,
          homeBootstrapStorageKey: options.homeBootstrapStorageKey,
          readConsoleCacheEnvelope: options.readConsoleCacheEnvelope,
          writeConsoleCacheEnvelope: options.writeConsoleCacheEnvelope,
        }),
      }),
      ...bootstrapSupport,
    },
    state,
    dom: {},
    api: () => {
      throw new Error("api should not be called by this wiring test");
    },
    flash: () => {},
    isAdminRole: () => false,
    buildUserSalesProjectFactsMarkup: () => "",
    formatEokValue: () => "",
    canUseAdminMode: () => true,
    getVisibleSalesProjectIds: salesStateHelpers.getVisibleSalesProjectIds,
    isActiveSalesClaim: salesStateHelpers.isActiveSalesClaim,
    isCurrentUserClaimOwner: salesStateHelpers.isCurrentUserClaimOwner,
    mergeActiveSalesClaims: salesStateHelpers.mergeActiveSalesClaims,
    mergeOrganizationInvitations: () => {},
    replaceVisibleSalesClaims: salesStateHelpers.replaceVisibleSalesClaims,
    loadTrackerEntries,
    resetTrackerBoardEdit: () => {},
    renderEntriesPagination: () => {},
    renderMySalesClaimsPanel: () => {},
    renderTrackerEntries: () => {},
    renderSalesSummaryPanel: () => {},
    renderOrganizationAdminPanel: () => {},
    applyHomeBootstrapPayload: () => {},
    applySalesOverviewPayload: () => {},
    persistHomeBootstrapCache: () => {},
    persistSalesOverviewCache: () => {},
    readConsoleCacheEnvelope: () => null,
    writeConsoleCacheEnvelope: () => {},
    syncUrlState: () => {},
    useGlobalTrackerEntriesScope: () => true,
    hasCachedHomeBootstrapData: bootstrapSupport.hasCachedHomeBootstrapData,
    hasCachedSalesOverviewData: bootstrapSupport.hasCachedSalesOverviewData,
    isMissingHomeBootstrapEndpointError: bootstrapSupport.isMissingHomeBootstrapEndpointError,
    isMissingSalesOverviewEndpointError: bootstrapSupport.isMissingSalesOverviewEndpointError,
    ...globals,
  });
  const exports = vm.runInContext(
    `(function () { ${functionSource}; return {
      getConsoleDataRuntimeDeps,
      requireConsoleDataRuntime,
      loadHomeBootstrap,
      loadSalesOverview,
      getConsoleDataRuntimeDepsIdentitySnapshot: (deps) => ({
        state: deps.state === state,
        api: deps.api === api,
        flash: deps.flash === flash,
        canUseAdminMode: deps.canUseAdminMode === canUseAdminMode,
        getVisibleSalesProjectIds: deps.getVisibleSalesProjectIds === getVisibleSalesProjectIds,
        isActiveSalesClaim: deps.isActiveSalesClaim === isActiveSalesClaim,
        isCurrentUserClaimOwner: deps.isCurrentUserClaimOwner === isCurrentUserClaimOwner,
        mergeActiveSalesClaims: deps.mergeActiveSalesClaims === mergeActiveSalesClaims,
        mergeOrganizationInvitations: deps.mergeOrganizationInvitations === mergeOrganizationInvitations,
        replaceVisibleSalesClaims: deps.replaceVisibleSalesClaims === replaceVisibleSalesClaims,
        loadTrackerEntries: deps.loadTrackerEntries === loadTrackerEntries,
        renderMySalesClaimsPanel: deps.renderMySalesClaimsPanel === renderMySalesClaimsPanel,
        renderTrackerEntries: deps.renderTrackerEntries === renderTrackerEntries,
        renderSalesSummaryPanel: deps.renderSalesSummaryPanel === renderSalesSummaryPanel,
        renderOrganizationAdminPanel: deps.renderOrganizationAdminPanel === renderOrganizationAdminPanel,
        applyHomeBootstrapPayload: deps.applyHomeBootstrapPayload === applyHomeBootstrapPayload,
        applySalesOverviewPayload: deps.applySalesOverviewPayload === applySalesOverviewPayload,
        persistHomeBootstrapCache: deps.persistHomeBootstrapCache === persistHomeBootstrapCache,
        persistSalesOverviewCache: deps.persistSalesOverviewCache === persistSalesOverviewCache,
        hasCachedHomeBootstrapData: deps.hasCachedHomeBootstrapData === hasCachedHomeBootstrapData,
        hasCachedSalesOverviewData: deps.hasCachedSalesOverviewData === hasCachedSalesOverviewData,
        isMissingHomeBootstrapEndpointError: deps.isMissingHomeBootstrapEndpointError === isMissingHomeBootstrapEndpointError,
        isMissingSalesOverviewEndpointError: deps.isMissingSalesOverviewEndpointError === isMissingSalesOverviewEndpointError,
      }),
    }; })()`,
    context,
    { filename: appPath },
  );
  return { context, loadTrackerEntries, ...exports };
}

test("applyHomeBootstrapPayload uses runtime helpers for sales overview and tracker entries", () => {
  const normalizeSalesCalls = [];
  const normalizeTrackerCalls = [];
  const mergeTrackerCalls = [];
  const renderCalls = [];
  const { applyHomeBootstrapPayload, context } = loadBootstrapAppHelpers({
    runtimeOverrides: {
      normalizeSalesOverviewPayload: (payload) => {
        normalizeSalesCalls.push(plain(payload));
        return {
          myItems: [{ id: "mine-1", title: "Mine" }],
          companyItems: [{ id: "company-1", title: "Company" }],
          organizationUsers: [{ id: "user-1", name: "User" }],
        };
      },
      normalizeTrackerFirstPagePayload: (payload, fallbackPageSize) => {
        normalizeTrackerCalls.push({ payload: plain(payload), fallbackPageSize });
        return {
          items: [
            { id: "shared", title: "Fresh Shared" },
            { id: "new-1", title: "Fresh New" },
          ],
          page: 2,
          page_size: 14,
          total: 2,
          sort_contract: { mode: "default", order_by: [] },
        };
      },
      mergeTrackerEntriesById: (previousEntries, nextEntries) => {
        mergeTrackerCalls.push({
          previousEntries: plain(previousEntries),
          nextEntries: plain(nextEntries),
        });
        const previousMap = new Map((Array.isArray(previousEntries) ? previousEntries : []).map((entry) => [entry.id, entry]));
        return (Array.isArray(nextEntries) ? nextEntries : []).map((entry) => ({
          ...(previousMap.get(entry.id) || {}),
          ...entry,
          mergedByRuntime: true,
        }));
      },
    },
    globals: {
      renderMySalesClaimsPanel: () => renderCalls.push("renderMySalesClaimsPanel"),
      renderTrackerEntries: () => renderCalls.push("renderTrackerEntries"),
      renderEntriesPagination: () => renderCalls.push("renderEntriesPagination"),
      syncUrlState: () => renderCalls.push("syncUrlState"),
      resetTrackerBoardEdit: () => renderCalls.push("resetTrackerBoardEdit"),
      mergeActiveSalesClaims: (items) => renderCalls.push(["mergeActiveSalesClaims", plain(items)]),
    },
  });

  context.state.trackerFilters.pageSize = 25;
  context.state.trackerEntries = [
    { id: "shared", title: "Stale Shared", existing: true },
    { id: "board-1", title: "Board Entry" },
  ];
  context.state.trackerBoardEdit.entryId = "shared";
  context.state.trackerRelatedEntryId = "shared";
  context.state.trackerRelatedResolvingEntryId = "shared";
  context.state.selectedEntryId = "shared";
  context.state.selectedEntry = { id: "shared", stale: true };
  context.state.selectedEntryLoadingId = "shared";
  context.state.selectedEntryError = "stale error";

  applyHomeBootstrapPayload({
    my_items: [{ id: "mine-1" }],
    company_items: [{ id: "company-1" }],
    organization_users: [{ id: "user-1" }],
    tracker_first_page: {
      items: [{ id: "shared", title: "Fresh Shared" }, { id: "new-1", title: "Fresh New" }],
      page: "2",
      page_size: "14",
      total: "2",
      sort_contract: { mode: "default", order_by: [] },
    },
  });

  assert.deepEqual(normalizeSalesCalls, [{
    my_items: [{ id: "mine-1" }],
    company_items: [{ id: "company-1" }],
    organization_users: [{ id: "user-1" }],
    tracker_first_page: {
      items: [{ id: "shared", title: "Fresh Shared" }, { id: "new-1", title: "Fresh New" }],
      page: "2",
      page_size: "14",
      total: "2",
      sort_contract: { mode: "default", order_by: [] },
    },
  }]);
  assert.deepEqual(normalizeTrackerCalls, [{
    payload: {
      items: [{ id: "shared", title: "Fresh Shared" }, { id: "new-1", title: "Fresh New" }],
      page: "2",
      page_size: "14",
      total: "2",
      sort_contract: { mode: "default", order_by: [] },
    },
    fallbackPageSize: 25,
  }]);
  assert.deepEqual(mergeTrackerCalls, [{
    previousEntries: [
      { id: "shared", title: "Stale Shared", existing: true },
      { id: "board-1", title: "Board Entry" },
    ],
    nextEntries: [{ id: "shared", title: "Fresh Shared" }, { id: "new-1", title: "Fresh New" }],
  }]);
  assert.deepEqual(plain(context.state.mySalesClaims), [{ id: "mine-1", title: "Mine" }]);
  assert.deepEqual(plain(context.state.companySalesClaims), [{ id: "company-1", title: "Company" }]);
  assert.deepEqual(plain(context.state.organizationUsers), [{ id: "user-1", name: "User" }]);
  assert.deepEqual(plain(context.state.trackerEntries), [
    { id: "shared", title: "Fresh Shared", existing: true, mergedByRuntime: true },
    { id: "new-1", title: "Fresh New", mergedByRuntime: true },
  ]);
  assert.equal(context.state.trackerEntriesTotal, 2);
  assert.equal(context.state.trackerEntriesError, "");
  assert.equal(context.state.organizationUsersLoading, false);
  assert.equal(context.state.organizationUsersError, "");
  assert.equal(context.state.mySalesClaimsLoading, false);
  assert.equal(context.state.mySalesClaimsError, "");
  assert.equal(context.state.homeBootstrapTrackerSnapshotActive, true);
  assert.equal(context.state.trackerFilters.page, 2);
  assert.equal(context.state.trackerFilters.pageSize, 14);
  assert.equal(context.state.selectedEntryId, "shared");
  assert.equal(context.state.selectedEntry?.id, "shared");
  assert.equal(context.dom.trackerContext.textContent.endsWith("2 row(s)"), true);
  assert.deepEqual(renderCalls, [
    ["mergeActiveSalesClaims", [{ id: "company-1", title: "Company" }]],
    "syncUrlState",
    "renderMySalesClaimsPanel",
    "renderTrackerEntries",
    "renderEntriesPagination",
  ]);
});

test("hydrateHomeBootstrapCache reads the cache envelope and re-applies the bootstrap payload", () => {
  const readCalls = [];
  const { hydrateHomeBootstrapCache, context } = loadBootstrapAppHelpers({
    runtimeOverrides: {
      normalizeSalesOverviewPayload: (payload) => ({
        myItems: Array.isArray(payload?.my_items) ? payload.my_items : [],
        companyItems: Array.isArray(payload?.company_items) ? payload.company_items : [],
        organizationUsers: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
      }),
      normalizeTrackerFirstPagePayload: (payload, fallbackPageSize) => ({
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
    },
    globals: {
      readConsoleCacheEnvelope: (key, options) => {
        readCalls.push({ key, options });
        return {
          payload: {
            my_items: [{ id: "mine-1" }],
            company_items: [{ id: "company-1" }],
            organization_users: [{ id: "user-1" }],
            tracker_first_page: {
              items: [{ id: "cached-1", title: "Cached" }],
              page: "1",
              page_size: "20",
              total: "1",
              sort_contract: { mode: "default", order_by: [] },
            },
          },
        };
      },
    },
  });

  const loaded = hydrateHomeBootstrapCache();

  assert.equal(loaded, true);
  assert.deepEqual(readCalls, [{
    key: HOME_BOOTSTRAP_STORAGE_KEY,
    options: undefined,
  }]);
  assert.deepEqual(plain(context.state.mySalesClaims), [{ id: "mine-1" }]);
  assert.deepEqual(plain(context.state.companySalesClaims), [{ id: "company-1" }]);
  assert.deepEqual(plain(context.state.organizationUsers), [{ id: "user-1" }]);
  assert.deepEqual(plain(context.state.trackerEntries), [{ id: "cached-1", title: "Cached" }]);
  assert.equal(context.state.trackerEntriesTotal, 1);
  assert.equal(context.state.homeBootstrapTrackerSnapshotActive, true);
});

test("persistSalesOverviewCache, syncHomeBootstrapSalesCache, and persistHomeBootstrapCache use runtime payload helpers", () => {
  const writes = [];
  const runtimeCalls = {
    buildSalesOverviewCachePayload: [],
    mergeSalesOverviewIntoHomeBootstrapPayload: [],
    buildHomeBootstrapCachePayload: [],
  };
  const { persistSalesOverviewCache, syncHomeBootstrapSalesCache, persistHomeBootstrapCache, context } = loadBootstrapAppHelpers({
    runtimeOverrides: {
      buildSalesOverviewCachePayload: (payload) => {
        runtimeCalls.buildSalesOverviewCachePayload.push(plain(payload));
        return { scope: "sales-cache", payload: plain(payload) };
      },
      mergeSalesOverviewIntoHomeBootstrapPayload: (existingPayload, salesPayload) => {
        runtimeCalls.mergeSalesOverviewIntoHomeBootstrapPayload.push({
          existingPayload: plain(existingPayload),
          salesPayload: plain(salesPayload),
        });
        return { scope: "home-cache-sync", existingPayload: plain(existingPayload), salesPayload: plain(salesPayload) };
      },
      buildHomeBootstrapCachePayload: (payload) => {
        runtimeCalls.buildHomeBootstrapCachePayload.push(plain(payload));
        return { scope: "home-cache", payload: plain(payload) };
      },
    },
    globals: {
      readConsoleCacheEnvelope: (key, options) => {
        if (key !== HOME_BOOTSTRAP_STORAGE_KEY || !options?.allowStale) {
          return null;
        }
        return {
          payload: {
            generated_at: "2026-04-07T00:00:00.000Z",
            snapshot_version: 2,
            tracker_first_page: {
              items: [{ id: "cached-1" }],
              page: 1,
              page_size: 20,
              total: 1,
              sort_contract: { mode: "default", order_by: [] },
            },
            my_items: [{ id: "old-mine" }],
            company_items: [{ id: "old-company" }],
            organization_users: [{ id: "old-user" }],
          },
        };
      },
      writeConsoleCacheEnvelope: (key, payload) => {
        writes.push({ key, payload: plain(payload) });
      },
    },
  });

  persistSalesOverviewCache({
    my_items: [{ id: "mine-1" }],
    company_items: [{ id: "company-1" }],
    organization_users: [{ id: "user-1" }],
  });
  persistHomeBootstrapCache({
    my_items: [{ id: "mine-2" }],
    company_items: [{ id: "company-2" }],
    organization_users: [{ id: "user-2" }],
    tracker_first_page: {
      items: [{ id: "tracker-1" }],
      page: "3",
      page_size: "15",
      total: "5",
      sort_contract: { mode: "custom", order_by: ["updated_at_desc"] },
    },
    generated_at: "2026-04-07T12:00:00.000Z",
    snapshot_version: "4",
  });

  assert.deepEqual(runtimeCalls.buildSalesOverviewCachePayload, [{
    my_items: [{ id: "mine-1" }],
    company_items: [{ id: "company-1" }],
    organization_users: [{ id: "user-1" }],
  }]);
  assert.deepEqual(runtimeCalls.mergeSalesOverviewIntoHomeBootstrapPayload, [{
    existingPayload: {
      generated_at: "2026-04-07T00:00:00.000Z",
      snapshot_version: 2,
      tracker_first_page: {
        items: [{ id: "cached-1" }],
        page: 1,
        page_size: 20,
        total: 1,
        sort_contract: { mode: "default", order_by: [] },
      },
      my_items: [{ id: "old-mine" }],
      company_items: [{ id: "old-company" }],
      organization_users: [{ id: "old-user" }],
    },
    salesPayload: {
      my_items: [{ id: "mine-1" }],
      company_items: [{ id: "company-1" }],
      organization_users: [{ id: "user-1" }],
    },
  }]);
  assert.deepEqual(runtimeCalls.buildHomeBootstrapCachePayload, [{
    my_items: [{ id: "mine-2" }],
    company_items: [{ id: "company-2" }],
    organization_users: [{ id: "user-2" }],
    tracker_first_page: {
      items: [{ id: "tracker-1" }],
      page: "3",
      page_size: "15",
      total: "5",
      sort_contract: { mode: "custom", order_by: ["updated_at_desc"] },
    },
    generated_at: "2026-04-07T12:00:00.000Z",
    snapshot_version: "4",
  }]);
  assert.deepEqual(writes, [
    {
      key: SALES_OVERVIEW_STORAGE_KEY,
      payload: {
        scope: "sales-cache",
        payload: {
          my_items: [{ id: "mine-1" }],
          company_items: [{ id: "company-1" }],
          organization_users: [{ id: "user-1" }],
        },
      },
    },
    {
      key: HOME_BOOTSTRAP_STORAGE_KEY,
      payload: {
        scope: "home-cache-sync",
        existingPayload: {
          generated_at: "2026-04-07T00:00:00.000Z",
          snapshot_version: 2,
          tracker_first_page: {
            items: [{ id: "cached-1" }],
            page: 1,
            page_size: 20,
            total: 1,
            sort_contract: { mode: "default", order_by: [] },
          },
          my_items: [{ id: "old-mine" }],
          company_items: [{ id: "old-company" }],
          organization_users: [{ id: "old-user" }],
        },
        salesPayload: {
          my_items: [{ id: "mine-1" }],
          company_items: [{ id: "company-1" }],
          organization_users: [{ id: "user-1" }],
        },
      },
    },
    {
      key: HOME_BOOTSTRAP_STORAGE_KEY,
      payload: {
        scope: "home-cache",
        payload: {
          my_items: [{ id: "mine-2" }],
          company_items: [{ id: "company-2" }],
          organization_users: [{ id: "user-2" }],
          tracker_first_page: {
            items: [{ id: "tracker-1" }],
            page: "3",
            page_size: "15",
            total: "5",
            sort_contract: { mode: "custom", order_by: ["updated_at_desc"] },
          },
          generated_at: "2026-04-07T12:00:00.000Z",
          snapshot_version: "4",
        },
      },
    },
  ]);
  assert.equal(context.state.homeBootstrapTrackerSnapshotActive, false);
});

test("shouldUseHomeBootstrapTrackerSnapshot delegates to the runtime predicate", () => {
  const runtimeCalls = [];
  const { shouldUseHomeBootstrapTrackerSnapshot, context } = loadBootstrapAppHelpers({
    runtimeOverrides: {
      canUseHomeBootstrapTrackerSnapshot: (input) => {
        runtimeCalls.push(plain(input));
        return false;
      },
    },
    globals: {
      useGlobalTrackerEntriesScope: () => true,
    },
  });

  context.state.homeBootstrapTrackerSnapshotActive = true;
  context.state.trackerFilters.q = "";
  context.state.trackerFilters.region = "";
  context.state.trackerFilters.editedOnly = false;
  context.state.trackerFilters.page = 1;

  const result = shouldUseHomeBootstrapTrackerSnapshot();

  assert.equal(result, false);
  assert.deepEqual(runtimeCalls, [{
    uiMode: "user",
    globalScope: true,
    snapshotActive: true,
    query: "",
    region: "",
    editedOnly: false,
    page: 1,
  }]);
});

test("app.js delegates the home bootstrap helpers to the bootstrap runtime", () => {
  const source = extractAppHomeBootstrapDelegates();

  assert.match(source, /function getBootstrapRuntimeDepsHelpers\(\) \{/);
  assert.match(source, /function getHomeBootstrapRuntimeDeps\(\) \{/);
  assert.match(source, /APP_SUPPORT\.createBootstrapRuntimeDepsHelpers\(/);
  assert.match(source, /return BOOTSTRAP_RUNTIME\?\.applyHomeBootstrapPayload\?\.\(getHomeBootstrapRuntimeDeps\(\), payload \|\| \{\}\);/);
  assert.match(source, /return BOOTSTRAP_RUNTIME\?\.hydrateHomeBootstrapCache\?\.\(getHomeBootstrapRuntimeDeps\(\)\) \|\| false;/);
  assert.match(source, /return BOOTSTRAP_RUNTIME\?\.persistSalesOverviewCache\?\.\(getHomeBootstrapRuntimeDeps\(\), payload\);/);
  assert.match(source, /return BOOTSTRAP_RUNTIME\?\.syncHomeBootstrapSalesCache\?\.\(getHomeBootstrapRuntimeDeps\(\), payload\);/);
  assert.match(source, /return BOOTSTRAP_RUNTIME\?\.persistHomeBootstrapCache\?\.\(getHomeBootstrapRuntimeDeps\(\), payload\);/);
  assert.match(source, /return BOOTSTRAP_RUNTIME\?\.shouldUseHomeBootstrapTrackerSnapshot\?\.\(getHomeBootstrapRuntimeDeps\(\)\) \|\| false;/);
  assert.match(source, /return getBootstrapRuntimeDepsHelpers\(\)\.buildHomeBootstrapRuntimeDeps\(\);/);
  assert.doesNotMatch(source, /state\.trackerEntriesTotal\s*=\s*Number\(/);
});

test("app.js centralizes console bootstrap runtime deps through the app-support helper", () => {
  const source = extractConsoleDataRuntimeSources();

  assert.match(source, /function getBootstrapRuntimeDepsHelpers\(\) \{/);
  assert.match(source, /APP_SUPPORT\.createBootstrapRuntimeDepsHelpers\(/);
  assert.match(source, /return getBootstrapRuntimeDepsHelpers\(\)\.buildConsoleDataRuntimeDeps\(\);/);
  assert.match(source, /return getBootstrapRuntimeDepsHelpers\(\)\.buildHomeBootstrapRuntimeDeps\(\);/);
  assert.doesNotMatch(source, /return \{\s*state,\s*api,\s*flash,/);
});

test("loadHomeBootstrap and loadSalesOverview forward getConsoleDataRuntimeDeps to the runtime", async () => {
  const runtimeCalls = [];
  const runtime = {
    loadHomeBootstrap: async (deps, options) => {
      runtimeCalls.push({
        name: "loadHomeBootstrap",
        deps,
        options: plain(options),
      });
      return { source: "home-bootstrap" };
    },
    loadSalesOverview: async (deps, options) => {
      runtimeCalls.push({
        name: "loadSalesOverview",
        deps,
        options: plain(options),
      });
      return { source: "sales-overview" };
    },
  };

  const {
    loadHomeBootstrap,
    loadSalesOverview,
    getConsoleDataRuntimeDeps,
    getConsoleDataRuntimeDepsIdentitySnapshot,
    context,
  } = loadConsoleDataRuntimeWrappers({
    runtime,
    globals: {
      canUseAdminMode: () => false,
      getVisibleSalesProjectIds: () => ["project-1"],
      isActiveSalesClaim: (claim) => Boolean(claim?.is_active),
      isCurrentUserClaimOwner: () => true,
      mergeActiveSalesClaims: () => {},
      mergeOrganizationInvitations: () => {},
      replaceVisibleSalesClaims: () => {},
      loadTrackerEntries: () => {},
      renderMySalesClaimsPanel: () => {},
      renderTrackerEntries: () => {},
      renderSalesSummaryPanel: () => {},
      renderOrganizationAdminPanel: () => {},
      applyHomeBootstrapPayload: () => {},
      applySalesOverviewPayload: () => {},
      persistHomeBootstrapCache: () => {},
      persistSalesOverviewCache: () => {},
      hasCachedHomeBootstrapData: () => false,
      hasCachedSalesOverviewData: () => false,
      isMissingHomeBootstrapEndpointError: () => false,
      isMissingSalesOverviewEndpointError: () => false,
    },
  });

  const homeResult = await loadHomeBootstrap({ silent: true, force: true });
  const salesResult = await loadSalesOverview({ silent: false, force: true });
  const depsSnapshot = getConsoleDataRuntimeDeps();
  const expectedKeys = [
    "state",
    "api",
    "flash",
    "canUseAdminMode",
    "getVisibleSalesProjectIds",
    "isActiveSalesClaim",
    "isCurrentUserClaimOwner",
    "mergeActiveSalesClaims",
    "mergeOrganizationInvitations",
    "replaceVisibleSalesClaims",
    "loadTrackerEntries",
    "renderMySalesClaimsPanel",
    "renderTrackerEntries",
    "renderSalesSummaryPanel",
    "renderOrganizationAdminPanel",
    "applyHomeBootstrapPayload",
    "applySalesOverviewPayload",
    "persistHomeBootstrapCache",
    "persistSalesOverviewCache",
    "hasCachedHomeBootstrapData",
    "hasCachedSalesOverviewData",
    "isMissingHomeBootstrapEndpointError",
    "isMissingSalesOverviewEndpointError",
  ];
  function assertConsoleDataRuntimeDepsShape(deps) {
    assert.deepEqual(Object.keys(deps).sort(), expectedKeys.slice().sort());
    const identityResults = getConsoleDataRuntimeDepsIdentitySnapshot(deps);
    assert.deepEqual(Object.keys(identityResults).sort(), expectedKeys.slice().sort());
    for (const key of expectedKeys) {
      assert.equal(identityResults[key], true, key);
    }
    assert.equal(deps.loadTrackerEntries.length, 0);
  }

  assert.deepEqual(homeResult, { source: "home-bootstrap" });
  assert.deepEqual(salesResult, { source: "sales-overview" });
  assertConsoleDataRuntimeDepsShape(depsSnapshot);
  assert.deepEqual(runtimeCalls.map(({ name, options }) => ({ name, options })), [
    {
      name: "loadHomeBootstrap",
      options: { silent: true, force: true },
    },
    {
      name: "loadSalesOverview",
      options: { silent: false, force: true },
    }
  ]);
  assertConsoleDataRuntimeDepsShape(runtimeCalls[0].deps);
  assertConsoleDataRuntimeDepsShape(runtimeCalls[1].deps);
});
