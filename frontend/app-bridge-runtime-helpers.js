(function attachAppBridgeRuntimeHelpers(global) {
  function requireFactory(owner, key, message) {
    const factory = owner?.[key];
    if (typeof factory !== "function") {
      throw new Error(message);
    }
    return factory;
  }

  function requireBridge(factory, options, message) {
    const bridge = factory(options) || null;
    if (!bridge) {
      throw new Error(message);
    }
    return bridge;
  }

  function createRequiredBridge(owner, key, options, message) {
    return requireBridge(requireFactory(owner, key, message), options, message);
  }

  global.SPMSAppBridgeRuntimeHelpers = {
    requireFactory,
    requireBridge,
    createRequiredBridge,
  };
})(typeof window !== "undefined" ? window : globalThis);
