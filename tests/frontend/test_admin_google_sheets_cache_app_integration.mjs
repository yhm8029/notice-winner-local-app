import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const bootstrapRuntimePath = path.resolve(__dirname, "../../frontend/bootstrap-runtime.js");
const homeBootstrapRuntimePath = path.resolve(__dirname, "../../frontend/home-bootstrap-runtime.js");
const appCoreRuntimePath = path.resolve(__dirname, "../../frontend/app-core-runtime.js");
const appSupportTrackerRuntimePath = path.resolve(__dirname, "../../frontend/app-support-tracker-runtime.js");
const appSupportAdminRuntimePath = path.resolve(__dirname, "../../frontend/app-support-admin-runtime.js");
const appSupportOrgRuntimePath = path.resolve(__dirname, "../../frontend/app-support-org-runtime.js");
const appSupportStartupRuntimePath = path.resolve(__dirname, "../../frontend/app-support-startup-runtime.js");
const appSupportAuthRuntimePath = path.resolve(__dirname, "../../frontend/app-support-auth-runtime.js");
const appSupportViewRuntimePath = path.resolve(__dirname, "../../frontend/app-support-view-runtime.js");
const appSupportTrackerDepsRuntimePath = path.resolve(__dirname, "../../frontend/app-support-tracker-deps-runtime.js");
const appSupportUiRuntimePath = path.resolve(__dirname, "../../frontend/app-support-ui-runtime.js");
const appSupportRuntimePath = path.resolve(__dirname, "../../frontend/app-support-runtime.js");
const appShellRuntimePath = path.resolve(__dirname, "../../frontend/app-shell-runtime.js");
const appBootstrapBridgePath = path.resolve(__dirname, "../../frontend/app-bootstrap-bridge.js");
const appControllerWiringAuthRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-auth-runtime.js");
const appControllerWiringRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-runtime.js");
const appRuntimeBodyRuntimePath = path.resolve(__dirname, "../../frontend/app-runtime-body-runtime.js");
const appRuntimeBodyControllerRuntimePath = path.resolve(__dirname, "../../frontend/app-runtime-body-controller-runtime.js");
const appRuntimeBodyConsoleRuntimePath = path.resolve(__dirname, "../../frontend/app-runtime-body-console-runtime.js");
const appRuntimeBodyAdminSalesRuntimePath = path.resolve(__dirname, "../../frontend/app-runtime-body-admin-sales-runtime.js");
const uiModeControllerPath = path.resolve(__dirname, "../../frontend/ui-mode-controller.js");
const adminTabsRuntimePath = path.resolve(__dirname, "../../frontend/admin-tabs-runtime.js");
const adminRuntimePath = path.resolve(__dirname, "../../frontend/admin-google-sheets-runtime.js");
const appAdminStateRuntimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-state-runtime.js");
const appAdminRuntimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-runtime.js");
const adminGoogleSheetsControllerPath = path.resolve(__dirname, "../../frontend/admin-google-sheets-controller.js");

function loadAdminGoogleSheetsRuntime() {
  const source = fs.readFileSync(adminRuntimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: adminRuntimePath });
  return window.SPMSAdminGoogleSheetsRuntime;
}

function loadBootstrapRuntime(window, context) {
  const source = fs.readFileSync(bootstrapRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: bootstrapRuntimePath });
  assert.ok(window.SPMSBootstrapRuntime, "expected bootstrap runtime to load before app.js");
}

function loadHomeBootstrapRuntime(window, context) {
  const source = fs.readFileSync(homeBootstrapRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: homeBootstrapRuntimePath });
  assert.ok(window.SPMSHomeBootstrapRuntime, "expected home bootstrap runtime to load before app.js");
}

function loadAppBootstrapBridge(window, context) {
  const source = fs.readFileSync(appBootstrapBridgePath, "utf8")
    .replace("export function createAppBootstrapBridge", "function createAppBootstrapBridge");
  vm.runInContext(source, context, { filename: appBootstrapBridgePath });
  assert.equal(typeof window.APP_BOOTSTRAP_BRIDGE?.createAppBootstrapBridge, "function");
}

function loadAppCoreRuntime(window, context) {
  const source = fs.readFileSync(appCoreRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appCoreRuntimePath });
  assert.equal(typeof window.createAppCoreRuntime, "function", "expected app-core runtime to load before app.js");
}

function loadAppSupportRuntime(window, context) {
  const trackerSource = fs.readFileSync(appSupportTrackerRuntimePath, "utf8");
  vm.runInContext(trackerSource, context, { filename: appSupportTrackerRuntimePath });
  assert.ok(window.SPMSAppSupportTrackerRuntime, "expected app-support tracker runtime to load before app.js");
  const adminSource = fs.readFileSync(appSupportAdminRuntimePath, "utf8");
  vm.runInContext(adminSource, context, { filename: appSupportAdminRuntimePath });
  assert.ok(window.SPMSAppSupportAdminRuntime, "expected app-support admin runtime to load before app.js");
  const orgSource = fs.readFileSync(appSupportOrgRuntimePath, "utf8");
  vm.runInContext(orgSource, context, { filename: appSupportOrgRuntimePath });
  assert.ok(window.SPMSAppSupportOrgRuntime, "expected app-support org runtime to load before app.js");
  const startupSource = fs.readFileSync(appSupportStartupRuntimePath, "utf8");
  vm.runInContext(startupSource, context, { filename: appSupportStartupRuntimePath });
  assert.ok(window.SPMSAppSupportStartupRuntime, "expected app-support startup runtime to load before app.js");
  const authSource = fs.readFileSync(appSupportAuthRuntimePath, "utf8");
  vm.runInContext(authSource, context, { filename: appSupportAuthRuntimePath });
  assert.ok(window.SPMSAppSupportAuthRuntime, "expected app-support auth runtime to load before app.js");
  const viewSource = fs.readFileSync(appSupportViewRuntimePath, "utf8");
  vm.runInContext(viewSource, context, { filename: appSupportViewRuntimePath });
  assert.ok(window.SPMSAppSupportViewRuntime, "expected app-support view runtime to load before app.js");
  const trackerDepsSource = fs.readFileSync(appSupportTrackerDepsRuntimePath, "utf8");
  vm.runInContext(trackerDepsSource, context, { filename: appSupportTrackerDepsRuntimePath });
  assert.ok(window.SPMSAppSupportTrackerDepsRuntime, "expected app-support tracker deps runtime to load before app.js");
  const uiSource = fs.readFileSync(appSupportUiRuntimePath, "utf8");
  vm.runInContext(uiSource, context, { filename: appSupportUiRuntimePath });
  assert.ok(window.SPMSAppSupportUiRuntime, "expected app-support ui runtime to load before app.js");
  const source = fs.readFileSync(appSupportRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appSupportRuntimePath });
  assert.ok(window.SPMSAppSupportRuntime, "expected app-support runtime to load before app.js");
}

function loadAppRuntimeBodyRuntimes(window, context) {
  for (const runtimePath of [appRuntimeBodyRuntimePath, appRuntimeBodyControllerRuntimePath, appRuntimeBodyConsoleRuntimePath, appRuntimeBodyAdminSalesRuntimePath]) {
    vm.runInContext(fs.readFileSync(runtimePath, "utf8"), context, { filename: runtimePath });
  }
}

function loadAppControllerWiringAuthRuntime(window, context) {
  const source = fs.readFileSync(appControllerWiringAuthRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appControllerWiringAuthRuntimePath });
  assert.ok(window.SPMSAppControllerWiringAuthRuntime, "expected app controller wiring auth runtime to load before app.js");
}

function loadAppControllerWiringRuntime(window, context) {
  const source = fs.readFileSync(appControllerWiringRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appControllerWiringRuntimePath });
  assert.ok(window.SPMSAppControllerWiringRuntime, "expected app controller wiring runtime to load before app.js");
}

function loadAppShellRuntime(window, context) {
  const source = fs.readFileSync(appShellRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appShellRuntimePath });
  assert.ok(window.SPMSAppShellRuntime, "expected app-shell runtime to load before app.js");
}

function loadUiModeController(window, context) {
  const source = fs.readFileSync(uiModeControllerPath, "utf8");
  vm.runInContext(source, context, { filename: uiModeControllerPath });
  assert.ok(window.SPMSUiModeController, "expected ui mode controller to load before app.js");
}

function loadAdminTabsRuntime(window, context) {
  const source = fs.readFileSync(adminTabsRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: adminTabsRuntimePath });
  assert.ok(window.SPMSAdminTabsRuntime, "expected admin tabs runtime to load before app.js");
}

function loadAppAdminGoogleSheetsRuntime(window, context) {
  const stateSource = fs.readFileSync(appAdminStateRuntimePath, "utf8");
  vm.runInContext(stateSource, context, { filename: appAdminStateRuntimePath });
  assert.ok(window.SPMSAppAdminGoogleSheetsStateRuntime, "expected app admin Google Sheets state runtime to load before app.js");
  const source = fs.readFileSync(appAdminRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appAdminRuntimePath });
  assert.ok(window.SPMSAppAdminGoogleSheetsRuntime, "expected app admin Google Sheets runtime to load before app.js");
}

function loadAdminGoogleSheetsController(window, context) {
  const source = fs.readFileSync(adminGoogleSheetsControllerPath, "utf8");
  vm.runInContext(source, context, { filename: adminGoogleSheetsControllerPath });
  assert.ok(window.SPMSAdminGoogleSheetsController, "expected admin Google Sheets controller to load before app.js");
}

function attachTrackerControllerStub(window) {
  window.TRACKER_CONTROLLER = {
    createTrackerController() {
      return {
        readTrackerFiltersFromControls() {},
        parseTrackerRegionFilter(region) {
          return String(region || "")
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean);
        },
        normalizeTrackerRegionFilter(region) {
          return String(region || "")
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean)
            .join(",");
        },
        renderTrackerRegionButtons() {
          return "";
        },
        renderTrackerTemplateStatus() {
          return "";
        },
        async loadTrackerTemplateStatus() {},
        async uploadTrackerTemplate() {},
        async resetTrackerTemplateOverride() {},
        async loadTrackerEntries() {},
        async loadTrackerMissingReport() {},
        async loadTrackerChangeEventUnreadCount() {},
        async loadTrackerChangeEvents() {},
        async loadBackfillConflicts() {},
        async markTrackerChangeEventsRead() {},
        async loadSelectedEntryChangeEvents() {},
      };
    },
  };
}

function createClassList() {
  const set = new Set();
  return {
    add: (...tokens) => tokens.forEach((token) => set.add(token)),
    remove: (...tokens) => tokens.forEach((token) => set.delete(token)),
    toggle: (token, force) => {
      const next = force === undefined ? !set.has(token) : Boolean(force);
      if (next) {
        set.add(token);
      } else {
        set.delete(token);
      }
      return next;
    },
    contains: (token) => set.has(token),
  };
}

function createStubElement() {
  const listeners = new Map();
  const attributes = new Map();
  return {
    classList: createClassList(),
    textContent: "",
    innerHTML: "",
    dataset: {},
    setAttribute: (name, value) => {
      attributes.set(String(name), String(value));
    },
    removeAttribute: (name) => {
      attributes.delete(String(name));
    },
    getAttribute: (name) => attributes.get(String(name)) || null,
    closest: () => null,
    addEventListener: (eventName, handler) => {
      const key = String(eventName || "");
      if (!key) {
        return;
      }
      const existing = listeners.get(key) || [];
      existing.push(handler);
      listeners.set(key, existing);
    },
  };
}

function makeJsonResponse(payload, { ok = true, status = 200, url = "http://local/api" } = {}) {
  return {
    ok,
    status,
    statusText: ok ? "OK" : "Bad Request",
    url,
    headers: {
      get: (key) => (String(key || "").toLowerCase() === "content-type" ? "application/json" : ""),
    },
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  };
}

function cloneJson(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function createStorage(initial = {}) {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  };
}

function createAdminGoogleSheetsCacheRuntime(snapshot) {
  let cachedSnapshot = cloneJson(snapshot);
  const calls = {
    read: 0,
    write: [],
    clear: 0,
  };

  return {
    calls,
    runtime: {
      readAdminGoogleSheetsCache: () => {
        calls.read += 1;
        return cloneJson(cachedSnapshot);
      },
      writeAdminGoogleSheetsCache: (nextValue) => {
        calls.write.push(cloneJson(nextValue));
        cachedSnapshot = cloneJson(nextValue);
        return true;
      },
      clearAdminGoogleSheetsCache: () => {
        calls.clear += 1;
        cachedSnapshot = null;
        return true;
      },
    },
  };
}

function loadAppForBehaviorTest({
  pathname = "/app/project-status",
  search = "",
  cacheSnapshot = null,
  payloadResponsesByKey = {},
} = {}) {
  const source = fs.readFileSync(appPath, "utf8");
  const runtime = loadAdminGoogleSheetsRuntime();
  const cacheHarness = createAdminGoogleSheetsCacheRuntime(cacheSnapshot);

  const elements = {
    "#flash-message": createStubElement(),
    "#admin-embed-panel": createStubElement(),
    "#admin-embed-title": createStubElement(),
    "#admin-embed-subtitle": createStubElement(),
    "#admin-google-sheets-sync-feedback": createStubElement(),
    "#admin-google-sheet-status": createStubElement(),
    "#admin-google-sheet-table": createStubElement(),
    "#admin-embed-empty": createStubElement(),
    "#admin-top-nav-list": createStubElement(),
    "#admin-google-sheets-sync-button": createStubElement(),
    ".layout-grid": createStubElement(),
    ".hero-copy": createStubElement(),
    ".hero": createStubElement(),
  };

  const document = {
    querySelector: (selector) => elements[selector] || null,
    querySelectorAll: () => [],
  };

  const storage = createStorage();
  const bootstrapDeferredQueue = [];
  let bootstrapRequestCount = 0;
  let payloadRequestCount = 0;
  const payloadRequestUrls = [];

  const fetch = (requestPath) => {
    const url = String(requestPath || "");
    if (url.startsWith("/api/admin/google-sheets/bootstrap")) {
      bootstrapRequestCount += 1;
      return new Promise((resolve, reject) => {
        bootstrapDeferredQueue.push({ resolve, reject });
      });
    }
    if (url.startsWith("/api/admin/google-sheets/sheets/")) {
      payloadRequestCount += 1;
      payloadRequestUrls.push(url);
      const sheetKey = decodeURIComponent(url.split("/").at(-1) || "");
      return Promise.resolve(makeJsonResponse(
        payloadResponsesByKey[sheetKey] || { headers: ["Name"], rows: [["Live Alice"]] },
        { url: `http://local${url}` },
      ));
    }
    return Promise.resolve(makeJsonResponse({ ok: false }, { ok: false, status: 404, url: `http://local${url}` }));
  };

  const window = {
    __SPMS_TEST_MODE__: true,
    __SPMS_TEST_MINIMAL_UI__: true,
    __SPMS_DISABLE_AUTO_BOOT__: true,
    SPMSAdminGoogleSheetsRuntime: runtime,
    SPMSAdminGoogleSheetsCacheRuntime: cacheHarness.runtime,
    localStorage: storage,
    location: {
      pathname,
      search,
      hash: "",
    },
    history: {
      pushState: (_state, _title, url) => {
        const parsed = new URL(String(url), "http://local");
        window.location.pathname = parsed.pathname;
        window.location.search = parsed.search;
      },
      replaceState: (_state, _title, url) => {
        const parsed = new URL(String(url), "http://local");
        window.location.pathname = parsed.pathname;
        window.location.search = parsed.search;
      },
    },
    addEventListener: () => {},
    setTimeout,
    clearTimeout,
    FormData: class FormData {},
  };
  attachTrackerControllerStub(window);

  const context = vm.createContext({
    window,
    document,
    fetch,
    console,
    URL,
    URLSearchParams,
    AbortController,
    FormData: window.FormData,
    setTimeout,
    clearTimeout,
  });

  loadBootstrapRuntime(window, context);
  loadHomeBootstrapRuntime(window, context);
  loadAppBootstrapBridge(window, context);
  loadAppShellRuntime(window, context);
  loadAppCoreRuntime(window, context);
  loadAppSupportRuntime(window, context);
  loadAppControllerWiringAuthRuntime(window, context);
  loadAppRuntimeBodyRuntimes(window, context);
  loadAppControllerWiringRuntime(window, context);
  loadUiModeController(window, context);
  loadAdminTabsRuntime(window, context);
  loadAppAdminGoogleSheetsRuntime(window, context);
  loadAdminGoogleSheetsController(window, context);
  vm.runInContext(source, context, { filename: appPath });

  const hooks = window.__SPMS_TEST_HOOKS__;
  assert.ok(hooks, "expected app.js to expose __SPMS_TEST_HOOKS__ in test mode");

  return {
    hooks,
    window,
    elements,
    cacheCalls: cacheHarness.calls,
    flushUi: () => new Promise((resolve) => setTimeout(resolve, 0)),
    getRequestCounts: () => ({
      bootstrapRequestCount,
      payloadRequestCount,
    }),
    getPayloadRequestUrls: () => payloadRequestUrls.slice(),
    resolveBootstrap: (payload) => {
      const deferred = bootstrapDeferredQueue.shift() || null;
      assert.ok(deferred, "expected bootstrap fetch to be pending");
      deferred.resolve(makeJsonResponse(payload, { url: "http://local/api/admin/google-sheets/bootstrap" }));
    },
    rejectBootstrap: (error) => {
      const deferred = bootstrapDeferredQueue.shift() || null;
      assert.ok(deferred, "expected bootstrap fetch to be pending");
      deferred.reject(error instanceof Error ? error : new Error(String(error || "bootstrap failed")));
    },
  };
}

function authorizeHarness(harness, { role = "org_admin" } = {}) {
  harness.hooks.state.auth.checking = false;
  harness.hooks.state.auth.enabled = true;
  harness.hooks.state.auth.authenticated = true;
  harness.hooks.state.auth.authorized = true;
  harness.hooks.state.auth.user = { role };
}

function renderProtectedAdminSheet(harness, { role = "org_admin" } = {}) {
  authorizeHarness(harness, { role });
  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();
}

function buildCachedSnapshot() {
  return {
    savedAt: 1713430800000,
    bootstrap: {
      sync_status: "ready",
      tabs: {
        "sheet-11": { key: "sheet-11", sheet_order: 1, raw_title: "Sheet One", sheet_id: 11 },
        "sheet-22": { key: "sheet-22", sheet_order: 2, raw_title: "Sheet Two", sheet_id: 22 },
      },
    },
    payloadsByKey: {
      "sheet-11": {
        key: "sheet-11",
        headers: ["Name"],
        rows: [["Cached Inactive"]],
      },
      "sheet-22": {
        key: "sheet-22",
        headers: ["Name"],
        rows: [["Cached Active"]],
      },
    },
  };
}

function buildPartialCachedSnapshotWithoutActivePayload() {
  return {
    savedAt: 1713430800000,
    bootstrap: {
      sync_status: "ready",
      tabs: {
        "sheet-11": { key: "sheet-11", sheet_order: 1, raw_title: "Sheet One", sheet_id: 11 },
        "sheet-22": { key: "sheet-22", sheet_order: 2, raw_title: "Sheet Two", sheet_id: 22 },
      },
    },
    payloadsByKey: {
      "sheet-11": {
        key: "sheet-11",
        headers: ["Name"],
        rows: [["Cached Inactive"]],
      },
    },
  };
}

test("stale-first admin render shows cached active sheet immediately while one live bootstrap request starts", () => {
  const harness = loadAppForBehaviorTest({
    search: "?mode=admin&admin_tab=sheet-22",
    cacheSnapshot: buildCachedSnapshot(),
  });

  renderProtectedAdminSheet(harness);

  assert.equal(harness.cacheCalls.read >= 1, true);
  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
  assert.match(harness.elements["#admin-google-sheet-status"].innerHTML, /ready/i);
  assert.match(harness.elements["#admin-google-sheet-status"].innerHTML, /Sheet Two/);
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Active/);
  assert.doesNotMatch(harness.elements["#admin-google-sheet-table"].innerHTML, /Live Alice/);
});

test("stale-first user render keeps cached shared sheet visible without admin-only controls", () => {
  const harness = loadAppForBehaviorTest({
    search: "?admin_tab=sheet-22",
    cacheSnapshot: buildCachedSnapshot(),
  });

  renderProtectedAdminSheet(harness, { role: "org_member" });

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.cacheCalls.read >= 1, true);
  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });
  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /Sheet Two/);
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Active/);
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheets-sync-feedback"].textContent, "");
  assert.equal(harness.elements["#admin-google-sheet-status"].classList.contains("hidden"), true);
});

test("project-status in user mode hides the google sheets overview and keeps the SPMS hero visible", async () => {
  const harness = loadAppForBehaviorTest({
    search: "",
    cacheSnapshot: {
      savedAt: 1713430800000,
      bootstrap: {
        sync_status: "not_configured",
        tabs: {},
      },
      payloadsByKey: {},
    },
  });

  renderProtectedAdminSheet(harness, { role: "org_member" });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheet-status"].classList.contains("hidden"), true);
  assert.equal(harness.elements[".hero-copy"].classList.contains("hidden"), false);
});

test("project-status in user mode starts bootstrap without showing the loading overview", async () => {
  const harness = loadAppForBehaviorTest({
    search: "",
    cacheSnapshot: null,
  });

  renderProtectedAdminSheet(harness, { role: "org_member" });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-embed-empty"].classList.contains("hidden"), true);
});

test("project-status in user mode ignores stale synced cache snapshots with no tabs and refreshes live google sheets tabs without showing the overview", async () => {
  const harness = loadAppForBehaviorTest({
    search: "",
    cacheSnapshot: {
      savedAt: 1713430800000,
      bootstrap: {
        sync_status: "synced",
        tabs: {},
      },
      payloadsByKey: {},
    },
  });

  renderProtectedAdminSheet(harness, { role: "org_member" });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-embed-empty"].classList.contains("hidden"), true);

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { key: "sheet-22", sheet_order: 1, raw_title: "Sheet Two", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /Sheet Two/);
});

test("project-status in user mode keeps the google sheets panel hidden after bootstrap returns dynamic tabs", async () => {
  const harness = loadAppForBehaviorTest({
    search: "",
    cacheSnapshot: null,
  });

  renderProtectedAdminSheet(harness, { role: "org_member" });
  await harness.flushUi();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { key: "sheet-22", sheet_order: 1, raw_title: "Sheet Two", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheet-status"].classList.contains("hidden"), true);
  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /Sheet Two/);
});

test("stale-first bootstrap refresh only re-fetches the live active sheet payload instead of every cached payload", async () => {
  const harness = loadAppForBehaviorTest({
    search: "?mode=admin&admin_tab=sheet-22",
    cacheSnapshot: buildCachedSnapshot(),
    payloadResponsesByKey: {
      "sheet-22": {
        key: "sheet-22",
        headers: ["Name"],
        rows: [["Live Active"]],
      },
      "sheet-11": {
        key: "sheet-11",
        headers: ["Name"],
        rows: [["Live Inactive"]],
      },
    },
  });

  renderProtectedAdminSheet(harness);

  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Active/);
  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-11": { key: "sheet-11", sheet_order: 1, raw_title: "Sheet One", sheet_id: 11 },
      "sheet-22": { key: "sheet-22", sheet_order: 2, raw_title: "Sheet Two", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 1,
  });
  assert.deepEqual(harness.getPayloadRequestUrls(), [
    "/api/admin/google-sheets/sheets/sheet-22",
  ]);
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Live Active/);
  assert.doesNotMatch(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Active/);
});

test("partial stale-first cache startup only fetches the missing active sheet payload once across bootstrap refresh", async () => {
  const harness = loadAppForBehaviorTest({
    search: "?mode=admin&admin_tab=sheet-22",
    cacheSnapshot: buildPartialCachedSnapshotWithoutActivePayload(),
    payloadResponsesByKey: {
      "sheet-22": {
        key: "sheet-22",
        headers: ["Name"],
        rows: [["Live Active"]],
      },
    },
  });

  renderProtectedAdminSheet(harness);
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-11": { key: "sheet-11", sheet_order: 1, raw_title: "Sheet One", sheet_id: 11 },
      "sheet-22": { key: "sheet-22", sheet_order: 2, raw_title: "Sheet Two", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 1,
  });
  assert.deepEqual(harness.getPayloadRequestUrls(), [
    "/api/admin/google-sheets/sheets/sheet-22",
  ]);
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Live Active/);
});

test("stale-first bootstrap failure keeps the cached table visible after the live refresh fails", async () => {
  const harness = loadAppForBehaviorTest({
    search: "?mode=admin&admin_tab=sheet-22",
    cacheSnapshot: buildCachedSnapshot(),
  });

  renderProtectedAdminSheet(harness);

  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Active/);
  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.rejectBootstrap(new Error("bootstrap failed"));
  await harness.flushUi();

  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Active/);
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
  assert.equal(harness.elements["#admin-embed-empty"].classList.contains("hidden"), false);
  assert.equal(harness.elements["#admin-embed-empty"].textContent, "bootstrap failed");
});
