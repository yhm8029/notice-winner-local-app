(function attachAppControllerBootstrapRuntime(global) {
  function isObject(value) {
    return typeof value === "object" && value !== null;
  }

  function createAppControllerBootstrapRuntime(options = {}) {
    const root = isObject(options.root) ? options.root : global;
    const APP_CONTROLLER_CONTEXT_RUNTIME = options.APP_CONTROLLER_CONTEXT_RUNTIME || null;
    if (typeof APP_CONTROLLER_CONTEXT_RUNTIME !== "object" || APP_CONTROLLER_CONTEXT_RUNTIME === null) {
      throw new Error("SPMSAppControllerContextRuntime is required before app.js loads");
    }

    const APP_CONTROLLER_WIRING_RUNTIME = isObject(options.APP_CONTROLLER_WIRING_RUNTIME)
      ? options.APP_CONTROLLER_WIRING_RUNTIME
      : isObject(root?.SPMSAppControllerWiringRuntime)
        ? root.SPMSAppControllerWiringRuntime
        : isObject(global?.SPMSAppControllerWiringRuntime)
          ? global.SPMSAppControllerWiringRuntime
          : null;
    if (typeof APP_CONTROLLER_WIRING_RUNTIME?.createAppControllerWiringRuntime !== "function") {
      throw new Error("SPMSAppControllerWiringRuntime.createAppControllerWiringRuntime is required before app.js loads");
    }

    const createAppControllerDepsContext = APP_CONTROLLER_CONTEXT_RUNTIME.createAppControllerDepsContext;
    if (typeof createAppControllerDepsContext !== "function") {
      throw new Error("SPMSAppControllerContextRuntime.createAppControllerDepsContext is required before app.js loads");
    }

    const createAppControllerDepsBootstrap = APP_CONTROLLER_CONTEXT_RUNTIME.createAppControllerDepsBootstrap;
    if (typeof createAppControllerDepsBootstrap !== "function") {
      throw new Error("SPMSAppControllerContextRuntime.createAppControllerDepsBootstrap is required before app.js loads");
    }

    const createAppControllerWiringRuntime = APP_CONTROLLER_WIRING_RUNTIME.createAppControllerWiringRuntime;
    const appControllerWiringRuntime = createAppControllerWiringRuntime({
      helperSources: options.helperSources,
      helpers: options.helpers,
      bindingNames: options.bindingNames,
    });

    const appControllerDepsBootstrap = createAppControllerDepsBootstrap({
      createAppControllerDepsContext() {
        return createAppControllerDepsContext({
          locals: options.locals,
          coreRuntime: options.coreRuntime,
          shellRuntime: options.shellRuntime,
          runtimes: options.runtimes,
          bridges: options.bridges,
          helpers: appControllerWiringRuntime.helpers,
          dynamic: options.dynamic,
        });
      },
      initialDeps: options.APP_CONTROLLER_DEPS,
      root,
    });

    return {
      waitForAppControllerDepsReady: appControllerDepsBootstrap.waitForAppControllerDepsReady,
      ...appControllerDepsBootstrap.createBindings(appControllerWiringRuntime.bindingNames),
    };
  }

  global.SPMSAppControllerBootstrapRuntime = {
    createAppControllerBootstrapRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
