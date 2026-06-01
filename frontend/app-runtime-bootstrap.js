(function attachAppRuntimeBootstrap(global) {
  function createAppRuntimeBootstrap(options = {}) {
    const root = options.root && typeof options.root === "object" ? options.root : global;
    let appStartupRuntime = null;

    function requireAppStartupRuntimeMethod(methodName) {
      const method = appStartupRuntime?.[methodName] || null;
      if (typeof method !== "function") {
        throw new Error(`appStartupRuntime.${methodName} is required before app startup runtime attaches`);
      }
      return method;
    }

    function refreshAuthSessionState(...args) {
      return requireAppStartupRuntimeMethod("refreshAuthSessionState")(...args);
    }

    function renderAuthUi(...args) {
      return requireAppStartupRuntimeMethod("renderAuthUi")(...args);
    }

    function attachAppStartupRuntime(nextAppStartupRuntime) {
      appStartupRuntime = nextAppStartupRuntime && typeof nextAppStartupRuntime === "object"
        ? nextAppStartupRuntime
        : null;
      return appStartupRuntime;
    }

    const APP_SHELL_RUNTIME = root.SPMSAppShellRuntime || null;
    if (typeof APP_SHELL_RUNTIME !== "object" || APP_SHELL_RUNTIME === null) {
      throw new Error("SPMSAppShellRuntime is required before app.js loads");
    }

    const {
      EDITABLE_FIELDS,
      RUN_TYPE_LABELS,
      TRACKER_REGION_OPTIONS,
      TRACKER_BOARD_COLUMNS,
      TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
      TRACKER_CHANGE_FIELD_LABELS,
      MEMBERSHIP_STATUS_OPTIONS,
      TRACKER_BOARD_TEXTAREA_FIELDS,
      AUTH_MODE_SIGN_IN,
      AUTH_MODE_SIGN_UP,
      AUTH_SESSION_HEARTBEAT_MS,
      PROJECT_RELATED_PREFETCH_LIMIT,
      TRACKER_DETAIL_PREFETCH_LIMIT,
      PROJECT_RELATED_READY_CACHE_TTL_MS,
      PROJECT_RELATED_SEED_CACHE_TTL_MS,
      PROJECT_RELATED_STORAGE_KEY,
      PROJECT_RELATED_STORAGE_MAX_ITEMS,
      SALES_OVERVIEW_STORAGE_KEY,
      HOME_BOOTSTRAP_STORAGE_KEY,
      createAppState,
      createAppDom,
    } = APP_SHELL_RUNTIME;

    const state = createAppState();
    const dom = createAppDom(options.document);

    const createAppCoreRuntime = root.createAppCoreRuntime;
    if (typeof createAppCoreRuntime !== "function") {
      throw new Error("SPMSAppCoreRuntime is required before app.js loads");
    }

    const APP_CORE_RUNTIME = createAppCoreRuntime({
      window: options.window,
      state,
      dom,
      document: options.document,
      navigator: options.navigator,
      fetch: options.fetch,
      AbortController: options.AbortController,
      FormData: options.FormData,
      setTimeout: options.setTimeout,
      clearTimeout: options.clearTimeout,
      refreshAuthSessionState,
      renderAuthUi,
    }) || null;
    if (!APP_CORE_RUNTIME) {
      throw new Error("SPMSAppCoreRuntime is required before app.js loads");
    }
    root.SPMSAppCoreRuntime = APP_CORE_RUNTIME;

    const APP_SUPPORT_RUNTIME = root.SPMSAppSupportRuntime || null;
    if (typeof APP_SUPPORT_RUNTIME !== "object" || APP_SUPPORT_RUNTIME === null) {
      throw new Error("SPMSAppSupportRuntime is required before app.js loads");
    }

    const APP_SUPPORT = APP_SUPPORT_RUNTIME.createAppSupportRuntime({
      state,
      bootstrapRuntime: options.bootstrapRuntime,
    }) || null;
    if (!APP_SUPPORT) {
      throw new Error("SPMSAppSupportRuntime.createAppSupportRuntime is required before app.js loads");
    }

    return {
      APP_SHELL_RUNTIME,
      state,
      dom,
      APP_CORE_RUNTIME,
      APP_SUPPORT,
      attachAppStartupRuntime,
      constants: {
        EDITABLE_FIELDS,
        RUN_TYPE_LABELS,
        TRACKER_REGION_OPTIONS,
        TRACKER_BOARD_COLUMNS,
        TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
        TRACKER_CHANGE_FIELD_LABELS,
        MEMBERSHIP_STATUS_OPTIONS,
        TRACKER_BOARD_TEXTAREA_FIELDS,
        AUTH_MODE_SIGN_IN,
        AUTH_MODE_SIGN_UP,
        AUTH_SESSION_HEARTBEAT_MS,
        PROJECT_RELATED_PREFETCH_LIMIT,
        TRACKER_DETAIL_PREFETCH_LIMIT,
        PROJECT_RELATED_READY_CACHE_TTL_MS,
        PROJECT_RELATED_SEED_CACHE_TTL_MS,
        PROJECT_RELATED_STORAGE_KEY,
        PROJECT_RELATED_STORAGE_MAX_ITEMS,
        SALES_OVERVIEW_STORAGE_KEY,
        HOME_BOOTSTRAP_STORAGE_KEY,
      },
      helpers: {
        api: APP_CORE_RUNTIME.api,
        flash: APP_CORE_RUNTIME.flash,
        setBusy: APP_CORE_RUNTIME.setBusy,
        metricCard: APP_CORE_RUNTIME.metricCard,
        statusBadge: APP_CORE_RUNTIME.statusBadge,
        progressPercent: APP_CORE_RUNTIME.progressPercent,
        formatJson: APP_CORE_RUNTIME.formatJson,
        formatDate: APP_CORE_RUNTIME.formatDate,
        formatKoreanDate: APP_CORE_RUNTIME.formatKoreanDate,
        formatBytes: APP_CORE_RUNTIME.formatBytes,
        truncate: APP_CORE_RUNTIME.truncate,
        clampPage: APP_CORE_RUNTIME.clampPage,
        escapeHtml: APP_CORE_RUNTIME.escapeHtml,
      },
    };
  }

  global.SPMSAppRuntimeBootstrap = {
    createAppRuntimeBootstrap,
  };
})(typeof window !== "undefined" ? window : globalThis);
