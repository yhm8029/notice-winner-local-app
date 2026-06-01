const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function createCallableProxy() {
  return new Proxy(function noop() {}, {
    apply() {
      return undefined;
    },
    get(target, prop) {
      if (prop === "then") {
        return undefined;
      }
      if (prop === Symbol.toStringTag) {
        return "Function";
      }
      if (prop in target) {
        return target[prop];
      }
      return createCallableProxy();
    },
  });
}

function createBridgeFactory() {
  return () => createCallableProxy();
}

function loadAppBridgeRuntime() {
  const root = path.join(__dirname, "..");
  const runtimeBindings = {
    APP_DOWNLOAD_BRIDGE: { createAppDownloadBridge: createBridgeFactory() },
    APP_CONSOLE_BRIDGE: { createAppConsoleBridge: createBridgeFactory() },
    APP_SALES_BRIDGE: { createAppSalesBridge: createBridgeFactory() },
    APP_ORG_ADMIN_BRIDGE: { createAppOrgAdminBridge: createBridgeFactory() },
    APP_RUN_REPORT_BRIDGE: { createAppRunReportBridge: createBridgeFactory() },
    APP_AUTH_BRIDGE: { createAppAuthBridge: createBridgeFactory() },
    APP_TRACKER_SUPPORT_BRIDGE: { createAppTrackerSupportBridge: createBridgeFactory() },
    APP_TRACKER_BRIDGE: { createAppTrackerBridge: createBridgeFactory() },
    APP_BOOTSTRAP_BRIDGE: { createAppBootstrapBridge: createBridgeFactory() },
    APP_PROJECT_RELATED_BRIDGE: { createAppProjectRelatedBridge: createBridgeFactory() },
    APP_SELECTED_ENTRY_BRIDGE: { createAppSelectedEntryBridge: createBridgeFactory() },
    APP_CONSOLE_DEPS_RUNTIME: { createAppConsoleDepsRuntime: createBridgeFactory() },
    APP_UI_GLUE_RUNTIME: { createAppUiGlueRuntime: createBridgeFactory() },
  };
  const context = vm.createContext({
    window: {},
    ...runtimeBindings,
  });

  const sources = [
    "app-bridge-runtime-helpers.js",
    "app-bridge-runtime-auth.js",
    "app-bridge-runtime-core.js",
    "app-bridge-runtime.js",
  ];

  for (const fileName of sources) {
    const source = fs.readFileSync(path.join(root, fileName), "utf8");
    vm.runInContext(source, context, { filename: path.join(root, fileName) });
  }

  return {
    runtime: context.window.SPMSAppBridgeRuntime,
    runtimeBindings,
  };
}

test("app bridge runtime remains loadable through the split helper/core facade", () => {
  const { runtime, runtimeBindings } = loadAppBridgeRuntime();

  assert.equal(typeof runtime.createAppBridgeRuntime, "function");

  const app = runtime.createAppBridgeRuntime({
    state: {},
    dom: {},
    window: {},
    document: {},
    BOOTSTRAP_RUNTIME: {},
    CONSOLE_DATA_RUNTIME: {},
    AUTH_SESSION_RUNTIME: {},
    SALES_RUNTIME: {},
    RUN_VIEW_RUNTIME: {},
    ORGANIZATION_ADMIN_RUNTIME: {},
    TRACKER_DIAGNOSTICS_RUNTIME: {},
    SELECTED_ENTRY_RUNTIME: {},
    ...runtimeBindings,
    AUTH_SESSION_HEARTBEAT_MS: 1000,
    SALES_OVERVIEW_STORAGE_KEY: "sales",
    HOME_BOOTSTRAP_STORAGE_KEY: "home",
    clampPage: (value) => value,
    api: () => Promise.resolve(),
    flash: () => {},
    callDownloadController: () => {},
    callConsolePanelsController: () => {},
    callSalesPanelController: () => {},
    callOrgAdminController: () => {},
    callRunPanelsController: () => {},
    callReportPanelsController: () => {},
    callAuthController: () => {},
    callAuthUiController: () => {},
    callRuntimeEnhancements: () => {},
    callAppEventBindings: () => {},
    callProjectRelatedController: () => {},
    callTrackerController: () => {},
    callTrackerDiagnosticsPanelController: () => {},
    callTrackerRenderController: () => {},
    callTrackerEntryActionsController: () => {},
    callSelectedEntryController: () => {},
    canUseAdminMode: () => false,
    hasCachedHomeBootstrapData: false,
    hasCachedSalesOverviewData: false,
    isMissingHomeBootstrapEndpointError: () => false,
    isMissingSalesOverviewEndpointError: () => false,
    getTrackerController: () => null,
    RUN_TYPE_LABELS: {},
    getVisibleSalesProjectIds: () => [],
    isActiveSalesClaim: () => false,
    isCurrentUserClaimOwner: () => false,
    mergeActiveSalesClaims: () => [],
    mergeOrganizationInvitations: () => [],
    replaceVisibleSalesClaims: () => [],
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderOrganizationAdminPanel: () => {},
    renderAuthUi: () => {},
    syncUiModeChrome: () => false,
    applyUiModeTransition: () => {},
  });

  assert.equal(typeof app.showDownloadProgressOverlay, "function");
  assert.equal(typeof app.loadVisibleSalesClaims, "function");
  assert.equal(typeof app.renderTrackerEntries, "function");
  assert.equal(typeof app.renderSelectedEntry, "function");
  assert.equal(typeof app.getConsoleBootstrapRuntimeDeps, "function");
});

test("app bridge auth section exposes auth bridge delegates directly", () => {
  const root = path.join(__dirname, "..");
  const context = vm.createContext({
    window: {},
    APP_AUTH_BRIDGE: { createAppAuthBridge: createBridgeFactory() },
  });

  for (const fileName of ["app-bridge-runtime-helpers.js", "app-bridge-runtime-auth.js"]) {
    const source = fs.readFileSync(path.join(root, fileName), "utf8");
    vm.runInContext(source, context, { filename: path.join(root, fileName) });
  }

  const section = context.window.SPMSAppBridgeRuntimeAuth.createAppAuthBridgeSection({
    APP_AUTH_BRIDGE: context.APP_AUTH_BRIDGE,
    callAuthController: () => {},
    callAuthUiController: () => {},
  });

  assert.equal(typeof section.appAuthBridge, "function");
  assert.equal(typeof section.renderAuthUi, "function");
  assert.equal(typeof section.applyUiModeTransition, "function");
});
