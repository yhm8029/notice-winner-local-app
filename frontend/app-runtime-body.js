if (typeof window !== "undefined") {
  window.__SPMS_APP_RUNTIME_BODY__ = true;
}
function loadAppRuntimeBodyRuntime() {
  if (window.SPMSAppRuntimeBodyRuntime) return window.SPMSAppRuntimeBodyRuntime;
  if (typeof XMLHttpRequest === "function" && typeof document !== "undefined") {
    const request = new XMLHttpRequest();
    request.open("GET", "/app/app-runtime-body-runtime.js?v=20260602b", false);
    request.send(null);
    if ((request.status >= 200 && request.status < 300) || request.status === 0) (0, eval)(request.responseText);
  }
  if (!window.SPMSAppRuntimeBodyRuntime) throw new Error("SPMSAppRuntimeBodyRuntime is required before app.js loads");
  return window.SPMSAppRuntimeBodyRuntime;
}
const APP_RUNTIME_BODY_RUNTIME = loadAppRuntimeBodyRuntime();
function loadAppRuntimeBodyControllerRuntime() {
  if (window.SPMSAppRuntimeBodyControllerRuntime) return window.SPMSAppRuntimeBodyControllerRuntime;
  if (typeof XMLHttpRequest === "function" && typeof document !== "undefined") {
    const request = new XMLHttpRequest();
    request.open("GET", "/app/app-runtime-body-controller-runtime.js?v=20260425a", false);
    request.send(null);
    if ((request.status >= 200 && request.status < 300) || request.status === 0) (0, eval)(request.responseText);
  }
  if (!window.SPMSAppRuntimeBodyControllerRuntime) throw new Error("SPMSAppRuntimeBodyControllerRuntime is required before app.js loads");
  return window.SPMSAppRuntimeBodyControllerRuntime;
}
const APP_RUNTIME_BODY_CONTROLLER_RUNTIME = loadAppRuntimeBodyControllerRuntime();
function loadAppRuntimeBodyConsoleRuntime() {
  if (window.SPMSAppRuntimeBodyConsoleRuntime) return window.SPMSAppRuntimeBodyConsoleRuntime;
  if (typeof XMLHttpRequest === "function" && typeof document !== "undefined") {
    const request = new XMLHttpRequest();
    request.open("GET", "/app/app-runtime-body-console-runtime.js?v=20260425a", false);
    request.send(null);
    if ((request.status >= 200 && request.status < 300) || request.status === 0) (0, eval)(request.responseText);
  }
  if (!window.SPMSAppRuntimeBodyConsoleRuntime) throw new Error("SPMSAppRuntimeBodyConsoleRuntime is required before app.js loads");
  return window.SPMSAppRuntimeBodyConsoleRuntime;
}
const APP_RUNTIME_BODY_CONSOLE_RUNTIME = loadAppRuntimeBodyConsoleRuntime();
function loadAppRuntimeBodyAdminSalesRuntime() {
  if (window.SPMSAppRuntimeBodyAdminSalesRuntime) return window.SPMSAppRuntimeBodyAdminSalesRuntime;
  if (typeof XMLHttpRequest === "function" && typeof document !== "undefined") {
    const request = new XMLHttpRequest();
    request.open("GET", "/app/app-runtime-body-admin-sales-runtime.js?v=20260425a", false);
    request.send(null);
    if ((request.status >= 200 && request.status < 300) || request.status === 0) (0, eval)(request.responseText);
  }
  if (!window.SPMSAppRuntimeBodyAdminSalesRuntime) throw new Error("SPMSAppRuntimeBodyAdminSalesRuntime is required before app.js loads");
  return window.SPMSAppRuntimeBodyAdminSalesRuntime;
}
const APP_RUNTIME_BODY_ADMIN_SALES_RUNTIME = loadAppRuntimeBodyAdminSalesRuntime();
function loadAppRuntimeBodyShellRuntime() {
  if (window.SPMSAppRuntimeBodyShellRuntime) return window.SPMSAppRuntimeBodyShellRuntime;
  if (typeof XMLHttpRequest === "function" && typeof document !== "undefined") {
    const request = new XMLHttpRequest();
    request.open("GET", "/app/app-runtime-body-shell-runtime.js?v=20260602g", false);
    request.send(null);
    if ((request.status >= 200 && request.status < 300) || request.status === 0) (0, eval)(request.responseText);
  }
  if (window.SPMSAppRuntimeBodyShellRuntime) return window.SPMSAppRuntimeBodyShellRuntime;
  return {
    CANONICAL_APP_URL: "/",
    CANONICAL_URL_STATE_STORAGE_KEY: "notice-winner-pipeline-web.canonicalUrlState.v1",
    writeCanonicalUrlStateSearch(params) {
      try {
        const next = params instanceof URLSearchParams ? params.toString() : String(params || "");
        if (next) window.sessionStorage?.setItem?.(this.CANONICAL_URL_STATE_STORAGE_KEY, next);
        else window.sessionStorage?.removeItem?.(this.CANONICAL_URL_STATE_STORAGE_KEY);
      } catch (_error) {}
    },
    createBootstrapSalesStateHelpers({
      salesStateHelpers,
      getVisibleSalesProjectIds,
      getSalesClaimForProject,
      getTrackerProjectSnapshot,
      renderUserSalesProjectFacts,
      isCurrentUserClaimOwner,
      canCurrentUserForceRelease,
      canCurrentUserManageClaim,
      isActiveSalesClaim,
      getOrganizationTransferTargets,
      getSalesNoteDraft,
      setSalesNoteDraft,
      upsertSalesClaim,
      replaceVisibleSalesClaims,
      mergeActiveSalesClaims,
      formatShortDateTime,
      formatEstimatedAmountRangeFromKrw,
    } = {}) {
      if (typeof salesStateHelpers !== "undefined" && salesStateHelpers) return salesStateHelpers;
      return {
        getVisibleSalesProjectIds: typeof getVisibleSalesProjectIds === "function" ? getVisibleSalesProjectIds : () => [],
        getSalesClaimForProject: typeof getSalesClaimForProject === "function" ? getSalesClaimForProject : () => null,
        getTrackerProjectSnapshot: typeof getTrackerProjectSnapshot === "function" ? getTrackerProjectSnapshot : () => null,
        renderUserSalesProjectFacts: typeof renderUserSalesProjectFacts === "function" ? renderUserSalesProjectFacts : () => "",
        isCurrentUserClaimOwner: typeof isCurrentUserClaimOwner === "function" ? isCurrentUserClaimOwner : () => true,
        canCurrentUserForceRelease: typeof canCurrentUserForceRelease === "function" ? canCurrentUserForceRelease : () => false,
        canCurrentUserManageClaim: typeof canCurrentUserManageClaim === "function" ? canCurrentUserManageClaim : () => false,
        isActiveSalesClaim: typeof isActiveSalesClaim === "function" ? isActiveSalesClaim : () => false,
        getOrganizationTransferTargets: typeof getOrganizationTransferTargets === "function" ? getOrganizationTransferTargets : () => [],
        getSalesNoteDraft: typeof getSalesNoteDraft === "function" ? getSalesNoteDraft : () => "",
        setSalesNoteDraft: typeof setSalesNoteDraft === "function" ? setSalesNoteDraft : () => {},
        upsertSalesClaim: typeof upsertSalesClaim === "function" ? upsertSalesClaim : () => {},
        replaceVisibleSalesClaims: typeof replaceVisibleSalesClaims === "function" ? replaceVisibleSalesClaims : () => {},
        mergeActiveSalesClaims: typeof mergeActiveSalesClaims === "function" ? mergeActiveSalesClaims : () => {},
        formatShortDateTime: typeof formatShortDateTime === "function" ? formatShortDateTime : () => "",
        formatEstimatedAmountRangeFromKrw: typeof formatEstimatedAmountRangeFromKrw === "function" ? formatEstimatedAmountRangeFromKrw : () => "",
      };
    },
    buildUrlForState({ state, pathname = null, uiMode, adminTab, defaultAdminTab, locationPathname, resolveStatePathname, persist = false } = {}) {
      const params = new URLSearchParams();
      if (state.runFilters.status) params.set("run_status", state.runFilters.status);
      if (state.runFilters.runType) params.set("run_type", state.runFilters.runType);
      if (state.runFilters.from) params.set("run_from", state.runFilters.from);
      if (state.runFilters.to) params.set("run_to", state.runFilters.to);
      if (state.runFilters.page !== 1) params.set("run_page", String(state.runFilters.page));
      if (state.runFilters.pageSize !== 20) params.set("run_page_size", String(state.runFilters.pageSize));
      if (state.selectedRunId) params.set("run_id", state.selectedRunId);
      if (state.selectedTrackerRunId) params.set("tracker_run_id", state.selectedTrackerRunId);
      if (state.trackerFilters.q) params.set("tracker_q", state.trackerFilters.q);
      if (state.trackerFilters.region) params.set("tracker_region", state.trackerFilters.region);
      if (state.trackerFilters.noticeYear) params.set("tracker_notice_year", state.trackerFilters.noticeYear);
      if (state.trackerFilters.editedOnly) params.set("tracker_edited", "1");
      if (state.trackerFilters.page !== 1) params.set("tracker_page", String(state.trackerFilters.page));
      if (state.trackerFilters.pageSize !== 20) params.set("tracker_page_size", String(state.trackerFilters.pageSize));
      if (!state.autoRefresh) params.set("auto_refresh", "0");
      if (state.reportKey && state.reportKey !== "phase1-artifact-diff") params.set("report_key", state.reportKey);
      if (state.selectedReportJobId) params.set("report_job_id", state.selectedReportJobId);
      if (uiMode === "admin") params.set("mode", "admin");
      if (adminTab && adminTab !== defaultAdminTab) params.set("admin_tab", adminTab);
      if (persist) this.writeCanonicalUrlStateSearch(params);
      return this.CANONICAL_APP_URL;
    },
    syncUrlState({ state, windowObject, buildUrlForStateFn }, options = {}) {
      const { historyMode = "replace" } = options;
      const nextUrl = buildUrlForStateFn({ ...options, persist: true });
      const canonicalSearch = String(windowObject?.sessionStorage?.getItem?.(this.CANONICAL_URL_STATE_STORAGE_KEY) || "");
      if (state && typeof state === "object") {
        state.canonicalUrlStateHydrated = true;
        state.canonicalUrlStateSource = canonicalSearch ? "storage" : "";
        state.canonicalLocationPathname = windowObject?.location?.pathname || this.CANONICAL_APP_URL;
        state.canonicalLocationSearch = canonicalSearch ? `?${canonicalSearch}` : "";
      }
      if (historyMode === "push") {
        windowObject.history.pushState({}, "", nextUrl);
        return;
      }
      windowObject.history.replaceState({}, "", nextUrl);
    },
    openDrawer({ state, dom }) {
      state.drawerOpen = true;
      dom.entryDrawer.classList.remove("hidden");
      dom.entryDrawer.setAttribute("aria-hidden", "false");
    },
    closeDrawer({ state, dom }) {
      state.drawerOpen = false;
      dom.entryDrawer.classList.add("hidden");
      dom.entryDrawer.setAttribute("aria-hidden", "true");
    },
    syncFilterControlsFromState({ state, dom, renderTrackerRegionButtons }) {
      dom.runFilterStatus.value = state.runFilters.status;
      dom.runFilterType.value = state.runFilters.runType;
      dom.runFilterFrom.value = state.runFilters.from;
      dom.runFilterTo.value = state.runFilters.to;
      dom.runPageSize.value = String(state.runFilters.pageSize);
      dom.trackerQuery.value = state.trackerFilters.q;
      renderTrackerRegionButtons();
      dom.trackerPageSize.value = String(state.trackerFilters.pageSize);
      dom.reportSelect.value = state.reportKey;
    },
    readRunFiltersFromControls({ state, dom }) {
      state.runFilters.status = dom.runFilterStatus.value;
      state.runFilters.runType = dom.runFilterType.value;
      state.runFilters.from = dom.runFilterFrom.value;
      state.runFilters.to = dom.runFilterTo.value;
      state.runFilters.pageSize = Number(dom.runPageSize.value || 20);
    },
  };
}
const APP_RUNTIME_BODY_SHELL_RUNTIME = loadAppRuntimeBodyShellRuntime();
const { EDITABLE_FIELDS, RUN_TYPE_LABELS, TRACKER_REGION_OPTIONS, TRACKER_BOARD_COLUMNS, TRACKER_BOARD_BLANK_PRIORITY_FIELDS, TRACKER_CHANGE_FIELD_LABELS, ORG_ROLE_OPTIONS, MEMBERSHIP_STATUS_OPTIONS, TRACKER_BOARD_TEXTAREA_FIELDS, AUTH_MODE_SIGN_IN, AUTH_MODE_SIGN_UP, AUTH_SESSION_HEARTBEAT_MS, AUTH_SESSION_RECHECK_COOLDOWN_MS, PROJECT_RELATED_PREFETCH_LIMIT, TRACKER_DETAIL_PREFETCH_LIMIT, PROJECT_RELATED_READY_CACHE_TTL_MS, PROJECT_RELATED_SEED_CACHE_TTL_MS, PROJECT_RELATED_STORAGE_KEY, PROJECT_RELATED_STORAGE_MAX_ITEMS, SALES_OVERVIEW_STORAGE_KEY, HOME_BOOTSTRAP_STORAGE_KEY, ORG_ADMIN_BOOTSTRAP_STORAGE_KEY, TRACKER_CHANGE_EVENTS_STORAGE_KEY, TRACKER_CHANGE_EVENTS_STORAGE_MAX_ITEMS, TRACKER_CHANGE_EVENTS_CACHE_TTL_MS, APP_ROOT_PATH, DEFAULT_ADMIN_TAB, ADMIN_TABS, LEGACY_ADMIN_ROUTE_ALIASES, getTrackerRenderFallbackRuntime, ensureProjectRelatedAppRuntimeLoaded, normalizePlatformAdminAccountDraft: normalizePlatformAdminAccountDraftBody, syncPlatformAdminAccountDraftFromForm: syncPlatformAdminAccountDraftFromFormBody, formatContractAmountInput: formatContractAmountInputBody, formatContractAmountDisplay: formatContractAmountDisplayBody, openTrackerChangeModal: openTrackerChangeModalBody, closeTrackerChangeModal: closeTrackerChangeModalBody, mountParityReportEnhancements: mountParityReportEnhancementsBody, renderOrgAdminRuntimeReloadFallback: renderOrgAdminRuntimeReloadFallbackBody, runTypeLabel: runTypeLabelBody, isProjectTrackerRun: isProjectTrackerRunBody, useGlobalTrackerEntriesScope: useGlobalTrackerEntriesScopeBody } = APP_RUNTIME_BODY_RUNTIME;
const ADMIN_ROUTE_PATH_SOURCE_MARKERS = Object.freeze(["routePath", "labelHint", "/app/design-list", "/app/planned-orders", "/app/lost", "/app/agency-list"]);
const {
  SPMSCacheRuntime: CACHE_RUNTIME = null, SPMSBootstrapRuntime: BOOTSTRAP_RUNTIME = null, SPMSConsoleDataRuntime: CONSOLE_DATA_RUNTIME = null, SPMSAuthSessionRuntime: AUTH_SESSION_RUNTIME = null,
  SPMSAdminGoogleSheetsRuntime: ADMIN_GOOGLE_SHEETS_RUNTIME = null, SPMSAdminGoogleSheetsCacheRuntime: ADMIN_GOOGLE_SHEETS_CACHE_RUNTIME = null, SPMSAdminGoogleSheetsController: ADMIN_GOOGLE_SHEETS_CONTROLLER_RUNTIME = null, SPMSUiModeController: UI_MODE_CONTROLLER_RUNTIME = null,
  SPMSSalesRuntime: SALES_RUNTIME = null, SPMSSalesViewRuntime: SALES_VIEW_RUNTIME = null, SPMSTrackerChangeRuntime: TRACKER_CHANGE_RUNTIME = null, SPMSTrackerDiagnosticsRuntime: TRACKER_DIAGNOSTICS_RUNTIME = null,
  SPMSTrackerBoardRuntime: TRACKER_BOARD_RUNTIME = null, SPMSOrgAdminRuntime: ORG_ADMIN_RUNTIME = null, SPMSPlatformAdminAccountRuntime: PLATFORM_ADMIN_ACCOUNT_RUNTIME = null, SPMSTrackerEntryRuntime: TRACKER_ENTRY_RUNTIME = null,
} = window;
ensureProjectRelatedAppRuntimeLoaded();
const {
  SPMSSelectedEntryRuntime: SELECTED_ENTRY_RUNTIME = null, SPMSRelatedNoticeRuntime: RELATED_NOTICE_RUNTIME = null, SPMSArtifactRuntime: ARTIFACT_RUNTIME = null, SPMSProjectRuntime: PROJECT_RUNTIME = null,
  SPMSRunViewRuntime: RUN_VIEW_RUNTIME = null, SPMSRunPanelsFallbackRuntime: RUN_PANELS_FALLBACK_RUNTIME = null, SPMSReportRuntime: REPORT_RUNTIME = null, SPMSTrackerMissingReportRuntime: TRACKER_MISSING_REPORT_RUNTIME = null, SPMSAdminTabsRuntime: ADMIN_TABS_RUNTIME = null,
} = window;
let orgAdminController = null, appEventBindings = null, runtimeEnhancements = null, trackerRenderController = null, projectRelatedController = null, runPanelsController = null, reportPanelsController = null, consolePanelsController = null, authController = null, authUiController = null, uiModeController = null, salesPanelController = null, selectedEntryController = null, trackerController = null, trackerEntryActionsController = null, downloadController = null, trackerDiagnosticsPanelController = null, appBootstrapBridge = null, bootstrapCacheHelpers = null, trackerChangeEventHelpers = null, trackerRenderFallbackHelpers = null, salesPanelDepsHelpers = null, orgAdminHelpers = null, projectRelatedBodyRuntime = null, appRuntimeBodyHelpers = null;
const APP_SHELL_RUNTIME = window.SPMSAppShellRuntime || null;
if (typeof APP_SHELL_RUNTIME !== "object" || APP_SHELL_RUNTIME === null) {
  throw new Error("SPMSAppShellRuntime is required before app.js loads");
}
const { createAppState, createAppDom } = APP_SHELL_RUNTIME;
const AUTH_SESSION_REFRESH_CONTROLLER = AUTH_SESSION_RUNTIME?.createAuthSessionRefreshController ? AUTH_SESSION_RUNTIME.createAuthSessionRefreshController({ cooldownMs: AUTH_SESSION_RECHECK_COOLDOWN_MS, nowFn: () => Date.now() }) : null;
const state = createAppState();
const APP_SUPPORT_RUNTIME = window.SPMSAppSupportRuntime || null;
if (typeof APP_SUPPORT_RUNTIME !== "object" || APP_SUPPORT_RUNTIME === null) {
  throw new Error("SPMSAppSupportRuntime is required before app.js loads");
}
const APP_SUPPORT = APP_SUPPORT_RUNTIME.createAppSupportRuntime({ state, bootstrapRuntime: BOOTSTRAP_RUNTIME, windowObject: window, documentObject: document, syncUrlState, renderTrackerEntries, loadSelectedEntryDetail, flash: (...args) => flash(...args) });
const { createMethodDelegates } = APP_RUNTIME_BODY_CONTROLLER_RUNTIME;
const {
  formatAccountStatusLabel,
  formatMembershipStatusLabel,
  resolveStatusClass,
  formatDownloadScopeLabel,
  formatDownloadFormatLabel,
  formatDownloadSourcePageLabel,
  formatOrgRoleLabel,
  formatInvitationStatusLabel,
  formatContactResolutionStatusLabel,
  formatContactResolutionReasonLabel,
  isAdminRole,
  canUseAdminMode,
  canLoadProtectedConsoleData,
  getMissingReportDownloadLimit,
} = APP_SUPPORT;
let adminGoogleSheetsController = null;
function getAppRuntimeBodyHelpers() {
  if (appRuntimeBodyHelpers) return appRuntimeBodyHelpers;
  const createAppRuntimeBodyHelpers = window.SPMSAppRuntimeBodyHelpers?.createAppRuntimeBodyHelpers;
  if (typeof createAppRuntimeBodyHelpers !== "function") return null;
  appRuntimeBodyHelpers = createAppRuntimeBodyHelpers({
    state,
    dom,
    windowObject: window,
    documentObject: document,
    runTypeLabels: RUN_TYPE_LABELS,
    runViewRuntime: RUN_VIEW_RUNTIME,
    renderTrackerChangeEventsPanel,
  });
  return appRuntimeBodyHelpers;
}
function getOrgAdminHelpers() {
  if (orgAdminHelpers) return orgAdminHelpers;
  orgAdminHelpers = APP_SUPPORT.createOrgAdminHelpers({ state, dom, windowObject: window, ORG_ROLE_OPTIONS, formatOrgRoleLabel, formatMembershipStatusLabel, escapeHtml, copyInvitationUrl, loadOrganizationInvitations, getOrgAdminRuntime });
  return orgAdminHelpers;
}
function normalizePlatformAdminAccountDraft(draft) {
  return normalizePlatformAdminAccountDraftBody(draft);
}
function syncPlatformAdminAccountDraftFromForm(form) {
  return syncPlatformAdminAccountDraftFromFormBody(state, form);
}
function getAppEventBindingsDeps() {
  return window.SPMSAppControllerWiringRuntime.createAppEventBindingsDeps({ dom, state, window, document, AUTH_MODE_SIGN_IN, AUTH_MODE_SIGN_UP, TRACKER_REGION_OPTIONS, handleAuthSubmit, setAuthMode, setAdminTab, handleAuthFindId, handleAuthPasswordReset, scheduleInvitationPreviewLookup, renderAuthUi, handleAuthSignOut, openProfileDialog, handleProfileSubmit, handleInvitationSubmit, loadOrganizationAdminData, closeProfileDialog, setTrackerChangeBellPopoverOpen, downloadSalesWorkbook, closeSalesCloseDialog, formatContractAmountInput, confirmSalesCloseDialog, refreshAuthSessionState, loadDashboardSummary, handleRunCreate, handleRunFormReset, refreshSelectedRun, loadRuns, loadSelectedRunLogs, runSelectedReport, refreshReportPanels, loadSelectedRunArtifacts, cancelSelectedRun, createTrackerExportForSelectedRun, toggleUiMode, renderSyncMeta, syncUrlState, loadReportJobs, loadPhaseReport, readRunFiltersFromControls, readTrackerFiltersFromControls, syncFilterControlsFromState, changeRunsPage, loadTrackerEntries, trackerChangeEventsCacheIsFresh, renderTrackerChangeBellPopover, loadTrackerChangeEvents, focusTrackerChangePanel, uploadTrackerTemplate, resetTrackerTemplateOverride, changeEntriesPageTo, changeEntriesPage, getEntriesTotalPages, normalizeTrackerRegionFilter, parseTrackerRegionFilter, saveEntryPatch, clearEntryPatch, loadSelectedEntryAudit, loadTrackerMissingReport, refreshSalesAdminPanels, getMissingReportDownloadLimit, syncPatchValueFromSelectedEntry, closeDrawer, loadRunPresets, applySelectedPreset, saveCurrentFormAsPreset, renderRunPresetPanel, loadProjects, changeProjectsPage, triggerTrackerEntriesXlsxDownload });
}
function getAppEventBindings() {
  if (appEventBindings) return appEventBindings;
  const createAppEventBindings = window.APP_EVENT_BINDINGS?.createAppEventBindings;
  if (typeof createAppEventBindings !== "function") return null;
  appEventBindings = createAppEventBindings(getAppEventBindingsDeps());
  return appEventBindings;
}
function createControllerWithWiringDeps({
  createController,
  wiringDepsFactoryName,
  depsFactory,
  missingFactoryError,
}) {
  if (typeof createController !== "function") {
    if (missingFactoryError) throw new Error(missingFactoryError);
    return null;
  }
  const createDeps = window.SPMSAppControllerWiringRuntime?.[wiringDepsFactoryName];
  if (typeof createDeps !== "function") throw new Error("SPMSAppControllerWiringRuntime is required before app.js loads");
  return createController(createDeps(depsFactory()));
}
function getAdminGoogleSheetsController() { if (adminGoogleSheetsController) return adminGoogleSheetsController; adminGoogleSheetsController = createControllerWithWiringDeps({ createController: ADMIN_GOOGLE_SHEETS_CONTROLLER_RUNTIME?.createAdminGoogleSheetsController, wiringDepsFactoryName: "createAdminGoogleSheetsControllerDeps", depsFactory: () => APP_SUPPORT.createAdminGoogleSheetsControllerDepsHelpers({ state, dom, window, api, flash, renderAdminTopNavigation, renderAdminEmbedPanel, canLoadProtectedConsoleData, maybeResolveLegacyAdminAliasToSheetTab, getValidatedActiveAdminGoogleSheetTab, isAdminGoogleSheetTabKey, isPendingLegacyAdminAlias, shouldDeferAdminGoogleSheetPayloadLoad, clearAdminGoogleSheetPopupStateForTab, syncUrlState, applyUiMode, persistAdminGoogleSheetsCache, googleSheetsRuntime: ADMIN_GOOGLE_SHEETS_RUNTIME, defaultAdminTab: DEFAULT_ADMIN_TAB }).buildAdminGoogleSheetsControllerDeps() }); return adminGoogleSheetsController; }
function getRuntimeEnhancements() { if (runtimeEnhancements) return runtimeEnhancements; runtimeEnhancements = createControllerWithWiringDeps({ createController: window.RUNTIME_ENHANCEMENTS?.createRuntimeEnhancements, wiringDepsFactoryName: "createRuntimeEnhancementsDeps", depsFactory: () => APP_SUPPORT.createRuntimeEnhancementsDepsHelpers({ dom, document, syncCollectModeOptions, RUN_VIEW_RUNTIME, renderOrganizationAdminPanel }).buildRuntimeEnhancementsDeps() }); return runtimeEnhancements; }
function getOrgAdminController() { if (orgAdminController) return orgAdminController; orgAdminController = createControllerWithWiringDeps({ createController: window.ORG_ADMIN_CONTROLLER?.createOrgAdminController, wiringDepsFactoryName: "createOrgAdminControllerDeps", depsFactory: () => APP_SUPPORT.createOrgAdminControllerDepsHelpers({ sharedDeps: { state, dom, window, document, navigator, api, flash, setBusy }, formattingDeps: { escapeHtml, formatOrgRoleLabel, renderInvitationStatus, renderOrganizationAdminPanel, canUseAdminMode, formatDate, formatInvitationStatusLabel, formatAccountStatusLabel, formatMembershipStatusLabel, resolveStatusClass, formatDownloadScopeLabel, formatDownloadFormatLabel, formatDownloadSourcePageLabel }, actionDeps: { syncPlatformAdminAccountDraftFromForm, handlePlatformAdminAccountSubmit, renderOrgAdminRuntimeReloadFallback, canManagePlatformAdminAccounts, resetOrganizationMemberPassword, requireConsoleDataRuntime, getConsoleDataRuntimeDeps, loadSalesClaimSummaryByUser, loadClosedSalesClaims }, runtimeDeps: { membershipStatusOptions: MEMBERSHIP_STATUS_OPTIONS, platformAdminAccountRuntime: PLATFORM_ADMIN_ACCOUNT_RUNTIME, requireOrganizationAdminRuntime: getOrgAdminRuntime } }).buildOrgAdminControllerDeps() }); return orgAdminController; }
function getTrackerRenderController() { if (trackerRenderController) return trackerRenderController; trackerRenderController = createControllerWithWiringDeps({ createController: window.TRACKER_RENDER_CONTROLLER?.createTrackerRenderController, wiringDepsFactoryName: "createTrackerRenderControllerDeps", depsFactory: () => APP_SUPPORT.createTrackerRenderControllerDepsHelpers({ sharedDeps: { dom, state, escapeHtml, formatKoreanDate, formatBuildingAutomationEstimateValue, TRACKER_ENTRY_RUNTIME, flash }, selectedEntryActions: { renderSalesClaimSection, renderTrackerEntryRelatedNotices, resetTrackerBoardEdit, renderSelectedEntry, buildTrackerEntrySummaryDetail, loadSelectedEntryDetail, toggleTrackerEntryRelated, openTrackerEntryNoticeViewer, bindRelatedNoticeViewerButtons, prefetchTrackerEntryDetails }, trackerSalesActions: { claimSalesProject, setSalesNoteDraft, saveSalesClaimNote, transferSalesClaim, openSalesCloseDialog, closeSalesClaim, releaseSalesClaim, syncUrlState, getSalesClaimForProject }, trackerBoardActions: { buildTrackerBoardEmptyStateView, buildTrackerBoardMarkup, buildTrackerEntryCardMarkupFallback, getSortedTrackerBoardEntries: sortTrackerBoardEntries, TRACKER_BOARD_COLUMNS, renderTrackerBoardHeaderCell, renderTrackerBoardCell, toggleTrackerBoardBlankPriority, beginTrackerBoardEdit, saveTrackerBoardEdit } }).buildTrackerRenderControllerDeps() }); return trackerRenderController; }
function getProjectRelatedController() { if (projectRelatedController) return projectRelatedController; projectRelatedController = createControllerWithWiringDeps({ createController: window.PROJECT_RELATED_CONTROLLER?.createProjectRelatedController, wiringDepsFactoryName: "createProjectRelatedControllerDeps", depsFactory: () => APP_SUPPORT.createProjectRelatedControllerDepsHelpers({ sharedDeps: { state, window, api, flash, escapeHtml }, projectRelatedConfig: { RELATED_NOTICE_RUNTIME, PROJECT_RELATED_READY_CACHE_TTL_MS, PROJECT_RELATED_SEED_CACHE_TTL_MS, PROJECT_RELATED_STORAGE_KEY, PROJECT_RELATED_STORAGE_MAX_ITEMS }, noticeViewerRenderers: { renderNoticeViewerWindow, renderNoticeViewerPayload, renderNoticeViewerError, renderProjects, renderTrackerEntries }, projectRelatedActions: { loadProjectRelatedNotices, loadSelectedEntryDetail } }).buildProjectRelatedControllerDeps() }); return projectRelatedController; }
function getTrackerControllerBaseDeps() { return getTrackerControllerDepsHelpers().buildTrackerControllerBaseDeps(); }
function getTrackerDiagnosticsScope(runSnapshot = state.selectedRun) { return getTrackerController().getTrackerDiagnosticsScope(runSnapshot); }
function getTrackerControllerDepsHelpers() {
  if (getTrackerControllerDepsHelpers.cache) return getTrackerControllerDepsHelpers.cache;
  getTrackerControllerDepsHelpers.cache = APP_SUPPORT.createTrackerControllerDepsHelpers({ state, dom, window, api, flash, setBusy, FormData, escapeHtml, formatDate, syncUrlState, renderTrackerEntries, EDITABLE_FIELDS, TRACKER_BOARD_BLANK_PRIORITY_FIELDS, readRunFiltersFromControls, renderRuns, renderRunsPagination, renderRunDetail, renderRunEventStatus, renderLogsList, upsertRunListItem: (run) => getRunPanelsController().upsertRunListItem(run), renderEntriesPagination, renderSalesSummaryPanel, renderTrackerChangeEventsPanel, renderTrackerContactResolutionSummary, renderBackfillConflictsPanel, renderTrackerCleanupPreview, renderProjectRelatedHosts, touchSyncMeta, persistTrackerChangeEventsCache, clearTrackerChangeEventsCache, handleOutOfRangePageError, canLoadProtectedConsoleData, TRACKER_REGION_OPTIONS, useGlobalTrackerEntriesScope, shouldUseHomeBootstrapTrackerSnapshot, isProjectTrackerRun, loadTrackerEntries, schedulePolling, loadWinnerRunPanels, loadTrackerExportPanels, loadSelectedRunLogs, loadBackfillConflicts, loadVisibleSalesClaims, requireTrackerDiagnosticsRuntime: () => TRACKER_DIAGNOSTICS_RUNTIME, getTrackerController: () => getTrackerController(), formatContactResolutionStatusLabel, formatContactResolutionReasonLabel, formatBackfillConflictResolutionLabel, getTrackerDiagnosticsScope, buildTrackerChangeEventsMarkup, buildTrackerChangeBellPopoverMarkup, buildBackfillConflictsMarkup, buildBackfillConflictsView, focusTrackerChangeEntry, closeTrackerChangeModal, patchTrackerEntry, syncTrackerEntryAfterPatch, clearProjectRelatedRefresh, maybeScheduleProjectRelatedRefresh, canReuseProjectRelatedPayload, cacheProjectRelatedPayload, isProjectRelatedVisible, resolveTrackerEntryProjectId, ensureTrackerEntryProjectId, TRACKER_ENTRY_RUNTIME, TRACKER_DETAIL_PREFETCH_LIMIT, warmTrackerEntriesDownload, closeDrawer, renderTrackerBoard, resetTrackerBoardEdit, loadAdminConsoleData, buildSelectedEntryAuditMarkup, loadSelectedEntryDetail, renderTrackerMissingReport, renderSelectedEntryChangeEvents, renderSelectedEntry, renderSelectedEntryLoading, resolveTrackerPatchActorLabel, runTypeLabel });
  return getTrackerControllerDepsHelpers.cache;
}
function getTrackerController() {
  if (trackerController) return trackerController;
  trackerController = createControllerWithWiringDeps({ createController: window.TRACKER_CONTROLLER?.createTrackerController, wiringDepsFactoryName: "createTrackerControllerDeps", missingFactoryError: "Missing tracker controller runtime: window.TRACKER_CONTROLLER.createTrackerController", depsFactory: () => getTrackerControllerDepsHelpers().buildTrackerControllerDeps() });
  return trackerController;
}
function getDownloadController() { if (downloadController) return downloadController; downloadController = createControllerWithWiringDeps({ createController: window.DOWNLOAD_CONTROLLER?.createDownloadController, wiringDepsFactoryName: "createDownloadControllerDeps", missingFactoryError: "Missing download controller runtime: window.DOWNLOAD_CONTROLLER.createDownloadController", depsFactory: () => APP_SUPPORT.createDownloadControllerDepsHelpers({ state, dom, window, document, setBusy, flash, api, readTrackerFiltersFromControls, useGlobalTrackerEntriesScope, resolveActiveTrackerRunId }).buildDownloadControllerDeps() }); return downloadController; }
function getTrackerDiagnosticsPanelController() { if (trackerDiagnosticsPanelController) return trackerDiagnosticsPanelController; trackerDiagnosticsPanelController = createControllerWithWiringDeps({ createController: window.TRACKER_DIAGNOSTICS_PANEL_CONTROLLER?.createTrackerDiagnosticsPanelController, wiringDepsFactoryName: "createTrackerDiagnosticsPanelControllerDeps", missingFactoryError: "Missing tracker diagnostics panel controller runtime: window.TRACKER_DIAGNOSTICS_PANEL_CONTROLLER.createTrackerDiagnosticsPanelController", depsFactory: () => getTrackerControllerDepsHelpers().buildTrackerDiagnosticsPanelControllerDeps() }); return trackerDiagnosticsPanelController; }
function getTrackerEntryActionsController() {
  if (trackerEntryActionsController) return trackerEntryActionsController;
  trackerEntryActionsController = createControllerWithWiringDeps({ createController: window.TRACKER_ENTRY_ACTIONS_CONTROLLER?.createTrackerEntryActionsController, wiringDepsFactoryName: "createTrackerEntryActionsControllerDeps", missingFactoryError: "Missing tracker entry actions controller runtime: window.TRACKER_ENTRY_ACTIONS_CONTROLLER.createTrackerEntryActionsController", depsFactory: () => getTrackerControllerDepsHelpers().buildTrackerEntryActionsControllerDeps() });
  return trackerEntryActionsController;
}
function getSelectedEntryController() { if (selectedEntryController) return selectedEntryController; selectedEntryController = createControllerWithWiringDeps({ createController: window.SELECTED_ENTRY_CONTROLLER?.createSelectedEntryController, wiringDepsFactoryName: "createSelectedEntryControllerDeps", missingFactoryError: "Missing selected entry controller runtime: window.SELECTED_ENTRY_CONTROLLER.createSelectedEntryController", depsFactory: () => APP_SUPPORT.createSelectedEntryControllerDepsHelpers({ dom, state, buildSelectedEntryLoadingView, buildSelectedEntryEmptyView, buildSelectedEntryDisplayView, buildPatchPanelView, buildSelectedEntryChangeEventsMarkup, buildSelectedEntryMeta, buildEntryDiagnosticsMarkup, buildEntryFieldGridMarkup, buildDrawerFieldListMarkup, truncate, escapeHtml, SELECTED_ENTRY_RUNTIME, formatJson, EDITABLE_FIELDS, loadSelectedEntryAudit, loadSelectedEntryChangeEvents, openDrawer, closeDrawer, syncUrlState }).buildSelectedEntryControllerDeps() }); return selectedEntryController; }
function getRunPanelsController() { if (runPanelsController) return runPanelsController; runPanelsController = createControllerWithWiringDeps({ createController: window.RUN_PANELS_CONTROLLER?.createRunPanelsController, wiringDepsFactoryName: "createRunPanelsControllerDeps", depsFactory: () => APP_SUPPORT.createRunPanelsControllerDepsHelpers({ state, dom, window, document, RUN_VIEW_RUNTIME, api, flash, touchSyncMeta, setBusy, loadRuns, trackerController: { disconnectRunEventStream }, resetTrackerBoardEdit, syncUrlState, refreshSelectedRun, escapeHtml, runTypeLabel, statusBadge, formatDate, formatJson, progressPercent, renderRunExecutionContext, isProjectTrackerRun, useGlobalTrackerEntriesScope, renderArtifactsList, buildArtifactEmptyMessage, loadTrackerEntries }).buildRunPanelsControllerDeps() }); return runPanelsController; }
function getReportPanelsController() { if (reportPanelsController) return reportPanelsController; reportPanelsController = createControllerWithWiringDeps({ createController: window.REPORT_PANELS_CONTROLLER?.createReportPanelsController, wiringDepsFactoryName: "createReportPanelsControllerDeps", missingFactoryError: "Missing report panels controller runtime: window.REPORT_PANELS_CONTROLLER.createReportPanelsController", depsFactory: () => APP_SUPPORT.createReportPanelsControllerDepsHelpers({ state, dom, api, flash, setBusy, escapeHtml, formatDate, formatJson, formatBytes, statusBadge, ARTIFACT_RUNTIME, RELATED_NOTICE_RUNTIME, loadDashboardSummary, touchSyncMeta, syncUrlState, callRunPanelsController: callRunPanelsControllerMethod }).buildReportPanelsControllerDeps() }); return reportPanelsController; }
function getConsolePanelsController() { if (consolePanelsController) return consolePanelsController; consolePanelsController = createControllerWithWiringDeps({ createController: window.CONSOLE_PANELS_CONTROLLER?.createConsolePanelsController, wiringDepsFactoryName: "createConsolePanelsControllerDeps", missingFactoryError: "Missing console panels controller runtime: window.CONSOLE_PANELS_CONTROLLER.createConsolePanelsController", depsFactory: () => APP_SUPPORT.createConsolePanelsControllerDepsHelpers({ dom, state, escapeHtml, formatDate, runTypeLabel, statusBadge, metricCard, PROJECT_RUNTIME, RUN_VIEW_RUNTIME, renderArtifactPreviewMarkup, resolveTrackerExecutionContext, trackerExecutionTone, trackerExecutionMessage, progressPercent, trackerExportStageLabel, renderRelatedProjectNotices, bindRelatedNoticeViewerButtons, toggleProjectRelated, openProjectNoticeViewer, applyPresetParams, api, syncUrlState, syncCollectModeOptions, touchSyncMeta, flash }).buildConsolePanelsControllerDeps() }); return consolePanelsController; }
function getUiModeController() { if (uiModeController) return uiModeController; uiModeController = createControllerWithWiringDeps({ createController: UI_MODE_CONTROLLER_RUNTIME?.createUiModeController, wiringDepsFactoryName: "createUiModeControllerDeps", missingFactoryError: "Missing ui mode controller runtime: window.SPMSUiModeController.createUiModeController", depsFactory: () => APP_SUPPORT.createUiModeControllerDepsHelpers({ state, dom, window, DEFAULT_ADMIN_TAB, APP_ROOT_PATH, normalizeLocationPath, getAdminRoutePath, canUseAdminMode, canLoadProtectedConsoleData, shouldShowAdminModeToggle, shouldShowSharedGoogleSheetsShell, isPendingLegacyAdminAlias, clearAdminLegacyRouteIntent, getAdminTabByPathname, resolveUiModeFromLocation, resolveLegacyAdminRoutePath, normalizeAdminTab, clearAdminGoogleSheetPopupStateForTab, maybePreloadAdminGoogleSheetsBootstrap, syncUrlState, syncTrackerChangeBellVisibility, hydrateTrackerChangeEventsCache, renderTrackerChangeEventUnreadCount, renderTrackerChangeBellPopover, renderAdminTopNavigation, renderAdminEmbedPanel, renderTrackerTemplateStatus, loadAdminConsoleData, loadBackfillConflicts, renderBackfillConflictsPanel, closeDrawer, renderAuthUi, renderOrganizationAdminPanel, renderMySalesClaimsPanel, renderSalesSummaryPanel, renderRunDetail, renderTrackerEntries, loadOrganizationUsers, loadTrackerEntries, loadTrackerChangeEventUnreadCount, loadTrackerChangeEvents, clearUserModeRunSelection, hydrateHomeBootstrapCache, loadHomeBootstrap, scheduleTrackerChangeEventsWarmup }).buildUiModeControllerDeps() }); return uiModeController; }
function getAuthControllerBaseDeps() { return getAuthControllerDepsHelpers().buildAuthControllerBaseDeps(); }
function getAuthControllerDepsHelpers() {
  if (getAuthControllerDepsHelpers.cache) return getAuthControllerDepsHelpers.cache;
  getAuthControllerDepsHelpers.cache = APP_SUPPORT.createAuthControllerDepsHelpers({ state, dom, documentObject: document, windowObject: window, api, flash, setBusy, escapeHtml, formatOrgRoleLabel, formatInvitationStatusLabel, formatSalesDateLabel, formatMembershipStatusLabel, requireAuthSessionRuntime, loadOrganizationUsers, loadOrganizationMembers, loadSalesOverview, loadMySalesClaims, refreshSalesAdminPanels, ensureConsoleInitialized, shouldShowSignUpMode, AUTH_MODE_SIGN_IN, AUTH_MODE_SIGN_UP, syncUiModeChrome: () => getUiModeController().syncUiModeChrome(), syncUiModeFromLocation: () => syncUiModeFromLocation(), applyUiModeTransition: (adminMode, options = {}) => getUiModeController().applyUiModeTransition(adminMode, options), renderAuthUi: () => renderAuthUi(), canUseAdminMode, canLoadProtectedConsoleData, loadAdminConsoleData, loadBackfillConflicts, renderBackfillConflictsPanel, renderTrackerContactResolutionSummary, renderTrackerCleanupPreview, closeDrawer, hydrateHomeBootstrapCache, clearUserModeRunSelection, loadHomeBootstrap, loadTrackerEntries, getTrackerController: () => getTrackerController(), renderOrganizationAdminPanel, renderMySalesClaimsPanel, renderSalesSummaryPanel, renderRunDetail, renderTrackerEntries });
  return getAuthControllerDepsHelpers.cache;
}
function getAuthController() {
  if (authController) return authController;
  authController = createControllerWithWiringDeps({ createController: window.AUTH_CONTROLLER?.createAuthController, wiringDepsFactoryName: "createAuthControllerDeps", missingFactoryError: "Missing auth controller runtime: window.AUTH_CONTROLLER.createAuthController", depsFactory: () => getAuthControllerDepsHelpers().buildAuthControllerDeps() });
  return authController;
}
function getAuthUiController() {
  if (authUiController) return authUiController;
  authUiController = createControllerWithWiringDeps({ createController: window.AUTH_UI_CONTROLLER?.createAuthUiController, wiringDepsFactoryName: "createAuthUiControllerDeps", missingFactoryError: "Missing auth ui controller runtime: window.AUTH_UI_CONTROLLER.createAuthUiController", depsFactory: () => getAuthControllerDepsHelpers().buildAuthUiControllerDeps() });
  return authUiController;
}
function getSalesPanelController() {
  if (salesPanelController) return salesPanelController;
  salesPanelController = createControllerWithWiringDeps({ createController: window.SALES_PANEL_CONTROLLER?.createSalesPanelController, wiringDepsFactoryName: "createSalesPanelControllerDeps", missingFactoryError: "Missing sales panel controller runtime: window.SALES_PANEL_CONTROLLER.createSalesPanelController", depsFactory: () => getSalesPanelDepsHelpers().buildSalesPanelControllerDeps() });
  return salesPanelController;
}
const dom = createAppDom(document);
const APP_CORE_RUNTIME_FACTORY = window.createAppCoreRuntime;
if (typeof APP_CORE_RUNTIME_FACTORY !== "function") {
  throw new Error("SPMSAppCoreRuntime is required before app.js loads");
}
const APP_CORE_RUNTIME = APP_CORE_RUNTIME_FACTORY({ window, state, dom, fetch, AbortController, FormData, refreshAuthSessionState, renderAuthUi }) || null;
if (!APP_CORE_RUNTIME) throw new Error("SPMSAppCoreRuntime is required before app.js loads");
const { api, flash, setBusy, metricCard, statusBadge, progressPercent, formatJson, formatDate, formatKoreanDate, formatBytes, truncate, clampPage, escapeHtml } = APP_CORE_RUNTIME;
const ADMIN_GOOGLE_SHEETS_APP_RUNTIME = window.SPMSAppAdminGoogleSheetsRuntime?.createAppAdminGoogleSheetsRuntime ? window.SPMSAppAdminGoogleSheetsRuntime.createAppAdminGoogleSheetsRuntime({ state, dom, window, googleSheetsRuntime: ADMIN_GOOGLE_SHEETS_RUNTIME, escapeHtml, renderAdminEmbedPanel: () => renderAdminEmbedPanel(), findResolvedAdminTab: (...args) => findResolvedAdminTab(...args), getActiveAdminTab: (...args) => getActiveAdminTab(...args), getValidatedActiveAdminGoogleSheetTab: (...args) => getValidatedActiveAdminGoogleSheetTab(...args), canLoadProtectedConsoleData, shouldShowSharedGoogleSheetsShell: (...args) => shouldShowSharedGoogleSheetsShell(...args), shouldShowAdminGoogleSheetsOverviewPanel: (...args) => shouldShowAdminGoogleSheetsOverviewPanel(...args), shouldShowAdminGoogleSheetsControls: (...args) => shouldShowAdminGoogleSheetsControls(...args), loadAdminGoogleSheetsBootstrap: (...args) => loadAdminGoogleSheetsBootstrap(...args), loadAdminGoogleSheetPayload: (...args) => loadAdminGoogleSheetPayload(...args) }) : null;
const { boot, ensureConsoleInitialized, initializeConsole, shouldPollGeneralConsole, shouldPollAdminGoogleSheets, pollGeneralConsoleTick } = APP_SUPPORT.createAppStartupFacade({
  state, dom, windowObject: window, documentObject: document, authSessionHeartbeatMs: AUTH_SESSION_HEARTBEAT_MS, adminGoogleSheetsRuntime: ADMIN_GOOGLE_SHEETS_RUNTIME, canLoadProtectedConsoleData,
  isAdminGoogleSheetTabKey: (...args) => isAdminGoogleSheetTabKey(...args), isPendingLegacyAdminAlias: (...args) => isPendingLegacyAdminAlias(...args), mountRuntimeEnhancements, hydrateStateFromUrl: (...args) => hydrateStateFromUrl(...args), hydrateProjectRelatedPayloadCache: (...args) => hydrateProjectRelatedPayloadCache(...args), hydratePatchFieldOptions: (...args) => hydratePatchFieldOptions(...args), syncFilterControlsFromState, renderSyncMeta: (...args) => renderSyncMeta(...args),
  applyUiMode: (...args) => applyUiMode(...args), bindEvents, renderAuthUi, renderDashboard, renderReport, renderReportJob, importAuthSessionFromLocationHash: (...args) => importAuthSessionFromLocationHash(...args), initializeAuthGate, clearUserModeRunSelection: (...args) => clearUserModeRunSelection(...args), hydrateHomeBootstrapCache, loadHomeBootstrap: (...args) => loadHomeBootstrap(...args),
  scheduleTrackerChangeEventsWarmup, hydrateTrackerChangeEventsCache, loadRuns: (...args) => loadRuns(...args), loadOrganizationUsers: (...args) => loadOrganizationUsers(...args), loadMySalesClaims: (...args) => loadMySalesClaims(...args), loadTrackerChangeEventUnreadCount: (...args) => loadTrackerChangeEventUnreadCount(...args), loadTrackerChangeEvents: (...args) => loadTrackerChangeEvents(...args),
  loadRunPresets: (...args) => loadRunPresets(...args), loadAdminConsoleData: (...args) => loadAdminConsoleData(...args), loadBackfillConflicts: (...args) => loadBackfillConflicts(...args), refreshAuthSessionState, loadDashboardSummary: (...args) => loadDashboardSummary(...args), loadReportJobs: (...args) => loadReportJobs(...args), loadPhaseReport: (...args) => loadPhaseReport(...args), loadAdminGoogleSheetsBootstrap: (...args) => loadAdminGoogleSheetsBootstrap(...args),
});
const ADMIN_TAB_HELPERS = APP_SUPPORT.createAdminTabsHelpers({
  state, dom, windowObject: window, documentObject: document, APP_ROOT_PATH, DEFAULT_ADMIN_TAB, ADMIN_TABS, LEGACY_ADMIN_ROUTE_ALIASES, adminGoogleSheetsRuntime: ADMIN_GOOGLE_SHEETS_RUNTIME, adminGoogleSheetsAppRuntime: ADMIN_GOOGLE_SHEETS_APP_RUNTIME,
  canLoadProtectedConsoleData, syncUrlState, applyUiMode, buildResolvedAdminGoogleSheetTabs: (...args) => buildResolvedAdminGoogleSheetTabs(...args), escapeHtml, buildUrlForState, loadAdminGoogleSheetsBootstrap: (...args) => loadAdminGoogleSheetsBootstrap(...args), loadAdminGoogleSheetPayload: (...args) => loadAdminGoogleSheetPayload(...args),
  syncAdminGoogleSheets: (...args) => syncAdminGoogleSheets(...args), setTrackerChangeBellPopoverOpen: (...args) => setTrackerChangeBellPopoverOpen(...args), closeTrackerChangeModal: (...args) => closeTrackerChangeModal(...args), closeProfileDialog: (...args) => closeProfileDialog(...args),
});
const {
  normalizeAdminTab, normalizeLocationPath, resolveLegacyAdminRoutePath, getAdminTabByPathname, isAdminRoutePath, getAdminRoutePath, isProjectStatusRoutePath, resolveUiModeFromLocation, resolveStatePathname, getActiveAdminTab, isPendingLegacyAdminAlias, isAdminGoogleSheetTabKey, buildResolvedAdminGoogleSheetTabs, getResolvedAdminTabs, findResolvedAdminTab, getValidatedActiveAdminGoogleSheetTab,
  normalizeSheetTabMatchValue, scoreLegacyAliasMatch, resolveLegacyAdminGoogleSheetTabKey, maybeResolveLegacyAdminAliasToSheetTab, clearAdminLegacyRouteIntent, getAdminGoogleSheetsBootstrapSyncStatus, readAdminGoogleSheetsCacheSnapshot, hydrateAdminGoogleSheetsCacheOnFirstProtectedRender, persistAdminGoogleSheetsCache, shouldDeferAdminGoogleSheetPayloadLoad, shouldShowAdminGoogleSheetsOverviewPanel, shouldShowSharedGoogleSheetsShell, shouldShowAdminGoogleSheetsControls,
  normalizeAdminGoogleSheetsFilterState, adminGoogleSheetsFilterStateEqual, getAdminGoogleSheetsFilterState, getAdminGoogleSheetMinHeight, measureAdminGoogleSheetTableHeight, syncAdminGoogleSheetMinHeight, sanitizeAdminGoogleSheetsFilterStateForSheet, setAdminGoogleSheetsFilterState, normalizeAdminGoogleSheetPopupState, getAdminGoogleSheetPopupState, setAdminGoogleSheetPopupState, setAdminGoogleSheetPopupSearch, openAdminGoogleSheetFilterPopup, toggleAdminGoogleSheetPopupValue, setAdminGoogleSheetPopupSort, clearAdminGoogleSheetPopupState, clearAdminGoogleSheetPopupStateForTab, confirmAdminGoogleSheetPopup, cancelAdminGoogleSheetPopup,
  getAdminGoogleSheetTableInteractionSheetKey, handleAdminGoogleSheetPopupDismissal, bindAdminGoogleSheetTableInteractions, renderAdminGoogleSheetTable, renderAdminTopNavigation, renderAdminEmbedPanel, setAdminTab, loadAdminGoogleSheetsBootstrap, loadAdminGoogleSheetPayload, scheduleAdminGoogleSheetsSyncFollowup, syncAdminGoogleSheets, bindAdminGoogleSheetsActions, bindGlobalDismissalListeners,
} = APP_SUPPORT.createAdminTabsFacade({
  state, dom, windowObject: window, APP_ROOT_PATH, DEFAULT_ADMIN_TAB, adminTabsHelpers: ADMIN_TAB_HELPERS, adminTabsRuntime: ADMIN_TABS_RUNTIME, adminGoogleSheetsCacheRuntime: ADMIN_GOOGLE_SHEETS_CACHE_RUNTIME, adminGoogleSheetsAppRuntime: ADMIN_GOOGLE_SHEETS_APP_RUNTIME,
  canUseAdminMode, canLoadProtectedConsoleData, buildUrlForState, escapeHtml, applyUiMode, getAdminGoogleSheetsController, syncUrlState,
});
async function loadAdminConsoleData({ silent = false, force = false } = {}) { return getAppBootstrapBridge().loadAdminConsoleData({ silent, force }); }
async function initializeAuthGate() {
  const initialized = await getAuthController().initializeAuthGate();
  if (initialized) { syncUiModeFromLocation(); applyUiMode(); }
}
const {
  loadInvitationPreview: loadInvitationPreviewDelegate,
  loadInvitationPreviewByEmail: loadInvitationPreviewByEmailDelegate,
  scheduleInvitationPreviewLookup: scheduleInvitationPreviewLookupDelegate,
  importAuthSessionFromLocationHash: importAuthSessionFromLocationHashDelegate,
  acceptPendingInvitationToken: acceptPendingInvitationTokenDelegate,
  applyAuthSession: applyAuthSessionDelegate,
} = createMethodDelegates({
  getter: getAuthController,
  methods: ["loadInvitationPreview", "loadInvitationPreviewByEmail", "scheduleInvitationPreviewLookup", "importAuthSessionFromLocationHash", "acceptPendingInvitationToken", "applyAuthSession"],
  strict: true,
});
async function loadInvitationPreview({ silent = false } = {}) { return getAuthController().loadInvitationPreview({ silent }); }
async function loadInvitationPreviewByEmail(email, { silent = false } = {}) { return getAuthController().loadInvitationPreviewByEmail(email, { silent }); }
function scheduleInvitationPreviewLookup(email) { return getAuthController().scheduleInvitationPreviewLookup(email); }
async function importAuthSessionFromLocationHash() { return getAuthController().importAuthSessionFromLocationHash(); }
async function acceptPendingInvitationToken({ silent = false } = {}) { return getAuthController().acceptPendingInvitationToken({ silent }); }
function applyAuthSession(session) { return getAuthController().applyAuthSession(session); }
async function performAuthSessionRefresh({ silent = false } = {}) {
  const session = await getAuthController().refreshAuthSessionState({ silent });
  syncUiModeFromLocation();
  applyUiMode();
  return session;
}
function refreshAuthSessionState({ silent = false, force = false } = {}) {
  if (!AUTH_SESSION_REFRESH_CONTROLLER) return performAuthSessionRefresh({ silent });
  return AUTH_SESSION_REFRESH_CONTROLLER.run(() => performAuthSessionRefresh({ silent }), { force });
}
function shouldShowSignUpMode() { return true; }
function syncAuthFormWithInvitationPreview() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.syncAuthFormWithInvitationPreview?.();
}
function renderAuthInvitationPreview() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.renderAuthInvitationPreview?.();
}
function renderAuthUi() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.renderAuthUi?.();
}
function formatContractAmountInput(rawValue) { return formatContractAmountInputBody(rawValue); }
function formatContractAmountDisplay(rawValue, fallback = "-") { return formatContractAmountDisplayBody(rawValue, fallback); }
function openSalesCloseDialog(projectId) {
  const controller = getSalesPanelController();
  return controller.openSalesCloseDialog(projectId);
}
function closeSalesCloseDialog() {
  const controller = getSalesPanelController();
  return controller.closeSalesCloseDialog();
}
async function confirmSalesCloseDialog() {
  const controller = getSalesPanelController();
  return controller.confirmSalesCloseDialog();
}
function renderProfileStatus(message = "", level = "") {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.renderProfileStatus?.(message, level);
}
function openTrackerChangeModal() {
  return openTrackerChangeModalBody(state, dom, renderTrackerChangeEventsPanel, window);
}
function closeTrackerChangeModal() { return closeTrackerChangeModalBody(state, dom); }
function renderInvitationStatus(message = "", level = "") {
  if (!dom.invitationStatusMessage) return;
  if (message && typeof message === "object") {
    const markup = getOrgAdminRuntime()?.buildInvitationResultMarkup?.(message, { escapeHtml, formatOrgRoleLabel, formatInvitationStatusLabel }) || "";
    dom.invitationStatusMessage.innerHTML = markup;
    dom.invitationStatusMessage.classList.toggle("hidden", !markup);
    dom.invitationStatusMessage.classList.toggle("error", level === "error");
    bindInvitationCopyButtons(dom.invitationStatusMessage);
    return;
  }
  const view = requireAuthSessionRuntime().buildInvitationStatusViewModel(message, level);
  dom.invitationStatusMessage.textContent = view.text;
  dom.invitationStatusMessage.classList.toggle("hidden", !view.hasMessage);
  dom.invitationStatusMessage.classList.toggle("error", view.isError);
}
function callRunPanelsControllerMethod(methodName, fallback, ...args) {
  return APP_SUPPORT.callRunPanelsControllerFallback({ methodName, fallback, args, controller: getRunPanelsController(), state, dom, windowObject: window, RUN_PANELS_FALLBACK_RUNTIME, flash, setBusy, api, FormData, isProjectTrackerRun, dispatch(nextMethodName, nextFallback, ...nextArgs) { return callRunPanelsControllerMethod(nextMethodName, nextFallback, ...nextArgs); } });
}
const ORG_ADMIN_HELPER_DELEGATES = createMethodDelegates({
  getter: getOrgAdminHelpers,
  methods: ["mergeOrganizationInvitationItem", "upsertOrganizationInvitation", "removeOrganizationInvitation", "bindInvitationCopyButtons", "getCurrentAuthLocalUserId", "isProtectedOrganizationMember", "canInviteOrganizationAdmins", "canManagePlatformAdminAccounts", "getAllowedInvitationRoleOptions", "syncInvitationRoleOptions", "getOrganizationPlanSummaryForDisplay", "formatAuthAuditEventLabel", "formatAuthAuditActorLabel", "formatAuthAuditSummary"],
  strict: true,
});
const {
  mergeOrganizationInvitationItem,
  upsertOrganizationInvitation,
  removeOrganizationInvitation,
  bindInvitationCopyButtons,
  getCurrentAuthLocalUserId,
  isProtectedOrganizationMember,
  canInviteOrganizationAdmins,
  canManagePlatformAdminAccounts,
  getAllowedInvitationRoleOptions,
  syncInvitationRoleOptions,
  getOrganizationPlanSummaryForDisplay,
  formatAuthAuditEventLabel,
  formatAuthAuditActorLabel,
  formatAuthAuditSummary,
} = ORG_ADMIN_HELPER_DELEGATES;
function mergeOrganizationInvitations(items, existingItems = state.organizationInvitations) { return getOrgAdminHelpers().mergeOrganizationInvitations(items, existingItems); }
function scheduleOrganizationInvitationSync(delayMs = 1500) { return getOrgAdminHelpers().scheduleOrganizationInvitationSync(delayMs); }
function getRenderableOrgRoleOptions(currentRole = "") { return getOrgAdminHelpers().getRenderableOrgRoleOptions(currentRole); }
const { renderOrganizationAdminPanel: renderOrganizationAdminPanelDelegate } = createMethodDelegates({ getter: getOrgAdminController, methods: ["renderOrganizationAdminPanel"] });
function renderOrganizationAdminPanel(...args) { return renderOrganizationAdminPanelDelegate(...args); }
const { syncProfileDialogWithSession: syncProfileDialogWithSessionDelegate, openProfileDialog: openProfileDialogDelegate, closeProfileDialog: closeProfileDialogDelegate, handleProfileSubmit: handleProfileSubmitDelegate, handleAuthSubmit: handleAuthSubmitDelegate, handleAuthFindId: handleAuthFindIdDelegate, handleAuthPasswordReset: handleAuthPasswordResetDelegate, handleAuthSignOut: handleAuthSignOutDelegate } = createMethodDelegates({
  getter: getAuthUiController,
  methods: ["syncProfileDialogWithSession", "openProfileDialog", "closeProfileDialog", "handleProfileSubmit", "handleAuthSubmit", "handleAuthFindId", "handleAuthPasswordReset", "handleAuthSignOut"],
});
function syncProfileDialogWithSession() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.syncProfileDialogWithSession?.();
}
function openProfileDialog() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.openProfileDialog?.();
}
function closeProfileDialog() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.closeProfileDialog?.();
}
async function handleProfileSubmit(event) {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.handleProfileSubmit?.(event);
}
async function handleAuthSubmit(event) {
  event?.preventDefault?.();
  let controller = null;
  try {
    controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  } catch (err) {
    console.error("[auth] submit handler failed before controller dispatch", err);
    if (typeof state !== "undefined" && state?.auth) {
      state.auth.message = "로그인 화면을 초기화하지 못했습니다. 새로고침 후 다시 시도해 주세요.";
    }
    if (typeof renderAuthUi === "function") {
      renderAuthUi();
    }
    return;
  }
  return controller?.handleAuthSubmit?.(event);
}
function handleAuthFindId() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.handleAuthFindId?.();
}
async function handleAuthPasswordReset() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.handleAuthPasswordReset?.();
}
async function handleAuthSignOut() {
  const controller = typeof getAuthUiController === "function" ? getAuthUiController() : null;
  return controller?.handleAuthSignOut?.();
}
function extractDownloadFilename(response, fallbackName) { return getDownloadController().extractDownloadFilename(response, fallbackName); }
function ensureDownloadProgressOverlay() { return getDownloadController().ensureDownloadProgressOverlay(); }
function showDownloadProgressOverlay(lines, title) { return getDownloadController().showDownloadProgressOverlay(lines, title); }
function updateDownloadProgressOverlay(message) { return getDownloadController().updateDownloadProgressOverlay(message); }
function hideDownloadProgressOverlay() { return getDownloadController().hideDownloadProgressOverlay(); }
function triggerFileDownload(url, options = {}) { return getDownloadController().triggerFileDownload(url, options); }
function downloadSalesWorkbook(target, button) { return getDownloadController().downloadSalesWorkbook(target, button); }
function setAuthMode(mode) { return getAuthController().setAuthMode(mode); }
function bindEvents() {
  bindShellRuntimeEvents();
  bindAuthSubmitFallback();
  const bindings = getAppEventBindings();
  if (!bindings?.bindEvents) return;
  return bindings.bindEvents();
}
function bindAuthSubmitFallback() {
  const authForm = typeof dom !== "undefined" ? dom.authForm : null;
  if (bindAuthSubmitFallback.bound || !authForm?.addEventListener) return;
  bindAuthSubmitFallback.bound = true;
  authForm.addEventListener("submit", handleAuthSubmit);
}
function bindShellRuntimeEvents() {
  if (bindShellRuntimeEvents.bound || typeof window === "undefined") return;
  bindShellRuntimeEvents.bound = true;
  window.addEventListener("popstate", () => { hydrateStateFromUrl(); syncUiModeFromLocation(); maybeResolveLegacyAdminAliasToSheetTab({ historyMode: "replace" }); applyUiMode(); });
  if (dom.trackerChangeBell) dom.trackerChangeBell.addEventListener("click", () => { openTrackerChangeModal(); });
}
function mountRuntimeEnhancements() { const enhancements = getRuntimeEnhancements(); return enhancements?.mountRuntimeEnhancements ? enhancements.mountRuntimeEnhancements() : undefined; }
function runTypeLabel(runType) { return runTypeLabelBody(runType, RUN_TYPE_LABELS, RUN_VIEW_RUNTIME); }
function isProjectTrackerRun(runType) { return isProjectTrackerRunBody(runType); }
function mountParityReportEnhancements() { return mountParityReportEnhancementsBody(dom, document); }
function handleRunFormReset() {
  const controller = getRunPanelsController();
  if (controller?.handleRunFormReset) {
    return controller.handleRunFormReset();
  }
  return RUN_PANELS_FALLBACK_RUNTIME?.handleRunFormResetFallback?.({ dom });
}
function buildRunPayload({ collectModeOverride = "" } = {}) {
  const controller = getRunPanelsController();
  if (controller?.buildRunPayload) {
    return controller.buildRunPayload({ collectModeOverride });
  }
  return RUN_PANELS_FALLBACK_RUNTIME?.buildRunPayloadFallback?.(
    { collectModeOverride },
    {
      dom,
      FormData,
      normalizeCollectMode,
    },
  ) || null;
}
async function createWinnerRun({ collectModeOverride = "", submitButton = null, busyLabel = "" } = {}) {
  const controller = getRunPanelsController();
  if (controller?.createWinnerRun) {
    return controller.createWinnerRun({ collectModeOverride, submitButton, busyLabel });
  }
  return RUN_PANELS_FALLBACK_RUNTIME?.createWinnerRunFallback?.(
    { collectModeOverride, submitButton, busyLabel },
    {
      dom,
      state,
      api,
      flash,
      setBusy,
      syncUrlState,
      loadRuns,
      selectRun,
      buildRunPayload,
    },
  );
}
const FRONTEND_RUNTIME_ADAPTERS = APP_SUPPORT.createFrontendRuntimeAdapters({ SALES_RUNTIME, TRACKER_CHANGE_RUNTIME, TRACKER_DIAGNOSTICS_RUNTIME, TRACKER_ENTRY_RUNTIME, SELECTED_ENTRY_RUNTIME, SALES_VIEW_RUNTIME, TRACKER_CHANGE_FIELD_LABELS, EDITABLE_FIELDS, escapeHtml, formatDate, formatKoreanDate, formatContractAmountDisplay, truncate, getTrackerProjectSnapshot: (...args) => getTrackerProjectSnapshot(...args), sortTrackerBoardEntriesFallback });
const { salesClaimStatusLabel, getSalesNoteEntries, parseSalesDateValue, getSalesDateParts, formatSalesDateLabel, formatSalesNoteTimestamp, serializeSalesNoteEntry, parseSalesNoteEntry, getSalesNoteTimeline, getLatestSalesNoteEntry, getLatestSalesNoteItem, extractContractAmountTextFromSalesNote, formatSalesNoteTextForDisplay, removeLatestSalesNoteEntry, getTrackerChangeFieldLabel, formatTrackerChangeEventLabel, buildTrackerChangeEventDescription, formatBackfillConflictResolutionLabel, buildBackfillConflictDescription, buildTrackerChangeEventsMarkup, buildTrackerChangeBellPopoverMarkup, buildBackfillConflictsMarkup, buildBackfillConflictsView, buildSelectedEntryChangeEventsMarkup, toTrackerEntrySummary, buildTrackerEntrySummaryDetail, buildTrackerEntriesEmptyStateView, buildTrackerEntryCardView, buildTrackerEntriesListMarkup, buildTrackerBoardEmptyStateView, buildSortedTrackerBoardEntries, buildTrackerBoardMarkup, formatEokValue, parseTrackerCostToWon, formatBuildingAutomationEstimateValue, buildSelectedEntryLoadingView, buildSelectedEntryEmptyView, buildPatchPanelView, buildSelectedEntryDisplayView, buildSelectedEntryMeta, buildEntryDiagnosticsMarkup, buildEntryFieldGridMarkup, buildDrawerFieldListMarkup, buildUserSalesProjectFactsMarkup, buildSalesNoteTimelineMarkup, buildSalesClaimEstimateLabel, buildUserOwnedSalesClaimCardMarkup, buildCompanySalesClaimCardMarkup, buildUserTrackerClaimSectionMarkup, buildSelectedEntryAuditMarkup } = FRONTEND_RUNTIME_ADAPTERS;
function readConsoleCacheEnvelope(storageKey, { allowStale = false } = {}) { return getBootstrapCacheHelpers().readConsoleCacheEnvelope(storageKey, { allowStale }); }
function writeConsoleCacheEnvelope(storageKey, payload) { return getBootstrapCacheHelpers().writeConsoleCacheEnvelope(storageKey, payload); }
const {
  normalizeSalesOverviewPayload,
  buildSalesOverviewCachePayload,
  mergeSalesOverviewIntoHomeBootstrapPayload,
  buildHomeBootstrapCachePayload,
  hasCachedSalesOverviewData,
  hasCachedHomeBootstrapData,
  isMissingSalesOverviewEndpointError,
  isMissingHomeBootstrapEndpointError,
} = APP_SUPPORT;
const buildOrganizationAdminBootstrapCachePayload = (payload) => (
  getBootstrapCacheHelpers().buildOrganizationAdminBootstrapCachePayload(payload)
);
function readOrganizationAdminBootstrapCache() { return getBootstrapCacheHelpers().readOrganizationAdminBootstrapCache(); }
function persistOrganizationAdminBootstrapCache(payload) { return getBootstrapCacheHelpers().persistOrganizationAdminBootstrapCache(payload); }
function getConsoleDataRuntimeDeps() { return getBootstrapRuntimeDepsHelpers().buildConsoleDataRuntimeDeps(); }
function requireConsoleDataRuntime() {
  if (!CONSOLE_DATA_RUNTIME) throw new Error("SPMSConsoleDataRuntime is not available.");
  return CONSOLE_DATA_RUNTIME;
}
async function loadHomeBootstrap({ silent = false, force = false } = {}) {
  return requireConsoleDataRuntime().loadHomeBootstrap(getConsoleDataRuntimeDeps(), { silent, force });
}
async function loadSalesOverview({ silent = false, force = false } = {}) {
  return requireConsoleDataRuntime().loadSalesOverview(getConsoleDataRuntimeDeps(), { silent, force });
}
function requireAuthSessionRuntime() {
  if (!AUTH_SESSION_RUNTIME) throw new Error("SPMSAuthSessionRuntime is not available.");
  return AUTH_SESSION_RUNTIME;
}
function shouldShowAdminModeToggle() {
  if (AUTH_SESSION_RUNTIME?.shouldShowAdminModeToggle) {
    return AUTH_SESSION_RUNTIME.shouldShowAdminModeToggle(state.auth);
  }
  return canUseAdminMode();
}
function getOrgAdminRuntime() { return window.SPMSOrgAdminRuntime || ORG_ADMIN_RUNTIME || null; }
function renderOrgAdminRuntimeReloadFallback(target) {
  if (!target) {
    return;
  }
  target.innerHTML = '<div class="empty-state">愿由ъ옄 ?붾㈃ 由ъ냼?ㅺ? 理쒖떊 ?곹깭媛 ?꾨떃?덈떎. ?덈줈怨좎묠 ???ㅼ떆 ?뺤씤?섏꽭??</div>';
}
function applySalesOverviewPayload(payload) {
  const { companyItems, myItems, organizationUsers } = normalizeSalesOverviewPayload(payload); state.companySalesClaims = companyItems; state.mySalesClaims = myItems; state.organizationUsers = organizationUsers; state.organizationUsersError = ""; state.salesClaimsByProjectId = {}; mergeActiveSalesClaims(companyItems);
}
function shouldApplyHomeBootstrapTrackerSnapshot() {
  return BOOTSTRAP_RUNTIME?.canUseHomeBootstrapTrackerSnapshot({ uiMode: state.uiMode, globalScope: useGlobalTrackerEntriesScope(), snapshotActive: true, query: state.trackerFilters.q, region: state.trackerFilters.region, editedOnly: state.trackerFilters.editedOnly, page: state.trackerFilters.page }) || (state.uiMode === "user" && useGlobalTrackerEntriesScope() && !String(state.trackerFilters.q || "").trim() && !String(state.trackerFilters.region || "").trim() && !state.trackerFilters.editedOnly && Number(state.trackerFilters.page || 1) === 1);
}
function applyHomeBootstrapPayload(payload) { return BOOTSTRAP_RUNTIME?.applyHomeBootstrapPayload?.(getHomeBootstrapRuntimeDeps(), payload || {}); }
function hydrateHomeBootstrapCache() { return BOOTSTRAP_RUNTIME?.hydrateHomeBootstrapCache?.(getHomeBootstrapRuntimeDeps()) || false; }
function persistSalesOverviewCache(payload) { return BOOTSTRAP_RUNTIME?.persistSalesOverviewCache?.(getHomeBootstrapRuntimeDeps(), payload); }
function syncHomeBootstrapSalesCache(payload) { return BOOTSTRAP_RUNTIME?.syncHomeBootstrapSalesCache?.(getHomeBootstrapRuntimeDeps(), payload); }
function persistHomeBootstrapCache(payload) { return BOOTSTRAP_RUNTIME?.persistHomeBootstrapCache?.(getHomeBootstrapRuntimeDeps(), payload); }
function shouldUseHomeBootstrapTrackerSnapshot() { return BOOTSTRAP_RUNTIME?.shouldUseHomeBootstrapTrackerSnapshot?.(getHomeBootstrapRuntimeDeps()) || false; }
function getBootstrapRuntimeDepsHelpers() {
  if (!getBootstrapRuntimeDepsHelpers.cache) {
    const shellRuntime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" && APP_RUNTIME_BODY_SHELL_RUNTIME
      ? APP_RUNTIME_BODY_SHELL_RUNTIME
      : {
          createBootstrapSalesStateHelpers({
            salesStateHelpers,
            getVisibleSalesProjectIds,
            getSalesClaimForProject,
            getTrackerProjectSnapshot,
            renderUserSalesProjectFacts,
            isCurrentUserClaimOwner,
            canCurrentUserForceRelease,
            canCurrentUserManageClaim,
            isActiveSalesClaim,
            getOrganizationTransferTargets,
            getSalesNoteDraft,
            setSalesNoteDraft,
            upsertSalesClaim,
            replaceVisibleSalesClaims,
            mergeActiveSalesClaims,
            formatShortDateTime,
            formatEstimatedAmountRangeFromKrw,
          } = {}) {
            if (typeof salesStateHelpers !== "undefined" && salesStateHelpers) return salesStateHelpers;
            return {
              getVisibleSalesProjectIds: typeof getVisibleSalesProjectIds === "function" ? getVisibleSalesProjectIds : () => [],
              getSalesClaimForProject: typeof getSalesClaimForProject === "function" ? getSalesClaimForProject : () => null,
              getTrackerProjectSnapshot: typeof getTrackerProjectSnapshot === "function" ? getTrackerProjectSnapshot : () => null,
              renderUserSalesProjectFacts: typeof renderUserSalesProjectFacts === "function" ? renderUserSalesProjectFacts : () => "",
              isCurrentUserClaimOwner: typeof isCurrentUserClaimOwner === "function" ? isCurrentUserClaimOwner : () => true,
              canCurrentUserForceRelease: typeof canCurrentUserForceRelease === "function" ? canCurrentUserForceRelease : () => false,
              canCurrentUserManageClaim: typeof canCurrentUserManageClaim === "function" ? canCurrentUserManageClaim : () => false,
              isActiveSalesClaim: typeof isActiveSalesClaim === "function" ? isActiveSalesClaim : () => false,
              getOrganizationTransferTargets: typeof getOrganizationTransferTargets === "function" ? getOrganizationTransferTargets : () => [],
              getSalesNoteDraft: typeof getSalesNoteDraft === "function" ? getSalesNoteDraft : () => "",
              setSalesNoteDraft: typeof setSalesNoteDraft === "function" ? setSalesNoteDraft : () => {},
              upsertSalesClaim: typeof upsertSalesClaim === "function" ? upsertSalesClaim : () => {},
              replaceVisibleSalesClaims: typeof replaceVisibleSalesClaims === "function" ? replaceVisibleSalesClaims : () => {},
              mergeActiveSalesClaims: typeof mergeActiveSalesClaims === "function" ? mergeActiveSalesClaims : () => {},
              formatShortDateTime: typeof formatShortDateTime === "function" ? formatShortDateTime : () => "",
              formatEstimatedAmountRangeFromKrw: typeof formatEstimatedAmountRangeFromKrw === "function" ? formatEstimatedAmountRangeFromKrw : () => "",
            };
          },
        };
    getBootstrapRuntimeDepsHelpers.cache = APP_SUPPORT.createBootstrapRuntimeDepsHelpers({
      state,
      dom,
      api,
      flash,
      salesStateHelpers: shellRuntime.createBootstrapSalesStateHelpers({
        salesStateHelpers: typeof SALES_STATE_HELPERS === "undefined" ? undefined : SALES_STATE_HELPERS,
        getVisibleSalesProjectIds: typeof getVisibleSalesProjectIds === "function" ? getVisibleSalesProjectIds : undefined,
        getSalesClaimForProject: typeof getSalesClaimForProject === "function" ? getSalesClaimForProject : undefined,
        getTrackerProjectSnapshot: typeof getTrackerProjectSnapshot === "function" ? getTrackerProjectSnapshot : undefined,
        renderUserSalesProjectFacts: typeof renderUserSalesProjectFacts === "function" ? renderUserSalesProjectFacts : undefined,
        isCurrentUserClaimOwner: typeof isCurrentUserClaimOwner === "function" ? isCurrentUserClaimOwner : undefined,
        canCurrentUserForceRelease: typeof canCurrentUserForceRelease === "function" ? canCurrentUserForceRelease : undefined,
        canCurrentUserManageClaim: typeof canCurrentUserManageClaim === "function" ? canCurrentUserManageClaim : undefined,
        isActiveSalesClaim: typeof isActiveSalesClaim === "function" ? isActiveSalesClaim : undefined,
        getOrganizationTransferTargets: typeof getOrganizationTransferTargets === "function" ? getOrganizationTransferTargets : undefined,
        getSalesNoteDraft: typeof getSalesNoteDraft === "function" ? getSalesNoteDraft : undefined,
        setSalesNoteDraft: typeof setSalesNoteDraft === "function" ? setSalesNoteDraft : undefined,
        upsertSalesClaim: typeof upsertSalesClaim === "function" ? upsertSalesClaim : undefined,
        replaceVisibleSalesClaims: typeof replaceVisibleSalesClaims === "function" ? replaceVisibleSalesClaims : undefined,
        mergeActiveSalesClaims: typeof mergeActiveSalesClaims === "function" ? mergeActiveSalesClaims : undefined,
        formatShortDateTime: typeof formatShortDateTime === "function" ? formatShortDateTime : undefined,
        formatEstimatedAmountRangeFromKrw: typeof formatEstimatedAmountRangeFromKrw === "function" ? formatEstimatedAmountRangeFromKrw : undefined,
      }),
      bootstrapSupport: APP_SUPPORT,
      canUseAdminMode,
      mergeOrganizationInvitations,
      loadTrackerEntries,
      renderMySalesClaimsPanel,
      renderTrackerEntries,
      renderSalesSummaryPanel,
      renderOrganizationAdminPanel,
      applyHomeBootstrapPayload,
      applySalesOverviewPayload,
      persistHomeBootstrapCache,
      persistSalesOverviewCache,
      resetTrackerBoardEdit,
      renderEntriesPagination,
      syncUrlState,
      useGlobalTrackerEntriesScope,
      salesOverviewStorageKey: SALES_OVERVIEW_STORAGE_KEY,
      homeBootstrapStorageKey: HOME_BOOTSTRAP_STORAGE_KEY,
      readConsoleCacheEnvelope,
      writeConsoleCacheEnvelope,
    });
  }
  return getBootstrapRuntimeDepsHelpers.cache;
}
function getHomeBootstrapRuntimeDeps() { return getBootstrapRuntimeDepsHelpers().buildHomeBootstrapRuntimeDeps(); }
async function handleInvitationSubmit(event) { return handleInvitationSubmitDelegate(event); }
function buildUrlForState({ pathname = null, uiMode = state.uiMode, adminTab = state.adminTab, persist = false } = {}) {
  const runtime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" ? APP_RUNTIME_BODY_SHELL_RUNTIME : null;
  if (runtime?.buildUrlForState) {
    return runtime.buildUrlForState({
      state,
      pathname,
      uiMode,
      adminTab,
      defaultAdminTab: DEFAULT_ADMIN_TAB,
      locationPathname: window.location.pathname,
      resolveStatePathname,
    });
  }
  const params = new URLSearchParams();
  if (state.runFilters.status) params.set("run_status", state.runFilters.status);
  if (state.runFilters.runType) params.set("run_type", state.runFilters.runType);
  if (state.runFilters.from) params.set("run_from", state.runFilters.from);
  if (state.runFilters.to) params.set("run_to", state.runFilters.to);
  if (state.runFilters.page !== 1) params.set("run_page", String(state.runFilters.page));
  if (state.runFilters.pageSize !== 20) params.set("run_page_size", String(state.runFilters.pageSize));
  if (state.selectedRunId) params.set("run_id", state.selectedRunId);
  if (state.selectedTrackerRunId) params.set("tracker_run_id", state.selectedTrackerRunId);
  if (state.trackerFilters.q) params.set("tracker_q", state.trackerFilters.q);
  if (state.trackerFilters.region) params.set("tracker_region", state.trackerFilters.region);
  if (state.trackerFilters.noticeYear) params.set("tracker_notice_year", state.trackerFilters.noticeYear);
  if (state.trackerFilters.editedOnly) params.set("tracker_edited", "1");
  if (state.trackerFilters.page !== 1) params.set("tracker_page", String(state.trackerFilters.page));
  if (state.trackerFilters.pageSize !== 20) params.set("tracker_page_size", String(state.trackerFilters.pageSize));
  if (!state.autoRefresh) params.set("auto_refresh", "0");
  if (state.reportKey && state.reportKey !== "phase1-artifact-diff") params.set("report_key", state.reportKey);
  if (state.selectedReportJobId) params.set("report_job_id", state.selectedReportJobId);
  if (uiMode === "admin") params.set("mode", "admin");
  if (adminTab && adminTab !== DEFAULT_ADMIN_TAB) params.set("admin_tab", adminTab);
  if (persist) try {
    const next = params.toString();
    if (next) window.sessionStorage?.setItem?.("notice-winner-pipeline-web.canonicalUrlState.v1", next);
    else window.sessionStorage?.removeItem?.("notice-winner-pipeline-web.canonicalUrlState.v1");
  } catch (_error) {}
  return "/";
}
function syncUrlState() {
  const runtime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" ? APP_RUNTIME_BODY_SHELL_RUNTIME : null;
  if (runtime?.syncUrlState) {
    return runtime.syncUrlState({
      state,
      windowObject: window,
      buildUrlForStateFn: buildUrlForState,
    }, arguments[0] || {});
  }
  const { historyMode = "replace", pathname = null, uiMode = state.uiMode, adminTab = state.adminTab } = arguments[0] || {};
  const nextUrl = buildUrlForState({ pathname, uiMode, adminTab, persist: true });
  if (historyMode === "push") {
    window.history.pushState({}, "", nextUrl);
    return;
  }
  window.history.replaceState({}, "", nextUrl);
}
function openDrawer() {
  const runtime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" ? APP_RUNTIME_BODY_SHELL_RUNTIME : null;
  if (runtime?.openDrawer) return runtime.openDrawer({ state, dom });
  state.drawerOpen = true;
  dom.entryDrawer.classList.remove("hidden");
  dom.entryDrawer.setAttribute("aria-hidden", "false");
}
function closeDrawer() {
  const runtime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" ? APP_RUNTIME_BODY_SHELL_RUNTIME : null;
  if (runtime?.closeDrawer) return runtime.closeDrawer({ state, dom });
  state.drawerOpen = false;
  dom.entryDrawer.classList.add("hidden");
  dom.entryDrawer.setAttribute("aria-hidden", "true");
}
function syncFilterControlsFromState() {
  const runtime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" ? APP_RUNTIME_BODY_SHELL_RUNTIME : null;
  if (runtime?.syncFilterControlsFromState) {
    return runtime.syncFilterControlsFromState({ state, dom, renderTrackerRegionButtons });
  }
  dom.runFilterStatus.value = state.runFilters.status;
  dom.runFilterType.value = state.runFilters.runType;
  dom.runFilterFrom.value = state.runFilters.from;
  dom.runFilterTo.value = state.runFilters.to;
  dom.runPageSize.value = String(state.runFilters.pageSize);
  dom.trackerQuery.value = state.trackerFilters.q;
  renderTrackerRegionButtons();
  dom.trackerPageSize.value = String(state.trackerFilters.pageSize);
  dom.reportSelect.value = state.reportKey;
}
function readRunFiltersFromControls() {
  const runtime = typeof APP_RUNTIME_BODY_SHELL_RUNTIME !== "undefined" ? APP_RUNTIME_BODY_SHELL_RUNTIME : null;
  if (runtime?.readRunFiltersFromControls) return runtime.readRunFiltersFromControls({ state, dom });
  state.runFilters.status = dom.runFilterStatus.value;
  state.runFilters.runType = dom.runFilterType.value;
  state.runFilters.from = dom.runFilterFrom.value;
  state.runFilters.to = dom.runFilterTo.value;
  state.runFilters.pageSize = Number(dom.runPageSize.value || 20);
}
function readTrackerFiltersFromControls() { return getTrackerController().readTrackerFiltersFromControls(); }
function parseTrackerRegionFilter(region) { return getTrackerController().parseTrackerRegionFilter(region); }
function normalizeTrackerRegionFilter(region) { return getTrackerController().normalizeTrackerRegionFilter(region); }
function renderTrackerRegionButtons() { return getTrackerController().renderTrackerRegionButtons(); }
async function loadDashboardSummary({ silent = false } = {}) {
  const controller = getConsolePanelsController();
  return controller.loadDashboardSummary({ silent });
}
function renderDashboard(summary, errorMessage = "") { const controller = getConsolePanelsController(); return controller.renderDashboard(summary, errorMessage); }
async function handleRunCreate(event) {
  event.preventDefault();
  await createWinnerRun({ submitButton: dom.submitRunButton, busyLabel: "실행 시작 중..." });
}
async function loadRuns({ initial = false, silent = false, preservePage = false } = {}) { return getTrackerController().loadRuns({ initial, silent, preservePage }); }
async function refreshSelectedRun({ silent = false } = {}) { return getTrackerController().refreshSelectedRun({ silent }); }
function renderRunDetail(run) { return getRunPanelsController().renderRunDetail(run); }
function disconnectRunEventStream() { return getTrackerController().disconnectRunEventStream(); }
function connectRunEventStream(runId) { return getTrackerController().connectRunEventStream(runId); }
async function loadRunPresets({ silent = false } = {}) { return getRunPanelsController().loadRunPresets({ silent }); }
function renderRunPresetPanel(errorMessage = "") { return renderRunPresetPanelDelegate(errorMessage); }
async function applySelectedPreset() { return applySelectedPresetDelegate(); }
async function saveCurrentFormAsPreset() { return saveCurrentFormAsPresetDelegate(); }
function syncTrackerChangeBellVisibility(adminMode = state.uiMode === "admin") {
  dom.trackerChangeBellShell?.classList.toggle("hidden", !adminMode);
  if (!adminMode) {
    setTrackerChangeBellPopoverOpen(false);
  }
}
function readTrackerChangeEventsCache() { return getTrackerChangeEventHelpers().readTrackerChangeEventsCache(); }
function persistTrackerChangeEventsCache() { return getTrackerChangeEventHelpers().persistTrackerChangeEventsCache(); }
function clearTrackerChangeEventsCache() { return getTrackerChangeEventHelpers().clearTrackerChangeEventsCache(); }
function hydrateTrackerChangeEventsCache() { return getTrackerChangeEventHelpers().hydrateTrackerChangeEventsCache(); }
function trackerChangeEventsCacheIsFresh() { return getTrackerChangeEventHelpers().trackerChangeEventsCacheIsFresh(); }
function scheduleTrackerChangeEventsWarmup() { return getTrackerChangeEventHelpers().scheduleTrackerChangeEventsWarmup(); }
function applyUiMode({ renderAuth = true } = {}) {
  const controller = getUiModeController();
  return controller.applyUiMode({ renderAuth });
}
function toggleUiMode() { return getUiModeController().toggleUiMode(); }
function syncUiModeFromLocation() { return getUiModeController().syncUiModeFromLocation(); }
function useGlobalTrackerEntriesScope() { return useGlobalTrackerEntriesScopeBody(); }
function clearUserModeRunSelection({ sync = false } = {}) {
  if (state.uiMode !== "user" || !useGlobalTrackerEntriesScope()) return clearUserModeRunSelectionAccessor?.({ sync });
  const hadRunContext = Boolean(
    state.selectedRunId ||
      state.selectedTrackerRunId ||
      state.selectedRun ||
      state.selectedTrackerRun ||
      state.selectedTrackerWorkbookArtifactId,
  );
  state.selectedRunId = null;
  state.selectedRun = null;
  state.selectedTrackerRunId = null;
  state.selectedTrackerRun = null;
  state.selectedTrackerWorkbookArtifactId = null;
  if (hadRunContext && sync) syncUrlState();
}
const {
  renderRuns,
  renderRunsPagination,
  changeRunsPage,
  selectRun,
  refreshSelectedRun: refreshSelectedRunDelegate,
  renderRunDetail: renderRunDetailDelegate,
  renderRunExecutionContext: renderRunExecutionContextDelegate,
  resolveTrackerExecutionContext: resolveTrackerExecutionContextDelegate,
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
  disconnectRunEventStream: disconnectRunEventStreamDelegate,
  connectRunEventStream: connectRunEventStreamDelegate,
  loadRunPresets: loadRunPresetsDelegate,
  renderRunPresetPanel: renderRunPresetPanelDelegate,
  applyPresetParams,
  applySelectedPreset: applySelectedPresetDelegate,
  saveCurrentFormAsPreset: saveCurrentFormAsPresetDelegate,
  loadProjects: loadProjectsDelegate,
  renderProjects: renderProjectsDelegate,
  renderRelatedProjectNotices: renderRelatedProjectNoticesDelegate,
  renderTrackerEntryRelatedNotices: renderTrackerEntryRelatedNoticesDelegate,
  renderRelatedNoticePanel: renderRelatedNoticePanelDelegate,
  bindRelatedNoticeViewerButtons: bindRelatedNoticeViewerButtonsDelegate,
  openRelatedNoticeViewer: openRelatedNoticeViewerDelegate,
  openProjectNoticeViewer: openProjectNoticeViewerDelegate,
  buildProjectNoticeUrl: buildProjectNoticeUrlDelegate,
  extractTrackerEntryBidParts: extractTrackerEntryBidPartsDelegate,
  buildTrackerEntryNoticeUrl: buildTrackerEntryNoticeUrlDelegate,
  openTrackerEntryNoticeViewer: openTrackerEntryNoticeViewerDelegate,
  renderNoticeViewerPayload: renderNoticeViewerPayloadDelegate,
  renderNoticeViewerError: renderNoticeViewerErrorDelegate,
  renderNoticeViewerWindow: renderNoticeViewerWindowDelegate,
  formatNoticeViewerSourceLabel: formatNoticeViewerSourceLabelDelegate,
  cancelSelectedRun,
  createTrackerExportForSelectedRun,
} = APP_RUNTIME_BODY_CONSOLE_RUNTIME.createAppRuntimeBodyConsoleDelegates({
  state,
  windowObject: window,
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
  getProjectRelatedBodyRuntime: (...args) => getProjectRelatedBodyRuntime(...args),
  getTrackerController,
  loadRuns,
});
function renderRunExecutionContext(run) {
  const controller = typeof getConsolePanelsController === "function" ? getConsolePanelsController() : null;
  return controller?.renderRunExecutionContext?.(run);
}
async function openRelatedNoticeViewer(item) {
  const controller = typeof getProjectRelatedController === "function" ? getProjectRelatedController() : null;
  return controller?.openRelatedNoticeViewer?.(item);
}
async function openProjectNoticeViewer(project) {
  const controller = typeof getProjectRelatedController === "function" ? getProjectRelatedController() : null;
  return controller?.openProjectNoticeViewer?.(project);
}
function buildProjectNoticeUrl(project) { return buildProjectNoticeUrlDelegate(project); }
function extractTrackerEntryBidParts(entry) { return extractTrackerEntryBidPartsDelegate(entry); }
function buildTrackerEntryNoticeUrl(entry) { return buildTrackerEntryNoticeUrlDelegate(entry); }
async function openTrackerEntryNoticeViewer(entryId, entries = state.trackerEntries) {
  const controller = typeof getProjectRelatedController === "function" ? getProjectRelatedController() : null;
  return controller?.openTrackerEntryNoticeViewer?.(entryId, entries);
}
function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = "공고문") {
  const controller = typeof getReportPanelsController === "function" ? getReportPanelsController() : null;
  if (controller?.renderNoticeViewerPayload) return controller.renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle);
  if (!viewerWindow?.document || !RELATED_NOTICE_RUNTIME) return undefined;
  const title = String(payload?.title || fallbackTitle || "공고문");
  const meta = [payload?.project_name, payload?.bid_no, payload?.bid_ord ? `${payload.bid_ord}차` : "", payload?.document_count ? `문서 ${payload.document_count}건` : ""].filter(Boolean).join(" · ");
  const body = RELATED_NOTICE_RUNTIME.buildNoticeViewerDocumentsMarkup?.(payload?.documents || payload?.items || []) || "";
  return renderNoticeViewerWindow(viewerWindow, { title, meta, body });
}
function renderNoticeViewerError(viewerWindow, { title = "오류", errorMessage = "", links = [] } = {}) {
  const controller = typeof getReportPanelsController === "function" ? getReportPanelsController() : null;
  if (controller?.renderNoticeViewerError) return controller.renderNoticeViewerError(viewerWindow, { title, errorMessage, links });
  const body = [`<p>${escapeHtml(errorMessage || "알 수 없는 오류가 발생했습니다.")}</p>`]
    .concat((Array.isArray(links) ? links : []).map((link) => `<p><a href="${escapeHtml(link?.href || "#")}" target="_blank" rel="noreferrer">${escapeHtml(link?.label || link?.href || "")}</a></p>`))
    .join("");
  return renderNoticeViewerWindow(viewerWindow, { title, meta: "", body });
}
function renderNoticeViewerWindow(targetWindow, { title = "공고문", meta = "", body = "" } = {}) {
  const controller = typeof getReportPanelsController === "function" ? getReportPanelsController() : null;
  if (controller?.renderNoticeViewerWindow) return controller.renderNoticeViewerWindow(targetWindow, { title, meta, body });
  if (!targetWindow?.document || !RELATED_NOTICE_RUNTIME) return undefined;
  targetWindow.document.open();
  targetWindow.document.write(RELATED_NOTICE_RUNTIME.buildNoticeViewerHtml({ title, meta, body }));
  targetWindow.document.close();
  return undefined;
}
function formatNoticeViewerSourceLabel(value) {
  return RELATED_NOTICE_RUNTIME?.formatNoticeViewerSourceLabel?.(value) || String(value ?? "");
}
function resolveOpenTrackerRelatedProjectId() { return resolveTrackerEntryProjectId(state.trackerRelatedEntryId); }
function isProjectRelatedVisible(projectId) { return Boolean(projectId) && (state.projectOpenId === projectId || resolveOpenTrackerRelatedProjectId() === projectId); }
async function loadProjects({ silent = false } = {}) {
  const controller = getConsolePanelsController();
  return controller.loadProjects({ silent });
}
function renderProjects(errorMessage = "") {
  const controller = getConsolePanelsController();
  return controller.renderProjects(errorMessage);
}
function renderRelatedProjectNotices(project) { return getProjectRelatedController().renderRelatedProjectNotices(project); }
function renderTrackerEntryRelatedNotices(entry) { return getProjectRelatedController().renderTrackerEntryRelatedNotices(entry); }
function renderRelatedNoticePanel(projectId) { return getProjectRelatedController().renderRelatedNoticePanel(projectId); }
function bindRelatedNoticeViewerButtons(container) { return getProjectRelatedController().bindRelatedNoticeViewerButtons(container); }
function renderProjectRelatedHosts() { return getProjectRelatedController().renderProjectRelatedHosts(); }
function clearProjectRelatedRefresh(projectId) { return getProjectRelatedController().clearProjectRelatedRefresh(projectId); }
function maybeScheduleProjectRelatedRefresh(projectId) { return getProjectRelatedController().maybeScheduleProjectRelatedRefresh(projectId); }
function canReuseProjectRelatedPayload(payload) { return getProjectRelatedController().canReuseProjectRelatedPayload(payload); }
function cacheProjectRelatedPayload(projectId, payload) { return getProjectRelatedController().cacheProjectRelatedPayload(projectId, payload); }
async function ensureTrackerEntryProjectId(entryId) { return getProjectRelatedController().ensureTrackerEntryProjectId(entryId); }
function prefetchProjectRelatedNotices(projectIds) { return getTrackerController().prefetchProjectRelatedNotices(projectIds); }
async function toggleProjectRelated(projectId) { return getTrackerController().toggleProjectRelated(projectId); }
async function toggleTrackerEntryRelated(entryId) { return getTrackerController().toggleTrackerEntryRelated(entryId); }
async function loadProjectRelatedNotices(projectId, { silent = false, force = false, prefetch = false } = {}) {
  return getTrackerController().loadProjectRelatedNotices(projectId, { silent, force, prefetch });
}
function prefetchVisibleProjectRelatedNotices(entries) { prefetchProjectRelatedNotices(entries.map((entry) => entry?.project_id || "")); }
function changeProjectsPage(delta) {
  return APP_SUPPORT.changeProjectsPage({
    state,
    controller: consolePanelsController || (window.CONSOLE_PANELS_CONTROLLER?.createConsolePanelsController ? getConsolePanelsController() : null),
    loadProjects,
  }, delta);
}
function renderRunExecutionContext(run) {
  const controller = getConsolePanelsController();
  return controller.renderRunExecutionContext(run);
}
function resolveTrackerExecutionContext(run) {
  return resolveTrackerExecutionContextDelegate(run);
}
async function loadPhaseReport({ silent = false } = {}) { return getReportPanelsController().loadPhaseReport({ silent }); }
async function loadReportJobs({ silent = false } = {}) { return getReportPanelsController().loadReportJobs({ silent }); }
async function runSelectedReport() { return getReportPanelsController().runSelectedReport(); }
async function refreshReportPanels() { return getReportPanelsController().refreshReportPanels(); }
function renderReport(report, errorMessage = "") { return getReportPanelsController().renderReport(report, errorMessage); }
function renderReportJobs(items) { return getReportPanelsController().renderReportJobs(items); }
function renderReportJob(job, errorMessage = "") { return getReportPanelsController().renderReportJob(job, errorMessage); }
async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) { return getRunPanelsController()?.loadSelectedRunArtifacts({ silent, runId, runSnapshot }); }
async function loadWinnerRunPanels(run) { return getRunPanelsController()?.loadWinnerRunPanels(run); }
async function loadTrackerExportPanels(run) { return getRunPanelsController()?.loadTrackerExportPanels(run); }
function scheduleArtifactRetry(runId) { return getRunPanelsController()?.scheduleArtifactRetry(runId); }
function renderArtifactsList() {
  return getReportPanelsController().renderArtifactsList();
}
function resolveTrackerContextRun(runSnapshot = state.selectedRun) {
  return getRunPanelsController()?.resolveTrackerContextRun(runSnapshot) || null;
}
function buildArtifactEmptyMessage() {
  return getReportPanelsController().buildArtifactEmptyMessage();
}
function normalizeCollectMode(value) { return APP_SUPPORT.normalizeCollectMode(value); }
function syncCollectModeOptions(value) { return getRunPanelsController()?.syncCollectModeOptions?.(value); }
function renderArtifactPreviewMarkup(artifactId) {
  return getReportPanelsController().renderArtifactPreviewMarkup(artifactId);
}
function trackerColumnStyle(widths, index) { return APP_SUPPORT.trackerColumnStyle(widths, index, ARTIFACT_RUNTIME); }
function buildWorkbookTitleCells(titleRow) { return APP_SUPPORT.buildWorkbookTitleCells(titleRow, { escapeHtml }, ARTIFACT_RUNTIME); }
async function fetchArtifactPreview(item) { return APP_SUPPORT.fetchArtifactPreview(item, api); }
async function ensureArtifactPreviewCached(item) { return APP_SUPPORT.ensureArtifactPreviewCached({ state, api, item, renderArtifactsList, renderRunExecutionContext }); }
function buildTrackerEntriesDownloadUrl(format) { return getDownloadController().buildTrackerEntriesDownloadUrl(format); }
function buildTrackerEntriesDownloadJobPayload() { return getDownloadController().buildTrackerEntriesDownloadJobPayload(); }
async function pollTrackerDownloadJob(jobId, options) { return getDownloadController().pollTrackerDownloadJob(jobId, options); }
async function triggerTrackerEntriesXlsxDownload(button) { return getDownloadController().triggerTrackerEntriesXlsxDownload(button); }
function buildTrackerEntriesDownloadWarmUrl() { return getDownloadController().buildTrackerEntriesDownloadWarmUrl(); }
async function warmTrackerEntriesDownload() { return getDownloadController().warmTrackerEntriesDownload(); }
function renderTrackerTemplateStatus(errorMessage = "") { return getTrackerController().renderTrackerTemplateStatus(errorMessage); }
async function loadTrackerTemplateStatus({ silent = false } = {}) { return getTrackerController().loadTrackerTemplateStatus({ silent }); }
async function uploadTrackerTemplate(file) { return getTrackerController().uploadTrackerTemplate(file); }
async function resetTrackerTemplateOverride() { return getTrackerController().resetTrackerTemplateOverride(); }
async function loadTrackerEntries({ silent = false, trackerRunId = resolveActiveTrackerRunId(), forceRefresh = false } = {}) { return getTrackerController().loadTrackerEntries({ silent, trackerRunId, forceRefresh }); }
async function loadTrackerMissingReport({ silent = false } = {}) { return getTrackerController().loadTrackerMissingReport({ silent }); }

const {
  renderTrackerContactResolutionSummary: renderTrackerContactResolutionSummaryDelegate,
  renderTrackerCleanupPreview: renderTrackerCleanupPreviewDelegate,
  renderTrackerMissingReport: renderTrackerMissingReportDelegate,
  loadVisibleSalesClaims: loadVisibleSalesClaimsDelegate,
  loadHomeBootstrap: loadHomeBootstrapDelegate,
  loadHomeBootstrapFromLegacy: loadHomeBootstrapFromLegacyDelegate,
  loadSalesOverview: loadSalesOverviewDelegate,
  loadSalesOverviewFromLegacy: loadSalesOverviewFromLegacyDelegate,
  loadMySalesClaims: loadMySalesClaimsDelegate,
  loadClosedSalesClaims: loadClosedSalesClaimsDelegate,
  refreshSalesAdminPanels: refreshSalesAdminPanelsDelegate,
  loadSalesClaimSummaryByUser: loadSalesClaimSummaryByUserDelegate,
  loadOrganizationUsers: loadOrganizationUsersDelegate,
  loadOrganizationMembers: loadOrganizationMembersDelegate,
  loadOrganizationInvitations: loadOrganizationInvitationsDelegate,
  loadOrganizationAuditLogs: loadOrganizationAuditLogsDelegate,
  loadOrganizationDownloadAuditLogs: loadOrganizationDownloadAuditLogsDelegate,
  loadOrganizationLoginAuditLogs: loadOrganizationLoginAuditLogsDelegate,
  loadOrganizationAdminData: loadOrganizationAdminDataDelegate,
  handleInvitationSubmit: handleInvitationSubmitDelegate,
  handlePlatformAdminAccountSubmit: handlePlatformAdminAccountSubmitDelegate,
  copyInvitationUrl: copyInvitationUrlDelegate,
  revokeOrganizationInvitation: revokeOrganizationInvitationDelegate,
  saveOrganizationMember: saveOrganizationMemberDelegate,
  deleteOrganizationMember: deleteOrganizationMemberDelegate,
  resetOrganizationMemberPassword: resetOrganizationMemberPasswordDelegate,
  performResetOrganizationMemberPassword: performResetOrganizationMemberPasswordDelegate,
  normalizeSalesClaimCardViewModel: normalizeSalesClaimCardViewModelDelegate,
  formatSalesClaimEstimateLabel: formatSalesClaimEstimateLabelDelegate,
  formatShortDateTime: formatShortDateTimeDelegate,
  formatEstimatedAmountRangeFromKrw: formatEstimatedAmountRangeFromKrwDelegate,
} = ((typeof APP_RUNTIME_BODY_ADMIN_SALES_RUNTIME !== "undefined"
  && APP_RUNTIME_BODY_ADMIN_SALES_RUNTIME?.createAppRuntimeBodyAdminSalesDelegates)
  ? APP_RUNTIME_BODY_ADMIN_SALES_RUNTIME.createAppRuntimeBodyAdminSalesDelegates({
      state,
      dom,
      APP_SUPPORT,
      TRACKER_DIAGNOSTICS_RUNTIME,
      TRACKER_MISSING_REPORT_RUNTIME,
      escapeHtml,
      formatDate,
      requireConsoleDataRuntime,
      getConsoleDataRuntimeDeps,
      getTrackerDiagnosticsPanelController,
      getOrgAdminController,
      windowObject: window,
      SALES_VIEW_RUNTIME,
      buildSalesClaimEstimateLabel: (...args) => buildSalesClaimEstimateLabel(...args),
      formatShortDateTimeHelper: (...args) => formatShortDateTimeHelper(...args),
      formatEstimatedAmountRangeFromKrwHelper: (...args) => formatEstimatedAmountRangeFromKrwHelper(...args),
    })
  : {
      renderTrackerMissingReport: () => "",
      loadVisibleSalesClaims: async () => undefined,
      loadHomeBootstrap: async () => undefined,
      loadHomeBootstrapFromLegacy: async () => undefined,
      loadSalesOverview: async () => undefined,
      loadSalesOverviewFromLegacy: async () => undefined,
      loadMySalesClaims: async () => undefined,
      loadClosedSalesClaims: async () => undefined,
      refreshSalesAdminPanels: () => undefined,
      loadSalesClaimSummaryByUser: async () => undefined,
      loadOrganizationUsers: async () => undefined,
      loadOrganizationMembers: async () => undefined,
      loadOrganizationInvitations: async () => undefined,
      loadOrganizationAuditLogs: async () => undefined,
      loadOrganizationDownloadAuditLogs: async () => undefined,
      loadOrganizationLoginAuditLogs: async () => undefined,
      loadOrganizationAdminData: () => undefined,
      handleInvitationSubmit: async () => undefined,
      handlePlatformAdminAccountSubmit: async () => undefined,
      copyInvitationUrl: async () => undefined,
      revokeOrganizationInvitation: async () => undefined,
      saveOrganizationMember: async () => undefined,
      deleteOrganizationMember: async () => undefined,
      resetOrganizationMemberPassword: async () => undefined,
      performResetOrganizationMemberPassword: async () => undefined,
      normalizeSalesClaimCardViewModel: () => ({}),
      formatSalesClaimEstimateLabel: () => "",
      formatShortDateTime: () => "",
      formatEstimatedAmountRangeFromKrw: () => "",
    });
function renderTrackerContactResolutionSummary(errorMessage = "") { const runtime = TRACKER_DIAGNOSTICS_RUNTIME; return trackerDiagnosticsPanelController?.renderTrackerContactResolutionSummary?.(errorMessage) ?? getTrackerDiagnosticsPanelController().renderTrackerContactResolutionSummary(errorMessage, runtime); }
function renderTrackerCleanupPreview(errorMessage = "") { const runtime = TRACKER_DIAGNOSTICS_RUNTIME; return trackerDiagnosticsPanelController?.renderTrackerCleanupPreview?.(errorMessage) ?? getTrackerDiagnosticsPanelController().renderTrackerCleanupPreview(errorMessage, runtime); }
function renderTrackerMissingReport(errorMessage = "") { return renderTrackerMissingReportDelegate(errorMessage); }
async function loadVisibleSalesClaims(...args) { return loadVisibleSalesClaimsDelegate(...args); } async function loadHomeBootstrap(...args) { return loadHomeBootstrapDelegate(...args); } async function loadHomeBootstrapFromLegacy(...args) { return loadHomeBootstrapFromLegacyDelegate(...args); } async function loadSalesOverview(...args) { return loadSalesOverviewDelegate(...args); } async function loadSalesOverviewFromLegacy(...args) { return loadSalesOverviewFromLegacyDelegate(...args); } async function loadMySalesClaims(...args) { return loadMySalesClaimsDelegate(...args); } async function loadClosedSalesClaims(...args) { return loadClosedSalesClaimsDelegate(...args); } function refreshSalesAdminPanels(...args) { return refreshSalesAdminPanelsDelegate(...args); } async function loadSalesClaimSummaryByUser(...args) { return loadSalesClaimSummaryByUserDelegate(...args); } async function loadOrganizationUsers(...args) { return loadOrganizationUsersDelegate(...args); } async function loadOrganizationMembers(...args) { return loadOrganizationMembersDelegate(...args); } async function loadOrganizationInvitations(...args) { return loadOrganizationInvitationsDelegate(...args); } async function loadOrganizationAuditLogs(...args) { return loadOrganizationAuditLogsDelegate(...args); } async function loadOrganizationDownloadAuditLogs(...args) { return loadOrganizationDownloadAuditLogsDelegate(...args); } async function loadOrganizationLoginAuditLogs(...args) { return loadOrganizationLoginAuditLogsDelegate(...args); } function loadOrganizationAdminData(...args) { return loadOrganizationAdminDataDelegate(...args); } async function handleInvitationSubmit(event) { return handleInvitationSubmitDelegate(event); } async function handlePlatformAdminAccountSubmit(...args) { return handlePlatformAdminAccountSubmitDelegate(...args); } async function copyInvitationUrl(...args) { return copyInvitationUrlDelegate(...args); } async function revokeOrganizationInvitation(...args) { return revokeOrganizationInvitationDelegate(...args); } async function saveOrganizationMember(...args) { return saveOrganizationMemberDelegate(...args); } async function deleteOrganizationMember(...args) { return deleteOrganizationMemberDelegate(...args); } async function resetOrganizationMemberPassword(...args) { return resetOrganizationMemberPasswordDelegate(...args); } async function performResetOrganizationMemberPassword(...args) { return performResetOrganizationMemberPasswordDelegate(...args); } function normalizeSalesClaimCardViewModel(...args) { return normalizeSalesClaimCardViewModelDelegate(...args); } function formatSalesClaimEstimateLabel(...args) { return formatSalesClaimEstimateLabelDelegate(...args); }
const SALES_STATE_HELPERS = APP_SUPPORT.createSalesStateHelpers
  ? APP_SUPPORT.createSalesStateHelpers({
      state,
      isAdminRole: typeof isAdminRole === "function" ? isAdminRole : () => false,
      buildUserSalesProjectFactsMarkup,
      formatEokValue,
    })
  : {
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
      setSalesNoteDraft: () => undefined,
      upsertSalesClaim: () => undefined,
      replaceVisibleSalesClaims: () => undefined,
      mergeActiveSalesClaims: () => undefined,
      formatShortDateTime: () => "",
      formatEstimatedAmountRangeFromKrw: () => "",
    };
const { getVisibleSalesProjectIds, getSalesClaimForProject, getTrackerProjectSnapshot, renderUserSalesProjectFacts, isCurrentUserClaimOwner, canCurrentUserForceRelease, canCurrentUserManageClaim, isActiveSalesClaim, getOrganizationTransferTargets, getSalesNoteDraft, setSalesNoteDraft, upsertSalesClaim, replaceVisibleSalesClaims, mergeActiveSalesClaims, formatShortDateTime: formatShortDateTimeHelper, formatEstimatedAmountRangeFromKrw: formatEstimatedAmountRangeFromKrwHelper } = SALES_STATE_HELPERS;
function renderSalesSummaryPanel() {
  const controller = getSalesPanelController();
  return controller.renderSalesSummaryPanel();
}
function renderMySalesClaimsPanel() {
  const controller = getSalesPanelController();
  return controller.renderMySalesClaimsPanel();
}
function renderUserOwnedSalesClaimCard(claim, index) { return getSalesPanelController().renderUserOwnedSalesClaimCard(claim, index); }
function renderCompanySalesClaimCard(claim, index) { return getSalesPanelController().renderCompanySalesClaimCard(claim, index); }
function renderUserTrackerClaimSection(entry, {
  project = null,
  summary = false,
  compact = false,
} = {}) {
  return getSalesPanelController().renderUserTrackerClaimSection(entry, { project, summary, compact });
}
function bindUserSalesSectionEvents() {
  const controller = getSalesPanelController();
  return controller.bindUserSalesSectionEvents();
}
function formatShortDateTime(value) { return formatShortDateTimeDelegate(value); }
function formatEstimatedAmountRangeFromKrw(minValue, maxValue) { return formatEstimatedAmountRangeFromKrwDelegate(minValue, maxValue); }
async function claimSalesProject(entry) {
  const controller = getSalesPanelController();
  return controller.claimSalesProject(entry);
}
async function saveSalesClaimNote(projectId) {
  const controller = getSalesPanelController();
  return controller.saveSalesClaimNote(projectId);
}
async function transferSalesClaim(projectId, targetUserId) {
  const controller = getSalesPanelController();
  return controller.transferSalesClaim(projectId, targetUserId);
}
async function closeSalesClaim(projectId, outcome, { contractAmountText = "" } = {}) {
  const controller = getSalesPanelController();
  return controller.closeSalesClaim(projectId, outcome, { contractAmountText });
}
async function adminDeleteLatestSalesNote(projectId, rawSalesNote) {
  const controller = getSalesPanelController();
  return controller.adminDeleteLatestSalesNote(projectId, rawSalesNote);
}
async function releaseSalesClaim(projectId, { force = false } = {}) {
  const controller = getSalesPanelController();
  return controller.releaseSalesClaim(projectId, { force });
}
const { getAppBootstrapBridge: getAppBootstrapBridgeAccessor, hydrateStateFromUrl: hydrateStateFromUrlAccessor, renderSyncMeta: renderSyncMetaAccessor, touchSyncMeta: touchSyncMetaAccessor, getProjectRelatedBodyRuntime, hydrateProjectRelatedPayloadCache: hydrateProjectRelatedPayloadCacheAccessor, persistProjectRelatedPayloadCache: persistProjectRelatedPayloadCacheAccessor, getBootstrapCacheHelpers, getTrackerChangeEventHelpers, getTrackerRenderFallbackHelpers, getSalesPanelDepsHelpers: getSalesPanelDepsHelpersAccessor, buildSalesOverviewStorageIdentity: buildSalesOverviewStorageIdentityAccessor, maybePreloadAdminGoogleSheetsBootstrap, clearUserModeRunSelection: clearUserModeRunSelectionAccessor } = ((typeof APP_RUNTIME_BODY_CONSOLE_RUNTIME !== "undefined" && APP_RUNTIME_BODY_CONSOLE_RUNTIME?.createAppRuntimeBodyAccessors)
  ? APP_RUNTIME_BODY_CONSOLE_RUNTIME.createAppRuntimeBodyAccessors({ state, dom, windowObject: window, BOOTSTRAP_RUNTIME, clampPage, normalizeTrackerRegionFilter, RELATED_NOTICE_RUNTIME, escapeHtml, APP_SUPPORT, CACHE_RUNTIME, ORG_ADMIN_BOOTSTRAP_STORAGE_KEY, TRACKER_CHANGE_EVENTS_STORAGE_KEY, TRACKER_CHANGE_EVENTS_STORAGE_MAX_ITEMS, TRACKER_CHANGE_EVENTS_CACHE_TTL_MS, canUseAdminMode, renderTrackerChangeEventsPanel: (...args) => renderTrackerChangeEventsPanel(...args), renderTrackerChangeEventUnreadCount: (...args) => renderTrackerChangeEventUnreadCount(...args), loadTrackerChangeEventUnreadCount: (...args) => loadTrackerChangeEventUnreadCount(...args), loadTrackerChangeEvents: (...args) => loadTrackerChangeEvents(...args), resetTrackerBoardEdit: (...args) => resetTrackerBoardEdit(...args), renderTrackerBoard: (...args) => renderTrackerBoard(...args), renderSelectedEntry: (...args) => renderSelectedEntry(...args), FRONTEND_RUNTIME_ADAPTERS, SALES_STATE_HELPERS, renderSalesClaimSection: (...args) => renderSalesClaimSection(...args), renderTrackerEntryRelatedNotices: (...args) => renderTrackerEntryRelatedNotices(...args), syncUrlState, toggleTrackerEntryRelated: (...args) => toggleTrackerEntryRelated(...args), openTrackerEntryNoticeViewer: (...args) => openTrackerEntryNoticeViewer(...args), bindRelatedNoticeViewerButtons: (...args) => bindRelatedNoticeViewerButtons(...args), claimSalesProject: (...args) => claimSalesProject(...args), saveSalesClaimNote: (...args) => saveSalesClaimNote(...args), transferSalesClaim: (...args) => transferSalesClaim(...args), flash, openSalesCloseDialog: (...args) => openSalesCloseDialog(...args), closeSalesClaim: (...args) => closeSalesClaim(...args), releaseSalesClaim: (...args) => releaseSalesClaim(...args), loadSelectedEntryDetail: (...args) => loadSelectedEntryDetail(...args), prefetchTrackerEntryDetails: (...args) => prefetchTrackerEntryDetails(...args), buildTrackerBoardMarkupFallback: (...args) => buildTrackerBoardMarkupFallback(...args), renderTrackerEntries: (...args) => renderTrackerEntries(...args), toggleTrackerBoardBlankPriority: (...args) => toggleTrackerBoardBlankPriority(...args), beginTrackerBoardEdit: (...args) => beginTrackerBoardEdit(...args), saveTrackerBoardEdit: (...args) => saveTrackerBoardEdit(...args), TRACKER_BOARD_COLUMNS, TRACKER_BOARD_TEXTAREA_FIELDS, TRACKER_BOARD_BLANK_PRIORITY_FIELDS, renderTrackerBoardHeaderCell: (...args) => renderTrackerBoardHeaderCell(...args), renderTrackerBoardCell: (...args) => renderTrackerBoardCell(...args), renderTrackerBoardEditingCell: (...args) => renderTrackerBoardEditingCell(...args), sortTrackerBoardEntriesFallback: (...args) => sortTrackerBoardEntriesFallback(...args), api, renderUserOwnedSalesClaimCard: (...args) => renderUserOwnedSalesClaimCard(...args), renderCompanySalesClaimCard: (...args) => renderCompanySalesClaimCard(...args), renderUserTrackerClaimSection: (...args) => renderUserTrackerClaimSection(...args), adminDeleteLatestSalesNote: (...args) => adminDeleteLatestSalesNote(...args), formatContractAmountInput, isAdminRole, normalizeSalesClaimCardViewModel: (...args) => normalizeSalesClaimCardViewModel(...args), loadSalesOverview: (...args) => loadSalesOverview(...args), loadMySalesClaims: (...args) => loadMySalesClaims(...args), loadVisibleSalesClaims: (...args) => loadVisibleSalesClaims(...args), refreshSalesAdminPanels: (...args) => refreshSalesAdminPanels(...args), SALES_VIEW_RUNTIME, getProjectRelatedController, getReportPanelsController, getAdminGoogleSheetsRuntimeState: () => ({ ADMIN_GOOGLE_SHEETS_RUNTIME, canLoadProtectedConsoleData, shouldShowSharedGoogleSheetsShell, hydrateAdminGoogleSheetsCacheOnFirstProtectedRender, loadAdminGoogleSheetsBootstrap }) })
  : { getAppBootstrapBridge: () => null, hydrateStateFromUrl: () => undefined, renderSyncMeta: () => undefined, touchSyncMeta: () => undefined, getProjectRelatedBodyRuntime: () => null, hydrateProjectRelatedPayloadCache: () => undefined, persistProjectRelatedPayloadCache: () => undefined, getBootstrapCacheHelpers: () => ({}), getTrackerChangeEventHelpers: () => ({}), getTrackerRenderFallbackHelpers: () => ({}), getSalesPanelDepsHelpers: () => null, buildSalesOverviewStorageIdentity: () => "", maybePreloadAdminGoogleSheetsBootstrap: () => undefined, clearUserModeRunSelection: () => undefined });
function getAppBootstrapBridge() {
  if (typeof getAppBootstrapBridgeAccessor === "function") return getAppBootstrapBridgeAccessor() ?? null;
  if (appBootstrapBridge) return appBootstrapBridge;
  const createAppBootstrapBridge = window.APP_BOOTSTRAP_BRIDGE?.createAppBootstrapBridge;
  if (typeof createAppBootstrapBridge !== "function") return null;
  appBootstrapBridge = createAppBootstrapBridge({ bootstrapRuntime: BOOTSTRAP_RUNTIME, state, window, clampPage, normalizeTrackerRegionFilter });
  return appBootstrapBridge;
}
function hydrateStateFromUrl() {
  if (typeof hydrateStateFromUrlAccessor === "function") return hydrateStateFromUrlAccessor() ?? undefined;
  return getAppBootstrapBridge()?.hydrateStateFromUrl?.() ?? undefined;
}
function renderSyncMeta() { return renderSyncMetaAccessor?.() ?? undefined; }
function touchSyncMeta(label) { return touchSyncMetaAccessor?.(label) ?? undefined; }
function hydrateProjectRelatedPayloadCache() {
  const controller = typeof getProjectRelatedController === "function" ? getProjectRelatedController() : null;
  if (controller?.hydrateProjectRelatedPayloadCache) return controller.hydrateProjectRelatedPayloadCache();
  const runtime = typeof getProjectRelatedBodyRuntime === "function" ? getProjectRelatedBodyRuntime() : null;
  return runtime?.hydrateProjectRelatedPayloadCache?.() ?? hydrateProjectRelatedPayloadCacheAccessor?.();
}

function persistProjectRelatedPayloadCache() {
  const controller = typeof getProjectRelatedController === "function" ? getProjectRelatedController() : null;
  if (controller?.persistProjectRelatedPayloadCache) return controller.persistProjectRelatedPayloadCache();
  const runtime = typeof getProjectRelatedBodyRuntime === "function" ? getProjectRelatedBodyRuntime() : null;
  return runtime?.persistProjectRelatedPayloadCache?.() ?? persistProjectRelatedPayloadCacheAccessor?.();
}

function getSalesPanelDepsHelpers() {
  if (salesPanelDepsHelpers) return salesPanelDepsHelpers;
  salesPanelDepsHelpers = APP_SUPPORT.createSalesPanelDepsHelpers({
    dom,
    state,
    windowObject: window,
    api,
    escapeHtml,
    runtimeAdapters: FRONTEND_RUNTIME_ADAPTERS,
    salesStateHelpers: SALES_STATE_HELPERS,
    renderUserOwnedSalesClaimCard,
    renderCompanySalesClaimCard,
    renderUserTrackerClaimSection,
    claimSalesProject,
    saveSalesClaimNote,
    transferSalesClaim,
    closeSalesClaim,
    adminDeleteLatestSalesNote,
    releaseSalesClaim,
    formatContractAmountInput,
    isAdminRole,
    normalizeSalesClaimCardViewModel: window.SPMSAppControllerWiringRuntime.normalizeSalesClaimCardViewModel,
    renderTrackerEntries,
    loadSalesOverview,
    loadMySalesClaims,
    loadVisibleSalesClaims,
    refreshSalesAdminPanels,
    salesViewRuntime: SALES_VIEW_RUNTIME,
    flash,
  });
  return salesPanelDepsHelpers ?? getSalesPanelDepsHelpersAccessor?.();
}
function buildSalesOverviewStorageIdentity() {
  return buildSalesOverviewStorageIdentityAccessor?.();
}

function mergeTrackerEntryInState(entry) {
  const summary = toTrackerEntrySummary(entry);
  state.trackerEntries = state.trackerEntries.map((item) => (item.id === summary.id ? { ...item, ...summary } : item));
  state.trackerEntryDetailCache = { ...state.trackerEntryDetailCache, [entry.id]: entry };
  if (state.selectedEntryId === entry.id) state.selectedEntry = entry;
}
function prefetchTrackerEntryDetails(entries) { return getTrackerController().prefetchTrackerEntryDetails(entries); }
async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) { return getTrackerController().fetchTrackerEntryDetail(entryId, { silent }); }
function renderSelectedEntryLoading(entry, errorMessage = "") { return getSelectedEntryController().renderSelectedEntryLoading(entry, errorMessage); }
function getSelectedEntryDisplayView(entry, { summaryOnly = false } = {}) { return getSelectedEntryController().getSelectedEntryDisplayView(entry, { summaryOnly }); }

function focusTrackerChangeEntry(entryId, entries = state.trackerEntries) { return APP_SUPPORT.focusTrackerChangeEntry(entryId, entries); }
function focusTrackerChangePanel() { return getTrackerDiagnosticsPanelController().focusTrackerChangePanel(); }
function bindTrackerChangeEventActions(container) { return getTrackerDiagnosticsPanelController().bindTrackerChangeEventActions(container); }
function bindBackfillConflictActions(container) { return getTrackerDiagnosticsPanelController().bindBackfillConflictActions(container); }
function setTrackerChangeBellPopoverOpen(open) { return getTrackerDiagnosticsPanelController().setTrackerChangeBellPopoverOpen(open); }
function renderTrackerChangeBellPopover() { return getTrackerDiagnosticsPanelController().renderTrackerChangeBellPopover(); }
function renderTrackerChangeEventsList(container) { return getTrackerDiagnosticsPanelController().renderTrackerChangeEventsList(container); }
function renderTrackerChangeEventsPanel() { return getTrackerDiagnosticsPanelController().renderTrackerChangeEventsPanel(); }
function renderBackfillConflictsPanel() { return getTrackerDiagnosticsPanelController().renderBackfillConflictsPanel(); }
function renderSelectedEntryChangeEvents() { return getSelectedEntryController().renderSelectedEntryChangeEvents(); }
function renderTrackerChangeEventUnreadCount() { return getTrackerDiagnosticsPanelController().renderTrackerChangeEventUnreadCount(); }
async function loadTrackerChangeEventUnreadCount({ silent = false } = {}) { return getTrackerController().loadTrackerChangeEventUnreadCount({ silent }); }
async function loadTrackerChangeEvents({ silent = false, includeSilent = false } = {}) { return getTrackerController().loadTrackerChangeEvents({ silent, includeSilent }); }
async function loadBackfillConflicts({ silent = false, includeResolved = false } = {}) { return getTrackerController().loadBackfillConflicts({ silent, includeResolved }); }
async function resolveBackfillConflict({ conflictId, resolution } = {}) { return getTrackerDiagnosticsPanelController().resolveBackfillConflict({ conflictId, resolution }); }
async function markTrackerChangeEventsRead({ eventIds = [], trackerEntryId = null, silent = false } = {}) { return getTrackerController().markTrackerChangeEventsRead({ eventIds, trackerEntryId, silent }); }
async function loadSelectedEntryChangeEvents({ entryId = state.selectedEntryId, silent = false } = {}) { return getTrackerController().loadSelectedEntryChangeEvents({ entryId, silent }); }
async function loadSelectedEntryDetail({ entryId = state.selectedEntryId, silent = false, background = false, force = false } = {}) { return getTrackerController().loadSelectedEntryDetail({ entryId, silent, background, force }); }
function resolveTrackerEntryProjectId(entryId) { return getProjectRelatedController().resolveTrackerEntryProjectId(entryId); }
function renderSalesClaimSection(entry) {
  const controller = getSalesPanelController();
  return controller.renderSalesClaimSection(entry);
}
function buildTrackerEntryCardMarkupFallback(payload = {}, helpers = {}) { return getTrackerRenderFallbackRuntime()?.buildTrackerEntryCardMarkupFallback?.(payload, helpers) || ""; }
function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {
  const controller = typeof getTrackerRenderController === "function" ? getTrackerRenderController() : null;
  if (controller?.renderTrackerEntries) return controller.renderTrackerEntries(entries, { refreshSelectedEntry });
  return typeof renderTrackerEntriesFallback === "function" ? renderTrackerEntriesFallback(entries, { refreshSelectedEntry }) : undefined;
}
function renderTrackerEntriesFallback(entries, { refreshSelectedEntry = true } = {}) { return getTrackerRenderFallbackRuntime()?.renderTrackerEntriesFallback?.(entries, getTrackerRenderFallbackHelpers().buildTrackerEntriesFallbackDeps(refreshSelectedEntry), { escapeHtml }) || undefined; }
function sortTrackerBoardEntriesFallback(entries, { fieldName = "", blankPriorityFields = TRACKER_BOARD_BLANK_PRIORITY_FIELDS } = {}, helpers = {}) {
  const runtime = getTrackerRenderFallbackRuntime();
  return runtime?.sortTrackerBoardEntriesFallback?.(entries, { fieldName, blankPriorityFields }, helpers)
    || (Array.isArray(entries) ? entries : []);
}
function buildTrackerBoardMarkupFallback(entries, options = {}, helpers = {}) {
  const runtime = getTrackerRenderFallbackRuntime();
  return runtime?.buildTrackerBoardMarkupFallback?.(entries, options, helpers) || "";
}
function renderTrackerBoard(entries) {
  const controller = typeof getTrackerRenderController === "function" ? getTrackerRenderController() : null;
  if (controller?.renderTrackerBoard) return controller.renderTrackerBoard(entries);
  return typeof renderTrackerBoardFallback === "function" ? renderTrackerBoardFallback(entries) : undefined;
}
function renderTrackerBoardFallback(entries) { return getTrackerRenderFallbackRuntime()?.renderTrackerBoardFallback?.(entries, getTrackerRenderFallbackHelpers().buildTrackerBoardFallbackDeps(), { escapeHtml }) || undefined; }
function toggleTrackerBoardBlankPriority(fieldName) { return getTrackerEntryActionsController().toggleTrackerBoardBlankPriority(fieldName); }
function renderTrackerBoardHeaderCell(column) {
  const fallbackHelpers = typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null;
  return APP_SUPPORT.renderTrackerBoardHeaderCellBridge({ column, TRACKER_BOARD_RUNTIME, fallbackHelpers, trackerBoardBlankPriorityFields: TRACKER_BOARD_BLANK_PRIORITY_FIELDS, trackerBoardSort: state.trackerBoardSort, escapeHtml });
}
function isTrackerBoardBlankValue(value) {
  const fallbackHelpers = typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null;
  return APP_SUPPORT.isTrackerBoardBlankValueBridge({ value, TRACKER_BOARD_RUNTIME, fallbackHelpers });
}
function sortTrackerBoardEntries(entries) {
  const fallbackHelpers = typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null;
  return APP_SUPPORT.sortTrackerBoardEntriesBridge({ entries, TRACKER_BOARD_RUNTIME, fallbackHelpers, fieldName: state.trackerBoardSort.fieldName, blankPriorityFields: TRACKER_BOARD_BLANK_PRIORITY_FIELDS, buildSortedTrackerBoardEntries });
}
function buildTrackerBoardCellMarkupFallback({ entry, column, displayNo, trackerBoardEdit = null }, { escapeHtml: fallbackEscapeHtml = escapeHtml, textareaFields = TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {
  return APP_SUPPORT.buildTrackerBoardCellMarkupFallbackBridge({
    payload: { entry, column, displayNo, trackerBoardEdit },
    fallbackHelpers: typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null,
    runtime: typeof getTrackerRenderFallbackRuntime === "function" ? getTrackerRenderFallbackRuntime() : null,
    escapeHtml: fallbackEscapeHtml,
    textareaFields,
  });
}
function buildTrackerBoardEditingCellMarkupFallback({ entry, fieldName, label, value, saving, errorMessage }, { escapeHtml: fallbackEscapeHtml = escapeHtml, textareaFields = TRACKER_BOARD_TEXTAREA_FIELDS } = {}) { return APP_SUPPORT.buildTrackerBoardEditingCellMarkupFallbackBridge({ payload: { entry, fieldName, label, value, saving, errorMessage }, fallbackHelpers: typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null, runtime: typeof getTrackerRenderFallbackRuntime === "function" ? getTrackerRenderFallbackRuntime() : null, escapeHtml: fallbackEscapeHtml, textareaFields }); }
function renderTrackerBoardCell({ entry, column, displayNo }) {
  return APP_SUPPORT.renderTrackerBoardCellBridge({ payload: { entry, column, displayNo, trackerBoardEdit: state.trackerBoardEdit }, TRACKER_BOARD_RUNTIME, fallbackHelpers: typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null, escapeHtml, textareaFields: TRACKER_BOARD_TEXTAREA_FIELDS, buildTrackerBoardCellMarkupFallback });
}
function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {
  return APP_SUPPORT.renderTrackerBoardEditingCellBridge({ payload: { entry, fieldName, label, value, saving, errorMessage }, TRACKER_BOARD_RUNTIME, fallbackHelpers: typeof getTrackerRenderFallbackHelpers === "function" ? getTrackerRenderFallbackHelpers() : null, escapeHtml, textareaFields: TRACKER_BOARD_TEXTAREA_FIELDS, buildTrackerBoardEditingCellMarkupFallback });
}
function beginTrackerBoardEdit(entryId, fieldName) { return getTrackerEntryActionsController().beginTrackerBoardEdit(entryId, fieldName); }
function resetTrackerBoardEdit() { return getTrackerEntryActionsController().resetTrackerBoardEdit(); }
function resolveTrackerPatchActorLabel() { return getTrackerEntryActionsController().resolveTrackerPatchActorLabel(); }
function getEntriesTotalPages() { return getTrackerEntryActionsController().getEntriesTotalPages(); }
function renderEntriesPagination() { return getTrackerEntryActionsController().renderEntriesPagination(); }
function changeEntriesPage(delta) { return getTrackerEntryActionsController().changeEntriesPage(delta); }
function changeEntriesPageTo(page) { return getTrackerEntryActionsController().changeEntriesPageTo(page); }
function renderSelectedEntry(entry, { summaryOnly = false } = {}) { return getSelectedEntryController().renderSelectedEntry(entry, { summaryOnly }); }
function renderEntryDiagnostics(entry, { summaryOnly = false, view = null } = {}) { return getSelectedEntryController().renderEntryDiagnostics(entry, { summaryOnly, view }); }
function renderEntryFieldGrid(entry, { view = null } = {}) { return getSelectedEntryController().renderEntryFieldGrid(entry, { view }); }
function renderDrawer(entry, { view = null } = {}) { return getSelectedEntryController().renderDrawer(entry, { view }); }
function syncPatchValueFromSelectedEntry({ patchView = null } = {}) { return getSelectedEntryController().syncPatchValueFromSelectedEntry({ patchView }); }
async function patchTrackerEntry({ entryId, fieldName, value, changeSource = "web", actorLabel = resolveTrackerPatchActorLabel(), }) { return getTrackerController().patchTrackerEntry({ entryId, fieldName, value, changeSource, actorLabel }); }
function replaceTrackerEntryInState(updatedEntry) { mergeTrackerEntryInState(updatedEntry); }
async function syncTrackerEntryAfterPatch(updatedEntry) { return getTrackerController().syncTrackerEntryAfterPatch(updatedEntry); }
async function saveEntryPatch(event) { return getTrackerEntryActionsController().saveEntryPatch(event); }
async function clearEntryPatch() { return getTrackerEntryActionsController().clearEntryPatch(); }
async function saveTrackerBoardEdit({ entryId, fieldName }) { return getTrackerController().saveTrackerBoardEdit({ entryId, fieldName }); }
async function loadSelectedEntryAudit() { return getTrackerController().loadSelectedEntryAudit(); }
function hydratePatchFieldOptions() { return getTrackerEntryActionsController().hydratePatchFieldOptions(); }
function handleOutOfRangePageError(error, filterState, scopeLabel) { return APP_SUPPORT.handleOutOfRangePageError(error, filterState, scopeLabel); }
function resolveActiveTrackerRunId() { return APP_SUPPORT.resolveActiveTrackerRunId(); }
if (typeof window !== "undefined" && window.__SPMS_TEST_MODE__) {
  window.__SPMS_TEST_HOOKS__ = Object.freeze({ state, hydrateStateFromUrl, syncUiModeFromLocation, applyUiMode, toggleUiMode, renderAdminTopNavigation, renderAdminEmbedPanel, loadAdminGoogleSheetsBootstrap, mountRuntimeEnhancements, bindAdminGoogleSheetsActions, bindGlobalDismissalListeners, bindAdminGoogleSheetTableInteractions, getAdminGoogleSheetsFilterState, setAdminGoogleSheetsFilterState, getAdminGoogleSheetPopupState, openAdminGoogleSheetFilterPopup, toggleAdminGoogleSheetPopupValue, setAdminGoogleSheetPopupSearch, setAdminGoogleSheetPopupSort, confirmAdminGoogleSheetPopup, cancelAdminGoogleSheetPopup, pollGeneralConsoleTick, maybeResolveLegacyAdminAliasToSheetTab, setAdminTab });
}
if (!(typeof window !== "undefined" && window.__SPMS_DISABLE_AUTO_BOOT__)) void boot();
