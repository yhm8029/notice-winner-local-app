const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadTrackerEntriesContext(overrides = {}) {
  const source = fs.readFileSync(path.join(__dirname, "..", "tracker-controller.js"), "utf8");

  class AbortControllerMock {
    constructor() {
      this.signal = { aborted: false };
    }

    abort() {
      this.signal.aborted = true;
    }
  }

  const runtimeContext = {
    window: {},
    document: {},
    URLSearchParams,
    AbortController: AbortControllerMock,
    Date,
    Math,
    Map,
    Promise,
    FormData,
    console,
  };

  vm.createContext(runtimeContext);
  vm.runInContext(source, runtimeContext);

  const state = {
    uiMode: "member",
    trackerEntries: [],
    trackerEntriesTotal: 0,
    salesClaimsByProjectId: {},
    salesClaimDrafts: {},
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    selectedEntry: null,
    selectedEntryId: null,
    selectedEntryLoadingId: null,
    selectedEntryError: "",
    trackerEntriesError: "",
    trackerEntriesRequest: null,
    trackerEntriesRequestKey: "",
    trackerBoardEdit: {
      entryId: null,
    },
    trackerFilters: {
      page: 1,
      pageSize: 20,
      q: "",
      region: "",
      editedOnly: false,
    },
    homeBootstrapTrackerSnapshotActive: true,
    trackerChangeEventsAvailability: "available",
    trackerChangeEventsUnread: 0,
    trackerChangeEvents: [],
    trackerChangeEventsLoading: false,
    trackerChangeEventsLoadedAt: 0,
    selectedEntryChangeEvents: [],
    selectedEntryChangeEventsLoading: false,
  };

  const dom = {
    trackerContext: {
      textContent: "",
    },
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
  };

  const controller = runtimeContext.window.TRACKER_CONTROLLER.createTrackerController({
    state,
    dom,
    canLoadProtectedConsoleData: () => true,
    TRACKER_REGION_OPTIONS: [],
    useGlobalTrackerEntriesScope: () => true,
    resolveActiveTrackerRunId: () => null,
    readRunFiltersFromControls: () => {},
    shouldUseHomeBootstrapTrackerSnapshot: () => false,
    api: async () => ({
      total: 1,
      items: [
        {
          id: "entry-1",
          project_name: "Alpha",
        },
      ],
    }),
    flash: () => {},
    setBusy: () => {},
    FormData,
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    syncUrlState: () => {},
    renderRuns: () => {},
    renderRunsPagination: () => {},
    renderRunDetail: () => {},
    renderRunEventStatus: () => {},
    renderTrackerEntries: () => {},
    renderEntriesPagination: () => {},
    renderSalesSummaryPanel: () => {},
    closeDrawer: () => {},
    touchSyncMeta: () => {},
    persistTrackerChangeEventsCache: () => {},
    clearTrackerChangeEventsCache: () => {},
    renderTrackerChangeEventsPanel: () => {},
    renderTrackerContactResolutionSummary: () => {},
    renderBackfillConflictsPanel: () => {},
    renderTrackerCleanupPreview: () => {},
    renderProjectRelatedHosts: () => {},
    warmTrackerEntriesDownload: async () => {},
    loadTrackerChangeEventUnreadCount: async () => {},
    loadTrackerChangeEvents: async () => {},
    prefetchVisibleProjectRelatedNotices: () => {},
    loadVisibleSalesClaims: async () => {},
    handleOutOfRangePageError: () => false,
    isProjectTrackerRun: () => false,
    schedulePolling: () => {},
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    loadBackfillConflicts: async () => {},
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
    ...overrides,
  });

  controller.prefetchVisibleProjectRelatedNotices = () => {};

  return {
    state,
    dom,
    loadTrackerEntries: controller.loadTrackerEntries,
  };
}

test("loadTrackerEntries does not auto-warm tracker download after global list refresh", async () => {
  let warmCalls = 0;
  const context = loadTrackerEntriesContext({
    warmTrackerEntriesDownload: async () => {
      warmCalls += 1;
    },
  });

  await context.loadTrackerEntries();

  assert.equal(context.state.trackerEntries.length, 1);
  assert.equal(context.state.trackerEntries[0].id, "entry-1");
  assert.equal(warmCalls, 0);
});
