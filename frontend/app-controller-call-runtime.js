(function attachAppControllerCallRuntime(root) {
  const CONTROLLER_CALL_RUNTIME_CONFIG = [
    ["callAuthUiController", "getAuthUiController", "AUTH_UI_CONTROLLER"],
    ["callAuthController", "getAuthController", "AUTH_CONTROLLER"],
    ["callOrgAdminController", "getOrgAdminController", "ORG_ADMIN_CONTROLLER"],
    ["callRuntimeEnhancements", "getRuntimeEnhancements", "RUNTIME_ENHANCEMENTS"],
    ["callReportPanelsController", "getReportPanelsController", "REPORT_PANELS_CONTROLLER"],
    ["callProjectRelatedController", "getProjectRelatedController", "PROJECT_RELATED_CONTROLLER"],
    ["callTrackerController", "getTrackerController", "TRACKER_CONTROLLER"],
    ["callRunPanelsController", "getRunPanelsController", "RUN_PANELS_CONTROLLER"],
    ["callConsolePanelsController", "getConsolePanelsController", "CONSOLE_PANELS_CONTROLLER"],
    ["callDownloadController", "getDownloadController", "DOWNLOAD_CONTROLLER"],
    ["callTrackerDiagnosticsPanelController", "getTrackerDiagnosticsPanelController", "TRACKER_DIAGNOSTICS_PANEL_CONTROLLER"],
    ["callTrackerEntryActionsController", "getTrackerEntryActionsController", "TRACKER_ENTRY_ACTIONS_CONTROLLER"],
    ["callTrackerRenderController", "getTrackerRenderController", "TRACKER_RENDER_CONTROLLER"],
    ["callSalesPanelController", "getSalesPanelController", "SALES_PANEL_CONTROLLER"],
    ["callAppEventBindings", "getAppEventBindings", "APP_EVENT_BINDINGS"],
    ["callSelectedEntryController", "getSelectedEntryController", "SELECTED_ENTRY_CONTROLLER"],
  ];

  function createControllerCaller(getController, controllerName) {
    return function callControllerMethod(methodName, ...args) {
      const method = getController?.()?.[methodName];
      if (typeof method !== "function") {
        throw new Error(`${controllerName}.${methodName} is required before app.js loads`);
      }
      return method(...args);
    };
  }

  function createAppControllerCallRuntime(getters = {}) {
    const runtime = {};
    for (const [wrapperName, getterName, controllerName] of CONTROLLER_CALL_RUNTIME_CONFIG) {
      runtime[wrapperName] = createControllerCaller(getters[getterName], controllerName);
    }
    return runtime;
  }

  const runtimeRoot = root.SPMSAppControllerCallRuntime || {};
  runtimeRoot.createAppControllerCallRuntime = createAppControllerCallRuntime;
  root.SPMSAppControllerCallRuntime = runtimeRoot;
}(typeof window !== "undefined" ? window : globalThis));
