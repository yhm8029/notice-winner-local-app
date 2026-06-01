(function attachAppLaunchRuntimeCoreRuntime(global) {
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

  function resolveAppLaunchRuntimeDeps({ globalObject, options = {}, runtimeHelpers }) {
    const { readRuntime, readFactory } = runtimeHelpers;
    const root = coerceObject(options.root, globalObject);
    const windowObject = coerceObject(options.window, root);
    const documentObject = options.document || windowObject?.document || null;
    const navigatorObject = options.navigator || windowObject?.navigator || null;
    const FormDataConstructor = options.FormData || windowObject?.FormData || global.FormData;
    const runtimeMap = coerceObject(options.runtimes, {});
    const startupOptions = coerceObject(options.startup, {});
    const entryOptions = coerceObject(options.entry, {});
    const runtimeSources = mergeRuntimeSources(startupOptions, runtimeMap);

    const runtimes = {
      APP_CONTROLLER_CALL_RUNTIME: readRuntime(runtimeSources, root, "APP_CONTROLLER_CALL_RUNTIME", "SPMSAppControllerCallRuntime", "SPMSAppControllerCallRuntime is required before app.js loads"),
      APP_UI_GLUE_RUNTIME: readRuntime(runtimeSources, root, "APP_UI_GLUE_RUNTIME", "SPMSAppUiGlueRuntime", "SPMSAppUiGlueRuntime is required before app.js loads"),
      APP_CONSOLE_DEPS_RUNTIME: readRuntime(runtimeSources, root, "APP_CONSOLE_DEPS_RUNTIME", "SPMSAppConsoleDepsRuntime", "SPMSAppConsoleDepsRuntime is required before app.js loads"),
      APP_BRIDGE_RUNTIME: readRuntime(runtimeSources, root, "APP_BRIDGE_RUNTIME", "SPMSAppBridgeRuntime", "SPMSAppBridgeRuntime.createAppBridgeRuntime is required before app.js loads"),
      APP_STARTUP_RUNTIME: readRuntime(runtimeSources, root, "APP_STARTUP_RUNTIME", "SPMSAppStartupRuntime", "SPMSAppStartupRuntime.createAppStartupRuntime is required before app.js loads"),
      APP_VIEW_BINDINGS_RUNTIME: readRuntime(runtimeSources, root, "APP_VIEW_BINDINGS_RUNTIME", "SPMSAppViewBindingsRuntime", "SPMSAppViewBindingsRuntime.createAppViewBindings is required before app.js loads"),
      APP_CONTROLLER_BOOTSTRAP_RUNTIME: readRuntime(runtimeSources, root, "APP_CONTROLLER_BOOTSTRAP_RUNTIME", "SPMSAppControllerBootstrapRuntime", "SPMSAppControllerBootstrapRuntime.createAppControllerBootstrapRuntime is required before app.js loads"),
      APP_ENTRY_RUNTIME: readRuntime(runtimeSources, root, "APP_ENTRY_RUNTIME", "SPMSAppEntryRuntime", "SPMSAppEntryRuntime.createAppEntryRuntime is required before app.js loads"),
    };

    const factories = {
      createAppStartupRuntime: readFactory(runtimes.APP_STARTUP_RUNTIME, "createAppStartupRuntime", "SPMSAppStartupRuntime.createAppStartupRuntime is required before app.js loads"),
      createAppViewBindings: readFactory(runtimes.APP_VIEW_BINDINGS_RUNTIME, "createAppViewBindings", "SPMSAppViewBindingsRuntime.createAppViewBindings is required before app.js loads"),
      createAppControllerBootstrapRuntime: readFactory(runtimes.APP_CONTROLLER_BOOTSTRAP_RUNTIME, "createAppControllerBootstrapRuntime", "SPMSAppControllerBootstrapRuntime.createAppControllerBootstrapRuntime is required before app.js loads"),
      createAppEntryRuntime: readFactory(runtimes.APP_ENTRY_RUNTIME, "createAppEntryRuntime", "SPMSAppEntryRuntime.createAppEntryRuntime is required before app.js loads"),
      createAppControllerState: isObject(options.controllerState)
        ? null
        : readFactory(runtimes.APP_ENTRY_RUNTIME, "createAppControllerState", "SPMSAppEntryRuntime.createAppControllerState is required before app.js loads"),
    };

    return {
      normalized: {
        root,
        window: windowObject,
        document: documentObject,
        navigator: navigatorObject,
        FormData: FormDataConstructor,
        runtimeMap,
        startupOptions,
        entryOptions,
        runtimeSources,
      },
      runtimes,
      factories,
    };
  }

  function createAppLaunchBoot({ startupDom, startupWindow, startupState, appStartupRuntime }) {
    return async function boot() {
      appStartupRuntime.mountRuntimeEnhancements();
      appStartupRuntime.hydrateStateFromUrl();
      appStartupRuntime.hydrateProjectRelatedPayloadCache();
      startupDom.apiBaseLabel.textContent = startupWindow.location.origin;
      appStartupRuntime.hydratePatchFieldOptions();
      appStartupRuntime.syncFilterControlsFromState();
      appStartupRuntime.renderSyncMeta();
      appStartupRuntime.applyUiMode();
      appStartupRuntime.bindEvents();
      appStartupRuntime.renderAuthUi();
      appStartupRuntime.renderDashboard(null);
      appStartupRuntime.renderReport(null);
      appStartupRuntime.renderReportJob(null);
      await appStartupRuntime.importAuthSessionFromLocationHash();
      await appStartupRuntime.initializeAuthGate();
      if (!startupState.auth.enabled || (startupState.auth.authenticated && startupState.auth.authorized)) {
        await appStartupRuntime.ensureConsoleInitialized();
      }
    };
  }

  function buildAppEntryRuntimeOptions(args) {
    const {
      entryOptions,
      createAppViewBindings,
      createAppControllerBootstrapRuntime,
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
      RELATED_NOTICE_RUNTIME,
      ARTIFACT_RUNTIME,
      PROJECT_RUNTIME,
      RUN_VIEW_RUNTIME,
      TRACKER_CHANGE_FIELD_LABELS,
      EDITABLE_FIELDS,
      escapeHtml,
      formatDate,
      truncate,
      formatKoreanDate,
      appDownloadBridge,
      appConsoleBridge,
      appSalesBridge,
      appOrgAdminBridge,
      appRunReportBridge,
      appAuthBridge,
      appTrackerSupportBridge,
      appTrackerBridge,
      appProjectRelatedBridge,
      appSelectedEntryBridge,
      formatOrgRoleLabel,
      formatInvitationStatusLabel,
      formatAccountStatusLabel,
      formatMembershipStatusLabel,
      formatContactResolutionStatusLabel,
      formatContactResolutionReasonLabel,
      formatBackfillConflictResolutionLabel,
      formatContractAmountDisplay,
      formatContractAmountInput,
      renderInvitationStatus,
      requireAuthSessionRuntime,
      requireConsoleDataRuntime,
      requireOrganizationAdminRuntime,
      requireTrackerDiagnosticsRuntime,
      requireSelectedEntryRuntime,
      getConsoleDataRuntimeDeps,
      resolveStatusClass,
      runTypeLabel,
      syncUiModeChrome,
      syncUrlState,
      syncFilterControlsFromState,
      touchSyncMeta,
      callRunPanelsController,
      handleAuthFindId,
      openDrawer,
      closeDrawer,
      loadSalesOverview,
      loadMySalesClaims,
      loadVisibleSalesClaims,
      loadSalesClaimSummaryByUser,
      loadClosedSalesClaims,
      refreshSalesAdminPanels,
      renderSyncMeta,
      readRunFiltersFromControls,
      getMissingReportDownloadLimit,
      toggleUiMode,
      canUseAdminMode,
      canLoadProtectedConsoleData,
      useGlobalTrackerEntriesScope,
      shouldUseHomeBootstrapTrackerSnapshot,
      isProjectTrackerRun,
      isAdminRole,
      isBootstrapEmail,
      shouldShowSignUpMode,
      clearUserModeRunSelection,
      hydrateHomeBootstrapCache,
      callTrackerDiagnosticsPanelController,
      callSelectedEntryController,
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
      createWinnerRun,
      boot,
    } = args;

    return {
      createAppViewBindings,
      createAppControllerBootstrapRuntime,
      controllerState,
      appStartupRuntime,
      APP_CONTROLLER_CONTEXT_RUNTIME: entryOptions.APP_CONTROLLER_CONTEXT_RUNTIME || APP_CONTROLLER_CONTEXT_RUNTIME,
      APP_CONTROLLER_DEPS: entryOptions.APP_CONTROLLER_DEPS || APP_CONTROLLER_DEPS,
      root: entryOptions.root || root,
      locals: entryOptions.locals || { state: startupState, dom: startupDom, document: documentObject, window: windowObject, navigator: navigatorObject, FormData: FormDataConstructor },
      coreRuntime: entryOptions.coreRuntime || APP_CORE_RUNTIME,
      shellRuntime: entryOptions.shellRuntime || APP_SHELL_RUNTIME,
      viewBindings: {
        SALES_RUNTIME: entryOptions.viewBindings?.SALES_RUNTIME || SALES_RUNTIME,
        SALES_VIEW_RUNTIME: entryOptions.viewBindings?.SALES_VIEW_RUNTIME || SALES_VIEW_RUNTIME,
        TRACKER_CHANGE_RUNTIME: entryOptions.viewBindings?.TRACKER_CHANGE_RUNTIME || TRACKER_CHANGE_RUNTIME,
        TRACKER_DIAGNOSTICS_RUNTIME: entryOptions.viewBindings?.TRACKER_DIAGNOSTICS_RUNTIME || TRACKER_DIAGNOSTICS_RUNTIME,
        TRACKER_ENTRY_RUNTIME: entryOptions.viewBindings?.TRACKER_ENTRY_RUNTIME || TRACKER_ENTRY_RUNTIME,
        SELECTED_ENTRY_RUNTIME: entryOptions.viewBindings?.SELECTED_ENTRY_RUNTIME || SELECTED_ENTRY_RUNTIME,
        TRACKER_CHANGE_FIELD_LABELS,
        EDITABLE_FIELDS,
        formatContractAmountDisplay: appStartupRuntime.formatContractAmountDisplay,
        escapeHtml,
        formatDate,
        truncate,
        formatKoreanDate,
        getTrackerProjectSnapshot: appStartupRuntime.getTrackerProjectSnapshot,
      },
      runtimes: entryOptions.runtimes || { RUN_VIEW_RUNTIME, TRACKER_ENTRY_RUNTIME, SALES_VIEW_RUNTIME, RELATED_NOTICE_RUNTIME, ARTIFACT_RUNTIME, PROJECT_RUNTIME },
      bridges: entryOptions.bridges || { appDownloadBridge, appConsoleBridge, appSalesBridge, appOrgAdminBridge, appRunReportBridge, appAuthBridge, appTrackerSupportBridge, appTrackerBridge, appProjectRelatedBridge, appSelectedEntryBridge },
      helpers: entryOptions.helpers || {
        formatOrgRoleLabel, formatInvitationStatusLabel, formatAccountStatusLabel, formatMembershipStatusLabel, formatContactResolutionStatusLabel, formatContactResolutionReasonLabel, formatBackfillConflictResolutionLabel, formatContractAmountDisplay, formatContractAmountInput, renderInvitationStatus, requireAuthSessionRuntime, requireConsoleDataRuntime, requireOrganizationAdminRuntime, requireTrackerDiagnosticsRuntime, requireSelectedEntryRuntime, getConsoleDataRuntimeDeps, resolveStatusClass, runTypeLabel, syncUiModeChrome, syncUrlState, syncFilterControlsFromState, touchSyncMeta, callRunPanelsController, handleAuthFindId, openDrawer, closeDrawer, loadSalesOverview, loadMySalesClaims, loadVisibleSalesClaims, loadSalesClaimSummaryByUser, loadClosedSalesClaims, refreshSalesAdminPanels, renderSyncMeta, readRunFiltersFromControls, getMissingReportDownloadLimit, toggleUiMode, canUseAdminMode, canLoadProtectedConsoleData, useGlobalTrackerEntriesScope, shouldUseHomeBootstrapTrackerSnapshot, isProjectTrackerRun, isAdminRole, isBootstrapEmail, shouldShowSignUpMode, clearUserModeRunSelection, hydrateHomeBootstrapCache, callTrackerDiagnosticsPanelController, callSelectedEntryController,
      },
      dynamic: entryOptions.dynamic || {
        loadSelectedEntryAudit: (...runtimeArgs) => controllerState.trackerController?.loadSelectedEntryAudit?.(...runtimeArgs),
        loadSelectedEntryChangeEvents: (...runtimeArgs) => controllerState.trackerController?.loadSelectedEntryChangeEvents?.(...runtimeArgs),
        get trackerController() { return controllerState.trackerController; },
      },
      controllerFactories: entryOptions.controllerFactories || {
        AUTH_UI_CONTROLLER, PROJECT_RELATED_CONTROLLER, TRACKER_CONTROLLER, AUTH_CONTROLLER, ORG_ADMIN_CONTROLLER, RUNTIME_ENHANCEMENTS, REPORT_PANELS_CONTROLLER, RUN_PANELS_CONTROLLER, TRACKER_ENTRY_ACTIONS_CONTROLLER, TRACKER_RENDER_CONTROLLER, CONSOLE_PANELS_CONTROLLER, DOWNLOAD_CONTROLLER, TRACKER_DIAGNOSTICS_PANEL_CONTROLLER, SALES_PANEL_CONTROLLER, APP_EVENT_BINDINGS, SELECTED_ENTRY_CONTROLLER,
      },
      dom: entryOptions.dom || startupDom,
      createWinnerRun: entryOptions.createWinnerRun || createWinnerRun,
      boot,
    };
  }

  global.SPMSAppLaunchRuntimeCoreRuntime = {
    isObject,
    coerceObject,
    mergeRuntimeSources,
    resolveAppLaunchRuntimeDeps,
    createAppLaunchBoot,
    buildAppEntryRuntimeOptions,
  };
})(typeof window !== "undefined" ? window : globalThis);
