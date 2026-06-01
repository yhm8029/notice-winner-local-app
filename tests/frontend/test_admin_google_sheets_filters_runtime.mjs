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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

test("buildAdminGoogleSheetFilterModel filters rows with checkbox selections and sorts by visible text", () => {
  const runtime = loadRuntime();

  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      header_cells: [
        { text: "Region" },
        { text: "Agency" },
      ],
      row_cells: [
        [{ text: "Seoul" }, { text: "Seoul Office" }],
        [{ text: "Busan" }, { text: "Busan Office" }],
        [{ text: "Gyeongnam" }, { text: "Changwon City" }],
      ],
    },
    {
      sort: { columnIndex: 1, direction: "asc" },
      columns: {
        0: { selectedValues: ["Seoul", "Gyeongnam", "Missing"] },
        1: { selectedValues: ["Busan Office", "Changwon City", "Seoul Office"] },
      },
    },
  );

  assert.deepEqual(JSON.parse(JSON.stringify(model.optionLists)), [
    ["Busan", "Gyeongnam", "Seoul"],
    ["Busan Office", "Changwon City", "Seoul Office"],
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(model.filteredRows.map((row) => row[1].text))), [
    "Changwon City",
    "Seoul Office",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(model.sheetState.columns["0"].selectedValues)), ["Seoul", "Gyeongnam"]);
  assert.equal(model.sheetState.columns["1"], undefined);
  assert.deepEqual(JSON.parse(JSON.stringify(model.sheetState.sort)), { columnIndex: 1, direction: "asc" });
});

test("buildAdminGoogleSheetFilterModel uses the blank bucket label for empty visible text", () => {
  const runtime = loadRuntime();

  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [
        [""],
        [{ text: "   " }],
        [{ text: "Seoul" }],
      ],
    },
    {},
  );

  assert.deepEqual(JSON.parse(JSON.stringify(model.optionLists[0])), ["빈값", "Seoul"]);
});

test("buildAdminGoogleSheetFilterModel uses rendered link text for link-only cells", () => {
  const runtime = loadRuntime();

  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Resource"],
      rows: [
        [{ href: "https://example.com/spec" }],
        [{ text: "Alpha", href: "https://example.com/alpha" }],
        [""],
      ],
    },
    {
      sort: { columnIndex: 0, direction: "asc" },
      columns: {
        0: { selectedValues: ["https://example.com/spec"] },
      },
    },
  );

  assert.deepEqual(JSON.parse(JSON.stringify(model.optionLists[0])), [
    "빈값",
    "Alpha",
    "https://example.com/spec",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(model.filteredRows.map((row) => row[0].href || row[0].text))), [
    "https://example.com/spec",
  ]);
});

test("buildAdminGoogleSheetFilterModel keeps synthetic blank values separate from literal blank text", () => {
  const runtime = loadRuntime();

  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [
        [""],
        [{ text: "빈값" }],
        [{ text: "Seoul" }],
      ],
    },
    {
      columns: {
        0: { selectedValues: ["빈값"] },
      },
    },
  );

  assert.deepEqual(JSON.parse(JSON.stringify(model.optionLists[0])), ["빈값", "\"빈값\"", "Seoul"]);
  assert.deepEqual(JSON.parse(JSON.stringify(model.filteredRows.map((row) => row[0].text))), ["빈값"]);
});

test("buildAdminGoogleSheetFilterModel prunes invalid selected values when the payload changes", () => {
  const runtime = loadRuntime();

  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [["Seoul"], ["Busan"]],
    },
    {
      columns: {
        0: { selectedValues: ["Seoul", "Gyeongnam", ""] },
      },
    },
  );

  assert.deepEqual(JSON.parse(JSON.stringify(model.sheetState.columns["0"].selectedValues)), ["Seoul"]);
  assert.deepEqual(JSON.parse(JSON.stringify(model.filteredRows.map((row) => row[0].text))), ["Seoul"]);
});

test("buildAdminGoogleSheetPopupModel scopes select-all to the visible searched values", () => {
  const runtime = loadRuntime();
  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [["Seoul"], ["Sejong"], ["Busan"]],
    },
    {
      columns: {
        0: { selectedValues: ["Seoul", "Sejong"] },
      },
    },
  );

  const popup = runtime.buildAdminGoogleSheetPopupModel(model, {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "se",
    pendingSelectedValues: ["Seoul"],
    pendingSortDirection: "desc",
  });

  assert.deepEqual(JSON.parse(JSON.stringify(popup.allValues)), ["Busan", "Sejong", "Seoul"]);
  assert.deepEqual(JSON.parse(JSON.stringify(popup.visibleValues)), ["Sejong", "Seoul"]);
  assert.equal(popup.allVisibleSelected, false);
  assert.equal(popup.partiallySelected, true);
  assert.deepEqual(JSON.parse(JSON.stringify(popup.pendingSelectedValues)), ["Seoul"]);
  assert.equal(popup.pendingSortDirection, "desc");
});

test("buildAdminGoogleSheetPopupModel falls back to the applied column selection when pending values are omitted", () => {
  const runtime = loadRuntime();
  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [["Seoul"], ["Busan"]],
    },
    {
      columns: {
        0: { selectedValues: ["Seoul"] },
      },
    },
  );

  const popup = runtime.buildAdminGoogleSheetPopupModel(model, {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "",
    pendingSortDirection: "",
  });

  assert.deepEqual(JSON.parse(JSON.stringify(popup.allValues)), ["Busan", "Seoul"]);
  assert.deepEqual(JSON.parse(JSON.stringify(popup.pendingSelectedValues)), ["Seoul"]);
  assert.equal(popup.allVisibleSelected, false);
  assert.equal(popup.partiallySelected, true);
});

test("buildAdminGoogleSheetPopupModel renders distinct labels for synthetic blank and literal blank text", () => {
  const runtime = loadRuntime();
  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [
        [""],
        [{ text: "빈값" }],
        [{ text: "Seoul" }],
      ],
    },
    {
      columns: {
        0: { selectedValues: ["__SPMS_ADMIN_GOOGLE_SHEET_BLANK__", "빈값"] },
      },
    },
  );

  const popup = runtime.buildAdminGoogleSheetPopupModel(model, {
    open: true,
    sheetKey: "sheet-1",
    columnIndex: 0,
    searchDraft: "빈",
    pendingSelectedValues: ["__SPMS_ADMIN_GOOGLE_SHEET_BLANK__", "빈값"],
    pendingSortDirection: "",
  });

  assert.deepEqual(JSON.parse(JSON.stringify(popup.allValues)), [
    "빈값",
    "\"빈값\"",
    "Seoul",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(popup.visibleValues)), [
    "빈값",
    "\"빈값\"",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(popup.visibleValueKeys)), [
    "__SPMS_ADMIN_GOOGLE_SHEET_BLANK__",
    "빈값",
  ]);
});

test("buildAdminGoogleSheetPopupModel returns null for closed or invalid popup state", () => {
  const runtime = loadRuntime();
  const model = runtime.buildAdminGoogleSheetFilterModel(
    {
      headers: ["Region"],
      rows: [["Seoul"]],
    },
    {},
  );

  assert.equal(runtime.buildAdminGoogleSheetPopupModel(model, { open: false, columnIndex: 0 }), null);
  assert.equal(runtime.buildAdminGoogleSheetPopupModel(model, { open: true, columnIndex: 9 }), null);
});

test("buildAdminGoogleSheetTableView keeps the legacy filter path when normalized state values are omitted", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region"],
      rows: [["Seoul"], ["Busan"]],
    },
    {
      escapeHtml,
      filters: [{ query: "", selected: "Busan" }],
      sheetState: undefined,
      popupState: undefined,
    },
  );

  assert.match(view.html, /admin-google-sheet-filter-row/);
  assert.match(view.html, /<tbody><tr><td>Busan<\/td><\/tr><\/tbody>/);
});

test("buildAdminGoogleSheetTableView renders one header row with triggers in new mode", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region", "Agency"],
      rows: [["Seoul", "A"], ["Busan", "B"]],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {
        columns: {},
      },
      popupState: {
        open: false,
        sheetKey: "sheet-1",
        columnIndex: 0,
      },
    },
  );

  assert.doesNotMatch(view.html, /admin-google-sheet-filter-row/);
  assert.match(view.html, /<thead>\s*<tr>[\s\S]*data-admin-google-sheet-trigger-index="0"/);
  assert.match(view.html, /<thead>\s*<tr>[\s\S]*data-admin-google-sheet-trigger-index="1"/);
});

test("buildAdminGoogleSheetTableView marks filtered, sorted, and open triggers active", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region", "Agency"],
      rows: [
        ["Seoul", "A"],
        ["Busan", "B"],
      ],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {
        sort: { columnIndex: 0, direction: "asc" },
        columns: {
          1: { selectedValues: ["B"] },
        },
      },
      popupState: {
        open: true,
        sheetKey: "sheet-1",
        columnIndex: 1,
        searchDraft: "b",
        pendingSelectedValues: ["B"],
        pendingSortDirection: "desc",
      },
    },
  );

  assert.match(view.html, /data-admin-google-sheet-trigger-index="0"/);
  assert.match(view.html, /class="admin-google-sheet-trigger-button is-active is-sorted"/);
  assert.match(view.html, /data-admin-google-sheet-trigger-index="1"/);
  assert.match(view.html, /class="admin-google-sheet-trigger-button is-active is-filtered is-open"/);
});

test("buildAdminGoogleSheetTableView renders popup markup inside the open header cell", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region", "Agency"],
      rows: [
        ["Seoul", "A"],
        ["Busan", "B"],
      ],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {
        columns: {
          1: { selectedValues: ["B"] },
        },
      },
      popupState: {
        open: true,
        sheetKey: "sheet-1",
        columnIndex: 1,
        searchDraft: "B",
        pendingSelectedValues: ["B"],
        pendingSortDirection: "asc",
      },
    },
  );

  assert.match(view.html, /data-admin-google-sheet-popup-sort="asc"/);
  assert.match(view.html, /data-admin-google-sheet-popup-sort="desc"/);
  assert.match(view.html, /data-admin-google-sheet-popup-search="1"/);
  assert.match(view.html, /data-admin-google-sheet-popup-select-all="1"/);
  assert.match(view.html, /data-admin-google-sheet-popup-value/);
  assert.match(view.html, /data-admin-google-sheet-popup-action="confirm"/);
  assert.match(view.html, /data-admin-google-sheet-popup-action="cancel"/);
});

test("buildAdminGoogleSheetTableView renders distinct popup labels for synthetic blank and literal blank text", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region"],
      rows: [
        [""],
        [{ text: "빈값" }],
      ],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {
        columns: {
          0: { selectedValues: ["__SPMS_ADMIN_GOOGLE_SHEET_BLANK__", "빈값"] },
        },
      },
      popupState: {
        open: true,
        sheetKey: "sheet-1",
        columnIndex: 0,
        searchDraft: "",
        pendingSelectedValues: ["__SPMS_ADMIN_GOOGLE_SHEET_BLANK__", "빈값"],
        pendingSortDirection: "",
      },
    },
  );

  assert.match(view.html, /<span>빈값<\/span>/);
  assert.match(view.html, /<span>&quot;빈값&quot;<\/span>/);
});

test("buildAdminGoogleSheetTableView renders korean popup action labels", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region"],
      rows: [["Seoul"], ["Busan"]],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {},
      popupState: {
        open: true,
        sheetKey: "sheet-1",
        columnIndex: 0,
        searchDraft: "",
        pendingSelectedValues: ["Seoul", "Busan"],
        pendingSortDirection: "asc",
      },
    },
  );

  assert.match(view.html, />오름차순</);
  assert.match(view.html, />내림차순</);
  assert.match(view.html, />전체 선택</);
  assert.match(view.html, />취소</);
  assert.match(view.html, />적용</);
});

test("buildAdminGoogleSheetTableView renders plain escaped header text inside trigger buttons", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: [
        { text: "Region", href: "https://example.com/region" },
      ],
      rows: [["Seoul"]],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {},
      popupState: {
        open: false,
        sheetKey: "sheet-1",
        columnIndex: 0,
      },
    },
  );

  assert.match(view.html, /<button[\s\S]*data-admin-google-sheet-trigger-index="0"[\s\S]*>[\s\S]*Region[\s\S]*<\/button>/);
  assert.doesNotMatch(view.html, /admin-google-sheet-link/);
});

test("buildAdminGoogleSheetTableView renders triggers for row-derived columns when headers are missing", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      rows: [
        ["Seoul", "A"],
        ["Busan", "B"],
      ],
    },
    {
      escapeHtml,
      sheetKey: "sheet-1",
      sheetState: {},
      popupState: {
        open: false,
        sheetKey: "sheet-1",
        columnIndex: 0,
      },
    },
  );

  assert.match(view.html, /data-admin-google-sheet-trigger-index="0"/);
  assert.match(view.html, /data-admin-google-sheet-trigger-index="1"/);
});

test("buildAdminGoogleSheetTableView renders no-match state when filters remove all rows", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region", "Agency"],
      rows: [
        ["Seoul", "A"],
        ["Busan", "B"],
      ],
    },
    {
      escapeHtml,
      sheetState: {
        columns: {
          0: { selectedValues: ["Seoul"] },
          1: { selectedValues: ["B"] },
        },
      },
    },
  );

  assert.match(view.html, /admin-google-sheet-empty-row/);
  assert.match(view.html, /조건에 맞는 데이터가 없습니다\./);
});

test("buildAdminGoogleSheetTableView renders a wrapper min-height style when provided", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Region"],
      rows: [["Seoul"]],
    },
    {
      escapeHtml,
      minTableHeightPx: 512,
    },
  );

  assert.match(view.html, /admin-google-sheet-table-wrap/);
  assert.match(view.html, /--admin-google-sheet-min-table-height:\s*512px/);
  assert.match(view.html, /min-height:\s*var\(--admin-google-sheet-min-table-height\)/);
});

test("admin google sheet filter styles exist", () => {
  const styles = readCombinedCssSource(stylesPath);

  assert.match(styles, /\.admin-google-sheet-filter-row/);
  assert.match(styles, /\.admin-google-sheet-filter-input/);
  assert.match(styles, /\.admin-google-sheet-filter-select/);
  assert.match(styles, /\.admin-google-sheet-header-cell/);
  assert.match(styles, /\.admin-google-sheet-trigger-button/);
  assert.match(styles, /\.admin-google-sheet-trigger-button\.is-active/);
  assert.match(styles, /\.admin-google-sheet-trigger-button\.is-open/);
  assert.match(styles, /\.admin-google-sheet-popup\s*\{[\s\S]*left:\s*0;/);
  assert.match(styles, /\.admin-google-sheet-popup\s*\{[\s\S]*min-width:\s*max\(100%,\s*240px\);/);
  assert.match(styles, /\.admin-google-sheet-popup\s*\{[\s\S]*width:\s*max-content;/);
  assert.match(styles, /\.admin-google-sheet-popup\s*\{[\s\S]*max-width:\s*min\(360px,\s*calc\(100vw - 48px\)\);/);
  assert.match(styles, /\.admin-google-sheet-popup-actions\s*\{[\s\S]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);/);
  assert.match(styles, /\.admin-google-sheet-popup-actions button,\s*[\s\S]*\.admin-google-sheet-popup-footer button\s*\{[\s\S]*min-width:\s*0;/);
  assert.match(styles, /\.admin-google-sheet-popup-value span\s*\{[\s\S]*white-space:\s*normal;/);
  assert.match(styles, /\.admin-google-sheet-popup-value span\s*\{[\s\S]*overflow-wrap:\s*anywhere;/);
  assert.match(styles, /\.admin-google-sheet-popup-search/);
  assert.match(styles, /\.admin-google-sheet-popup-select-all/);
  assert.match(styles, /\.admin-google-sheet-popup-values/);
  assert.match(styles, /\.admin-google-sheet-popup-value/);
  assert.match(styles, /\.admin-google-sheet-popup-footer/);
  assert.match(styles, /--admin-google-sheet-min-table-height/);
});
