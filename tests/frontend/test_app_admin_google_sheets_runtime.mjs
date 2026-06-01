import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const stateRuntimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-state-runtime.js");
const runtimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-runtime.js");

function loadStateRuntime() {
  const source = fs.readFileSync(stateRuntimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: stateRuntimePath });
  return window.SPMSAppAdminGoogleSheetsStateRuntime;
}

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  window.SPMSAppAdminGoogleSheetsStateRuntime = loadStateRuntime();
  window.SPMSAdminGoogleSheetsRuntime = createGoogleSheetsRuntimeStub();
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAppAdminGoogleSheetsRuntime;
}

function createClassList() {
  const values = new Set();
  return {
    add: (...tokens) => tokens.forEach((token) => values.add(token)),
    remove: (...tokens) => tokens.forEach((token) => values.delete(token)),
    toggle: (token, force) => {
      const next = force === undefined ? !values.has(token) : Boolean(force);
      if (next) {
        values.add(token);
      } else {
        values.delete(token);
      }
      return next;
    },
    contains: (token) => values.has(token),
  };
}

function createStubElement() {
  const listeners = new Map();
  const attributes = new Map();
  let html = "";
  let innerHTMLWriteCount = 0;
  return {
    classList: createClassList(),
    dataset: {},
    get innerHTML() {
      return html;
    },
    set innerHTML(value) {
      html = String(value ?? "");
      innerHTMLWriteCount += 1;
    },
    getInnerHTMLWriteCount: () => innerHTMLWriteCount,
    textContent: "",
    setAttribute: (name, value) => {
      attributes.set(String(name), String(value));
    },
    removeAttribute: (name) => {
      attributes.delete(String(name));
    },
    getAttribute: (name) => attributes.get(String(name)),
    querySelector: () => null,
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

function createGoogleSheetsRuntimeStub() {
  return {
    normalizeAdminGoogleSheetState(sheetState) {
      const source = sheetState && typeof sheetState === "object" ? sheetState : {};
      const columnsSource = source.columns && typeof source.columns === "object" ? source.columns : {};
      const columns = {};
      for (const [columnKey, columnState] of Object.entries(columnsSource)) {
        const columnIndex = Number(columnKey);
        if (!Number.isInteger(columnIndex) || columnIndex < 0) {
          continue;
        }
        const selectedValues = Array.from(new Set(
          (Array.isArray(columnState?.selectedValues) ? columnState.selectedValues : [])
            .map((value) => String(value ?? "").trim())
            .filter(Boolean),
        ));
        if (selectedValues.length) {
          columns[String(columnIndex)] = { selectedValues };
        }
      }
      const sortColumnIndex = Number(source.sort?.columnIndex);
      const sortDirection = String(source.sort?.direction || "").trim();
      const sort = Number.isInteger(sortColumnIndex) && (sortDirection === "asc" || sortDirection === "desc")
        ? { columnIndex: sortColumnIndex, direction: sortDirection }
        : null;
      return { sort, columns };
    },
    buildAdminGoogleSheetFilterModel(payload, sheetState = {}) {
      const headers = Array.isArray(payload?.headers) ? payload.headers.slice() : [];
      const rows = Array.isArray(payload?.rows) ? payload.rows.map((row) => row.slice()) : [];
      const optionValueLists = headers.map((_, columnIndex) => Array.from(new Set(
        rows.map((row) => String(row[columnIndex] ?? "").trim()).filter(Boolean),
      )));
      const normalizedState = this.normalizeAdminGoogleSheetState(sheetState);
      return {
        headers,
        rows,
        optionLists: optionValueLists,
        optionValueLists,
        columnCount: headers.length,
        sheetState: normalizedState,
      };
    },
    buildAdminGoogleSheetTableView(_payload, options = {}) {
      return {
        html: `<div data-sheet="${String(options.sheetKey || "")}">table</div>`,
        sheetState: options.sheetState || { sort: null, columns: {} },
      };
    },
    buildAdminGoogleSheetStatusView(_bootstrap, activeSheet = {}) {
      return {
        html: `<div data-sheet="${String(activeSheet.key || "")}">status</div>`,
      };
    },
  };
}

function snapshot(value) {
  return JSON.parse(JSON.stringify(value));
}

function createRuntimeHarness({ withEmbedPanel = false, googleSheetsRuntime = createGoogleSheetsRuntimeStub(), windowOverrides = {} } = {}) {
  const appRuntime = loadRuntime();
  assert.ok(appRuntime, "expected SPMSAppAdminGoogleSheetsRuntime to load");
  assert.equal(typeof appRuntime.createAppAdminGoogleSheetsRuntime, "function");

  const state = {
    uiMode: "admin",
    adminTab: "sheet-1",
    adminLegacyRoutePath: "",
    adminGoogleSheetsFilterStateByKey: {},
    adminGoogleSheetMinHeightByKey: {},
    adminGoogleSheetsPopupState: {
      open: false,
      sheetKey: "",
      columnIndex: -1,
      searchDraft: "",
      pendingSelectedValues: [],
      pendingSortDirection: "",
    },
    adminGoogleSheetsBootstrap: {
      sync_status: "synced",
    },
    adminGoogleSheetsBootstrapLoading: false,
    adminGoogleSheetsBootstrapError: "",
    adminGoogleSheetsSyncMessage: "",
    adminGoogleSheetsSyncing: false,
    adminGoogleSheetTabs: [
      {
        key: "sheet-1",
        label: "Sheet 1",
        type: "google_sheet",
        routePath: "/app/project-status",
      },
    ],
    adminGoogleSheetPayloadByKey: {
      "sheet-1": {
        headers: ["Region", "Owner"],
        rows: [
          ["Alpha", "Kim"],
          ["Beta", "Lee"],
          ["Gamma", "Kim"],
        ],
      },
    },
    adminGoogleSheetPayloadLoadingByKey: {},
    adminGoogleSheetPayloadErrorByKey: {},
  };
  const dom = {
    adminGoogleSheetTable: createStubElement(),
  };
  if (withEmbedPanel) {
    dom.adminEmbedPanel = createStubElement();
    dom.adminEmbedTitle = createStubElement();
    dom.adminEmbedSubtitle = createStubElement();
    dom.adminGoogleSheetsSyncFeedback = createStubElement();
    dom.adminGoogleSheetStatus = createStubElement();
    dom.adminEmbedEmpty = createStubElement();
    dom.adminGoogleSheetsSyncButton = createStubElement();
  }
  let renderCount = 0;
  const runtime = appRuntime.createAppAdminGoogleSheetsRuntime({
    state,
    dom,
    window: {
      setTimeout,
      clearTimeout,
      ...windowOverrides,
    },
    googleSheetsRuntime,
    escapeHtml(value) {
      return String(value ?? "");
    },
    renderAdminEmbedPanel() {
      renderCount += 1;
    },
    findResolvedAdminTab(tabKey) {
      const key = String(tabKey || "").trim();
      return key && key.startsWith("sheet-")
        ? { key, type: "google_sheet" }
        : { key: "project-status", type: "builtin" };
    },
  });
  return {
    runtime,
    state,
    dom,
    getRenderCount: () => renderCount,
  };
}

test("app admin google sheets runtime normalizes filter state and compares normalized equality", () => {
  const harness = createRuntimeHarness();
  const normalized = harness.runtime.normalizeAdminGoogleSheetsFilterState({
    sort: { columnIndex: 1, direction: "asc" },
    columns: {
      0: { selectedValues: ["Alpha", "Alpha", "", "Beta"] },
      bad: { selectedValues: ["ignored"] },
    },
  });

  assert.deepEqual(normalized, {
    sort: { columnIndex: 1, direction: "asc" },
    columns: {
      0: { selectedValues: ["Alpha", "Beta"] },
    },
  });

  assert.equal(
    harness.runtime.adminGoogleSheetsFilterStateEqual(
      normalized,
      {
        sort: { columnIndex: 1, direction: "asc" },
        columns: {
          0: { selectedValues: ["Alpha", "Beta"] },
        },
      },
    ),
    true,
  );
});

test("app admin google sheets runtime confirms popup selection into sheet filter state and closes popup", () => {
  const harness = createRuntimeHarness();

  harness.runtime.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.runtime.toggleAdminGoogleSheetPopupValue("Alpha", true);
  harness.runtime.toggleAdminGoogleSheetPopupValue("Gamma", true);
  harness.runtime.setAdminGoogleSheetPopupSort("desc");
  harness.runtime.confirmAdminGoogleSheetPopup();

  assert.deepEqual(snapshot(harness.state.adminGoogleSheetsFilterStateByKey["sheet-1"]), {
    sort: { columnIndex: 0, direction: "desc" },
    columns: {
      0: { selectedValues: ["Alpha", "Beta", "Gamma"] },
    },
  });
  assert.deepEqual(snapshot(harness.runtime.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("app admin google sheets runtime renders table markup through the delegated runtime", () => {
  const harness = createRuntimeHarness();

  harness.runtime.renderAdminGoogleSheetTable("sheet-1", harness.state.adminGoogleSheetPayloadByKey["sheet-1"]);

  assert.match(harness.dom.adminGoogleSheetTable.innerHTML, /data-sheet="sheet-1"/);
});

test("app admin google sheets runtime preserves table DOM when rendered markup is unchanged", () => {
  const harness = createRuntimeHarness();

  harness.runtime.renderAdminGoogleSheetTable("sheet-1", harness.state.adminGoogleSheetPayloadByKey["sheet-1"]);
  const firstWriteCount = harness.dom.adminGoogleSheetTable.getInnerHTMLWriteCount();
  harness.runtime.renderAdminGoogleSheetTable("sheet-1", harness.state.adminGoogleSheetPayloadByKey["sheet-1"]);

  assert.equal(harness.dom.adminGoogleSheetTable.getInnerHTMLWriteCount(), firstWriteCount);
});

test("app admin google sheets runtime defers table DOM replacement while text selection is active", () => {
  let version = 1;
  let deferredRender = null;
  let selectionActive = true;
  const googleSheetsRuntime = {
    ...createGoogleSheetsRuntimeStub(),
    buildAdminGoogleSheetTableView(_payload, options = {}) {
      return {
        html: `<div data-sheet="${String(options.sheetKey || "")}">table-${version}</div>`,
        sheetState: options.sheetState || { sort: null, columns: {} },
      };
    },
  };
  const harness = createRuntimeHarness({
    googleSheetsRuntime,
    windowOverrides: {
      getSelection: () => ({
        isCollapsed: !selectionActive,
        toString: () => (selectionActive ? "selected text" : ""),
      }),
      setTimeout: (handler) => {
        deferredRender = handler;
        return 1;
      },
    },
  });

  harness.runtime.renderAdminGoogleSheetTable("sheet-1", harness.state.adminGoogleSheetPayloadByKey["sheet-1"]);
  const firstWriteCount = harness.dom.adminGoogleSheetTable.getInnerHTMLWriteCount();
  version = 2;
  harness.runtime.renderAdminGoogleSheetTable("sheet-1", harness.state.adminGoogleSheetPayloadByKey["sheet-1"]);

  assert.equal(harness.dom.adminGoogleSheetTable.getInnerHTMLWriteCount(), firstWriteCount);
  assert.match(harness.dom.adminGoogleSheetTable.innerHTML, /table-1/);
  assert.equal(typeof deferredRender, "function");

  selectionActive = false;
  deferredRender();

  assert.equal(harness.dom.adminGoogleSheetTable.getInnerHTMLWriteCount(), firstWriteCount + 1);
  assert.match(harness.dom.adminGoogleSheetTable.innerHTML, /table-2/);
});

test("app admin google sheets runtime keeps protected loads blocked and disables sync when auth is unavailable", () => {
  const harness = createRuntimeHarness({ withEmbedPanel: true });
  let bootstrapCalls = 0;
  let payloadCalls = 0;

  harness.runtime.renderAdminEmbedPanel({
    getActiveAdminTab: () => ({
      key: "sheet-1",
      label: "Sheet 1",
      subtitle: "Sheet subtitle",
      type: "google_sheet",
    }),
    getValidatedActiveAdminGoogleSheetTab: () => ({
      key: "sheet-1",
      type: "google_sheet",
    }),
    canLoadProtectedConsoleData: () => false,
    shouldShowSharedGoogleSheetsShell: () => true,
    shouldShowAdminGoogleSheetsOverviewPanel: () => false,
    shouldShowAdminGoogleSheetsControls: () => true,
    loadAdminGoogleSheetsBootstrap: () => {
      bootstrapCalls += 1;
    },
    loadAdminGoogleSheetPayload: () => {
      payloadCalls += 1;
    },
  });

  assert.equal(bootstrapCalls, 0);
  assert.equal(payloadCalls, 0);
  assert.equal(harness.dom.adminGoogleSheetsSyncButton.classList.contains("hidden"), false);
  assert.equal(harness.dom.adminGoogleSheetsSyncButton.getAttribute("disabled"), "disabled");
});

test("app admin google sheets runtime renders the embed panel through the delegated helper", () => {
  const harness = createRuntimeHarness({ withEmbedPanel: true });

  harness.runtime.renderAdminEmbedPanel({
    getActiveAdminTab: () => ({
      key: "sheet-1",
      label: "Sheet 1",
      subtitle: "Sheet subtitle",
      type: "google_sheet",
    }),
    getValidatedActiveAdminGoogleSheetTab: () => ({
      key: "sheet-1",
      type: "google_sheet",
    }),
    canLoadProtectedConsoleData: () => true,
    shouldShowSharedGoogleSheetsShell: () => true,
    shouldShowAdminGoogleSheetsOverviewPanel: () => false,
    shouldShowAdminGoogleSheetsControls: () => true,
    loadAdminGoogleSheetsBootstrap: () => {
      throw new Error("bootstrap load should not be requested");
    },
    loadAdminGoogleSheetPayload: () => {
      throw new Error("payload load should not be requested");
    },
    buildAdminGoogleSheetsOverviewMessage: () => "overview message",
  });

  assert.equal(harness.dom.adminEmbedPanel.classList.contains("hidden"), false);
  assert.equal(harness.dom.adminEmbedTitle.textContent, "Sheet 1");
  assert.equal(harness.dom.adminEmbedSubtitle.textContent, "Sheet subtitle");
  assert.equal(harness.dom.adminGoogleSheetsSyncButton.textContent, "Google Sheets 동기화");
  assert.match(harness.dom.adminGoogleSheetStatus.innerHTML, /data-sheet="sheet-1"/);
  assert.match(harness.dom.adminGoogleSheetTable.innerHTML, /data-sheet="sheet-1"/);
});

test("app admin google sheets runtime hides the overview panel in user mode when no sheet tab is active", () => {
  const harness = createRuntimeHarness({ withEmbedPanel: true });
  harness.state.uiMode = "user";
  harness.state.adminTab = "project-status";

  harness.runtime.renderAdminEmbedPanel({
    getActiveAdminTab: () => ({
      key: "project-status",
      label: "프로젝트 현황",
      subtitle: "",
      type: "existing",
    }),
    getValidatedActiveAdminGoogleSheetTab: () => null,
    canLoadProtectedConsoleData: () => true,
    shouldShowSharedGoogleSheetsShell: () => true,
    shouldShowAdminGoogleSheetsOverviewPanel: () => true,
    shouldShowAdminGoogleSheetsControls: () => false,
    loadAdminGoogleSheetsBootstrap: () => {
      throw new Error("bootstrap load should not be requested for user overview");
    },
    loadAdminGoogleSheetPayload: () => {
      throw new Error("payload load should not be requested for user overview");
    },
  });

  assert.equal(harness.dom.adminEmbedPanel.classList.contains("hidden"), true);
});
