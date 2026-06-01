(function attachAppControllerContextRuntime(global) {
  const APP_CONTROLLER_DEPS_READY_KEY = "__appControllerDepsReadyState";
  const LOCAL_KEYS = [
    "state",
    "dom",
    "document",
    "window",
    "navigator",
    "FormData",
  ];

  const CORE_RUNTIME_KEYS = [
    "api",
    "flash",
    "setBusy",
    "metricCard",
    "statusBadge",
    "progressPercent",
    "formatJson",
    "formatDate",
    "formatKoreanDate",
    "formatBytes",
    "truncate",
    "escapeHtml",
  ];

  const SHELL_RUNTIME_KEYS = [
    "AUTH_MODE_SIGN_IN",
    "AUTH_MODE_SIGN_UP",
    "TRACKER_REGION_OPTIONS",
    "EDITABLE_FIELDS",
    "TRACKER_BOARD_COLUMNS",
    "TRACKER_BOARD_TEXTAREA_FIELDS",
    "TRACKER_BOARD_BLANK_PRIORITY_FIELDS",
    "MEMBERSHIP_STATUS_OPTIONS",
    "TRACKER_DETAIL_PREFETCH_LIMIT",
    "PROJECT_RELATED_READY_CACHE_TTL_MS",
    "PROJECT_RELATED_SEED_CACHE_TTL_MS",
    "PROJECT_RELATED_STORAGE_KEY",
    "PROJECT_RELATED_STORAGE_MAX_ITEMS",
  ];

  const HELPER_KEYS = [
    "formatOrgRoleLabel",
    "formatInvitationStatusLabel",
    "formatAccountStatusLabel",
    "formatMembershipStatusLabel",
    "formatContactResolutionStatusLabel",
    "formatContactResolutionReasonLabel",
    "formatBackfillConflictResolutionLabel",
    "formatBuildingAutomationEstimateValue",
    "formatSalesDateLabel",
    "formatSalesNoteTextForDisplay",
    "formatContractAmountDisplay",
    "formatContractAmountInput",
    "formatEokValue",
    "renderReportPanels",
    "renderInvitationStatus",
    "buildTrackerEntriesEmptyStateView",
    "buildTrackerEntryCardView",
    "buildTrackerEntriesListMarkup",
    "buildTrackerBoardEmptyStateView",
    "buildTrackerBoardMarkup",
    "buildTrackerEntrySummaryDetail",
    "buildSelectedEntryAuditMarkup",
    "buildSelectedEntryLoadingView",
    "buildSelectedEntryEmptyView",
    "buildSelectedEntryDisplayView",
    "buildPatchPanelView",
    "buildSelectedEntryMeta",
    "buildSelectedEntryChangeEventsMarkup",
    "buildEntryDiagnosticsMarkup",
    "buildEntryFieldGridMarkup",
    "buildDrawerFieldListMarkup",
    "buildTrackerChangeEventsMarkup",
    "buildBackfillConflictsView",
    "requireAuthSessionRuntime",
    "requireConsoleDataRuntime",
    "requireOrganizationAdminRuntime",
    "requireTrackerDiagnosticsRuntime",
    "requireSelectedEntryRuntime",
    "getConsoleDataRuntimeDeps",
    "getLatestSalesNoteItem",
    "getSalesNoteEntries",
    "getSalesNoteTimeline",
    "getSalesYearMonthBucket",
    "normalizeSalesClaimCardViewModel",
    "resolveStatusClass",
    "runTypeLabel",
    "syncUiModeChrome",
    "syncUrlState",
    "syncFilterControlsFromState",
    "touchSyncMeta",
    "callRunPanelsController",
    "handleAuthFindId",
    "handleRunCreate",
    "openDrawer",
    "closeDrawer",
    "ensureConsoleInitialized",
    "loadSalesOverview",
    "loadMySalesClaims",
    "loadAdminConsoleData",
    "loadHomeBootstrap",
    "loadVisibleSalesClaims",
    "loadSalesClaimSummaryByUser",
    "loadClosedSalesClaims",
    "refreshSalesAdminPanels",
    "renderSyncMeta",
    "readRunFiltersFromControls",
    "getMissingReportDownloadLimit",
    "toggleUiMode",
    "canUseAdminMode",
    "canLoadProtectedConsoleData",
    "useGlobalTrackerEntriesScope",
    "shouldUseHomeBootstrapTrackerSnapshot",
    "isProjectTrackerRun",
    "isAdminRole",
    "isBootstrapEmail",
    "shouldShowSignUpMode",
    "clearUserModeRunSelection",
    "hydrateHomeBootstrapCache",
    "buildUserSalesProjectFactsMarkup",
    "buildSalesClaimEstimateLabelMarkup",
    "buildUserOwnedSalesClaimCardMarkup",
    "buildCompanySalesClaimCardMarkup",
    "buildUserTrackerClaimSectionMarkup",
    "extractContractAmountTextFromSalesNote",
    "salesClaimStatusLabel",
    "serializeSalesNoteEntry",
    "removeLatestSalesNoteEntry",
    "callTrackerDiagnosticsPanelController",
    "callSelectedEntryController",
  ];

  const RUNTIME_KEYS = [
    "RUN_VIEW_RUNTIME",
    "TRACKER_ENTRY_RUNTIME",
    "SALES_VIEW_RUNTIME",
    "RELATED_NOTICE_RUNTIME",
    "ARTIFACT_RUNTIME",
    "PROJECT_RUNTIME",
  ];

  const DYNAMIC_KEYS = [
    "loadSelectedEntryAudit",
    "loadSelectedEntryChangeEvents",
    "trackerController",
  ];

  const BRIDGE_KEY_MAP = {
    appDownloadBridge: [
      "triggerFileDownload",
      "downloadSalesWorkbook",
      "buildTrackerEntriesDownloadUrl",
      "warmTrackerEntriesDownload",
    ],
    appConsoleBridge: [
      "loadDashboardSummary",
      "renderDashboard",
      "renderRunExecutionContext",
      "loadProjects",
      "renderProjects",
      "changeProjectsPage",
      "handleOutOfRangePageError",
    ],
    appSalesBridge: [
      "openSalesCloseDialog",
      "closeSalesCloseDialog",
      "confirmSalesCloseDialog",
      "getVisibleSalesProjectIds",
      "getSalesClaimForProject",
      "getTrackerProjectSnapshot",
      "renderUserSalesProjectFacts",
      "isCurrentUserClaimOwner",
      "canCurrentUserForceRelease",
      "canCurrentUserManageClaim",
      "isActiveSalesClaim",
      "getOrganizationTransferTargets",
      "getSalesNoteDraft",
      "setSalesNoteDraft",
      "upsertSalesClaim",
      "replaceVisibleSalesClaims",
      "mergeActiveSalesClaims",
      "renderSalesSummaryPanel",
      "renderMySalesClaimsPanel",
      "renderUserOwnedSalesClaimCard",
      "formatSalesClaimEstimateLabel",
      "renderCompanySalesClaimCard",
      "renderUserTrackerClaimSection",
      "claimSalesProject",
      "saveSalesClaimNote",
      "transferSalesClaim",
      "closeSalesClaim",
      "adminDeleteLatestSalesNote",
      "releaseSalesClaim",
      "formatEstimatedAmountRangeFromKrw",
      "renderSalesClaimSection",
    ],
    appOrgAdminBridge: [
      "formatDownloadScopeLabel",
      "formatDownloadFormatLabel",
      "formatDownloadSourcePageLabel",
      "bindOrganizationAdminAuditActions",
      "renderOrganizationAdminPanel",
      "loadOrganizationUsers",
      "loadOrganizationMembers",
      "loadOrganizationInvitations",
      "loadOrganizationAuditLogs",
      "loadOrganizationDownloadAuditLogs",
      "loadOrganizationLoginAuditLogs",
      "loadOrganizationAdminData",
      "handleInvitationSubmit",
    ],
    appRunReportBridge: [
      "handleRunFormReset",
      "syncCollectModeOptions",
      "renderRuns",
      "renderRunsPagination",
      "changeRunsPage",
      "renderRunDetail",
      "resolveTrackerExecutionContext",
      "trackerExportStageLabel",
      "trackerExecutionTone",
      "trackerExecutionMessage",
      "schedulePolling",
      "loadSelectedRunLogs",
      "renderRunEventStatus",
      "loadRunPresets",
      "renderRunPresetPanel",
      "applyPresetParams",
      "applySelectedPreset",
      "saveCurrentFormAsPreset",
      "loadSelectedRunArtifacts",
      "loadWinnerRunPanels",
      "loadTrackerExportPanels",
      "cancelSelectedRun",
      "createTrackerExportForSelectedRun",
      "renderNoticeViewerPayload",
      "renderNoticeViewerError",
      "renderNoticeViewerWindow",
      "loadPhaseReport",
      "loadReportJobs",
      "runSelectedReport",
      "refreshReportPanels",
      "renderReport",
      "renderReportJob",
      "renderArtifactsList",
      "buildArtifactEmptyMessage",
      "renderArtifactPreviewMarkup",
    ],
    appAuthBridge: [
      "scheduleInvitationPreviewLookup",
      "refreshAuthSessionState",
      "renderAuthUi",
      "openProfileDialog",
      "closeProfileDialog",
      "handleProfileSubmit",
      "handleAuthSubmit",
      "handleAuthPasswordReset",
      "handleAuthSignOut",
      "setAuthMode",
      "syncUiModeChrome",
      "applyUiModeTransition",
    ],
    appTrackerSupportBridge: [
      "renderTrackerContactResolutionSummary",
      "renderTrackerCleanupPreview",
      "renderTrackerChangeEventsPanel",
      "renderBackfillConflictsPanel",
      "renderTrackerEntries",
      "renderTrackerBoard",
      "toggleTrackerBoardBlankPriority",
      "beginTrackerBoardEdit",
      "resetTrackerBoardEdit",
      "resolveTrackerPatchActorLabel",
      "getEntriesTotalPages",
      "renderEntriesPagination",
      "changeEntriesPage",
      "changeEntriesPageTo",
    ],
    appTrackerBridge: [
      "getTrackerDiagnosticsScope",
      "refreshTrackerOperationalDiagnostics",
      "readTrackerFiltersFromControls",
      "parseTrackerRegionFilter",
      "normalizeTrackerRegionFilter",
      "loadRuns",
      "refreshSelectedRun",
      "renderTrackerTemplateStatus",
      "uploadTrackerTemplate",
      "resetTrackerTemplateOverride",
      "loadTrackerEntries",
      "loadTrackerContactResolutionSummary",
      "loadTrackerCleanupPreview",
      "applyTrackerCleanupForScope",
      "prefetchTrackerEntryDetails",
      "loadBackfillConflicts",
    ],
    appProjectRelatedBridge: [
      "openTrackerEntryNoticeViewer",
      "renderRelatedProjectNotices",
      "renderTrackerEntryRelatedNotices",
      "bindRelatedNoticeViewerButtons",
      "openProjectNoticeViewer",
      "toggleProjectRelated",
      "toggleTrackerEntryRelated",
      "loadProjectRelatedNotices",
      "isProjectRelatedVisible",
      "renderProjectRelatedHosts",
      "clearProjectRelatedRefresh",
      "maybeScheduleProjectRelatedRefresh",
      "canReuseProjectRelatedPayload",
      "cacheProjectRelatedPayload",
      "ensureTrackerEntryProjectId",
      "resolveTrackerEntryProjectId",
    ],
    appSelectedEntryBridge: [
      "renderSelectedEntryLoading",
      "loadSelectedEntryDetail",
      "renderSelectedEntry",
      "syncPatchValueFromSelectedEntry",
      "patchTrackerEntry",
      "syncTrackerEntryAfterPatch",
      "saveEntryPatch",
      "clearEntryPatch",
      "saveTrackerBoardEdit",
    ],
  };

  function defineAllowlistedDescriptors(target, source, keys) {
    if (!source || typeof source !== "object") {
      return target;
    }
    for (const key of keys) {
      const descriptor = Object.getOwnPropertyDescriptor(source, key);
      if (descriptor) {
        Object.defineProperty(target, key, descriptor);
      }
    }
    return target;
  }

  function getSectionSource(sections, primaryKey, fallbackKey) {
    return sections?.[primaryKey] || sections?.[fallbackKey] || null;
  }

  function getAppControllerDeps(root, initialDeps) {
    return root?.APP_CONTROLLER_DEPS || initialDeps || null;
  }

  function getAppControllerDepsReadyState(root = global, initialDeps = null) {
    const existingReadyState = root[APP_CONTROLLER_DEPS_READY_KEY];
    if (
      existingReadyState
      && typeof existingReadyState === "object"
      && typeof existingReadyState.resolve === "function"
      && existingReadyState.promise
      && typeof existingReadyState.promise.then === "function"
    ) {
      const deps = getAppControllerDeps(root, initialDeps);
      if (deps) {
        existingReadyState.resolve(deps);
      }
      root.APP_CONTROLLER_DEPS_READY = existingReadyState.promise;
      return existingReadyState;
    }

    let resolveReady;
    const readyState = {
      resolved: false,
      promise: new Promise((resolve) => {
        resolveReady = resolve;
      }),
      resolve(value) {
        if (!readyState.resolved) {
          readyState.resolved = true;
          resolveReady(value);
        }
        return value;
      },
    };

    root[APP_CONTROLLER_DEPS_READY_KEY] = readyState;
    const deps = getAppControllerDeps(root, initialDeps);
    if (deps) {
      readyState.resolve(deps);
    }
    root.APP_CONTROLLER_DEPS_READY = readyState.promise;
    return readyState;
  }

  async function waitForAppControllerDepsReady(root = global, initialDeps = null) {
    const readyState = getAppControllerDepsReadyState(root, initialDeps);
    const deps = getAppControllerDeps(root, initialDeps);
    if (deps) {
      readyState.resolve(deps);
      root.APP_CONTROLLER_DEPS_READY = readyState.promise;
      return deps;
    }
    return readyState.promise;
  }

  function createAppControllerDepsContext(sections = {}) {
    const context = {};
    const coreRuntime = getSectionSource(sections, "coreRuntime", "core");
    const shellRuntime = getSectionSource(sections, "shellRuntime", "shell");
    const bridges = sections.bridges || sections.bridgeSources || {};

    defineAllowlistedDescriptors(context, sections.locals, LOCAL_KEYS);
    defineAllowlistedDescriptors(context, coreRuntime, CORE_RUNTIME_KEYS);
    defineAllowlistedDescriptors(context, sections.helpers, HELPER_KEYS);

    for (const [bridgeName, keys] of Object.entries(BRIDGE_KEY_MAP)) {
      defineAllowlistedDescriptors(context, bridges[bridgeName], keys);
    }

    defineAllowlistedDescriptors(context, shellRuntime, SHELL_RUNTIME_KEYS);
    defineAllowlistedDescriptors(context, sections.runtimes, RUNTIME_KEYS);
    defineAllowlistedDescriptors(context, sections.dynamic, DYNAMIC_KEYS);
    return context;
  }

  function createAppControllerDepsBootstrap(options = {}) {
    const root = options.root || global;
    const initialDeps = options.initialDeps || null;
    const createContext = options.createAppControllerDepsContext;
    let appControllerDepsContext = null;

    getAppControllerDepsReadyState(root, initialDeps);

    function getAppControllerDepsContext() {
      if (!appControllerDepsContext) {
        appControllerDepsContext = createContext();
      }
      return appControllerDepsContext;
    }

    function requireAppControllerDeps(methodName) {
      const method = getAppControllerDeps(root, initialDeps)?.[methodName];
      if (typeof method !== "function") {
        throw new Error(`APP_CONTROLLER_DEPS.${methodName} is required before app.js loads`);
      }
      return method;
    }

    function createAppControllerDeps(methodName) {
      return requireAppControllerDeps(methodName)(getAppControllerDepsContext());
    }

    function createBuilder(methodName) {
      return function buildAppControllerDeps() {
        return createAppControllerDeps(methodName);
      };
    }

    function createBindings(methodNames = []) {
      const bindings = {};
      for (const methodName of methodNames) {
        bindings[methodName] = createBuilder(methodName);
      }
      return bindings;
    }

    return {
      getAppControllerDepsReadyState() {
        return getAppControllerDepsReadyState(root, initialDeps);
      },
      waitForAppControllerDepsReady() {
        return waitForAppControllerDepsReady(root, initialDeps);
      },
      createBindings,
    };
  }

  global.SPMSAppControllerContextRuntime = {
    createAppControllerDepsContext,
    createAppControllerDepsBootstrap,
  };
})(window);
