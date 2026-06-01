(function attachSPMSTrackerRenderFallbackRuntime(globalObject) {
  const entryRuntime = globalObject.SPMSTrackerRenderFallbackEntryRuntime || null;
  const boardRuntime = globalObject.SPMSTrackerRenderFallbackBoardRuntime || null;

  if (typeof entryRuntime?.buildTrackerEntryCardMarkupFallback !== "function") {
    throw new Error("SPMSTrackerRenderFallbackEntryRuntime is required before tracker-render-fallback-runtime.js loads");
  }
  if (typeof boardRuntime?.buildTrackerBoardMarkupFallback !== "function") {
    throw new Error("SPMSTrackerRenderFallbackBoardRuntime is required before tracker-render-fallback-runtime.js loads");
  }

  globalObject.SPMSTrackerRenderFallbackRuntime = {
    ...entryRuntime,
    ...boardRuntime,
  };
})(window);
