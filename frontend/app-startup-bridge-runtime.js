(function attachAppStartupBridgeRuntime(global) {
  function createAppStartupBridgeExports({ appControllerCallRuntime, appBridgeRuntime } = {}) {
    if (typeof appControllerCallRuntime !== "object" || appControllerCallRuntime === null) {
      throw new Error("SPMSAppControllerCallRuntime.createAppControllerCallRuntime is required before app.js loads");
    }
    if (typeof appBridgeRuntime !== "object" || appBridgeRuntime === null) {
      throw new Error("SPMSAppBridgeRuntime.createAppBridgeRuntime is required before app.js loads");
    }
    return {
      ...appControllerCallRuntime,
      ...appBridgeRuntime,
    };
  }

  global.SPMSAppStartupBridgeRuntime = {
    createAppStartupBridgeExports,
  };
})(typeof window !== "undefined" ? window : globalThis);
