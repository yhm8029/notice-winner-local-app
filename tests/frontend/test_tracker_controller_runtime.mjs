import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/tracker-controller.js");

function readRuntimeSource() {
  return fs.readFileSync(runtimePath, "utf8");
}

function createClassList(initial = []) {
  const classes = new Set(initial);
  return {
    add(...tokens) {
      for (const token of tokens) {
        classes.add(token);
      }
    },
    remove(...tokens) {
      for (const token of tokens) {
        classes.delete(token);
      }
    },
    toggle(token, force) {
      const shouldAdd = force === undefined ? !classes.has(token) : Boolean(force);
      if (shouldAdd) {
        classes.add(token);
      } else {
        classes.delete(token);
      }
      return shouldAdd;
    },
    contains(token) {
      return classes.has(token);
    },
    toString() {
      return [...classes].join(" ");
    },
  };
}

function createElement(overrides = {}) {
  return {
    value: "",
    checked: false,
    innerHTML: "",
    textContent: "",
    files: [],
    classList: createClassList(),
    addEventListener() {},
    removeEventListener() {},
    focus() {},
    select() {},
    click() {},
    ...overrides,
  };
}

function createTrackerControllerHarness(apiImpl = async () => ({})) {
  const source = readRuntimeSource();
  const window = {};
  const context = vm.createContext({
    console,
    window,
    URLSearchParams,
    AbortController,
  });
  vm.runInContext(source, context, { filename: runtimePath });

  const calls = {
    api: [],
    flash: [],
    busy: [],
    renderEntries: [],
    pagination: 0,
    salesSummary: 0,
    renderChangePanels: 0,
    renderBackfillPanels: 0,
    renderMissingReport: [],
    renderSelectedEntryEvents: 0,
    persistCache: 0,
    clearCache: 0,
  };

  const state = {
    uiMode: "admin",
    trackerFilters: {
      q: "",
      region: "",
      editedOnly: false,
      page: 1,
      pageSize: 20,
    },
    trackerTemplateStatus: null,
    trackerEntries: [],
    trackerEntriesTotal: 0,
    trackerEntriesError: "",
    trackerEntriesRequest: null,
    trackerEntriesRequestKey: "",
    trackerChangeEventsAvailability: "available",
    trackerChangeEventsUnread: 0,
    trackerChangeEvents: [],
    trackerChangeEventsLoading: false,
    trackerChangeEventsLoadedAt: 0,
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    trackerBoardEdit: {
      entryId: null,
      fieldName: "",
      draftValue: "",
      saving: false,
      errorMessage: "",
    },
    trackerEntryDetailCache: {},
    selectedEntryDetailRequests: {},
    selectedEntryId: null,
    selectedEntry: null,
    selectedEntryLoadingId: null,
    selectedEntryError: "",
    selectedEntryChangeEvents: [],
    selectedEntryChangeEventsLoading: false,
    homeBootstrapTrackerSnapshotActive: false,
    salesClaimsByProjectId: {},
    salesClaimDrafts: {},
    projectRelatedPayloads: {},
    projectRelatedNotices: {},
    projectRelatedInFlight: {},
    projectRelatedErrors: {},
    projectOpenId: null,
    projectRelatedLoadingId: null,
    backfillConflicts: [],
    backfillConflictsLoading: false,
    trackerMissingReport: null,
  };

  const dom = {
    trackerRegionButtons: createElement(),
    trackerQuery: createElement({ value: "" }),
    trackerEditedOnly: createElement({ checked: false }),
    trackerPageSize: createElement({ value: "20" }),
    trackerTemplateStatus: createElement(),
    trackerTemplateUploadButton: createElement(),
    trackerTemplateResetButton: createElement(),
    trackerContext: createElement(),
    trackerChangeBellBadge: createElement(),
    trackerChangeBellShell: createElement(),
    panelMissingReport: createElement(),
    missingReportSummary: createElement(),
    missingReportList: createElement(),
    auditLogList: createElement(),
  };

  const FormData = class FakeFormData {
    constructor() {
      this.entries = [];
    }

    append(name, value) {
      this.entries.push([name, value]);
    }
  };

  const api = async (path, options = {}) => {
    calls.api.push([path, options]);
    return apiImpl(path, options);
  };

  const controller = window.TRACKER_CONTROLLER.createTrackerController({
    state,
    dom,
    window,
    document: {},
    api,
    flash(message, level) {
      calls.flash.push([message, level]);
    },
    setBusy(element, busy, label) {
      const target = element === dom.trackerTemplateUploadButton
        ? "upload"
        : element === dom.trackerTemplateResetButton
          ? "reset"
          : "other";
      calls.busy.push([target, busy, label]);
    },
    FormData,
    escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    },
    formatDate(value) {
      return `formatted:${value}`;
    },
    syncUrlState() {},
    readRunFiltersFromControls() {},
    renderRuns() {},
    renderRunsPagination() {
      calls.pagination += 1;
    },
    renderRunDetail() {},
    renderRunEventStatus() {},
    renderTrackerEntries(entries, options) {
      calls.renderEntries.push([entries, options]);
    },
    renderEntriesPagination() {
      calls.pagination += 1;
    },
    renderSalesSummaryPanel() {
      calls.salesSummary += 1;
    },
    renderTrackerChangeEventsPanel() {
      calls.renderChangePanels += 1;
    },
    renderTrackerContactResolutionSummary() {},
    renderBackfillConflictsPanel() {
      calls.renderBackfillPanels += 1;
    },
    renderTrackerCleanupPreview() {},
    renderProjectRelatedHosts() {},
    touchSyncMeta() {},
    handleOutOfRangePageError() {
      return false;
    },
    canLoadProtectedConsoleData() {
      return true;
    },
    TRACKER_REGION_OPTIONS: [
      { value: "", label: "전체" },
      { value: "서울", label: "서울" },
      { value: "부산", label: "부산" },
      { value: "대구", label: "대구" },
    ],
    useGlobalTrackerEntriesScope() {
      return true;
    },
    shouldUseHomeBootstrapTrackerSnapshot() {
      return false;
    },
    isProjectTrackerRun() {
      return false;
    },
    resolveActiveTrackerRunId() {
      return "run-1";
    },
    schedulePolling() {},
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    loadBackfillConflicts: async () => {},
    loadVisibleSalesClaims: async () => {},
    requireTrackerDiagnosticsRuntime() {
      return {
        filterBackfillConflictsBySourceRun(items) {
          return items;
        },
      };
    },
    clearProjectRelatedRefresh() {},
    maybeScheduleProjectRelatedRefresh() {},
    canReuseProjectRelatedPayload() {
      return false;
    },
    cacheProjectRelatedPayload(_projectId, payload) {
      return payload;
    },
    isProjectRelatedVisible() {
      return false;
    },
    resolveTrackerEntryProjectId() {
      return null;
    },
    ensureTrackerEntryProjectId: async () => null,
    TRACKER_ENTRY_RUNTIME: null,
    TRACKER_DETAIL_PREFETCH_LIMIT: 3,
    warmTrackerEntriesDownload: async () => {},
    closeDrawer() {},
    renderTrackerBoard() {},
    resetTrackerBoardEdit() {},
    loadAdminConsoleData: async () => {},
    buildSelectedEntryAuditMarkup() {
      return '<div data-test="audit-log">audit</div>';
    },
    loadSelectedEntryDetail: async () => {},
    renderTrackerMissingReport(errorMessage = "") {
      calls.renderMissingReport.push(errorMessage);
    },
    renderSelectedEntryChangeEvents() {
      calls.renderSelectedEntryEvents += 1;
    },
    renderSelectedEntry() {},
    renderSelectedEntryLoading() {},
    resolveTrackerPatchActorLabel() {
      return "";
    },
    persistTrackerChangeEventsCache() {
      calls.persistCache += 1;
    },
    clearTrackerChangeEventsCache() {
      calls.clearCache += 1;
    },
    runTypeLabel(value) {
      return String(value ?? "");
    },
  });

  return {
    controller,
    state,
    dom,
    calls,
    FormData,
  };
}

test("tracker controller parses region filters and syncs the filter controls", () => {
  const { controller, state, dom } = createTrackerControllerHarness();

  state.trackerFilters.region = "부산,unknown,서울";
  dom.trackerQuery.value = "  school  ";
  dom.trackerEditedOnly.checked = true;
  dom.trackerPageSize.value = "50";

  assert.deepEqual(controller.parseTrackerRegionFilter("부산,unknown,서울"), ["서울", "부산"]);
  assert.equal(controller.normalizeTrackerRegionFilter("부산,unknown,서울"), "서울,부산");

  controller.renderTrackerRegionButtons();
  assert.match(dom.trackerRegionButtons.innerHTML, /data-tracker-region="서울"[\s\S]*aria-pressed="true"/);
  assert.match(dom.trackerRegionButtons.innerHTML, /data-tracker-region="부산"[\s\S]*aria-pressed="true"/);
  assert.match(dom.trackerRegionButtons.innerHTML, /data-tracker-region=""[\s\S]*aria-pressed="false"/);

  controller.readTrackerFiltersFromControls();
  assert.equal(state.trackerFilters.q, "school");
  assert.equal(state.trackerFilters.region, "서울,부산");
  assert.equal(state.trackerFilters.editedOnly, true);
  assert.equal(state.trackerFilters.pageSize, 50);
});

test("tracker controller loads and mutates tracker template status through the API", async () => {
  const responses = {
    get: {
      source_label: "server",
      original_file_name: "tracker.xlsx",
      updated_at: "2024-01-02",
    },
    post: {
      source_label: "upload",
      original_file_name: "override.xlsx",
      updated_at: "2024-02-03",
    },
    delete: {
      source_label: "reset",
      file_name: "base.xlsx",
      updated_at: "2024-03-04",
    },
  };
  const { controller, state, dom, calls, FormData } = createTrackerControllerHarness(async (_path, options = {}) => {
    if (!options.method || options.method === "GET") {
      return responses.get;
    }
    if (options.method === "POST") {
      return responses.post;
    }
    if (options.method === "DELETE") {
      return responses.delete;
    }
    throw new Error(`unexpected tracker template method: ${options.method}`);
  });

  await controller.loadTrackerTemplateStatus({ silent: true });
  assert.deepEqual(state.trackerTemplateStatus, responses.get);
  assert.equal(dom.trackerTemplateStatus.classList.contains("hidden"), false);
  assert.match(dom.trackerTemplateStatus.textContent, /server/);
  assert.match(dom.trackerTemplateStatus.textContent, /tracker\.xlsx/);
  assert.match(dom.trackerTemplateStatus.textContent, /formatted:2024-01-02/);

  const file = { name: "tracker.xlsx" };
  await controller.uploadTrackerTemplate(file);
  assert.deepEqual(state.trackerTemplateStatus, responses.post);
  assert.equal(calls.api[1][1].method, "POST");
  assert.ok(calls.api[1][1].body instanceof FormData);
  assert.deepEqual(calls.api[1][1].body.entries, [["file", file]]);
  assert.deepEqual(calls.busy.slice(0, 2).map(([target, busy]) => [target, busy]), [
    ["upload", true],
    ["upload", false],
  ]);
  assert.ok(calls.flash.some(([message]) => String(message).includes("override.xlsx")));

  await controller.resetTrackerTemplateOverride();
  assert.deepEqual(state.trackerTemplateStatus, responses.delete);
  assert.equal(calls.api[2][1].method, "DELETE");
  assert.deepEqual(calls.busy.slice(2).map(([target, busy]) => [target, busy]), [
    ["reset", true],
    ["reset", false],
  ]);
  assert.match(dom.trackerTemplateStatus.textContent, /reset/);
});

test("tracker controller loads tracker entries with normalized filters and renders results", async () => {
  const { controller, state, dom, calls } = createTrackerControllerHarness(async (path) => {
    assert.match(path, /^\/api\/tracker-entry-summaries\?/);
    const query = new URLSearchParams(path.split("?")[1]);
    assert.equal(query.get("page"), "1");
    assert.equal(query.get("page_size"), "25");
    assert.equal(query.get("q"), "school");
    assert.equal(query.get("region"), "서울,부산");
    assert.equal(query.get("edited_only"), "true");
    assert.equal(query.get("exclude_auxiliary_titles"), "true");
    assert.equal(query.get("refresh"), "true");
    assert.equal(query.has("source_tracker_run_id"), false);
    return {
      total: 2,
      items: [
        { id: "entry-1", project_id: "project-1" },
        { id: "entry-2", project_id: "project-2" },
      ],
    };
  });

  controller.loadTrackerChangeEventUnreadCount = async () => {};
  controller.loadTrackerChangeEvents = async () => {};
  controller.prefetchVisibleProjectRelatedNotices = () => {};

  state.trackerFilters.region = "부산,서울,invalid";
  dom.trackerQuery.value = "school";
  dom.trackerEditedOnly.checked = true;
  dom.trackerPageSize.value = "25";

  await controller.loadTrackerEntries({ silent: true, forceRefresh: true });

  assert.equal(state.trackerEntriesTotal, 2);
  assert.equal(state.trackerEntriesError, "");
  assert.equal(calls.renderEntries.length, 1);
  assert.deepEqual(
    calls.renderEntries[0][0].map((entry) => ({
      id: entry.id,
      project_id: entry.project_id,
    })),
    [
      { id: "entry-1", project_id: "project-1" },
      { id: "entry-2", project_id: "project-2" },
    ],
  );
  assert.equal(calls.renderEntries[0][1].refreshSelectedEntry, true);
  assert.equal(calls.pagination, 1);
});

test("tracker controller fetches and prefetches selected-entry detail through the shared cache", async () => {
  const { controller, state, calls } = createTrackerControllerHarness(async (requestPath) => {
    if (requestPath === "/api/tracker-entries/entry-1") {
      return { id: "entry-1", project_id: "project-1", project_name: "Alpha" };
    }
    if (requestPath === "/api/tracker-entries/entry-2") {
      return { id: "entry-2", project_id: "project-2", project_name: "Beta" };
    }
    throw new Error(`unexpected selected-entry detail request: ${requestPath}`);
  });

  state.trackerEntries = [
    { id: "entry-1", project_id: "project-1" },
    { id: "entry-2", project_id: "project-2" },
  ];

  const detail = await controller.fetchTrackerEntryDetail("entry-1", { silent: true });
  assert.equal(detail.project_name, "Alpha");
  assert.equal(state.trackerEntryDetailCache["entry-1"].project_name, "Alpha");

  controller.prefetchTrackerEntryDetails([
    { id: "entry-1" },
    { id: "entry-2" },
    { id: "entry-2" },
  ]);
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.equal(calls.api.filter(([requestPath]) => requestPath === "/api/tracker-entries/entry-1").length, 1);
  assert.equal(calls.api.filter(([requestPath]) => requestPath === "/api/tracker-entries/entry-2").length, 1);
  assert.equal(state.trackerEntryDetailCache["entry-2"].project_name, "Beta");
});

test("tracker controller loads tracker change events and keeps cache state in sync", async () => {
  const { controller, state, dom, calls } = createTrackerControllerHarness(async (requestPath) => {
    if (requestPath.startsWith("/api/tracker-change-events/unread-count")) {
      return { unread_count: 5 };
    }
    if (requestPath.startsWith("/api/tracker-change-events?")) {
      const query = new URLSearchParams(requestPath.split("?")[1]);
      assert.equal(query.get("limit"), "20");
      assert.equal(query.get("include_silent"), "true");
      return {
        items: [
          { id: "event-1", tracker_entry_id: "entry-1", is_read: false },
        ],
      };
    }
    throw new Error(`unexpected tracker change request: ${requestPath}`);
  });

  await controller.loadTrackerChangeEvents({ silent: true, includeSilent: true });

  assert.equal(state.trackerChangeEventsAvailability, "available");
  assert.equal(state.trackerChangeEvents.length, 1);
  assert.equal(state.trackerChangeEventsUnread, 5);
  assert.ok(state.trackerChangeEventsLoadedAt > 0);
  assert.equal(dom.trackerChangeBellBadge.textContent, "5");
  assert.equal(dom.trackerChangeBellBadge.classList.contains("hidden"), false);
  assert.ok(calls.renderChangePanels >= 2);
  assert.equal(calls.persistCache, 2);
  assert.equal(calls.clearCache, 0);
});

test("tracker controller loads diagnostics data and selected-entry change events", async () => {
  const { controller, state, calls } = createTrackerControllerHarness(async (requestPath, options = {}) => {
    if (requestPath.startsWith("/api/tracker-entries/missing-report")) {
      return {
        summary: { total_entries: 1, missing_entries: 1 },
        items: [],
      };
    }
    if (requestPath.startsWith("/api/backfill-conflicts?")) {
      return {
        items: [{ id: "conflict-1", tracker_entry_id: "entry-9" }],
      };
    }
    if (requestPath.startsWith("/api/tracker-change-events?")) {
      const query = new URLSearchParams(requestPath.split("?")[1]);
      assert.equal(query.get("tracker_entry_id"), "entry-9");
      assert.equal(query.get("include_silent"), "true");
      return {
        items: [{ id: "event-9", tracker_entry_id: "entry-9", is_read: false }],
      };
    }
    if (requestPath === "/api/tracker-change-events/mark-read") {
      assert.equal(options.method, "POST");
      return { updated_count: 1 };
    }
    if (requestPath === "/api/tracker-change-events/unread-count") {
      return { unread_count: 0 };
    }
    throw new Error(`unexpected tracker diagnostics request: ${requestPath}`);
  });

  state.selectedEntryId = "entry-9";

  await controller.loadTrackerMissingReport({ silent: true });
  assert.equal(state.trackerMissingReport.summary.total_entries, 1);
  assert.equal(calls.renderMissingReport.length, 1);
  assert.equal(calls.renderMissingReport[0], "");

  await controller.loadBackfillConflicts({ silent: true, includeResolved: true });
  assert.equal(state.backfillConflicts.length, 1);
  assert.ok(calls.renderBackfillPanels >= 2);

  await controller.loadSelectedEntryChangeEvents({ entryId: "entry-9", silent: true });
  assert.equal(state.selectedEntryChangeEvents.length, 1);
  assert.equal(state.selectedEntryChangeEvents[0].is_read, true);
  assert.ok(calls.renderSelectedEntryEvents >= 2);
  assert.equal(calls.api.some(([requestPath]) => requestPath === "/api/tracker-change-events/mark-read"), true);
});

test("tracker controller loads selected-entry audit logs and refreshes audit during patched-entry sync", async () => {
  const { controller, state, dom, calls } = createTrackerControllerHarness(async (requestPath) => {
    if (requestPath === "/api/tracker-entries/entry-9/audit-logs?limit=20") {
      return {
        items: [{ id: "audit-1" }],
      };
    }
    if (requestPath.startsWith("/api/tracker-entry-summaries?")) {
      return {
        total: 1,
        items: [{ id: "entry-9", project_id: "project-9" }],
      };
    }
    if (requestPath.startsWith("/api/tracker-change-events?")) {
      return {
        items: [{ id: "event-9", tracker_entry_id: "entry-9", is_read: false }],
      };
    }
    if (requestPath === "/api/tracker-change-events/mark-read") {
      return { updated_count: 1 };
    }
    if (requestPath === "/api/tracker-change-events/unread-count") {
      return { unread_count: 0 };
    }
    throw new Error(`unexpected audit/sync request: ${requestPath}`);
  });

  state.uiMode = "user";
  state.selectedEntryId = "entry-9";
  state.selectedEntry = { id: "entry-9" };
  state.trackerEntries = [{ id: "entry-9", project_id: "project-9" }];

  await controller.loadSelectedEntryAudit();
  assert.match(dom.auditLogList.innerHTML, /data-test="audit-log"/);

  let auditRefreshes = 0;
  const originalLoadSelectedEntryAudit = controller.loadSelectedEntryAudit;
  controller.loadSelectedEntryAudit = async (...args) => {
    auditRefreshes += 1;
    return originalLoadSelectedEntryAudit(...args);
  };

  await controller.syncTrackerEntryAfterPatch({ id: "entry-9", project_id: "project-9" });

  assert.equal(auditRefreshes, 1);
  assert.equal(calls.renderEntries.length >= 1, true);
  assert.equal(state.selectedEntryChangeEvents.length, 1);
});

test("tracker controller preserves app-side abort semantics for project-related notice loads", async () => {
  const { controller, state, calls } = createTrackerControllerHarness(async (requestPath) => {
    if (requestPath === "/api/projects/project-9/related-notices") {
      const error = new Error("aborted");
      error.name = "AbortError";
      throw error;
    }
    throw new Error(`unexpected project-related request: ${requestPath}`);
  });

  state.projectRelatedPayloads = {};
  state.projectRelatedNotices = {};
  state.projectRelatedErrors = {};
  state.projectRelatedInFlight = {};

  const result = await controller.loadProjectRelatedNotices("project-9", { silent: true, force: true });

  assert.equal(result, undefined);
  assert.equal(Object.prototype.hasOwnProperty.call(state.projectRelatedNotices, "project-9"), false);
  assert.equal(Object.prototype.hasOwnProperty.call(state.projectRelatedErrors, "project-9"), false);
  assert.equal(calls.flash.length, 0);
});

test("tracker controller ignores aborted tracker-entry requests during rapid requery", async () => {
  const { controller, state, dom, calls } = createTrackerControllerHarness(async (requestPath, options = {}) => {
    if (!requestPath.startsWith("/api/tracker-entry-summaries?")) {
      throw new Error(`unexpected tracker entry request: ${requestPath}`);
    }
    const query = new URLSearchParams(requestPath.split("?")[1]);
    if (query.get("q") === "first") {
      return await new Promise((resolve, reject) => {
        const abortError = new Error("aborted");
        abortError.name = "AbortError";
        options.signal?.addEventListener("abort", () => {
          setTimeout(() => reject(abortError), 0);
        }, { once: true });
      });
    }
    return {
      total: 1,
      items: [{ id: "entry-2", project_id: "project-2" }],
    };
  });

  controller.loadTrackerChangeEventUnreadCount = async () => {};
  controller.loadTrackerChangeEvents = async () => {};
  controller.prefetchVisibleProjectRelatedNotices = () => {};

  dom.trackerQuery.value = "first";
  const firstLoad = controller.loadTrackerEntries({ silent: false, forceRefresh: true });

  dom.trackerQuery.value = "second";
  const secondLoad = controller.loadTrackerEntries({ silent: false, forceRefresh: true });

  await Promise.allSettled([firstLoad, secondLoad]);

  assert.equal(state.trackerEntriesError, "");
  assert.equal(calls.flash.length, 0);
  assert.equal(state.trackerEntries[0]?.id, "entry-2");
  assert.equal(calls.renderEntries.length >= 1, true);
});
