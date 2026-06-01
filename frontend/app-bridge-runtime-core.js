(function attachAppBridgeRuntimeCore(global) {
  function requireHelpers() {
    const helpers = global.SPMSAppBridgeRuntimeHelpers;
    if (!helpers) {
      throw new Error("SPMSAppBridgeRuntimeHelpers is required before app.js loads");
    }
    return helpers;
  }

  function pickBridgeSection(bridge, bridgeKey, keys) {
    const section = { [bridgeKey]: bridge };
    for (const key of keys) {
      section[key] = bridge[key];
    }
    return section;
  }

  function pickSection(source, keys) {
    const section = {};
    for (const key of keys) {
      section[key] = source[key];
    }
    return section;
  }

  function createAppBridgeRuntimeCore(options = {}) {
    const { requireFactory, requireBridge, createRequiredBridge } = requireHelpers();
    const state = options.state;
    const dom = options.dom;
    const window = options.window;
    const document = options.document;
    const BOOTSTRAP_RUNTIME = options.BOOTSTRAP_RUNTIME;
    const CONSOLE_DATA_RUNTIME = options.CONSOLE_DATA_RUNTIME;
    const AUTH_SESSION_RUNTIME = options.AUTH_SESSION_RUNTIME;
    const SALES_RUNTIME = options.SALES_RUNTIME;
    const RUN_VIEW_RUNTIME = options.RUN_VIEW_RUNTIME;
    const ORGANIZATION_ADMIN_RUNTIME = options.ORGANIZATION_ADMIN_RUNTIME;
    const TRACKER_DIAGNOSTICS_RUNTIME = options.TRACKER_DIAGNOSTICS_RUNTIME;
    const SELECTED_ENTRY_RUNTIME = options.SELECTED_ENTRY_RUNTIME;
    const APP_DOWNLOAD_BRIDGE = options.APP_DOWNLOAD_BRIDGE;
    const APP_CONSOLE_BRIDGE = options.APP_CONSOLE_BRIDGE;
    const APP_SALES_BRIDGE = options.APP_SALES_BRIDGE;
    const APP_ORG_ADMIN_BRIDGE = options.APP_ORG_ADMIN_BRIDGE;
    const APP_RUN_REPORT_BRIDGE = options.APP_RUN_REPORT_BRIDGE;
    const APP_TRACKER_SUPPORT_BRIDGE = options.APP_TRACKER_SUPPORT_BRIDGE;
    const APP_TRACKER_BRIDGE = options.APP_TRACKER_BRIDGE;
    const APP_BOOTSTRAP_BRIDGE = options.APP_BOOTSTRAP_BRIDGE;
    const APP_PROJECT_RELATED_BRIDGE = options.APP_PROJECT_RELATED_BRIDGE;
    const APP_SELECTED_ENTRY_BRIDGE = options.APP_SELECTED_ENTRY_BRIDGE;
    const APP_UI_GLUE_RUNTIME = options.APP_UI_GLUE_RUNTIME;
    const APP_CONSOLE_DEPS_RUNTIME = options.APP_CONSOLE_DEPS_RUNTIME;
    const AUTH_SESSION_HEARTBEAT_MS = options.AUTH_SESSION_HEARTBEAT_MS;
    const SALES_OVERVIEW_STORAGE_KEY = options.SALES_OVERVIEW_STORAGE_KEY;
    const HOME_BOOTSTRAP_STORAGE_KEY = options.HOME_BOOTSTRAP_STORAGE_KEY;
    const clampPage = options.clampPage;
    const api = options.api;
    const flash = options.flash;
    const callDownloadController = options.callDownloadController;
    const callConsolePanelsController = options.callConsolePanelsController;
    const callSalesPanelController = options.callSalesPanelController;
    const callOrgAdminController = options.callOrgAdminController;
    const callRunPanelsController = options.callRunPanelsController;
    const callReportPanelsController = options.callReportPanelsController;
    const callAuthController = options.callAuthController;
    const callAuthUiController = options.callAuthUiController;
    const callRuntimeEnhancements = options.callRuntimeEnhancements;
    const callAppEventBindings = options.callAppEventBindings;
    const callProjectRelatedController = options.callProjectRelatedController;
    const callTrackerController = options.callTrackerController;
    const callTrackerDiagnosticsPanelController = options.callTrackerDiagnosticsPanelController;
    const callTrackerRenderController = options.callTrackerRenderController;
    const callTrackerEntryActionsController = options.callTrackerEntryActionsController;
    const callSelectedEntryController = options.callSelectedEntryController;
    const canUseAdminMode = options.canUseAdminMode;
    const hasCachedHomeBootstrapData = options.hasCachedHomeBootstrapData;
    const hasCachedSalesOverviewData = options.hasCachedSalesOverviewData;
    const isMissingHomeBootstrapEndpointError = options.isMissingHomeBootstrapEndpointError;
    const isMissingSalesOverviewEndpointError = options.isMissingSalesOverviewEndpointError;
    const getTrackerController = typeof options.getTrackerController === "function"
      ? options.getTrackerController
      : () => null;

    let appBootstrapBridge = null;
    let loadTrackerEntries = null;
    let renderTrackerEntries = null;

    const appDownloadBridge = createRequiredBridge(
      APP_DOWNLOAD_BRIDGE,
      "createAppDownloadBridge",
      {
        callDownloadController,
      },
      "APP_DOWNLOAD_BRIDGE.createAppDownloadBridge is required before app.js loads",
    );
    const appDownloadSection = pickBridgeSection(appDownloadBridge, "appDownloadBridge", [
      "showDownloadProgressOverlay", "updateDownloadProgressOverlay", "hideDownloadProgressOverlay", "triggerFileDownload",
      "downloadSalesWorkbook", "buildTrackerEntriesDownloadUrl", "buildTrackerEntriesDownloadWarmUrl", "warmTrackerEntriesDownload",
    ]);

    const appConsoleBridge = createRequiredBridge(
      APP_CONSOLE_BRIDGE,
      "createAppConsoleBridge",
      {
        callConsolePanelsController,
      },
      "APP_CONSOLE_BRIDGE.createAppConsoleBridge is required before app.js loads",
    );
    const { loadDashboardSummary, loadProjects } = appConsoleBridge;
    const appConsoleSection = pickBridgeSection(appConsoleBridge, "appConsoleBridge", [
      "loadDashboardSummary", "renderDashboard", "renderRunExecutionContext", "loadProjects", "renderProjects", "changeProjectsPage", "handleOutOfRangePageError",
    ]);

    const appSalesBridge = createRequiredBridge(
      APP_SALES_BRIDGE,
      "createAppSalesBridge",
      {
        state,
        callSalesPanelController,
      },
      "APP_SALES_BRIDGE.createAppSalesBridge is required before app.js loads",
    );
    const {
      getVisibleSalesProjectIds,
      isCurrentUserClaimOwner,
      isActiveSalesClaim,
      replaceVisibleSalesClaims,
      mergeActiveSalesClaims,
      renderSalesSummaryPanel,
      renderMySalesClaimsPanel,
    } = appSalesBridge;
    const appSalesSection = pickBridgeSection(appSalesBridge, "appSalesBridge", [
      "openSalesCloseDialog", "closeSalesCloseDialog", "confirmSalesCloseDialog", "getVisibleSalesProjectIds", "getSalesClaimForProject", "getTrackerProjectSnapshot",
      "renderUserSalesProjectFacts", "isCurrentUserClaimOwner", "canCurrentUserForceRelease", "canCurrentUserManageClaim", "isActiveSalesClaim", "getOrganizationTransferTargets",
      "getSalesNoteDraft", "setSalesNoteDraft", "upsertSalesClaim", "replaceVisibleSalesClaims", "mergeActiveSalesClaims", "renderSalesSummaryPanel", "renderClosedSalesArchiveSection",
      "renderMySalesClaimsPanel", "renderUserOwnedSalesClaimCard", "formatSalesClaimEstimateLabel", "renderCompanySalesClaimCard", "renderUserTrackerClaimSection", "claimSalesProject",
      "saveSalesClaimNote", "transferSalesClaim", "closeSalesClaim", "adminDeleteLatestSalesNote", "releaseSalesClaim", "bindUserSalesSectionEvents", "formatEstimatedAmountRangeFromKrw",
      "renderSalesClaimSection",
    ]);

    const appOrgAdminBridge = createRequiredBridge(
      APP_ORG_ADMIN_BRIDGE,
      "createAppOrgAdminBridge",
      {
        callOrgAdminController,
      },
      "APP_ORG_ADMIN_BRIDGE.createAppOrgAdminBridge is required before app.js loads",
    );
    const { mergeOrganizationInvitations, renderOrganizationAdminPanel, loadOrganizationUsers, loadOrganizationAdminData } = appOrgAdminBridge;
    const appOrgAdminSection = pickBridgeSection(appOrgAdminBridge, "appOrgAdminBridge", [
      "mergeOrganizationInvitationItem", "mergeOrganizationInvitations", "upsertOrganizationInvitation", "removeOrganizationInvitation", "scheduleOrganizationInvitationSync",
      "getRenderableOrgRoleOptions", "getCurrentAuthLocalUserId", "isProtectedOrganizationMember", "canInviteOrganizationAdmins", "getAllowedInvitationRoleOptions",
      "syncInvitationRoleOptions", "getOrganizationPlanSummaryForDisplay", "formatAuthAuditEventLabel", "formatAuthAuditActorLabel", "formatDownloadScopeLabel",
      "formatDownloadFormatLabel", "formatDownloadSourcePageLabel", "bindOrganizationAdminAuditActions", "renderOrganizationAdminPanel", "loadOrganizationUsers",
      "loadOrganizationMembers", "loadOrganizationInvitations", "loadOrganizationAuditLogs", "loadOrganizationDownloadAuditLogs", "loadOrganizationLoginAuditLogs",
      "loadOrganizationAdminData", "handleInvitationSubmit", "copyInvitationUrl", "revokeOrganizationInvitation", "saveOrganizationMember", "deleteOrganizationMember",
    ]);

    const appRunReportBridge = createRequiredBridge(
      APP_RUN_REPORT_BRIDGE,
      "createAppRunReportBridge",
      {
        state,
        callRunPanelsController,
        callReportPanelsController,
      },
      "APP_RUN_REPORT_BRIDGE.createAppRunReportBridge is required before app.js loads",
    );
    const { loadRuns, loadRunPresets, loadPhaseReport, loadReportJobs } = appRunReportBridge;
    const appRunReportSection = pickBridgeSection(appRunReportBridge, "appRunReportBridge", [
      "handleRunFormReset", "buildRunPayload", "createWinnerRun", "normalizeCollectMode", "syncCollectModeOptions", "renderRuns", "renderRunsPagination", "changeRunsPage",
      "selectRun", "renderRunDetail", "resolveTrackerExecutionContext", "normalizeTrackerExecutionContext", "numericSummaryValue", "trackerExportStageLabel", "trackerExecutionTone",
      "trackerExecutionMessage", "schedulePolling", "loadSelectedRunLogs", "renderLogsList", "renderRunEventStatus", "upsertRunListItem", "loadRunPresets", "renderRunPresetPanel",
      "applyPresetParams", "applySelectedPreset", "saveCurrentFormAsPreset", "loadSelectedRunArtifacts", "loadWinnerRunPanels", "loadTrackerExportPanels", "scheduleArtifactRetry",
      "resolveTrackerContextRun", "cancelSelectedRun", "createTrackerExportForSelectedRun", "renderNoticeViewerPayload", "renderNoticeViewerError", "renderNoticeViewerWindow",
      "loadPhaseReport", "loadReportJobs", "runSelectedReport", "refreshReportPanels", "renderReport", "renderReportJobs", "renderReportJob", "renderArtifactsList",
      "buildArtifactEmptyMessage", "renderArtifactPreviewMarkup",
    ]);

    const createAppAuthBridgeSection = requireFactory(
      global.SPMSAppBridgeRuntimeAuth,
      "createAppAuthBridgeSection",
      "SPMSAppBridgeRuntimeAuth.createAppAuthBridgeSection is required before app.js loads",
    );
    const appAuthSource = createAppAuthBridgeSection({
      APP_AUTH_BRIDGE: options.APP_AUTH_BRIDGE,
      callAuthController,
      callAuthUiController,
    });
    const { refreshAuthSessionState, renderAuthUi, syncUiModeChrome, applyUiModeTransition } = appAuthSource;
    const appAuthSection = pickSection(appAuthSource, [
      "appAuthBridge", "initializeAuthGate", "loadInvitationPreview", "loadInvitationPreviewByEmail", "scheduleInvitationPreviewLookup",
      "importAuthSessionFromLocationHash", "acceptPendingInvitationToken", "applyAuthSession", "refreshAuthSessionState",
      "syncAuthFormWithInvitationPreview", "renderAuthInvitationPreview", "renderAuthUi", "renderProfileStatus",
      "syncProfileDialogWithSession", "openProfileDialog", "closeProfileDialog", "handleProfileSubmit", "handleAuthSubmit",
      "handleAuthPasswordReset", "handleAuthSignOut", "setAuthMode", "syncUiModeChrome", "applyUiModeTransition",
    ]);

    const createAppConsoleDepsRuntime = requireFactory(
      APP_CONSOLE_DEPS_RUNTIME,
      "createAppConsoleDepsRuntime",
      "SPMSAppConsoleDepsRuntime.createAppConsoleDepsRuntime is required before app.js loads",
    );
    const appConsoleDepsSource = createAppConsoleDepsRuntime({
      state,
      api,
      flash,
      consoleDataRuntime: CONSOLE_DATA_RUNTIME,
      authSessionRuntime: AUTH_SESSION_RUNTIME,
      organizationAdminRuntime: ORGANIZATION_ADMIN_RUNTIME,
      trackerDiagnosticsRuntime: TRACKER_DIAGNOSTICS_RUNTIME,
      selectedEntryRuntime: SELECTED_ENTRY_RUNTIME,
      getAppBootstrapBridge: () => appBootstrapBridge,
      canUseAdminMode,
      getVisibleSalesProjectIds,
      isActiveSalesClaim,
      isCurrentUserClaimOwner,
      mergeActiveSalesClaims,
      mergeOrganizationInvitations,
      replaceVisibleSalesClaims,
      getLoadTrackerEntries: () => loadTrackerEntries,
      renderMySalesClaimsPanel,
      getRenderTrackerEntries: () => renderTrackerEntries,
      renderSalesSummaryPanel,
      renderOrganizationAdminPanel,
      hasCachedHomeBootstrapData,
      hasCachedSalesOverviewData,
      isMissingHomeBootstrapEndpointError,
      isMissingSalesOverviewEndpointError,
    }) || {};
    const appConsoleDepsSection = pickSection(appConsoleDepsSource, [
      "readConsoleCacheEnvelope", "writeConsoleCacheEnvelope", "getConsoleDataRuntimeDeps", "requireConsoleDataRuntime",
      "requireAuthSessionRuntime", "requireOrganizationAdminRuntime", "requireTrackerDiagnosticsRuntime", "requireSelectedEntryRuntime",
      "applyHomeBootstrapPayload", "hydrateHomeBootstrapCache", "persistSalesOverviewCache", "syncHomeBootstrapSalesCache",
      "persistHomeBootstrapCache", "shouldUseHomeBootstrapTrackerSnapshot", "syncUrlState", "loadVisibleSalesClaims", "loadHomeBootstrap",
      "loadHomeBootstrapFromLegacy", "loadSalesOverview", "loadSalesOverviewFromLegacy", "loadMySalesClaims", "loadClosedSalesClaims",
      "refreshSalesAdminPanels", "loadSalesClaimSummaryByUser", "formatAccountStatusLabel", "formatMembershipStatusLabel", "resolveStatusClass",
    ]);
    const {
      requireAuthSessionRuntime,
      requireOrganizationAdminRuntime,
      syncUrlState,
      loadHomeBootstrap,
      loadMySalesClaims,
      refreshSalesAdminPanels,
    } = appConsoleDepsSection;

    const createAppUiGlueRuntime = requireFactory(
      APP_UI_GLUE_RUNTIME,
      "createAppUiGlueRuntime",
      "SPMSAppUiGlueRuntime.createAppUiGlueRuntime is required before app.js loads",
    );
    const appUiGlueSource = createAppUiGlueRuntime({
      state,
      dom,
      salesRuntime: SALES_RUNTIME,
      runViewRuntime: RUN_VIEW_RUNTIME,
      runTypeLabels: options.RUN_TYPE_LABELS,
      callRuntimeEnhancements,
      callAppEventBindings,
      callProjectRelatedController,
      callRunPanelsController,
      callTrackerController,
      callReportPanelsController,
      requireOrganizationAdminRuntime,
      requireAuthSessionRuntime,
      renderAuthUi,
      canUseAdminMode,
      syncUiModeChrome,
      applyUiModeTransition,
      getAppBootstrapBridge: () => appBootstrapBridge,
    }) || {};
    const appUiGlueSection = pickSection(appUiGlueSource, [
      "canUseBootstrapSignUp", "isBootstrapEmail", "shouldShowSignUpMode", "mountRuntimeEnhancements",
      "formatContractAmountInput", "formatContractAmountDisplay", "renderInvitationStatus", "handleAuthFindId",
      "bindEvents", "runTypeLabel", "isProjectTrackerRun", "hydrateStateFromUrl", "renderSyncMeta", "touchSyncMeta",
      "hydrateProjectRelatedPayloadCache", "persistProjectRelatedPayloadCache", "openDrawer", "closeDrawer",
      "syncFilterControlsFromState", "readRunFiltersFromControls", "toggleUiMode", "useGlobalTrackerEntriesScope",
      "shouldPollGeneralConsole", "applyUiMode", "clearUserModeRunSelection",
    ]);
    const { useGlobalTrackerEntriesScope } = appUiGlueSection;

    const appTrackerSupportBridge = createRequiredBridge(
      APP_TRACKER_SUPPORT_BRIDGE,
      "createAppTrackerSupportBridge",
      {
        callTrackerDiagnosticsPanelController,
        callTrackerRenderController,
        callTrackerEntryActionsController,
      },
      "APP_TRACKER_SUPPORT_BRIDGE.createAppTrackerSupportBridge is required before app.js loads",
    );
    const {
      renderTrackerEntries: runtimeRenderTrackerEntries,
      resetTrackerBoardEdit,
      resolveTrackerPatchActorLabel,
      renderEntriesPagination,
    } = appTrackerSupportBridge;
    renderTrackerEntries = runtimeRenderTrackerEntries;
    const appTrackerSupportSection = {
      ...pickBridgeSection(appTrackerSupportBridge, "appTrackerSupportBridge", [
        "renderTrackerContactResolutionSummary", "renderTrackerCleanupPreview", "renderTrackerChangeEventsPanel", "renderBackfillConflictsPanel",
        "renderTrackerBoard", "toggleTrackerBoardBlankPriority", "beginTrackerBoardEdit", "resetTrackerBoardEdit", "resolveTrackerPatchActorLabel",
        "getEntriesTotalPages", "renderEntriesPagination", "changeEntriesPage", "changeEntriesPageTo",
      ]),
      renderTrackerEntries,
    };

    const appTrackerBridge = createRequiredBridge(
      APP_TRACKER_BRIDGE,
      "createAppTrackerBridge",
      {
        state,
        getTrackerController,
      },
      "APP_TRACKER_BRIDGE.createAppTrackerBridge is required before app.js loads",
    );
    const {
      loadTrackerEntries: runtimeLoadTrackerEntries,
      loadTrackerTemplateStatus,
      loadTrackerContactResolutionSummary,
      loadTrackerCleanupPreview,
      loadBackfillConflicts,
      normalizeTrackerRegionFilter,
    } = appTrackerBridge;
    loadTrackerEntries = runtimeLoadTrackerEntries;
    const appTrackerSection = {
      ...pickBridgeSection(appTrackerBridge, "appTrackerBridge", [
        "getTrackerDiagnosticsScope", "refreshTrackerOperationalDiagnostics", "readTrackerFiltersFromControls", "parseTrackerRegionFilter",
        "normalizeTrackerRegionFilter", "renderTrackerRegionButtons", "loadRuns", "refreshSelectedRun", "renderTrackerTemplateStatus",
        "loadTrackerTemplateStatus", "uploadTrackerTemplate", "resetTrackerTemplateOverride", "loadTrackerContactResolutionSummary",
        "loadTrackerCleanupPreview", "applyTrackerCleanupForScope", "prefetchTrackerEntryDetails", "fetchTrackerEntryDetail", "loadBackfillConflicts",
      ]),
      loadTrackerEntries,
    };

    const createAppBootstrapBridge = requireFactory(
      APP_BOOTSTRAP_BRIDGE,
      "createAppBootstrapBridge",
      "APP_BOOTSTRAP_BRIDGE.createAppBootstrapBridge is required before app.js loads",
    );
    appBootstrapBridge = requireBridge(
      createAppBootstrapBridge,
      {
        bootstrapRuntime: BOOTSTRAP_RUNTIME,
        state,
        window,
        document,
        AUTH_SESSION_HEARTBEAT_MS,
        loadHomeBootstrap,
        callAuthController,
        loadRuns,
        loadOrganizationUsers,
        loadMySalesClaims,
        getTrackerController,
        loadRunPresets,
        loadDashboardSummary,
        loadReportJobs,
        loadPhaseReport,
        refreshAuthSessionState,
        loadBackfillConflicts,
        loadOrganizationAdminData,
        loadTrackerTemplateStatus,
        loadProjects,
        refreshSalesAdminPanels,
        loadTrackerContactResolutionSummary,
        loadTrackerCleanupPreview,
        dom,
        mergeActiveSalesClaims,
        resetTrackerBoardEdit,
        renderEntriesPagination,
        renderMySalesClaimsPanel,
        renderTrackerEntries,
        syncUrlState,
        useGlobalTrackerEntriesScope,
        salesOverviewStorageKey: SALES_OVERVIEW_STORAGE_KEY,
        homeBootstrapStorageKey: HOME_BOOTSTRAP_STORAGE_KEY,
        clampPage,
        normalizeTrackerRegionFilter,
      },
      "APP_BOOTSTRAP_BRIDGE.createAppBootstrapBridge is required before app.js loads",
    );
    const appBootstrapSection = {
      appBootstrapBridge,
      getConsoleBootstrapRuntimeDeps: appBootstrapBridge.getConsoleBootstrapRuntimeDeps,
      ensureConsoleInitialized: appBootstrapBridge.ensureConsoleInitialized,
      initializeConsole: appBootstrapBridge.initializeConsole,
      loadAdminConsoleData: appBootstrapBridge.loadAdminConsoleData,
    };

    const appProjectRelatedBridge = createRequiredBridge(
      APP_PROJECT_RELATED_BRIDGE,
      "createAppProjectRelatedBridge",
      {
        callProjectRelatedController,
        getTrackerController,
        state,
      },
      "APP_PROJECT_RELATED_BRIDGE.createAppProjectRelatedBridge is required before app.js loads",
    );
    const appProjectRelatedSection = pickBridgeSection(appProjectRelatedBridge, "appProjectRelatedBridge", [
      "openTrackerEntryNoticeViewer", "renderRelatedProjectNotices", "renderTrackerEntryRelatedNotices", "renderRelatedNoticePanel", "bindRelatedNoticeViewerButtons",
      "openRelatedNoticeViewer", "openProjectNoticeViewer", "buildProjectNoticeUrl", "extractTrackerEntryBidParts", "buildTrackerEntryNoticeUrl", "prefetchProjectRelatedNotices",
      "prefetchVisibleProjectRelatedNotices", "toggleProjectRelated", "toggleTrackerEntryRelated", "loadProjectRelatedNotices", "resolveOpenTrackerRelatedProjectId",
      "isProjectRelatedVisible", "renderProjectRelatedHosts", "clearProjectRelatedRefresh", "maybeScheduleProjectRelatedRefresh", "canReuseProjectRelatedPayload",
      "cacheProjectRelatedPayload", "ensureTrackerEntryProjectId", "resolveTrackerEntryProjectId",
    ]);

    const appSelectedEntryBridge = createRequiredBridge(
      APP_SELECTED_ENTRY_BRIDGE,
      "createAppSelectedEntryBridge",
      {
        state,
        callSelectedEntryController,
        callTrackerEntryActionsController,
        resolveTrackerPatchActorLabel,
        getTrackerController,
      },
      "APP_SELECTED_ENTRY_BRIDGE.createAppSelectedEntryBridge is required before app.js loads",
    );
    const appSelectedEntrySection = pickBridgeSection(appSelectedEntryBridge, "appSelectedEntryBridge", [
      "renderSelectedEntryLoading", "loadSelectedEntryDetail", "renderSelectedEntry", "renderEntryDiagnostics", "renderEntryFieldGrid", "renderDrawer",
      "syncPatchValueFromSelectedEntry", "getSelectedEntryDisplayView", "patchTrackerEntry", "replaceTrackerEntryInState", "syncTrackerEntryAfterPatch", "saveEntryPatch",
      "clearEntryPatch", "saveTrackerBoardEdit", "hydratePatchFieldOptions",
    ]);

    return {
      ...appDownloadSection,
      ...appConsoleSection,
      ...appSalesSection,
      ...appOrgAdminSection,
      ...appRunReportSection,
      ...appAuthSection,
      ...appConsoleDepsSection,
      ...appUiGlueSection,
      ...appTrackerSupportSection,
      ...appTrackerSection,
      ...appBootstrapSection,
      ...appProjectRelatedSection,
      ...appSelectedEntrySection,
    };
  }

  global.SPMSAppBridgeRuntimeCore = {
    createAppBridgeRuntimeCore,
  };
})(typeof window !== "undefined" ? window : globalThis);
