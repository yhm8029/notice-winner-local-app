(function initAppRuntimeBodyConsoleRuntime(global) {
  function createAppRuntimeBodyAccessors({
    state,
    dom,
    windowObject,
    BOOTSTRAP_RUNTIME,
    clampPage,
    normalizeTrackerRegionFilter,
    RELATED_NOTICE_RUNTIME,
    escapeHtml,
    APP_SUPPORT,
    CACHE_RUNTIME,
    ORG_ADMIN_BOOTSTRAP_STORAGE_KEY,
    TRACKER_CHANGE_EVENTS_STORAGE_KEY,
    TRACKER_CHANGE_EVENTS_STORAGE_MAX_ITEMS,
    TRACKER_CHANGE_EVENTS_CACHE_TTL_MS,
    canUseAdminMode,
    renderTrackerChangeEventsPanel,
    renderTrackerChangeEventUnreadCount,
    loadTrackerChangeEventUnreadCount,
    loadTrackerChangeEvents,
    resetTrackerBoardEdit,
    renderTrackerBoard,
    renderSelectedEntry,
    FRONTEND_RUNTIME_ADAPTERS,
    SALES_STATE_HELPERS,
    renderSalesClaimSection,
    renderTrackerEntryRelatedNotices,
    syncUrlState,
    toggleTrackerEntryRelated,
    openTrackerEntryNoticeViewer,
    bindRelatedNoticeViewerButtons,
    claimSalesProject,
    saveSalesClaimNote,
    transferSalesClaim,
    flash,
    openSalesCloseDialog,
    closeSalesClaim,
    releaseSalesClaim,
    loadSelectedEntryDetail,
    prefetchTrackerEntryDetails,
    buildTrackerBoardMarkupFallback,
    renderTrackerEntries,
    toggleTrackerBoardBlankPriority,
    beginTrackerBoardEdit,
    saveTrackerBoardEdit,
    TRACKER_BOARD_COLUMNS,
    TRACKER_BOARD_TEXTAREA_FIELDS,
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    renderTrackerBoardHeaderCell,
    renderTrackerBoardCell,
    renderTrackerBoardEditingCell,
    sortTrackerBoardEntriesFallback,
    api,
    renderUserOwnedSalesClaimCard,
    renderCompanySalesClaimCard,
    renderUserTrackerClaimSection,
    adminDeleteLatestSalesNote,
    formatContractAmountInput,
    isAdminRole,
    normalizeSalesClaimCardViewModel,
    loadSalesOverview,
    loadMySalesClaims,
    loadVisibleSalesClaims,
    refreshSalesAdminPanels,
    SALES_VIEW_RUNTIME,
    getProjectRelatedController,
    getReportPanelsController,
    getAdminGoogleSheetsRuntimeState,
  }) {
    let appBootstrapBridge = null;
    let projectRelatedBodyRuntime = null;
    let bootstrapCacheHelpers = null;
    let trackerChangeEventHelpers = null;
    let trackerRenderFallbackHelpers = null;
    let salesPanelDepsHelpers = null;

    function getAppBootstrapBridge() {
      if (appBootstrapBridge) return appBootstrapBridge;
      const createAppBootstrapBridge = windowObject.APP_BOOTSTRAP_BRIDGE?.createAppBootstrapBridge;
      if (typeof createAppBootstrapBridge !== "function") {
        throw new Error("APP_BOOTSTRAP_BRIDGE.createAppBootstrapBridge is required before app.js loads");
      }
      appBootstrapBridge = createAppBootstrapBridge({ bootstrapRuntime: BOOTSTRAP_RUNTIME, state, window: windowObject, clampPage, normalizeTrackerRegionFilter });
      return appBootstrapBridge;
    }
    function hydrateStateFromUrl() { return getAppBootstrapBridge().hydrateStateFromUrl(); }
    function renderSyncMeta() { dom.autoRefreshToggle.checked = state.autoRefresh; dom.lastSyncLabel.textContent = state.lastSyncLabel; }
    function touchSyncMeta(label) { state.lastSyncLabel = label; renderSyncMeta(); }
    function getProjectRelatedBodyRuntime() {
      if (projectRelatedBodyRuntime) return projectRelatedBodyRuntime;
      const createProjectRelatedBodyRuntime = windowObject.SPMSProjectRelatedAppRuntime?.createProjectRelatedBodyRuntime;
      if (typeof createProjectRelatedBodyRuntime !== "function") {
        throw new Error("SPMSProjectRelatedAppRuntime.createProjectRelatedBodyRuntime is required before app.js loads");
      }
      projectRelatedBodyRuntime = createProjectRelatedBodyRuntime({ getProjectRelatedController: () => getProjectRelatedController(), getReportPanelsController: () => getReportPanelsController(), getExistingReportPanelsController: () => null, relatedNoticeRuntime: RELATED_NOTICE_RUNTIME, escapeHtml });
      return projectRelatedBodyRuntime;
    }
    function hydrateProjectRelatedPayloadCache() { return getProjectRelatedController()?.hydrateProjectRelatedPayloadCache?.() ?? getProjectRelatedBodyRuntime()?.hydrateProjectRelatedPayloadCache?.(); }
    function persistProjectRelatedPayloadCache() { return getProjectRelatedController()?.persistProjectRelatedPayloadCache?.() ?? getProjectRelatedBodyRuntime()?.persistProjectRelatedPayloadCache?.(); }
    function getBootstrapCacheHelpers() {
      if (bootstrapCacheHelpers) return bootstrapCacheHelpers;
      bootstrapCacheHelpers = APP_SUPPORT.createBootstrapCacheHelpers({ state, cacheRuntime: CACHE_RUNTIME, buildStorageIdentity: APP_SUPPORT.buildStorageIdentity, orgAdminBootstrapStorageKey: ORG_ADMIN_BOOTSTRAP_STORAGE_KEY });
      return bootstrapCacheHelpers;
    }
    function getTrackerChangeEventHelpers() {
      if (trackerChangeEventHelpers) return trackerChangeEventHelpers;
      trackerChangeEventHelpers = APP_SUPPORT.createTrackerChangeEventHelpers({ state, windowObject, storageKey: TRACKER_CHANGE_EVENTS_STORAGE_KEY, storageMaxItems: TRACKER_CHANGE_EVENTS_STORAGE_MAX_ITEMS, cacheTtlMs: TRACKER_CHANGE_EVENTS_CACHE_TTL_MS, canUseAdminMode, renderTrackerChangeEventsPanel, renderTrackerChangeEventUnreadCount, loadTrackerChangeEventUnreadCount, loadTrackerChangeEvents });
      return trackerChangeEventHelpers;
    }
    function getTrackerRenderFallbackHelpers() {
      if (trackerRenderFallbackHelpers) return trackerRenderFallbackHelpers;
      trackerRenderFallbackHelpers = APP_SUPPORT.createTrackerRenderFallbackHelpers({ dom, state, resetTrackerBoardEdit, renderTrackerBoard, renderSelectedEntry, runtimeAdapters: FRONTEND_RUNTIME_ADAPTERS, salesStateHelpers: SALES_STATE_HELPERS, renderSalesClaimSection, renderTrackerEntryRelatedNotices, syncUrlState, toggleTrackerEntryRelated, openTrackerEntryNoticeViewer, bindRelatedNoticeViewerButtons, claimSalesProject, saveSalesClaimNote, transferSalesClaim, flash, openSalesCloseDialog, closeSalesClaim, releaseSalesClaim, loadSelectedEntryDetail, prefetchTrackerEntryDetails, buildTrackerBoardMarkupFallback, renderTrackerEntries, toggleTrackerBoardBlankPriority, beginTrackerBoardEdit, saveTrackerBoardEdit, columns: TRACKER_BOARD_COLUMNS, textareaFields: TRACKER_BOARD_TEXTAREA_FIELDS, blankPriorityFields: TRACKER_BOARD_BLANK_PRIORITY_FIELDS, renderTrackerBoardHeaderCell, renderTrackerBoardCell, renderTrackerBoardEditingCell, sortTrackerBoardEntriesFallback });
      return trackerRenderFallbackHelpers;
    }
    function getSalesPanelDepsHelpers() {
      if (salesPanelDepsHelpers) return salesPanelDepsHelpers;
      salesPanelDepsHelpers = APP_SUPPORT.createSalesPanelDepsHelpers({ dom, state, windowObject, api, escapeHtml, runtimeAdapters: FRONTEND_RUNTIME_ADAPTERS, salesStateHelpers: SALES_STATE_HELPERS, renderUserOwnedSalesClaimCard, renderCompanySalesClaimCard, renderUserTrackerClaimSection, claimSalesProject, saveSalesClaimNote, transferSalesClaim, closeSalesClaim, adminDeleteLatestSalesNote, releaseSalesClaim, formatContractAmountInput, isAdminRole, normalizeSalesClaimCardViewModel: windowObject.SPMSAppControllerWiringRuntime.normalizeSalesClaimCardViewModel, renderTrackerEntries, loadSalesOverview, loadMySalesClaims, loadVisibleSalesClaims, refreshSalesAdminPanels, salesViewRuntime: SALES_VIEW_RUNTIME, flash });
      return salesPanelDepsHelpers;
    }
    function buildSalesOverviewStorageIdentity() { return getBootstrapCacheHelpers().buildSalesOverviewStorageIdentity(); }
    function maybePreloadAdminGoogleSheetsBootstrap() {
      const runtimeState = getAdminGoogleSheetsRuntimeState();
      if (!runtimeState.ADMIN_GOOGLE_SHEETS_RUNTIME || !runtimeState.canLoadProtectedConsoleData() || !runtimeState.shouldShowSharedGoogleSheetsShell({ canLoadProtectedData: true })) return;
      if (runtimeState.hydrateAdminGoogleSheetsCacheOnFirstProtectedRender()) {
        if (!state.adminGoogleSheetsCacheBootstrapRefreshRequested && !state.adminGoogleSheetsBootstrapLoading) {
          state.adminGoogleSheetsCacheBootstrapRefreshRequested = true;
          void runtimeState.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
        }
        return;
      }
      if (state.adminGoogleSheetsBootstrap || state.adminGoogleSheetsBootstrapLoading || state.adminGoogleSheetsBootstrapError) return;
      void runtimeState.loadAdminGoogleSheetsBootstrap({ silent: true });
    }
    function clearUserModeRunSelection({ sync = false } = {}) {
      if (state.uiMode !== "user" || !APP_SUPPORT.useGlobalTrackerEntriesScope()) return;
      const hadRunContext = Boolean(state.selectedRunId || state.selectedTrackerRunId || state.selectedRun || state.selectedTrackerRun || state.selectedTrackerWorkbookArtifactId);
      state.selectedRunId = null;
      state.selectedRun = null;
      state.selectedTrackerRunId = null;
      state.selectedTrackerRun = null;
      state.selectedTrackerWorkbookArtifactId = null;
      if (hadRunContext && sync) syncUrlState();
    }
    return {
      getAppBootstrapBridge,
      hydrateStateFromUrl,
      renderSyncMeta,
      touchSyncMeta,
      getProjectRelatedBodyRuntime,
      hydrateProjectRelatedPayloadCache,
      persistProjectRelatedPayloadCache,
      getBootstrapCacheHelpers,
      getTrackerChangeEventHelpers,
      getTrackerRenderFallbackHelpers,
      getSalesPanelDepsHelpers,
      buildSalesOverviewStorageIdentity,
      maybePreloadAdminGoogleSheetsBootstrap,
      clearUserModeRunSelection,
    };
  }

  function createAppRuntimeBodyConsoleDelegates({
    state,
    windowObject,
    APP_SUPPORT,
    RELATED_NOTICE_RUNTIME,
    escapeHtml,
    api,
    flash,
    setBusy,
    dom,
    callRunPanelsControllerMethod,
    getRunPanelsController,
    getConsolePanelsController,
    getProjectRelatedController,
    getReportPanelsController,
    getProjectRelatedBodyRuntime,
    getTrackerController,
    loadRuns,
    selectRun,
  }) {
    function renderRuns() { return callRunPanelsControllerMethod("renderRuns", null); }
    function renderRunsPagination() { return callRunPanelsControllerMethod("renderRunsPagination", null); }
    function changeRunsPage(delta) { return callRunPanelsControllerMethod("changeRunsPage", null, delta); }
    async function selectRunById(runId) { return callRunPanelsControllerMethod("selectRun", null, runId); }
    async function refreshSelectedRun({ silent = false } = {}) { return getTrackerController().refreshSelectedRun({ silent }); }
    function renderRunDetail(run) { return callRunPanelsControllerMethod("renderRunDetail", null, run); }
    function renderRunExecutionContext(run) { return getConsolePanelsController().renderRunExecutionContext(run); }
    function resolveTrackerExecutionContext(run) { return callRunPanelsControllerMethod("resolveTrackerExecutionContext", null, run); }
    function normalizeTrackerExecutionContext(payload = {}) { return callRunPanelsControllerMethod("normalizeTrackerExecutionContext", null, payload); }
    function numericSummaryValue(...values) { return callRunPanelsControllerMethod("numericSummaryValue", null, ...values); }
    function trackerExportStageLabel(stage) { return callRunPanelsControllerMethod("trackerExportStageLabel", null, stage); }
    function trackerExecutionTone(status) { return callRunPanelsControllerMethod("trackerExecutionTone", null, status); }
    function trackerExecutionMessage(context) { return callRunPanelsControllerMethod("trackerExecutionMessage", null, context); }
    function syncRunActionButtons(run) { return callRunPanelsControllerMethod("syncRunActionButtons", null, run); }
    function schedulePolling(run) { return callRunPanelsControllerMethod("schedulePolling", null, run); }
    async function loadSelectedRunLogs({ silent = false, runId = state.selectedRunId } = {}) { return callRunPanelsControllerMethod("loadSelectedRunLogs", null, { silent, runId }); }
    function renderLogsList(items) { return getRunPanelsController()?.renderLogsList?.(items) ?? callRunPanelsControllerMethod("renderLogsList", null, items); }
    function renderRunEventStatus(message, tone = "") { return getRunPanelsController()?.renderRunEventStatus?.(message, tone) ?? callRunPanelsControllerMethod("renderRunEventStatus", null, message, tone); }
    function disconnectRunEventStream() { return getTrackerController().disconnectRunEventStream(); }
    function connectRunEventStream(runId) { return getTrackerController().connectRunEventStream(runId); }
    async function loadRunPresets({ silent = false } = {}) { return callRunPanelsControllerMethod("loadRunPresets", null, { silent }); }
    function renderRunPresetPanel(errorMessage = "") { return callRunPanelsControllerMethod("renderRunPresetPanel", null, errorMessage); }
    function applyPresetParams(params) { return callRunPanelsControllerMethod("applyPresetParams", null, params); }
    async function applySelectedPreset() { return callRunPanelsControllerMethod("applySelectedPreset", null); }
    async function saveCurrentFormAsPreset() { return callRunPanelsControllerMethod("saveCurrentFormAsPreset", null); }
    async function loadProjects({ silent = false } = {}) { return getConsolePanelsController().loadProjects({ silent }); }
    function renderProjects(errorMessage = "") { return getConsolePanelsController().renderProjects(errorMessage); }
    function renderRelatedProjectNotices(project) { return getProjectRelatedController()?.renderRelatedProjectNotices?.(project) ?? ""; }
    function renderTrackerEntryRelatedNotices(entry) { return getProjectRelatedController()?.renderTrackerEntryRelatedNotices?.(entry) ?? ""; }
    function renderRelatedNoticePanel(projectId) { return getProjectRelatedController()?.renderRelatedNoticePanel?.(projectId) ?? ""; }
    function bindRelatedNoticeViewerButtons(root) { return getProjectRelatedController()?.bindRelatedNoticeViewerButtons?.(root); }
    async function openRelatedNoticeViewer(item) { return getProjectRelatedController()?.openRelatedNoticeViewer?.(item); }
    async function openProjectNoticeViewer(project) { return getProjectRelatedController()?.openProjectNoticeViewer?.(project); }
    function buildProjectNoticeUrl(project) { return RELATED_NOTICE_RUNTIME?.buildProjectNoticeUrl(project) || ""; }
    function extractTrackerEntryBidParts(entry) { return RELATED_NOTICE_RUNTIME?.extractTrackerEntryBidParts(entry) || { bidNo: "", bidOrd: "" }; }
    function buildTrackerEntryNoticeUrl(entry) { return RELATED_NOTICE_RUNTIME?.buildTrackerEntryNoticeUrl(entry) || ""; }
    async function openTrackerEntryNoticeViewer(entryId, entries = state.trackerEntries) { return getProjectRelatedController()?.openTrackerEntryNoticeViewer?.(entryId, entries); }
    function formatNoticeViewerSourceLabel(value) {
      return getProjectRelatedBodyRuntime()?.formatNoticeViewerSourceLabel?.(value) || String(value || "");
    }
    function renderNoticeViewerWindow(targetWindow, { title = "Notice", meta = "", body = "" } = {}) {
      const controller = windowObject.REPORT_PANELS_CONTROLLER?.createReportPanelsController ? getReportPanelsController() : null;
      if (controller?.renderNoticeViewerWindow) return controller.renderNoticeViewerWindow(targetWindow, { title, meta, body });
      const runtime = getProjectRelatedBodyRuntime();
      if (runtime?.renderNoticeViewerWindow) return runtime.renderNoticeViewerWindow(targetWindow, { title, meta, body });
      const html = RELATED_NOTICE_RUNTIME?.buildNoticeViewerHtml?.({ title, meta, body })
        || `<!doctype html><html><body><h1>${escapeHtml(title)}</h1><div>${escapeHtml(meta)}</div>${body}</body></html>`;
      if (targetWindow?.document?.open) targetWindow.document.open();
      if (targetWindow?.document?.write) targetWindow.document.write(html);
      if (targetWindow?.document?.close) targetWindow.document.close();
      return undefined;
    }
    function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = "Notice") {
      const controller = windowObject.REPORT_PANELS_CONTROLLER?.createReportPanelsController ? getReportPanelsController() : null;
      if (controller?.renderNoticeViewerPayload) return controller.renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle);
      const runtime = getProjectRelatedBodyRuntime();
      if (runtime?.renderNoticeViewerPayload) return runtime.renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle);
      const title = String(payload?.title || payload?.project_name || fallbackTitle || "Notice").trim() || "Notice";
      const sourceLabel = RELATED_NOTICE_RUNTIME?.formatNoticeViewerSourceLabel?.(payload?.source) || "";
      const documentMarkup = RELATED_NOTICE_RUNTIME?.buildNoticeViewerDocumentsMarkup?.(payload) || "";
      const meta = [sourceLabel, payload?.bid_no, payload?.bid_ord].filter(Boolean).join(" ");
      return renderNoticeViewerWindow(viewerWindow, { title, meta, body: `${documentMarkup}${payload?.body || ""}` });
    }
    function renderNoticeViewerError(viewerWindow, { title = "Notice", errorMessage = "", links = [] } = {}) {
      const controller = windowObject.REPORT_PANELS_CONTROLLER?.createReportPanelsController ? getReportPanelsController() : null;
      if (controller?.renderNoticeViewerError) return controller.renderNoticeViewerError(viewerWindow, { title, errorMessage, links });
      const runtime = getProjectRelatedBodyRuntime();
      if (runtime?.renderNoticeViewerError) return runtime.renderNoticeViewerError(viewerWindow, { title, errorMessage, links });
      const linkMarkup = Array.isArray(links) && links.length
        ? `<ul>${links.map((link) => `<li><a href="${escapeHtml(link?.href || "#")}">${escapeHtml(link?.label || link?.href || "link")}</a></li>`).join("")}</ul>`
        : "";
      return renderNoticeViewerWindow(viewerWindow, { title, meta: "error", body: `<p>${escapeHtml(errorMessage || "")}</p>${linkMarkup}` });
    }
    async function cancelSelectedRun() {
      if (!state.selectedRunId) return;
      setBusy(dom.cancelRunButton, true, "Cancelling...");
      try {
        const response = await api(`/api/runs/${state.selectedRunId}/cancel`, { method: "POST" });
        flash(`Cancel requested for ${response.id}`);
        await refreshSelectedRun();
        await loadRuns({ silent: true, preservePage: true });
      } catch (err) {
        flash(err.message, "error");
      } finally {
        setBusy(dom.cancelRunButton, false, "Cancel run");
      }
    }
    async function createTrackerExportForSelectedRun() {
      if (!state.selectedRunId) return;
      setBusy(dom.trackerExportButton, true, "Processing...");
      try {
        const response = await api(`/api/runs/${state.selectedRunId}/tracker-export`, { method: "POST" });
        flash(`Tracker export queued: ${response.id}`);
        state.selectedTrackerRunId = response.id;
        state.runFilters.page = 1;
        await (typeof selectRun === "function" ? selectRun(response.id) : selectRunById(response.id));
        await loadRuns({ silent: true, preservePage: true });
      } catch (err) {
        flash(err.message, "error");
      } finally {
        setBusy(dom.trackerExportButton, false, "Create tracker export");
      }
    }
    return {
      renderRuns,
      renderRunsPagination,
      changeRunsPage,
      selectRun: selectRunById,
      refreshSelectedRun,
      renderRunDetail,
      renderRunExecutionContext,
      resolveTrackerExecutionContext,
      normalizeTrackerExecutionContext,
      numericSummaryValue,
      trackerExportStageLabel,
      trackerExecutionTone,
      trackerExecutionMessage,
      syncRunActionButtons,
      schedulePolling,
      loadSelectedRunLogs,
      renderLogsList,
      renderRunEventStatus,
      disconnectRunEventStream,
      connectRunEventStream,
      loadRunPresets,
      renderRunPresetPanel,
      applyPresetParams,
      applySelectedPreset,
      saveCurrentFormAsPreset,
      loadProjects,
      renderProjects,
      renderRelatedProjectNotices,
      renderTrackerEntryRelatedNotices,
      renderRelatedNoticePanel,
      bindRelatedNoticeViewerButtons,
      openRelatedNoticeViewer,
      openProjectNoticeViewer,
      buildProjectNoticeUrl,
      extractTrackerEntryBidParts,
      buildTrackerEntryNoticeUrl,
      openTrackerEntryNoticeViewer,
      renderNoticeViewerPayload,
      renderNoticeViewerError,
      renderNoticeViewerWindow,
      formatNoticeViewerSourceLabel,
      cancelSelectedRun,
      createTrackerExportForSelectedRun,
    };
  }

  global.SPMSAppRuntimeBodyConsoleRuntime = {
    createAppRuntimeBodyAccessors,
    createAppRuntimeBodyConsoleDelegates,
  };
})(typeof window !== "undefined" ? window : globalThis);
