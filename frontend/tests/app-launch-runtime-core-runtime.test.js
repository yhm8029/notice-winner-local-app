const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime() {
  const runtimePath = path.join(__dirname, "..", "app-launch-runtime-core-runtime.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console, globalThis: window });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAppLaunchRuntimeCoreRuntime;
}

test("launch runtime core helper resolves runtime sources with startup bridge precedence and explicit runtime overrides", () => {
  const runtime = loadRuntime();
  const readRuntimeCalls = [];
  const readFactoryCalls = [];
  const root = {
    SPMSAppControllerCallRuntime: { from: "root-controller-call" },
    SPMSAppUiGlueRuntime: { from: "root-ui-glue" },
    SPMSAppConsoleDepsRuntime: { from: "root-console-deps" },
    SPMSAppBridgeRuntime: { from: "root-bridge" },
    SPMSAppStartupRuntime: { from: "root-startup" },
    SPMSAppViewBindingsRuntime: { from: "root-view-bindings" },
    SPMSAppControllerBootstrapRuntime: { from: "root-controller-bootstrap" },
    SPMSAppEntryRuntime: { from: "root-entry" },
  };
  const runtimeLookup = {
    APP_CONTROLLER_CALL_RUNTIME: { from: "startup-controller-call" },
    APP_UI_GLUE_RUNTIME: { from: "runtime-ui-glue" },
    APP_CONSOLE_DEPS_RUNTIME: { from: "startup-console-deps" },
    APP_BRIDGE_RUNTIME: { from: "runtime-bridge" },
    APP_STARTUP_RUNTIME: { from: "startup-runtime" },
    APP_VIEW_BINDINGS_RUNTIME: { from: "runtime-view-bindings" },
    APP_CONTROLLER_BOOTSTRAP_RUNTIME: { from: "startup-controller-bootstrap" },
    APP_ENTRY_RUNTIME: { from: "runtime-entry" },
  };
  const startupRuntimeFactory = () => "startup-runtime-factory";
  const viewBindingsFactory = () => "view-bindings-factory";
  const controllerBootstrapFactory = () => "controller-bootstrap-factory";
  const entryRuntimeFactory = () => "entry-runtime-factory";
  const controllerStateFactory = () => ({ created: true });

  const resolved = runtime.resolveAppLaunchRuntimeDeps({
    globalObject: root,
    options: {
      root,
      window: { location: { origin: "https://example.test" } },
      document: { name: "doc" },
      navigator: { userAgent: "ua" },
      FormData: function ExplicitFormData() {},
      startup: {
        bridgeFactories: {
          APP_CONTROLLER_CALL_RUNTIME: runtimeLookup.APP_CONTROLLER_CALL_RUNTIME,
          APP_CONSOLE_DEPS_RUNTIME: runtimeLookup.APP_CONSOLE_DEPS_RUNTIME,
          APP_STARTUP_RUNTIME: runtimeLookup.APP_STARTUP_RUNTIME,
          APP_CONTROLLER_BOOTSTRAP_RUNTIME: runtimeLookup.APP_CONTROLLER_BOOTSTRAP_RUNTIME,
        },
      },
      runtimes: {
        APP_UI_GLUE_RUNTIME: runtimeLookup.APP_UI_GLUE_RUNTIME,
        APP_BRIDGE_RUNTIME: runtimeLookup.APP_BRIDGE_RUNTIME,
        APP_VIEW_BINDINGS_RUNTIME: runtimeLookup.APP_VIEW_BINDINGS_RUNTIME,
        APP_ENTRY_RUNTIME: runtimeLookup.APP_ENTRY_RUNTIME,
      },
    },
    runtimeHelpers: {
      isObject: runtime.isObject,
      readRuntime(runtimeSources, runtimeRoot, runtimeKey, globalKey) {
        readRuntimeCalls.push({ runtimeSources, runtimeRoot, runtimeKey, globalKey });
        return runtimeSources[runtimeKey] || runtimeRoot[globalKey] || null;
      },
      readFactory(runtimeObject, factoryName) {
        readFactoryCalls.push({ runtimeObject, factoryName });
        if (factoryName === "createAppStartupRuntime") return startupRuntimeFactory;
        if (factoryName === "createAppViewBindings") return viewBindingsFactory;
        if (factoryName === "createAppControllerBootstrapRuntime") return controllerBootstrapFactory;
        if (factoryName === "createAppEntryRuntime") return entryRuntimeFactory;
        if (factoryName === "createAppControllerState") return controllerStateFactory;
        return null;
      },
    },
  });

  assert.equal(resolved.normalized.root, root);
  assert.equal(resolved.normalized.runtimeSources.APP_CONTROLLER_CALL_RUNTIME.from, "startup-controller-call");
  assert.equal(resolved.normalized.runtimeSources.APP_UI_GLUE_RUNTIME.from, "runtime-ui-glue");
  assert.equal(resolved.factories.createAppStartupRuntime, startupRuntimeFactory);
  assert.equal(resolved.factories.createAppViewBindings, viewBindingsFactory);
  assert.equal(resolved.factories.createAppControllerBootstrapRuntime, controllerBootstrapFactory);
  assert.equal(resolved.factories.createAppEntryRuntime, entryRuntimeFactory);
  assert.equal(resolved.factories.createAppControllerState, controllerStateFactory);
  assert.deepEqual(
    readRuntimeCalls.map(({ runtimeKey }) => runtimeKey),
    [
      "APP_CONTROLLER_CALL_RUNTIME",
      "APP_UI_GLUE_RUNTIME",
      "APP_CONSOLE_DEPS_RUNTIME",
      "APP_BRIDGE_RUNTIME",
      "APP_STARTUP_RUNTIME",
      "APP_VIEW_BINDINGS_RUNTIME",
      "APP_CONTROLLER_BOOTSTRAP_RUNTIME",
      "APP_ENTRY_RUNTIME",
    ],
  );
  assert.deepEqual(
    readFactoryCalls.map(({ factoryName }) => factoryName),
    [
      "createAppStartupRuntime",
      "createAppViewBindings",
      "createAppControllerBootstrapRuntime",
      "createAppEntryRuntime",
      "createAppControllerState",
    ],
  );
});

test("launch runtime core helper builds boot function from startup runtime delegates", async () => {
  const runtime = loadRuntime();
  const calls = [];
  const startupDom = { apiBaseLabel: { textContent: "" } };
  const startupWindow = { location: { origin: "https://origin.test" } };
  const startupState = { auth: { enabled: true, authenticated: true, authorized: true } };
  const boot = runtime.createAppLaunchBoot({
    startupDom,
    startupWindow,
    startupState,
    appStartupRuntime: {
      mountRuntimeEnhancements: () => calls.push("mountRuntimeEnhancements"),
      hydrateStateFromUrl: () => calls.push("hydrateStateFromUrl"),
      hydrateProjectRelatedPayloadCache: () => calls.push("hydrateProjectRelatedPayloadCache"),
      hydratePatchFieldOptions: () => calls.push("hydratePatchFieldOptions"),
      syncFilterControlsFromState: () => calls.push("syncFilterControlsFromState"),
      renderSyncMeta: () => calls.push("renderSyncMeta"),
      applyUiMode: () => calls.push("applyUiMode"),
      bindEvents: () => calls.push("bindEvents"),
      renderAuthUi: () => calls.push("renderAuthUi"),
      renderDashboard: (value) => calls.push(["renderDashboard", value]),
      renderReport: (value) => calls.push(["renderReport", value]),
      renderReportJob: (value) => calls.push(["renderReportJob", value]),
      importAuthSessionFromLocationHash: async () => calls.push("importAuthSessionFromLocationHash"),
      initializeAuthGate: async () => calls.push("initializeAuthGate"),
      ensureConsoleInitialized: async () => calls.push("ensureConsoleInitialized"),
    },
  });

  await boot();

  assert.equal(startupDom.apiBaseLabel.textContent, "https://origin.test");
  assert.deepEqual(calls, [
    "mountRuntimeEnhancements",
    "hydrateStateFromUrl",
    "hydrateProjectRelatedPayloadCache",
    "hydratePatchFieldOptions",
    "syncFilterControlsFromState",
    "renderSyncMeta",
    "applyUiMode",
    "bindEvents",
    "renderAuthUi",
    ["renderDashboard", null],
    ["renderReport", null],
    ["renderReportJob", null],
    "importAuthSessionFromLocationHash",
    "initializeAuthGate",
    "ensureConsoleInitialized",
  ]);
});
