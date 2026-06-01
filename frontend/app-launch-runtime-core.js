const APP_LAUNCH_RUNTIME_INTERNALS = (() => {
  function isObject(value) {
    return typeof value === "object" && value !== null;
  }

  function coerceObject(value, fallback = null) {
    return isObject(value) ? value : fallback;
  }

  function mergeRuntimeSources(startupOptions, runtimeMap) {
    return {
      ...(isObject(startupOptions?.bridgeFactories) ? startupOptions.bridgeFactories : {}),
      ...(isObject(runtimeMap) ? runtimeMap : {}),
    };
  }

  return {
    isObject,
    coerceObject,
    mergeRuntimeSources,
  };
})();

function loadAppLaunchRuntimeCoreRuntime() {
  if (typeof window === "undefined") {
    return globalThis.SPMSAppLaunchRuntimeCoreRuntime || null;
  }
  if (window.SPMSAppLaunchRuntimeCoreRuntime) {
    return window.SPMSAppLaunchRuntimeCoreRuntime;
  }
  if (typeof XMLHttpRequest === "function" && typeof document !== "undefined") {
    const request = new XMLHttpRequest();
    request.open("GET", "/app/app-launch-runtime-core-runtime.js?v=20260425a", false);
    request.send(null);
    if ((request.status >= 200 && request.status < 300) || request.status === 0) {
      (0, eval)(request.responseText);
    }
  }
  return window.SPMSAppLaunchRuntimeCoreRuntime || null;
}

const APP_LAUNCH_RUNTIME_CORE_RUNTIME = loadAppLaunchRuntimeCoreRuntime();

(function attachAppLaunchRuntimeCore(global) {
  const APP_LAUNCH_RUNTIME_HELPERS = global.SPMSAppLaunchRuntimeHelpers || null;
  if (!APP_LAUNCH_RUNTIME_HELPERS) {
    throw new Error("SPMSAppLaunchRuntimeHelpers is required before app.js loads");
  }
  if (!APP_LAUNCH_RUNTIME_CORE_RUNTIME) {
    throw new Error("SPMSAppLaunchRuntimeCoreRuntime is required before app.js loads");
  }

  const {
    isObject,
    createControllerAccessors,
    readRuntime,
    readFactory,
  } = APP_LAUNCH_RUNTIME_HELPERS;
  const {
    resolveAppLaunchRuntimeDeps,
    createAppLaunchBoot,
    buildAppEntryRuntimeConfig,
  } = APP_LAUNCH_RUNTIME_CORE_RUNTIME;

  function createAppLaunchRuntime(options = {}) {
    const resolved = resolveAppLaunchRuntimeDeps({
      globalObject: global,
      options,
      runtimeHelpers: {
        isObject,
        readRuntime,
        readFactory,
      },
    });
    const {
      normalized: {
        root,
        windowObject,
        documentObject,
        navigatorObject,
        FormDataConstructor,
        startupOptions,
        entryOptions,
      },
      bindings,
      bootstrap,
      constants,
      support,
      helperValues,
      runtimes: {
        APP_CONTROLLER_CALL_RUNTIME,
        APP_UI_GLUE_RUNTIME,
        APP_CONSOLE_DEPS_RUNTIME,
        APP_BRIDGE_RUNTIME,
      },
      factories: {
        createAppStartupRuntime,
        createAppViewBindings,
        createAppControllerBootstrapRuntime,
        createAppEntryRuntime,
        createAppControllerState,
      },
    } = resolved;

    const {
      BOOTSTRAP_RUNTIME = null,
      CONSOLE_DATA_RUNTIME = null,
      AUTH_SESSION_RUNTIME = null,
      SALES_RUNTIME = null,
      SALES_VIEW_RUNTIME = null,
      TRACKER_CHANGE_RUNTIME = null,
      TRACKER_DIAGNOSTICS_RUNTIME = null,
      TRACKER_ENTRY_RUNTIME = null,
      SELECTED_ENTRY_RUNTIME = null,
      RELATED_NOTICE_RUNTIME = null,
      ARTIFACT_RUNTIME = null,
      PROJECT_RUNTIME = null,
      RUN_VIEW_RUNTIME = null,
      ORGANIZATION_ADMIN_RUNTIME = null,
      APP_DOWNLOAD_BRIDGE = null,
      APP_CONSOLE_BRIDGE = null,
      APP_SALES_BRIDGE = null,
      APP_ORG_ADMIN_BRIDGE = null,
      APP_RUN_REPORT_BRIDGE = null,
      APP_AUTH_BRIDGE = null,
      APP_TRACKER_SUPPORT_BRIDGE = null,
      APP_TRACKER_BRIDGE = null,
      APP_BOOTSTRAP_BRIDGE = null,
      APP_PROJECT_RELATED_BRIDGE = null,
      APP_SELECTED_ENTRY_BRIDGE = null,
      APP_CONTROLLER_DEPS = null,
      APP_CONTROLLER_CONTEXT_RUNTIME = null,
      AUTH_UI_CONTROLLER = null,
      PROJECT_RELATED_CONTROLLER = null,
      TRACKER_CONTROLLER = null,
      AUTH_CONTROLLER = null,
      ORG_ADMIN_CONTROLLER = null,
      RUNTIME_ENHANCEMENTS = null,
      REPORT_PANELS_CONTROLLER = null,
      RUN_PANELS_CONTROLLER = null,
      TRACKER_ENTRY_ACTIONS_CONTROLLER = null,
      TRACKER_RENDER_CONTROLLER = null,
      CONSOLE_PANELS_CONTROLLER = null,
      DOWNLOAD_CONTROLLER = null,
      TRACKER_DIAGNOSTICS_PANEL_CONTROLLER = null,
      SALES_PANEL_CONTROLLER = null,
      APP_EVENT_BINDINGS = null,
      SELECTED_ENTRY_CONTROLLER = null,
    } = bindings;
    const {
      APP_SHELL_RUNTIME = null,
      state,
      dom,
      APP_CORE_RUNTIME = null,
    } = bootstrap;
    const {
      EDITABLE_FIELDS,
      RUN_TYPE_LABELS,
      TRACKER_CHANGE_FIELD_LABELS,
    } = constants;
    const {
      hasCachedSalesOverviewData,
      hasCachedHomeBootstrapData,
      isMissingSalesOverviewEndpointError,
      isMissingHomeBootstrapEndpointError,
      formatOrgRoleLabel,
      formatInvitationStatusLabel,
      formatContactResolutionStatusLabel,
      formatContactResolutionReasonLabel,
      isAdminRole,
      canUseAdminMode,
      canLoadProtectedConsoleData,
      getMissingReportDownloadLimit,
    } = support;
    const {
      api,
      flash,
      formatDate,
      formatKoreanDate,
      truncate,
      clampPage,
      escapeHtml,
    } = helperValues;
    const formatBackfillConflictResolutionLabel =
      TRACKER_CHANGE_RUNTIME?.formatBackfillConflictResolutionLabel;

    const controllerState = isObject(options.controllerState)
      ? options.controllerState
      : createAppControllerState();
    const controllerAccessors = createControllerAccessors(controllerState, options.controllerAccessors || {});
    const startupState = startupOptions.state || state;
    const startupDom = startupOptions.dom || dom;
    const startupWindow = startupOptions.window || windowObject;
    const startupDocument = startupOptions.document || documentObject;

    const appStartupRuntime = createAppStartupRuntime({
      APP_CONTROLLER_CALL_RUNTIME,
      APP_BRIDGE_RUNTIME,
      ...controllerAccessors,
      state: startupState,
      dom: startupDom,
      window: startupWindow,
      document: startupDocument,
      BOOTSTRAP_RUNTIME,
      CONSOLE_DATA_RUNTIME,
      AUTH_SESSION_RUNTIME,
      SALES_RUNTIME,
      RUN_VIEW_RUNTIME,
      ORGANIZATION_ADMIN_RUNTIME,
      TRACKER_DIAGNOSTICS_RUNTIME,
      SELECTED_ENTRY_RUNTIME,
      APP_DOWNLOAD_BRIDGE,
      APP_CONSOLE_BRIDGE,
      APP_SALES_BRIDGE,
      APP_ORG_ADMIN_BRIDGE,
      APP_RUN_REPORT_BRIDGE,
      APP_AUTH_BRIDGE,
      APP_TRACKER_SUPPORT_BRIDGE,
      APP_TRACKER_BRIDGE,
      APP_BOOTSTRAP_BRIDGE,
      APP_PROJECT_RELATED_BRIDGE,
      APP_SELECTED_ENTRY_BRIDGE,
      APP_UI_GLUE_RUNTIME,
      APP_CONSOLE_DEPS_RUNTIME,
      AUTH_SESSION_HEARTBEAT_MS:
        startupOptions.constants?.AUTH_SESSION_HEARTBEAT_MS
        ?? bootstrap.constants.AUTH_SESSION_HEARTBEAT_MS,
      SALES_OVERVIEW_STORAGE_KEY:
        startupOptions.constants?.SALES_OVERVIEW_STORAGE_KEY
        ?? bootstrap.constants.SALES_OVERVIEW_STORAGE_KEY,
      HOME_BOOTSTRAP_STORAGE_KEY:
        startupOptions.constants?.HOME_BOOTSTRAP_STORAGE_KEY
        ?? bootstrap.constants.HOME_BOOTSTRAP_STORAGE_KEY,
      clampPage,
      api,
      flash,
      canUseAdminMode,
      hasCachedHomeBootstrapData,
      hasCachedSalesOverviewData,
      isMissingHomeBootstrapEndpointError,
      isMissingSalesOverviewEndpointError,
      getTrackerController: controllerAccessors.getTrackerController,
      RUN_TYPE_LABELS,
    });
    bootstrap.appRuntimeBootstrap?.attachAppStartupRuntime?.(appStartupRuntime);

    const boot = createAppLaunchBoot({
      startupDom,
      startupWindow,
      startupState,
      appStartupRuntime,
    });
    const appEntryRuntime = createAppEntryRuntime(buildAppEntryRuntimeConfig({
      entryOptions,
      controllerState,
      appStartupRuntime,
      APP_CONTROLLER_CONTEXT_RUNTIME,
      APP_CONTROLLER_DEPS,
      root,
      startupState,
      startupDom,
      documentObject,
      windowObject,
      navigatorObject,
      FormDataConstructor,
      APP_CORE_RUNTIME,
      APP_SHELL_RUNTIME,
      SALES_RUNTIME,
      SALES_VIEW_RUNTIME,
      TRACKER_CHANGE_RUNTIME,
      TRACKER_DIAGNOSTICS_RUNTIME,
      TRACKER_ENTRY_RUNTIME,
      SELECTED_ENTRY_RUNTIME,
      TRACKER_CHANGE_FIELD_LABELS,
      EDITABLE_FIELDS,
      escapeHtml,
      formatDate,
      truncate,
      formatKoreanDate,
      RUN_VIEW_RUNTIME,
      RELATED_NOTICE_RUNTIME,
      ARTIFACT_RUNTIME,
      PROJECT_RUNTIME,
      createAppViewBindings,
      createAppControllerBootstrapRuntime,
      appDownloadBridge: appStartupRuntime.appDownloadBridge,
      appConsoleBridge: appStartupRuntime.appConsoleBridge,
      appSalesBridge: appStartupRuntime.appSalesBridge,
      appOrgAdminBridge: appStartupRuntime.appOrgAdminBridge,
      appRunReportBridge: appStartupRuntime.appRunReportBridge,
      appAuthBridge: appStartupRuntime.appAuthBridge,
      appTrackerSupportBridge: appStartupRuntime.appTrackerSupportBridge,
      appTrackerBridge: appStartupRuntime.appTrackerBridge,
      appProjectRelatedBridge: appStartupRuntime.appProjectRelatedBridge,
      appSelectedEntryBridge: appStartupRuntime.appSelectedEntryBridge,
      formatOrgRoleLabel,
      formatInvitationStatusLabel,
      formatAccountStatusLabel: appStartupRuntime.formatAccountStatusLabel,
      formatMembershipStatusLabel: appStartupRuntime.formatMembershipStatusLabel,
      formatContactResolutionStatusLabel,
      formatContactResolutionReasonLabel,
      formatBackfillConflictResolutionLabel,
      formatContractAmountDisplay: appStartupRuntime.formatContractAmountDisplay,
      formatContractAmountInput: appStartupRuntime.formatContractAmountInput,
      renderInvitationStatus: appStartupRuntime.renderInvitationStatus,
      requireAuthSessionRuntime: appStartupRuntime.requireAuthSessionRuntime,
      requireConsoleDataRuntime: appStartupRuntime.requireConsoleDataRuntime,
      requireOrganizationAdminRuntime: appStartupRuntime.requireOrganizationAdminRuntime,
      requireTrackerDiagnosticsRuntime: appStartupRuntime.requireTrackerDiagnosticsRuntime,
      requireSelectedEntryRuntime: appStartupRuntime.requireSelectedEntryRuntime,
      getConsoleDataRuntimeDeps: appStartupRuntime.getConsoleDataRuntimeDeps,
      resolveStatusClass: appStartupRuntime.resolveStatusClass,
      runTypeLabel: appStartupRuntime.runTypeLabel,
      syncUiModeChrome: appStartupRuntime.syncUiModeChrome,
      syncUrlState: appStartupRuntime.syncUrlState,
      syncFilterControlsFromState: appStartupRuntime.syncFilterControlsFromState,
      touchSyncMeta: appStartupRuntime.touchSyncMeta,
      callRunPanelsController: appStartupRuntime.callRunPanelsController,
      handleAuthFindId: appStartupRuntime.handleAuthFindId,
      openDrawer: appStartupRuntime.openDrawer,
      closeDrawer: appStartupRuntime.closeDrawer,
      loadSalesOverview: appStartupRuntime.loadSalesOverview,
      loadMySalesClaims: appStartupRuntime.loadMySalesClaims,
      loadVisibleSalesClaims: appStartupRuntime.loadVisibleSalesClaims,
      loadSalesClaimSummaryByUser: appStartupRuntime.loadSalesClaimSummaryByUser,
      loadClosedSalesClaims: appStartupRuntime.loadClosedSalesClaims,
      refreshSalesAdminPanels: appStartupRuntime.refreshSalesAdminPanels,
      renderSyncMeta: appStartupRuntime.renderSyncMeta,
      readRunFiltersFromControls: appStartupRuntime.readRunFiltersFromControls,
      getMissingReportDownloadLimit,
      toggleUiMode: appStartupRuntime.toggleUiMode,
      canUseAdminMode,
      canLoadProtectedConsoleData,
      useGlobalTrackerEntriesScope: appStartupRuntime.useGlobalTrackerEntriesScope,
      shouldUseHomeBootstrapTrackerSnapshot: appStartupRuntime.shouldUseHomeBootstrapTrackerSnapshot,
      isProjectTrackerRun: appStartupRuntime.isProjectTrackerRun,
      isAdminRole,
      isBootstrapEmail: appStartupRuntime.isBootstrapEmail,
      shouldShowSignUpMode: appStartupRuntime.shouldShowSignUpMode,
      clearUserModeRunSelection: appStartupRuntime.clearUserModeRunSelection,
      hydrateHomeBootstrapCache: appStartupRuntime.hydrateHomeBootstrapCache,
      callTrackerDiagnosticsPanelController: appStartupRuntime.callTrackerDiagnosticsPanelController,
      callSelectedEntryController: appStartupRuntime.callSelectedEntryController,
      AUTH_UI_CONTROLLER,
      PROJECT_RELATED_CONTROLLER,
      TRACKER_CONTROLLER,
      AUTH_CONTROLLER,
      ORG_ADMIN_CONTROLLER,
      RUNTIME_ENHANCEMENTS,
      REPORT_PANELS_CONTROLLER,
      RUN_PANELS_CONTROLLER,
      TRACKER_ENTRY_ACTIONS_CONTROLLER,
      TRACKER_RENDER_CONTROLLER,
      CONSOLE_PANELS_CONTROLLER,
      DOWNLOAD_CONTROLLER,
      TRACKER_DIAGNOSTICS_PANEL_CONTROLLER,
      SALES_PANEL_CONTROLLER,
      APP_EVENT_BINDINGS,
      SELECTED_ENTRY_CONTROLLER,
      createWinnerRun: appStartupRuntime.createWinnerRun,
      boot,
    }));
    const {
      appViewBindings,
      launchApp,
    } = appEntryRuntime;

    return {
      controllerState,
      appStartupRuntime,
      appEntryRuntime,
      appViewBindings,
      boot,
      launchApp,
    };
  }

  global.SPMSAppLaunchRuntimeCore = {
    createAppLaunchRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
