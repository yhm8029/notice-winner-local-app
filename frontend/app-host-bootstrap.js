(function attachAppHostBootstrap(global) {
  function bootstrapApp(options = {}) {
    const root = options.root && typeof options.root === "object" ? options.root : global;
    const window = options.window && typeof options.window === "object" ? options.window : root;

    const APP_RUNTIME_REGISTRY = window.SPMSAppRuntimeRegistry || null;
    if (typeof APP_RUNTIME_REGISTRY !== "object" || APP_RUNTIME_REGISTRY === null) {
      throw new Error("SPMSAppRuntimeRegistry is required before app.js loads");
    }
    const readAppRuntimeBindings = APP_RUNTIME_REGISTRY.readAppRuntimeBindings;
    if (typeof readAppRuntimeBindings !== "function") {
      throw new Error("SPMSAppRuntimeRegistry.readAppRuntimeBindings is required before app.js loads");
    }
    const appRuntimeBindings = readAppRuntimeBindings(window);

    const APP_RUNTIME_BOOTSTRAP = window.SPMSAppRuntimeBootstrap || null;
    if (typeof APP_RUNTIME_BOOTSTRAP !== "object" || APP_RUNTIME_BOOTSTRAP === null) {
      throw new Error("SPMSAppRuntimeBootstrap.createAppRuntimeBootstrap is required before app.js loads");
    }
    const createAppRuntimeBootstrap = APP_RUNTIME_BOOTSTRAP.createAppRuntimeBootstrap;
    if (typeof createAppRuntimeBootstrap !== "function") {
      throw new Error("SPMSAppRuntimeBootstrap.createAppRuntimeBootstrap is required before app.js loads");
    }

    const APP_LAUNCH_RUNTIME = window.SPMSAppLaunchRuntime || null;
    if (typeof APP_LAUNCH_RUNTIME !== "object" || APP_LAUNCH_RUNTIME === null) {
      throw new Error("SPMSAppLaunchRuntime.createAppLaunchRuntime is required before app.js loads");
    }
    const createAppLaunchRuntime = APP_LAUNCH_RUNTIME.createAppLaunchRuntime;
    if (typeof createAppLaunchRuntime !== "function") {
      throw new Error("SPMSAppLaunchRuntime.createAppLaunchRuntime is required before app.js loads");
    }

    const appRuntimeBootstrap = createAppRuntimeBootstrap({
      root,
      window,
      document: options.document,
      navigator: options.navigator,
      fetch: options.fetch,
      AbortController: options.AbortController,
      FormData: options.FormData,
      setTimeout: options.setTimeout,
      clearTimeout: options.clearTimeout,
      bootstrapRuntime: appRuntimeBindings.BOOTSTRAP_RUNTIME,
    });

    const appLaunchRuntime = createAppLaunchRuntime({
      root,
      window,
      document: options.document,
      navigator: options.navigator,
      FormData: options.FormData,
      appRuntimeBindings,
      appRuntimeBootstrap,
    });

    const {
      appViewBindings,
      launchApp,
    } = appLaunchRuntime;

    launchApp();

    return {
      appRuntimeBindings,
      appRuntimeBootstrap,
      appLaunchRuntime,
      appViewBindings,
      launchApp,
    };
  }

  global.SPMSAppHostBootstrap = {
    bootstrapApp,
  };
})(window);
