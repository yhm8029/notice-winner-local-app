import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { readCombinedCssSource } from "./css-source.mjs";

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
const htmlPath = path.resolve(__dirname, "../../frontend/index.html");
const stylesPath = path.resolve(__dirname, "../../frontend/styles.css");
const adminTabsRuntimePath = path.resolve(__dirname, "../../frontend/admin-tabs-runtime.js");
const adminRuntimePath = path.resolve(__dirname, "../../frontend/admin-google-sheets-runtime.js");
const appAdminStateRuntimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-state-runtime.js");
const appAdminRuntimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-runtime.js");
const adminGoogleSheetsControllerPath = path.resolve(__dirname, "../../frontend/admin-google-sheets-controller.js");
const CANONICAL_URL_STATE_STORAGE_KEY = "notice-winner-pipeline-web.canonicalUrlState.v1";

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function readAppSupportRuntimeSource() {
  return fs.readFileSync(appSupportRuntimePath, "utf8");
}

function readAppSupportAdminRuntimeSource() {
  return fs.readFileSync(appSupportAdminRuntimePath, "utf8");
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

function readAppCoreRuntimeSource() {
  return fs.readFileSync(appCoreRuntimePath, "utf8");
}

function extractFunction(source, startSignature, nextSignature) {
  const start = source.indexOf(startSignature);
  assert.notEqual(start, -1, `missing ${startSignature}`);
  const end = nextSignature ? source.indexOf(nextSignature, start + startSignature.length) : -1;
  assert.notEqual(end, -1, `missing ${nextSignature}`);
  return source.slice(start, end);
}

function normalizeWhitespace(source) {
  return source.replace(/\s+/g, " ").trim();
}

function readAppShellRuntimeSource() {
  return fs.readFileSync(appShellRuntimePath, "utf8");
}

function loadAppCoreRuntime(window, context) {
  vm.runInContext(readAppCoreRuntimeSource(), context, { filename: appCoreRuntimePath });
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

function loadAppControllerWiringRuntime(window, context) {
  const source = fs.readFileSync(appControllerWiringRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appControllerWiringRuntimePath });
  assert.ok(window.SPMSAppControllerWiringRuntime, "expected app controller wiring runtime to load before app.js");
}

function loadAppControllerWiringAuthRuntime(window, context) {
  const source = fs.readFileSync(appControllerWiringAuthRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appControllerWiringAuthRuntimePath });
  assert.ok(window.SPMSAppControllerWiringAuthRuntime, "expected app controller wiring auth runtime to load before app.js");
}

function readUiModeControllerSource() {
  return fs.readFileSync(uiModeControllerPath, "utf8");
}

function loadUiModeController(window, context) {
  vm.runInContext(readUiModeControllerSource(), context, { filename: uiModeControllerPath });
  assert.ok(window.SPMSUiModeController, "expected ui mode controller to load before app.js");
}

function readAdminGoogleSheetsControllerSource() {
  return fs.readFileSync(adminGoogleSheetsControllerPath, "utf8");
}

function readHtmlSource() {
  return fs.readFileSync(htmlPath, "utf8");
}

function readStylesSource() {
  return readCombinedCssSource(stylesPath);
}

function loadAdminTabsRuntime(window, context) {
  const source = fs.readFileSync(adminTabsRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: adminTabsRuntimePath });
  assert.ok(window.SPMSAdminTabsRuntime, "expected admin tabs runtime to load before app.js");
}

function loadAdminGoogleSheetsRuntime() {
  const source = fs.readFileSync(adminRuntimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: adminRuntimePath });
  return window.SPMSAdminGoogleSheetsRuntime;
}

function loadAppShellRuntime(window, context) {
  const source = fs.readFileSync(appShellRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appShellRuntimePath });
  assert.ok(window.SPMSAppShellRuntime, "expected app-shell runtime to load before app.js");
}

function loadAppAdminGoogleSheetsRuntime(window, context) {
  const stateSource = fs.readFileSync(appAdminStateRuntimePath, "utf8");
  vm.runInContext(stateSource, context, { filename: appAdminStateRuntimePath });
  assert.ok(window.SPMSAppAdminGoogleSheetsStateRuntime, "expected app admin Google Sheets state runtime to load before app.js");
  const source = fs.readFileSync(appAdminRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appAdminRuntimePath });
  assert.ok(window.SPMSAppAdminGoogleSheetsRuntime, "expected app admin Google Sheets runtime to load before app.js");
}

function loadAppRuntimeBodyRuntimes(window, context) {
  for (const runtimePath of [appRuntimeBodyRuntimePath, appRuntimeBodyControllerRuntimePath, appRuntimeBodyConsoleRuntimePath, appRuntimeBodyAdminSalesRuntimePath]) {
    vm.runInContext(fs.readFileSync(runtimePath, "utf8"), context, { filename: runtimePath });
  }
  assert.ok(window.SPMSAppRuntimeBodyRuntime, "expected app runtime body runtime to load before app.js");
  assert.ok(window.SPMSAppRuntimeBodyControllerRuntime, "expected app runtime body controller runtime to load before app.js");
  assert.ok(window.SPMSAppRuntimeBodyConsoleRuntime, "expected app runtime body console runtime to load before app.js");
  assert.ok(window.SPMSAppRuntimeBodyAdminSalesRuntime, "expected app runtime body admin/sales runtime to load before app.js");
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
      if (next) set.add(token);
      else set.delete(token);
      return next;
    },
    contains: (token) => set.has(token),
  };
}

function createStubElement() {
  const listeners = new Map();
  return {
    classList: createClassList(),
    textContent: "",
    innerHTML: "",
    dataset: {},
    setAttribute: () => {},
    removeAttribute: () => {},
    closest: () => null,
    addEventListener: (eventName, handler) => {
      const key = String(eventName || "");
      if (!key) return;
      const existing = listeners.get(key) || [];
      existing.push(handler);
      listeners.set(key, existing);
    },
    dispatch: (eventName, event = {}) => {
      const handlers = listeners.get(String(eventName || "")) || [];
      for (const handler of handlers) {
        handler({
          preventDefault: () => {},
          ...event,
        });
      }
    },
    click: () => {
      const handlers = listeners.get("click") || [];
      for (const handler of handlers) {
        handler({ preventDefault: () => {} });
      }
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

function createClosestTarget(matchingSelectors, extra = {}) {
  const selectorSet = new Set(Array.isArray(matchingSelectors) ? matchingSelectors : [matchingSelectors]);
  return {
    value: "",
    checked: false,
    getAttribute: () => null,
    closest: (selector) => (selectorSet.has(String(selector || "")) ? createClosestTargetMatch(selector, extra) : null),
    ...extra,
  };
}

function createClosestTargetMatch(selector, extra = {}) {
  return {
    value: "",
    checked: false,
    getAttribute: (name) => {
      if (typeof extra.getAttribute === "function") {
        return extra.getAttribute(name, selector);
      }
      return extra.attributes?.[String(name || "")] ?? null;
    },
    closest: (nextSelector) => (String(nextSelector || "") === String(selector || "") ? createClosestTargetMatch(selector, extra) : null),
    ...extra,
  };
}

function loadAppForBehaviorTest({
  pathname,
  search = "",
  syncResponsePayload = null,
  sheetPayload = { headers: ["Name"], rows: [["Alice"]] },
} = {}) {
  const source = fs.readFileSync(appPath, "utf8");
  const runtime = loadAdminGoogleSheetsRuntime();

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
  };

  const document = {
    querySelector: (selector) => elements[selector] || null,
    querySelectorAll: () => [],
  };
  const sessionStorageMap = new Map();

  const window = {
    __SPMS_TEST_MODE__: true,
    __SPMS_TEST_MINIMAL_UI__: true,
    __SPMS_DISABLE_AUTO_BOOT__: true,
    SPMSAdminGoogleSheetsRuntime: runtime,
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
    sessionStorage: {
      getItem: (key) => sessionStorageMap.has(key) ? sessionStorageMap.get(key) : null,
      setItem: (key, value) => sessionStorageMap.set(key, String(value)),
      removeItem: (key) => sessionStorageMap.delete(key),
    },
    addEventListener: () => {},
    setTimeout,
    clearTimeout,
    FormData: class FormData {},
  };
  attachTrackerControllerStub(window);

  const bootstrapDeferredQueue = [];
  let bootstrapRequestCount = 0;
  let payloadRequestCount = 0;
  const payloadRequestUrls = [];
  let syncRequestCount = 0;
  const resolvedSyncPayload = syncResponsePayload || { started: true, sync_status: "queued" };
  const fetch = (requestPath) => {
    const url = String(requestPath || "");
    if (url.startsWith("/api/admin/google-sheets/bootstrap")) {
      bootstrapRequestCount += 1;
      return new Promise((resolve, reject) => {
        bootstrapDeferredQueue.push({ resolve, reject });
      });
    }
    if (url.startsWith("/api/admin/google-sheets/sync")) {
      syncRequestCount += 1;
      return Promise.resolve(makeJsonResponse(resolvedSyncPayload));
    }
    if (url.startsWith("/api/admin/google-sheets/sheets/")) {
      payloadRequestCount += 1;
      payloadRequestUrls.push(url);
      return Promise.resolve(makeJsonResponse(sheetPayload));
    }
    return Promise.resolve(makeJsonResponse({ ok: false }, { ok: false, status: 404 }));
  };

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
  loadAppControllerWiringRuntime(window, context);
  loadAppRuntimeBodyRuntimes(window, context);
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
    flushUi: () => new Promise((resolve) => setTimeout(resolve, 0)),
    getRequestCounts: () => ({
      bootstrapRequestCount,
      payloadRequestCount,
    }),
    getPayloadRequestUrls: () => payloadRequestUrls.slice(),
    getSyncRequestCount: () => syncRequestCount,
    getCanonicalUrlState: () => window.sessionStorage.getItem(CANONICAL_URL_STATE_STORAGE_KEY) || "",
    resolveBootstrap: (payload) => {
      const deferred = bootstrapDeferredQueue.shift() || null;
      assert.ok(deferred, "expected bootstrap fetch to be pending");
      deferred.resolve(makeJsonResponse(payload));
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

test("user mode org members default to the shared project-status shell", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/", search: "" });
  authorizeHarness(harness, { role: "org_member" });

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.pathname, "/");
  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });
});

test("user mode org members can open shared google sheets tabs without admin-only controls", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-22" });
  authorizeHarness(harness, { role: "org_member" });

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /Lost/);
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheets-sync-feedback"].textContent, "");
  assert.equal(harness.elements["#admin-embed-subtitle"].textContent, "");
});

test("user mode shared google sheets filters stay client-side and keep admin-only controls hidden", async () => {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/project-status",
    search: "?admin_tab=sheet-22",
    sheetPayload: {
      headers: ["Name"],
      rows: [["Alice"], ["Bob"]],
    },
  });
  authorizeHarness(harness, { role: "org_member" });

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheets-sync-feedback"].textContent, "");
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Alice/);
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Bob/);

  const before = harness.getRequestCounts();
  assert.deepEqual(before, {
    bootstrapRequestCount: 1,
    payloadRequestCount: 1,
  });

  harness.elements["#admin-google-sheet-table"].dispatch("click", {
    target: createClosestTarget("[data-admin-google-sheet-trigger-index]", {
      getAttribute: (name) => (name === "data-admin-google-sheet-trigger-index" ? "0" : null),
    }),
  });
  assert.equal(harness.hooks.getAdminGoogleSheetPopupState().open, true);

  harness.elements["#admin-google-sheet-table"].dispatch("input", {
    target: createClosestTarget("[data-admin-google-sheet-popup-search=\"1\"]", {
      value: "bo",
    }),
  });
  assert.equal(harness.hooks.getAdminGoogleSheetPopupState().searchDraft, "bo");

  harness.elements["#admin-google-sheet-table"].dispatch("change", {
    target: createClosestTarget("[data-admin-google-sheet-popup-select-all=\"1\"]", {
      checked: false,
    }),
  });
  assert.deepEqual(JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetPopupState().pendingSelectedValues)), ["Alice"]);

  harness.elements["#admin-google-sheet-table"].dispatch("input", {
    target: createClosestTarget("[data-admin-google-sheet-popup-search=\"1\"]", {
      value: "",
    }),
  });
  assert.equal(harness.hooks.getAdminGoogleSheetPopupState().searchDraft, "");

  harness.elements["#admin-google-sheet-table"].dispatch("change", {
    target: createClosestTarget("[data-admin-google-sheet-popup-value]", {
      checked: false,
      getAttribute: (name) => (name === "data-admin-google-sheet-popup-value" ? "Alice" : null),
    }),
  });
  assert.deepEqual(JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetPopupState().pendingSelectedValues)), []);

  harness.elements["#admin-google-sheet-table"].dispatch("change", {
    target: createClosestTarget("[data-admin-google-sheet-popup-value]", {
      checked: true,
      getAttribute: (name) => (name === "data-admin-google-sheet-popup-value" ? "Bob" : null),
    }),
  });
  assert.deepEqual(JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetPopupState().pendingSelectedValues)), ["Bob"]);

  harness.elements["#admin-google-sheet-table"].dispatch("click", {
    target: createClosestTarget("[data-admin-google-sheet-popup-action]", {
      getAttribute: (name) => (name === "data-admin-google-sheet-popup-action" ? "confirm" : null),
    }),
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), before);
  assert.equal(harness.hooks.getAdminGoogleSheetPopupState().open, false);
  assert.deepEqual(JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetsFilterState("sheet-22"))), {
    sort: null,
    columns: {
      0: { selectedValues: ["Bob"] },
    },
  });
  assert.doesNotMatch(harness.elements["#admin-google-sheet-table"].innerHTML, /Alice/);
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Bob/);
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheets-sync-feedback"].textContent, "");
});

test("admin shared google sheets links keep explicit admin mode in the url", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?mode=admin&admin_tab=sheet-22" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), false);
  assert.doesNotMatch(harness.elements["#admin-top-nav-list"].innerHTML, /mode=admin/);
  assert.match(harness.getCanonicalUrlState(), /mode=admin/);
});

test("admin tab state is wired through pathname hydration and query-backed URL sync", () => {
  const source = readAppSource();
  const bridgeSource = fs.readFileSync(appBootstrapBridgePath, "utf8");

  assert.match(source, /SPMSAdminTabsRuntime:\s*ADMIN_TABS_RUNTIME/);
  assert.match(source, /window\.SPMSAppShellRuntime/);
  assert.match(source, /adminTab/);
  assert.match(source, /window\.location\.pathname/);
  assert.match(source, /routePath/);
  assert.match(bridgeSource, /params\.get\("admin_tab"/);
  assert.match(source, /params\.set\("admin_tab"/);
});

test("admin tabs runtime owns the helper and cache logic", () => {
  const source = fs.readFileSync(adminTabsRuntimePath, "utf8");

  assert.match(source, /function normalizeAdminTab\(/);
  assert.match(source, /function resolveUiModeFromLocation\(/);
  assert.match(source, /function buildResolvedAdminGoogleSheetTabs\(/);
  assert.match(source, /function readAdminGoogleSheetsCacheSnapshot\(/);
  assert.match(source, /function hydrateAdminGoogleSheetsCacheOnFirstProtectedRender\(/);
  assert.match(source, /function persistAdminGoogleSheetsCache\(/);
  assert.match(source, /global\.SPMSAdminTabsRuntime/);
});

test("admin tab helpers in app.js are thin runtime delegates", () => {
  const source = readAppSource();
  assert.match(source, /APP_SUPPORT\.createAdminTabsFacade\(\{/);
  assert.match(source, /const \{\s*normalizeAdminTab,\s*normalizeLocationPath,\s*resolveLegacyAdminRoutePath,/s);
  assert.match(source, /renderAdminTopNavigation,\s*renderAdminEmbedPanel,\s*setAdminTab,/s);
  assert.doesNotMatch(source, /function normalizeAdminTab\(rawValue\) \{/);
  assert.doesNotMatch(source, /function resolveUiModeFromLocation\(pathname = window\.location\.pathname, search = window\.location\.search\) \{/);
  assert.doesNotMatch(source, /function hydrateAdminGoogleSheetsCacheOnFirstProtectedRender\(\) \{/);
  assert.doesNotMatch(source, /function persistAdminGoogleSheetsCache\(\) \{/);
});

test("admin navigation shell selectors exist in the app shell runtime", () => {
  const source = readAppShellRuntimeSource();

  assert.match(source, /adminHeaderBar: query\("#admin-header-bar"\)/);
  assert.match(source, /adminBrand: query\("#admin-brand"\)/);
  assert.match(source, /adminTopNav: query\("#admin-top-nav"\)/);
  assert.match(source, /adminTopNavList: query\("#admin-top-nav-list"\)/);
  assert.match(source, /adminEmbedPanel: query\("#admin-embed-panel"\)/);
  assert.match(source, /adminEmbedEmpty: query\("#admin-embed-empty"\)/);
  assert.match(source, /adminGoogleSheetStatus: query\("#admin-google-sheet-status"\)/);
  assert.match(source, /adminGoogleSheetTable: query\("#admin-google-sheet-table"\)/);
  assert.doesNotMatch(source, /adminEmbedFrame: query\("#admin-embed-frame"\)/);
});

test("admin tab render hooks and styles exist", () => {
  const appSource = readAppSource();
  const appSupportAdminRuntimeSource = readAppSupportAdminRuntimeSource();
  const uiModeControllerSource = readUiModeControllerSource();
  const stylesSource = readStylesSource();

  assert.match(appSource, /renderAdminTopNavigation,/);
  assert.match(appSource, /renderAdminEmbedPanel,/);
  assert.match(appSupportAdminRuntimeSource, /data-admin-tab/);
  assert.match(uiModeControllerSource, /adminHeaderBar/);
  assert.match(uiModeControllerSource, /heroCopy/);
  assert.match(uiModeControllerSource, /renderAdminTopNavigation/);
  assert.match(uiModeControllerSource, /renderAdminEmbedPanel/);
  assert.match(appSource, /pushState/);
  assert.match(stylesSource, /\.admin-top-nav/);
  assert.match(stylesSource, /\.admin-header-bar/);
  assert.match(stylesSource, /\.admin-brand/);
  assert.match(stylesSource, /\.admin-google-sheet-status-view/);
  assert.match(stylesSource, /\.admin-google-sheet-table-wrap/);
  assert.match(stylesSource, /\.admin-google-sheet-table/);
});

test("admin google sheets wrappers delegate to the runtime", () => {
  const source = readAppSource();
  const controllerSource = readAdminGoogleSheetsControllerSource();
  assert.match(source, /APP_SUPPORT\.createAdminTabsFacade\(\{/);
  assert.match(source, /bindAdminGoogleSheetTableInteractions,/);
  assert.match(source, /renderAdminGoogleSheetTable,/);
  assert.match(source, /renderAdminEmbedPanel,/);
  assert.match(source, /loadAdminGoogleSheetsBootstrap,/);
  assert.match(source, /loadAdminGoogleSheetPayload,/);
  assert.match(source, /scheduleAdminGoogleSheetsSyncFollowup,/);
  assert.match(source, /syncAdminGoogleSheets,/);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/bootstrap/);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/sheets\//);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/sync/);
  assert.match(controllerSource, /timeoutMs: 12000/);
  assert.match(controllerSource, /timeoutMs: 20000/);
  assert.match(controllerSource, /timeoutMs: 60000/);
  assert.match(controllerSource, /scheduleAdminGoogleSheetsSyncFollowup/);
});

test("admin google sheets sync action exists in markup and app wiring", () => {
  const appSource = readAppSource();
  const controllerSource = readAdminGoogleSheetsControllerSource();
  const appShellRuntimeSource = readAppShellRuntimeSource();

  assert.match(appShellRuntimeSource, /adminGoogleSheetsSyncButton: query\("#admin-google-sheets-sync-button"\)/);
  assert.match(appSource, /syncAdminGoogleSheets,/);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/sync/);
});

test("shared google sheets top nav clicks stay client-side through setAdminTab", () => {
  const appEventBindingsSource = fs.readFileSync(path.resolve(__dirname, "../../frontend/app-event-bindings.js"), "utf8");

  assert.match(appEventBindingsSource, /adminTopNavList\?\.addEventListener\("click"/);
  assert.match(appEventBindingsSource, /event\.preventDefault\(\)/);
  assert.match(appEventBindingsSource, /target\.closest\("\[data-admin-tab\]"\)/);
  assert.match(appEventBindingsSource, /setAdminTab\(/);
});

test("google sheet-backed admin tabs load dynamically and render via the runtime helpers", () => {
  const source = readAppSource();
  const controllerSource = readAdminGoogleSheetsControllerSource();

  assert.match(source, /SPMSAdminTabsRuntime:\s*ADMIN_TABS_RUNTIME/);
  assert.match(source, /ADMIN_TABS_RUNTIME/);
  assert.match(source, /SPMSAdminGoogleSheetsRuntime:\s*ADMIN_GOOGLE_SHEETS_RUNTIME/);
  assert.match(source, /window\.SPMSAppAdminGoogleSheetsRuntime/);
  assert.match(source, /ADMIN_GOOGLE_SHEETS_RUNTIME/);
  assert.match(source, /ADMIN_GOOGLE_SHEETS_APP_RUNTIME/);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/bootstrap/);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/sheets\//);
  assert.match(controllerSource, /\/api\/admin\/google-sheets\/sync/);
  assert.match(controllerSource, /buildAdminGoogleSheetTabs/);
  assert.match(source, /bindAdminGoogleSheetTableInteractions/);
  assert.match(source, /renderAdminEmbedPanel/);
});

test("legacy admin route aliases resolve to dynamic google sheets tabs after bootstrap", () => {
  const source = readAppSource();
  const appSupportAdminRuntimeSource = readAppSupportAdminRuntimeSource();

  assert.match(appSupportAdminRuntimeSource, /adminLegacyRoutePath/);
  assert.match(appSupportAdminRuntimeSource, /function maybeResolveLegacyAdminAliasToSheetTab\(/);
  assert.match(source, /window\.addEventListener\("popstate", \(\) => \{[\s\S]*maybeResolveLegacyAdminAliasToSheetTab/);
  assert.match(source, /\/app\/design-list/);
  assert.match(source, /\/app\/planned-orders/);
  assert.match(source, /\/app\/lost/);
  assert.match(source, /\/app\/agency-list/);
  assert.match(source, /LEGACY_ADMIN_ROUTE_ALIASES/);
  assert.match(source, /labelHint/);
});

test("legacy alias cold loads stay on the sheet-oriented screen and respect explicit user override", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/design-list", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.hooks.state.adminLegacyRoutePath, "/app/design-list");
  assert.equal(harness.window.location.pathname, "/");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);

  assert.equal(harness.hooks.state.adminGoogleSheetsBootstrapLoading, true);
  harness.hooks.setAdminTab("project-status", { historyMode: "replace" });
  assert.equal(harness.hooks.state.adminLegacyRoutePath, "");

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-1": { sheet_order: 1, raw_title: "설계리스트", sheet_id: 101 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.search.includes("admin_tab="), false);
});

test("legacy alias navigation resolves immediately when bootstrap is already loaded", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();

  const bootstrapPromise = harness.hooks.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-11": { sheet_order: 1, raw_title: "설계리스트", sheet_id: 11 },
      "sheet-22": { sheet_order: 2, raw_title: "LOST", display_title: "LOST", sheet_id: 22 },
    },
  });
  await bootstrapPromise;

  harness.window.location.pathname = "/app/lost";
  harness.window.location.search = "";
  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.maybeResolveLegacyAdminAliasToSheetTab({ historyMode: "replace" });

  assert.equal(harness.hooks.state.adminTab, "sheet-22");
  assert.equal(harness.window.location.search, "");
});

test("legacy /app/lost resolves when bootstrap returns normalized LOST tab titles", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/lost", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.hooks.state.adminLegacyRoutePath, "/app/lost");
  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "LOST", display_title: "LOST", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminLegacyRoutePath, "");
  assert.equal(harness.hooks.state.adminTab, "sheet-22");
  assert.equal(harness.window.location.search, "");
  assert.equal(harness.getRequestCounts().payloadRequestCount, 1);
});

test("mode toggles clear stale legacy alias intent before returning to project status", () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/design-list", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(typeof harness.hooks.toggleUiMode, "function");
  assert.equal(harness.hooks.state.adminLegacyRoutePath, "/app/design-list");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);

  harness.hooks.toggleUiMode();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.window.location.pathname, "/");
  assert.equal(harness.hooks.state.adminLegacyRoutePath, "");

  harness.hooks.toggleUiMode();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.pathname, "/");
  assert.equal(harness.window.location.search, "");
  assert.equal(harness.window.location.search, "");
  assert.equal(harness.hooks.state.adminLegacyRoutePath, "");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
});

test("project-status route stays in admin mode for authorized admins without mode query", () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "" });
  authorizeHarness(harness, { role: "org_admin" });

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.state.uiMode = "user";
  harness.hooks.syncUiModeFromLocation();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.hooks.state.adminTab, "project-status");
});

test("project-status trailing-slash route stays in admin mode for authorized admins without mode query", () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status/", search: "" });
  authorizeHarness(harness, { role: "org_admin" });

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.state.uiMode = "user";
  harness.hooks.syncUiModeFromLocation();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.hooks.state.adminTab, "project-status");
});

test("hydrateStateFromUrl keeps trailing-slash project-status routes in admin mode", () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status/", search: "" });
  authorizeHarness(harness, { role: "org_admin" });

  harness.hooks.hydrateStateFromUrl();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.hooks.state.adminTab, "project-status");
});

test("legacy alias resolution prefers exact matches over earlier substring matches", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/design-list", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.adminGoogleSheetsBootstrapLoading, true);
  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-10": { sheet_order: 1, raw_title: "설계리스트 백업", sheet_id: 10 },
      "sheet-20": { sheet_order: 2, raw_title: "설계리스트", sheet_id: 20 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "sheet-20");
  assert.equal(harness.window.location.search, "");
  assert.equal(harness.getRequestCounts().payloadRequestCount, 1);
});

test("unmatched legacy alias resolves out of pending sheet mode after bootstrap loads", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/design-list", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.adminLegacyRoutePath, "/app/design-list");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);

  assert.equal(harness.hooks.state.adminGoogleSheetsBootstrapLoading, true);
  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-99": { sheet_order: 1, raw_title: "other", sheet_id: 99 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminLegacyRoutePath, "");
  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.pathname, "/");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
});

test("bootstrap failure re-renders the pending sheet panel with an immediate error state", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/design-list", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.adminGoogleSheetsBootstrapLoading, true);
  harness.rejectBootstrap(new Error("bootstrap failed"));
  await harness.flushUi();

  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
  assert.equal(harness.elements["#admin-embed-empty"].classList.contains("hidden"), false);
  assert.equal(harness.elements["#admin-embed-empty"].textContent, "bootstrap failed");
  assert.doesNotMatch(harness.elements["#admin-google-sheet-status"].innerHTML, /loading/i);
  assert.match(harness.elements["#admin-google-sheet-status"].innerHTML, /failed|error/i);
});

test("invalid admin_tab cold loads wait for bootstrap validation before any sheet payload request", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-999" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "로스트", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.search.includes("admin_tab="), false);
  assert.equal(harness.getRequestCounts().payloadRequestCount, 0);
});

test("invalid sheet deep links restore the normal admin layout after falling back to project-status", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();

  harness.hooks.setAdminTab("sheet-999", { historyMode: "replace" });
  assert.equal(harness.window.location.search, "");
  assert.equal(harness.elements[".layout-grid"].classList.contains("hidden"), true);

  const bootstrapPromise = harness.hooks.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
  assert.equal(harness.getRequestCounts().bootstrapRequestCount, 1);

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await bootstrapPromise;
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.search.includes("admin_tab="), false);
  assert.equal(harness.elements[".layout-grid"].classList.contains("hidden"), false);
});

test("valid admin_tab cold loads stay pending when bootstrap is still initializing and has no tabs yet", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-22" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    sync_status: "initializing",
    tabs: {},
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "sheet-22");
  assert.equal(harness.window.location.search, "");
  assert.match(harness.getCanonicalUrlState(), /admin_tab=sheet-22/);
  assert.equal(harness.getRequestCounts().payloadRequestCount, 0);

  const refreshPromise = harness.hooks.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
  assert.equal(harness.getRequestCounts().bootstrapRequestCount, 2);

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await refreshPromise;
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "sheet-22");
  assert.equal(harness.window.location.search, "");
  assert.match(harness.getCanonicalUrlState(), /admin_tab=sheet-22/);
  assert.equal(harness.getRequestCounts().payloadRequestCount, 1);
});

test("google sheets bootstrap refresh re-fetches the active sheet payload", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-22" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 1,
  });

  const refreshPromise = harness.hooks.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
  assert.equal(harness.getRequestCounts().bootstrapRequestCount, 2);

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await refreshPromise;
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 2,
    payloadRequestCount: 2,
  });
});

test("bootstrap fallback to project-status clears stale google sheets popup draft state", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-22" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-22", 0);
  harness.hooks.setAdminGoogleSheetPopupSearch("los");
  harness.hooks.setAdminGoogleSheetPopupSort("desc");

  assert.deepEqual(JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetPopupState())), {
    open: true,
    sheetKey: "sheet-22",
    columnIndex: 0,
    searchDraft: "los",
    pendingSelectedValues: ["Alice"],
    pendingSortDirection: "desc",
  });

  const refreshPromise = harness.hooks.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-99": { sheet_order: 1, raw_title: "Replacement", sheet_id: 99 },
    },
  });
  await refreshPromise;
  await harness.flushUi();

  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.deepEqual(JSON.parse(JSON.stringify(harness.hooks.getAdminGoogleSheetPopupState())), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("admin google sheets requests stay gated until protected-data auth is allowed", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/design-list", search: "" });

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 0,
    payloadRequestCount: 0,
  });

  harness.hooks.state.auth.checking = false;
  harness.hooks.state.auth.enabled = true;
  harness.hooks.state.auth.authenticated = false;
  harness.hooks.state.auth.authorized = false;
  harness.hooks.renderAdminEmbedPanel();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 0,
    payloadRequestCount: 0,
  });

  harness.hooks.state.auth.checking = false;
  harness.hooks.state.auth.enabled = true;
  harness.hooks.state.auth.authenticated = true;
  harness.hooks.state.auth.authorized = true;
  harness.hooks.state.auth.user = { role: "org_admin" };
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.getRequestCounts().bootstrapRequestCount, 1);

  const payloadHarness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-22" });
  payloadHarness.hooks.state.adminGoogleSheetsBootstrap = { sync_status: "synced" };
  payloadHarness.hooks.state.adminGoogleSheetTabs = [
    { key: "sheet-22", label: "로스트", rawTitle: "로스트", sheetId: 22 },
  ];

  payloadHarness.hooks.hydrateStateFromUrl();
  payloadHarness.hooks.syncUiModeFromLocation();
  payloadHarness.hooks.renderAdminEmbedPanel();

  assert.deepEqual(payloadHarness.getRequestCounts(), {
    bootstrapRequestCount: 0,
    payloadRequestCount: 0,
  });

  payloadHarness.hooks.state.auth.checking = false;
  payloadHarness.hooks.state.auth.enabled = true;
  payloadHarness.hooks.state.auth.authenticated = true;
  payloadHarness.hooks.state.auth.authorized = true;
  payloadHarness.hooks.state.auth.user = { role: "org_admin" };
  payloadHarness.hooks.renderAdminEmbedPanel();

  assert.equal(payloadHarness.getRequestCounts().payloadRequestCount, 1);
});

test("manual google sheets sync button posts to sync endpoint and forces bootstrap/payload refresh", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?mode=admin&admin_tab=sheet-22" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 1,
  });
  assert.equal(harness.getSyncRequestCount(), 0);

  assert.equal(typeof harness.hooks.bindAdminGoogleSheetsActions, "function");
  harness.hooks.bindAdminGoogleSheetsActions();
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), false);

  harness.elements["#admin-google-sheets-sync-button"].click();
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 2,
    payloadRequestCount: 1,
  });
  assert.equal(harness.getSyncRequestCount(), 1);
  assert.match(harness.elements["#admin-google-sheets-sync-feedback"].textContent, /queued/);

  harness.resolveBootstrap({
    sync_status: "initializing",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.getRequestCounts().bootstrapRequestCount >= 2, true);
  assert.equal(harness.getRequestCounts().payloadRequestCount >= 2, true);
  assert.equal(harness.getSyncRequestCount(), 1);

  await new Promise((resolve) => setTimeout(resolve, 40));
  assert.equal(harness.getRequestCounts().bootstrapRequestCount >= 3, true);

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();
  assert.equal(harness.getRequestCounts().payloadRequestCount >= 3, true);
  assert.equal(harness.getSyncRequestCount(), 1);
});

test("manual google sheets sync surfaces already_running and still follows up with refresh retries", async () => {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/project-status",
    search: "?mode=admin&admin_tab=sheet-22",
    syncResponsePayload: { started: false, sync_status: "already_running" },
  });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  harness.hooks.bindAdminGoogleSheetsActions();
  harness.elements["#admin-google-sheets-sync-button"].click();
  await harness.flushUi();

  assert.equal(harness.getSyncRequestCount(), 1);
  assert.match(harness.elements["#admin-google-sheets-sync-feedback"].textContent, /already_running/);

  harness.resolveBootstrap({
    sync_status: "initializing",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  await new Promise((resolve) => setTimeout(resolve, 40));
  assert.equal(harness.getRequestCounts().bootstrapRequestCount >= 3, true);
});

test("force bootstrap refresh invalidates non-active cached sheet payloads so revisiting refetches", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?admin_tab=sheet-1" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-1": { sheet_order: 1, raw_title: "Sheet A", sheet_id: 1 },
      "sheet-2": { sheet_order: 2, raw_title: "Sheet B", sheet_id: 2 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.getRequestCounts().payloadRequestCount, 1);
  assert.equal(harness.getPayloadRequestUrls().filter((url) => url.includes("/sheets/sheet-1")).length, 1);

  harness.hooks.setAdminTab("sheet-2", { historyMode: "replace" });
  await harness.flushUi();
  assert.equal(harness.getRequestCounts().payloadRequestCount, 2);
  assert.equal(harness.getPayloadRequestUrls().filter((url) => url.includes("/sheets/sheet-2")).length, 1);

  harness.hooks.setAdminTab("sheet-1", { historyMode: "replace" });
  await harness.flushUi();
  assert.equal(harness.getPayloadRequestUrls().filter((url) => url.includes("/sheets/sheet-1")).length, 1);

  const refreshPromise = harness.hooks.loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-1": { sheet_order: 1, raw_title: "Sheet A", sheet_id: 1 },
      "sheet-2": { sheet_order: 2, raw_title: "Sheet B", sheet_id: 2 },
    },
  });
  await refreshPromise;
  await harness.flushUi();

  assert.equal(harness.getPayloadRequestUrls().filter((url) => url.includes("/sheets/sheet-1")).length >= 2, true);

  harness.hooks.setAdminTab("sheet-2", { historyMode: "replace" });
  await harness.flushUi();

  // The key assertion: after a force refresh, revisiting a previously viewed but inactive tab must refetch.
  assert.equal(harness.getPayloadRequestUrls().filter((url) => url.includes("/sheets/sheet-2")).length >= 2, true);
});

test("admin project-status mode preloads google sheets bootstrap so dynamic tabs appear", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?mode=admin" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    sync_status: "ready",
    tabs: {
      "sheet-11": { sheet_order: 1, raw_title: "설계리스트", sheet_id: 11 },
      "sheet-22": { sheet_order: 2, raw_title: "발주예정", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /설계리스트/);
  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /발주예정/);
});

test("admin project-status mode shows google sheets diagnostics when bootstrap is not configured and no tabs exist", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?mode=admin" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 0,
  });

  harness.resolveBootstrap({
    enabled: false,
    sync_status: "not_configured",
    tabs: {},
  });
  await harness.flushUi();

  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
  assert.match(harness.elements["#admin-embed-title"].textContent, /Google Sheets/i);
  assert.match(harness.elements["#admin-embed-empty"].textContent, /GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID/);
  assert.equal(harness.elements["#admin-google-sheet-table"].classList.contains("hidden"), true);
});

test("admin google sheets view refreshes with force bootstrap/payload refresh on production poll tick", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/project-status", search: "?mode=admin&admin_tab=sheet-22" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.renderAdminEmbedPanel();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 1,
    payloadRequestCount: 1,
  });
  assert.equal(harness.getSyncRequestCount(), 0);

  assert.equal(typeof harness.hooks.pollGeneralConsoleTick, "function");
  harness.hooks.pollGeneralConsoleTick();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 2,
    payloadRequestCount: 1,
  });
  assert.equal(harness.getSyncRequestCount(), 0);

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.deepEqual(harness.getRequestCounts(), {
    bootstrapRequestCount: 2,
    payloadRequestCount: 2,
  });
  assert.equal(harness.getSyncRequestCount(), 0);
});
