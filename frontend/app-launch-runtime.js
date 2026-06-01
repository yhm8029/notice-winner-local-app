(function attachAppLaunchRuntime(global) {
  const runtime = global.SPMSAppLaunchRuntimeCore;
  if (!runtime || typeof runtime.createAppLaunchRuntime !== "function") {
    throw new Error("SPMSAppLaunchRuntimeCore.createAppLaunchRuntime is required before app.js loads");
  }

  global.SPMSAppLaunchRuntime = {
    createAppLaunchRuntime: runtime.createAppLaunchRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
