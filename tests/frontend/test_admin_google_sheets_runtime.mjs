import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { readCombinedCssSource } from "./css-source.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/admin-google-sheets-runtime.js");
const stylesPath = path.resolve(__dirname, "../../frontend/styles.css");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAdminGoogleSheetsRuntime;
}

test("isAdminGoogleSheetTabKey recognizes admin sheet tab keys", () => {
  const runtime = loadRuntime();

  assert.equal(typeof runtime.isAdminGoogleSheetTabKey, "function");
  assert.equal(runtime.isAdminGoogleSheetTabKey("sheet-1664606955"), true);
  assert.equal(runtime.isAdminGoogleSheetTabKey("sheet-abc"), false);
  assert.equal(runtime.isAdminGoogleSheetTabKey("not-a-sheet-key"), false);
});

test("buildAdminGoogleSheetTabs sorts tabs and normalizes labels", () => {
  const runtime = loadRuntime();

  const tabs = runtime.buildAdminGoogleSheetTabs({
    tabs: {
      "sheet-2": {
        sheet_order: 2,
        display_title: "Display B",
        raw_title: "Raw B",
        sheet_id: 101,
      },
      "sheet-1": {
        sheet_order: 1,
        raw_title: "Raw A",
        sheet_id: 202,
      },
      "sheet-3": {
        sheet_order: 3,
        display_title: "",
        raw_title: "Raw C",
        sheet_id: 303,
      },
    },
  });

  assert.deepEqual(JSON.parse(JSON.stringify(tabs)), [
    { key: "sheet-1", label: "Raw A", rawTitle: "Raw A", sheetId: 202 },
    { key: "sheet-2", label: "Display B", rawTitle: "Raw B", sheetId: 101 },
    { key: "sheet-3", label: "Raw C", rawTitle: "Raw C", sheetId: 303 },
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(runtime.buildAdminGoogleSheetTabs({}))), []);
});

test("buildAdminGoogleSheetStatusView renders backend ready and initializing statuses and active sheet label", () => {
  const runtime = loadRuntime();

  const readyView = runtime.buildAdminGoogleSheetStatusView(
    {
      sync_status: "ready",
      synced_at: "2026-04-18T09:30:00Z",
    },
    {
      key: "sheet-1664606955",
      label: "Sheet Alpha",
    },
  );

  assert.equal(typeof readyView.html, "string");
  assert.match(readyView.html, /status/);
  assert.match(readyView.html, /ready/);
  assert.match(readyView.html, /2026-04-18T09:30:00Z/);
  assert.match(readyView.html, /Sheet Alpha/);

  const initializingView = runtime.buildAdminGoogleSheetStatusView(
    { sync_status: "initializing" },
    { label: "Sheet Beta" },
  );
  assert.match(initializingView.html, /initializing/);
  assert.match(initializingView.html, /Sheet Beta/);
});

test("admin google sheet status styles cover backend ready and initializing states", () => {
  const styles = readCombinedCssSource(stylesPath);

  assert.match(styles, /\.admin-google-sheet-status-badge\.status-ready/);
  assert.match(styles, /\.admin-google-sheet-status-badge\.status-initializing/);
});

test("buildAdminGoogleSheetTableView renders headers and rows safely", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Name", "Note"],
      rows: [
        ["Alice", "<safe>"],
        ["Bob", "& more"],
      ],
    },
    {
      escapeHtml: (value) => String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;"),
    },
  );

  const emptyView = runtime.buildAdminGoogleSheetTableView({}, {
    escapeHtml: (value) => String(value),
  });

  assert.equal(typeof view.html, "string");
  assert.match(view.html, /<table/);
  assert.match(view.html, /class="admin-google-sheet-header-cell"/);
  assert.match(view.html, /class="admin-google-sheet-trigger-label">Name<\/span>/);
  assert.match(view.html, /&lt;safe&gt;/);
  assert.match(view.html, /&amp; more/);
  assert.match(emptyView.html, /<table/);
});

test("buildAdminGoogleSheetTableView renders linked document cells from google sheet payload", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      header_cells: [
        { text: "문서", href: "" },
        { text: "상태", href: "" },
      ],
      row_cells: [
        [
          { text: "설계서", href: "https://docs.google.com/document/d/design-doc/edit" },
          { text: "확인", href: "" },
        ],
      ],
    },
    {
      escapeHtml: (value) => String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;"),
    },
  );

  assert.match(view.html, /class="admin-google-sheet-header-cell"/);
  assert.match(view.html, /class="admin-google-sheet-trigger-label">문서<\/span>/);
  assert.match(view.html, /href="https:\/\/docs\.google\.com\/document\/d\/design-doc\/edit"/);
  assert.match(view.html, />설계서<\/a>/);
  assert.match(view.html, /target="_blank"/);
});

test("buildAdminGoogleSheetTableView does not render unsafe link schemes as anchors", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      row_cells: [
        [
          { text: "실행", href: "javascript:alert(1)" },
        ],
      ],
    },
    {
      escapeHtml: (value) => String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;"),
    },
  );

  assert.doesNotMatch(view.html, /href="javascript:alert\(1\)"/);
  assert.doesNotMatch(view.html, /<a class="admin-google-sheet-link"/);
  assert.match(view.html, />실행</);
});
