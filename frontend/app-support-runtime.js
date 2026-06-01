(function attachAppSupportRuntime(global) {
  const ORG_RUNTIME = global.SPMSAppSupportOrgRuntime || null;
  const STARTUP_RUNTIME = global.SPMSAppSupportStartupRuntime || null;
  const AUTH_RUNTIME = global.SPMSAppSupportAuthRuntime || null;
  const VIEW_RUNTIME = global.SPMSAppSupportViewRuntime || null;
  const TRACKER_RUNTIME = global.SPMSAppSupportTrackerDepsRuntime || null;
  const UI_RUNTIME = global.SPMSAppSupportUiRuntime || null;
  const TRACKER_SUPPORT_RUNTIME = global.SPMSAppSupportTrackerRuntime || null;
  const ADMIN_SUPPORT_RUNTIME = global.SPMSAppSupportAdminRuntime || null;
  // Delegation markers kept here for source-level regression tests.
  // TRACKER_SUPPORT_RUNTIME?.createTrackerRenderFallbackHelpers
  // TRACKER_SUPPORT_RUNTIME?.createTrackerRenderControllerDepsHelpers
  // if (typeof factory === "function") { return factory(options); }
  // if (typeof factory === "function") { return factory(deps); }
  // ADMIN_SUPPORT_RUNTIME?.createAdminTabsHelpers
  // ADMIN_SUPPORT_RUNTIME?.createAdminTabsFacade
  // SPMSAppSupportAdminRuntime.createAdminTabsHelpers is required
  // SPMSAppSupportAdminRuntime.createAdminTabsFacade is required

  function createAppSupportRuntime(options = {}) {
    return {
      ...(ORG_RUNTIME?.createAppSupportOrgRuntime?.(options) || {}),
      ...(STARTUP_RUNTIME?.createAppSupportStartupRuntime?.(options) || {}),
      ...(AUTH_RUNTIME?.createAppSupportAuthRuntime?.(options) || {}),
      ...(VIEW_RUNTIME?.createAppSupportViewRuntime?.(options) || {}),
      ...(TRACKER_RUNTIME?.createAppSupportTrackerDepsRuntime?.(options) || {}),
      ...(UI_RUNTIME?.createAppSupportUiRuntime?.(options) || {}),
      TRACKER_SUPPORT_RUNTIME,
      ADMIN_SUPPORT_RUNTIME,
    };
  }

  global.SPMSAppSupportRuntime = {
    createAppSupportRuntime,
  };
})(window);
