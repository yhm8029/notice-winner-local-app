(function attachAppStartupRuntime(global) {
  function requireRuntime(options, key, errorMessage) {
    const runtime = options[key];
    if (typeof runtime !== "object" || runtime === null) {
      throw new Error(errorMessage);
    }
    return runtime;
  }

  function requireFactory(target, key, errorMessage) {
    const factory = target?.[key];
    if (typeof factory !== "function") {
      throw new Error(errorMessage);
    }
    return factory;
  }

  function createControllerCallRuntime(options) {
    const controllerCallRuntime = requireRuntime(
      options,
      "APP_CONTROLLER_CALL_RUNTIME",
      "SPMSAppControllerCallRuntime is required before app.js loads",
    );
    const createAppControllerCallRuntime = requireFactory(
      controllerCallRuntime,
      "createAppControllerCallRuntime",
      "SPMSAppControllerCallRuntime.createAppControllerCallRuntime is required before app.js loads",
    );
    const runtime = createAppControllerCallRuntime({
      getAuthUiController: options.getAuthUiController,
      getAuthController: options.getAuthController,
      getOrgAdminController: options.getOrgAdminController,
      getRuntimeEnhancements: options.getRuntimeEnhancements,
      getReportPanelsController: options.getReportPanelsController,
      getProjectRelatedController: options.getProjectRelatedController,
      getTrackerController: options.getTrackerController,
      getRunPanelsController: options.getRunPanelsController,
      getConsolePanelsController: options.getConsolePanelsController,
      getDownloadController: options.getDownloadController,
      getTrackerDiagnosticsPanelController: options.getTrackerDiagnosticsPanelController,
      getTrackerEntryActionsController: options.getTrackerEntryActionsController,
      getTrackerRenderController: options.getTrackerRenderController,
      getSalesPanelController: options.getSalesPanelController,
      getAppEventBindings: options.getAppEventBindings,
      getSelectedEntryController: options.getSelectedEntryController,
    }) || null;
    if (!runtime) {
      throw new Error("SPMSAppControllerCallRuntime.createAppControllerCallRuntime is required before app.js loads");
    }
    return runtime;
  }

  function createBridgeRuntime(options, appControllerCallRuntime) {
    const bridgeRuntime = requireRuntime(
      options,
      "APP_BRIDGE_RUNTIME",
      "SPMSAppBridgeRuntime.createAppBridgeRuntime is required before app.js loads",
    );
    const createAppBridgeRuntime = requireFactory(
      bridgeRuntime,
      "createAppBridgeRuntime",
      "SPMSAppBridgeRuntime.createAppBridgeRuntime is required before app.js loads",
    );
    return createAppBridgeRuntime({
      state: options.state,
      dom: options.dom,
      window: options.window,
      document: options.document,
      BOOTSTRAP_RUNTIME: options.BOOTSTRAP_RUNTIME,
      CONSOLE_DATA_RUNTIME: options.CONSOLE_DATA_RUNTIME,
      AUTH_SESSION_RUNTIME: options.AUTH_SESSION_RUNTIME,
      SALES_RUNTIME: options.SALES_RUNTIME,
      RUN_VIEW_RUNTIME: options.RUN_VIEW_RUNTIME,
      ORGANIZATION_ADMIN_RUNTIME: options.ORGANIZATION_ADMIN_RUNTIME,
      TRACKER_DIAGNOSTICS_RUNTIME: options.TRACKER_DIAGNOSTICS_RUNTIME,
      SELECTED_ENTRY_RUNTIME: options.SELECTED_ENTRY_RUNTIME,
      APP_DOWNLOAD_BRIDGE: options.APP_DOWNLOAD_BRIDGE,
      APP_CONSOLE_BRIDGE: options.APP_CONSOLE_BRIDGE,
      APP_SALES_BRIDGE: options.APP_SALES_BRIDGE,
      APP_ORG_ADMIN_BRIDGE: options.APP_ORG_ADMIN_BRIDGE,
      APP_RUN_REPORT_BRIDGE: options.APP_RUN_REPORT_BRIDGE,
      APP_AUTH_BRIDGE: options.APP_AUTH_BRIDGE,
      APP_TRACKER_SUPPORT_BRIDGE: options.APP_TRACKER_SUPPORT_BRIDGE,
      APP_TRACKER_BRIDGE: options.APP_TRACKER_BRIDGE,
      APP_BOOTSTRAP_BRIDGE: options.APP_BOOTSTRAP_BRIDGE,
      APP_PROJECT_RELATED_BRIDGE: options.APP_PROJECT_RELATED_BRIDGE,
      APP_SELECTED_ENTRY_BRIDGE: options.APP_SELECTED_ENTRY_BRIDGE,
      APP_UI_GLUE_RUNTIME: options.APP_UI_GLUE_RUNTIME,
      APP_CONSOLE_DEPS_RUNTIME: options.APP_CONSOLE_DEPS_RUNTIME,
      AUTH_SESSION_HEARTBEAT_MS: options.AUTH_SESSION_HEARTBEAT_MS,
      SALES_OVERVIEW_STORAGE_KEY: options.SALES_OVERVIEW_STORAGE_KEY,
      HOME_BOOTSTRAP_STORAGE_KEY: options.HOME_BOOTSTRAP_STORAGE_KEY,
      clampPage: options.clampPage,
      api: options.api,
      flash: options.flash,
      callDownloadController: appControllerCallRuntime.callDownloadController,
      callConsolePanelsController: appControllerCallRuntime.callConsolePanelsController,
      callSalesPanelController: appControllerCallRuntime.callSalesPanelController,
      callOrgAdminController: appControllerCallRuntime.callOrgAdminController,
      callRunPanelsController: appControllerCallRuntime.callRunPanelsController,
      callReportPanelsController: appControllerCallRuntime.callReportPanelsController,
      callAuthController: appControllerCallRuntime.callAuthController,
      callAuthUiController: appControllerCallRuntime.callAuthUiController,
      callRuntimeEnhancements: appControllerCallRuntime.callRuntimeEnhancements,
      callAppEventBindings: appControllerCallRuntime.callAppEventBindings,
      callProjectRelatedController: appControllerCallRuntime.callProjectRelatedController,
      callTrackerController: appControllerCallRuntime.callTrackerController,
      callTrackerDiagnosticsPanelController: appControllerCallRuntime.callTrackerDiagnosticsPanelController,
      callTrackerRenderController: appControllerCallRuntime.callTrackerRenderController,
      callTrackerEntryActionsController: appControllerCallRuntime.callTrackerEntryActionsController,
      callSelectedEntryController: appControllerCallRuntime.callSelectedEntryController,
      canUseAdminMode: options.canUseAdminMode,
      hasCachedHomeBootstrapData: options.hasCachedHomeBootstrapData,
      hasCachedSalesOverviewData: options.hasCachedSalesOverviewData,
      isMissingHomeBootstrapEndpointError: options.isMissingHomeBootstrapEndpointError,
      isMissingSalesOverviewEndpointError: options.isMissingSalesOverviewEndpointError,
      getTrackerController: options.getTrackerController,
      RUN_TYPE_LABELS: options.RUN_TYPE_LABELS,
    });
  }

  function createAppStartupRuntime(options = {}) {
    const createAppStartupBridgeExports = requireFactory(
      global.SPMSAppStartupBridgeRuntime,
      "createAppStartupBridgeExports",
      "SPMSAppStartupBridgeRuntime.createAppStartupBridgeExports is required before app.js loads",
    );
    const appControllerCallRuntime = createControllerCallRuntime(options);
    const appBridgeRuntime = createBridgeRuntime(options, appControllerCallRuntime);
    return createAppStartupBridgeExports({ appControllerCallRuntime, appBridgeRuntime });
  }

  global.SPMSAppStartupRuntime = {
    createAppStartupRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
