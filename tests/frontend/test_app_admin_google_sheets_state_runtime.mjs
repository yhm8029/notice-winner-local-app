import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const stateRuntimePath = path.resolve(__dirname, "../../frontend/app-admin-google-sheets-state-runtime.js");

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
  return {
    classList: createClassList(),
    dataset: {},
    querySelector: () => null,
    getBoundingClientRect: () => ({ height: 0 }),
    offsetHeight: 0,
    scrollHeight: 0,
  };
}

function loadRuntime({ googleSheetsRuntime, renderAdminEmbedPanel = () => {}, findResolvedAdminTab = () => null } = {}) {
  const source = fs.readFileSync(stateRuntimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: stateRuntimePath });
  const runtimeFactory = window.SPMSAppAdminGoogleSheetsStateRuntime?.createAppAdminGoogleSheetsStateRuntime;
  assert.equal(typeof runtimeFactory, "function");

  return runtimeFactory({
    state: {
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
      adminGoogleSheetPayloadByKey: {
        "sheet-1": {
          headers: ["Region"],
          rows: [["Seoul"], ["Busan"]],
        },
      },
    },
    dom: {
      adminGoogleSheetTable: createStubElement(),
    },
    window,
    googleSheetsRuntime,
    renderAdminEmbedPanel,
    findResolvedAdminTab,
  });
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
      const normalizedState = this.normalizeAdminGoogleSheetState(sheetState);
      return {
        headers,
        rows,
        optionLists: rows.map(() => ["Busan", "Seoul"]),
        optionValueLists: rows.map(() => ["Busan", "Seoul"]),
        columnCount: headers.length || 1,
        sheetState: normalizedState,
      };
    },
  };
}

function snapshot(value) {
  return JSON.parse(JSON.stringify(value));
}

test("state runtime normalizes filters, popup state, and table interaction helpers", () => {
  const runtime = loadRuntime({ googleSheetsRuntime: createGoogleSheetsRuntimeStub() });

  assert.deepEqual(runtime.normalizeAdminGoogleSheetsFilterState({
    sort: { columnIndex: 1, direction: "desc" },
    columns: {
      0: { selectedValues: ["Seoul", "Seoul", ""] },
    },
  }), {
    sort: { columnIndex: 1, direction: "desc" },
    columns: {
      0: { selectedValues: ["Seoul"] },
    },
  });

  runtime.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  runtime.setAdminGoogleSheetPopupSearch("seo");
  runtime.setAdminGoogleSheetPopupSort("asc");
  runtime.toggleAdminGoogleSheetPopupValue("Busan", false);
  runtime.confirmAdminGoogleSheetPopup();

  assert.deepEqual(snapshot(runtime.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: { columnIndex: 0, direction: "asc" },
    columns: {
      0: { selectedValues: ["Seoul"] },
    },
  });
});

test("state runtime clears popup draft state when switching to another resolved admin tab", () => {
  const runtime = loadRuntime({
    googleSheetsRuntime: createGoogleSheetsRuntimeStub(),
    findResolvedAdminTab: (tab) => (tab === "sheet-1"
      ? { key: "sheet-1", type: "google_sheet" }
      : { key: "project-status", type: "builtin" }),
  });

  runtime.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  runtime.setAdminGoogleSheetPopupSearch("seo");
  assert.equal(runtime.clearAdminGoogleSheetPopupStateForTab("sheet-1"), false);
  assert.equal(runtime.clearAdminGoogleSheetPopupStateForTab("project-status"), true);
  assert.deepEqual(snapshot(runtime.getAdminGoogleSheetPopupState()), {
    open: false,
    sheetKey: "",
    columnIndex: -1,
    searchDraft: "",
    pendingSelectedValues: [],
    pendingSortDirection: "",
  });
});

test("state runtime tracks the active table key and dismissal selectors", () => {
  const runtime = loadRuntime({ googleSheetsRuntime: createGoogleSheetsRuntimeStub() });
  runtime.setAdminGoogleSheetPopupState({
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "",
    pendingSelectedValues: ["Seoul"],
    pendingSortDirection: "",
  }, { render: false });

  assert.equal(runtime.getAdminGoogleSheetTableInteractionSheetKey(), "");
  assert.equal(runtime.handleAdminGoogleSheetPopupDismissal({ target: { closest: (selector) => (selector === "[data-admin-google-sheet-popup-root=\"1\"]" ? {} : null) } }), false);
  assert.equal(runtime.handleAdminGoogleSheetPopupDismissal({ target: { closest: () => null } }), true);
});
