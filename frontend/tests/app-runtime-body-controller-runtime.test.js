const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime() {
  const runtimePath = path.join(__dirname, "..", "app-runtime-body-controller-runtime.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console, globalThis: window });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAppRuntimeBodyControllerRuntime;
}

test("controller runtime caches app event bindings and controller deps factories", () => {
  const runtime = loadRuntime();
  const wiringCalls = [];
  const controllerCalls = [];
  const supportCalls = [];
  const state = {};
  const dom = {};
  const windowObject = {
    SPMSAppControllerWiringRuntime: {
      createAppEventBindingsDeps(payload) {
        wiringCalls.push(["createAppEventBindingsDeps", payload]);
        return { deps: "bindings" };
      },
      createTrackerControllerDeps(payload) {
        wiringCalls.push(["createTrackerControllerDeps", payload]);
        return { wired: payload };
      },
    },
    APP_EVENT_BINDINGS: {
      createAppEventBindings(deps) {
        controllerCalls.push(["createAppEventBindings", deps]);
        return { kind: "bindings", deps };
      },
    },
  };
  const appSupport = {
    createTrackerControllerDepsHelpers(payload) {
      supportCalls.push(["createTrackerControllerDepsHelpers", payload]);
      return {
        buildTrackerControllerDeps() {
          supportCalls.push(["buildTrackerControllerDeps"]);
          return { deps: "tracker-controller" };
        },
        buildTrackerControllerBaseDeps() {
          supportCalls.push(["buildTrackerControllerBaseDeps"]);
          return { deps: "tracker-base" };
        },
      };
    },
  };
  const accessors = runtime.createAppRuntimeBodyControllerAccessors({
    state,
    dom,
    windowObject,
    appSupport,
    deps: {
      AUTH_MODE_SIGN_IN: "sign-in",
      AUTH_MODE_SIGN_UP: "sign-up",
      TRACKER_REGION_OPTIONS: ["all"],
      handleAuthSubmit() {},
      setAuthMode() {},
      handleAuthFindId() {},
      handleAuthPasswordReset() {},
      scheduleInvitationPreviewLookup() {},
      renderAuthUi() {},
      handleAuthSignOut() {},
      openProfileDialog() {},
      handleProfileSubmit() {},
      handleInvitationSubmit() {},
      loadOrganizationAdminData() {},
      closeProfileDialog() {},
      setTrackerChangeBellPopoverOpen() {},
      downloadSalesWorkbook() {},
      closeSalesCloseDialog() {},
      formatContractAmountInput() {},
      confirmSalesCloseDialog() {},
      refreshAuthSessionState() {},
      loadDashboardSummary() {},
      handleRunCreate() {},
      handleRunFormReset() {},
      refreshSelectedRun() {},
      loadRuns() {},
      loadSelectedRunLogs() {},
      runSelectedReport() {},
      refreshReportPanels() {},
      loadSelectedRunArtifacts() {},
      cancelSelectedRun() {},
      createTrackerExportForSelectedRun() {},
      toggleUiMode() {},
      renderSyncMeta() {},
      syncUrlState() {},
      loadReportJobs() {},
      loadPhaseReport() {},
      readRunFiltersFromControls() {},
      readTrackerFiltersFromControls() {},
      syncFilterControlsFromState() {},
      changeRunsPage() {},
      loadTrackerEntries() {},
      trackerChangeEventsCacheIsFresh() {},
      renderTrackerChangeBellPopover() {},
      loadTrackerChangeEvents() {},
      focusTrackerChangePanel() {},
      uploadTrackerTemplate() {},
      resetTrackerTemplateOverride() {},
      changeEntriesPageTo() {},
      changeEntriesPage() {},
      getEntriesTotalPages() {},
      normalizeTrackerRegionFilter() {},
      parseTrackerRegionFilter() {},
      saveEntryPatch() {},
      clearEntryPatch() {},
      loadSelectedEntryAudit() {},
      loadTrackerMissingReport() {},
      refreshSalesAdminPanels() {},
      getMissingReportDownloadLimit() {},
      syncPatchValueFromSelectedEntry() {},
      closeDrawer() {},
      loadRunPresets() {},
      applySelectedPreset() {},
      saveCurrentFormAsPreset() {},
      renderRunPresetPanel() {},
      loadProjects() {},
      changeProjectsPage() {},
      triggerTrackerEntriesXlsxDownload() {},
    },
    controllerDeps: {
      TRACKER_BOARD_BLANK_PRIORITY_FIELDS: ["name"],
      EDITABLE_FIELDS: ["project_name"],
      renderTrackerEntries() {},
      renderRuns() {},
      renderRunsPagination() {},
      renderRunDetail() {},
      renderRunEventStatus() {},
      renderLogsList() {},
      getRunPanelsController: () => ({ upsertRunListItem() {} }),
      renderEntriesPagination() {},
      renderSalesSummaryPanel() {},
      renderTrackerChangeEventsPanel() {},
      renderTrackerContactResolutionSummary() {},
      renderBackfillConflictsPanel() {},
      renderTrackerCleanupPreview() {},
      renderProjectRelatedHosts() {},
      touchSyncMeta() {},
      persistTrackerChangeEventsCache() {},
      clearTrackerChangeEventsCache() {},
      handleOutOfRangePageError() {},
      canLoadProtectedConsoleData() {},
      useGlobalTrackerEntriesScope() {},
      shouldUseHomeBootstrapTrackerSnapshot() {},
      isProjectTrackerRun() {},
      schedulePolling() {},
      loadWinnerRunPanels() {},
      loadTrackerExportPanels() {},
      loadBackfillConflicts() {},
      loadVisibleSalesClaims() {},
      TRACKER_DIAGNOSTICS_RUNTIME: { kind: "tracker-diagnostics" },
      formatContactResolutionStatusLabel() {},
      formatContactResolutionReasonLabel() {},
      formatBackfillConflictResolutionLabel() {},
      getTrackerDiagnosticsScope() {},
      buildTrackerChangeEventsMarkup() {},
      buildTrackerChangeBellPopoverMarkup() {},
      buildBackfillConflictsMarkup() {},
      buildBackfillConflictsView() {},
      focusTrackerChangeEntry() {},
      closeTrackerChangeModal() {},
      patchTrackerEntry() {},
      syncTrackerEntryAfterPatch() {},
      clearProjectRelatedRefresh() {},
      maybeScheduleProjectRelatedRefresh() {},
      canReuseProjectRelatedPayload() {},
      cacheProjectRelatedPayload() {},
      isProjectRelatedVisible() {},
      resolveTrackerEntryProjectId() {},
      ensureTrackerEntryProjectId() {},
      TRACKER_ENTRY_RUNTIME: { kind: "tracker-entry" },
      TRACKER_DETAIL_PREFETCH_LIMIT: 5,
      warmTrackerEntriesDownload() {},
      loadAdminConsoleData() {},
      buildSelectedEntryAuditMarkup() {},
      loadSelectedEntryDetail() {},
      renderTrackerMissingReport() {},
      renderSelectedEntryChangeEvents() {},
      renderSelectedEntry() {},
      renderSelectedEntryLoading() {},
      resolveTrackerPatchActorLabel() {},
      runTypeLabel() {},
    },
    coreDeps: {
      api() {},
      flash() {},
      setBusy() {},
      FormData: function FormData() {},
      escapeHtml() {},
      formatDate() {},
    },
  });

  const appEventBindingsA = accessors.getAppEventBindings();
  const appEventBindingsB = accessors.getAppEventBindings();
  const trackerControllerA = accessors.getTrackerController({
    createController: (deps) => {
      controllerCalls.push(["createTrackerController", deps]);
      return { kind: "tracker", deps };
    },
    missingFactoryError: "tracker missing",
  });
  const trackerControllerB = accessors.getTrackerController({
    createController: () => {
      throw new Error("should not re-create");
    },
    missingFactoryError: "tracker missing",
  });

  assert.equal(appEventBindingsA, appEventBindingsB);
  assert.equal(trackerControllerA, trackerControllerB);
  assert.deepEqual(
    wiringCalls.map(([name]) => name),
    ["createAppEventBindingsDeps", "createTrackerControllerDeps"],
  );
  assert.deepEqual(
    controllerCalls.map(([name]) => name),
    ["createAppEventBindings", "createTrackerController"],
  );
  assert.deepEqual(
    supportCalls.map(([name]) => name),
    ["createTrackerControllerDepsHelpers", "buildTrackerControllerDeps"],
  );
});

test("controller runtime method delegates cache target lookup per call and support strict mode", () => {
  const runtime = loadRuntime();
  let callCount = 0;
  const delegates = runtime.createMethodDelegates({
    getter() {
      callCount += 1;
      return {
        ping(value) {
          return `pong:${value}`;
        },
      };
    },
    methods: ["ping"],
  });

  assert.equal(delegates.ping("a"), "pong:a");
  assert.equal(delegates.ping("b"), "pong:b");
  assert.equal(callCount, 2);

  const strictDelegates = runtime.createMethodDelegates({
    getter() {
      return {};
    },
    methods: ["missing"],
    strict: true,
  });
  assert.throws(() => strictDelegates.missing(), /Missing delegated method: missing/);
});

test("controller runtime tracker board helpers delegate through support bridges and runtime fallbacks", () => {
  const runtime = loadRuntime();
  const bridgeCalls = [];
  const state = { trackerBoardSort: { fieldName: "priority" }, trackerBoardEdit: { entryId: "entry-1" } };
  const appSupport = {
    renderTrackerBoardHeaderCellBridge(payload) {
      bridgeCalls.push(["renderTrackerBoardHeaderCellBridge", payload]);
      return "header-cell";
    },
    isTrackerBoardBlankValueBridge(payload) {
      bridgeCalls.push(["isTrackerBoardBlankValueBridge", payload]);
      return payload.value == null;
    },
    sortTrackerBoardEntriesBridge(payload) {
      bridgeCalls.push(["sortTrackerBoardEntriesBridge", payload]);
      return ["sorted"];
    },
    buildTrackerBoardCellMarkupFallbackBridge(payload) {
      bridgeCalls.push(["buildTrackerBoardCellMarkupFallbackBridge", payload]);
      return "cell-fallback";
    },
    buildTrackerBoardEditingCellMarkupFallbackBridge(payload) {
      bridgeCalls.push(["buildTrackerBoardEditingCellMarkupFallbackBridge", payload]);
      return "editing-fallback";
    },
    renderTrackerBoardCellBridge(payload) {
      bridgeCalls.push(["renderTrackerBoardCellBridge", payload]);
      return "rendered-cell";
    },
    renderTrackerBoardEditingCellBridge(payload) {
      bridgeCalls.push(["renderTrackerBoardEditingCellBridge", payload]);
      return "rendered-editing-cell";
    },
  };
  const fallbackHelpers = {
    buildTrackerEntriesFallbackDeps(refreshSelectedEntry) {
      return { refreshSelectedEntry };
    },
    buildTrackerBoardFallbackDeps() {
      return { board: true };
    },
  };
  const fallbackRuntime = {
    renderTrackerEntriesFallback(entries, deps) {
      bridgeCalls.push(["renderTrackerEntriesFallback", { entries, deps }]);
      return "entries-fallback";
    },
    renderTrackerBoardFallback(entries, deps) {
      bridgeCalls.push(["renderTrackerBoardFallback", { entries, deps }]);
      return "board-fallback";
    },
    buildTrackerEntryCardMarkupFallback(payload) {
      bridgeCalls.push(["buildTrackerEntryCardMarkupFallback", payload]);
      return "card-fallback";
    },
    sortTrackerBoardEntriesFallback(entries) {
      bridgeCalls.push(["sortTrackerBoardEntriesFallback", entries]);
      return ["fallback-sorted"];
    },
    buildTrackerBoardMarkupFallback(entries) {
      bridgeCalls.push(["buildTrackerBoardMarkupFallback", entries]);
      return "board-markup";
    },
  };
  const trackerHelpers = runtime.createTrackerRenderFallbackAccessors({
    state,
    appSupport,
    runtimeDeps: {
      TRACKER_BOARD_RUNTIME: { kind: "board-runtime" },
      TRACKER_BOARD_BLANK_PRIORITY_FIELDS: ["priority"],
      TRACKER_BOARD_TEXTAREA_FIELDS: ["notes"],
      escapeHtml(value) {
        return String(value);
      },
      getTrackerRenderFallbackHelpers: () => fallbackHelpers,
      getTrackerRenderFallbackRuntime: () => fallbackRuntime,
      getTrackerRenderController: () => null,
      getTrackerEntryActionsController: () => ({
        toggleTrackerBoardBlankPriority(fieldName) {
          return `toggle:${fieldName}`;
        },
      }),
      buildSortedTrackerBoardEntries() {
        return ["sorted-by-builder"];
      },
    },
  });

  assert.equal(trackerHelpers.renderTrackerEntries(["entry-1"]), "entries-fallback");
  assert.equal(trackerHelpers.renderTrackerBoard(["entry-1"]), "board-fallback");
  assert.equal(trackerHelpers.renderTrackerBoardHeaderCell({ key: "priority" }), "header-cell");
  assert.equal(trackerHelpers.isTrackerBoardBlankValue(null), true);
  assert.deepEqual(trackerHelpers.sortTrackerBoardEntries(["entry-1"]), ["sorted"]);
  assert.equal(trackerHelpers.buildTrackerBoardCellMarkupFallback({ entry: { id: "entry-1" }, column: { key: "priority" }, displayNo: 1 }), "cell-fallback");
  assert.equal(trackerHelpers.buildTrackerBoardEditingCellMarkupFallback({ entry: { id: "entry-1" }, fieldName: "notes", label: "Notes", value: "n", saving: false, errorMessage: "" }), "editing-fallback");
  assert.equal(trackerHelpers.renderTrackerBoardCell({ entry: { id: "entry-1" }, column: { key: "priority" }, displayNo: 1 }), "rendered-cell");
  assert.equal(trackerHelpers.renderTrackerBoardEditingCell({ entry: { id: "entry-1" }, fieldName: "notes", label: "Notes", value: "n", saving: false, errorMessage: "" }), "rendered-editing-cell");
  assert.equal(trackerHelpers.toggleTrackerBoardBlankPriority("priority"), "toggle:priority");
  assert.equal(trackerHelpers.buildTrackerEntryCardMarkupFallback({ id: "entry-1" }), "card-fallback");
  assert.deepEqual(trackerHelpers.sortTrackerBoardEntriesFallback(["entry-1"]), ["fallback-sorted"]);
  assert.equal(trackerHelpers.buildTrackerBoardMarkupFallback(["entry-1"]), "board-markup");
  assert.deepEqual(
    bridgeCalls.map(([name]) => name),
    [
      "renderTrackerEntriesFallback",
      "renderTrackerBoardFallback",
      "renderTrackerBoardHeaderCellBridge",
      "isTrackerBoardBlankValueBridge",
      "sortTrackerBoardEntriesBridge",
      "buildTrackerBoardCellMarkupFallbackBridge",
      "buildTrackerBoardEditingCellMarkupFallbackBridge",
      "renderTrackerBoardCellBridge",
      "renderTrackerBoardEditingCellBridge",
      "buildTrackerEntryCardMarkupFallback",
      "sortTrackerBoardEntriesFallback",
      "buildTrackerBoardMarkupFallback",
    ],
  );
});
