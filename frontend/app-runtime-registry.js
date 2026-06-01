(function attachAppRuntimeRegistry(global) {
  function readAppRuntimeBindings(root = global) {
    const runtimeRoot = root && typeof root === "object" ? root : global;

    return {
      BOOTSTRAP_RUNTIME: runtimeRoot.SPMSBootstrapRuntime || null,
      CONSOLE_DATA_RUNTIME: runtimeRoot.SPMSConsoleDataRuntime || null,
      AUTH_SESSION_RUNTIME: runtimeRoot.SPMSAuthSessionRuntime || null,
      SALES_RUNTIME: runtimeRoot.SPMSSalesRuntime || null,
      SALES_VIEW_RUNTIME: runtimeRoot.SPMSSalesViewRuntime || null,
      TRACKER_CHANGE_RUNTIME: runtimeRoot.SPMSTrackerChangeRuntime || null,
      TRACKER_DIAGNOSTICS_RUNTIME: runtimeRoot.SPMSTrackerDiagnosticsRuntime || null,
      TRACKER_ENTRY_RUNTIME: runtimeRoot.SPMSTrackerEntryRuntime || null,
      SELECTED_ENTRY_RUNTIME: runtimeRoot.SPMSSelectedEntryRuntime || null,
      RELATED_NOTICE_RUNTIME: runtimeRoot.SPMSRelatedNoticeRuntime || null,
      PROJECT_RELATED_CONTROLLER: runtimeRoot.PROJECT_RELATED_CONTROLLER || null,
      ARTIFACT_RUNTIME: runtimeRoot.SPMSArtifactRuntime || null,
      PROJECT_RUNTIME: runtimeRoot.SPMSProjectRuntime || null,
      RUN_VIEW_RUNTIME: runtimeRoot.SPMSRunViewRuntime || null,
      ORGANIZATION_ADMIN_RUNTIME:
        runtimeRoot.SPMSOrgAdminRuntime || runtimeRoot.SPMSOrganizationAdminRuntime || null,
      RUNTIME_ENHANCEMENTS: runtimeRoot.RUNTIME_ENHANCEMENTS || null,
      REPORT_PANELS_CONTROLLER: runtimeRoot.REPORT_PANELS_CONTROLLER || null,
      CONSOLE_PANELS_CONTROLLER: runtimeRoot.CONSOLE_PANELS_CONTROLLER || null,
      TRACKER_RENDER_CONTROLLER: runtimeRoot.TRACKER_RENDER_CONTROLLER || null,
      TRACKER_ENTRY_ACTIONS_CONTROLLER: runtimeRoot.TRACKER_ENTRY_ACTIONS_CONTROLLER || null,
      DOWNLOAD_CONTROLLER: runtimeRoot.DOWNLOAD_CONTROLLER || null,
      TRACKER_DIAGNOSTICS_PANEL_CONTROLLER:
        runtimeRoot.TRACKER_DIAGNOSTICS_PANEL_CONTROLLER || null,
      SALES_PANEL_CONTROLLER: runtimeRoot.SALES_PANEL_CONTROLLER || null,
      RUN_PANELS_CONTROLLER: runtimeRoot.RUN_PANELS_CONTROLLER || null,
      APP_EVENT_BINDINGS: runtimeRoot.APP_EVENT_BINDINGS || null,
      SELECTED_ENTRY_CONTROLLER: runtimeRoot.SELECTED_ENTRY_CONTROLLER || null,
      AUTH_UI_CONTROLLER: runtimeRoot.AUTH_UI_CONTROLLER || null,
      AUTH_CONTROLLER: runtimeRoot.AUTH_CONTROLLER || null,
      TRACKER_CONTROLLER: runtimeRoot.TRACKER_CONTROLLER || null,
      ORG_ADMIN_CONTROLLER: runtimeRoot.ORG_ADMIN_CONTROLLER || null,
      APP_AUTH_BRIDGE: runtimeRoot.APP_AUTH_BRIDGE || null,
      APP_BOOTSTRAP_BRIDGE: runtimeRoot.APP_BOOTSTRAP_BRIDGE || null,
      APP_DOWNLOAD_BRIDGE: runtimeRoot.APP_DOWNLOAD_BRIDGE || null,
      APP_CONSOLE_BRIDGE: runtimeRoot.APP_CONSOLE_BRIDGE || null,
      APP_ORG_ADMIN_BRIDGE: runtimeRoot.APP_ORG_ADMIN_BRIDGE || null,
      APP_SALES_BRIDGE: runtimeRoot.APP_SALES_BRIDGE || null,
      APP_RUN_REPORT_BRIDGE: runtimeRoot.APP_RUN_REPORT_BRIDGE || null,
      APP_TRACKER_BRIDGE: runtimeRoot.APP_TRACKER_BRIDGE || null,
      APP_TRACKER_SUPPORT_BRIDGE: runtimeRoot.APP_TRACKER_SUPPORT_BRIDGE || null,
      APP_PROJECT_RELATED_BRIDGE: runtimeRoot.APP_PROJECT_RELATED_BRIDGE || null,
      APP_SELECTED_ENTRY_BRIDGE: runtimeRoot.APP_SELECTED_ENTRY_BRIDGE || null,
      APP_CONTROLLER_DEPS: runtimeRoot.APP_CONTROLLER_DEPS || null,
      APP_CONTROLLER_CONTEXT_RUNTIME: runtimeRoot.SPMSAppControllerContextRuntime || null,
    };
  }

  global.SPMSAppRuntimeRegistry = {
    readAppRuntimeBindings,
  };
})(window);
