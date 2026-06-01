import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const wiringAuthRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-auth-runtime.js");
const wiringRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-runtime.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8").replace(/\r\n/g, "\n");
}

function readWiringRuntimeSource() {
  return [
    fs.readFileSync(wiringAuthRuntimePath, "utf8"),
    fs.readFileSync(wiringRuntimePath, "utf8"),
  ].join("\n");
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

function createAppSupportStub(appSupportCalls = null, appSupportContexts = null) {
  const record = (name) => {
    if (Array.isArray(appSupportCalls)) {
      appSupportCalls.push(name);
    }
  };

  const buildDownloadControllerDeps = (deps) => ({
    state: deps.state,
    dom: deps.dom,
    window: deps.window,
    document: deps.document,
    setBusy: deps.setBusy,
    flash: deps.flash,
    api: deps.api,
    readTrackerFiltersFromControls: deps.readTrackerFiltersFromControls,
    useGlobalTrackerEntriesScope: deps.useGlobalTrackerEntriesScope,
    resolveActiveTrackerRunId: deps.resolveActiveTrackerRunId,
  });

  const buildSelectedEntryControllerDeps = (deps) => ({
    dom: deps.dom,
    state: deps.state,
    buildSelectedEntryLoadingView: deps.buildSelectedEntryLoadingView,
    buildSelectedEntryEmptyView: deps.buildSelectedEntryEmptyView,
    buildSelectedEntryDisplayView: deps.buildSelectedEntryDisplayView,
    buildPatchPanelView: deps.buildPatchPanelView,
    buildSelectedEntryChangeEventsMarkup: deps.buildSelectedEntryChangeEventsMarkup,
    buildSelectedEntryMeta: deps.buildSelectedEntryMeta,
    buildEntryDiagnosticsMarkup: deps.buildEntryDiagnosticsMarkup,
    buildEntryFieldGridMarkup: deps.buildEntryFieldGridMarkup,
    buildDrawerFieldListMarkup: deps.buildDrawerFieldListMarkup,
    truncate: deps.truncate,
    escapeHtml: deps.escapeHtml,
    requireSelectedEntryRuntime: () => deps.SELECTED_ENTRY_RUNTIME || null,
    formatJson: deps.formatJson,
    EDITABLE_FIELDS: deps.EDITABLE_FIELDS,
    loadSelectedEntryAudit: deps.loadSelectedEntryAudit,
    loadSelectedEntryChangeEvents: deps.loadSelectedEntryChangeEvents,
    openDrawer: deps.openDrawer,
    closeDrawer: deps.closeDrawer,
    syncUrlState: deps.syncUrlState,
  });

  const buildRunPanelsControllerDeps = (deps) => ({
    state: deps.state,
    dom: deps.dom,
    window: deps.window,
    document: deps.document,
    RUN_VIEW_RUNTIME: deps.RUN_VIEW_RUNTIME,
    api: deps.api,
    flash: deps.flash,
    touchSyncMeta: deps.touchSyncMeta,
    setBusy: deps.setBusy,
    loadRuns: deps.loadRuns,
    trackerController: deps.trackerController,
    resetTrackerBoardEdit: deps.resetTrackerBoardEdit,
    syncUrlState: deps.syncUrlState,
    refreshSelectedRun: deps.refreshSelectedRun,
    escapeHtml: deps.escapeHtml,
    runTypeLabel: deps.runTypeLabel,
    statusBadge: deps.statusBadge,
    formatDate: deps.formatDate,
    formatJson: deps.formatJson,
    progressPercent: deps.progressPercent,
    renderRunExecutionContext: deps.renderRunExecutionContext,
    isProjectTrackerRun: deps.isProjectTrackerRun,
    useGlobalTrackerEntriesScope: deps.useGlobalTrackerEntriesScope,
    renderArtifactsList: deps.renderArtifactsList,
    buildArtifactEmptyMessage: deps.buildArtifactEmptyMessage,
    loadTrackerEntries: deps.loadTrackerEntries,
  });

  const buildReportPanelsControllerDeps = (deps) => ({
    state: deps.state,
    dom: deps.dom,
    api: deps.api,
    flash: deps.flash,
    setBusy: deps.setBusy,
    escapeHtml: deps.escapeHtml,
    formatDate: deps.formatDate,
    formatJson: deps.formatJson,
    formatBytes: deps.formatBytes,
    statusBadge: deps.statusBadge,
    ARTIFACT_RUNTIME: deps.ARTIFACT_RUNTIME,
    RELATED_NOTICE_RUNTIME: deps.RELATED_NOTICE_RUNTIME,
    loadDashboardSummary: deps.loadDashboardSummary,
    touchSyncMeta: deps.touchSyncMeta,
    syncUrlState: deps.syncUrlState,
    callRunPanelsController: deps.callRunPanelsController,
  });

  const buildConsolePanelsControllerDeps = (deps) => ({
    dom: deps.dom,
    state: deps.state,
    escapeHtml: deps.escapeHtml,
    formatDate: deps.formatDate,
    runTypeLabel: deps.runTypeLabel,
    statusBadge: deps.statusBadge,
    metricCard: deps.metricCard,
    PROJECT_RUNTIME: deps.PROJECT_RUNTIME,
    RUN_VIEW_RUNTIME: deps.RUN_VIEW_RUNTIME,
    renderArtifactPreviewMarkup: deps.renderArtifactPreviewMarkup,
    resolveTrackerExecutionContext: deps.resolveTrackerExecutionContext,
    trackerExecutionTone: deps.trackerExecutionTone,
    trackerExecutionMessage: deps.trackerExecutionMessage,
    progressPercent: deps.progressPercent,
    trackerExportStageLabel: deps.trackerExportStageLabel,
    renderRelatedProjectNotices: deps.renderRelatedProjectNotices,
    bindRelatedNoticeViewerButtons: deps.bindRelatedNoticeViewerButtons,
    toggleProjectRelated: deps.toggleProjectRelated,
    openProjectNoticeViewer: deps.openProjectNoticeViewer,
    applyPresetParams: deps.applyPresetParams,
    api: deps.api,
    syncUrlState: deps.syncUrlState,
    syncCollectModeOptions: deps.syncCollectModeOptions,
    touchSyncMeta: deps.touchSyncMeta,
    flash: deps.flash,
  });

  const buildAdminGoogleSheetsControllerDeps = (deps) => deps;

  const buildRuntimeEnhancementsDeps = (deps) => deps;

  const buildUiModeControllerDeps = (deps) => ({
    state: deps.state,
    dom: deps.dom,
    window: deps.window,
    DEFAULT_ADMIN_TAB: deps.DEFAULT_ADMIN_TAB,
    APP_ROOT_PATH: deps.APP_ROOT_PATH,
    normalizeLocationPath: deps.normalizeLocationPath,
    getAdminRoutePath: deps.getAdminRoutePath,
    canUseAdminMode: deps.canUseAdminMode,
    canLoadProtectedConsoleData: deps.canLoadProtectedConsoleData,
    shouldShowAdminModeToggle: deps.shouldShowAdminModeToggle,
    shouldShowSharedGoogleSheetsShell: deps.shouldShowSharedGoogleSheetsShell,
    isPendingLegacyAdminAlias: deps.isPendingLegacyAdminAlias,
    clearAdminLegacyRouteIntent: deps.clearAdminLegacyRouteIntent,
    getAdminTabByPathname: deps.getAdminTabByPathname,
    resolveUiModeFromLocation: deps.resolveUiModeFromLocation,
    resolveLegacyAdminRoutePath: deps.resolveLegacyAdminRoutePath,
    normalizeAdminTab: deps.normalizeAdminTab,
    clearAdminGoogleSheetPopupStateForTab: deps.clearAdminGoogleSheetPopupStateForTab,
    maybePreloadAdminGoogleSheetsBootstrap: deps.maybePreloadAdminGoogleSheetsBootstrap,
    syncUrlState: deps.syncUrlState,
    syncTrackerChangeBellVisibility: deps.syncTrackerChangeBellVisibility,
    hydrateTrackerChangeEventsCache: deps.hydrateTrackerChangeEventsCache,
    renderTrackerChangeEventUnreadCount: deps.renderTrackerChangeEventUnreadCount,
    renderTrackerChangeBellPopover: deps.renderTrackerChangeBellPopover,
    renderAdminTopNavigation: deps.renderAdminTopNavigation,
    renderAdminEmbedPanel: deps.renderAdminEmbedPanel,
    renderTrackerTemplateStatus: deps.renderTrackerTemplateStatus,
    loadAdminConsoleData: deps.loadAdminConsoleData,
    loadBackfillConflicts: deps.loadBackfillConflicts,
    renderBackfillConflictsPanel: deps.renderBackfillConflictsPanel,
    closeDrawer: deps.closeDrawer,
    renderAuthUi: deps.renderAuthUi,
    renderOrganizationAdminPanel: deps.renderOrganizationAdminPanel,
    renderMySalesClaimsPanel: deps.renderMySalesClaimsPanel,
    renderSalesSummaryPanel: deps.renderSalesSummaryPanel,
    renderRunDetail: deps.renderRunDetail,
    renderTrackerEntries: deps.renderTrackerEntries,
    loadOrganizationUsers: deps.loadOrganizationUsers,
    loadTrackerEntries: deps.loadTrackerEntries,
    loadTrackerChangeEventUnreadCount: deps.loadTrackerChangeEventUnreadCount,
    loadTrackerChangeEvents: deps.loadTrackerChangeEvents,
    clearUserModeRunSelection: deps.clearUserModeRunSelection,
    hydrateHomeBootstrapCache: deps.hydrateHomeBootstrapCache,
    loadHomeBootstrap: deps.loadHomeBootstrap,
    scheduleTrackerChangeEventsWarmup: deps.scheduleTrackerChangeEventsWarmup,
  });

  const buildOrgAdminControllerDeps = (deps) => ({
    ...(deps.sharedDeps || {}),
    ...(deps.formattingDeps || {}),
    ...(deps.actionDeps || {}),
    ...(deps.runtimeDeps || {}),
  });

  const buildAuthBaseDeps = (deps) => ({
    state: deps.state,
    dom: deps.dom,
    document: deps.documentObject,
    window: deps.windowObject,
    api: deps.api,
    flash: deps.flash,
    setBusy: deps.setBusy,
    escapeHtml: deps.escapeHtml,
    formatOrgRoleLabel: deps.formatOrgRoleLabel,
    formatInvitationStatusLabel: deps.formatInvitationStatusLabel,
    formatSalesDateLabel: deps.formatSalesDateLabel,
    formatMembershipStatusLabel: deps.formatMembershipStatusLabel,
    requireAuthSessionRuntime: deps.requireAuthSessionRuntime,
    loadOrganizationUsers: deps.loadOrganizationUsers,
    loadOrganizationMembers: deps.loadOrganizationMembers,
    loadSalesOverview: deps.loadSalesOverview,
    loadMySalesClaims: deps.loadMySalesClaims,
    refreshSalesAdminPanels: deps.refreshSalesAdminPanels,
    ensureConsoleInitialized: deps.ensureConsoleInitialized,
    shouldShowSignUpMode: deps.shouldShowSignUpMode,
    AUTH_MODE_SIGN_IN: deps.AUTH_MODE_SIGN_IN,
    AUTH_MODE_SIGN_UP: deps.AUTH_MODE_SIGN_UP,
    syncUiModeChrome: deps.syncUiModeChrome,
    applyUiModeTransition: deps.applyUiModeTransition,
  });

  const buildTrackerBaseDeps = (deps) => ({
    state: deps.state,
    dom: deps.dom,
    flash: deps.flash,
    escapeHtml: deps.escapeHtml,
    syncUrlState: deps.syncUrlState,
    renderTrackerEntries: deps.renderTrackerEntries,
  });

  const buildTrackerEntryActionsDeps = (deps) => ({
    ...buildTrackerBaseDeps(deps),
    EDITABLE_FIELDS: deps.EDITABLE_FIELDS,
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: deps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    renderTrackerBoard: deps.renderTrackerBoard,
    loadTrackerEntries: deps.loadTrackerEntries,
    setBusy: deps.setBusy,
    patchTrackerEntry: deps.patchTrackerEntry,
    syncTrackerEntryAfterPatch: deps.syncTrackerEntryAfterPatch,
  });

  const buildTrackerDiagnosticsPanelDeps = (deps) => ({
    ...buildTrackerBaseDeps(deps),
    window: deps.window,
    api: deps.api,
    trackerController: typeof deps.getTrackerController === "function" ? deps.getTrackerController() : null,
    formatDate: deps.formatDate,
    formatContactResolutionStatusLabel: deps.formatContactResolutionStatusLabel,
    formatContactResolutionReasonLabel: deps.formatContactResolutionReasonLabel,
    formatBackfillConflictResolutionLabel: deps.formatBackfillConflictResolutionLabel,
    getTrackerDiagnosticsScope: deps.getTrackerDiagnosticsScope,
    requireTrackerDiagnosticsRuntime: deps.requireTrackerDiagnosticsRuntime,
    buildTrackerChangeEventsMarkup: deps.buildTrackerChangeEventsMarkup,
    buildTrackerChangeBellPopoverMarkup: deps.buildTrackerChangeBellPopoverMarkup,
    buildBackfillConflictsMarkup: deps.buildBackfillConflictsMarkup,
    buildBackfillConflictsView: deps.buildBackfillConflictsView,
    loadSelectedEntryDetail: deps.loadSelectedEntryDetail,
    focusTrackerChangeEntry: deps.focusTrackerChangeEntry,
    closeTrackerChangeModal: deps.closeTrackerChangeModal,
  });

  const buildTrackerRenderControllerDeps = (deps) => ({
    ...deps.sharedDeps,
    ...deps.trackerSalesActions,
    ...deps.selectedEntryActions,
    ...deps.trackerBoardActions,
  });
  const buildProjectRelatedControllerDeps = (deps) => ({
    ...deps.sharedDeps,
    ...deps.projectRelatedConfig,
    ...deps.noticeViewerRenderers,
    ...deps.projectRelatedActions,
  });

  return {
    resolveActiveTrackerRunId() {
      const state = this.state || globalThis.state || {};
      if (state.selectedRun && state.selectedRun.run_type === "tracker_export") {
        return state.selectedRun.id || null;
      }
      return state.selectedTrackerRunId || null;
    },
    handleOutOfRangePageError(error, filterState, scopeLabel) {
      const message = String(error && error.message ? error.message : error || "").toLowerCase();
      const isOutOfRangePageError =
        message.includes("requested range not satisfiable") || message.includes("offset of");
      if (!isOutOfRangePageError || !filterState || Number(filterState.page || 1) <= 1) {
        return false;
      }
      const rawMessage = String(error && error.message ? error.message : error || "");
      const match = rawMessage.match(/there are only\s+(\d+)\s+rows/i);
      const totalRows = match ? Number(match[1]) || 0 : 0;
      const pageSize = Math.max(1, Number(filterState.pageSize || 20));
      const fallbackPage = totalRows > 0 ? Math.max(1, Math.ceil(totalRows / pageSize)) : 1;
      filterState.page = fallbackPage;
      globalThis.flash?.(`${scopeLabel} 목록 페이지를 ${fallbackPage}로 보정했습니다.`, "warn");
      return true;
    },
    focusTrackerChangeEntry(entryId, entries = globalThis.state?.trackerEntries) {
      const nextEntryId = String(entryId || "").trim();
      if (!nextEntryId) {
        return Promise.resolve(null);
      }
      const state = this.state || globalThis.state || {};
      const dom = this.dom || globalThis.dom || {};
      const syncUrlState = this.syncUrlState || globalThis.syncUrlState;
      const renderTrackerEntries = this.renderTrackerEntries || globalThis.renderTrackerEntries;
      const documentObject = this.documentObject || globalThis.document;
      const windowObject = this.windowObject || globalThis.window || {};
      const loadSelectedEntryDetail = this.loadSelectedEntryDetail || globalThis.loadSelectedEntryDetail;
      state.selectedEntryId = nextEntryId;
      state.drawerOpen = state.uiMode !== "admin";
      syncUrlState?.();
      renderTrackerEntries?.(entries, { refreshSelectedEntry: state.uiMode === "admin" });
      const escapedEntryId = windowObject.CSS?.escape ? windowObject.CSS.escape(nextEntryId) : nextEntryId;
      documentObject?.querySelector?.(`[data-board-entry-id="${escapedEntryId}"], [data-entry-id="${escapedEntryId}"]`)
        ?.scrollIntoView?.({ behavior: "smooth", block: "center" });
      const detailPromise = loadSelectedEntryDetail?.({ entryId: nextEntryId, silent: true, force: true });
      if (!detailPromise || typeof detailPromise.finally !== "function") {
        if (state.uiMode === "admin") {
          dom.entryEditor?.scrollIntoView?.({ behavior: "smooth", block: "start" });
        }
        return Promise.resolve(detailPromise ?? null);
      }
      return detailPromise.finally(() => {
        if (state.uiMode === "admin") {
          dom.entryEditor?.scrollIntoView?.({ behavior: "smooth", block: "start" });
        }
      });
    },
    changeProjectsPage(options = {}, delta = 0) {
      if (options.controller?.changeProjectsPage) {
        return options.controller.changeProjectsPage(delta);
      }
      const state = options.state || {};
      const totalPages = Math.max(1, Math.ceil((state.projectsTotal || 0) / (state.projectFilters?.pageSize || 1)));
      const nextPage = Math.min(totalPages, Math.max(1, (state.projectFilters?.page || 1) + delta));
      if (nextPage === state.projectFilters?.page) {
        return undefined;
      }
      state.projectFilters.page = nextPage;
      void options.loadProjects?.({ silent: true });
      return undefined;
    },
    normalizeCollectMode(value) {
      const raw = String(value || "").trim().toLowerCase();
      if (raw === "synthetic") {
        return "auto";
      }
      if (["auto", "native", "synthetic"].includes(raw)) {
        return raw;
      }
      return "auto";
    },
    trackerColumnStyle(widths, index, runtime = null) {
      return runtime?.trackerColumnStyle?.(widths, index) || "";
    },
    buildWorkbookTitleCells(titleRow, helpers = {}, runtime = null) {
      return runtime?.buildWorkbookTitleCells?.(titleRow, helpers) || "";
    },
    fetchArtifactPreview(item, api) {
      const limit = item?.artifact_type === "tracking_excel" ? 16 : 6;
      return api(`/api/artifacts/${item?.id}/preview?limit=${limit}`);
    },
    ensureArtifactPreviewCached(options = {}) {
      return (async () => {
        if (!options.item || options.state?.artifactPreviewCache?.[options.item.id]) {
          return;
        }
        options.state.artifactPreviewCache[options.item.id] = { ok: true };
        options.renderArtifactsList?.();
        options.renderRunExecutionContext?.(options.state?.selectedRun);
      })();
    },
    renderTrackerContactResolutionSummary(options = {}, errorMessage = "") {
      if (!options.TRACKER_DIAGNOSTICS_RUNTIME) {
        options.dom.trackerContactResolutionSummary.className = "missing-report-summary empty-state";
        options.dom.trackerContactResolutionSummary.innerHTML = '<div class="empty-state">연락처 검증 UI 런타임을 불러오지 못했습니다.</div>';
        options.dom.trackerContactResolutionList.className = "missing-report-list empty-state";
        options.dom.trackerContactResolutionList.innerHTML = '<div class="empty-state">연락처 검증 UI 런타임을 불러오지 못했습니다.</div>';
        return undefined;
      }
      return options.renderTrackerContactResolutionSummary?.(errorMessage);
    },
    renderTrackerCleanupPreview(options = {}, errorMessage = "") {
      if (!options.TRACKER_DIAGNOSTICS_RUNTIME) {
        options.dom.trackerCleanupPreview.className = "missing-report-list empty-state";
        options.dom.trackerCleanupPreview.innerHTML = '<div class="empty-state">tracker cleanup UI 런타임을 불러오지 못했습니다.</div>';
        return undefined;
      }
      return options.renderTrackerCleanupPreview?.(errorMessage);
    },
    renderTrackerMissingReport(options = {}, errorMessage = "") {
      if (!options.TRACKER_MISSING_REPORT_RUNTIME) {
        options.dom.missingReportSummary.innerHTML = '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>';
        options.dom.missingReportList.innerHTML = '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>';
        return undefined;
      }
      const view = options.TRACKER_MISSING_REPORT_RUNTIME.buildMissingReportViewModel(
        options.state.trackerMissingReport,
        { errorMessage },
        { escapeHtml: options.escapeHtml, formatDate: options.formatDate },
      );
      if (view.summaryClassName) {
        options.dom.missingReportSummary.className = view.summaryClassName;
      }
      options.dom.missingReportSummary.innerHTML = view.summaryMarkup;
      if (view.listClassName) {
        options.dom.missingReportList.className = view.listClassName;
      }
      options.dom.missingReportList.innerHTML = view.listMarkup;
      return undefined;
    },
    buildAppEventBindingsDepsFromApp(options = {}) {
      const {
        core = {},
        auth = {},
        orgAdmin = {},
        sales = {},
        runs = {},
        reports = {},
        ui = {},
        tracker = {},
        downloads = {},
      } = options;
      return {
        dom: core.dom,
        state: core.state,
        window: core.window,
        document: core.document,
        AUTH_MODE_SIGN_IN: auth.AUTH_MODE_SIGN_IN,
        AUTH_MODE_SIGN_UP: auth.AUTH_MODE_SIGN_UP,
        TRACKER_REGION_OPTIONS: tracker.TRACKER_REGION_OPTIONS,
        handleAuthSubmit: auth.handleAuthSubmit,
        setAuthMode: auth.setAuthMode,
        handleAuthFindId: auth.handleAuthFindId,
        handleAuthPasswordReset: auth.handleAuthPasswordReset,
        scheduleInvitationPreviewLookup: auth.scheduleInvitationPreviewLookup,
        renderAuthUi: auth.renderAuthUi,
        handleAuthSignOut: auth.handleAuthSignOut,
        openProfileDialog: auth.openProfileDialog,
        handleProfileSubmit: auth.handleProfileSubmit,
        handleInvitationSubmit: orgAdmin.handleInvitationSubmit,
        loadOrganizationAdminData: orgAdmin.loadOrganizationAdminData,
        closeProfileDialog: auth.closeProfileDialog,
        setTrackerChangeBellPopoverOpen: tracker.setTrackerChangeBellPopoverOpen,
        downloadSalesWorkbook: downloads.downloadSalesWorkbook,
        closeSalesCloseDialog: sales.closeSalesCloseDialog,
        formatContractAmountInput: sales.formatContractAmountInput,
        confirmSalesCloseDialog: sales.confirmSalesCloseDialog,
        refreshAuthSessionState: auth.refreshAuthSessionState,
        loadDashboardSummary: reports.loadDashboardSummary,
        handleRunCreate: runs.handleRunCreate,
        handleRunFormReset: runs.handleRunFormReset,
        refreshSelectedRun: runs.refreshSelectedRun,
        loadRuns: runs.loadRuns,
        loadSelectedRunLogs: runs.loadSelectedRunLogs,
        runSelectedReport: reports.runSelectedReport,
        refreshReportPanels: reports.refreshReportPanels,
        loadSelectedRunArtifacts: runs.loadSelectedRunArtifacts,
        cancelSelectedRun: runs.cancelSelectedRun,
        createTrackerExportForSelectedRun: runs.createTrackerExportForSelectedRun,
        toggleUiMode: ui.toggleUiMode,
        renderSyncMeta: ui.renderSyncMeta,
        syncUrlState: ui.syncUrlState,
        loadReportJobs: reports.loadReportJobs,
        loadPhaseReport: reports.loadPhaseReport,
        readRunFiltersFromControls: runs.readRunFiltersFromControls,
        readTrackerFiltersFromControls: tracker.readTrackerFiltersFromControls,
        syncFilterControlsFromState: tracker.syncFilterControlsFromState,
        changeRunsPage: runs.changeRunsPage,
        loadTrackerEntries: tracker.loadTrackerEntries,
        trackerChangeEventsCacheIsFresh: tracker.trackerChangeEventsCacheIsFresh,
        renderTrackerChangeBellPopover: tracker.renderTrackerChangeBellPopover,
        loadTrackerChangeEvents: tracker.loadTrackerChangeEvents,
        focusTrackerChangePanel: tracker.focusTrackerChangePanel,
        uploadTrackerTemplate: tracker.uploadTrackerTemplate,
        resetTrackerTemplateOverride: tracker.resetTrackerTemplateOverride,
        changeEntriesPageTo: tracker.changeEntriesPageTo,
        changeEntriesPage: tracker.changeEntriesPage,
        getEntriesTotalPages: tracker.getEntriesTotalPages,
        normalizeTrackerRegionFilter: tracker.normalizeTrackerRegionFilter,
        parseTrackerRegionFilter: tracker.parseTrackerRegionFilter,
        saveEntryPatch: tracker.saveEntryPatch,
        clearEntryPatch: tracker.clearEntryPatch,
        loadSelectedEntryAudit: tracker.loadSelectedEntryAudit,
        loadTrackerMissingReport: tracker.loadTrackerMissingReport,
        refreshSalesAdminPanels: sales.refreshSalesAdminPanels,
        getMissingReportDownloadLimit: tracker.getMissingReportDownloadLimit,
        syncPatchValueFromSelectedEntry: tracker.syncPatchValueFromSelectedEntry,
        closeDrawer: tracker.closeDrawer,
        loadRunPresets: runs.loadRunPresets,
        applySelectedPreset: runs.applySelectedPreset,
        saveCurrentFormAsPreset: runs.saveCurrentFormAsPreset,
        renderRunPresetPanel: runs.renderRunPresetPanel,
        loadProjects: reports.loadProjects,
        changeProjectsPage: reports.changeProjectsPage,
        triggerTrackerEntriesXlsxDownload: downloads.triggerTrackerEntriesXlsxDownload,
      };
    },
    createUiModeControllerDepsHelpersFromApp(options = {}) {
      return this.createUiModeControllerDepsHelpers({
        state: options.core?.state,
        dom: options.core?.dom,
        window: options.core?.window,
        DEFAULT_ADMIN_TAB: options.adminTabs?.DEFAULT_ADMIN_TAB,
        APP_ROOT_PATH: options.adminTabs?.APP_ROOT_PATH,
        normalizeLocationPath: options.adminTabs?.normalizeLocationPath,
        getAdminRoutePath: options.adminTabs?.getAdminRoutePath,
        canUseAdminMode: options.ui?.canUseAdminMode,
        canLoadProtectedConsoleData: options.ui?.canLoadProtectedConsoleData,
        shouldShowAdminModeToggle: options.ui?.shouldShowAdminModeToggle,
        shouldShowSharedGoogleSheetsShell: options.ui?.shouldShowSharedGoogleSheetsShell,
        isPendingLegacyAdminAlias: options.adminTabs?.isPendingLegacyAdminAlias,
        clearAdminLegacyRouteIntent: options.adminTabs?.clearAdminLegacyRouteIntent,
        getAdminTabByPathname: options.adminTabs?.getAdminTabByPathname,
        resolveUiModeFromLocation: options.adminTabs?.resolveUiModeFromLocation,
        resolveLegacyAdminRoutePath: options.adminTabs?.resolveLegacyAdminRoutePath,
        normalizeAdminTab: options.adminTabs?.normalizeAdminTab,
        clearAdminGoogleSheetPopupStateForTab: options.adminTabs?.clearAdminGoogleSheetPopupStateForTab,
        maybePreloadAdminGoogleSheetsBootstrap: options.adminData?.maybePreloadAdminGoogleSheetsBootstrap,
        syncUrlState: options.ui?.syncUrlState,
        syncTrackerChangeBellVisibility: options.trackerChange?.syncTrackerChangeBellVisibility,
        hydrateTrackerChangeEventsCache: options.trackerChange?.hydrateTrackerChangeEventsCache,
        renderTrackerChangeEventUnreadCount: options.trackerChange?.renderTrackerChangeEventUnreadCount,
        renderTrackerChangeBellPopover: options.trackerChange?.renderTrackerChangeBellPopover,
        renderAdminTopNavigation: options.renders?.renderAdminTopNavigation,
        renderAdminEmbedPanel: options.renders?.renderAdminEmbedPanel,
        renderTrackerTemplateStatus: options.renders?.renderTrackerTemplateStatus,
        loadAdminConsoleData: options.adminData?.loadAdminConsoleData,
        loadBackfillConflicts: options.trackers?.loadBackfillConflicts,
        renderBackfillConflictsPanel: options.trackers?.renderBackfillConflictsPanel,
        closeDrawer: options.trackers?.closeDrawer,
        renderAuthUi: options.renders?.renderAuthUi,
        renderOrganizationAdminPanel: options.renders?.renderOrganizationAdminPanel,
        renderMySalesClaimsPanel: options.renders?.renderMySalesClaimsPanel,
        renderSalesSummaryPanel: options.renders?.renderSalesSummaryPanel,
        renderRunDetail: options.renders?.renderRunDetail,
        renderTrackerEntries: options.renders?.renderTrackerEntries,
        loadOrganizationUsers: options.adminData?.loadOrganizationUsers,
        loadTrackerEntries: options.trackers?.loadTrackerEntries,
        loadTrackerChangeEventUnreadCount: options.trackerChange?.loadTrackerChangeEventUnreadCount,
        loadTrackerChangeEvents: options.trackerChange?.loadTrackerChangeEvents,
        clearUserModeRunSelection: options.bootstrap?.clearUserModeRunSelection,
        hydrateHomeBootstrapCache: options.bootstrap?.hydrateHomeBootstrapCache,
        loadHomeBootstrap: options.bootstrap?.loadHomeBootstrap,
        scheduleTrackerChangeEventsWarmup: options.trackerChange?.scheduleTrackerChangeEventsWarmup,
      });
    },
    createAuthControllerDepsHelpersFromApp(options = {}) {
      const {
        core = {},
        authUi = {},
        uiMode = {},
        authState = {},
        adminData = {},
        trackerPanels = {},
        salesPanels = {},
        tracker = {},
      } = options;
      return this.createAuthControllerDepsHelpers({
        state: core.state,
        dom: core.dom,
        documentObject: core.documentObject,
        windowObject: core.windowObject,
        api: core.api,
        flash: core.flash,
        setBusy: core.setBusy,
        escapeHtml: core.escapeHtml,
        formatOrgRoleLabel: core.formatOrgRoleLabel,
        formatInvitationStatusLabel: core.formatInvitationStatusLabel,
        formatSalesDateLabel: core.formatSalesDateLabel,
        formatMembershipStatusLabel: core.formatMembershipStatusLabel,
        requireAuthSessionRuntime: authState.requireAuthSessionRuntime,
        loadOrganizationUsers: adminData.loadOrganizationUsers,
        loadOrganizationMembers: adminData.loadOrganizationMembers,
        loadSalesOverview: salesPanels.loadSalesOverview,
        loadMySalesClaims: salesPanels.loadMySalesClaims,
        refreshSalesAdminPanels: salesPanels.refreshSalesAdminPanels,
        ensureConsoleInitialized: authState.ensureConsoleInitialized,
        shouldShowSignUpMode: authUi.shouldShowSignUpMode,
        AUTH_MODE_SIGN_IN: authUi.AUTH_MODE_SIGN_IN,
        AUTH_MODE_SIGN_UP: authUi.AUTH_MODE_SIGN_UP,
        syncUiModeChrome: uiMode.syncUiModeChrome,
        applyUiModeTransition: uiMode.applyUiModeTransition,
        renderAuthUi: authUi.renderAuthUi,
        canUseAdminMode: authState.canUseAdminMode,
        canLoadProtectedConsoleData: authState.canLoadProtectedConsoleData,
        loadAdminConsoleData: adminData.loadAdminConsoleData,
        loadBackfillConflicts: trackerPanels.loadBackfillConflicts,
        renderBackfillConflictsPanel: trackerPanels.renderBackfillConflictsPanel,
        renderTrackerContactResolutionSummary: trackerPanels.renderTrackerContactResolutionSummary,
        renderTrackerCleanupPreview: trackerPanels.renderTrackerCleanupPreview,
        closeDrawer: tracker.closeDrawer,
        hydrateHomeBootstrapCache: authState.hydrateHomeBootstrapCache,
        clearUserModeRunSelection: authState.clearUserModeRunSelection,
        loadHomeBootstrap: authState.loadHomeBootstrap,
        loadTrackerEntries: tracker.loadTrackerEntries,
        getTrackerController: tracker.getTrackerController,
        renderOrganizationAdminPanel: adminData.renderOrganizationAdminPanel,
        renderMySalesClaimsPanel: salesPanels.renderMySalesClaimsPanel,
        renderSalesSummaryPanel: salesPanels.renderSalesSummaryPanel,
        renderRunDetail: trackerPanels.renderRunDetail,
        renderTrackerEntries: tracker.renderTrackerEntries,
      });
    },
    createTrackerControllerDepsHelpersFromApp(options = {}) {
      const {
        core = {},
        trackerCore = {},
        trackerActions = {},
        runPanels = {},
        diagnostics = {},
        trackerChange = {},
        projectRelated = {},
        adminData = {},
        constants = {},
      } = options;
      return this.createTrackerControllerDepsHelpers({
        state: core.state,
        dom: core.dom,
        window: core.window,
        api: core.api,
        flash: core.flash,
        setBusy: core.setBusy,
        FormData: core.FormData,
        escapeHtml: core.escapeHtml,
        formatDate: core.formatDate,
        syncUrlState: trackerCore.syncUrlState,
        renderTrackerEntries: trackerCore.renderTrackerEntries,
        EDITABLE_FIELDS: constants.EDITABLE_FIELDS,
        TRACKER_BOARD_BLANK_PRIORITY_FIELDS: constants.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
        patchTrackerEntry: trackerActions.patchTrackerEntry,
        syncTrackerEntryAfterPatch: trackerActions.syncTrackerEntryAfterPatch,
        readRunFiltersFromControls: runPanels.readRunFiltersFromControls,
        renderRuns: runPanels.renderRuns,
        renderRunsPagination: runPanels.renderRunsPagination,
        renderRunDetail: runPanels.renderRunDetail,
        renderRunEventStatus: runPanels.renderRunEventStatus,
        renderLogsList: runPanels.renderLogsList,
        upsertRunListItem: runPanels.upsertRunListItem,
        renderEntriesPagination: trackerCore.renderEntriesPagination,
        renderSalesSummaryPanel: diagnostics.renderSalesSummaryPanel,
        renderTrackerChangeEventsPanel: diagnostics.renderTrackerChangeEventsPanel,
        renderTrackerContactResolutionSummary: diagnostics.renderTrackerContactResolutionSummary,
        renderBackfillConflictsPanel: diagnostics.renderBackfillConflictsPanel,
        renderTrackerCleanupPreview: diagnostics.renderTrackerCleanupPreview,
        renderProjectRelatedHosts: projectRelated.renderProjectRelatedHosts,
        touchSyncMeta: trackerChange.touchSyncMeta,
        persistTrackerChangeEventsCache: trackerChange.persistTrackerChangeEventsCache,
        clearTrackerChangeEventsCache: trackerChange.clearTrackerChangeEventsCache,
        handleOutOfRangePageError: trackerCore.handleOutOfRangePageError,
        canLoadProtectedConsoleData: adminData.canLoadProtectedConsoleData,
        TRACKER_REGION_OPTIONS: constants.TRACKER_REGION_OPTIONS,
        useGlobalTrackerEntriesScope: trackerCore.useGlobalTrackerEntriesScope,
        shouldUseHomeBootstrapTrackerSnapshot: trackerCore.shouldUseHomeBootstrapTrackerSnapshot,
        isProjectTrackerRun: runPanels.isProjectTrackerRun,
        loadTrackerEntries: trackerCore.loadTrackerEntries,
        schedulePolling: runPanels.schedulePolling,
        loadWinnerRunPanels: runPanels.loadWinnerRunPanels,
        loadTrackerExportPanels: runPanels.loadTrackerExportPanels,
        loadSelectedRunLogs: runPanels.loadSelectedRunLogs,
        loadBackfillConflicts: diagnostics.loadBackfillConflicts,
        loadVisibleSalesClaims: diagnostics.loadVisibleSalesClaims,
        requireTrackerDiagnosticsRuntime: diagnostics.requireTrackerDiagnosticsRuntime,
        getTrackerController: trackerCore.getTrackerController,
        formatContactResolutionStatusLabel: diagnostics.formatContactResolutionStatusLabel,
        formatContactResolutionReasonLabel: diagnostics.formatContactResolutionReasonLabel,
        formatBackfillConflictResolutionLabel: diagnostics.formatBackfillConflictResolutionLabel,
        getTrackerDiagnosticsScope: diagnostics.getTrackerDiagnosticsScope,
        buildTrackerChangeEventsMarkup: diagnostics.buildTrackerChangeEventsMarkup,
        buildTrackerChangeBellPopoverMarkup: diagnostics.buildTrackerChangeBellPopoverMarkup,
        buildBackfillConflictsMarkup: diagnostics.buildBackfillConflictsMarkup,
        buildBackfillConflictsView: diagnostics.buildBackfillConflictsView,
        focusTrackerChangeEntry: trackerChange.focusTrackerChangeEntry,
        closeTrackerChangeModal: trackerChange.closeTrackerChangeModal,
        clearProjectRelatedRefresh: projectRelated.clearProjectRelatedRefresh,
        maybeScheduleProjectRelatedRefresh: projectRelated.maybeScheduleProjectRelatedRefresh,
        canReuseProjectRelatedPayload: projectRelated.canReuseProjectRelatedPayload,
        cacheProjectRelatedPayload: projectRelated.cacheProjectRelatedPayload,
        isProjectRelatedVisible: projectRelated.isProjectRelatedVisible,
        resolveTrackerEntryProjectId: projectRelated.resolveTrackerEntryProjectId,
        ensureTrackerEntryProjectId: projectRelated.ensureTrackerEntryProjectId,
        TRACKER_ENTRY_RUNTIME: constants.TRACKER_ENTRY_RUNTIME,
        TRACKER_DETAIL_PREFETCH_LIMIT: constants.TRACKER_DETAIL_PREFETCH_LIMIT,
        warmTrackerEntriesDownload: trackerActions.warmTrackerEntriesDownload,
        closeDrawer: trackerActions.closeDrawer,
        renderTrackerBoard: trackerActions.renderTrackerBoard,
        resetTrackerBoardEdit: trackerActions.resetTrackerBoardEdit,
        loadAdminConsoleData: adminData.loadAdminConsoleData,
        buildSelectedEntryAuditMarkup: trackerActions.buildSelectedEntryAuditMarkup,
        loadSelectedEntryDetail: trackerActions.loadSelectedEntryDetail,
        renderTrackerMissingReport: diagnostics.renderTrackerMissingReport,
        renderSelectedEntryChangeEvents: trackerActions.renderSelectedEntryChangeEvents,
        renderSelectedEntry: trackerActions.renderSelectedEntry,
        renderSelectedEntryLoading: trackerActions.renderSelectedEntryLoading,
        resolveTrackerPatchActorLabel: trackerActions.resolveTrackerPatchActorLabel,
        runTypeLabel: runPanels.runTypeLabel,
      });
    },
    createAuthControllerDepsHelpers(deps) {
      return {
        buildAuthControllerBaseDeps: () => buildAuthBaseDeps(deps),
        buildAuthControllerDeps: () => ({
          ...buildAuthBaseDeps(deps),
          renderAuthUi: deps.renderAuthUi,
          canUseAdminMode: deps.canUseAdminMode,
          canLoadProtectedConsoleData: deps.canLoadProtectedConsoleData,
          loadAdminConsoleData: deps.loadAdminConsoleData,
          loadBackfillConflicts: deps.loadBackfillConflicts,
          renderBackfillConflictsPanel: deps.renderBackfillConflictsPanel,
          renderTrackerContactResolutionSummary: deps.renderTrackerContactResolutionSummary,
          renderTrackerCleanupPreview: deps.renderTrackerCleanupPreview,
          closeDrawer: deps.closeDrawer,
          hydrateHomeBootstrapCache: deps.hydrateHomeBootstrapCache,
          clearUserModeRunSelection: deps.clearUserModeRunSelection,
          loadHomeBootstrap: deps.loadHomeBootstrap,
          loadTrackerEntries: deps.loadTrackerEntries,
          trackerController: typeof deps.getTrackerController === "function" ? deps.getTrackerController() : null,
          renderOrganizationAdminPanel: deps.renderOrganizationAdminPanel,
          renderMySalesClaimsPanel: deps.renderMySalesClaimsPanel,
          renderSalesSummaryPanel: deps.renderSalesSummaryPanel,
          renderRunDetail: deps.renderRunDetail,
          renderTrackerEntries: deps.renderTrackerEntries,
        }),
        buildAuthUiControllerDeps: () => buildAuthBaseDeps(deps),
      };
    },
    createTrackerControllerDepsHelpers(deps) {
      return {
        buildTrackerControllerBaseDeps: () => buildTrackerBaseDeps(deps),
        buildTrackerControllerDeps: () => ({
          ...buildTrackerBaseDeps(deps),
          api: deps.api,
          setBusy: deps.setBusy,
          FormData: deps.FormData,
          formatDate: deps.formatDate,
          readRunFiltersFromControls: deps.readRunFiltersFromControls,
          renderRuns: deps.renderRuns,
          renderRunsPagination: deps.renderRunsPagination,
          renderRunDetail: deps.renderRunDetail,
          renderRunEventStatus: deps.renderRunEventStatus,
          renderLogsList: deps.renderLogsList,
          upsertRunListItem: deps.upsertRunListItem,
          renderEntriesPagination: deps.renderEntriesPagination,
          renderSalesSummaryPanel: deps.renderSalesSummaryPanel,
          renderTrackerChangeEventsPanel: deps.renderTrackerChangeEventsPanel,
          renderTrackerContactResolutionSummary: deps.renderTrackerContactResolutionSummary,
          renderBackfillConflictsPanel: deps.renderBackfillConflictsPanel,
          renderTrackerCleanupPreview: deps.renderTrackerCleanupPreview,
          renderProjectRelatedHosts: deps.renderProjectRelatedHosts,
          touchSyncMeta: deps.touchSyncMeta,
          persistTrackerChangeEventsCache: deps.persistTrackerChangeEventsCache,
          clearTrackerChangeEventsCache: deps.clearTrackerChangeEventsCache,
          handleOutOfRangePageError: deps.handleOutOfRangePageError,
          canLoadProtectedConsoleData: deps.canLoadProtectedConsoleData,
          TRACKER_REGION_OPTIONS: deps.TRACKER_REGION_OPTIONS,
          useGlobalTrackerEntriesScope: deps.useGlobalTrackerEntriesScope,
          shouldUseHomeBootstrapTrackerSnapshot: deps.shouldUseHomeBootstrapTrackerSnapshot,
          isProjectTrackerRun: deps.isProjectTrackerRun,
          loadTrackerEntries: deps.loadTrackerEntries,
          schedulePolling: deps.schedulePolling,
          loadWinnerRunPanels: deps.loadWinnerRunPanels,
          loadTrackerExportPanels: deps.loadTrackerExportPanels,
          loadSelectedRunLogs: deps.loadSelectedRunLogs,
          loadBackfillConflicts: deps.loadBackfillConflicts,
          loadVisibleSalesClaims: deps.loadVisibleSalesClaims,
          requireTrackerDiagnosticsRuntime: () => (typeof deps.requireTrackerDiagnosticsRuntime === "function" ? deps.requireTrackerDiagnosticsRuntime() : null),
          clearProjectRelatedRefresh: deps.clearProjectRelatedRefresh,
          maybeScheduleProjectRelatedRefresh: deps.maybeScheduleProjectRelatedRefresh,
          canReuseProjectRelatedPayload: deps.canReuseProjectRelatedPayload,
          cacheProjectRelatedPayload: deps.cacheProjectRelatedPayload,
          isProjectRelatedVisible: deps.isProjectRelatedVisible,
          resolveTrackerEntryProjectId: deps.resolveTrackerEntryProjectId,
          ensureTrackerEntryProjectId: deps.ensureTrackerEntryProjectId,
          TRACKER_ENTRY_RUNTIME: deps.TRACKER_ENTRY_RUNTIME,
          TRACKER_DETAIL_PREFETCH_LIMIT: deps.TRACKER_DETAIL_PREFETCH_LIMIT,
          warmTrackerEntriesDownload: deps.warmTrackerEntriesDownload,
          closeDrawer: deps.closeDrawer,
          renderTrackerBoard: deps.renderTrackerBoard,
          resetTrackerBoardEdit: deps.resetTrackerBoardEdit,
          loadAdminConsoleData: deps.loadAdminConsoleData,
          buildSelectedEntryAuditMarkup: deps.buildSelectedEntryAuditMarkup,
          loadSelectedEntryDetail: deps.loadSelectedEntryDetail,
          renderTrackerMissingReport: deps.renderTrackerMissingReport,
          renderSelectedEntryChangeEvents: deps.renderSelectedEntryChangeEvents,
          renderSelectedEntry: deps.renderSelectedEntry,
          renderSelectedEntryLoading: deps.renderSelectedEntryLoading,
          resolveTrackerPatchActorLabel: deps.resolveTrackerPatchActorLabel,
          runTypeLabel: deps.runTypeLabel,
        }),
        buildTrackerEntryActionsControllerDeps: () => buildTrackerEntryActionsDeps(deps),
        buildTrackerDiagnosticsPanelControllerDeps: () => buildTrackerDiagnosticsPanelDeps(deps),
      };
    },
    createTrackerRenderControllerDepsHelpers(deps) {
      record("createTrackerRenderControllerDepsHelpers");
      if (Array.isArray(appSupportContexts)) {
        appSupportContexts.push({ helper: "trackerRender", deps });
      }
      let cached = null;
      return {
        buildTrackerRenderControllerDeps() {
          record("buildTrackerRenderControllerDeps");
          if (!cached) {
            cached = buildTrackerRenderControllerDeps(deps);
          }
          return cached;
        },
      };
    },
    createProjectRelatedControllerDepsHelpers(deps) {
      record("createProjectRelatedControllerDepsHelpers");
      if (Array.isArray(appSupportContexts)) {
        appSupportContexts.push({ helper: "projectRelated", deps });
      }
      let cached = null;
      return {
        buildProjectRelatedControllerDeps() {
          record("buildProjectRelatedControllerDeps");
          if (!cached) {
            cached = buildProjectRelatedControllerDeps(deps);
          }
          return cached;
        },
      };
    },
    createSalesPanelDepsHelpers(deps) {
      return {
        buildSalesPanelControllerDeps: () => ({
          ...deps,
          window: deps.windowObject,
        }),
      };
    },
    createDownloadControllerDepsHelpers(deps) {
      return {
        buildDownloadControllerDeps: () => buildDownloadControllerDeps(deps),
      };
    },
    createConsolePanelsControllerDepsHelpers(deps) {
      record("createConsolePanelsControllerDepsHelpers");
      return {
        buildConsolePanelsControllerDeps: () => buildConsolePanelsControllerDeps(deps),
      };
    },
    createUiModeControllerDepsHelpers(deps) {
      record("createUiModeControllerDepsHelpers");
      return {
        buildUiModeControllerDeps: () => buildUiModeControllerDeps(deps),
      };
    },
    createOrgAdminControllerDepsHelpers(deps) {
      record("createOrgAdminControllerDepsHelpers");
      if (Array.isArray(appSupportContexts)) {
        appSupportContexts.push({ helper: "orgAdminControllerDeps", deps });
      }
      let cached = null;
      return {
        buildOrgAdminControllerDeps() {
          record("buildOrgAdminControllerDeps");
          if (!cached) {
            cached = buildOrgAdminControllerDeps(deps);
          }
          return cached;
        },
      };
    },
    createAdminGoogleSheetsControllerDepsHelpers(deps) {
      record("createAdminGoogleSheetsControllerDepsHelpers");
      return {
        buildAdminGoogleSheetsControllerDeps: () => buildAdminGoogleSheetsControllerDeps(deps),
      };
    },
    createRuntimeEnhancementsDepsHelpers(deps) {
      record("createRuntimeEnhancementsDepsHelpers");
      return {
        buildRuntimeEnhancementsDeps: () => buildRuntimeEnhancementsDeps(deps),
      };
    },
    createSelectedEntryControllerDepsHelpers(deps) {
      return {
        buildSelectedEntryControllerDeps: () => buildSelectedEntryControllerDeps(deps),
      };
    },
    createRunPanelsControllerDepsHelpers(deps) {
      record("createRunPanelsControllerDepsHelpers");
      return {
        buildRunPanelsControllerDeps: () => buildRunPanelsControllerDeps(deps),
      };
    },
    createReportPanelsControllerDepsHelpers(deps) {
      record("createReportPanelsControllerDepsHelpers");
      return {
        buildReportPanelsControllerDeps: () => buildReportPanelsControllerDeps(deps),
      };
    },
  };
}

function createAuthControllerHarnessGlobals() {
  return {
    renderAuthUi: () => {},
    canUseAdminMode: () => false,
    canLoadProtectedConsoleData: () => true,
    loadAdminConsoleData: async () => {},
    loadBackfillConflicts: async () => {},
    renderBackfillConflictsPanel: () => {},
    renderTrackerContactResolutionSummary: () => {},
    renderTrackerCleanupPreview: () => {},
    closeDrawer: () => {},
    hydrateHomeBootstrapCache: () => {},
    clearUserModeRunSelection: () => {},
    loadHomeBootstrap: async () => {},
    loadTrackerEntries: async () => {},
    getTrackerController: () => ({ runtime: true }),
    renderOrganizationAdminPanel: () => {},
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderRunDetail: () => {},
    renderTrackerEntries: () => {},
  };
}

function createTrackerControllerHarnessGlobals() {
  const noop = () => {};
  return {
    api: async () => {
      throw new Error("api should not run in tracker delegation test");
    },
    setBusy: noop,
    FormData: class FormData {},
    formatDate: (value) => String(value ?? ""),
    readRunFiltersFromControls: noop,
    renderRuns: noop,
    renderRunsPagination: noop,
    renderRunDetail: noop,
    renderRunEventStatus: noop,
    renderLogsList: noop,
    upsertRunListItem: noop,
    renderEntriesPagination: noop,
    renderSalesSummaryPanel: noop,
    renderTrackerChangeEventsPanel: noop,
    renderTrackerContactResolutionSummary: noop,
    renderBackfillConflictsPanel: noop,
    renderTrackerCleanupPreview: noop,
    renderProjectRelatedHosts: noop,
    touchSyncMeta: noop,
    persistTrackerChangeEventsCache: noop,
    clearTrackerChangeEventsCache: noop,
    handleOutOfRangePageError: () => false,
    canLoadProtectedConsoleData: () => true,
    TRACKER_REGION_OPTIONS: [],
    useGlobalTrackerEntriesScope: () => false,
    shouldUseHomeBootstrapTrackerSnapshot: () => false,
    isProjectTrackerRun: () => false,
    schedulePolling: noop,
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    loadBackfillConflicts: async () => {},
    loadVisibleSalesClaims: async () => {},
    loadTrackerEntries: async () => {},
    getTrackerController: () => ({ runtime: true }),
    EDITABLE_FIELDS: ["project_name"],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact"]),
    formatContactResolutionStatusLabel: (value) => String(value ?? ""),
    formatContactResolutionReasonLabel: (value) => String(value ?? ""),
    formatBackfillConflictResolutionLabel: (value) => String(value ?? ""),
    getTrackerDiagnosticsScope: () => ({ trackerRunId: "run-1" }),
    buildTrackerChangeEventsMarkup: noop,
    buildTrackerChangeBellPopoverMarkup: noop,
    buildBackfillConflictsMarkup: noop,
    buildBackfillConflictsView: () => ({ html: "" }),
    focusTrackerChangeEntry: async () => {},
    closeTrackerChangeModal: noop,
    patchTrackerEntry: async () => {},
    syncTrackerEntryAfterPatch: async () => {},
    requireTrackerDiagnosticsRuntime: () => ({}),
    clearProjectRelatedRefresh: noop,
    maybeScheduleProjectRelatedRefresh: noop,
    canReuseProjectRelatedPayload: () => false,
    cacheProjectRelatedPayload: () => null,
    isProjectRelatedVisible: () => false,
    resolveTrackerEntryProjectId: () => null,
    ensureTrackerEntryProjectId: async () => null,
    TRACKER_ENTRY_RUNTIME: null,
    TRACKER_DETAIL_PREFETCH_LIMIT: 3,
    warmTrackerEntriesDownload: async () => {},
    closeDrawer: noop,
    renderTrackerBoard: noop,
    resetTrackerBoardEdit: noop,
    loadAdminConsoleData: async () => {},
    buildSelectedEntryAuditMarkup: () => "",
    loadSelectedEntryDetail: async () => {},
    renderTrackerMissingReport: noop,
    renderSelectedEntryChangeEvents: noop,
    renderSelectedEntry: noop,
    renderSelectedEntryLoading: noop,
    resolveTrackerPatchActorLabel: () => "",
    runTypeLabel: (value) => String(value ?? ""),
  };
}

function extractFunction(source, startSignature, nextSignature) {
  const start = source.indexOf(startSignature);
  assert.notEqual(start, -1, `missing ${startSignature}`);
  const end = nextSignature ? source.indexOf(nextSignature, start + startSignature.length) : -1;
  assert.notEqual(end, -1, `missing ${nextSignature}`);
  const snippet = source.slice(start, end);
  if (!startSignature.startsWith("function get")) {
    return snippet;
  }
  const helperStartSignature = "function createControllerWithWiringDeps({";
  const helperEndSignature = "function getAdminGoogleSheetsController() {";
  const helperStart = source.indexOf(helperStartSignature);
  assert.notEqual(helperStart, -1, `missing ${helperStartSignature}`);
  const helperEnd = source.indexOf(helperEndSignature, helperStart + helperStartSignature.length);
  assert.notEqual(helperEnd, -1, `missing ${helperEndSignature}`);
  const helperSource = source.slice(helperStart, helperEnd);
  let extraHelperSource = "";
  if (snippet.includes("getAuthControllerBaseDeps(")) {
    const authHelperStartSignature = "function getAuthControllerBaseDeps() {";
    const authHelperEndSignature = "function getAuthController() {";
    const authHelperStart = source.indexOf(authHelperStartSignature);
    assert.notEqual(authHelperStart, -1, `missing ${authHelperStartSignature}`);
    const authHelperEnd = source.indexOf(authHelperEndSignature, authHelperStart + authHelperStartSignature.length);
    assert.notEqual(authHelperEnd, -1, `missing ${authHelperEndSignature}`);
    extraHelperSource = `${source.slice(authHelperStart, authHelperEnd)}\n`;
  }
  if (snippet.includes("getTrackerControllerBaseDeps(")) {
    const trackerHelperStartSignature = "function getTrackerControllerBaseDeps() {";
    const trackerHelperEndSignature = "function getTrackerController() {";
    const trackerHelperStart = source.indexOf(trackerHelperStartSignature);
    assert.notEqual(trackerHelperStart, -1, `missing ${trackerHelperStartSignature}`);
    const trackerHelperEnd = source.indexOf(trackerHelperEndSignature, trackerHelperStart + trackerHelperStartSignature.length);
    assert.notEqual(trackerHelperEnd, -1, `missing ${trackerHelperEndSignature}`);
    extraHelperSource = `${extraHelperSource}${source.slice(trackerHelperStart, trackerHelperEnd)}\n`;
  }
  if (snippet.includes("getAuthControllerDepsHelpers(")) {
    const authDepsHelperStartSignature = "function getAuthControllerDepsHelpers() {";
    const authDepsHelperEndSignature = "function getAuthController() {";
    const authDepsHelperStart = source.indexOf(authDepsHelperStartSignature);
    assert.notEqual(authDepsHelperStart, -1, `missing ${authDepsHelperStartSignature}`);
    const authDepsHelperEnd = source.indexOf(authDepsHelperEndSignature, authDepsHelperStart + authDepsHelperStartSignature.length);
    assert.notEqual(authDepsHelperEnd, -1, `missing ${authDepsHelperEndSignature}`);
    extraHelperSource = `${extraHelperSource}${source.slice(authDepsHelperStart, authDepsHelperEnd)}\n`;
  }
  if (snippet.includes("getTrackerControllerDepsHelpers(")) {
    const trackerDepsHelperStartSignature = "function getTrackerControllerDepsHelpers() {";
    const trackerDepsHelperEndSignature = "function getTrackerController() {";
    const trackerDepsHelperStart = source.indexOf(trackerDepsHelperStartSignature);
    assert.notEqual(trackerDepsHelperStart, -1, `missing ${trackerDepsHelperStartSignature}`);
    const trackerDepsHelperEnd = source.indexOf(trackerDepsHelperEndSignature, trackerDepsHelperStart + trackerDepsHelperStartSignature.length);
    assert.notEqual(trackerDepsHelperEnd, -1, `missing ${trackerDepsHelperEndSignature}`);
    extraHelperSource = `${extraHelperSource}${source.slice(trackerDepsHelperStart, trackerDepsHelperEnd)}\n`;
  }
  if (snippet.includes("getSalesPanelDepsHelpers(")) {
    const salesHelperStartSignature = "function getSalesPanelDepsHelpers() {";
    const salesHelperEndSignature = "function buildSalesOverviewStorageIdentity() {";
    const salesHelperStart = source.indexOf(salesHelperStartSignature);
    assert.notEqual(salesHelperStart, -1, `missing ${salesHelperStartSignature}`);
    const salesHelperEnd = source.indexOf(salesHelperEndSignature, salesHelperStart + salesHelperStartSignature.length);
    assert.notEqual(salesHelperEnd, -1, `missing ${salesHelperEndSignature}`);
    extraHelperSource = `${extraHelperSource}${source.slice(salesHelperStart, salesHelperEnd)}\n`;
  }
  return `${helperSource}\n${extraHelperSource}${snippet}`;
}

function normalizeWhitespace(source) {
  return source.replace(/\s+/g, " ").trim();
}

function createAuthUiHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getAuthUiController() {",
    "function getSalesPanelController() {",
  );
  const wrapperSource = [
    extractFunction(source, "function applyAuthSession(session) {", "async function performAuthSessionRefresh("),
    extractFunction(source, "function syncAuthFormWithInvitationPreview() {", "function renderAuthInvitationPreview() {"),
    extractFunction(source, "function renderAuthInvitationPreview() {", "function renderAuthUi() {"),
    extractFunction(source, "function renderAuthUi() {", "function formatContractAmountInput(rawValue) {"),
    extractFunction(source, "function renderProfileStatus(message = \"\", level = \"\") {", "function renderInvitationStatus(message = \"\", level = \"\") {"),
    extractFunction(source, "function syncProfileDialogWithSession() {", "function openProfileDialog() {"),
    extractFunction(source, "function openProfileDialog() {", "function closeProfileDialog() {"),
    extractFunction(source, "function closeProfileDialog() {", "async function handleProfileSubmit(event) {"),
    extractFunction(source, "async function handleProfileSubmit(event) {", "async function handleAuthSubmit(event) {"),
    extractFunction(source, "async function handleAuthSubmit(event) {", "function handleAuthFindId() {"),
    extractFunction(source, "function handleAuthFindId() {", "async function handleAuthPasswordReset() {"),
    extractFunction(source, "async function handleAuthPasswordReset() {", "async function handleAuthSignOut() {"),
    extractFunction(source, "async function handleAuthSignOut() {", "function extractDownloadFilename(response, fallbackName) {"),
  ].join("\n");

  const calls = [];
  let factoryDeps = null;
  const controller = {
    applyAuthSession(session) {
      calls.push(["applyAuthSession", session]);
      return { ok: "applyAuthSession" };
    },
    syncAuthFormWithInvitationPreview() {
      calls.push(["syncAuthFormWithInvitationPreview"]);
      return { ok: "syncAuthFormWithInvitationPreview" };
    },
    renderAuthInvitationPreview() {
      calls.push(["renderAuthInvitationPreview"]);
      return { ok: "renderAuthInvitationPreview" };
    },
    renderAuthUi() {
      calls.push(["renderAuthUi"]);
      return { ok: "renderAuthUi" };
    },
    renderProfileStatus(message, level) {
      calls.push(["renderProfileStatus", message, level]);
      return { ok: "renderProfileStatus" };
    },
    syncProfileDialogWithSession() {
      calls.push(["syncProfileDialogWithSession"]);
      return { ok: "syncProfileDialogWithSession" };
    },
    openProfileDialog() {
      calls.push(["openProfileDialog"]);
      return { ok: "openProfileDialog" };
    },
    closeProfileDialog() {
      calls.push(["closeProfileDialog"]);
      return { ok: "closeProfileDialog" };
    },
    async handleProfileSubmit(event) {
      calls.push(["handleProfileSubmit", event]);
      return { ok: "handleProfileSubmit" };
    },
    async handleAuthSubmit(event) {
      calls.push(["handleAuthSubmit", event]);
      return { ok: "handleAuthSubmit" };
    },
    handleAuthFindId() {
      calls.push(["handleAuthFindId"]);
      return { ok: "handleAuthFindId" };
    },
    async handleAuthPasswordReset() {
      calls.push(["handleAuthPasswordReset"]);
      return { ok: "handleAuthPasswordReset" };
    },
    async handleAuthSignOut() {
      calls.push(["handleAuthSignOut"]);
      return { ok: "handleAuthSignOut" };
    },
  };
  let factoryCalls = 0;

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    ...createAuthControllerHarnessGlobals(),
    window: {
      AUTH_UI_CONTROLLER: {
        createAuthUiController(deps) {
          factoryCalls += 1;
          factoryDeps = deps;
          calls.push(["factory", deps]);
          return controller;
        },
      },
    },
    authUiController: null,
    state: { auth: {}, profileDialog: {} },
    dom: {},
    document: {},
    api: async () => {
      throw new Error("api should not run in auth-ui delegation test");
    },
    flash() {},
    setBusy() {},
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    requireAuthSessionRuntime: () => ({ runtime: true }),
    loadOrganizationUsers: async () => {},
    loadOrganizationMembers: async () => {},
    loadSalesOverview: async () => {},
    loadMySalesClaims: async () => {},
    refreshSalesAdminPanels: async () => {},
    ensureConsoleInitialized: async () => {},
    shouldShowSignUpMode: () => true,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    syncUiModeChrome: () => false,
    applyUiModeTransition() {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return {
    context,
    calls,
    get factoryCalls() {
      return factoryCalls;
    },
    get factoryDeps() {
      return factoryDeps;
    },
  };
}

function assertAuthUiControllerDeps(deps, context) {
  const expectedKeys = [
    "state",
    "dom",
    "document",
    "window",
    "api",
    "flash",
    "setBusy",
    "escapeHtml",
    "formatOrgRoleLabel",
    "formatInvitationStatusLabel",
    "formatSalesDateLabel",
    "formatMembershipStatusLabel",
    "requireAuthSessionRuntime",
    "loadOrganizationUsers",
    "loadOrganizationMembers",
    "loadSalesOverview",
    "loadMySalesClaims",
    "refreshSalesAdminPanels",
    "ensureConsoleInitialized",
    "shouldShowSignUpMode",
    "AUTH_MODE_SIGN_IN",
    "AUTH_MODE_SIGN_UP",
    "syncUiModeChrome",
    "applyUiModeTransition",
  ];

  assert.deepEqual(Object.keys(deps).sort(), [...expectedKeys].sort());
  for (const key of expectedKeys) {
    if (key === "syncUiModeChrome" || key === "applyUiModeTransition") {
      assert.equal(typeof deps[key], "function", `unexpected auth ui dependency type for ${key}`);
      continue;
    }
    assert.strictEqual(deps[key], context[key], `unexpected auth ui dependency for ${key}`);
  }
}

function assertAdminGoogleSheetsControllerDeps(deps, context) {
  const expectedKeys = [
    "state",
    "dom",
    "window",
    "api",
    "flash",
    "renderAdminTopNavigation",
    "renderAdminEmbedPanel",
    "canLoadProtectedConsoleData",
    "maybeResolveLegacyAdminAliasToSheetTab",
    "getValidatedActiveAdminGoogleSheetTab",
    "isAdminGoogleSheetTabKey",
    "isPendingLegacyAdminAlias",
    "shouldDeferAdminGoogleSheetPayloadLoad",
    "clearAdminGoogleSheetPopupStateForTab",
    "syncUrlState",
    "applyUiMode",
    "persistAdminGoogleSheetsCache",
    "googleSheetsRuntime",
    "defaultAdminTab",
  ];

  assert.deepEqual(Object.keys(deps).sort(), [...expectedKeys].sort());
  for (const key of expectedKeys) {
    const expectedValue = key === "googleSheetsRuntime"
      ? context.ADMIN_GOOGLE_SHEETS_RUNTIME
      : key === "defaultAdminTab"
        ? context.DEFAULT_ADMIN_TAB
        : context[key];
    assert.strictEqual(deps[key], expectedValue, `unexpected admin google sheets dependency for ${key}`);
  }
}

function createTrackerRenderHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerRenderController() {",
    "function getTrackerController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      "function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {",
      "function renderTrackerEntriesFallback(entries, { refreshSelectedEntry = true } = {}) {",
    ),
    extractFunction(
      source,
      "function renderTrackerBoard(entries) {",
      "function renderTrackerBoardFallback(entries) {",
    ),
  ].join("\n");

  const expectedKeys = [
    "dom",
    "state",
    "escapeHtml",
    "formatKoreanDate",
    "formatBuildingAutomationEstimateValue",
    "TRACKER_ENTRY_RUNTIME",
    "buildTrackerBoardEmptyStateView",
    "buildTrackerBoardMarkup",
    "buildTrackerEntryCardMarkupFallback",
    "renderSalesClaimSection",
    "renderTrackerEntryRelatedNotices",
    "resetTrackerBoardEdit",
    "renderSelectedEntry",
    "buildTrackerEntrySummaryDetail",
    "loadSelectedEntryDetail",
    "toggleTrackerEntryRelated",
    "openTrackerEntryNoticeViewer",
    "bindRelatedNoticeViewerButtons",
    "claimSalesProject",
    "setSalesNoteDraft",
    "saveSalesClaimNote",
    "transferSalesClaim",
    "flash",
    "openSalesCloseDialog",
    "closeSalesClaim",
    "releaseSalesClaim",
    "syncUrlState",
    "prefetchTrackerEntryDetails",
    "getSalesClaimForProject",
    "getSortedTrackerBoardEntries",
    "TRACKER_BOARD_COLUMNS",
    "renderTrackerBoardHeaderCell",
    "renderTrackerBoardCell",
    "toggleTrackerBoardBlankPriority",
    "beginTrackerBoardEdit",
    "saveTrackerBoardEdit",
  ];

  const factoryCalls = [];
  const appSupportCalls = [];
  const appSupportContexts = [];
  let capturedHelperContext = null;
  let capturedFactoryDeps = null;
  const controller = {
    renderTrackerEntries(entries, options) {
      factoryCalls.push(["renderTrackerEntries", entries, options]);
      return { ok: "renderTrackerEntries" };
    },
    renderTrackerBoard(entries) {
      factoryCalls.push(["renderTrackerBoard", entries]);
      return { ok: "renderTrackerBoard" };
    },
  };

  const context = vm.createContext({
    console,
    trackerRenderController: null,
    APP_SUPPORT: createAppSupportStub(appSupportCalls, appSupportContexts),
    window: {
      TRACKER_RENDER_CONTROLLER: {
        createTrackerRenderController(deps) {
          factoryCalls.push(["factory", deps]);
          return controller;
        },
      },
      SPMSAppControllerWiringRuntime: {
        createTrackerRenderControllerDeps(deps) {
          factoryCalls.push(["helper", deps]);
          capturedHelperContext = deps;
          assert.deepEqual(Object.keys(deps).sort(), [...expectedKeys].sort());
          return deps;
        },
      },
    },
    dom: { tracker: true },
    state: { tracker: true },
    escapeHtml: () => "",
    formatKoreanDate: () => "",
    formatBuildingAutomationEstimateValue: () => "",
    TRACKER_ENTRY_RUNTIME: { runtime: true },
    buildTrackerBoardEmptyStateView: () => "",
    buildTrackerBoardMarkup: () => "",
    buildTrackerEntryCardMarkupFallback: () => "",
    renderSalesClaimSection: () => "",
    renderTrackerEntryRelatedNotices: () => "",
    resetTrackerBoardEdit: () => {},
    renderSelectedEntry: () => "",
    buildTrackerEntrySummaryDetail: () => "",
    loadSelectedEntryDetail: () => Promise.resolve(),
    toggleTrackerEntryRelated: () => {},
    openTrackerEntryNoticeViewer: () => {},
    bindRelatedNoticeViewerButtons: () => {},
    claimSalesProject: async () => {},
    setSalesNoteDraft: () => {},
    saveSalesClaimNote: async () => {},
    transferSalesClaim: async () => {},
    flash: () => {},
    openSalesCloseDialog: () => {},
    closeSalesClaim: async () => {},
    releaseSalesClaim: async () => {},
    syncUrlState: () => {},
    prefetchTrackerEntryDetails: async () => {},
    getSalesClaimForProject: () => null,
    sortTrackerBoardEntries: () => [],
    TRACKER_BOARD_COLUMNS: [],
    renderTrackerBoardHeaderCell: () => "",
    renderTrackerBoardCell: () => "",
    toggleTrackerBoardBlankPriority: () => {},
    beginTrackerBoardEdit: () => {},
    saveTrackerBoardEdit: async () => {},
    renderTrackerEntriesFallback: () => {
      throw new Error("renderTrackerEntriesFallback should not run");
    },
    renderTrackerBoardFallback: () => {
      throw new Error("renderTrackerBoardFallback should not run");
    },
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const wiringRuntime = context.window.SPMSAppControllerWiringRuntime;
  const actualCreateTrackerRenderControllerDeps = wiringRuntime.createTrackerRenderControllerDeps;
  wiringRuntime.createTrackerRenderControllerDeps = (deps) => {
    factoryCalls.push(["helper", deps]);
    capturedHelperContext = deps;
    assert.deepEqual(Object.keys(deps).sort(), [...expectedKeys].sort());
    capturedFactoryDeps = actualCreateTrackerRenderControllerDeps(deps);
    return capturedFactoryDeps;
  };
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });

  return {
    context,
    factoryCalls,
    appSupportCalls,
    appSupportContexts,
    get capturedHelperContext() {
      return capturedHelperContext;
    },
    get capturedFactoryDeps() {
      return capturedFactoryDeps;
    },
  };
}

test("getTrackerRenderController uses the wiring helper, preserves deps identity, and caches the controller", () => {
  const harness = createTrackerRenderHarness();
  const { context, factoryCalls, appSupportCalls, appSupportContexts } = harness;

  assert.strictEqual(context.getTrackerRenderController(), context.getTrackerRenderController());
  assert.deepEqual(appSupportCalls, [
    "createTrackerRenderControllerDepsHelpers",
    "buildTrackerRenderControllerDeps",
  ]);
  assert.equal(appSupportContexts.length, 1);
  assert.deepEqual(Object.keys(appSupportContexts[0].deps).sort(), [
    "selectedEntryActions",
    "sharedDeps",
    "trackerBoardActions",
    "trackerSalesActions",
  ]);
  assert.strictEqual(factoryCalls.filter(([type]) => type === "helper").length, 1);
  assert.strictEqual(factoryCalls.filter(([type]) => type === "factory").length, 1);
  assert.strictEqual(harness.capturedHelperContext, factoryCalls.find(([type]) => type === "helper")[1]);
  assert.strictEqual(harness.capturedFactoryDeps, factoryCalls.find(([type]) => type === "factory")[1]);
  assert.notStrictEqual(harness.capturedFactoryDeps, harness.capturedHelperContext);
  assert.strictEqual(harness.capturedHelperContext.dom, context.dom);
  assert.strictEqual(harness.capturedHelperContext.state, context.state);
  assert.strictEqual(harness.capturedHelperContext.escapeHtml, context.escapeHtml);
  assert.strictEqual(harness.capturedHelperContext.formatKoreanDate, context.formatKoreanDate);
  assert.strictEqual(harness.capturedHelperContext.formatBuildingAutomationEstimateValue, context.formatBuildingAutomationEstimateValue);
  assert.strictEqual(harness.capturedHelperContext.flash, context.flash);
  assert.strictEqual(harness.capturedHelperContext.getSortedTrackerBoardEntries, context.sortTrackerBoardEntries);
  assert.strictEqual(harness.capturedHelperContext.TRACKER_BOARD_COLUMNS, context.TRACKER_BOARD_COLUMNS);
  assert.strictEqual(harness.capturedHelperContext.renderSalesClaimSection, context.renderSalesClaimSection);
  assert.strictEqual(harness.capturedHelperContext.openTrackerEntryNoticeViewer, context.openTrackerEntryNoticeViewer);
  assert.strictEqual(harness.capturedHelperContext.claimSalesProject, context.claimSalesProject);
  assert.strictEqual(harness.capturedFactoryDeps.getSortedTrackerBoardEntries, context.sortTrackerBoardEntries);
  assert.strictEqual(harness.capturedFactoryDeps.renderSalesClaimSection, context.renderSalesClaimSection);
  assert.ok(!("buildSortedTrackerBoardEntries" in harness.capturedFactoryDeps));

  assert.doesNotThrow(() => context.renderTrackerEntries([{ id: 1 }]));
  assert.doesNotThrow(() => context.renderTrackerBoard([{ id: 1 }]));
  assert.doesNotThrow(() => context.renderTrackerEntries([{ id: 2 }]));
  assert.doesNotThrow(() => context.renderTrackerBoard([{ id: 2 }]));

  assert.strictEqual(factoryCalls.filter(([type]) => type === "factory").length, 1);
  assert.strictEqual(factoryCalls.filter(([type]) => type === "helper").length, 1);
  assert.strictEqual(factoryCalls.filter(([type]) => type === "renderTrackerEntries").length, 2);
  assert.strictEqual(factoryCalls.filter(([type]) => type === "renderTrackerBoard").length, 2);
});

test("getTrackerRenderController fails fast when wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerRenderController() {",
    "function getTrackerController() {",
  );
  const context = vm.createContext({
    console,
    trackerRenderController: null,
    window: {
      TRACKER_RENDER_CONTROLLER: {
        createTrackerRenderController() {
          throw new Error("factory should not run");
        },
      },
    },
    dom: {},
    state: {},
    escapeHtml: () => "",
    formatKoreanDate: () => "",
    formatBuildingAutomationEstimateValue: () => "",
    TRACKER_ENTRY_RUNTIME: {},
    buildTrackerBoardEmptyStateView: () => "",
    buildTrackerBoardMarkup: () => "",
    buildTrackerEntryCardMarkupFallback: () => "",
    renderSalesClaimSection: () => "",
    renderTrackerEntryRelatedNotices: () => "",
    resetTrackerBoardEdit: () => {},
    renderSelectedEntry: () => "",
    buildTrackerEntrySummaryDetail: () => "",
    loadSelectedEntryDetail: () => {},
    toggleTrackerEntryRelated: () => {},
    openTrackerEntryNoticeViewer: () => {},
    bindRelatedNoticeViewerButtons: () => {},
    claimSalesProject: () => {},
    setSalesNoteDraft: () => {},
    saveSalesClaimNote: () => {},
    transferSalesClaim: () => {},
    flash: () => {},
    openSalesCloseDialog: () => {},
    closeSalesClaim: () => {},
    releaseSalesClaim: () => {},
    syncUrlState: () => {},
    prefetchTrackerEntryDetails: () => {},
    getSalesClaimForProject: () => null,
    sortTrackerBoardEntries: () => [],
    TRACKER_BOARD_COLUMNS: [],
    renderTrackerBoardHeaderCell: () => "",
    renderTrackerBoardCell: () => "",
    toggleTrackerBoardBlankPriority: () => {},
    beginTrackerBoardEdit: () => {},
    saveTrackerBoardEdit: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });

  assert.throws(() => context.getTrackerRenderController(), /SPMSAppControllerWiringRuntime is required before app\.js loads/);
});

function createProjectRelatedHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getProjectRelatedController() {",
    "function getTrackerController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      "function hydrateProjectRelatedPayloadCache() {",
      "function persistProjectRelatedPayloadCache() {",
    ),
    extractFunction(
      source,
      "function persistProjectRelatedPayloadCache() {",
      "function buildSalesOverviewStorageIdentity() {",
    ),
    extractFunction(
      source,
      "async function openRelatedNoticeViewer(item) {",
      "async function openProjectNoticeViewer(project) {",
    ),
    extractFunction(
      source,
      "async function openProjectNoticeViewer(project) {",
      "function buildProjectNoticeUrl(project) {",
    ),
    extractFunction(
      source,
      "async function openTrackerEntryNoticeViewer(entryId, entries = state.trackerEntries) {",
      "function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = \"공고문\") {",
    ),
    extractFunction(
      source,
      "function renderRelatedProjectNotices(project) {",
      "function prefetchProjectRelatedNotices(projectIds) {",
    ),
    extractFunction(
      source,
      "function resolveTrackerEntryProjectId(entryId) {",
      "function renderSalesClaimSection(entry) {",
    ),
  ].join("\n");

  const expectedKeys = [
    "state",
    "window",
    "api",
    "flash",
    "escapeHtml",
    "RELATED_NOTICE_RUNTIME",
    "PROJECT_RELATED_READY_CACHE_TTL_MS",
    "PROJECT_RELATED_SEED_CACHE_TTL_MS",
    "PROJECT_RELATED_STORAGE_KEY",
    "PROJECT_RELATED_STORAGE_MAX_ITEMS",
    "renderNoticeViewerWindow",
    "renderNoticeViewerPayload",
    "renderNoticeViewerError",
    "renderProjects",
    "renderTrackerEntries",
    "loadProjectRelatedNotices",
    "loadSelectedEntryDetail",
  ];

  const calls = [];
  let capturedHelperContext = null;
  let capturedFactoryDeps = null;
  const state = { trackerEntries: [{ id: "entry-1" }] };
  const cachedByProject = new Map();
  const controller = {
    openRelatedNoticeViewer(item) {
      calls.push(["openRelatedNoticeViewer", item]);
      return "open-related";
    },
    openProjectNoticeViewer(project) {
      calls.push(["openProjectNoticeViewer", project]);
      return "open-project";
    },
    openTrackerEntryNoticeViewer(entryId, entries) {
      calls.push(["openTrackerEntryNoticeViewer", entryId, entries]);
      return "open-tracker-entry";
    },
    hydrateProjectRelatedPayloadCache() {
      calls.push(["hydrateProjectRelatedPayloadCache"]);
      return "hydrate-project-related";
    },
    persistProjectRelatedPayloadCache() {
      calls.push(["persistProjectRelatedPayloadCache"]);
      return "persist-project-related";
    },
    renderRelatedProjectNotices(project) {
      calls.push(["renderRelatedProjectNotices", project]);
      return "render-related-project-notices";
    },
    renderTrackerEntryRelatedNotices(entry) {
      calls.push(["renderTrackerEntryRelatedNotices", entry]);
      return "render-tracker-entry-related-notices";
    },
    renderRelatedNoticePanel(projectId) {
      calls.push(["renderRelatedNoticePanel", projectId]);
      return `panel:${projectId}`;
    },
    bindRelatedNoticeViewerButtons(root) {
      calls.push(["bindRelatedNoticeViewerButtons", root]);
      return "bind-buttons";
    },
    renderProjectRelatedHosts() {
      calls.push(["renderProjectRelatedHosts"]);
      return "render-project-related-hosts";
    },
    clearProjectRelatedRefresh(projectId) {
      calls.push(["clearProjectRelatedRefresh", projectId]);
      return `cleared:${projectId || ""}`;
    },
    maybeScheduleProjectRelatedRefresh(projectId) {
      calls.push(["maybeScheduleProjectRelatedRefresh", projectId]);
      return `scheduled:${projectId}`;
    },
    canReuseProjectRelatedPayload(payload) {
      calls.push(["canReuseProjectRelatedPayload", payload]);
      return payload?.status === "ready" && payload?.__cachedAt === 123;
    },
    cacheProjectRelatedPayload(projectId, payload) {
      calls.push(["cacheProjectRelatedPayload", projectId, payload]);
      if (cachedByProject.has(projectId)) {
        return cachedByProject.get(projectId);
      }
      const cached = { ...payload, __cachedAt: 123, projectId };
      cachedByProject.set(projectId, cached);
      return cached;
    },
    resolveTrackerEntryProjectId(entryId) {
      calls.push(["resolveTrackerEntryProjectId", entryId]);
      return `project-for-${entryId}`;
    },
    async ensureTrackerEntryProjectId(entryId) {
      calls.push(["ensureTrackerEntryProjectId", entryId]);
      return `ensured-${entryId}`;
    },
  };

  const appSupportCalls = [];
  const appSupportContexts = [];
  const context = vm.createContext({
    console,
    projectRelatedController: null,
    APP_SUPPORT: createAppSupportStub(appSupportCalls, appSupportContexts),
    state,
    window: {
      PROJECT_RELATED_CONTROLLER: {
        createProjectRelatedController(deps) {
          calls.push(["factory", deps]);
          return controller;
        },
      },
    },
    api: async () => ({ ok: true }),
    flash: () => {},
    escapeHtml: (value) => String(value ?? ""),
    RELATED_NOTICE_RUNTIME: { runtime: true },
    PROJECT_RELATED_READY_CACHE_TTL_MS: 5 * 60 * 1000,
    PROJECT_RELATED_SEED_CACHE_TTL_MS: 60 * 1000,
    PROJECT_RELATED_STORAGE_KEY: "notice-winner-pipeline-web.projectRelatedCache.v1",
    PROJECT_RELATED_STORAGE_MAX_ITEMS: 80,
    renderNoticeViewerWindow: () => {},
    renderNoticeViewerPayload: () => {},
    renderNoticeViewerError: () => {},
    renderProjects: () => {},
    renderTrackerEntries: () => {},
    loadProjectRelatedNotices: async () => {},
    loadSelectedEntryDetail: async () => null,
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const wiringRuntime = context.window.SPMSAppControllerWiringRuntime;
  const actualCreateProjectRelatedControllerDeps = wiringRuntime.createProjectRelatedControllerDeps;
  wiringRuntime.createProjectRelatedControllerDeps = (deps) => {
    calls.push(["helper", deps]);
    capturedHelperContext = deps;
    assert.deepEqual(Object.keys(deps).sort(), [...expectedKeys].sort());
    capturedFactoryDeps = actualCreateProjectRelatedControllerDeps(deps);
    return capturedFactoryDeps;
  };
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });

  return {
    context,
    calls,
    appSupportCalls,
    appSupportContexts,
    state,
    controller,
    get capturedHelperContext() {
      return capturedHelperContext;
    },
    get capturedFactoryDeps() {
      return capturedFactoryDeps;
    },
  };
}

test("app.js delegates project-related notice wrappers through a cached controller", async () => {
  const harness = createProjectRelatedHarness();
  const { context, calls, appSupportCalls, appSupportContexts, state, controller } = harness;

  const controllerA = context.getProjectRelatedController();
  const controllerB = context.getProjectRelatedController();
  assert.strictEqual(controllerA, controller);
  assert.strictEqual(controllerB, controller);
  assert.strictEqual(controllerA, controllerB);
  assert.deepEqual(appSupportCalls, [
    "createProjectRelatedControllerDepsHelpers",
    "buildProjectRelatedControllerDeps",
  ]);
  assert.equal(appSupportContexts.length, 1);
  assert.deepEqual(Object.keys(appSupportContexts[0].deps).sort(), [
    "noticeViewerRenderers",
    "projectRelatedActions",
    "projectRelatedConfig",
    "sharedDeps",
  ]);
  assert.strictEqual(calls.filter(([type]) => type === "helper").length, 1);
  assert.strictEqual(calls.filter(([type]) => type === "factory").length, 1);
  assert.strictEqual(harness.capturedHelperContext, calls.find(([type]) => type === "helper")[1]);
  assert.strictEqual(harness.capturedFactoryDeps, calls.find(([type]) => type === "factory")[1]);
  assert.notStrictEqual(harness.capturedFactoryDeps, harness.capturedHelperContext);
  assert.strictEqual(harness.capturedHelperContext.state, state);
  assert.strictEqual(harness.capturedHelperContext.window, context.window);
  assert.strictEqual(harness.capturedHelperContext.api, context.api);
  assert.strictEqual(harness.capturedHelperContext.flash, context.flash);
  assert.strictEqual(harness.capturedHelperContext.RELATED_NOTICE_RUNTIME, context.RELATED_NOTICE_RUNTIME);
  assert.strictEqual(harness.capturedHelperContext.PROJECT_RELATED_STORAGE_KEY, context.PROJECT_RELATED_STORAGE_KEY);
  assert.strictEqual(harness.capturedHelperContext.renderNoticeViewerWindow, context.renderNoticeViewerWindow);
  assert.strictEqual(harness.capturedHelperContext.loadProjectRelatedNotices, context.loadProjectRelatedNotices);
  assert.strictEqual(harness.capturedFactoryDeps.state, state);
  assert.strictEqual(harness.capturedFactoryDeps.renderNoticeViewerWindow, context.renderNoticeViewerWindow);

  assert.equal(await context.openRelatedNoticeViewer({ id: "notice-1", project_name: "Alpha" }), "open-related");
  assert.equal(await context.openProjectNoticeViewer({ id: "project-1", project_name: "Beta" }), "open-project");
  assert.equal(await context.openTrackerEntryNoticeViewer("entry-1"), "open-tracker-entry");

  assert.deepEqual(calls.slice(2), [
    ["openRelatedNoticeViewer", { id: "notice-1", project_name: "Alpha" }],
    ["openProjectNoticeViewer", { id: "project-1", project_name: "Beta" }],
    ["openTrackerEntryNoticeViewer", "entry-1", state.trackerEntries],
  ]);
});

test("app.js delegates the remaining project-related wrappers and preserves cache reuse through the controller", async () => {
  const harness = createProjectRelatedHarness();
  const { context, calls, state } = harness;

  assert.equal(await context.hydrateProjectRelatedPayloadCache(), "hydrate-project-related");
  assert.equal(await context.persistProjectRelatedPayloadCache(), "persist-project-related");
  assert.equal(context.renderRelatedProjectNotices({ id: "project-1" }), "render-related-project-notices");
  assert.equal(context.renderTrackerEntryRelatedNotices({ id: "entry-1" }), "render-tracker-entry-related-notices");
  assert.equal(context.renderRelatedNoticePanel("project-1"), "panel:project-1");
  assert.equal(context.bindRelatedNoticeViewerButtons({ id: "root" }), "bind-buttons");
  assert.equal(context.renderProjectRelatedHosts(), "render-project-related-hosts");
  assert.equal(context.clearProjectRelatedRefresh("project-1"), "cleared:project-1");
  assert.equal(context.maybeScheduleProjectRelatedRefresh("project-1"), "scheduled:project-1");
  assert.equal(context.canReuseProjectRelatedPayload({ status: "ready", __cachedAt: 123 }), true);

  const firstCached = context.cacheProjectRelatedPayload("project-1", { status: "ready", items: [{ id: "a" }] });
  const secondCached = context.cacheProjectRelatedPayload("project-1", { status: "ready", items: [{ id: "b" }] });
  assert.strictEqual(firstCached, secondCached);
  assert.equal(context.resolveTrackerEntryProjectId("entry-1"), "project-for-entry-1");
  assert.equal(await context.ensureTrackerEntryProjectId("entry-1"), "ensured-entry-1");

  assert.deepEqual(calls.slice(2), [
    ["hydrateProjectRelatedPayloadCache"],
    ["persistProjectRelatedPayloadCache"],
    ["renderRelatedProjectNotices", { id: "project-1" }],
    ["renderTrackerEntryRelatedNotices", { id: "entry-1" }],
    ["renderRelatedNoticePanel", "project-1"],
    ["bindRelatedNoticeViewerButtons", { id: "root" }],
    ["renderProjectRelatedHosts"],
    ["clearProjectRelatedRefresh", "project-1"],
    ["maybeScheduleProjectRelatedRefresh", "project-1"],
    ["canReuseProjectRelatedPayload", { status: "ready", __cachedAt: 123 }],
    ["cacheProjectRelatedPayload", "project-1", { status: "ready", items: [{ id: "a" }] }],
    ["cacheProjectRelatedPayload", "project-1", { status: "ready", items: [{ id: "b" }] }],
    ["resolveTrackerEntryProjectId", "entry-1"],
    ["ensureTrackerEntryProjectId", "entry-1"],
  ]);

  assert.equal(state.trackerEntries.length, 1);
});

test("getProjectRelatedController fails fast when wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getProjectRelatedController() {",
    "function getTrackerController() {",
  );
  const context = vm.createContext({
    console,
    projectRelatedController: null,
    state: {},
    window: {
      PROJECT_RELATED_CONTROLLER: {
        createProjectRelatedController() {
          return {};
        },
      },
    },
    api: async () => ({}),
    flash: () => {},
    escapeHtml: () => "",
    RELATED_NOTICE_RUNTIME: {},
    PROJECT_RELATED_READY_CACHE_TTL_MS: 1,
    PROJECT_RELATED_SEED_CACHE_TTL_MS: 1,
    PROJECT_RELATED_STORAGE_KEY: "cache-key",
    PROJECT_RELATED_STORAGE_MAX_ITEMS: 1,
    renderNoticeViewerWindow: () => {},
    renderNoticeViewerPayload: () => {},
    renderNoticeViewerError: () => {},
    renderProjects: () => {},
    renderTrackerEntries: () => {},
    loadProjectRelatedNotices: async () => {},
    loadSelectedEntryDetail: async () => null,
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getProjectRelatedController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

function createSalesPanelHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getSalesPanelController() {",
    "const dom = createAppDom(document);",
  );
  const wrapperSource = [
    extractFunction(source, "function renderSalesSummaryPanel() {", "function renderMySalesClaimsPanel() {"),
    extractFunction(source, "function renderMySalesClaimsPanel() {", "function bindUserSalesSectionEvents() {"),
    extractFunction(source, "function bindUserSalesSectionEvents() {", "function formatShortDateTime(value) {"),
    extractFunction(source, "async function claimSalesProject(entry) {", "async function saveSalesClaimNote(projectId) {"),
    extractFunction(source, "async function saveSalesClaimNote(projectId) {", "async function transferSalesClaim(projectId, targetUserId) {"),
    extractFunction(source, "async function transferSalesClaim(projectId, targetUserId) {", "async function closeSalesClaim(projectId, outcome, { contractAmountText = \"\" } = {}) {"),
    extractFunction(source, "async function closeSalesClaim(projectId, outcome, { contractAmountText = \"\" } = {}) {", "async function adminDeleteLatestSalesNote(projectId, rawSalesNote) {"),
    extractFunction(source, "async function adminDeleteLatestSalesNote(projectId, rawSalesNote) {", "async function releaseSalesClaim(projectId, { force = false } = {}) {"),
    extractFunction(source, "async function releaseSalesClaim(projectId, { force = false } = {}) {", "function renderSalesClaimSection(entry) {"),
    extractFunction(source, "function renderSalesClaimSection(entry) {", "function buildTrackerEntryCardMarkupFallback(payload = {}, helpers = {}) {"),
    extractFunction(source, "function openSalesCloseDialog(projectId) {", "function closeSalesCloseDialog() {"),
    extractFunction(source, "function closeSalesCloseDialog() {", "async function confirmSalesCloseDialog() {"),
    extractFunction(source, "async function confirmSalesCloseDialog() {", "function renderProfileStatus(message = \"\", level = \"\") {"),
  ].join("\n");

  const calls = [];
  const controller = {
    renderSalesSummaryPanel() {
      calls.push(["renderSalesSummaryPanel"]);
      return { ok: "renderSalesSummaryPanel" };
    },
    renderMySalesClaimsPanel() {
      calls.push(["renderMySalesClaimsPanel"]);
      return { ok: "renderMySalesClaimsPanel" };
    },
    bindUserSalesSectionEvents() {
      calls.push(["bindUserSalesSectionEvents"]);
      return { ok: "bindUserSalesSectionEvents" };
    },
    async claimSalesProject(entry) {
      calls.push(["claimSalesProject", entry]);
      return { ok: "claimSalesProject", entry };
    },
    async saveSalesClaimNote(projectId) {
      calls.push(["saveSalesClaimNote", projectId]);
      return { ok: "saveSalesClaimNote", projectId };
    },
    async transferSalesClaim(projectId, targetUserId) {
      calls.push(["transferSalesClaim", projectId, targetUserId]);
      return { ok: "transferSalesClaim", projectId, targetUserId };
    },
    async closeSalesClaim(projectId, outcome, options) {
      calls.push(["closeSalesClaim", projectId, outcome, options]);
      return { ok: "closeSalesClaim", projectId, outcome, options };
    },
    async adminDeleteLatestSalesNote(projectId, rawSalesNote) {
      calls.push(["adminDeleteLatestSalesNote", projectId, rawSalesNote]);
      return { ok: "adminDeleteLatestSalesNote", projectId, rawSalesNote };
    },
    async releaseSalesClaim(projectId, options) {
      calls.push(["releaseSalesClaim", projectId, options]);
      return { ok: "releaseSalesClaim", projectId, options };
    },
    renderSalesClaimSection(entry) {
      calls.push(["renderSalesClaimSection", entry]);
      return { ok: "renderSalesClaimSection", entry };
    },
    openSalesCloseDialog(projectId) {
      calls.push(["openSalesCloseDialog", projectId]);
      return { ok: "openSalesCloseDialog", projectId };
    },
    closeSalesCloseDialog() {
      calls.push(["closeSalesCloseDialog"]);
      return { ok: "closeSalesCloseDialog" };
    },
    async confirmSalesCloseDialog() {
      calls.push(["confirmSalesCloseDialog"]);
      return { ok: "confirmSalesCloseDialog" };
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    FRONTEND_RUNTIME_ADAPTERS: {},
    SALES_STATE_HELPERS: {},
    salesPanelController: null,
    salesPanelDepsHelpers: null,
    window: {
      SALES_PANEL_CONTROLLER: {
        createSalesPanelController() {
          calls.push(["factory"]);
          return controller;
        },
      },
    },
    dom: {},
    state: {},
    api: async () => {
      throw new Error("api should not run in sales delegation test");
    },
    escapeHtml: (value) => String(value ?? ""),
    getLatestSalesNoteItem: () => null,
    truncate: (value) => String(value ?? ""),
    formatSalesNoteTextForDisplay: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    getSalesNoteEntries: () => [],
    getSalesYearMonthBucket: () => null,
    formatContractAmountDisplay: (value) => String(value ?? ""),
    extractContractAmountTextFromSalesNote: () => "",
    salesClaimStatusLabel: (value) => String(value ?? ""),
    getVisibleSalesProjectIds: () => [],
    getSalesClaimForProject: () => null,
    getTrackerProjectSnapshot: () => null,
    renderUserSalesProjectFacts: () => "",
    isCurrentUserClaimOwner: () => false,
    canCurrentUserForceRelease: () => false,
    canCurrentUserManageClaim: () => false,
    isActiveSalesClaim: () => false,
    getOrganizationTransferTargets: () => [],
    getSalesNoteDraft: () => "",
    setSalesNoteDraft: () => {},
    upsertSalesClaim: () => {},
    replaceVisibleSalesClaims: () => {},
    mergeActiveSalesClaims: () => {},
    renderUserOwnedSalesClaimCard: () => "",
    formatSalesClaimEstimateLabel: () => "",
    renderCompanySalesClaimCard: () => "",
    renderUserTrackerClaimSection: () => "",
    formatEstimatedAmountRangeFromKrw: () => "",
    claimSalesProject: async () => {},
    saveSalesClaimNote: async () => {},
    transferSalesClaim: async () => {},
    closeSalesClaim: async () => {},
    adminDeleteLatestSalesNote: async () => {},
    releaseSalesClaim: async () => {},
    formatContractAmountInput: (value) => String(value ?? ""),
    buildUserSalesProjectFactsMarkup: () => "",
    buildSalesClaimEstimateLabelMarkup: () => "",
    buildUserOwnedSalesClaimCardMarkup: () => "",
    buildCompanySalesClaimCardMarkup: () => "",
    buildUserTrackerClaimSectionMarkup: () => "",
    formatEokValue: (value) => String(value ?? ""),
    getSalesNoteTimeline: () => [],
    serializeSalesNoteEntry: (value) => String(value ?? ""),
    removeLatestSalesNoteEntry: () => [],
    isAdminRole: () => false,
    renderTrackerEntries: () => {},
    loadSalesOverview: async () => {},
    loadMySalesClaims: async () => {},
    loadVisibleSalesClaims: async () => {},
    refreshSalesAdminPanels: async () => {},
    SALES_VIEW_RUNTIME: null,
    flash: () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls };
}

function createHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const bindEventsSource = extractFunction(
    source,
    "function bindEvents() {",
    "function mountRuntimeEnhancements() {",
  );
  const mountRuntimeEnhancementsSource = extractFunction(
    source,
    "function mountRuntimeEnhancements() {",
    "function runTypeLabel(runType) {",
  );
  const renderTrackerEntriesSource = extractFunction(
    source,
    "function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {",
    "function renderTrackerEntriesFallback(entries, { refreshSelectedEntry = true } = {}) {",
  );
  const renderTrackerBoardSource = extractFunction(
    source,
    "function renderTrackerBoard(entries) {",
    "function renderTrackerBoardFallback(entries) {",
  );
  const renderRunExecutionContextSource = extractFunction(
    source,
    "function renderRunExecutionContext(run) {",
    "function resolveTrackerExecutionContext(run) {",
  );
  const runGetterSource = extractFunction(
    source,
    "function getRunPanelsController() {",
    "function getReportPanelsController() {",
  );
  const reportGetterSource = extractFunction(
    source,
    "function getReportPanelsController() {",
    "function getConsolePanelsController() {",
  );
  const consoleGetterSource = extractFunction(
    source,
    "function getConsolePanelsController() {",
    "function getUiModeController() {",
  );
  const reportLoadPhaseSource = extractFunction(
    source,
    "async function loadPhaseReport({ silent = false } = {}) {",
    "async function loadReportJobs({ silent = false } = {}) {",
  );
  const reportLoadJobsSource = extractFunction(
    source,
    "async function loadReportJobs({ silent = false } = {}) {",
    "async function runSelectedReport() {",
  );
  const reportRunSelectedSource = extractFunction(
    source,
    "async function runSelectedReport() {",
    "async function refreshReportPanels() {",
  );
  const reportRefreshSource = extractFunction(
    source,
    "async function refreshReportPanels() {",
    "function renderReport(report, errorMessage = \"\") {",
  );
  const loadDashboardSummarySource = extractFunction(
    source,
    "async function loadDashboardSummary({ silent = false } = {}) {",
    "function renderDashboard(summary, errorMessage = \"\") {",
  );
  const renderReportSource = extractFunction(
    source,
    "function renderReport(report, errorMessage = \"\") {",
    "function renderReportJobs(items) {",
  );
  const renderReportJobsSource = extractFunction(
    source,
    "function renderReportJobs(items) {",
    "function renderReportJob(job, errorMessage = \"\") {",
  );
  const renderReportJobSource = extractFunction(
    source,
    "function renderReportJob(job, errorMessage = \"\") {",
    "async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) {",
  );
  const loadSelectedRunArtifactsSource = extractFunction(
    source,
    "async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) {",
    "async function loadWinnerRunPanels(run) {",
  );
  const loadWinnerRunPanelsSource = extractFunction(
    source,
    "async function loadWinnerRunPanels(run) {",
    "async function loadTrackerExportPanels(run) {",
  );
  const loadTrackerExportPanelsSource = extractFunction(
    source,
    "async function loadTrackerExportPanels(run) {",
    "function scheduleArtifactRetry(runId) {",
  );
  const scheduleArtifactRetrySource = extractFunction(
    source,
    "function scheduleArtifactRetry(runId) {",
    "function renderArtifactsList() {",
  );
  const renderArtifactsListSource = extractFunction(
    source,
    "function renderArtifactsList() {",
    "function resolveTrackerContextRun(runSnapshot = state.selectedRun) {",
  );
  const resolveTrackerContextRunSource = extractFunction(
    source,
    "function resolveTrackerContextRun(runSnapshot = state.selectedRun) {",
    "function buildArtifactEmptyMessage() {",
  );
  const buildArtifactEmptyMessageSource = extractFunction(
    source,
    "function buildArtifactEmptyMessage() {",
    "function normalizeCollectMode(value) {",
  );
  const renderArtifactPreviewMarkupSource = extractFunction(
    source,
    "function renderArtifactPreviewMarkup(artifactId) {",
    "function trackerColumnStyle(widths, index) {",
  );
  const calls = {
    console: [],
    report: [],
    reportDeps: null,
    run: null,
  };
  const appSupportCalls = [];

  const window = {
    RUN_PANELS_CONTROLLER: {
      createRunPanelsController(deps) {
        calls.run = deps;
        return { id: "run-controller" };
      },
    },
  };

  const context = vm.createContext({
    window,
    console,
    state: {},
    document: {},
    dom: {
      dashboardMetrics: { innerHTML: "" },
      dashboardFailedRuns: { innerHTML: "" },
      dashboardReportJobs: { innerHTML: "" },
      reportStatus: { textContent: "" },
      reportSummary: { textContent: "" },
      reportJson: { textContent: "" },
    },
    api: async () => {
      throw new Error("api should not be called in this delegation test");
    },
    flash: () => {},
    touchSyncMeta: () => {},
    setBusy: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    formatBytes: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    metricCard: (label, value) => `${label}:${value}`,
    PROJECT_RUNTIME: null,
    RUN_VIEW_RUNTIME: null,
    ARTIFACT_RUNTIME: null,
    RELATED_NOTICE_RUNTIME: null,
    PROJECT_RUNTIME: null,
    renderRelatedProjectNotices: () => "",
    bindRelatedNoticeViewerButtons: () => {},
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    renderArtifactPreviewMarkup: () => "",
    resolveTrackerExecutionContext: () => null,
    trackerExecutionTone: () => "",
    trackerExecutionMessage: () => "",
    progressPercent: () => 0,
    trackerExportStageLabel: () => "",
    loadRuns: async () => {},
    resetTrackerBoardEdit: () => {},
    refreshSelectedRun: async () => {},
    isProjectTrackerRun: () => false,
    useGlobalTrackerEntriesScope: () => false,
    renderRunExecutionContext: () => {},
    renderArtifactsList: () => "fallback-artifacts",
    buildArtifactEmptyMessage: () => "empty",
    loadTrackerEntries: async () => {},
    disconnectRunEventStream: () => {},
    APP_SUPPORT: createAppSupportStub(appSupportCalls),
    callRunPanelsControllerMethod: (methodName, fallback, ...args) => (
      typeof fallback === "function" ? fallback(...args) : fallback
    ),
    runPanelsController: null,
    reportPanelsController: null,
    consolePanelsController: null,
    window: {
      RUN_PANELS_CONTROLLER: {
        createRunPanelsController(deps) {
          calls.run = deps;
          return { id: "run-controller" };
        },
      },
      CONSOLE_PANELS_CONTROLLER: {
        createConsolePanelsController() {
          return {
            loadDashboardSummary({ silent }) {
              calls.console.push(["loadDashboardSummary", silent]);
              return "console-load";
            },
            renderDashboard(summary, errorMessage) {
              calls.console.push(["renderDashboard", summary, errorMessage]);
            },
            renderRunExecutionContext(run) {
              calls.console.push(["renderRunExecutionContext", run]);
            },
            loadProjects({ silent }) {
              calls.console.push(["loadProjects", silent]);
              return "projects-load";
            },
            changeProjectsPage(delta) {
              calls.console.push(["changeProjectsPage", delta]);
            },
            renderProjects(errorMessage) {
              calls.console.push(["renderProjects", errorMessage]);
            },
          };
        },
      },
      REPORT_PANELS_CONTROLLER: {
        createReportPanelsController(deps) {
          calls.reportDeps = deps;
          return {
            loadPhaseReport({ silent }) {
              calls.report.push(["loadPhaseReport", silent]);
              return "phase-load";
            },
            loadReportJobs({ silent }) {
              calls.report.push(["loadReportJobs", silent]);
              return "jobs-load";
            },
            runSelectedReport() {
              calls.report.push(["runSelectedReport"]);
              return "run-report";
            },
            refreshReportPanels() {
              calls.report.push(["refreshReportPanels"]);
              return "refresh-report";
            },
            renderReport(report, errorMessage) {
              calls.report.push(["renderReport", report, errorMessage]);
            },
            renderReportJobs(items) {
              calls.report.push(["renderReportJobs", items]);
            },
            renderReportJob(job, errorMessage) {
              calls.report.push(["renderReportJob", job, errorMessage]);
            },
            renderArtifactsList() {
              calls.report.push(["renderArtifactsList"]);
            },
            renderArtifactPreviewMarkup(artifactId) {
              calls.report.push(["renderArtifactPreviewMarkup", artifactId]);
              return "preview";
            },
            buildArtifactEmptyMessage() {
              calls.report.push(["buildArtifactEmptyMessage"]);
              return "empty-from-controller";
            },
          };
        },
      },
    },
  });

  vm.runInContext(
    `${wiringRuntimeSource}\n${bindEventsSource}\n${mountRuntimeEnhancementsSource}\n${renderTrackerEntriesSource}\n${renderTrackerBoardSource}\n${renderRunExecutionContextSource}\n${runGetterSource}\n${reportGetterSource}\n${consoleGetterSource}\n${reportLoadPhaseSource}\n${reportLoadJobsSource}\n${reportRunSelectedSource}\n${reportRefreshSource}\n${loadDashboardSummarySource}\n${renderReportSource}\n${renderReportJobsSource}\n${renderReportJobSource}\n${renderArtifactsListSource}\n${buildArtifactEmptyMessageSource}\n${renderArtifactPreviewMarkupSource}`,
    context,
    {
    filename: appPath,
    },
  );

  return { context, calls, appSupportCalls, window, runGetterSource, reportGetterSource, consoleGetterSource };
}

function createConsoleChangeProjectsHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getConsolePanelsController() {",
    "function getUiModeController() {",
  );
  const wrapperSource = extractFunction(
    source,
    "function changeProjectsPage(delta) {",
    "async function loadPhaseReport({ silent = false } = {}) {",
  );
  const calls = [];

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    consolePanelsController: null,
    dom: {},
    state: {},
    document: {},
    window: {
      CONSOLE_PANELS_CONTROLLER: {
        createConsolePanelsController() {
          calls.push(["factory"]);
          return {
            changeProjectsPage(delta) {
              calls.push(["changeProjectsPage", delta]);
              return "console-change-projects-page";
            },
          };
        },
      },
    },
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => String(value ?? ""),
    metricCard: (label, value) => `${label}:${value}`,
    PROJECT_RUNTIME: null,
    RUN_VIEW_RUNTIME: null,
    renderArtifactPreviewMarkup: () => "",
    resolveTrackerExecutionContext: () => null,
    trackerExecutionTone: () => "",
    trackerExecutionMessage: () => "",
    progressPercent: () => 0,
    trackerExportStageLabel: () => "",
    renderRelatedProjectNotices: () => "",
    bindRelatedNoticeViewerButtons: () => {},
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    api: async () => {
      throw new Error("api should not run in console thin wrapper test");
    },
    loadProjects: () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: () => {},
    flash: () => {},
  });

  vm.runInContext(`${wiringRuntimeSource}\n${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls, getterSource };
}

function createConsoleChangeProjectsFallbackHarness() {
  const source = readAppSource();
  const wrapperSource = extractFunction(
    source,
    "function changeProjectsPage(delta) {",
    "async function loadPhaseReport({ silent = false } = {}) {",
  );
  const calls = [];
  const state = {
    projectsTotal: 45,
    projectFilters: {
      page: 2,
      pageSize: 10,
    },
  };
  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    state,
    consolePanelsController: null,
    window: {
      CONSOLE_PANELS_CONTROLLER: {},
    },
    loadProjects(options) {
      calls.push(["loadProjects", options]);
    },
  });

  vm.runInContext(wrapperSource, context, { filename: appPath });
  return { context, calls, state };
}

function createNoticeViewerWrapperHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getReportPanelsController() {",
    "function getConsolePanelsController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      'function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = "',
      'function renderNoticeViewerError(viewerWindow, { title = "',
    ),
    extractFunction(
      source,
      'function renderNoticeViewerError(viewerWindow, { title = "',
      'function renderNoticeViewerWindow(targetWindow, { title = "',
    ),
    extractFunction(
      source,
      'function renderNoticeViewerWindow(targetWindow, { title = "',
      "function formatNoticeViewerSourceLabel(value) {",
    ),
  ].join("\n");
  const calls = [];

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    reportPanelsController: null,
    state: {},
    dom: {},
    window: {
      REPORT_PANELS_CONTROLLER: {
        createReportPanelsController() {
          calls.push(["factory"]);
          return {
            renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle) {
              calls.push(["renderNoticeViewerPayload", viewerWindow, payload, fallbackTitle]);
              return "notice-viewer-payload";
            },
            renderNoticeViewerError(viewerWindow, options) {
              calls.push(["renderNoticeViewerError", viewerWindow, options]);
              return "notice-viewer-error";
            },
            renderNoticeViewerWindow(targetWindow, options) {
              calls.push(["renderNoticeViewerWindow", targetWindow, options]);
              return "notice-viewer-window";
            },
          };
        },
      },
    },
    api: async () => {
      throw new Error("api should not run in notice viewer wrapper test");
    },
    flash: () => {},
    setBusy: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    formatBytes: (value) => String(value ?? ""),
    statusBadge: (value) => String(value ?? ""),
    ARTIFACT_RUNTIME: null,
    RELATED_NOTICE_RUNTIME: null,
    loadDashboardSummary: async () => {},
    touchSyncMeta: () => {},
    syncUrlState: () => {},
    callRunPanelsControllerMethod: () => undefined,
  });

  vm.runInContext(`${wiringRuntimeSource}\n${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls, getterSource };
}

function createNoticeViewerFallbackHarness() {
  const source = readAppSource();
  const wrapperSource = [
    extractFunction(
      source,
      'function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = "',
      'function renderNoticeViewerError(viewerWindow, { title = "',
    ),
    extractFunction(
      source,
      'function renderNoticeViewerError(viewerWindow, { title = "',
      'function renderNoticeViewerWindow(targetWindow, { title = "',
    ),
    extractFunction(
      source,
      'function renderNoticeViewerWindow(targetWindow, { title = "',
      "function formatNoticeViewerSourceLabel(value) {",
    ),
    extractFunction(
      source,
      "function formatNoticeViewerSourceLabel(value) {",
      "function resolveOpenTrackerRelatedProjectId() {",
    ),
  ].join("\n");
  const writes = [];
  const targetWindow = {
    closed: false,
    document: {
      open() {
        writes.push("open");
      },
      write(value) {
        writes.push(value);
      },
      close() {
        writes.push("close");
      },
    },
  };
  const context = vm.createContext({
    console,
    reportPanelsController: null,
    window: {
      REPORT_PANELS_CONTROLLER: {},
    },
    escapeHtml: (value) => String(value ?? ""),
    RELATED_NOTICE_RUNTIME: {
      buildNoticeViewerDocumentsMarkup() {
        return "<p>docs</p>";
      },
      buildNoticeViewerHtml({ title, meta, body }) {
        return `<html><body><h1>${title}</h1><div>${meta}</div>${body}</body></html>`;
      },
      formatNoticeViewerSourceLabel(value) {
        return String(value ?? "");
      },
    },
  });

  vm.runInContext(wrapperSource, context, { filename: appPath });
  return { context, targetWindow, writes };
}

test("app.js delegates dashboard and report wrappers to the loaded panel controllers", async () => {
  const harness = createHarness();
  const { context, calls, appSupportCalls, runGetterSource, reportGetterSource, consoleGetterSource } = harness;

  const runController = context.getRunPanelsController();
  assert.equal(runController.id, "run-controller");
  assert.ok(calls.run);
  assert.equal(typeof calls.run.trackerController?.disconnectRunEventStream, "function");
  assert.match(reportGetterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(reportGetterSource, /wiringDepsFactoryName:\s*"createReportPanelsControllerDeps"/);
  assert.match(consoleGetterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(consoleGetterSource, /wiringDepsFactoryName:\s*"createConsolePanelsControllerDeps"/);
  assert.deepEqual(appSupportCalls, ["createRunPanelsControllerDepsHelpers"]);

  const dashboardResult = await context.loadDashboardSummary({ silent: true });
  assert.equal(dashboardResult, "console-load");
  assert.deepEqual(calls.console[0], ["loadDashboardSummary", true]);
  assert.deepEqual(appSupportCalls, [
    "createRunPanelsControllerDepsHelpers",
    "createConsolePanelsControllerDepsHelpers",
  ]);

  assert.equal(await context.loadPhaseReport({ silent: true }), "phase-load");
  assert.equal(await context.loadReportJobs({ silent: true }), "jobs-load");
  assert.equal(await context.runSelectedReport(), "run-report");
  assert.equal(await context.refreshReportPanels(), "refresh-report");
  assert.deepEqual(appSupportCalls, [
    "createRunPanelsControllerDepsHelpers",
    "createConsolePanelsControllerDepsHelpers",
    "createReportPanelsControllerDepsHelpers",
  ]);
  assert.equal(calls.reportDeps.callRunPanelsController, context.callRunPanelsControllerMethod);
  assert.equal(calls.reportDeps.loadDashboardSummary, context.loadDashboardSummary);
  context.renderReport({ summary: { matched_count: 1 } }, "boom");
  context.renderReportJobs([{ id: "job-1" }]);
  context.renderReportJob({ id: "job-1" }, "err");
  context.renderArtifactsList();
  assert.equal(context.buildArtifactEmptyMessage(), "empty-from-controller");
  assert.equal(context.renderArtifactPreviewMarkup("artifact-1"), "preview");

  assert.deepEqual(calls.report.slice(0, 8), [
    ["loadPhaseReport", true],
    ["loadReportJobs", true],
    ["runSelectedReport"],
    ["refreshReportPanels"],
    ["renderReport", { summary: { matched_count: 1 } }, "boom"],
    ["renderReportJobs", [{ id: "job-1" }]],
    ["renderReportJob", { id: "job-1" }, "err"],
    ["renderArtifactsList"],
  ]);
  assert.deepEqual(calls.report.slice(8), [
    ["buildArtifactEmptyMessage"],
    ["renderArtifactPreviewMarkup", "artifact-1"],
  ]);
});

test("getReportPanelsController fails fast when the report panels controller factory is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getReportPanelsController() {",
    "function getConsolePanelsController() {",
  );

  const context = vm.createContext({
    console,
    window: {},
    reportPanelsController: null,
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getReportPanelsController(),
    /REPORT_PANELS_CONTROLLER\.createReportPanelsController/,
  );
});

test("getReportPanelsController fails fast when the report panels wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getReportPanelsController() {",
    "function getConsolePanelsController() {",
  );

  const context = vm.createContext({
    console,
    window: {
      REPORT_PANELS_CONTROLLER: {
        createReportPanelsController() {
          return {};
        },
      },
    },
    reportPanelsController: null,
    state: {},
    dom: {},
    api: async () => {},
    flash: () => {},
    setBusy: () => {},
    escapeHtml: () => "",
    formatDate: () => "",
    formatJson: () => "",
    formatBytes: () => "",
    statusBadge: () => "",
    ARTIFACT_RUNTIME: null,
    RELATED_NOTICE_RUNTIME: null,
    loadDashboardSummary: async () => {},
    touchSyncMeta: () => {},
    syncUrlState: () => {},
    callRunPanelsControllerMethod: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getReportPanelsController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("getConsolePanelsController fails fast when the console panels controller factory is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getConsolePanelsController() {",
    "function getAuthUiController() {",
  );

  const context = vm.createContext({
    console,
    window: {},
    consolePanelsController: null,
    dom: {},
    state: {},
    escapeHtml: () => "",
    formatDate: () => "",
    runTypeLabel: () => "",
    statusBadge: () => "",
    metricCard: () => "",
    PROJECT_RUNTIME: null,
    RUN_VIEW_RUNTIME: null,
    renderArtifactPreviewMarkup: () => "",
    resolveTrackerExecutionContext: () => null,
    trackerExecutionTone: () => "",
    trackerExecutionMessage: () => "",
    progressPercent: () => 0,
    trackerExportStageLabel: () => "",
    renderRelatedProjectNotices: () => "",
    bindRelatedNoticeViewerButtons: () => {},
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    api: async () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: () => {},
    flash: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getConsolePanelsController(),
    /CONSOLE_PANELS_CONTROLLER\.createConsolePanelsController/,
  );
});

test("getConsolePanelsController fails fast when the console panels wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getConsolePanelsController() {",
    "function getUiModeController() {",
  );

  const context = vm.createContext({
    console,
    window: {
      CONSOLE_PANELS_CONTROLLER: {
        createConsolePanelsController() {
          return {};
        },
      },
    },
    consolePanelsController: null,
    dom: {},
    state: {},
    escapeHtml: () => "",
    formatDate: () => "",
    runTypeLabel: () => "",
    statusBadge: () => "",
    metricCard: () => "",
    PROJECT_RUNTIME: null,
    RUN_VIEW_RUNTIME: null,
    renderArtifactPreviewMarkup: () => "",
    resolveTrackerExecutionContext: () => null,
    trackerExecutionTone: () => "",
    trackerExecutionMessage: () => "",
    progressPercent: () => 0,
    trackerExportStageLabel: () => "",
    renderRelatedProjectNotices: () => "",
    bindRelatedNoticeViewerButtons: () => {},
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    api: async () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: () => {},
    flash: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getConsolePanelsController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("report panel wrappers stay thin and do not keep inline report/artifact behavior in app.js", () => {
  const source = readAppSource();
  const loadPhaseReportSource = extractFunction(
    source,
    "async function loadPhaseReport({ silent = false } = {}) {",
    "async function loadReportJobs({ silent = false } = {}) {",
  );
  const loadReportJobsSource = extractFunction(
    source,
    "async function loadReportJobs({ silent = false } = {}) {",
    "async function runSelectedReport() {",
  );
  const runSelectedReportSource = extractFunction(
    source,
    "async function runSelectedReport() {",
    "async function refreshReportPanels() {",
  );
  const refreshReportPanelsSource = extractFunction(
    source,
    "async function refreshReportPanels() {",
    "function renderReport(report, errorMessage = \"\") {",
  );
  const renderReportSource = extractFunction(
    source,
    "function renderReport(report, errorMessage = \"\") {",
    "function renderReportJobs(items) {",
  );
  const renderReportJobsSource = extractFunction(
    source,
    "function renderReportJobs(items) {",
    "function renderReportJob(job, errorMessage = \"\") {",
  );
  const renderReportJobSource = extractFunction(
    source,
    "function renderReportJob(job, errorMessage = \"\") {",
    "async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) {",
  );
  const loadSelectedRunArtifactsSource = extractFunction(
    source,
    "async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) {",
    "async function loadWinnerRunPanels(run) {",
  );
  const loadWinnerRunPanelsSource = extractFunction(
    source,
    "async function loadWinnerRunPanels(run) {",
    "async function loadTrackerExportPanels(run) {",
  );
  const loadTrackerExportPanelsSource = extractFunction(
    source,
    "async function loadTrackerExportPanels(run) {",
    "function scheduleArtifactRetry(runId) {",
  );
  const scheduleArtifactRetrySource = extractFunction(
    source,
    "function scheduleArtifactRetry(runId) {",
    "function renderArtifactsList() {",
  );
  const renderArtifactsListSource = extractFunction(
    source,
    "function renderArtifactsList() {",
    "function resolveTrackerContextRun(runSnapshot = state.selectedRun) {",
  );
  const resolveTrackerContextRunSource = extractFunction(
    source,
    "function resolveTrackerContextRun(runSnapshot = state.selectedRun) {",
    "function buildArtifactEmptyMessage() {",
  );
  const buildArtifactEmptyMessageSource = extractFunction(
    source,
    "function buildArtifactEmptyMessage() {",
    "function normalizeCollectMode(value) {",
  );
  const renderArtifactPreviewMarkupSource = extractFunction(
    source,
    "function renderArtifactPreviewMarkup(artifactId) {",
    "function trackerColumnStyle(widths, index) {",
  );

  assert.equal(normalizeWhitespace(loadPhaseReportSource), normalizeWhitespace("async function loadPhaseReport({ silent = false } = {}) { return getReportPanelsController().loadPhaseReport({ silent }); }"));
  assert.equal(normalizeWhitespace(loadReportJobsSource), normalizeWhitespace("async function loadReportJobs({ silent = false } = {}) { return getReportPanelsController().loadReportJobs({ silent }); }"));
  assert.equal(normalizeWhitespace(runSelectedReportSource), normalizeWhitespace("async function runSelectedReport() { return getReportPanelsController().runSelectedReport(); }"));
  assert.equal(normalizeWhitespace(refreshReportPanelsSource), normalizeWhitespace("async function refreshReportPanels() { return getReportPanelsController().refreshReportPanels(); }"));
  assert.equal(normalizeWhitespace(renderReportSource), normalizeWhitespace("function renderReport(report, errorMessage = \"\") { return getReportPanelsController().renderReport(report, errorMessage); }"));
  assert.equal(normalizeWhitespace(renderReportJobsSource), normalizeWhitespace("function renderReportJobs(items) { return getReportPanelsController().renderReportJobs(items); }"));
  assert.equal(normalizeWhitespace(renderReportJobSource), normalizeWhitespace("function renderReportJob(job, errorMessage = \"\") { return getReportPanelsController().renderReportJob(job, errorMessage); }"));
  assert.equal(normalizeWhitespace(loadSelectedRunArtifactsSource), normalizeWhitespace("async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) { return getRunPanelsController()?.loadSelectedRunArtifacts({ silent, runId, runSnapshot }); }"));
  assert.equal(normalizeWhitespace(loadWinnerRunPanelsSource), normalizeWhitespace("async function loadWinnerRunPanels(run) { return getRunPanelsController()?.loadWinnerRunPanels(run); }"));
  assert.equal(normalizeWhitespace(loadTrackerExportPanelsSource), normalizeWhitespace("async function loadTrackerExportPanels(run) { return getRunPanelsController()?.loadTrackerExportPanels(run); }"));
  assert.equal(normalizeWhitespace(scheduleArtifactRetrySource), normalizeWhitespace("function scheduleArtifactRetry(runId) { return getRunPanelsController()?.scheduleArtifactRetry(runId); }"));
  assert.equal(renderArtifactsListSource.trim(), "function renderArtifactsList() {\n  return getReportPanelsController().renderArtifactsList();\n}");
  assert.equal(resolveTrackerContextRunSource.trim(), "function resolveTrackerContextRun(runSnapshot = state.selectedRun) {\n  return getRunPanelsController()?.resolveTrackerContextRun(runSnapshot) || null;\n}");
  assert.equal(buildArtifactEmptyMessageSource.trim(), "function buildArtifactEmptyMessage() {\n  return getReportPanelsController().buildArtifactEmptyMessage();\n}");
  assert.equal(renderArtifactPreviewMarkupSource.trim(), "function renderArtifactPreviewMarkup(artifactId) {\n  return getReportPanelsController().renderArtifactPreviewMarkup(artifactId);\n}");

  assert.doesNotMatch(loadPhaseReportSource, /api\("\/api\/reports/);
  assert.doesNotMatch(loadReportJobsSource, /api\("\/api\/report-jobs/);
  assert.doesNotMatch(runSelectedReportSource, /setBusy\(dom\.runReportButton/);
  assert.doesNotMatch(refreshReportPanelsSource, /Promise\.all/);
  assert.doesNotMatch(renderReportSource, /REPORT_RUNTIME/);
  assert.doesNotMatch(renderReportJobsSource, /REPORT_RUNTIME/);
  assert.doesNotMatch(renderReportJobSource, /REPORT_RUNTIME/);
  assert.doesNotMatch(loadSelectedRunArtifactsSource, /artifactResult|selectedTrackerWorkbookArtifactId|touchSyncMeta/);
  assert.doesNotMatch(loadWinnerRunPanelsSource, /loadSelectedRunLogs/);
  assert.doesNotMatch(loadTrackerExportPanelsSource, /loadTrackerEntries/);
  assert.doesNotMatch(scheduleArtifactRetrySource, /setTimeout/);
  assert.doesNotMatch(renderArtifactsListSource, /state\.artifactSections/);
  assert.doesNotMatch(renderArtifactsListSource, /buildArtifactSectionMarkup/);
  assert.doesNotMatch(resolveTrackerContextRunSource, /selectedTrackerRun/);
  assert.doesNotMatch(buildArtifactEmptyMessageSource, /artifact_metadata_persistent/);
  assert.doesNotMatch(renderArtifactPreviewMarkupSource, /artifactPreviewCache/);
});

test("app.js wrappers fall back safely when controller globals are absent", () => {
  const source = readAppSource();
  const bindEventsSource = extractFunction(
    source,
    "function bindEvents() {",
    "function mountRuntimeEnhancements() {",
  );
  const mountRuntimeEnhancementsSource = extractFunction(
    source,
    "function mountRuntimeEnhancements() {",
    "function runTypeLabel(runType) {",
  );
  const renderTrackerEntriesSource = extractFunction(
    source,
    "function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {",
    "function renderTrackerEntriesFallback(entries, { refreshSelectedEntry = true } = {}) {",
  );
  const renderTrackerBoardSource = extractFunction(
    source,
    "function renderTrackerBoard(entries) {",
    "function renderTrackerBoardFallback(entries) {",
  );
  const context = vm.createContext({
    console,
    getAppEventBindings: () => null,
    getRuntimeEnhancements: () => null,
    getTrackerRenderController: () => null,
    TRACKER_RENDER_FALLBACK_RUNTIME: null,
    renderTrackerEntriesFallback: () => undefined,
    renderTrackerBoardFallback: () => undefined,
  });

  vm.runInContext(
    `${bindEventsSource}\n${mountRuntimeEnhancementsSource}\n${renderTrackerEntriesSource}\n${renderTrackerBoardSource}`,
    context,
    { filename: appPath },
  );

  assert.doesNotThrow(() => context.bindEvents());
  assert.doesNotThrow(() => context.mountRuntimeEnhancements());
  assert.doesNotThrow(() => context.renderTrackerEntries([]));
  assert.doesNotThrow(() => context.renderTrackerBoard([]));
});

test("getAppEventBindings delegates through the wiring helper, caches the controller, and preserves deps", () => {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const helperSource = extractFunction(
    source,
    "function getAppEventBindingsDeps() {",
    "function getAppEventBindings() {",
  );
  const getterSource = extractFunction(
    source,
    "function getAppEventBindings() {",
    "function getRuntimeEnhancements() {",
  );

  assert.match(helperSource, /window\.SPMSAppControllerWiringRuntime\.createAppEventBindingsDeps\(/);
  assert.match(getterSource, /getAppEventBindingsDeps\(\)/);
  assert.doesNotMatch(getterSource, /createAppEventBindingsDeps\(\{/);
  assert.doesNotMatch(getterSource, /handleAuthSubmit:/);

  const calls = [];
  let helperDeps = null;
  const controller = {
    bindEvents() {
      calls.push(["bindEvents"]);
      return "bound";
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    window: {
      addEventListener() {
        calls.push(["addEventListener"]);
      },
      APP_EVENT_BINDINGS: {
        createAppEventBindings(deps) {
          calls.push(["factory", deps]);
          return controller;
        },
      },
      SPMSAppControllerWiringRuntime: {},
    },
    appEventBindings: null,
    dom: { trackerChangeBell: null },
    state: { app: true },
    document: { name: "document" },
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    TRACKER_REGION_OPTIONS: [{ value: "", label: "전체" }],
    handleAuthSubmit: () => {},
    setAuthMode: () => {},
    setAdminTab: () => {},
    handleAuthFindId: () => {},
    handleAuthPasswordReset: () => {},
    scheduleInvitationPreviewLookup: () => {},
    renderAuthUi: () => {},
    handleAuthSignOut: () => {},
    openProfileDialog: () => {},
    handleProfileSubmit: () => {},
    handleInvitationSubmit: () => {},
    loadOrganizationAdminData: () => {},
    closeProfileDialog: () => {},
    setTrackerChangeBellPopoverOpen: () => {},
    downloadSalesWorkbook: () => {},
    closeSalesCloseDialog: () => {},
    formatContractAmountInput: () => {},
    confirmSalesCloseDialog: () => {},
    refreshAuthSessionState: () => {},
    loadDashboardSummary: () => {},
    handleRunCreate: () => {},
    handleRunFormReset: () => {},
    refreshSelectedRun: () => {},
    loadRuns: () => {},
    loadSelectedRunLogs: () => {},
    runSelectedReport: () => {},
    refreshReportPanels: () => {},
    loadSelectedRunArtifacts: () => {},
    cancelSelectedRun: () => {},
    createTrackerExportForSelectedRun: () => {},
    toggleUiMode: () => {},
    renderSyncMeta: () => {},
    syncUrlState: () => {},
    loadReportJobs: () => {},
    loadPhaseReport: () => {},
    readRunFiltersFromControls: () => {},
    readTrackerFiltersFromControls: () => {},
    syncFilterControlsFromState: () => {},
    changeRunsPage: () => {},
    loadTrackerEntries: () => {},
    trackerChangeEventsCacheIsFresh: () => false,
    renderTrackerChangeBellPopover: () => {},
    loadTrackerChangeEvents: () => {},
    focusTrackerChangePanel: () => {},
    uploadTrackerTemplate: () => {},
    resetTrackerTemplateOverride: () => {},
    changeEntriesPageTo: () => {},
    changeEntriesPage: () => {},
    getEntriesTotalPages: () => 1,
    normalizeTrackerRegionFilter: () => "",
    parseTrackerRegionFilter: () => "",
    saveEntryPatch: () => {},
    clearEntryPatch: () => {},
    loadSelectedEntryAudit: () => {},
    loadTrackerMissingReport: () => {},
    refreshSalesAdminPanels: () => {},
    getMissingReportDownloadLimit: () => 0,
    syncPatchValueFromSelectedEntry: () => {},
    closeDrawer: () => {},
    loadRunPresets: () => {},
    applySelectedPreset: () => {},
    saveCurrentFormAsPreset: () => {},
    renderRunPresetPanel: () => {},
    loadProjects: () => {},
    changeProjectsPage: () => {},
    triggerTrackerEntriesXlsxDownload: () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const wiringRuntime = context.window.SPMSAppControllerWiringRuntime;
  const actualCreateAppEventBindingsDeps = wiringRuntime.createAppEventBindingsDeps;
  wiringRuntime.createAppEventBindingsDeps = (deps) => {
    calls.push(["helper", deps]);
    helperDeps = deps;
    return actualCreateAppEventBindingsDeps(deps);
  };
  vm.runInContext(`${helperSource}\n${getterSource}`, context, { filename: appPath });

  assert.strictEqual(context.getAppEventBindings(), context.getAppEventBindings());
  assert.strictEqual(calls.filter(([type]) => type === "helper").length, 1);
  assert.strictEqual(calls.filter(([type]) => type === "factory").length, 1);
  assert.strictEqual(helperDeps, calls.find(([type]) => type === "helper")[1]);
  const factoryDeps = calls.find(([type]) => type === "factory")[1];
  assert.notStrictEqual(factoryDeps, helperDeps);
  assert.strictEqual(helperDeps.loadProjects, context.loadProjects);
  assert.strictEqual(helperDeps.triggerTrackerEntriesXlsxDownload, context.triggerTrackerEntriesXlsxDownload);
  assert.strictEqual(factoryDeps.loadProjects, context.loadProjects);
  assert.strictEqual(factoryDeps.triggerTrackerEntriesXlsxDownload, context.triggerTrackerEntriesXlsxDownload);
});

test("getRuntimeEnhancements uses the wiring helper, preserves deps identity, and caches the controller", () => {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getRuntimeEnhancements() {",
    "function getOrgAdminController() {",
  );
  const mountRuntimeEnhancementsSource = extractFunction(
    source,
    "function mountRuntimeEnhancements() {",
    "function runTypeLabel(runType) {",
  );

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createRuntimeEnhancementsDeps"/);
  assert.match(getterSource, /buildRuntimeEnhancementsDeps\(\)/);

  const calls = [];
  let helperContext = null;
  let factoryDeps = null;
  const controller = {
    mountRuntimeEnhancements() {
      calls.push(["mountRuntimeEnhancements"]);
      return { mounted: true };
    },
  };

  const context = vm.createContext({
    console,
    runtimeEnhancements: null,
    APP_SUPPORT: createAppSupportStub(calls),
    window: {
      RUNTIME_ENHANCEMENTS: {
        createRuntimeEnhancements(deps) {
          calls.push(["factory", deps]);
          factoryDeps = deps;
          return controller;
        },
      },
      SPMSAppControllerWiringRuntime: {},
    },
    dom: { runtimeEnhancements: true },
    document: { name: "document" },
    syncCollectModeOptions: () => {},
    RUN_VIEW_RUNTIME: { runtime: true },
    renderOrganizationAdminPanel: () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const wiringRuntime = context.window.SPMSAppControllerWiringRuntime;
  const actualCreateRuntimeEnhancementsDeps = wiringRuntime.createRuntimeEnhancementsDeps;
  wiringRuntime.createRuntimeEnhancementsDeps = (deps) => {
    calls.push(["helper", deps]);
    helperContext = deps;
    return actualCreateRuntimeEnhancementsDeps(deps);
  };

  vm.runInContext(`${getterSource}\n${mountRuntimeEnhancementsSource}`, context, { filename: appPath });

  assert.strictEqual(context.getRuntimeEnhancements(), controller);
  assert.strictEqual(context.getRuntimeEnhancements(), controller);
  assert.ok(calls.includes("createRuntimeEnhancementsDepsHelpers"));
  assert.ok(calls.some((entry) => Array.isArray(entry) && entry[0] === "helper"));
  assert.ok(calls.some((entry) => Array.isArray(entry) && entry[0] === "factory"));
  assert.strictEqual(helperContext, calls.find((entry) => Array.isArray(entry) && entry[0] === "helper")[1]);
  assert.strictEqual(factoryDeps, calls.find((entry) => Array.isArray(entry) && entry[0] === "factory")[1]);
  assert.notStrictEqual(factoryDeps, helperContext);
  assert.deepEqual(Object.keys(helperContext).sort(), [
    "RUN_VIEW_RUNTIME",
    "document",
    "dom",
    "renderOrganizationAdminPanel",
    "syncCollectModeOptions",
  ].sort());
  assert.strictEqual(helperContext.dom, context.dom);
  assert.strictEqual(helperContext.document, context.document);
  assert.strictEqual(helperContext.syncCollectModeOptions, context.syncCollectModeOptions);
  assert.strictEqual(helperContext.RUN_VIEW_RUNTIME, context.RUN_VIEW_RUNTIME);
  assert.strictEqual(helperContext.renderOrganizationAdminPanel, context.renderOrganizationAdminPanel);
  assert.deepEqual(Object.keys(factoryDeps).sort(), [
    "RUN_VIEW_RUNTIME",
    "document",
    "dom",
    "renderOrganizationAdminPanel",
    "syncCollectModeOptions",
  ].sort());
  assert.strictEqual(factoryDeps.dom, context.dom);
  assert.strictEqual(factoryDeps.document, context.document);
  assert.strictEqual(factoryDeps.syncCollectModeOptions, context.syncCollectModeOptions);
  assert.strictEqual(factoryDeps.RUN_VIEW_RUNTIME, context.RUN_VIEW_RUNTIME);
  assert.strictEqual(factoryDeps.renderOrganizationAdminPanel, context.renderOrganizationAdminPanel);
  assert.deepEqual(context.mountRuntimeEnhancements(), { mounted: true });
  assert.deepEqual(context.mountRuntimeEnhancements(), { mounted: true });
  assert.strictEqual(calls.filter(([type]) => type === "mountRuntimeEnhancements").length, 2);
  assert.strictEqual(calls.filter(([type]) => type === "factory").length, 1);
  assert.strictEqual(calls.filter(([type]) => type === "helper").length, 1);
});

test("getRuntimeEnhancements fails fast when the wiring helper is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getRuntimeEnhancements() {",
    "function getOrgAdminController() {",
  );

  const context = vm.createContext({
    console,
    runtimeEnhancements: null,
    APP_SUPPORT: createAppSupportStub(),
    window: {
      RUNTIME_ENHANCEMENTS: {
        createRuntimeEnhancements() {
          return {};
        },
      },
      SPMSAppControllerWiringRuntime: {},
    },
    dom: {},
    document: {},
    syncCollectModeOptions: () => {},
    RUN_VIEW_RUNTIME: {},
    renderOrganizationAdminPanel: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getRuntimeEnhancements(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("getOrgAdminController uses the APP_SUPPORT helper builder and preserves dependency references", () => {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getOrgAdminController() {",
    "function getTrackerRenderController() {",
  );

  const calls = [];
  let helperInput = null;
  let helperDeps = null;
  let wiringInput = null;
  let factoryDeps = null;
  const controller = { orgAdmin: true };
  const context = vm.createContext({
    console,
    orgAdminController: null,
    APP_SUPPORT: createAppSupportStub(calls),
    window: {
      ORG_ADMIN_CONTROLLER: {
        createOrgAdminController(deps) {
          calls.push(["factory", deps]);
          factoryDeps = deps;
          return controller;
        },
      },
      SPMSAppControllerWiringRuntime: {},
    },
    state: { orgAdmin: true },
    dom: { orgAdmin: true },
    document: { name: "document" },
    navigator: { name: "navigator" },
    api: () => Promise.resolve(),
    flash: () => {},
    setBusy: () => {},
    escapeHtml: () => "",
    formatOrgRoleLabel: () => "",
    renderInvitationStatus: () => {},
    renderOrganizationAdminPanel: () => {},
    canUseAdminMode: () => true,
    formatDate: () => "",
    formatInvitationStatusLabel: () => "",
    formatAccountStatusLabel: () => "",
    formatMembershipStatusLabel: () => "",
    resolveStatusClass: () => "",
    MEMBERSHIP_STATUS_OPTIONS: ["active"],
    formatDownloadScopeLabel: () => "",
    formatDownloadFormatLabel: () => "",
    formatDownloadSourcePageLabel: () => "",
    PLATFORM_ADMIN_ACCOUNT_RUNTIME: { runtime: true },
    syncPlatformAdminAccountDraftFromForm: () => {},
    handlePlatformAdminAccountSubmit: () => {},
    renderOrgAdminRuntimeReloadFallback: () => {},
    canManagePlatformAdminAccounts: () => true,
    resetOrganizationMemberPassword: () => Promise.resolve(),
    requireConsoleDataRuntime: () => ({ runtime: true }),
    getConsoleDataRuntimeDeps: () => ({ runtimeDeps: true }),
    getOrgAdminRuntime: () => ({ orgAdminRuntime: true }),
    loadSalesClaimSummaryByUser: () => Promise.resolve(),
    loadClosedSalesClaims: () => Promise.resolve(),
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const wiringRuntime = context.window.SPMSAppControllerWiringRuntime;
  const actualCreateOrgAdminControllerDeps = wiringRuntime.createOrgAdminControllerDeps;
  wiringRuntime.createOrgAdminControllerDeps = (deps) => {
    calls.push(["helper", deps]);
    wiringInput = deps;
    return actualCreateOrgAdminControllerDeps(deps);
  };

  const actualCreateOrgAdminControllerDepsHelpers = context.APP_SUPPORT.createOrgAdminControllerDepsHelpers;
  context.APP_SUPPORT.createOrgAdminControllerDepsHelpers = (deps) => {
    calls.push(["helperBuilder", deps]);
    helperInput = deps;
    const helpers = actualCreateOrgAdminControllerDepsHelpers(deps);
    return {
      buildOrgAdminControllerDeps() {
        calls.push(["buildDeps"]);
        helperDeps = helpers.buildOrgAdminControllerDeps();
        return helperDeps;
      },
    };
  };

  vm.runInContext(getterSource, context, { filename: appPath });

  assert.strictEqual(context.getOrgAdminController(), controller);
  assert.strictEqual(context.getOrgAdminController(), controller);
  assert.ok(calls.some(([type]) => type === "helperBuilder"));
  assert.ok(calls.some(([type]) => type === "helper"));
  assert.ok(calls.some(([type]) => type === "factory"));
  assert.strictEqual(helperInput, calls.find(([type]) => type === "helperBuilder")[1]);
  assert.strictEqual(wiringInput, calls.find(([type]) => type === "helper")[1]);
  assert.strictEqual(factoryDeps, calls.find(([type]) => type === "factory")[1]);
  assert.strictEqual(helperDeps.state, context.state);
  assert.strictEqual(helperDeps.dom, context.dom);
  assert.strictEqual(helperDeps.window, context.window);
  assert.strictEqual(helperDeps.document, context.document);
  assert.strictEqual(helperDeps.navigator, context.navigator);
  assert.strictEqual(helperDeps.api, context.api);
  assert.strictEqual(helperDeps.flash, context.flash);
  assert.strictEqual(helperDeps.setBusy, context.setBusy);
  assert.strictEqual(helperDeps.escapeHtml, context.escapeHtml);
  assert.strictEqual(helperDeps.formatOrgRoleLabel, context.formatOrgRoleLabel);
  assert.strictEqual(helperDeps.renderInvitationStatus, context.renderInvitationStatus);
  assert.strictEqual(helperDeps.renderOrganizationAdminPanel, context.renderOrganizationAdminPanel);
  assert.strictEqual(helperDeps.canUseAdminMode, context.canUseAdminMode);
  assert.strictEqual(helperDeps.formatDate, context.formatDate);
  assert.strictEqual(helperDeps.formatInvitationStatusLabel, context.formatInvitationStatusLabel);
  assert.strictEqual(helperDeps.formatAccountStatusLabel, context.formatAccountStatusLabel);
  assert.strictEqual(helperDeps.formatMembershipStatusLabel, context.formatMembershipStatusLabel);
  assert.strictEqual(helperDeps.resolveStatusClass, context.resolveStatusClass);
  assert.deepEqual(helperDeps.membershipStatusOptions, context.MEMBERSHIP_STATUS_OPTIONS);
  assert.strictEqual(helperDeps.formatDownloadScopeLabel, context.formatDownloadScopeLabel);
  assert.strictEqual(helperDeps.formatDownloadFormatLabel, context.formatDownloadFormatLabel);
  assert.strictEqual(helperDeps.formatDownloadSourcePageLabel, context.formatDownloadSourcePageLabel);
  assert.strictEqual(helperDeps.platformAdminAccountRuntime, context.PLATFORM_ADMIN_ACCOUNT_RUNTIME);
  assert.strictEqual(helperDeps.syncPlatformAdminAccountDraftFromForm, context.syncPlatformAdminAccountDraftFromForm);
  assert.strictEqual(helperDeps.handlePlatformAdminAccountSubmit, context.handlePlatformAdminAccountSubmit);
  assert.strictEqual(helperDeps.renderOrgAdminRuntimeReloadFallback, context.renderOrgAdminRuntimeReloadFallback);
  assert.strictEqual(helperDeps.canManagePlatformAdminAccounts, context.canManagePlatformAdminAccounts);
  assert.strictEqual(helperDeps.resetOrganizationMemberPassword, context.resetOrganizationMemberPassword);
  assert.strictEqual(helperDeps.requireConsoleDataRuntime, context.requireConsoleDataRuntime);
  assert.strictEqual(helperDeps.getConsoleDataRuntimeDeps, context.getConsoleDataRuntimeDeps);
  assert.strictEqual(helperDeps.requireOrganizationAdminRuntime, context.getOrgAdminRuntime);
  assert.strictEqual(helperDeps.loadSalesClaimSummaryByUser, context.loadSalesClaimSummaryByUser);
  assert.strictEqual(helperDeps.loadClosedSalesClaims, context.loadClosedSalesClaims);
  assert.strictEqual(wiringInput.state, context.state);
  assert.strictEqual(wiringInput.dom, context.dom);
  assert.strictEqual(wiringInput.window, context.window);
  assert.strictEqual(wiringInput.document, context.document);
  assert.strictEqual(wiringInput.navigator, context.navigator);
  assert.strictEqual(wiringInput.api, context.api);
  assert.strictEqual(wiringInput.flash, context.flash);
  assert.strictEqual(wiringInput.setBusy, context.setBusy);
  assert.strictEqual(wiringInput.escapeHtml, context.escapeHtml);
  assert.strictEqual(wiringInput.formatOrgRoleLabel, context.formatOrgRoleLabel);
  assert.strictEqual(wiringInput.renderInvitationStatus, context.renderInvitationStatus);
  assert.strictEqual(wiringInput.renderOrganizationAdminPanel, context.renderOrganizationAdminPanel);
  assert.strictEqual(wiringInput.canUseAdminMode, context.canUseAdminMode);
  assert.strictEqual(wiringInput.formatDate, context.formatDate);
  assert.strictEqual(wiringInput.formatInvitationStatusLabel, context.formatInvitationStatusLabel);
  assert.strictEqual(wiringInput.formatAccountStatusLabel, context.formatAccountStatusLabel);
  assert.strictEqual(wiringInput.formatMembershipStatusLabel, context.formatMembershipStatusLabel);
  assert.strictEqual(wiringInput.resolveStatusClass, context.resolveStatusClass);
  assert.deepEqual(wiringInput.membershipStatusOptions, context.MEMBERSHIP_STATUS_OPTIONS);
  assert.strictEqual(wiringInput.formatDownloadScopeLabel, context.formatDownloadScopeLabel);
  assert.strictEqual(wiringInput.formatDownloadFormatLabel, context.formatDownloadFormatLabel);
  assert.strictEqual(wiringInput.formatDownloadSourcePageLabel, context.formatDownloadSourcePageLabel);
  assert.strictEqual(wiringInput.platformAdminAccountRuntime, context.PLATFORM_ADMIN_ACCOUNT_RUNTIME);
  assert.strictEqual(wiringInput.syncPlatformAdminAccountDraftFromForm, context.syncPlatformAdminAccountDraftFromForm);
  assert.strictEqual(wiringInput.handlePlatformAdminAccountSubmit, context.handlePlatformAdminAccountSubmit);
  assert.strictEqual(wiringInput.renderOrgAdminRuntimeReloadFallback, context.renderOrgAdminRuntimeReloadFallback);
  assert.strictEqual(wiringInput.canManagePlatformAdminAccounts, context.canManagePlatformAdminAccounts);
  assert.strictEqual(wiringInput.resetOrganizationMemberPassword, context.resetOrganizationMemberPassword);
  assert.strictEqual(wiringInput.requireConsoleDataRuntime, context.requireConsoleDataRuntime);
  assert.strictEqual(wiringInput.getConsoleDataRuntimeDeps, context.getConsoleDataRuntimeDeps);
  assert.strictEqual(wiringInput.requireOrganizationAdminRuntime, context.getOrgAdminRuntime);
  assert.strictEqual(wiringInput.loadSalesClaimSummaryByUser, context.loadSalesClaimSummaryByUser);
  assert.strictEqual(wiringInput.loadClosedSalesClaims, context.loadClosedSalesClaims);
  assert.strictEqual(factoryDeps.state, context.state);
  assert.strictEqual(factoryDeps.dom, context.dom);
  assert.strictEqual(factoryDeps.window, context.window);
  assert.strictEqual(factoryDeps.document, context.document);
  assert.strictEqual(factoryDeps.navigator, context.navigator);
  assert.strictEqual(factoryDeps.api, context.api);
  assert.strictEqual(factoryDeps.flash, context.flash);
  assert.strictEqual(factoryDeps.setBusy, context.setBusy);
  assert.strictEqual(factoryDeps.escapeHtml, context.escapeHtml);
  assert.strictEqual(factoryDeps.formatOrgRoleLabel, context.formatOrgRoleLabel);
  assert.strictEqual(factoryDeps.renderInvitationStatus, context.renderInvitationStatus);
  assert.strictEqual(factoryDeps.renderOrganizationAdminPanel, context.renderOrganizationAdminPanel);
  assert.strictEqual(factoryDeps.canUseAdminMode, context.canUseAdminMode);
  assert.strictEqual(factoryDeps.formatDate, context.formatDate);
  assert.strictEqual(factoryDeps.formatInvitationStatusLabel, context.formatInvitationStatusLabel);
  assert.strictEqual(factoryDeps.formatAccountStatusLabel, context.formatAccountStatusLabel);
  assert.strictEqual(factoryDeps.formatMembershipStatusLabel, context.formatMembershipStatusLabel);
  assert.strictEqual(factoryDeps.resolveStatusClass, context.resolveStatusClass);
  assert.deepEqual(factoryDeps.membershipStatusOptions, context.MEMBERSHIP_STATUS_OPTIONS);
  assert.strictEqual(factoryDeps.formatDownloadScopeLabel, context.formatDownloadScopeLabel);
  assert.strictEqual(factoryDeps.formatDownloadFormatLabel, context.formatDownloadFormatLabel);
  assert.strictEqual(factoryDeps.formatDownloadSourcePageLabel, context.formatDownloadSourcePageLabel);
  assert.strictEqual(factoryDeps.platformAdminAccountRuntime, context.PLATFORM_ADMIN_ACCOUNT_RUNTIME);
  assert.strictEqual(factoryDeps.syncPlatformAdminAccountDraftFromForm, context.syncPlatformAdminAccountDraftFromForm);
  assert.strictEqual(factoryDeps.handlePlatformAdminAccountSubmit, context.handlePlatformAdminAccountSubmit);
  assert.strictEqual(factoryDeps.renderOrgAdminRuntimeReloadFallback, context.renderOrgAdminRuntimeReloadFallback);
  assert.strictEqual(factoryDeps.canManagePlatformAdminAccounts, context.canManagePlatformAdminAccounts);
  assert.strictEqual(factoryDeps.resetOrganizationMemberPassword, context.resetOrganizationMemberPassword);
  assert.strictEqual(factoryDeps.requireConsoleDataRuntime, context.requireConsoleDataRuntime);
  assert.strictEqual(factoryDeps.getConsoleDataRuntimeDeps, context.getConsoleDataRuntimeDeps);
  assert.strictEqual(factoryDeps.requireOrganizationAdminRuntime, context.getOrgAdminRuntime);
  assert.strictEqual(factoryDeps.loadSalesClaimSummaryByUser, context.loadSalesClaimSummaryByUser);
  assert.strictEqual(factoryDeps.loadClosedSalesClaims, context.loadClosedSalesClaims);
});

test("console panel wrappers stay thin and delegate to the console controller", () => {
  const source = readAppSource();
  const loadDashboardSummarySource = extractFunction(
    source,
    "async function loadDashboardSummary({ silent = false } = {}) {",
    "function renderDashboard(summary, errorMessage = \"\") {",
  );
  const renderDashboardSource = extractFunction(
    source,
    "function renderDashboard(summary, errorMessage = \"\") {",
    "async function handleRunCreate(event) {",
  );
  const loadProjectsSource = extractFunction(
    source,
    "async function loadProjects({ silent = false } = {}) {",
    "function renderProjects(errorMessage = \"\") {",
  );
  const renderProjectsSource = extractFunction(
    source,
    "function renderProjects(errorMessage = \"\") {",
    "function renderRelatedProjectNotices(project) {",
  );

  assert.match(loadDashboardSummarySource, /controller\.loadDashboardSummary/);
  assert.match(renderDashboardSource, /controller\.renderDashboard/);
  assert.match(loadProjectsSource, /controller\.loadProjects/);
  assert.match(renderProjectsSource, /controller\.renderProjects/);

  assert.doesNotMatch(loadDashboardSummarySource, /api\("\/api\/dashboard\/summary"\)/);
  assert.doesNotMatch(renderDashboardSource, /dashboardMetrics\.innerHTML/);
  assert.doesNotMatch(renderDashboardSource, /dashboardFailedRuns\.innerHTML/);
  assert.doesNotMatch(renderDashboardSource, /dashboardReportJobs\.innerHTML/);
  assert.doesNotMatch(loadProjectsSource, /api\(`\/api\/projects\?/);
  assert.doesNotMatch(renderProjectsSource, /projectList\.innerHTML/);
  assert.doesNotMatch(renderProjectsSource, /addEventListener/);
  assert.doesNotMatch(source, /function loadDashboardSummaryFallback\(/);
  assert.doesNotMatch(source, /function renderDashboardFallback\(/);
  assert.doesNotMatch(source, /function loadProjectsFallback\(/);
  assert.doesNotMatch(source, /function renderProjectsFallback\(/);
  assert.doesNotMatch(source, /function renderRunExecutionContextFallback\(/);
});

test("renderRunExecutionContext delegates through the console controller and stays thin", () => {
  const source = readAppSource();
  const renderRunExecutionContextSource = extractFunction(
    source,
    "function renderRunExecutionContext(run) {",
    "function resolveTrackerExecutionContext(run) {",
  );

  assert.match(renderRunExecutionContextSource, /controller\.renderRunExecutionContext/);
  assert.doesNotMatch(renderRunExecutionContextSource, /resolveTrackerExecutionContext/);
  assert.doesNotMatch(renderRunExecutionContextSource, /RUN_VIEW_RUNTIME\?\.buildRunExecutionContextMarkup/);
  assert.doesNotMatch(renderRunExecutionContextSource, /tracker-export-inline-preview/);
  assert.doesNotMatch(renderRunExecutionContextSource, /artifact-actions/);
  assert.doesNotMatch(renderRunExecutionContextSource, /runExecutionContext\.innerHTML/);

  const harness = createHarness();
  const { context, calls } = harness;
  const run = { id: "run-42", run_type: "tracker_export", status: "running" };
  const rendered = [];
  const domRunExecutionContext = {
    classList: {
      add(token) {
        rendered.push(["add", token]);
      },
      remove(token) {
        rendered.push(["remove", token]);
      },
    },
    dataset: {},
    className: "",
    innerHTML: "",
  };

  context.dom.runExecutionContext = domRunExecutionContext;
  context.renderRunExecutionContext(run);

  assert.deepEqual(calls.console, [["renderRunExecutionContext", run]]);
  assert.deepEqual(rendered, []);
  assert.equal(domRunExecutionContext.className, "");
  assert.equal(domRunExecutionContext.innerHTML, "");
});

test("changeProjectsPage delegates through the console controller and keeps the local fallback", () => {
  const source = readAppSource();
  const changeProjectsPageSource = extractFunction(
    source,
    "function changeProjectsPage(delta) {",
    "async function loadPhaseReport({ silent = false } = {}) {",
  );

  assert.match(changeProjectsPageSource, /APP_SUPPORT\.changeProjectsPage/);
  assert.match(changeProjectsPageSource, /loadProjects,/);

  const { context, calls, getterSource } = createConsoleChangeProjectsHarness();
  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createConsolePanelsControllerDeps"/);
  assert.equal(context.changeProjectsPage(-1), "console-change-projects-page");
  assert.deepEqual(calls, [["factory"], ["changeProjectsPage", -1]]);

  const fallbackHarness = createConsoleChangeProjectsFallbackHarness();
  assert.equal(fallbackHarness.context.changeProjectsPage(1), undefined);
  assert.equal(fallbackHarness.state.projectFilters.page, 3);
  assert.deepEqual(plain(fallbackHarness.calls), [["loadProjects", { silent: true }]]);
});

test("notice viewer wrappers delegate when available and preserve the local fallback otherwise", () => {
  const source = readAppSource();
  assert.match(source, /function renderNoticeViewerPayload\(viewerWindow, payload, fallbackTitle = /);
  assert.match(source, /controller\?\.renderNoticeViewerPayload/);
  assert.match(source, /controller\?\.renderNoticeViewerError/);
  assert.match(source, /controller\?\.renderNoticeViewerWindow/);

  const { context, calls, getterSource } = createNoticeViewerWrapperHarness();
  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createReportPanelsControllerDeps"/);

  const viewerWindow = { id: "viewer-window" };
  const payload = { title: "notice" };
  const errorOptions = { title: "error", errorMessage: "broken", links: [{ href: "/a" }] };
  const windowOptions = { title: "body", meta: "meta", body: "body" };

  assert.equal(context.renderNoticeViewerPayload(viewerWindow, payload, "basic title"), "notice-viewer-payload");
  assert.equal(context.renderNoticeViewerError(viewerWindow, errorOptions), "notice-viewer-error");
  assert.equal(context.renderNoticeViewerWindow(viewerWindow, windowOptions), "notice-viewer-window");
  assert.deepEqual(plain(calls), [
    ["factory"],
    ["renderNoticeViewerPayload", viewerWindow, payload, "basic title"],
    ["renderNoticeViewerError", viewerWindow, errorOptions],
    ["renderNoticeViewerWindow", viewerWindow, windowOptions],
  ]);

  const fallbackHarness = createNoticeViewerFallbackHarness();
  const fallbackPayload = {
    title: "fallback-title",
    project_name: "alpha",
    bid_no: "bid-1",
    bid_ord: "2",
    document_count: 3,
  };

  assert.equal(fallbackHarness.context.renderNoticeViewerPayload(fallbackHarness.targetWindow, fallbackPayload, "basic"), undefined);
  assert.match(fallbackHarness.writes[1], /fallback-title/);

  fallbackHarness.writes.length = 0;
  assert.equal(
    fallbackHarness.context.renderNoticeViewerError(
      fallbackHarness.targetWindow,
      { title: "error-title", errorMessage: "broken" },
    ),
    undefined,
  );
  assert.match(fallbackHarness.writes[1], /error-title/);
});

test("app.js delegates auth ui wrappers to the auth-ui controller runtime", async () => {
  const harness = createAuthUiHarness();
  const { context, calls } = harness;
  const getterSource = extractFunction(
    readAppSource(),
    "function getAuthUiController() {",
    "function getSalesPanelController() {",
  );
  const submitEvent = { type: "submit" };

  assert.deepEqual(context.syncAuthFormWithInvitationPreview(), { ok: "syncAuthFormWithInvitationPreview" });
  assert.deepEqual(context.renderAuthInvitationPreview(), { ok: "renderAuthInvitationPreview" });
  assert.deepEqual(context.renderAuthUi(), { ok: "renderAuthUi" });
  assert.deepEqual(context.renderProfileStatus("message", "error"), { ok: "renderProfileStatus" });
  assert.deepEqual(context.syncProfileDialogWithSession(), { ok: "syncProfileDialogWithSession" });
  assert.deepEqual(context.openProfileDialog(), { ok: "openProfileDialog" });
  assert.deepEqual(context.closeProfileDialog(), { ok: "closeProfileDialog" });
  assert.deepEqual(await context.handleProfileSubmit(submitEvent), { ok: "handleProfileSubmit" });
  assert.deepEqual(await context.handleAuthSubmit(submitEvent), { ok: "handleAuthSubmit" });
  assert.deepEqual(context.handleAuthFindId(), { ok: "handleAuthFindId" });
  assert.deepEqual(await context.handleAuthPasswordReset(), { ok: "handleAuthPasswordReset" });
  assert.deepEqual(await context.handleAuthSignOut(), { ok: "handleAuthSignOut" });

  assert.equal(harness.factoryCalls, 1);
  assertAuthUiControllerDeps(harness.factoryDeps, context);
  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createAuthUiControllerDeps"/);
  assert.match(getterSource, /syncUiModeChrome: \(\) => getUiModeController\(\)\.syncUiModeChrome\(\)/);
  assert.match(
    getterSource,
    /applyUiModeTransition: \(adminMode, options = \{\}\) => getUiModeController\(\)\.applyUiModeTransition\(adminMode, options\)/,
  );
  assert.deepEqual(calls.map(([name]) => name), [
    "factory",
    "syncAuthFormWithInvitationPreview",
    "renderAuthInvitationPreview",
    "renderAuthUi",
    "renderProfileStatus",
    "syncProfileDialogWithSession",
    "openProfileDialog",
    "closeProfileDialog",
    "handleProfileSubmit",
    "handleAuthSubmit",
    "handleAuthFindId",
    "handleAuthPasswordReset",
    "handleAuthSignOut",
  ]);
});

test("app.js delegates ui mode chrome and transition work to the ui-mode controller runtime", () => {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const appSupportCalls = [];
  const getterSource = extractFunction(
    source,
    "function getUiModeController() {",
    "function getAuthController() {",
  );
  const applyUiModeSource = extractFunction(
    source,
    "function applyUiMode({ renderAuth = true } = {}) {",
    "function clearUserModeRunSelection({ sync = false } = {}) {",
  );
  const toggleUiModeSource = extractFunction(
    source,
    "function toggleUiMode() {",
    "function syncUiModeFromLocation() {",
  );
  const syncUiModeFromLocationSource = extractFunction(
    source,
    "function syncUiModeFromLocation() {",
    "function useGlobalTrackerEntriesScope() {",
  );

  assert.match(getterSource, /UI_MODE_CONTROLLER_RUNTIME\?\.createUiModeController/);
  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createUiModeControllerDeps"/);
  assert.match(applyUiModeSource, /const controller = getUiModeController\(\);/);
  assert.match(applyUiModeSource, /return controller\.applyUiMode\(\{ renderAuth \}\);/);
  assert.match(toggleUiModeSource, /return getUiModeController\(\)\.toggleUiMode\(\);/);
  assert.match(syncUiModeFromLocationSource, /return getUiModeController\(\)\.syncUiModeFromLocation\(\);/);
  assert.doesNotMatch(applyUiModeSource, /syncUiModeChrome\(\)/);
  assert.doesNotMatch(applyUiModeSource, /applyUiModeTransition\(/);
  assert.doesNotMatch(applyUiModeSource, /renderTrackerEntries\(state\.trackerEntries/);
  assert.doesNotMatch(applyUiModeSource, /renderSalesSummaryPanel\(\);/);
  assert.doesNotMatch(toggleUiModeSource, /clearAdminLegacyRouteIntent\(/);
  assert.doesNotMatch(syncUiModeFromLocationSource, /new URLSearchParams/);

  const calls = [];
  let factoryDeps = null;
  const controller = {
    applyUiMode(options) {
      calls.push(["applyUiMode", options]);
      return { options };
    },
    syncUiModeChrome() {
      calls.push(["syncUiModeChrome"]);
      return true;
    },
    applyUiModeTransition(adminMode, options) {
      calls.push(["applyUiModeTransition", adminMode, options]);
      return { adminMode, options };
    },
    toggleUiMode() {
      calls.push(["toggleUiMode"]);
      return "toggle-ui-mode";
    },
    syncUiModeFromLocation() {
      calls.push(["syncUiModeFromLocation"]);
      return "sync-ui-mode";
    },
  };

  const context = vm.createContext({
    console,
    window: {
      __SPMS_TEST_MODE__: false,
    },
    APP_SUPPORT: createAppSupportStub(appSupportCalls),
    UI_MODE_CONTROLLER_RUNTIME: {
      createUiModeController(deps) {
        factoryDeps = deps;
        calls.push(["factory", deps]);
        return controller;
      },
    },
    uiModeController: null,
    state: {
      uiMode: "admin",
      adminTab: "project-status",
      trackerChangeEventsWarmupHandle: null,
    },
    dom: {
      layoutGrid: { classList: { toggle() {} } },
    },
    DEFAULT_ADMIN_TAB: "project-status",
    APP_ROOT_PATH: "/app/",
    normalizeLocationPath: (value) => String(value || ""),
    getAdminRoutePath: () => "/app/project-status",
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => false,
    shouldShowAdminModeToggle: () => true,
    shouldShowSharedGoogleSheetsShell: () => false,
    isPendingLegacyAdminAlias: () => false,
    clearAdminLegacyRouteIntent: () => {},
    getAdminTabByPathname: () => null,
    resolveUiModeFromLocation: () => "user",
    resolveLegacyAdminRoutePath: () => "",
    normalizeAdminTab: (value) => value,
    clearAdminGoogleSheetPopupStateForTab: () => false,
    syncUrlState: () => {},
    maybePreloadAdminGoogleSheetsBootstrap: () => {},
    syncTrackerChangeBellVisibility: () => {},
    hydrateTrackerChangeEventsCache: () => {},
    renderTrackerChangeEventUnreadCount: () => {},
    renderTrackerChangeBellPopover: () => {},
    renderAdminTopNavigation: () => {},
    renderAdminEmbedPanel: () => {},
    renderTrackerTemplateStatus: () => {},
    loadAdminConsoleData: async () => {},
    loadBackfillConflicts: async () => {},
    renderBackfillConflictsPanel: () => {},
    closeDrawer: () => {},
    renderAuthUi: () => {},
    renderOrganizationAdminPanel: () => {},
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderRunDetail: () => {},
    renderTrackerEntries: () => {},
    loadOrganizationUsers: async () => {},
    loadTrackerEntries: async () => {},
    loadTrackerChangeEventUnreadCount: async () => {},
    loadTrackerChangeEvents: async () => {},
    clearUserModeRunSelection: () => {},
    hydrateHomeBootstrapCache: () => {},
    loadHomeBootstrap: async () => {},
    scheduleTrackerChangeEventsWarmup: () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${applyUiModeSource}\n${toggleUiModeSource}\n${syncUiModeFromLocationSource}`, context, { filename: appPath });
  context.applyUiMode();
  assert.equal(context.toggleUiMode(), "toggle-ui-mode");
  assert.equal(context.syncUiModeFromLocation(), "sync-ui-mode");

  assert.deepEqual(appSupportCalls, ["createUiModeControllerDepsHelpers"]);
  assert.equal(calls[0][0], "factory");
  assert.ok(factoryDeps);
  assert.strictEqual(factoryDeps.state, context.state);
  assert.strictEqual(factoryDeps.dom, context.dom);
  assert.strictEqual(factoryDeps.window, context.window);
  assert.strictEqual(factoryDeps.DEFAULT_ADMIN_TAB, context.DEFAULT_ADMIN_TAB);
  assert.strictEqual(factoryDeps.APP_ROOT_PATH, context.APP_ROOT_PATH);
  assert.strictEqual(factoryDeps.normalizeLocationPath, context.normalizeLocationPath);
  assert.strictEqual(factoryDeps.getAdminRoutePath, context.getAdminRoutePath);
  assert.strictEqual(factoryDeps.syncUrlState, context.syncUrlState);
  assert.strictEqual(factoryDeps.canUseAdminMode, context.canUseAdminMode);
  assert.strictEqual(factoryDeps.canLoadProtectedConsoleData, context.canLoadProtectedConsoleData);
  assert.strictEqual(factoryDeps.shouldShowAdminModeToggle, context.shouldShowAdminModeToggle);
  assert.strictEqual(factoryDeps.shouldShowSharedGoogleSheetsShell, context.shouldShowSharedGoogleSheetsShell);
  assert.strictEqual(factoryDeps.isPendingLegacyAdminAlias, context.isPendingLegacyAdminAlias);
  assert.strictEqual(factoryDeps.clearAdminLegacyRouteIntent, context.clearAdminLegacyRouteIntent);
  assert.strictEqual(factoryDeps.getAdminTabByPathname, context.getAdminTabByPathname);
  assert.strictEqual(factoryDeps.resolveUiModeFromLocation, context.resolveUiModeFromLocation);
  assert.strictEqual(factoryDeps.resolveLegacyAdminRoutePath, context.resolveLegacyAdminRoutePath);
  assert.strictEqual(factoryDeps.normalizeAdminTab, context.normalizeAdminTab);
  assert.strictEqual(factoryDeps.clearAdminGoogleSheetPopupStateForTab, context.clearAdminGoogleSheetPopupStateForTab);
  assert.equal(calls[1][0], "applyUiMode");
  assert.deepEqual(JSON.parse(JSON.stringify(calls[1][1])), { renderAuth: true });
  assert.equal(calls[2][0], "toggleUiMode");
  assert.equal(calls[3][0], "syncUiModeFromLocation");
});

test("getUiModeController fails fast when the ui mode wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getUiModeController() {",
    "function getAuthController() {",
  );

  const context = vm.createContext({
    console,
    window: {},
    UI_MODE_CONTROLLER_RUNTIME: {
      createUiModeController() {
        return {};
      },
    },
    uiModeController: null,
    state: {},
    dom: {},
    DEFAULT_ADMIN_TAB: "project-status",
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => false,
    shouldShowAdminModeToggle: () => true,
    shouldShowSharedGoogleSheetsShell: () => false,
    isPendingLegacyAdminAlias: () => false,
    maybePreloadAdminGoogleSheetsBootstrap: () => {},
    syncTrackerChangeBellVisibility: () => {},
    hydrateTrackerChangeEventsCache: () => {},
    renderTrackerChangeEventUnreadCount: () => {},
    renderTrackerChangeBellPopover: () => {},
    renderAdminTopNavigation: () => {},
    renderAdminEmbedPanel: () => {},
    renderTrackerTemplateStatus: () => {},
    loadAdminConsoleData: async () => {},
    loadBackfillConflicts: async () => {},
    renderBackfillConflictsPanel: () => {},
    closeDrawer: () => {},
    renderAuthUi: () => {},
    renderOrganizationAdminPanel: () => {},
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderRunDetail: () => {},
    renderTrackerEntries: () => {},
    loadOrganizationUsers: async () => {},
    loadTrackerEntries: async () => {},
    loadTrackerChangeEventUnreadCount: async () => {},
    loadTrackerChangeEvents: async () => {},
    clearUserModeRunSelection: () => {},
    hydrateHomeBootstrapCache: () => {},
    loadHomeBootstrap: async () => {},
    scheduleTrackerChangeEventsWarmup: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getUiModeController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("app.js delegates auth session bootstrap wrappers to the auth controller runtime", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getAuthController() {",
    "function getAuthUiController() {",
  );
  const initializeAuthGateSource = extractFunction(
    source,
    "async function initializeAuthGate() {",
    "async function loadInvitationPreview({ silent = false } = {}) {",
  );
  const loadInvitationPreviewSource = extractFunction(
    source,
    "async function loadInvitationPreview({ silent = false } = {}) {",
    "async function loadInvitationPreviewByEmail(email, { silent = false } = {}) {",
  );
  const loadInvitationPreviewByEmailSource = extractFunction(
    source,
    "async function loadInvitationPreviewByEmail(email, { silent = false } = {}) {",
    "function scheduleInvitationPreviewLookup(email) {",
  );
  const scheduleInvitationPreviewLookupSource = extractFunction(
    source,
    "function scheduleInvitationPreviewLookup(email) {",
    "async function importAuthSessionFromLocationHash() {",
  );
  const importAuthSessionFromLocationHashSource = extractFunction(
    source,
    "async function importAuthSessionFromLocationHash() {",
    "async function acceptPendingInvitationToken({ silent = false } = {}) {",
  );
  const acceptPendingInvitationTokenSource = extractFunction(
    source,
    "async function acceptPendingInvitationToken({ silent = false } = {}) {",
    "function applyAuthSession(session) {",
  );
  const applyAuthSessionSource = extractFunction(
    source,
    "function applyAuthSession(session) {",
    "async function performAuthSessionRefresh({ silent = false } = {}) {",
  );
  const performAuthSessionRefreshSource = extractFunction(
    source,
    "async function performAuthSessionRefresh({ silent = false } = {}) {",
    "function refreshAuthSessionState({ silent = false, force = false } = {}) {",
  );
  const setAuthModeSource = extractFunction(
    source,
    "function setAuthMode(mode) {",
    "function bindEvents() {",
  );

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createAuthControllerDeps"/);
  assert.match(getterSource, /getAuthControllerDepsHelpers\(\)\.buildAuthControllerDeps\(\)/);
  assert.match(getterSource, /getTrackerController:\s*\(\)\s*=>\s*getTrackerController\(\)/);
  assert.match(getterSource, /syncUiModeChrome:\s*\(\)\s*=>\s*getUiModeController\(\)\.syncUiModeChrome\(\)/s);
  assert.match(getterSource, /applyUiModeTransition:\s*\(adminMode,\s*options = \{\}\)\s*=>\s*getUiModeController\(\)\.applyUiModeTransition\(adminMode,\s*options\)/s);
  assert.doesNotMatch(getterSource, /loadOrganizationUsers:/);
  assert.doesNotMatch(getterSource, /renderTrackerEntries:/);
  assert.match(initializeAuthGateSource, /const initialized = await getAuthController\(\)\.initializeAuthGate\(\);/);
  assert.match(initializeAuthGateSource, /if \(initialized\) \{/);
  assert.match(initializeAuthGateSource, /syncUiModeFromLocation\(\);/);
  assert.match(initializeAuthGateSource, /applyUiMode\(\);/);
  assert.doesNotMatch(initializeAuthGateSource, /\/api\/auth\/session/);
  assert.match(loadInvitationPreviewSource, /getAuthController\(\)\.loadInvitationPreview\(\{ silent \}\)/);
  assert.match(loadInvitationPreviewByEmailSource, /getAuthController\(\)\.loadInvitationPreviewByEmail\(email, \{ silent \}\)/);
  assert.match(scheduleInvitationPreviewLookupSource, /getAuthController\(\)\.scheduleInvitationPreviewLookup\(email\)/);
  assert.match(importAuthSessionFromLocationHashSource, /getAuthController\(\)\.importAuthSessionFromLocationHash\(\)/);
  assert.match(acceptPendingInvitationTokenSource, /getAuthController\(\)\.acceptPendingInvitationToken\(\{ silent \}\)/);
  assert.match(applyAuthSessionSource, /getAuthController\(\)\.applyAuthSession\(session\)/);
  assert.match(performAuthSessionRefreshSource, /await getAuthController\(\)\.refreshAuthSessionState\(\{ silent \}\)/);
  assert.match(performAuthSessionRefreshSource, /syncUiModeFromLocation\(\);/);
  assert.match(performAuthSessionRefreshSource, /applyUiMode\(\);/);
  assert.doesNotMatch(performAuthSessionRefreshSource, /\/api\/auth\/session/);
  assert.match(setAuthModeSource, /getAuthController\(\)\.setAuthMode\(mode\)/);
});

test("getAuthUiController fails fast when the auth ui controller factory is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getAuthUiController() {",
    "function getSalesPanelController() {",
  );

  const context = vm.createContext({
    console,
    window: {},
    authUiController: null,
    state: { auth: {}, profileDialog: {} },
    dom: {},
    document: {},
    api: async () => {},
    flash() {},
    setBusy() {},
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    requireAuthSessionRuntime: () => ({ runtime: true }),
    loadOrganizationUsers: async () => {},
    loadOrganizationMembers: async () => {},
    loadSalesOverview: async () => {},
    loadMySalesClaims: async () => {},
    refreshSalesAdminPanels: async () => {},
    shouldShowSignUpMode: () => true,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    syncUiModeChrome: () => false,
    applyUiModeTransition() {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getAuthUiController(),
    /AUTH_UI_CONTROLLER\.createAuthUiController/,
  );
});

test("getAuthUiController fails fast when the auth ui wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getAuthUiController() {",
    "function getSalesPanelController() {",
  );

  const context = vm.createContext({
    console,
    window: {
      AUTH_UI_CONTROLLER: {
        createAuthUiController() {
          return {};
        },
      },
    },
    authUiController: null,
    state: { auth: {}, profileDialog: {} },
    dom: {},
    document: {},
    api: async () => {},
    flash() {},
    setBusy() {},
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    requireAuthSessionRuntime: () => ({ runtime: true }),
    loadOrganizationUsers: async () => {},
    loadOrganizationMembers: async () => {},
    loadSalesOverview: async () => {},
    loadMySalesClaims: async () => {},
    refreshSalesAdminPanels: async () => {},
    ensureConsoleInitialized: async () => {},
    shouldShowSignUpMode: () => true,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    syncUiModeChrome: () => false,
    applyUiModeTransition() {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getAuthUiController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("getSalesPanelController fails fast when the sales panel controller factory is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getSalesPanelController() {",
    "const dom = createAppDom(document);",
  );

  const context = vm.createContext({
    console,
    window: {},
    salesPanelController: null,
    dom: {},
    state: {},
    api: async () => {},
    escapeHtml: (value) => String(value ?? ""),
    getLatestSalesNoteItem: () => null,
    truncate: (value) => String(value ?? ""),
    formatSalesNoteTextForDisplay: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    getSalesNoteEntries: () => [],
    getSalesYearMonthBucket: () => null,
    formatContractAmountDisplay: (value) => String(value ?? ""),
    extractContractAmountTextFromSalesNote: () => "",
    salesClaimStatusLabel: (value) => String(value ?? ""),
    getVisibleSalesProjectIds: () => [],
    getSalesClaimForProject: () => null,
    getTrackerProjectSnapshot: () => null,
    renderUserSalesProjectFacts: () => "",
    isCurrentUserClaimOwner: () => false,
    canCurrentUserForceRelease: () => false,
    canCurrentUserManageClaim: () => false,
    isActiveSalesClaim: () => false,
    getOrganizationTransferTargets: () => [],
    getSalesNoteDraft: () => "",
    setSalesNoteDraft: () => {},
    upsertSalesClaim: () => {},
    replaceVisibleSalesClaims: () => {},
    mergeActiveSalesClaims: () => {},
    renderUserOwnedSalesClaimCard: () => "",
    formatSalesClaimEstimateLabel: () => "",
    renderCompanySalesClaimCard: () => "",
    renderUserTrackerClaimSection: () => "",
    formatEstimatedAmountRangeFromKrw: () => "",
    claimSalesProject: async () => {},
    saveSalesClaimNote: async () => {},
    transferSalesClaim: async () => {},
    closeSalesClaim: async () => {},
    adminDeleteLatestSalesNote: async () => {},
    releaseSalesClaim: async () => {},
    formatContractAmountInput: (value) => String(value ?? ""),
    buildUserSalesProjectFactsMarkup: () => "",
    buildSalesClaimEstimateLabelMarkup: () => "",
    buildUserOwnedSalesClaimCardMarkup: () => "",
    buildCompanySalesClaimCardMarkup: () => "",
    buildUserTrackerClaimSectionMarkup: () => "",
    formatEokValue: (value) => String(value ?? ""),
    getSalesNoteTimeline: () => [],
    serializeSalesNoteEntry: (value) => String(value ?? ""),
    removeLatestSalesNoteEntry: () => [],
    isAdminRole: () => false,
    renderTrackerEntries: () => {},
    loadSalesOverview: async () => {},
    loadMySalesClaims: async () => {},
    loadVisibleSalesClaims: async () => {},
    refreshSalesAdminPanels: async () => {},
    SALES_VIEW_RUNTIME: null,
    flash: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getSalesPanelController(),
    /SALES_PANEL_CONTROLLER\.createSalesPanelController/,
  );
});

test("auth ui wrappers stay thin and do not keep inline auth/profile behavior in app.js", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getAuthUiController() {",
    "function getSalesPanelController() {",
  );
  const applyAuthSessionSource = extractFunction(
    source,
    "function applyAuthSession(session) {",
    "async function performAuthSessionRefresh(",
  );
  const syncAuthFormSource = extractFunction(
    source,
    "function syncAuthFormWithInvitationPreview() {",
    "function renderAuthInvitationPreview() {",
  );
  const renderAuthInvitationPreviewSource = extractFunction(
    source,
    "function renderAuthInvitationPreview() {",
    "function renderAuthUi() {",
  );
  const renderAuthUiSource = extractFunction(
    source,
    "function renderAuthUi() {",
    "function formatContractAmountInput(rawValue) {",
  );
  const renderProfileStatusSource = extractFunction(
    source,
    "function renderProfileStatus(message = \"\", level = \"\") {",
    "function renderInvitationStatus(message = \"\", level = \"\") {",
  );
  const syncProfileDialogSource = extractFunction(
    source,
    "function syncProfileDialogWithSession() {",
    "function openProfileDialog() {",
  );
  const openProfileDialogSource = extractFunction(
    source,
    "function openProfileDialog() {",
    "function closeProfileDialog() {",
  );
  const closeProfileDialogSource = extractFunction(
    source,
    "function closeProfileDialog() {",
    "async function handleProfileSubmit(event) {",
  );
  const handleProfileSubmitSource = extractFunction(
    source,
    "async function handleProfileSubmit(event) {",
    "async function handleAuthSubmit(event) {",
  );
  const handleAuthSubmitSource = extractFunction(
    source,
    "async function handleAuthSubmit(event) {",
    "function handleAuthFindId() {",
  );
  const handleAuthFindIdSource = extractFunction(
    source,
    "function handleAuthFindId() {",
    "async function handleAuthPasswordReset() {",
  );
  const handleAuthPasswordResetSource = extractFunction(
    source,
    "async function handleAuthPasswordReset() {",
    "async function handleAuthSignOut() {",
  );
  const handleAuthSignOutSource = extractFunction(
    source,
    "async function handleAuthSignOut() {",
    "function extractDownloadFilename(response, fallbackName) {",
  );

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createAuthUiControllerDeps"/);
  assert.match(applyAuthSessionSource, /getAuthController\(\)\.applyAuthSession/);
  assert.match(syncAuthFormSource, /controller\?\.syncAuthFormWithInvitationPreview/);
  assert.match(renderAuthInvitationPreviewSource, /controller\?\.renderAuthInvitationPreview/);
  assert.match(renderAuthUiSource, /controller\?\.renderAuthUi/);
  assert.match(renderProfileStatusSource, /controller\?\.renderProfileStatus/);
  assert.match(syncProfileDialogSource, /controller\?\.syncProfileDialogWithSession/);
  assert.match(openProfileDialogSource, /controller\?\.openProfileDialog/);
  assert.match(closeProfileDialogSource, /controller\?\.closeProfileDialog/);
  assert.match(handleProfileSubmitSource, /controller\?\.handleProfileSubmit/);
  assert.match(handleAuthSubmitSource, /controller\?\.handleAuthSubmit/);
  assert.match(handleAuthFindIdSource, /controller\?\.handleAuthFindId/);
  assert.match(handleAuthPasswordResetSource, /controller\?\.handleAuthPasswordReset/);
  assert.match(handleAuthSignOutSource, /controller\?\.handleAuthSignOut/);

  assert.doesNotMatch(applyAuthSessionSource, /normalizeAuthSession/);
  assert.match(applyAuthSessionSource, /getAuthController\(\)\.applyAuthSession/);
  assert.doesNotMatch(syncAuthFormSource, /buildAuthFormFieldViewModel/);
  assert.doesNotMatch(renderAuthInvitationPreviewSource, /buildAuthInvitationPreviewViewModel/);
  assert.doesNotMatch(renderAuthUiSource, /buildAuthUiViewModel/);
  assert.doesNotMatch(renderProfileStatusSource, /buildProfileStatusViewModel/);
  assert.doesNotMatch(syncProfileDialogSource, /buildProfileDialogViewModel/);
  assert.doesNotMatch(openProfileDialogSource, /profileDialog\.classList\.remove/);
  assert.doesNotMatch(closeProfileDialogSource, /profileForm\.reset/);
  assert.doesNotMatch(handleProfileSubmitSource, /api\("\/api\/auth\/profile"/);
  assert.doesNotMatch(handleAuthSubmitSource, /api\("\/api\/auth\/sign-(in|up)"/);
  assert.doesNotMatch(handleAuthFindIdSource, /로그인 아이디는 초대/);
  assert.doesNotMatch(handleAuthPasswordResetSource, /api\("\/api\/auth\/password-reset"/);
  assert.doesNotMatch(handleAuthSignOutSource, /api\("\/api\/auth\/sign-out"/);
  assert.doesNotMatch(handleAuthSignOutSource, /organizationUsers = \[\]/);
});

test("app.js delegates sales panel wrappers to the sales panel controller runtime", async () => {
  const harness = createSalesPanelHarness();
  const { context, calls } = harness;
  const entry = { project_id: "P-7" };
  const closeOptions = { contractAmountText: "9억" };

  assert.deepEqual(context.renderSalesSummaryPanel(), { ok: "renderSalesSummaryPanel" });
  assert.deepEqual(context.renderMySalesClaimsPanel(), { ok: "renderMySalesClaimsPanel" });
  assert.deepEqual(context.bindUserSalesSectionEvents(), { ok: "bindUserSalesSectionEvents" });
  assert.deepEqual(await context.claimSalesProject(entry), { ok: "claimSalesProject", entry });
  assert.deepEqual(await context.saveSalesClaimNote("P-7"), { ok: "saveSalesClaimNote", projectId: "P-7" });
  assert.deepEqual(await context.transferSalesClaim("P-7", "U-2"), { ok: "transferSalesClaim", projectId: "P-7", targetUserId: "U-2" });
  const closeResult = await context.closeSalesClaim("P-7", "won", closeOptions);
  assert.equal(closeResult.ok, "closeSalesClaim");
  assert.equal(closeResult.projectId, "P-7");
  assert.equal(closeResult.outcome, "won");
  assert.equal(closeResult.options.contractAmountText, closeOptions.contractAmountText);
  assert.deepEqual(context.renderSalesClaimSection(entry), { ok: "renderSalesClaimSection", entry });
  assert.deepEqual(context.openSalesCloseDialog("P-7"), { ok: "openSalesCloseDialog", projectId: "P-7" });
  assert.deepEqual(context.closeSalesCloseDialog(), { ok: "closeSalesCloseDialog" });
  assert.deepEqual(await context.confirmSalesCloseDialog(), { ok: "confirmSalesCloseDialog" });

  assert.deepEqual(calls.slice(0, 7), [
    ["factory"],
    ["renderSalesSummaryPanel"],
    ["renderMySalesClaimsPanel"],
    ["bindUserSalesSectionEvents"],
    ["claimSalesProject", entry],
    ["saveSalesClaimNote", "P-7"],
    ["transferSalesClaim", "P-7", "U-2"],
  ]);
  assert.equal(calls[7][0], "closeSalesClaim");
  assert.equal(calls[7][1], "P-7");
  assert.equal(calls[7][2], "won");
  assert.equal(calls[7][3].contractAmountText, closeOptions.contractAmountText);
  assert.deepEqual(calls.slice(8), [
    ["renderSalesClaimSection", entry],
    ["openSalesCloseDialog", "P-7"],
    ["closeSalesCloseDialog"],
    ["confirmSalesCloseDialog"],
  ]);
});

test("sales panel wrappers stay thin and remove the old inline sales logic from app.js", async () => {
  const source = readAppSource();
  const renderSalesSummaryPanelSource = extractFunction(
    source,
    "function renderSalesSummaryPanel() {",
    "function renderMySalesClaimsPanel() {",
  );
  const renderMySalesClaimsPanelSource = extractFunction(
    source,
    "function renderMySalesClaimsPanel() {",
    "function bindUserSalesSectionEvents() {",
  );
  const renderUserOwnedSalesClaimCardSource = extractFunction(
    source,
    "function renderUserOwnedSalesClaimCard(claim, index) {",
    "function renderCompanySalesClaimCard(claim, index) {",
  );
  const renderCompanySalesClaimCardSource = extractFunction(
    source,
    "function renderCompanySalesClaimCard(claim, index) {",
    "function renderUserTrackerClaimSection(entry, {",
  );
  const renderUserTrackerClaimSectionSource = extractFunction(
    source,
    "function renderUserTrackerClaimSection(entry, {",
    "function bindUserSalesSectionEvents() {",
  );
  const salesGetterSource = extractFunction(
    source,
    "function getSalesPanelController() {",
    "const dom = createAppDom(document);",
  );
  const bindUserSalesSectionEventsSource = extractFunction(
    source,
    "function bindUserSalesSectionEvents() {",
    "function formatShortDateTime(value) {",
  );
  const claimSalesProjectSource = extractFunction(
    source,
    "async function claimSalesProject(entry) {",
    "async function saveSalesClaimNote(projectId) {",
  );
  const saveSalesClaimNoteSource = extractFunction(
    source,
    "async function saveSalesClaimNote(projectId) {",
    "async function transferSalesClaim(projectId, targetUserId) {",
  );
  const transferSalesClaimSource = extractFunction(
    source,
    "async function transferSalesClaim(projectId, targetUserId) {",
    "async function closeSalesClaim(projectId, outcome, { contractAmountText = \"\" } = {}) {",
  );
  const closeSalesClaimSource = extractFunction(
    source,
    "async function closeSalesClaim(projectId, outcome, { contractAmountText = \"\" } = {}) {",
    "async function adminDeleteLatestSalesNote(projectId, rawSalesNote) {",
  );
  const adminDeleteLatestSalesNoteSource = extractFunction(
    source,
    "async function adminDeleteLatestSalesNote(projectId, rawSalesNote) {",
    "async function releaseSalesClaim(projectId, { force = false } = {}) {",
  );
  const releaseSalesClaimSource = extractFunction(
    source,
    "async function releaseSalesClaim(projectId, { force = false } = {}) {",
    "function renderSalesClaimSection(entry) {",
  );
  const renderSalesClaimSectionSource = extractFunction(
    source,
    "function renderSalesClaimSection(entry) {",
    "function buildTrackerEntryCardMarkupFallback(payload = {}, helpers = {}) {",
  );
  const openSalesCloseDialogSource = extractFunction(
    source,
    "function openSalesCloseDialog(projectId) {",
    "function closeSalesCloseDialog() {",
  );
  const closeSalesCloseDialogSource = extractFunction(
    source,
    "function closeSalesCloseDialog() {",
    "async function confirmSalesCloseDialog() {",
  );
  const confirmSalesCloseDialogSource = extractFunction(
    source,
    "async function confirmSalesCloseDialog() {",
    "function renderProfileStatus(message = \"\", level = \"\") {",
  );

  assert.match(salesGetterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(salesGetterSource, /wiringDepsFactoryName:\s*"createSalesPanelControllerDeps"/);
  assert.match(salesGetterSource, /depsFactory: \(\) => getSalesPanelDepsHelpers\(\)\.buildSalesPanelControllerDeps\(\)/);
  assert.match(salesGetterSource, /missingFactoryError:\s*"Missing sales panel controller runtime: window\.SALES_PANEL_CONTROLLER\.createSalesPanelController"/);
  assert.match(renderUserOwnedSalesClaimCardSource, /return getSalesPanelController\(\)\.renderUserOwnedSalesClaimCard\(claim, index\);/);
  assert.match(renderCompanySalesClaimCardSource, /return getSalesPanelController\(\)\.renderCompanySalesClaimCard\(claim, index\);/);
  assert.match(renderUserTrackerClaimSectionSource, /return getSalesPanelController\(\)\.renderUserTrackerClaimSection\(entry, \{/);
  assert.match(renderSalesSummaryPanelSource, /return controller\.renderSalesSummaryPanel\(\);/);
  assert.match(renderMySalesClaimsPanelSource, /return controller\.renderMySalesClaimsPanel\(\);/);
  assert.match(bindUserSalesSectionEventsSource, /return controller\.bindUserSalesSectionEvents\(\);/);
  assert.match(claimSalesProjectSource, /const controller = getSalesPanelController\(\);/);
  assert.match(claimSalesProjectSource, /return controller\.claimSalesProject\(entry\);/);
  assert.match(saveSalesClaimNoteSource, /const controller = getSalesPanelController\(\);/);
  assert.match(saveSalesClaimNoteSource, /return controller\.saveSalesClaimNote\(projectId\);/);
  assert.match(transferSalesClaimSource, /const controller = getSalesPanelController\(\);/);
  assert.match(transferSalesClaimSource, /return controller\.transferSalesClaim\(projectId, targetUserId\);/);
  assert.match(closeSalesClaimSource, /const controller = getSalesPanelController\(\);/);
  assert.match(closeSalesClaimSource, /return controller\.closeSalesClaim\(projectId, outcome, \{ contractAmountText \}\);/);
  assert.match(adminDeleteLatestSalesNoteSource, /const controller = getSalesPanelController\(\);/);
  assert.match(adminDeleteLatestSalesNoteSource, /return controller\.adminDeleteLatestSalesNote\(projectId, rawSalesNote\);/);
  assert.match(releaseSalesClaimSource, /const controller = getSalesPanelController\(\);/);
  assert.match(releaseSalesClaimSource, /return controller\.releaseSalesClaim\(projectId, \{ force \}\);/);
  assert.match(renderSalesClaimSectionSource, /return controller\.renderSalesClaimSection\(entry\);/);
  assert.match(openSalesCloseDialogSource, /return controller\.openSalesCloseDialog\(projectId\);/);
  assert.match(closeSalesCloseDialogSource, /return controller\.closeSalesCloseDialog\(\);/);
  assert.match(confirmSalesCloseDialogSource, /return controller\.confirmSalesCloseDialog\(\);/);

  assert.doesNotMatch(renderSalesSummaryPanelSource, /salesSummaryList\.innerHTML/);
  assert.doesNotMatch(renderSalesSummaryPanelSource, /querySelectorAll/);
  assert.doesNotMatch(renderSalesSummaryPanelSource, /renderClosedSalesArchiveSection/);
  assert.doesNotMatch(renderMySalesClaimsPanelSource, /trackerUserSalesList\.innerHTML/);
  assert.doesNotMatch(renderMySalesClaimsPanelSource, /classList\.toggle/);
  assert.doesNotMatch(renderUserOwnedSalesClaimCardSource, /projectId = String/);
  assert.doesNotMatch(renderUserOwnedSalesClaimCardSource, /noteDraft = getSalesNoteDraft/);
  assert.doesNotMatch(renderUserOwnedSalesClaimCardSource, /buildUserOwnedSalesClaimCardMarkup/);
  assert.doesNotMatch(renderCompanySalesClaimCardSource, /getSalesNoteTimeline/);
  assert.doesNotMatch(renderCompanySalesClaimCardSource, /buildCompanySalesClaimCardMarkup/);
  assert.doesNotMatch(renderUserTrackerClaimSectionSource, /buildUserTrackerClaimSectionMarkup/);
  assert.doesNotMatch(bindUserSalesSectionEventsSource, /addEventListener/);
  assert.doesNotMatch(bindUserSalesSectionEventsSource, /querySelectorAll/);
  assert.doesNotMatch(claimSalesProjectSource, /\/api\/sales-claims\/projects\/.*\/claim/);
  assert.doesNotMatch(claimSalesProjectSource, /salesClaimSavingProjectIds/);
  assert.doesNotMatch(claimSalesProjectSource, /영업을 시작했다|이미 본인이 담당 중인 프로젝트다|project_id가 없는 행은 영업 대상 지정이 불가능합니다/);
  assert.doesNotMatch(saveSalesClaimNoteSource, /\/api\/sales-claims\/projects\//);
  assert.doesNotMatch(saveSalesClaimNoteSource, /salesClaimSavingProjectIds/);
  assert.doesNotMatch(saveSalesClaimNoteSource, /영업 현황을 저장했다|영업 현황을 입력해라|영업 현황을 저장할 대상이 없습니다/);
  assert.doesNotMatch(transferSalesClaimSource, /\/api\/sales-claims\/projects\/.*\/transfer/);
  assert.doesNotMatch(transferSalesClaimSource, /salesClaimSavingProjectIds/);
  assert.doesNotMatch(transferSalesClaimSource, /이관 대상 사용자를 선택해라|canCurrentUserForceRelease|영업을 이관했다/);
  assert.doesNotMatch(closeSalesClaimSource, /\/api\/sales-claims\/projects\/.*\/close/);
  assert.doesNotMatch(closeSalesClaimSource, /salesClaimSavingProjectIds/);
  assert.doesNotMatch(closeSalesClaimSource, /계약 완료|영업 종료|계약금액을 입력해야 계약 완료 처리할 수 있다|canCurrentUserForceRelease/);
  assert.doesNotMatch(adminDeleteLatestSalesNoteSource, /\/api\/sales-claims\/projects\//);
  assert.doesNotMatch(adminDeleteLatestSalesNoteSource, /salesClaimSavingProjectIds/);
  assert.doesNotMatch(adminDeleteLatestSalesNoteSource, /removeLatestSalesNoteEntry\(/);
  assert.doesNotMatch(adminDeleteLatestSalesNoteSource, /upsertSalesClaim\(/);
  assert.doesNotMatch(adminDeleteLatestSalesNoteSource, /관리자 권한으로 최근 메모를 삭제했다/);
  assert.doesNotMatch(releaseSalesClaimSource, /\/api\/sales-claims\/projects\//);
  assert.doesNotMatch(releaseSalesClaimSource, /salesClaimSavingProjectIds/);
  assert.doesNotMatch(releaseSalesClaimSource, /salesClaimsByProjectId/);
  assert.doesNotMatch(releaseSalesClaimSource, /salesClaimDrafts/);
  assert.doesNotMatch(releaseSalesClaimSource, /관리자 권한으로 영업을 해제했다|영업을 해제했다/);
  assert.doesNotMatch(renderSalesClaimSectionSource, /buildAdminSalesClaimSectionMarkup/);
  assert.doesNotMatch(renderSalesClaimSectionSource, /renderUserTrackerClaimSection/);
  assert.doesNotMatch(openSalesCloseDialogSource, /salesCloseDialog\.open/);
  assert.doesNotMatch(openSalesCloseDialogSource, /salesCloseDialog\.classList/);
  assert.doesNotMatch(openSalesCloseDialogSource, /salesCloseAmountInput/);
  assert.doesNotMatch(closeSalesCloseDialogSource, /salesCloseDialog\.open/);
  assert.doesNotMatch(closeSalesCloseDialogSource, /salesCloseDialog\.classList/);
  assert.doesNotMatch(closeSalesCloseDialogSource, /salesCloseAmountInput/);
  assert.doesNotMatch(confirmSalesCloseDialogSource, /salesCloseDialog\.open/);
  assert.doesNotMatch(confirmSalesCloseDialogSource, /salesCloseDialog\.classList/);
  assert.doesNotMatch(confirmSalesCloseDialogSource, /salesCloseAmountInput/);
  assert.equal(source.includes("function renderSalesNoteTimelineMarkup(noteEntries) {"), false);
  assert.equal(source.includes("function renderClosedSalesArchiveSection("), false);
});

test("admin google sheet table rendering delegates through the app-level runtime wrapper", () => {
  const source = readAppSource();
  assert.match(source, /APP_SUPPORT\.createAdminTabsFacade\(\{/);
  assert.match(source, /renderAdminGoogleSheetTable,/);
  assert.doesNotMatch(source, /function renderAdminGoogleSheetTable\(sheetKey, sheetPayload\) \{/);
  assert.doesNotMatch(source, /buildAdminGoogleSheetTableView/);
  assert.doesNotMatch(source, /ADMIN_GOOGLE_SHEETS_RUNTIME\.buildAdminGoogleSheetTableView/);
});

test("admin google sheet table interactions delegate through the app-level runtime wrapper", () => {
  const source = readAppSource();
  const facadeDestructureSource = extractFunction(
    source,
    "const {",
    "} = APP_SUPPORT.createAdminTabsFacade({",
  );
  assert.match(facadeDestructureSource, /bindAdminGoogleSheetTableInteractions,/);
  assert.doesNotMatch(source, /function bindAdminGoogleSheetTableInteractions\(sheetKey\) \{/);
  assert.doesNotMatch(facadeDestructureSource, /buildAdminGoogleSheetTableView/);
  assert.doesNotMatch(facadeDestructureSource, /addEventListener/);
  assert.doesNotMatch(facadeDestructureSource, /querySelector/);
});

test("admin embed panel rendering delegates through the app-level runtime wrapper", () => {
  const source = readAppSource();
  const facadeDestructureSource = extractFunction(
    source,
    "const {",
    "} = APP_SUPPORT.createAdminTabsFacade({",
  );
  assert.match(facadeDestructureSource, /renderAdminEmbedPanel,/);
  assert.doesNotMatch(source, /function renderAdminEmbedPanel\(\) \{/);
  assert.doesNotMatch(facadeDestructureSource, /buildAdminGoogleSheetTableView/);
  assert.doesNotMatch(facadeDestructureSource, /addEventListener/);
  assert.doesNotMatch(facadeDestructureSource, /querySelector/);
});

function createTrackerDelegationHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerController() {",
    "function getSelectedEntryController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      "async function toggleProjectRelated(projectId) {",
      "async function toggleTrackerEntryRelated(entryId) {",
    ),
    extractFunction(
      source,
      "async function toggleTrackerEntryRelated(entryId) {",
      "async function loadProjectRelatedNotices(projectId, { silent = false, force = false, prefetch = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadProjectRelatedNotices(projectId, { silent = false, force = false, prefetch = false } = {}) {",
      "function changeProjectsPage(delta) {",
    ),
    extractFunction(
      source,
      "function prefetchTrackerEntryDetails(entries) {",
      "async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) {",
      "function renderSelectedEntryLoading(entry, errorMessage = \"\") {",
    ),
    extractFunction(
      source,
      "function readTrackerFiltersFromControls() {",
      "function parseTrackerRegionFilter(region) {",
    ),
    extractFunction(
      source,
      "function parseTrackerRegionFilter(region) {",
      "function normalizeTrackerRegionFilter(region) {",
    ),
    extractFunction(
      source,
      "function normalizeTrackerRegionFilter(region) {",
      "function renderTrackerRegionButtons() {",
    ),
    extractFunction(
      source,
      "function renderTrackerRegionButtons() {",
      "async function loadDashboardSummary({ silent = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadTrackerTemplateStatus({ silent = false } = {}) {",
      "async function uploadTrackerTemplate(file) {",
    ),
    extractFunction(
      source,
      "async function uploadTrackerTemplate(file) {",
      "async function resetTrackerTemplateOverride() {",
    ),
    extractFunction(
      source,
      "async function resetTrackerTemplateOverride() {",
      "async function loadTrackerEntries({ silent = false, trackerRunId = resolveActiveTrackerRunId(), forceRefresh = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadTrackerEntries({ silent = false, trackerRunId = resolveActiveTrackerRunId(), forceRefresh = false } = {}) {",
      "async function loadTrackerMissingReport({ silent = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadTrackerMissingReport({ silent = false } = {}) {",
      "function renderTrackerMissingReport(errorMessage = \"\") {",
    ),
    extractFunction(
      source,
      "async function loadTrackerChangeEventUnreadCount({ silent = false } = {}) {",
      "async function loadTrackerChangeEvents({ silent = false, includeSilent = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadTrackerChangeEvents({ silent = false, includeSilent = false } = {}) {",
      "async function loadBackfillConflicts({ silent = false, includeResolved = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadBackfillConflicts({ silent = false, includeResolved = false } = {}) {",
      "async function resolveBackfillConflict({ conflictId, resolution } = {}) {",
    ),
    extractFunction(
      source,
      "async function markTrackerChangeEventsRead({ eventIds = [], trackerEntryId = null, silent = false } = {}) {",
      "async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) {",
      "async function loadSelectedEntryDetail({",
    ),
    extractFunction(
      source,
      "async function loadRuns({ initial = false, silent = false, preservePage = false } = {}) {",
      "function toggleUiMode() {",
    ),
    extractFunction(
      source,
      "async function refreshSelectedRun({ silent = false } = {}) {",
      "function renderRunDetail(run) {",
    ),
    extractFunction(
      source,
      "function disconnectRunEventStream() {",
      "function connectRunEventStream(runId) {",
    ),
    extractFunction(
      source,
      "function connectRunEventStream(runId) {",
      "async function loadRunPresets({ silent = false } = {}) {",
    ),
    extractFunction(
      source,
      "async function loadSelectedEntryDetail({",
      "async function patchTrackerEntry({",
    ),
    extractFunction(
      source,
      "async function patchTrackerEntry({",
      "function replaceTrackerEntryInState(updatedEntry) {",
    ),
    extractFunction(
      source,
      "async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) {",
      "async function syncTrackerEntryAfterPatch(updatedEntry) {",
    ),
    extractFunction(
      source,
      "async function syncTrackerEntryAfterPatch(updatedEntry) {",
      "async function saveEntryPatch(event) {",
    ),
    extractFunction(
      source,
      "async function saveTrackerBoardEdit({ entryId, fieldName }) {",
      "async function loadSelectedEntryAudit() {",
    ),
    extractFunction(
      source,
      "async function loadSelectedEntryAudit() {",
      "function hydratePatchFieldOptions() {",
    ),
  ].join("\n");

  const calls = [];
  const controller = {
    readTrackerFiltersFromControls() {
      calls.push(["readTrackerFiltersFromControls"]);
      return "read";
    },
    parseTrackerRegionFilter(region) {
      calls.push(["parseTrackerRegionFilter", region]);
      return ["서울"];
    },
    normalizeTrackerRegionFilter(region) {
      calls.push(["normalizeTrackerRegionFilter", region]);
      return "서울";
    },
    renderTrackerRegionButtons() {
      calls.push(["renderTrackerRegionButtons"]);
      return "render";
    },
    loadTrackerTemplateStatus(options) {
      calls.push(["loadTrackerTemplateStatus", options]);
      return "template";
    },
    uploadTrackerTemplate(file) {
      calls.push(["uploadTrackerTemplate", file]);
      return "upload";
    },
    resetTrackerTemplateOverride() {
      calls.push(["resetTrackerTemplateOverride"]);
      return "reset";
    },
    loadTrackerEntries(options) {
      calls.push(["loadTrackerEntries", options]);
      return "entries";
    },
    loadTrackerMissingReport(options) {
      calls.push(["loadTrackerMissingReport", options]);
      return "missing-report";
    },
    loadTrackerChangeEventUnreadCount(options) {
      calls.push(["loadTrackerChangeEventUnreadCount", options]);
      return "unread";
    },
    loadTrackerChangeEvents(options) {
      calls.push(["loadTrackerChangeEvents", options]);
      return "change-events";
    },
    loadBackfillConflicts(options) {
      calls.push(["loadBackfillConflicts", options]);
      return "backfill";
    },
    markTrackerChangeEventsRead(options) {
      calls.push(["markTrackerChangeEventsRead", options]);
      return "mark-read";
    },
    loadSelectedEntryChangeEvents(options) {
      calls.push(["loadSelectedEntryChangeEvents", options]);
      return "selected-entry-events";
    },
    loadRuns(options) {
      calls.push(["loadRuns", options]);
      return "load-runs";
    },
    toggleProjectRelated(projectId) {
      calls.push(["toggleProjectRelated", projectId]);
      return "toggle-project-related";
    },
    toggleTrackerEntryRelated(entryId) {
      calls.push(["toggleTrackerEntryRelated", entryId]);
      return "toggle-entry-related";
    },
    loadProjectRelatedNotices(projectId, options) {
      calls.push(["loadProjectRelatedNotices", projectId, options]);
      return "project-related";
    },
    prefetchTrackerEntryDetails(entries) {
      calls.push(["prefetchTrackerEntryDetails", entries]);
      return "prefetch-entry-details";
    },
    fetchTrackerEntryDetail(entryId, options) {
      calls.push(["fetchTrackerEntryDetail", entryId, options]);
      return "fetch-entry-detail";
    },
    loadSelectedEntryDetail(options) {
      calls.push(["loadSelectedEntryDetail", options]);
      return "selected-entry-detail";
    },
    patchTrackerEntry(options) {
      calls.push(["patchTrackerEntry", options]);
      return "patch-entry";
    },
    refreshSelectedRun(options) {
      calls.push(["refreshSelectedRun", options]);
      return "refresh-run";
    },
    syncTrackerEntryAfterPatch(updatedEntry) {
      calls.push(["syncTrackerEntryAfterPatch", updatedEntry]);
      return "sync-entry";
    },
    saveTrackerBoardEdit(options) {
      calls.push(["saveTrackerBoardEdit", options]);
      return "save-board-edit";
    },
    connectRunEventStream(runId) {
      calls.push(["connectRunEventStream", runId]);
      return "connect-stream";
    },
    disconnectRunEventStream() {
      calls.push(["disconnectRunEventStream"]);
      return "disconnect-stream";
    },
    loadSelectedEntryAudit() {
      calls.push(["loadSelectedEntryAudit"]);
      return "audit";
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    window: {
      TRACKER_CONTROLLER: {
        createTrackerController() {
          calls.push(["factory"]);
          return controller;
        },
      },
    },
    trackerController: null,
    state: {
      uiMode: "admin",
      trackerFilters: {
        q: "",
        region: "",
        editedOnly: false,
        page: 1,
        pageSize: 20,
      },
    },
    dom: {
      trackerQuery: { value: "" },
      trackerEditedOnly: { checked: false },
      trackerPageSize: { value: "20" },
      trackerRegionButtons: { innerHTML: "" },
    },
    document: {},
    api: async () => {
      throw new Error("api should not run in tracker delegation test");
    },
    flash: () => {},
    setBusy: () => {},
    FormData: class FormData {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    syncUrlState: () => {},
    readRunFiltersFromControls: () => {},
    renderRuns: () => {},
    renderRunsPagination: () => {},
    renderRunDetail: () => {},
    renderRunEventStatus: () => {},
    renderLogsList: () => {},
    TRACKER_REGION_OPTIONS: [
      { value: "", label: "전체" },
      { value: "서울", label: "서울" },
      { value: "부산", label: "부산" },
    ],
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
    useGlobalTrackerEntriesScope: () => true,
    shouldUseHomeBootstrapTrackerSnapshot: () => false,
    resolveActiveTrackerRunId: () => "run-1",
    isProjectTrackerRun: () => false,
    schedulePolling: () => {},
    loadWinnerRunPanels: async () => {},
    loadTrackerExportPanels: async () => {},
    loadSelectedRunLogs: async () => {},
    loadBackfillConflicts: async () => {},
    loadVisibleSalesClaims: async () => {},
    getTrackerController: () => ({ runtime: true }),
    EDITABLE_FIELDS: ["project_name"],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact"]),
    formatContactResolutionStatusLabel: (value) => String(value ?? ""),
    formatContactResolutionReasonLabel: (value) => String(value ?? ""),
    formatBackfillConflictResolutionLabel: (value) => String(value ?? ""),
    getTrackerDiagnosticsScope: () => ({ trackerRunId: "run-1" }),
    buildTrackerChangeEventsMarkup: () => "",
    buildTrackerChangeBellPopoverMarkup: () => "",
    buildBackfillConflictsMarkup: () => "",
    buildBackfillConflictsView: () => ({ html: "" }),
    focusTrackerChangeEntry: async () => {},
    closeTrackerChangeModal: () => {},
    patchTrackerEntry: async () => {},
    syncTrackerEntryAfterPatch: async () => {},
    requireTrackerDiagnosticsRuntime: () => ({}),
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
    loadTrackerChangeEventUnreadCount: async () => {},
    loadTrackerChangeEvents: async () => {},
    prefetchVisibleProjectRelatedNotices: () => {},
    TRACKER_DIAGNOSTICS_RUNTIME: {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls, getterSource, wrapperSource };
}

function createTrackerEntryActionsHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerEntryActionsController() {",
    "function getSelectedEntryController() {",
  );
  const wrapperSource = [
    extractFunction(source, "function toggleTrackerBoardBlankPriority(fieldName) {", "function renderTrackerBoardHeaderCell(column) {"),
    extractFunction(source, "function beginTrackerBoardEdit(entryId, fieldName) {", "function resetTrackerBoardEdit() {"),
    extractFunction(source, "function resetTrackerBoardEdit() {", "function resolveTrackerPatchActorLabel() {"),
    extractFunction(source, "function resolveTrackerPatchActorLabel() {", "function getEntriesTotalPages() {"),
    extractFunction(source, "function getEntriesTotalPages() {", "function renderEntriesPagination() {"),
    extractFunction(source, "function renderEntriesPagination() {", "function changeEntriesPage(delta) {"),
    extractFunction(source, "function changeEntriesPage(delta) {", "function changeEntriesPageTo(page) {"),
    extractFunction(source, "function changeEntriesPageTo(page) {", "function renderSelectedEntry(entry, { summaryOnly = false } = {}) {"),
    extractFunction(source, "async function saveEntryPatch(event) {", "async function clearEntryPatch() {"),
    extractFunction(source, "async function clearEntryPatch() {", "async function saveTrackerBoardEdit({ entryId, fieldName }) {"),
    extractFunction(source, "function hydratePatchFieldOptions() {", "function resolveActiveTrackerRunId() {"),
  ].join("\n");

  const expectedKeys = [
    "state",
    "dom",
    "escapeHtml",
    "syncUrlState",
    "renderTrackerEntries",
    "EDITABLE_FIELDS",
    "TRACKER_BOARD_BLANK_PRIORITY_FIELDS",
    "renderTrackerBoard",
    "loadTrackerEntries",
    "setBusy",
    "patchTrackerEntry",
    "flash",
    "syncTrackerEntryAfterPatch",
  ];
  const calls = [];
  let capturedHelperContext = null;
  let capturedFactoryDeps = null;
  const controller = {
    toggleTrackerBoardBlankPriority(fieldName) {
      calls.push(["toggleTrackerBoardBlankPriority", fieldName]);
      return "toggle-blank-priority";
    },
    beginTrackerBoardEdit(entryId, fieldName) {
      calls.push(["beginTrackerBoardEdit", entryId, fieldName]);
      return "begin-board-edit";
    },
    resetTrackerBoardEdit() {
      calls.push(["resetTrackerBoardEdit"]);
      return "reset-board-edit";
    },
    resolveTrackerPatchActorLabel() {
      calls.push(["resolveTrackerPatchActorLabel"]);
      return "actor-label";
    },
    getEntriesTotalPages() {
      calls.push(["getEntriesTotalPages"]);
      return 7;
    },
    renderEntriesPagination() {
      calls.push(["renderEntriesPagination"]);
      return "render-pagination";
    },
    changeEntriesPage(delta) {
      calls.push(["changeEntriesPage", delta]);
      return "change-page";
    },
    changeEntriesPageTo(page) {
      calls.push(["changeEntriesPageTo", page]);
      return "change-page-to";
    },
    async saveEntryPatch(event) {
      calls.push(["saveEntryPatch", event]);
      return "save-entry-patch";
    },
    async clearEntryPatch() {
      calls.push(["clearEntryPatch"]);
      return "clear-entry-patch";
    },
    hydratePatchFieldOptions() {
      calls.push(["hydratePatchFieldOptions"]);
      return "hydrate-patch-options";
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    ...createTrackerControllerHarnessGlobals(),
    window: {
      TRACKER_ENTRY_ACTIONS_CONTROLLER: {
        createTrackerEntryActionsController(deps) {
          capturedFactoryDeps = deps;
          calls.push(["factory", deps]);
          return controller;
        },
      },
    },
    trackerEntryActionsController: null,
    state: {
      selectedEntry: null,
      trackerEntries: [],
      trackerEntriesTotal: 0,
      trackerFilters: { page: 1, pageSize: 20 },
      trackerBoardEdit: { entryId: null, fieldName: "", draftValue: "", saving: false, errorMessage: "" },
      trackerBoardSort: { fieldName: "" },
      auth: { user: null },
      uiMode: "admin",
    },
    dom: {
      patchField: { value: "project_name", innerHTML: "" },
      patchValue: { value: "" },
      patchActorLabel: { value: "" },
      saveEntryButton: {},
      clearEntryButton: {},
      entriesPageMeta: { textContent: "" },
      entriesFirstButton: { disabled: false },
      entriesPrevButton: { disabled: false },
      entriesNextButton: { disabled: false },
      entriesLastButton: { disabled: false },
    },
    EDITABLE_FIELDS: ["project_name"],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact"]),
    escapeHtml: (value) => String(value ?? ""),
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    renderTrackerBoard: () => {},
    loadTrackerEntries: () => {},
    setBusy: () => {},
    patchTrackerEntry: async () => {
      throw new Error("patchTrackerEntry should not run in tracker entry actions delegation test");
    },
    flash: () => {},
    syncTrackerEntryAfterPatch: async () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const wiringRuntime = context.window.SPMSAppControllerWiringRuntime;
  const actualCreateTrackerEntryActionsControllerDeps = wiringRuntime.createTrackerEntryActionsControllerDeps;
  wiringRuntime.createTrackerEntryActionsControllerDeps = (deps) => {
    calls.push(["helper", deps]);
    capturedHelperContext = deps;
    assert.deepEqual(Object.keys(deps).sort(), [...expectedKeys].sort());
    capturedFactoryDeps = actualCreateTrackerEntryActionsControllerDeps(deps);
    return capturedFactoryDeps;
  };
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return {
    context,
    calls,
    getterSource,
    get capturedHelperContext() {
      return capturedHelperContext;
    },
    get capturedFactoryDeps() {
      return capturedFactoryDeps;
    },
  };
}

function createAdminGoogleSheetsHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getAdminGoogleSheetsController() {",
    "function getRuntimeEnhancements() {",
  );

  const calls = [];
  let factoryCalls = 0;
  let factoryDeps = null;
  const controller = { marker: "admin-google-sheets-controller" };

  const context = vm.createContext({
    console,
    window: {},
    APP_SUPPORT: createAppSupportStub(calls),
    ADMIN_GOOGLE_SHEETS_CONTROLLER_RUNTIME: {
      createAdminGoogleSheetsController(deps) {
        factoryCalls += 1;
        factoryDeps = deps;
        calls.push(["factory", deps]);
        return controller;
      },
    },
    adminGoogleSheetsController: null,
    state: { adminTab: "project-status" },
    dom: { adminEmbedPanel: true },
    api: () => {},
    flash: () => {},
    renderAdminTopNavigation: () => {},
    renderAdminEmbedPanel: () => {},
    canLoadProtectedConsoleData: () => false,
    maybeResolveLegacyAdminAliasToSheetTab: () => null,
    getValidatedActiveAdminGoogleSheetTab: () => null,
    isAdminGoogleSheetTabKey: () => false,
    isPendingLegacyAdminAlias: () => false,
    shouldDeferAdminGoogleSheetPayloadLoad: () => false,
    clearAdminGoogleSheetPopupStateForTab: () => {},
    syncUrlState: () => {},
    applyUiMode: () => {},
    persistAdminGoogleSheetsCache: () => {},
    ADMIN_GOOGLE_SHEETS_RUNTIME: { runtime: true },
    DEFAULT_ADMIN_TAB: "project-status",
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(getterSource, context, { filename: appPath });
  return {
    context,
    calls,
    controller,
    get factoryCalls() {
      return factoryCalls;
    },
    get factoryDeps() {
      return factoryDeps;
    },
  };
}

function createDownloadControllerHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getDownloadController() {",
    "function getTrackerEntryActionsController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      "function extractDownloadFilename(response, fallbackName) {",
      "function setAuthMode(mode) {",
    ),
    extractFunction(
      source,
      "function buildTrackerEntriesDownloadUrl(format) {",
      "function renderTrackerTemplateStatus(errorMessage = \"\") {",
    ),
  ].join("\n");

  const calls = [];
  const controller = {
    extractDownloadFilename(response, fallbackName) {
      calls.push(["extractDownloadFilename", response, fallbackName]);
      return "extracted-file.xlsx";
    },
    ensureDownloadProgressOverlay() {
      calls.push(["ensureDownloadProgressOverlay"]);
      return "overlay";
    },
    showDownloadProgressOverlay(stages, title) {
      calls.push(["showDownloadProgressOverlay", stages, title]);
      return "shown";
    },
    updateDownloadProgressOverlay(message) {
      calls.push(["updateDownloadProgressOverlay", message]);
      return "updated";
    },
    hideDownloadProgressOverlay() {
      calls.push(["hideDownloadProgressOverlay"]);
      return "hidden";
    },
    async triggerFileDownload(url, options) {
      calls.push(["triggerFileDownload", url, options]);
      return "file-download";
    },
    downloadSalesWorkbook(scope, button) {
      calls.push(["downloadSalesWorkbook", scope, button]);
      return "sales-workbook";
    },
    buildTrackerEntriesDownloadUrl(format) {
      calls.push(["buildTrackerEntriesDownloadUrl", format]);
      return `/delegated/${format || "xlsx"}`;
    },
    buildTrackerEntriesDownloadJobPayload() {
      calls.push(["buildTrackerEntriesDownloadJobPayload"]);
      return { delegated: true };
    },
    async pollTrackerDownloadJob(jobId, options) {
      calls.push(["pollTrackerDownloadJob", jobId, options]);
      return { status: "success", download_url: "/downloaded.xlsx" };
    },
    async triggerTrackerEntriesXlsxDownload(button) {
      calls.push(["triggerTrackerEntriesXlsxDownload", button]);
      return "tracker-xlsx";
    },
    buildTrackerEntriesDownloadWarmUrl() {
      calls.push(["buildTrackerEntriesDownloadWarmUrl"]);
      return "/warm";
    },
    async warmTrackerEntriesDownload() {
      calls.push(["warmTrackerEntriesDownload"]);
      return "warm";
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    window: {
      DOWNLOAD_CONTROLLER: {
        createDownloadController() {
          calls.push(["factory"]);
          return controller;
        },
      },
    },
    downloadController: null,
    state: {
      uiMode: "admin",
      trackerFilters: {
        q: "",
        region: "",
        editedOnly: false,
      },
      selectedTrackerWorkbookArtifactId: "artifact-1",
    },
    dom: {},
    document: {},
    setBusy: () => {},
    flash: () => {},
    api: async () => {
      throw new Error("api should not run in download delegation test");
    },
    readTrackerFiltersFromControls: () => {},
    useGlobalTrackerEntriesScope: () => false,
    resolveActiveTrackerRunId: () => "run-1",
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls, getterSource, wrapperSource };
}

function createSelectedEntryControllerHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getSelectedEntryController() {",
    "function getRunPanelsController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      "function renderSelectedEntryLoading(entry, errorMessage = \"\") {",
      "function getSelectedEntryDisplayView(entry, { summaryOnly = false } = {}) {",
    ),
    extractFunction(
      source,
      "function getSelectedEntryDisplayView(entry, { summaryOnly = false } = {}) {",
      "function focusTrackerChangeEntry(entryId, entries = state.trackerEntries) {",
    ),
    extractFunction(
      source,
      "function renderSelectedEntry(entry, { summaryOnly = false } = {}) {",
      "function renderEntryDiagnostics(entry, { summaryOnly = false, view = null } = {}) {",
    ),
    extractFunction(
      source,
      "function renderEntryDiagnostics(entry, { summaryOnly = false, view = null } = {}) {",
      "function renderEntryFieldGrid(entry, { view = null } = {}) {",
    ),
    extractFunction(
      source,
      "function renderEntryFieldGrid(entry, { view = null } = {}) {",
      "function renderDrawer(entry, { view = null } = {}) {",
    ),
    extractFunction(
      source,
      "function renderDrawer(entry, { view = null } = {}) {",
      "function syncPatchValueFromSelectedEntry({ patchView = null } = {}) {",
    ),
    extractFunction(
      source,
      "function syncPatchValueFromSelectedEntry({ patchView = null } = {}) {",
      "async function patchTrackerEntry({",
    ),
  ].join("\n");

  const calls = [];
  const controller = {
    renderSelectedEntryLoading(entry, errorMessage) {
      calls.push(["renderSelectedEntryLoading", entry, errorMessage]);
      return "loading";
    },
    getSelectedEntryDisplayView(entry, options) {
      calls.push(["getSelectedEntryDisplayView", entry, options]);
      return "display-view";
    },
    renderSelectedEntry(entry, options) {
      calls.push(["renderSelectedEntry", entry, options]);
      return "selected-entry";
    },
    renderEntryDiagnostics(entry, options) {
      calls.push(["renderEntryDiagnostics", entry, options]);
      return "entry-diagnostics";
    },
    renderEntryFieldGrid(entry, options) {
      calls.push(["renderEntryFieldGrid", entry, options]);
      return "entry-field-grid";
    },
    renderDrawer(entry, options) {
      calls.push(["renderDrawer", entry, options]);
      return "drawer";
    },
    syncPatchValueFromSelectedEntry(options) {
      calls.push(["syncPatchValueFromSelectedEntry", options]);
      return "sync-patch";
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    window: {
      SELECTED_ENTRY_CONTROLLER: {
        createSelectedEntryController(deps) {
          calls.push(["factory", deps]);
          return controller;
        },
      },
    },
    selectedEntryController: null,
    state: {
      selectedEntry: { id: "entry-1" },
      selectedEntryId: "entry-1",
      uiMode: "user",
    },
    dom: {},
    buildSelectedEntryLoadingView: () => "loading-view",
    buildSelectedEntryEmptyView: () => "empty-view",
    buildSelectedEntryDisplayView: () => "display-view-builder",
    buildPatchPanelView: () => "patch-view",
    buildSelectedEntryChangeEventsMarkup: () => "change-events",
    buildSelectedEntryMeta: () => "meta",
    buildEntryDiagnosticsMarkup: () => "diagnostics",
    buildEntryFieldGridMarkup: () => "field-grid",
    buildDrawerFieldListMarkup: () => "drawer-fields",
    truncate: (value) => String(value ?? ""),
    escapeHtml: (value) => String(value ?? ""),
    SELECTED_ENTRY_RUNTIME: { runtime: true },
    formatJson: (value) => JSON.stringify(value),
    EDITABLE_FIELDS: ["project_name"],
    loadSelectedEntryAudit: async () => "audit",
    loadSelectedEntryChangeEvents: async () => "change-events",
    openDrawer: () => "open-drawer",
    closeDrawer: () => "close-drawer",
    syncUrlState: () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls, getterSource, wrapperSource };
}

function createTrackerDiagnosticsPanelHarness() {
  const source = readAppSource();
  const wiringRuntimeSource = readWiringRuntimeSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerDiagnosticsPanelController() {",
    "function getTrackerEntryActionsController() {",
  );
  const wrapperSource = [
    extractFunction(
      source,
      "function focusTrackerChangePanel() {",
      "function bindTrackerChangeEventActions(container) {",
    ),
    extractFunction(
      source,
      "function bindTrackerChangeEventActions(container) {",
      "function bindBackfillConflictActions(container) {",
    ),
    extractFunction(
      source,
      "function bindBackfillConflictActions(container) {",
      "function setTrackerChangeBellPopoverOpen(open) {",
    ),
    extractFunction(
      source,
      "function setTrackerChangeBellPopoverOpen(open) {",
      "function renderTrackerChangeBellPopover() {",
    ),
    extractFunction(
      source,
      "function renderTrackerChangeBellPopover() {",
      "function renderTrackerChangeEventsList(container) {",
    ),
    extractFunction(
      source,
      "function renderTrackerChangeEventsList(container) {",
      "function renderTrackerChangeEventsPanel() {",
    ),
    extractFunction(
      source,
      "function renderTrackerChangeEventsPanel() {",
      "function renderBackfillConflictsPanel() {",
    ),
    extractFunction(
      source,
      "function renderBackfillConflictsPanel() {",
      "function renderSelectedEntryChangeEvents() {",
    ),
    extractFunction(
      source,
      "function renderTrackerChangeEventUnreadCount() {",
      "async function loadTrackerChangeEventUnreadCount({ silent = false } = {}) {",
    ),
    extractFunction(
      source,
      "function renderTrackerContactResolutionSummary(errorMessage = \"\") {",
      "function renderTrackerCleanupPreview(errorMessage = \"\") {",
    ),
    extractFunction(
      source,
      "function renderTrackerCleanupPreview(errorMessage = \"\") {",
      "function renderTrackerMissingReport(errorMessage = \"\") {",
    ),
    extractFunction(
      source,
      "async function resolveBackfillConflict({ conflictId, resolution } = {}) {",
      "async function markTrackerChangeEventsRead({ eventIds = [], trackerEntryId = null, silent = false } = {}) {",
    ),
  ].join("\n");

  const calls = [];
  const controller = {
    focusTrackerChangePanel() {
      calls.push(["focusTrackerChangePanel"]);
      return "focus-panel";
    },
    bindTrackerChangeEventActions(container) {
      calls.push(["bindTrackerChangeEventActions", container?.id || "container"]);
      return "bind-change-actions";
    },
    bindBackfillConflictActions(container) {
      calls.push(["bindBackfillConflictActions", container?.id || "container"]);
      return "bind-backfill-actions";
    },
    setTrackerChangeBellPopoverOpen(open) {
      calls.push(["setTrackerChangeBellPopoverOpen", open]);
      return "set-popover";
    },
    renderTrackerChangeBellPopover() {
      calls.push(["renderTrackerChangeBellPopover"]);
      return "render-popover";
    },
    renderTrackerChangeEventsList(container) {
      calls.push(["renderTrackerChangeEventsList", container?.id || "container"]);
      return "render-change-list";
    },
    renderTrackerChangeEventsPanel() {
      calls.push(["renderTrackerChangeEventsPanel"]);
      return "render-change-panel";
    },
    renderBackfillConflictsPanel() {
      calls.push(["renderBackfillConflictsPanel"]);
      return "render-backfill-panel";
    },
    renderTrackerChangeEventUnreadCount() {
      calls.push(["renderTrackerChangeEventUnreadCount"]);
      return "render-unread";
    },
    renderTrackerContactResolutionSummary(errorMessage) {
      calls.push(["renderTrackerContactResolutionSummary", errorMessage]);
      return "contact-resolution";
    },
    renderTrackerCleanupPreview(errorMessage) {
      calls.push(["renderTrackerCleanupPreview", errorMessage]);
      return "cleanup-preview";
    },
    resolveBackfillConflict(options) {
      calls.push(["resolveBackfillConflict", options]);
      return "resolve-backfill";
    },
  };

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    ...createTrackerControllerHarnessGlobals(),
    window: {
      TRACKER_DIAGNOSTICS_PANEL_CONTROLLER: {
        createTrackerDiagnosticsPanelController() {
          calls.push(["factory"]);
          return controller;
        },
      },
    },
    trackerDiagnosticsPanelController: null,
    TRACKER_DIAGNOSTICS_RUNTIME: {},
    dom: {
      trackerChangePanel: { id: "panel" },
      trackerChangeBell: { id: "bell" },
      trackerChangeBellPopover: { id: "popover", classList: { toggle() {} } },
      trackerChangeList: { id: "change-list" },
      trackerChangeModalList: { id: "modal-list" },
      trackerChangeBellBadge: { id: "badge", classList: { toggle() {} }, textContent: "" },
      backfillConflictList: { id: "backfill-list", classList: { add() {}, remove() {} }, innerHTML: "" },
      trackerContactResolutionSummary: { className: "", innerHTML: "" },
      trackerContactResolutionList: { className: "", innerHTML: "" },
      trackerCleanupPreview: { className: "", innerHTML: "" },
    },
    state: { trackerChangeModal: { open: false } },
    api: async () => {
      throw new Error("api should not run in tracker diagnostics delegation test");
    },
    flash: () => {},
    getTrackerController: () => ({ markTrackerChangeEventsRead: async () => {} }),
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    formatContactResolutionStatusLabel: (value) => String(value ?? ""),
    formatContactResolutionReasonLabel: (value) => String(value ?? ""),
    formatBackfillConflictResolutionLabel: (value) => String(value ?? ""),
    getTrackerDiagnosticsScope: () => ({ trackerRunId: "run-1", scopeLabel: "run-1" }),
    buildTrackerChangeEventsMarkup: () => "",
    buildTrackerChangeBellPopoverMarkup: () => "",
    buildBackfillConflictsMarkup: () => "",
    buildBackfillConflictsView: () => ({ html: "", className: "", bindActions: false }),
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    loadSelectedEntryDetail: async () => {},
    focusTrackerChangeEntry: async () => {},
    closeTrackerChangeModal: () => {},
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  vm.runInContext(`${getterSource}\n${wrapperSource}`, context, { filename: appPath });
  return { context, calls, getterSource, wrapperSource };
}

function createDownloadControllerBehaviorHarness() {
  const source = fs.readFileSync(path.resolve(__dirname, "../../frontend/download-controller.js"), "utf8")
    .replace("export function createDownloadController", "function createDownloadController");
  const context = {
    console,
    URLSearchParams,
    Date,
    Math,
    JSON,
    Promise,
  };

  const calls = [];
  let overlayVisible = false;
  let stageTimer = 0;
  let hideTimer = 0;
  let warmResolve = null;
  let globalScope = false;
  let nextPollStatus = 0;
  const overlayTitle = { textContent: "" };
  const overlayDetail = { textContent: "" };
  const overlayNode = {
    id: "",
    className: "",
    innerHTML: "",
    classList: {
      add(token) {
        calls.push(["overlayClassAdd", token]);
      },
      remove(token) {
        calls.push(["overlayClassRemove", token]);
      },
    },
    querySelector(selector) {
      if (selector === ".download-progress-title") {
        return overlayTitle;
      }
      if (selector === ".download-progress-detail") {
        return overlayDetail;
      }
      return null;
    },
  };
  const anchorNode = () => ({
    href: "",
    download: "",
    click() {
      calls.push(["anchorClick", this.download, this.href]);
    },
    remove() {
      calls.push(["anchorRemove"]);
    },
  });

  context.window = {
    DOWNLOAD_CONTROLLER: {},
    URL: {
      createObjectURL(blob) {
        calls.push(["createObjectURL", blob]);
        return "blob:download";
      },
      revokeObjectURL(url) {
        calls.push(["revokeObjectURL", url]);
      },
    },
    requestAnimationFrame(callback) {
      calls.push(["requestAnimationFrame"]);
      callback();
    },
    clearInterval(handle) {
      calls.push(["clearInterval", handle]);
    },
    clearTimeout(handle) {
      calls.push(["clearTimeout", handle]);
    },
    setInterval(callback, intervalMs) {
      calls.push(["setInterval", intervalMs]);
      stageTimer += 1;
      return stageTimer;
    },
    setTimeout(callback, timeoutMs) {
      calls.push(["setTimeout", timeoutMs]);
      if (timeoutMs === 180) {
        hideTimer += 1;
        callback();
        return hideTimer;
      }
      if (timeoutMs === 0) {
        callback();
        return 0;
      }
      callback();
      return timeoutMs;
    },
    location: {
      href: "",
    },
  };

  context.document = {
    querySelector(selector) {
      if (selector === "#download-progress-overlay") {
        return overlayVisible ? overlayNode : null;
      }
      return null;
    },
    createElement(tagName) {
      if (tagName === "a") {
        return anchorNode();
      }
      if (tagName === "div") {
        return overlayNode;
      }
      throw new Error(`unexpected element tag: ${tagName}`);
    },
    body: {
      appendChild(node) {
        calls.push(["appendChild", node.id || node.download || node.tagName || "node"]);
        if (node === overlayNode) {
          overlayVisible = true;
        }
      },
    },
  };

  context.state = {
    uiMode: "user",
    trackerFilters: {
      q: "alpha",
      region: "서울",
      editedOnly: true,
    },
    selectedTrackerWorkbookArtifactId: null,
    trackerDownloadWarmRequest: null,
    trackerDownloadWarmRequestKey: "",
    downloadProgressStageHandle: null,
    downloadProgressHideHandle: null,
  };
  context.dom = {};
  context.setBusy = (button, busy, label) => {
    calls.push(["setBusy", button?.id || null, busy, label]);
  };
  context.flash = (message, level) => {
    calls.push(["flash", message, level]);
  };
  context.api = async (url, options = {}) => {
    calls.push(["api", url, options]);
    if (url === "/api/tracker-entry-summaries/download-jobs") {
      return { id: "job-1" };
    }
    if (url.startsWith("/api/tracker-entry-summaries/download-jobs/")) {
      nextPollStatus += 1;
      if (nextPollStatus === 1) {
        return { status: "running" };
      }
      return {
        status: "success",
        download_url: "/api/tracker-entry-summaries/download/job-1.xlsx",
        reused_existing: false,
      };
    }
    if (url.startsWith("/api/tracker-entry-summaries/download/warm")) {
      return await new Promise((resolve) => {
        warmResolve = resolve;
      });
    }
    return {};
  };
  context.fetch = async (url, options = {}) => {
    calls.push(["fetch", url, options]);
    return {
      ok: true,
      status: 200,
      headers: {
        get(name) {
          if (name === "content-disposition") {
            return "attachment; filename*=UTF-8''final%20report.xlsx";
          }
          if (name === "content-type") {
            return "application/octet-stream";
          }
          return "";
        },
      },
      blob: async () => ({ blob: true, url }),
    };
  };
  context.readTrackerFiltersFromControls = () => {
    calls.push(["readTrackerFiltersFromControls"]);
  };
  context.useGlobalTrackerEntriesScope = () => globalScope;
  context.resolveActiveTrackerRunId = () => "run-1";

  vm.createContext(context);
  vm.runInContext(source, context, { filename: path.resolve(__dirname, "../../frontend/download-controller.js") });
  const controller = context.window.DOWNLOAD_CONTROLLER.createDownloadController({
    state: context.state,
    dom: context.dom,
    window: context.window,
    document: context.document,
    setBusy: context.setBusy,
    flash: context.flash,
    api: context.api,
    fetch: context.fetch,
    readTrackerFiltersFromControls: context.readTrackerFiltersFromControls,
    useGlobalTrackerEntriesScope: context.useGlobalTrackerEntriesScope,
    resolveActiveTrackerRunId: context.resolveActiveTrackerRunId,
  });

  return {
    controller,
    context,
    calls,
    overlayTitle,
    overlayDetail,
    setGlobalScope(value) {
      globalScope = value;
    },
    resolveWarmRequest(payload) {
      if (warmResolve) {
        warmResolve(payload);
        warmResolve = null;
      }
    },
  };
}

test("tracker controller wrappers stay thin and delegate through the tracker controller", async () => {
  const { context, calls, getterSource, wrapperSource } = createTrackerDelegationHarness();

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createTrackerControllerDeps"/);
  assert.match(getterSource, /Missing tracker controller runtime: window\.TRACKER_CONTROLLER\.createTrackerController/);
  assert.match(getterSource, /getTrackerControllerDepsHelpers\(\)\.buildTrackerControllerDeps\(\)/);
  assert.doesNotMatch(getterSource, /readTrackerFiltersFromControlsImpl/);
  assert.doesNotMatch(getterSource, /renderTrackerChangeEventsPanel:/);
  assert.doesNotMatch(getterSource, /loadSelectedEntryDetail:/);

  const toggleProjectRelatedSource = extractFunction(
    readAppSource(),
    "async function toggleProjectRelated(projectId) {",
    "async function toggleTrackerEntryRelated(entryId) {",
  );
  const toggleTrackerEntryRelatedSource = extractFunction(
    readAppSource(),
    "async function toggleTrackerEntryRelated(entryId) {",
    "async function loadProjectRelatedNotices(projectId, { silent = false, force = false, prefetch = false } = {}) {",
  );
  const loadProjectRelatedNoticesSource = extractFunction(
    readAppSource(),
    "async function loadProjectRelatedNotices(projectId, { silent = false, force = false, prefetch = false } = {}) {",
    "function changeProjectsPage(delta) {",
  );
  const prefetchTrackerEntryDetailsSource = extractFunction(
    readAppSource(),
    "function prefetchTrackerEntryDetails(entries) {",
    "async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) {",
  );
  const fetchTrackerEntryDetailSource = extractFunction(
    readAppSource(),
    "async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) {",
    "function renderSelectedEntryLoading(entry, errorMessage = \"\") {",
  );
  const readTrackerFiltersSource = extractFunction(
    readAppSource(),
    "function readTrackerFiltersFromControls() {",
    "function parseTrackerRegionFilter(region) {",
  );
  const parseTrackerRegionFilterSource = extractFunction(
    readAppSource(),
    "function parseTrackerRegionFilter(region) {",
    "function normalizeTrackerRegionFilter(region) {",
  );
  const normalizeTrackerRegionFilterSource = extractFunction(
    readAppSource(),
    "function normalizeTrackerRegionFilter(region) {",
    "function renderTrackerRegionButtons() {",
  );
  const renderTrackerRegionButtonsSource = extractFunction(
    readAppSource(),
    "function renderTrackerRegionButtons() {",
    "async function loadDashboardSummary({ silent = false } = {}) {",
  );
  const loadTrackerTemplateStatusSource = extractFunction(
    readAppSource(),
    "async function loadTrackerTemplateStatus({ silent = false } = {}) {",
    "async function uploadTrackerTemplate(file) {",
  );
  const uploadTrackerTemplateSource = extractFunction(
    readAppSource(),
    "async function uploadTrackerTemplate(file) {",
    "async function resetTrackerTemplateOverride() {",
  );
  const resetTrackerTemplateOverrideSource = extractFunction(
    readAppSource(),
    "async function resetTrackerTemplateOverride() {",
    "async function loadTrackerEntries({ silent = false, trackerRunId = resolveActiveTrackerRunId(), forceRefresh = false } = {}) {",
  );
  const loadTrackerEntriesSource = extractFunction(
    readAppSource(),
    "async function loadTrackerEntries({ silent = false, trackerRunId = resolveActiveTrackerRunId(), forceRefresh = false } = {}) {",
    "async function loadTrackerMissingReport({ silent = false } = {}) {",
  );
  const loadTrackerMissingReportSource = extractFunction(
    readAppSource(),
    "async function loadTrackerMissingReport({ silent = false } = {}) {",
    "function renderTrackerMissingReport(errorMessage = \"\") {",
  );
  const loadTrackerChangeEventUnreadCountSource = extractFunction(
    readAppSource(),
    "async function loadTrackerChangeEventUnreadCount({ silent = false } = {}) {",
    "async function loadTrackerChangeEvents({ silent = false, includeSilent = false } = {}) {",
  );
  const loadTrackerChangeEventsSource = extractFunction(
    readAppSource(),
    "async function loadTrackerChangeEvents({ silent = false, includeSilent = false } = {}) {",
    "async function loadBackfillConflicts({ silent = false, includeResolved = false } = {}) {",
  );
  const loadBackfillConflictsSource = extractFunction(
    readAppSource(),
    "async function loadBackfillConflicts({ silent = false, includeResolved = false } = {}) {",
    "async function resolveBackfillConflict({ conflictId, resolution } = {}) {",
  );
  const markTrackerChangeEventsReadSource = extractFunction(
    readAppSource(),
    "async function markTrackerChangeEventsRead({ eventIds = [], trackerEntryId = null, silent = false } = {}) {",
    "async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) {",
  );
  const loadSelectedEntryChangeEventsSource = extractFunction(
    readAppSource(),
    "async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) {",
    "async function loadSelectedEntryDetail({",
  );
  const loadRunsSource = extractFunction(
    readAppSource(),
    "async function loadRuns({ initial = false, silent = false, preservePage = false } = {}) {",
    "function toggleUiMode() {",
  );
  const loadSelectedEntryDetailSource = extractFunction(
    readAppSource(),
    "async function loadSelectedEntryDetail({",
    "function resolveTrackerEntryProjectId(entryId) {",
  );
  const refreshSelectedRunSource = extractFunction(
    readAppSource(),
    "async function refreshSelectedRun({ silent = false } = {}) {",
    "function renderRunDetail(run) {",
  );
  const loadSelectedEntryChangeEventsBridgeSource = extractFunction(
    readAppSource(),
    "async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) {",
    "async function syncTrackerEntryAfterPatch(updatedEntry) {",
  );
  const syncTrackerEntryAfterPatchSource = extractFunction(
    readAppSource(),
    "async function syncTrackerEntryAfterPatch(updatedEntry) {",
    "async function saveEntryPatch(event) {",
  );
  const loadSelectedEntryAuditSource = extractFunction(
    readAppSource(),
    "async function loadSelectedEntryAudit() {",
    "function hydratePatchFieldOptions() {",
  );
  const saveTrackerBoardEditSource = extractFunction(
    readAppSource(),
    "async function saveTrackerBoardEdit({ entryId, fieldName }) {",
    "async function loadSelectedEntryAudit() {",
  );

  assert.match(toggleProjectRelatedSource, /getTrackerController\(\)/);
  assert.match(toggleTrackerEntryRelatedSource, /getTrackerController\(\)/);
  assert.match(loadProjectRelatedNoticesSource, /getTrackerController\(\)/);
  assert.match(prefetchTrackerEntryDetailsSource, /getTrackerController\(\)/);
  assert.match(fetchTrackerEntryDetailSource, /getTrackerController\(\)/);
  assert.match(readTrackerFiltersSource, /getTrackerController\(\)/);
  assert.match(parseTrackerRegionFilterSource, /getTrackerController\(\)/);
  assert.match(normalizeTrackerRegionFilterSource, /getTrackerController\(\)/);
  assert.match(renderTrackerRegionButtonsSource, /getTrackerController\(\)/);
  assert.match(loadTrackerTemplateStatusSource, /getTrackerController\(\)/);
  assert.match(uploadTrackerTemplateSource, /getTrackerController\(\)/);
  assert.match(resetTrackerTemplateOverrideSource, /getTrackerController\(\)/);
  assert.match(loadTrackerEntriesSource, /getTrackerController\(\)/);
  assert.match(loadTrackerMissingReportSource, /getTrackerController\(\)/);
  assert.match(loadTrackerChangeEventUnreadCountSource, /getTrackerController\(\)/);
  assert.match(loadTrackerChangeEventsSource, /getTrackerController\(\)/);
  assert.match(loadBackfillConflictsSource, /getTrackerController\(\)/);
  assert.match(markTrackerChangeEventsReadSource, /getTrackerController\(\)/);
  assert.match(loadSelectedEntryChangeEventsSource, /getTrackerController\(\)/);
  assert.match(loadRunsSource, /getTrackerController\(\)/);
  assert.match(loadRunsSource, /loadRuns\(\{ initial, silent, preservePage \}\)/);
  assert.match(refreshSelectedRunSource, /getTrackerController\(\)/);
  assert.match(loadSelectedEntryDetailSource, /getTrackerController\(\)/);
  assert.match(loadSelectedEntryChangeEventsBridgeSource, /getTrackerController\(\)/);
  assert.match(syncTrackerEntryAfterPatchSource, /getTrackerController\(\)/);
  assert.match(loadSelectedEntryAuditSource, /getTrackerController\(\)/);
  assert.match(saveTrackerBoardEditSource, /getTrackerController\(\)/);
  assert.doesNotMatch(toggleProjectRelatedSource, /state\.projectOpenId/);
  assert.doesNotMatch(toggleTrackerEntryRelatedSource, /trackerRelatedResolvingEntryId/);
  assert.doesNotMatch(loadProjectRelatedNoticesSource, /related-notices/);
  assert.doesNotMatch(prefetchTrackerEntryDetailsSource, /TRACKER_DETAIL_PREFETCH_LIMIT/);
  assert.doesNotMatch(fetchTrackerEntryDetailSource, /api\(\/api\/tracker-entries/);
  assert.doesNotMatch(readTrackerFiltersSource, /trackerFilters\.editedOnly = false/);
  assert.doesNotMatch(parseTrackerRegionFilterSource, /split\(\[/);
  assert.doesNotMatch(normalizeTrackerRegionFilterSource, /join\(","\)/);
  assert.doesNotMatch(renderTrackerRegionButtonsSource, /aria-pressed/);
  assert.doesNotMatch(loadTrackerTemplateStatusSource, /trackerTemplateStatus\s*=\s*await api/);
  assert.doesNotMatch(uploadTrackerTemplateSource, /new FormData/);
  assert.doesNotMatch(resetTrackerTemplateOverrideSource, /trackerTemplateStatus\s*=\s*await api/);
  assert.doesNotMatch(loadTrackerEntriesSource, /tracker-entry-summaries/);
  assert.doesNotMatch(loadTrackerMissingReportSource, /tracker-entries\/missing-report/);
  assert.doesNotMatch(loadTrackerChangeEventUnreadCountSource, /tracker-change-events\/unread-count/);
  assert.doesNotMatch(loadTrackerChangeEventsSource, /tracker-change-events\?/);
  assert.doesNotMatch(loadBackfillConflictsSource, /backfill-conflicts\?/);
  assert.doesNotMatch(markTrackerChangeEventsReadSource, /tracker-change-events\/mark-read/);
  assert.doesNotMatch(loadSelectedEntryChangeEventsSource, /tracker-change-events\?/);
  assert.doesNotMatch(loadRunsSource, /new URLSearchParams/);
  assert.doesNotMatch(loadRunsSource, /\/api\/runs/);
  assert.doesNotMatch(loadRunsSource, /state\.runs\s*=/);
  assert.doesNotMatch(loadRunsSource, /touchSyncMeta\(/);
  assert.doesNotMatch(loadRunsSource, /flash\(/);
  assert.doesNotMatch(loadRunsSource, /readRunFiltersFromControls\(/);
  assert.doesNotMatch(loadRunsSource, /handleOutOfRangePageError\(/);
  assert.doesNotMatch(refreshSelectedRunSource, /api\(\/api\/runs\//);
  assert.doesNotMatch(refreshSelectedRunSource, /resolvePreferredTrackerRunIdForRun\(/);
  assert.doesNotMatch(loadSelectedEntryDetailSource, /fetchTrackerEntryDetail\(/);
  assert.doesNotMatch(loadSelectedEntryDetailSource, /renderSelectedEntryLoading\(/);
  assert.doesNotMatch(syncTrackerEntryAfterPatchSource, /renderTrackerEntries\(/);
  assert.doesNotMatch(syncTrackerEntryAfterPatchSource, /loadTrackerEntries\(/);
  assert.doesNotMatch(loadSelectedEntryAuditSource, /audit-logs\?limit=20/);
  assert.doesNotMatch(saveTrackerBoardEditSource, /state\.trackerBoardEdit\.saving/);
  assert.doesNotMatch(saveTrackerBoardEditSource, /patchTrackerEntry\(/);
  const trackerController = context.getTrackerController();
  assert.equal(trackerController, context.getTrackerController());
  assert.equal(calls.length, 1, "tracker controller should be created once");
  assert.equal(calls[0][0], "factory");

  assert.equal(await context.toggleProjectRelated("project-7"), "toggle-project-related");
  assert.deepEqual(calls[1], ["toggleProjectRelated", "project-7"]);
  assert.equal(await context.toggleTrackerEntryRelated("entry-7"), "toggle-entry-related");
  assert.deepEqual(calls[2], ["toggleTrackerEntryRelated", "entry-7"]);
  assert.equal(
    await context.loadProjectRelatedNotices("project-7", { silent: true, force: true, prefetch: true }),
    "project-related",
  );
  assert.equal(calls[3][0], "loadProjectRelatedNotices");
  assert.equal(calls[3][1], "project-7");
  assert.equal(calls[3][2].silent, true);
  assert.equal(calls[3][2].force, true);
  assert.equal(calls[3][2].prefetch, true);
  assert.equal(context.prefetchTrackerEntryDetails([{ id: "entry-7" }]), "prefetch-entry-details");
  assert.deepEqual(calls[4], ["prefetchTrackerEntryDetails", [{ id: "entry-7" }]]);
  assert.equal(await context.fetchTrackerEntryDetail("entry-7", { silent: true }), "fetch-entry-detail");
  assert.equal(calls[5][0], "fetchTrackerEntryDetail");
  assert.equal(calls[5][1], "entry-7");
  assert.equal(calls[5][2].silent, true);
  calls.splice(1, 5);

  assert.equal(context.readTrackerFiltersFromControls(), "read");
  assert.deepEqual(calls[1], ["readTrackerFiltersFromControls"]);
  assert.deepEqual(context.parseTrackerRegionFilter("부산"), ["서울"]);
  assert.deepEqual(calls[2], ["parseTrackerRegionFilter", "부산"]);
  assert.equal(context.normalizeTrackerRegionFilter("부산"), "서울");
  assert.deepEqual(calls[3], ["normalizeTrackerRegionFilter", "부산"]);
  assert.equal(context.renderTrackerRegionButtons(), "render");
  assert.deepEqual(calls[4], ["renderTrackerRegionButtons"]);
  assert.equal(await context.loadTrackerTemplateStatus({ silent: true }), "template");
  assert.equal(calls[5][0], "loadTrackerTemplateStatus");
  assert.equal(calls[5][1].silent, true);
  assert.equal(await context.uploadTrackerTemplate({ name: "tracker.xlsx" }), "upload");
  assert.equal(calls[6][0], "uploadTrackerTemplate");
  assert.equal(calls[6][1].name, "tracker.xlsx");
  assert.equal(await context.resetTrackerTemplateOverride(), "reset");
  assert.deepEqual(calls[7], ["resetTrackerTemplateOverride"]);
  assert.equal(await context.loadTrackerEntries({ silent: true, trackerRunId: "run-99", forceRefresh: true }), "entries");
  assert.equal(calls[8][0], "loadTrackerEntries");
  assert.equal(calls[8][1].silent, true);
  assert.equal(calls[8][1].trackerRunId, "run-99");
  assert.equal(calls[8][1].forceRefresh, true);
  assert.equal(await context.loadTrackerMissingReport({ silent: true }), "missing-report");
  assert.equal(calls[9][0], "loadTrackerMissingReport");
  assert.equal(calls[9][1].silent, true);
  assert.equal(await context.loadTrackerChangeEventUnreadCount({ silent: true }), "unread");
  assert.equal(calls[10][0], "loadTrackerChangeEventUnreadCount");
  assert.equal(calls[10][1].silent, true);
  assert.equal(await context.loadTrackerChangeEvents({ silent: true, includeSilent: true }), "change-events");
  assert.equal(calls[11][0], "loadTrackerChangeEvents");
  assert.equal(calls[11][1].silent, true);
  assert.equal(calls[11][1].includeSilent, true);
  assert.equal(await context.loadBackfillConflicts({ silent: true, includeResolved: true }), "backfill");
  assert.equal(calls[12][0], "loadBackfillConflicts");
  assert.equal(calls[12][1].silent, true);
  assert.equal(calls[12][1].includeResolved, true);
  assert.equal(
    await context.markTrackerChangeEventsRead({ eventIds: ["event-1"], trackerEntryId: "entry-7", silent: true }),
    "mark-read",
  );
  assert.equal(calls[13][0], "markTrackerChangeEventsRead");
  assert.deepEqual(calls[13][1].eventIds, ["event-1"]);
  assert.equal(calls[13][1].trackerEntryId, "entry-7");
  assert.equal(calls[13][1].silent, true);
  assert.equal(await context.loadSelectedEntryChangeEvents({ entryId: "entry-7", silent: true }), "selected-entry-events");
  assert.equal(calls[14][0], "loadSelectedEntryChangeEvents");
  assert.equal(calls[14][1].entryId, "entry-7");
  assert.equal(calls[14][1].silent, true);
  assert.equal(
    await context.loadRuns({ initial: true, silent: true, preservePage: true }),
    "load-runs",
  );
  assert.equal(calls[15][0], "loadRuns");
  assert.equal(calls[15][1].initial, true);
  assert.equal(calls[15][1].silent, true);
  assert.equal(calls[15][1].preservePage, true);
  assert.equal(
    await context.loadSelectedEntryDetail({ entryId: "entry-7", silent: true, background: true, force: true }),
    "selected-entry-detail",
  );
  assert.equal(calls[16][0], "loadSelectedEntryDetail");
  assert.equal(calls[16][1].entryId, "entry-7");
  assert.equal(calls[16][1].silent, true);
  assert.equal(calls[16][1].background, true);
  assert.equal(calls[16][1].force, true);
  assert.equal(
    await context.patchTrackerEntry({
      entryId: "entry-7",
      fieldName: "project_name",
      value: "next-value",
      changeSource: "web",
      actorLabel: "tester",
    }),
    "patch-entry",
  );
  assert.equal(calls[17][0], "patchTrackerEntry");
  assert.deepEqual(plain(calls[17][1]), {
    entryId: "entry-7",
    fieldName: "project_name",
    value: "next-value",
    changeSource: "web",
    actorLabel: "tester",
  });
  assert.equal(await context.refreshSelectedRun({ silent: true }), "refresh-run");
  assert.equal(calls[18][0], "refreshSelectedRun");
  assert.equal(calls[18][1].silent, true);
  assert.equal(await context.syncTrackerEntryAfterPatch({ id: "entry-7" }), "sync-entry");
  assert.equal(calls[19][0], "syncTrackerEntryAfterPatch");
  assert.deepEqual(calls[19][1], { id: "entry-7" });
  assert.equal(await context.loadSelectedEntryAudit(), "audit");
  assert.equal(calls[20][0], "loadSelectedEntryAudit");
  assert.equal(await context.saveTrackerBoardEdit({ entryId: "entry-7", fieldName: "project_name" }), "save-board-edit");
  assert.equal(calls[21][0], "saveTrackerBoardEdit");
  assert.equal(calls[21][1].entryId, "entry-7");
  assert.equal(calls[21][1].fieldName, "project_name");
  assert.equal(context.connectRunEventStream("run-55"), "connect-stream");
  assert.deepEqual(calls[22], ["connectRunEventStream", "run-55"]);
  assert.equal(context.disconnectRunEventStream(), "disconnect-stream");
  assert.deepEqual(calls[23], ["disconnectRunEventStream"]);
});

test("tracker entry action wrappers stay thin and delegate through the tracker entry actions controller", async () => {
  const harness = createTrackerEntryActionsHarness();
  const { context, calls, getterSource } = harness;
  const source = readAppSource();

  const toggleSource = extractFunction(
    source,
    "function toggleTrackerBoardBlankPriority(fieldName) {",
    "function renderTrackerBoardHeaderCell(column) {",
  );
  const beginSource = extractFunction(
    source,
    "function beginTrackerBoardEdit(entryId, fieldName) {",
    "function resetTrackerBoardEdit() {",
  );
  const resetSource = extractFunction(
    source,
    "function resetTrackerBoardEdit() {",
    "function resolveTrackerPatchActorLabel() {",
  );
  const actorLabelSource = extractFunction(
    source,
    "function resolveTrackerPatchActorLabel() {",
    "function getEntriesTotalPages() {",
  );
  const totalPagesSource = extractFunction(
    source,
    "function getEntriesTotalPages() {",
    "function renderEntriesPagination() {",
  );
  const renderPaginationSource = extractFunction(
    source,
    "function renderEntriesPagination() {",
    "function changeEntriesPage(delta) {",
  );
  const changePageSource = extractFunction(
    source,
    "function changeEntriesPage(delta) {",
    "function changeEntriesPageTo(page) {",
  );
  const changePageToSource = extractFunction(
    source,
    "function changeEntriesPageTo(page) {",
    "function renderSelectedEntry(entry, { summaryOnly = false } = {}) {",
  );
  const saveEntryPatchSource = extractFunction(
    source,
    "async function saveEntryPatch(event) {",
    "async function clearEntryPatch() {",
  );
  const clearEntryPatchSource = extractFunction(
    source,
    "async function clearEntryPatch() {",
    "async function saveTrackerBoardEdit({ entryId, fieldName }) {",
  );
  const hydratePatchFieldOptionsSource = extractFunction(
    source,
    "function hydratePatchFieldOptions() {",
    "function resolveActiveTrackerRunId() {",
  );

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createTrackerEntryActionsControllerDeps"/);
  assert.match(getterSource, /buildTrackerEntryActionsControllerDeps\(\)/);
  assert.match(toggleSource, /getTrackerEntryActionsController\(\)/);
  assert.match(beginSource, /getTrackerEntryActionsController\(\)/);
  assert.match(resetSource, /getTrackerEntryActionsController\(\)/);
  assert.match(actorLabelSource, /getTrackerEntryActionsController\(\)/);
  assert.match(totalPagesSource, /getTrackerEntryActionsController\(\)/);
  assert.match(renderPaginationSource, /getTrackerEntryActionsController\(\)/);
  assert.match(changePageSource, /getTrackerEntryActionsController\(\)/);
  assert.match(changePageToSource, /getTrackerEntryActionsController\(\)/);
  assert.match(saveEntryPatchSource, /getTrackerEntryActionsController\(\)/);
  assert.match(clearEntryPatchSource, /getTrackerEntryActionsController\(\)/);
  assert.match(hydratePatchFieldOptionsSource, /getTrackerEntryActionsController\(\)/);
  assert.doesNotMatch(toggleSource, /TRACKER_BOARD_BLANK_PRIORITY_FIELDS/);
  assert.doesNotMatch(beginSource, /state\.trackerBoardEdit =/);
  assert.doesNotMatch(resetSource, /draftValue:/);
  assert.doesNotMatch(actorLabelSource, /patchActorLabel/);
  assert.doesNotMatch(totalPagesSource, /trackerEntriesTotal/);
  assert.doesNotMatch(renderPaginationSource, /entriesPageMeta\.textContent/);
  assert.doesNotMatch(changePageSource, /state\.trackerFilters\.page =/);
  assert.doesNotMatch(changePageToSource, /Number\(page\)/);
  assert.doesNotMatch(saveEntryPatchSource, /patchTrackerEntry\(/);
  assert.doesNotMatch(clearEntryPatchSource, /patchTrackerEntry\(/);
  assert.doesNotMatch(hydratePatchFieldOptionsSource, /EDITABLE_FIELDS\.map/);

  const trackerEntryActionsController = context.getTrackerEntryActionsController();
  assert.equal(trackerEntryActionsController, context.getTrackerEntryActionsController());
  assert.equal(calls.filter(([type]) => type === "helper").length, 1);
  assert.equal(calls.filter(([type]) => type === "factory").length, 1);
  assert.strictEqual(harness.capturedHelperContext, calls.find(([type]) => type === "helper")[1]);
  assert.strictEqual(harness.capturedFactoryDeps, calls.find(([type]) => type === "factory")[1]);
  assert.notStrictEqual(harness.capturedFactoryDeps, harness.capturedHelperContext);
  assert.strictEqual(
    harness.capturedHelperContext.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    context.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
  );
  assert.strictEqual(
    harness.capturedFactoryDeps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    context.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
  );

  assert.equal(context.toggleTrackerBoardBlankPriority("demand_contact"), "toggle-blank-priority");
  assert.deepEqual(calls[2], ["toggleTrackerBoardBlankPriority", "demand_contact"]);
  assert.equal(context.beginTrackerBoardEdit("entry-7", "project_name"), "begin-board-edit");
  assert.deepEqual(calls[3], ["beginTrackerBoardEdit", "entry-7", "project_name"]);
  assert.equal(context.resetTrackerBoardEdit(), "reset-board-edit");
  assert.deepEqual(calls[4], ["resetTrackerBoardEdit"]);
  assert.equal(context.resolveTrackerPatchActorLabel(), "actor-label");
  assert.deepEqual(calls[5], ["resolveTrackerPatchActorLabel"]);
  assert.equal(context.getEntriesTotalPages(), 7);
  assert.deepEqual(calls[6], ["getEntriesTotalPages"]);
  assert.equal(context.renderEntriesPagination(), "render-pagination");
  assert.deepEqual(calls[7], ["renderEntriesPagination"]);
  assert.equal(context.changeEntriesPage(1), "change-page");
  assert.deepEqual(calls[8], ["changeEntriesPage", 1]);
  assert.equal(context.changeEntriesPageTo(3), "change-page-to");
  assert.deepEqual(calls[9], ["changeEntriesPageTo", 3]);
  assert.equal(await context.saveEntryPatch({ type: "submit" }), "save-entry-patch");
  assert.deepEqual(calls[10], ["saveEntryPatch", { type: "submit" }]);
  assert.equal(await context.clearEntryPatch(), "clear-entry-patch");
  assert.deepEqual(calls[11], ["clearEntryPatch"]);
  assert.equal(context.hydratePatchFieldOptions(), "hydrate-patch-options");
  assert.deepEqual(calls[12], ["hydratePatchFieldOptions"]);
});

test("tracker board render wrappers stay thin and delegate through app-support", () => {
  const source = readAppSource();
  const headerSource = extractFunction(
    source,
    "function renderTrackerBoardHeaderCell(column) {",
    "function isTrackerBoardBlankValue(value) {",
  );
  const blankValueSource = extractFunction(
    source,
    "function isTrackerBoardBlankValue(value) {",
    "function sortTrackerBoardEntries(entries) {",
  );
  const sortSource = extractFunction(
    source,
    "function sortTrackerBoardEntries(entries) {",
    "function buildTrackerBoardCellMarkupFallback({ entry, column, displayNo, trackerBoardEdit = null }, { escapeHtml: fallbackEscapeHtml = escapeHtml, textareaFields = TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {",
  );
  const cellMarkupSource = extractFunction(
    source,
    "function buildTrackerBoardCellMarkupFallback({ entry, column, displayNo, trackerBoardEdit = null }, { escapeHtml: fallbackEscapeHtml = escapeHtml, textareaFields = TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {",
    "function buildTrackerBoardEditingCellMarkupFallback(",
  );
  const editingMarkupSource = extractFunction(
    source,
    "function buildTrackerBoardEditingCellMarkupFallback(",
    "function renderTrackerBoardCell({ entry, column, displayNo }) {",
  );
  const cellSource = extractFunction(
    source,
    "function renderTrackerBoardCell({ entry, column, displayNo }) {",
    "function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {",
  );
  const editingSource = extractFunction(
    source,
    "function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {",
    "function beginTrackerBoardEdit(entryId, fieldName) {",
  );

  assert.match(headerSource, /APP_SUPPORT\.renderTrackerBoardHeaderCellBridge\(/);
  assert.match(blankValueSource, /APP_SUPPORT\.isTrackerBoardBlankValueBridge\(/);
  assert.match(sortSource, /APP_SUPPORT\.sortTrackerBoardEntriesBridge\(/);
  assert.match(cellMarkupSource, /APP_SUPPORT\.buildTrackerBoardCellMarkupFallbackBridge\(/);
  assert.match(editingMarkupSource, /APP_SUPPORT\.buildTrackerBoardEditingCellMarkupFallbackBridge\(/);
  assert.match(cellSource, /APP_SUPPORT\.renderTrackerBoardCellBridge\(/);
  assert.match(editingSource, /APP_SUPPORT\.renderTrackerBoardEditingCellBridge\(/);

  assert.doesNotMatch(headerSource, /tracker-board-sort-trigger/);
  assert.doesNotMatch(blankValueSource, /String\(value \?\? ""\)\.trim/);
  assert.doesNotMatch(sortSource, /buildSortedTrackerBoardEntries\(/);
  assert.doesNotMatch(cellMarkupSource, /renderTrackerBoardEditingCellFallback/);
  assert.doesNotMatch(editingMarkupSource, /renderTrackerBoardEditingCellFallback/);
  assert.doesNotMatch(cellSource, /TRACKER_BOARD_RUNTIME\?\.renderTrackerBoardCell/);
  assert.doesNotMatch(editingSource, /TRACKER_BOARD_RUNTIME\?\.renderTrackerBoardEditingCell/);
});

test("getTrackerEntryActionsController fails fast when the tracker entry actions wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerEntryActionsController() {",
    "function getSelectedEntryController() {",
  );

  const context = vm.createContext({
    console,
    window: {
      TRACKER_ENTRY_ACTIONS_CONTROLLER: {
        createTrackerEntryActionsController() {
          return {};
        },
      },
    },
    trackerEntryActionsController: null,
    state: {},
    dom: {},
    EDITABLE_FIELDS: ["project_name"],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact"]),
    escapeHtml: () => "",
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    renderTrackerBoard: () => {},
    loadTrackerEntries: async () => {},
    setBusy: () => {},
    patchTrackerEntry: async () => {},
    flash: () => {},
    syncTrackerEntryAfterPatch: async () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getTrackerEntryActionsController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("utility wrappers stay thin and delegate through app support runtime", async () => {
  const source = readAppSource();
  const focusSource = extractFunction(
    source,
    "function focusTrackerChangeEntry(entryId, entries = state.trackerEntries) {",
    "function focusTrackerChangePanel() {",
  );
  const handleSource = extractFunction(
    source,
    "function handleOutOfRangePageError(error, filterState, scopeLabel) {",
    "function resolveActiveTrackerRunId() {",
  );
  const resolveSource = extractFunction(
    source,
    "function resolveActiveTrackerRunId() {",
    "if (typeof window !== \"undefined\" && window.__SPMS_TEST_MODE__) {",
  );

  assert.match(focusSource, /APP_SUPPORT\.focusTrackerChangeEntry\(/);
  assert.match(handleSource, /APP_SUPPORT\.handleOutOfRangePageError\(/);
  assert.match(resolveSource, /APP_SUPPORT\.resolveActiveTrackerRunId\(\)/);
  assert.doesNotMatch(focusSource, /scrollIntoView/);
  assert.doesNotMatch(handleSource, /fallbackPage/);
  assert.doesNotMatch(resolveSource, /selectedRun\.run_type/);

  const scrollEvents = [];
  const state = {
    uiMode: "admin",
    trackerEntries: [{ id: "entry-1" }],
    selectedEntryId: "",
    drawerOpen: false,
    selectedRun: { run_type: "tracker_export", id: "run-9" },
    selectedTrackerRunId: "run-old",
  };
  const appSupport = createAppSupportStub();
  Object.assign(appSupport, {
    state,
    dom: {
      entryEditor: {
        scrollIntoView(options) {
          scrollEvents.push(["editor", options]);
        },
      },
    },
    documentObject: {
      querySelector() {
        return {
          scrollIntoView(options) {
            scrollEvents.push(["entry", options]);
          },
        };
      },
    },
    windowObject: {
      CSS: {
        escape: (value) => `escaped:${value}`,
      },
    },
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    loadSelectedEntryDetail: async () => ({}),
    flash: () => {},
  });
  const context = vm.createContext({
    console,
    APP_SUPPORT: appSupport,
    state,
  });

  vm.runInContext(`${focusSource}\n${handleSource}\n${resolveSource}`, context, { filename: appPath });

  assert.equal(context.resolveActiveTrackerRunId(), "run-9");
  const filterState = { page: 4, pageSize: 10 };
  assert.equal(
    context.handleOutOfRangePageError({
      message: "Requested range not satisfiable. There are only 21 rows.",
    }, filterState, "트래커"),
    true,
  );
  assert.equal(filterState.page, 3);
  await context.focusTrackerChangeEntry(" entry-7 ");
  assert.equal(state.selectedEntryId, "entry-7");
  assert.equal(state.drawerOpen, false);
  assert.equal(scrollEvents.length, 2);
  assert.deepEqual(scrollEvents[0], ["entry", { behavior: "smooth", block: "center" }]);
  assert.deepEqual(scrollEvents[1], ["editor", { behavior: "smooth", block: "start" }]);
});

test("download wrappers stay thin and delegate through the download controller", async () => {
  const { context, calls, getterSource, wrapperSource } = createDownloadControllerHarness();

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createDownloadControllerDeps"/);
  assert.match(getterSource, /buildDownloadControllerDeps\(\)/);
  assert.match(wrapperSource, /getDownloadController\(\)/);
  assert.doesNotMatch(wrapperSource, /content-disposition/);
  assert.doesNotMatch(wrapperSource, /download-progress-overlay/);
  assert.doesNotMatch(wrapperSource, /requestAnimationFrame/);
  assert.doesNotMatch(wrapperSource, /fetch\(/);
  assert.doesNotMatch(wrapperSource, /URLSearchParams/);
  assert.doesNotMatch(wrapperSource, /tracker-entry-summaries\/download-jobs/);
  assert.doesNotMatch(wrapperSource, /selectedTrackerWorkbookArtifactId/);
  assert.doesNotMatch(wrapperSource, /window\.location\.href/);
  assert.doesNotMatch(getterSource, /readTrackerFiltersFromControls:/);
  assert.doesNotMatch(getterSource, /resolveActiveTrackerRunId:/);

  const downloadController = context.getDownloadController();
  assert.equal(downloadController, context.getDownloadController());
  assert.equal(calls.length, 1, "download controller should be created once");
  assert.equal(calls[0][0], "factory");

  assert.equal(context.extractDownloadFilename({ headers: {} }, "fallback"), "extracted-file.xlsx");
  assert.deepEqual(calls[1], ["extractDownloadFilename", { headers: {} }, "fallback"]);
  assert.equal(context.ensureDownloadProgressOverlay(), "overlay");
  assert.deepEqual(calls[2], ["ensureDownloadProgressOverlay"]);
  assert.equal(context.showDownloadProgressOverlay(["one", "two"], "title"), "shown");
  assert.deepEqual(calls[3], ["showDownloadProgressOverlay", ["one", "two"], "title"]);
  assert.equal(context.updateDownloadProgressOverlay("msg"), "updated");
  assert.deepEqual(calls[4], ["updateDownloadProgressOverlay", "msg"]);
  assert.equal(context.hideDownloadProgressOverlay(), "hidden");
  assert.deepEqual(calls[5], ["hideDownloadProgressOverlay"]);
  assert.equal(await context.triggerFileDownload("/download", { fallbackName: "file.xlsx" }), "file-download");
  assert.equal(calls[6][0], "triggerFileDownload");
  assert.equal(calls[6][1], "/download");
  assert.deepEqual(Object.keys(calls[6][2]).sort(), ["fallbackName"]);
  assert.equal(calls[6][2].fallbackName, "file.xlsx");
  assert.equal(context.downloadSalesWorkbook("company", { id: "button" }), "sales-workbook");
  assert.deepEqual(calls[7], ["downloadSalesWorkbook", "company", { id: "button" }]);
  assert.equal(context.buildTrackerEntriesDownloadUrl("csv"), "/delegated/csv");
  assert.deepEqual(calls[8], ["buildTrackerEntriesDownloadUrl", "csv"]);
  assert.deepEqual(JSON.parse(JSON.stringify(context.buildTrackerEntriesDownloadJobPayload())), { delegated: true });
  assert.deepEqual(calls[9], ["buildTrackerEntriesDownloadJobPayload"]);
  const pollResult = await context.pollTrackerDownloadJob("job-1", { intervalMs: 10 });
  assert.equal(pollResult.status, "success");
  assert.equal(pollResult.download_url, "/downloaded.xlsx");
  assert.deepEqual(calls[10], ["pollTrackerDownloadJob", "job-1", { intervalMs: 10 }]);
  assert.equal(await context.triggerTrackerEntriesXlsxDownload({ id: "button" }), "tracker-xlsx");
  assert.deepEqual(calls[11], ["triggerTrackerEntriesXlsxDownload", { id: "button" }]);
  assert.equal(context.buildTrackerEntriesDownloadWarmUrl(), "/warm");
  assert.deepEqual(calls[12], ["buildTrackerEntriesDownloadWarmUrl"]);
  assert.equal(await context.warmTrackerEntriesDownload(), "warm");
  assert.deepEqual(calls[13], ["warmTrackerEntriesDownload"]);
});

test("selected entry controller wrappers stay thin and delegate through the selected entry controller", () => {
  const { context, calls, getterSource, wrapperSource } = createSelectedEntryControllerHarness();

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createSelectedEntryControllerDeps"/);
  assert.match(getterSource, /buildSelectedEntryControllerDeps\(\)/);
  assert.match(wrapperSource, /getSelectedEntryController\(\)/);
  assert.doesNotMatch(getterSource, /buildSelectedEntryLoadingView:/);
  assert.doesNotMatch(getterSource, /buildPatchPanelView:/);
  assert.doesNotMatch(getterSource, /loadSelectedEntryAudit:/);

  const selectedEntryController = context.getSelectedEntryController();
  assert.equal(selectedEntryController, context.getSelectedEntryController());
  assert.equal(calls.length, 1, "selected entry controller should be created once");
  assert.equal(calls[0][0], "factory");

  assert.equal(context.renderSelectedEntryLoading({ id: "entry-1" }, "error"), "loading");
  assert.deepEqual(calls[1], ["renderSelectedEntryLoading", { id: "entry-1" }, "error"]);
  assert.equal(context.getSelectedEntryDisplayView({ id: "entry-1" }, { summaryOnly: true }), "display-view");
  assert.equal(calls[2][0], "getSelectedEntryDisplayView");
  assert.deepEqual(plain(calls[2][1]), { id: "entry-1" });
  assert.deepEqual(plain(calls[2][2]), { summaryOnly: true });
  assert.equal(context.renderSelectedEntry({ id: "entry-1" }, { summaryOnly: true }), "selected-entry");
  assert.equal(calls[3][0], "renderSelectedEntry");
  assert.deepEqual(plain(calls[3][1]), { id: "entry-1" });
  assert.deepEqual(plain(calls[3][2]), { summaryOnly: true });
  assert.equal(context.renderEntryDiagnostics({ id: "entry-1" }, { summaryOnly: false, view: { mode: "full" } }), "entry-diagnostics");
  assert.equal(calls[4][0], "renderEntryDiagnostics");
  assert.deepEqual(plain(calls[4][1]), { id: "entry-1" });
  assert.deepEqual(plain(calls[4][2]), { summaryOnly: false, view: { mode: "full" } });
  assert.equal(context.renderEntryFieldGrid({ id: "entry-1" }, { view: { mode: "grid" } }), "entry-field-grid");
  assert.equal(calls[5][0], "renderEntryFieldGrid");
  assert.deepEqual(plain(calls[5][1]), { id: "entry-1" });
  assert.deepEqual(plain(calls[5][2]), { view: { mode: "grid" } });
  assert.equal(context.renderDrawer({ id: "entry-1" }, { view: { mode: "drawer" } }), "drawer");
  assert.equal(calls[6][0], "renderDrawer");
  assert.deepEqual(plain(calls[6][1]), { id: "entry-1" });
  assert.deepEqual(plain(calls[6][2]), { view: { mode: "drawer" } });
  assert.equal(context.syncPatchValueFromSelectedEntry({ patchView: { fieldName: "project_name" } }), "sync-patch");
  assert.equal(calls[7][0], "syncPatchValueFromSelectedEntry");
  assert.deepEqual(plain(calls[7][1]), { patchView: { fieldName: "project_name" } });
});

test("getDownloadController fails fast when the download wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getDownloadController() {",
    "function getTrackerEntryActionsController() {",
  );

  const context = vm.createContext({
    console,
    window: {
      DOWNLOAD_CONTROLLER: {
        createDownloadController() {
          return {};
        },
      },
    },
    downloadController: null,
    state: {},
    dom: {},
    document: {},
    setBusy: () => {},
    flash: () => {},
    api: async () => {},
    readTrackerFiltersFromControls: () => ({}),
    useGlobalTrackerEntriesScope: () => false,
    resolveActiveTrackerRunId: () => "run-1",
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getDownloadController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("getAdminGoogleSheetsController uses the wiring helper and fails fast when it is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getAdminGoogleSheetsController() {",
    "function getRuntimeEnhancements() {",
  );

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createAdminGoogleSheetsControllerDeps"/);
  assert.match(getterSource, /buildAdminGoogleSheetsControllerDeps\(\)/);

  const context = vm.createContext({
    console,
    APP_SUPPORT: createAppSupportStub(),
    window: {
      SPMSAppControllerWiringRuntime: {},
      SPMSAdminGoogleSheetsController: {
        createAdminGoogleSheetsController() {
          return {};
        },
      },
    },
    adminGoogleSheetsController: null,
    state: {},
    dom: {},
    api: () => {},
    flash: () => {},
    renderAdminTopNavigation: () => {},
    renderAdminEmbedPanel: () => {},
    canLoadProtectedConsoleData: () => false,
    maybeResolveLegacyAdminAliasToSheetTab: () => null,
    getValidatedActiveAdminGoogleSheetTab: () => null,
    isAdminGoogleSheetTabKey: () => false,
    isPendingLegacyAdminAlias: () => false,
    shouldDeferAdminGoogleSheetPayloadLoad: () => false,
    clearAdminGoogleSheetPopupStateForTab: () => {},
    syncUrlState: () => {},
    applyUiMode: () => {},
    persistAdminGoogleSheetsCache: () => {},
    ADMIN_GOOGLE_SHEETS_RUNTIME: {},
    ADMIN_GOOGLE_SHEETS_CONTROLLER_RUNTIME: {
      createAdminGoogleSheetsController() {
        return {};
      },
    },
    DEFAULT_ADMIN_TAB: "project-status",
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getAdminGoogleSheetsController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("getAdminGoogleSheetsController passes the actual factory deps and reuses the controller", () => {
  const harness = createAdminGoogleSheetsHarness();
  const firstController = harness.context.getAdminGoogleSheetsController();
  const secondController = harness.context.getAdminGoogleSheetsController();

  assert.strictEqual(firstController, harness.controller);
  assert.strictEqual(secondController, harness.controller);
  assert.strictEqual(firstController, secondController);
  assert.strictEqual(harness.factoryCalls, 1);
  assert.ok(harness.calls.includes("createAdminGoogleSheetsControllerDepsHelpers"));
  assert.ok(harness.calls.some((entry) => Array.isArray(entry) && entry[0] === "factory"));
  assert.ok(harness.factoryDeps);
  assertAdminGoogleSheetsControllerDeps(harness.factoryDeps, harness.context);
});

test("download controller keeps the download workflow intact after modularization", async () => {
  const harness = createDownloadControllerBehaviorHarness();
  const { controller, context, calls, overlayTitle, overlayDetail, setGlobalScope, resolveWarmRequest } = harness;

  const fileButton = { id: "sales-download-button", textContent: "영업 엑셀 다운로드" };
  await controller.triggerFileDownload("/api/files/sales.xlsx", {
    button: fileButton,
    showProgressOverlay: true,
    fallbackName: "fallback.xlsx",
  });

  assert.ok(calls.some((entry) => entry[0] === "setBusy" && entry[1] === "sales-download-button" && entry[2] === true));
  assert.ok(calls.some((entry) => entry[0] === "fetch" && entry[1] === "/api/files/sales.xlsx"));
  assert.ok(calls.some((entry) => entry[0] === "createObjectURL" && entry[1]?.blob === true));
  assert.ok(calls.some((entry) => entry[0] === "anchorClick" && entry[1] === "final report.xlsx"));
  assert.ok(calls.some((entry) => entry[0] === "revokeObjectURL" && entry[1] === "blob:download"));
  assert.equal(overlayTitle.textContent, "엑셀 다운로드를 준비하고 있습니다.");
  assert.equal(overlayDetail.textContent, "브라우저 다운로드를 시작하는 중입니다.");

  context.state.selectedTrackerWorkbookArtifactId = null;
  context.state.trackerFilters = {
    q: "alpha",
    region: "서울",
    editedOnly: true,
  };
  context.state.uiMode = "user";
  const trackerButton = { id: "tracker-download-button", textContent: "프로젝트 현황 다운로드" };
  await controller.triggerTrackerEntriesXlsxDownload(trackerButton);

  const trackerJobPost = calls.find((entry) => entry[0] === "api" && entry[1] === "/api/tracker-entry-summaries/download-jobs" && entry[2].method === "POST");
  assert.ok(trackerJobPost, "expected tracker download job creation request");
  assert.equal(
    trackerJobPost[2].body,
    JSON.stringify({
      format: "xlsx",
      q: "alpha",
      region: "서울",
      exclude_auxiliary_titles: false,
      edited_only: true,
      blank_progress_note: true,
      source_tracker_run_id: "run-1",
      source_run_id: null,
      sheet_name: "",
      section_name: "",
    }),
  );
  assert.equal(context.window.location.href, "/api/tracker-entry-summaries/download/job-1.xlsx");
  setGlobalScope(true);
  const warm1 = controller.warmTrackerEntriesDownload();
  const warm2 = controller.warmTrackerEntriesDownload();
  assert.ok(warm1);
  assert.ok(warm2);
  assert.equal(
    calls.filter((entry) => entry[0] === "api" && String(entry[1]).startsWith("/api/tracker-entry-summaries/download/warm")).length,
    1,
  );
  resolveWarmRequest({ ok: true });
  await warm1;
  assert.equal(context.state.trackerDownloadWarmRequest, null);
  assert.equal(context.state.trackerDownloadWarmRequestKey, "");
});

test("tracker diagnostics panel wrappers keep runtime guards and delegate markup rendering", async () => {
  const { context, calls, getterSource, wrapperSource } = createTrackerDiagnosticsPanelHarness();

  assert.match(getterSource, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSource, /wiringDepsFactoryName:\s*"createTrackerDiagnosticsPanelControllerDeps"/);
  assert.match(getterSource, /buildTrackerDiagnosticsPanelControllerDeps\(\)/);
  assert.match(wrapperSource, /getTrackerDiagnosticsPanelController\(\)/);
  assert.match(wrapperSource, /TRACKER_DIAGNOSTICS_RUNTIME/);
  assert.doesNotMatch(wrapperSource, /trackerChangePanel\.classList\.add/);
  assert.doesNotMatch(wrapperSource, /buildTrackerChangeBellPopoverMarkup/);
  assert.doesNotMatch(wrapperSource, /buildBackfillConflictsMarkup/);
  assert.doesNotMatch(wrapperSource, /buildContactResolutionSummaryMarkup/);
  assert.doesNotMatch(wrapperSource, /buildTrackerCleanupPreviewMarkup/);
  assert.doesNotMatch(wrapperSource, /scopeLabel: scope\.scopeLabel/);
  assert.doesNotMatch(getterSource, /formatContactResolutionStatusLabel:/);
  assert.doesNotMatch(getterSource, /closeTrackerChangeModal:/);

  const trackerDiagnosticsPanelController = context.getTrackerDiagnosticsPanelController();
  assert.equal(trackerDiagnosticsPanelController, context.getTrackerDiagnosticsPanelController());
  assert.equal(calls.length, 1, "tracker diagnostics panel controller should be created once");
  assert.equal(calls[0][0], "factory");

  assert.equal(context.focusTrackerChangePanel(), "focus-panel");
  assert.deepEqual(calls[1], ["focusTrackerChangePanel"]);
  assert.equal(context.bindTrackerChangeEventActions({ id: "change-actions" }), "bind-change-actions");
  assert.deepEqual(calls[2], ["bindTrackerChangeEventActions", "change-actions"]);
  assert.equal(context.bindBackfillConflictActions({ id: "backfill-actions" }), "bind-backfill-actions");
  assert.deepEqual(calls[3], ["bindBackfillConflictActions", "backfill-actions"]);
  assert.equal(context.setTrackerChangeBellPopoverOpen(true), "set-popover");
  assert.deepEqual(calls[4], ["setTrackerChangeBellPopoverOpen", true]);
  assert.equal(context.renderTrackerChangeBellPopover(), "render-popover");
  assert.deepEqual(calls[5], ["renderTrackerChangeBellPopover"]);
  assert.equal(context.renderTrackerChangeEventsList({ id: "list" }), "render-change-list");
  assert.deepEqual(calls[6], ["renderTrackerChangeEventsList", "list"]);
  assert.equal(context.renderTrackerChangeEventsPanel(), "render-change-panel");
  assert.deepEqual(calls[7], ["renderTrackerChangeEventsPanel"]);
  assert.equal(context.renderBackfillConflictsPanel(), "render-backfill-panel");
  assert.deepEqual(calls[8], ["renderBackfillConflictsPanel"]);
  assert.equal(context.renderTrackerChangeEventUnreadCount(), "render-unread");
  assert.deepEqual(calls[9], ["renderTrackerChangeEventUnreadCount"]);
  assert.equal(context.renderTrackerContactResolutionSummary("bad"), "contact-resolution");
  assert.deepEqual(calls[10], ["renderTrackerContactResolutionSummary", "bad"]);
  assert.equal(context.renderTrackerCleanupPreview("warn"), "cleanup-preview");
  assert.deepEqual(calls[11], ["renderTrackerCleanupPreview", "warn"]);
  assert.equal(
    await context.resolveBackfillConflict({ conflictId: "conflict-1", resolution: "dismissed" }),
    "resolve-backfill",
  );
  assert.equal(calls[12][0], "resolveBackfillConflict");
  assert.equal(calls[12][1].conflictId, "conflict-1");
  assert.equal(calls[12][1].resolution, "dismissed");
});

test("getTrackerDiagnosticsPanelController fails fast when the tracker diagnostics wiring runtime is missing", () => {
  const source = readAppSource();
  const getterSource = extractFunction(
    source,
    "function getTrackerDiagnosticsPanelController() {",
    "function getTrackerEntryActionsController() {",
  );

  const context = vm.createContext({
    console,
    window: {
      TRACKER_DIAGNOSTICS_PANEL_CONTROLLER: {
        createTrackerDiagnosticsPanelController() {
          return {};
        },
      },
    },
    trackerDiagnosticsPanelController: null,
    TRACKER_DIAGNOSTICS_RUNTIME: {},
    dom: {},
    state: {},
    api: async () => {},
    flash: () => {},
    getTrackerController: () => ({ runtime: true }),
    escapeHtml: () => "",
    formatDate: () => "",
    formatContactResolutionStatusLabel: () => "",
    formatContactResolutionReasonLabel: () => "",
    formatBackfillConflictResolutionLabel: () => "",
    getTrackerDiagnosticsScope: () => ({ trackerRunId: "run-1" }),
    buildTrackerChangeEventsMarkup: () => "",
    buildTrackerChangeBellPopoverMarkup: () => "",
    buildBackfillConflictsMarkup: () => "",
    buildBackfillConflictsView: () => ({ html: "" }),
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    loadSelectedEntryDetail: async () => {},
    focusTrackerChangeEntry: async () => {},
    closeTrackerChangeModal: () => {},
  });

  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getTrackerDiagnosticsPanelController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});
