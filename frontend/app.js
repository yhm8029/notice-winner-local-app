(function loadAppRuntimeBody() {
  if (typeof window !== "undefined" && window.__SPMS_APP_RUNTIME_BODY__) {
    return;
  }
  if (typeof document === "undefined") {
    throw new Error("SPMS app runtime body is required before app.js loads");
  }
  const helperScript = document.createElement("script");
  helperScript.src = "/app/app-runtime-body-helpers.js?v=20260425a";
  helperScript.defer = false;
  helperScript.async = false;
  helperScript.dataset.spmsAppRuntimeBodyHelpers = "true";
  document.head.appendChild(helperScript);
  const script = document.createElement("script");
  script.src = "/app/app-runtime-body.js?v=20260602g";
  script.defer = false;
  script.async = false;
  script.dataset.spmsAppRuntimeBody = "true";
  script.onerror = () => {
    throw new Error("Failed to load /app/app-runtime-body.js");
  };
  document.head.appendChild(script);
})();
