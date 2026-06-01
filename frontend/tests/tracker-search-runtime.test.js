const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function buildTrackerSearchContext({ apiImpl } = {}) {
  const source = fs.readFileSync(path.join(__dirname, "..", "tracker-controller.js"), "utf8");

  class AbortControllerMock {
    constructor() {
      this.signal = { aborted: false };
    }

    abort() {
      this.signal.aborted = true;
    }
  }

  const calls = {
    api: [],
    unread: 0,
    events: 0,
  };
  const deferredApiCalls = [];
  const defaultApi = (requestPath, options = {}) => {
    calls.api.push({ requestPath, options });
    let resolve;
    let reject;
    const promise = new Promise((res, rej) => {
      resolve = res;
      reject = rej;
    });
    deferredApiCalls.push({ resolve, reject, signal: options.signal });
    return promise;
  };

  const context = {
    window: {},
    document: {},
    URLSearchParams,
    AbortController: AbortControllerMock,
    Date,
    Map,
    Promise,
    FormData,
    console,
  };
  vm.createContext(context);
  vm.runInContext(source, context);

  const state = {
    uiMode: "user",
    trackerEntries: [],
    trackerEntriesTotal: 0,
    salesClaimsByProjectId: {},
    salesClaimDrafts: {},
    trackerEntriesError: "",
    trackerEntriesRequest: null,
    trackerEntriesRequestKey: "",
    trackerFilters: {
      q: "",
      region: "",
      editedOnly: false,
      page: 1,
      pageSize: 20,
    },
    trackerBoardEdit: {
      entryId: null,
    },
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    selectedEntryId: null,
    selectedEntry: null,
    selectedEntryLoadingId: null,
    selectedEntryError: "",
    homeBootstrapTrackerSnapshotActive: false,
    trackerChangeEventsAvailability: "available",
    trackerChangeEventsUnread: 0,
    trackerChangeEvents: [],
    trackerChangeEventsLoading: false,
    trackerChangeEventsLoadedAt: 0,
    selectedEntryChangeEvents: [],
    selectedEntryChangeEventsLoading: false,
  };

  const dom = {
    trackerContext: { textContent: "" },
    trackerQuery: { value: "" },
    trackerPageSize: { value: "20" },
    trackerChangeBellBadge: {
      textContent: "",
      classList: {
        add() {},
        remove() {},
        toggle() {},
      },
    },
    panelMissingReport: null,
  };

  const controller = context.window.TRACKER_CONTROLLER.createTrackerController({
    state,
    dom,
    api: (...args) => (apiImpl || defaultApi)(...args),
    flash: () => {},
    setBusy: () => {},
    FormData,
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    syncUrlState: () => {},
    readRunFiltersFromControls: () => {},
    renderRuns: () => {},
    renderRunsPagination: () => {},
    renderRunDetail: () => {},
    renderRunEventStatus: () => {},
    renderTrackerEntries: () => {},
    renderEntriesPagination: () => {},
    renderSalesSummaryPanel: () => {},
    renderTrackerChangeEventsPanel: () => {},
    renderTrackerContactResolutionSummary: () => {},
    renderBackfillConflictsPanel: () => {},
    renderTrackerCleanupPreview: () => {},
    renderProjectRelatedHosts: () => {},
    touchSyncMeta: () => {},
    persistTrackerChangeEventsCache: () => {},
    clearTrackerChangeEventsCache: () => {},
    handleOutOfRangePageError: () => false,
    canLoadProtectedConsoleData: () => true,
    TRACKER_REGION_OPTIONS: [],
    useGlobalTrackerEntriesScope: () => true,
    resolveActiveTrackerRunId: () => null,
    shouldUseHomeBootstrapTrackerSnapshot: () => false,
    isProjectTrackerRun: () => false,
    schedulePolling: () => {},
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    loadBackfillConflicts: async () => {},
    loadVisibleSalesClaims: async () => {},
    requireTrackerDiagnosticsRuntime: () => ({
      filterBackfillConflictsBySourceRun(items) {
        return items;
      },
    }),
    clearProjectRelatedRefresh: () => {},
    maybeScheduleProjectRelatedRefresh: () => {},
    canReuseProjectRelatedPayload: () => false,
    cacheProjectRelatedPayload: () => null,
    isProjectRelatedVisible: () => false,
    resolveTrackerEntryProjectId: () => null,
    ensureTrackerEntryProjectId: async () => null,
    TRACKER_ENTRY_RUNTIME: null,
    TRACKER_DETAIL_PREFETCH_LIMIT: 3,
    warmTrackerEntriesDownload: async () => {},
    closeDrawer: () => {},
    renderTrackerBoard: () => {},
    resetTrackerBoardEdit: () => {},
    loadAdminConsoleData: async () => {},
    buildSelectedEntryAuditMarkup: () => "",
    loadSelectedEntryDetail: async () => {},
    renderTrackerMissingReport: () => {},
    renderSelectedEntryChangeEvents: () => {},
    renderSelectedEntry: () => {},
    renderSelectedEntryLoading: () => {},
    resolveTrackerPatchActorLabel: () => "",
    runTypeLabel: (value) => String(value ?? ""),
  });

  controller.loadTrackerChangeEventUnreadCount = async () => {
    calls.unread += 1;
  };
  controller.loadTrackerChangeEvents = async () => {
    calls.events += 1;
  };
  controller.prefetchVisibleProjectRelatedNotices = () => {};

  const harnessContext = {
    state,
    dom,
    loadTrackerEntries: controller.loadTrackerEntries,
  };

  return {
    context: harnessContext,
    calls,
    deferredApiCalls,
    loadTrackerEntries: controller.loadTrackerEntries,
  };
}

function loadApiHelperContext({ fetchImpl } = {}) {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("class ApiRequestError extends Error {");
  const end = source.indexOf("function handleOutOfRangePageError(", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate ApiRequestError/api helper in app.js");
  }
  const context = {
    window: {
      setTimeout,
      clearTimeout,
    },
    Date,
    AbortController,
    FormData,
    fetch: fetchImpl,
    state: {
      auth: {
        enabled: false,
        authenticated: false,
        authorized: false,
        user: null,
        message: "",
      },
    },
    refreshAuthSessionState: async () => null,
    renderAuthUi: () => {},
    console,
  };
  vm.createContext(context);
  vm.runInContext(`${source.slice(start, end)}\nglobalThis.__api = api;`, context);
  return context;
}

test("loadTrackerEntries aborts superseded tracker search requests", () => {
  const harness = buildTrackerSearchContext();
  harness.context.dom.trackerQuery.value = "alpha";
  harness.loadTrackerEntries();

  assert.equal(harness.calls.api.length, 1);
  assert.ok(harness.calls.api[0].options.signal, "expected loadTrackerEntries to forward an abort signal");
  assert.equal(harness.calls.api[0].options.signal.aborted, false);

  harness.context.dom.trackerQuery.value = "beta";
  harness.loadTrackerEntries();

  assert.equal(harness.calls.api.length, 2);
  assert.equal(
    harness.calls.api[0].options.signal.aborted,
    true,
    "expected the prior in-flight tracker search to be aborted",
  );
});

test("loadTrackerEntries does not auto-refresh tracker change events after successful search", async () => {
  const harness = buildTrackerSearchContext({
    apiImpl: async () => ({ items: [], total: 0 }),
  });

  await harness.loadTrackerEntries();

  assert.equal(harness.calls.unread, 0);
  assert.equal(harness.calls.events, 0);
});

test("api preserves external aborts instead of rewriting them as request timeouts", async () => {
  const externalController = new AbortController();
  const context = loadApiHelperContext({
    fetchImpl: (_requestPath, options = {}) => new Promise((_resolve, reject) => {
      options.signal.addEventListener("abort", () => {
        const error = new Error("aborted");
        error.name = "AbortError";
        reject(error);
      }, { once: true });
    }),
  });

  const promise = context.__api("/api/tracker-entry-summaries", {
    signal: externalController.signal,
    timeoutMs: 5000,
  });
  externalController.abort();

  await assert.rejects(
    promise,
    (error) => {
      assert.equal(error?.name, "AbortError");
      assert.equal(String(error?.message || "").includes("Request timed out"), false);
      return true;
    },
  );
});
