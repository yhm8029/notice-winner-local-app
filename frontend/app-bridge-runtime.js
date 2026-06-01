(function attachAppBridgeRuntime(global) {
  function createAppBridgeRuntime(options = {}) {
    const runtime = global.SPMSAppBridgeRuntimeCore;
    if (!runtime || typeof runtime.createAppBridgeRuntimeCore !== "function") {
      throw new Error("SPMSAppBridgeRuntimeCore.createAppBridgeRuntimeCore is required before app.js loads");
    }
    return runtime.createAppBridgeRuntimeCore(options);
  }

  global.SPMSAppBridgeRuntime = {
    createAppBridgeRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
