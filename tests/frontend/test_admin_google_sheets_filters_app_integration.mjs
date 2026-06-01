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
  const attributes = new Map();
  return {
    classList: createClassList(),
    textContent: "",
    innerHTML: "",
    dataset: {},
    value: "",
    checked: false,
    setAttribute: (name, value) => {
      const key = String(name || "");
      if (key) {
        attributes.set(key, String(value));
      }
    },
    getAttribute: (name) => attributes.get(String(name || "")) || null,
    removeAttribute: (name) => {
      attributes.delete(String(name || ""));
    },
    closest: () => null,
    querySelector: () => null,
    querySelectorAll: () => [],
    contains: () => false,
    append: () => {},
    insertBefore: () => {},
    addEventListener: (eventName, handler) => {
      const key = String(eventName || "");
      if (!key) {
        return;
      }
      const existing = listeners.get(key) || [];
      existing.push(handler);
      listeners.set(key, existing);
    },
    emit: (eventName, event = {}) => {
      const handlers = listeners.get(String(eventName || "")) || [];
      for (const handler of handlers) {
        handler({
          preventDefault: () => {},
          stopPropagation: () => {},
          ...event,
        });
      }
    },
  };
}

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

function loadAppForBehaviorTest({ pathname, search = "" } = {}) {
  const source = fs.readFileSync(appPath, "utf8");
  const runtime = loadAdminGoogleSheetsRuntime();
  class Element {}

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
    "#console-shell": createStubElement(),
    "#auth-session-actions": createStubElement(),
    ".layout-grid": createStubElement(),
  };
  elements["#admin-google-sheet-table"].contains = (target) => Boolean(target && target.__insideTable);

  const documentListeners = new Map();
  const windowListeners = new Map();

  const registerListener = (registry, eventName, handler) => {
    const key = String(eventName || "");
    if (!key) {
      return;
    }
    const existing = registry.get(key) || [];
    existing.push(handler);
    registry.set(key, existing);
  };

  const document = {
    body: {
      appendChild: () => {},
    },
    querySelector: (selector) => elements[selector] || null,
    querySelectorAll: () => [],
    createElement: () => createStubElement(),
    addEventListener: (eventName, handler) => registerListener(documentListeners, eventName, handler),
    emit: (eventName, event = {}) => {
      const handlers = documentListeners.get(String(eventName || "")) || [];
      for (const handler of handlers) {
        handler({
          preventDefault: () => {},
          stopPropagation: () => {},
          ...event,
        });
      }
    },
  };

  const window = {
    __SPMS_TEST_MODE__: true,
    __SPMS_TEST_MINIMAL_UI__: true,
    __SPMS_DISABLE_AUTO_BOOT__: true,
    SPMSAdminGoogleSheetsRuntime: runtime,
    TRACKER_DIAGNOSTICS_PANEL_CONTROLLER: {
      createTrackerDiagnosticsPanelController(options = {}) {
        return {
          focusTrackerChangePanel() {},
          bindTrackerChangeEventActions() {},
          bindBackfillConflictActions() {},
          setTrackerChangeBellPopoverOpen(open) {
            if (options.state && typeof options.state === "object") {
              options.state.trackerChangeBellPopoverOpen = Boolean(open);
            }
          },
          renderTrackerChangeBellPopover() {
            return "";
          },
          renderTrackerChangeEventsList() {
            return "";
          },
          renderTrackerChangeEventsPanel() {
            return "";
          },
          renderBackfillConflictsPanel() {
            return "";
          },
          renderTrackerChangeEventUnreadCount() {
            return "";
          },
          resolveBackfillConflict() {},
          renderTrackerContactResolutionSummary() {
            return "";
          },
          renderTrackerCleanupPreview() {
            return "";
          },
        };
      },
    },
    Element,
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
    addEventListener: (eventName, handler) => registerListener(windowListeners, eventName, handler),
    emit: (eventName, event = {}) => {
      const handlers = windowListeners.get(String(eventName || "")) || [];
      for (const handler of handlers) {
        handler({
          preventDefault: () => {},
          stopPropagation: () => {},
          ...event,
        });
      }
    },
    setTimeout,
    clearTimeout,
    FormData: class FormData {},
  };
  attachTrackerControllerStub(window);

  const fetch = () => Promise.resolve(makeJsonResponse({ ok: true }));

  const context = vm.createContext({
    window,
    document,
    fetch,
    console,
    URL,
    URLSearchParams,
    AbortController,
    Element,
    FormData: window.FormData,
    setTimeout,
    clearTimeout,
    formatDate: () => "",
    formatContactResolutionStatusLabel: () => "",
    formatContactResolutionReasonLabel: () => "",
    formatBackfillConflictResolutionLabel: () => "",
    getTrackerDiagnosticsScope: () => ({}),
    buildTrackerChangeEventsMarkup: () => "",
    buildTrackerChangeBellPopoverMarkup: () => "",
    buildBackfillConflictsMarkup: () => "",
    buildBackfillConflictsView: () => "",
    renderTrackerEntries: () => "",
    loadSelectedEntryDetail: () => {},
    focusTrackerChangeEntry: () => {},
    closeTrackerChangeModal: () => {},
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
  vm.runInContext(source, context, { filename: appPath });

  return {
    hooks: window.__SPMS_TEST_HOOKS__,
    runtime,
    document,
    window,
    elements,
    Element,
  };
}

function authorizeHarness(harness) {
  harness.hooks.state.auth.checking = false;
  harness.hooks.state.auth.enabled = true;
  harness.hooks.state.auth.authenticated = true;
  harness.hooks.state.auth.authorized = true;
  harness.hooks.state.auth.user = { role: "org_admin" };
}

function seedGoogleSheetHarness() {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/admin",
    search: "?mode=admin&admin_tab=sheet-1",
  });
  authorizeHarness(harness);

  const state = harness.hooks.state;
  state.uiMode = "admin";
  state.adminTab = "sheet-1";
  state.adminGoogleSheetsBootstrap = {
    sync_status: "ready",
    tabs: [
      { key: "sheet-1", display_title: "Design List", raw_title: "Design List", sheet_id: 1, sheet_order: 1 },
      { key: "sheet-2", display_title: "Planned Orders", raw_title: "Planned Orders", sheet_id: 2, sheet_order: 2 },
    ],
  };
  state.adminGoogleSheetTabs = harness.runtime.buildAdminGoogleSheetTabs(state.adminGoogleSheetsBootstrap);
  state.adminGoogleSheetPayloadByKey["sheet-1"] = {
    headers: ["Region"],
    rows: [["Alpha"], ["Beta"], ["Gamma"]],
  };
  state.adminGoogleSheetPayloadByKey["sheet-2"] = {
    headers: ["Region"],
    rows: [["Busan"], ["Daegu"]],
  };

  return harness;
}

function snapshot(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizeSelectionState(value) {
  const copy = snapshot(value);
  if (Array.isArray(copy?.pendingSelectedValues)) {
    copy.pendingSelectedValues = copy.pendingSelectedValues.slice().sort();
  }
  if (copy?.columns && typeof copy.columns === "object") {
    for (const column of Object.values(copy.columns)) {
      if (Array.isArray(column?.selectedValues)) {
        column.selectedValues = column.selectedValues.slice().sort();
      }
    }
  }
  return copy;
}

function createInteractiveTarget(attributeName, attributeValue, extra = {}) {
  const match = {
    ...extra,
    getAttribute: (name) => {
      const key = attributeName.replace(/^\[|\]$/g, "").split("=")[0];
      return String(name) === key ? String(attributeValue) : null;
    },
  };
  return {
    __insideTable: true,
    closest: (selector) => {
      if (selector === attributeName) {
        return match;
      }
      return null;
    },
    ...extra,
  };
}

test("admin google sheets keeps applied filter state isolated per sheet key", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.setAdminGoogleSheetsFilterState(
    "sheet-1",
    { sort: { columnIndex: 0, direction: "asc" }, columns: { 0: { selectedValues: ["Alpha"] } } },
    { render: false },
  );
  harness.hooks.setAdminGoogleSheetsFilterState(
    "sheet-2",
    { sort: null, columns: { 0: { selectedValues: ["Busan"] } } },
    { render: false },
  );

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: { columnIndex: 0, direction: "asc" },
    columns: { 0: { selectedValues: ["Alpha"] } },
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-2")), {
    sort: null,
    columns: { 0: { selectedValues: ["Busan"] } },
  });

  harness.hooks.setAdminGoogleSheetsFilterState(
    "sheet-1",
    { sort: null, columns: { 0: { selectedValues: ["Gamma"] } } },
    { render: false },
  );

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-2")), {
    sort: null,
    columns: { 0: { selectedValues: ["Busan"] } },
  });
});

test("admin google sheets popup draft commits only on confirm", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "",
    pendingSelectedValues: ["Alpha", "Beta", "Gamma"],
    pendingSortDirection: "",
  });

  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.setAdminGoogleSheetPopupSort("asc");

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });

  harness.hooks.confirmAdminGoogleSheetPopup();

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: { columnIndex: 0, direction: "asc" },
    columns: { 0: { selectedValues: ["Alpha", "Gamma"] } },
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("admin google sheets popup confirm preserves other column filters and other-column sort", () => {
  const harness = seedGoogleSheetHarness();
  const state = harness.hooks.state;
  state.adminGoogleSheetPayloadByKey["sheet-1"] = {
    headers: ["Region", "Type"],
    rows: [
      ["Alpha", "X"],
      ["Beta", "Y"],
      ["Gamma", "X"],
    ],
  };

  harness.hooks.setAdminGoogleSheetsFilterState(
    "sheet-1",
    {
      sort: { columnIndex: 1, direction: "desc" },
      columns: {
        0: { selectedValues: ["Alpha"] },
        1: { selectedValues: ["X"] },
      },
    },
    { render: false },
  );

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Alpha", false);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", true);
  harness.hooks.confirmAdminGoogleSheetPopup();

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: { columnIndex: 1, direction: "desc" },
    columns: {
      0: { selectedValues: ["Beta"] },
      1: { selectedValues: ["X"] },
    },
  });
});

test("admin google sheets popup confirm clears only the popup column sort when popup sort is blank", () => {
  const harness = seedGoogleSheetHarness();
  const state = harness.hooks.state;
  state.adminGoogleSheetPayloadByKey["sheet-1"] = {
    headers: ["Region", "Type"],
    rows: [
      ["Alpha", "X"],
      ["Beta", "Y"],
      ["Gamma", "X"],
    ],
  };

  harness.hooks.setAdminGoogleSheetsFilterState(
    "sheet-1",
    {
      sort: { columnIndex: 0, direction: "asc" },
      columns: {
        0: { selectedValues: ["Alpha", "Beta"] },
        1: { selectedValues: ["X"] },
      },
    },
    { render: false },
  );

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.setAdminGoogleSheetPopupSort("");
  harness.hooks.confirmAdminGoogleSheetPopup();

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {
      0: { selectedValues: ["Alpha", "Beta"] },
      1: { selectedValues: ["X"] },
    },
  });
});

test("admin google sheets popup draft is discarded on cancel", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Alpha", false);
  harness.hooks.setAdminGoogleSheetPopupSort("desc");

  harness.hooks.cancelAdminGoogleSheetPopup();

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("admin google sheets popup seeds from the applied selection", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.setAdminGoogleSheetsFilterState(
    "sheet-1",
    { sort: null, columns: { 0: { selectedValues: ["Beta"] } } },
    { render: false },
  );

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "",
    pendingSelectedValues: ["Beta"],
    pendingSortDirection: "",
  });
});

test("admin google sheets preserves the measured minimum height across filtered rerenders", () => {
  const harness = seedGoogleSheetHarness();
  const table = harness.elements["#admin-google-sheet-table"];
  let measuredHeight = 540;
  table.querySelector = (selector) => {
    if (selector !== ".admin-google-sheet-table-wrap") {
      return null;
    }
    return {
      offsetHeight: measuredHeight,
      getBoundingClientRect: () => ({ height: measuredHeight }),
    };
  };

  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 540);
  assert.match(table.innerHTML, /540px/);

  measuredHeight = 120;
  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Gamma", false);
  harness.hooks.confirmAdminGoogleSheetPopup();

  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 540);
  assert.match(table.innerHTML, /540px/);
});

test("admin google sheets keeps measured minimum heights isolated per sheet", () => {
  const harness = seedGoogleSheetHarness();
  const table = harness.elements["#admin-google-sheet-table"];
  let measuredHeight = 480;
  table.querySelector = (selector) => {
    if (selector !== ".admin-google-sheet-table-wrap") {
      return null;
    }
    return {
      offsetHeight: measuredHeight,
      getBoundingClientRect: () => ({ height: measuredHeight }),
    };
  };

  harness.hooks.renderAdminEmbedPanel();
  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 480);
  assert.match(table.innerHTML, /480px/);

  harness.hooks.state.adminTab = "sheet-2";
  measuredHeight = 320;
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 480);
  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-2"], 320);
  assert.match(table.innerHTML, /320px/);
});

test("admin google sheets table interaction bindings open, search, select visible values, sort, and confirm", () => {
  const harness = seedGoogleSheetHarness();
  const state = harness.hooks.state;
  state.adminGoogleSheetPayloadByKey["sheet-1"] = {
    headers: ["Region"],
    rows: [["Alpha"], ["Beta"], ["Gamma"], ["Delta"]],
  };

  harness.hooks.bindGlobalDismissalListeners();
  harness.hooks.renderAdminEmbedPanel();

  const triggerButton = createInteractiveTarget("[data-admin-google-sheet-trigger-index]", "0");

  harness.elements["#admin-google-sheet-table"].emit("click", {
    target: triggerButton,
    currentTarget: harness.elements["#admin-google-sheet-table"],
  });

  assert.deepEqual(normalizeSelectionState(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "",
    pendingSelectedValues: ["Alpha", "Beta", "Delta", "Gamma"],
    pendingSortDirection: "",
  });

  const searchInput = createInteractiveTarget("[data-admin-google-sheet-popup-search=\"1\"]", "1", {
    value: "et",
  });
  harness.elements["#admin-google-sheet-table"].emit("input", {
    target: searchInput,
    currentTarget: harness.elements["#admin-google-sheet-table"],
  });

  assert.equal(harness.hooks.getAdminGoogleSheetPopupState().searchDraft, "et");
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });

  const sortButton = createInteractiveTarget("[data-admin-google-sheet-popup-sort]", "asc");
  harness.elements["#admin-google-sheet-table"].emit("click", {
    target: sortButton,
    currentTarget: harness.elements["#admin-google-sheet-table"],
  });

  assert.equal(harness.hooks.getAdminGoogleSheetPopupState().pendingSortDirection, "asc");

  const selectAll = createInteractiveTarget("[data-admin-google-sheet-popup-select-all=\"1\"]", "1", {
    checked: false,
  });
  harness.elements["#admin-google-sheet-table"].emit("change", {
    target: selectAll,
    currentTarget: harness.elements["#admin-google-sheet-table"],
  });

  const popupState = harness.hooks.getAdminGoogleSheetPopupState();
  assert.deepEqual(normalizeSelectionState(popupState).pendingSelectedValues, ["Alpha", "Delta", "Gamma"]);

  const confirmButton = createInteractiveTarget("[data-admin-google-sheet-popup-action]", "confirm");
  harness.elements["#admin-google-sheet-table"].emit("click", {
    target: confirmButton,
    currentTarget: harness.elements["#admin-google-sheet-table"],
  });

  assert.deepEqual(normalizeSelectionState(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: { columnIndex: 0, direction: "asc" },
    columns: { 0: { selectedValues: ["Alpha", "Delta", "Gamma"] } },
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("admin google sheets popup outside click and escape discard draft changes", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.bindGlobalDismissalListeners();
  harness.hooks.renderAdminEmbedPanel();
  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.setAdminGoogleSheetPopupSort("desc");
  harness.hooks.setAdminGoogleSheetPopupSearch("ga");

  harness.document.emit("click", {
    target: { closest: () => null },
  });

  assert.deepEqual(normalizeSelectionState(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.setAdminGoogleSheetPopupSort("desc");
  harness.hooks.setAdminGoogleSheetPopupSearch("ga");

  harness.document.emit("click", {
    target: { __insideTable: true, closest: () => null },
  });

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.setAdminGoogleSheetPopupSort("desc");
  harness.hooks.setAdminGoogleSheetPopupSearch("ga");

  harness.window.emit("keydown", { key: "Escape" });

  assert.deepEqual(normalizeSelectionState(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("admin google sheets clears popup draft state when switching to a different admin tab", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.setAdminGoogleSheetPopupSort("desc");
  harness.hooks.setAdminGoogleSheetPopupSearch("ga");

  assert.deepEqual(normalizeSelectionState(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "ga",
    pendingSelectedValues: ["Alpha", "Gamma"],
    pendingSortDirection: "desc",
  });

  harness.hooks.setAdminTab("sheet-2", { historyMode: "replace" });

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: null,
    columns: {},
  });
});

test("admin google sheets outside click closes sheets popup and tracker bell popover together", () => {
  const harness = seedGoogleSheetHarness();

  harness.hooks.bindGlobalDismissalListeners();
  harness.hooks.mountRuntimeEnhancements();
  harness.hooks.renderAdminEmbedPanel();

  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.state.trackerChangeBellPopoverOpen = true;

  const outsideTarget = new harness.Element();
  outsideTarget.closest = () => null;

  harness.document.emit("click", {
    target: outsideTarget,
  });

  assert.deepEqual(snapshot(harness.hooks.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
  assert.equal(harness.hooks.state.trackerChangeBellPopoverOpen, false);
});
