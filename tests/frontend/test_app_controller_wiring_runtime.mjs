import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const wiringAuthRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-auth-runtime.js");
const wiringRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-runtime.js");

function loadWiringRuntime(window, context) {
  const authSource = fs.readFileSync(wiringAuthRuntimePath, "utf8");
  const source = fs.readFileSync(wiringRuntimePath, "utf8");
  vm.runInContext(authSource, context, { filename: wiringAuthRuntimePath });
  vm.runInContext(source, context, { filename: wiringRuntimePath });
  assert.ok(window.SPMSAppControllerWiringRuntime, "expected app controller wiring runtime to load");
  return window.SPMSAppControllerWiringRuntime;
}

function assertDepsMatch(actual, expected) {
  assert.deepEqual(Object.keys(actual).sort(), Object.keys(expected).sort());
  for (const key of Object.keys(expected)) {
    assert.strictEqual(actual[key], expected[key], `unexpected dependency reference for ${key}`);
  }
}

test("app controller wiring runtime builds sales panel controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    dom: { salesPanel: true },
    state: { salesPanel: true },
    window: { name: "window" },
    api: () => {},
    escapeHtml: () => {},
    getLatestSalesNoteItem: () => null,
    truncate: () => {},
    formatSalesNoteTextForDisplay: () => {},
    formatSalesDateLabel: () => {},
    getSalesNoteEntries: () => [],
    getSalesYearMonthBucket: () => null,
    formatContractAmountDisplay: () => "",
    extractContractAmountTextFromSalesNote: () => "",
    salesClaimStatusLabel: () => "",
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
    claimSalesProject: () => Promise.resolve(),
    saveSalesClaimNote: () => Promise.resolve(),
    transferSalesClaim: () => Promise.resolve(),
    closeSalesClaim: () => Promise.resolve(),
    adminDeleteLatestSalesNote: () => Promise.resolve(),
    releaseSalesClaim: () => Promise.resolve(),
    formatContractAmountInput: () => "",
    buildUserSalesProjectFactsMarkup: () => "",
    buildSalesClaimEstimateLabelMarkup: () => "",
    buildUserOwnedSalesClaimCardMarkup: () => "",
    buildCompanySalesClaimCardMarkup: () => "",
    buildUserTrackerClaimSectionMarkup: () => "",
    formatEokValue: () => "",
    getSalesNoteTimeline: () => [],
    serializeSalesNoteEntry: () => "",
    removeLatestSalesNoteEntry: () => [],
    isAdminRole: () => false,
    normalizeSalesClaimCardViewModel: () => ({}),
    renderTrackerEntries: () => {},
    loadSalesOverview: () => Promise.resolve(),
    loadMySalesClaims: () => Promise.resolve(),
    loadVisibleSalesClaims: () => Promise.resolve(),
    refreshSalesAdminPanels: () => Promise.resolve(),
    syncUrlState: () => {},
    salesViewRuntime: { runtime: true },
    flash: () => {},
  };

  const deps = runtime.createSalesPanelControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds app event bindings deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    dom: { form: true },
    state: { app: true },
    window: { name: "window" },
    document: { name: "document" },
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    TRACKER_REGION_OPTIONS: [],
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
  };

  const deps = runtime.createAppEventBindingsDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds project related controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { projectRelated: true },
    window: { name: "window" },
    api: () => Promise.resolve({ ok: true }),
    flash: () => {},
    escapeHtml: () => "",
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
    loadProjectRelatedNotices: () => Promise.resolve(),
    loadSelectedEntryDetail: () => Promise.resolve(null),
  };

  const deps = runtime.createProjectRelatedControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds tracker controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { tracker: true },
    dom: { tracker: true },
    api: () => {},
    flash: () => {},
    setBusy: () => {},
    FormData: function FormData() {},
    escapeHtml: () => {},
    formatDate: () => {},
    syncUrlState: () => {},
    readRunFiltersFromControls: () => {},
    renderRuns: () => {},
    renderRunsPagination: () => {},
    renderRunDetail: () => {},
    renderRunEventStatus: () => {},
    renderLogsList: () => {},
    upsertRunListItem: () => {},
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
    canLoadProtectedConsoleData: () => false,
    TRACKER_REGION_OPTIONS: [],
    useGlobalTrackerEntriesScope: () => false,
    shouldUseHomeBootstrapTrackerSnapshot: () => false,
    isProjectTrackerRun: () => false,
    schedulePolling: () => {},
    loadWinnerRunPanels: () => {},
    loadTrackerExportPanels: () => {},
    loadSelectedRunLogs: () => {},
    loadBackfillConflicts: () => {},
    loadVisibleSalesClaims: () => {},
    requireTrackerDiagnosticsRuntime: () => ({ runtime: true }),
    clearProjectRelatedRefresh: () => {},
    maybeScheduleProjectRelatedRefresh: () => {},
    canReuseProjectRelatedPayload: () => false,
    cacheProjectRelatedPayload: () => {},
    isProjectRelatedVisible: () => false,
    resolveTrackerEntryProjectId: () => "",
    ensureTrackerEntryProjectId: () => Promise.resolve(""),
    TRACKER_ENTRY_RUNTIME: { runtime: true },
    TRACKER_DETAIL_PREFETCH_LIMIT: 3,
    warmTrackerEntriesDownload: () => {},
    closeDrawer: () => {},
    renderTrackerBoard: () => {},
    resetTrackerBoardEdit: () => {},
    loadAdminConsoleData: () => {},
    buildSelectedEntryAuditMarkup: () => "",
    loadSelectedEntryDetail: () => {},
    renderTrackerMissingReport: () => {},
    renderSelectedEntryChangeEvents: () => {},
    renderSelectedEntry: () => {},
    renderSelectedEntryLoading: () => {},
    resolveTrackerPatchActorLabel: () => "",
    runTypeLabel: () => "",
  };

  const deps = runtime.createTrackerControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds tracker render controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    dom: { trackerRender: true },
    state: { trackerRender: true },
    escapeHtml: () => {},
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
    claimSalesProject: () => Promise.resolve(),
    setSalesNoteDraft: () => {},
    saveSalesClaimNote: () => Promise.resolve(),
    transferSalesClaim: () => Promise.resolve(),
    flash: () => {},
    openSalesCloseDialog: () => {},
    closeSalesClaim: () => Promise.resolve(),
    releaseSalesClaim: () => Promise.resolve(),
    syncUrlState: () => {},
    prefetchTrackerEntryDetails: () => Promise.resolve(),
    getSalesClaimForProject: () => null,
    getSortedTrackerBoardEntries: () => [],
    TRACKER_BOARD_COLUMNS: [],
    renderTrackerBoardHeaderCell: () => "",
    renderTrackerBoardCell: () => "",
    toggleTrackerBoardBlankPriority: () => {},
    beginTrackerBoardEdit: () => {},
    saveTrackerBoardEdit: () => Promise.resolve(),
  };

  const deps = runtime.createTrackerRenderControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds auth controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { auth: true },
    dom: { auth: true },
    document: { name: "document" },
    window: { name: "window" },
    api: () => {},
    flash: () => {},
    setBusy: () => {},
    escapeHtml: () => {},
    formatOrgRoleLabel: () => "",
    formatInvitationStatusLabel: () => "",
    formatSalesDateLabel: () => "",
    formatMembershipStatusLabel: () => "",
    requireAuthSessionRuntime: () => ({ runtime: true }),
    loadOrganizationUsers: () => Promise.resolve(),
    loadOrganizationMembers: () => Promise.resolve(),
    loadSalesOverview: () => Promise.resolve(),
    loadMySalesClaims: () => Promise.resolve(),
    refreshSalesAdminPanels: () => Promise.resolve(),
    ensureConsoleInitialized: () => Promise.resolve(),
    shouldShowSignUpMode: () => true,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    renderAuthUi: () => {},
    syncUiModeChrome: () => {},
    applyUiModeTransition: () => {},
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => false,
    loadAdminConsoleData: () => Promise.resolve(),
    loadBackfillConflicts: () => Promise.resolve(),
    renderBackfillConflictsPanel: () => {},
    renderTrackerContactResolutionSummary: () => {},
    renderTrackerCleanupPreview: () => {},
    closeDrawer: () => {},
    hydrateHomeBootstrapCache: () => {},
    clearUserModeRunSelection: () => {},
    loadHomeBootstrap: () => Promise.resolve(),
    loadTrackerEntries: () => Promise.resolve(),
    trackerController: { runtime: true },
    renderOrganizationAdminPanel: () => {},
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderRunDetail: () => {},
    renderTrackerEntries: () => {},
  };

  const deps = runtime.createAuthControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds auth ui controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { auth: true },
    dom: { auth: true },
    document: { name: "document" },
    window: { name: "window" },
    api: () => Promise.resolve(),
    flash: () => {},
    setBusy: () => {},
    escapeHtml: () => "",
    formatOrgRoleLabel: () => "",
    formatInvitationStatusLabel: () => "",
    formatSalesDateLabel: () => "",
    formatMembershipStatusLabel: () => "",
    requireAuthSessionRuntime: () => ({ runtime: true }),
    loadOrganizationUsers: () => Promise.resolve(),
    loadOrganizationMembers: () => Promise.resolve(),
    loadSalesOverview: () => Promise.resolve(),
    loadMySalesClaims: () => Promise.resolve(),
    refreshSalesAdminPanels: () => Promise.resolve(),
    ensureConsoleInitialized: () => Promise.resolve(),
    shouldShowSignUpMode: () => true,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    syncUiModeChrome: () => false,
    applyUiModeTransition: () => {},
  };

  const deps = runtime.createAuthUiControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds org admin controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { orgAdmin: true },
    dom: { orgAdmin: true },
    window: { name: "window" },
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
    membershipStatusOptions: ["active"],
    formatDownloadScopeLabel: () => "",
    formatDownloadFormatLabel: () => "",
    formatDownloadSourcePageLabel: () => "",
    platformAdminAccountRuntime: { runtime: true },
    syncPlatformAdminAccountDraftFromForm: () => {},
    handlePlatformAdminAccountSubmit: () => {},
    renderOrgAdminRuntimeReloadFallback: () => {},
    canManagePlatformAdminAccounts: () => true,
    resetOrganizationMemberPassword: () => Promise.resolve(),
    requireConsoleDataRuntime: () => ({ runtime: true }),
    getConsoleDataRuntimeDeps: () => ({ runtimeDeps: true }),
    requireOrganizationAdminRuntime: () => ({ orgAdminRuntime: true }),
    loadSalesClaimSummaryByUser: () => Promise.resolve(),
    loadClosedSalesClaims: () => Promise.resolve(),
  };

  const deps = runtime.createOrgAdminControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds ui mode controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { uiMode: true },
    dom: { uiMode: true },
    window: { name: "window" },
    DEFAULT_ADMIN_TAB: "project-status",
    APP_ROOT_PATH: "/app/",
    normalizeLocationPath: () => "",
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
    maybePreloadAdminGoogleSheetsBootstrap: () => {},
    syncTrackerChangeBellVisibility: () => {},
    hydrateTrackerChangeEventsCache: () => {},
    renderTrackerChangeEventUnreadCount: () => {},
    renderTrackerChangeBellPopover: () => {},
    renderAdminTopNavigation: () => {},
    renderAdminEmbedPanel: () => {},
    renderTrackerTemplateStatus: () => {},
    syncUrlState: () => {},
    loadAdminConsoleData: () => Promise.resolve(),
    loadBackfillConflicts: () => Promise.resolve(),
    renderBackfillConflictsPanel: () => {},
    closeDrawer: () => {},
    renderAuthUi: () => {},
    renderOrganizationAdminPanel: () => {},
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderRunDetail: () => {},
    renderTrackerEntries: () => {},
    loadOrganizationUsers: () => Promise.resolve(),
    loadTrackerEntries: () => Promise.resolve(),
    loadTrackerChangeEventUnreadCount: () => Promise.resolve(),
    loadTrackerChangeEvents: () => Promise.resolve(),
    clearUserModeRunSelection: () => {},
    hydrateHomeBootstrapCache: () => {},
    loadHomeBootstrap: () => Promise.resolve(),
    scheduleTrackerChangeEventsWarmup: () => {},
  };

  const deps = runtime.createUiModeControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds run panels controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { runs: true },
    dom: { runs: true },
    window: { name: "window" },
    document: { name: "document" },
    RUN_VIEW_RUNTIME: { runtime: true },
    api: () => Promise.resolve(),
    flash: () => {},
    touchSyncMeta: () => {},
    setBusy: () => {},
    loadRuns: () => Promise.resolve(),
    trackerController: { disconnectRunEventStream: () => {} },
    resetTrackerBoardEdit: () => {},
    syncUrlState: () => {},
    refreshSelectedRun: () => Promise.resolve(),
    escapeHtml: () => "",
    runTypeLabel: () => "",
    statusBadge: () => "",
    formatDate: () => "",
    formatJson: () => "",
    progressPercent: () => 0,
    renderRunExecutionContext: () => {},
    isProjectTrackerRun: () => false,
    useGlobalTrackerEntriesScope: () => false,
    renderArtifactsList: () => {},
    buildArtifactEmptyMessage: () => "",
    loadTrackerEntries: () => Promise.resolve(),
  };

  const deps = runtime.createRunPanelsControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds report panels controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { report: true },
    dom: { report: true },
    api: () => Promise.resolve(),
    flash: () => {},
    setBusy: () => {},
    escapeHtml: () => "",
    formatDate: () => "",
    formatJson: () => "",
    formatBytes: () => "",
    statusBadge: () => "",
    ARTIFACT_RUNTIME: { runtime: true },
    RELATED_NOTICE_RUNTIME: { runtime: true },
    loadDashboardSummary: () => Promise.resolve(),
    touchSyncMeta: () => {},
    syncUrlState: () => {},
    callRunPanelsController: () => {},
  };

  const deps = runtime.createReportPanelsControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds console panels controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    dom: { console: true },
    state: { console: true },
    escapeHtml: () => "",
    formatDate: () => "",
    runTypeLabel: () => "",
    statusBadge: () => "",
    metricCard: () => "",
    PROJECT_RUNTIME: { runtime: true },
    RUN_VIEW_RUNTIME: { runtime: true },
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
    api: () => Promise.resolve(),
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: () => {},
    flash: () => {},
  };

  const deps = runtime.createConsolePanelsControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds download controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { download: true },
    dom: { download: true },
    window: { name: "window" },
    document: { name: "document" },
    setBusy: () => {},
    flash: () => {},
    api: () => Promise.resolve(),
    readTrackerFiltersFromControls: () => ({}),
    useGlobalTrackerEntriesScope: () => false,
    resolveActiveTrackerRunId: () => "run-1",
  };

  const deps = runtime.createDownloadControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds admin google sheets controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { adminGoogleSheets: true },
    dom: { adminGoogleSheets: true },
    window: { name: "window" },
    api: () => Promise.resolve(),
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
    googleSheetsRuntime: { runtime: true },
    defaultAdminTab: "project-status",
  };

  const deps = runtime.createAdminGoogleSheetsControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds tracker entry actions controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    state: { trackerEntryActions: true },
    dom: { trackerEntryActions: true },
    EDITABLE_FIELDS: ["project_name"],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact"]),
    escapeHtml: () => "",
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    renderTrackerBoard: () => {},
    loadTrackerEntries: () => Promise.resolve(),
    setBusy: () => {},
    patchTrackerEntry: () => Promise.resolve(),
    flash: () => {},
    syncTrackerEntryAfterPatch: () => Promise.resolve(),
  };

  const deps = runtime.createTrackerEntryActionsControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds tracker diagnostics panel controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    window: { name: "window" },
    dom: { diagnostics: true },
    state: { diagnostics: true },
    api: () => Promise.resolve(),
    flash: () => {},
    trackerController: { runtime: true },
    escapeHtml: () => "",
    formatDate: () => "",
    formatContactResolutionStatusLabel: () => "",
    formatContactResolutionReasonLabel: () => "",
    formatBackfillConflictResolutionLabel: () => "",
    getTrackerDiagnosticsScope: () => ({ trackerRunId: "run-1" }),
    requireTrackerDiagnosticsRuntime: () => ({ runtime: true }),
    buildTrackerChangeEventsMarkup: () => "",
    buildTrackerChangeBellPopoverMarkup: () => "",
    buildBackfillConflictsMarkup: () => "",
    buildBackfillConflictsView: () => ({ html: "" }),
    syncUrlState: () => {},
    renderTrackerEntries: () => {},
    loadSelectedEntryDetail: () => Promise.resolve(),
    focusTrackerChangeEntry: () => Promise.resolve(),
    closeTrackerChangeModal: () => {},
  };

  const deps = runtime.createTrackerDiagnosticsPanelControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds selected entry controller deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    dom: { selectedEntry: true },
    state: { selectedEntry: true },
    buildSelectedEntryLoadingView: () => "",
    buildSelectedEntryEmptyView: () => "",
    buildSelectedEntryDisplayView: () => "",
    buildPatchPanelView: () => "",
    buildSelectedEntryChangeEventsMarkup: () => "",
    buildSelectedEntryMeta: () => ({}),
    buildEntryDiagnosticsMarkup: () => "",
    buildEntryFieldGridMarkup: () => "",
    buildDrawerFieldListMarkup: () => "",
    truncate: () => "",
    escapeHtml: () => "",
    requireSelectedEntryRuntime: () => ({ runtime: true }),
    formatJson: () => "",
    EDITABLE_FIELDS: ["project_name"],
    loadSelectedEntryAudit: () => Promise.resolve(),
    loadSelectedEntryChangeEvents: () => Promise.resolve(),
    openDrawer: () => {},
    closeDrawer: () => {},
    syncUrlState: () => {},
  };

  const deps = runtime.createSelectedEntryControllerDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime builds runtime enhancements deps without changing references", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const expected = {
    dom: { runtimeEnhancements: true },
    document: { name: "document" },
    syncCollectModeOptions: () => {},
    RUN_VIEW_RUNTIME: { runtime: true },
    renderOrganizationAdminPanel: () => {},
  };

  const deps = runtime.createRuntimeEnhancementsDeps(expected);
  assertDepsMatch(deps, expected);
});

test("app controller wiring runtime merges helper sources and defaults binding names through the seam", () => {
  const window = {};
  const context = vm.createContext({ window, console });
  const runtime = loadWiringRuntime(window, context);

  const wiring = runtime.createAppControllerWiringRuntime({
    helperSources: [
      { alpha: "a", shared: "first" },
      { beta: "b" },
    ],
    helpers: {
      shared: "override",
      gamma: "c",
    },
  });

  assert.deepEqual(wiring.helperSources, [
    { alpha: "a", shared: "first" },
    { beta: "b" },
  ]);
  assert.deepEqual({ ...wiring.helpers }, {
    alpha: "a",
    shared: "override",
    beta: "b",
    gamma: "c",
  });
  assert.deepEqual(wiring.bindingNames, runtime.DEFAULT_BINDING_NAMES);
});
