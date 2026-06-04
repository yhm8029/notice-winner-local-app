const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { pathToFileURL } = require("node:url");
const controllerPath = path.resolve(__dirname, "..", "tracker-controller.js");
const controllerRuntimePaths = [
  path.resolve(__dirname, "..", "tracker-controller-diagnostics-runtime.js"),
  path.resolve(__dirname, "..", "tracker-controller-runs-runtime.js"),
  path.resolve(__dirname, "..", "tracker-controller-entries-runtime.js"),
];

function loadTrackerControllerFactory() {
  const source = fs.readFileSync(controllerPath, "utf8");
  const context = { window: {}, URLSearchParams };
  vm.createContext(context);
  for (const runtimePath of controllerRuntimePaths) {
    const runtimeSource = fs.readFileSync(runtimePath, "utf8");
    vm.runInContext(runtimeSource, context);
  }
  vm.runInContext(source, context);
  return context.window.TRACKER_CONTROLLER.createTrackerController;
}

test("tracker controller source stays within the modularization line budget", () => {
  const lineCount = fs.readFileSync(controllerPath, "utf8").split(/\r?\n/).length;
  assert.ok(lineCount <= 700, `expected tracker-controller.js to stay at 700 lines or fewer, got ${lineCount}`);
});

function createDeferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function createController(overrides = {}) {
  const state = {
    trackerEntries: [],
    trackerEntryDetailCache: {},
    selectedEntryDetailRequests: {},
    selectedEntryId: null,
    selectedEntry: null,
    selectedEntryLoadingId: null,
    selectedEntryError: "",
    uiMode: "admin",
    trackerFilters: { page: 1, pageSize: 10, q: "", region: "", noticeYear: "", editedOnly: false },
    trackerEntriesTotal: 0,
    trackerEntriesRequest: null,
    trackerEntriesRequestKey: "",
    trackerEntriesError: "",
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    trackerBoardEdit: { entryId: "" },
    trackerChangeEventsAvailability: "available",
    trackerChangeEventsUnread: 0,
    trackerChangeEvents: [],
    trackerChangeEventsLoading: false,
    salesClaimsByProjectId: {},
    salesClaimDrafts: {},
  };
  const dom = {
    trackerQuery: { value: "" },
    trackerEditedOnly: null,
    trackerPageSize: { value: "10" },
    trackerNoticeYear: { value: "" },
    trackerContext: { textContent: "" },
    ...overrides.dom,
  };
  const renderSelectedEntryCalls = [];
  const renderSelectedEntryLoadingCalls = [];
  const flashCalls = [];
  const factory = loadTrackerControllerFactory();
  const controller = factory({
    state,
    dom,
    api: async () => {
      throw new Error("api not stubbed");
    },
    flash: (message, level) => {
      flashCalls.push({ message, level });
    },
    setBusy: () => {},
    FormData: typeof FormData === "function" ? FormData : undefined,
    renderSelectedEntry: (...args) => {
      renderSelectedEntryCalls.push(args);
    },
    renderSelectedEntryLoading: (...args) => {
      renderSelectedEntryLoadingCalls.push(args);
    },
    renderTrackerEntries: () => {},
    renderEntriesPagination: () => {},
    renderSalesSummaryPanel: () => {},
    renderTrackerChangeEventsPanel: () => {},
    loadTrackerEntries: async () => {},
    loadTrackerChangeEvents: async () => {},
    loadTrackerMissingReport: async () => {},
    loadSelectedEntryAudit: async () => {},
    loadSelectedEntryChangeEvents: async () => {},
    replaceTrackerEntryInState: () => {},
    toTrackerEntrySummary: (entry) => ({
      id: entry.id,
      project_name: entry.project_name || "",
      entry_key: entry.entry_key || "",
    }),
    canLoadProtectedConsoleData: () => true,
    isProjectTrackerRun: (runType) => {
      const raw = String(runType || "").trim();
      return raw === "project_tracker" || raw === "winner_pipeline";
    },
    resolveActiveTrackerRunId: () => "run-1",
    useGlobalTrackerEntriesScope: () => false,
    syncUrlState: () => {},
    touchSyncMeta: () => {},
    prefetchVisibleProjectRelatedNotices: () => {},
    resetTrackerBoardEdit: () => {},
    warmTrackerEntriesDownload: async () => {},
    loadVisibleSalesClaims: async () => {},
    TRACKER_DETAIL_PREFETCH_LIMIT: 2,
    ...overrides,
  });
  return {
    controller,
    state,
    dom,
    renderSelectedEntryCalls,
    renderSelectedEntryLoadingCalls,
    flashCalls,
  };
}

test("tracker controller computes the diagnostics scope from the selected tracker run", async () => {
  const mod = await import(pathToFileURL(controllerPath).href);
  const state = {
    selectedRun: {
      id: "project-run-1",
      run_type: "project_tracker",
    },
    selectedTrackerRun: {
      id: "tracker-run-9",
      run_type: "tracker_export",
      parent_run_id: "source-run-7",
    },
  };
  const controller = mod.createTrackerController({
    state,
    dom: {},
  });

  assert.deepEqual(controller.getTrackerDiagnosticsScope(), {
    trackerRunId: "tracker-run-9",
    sourceRunId: "source-run-7",
    scopeLabel: "tracker_export tracker-run-9 / source source-run-7",
  });
  assert.deepEqual(
    controller.getTrackerDiagnosticsScope({
      id: "tracker-run-9",
      run_type: "tracker_export",
      parent_run_id: "source-run-7",
    }),
    {
      trackerRunId: "tracker-run-9",
      sourceRunId: "source-run-7",
      scopeLabel: "tracker_export tracker-run-9 / source source-run-7",
    },
  );
  state.selectedTrackerRun = null;
  assert.equal(controller.getTrackerDiagnosticsScope({ id: "run-2", run_type: "project_tracker" }), null);
});

test("tracker controller fans out operational diagnostics in admin mode", async () => {
  const calls = [];
  const mod = await import(pathToFileURL(controllerPath).href);
  const controller = mod.createTrackerController({
    state: { uiMode: "admin" },
    dom: {},
  });
  controller.loadTrackerContactResolutionSummary = async (options) => {
    calls.push(["contact", options]);
  };
  controller.loadTrackerCleanupPreview = async (options) => {
    calls.push(["cleanup", options]);
  };
  controller.loadBackfillConflicts = async (options) => {
    calls.push(["backfill", options]);
  };

  controller.refreshTrackerOperationalDiagnostics({ silent: false });

  assert.deepEqual(calls, [
    ["contact", { silent: false }],
    ["cleanup", { silent: false }],
    ["backfill", { silent: false }],
  ]);
});

test("tracker controller loads tracker contact resolution summary for the resolved scope", async () => {
  const apiCalls = [];
  const renderCalls = [];
  const mod = await import(pathToFileURL(controllerPath).href);
  const controller = mod.createTrackerController({
    state: {
      uiMode: "admin",
      selectedRun: {
        id: "project-run-1",
        run_type: "project_tracker",
      },
      selectedTrackerRun: {
        id: "tracker-run-42",
        run_type: "tracker_export",
        parent_run_id: "source-run-88",
      },
      trackerContactResolutionSummary: null,
      trackerContactResolutionLoading: false,
    },
    dom: {
      trackerContactResolutionPanel: {},
    },
    renderTrackerContactResolutionSummary: () => {
      renderCalls.push("render");
    },
    api: async (url, options) => {
      apiCalls.push([url, options]);
      return { items: [], summary: { total: 1 } };
    },
  });

  await controller.loadTrackerContactResolutionSummary({ silent: true });

  assert.deepEqual(apiCalls, [[
    "/api/admin/tracker-contact-resolution-summary?limit=12&source_tracker_run_id=tracker-run-42",
    { timeoutMs: 90000 },
  ]]);
  assert.deepEqual(renderCalls, ["render", "render"]);
  assert.equal(controller.getTrackerDiagnosticsScope().trackerRunId, "tracker-run-42");
});

test("tracker controller loads tracker template status through the controller seam", async () => {
  const apiCalls = [];
  const renderCalls = [];
  const mod = await import(pathToFileURL(controllerPath).href);
  const controller = mod.createTrackerController({
    state: {
      uiMode: "admin",
      trackerTemplateStatus: null,
    },
    dom: {
      trackerTemplateStatus: {
        classList: {
          add() {},
          remove() {},
        },
        textContent: "",
      },
    },
    api: async (url, options) => {
      apiCalls.push([url, options]);
      return {
        updated_at: "2024-04-01T09:30:00Z",
        original_file_name: "tracker.xlsx",
        source_label: "server",
      };
    },
  });
  controller.renderTrackerTemplateStatus = (errorMessage = "") => {
    renderCalls.push(errorMessage);
  };

  await controller.loadTrackerTemplateStatus({ silent: true });

  assert.deepEqual(apiCalls, [[
    "/api/tracker-template",
    { timeoutMs: 20000 },
  ]]);
  assert.deepEqual(renderCalls, [""]);
});

test("tracker controller uploads tracker template files through the controller seam", async () => {
  const busyCalls = [];
  const apiCalls = [];
  const renderCalls = [];
  class FakeFormData {
    constructor() {
      this.entries = [];
    }
    append(name, value) {
      this.entries.push([name, value]);
    }
  }
  const uploadButton = { label: "양식 업로드" };
  const file = { name: "uploaded-template.xlsx" };
  const { controller, state, flashCalls } = createController({
    dom: {
      trackerTemplateUploadButton: uploadButton,
    },
    setBusy: (...args) => {
      busyCalls.push(args);
    },
    FormData: FakeFormData,
    api: async (url, options) => {
      apiCalls.push([url, options]);
      return {
        updated_at: "2024-04-01T09:30:00Z",
        source_label: "server",
      };
    },
  });
  controller.renderTrackerTemplateStatus = (errorMessage = "") => {
    renderCalls.push(errorMessage);
  };

  await controller.uploadTrackerTemplate(file);

  assert.equal(apiCalls.length, 1);
  assert.equal(apiCalls[0][0], "/api/tracker-template");
  assert.equal(apiCalls[0][1].method, "POST");
  assert.equal(apiCalls[0][1].timeoutMs, 60000);
  assert.ok(apiCalls[0][1].body instanceof FakeFormData);
  assert.deepEqual(apiCalls[0][1].body.entries, [["file", file]]);
  assert.deepEqual(busyCalls, [
    [uploadButton, true, "업로드 중..."],
    [uploadButton, false, "양식 업로드"],
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(state.trackerTemplateStatus || null)), {
    updated_at: "2024-04-01T09:30:00Z",
    source_label: "server",
  });
  assert.deepEqual(renderCalls, [""]);
  assert.deepEqual(flashCalls, [
    { message: "양식 업로드 완료: uploaded-template.xlsx", level: undefined },
  ]);
});

test("tracker controller resets the tracker template override through the controller seam", async () => {
  const busyCalls = [];
  const apiCalls = [];
  const renderCalls = [];
  const resetButton = { label: "양식 초기화" };
  const { controller, state, flashCalls } = createController({
    dom: {
      trackerTemplateResetButton: resetButton,
    },
    setBusy: (...args) => {
      busyCalls.push(args);
    },
    api: async (url, options) => {
      apiCalls.push([url, options]);
      return {
        updated_at: "2024-04-02T09:30:00Z",
        source_label: "server",
      };
    },
  });
  state.trackerTemplateStatus = {
    updated_at: "2024-03-01T00:00:00Z",
    source_label: "override",
  };
  controller.renderTrackerTemplateStatus = (errorMessage = "") => {
    renderCalls.push(errorMessage);
  };

  await controller.resetTrackerTemplateOverride();

  assert.equal(apiCalls.length, 1);
  assert.equal(apiCalls[0][0], "/api/tracker-template");
  assert.equal(apiCalls[0][1].method, "DELETE");
  assert.equal(apiCalls[0][1].timeoutMs, 20000);
  assert.deepEqual(busyCalls, [
    [resetButton, true, "초기화 중..."],
    [resetButton, false, "양식 초기화"],
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(state.trackerTemplateStatus || null)), {
    updated_at: "2024-04-02T09:30:00Z",
    source_label: "server",
  });
  assert.deepEqual(renderCalls, [""]);
  assert.deepEqual(flashCalls, [
    { message: "서버 업로드 양식을 제거하고 기본 양식으로 되돌렸습니다.", level: undefined },
  ]);
});

test("tracker controller fetches, caches, and deduplicates tracker entry details", async () => {
  const deferred = createDeferred();
  let apiCalls = 0;
  const { controller, state, flashCalls } = createController({
    api: async (url) => {
      apiCalls += 1;
      assert.equal(url, "/api/tracker-entries/entry-1");
      return deferred.promise;
    },
  });
  state.trackerEntries = [{ id: "entry-1", project_name: "Old name", entry_key: "K-1" }];
  state.selectedEntryId = "entry-1";

  const firstRequest = controller.fetchTrackerEntryDetail("entry-1");
  const secondRequest = controller.fetchTrackerEntryDetail("entry-1");

  assert.equal(apiCalls, 1);
  assert.ok(state.selectedEntryDetailRequests["entry-1"]);

  deferred.resolve({
    id: "entry-1",
    project_name: "New name",
    entry_key: "K-1",
  });

  const entry = await firstRequest;
  assert.deepEqual(entry, {
    id: "entry-1",
    project_name: "New name",
    entry_key: "K-1",
  });
  assert.deepEqual(JSON.parse(JSON.stringify(state.trackerEntries)), [
    { id: "entry-1", project_name: "New name", entry_key: "K-1" },
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(state.trackerEntryDetailCache["entry-1"])), entry);
  assert.deepEqual(JSON.parse(JSON.stringify(state.selectedEntry)), entry);
  assert.equal(JSON.stringify(state.selectedEntryDetailRequests), "{}");
  assert.deepEqual(flashCalls, []);
});

test("tracker controller prefetches tracker entry details without duplicates or cached ids", () => {
  const requested = [];
  const { controller, state } = createController({
    api: async (url) => {
      requested.push(url);
      return new Promise(() => {});
    },
  });
  state.trackerEntryDetailCache = { b: { id: "b" } };
  state.selectedEntryDetailRequests = { c: Promise.resolve({ id: "c" }) };

  controller.prefetchTrackerEntryDetails([
    { id: "a" },
    { id: "a" },
    { id: "b" },
    { id: "c" },
    { id: "d" },
  ]);

  assert.deepEqual(requested, [
    "/api/tracker-entries/a",
    "/api/tracker-entries/d",
  ]);
});

test("tracker controller resolves project tracker runs to the best tracker export child", async () => {
  const apiCalls = [];
  const renderRunDetailCalls = [];
  const { controller, state } = createController({
    api: async (url) => {
      apiCalls.push(url);
      if (url === "/api/runs/run-1") {
        return {
          id: "run-1",
          run_type: "project_tracker",
          status: "success",
          summary: { output: { auto_tracker_export_run_id: " tracker-c " } },
        };
      }
      if (url === "/api/runs?parent_run_id=run-1&page=1&page_size=50") {
        return {
          items: [
            { id: "noise", run_type: "project_tracker", status: "success", created_at: "2026-04-10T00:10:00Z" },
            { id: "tracker-a", run_type: "tracker_export", status: "running", created_at: "2026-04-10T00:05:00Z" },
            { id: "tracker-b", run_type: "tracker_export", status: "queued", created_at: "2026-04-10T00:06:00Z" },
            { id: "tracker-c", run_type: "tracker_export", status: "queued", created_at: "2026-04-10T00:07:00Z" },
          ],
        };
      }
      if (url === "/api/runs/tracker-a") {
        return {
          id: "tracker-a",
          run_type: "tracker_export",
          status: "running",
          created_at: "2026-04-10T00:05:00Z",
        };
      }
      throw new Error(`unexpected url: ${url}`);
    },
    renderRunDetail: (run) => {
      renderRunDetailCalls.push(run && run.id);
    },
    renderRunEventStatus: () => {},
    schedulePolling: () => {},
    syncUrlState: () => {},
    touchSyncMeta: () => {},
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    refreshTrackerOperationalDiagnostics: () => {},
  });
  state.uiMode = "user";
  state.selectedRunId = "run-1";
  state.selectedTrackerRunId = "tracker-old";
  state.selectedTrackerWorkbookArtifactId = "workbook-old";

  await controller.refreshSelectedRun();

  assert.deepEqual(apiCalls, [
    "/api/runs/run-1",
    "/api/runs?parent_run_id=run-1&page=1&page_size=50",
    "/api/runs/tracker-a",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(state.selectedRun)), {
    id: "run-1",
    run_type: "project_tracker",
    status: "success",
    summary: { output: { auto_tracker_export_run_id: " tracker-c " } },
  });
  assert.deepEqual(JSON.parse(JSON.stringify(state.selectedTrackerRun)), {
    id: "tracker-a",
    run_type: "tracker_export",
    status: "running",
    created_at: "2026-04-10T00:05:00Z",
  });
  assert.equal(state.selectedTrackerRunId, "tracker-a");
  assert.equal(state.selectedTrackerWorkbookArtifactId, null);
  assert.deepEqual(renderRunDetailCalls, ["run-1"]);
});

test("tracker controller keeps the selected tracker export run object while resolving a preferred child id", async () => {
  const apiCalls = [];
  const { controller, state } = createController({
    api: async (url) => {
      apiCalls.push(url);
      if (url === "/api/runs/tracker-root") {
        return {
          id: "tracker-root",
          run_type: "tracker_export",
          status: "failed",
          parent_run_id: "run-1",
          created_at: "2026-04-10T00:03:00Z",
        };
      }
      if (url === "/api/runs?parent_run_id=run-1&page=1&page_size=50") {
        return {
          items: [
            { id: "tracker-root", run_type: "tracker_export", status: "failed", created_at: "2026-04-10T00:03:00Z" },
            { id: "tracker-success", run_type: "tracker_export", status: "success", created_at: "2026-04-10T00:05:00Z" },
          ],
        };
      }
      throw new Error(`unexpected url: ${url}`);
    },
    renderRunDetail: () => {},
    renderRunEventStatus: () => {},
    schedulePolling: () => {},
    syncUrlState: () => {},
    touchSyncMeta: () => {},
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    refreshTrackerOperationalDiagnostics: () => {},
  });
  state.uiMode = "user";
  state.selectedRunId = "tracker-root";
  state.selectedTrackerRunId = "tracker-old";
  state.selectedTrackerWorkbookArtifactId = "workbook-old";

  await controller.refreshSelectedRun();

  assert.deepEqual(apiCalls, [
    "/api/runs/tracker-root",
    "/api/runs?parent_run_id=run-1&page=1&page_size=50",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(state.selectedRun)), {
    id: "tracker-root",
    run_type: "tracker_export",
    status: "failed",
    parent_run_id: "run-1",
    created_at: "2026-04-10T00:03:00Z",
  });
  assert.deepEqual(JSON.parse(JSON.stringify(state.selectedTrackerRun)), {
    id: "tracker-root",
    run_type: "tracker_export",
    status: "failed",
    parent_run_id: "run-1",
    created_at: "2026-04-10T00:03:00Z",
  });
  assert.equal(state.selectedTrackerRunId, "tracker-success");
  assert.equal(state.selectedTrackerWorkbookArtifactId, null);
});

test("tracker controller loadTrackerEntries still uses out-of-range handler deps", async () => {
  const apiCalls = [];
  const outOfRangeCalls = [];
  const syncUrlStateCalls = [];
  const { controller, state } = createController({
    api: async (url) => {
      apiCalls.push(url);
      if (apiCalls.length === 1) {
        throw new Error("Requested range not satisfiable: there are only 11 rows");
      }
      return { items: [{ id: "entry-1" }], total: 11 };
    },
    syncUrlState: () => {
      syncUrlStateCalls.push("sync");
    },
    handleOutOfRangePageError: (error, filterState, scopeLabel) => {
      outOfRangeCalls.push([error.message, filterState.page, scopeLabel]);
      filterState.page = 2;
      return true;
    },
  });
  state.trackerFilters.page = 3;
  controller.loadTrackerChangeEventUnreadCount = async () => {};
  controller.loadTrackerChangeEvents = async () => {};
  controller.prefetchVisibleProjectRelatedNotices = () => {};
  controller.warmVisibleTrackerEntryNoticeFiles = () => {};

  await controller.loadTrackerEntries();

  assert.deepEqual(apiCalls, [
    "/api/tracker-entry-summaries?page=3&page_size=10&source_tracker_run_id=run-1",
    "/api/tracker-entry-summaries?page=2&page_size=10&source_tracker_run_id=run-1",
  ]);
  assert.deepEqual(syncUrlStateCalls, ["sync", "sync"]);
  assert.equal(outOfRangeCalls.length, 1);
  assert.deepEqual(outOfRangeCalls[0], [
    "Requested range not satisfiable: there are only 11 rows",
    3,
    "트래커",
  ]);
  assert.equal(state.trackerFilters.page, 2);
  assert.equal(state.trackerEntriesTotal, 11);
  assert.deepEqual(JSON.parse(JSON.stringify(state.trackerEntries)), [{ id: "entry-1" }]);
});

test("tracker controller sends notice year and region filters together", async () => {
  const apiCalls = [];
  const { controller, state, dom } = createController({
    api: async (url) => {
      apiCalls.push(url);
      return { items: [], total: 0 };
    },
    TRACKER_REGION_OPTIONS: [{ value: "서울", label: "서울" }],
  });
  state.trackerFilters.region = "서울";
  dom.trackerNoticeYear.value = "2025";
  controller.loadTrackerChangeEventUnreadCount = async () => {};
  controller.loadTrackerChangeEvents = async () => {};
  controller.prefetchVisibleProjectRelatedNotices = () => {};

  await controller.loadTrackerEntries({ forceRefresh: true });

  assert.deepEqual(apiCalls, [
    "/api/tracker-entry-summaries?page=1&page_size=10&source_tracker_run_id=run-1&region=%EC%84%9C%EC%9A%B8&notice_year=2025",
  ]);
  assert.equal(state.trackerFilters.region, "서울");
  assert.equal(state.trackerFilters.noticeYear, "2025");
});

test("tracker controller does not prewarm notice viewers after loading entries", async () => {
  const apiCalls = [];
  const { controller } = createController({
    api: async (url, options = {}) => {
      apiCalls.push([url, options.method || "GET"]);
      if (String(url).startsWith("/api/tracker-entry-summaries?")) {
        return {
          items: [
            { id: "entry-1", project_name: "One" },
            { id: "entry-2", project_name: "Two" },
          ],
          total: 2,
        };
      }
      throw new Error(`unexpected url: ${url}`);
    },
    TRACKER_NOTICE_WARM_LIMIT: 10,
  });
  controller.loadTrackerChangeEventUnreadCount = async () => {};
  controller.loadTrackerChangeEvents = async () => {};
  controller.prefetchVisibleProjectRelatedNotices = () => {};

  await controller.loadTrackerEntries({ forceRefresh: true });
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.deepEqual(apiCalls, [
    ["/api/tracker-entry-summaries?page=1&page_size=10&source_tracker_run_id=run-1", "GET"],
  ]);
});

test("tracker controller keeps selected entry detail state when loading from cache", async () => {
  const cachedEntry = {
    id: "entry-2",
    project_name: "Cached name",
    entry_key: "K-2",
  };
  const { controller, state, renderSelectedEntryCalls } = createController({
    api: async () => {
      throw new Error("cache hit should not call api");
    },
  });
  state.trackerEntries = [{ id: "entry-2", project_name: "Old name", entry_key: "K-2" }];
  state.selectedEntryId = "entry-2";
  state.selectedEntry = null;
  state.selectedEntryLoadingId = "entry-2";
  state.selectedEntryError = "previous error";
  state.trackerEntryDetailCache = { "entry-2": cachedEntry };

  const entry = await controller.loadSelectedEntryDetail({ entryId: "entry-2" });

  assert.deepEqual(entry, cachedEntry);
  assert.deepEqual(state.selectedEntry, cachedEntry);
  assert.equal(state.selectedEntryLoadingId, null);
  assert.equal(state.selectedEntryError, "");
  assert.deepEqual(renderSelectedEntryCalls, [[cachedEntry]]);
});

test("tracker controller syncs patched entry state and follows the non-admin refresh path", async () => {
  const calls = [];
  const { controller, state } = createController({
    renderTrackerEntries: (entries, options) => {
      calls.push(["renderTrackerEntries", JSON.parse(JSON.stringify(entries)), options]);
    },
  });
  controller.loadTrackerEntries = async (options) => {
    calls.push(["loadTrackerEntries", options]);
  };
  controller.loadTrackerChangeEvents = async (options) => {
    calls.push(["loadTrackerChangeEvents", options]);
  };
  controller.loadSelectedEntryAudit = async () => {
    calls.push(["loadSelectedEntryAudit"]);
  };
  controller.loadSelectedEntryChangeEvents = async (options) => {
    calls.push(["loadSelectedEntryChangeEvents", options]);
  };
  controller.loadTrackerMissingReport = async () => {
    calls.push(["loadTrackerMissingReport"]);
  };
  state.uiMode = "user";
  state.selectedEntryId = "entry-3";
  state.selectedEntry = {
    id: "entry-3",
    project_name: "Before patch",
    entry_key: "K-3",
  };
  state.trackerEntries = [
    { id: "entry-3", project_name: "Before patch", entry_key: "K-3" },
  ];

  await controller.syncTrackerEntryAfterPatch({
    id: "entry-3",
    project_name: "After patch",
    entry_key: "K-3",
  });

  assert.deepEqual(JSON.parse(JSON.stringify(state.trackerEntries)), [
    { id: "entry-3", project_name: "After patch", entry_key: "K-3" },
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(state.selectedEntry)), {
    id: "entry-3",
    project_name: "After patch",
    entry_key: "K-3",
  });
  assert.deepEqual(JSON.parse(JSON.stringify(calls)), [
    ["renderTrackerEntries", [
      { id: "entry-3", project_name: "After patch", entry_key: "K-3" },
    ], { refreshSelectedEntry: false }],
    ["loadTrackerEntries", { silent: true }],
    ["loadTrackerChangeEvents", { silent: true }],
    ["loadSelectedEntryAudit"],
    ["loadSelectedEntryChangeEvents", { entryId: "entry-3", silent: true }],
  ]);
});
