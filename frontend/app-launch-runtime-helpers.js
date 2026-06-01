(function attachAppLaunchRuntimeHelpers(global) {
  function isObject(value) {
    return typeof value === "object" && value !== null;
  }

  function createControllerAccessors(controllerState, overrides = {}) {
    return {
      getAuthUiController: overrides.getAuthUiController || (() => controllerState.authUiController),
      getAuthController: overrides.getAuthController || (() => controllerState.authController),
      getOrgAdminController: overrides.getOrgAdminController || (() => controllerState.orgAdminController),
      getRuntimeEnhancements: overrides.getRuntimeEnhancements || (() => controllerState.runtimeEnhancements),
      getReportPanelsController: overrides.getReportPanelsController || (() => controllerState.reportPanelsController),
      getProjectRelatedController: overrides.getProjectRelatedController || (() => controllerState.projectRelatedController),
      getTrackerController: overrides.getTrackerController || (() => controllerState.trackerController),
      getRunPanelsController: overrides.getRunPanelsController || (() => controllerState.runPanelsController),
      getConsolePanelsController: overrides.getConsolePanelsController || (() => controllerState.consolePanelsController),
      getDownloadController: overrides.getDownloadController || (() => controllerState.downloadController),
      getTrackerDiagnosticsPanelController:
        overrides.getTrackerDiagnosticsPanelController || (() => controllerState.trackerDiagnosticsPanelController),
      getTrackerEntryActionsController:
        overrides.getTrackerEntryActionsController || (() => controllerState.trackerEntryActionsController),
      getTrackerRenderController: overrides.getTrackerRenderController || (() => controllerState.trackerRenderController),
      getSalesPanelController: overrides.getSalesPanelController || (() => controllerState.salesPanelController),
      getAppEventBindings: overrides.getAppEventBindings || (() => controllerState.appEventBindings),
      getSelectedEntryController: overrides.getSelectedEntryController || (() => controllerState.selectedEntryController),
    };
  }

  function readRuntime(optionsRuntimeMap, root, explicitKey, globalKey, errorMessage) {
    const runtime = optionsRuntimeMap?.[explicitKey] || root?.[globalKey] || null;
    if (!isObject(runtime)) {
      throw new Error(errorMessage);
    }
    return runtime;
  }

  function readFactory(runtime, key, errorMessage) {
    const factory = runtime?.[key];
    if (typeof factory !== "function") {
      throw new Error(errorMessage);
    }
    return factory;
  }

  global.SPMSAppLaunchRuntimeHelpers = {
    isObject,
    createControllerAccessors,
    readRuntime,
    readFactory,
  };
})(typeof window !== "undefined" ? window : globalThis);
