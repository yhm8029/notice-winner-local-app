const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadAppSupportRuntime() {
  const trackerRuntimePath = path.join(__dirname, "..", "app-support-tracker-runtime.js");
  const runtimePath = path.join(__dirname, "..", "app-support-runtime.js");
  const trackerSource = fs.readFileSync(trackerRuntimePath, "utf8");
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window });
  vm.runInContext(trackerSource, context, { filename: trackerRuntimePath });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAppSupportRuntime;
}

function createTrackerRenderFallbackHelpers(runtime) {
  return runtime.createAppSupportRuntime().createTrackerRenderFallbackHelpers({
    dom: {},
    state: {},
    resetTrackerBoardEdit: () => {},
    renderTrackerBoard: () => {},
    renderSelectedEntry: () => {},
    runtimeAdapters: {},
    salesStateHelpers: {},
    renderSalesClaimSection: () => "",
    renderTrackerEntryRelatedNotices: () => "",
    syncUrlState: () => {},
    toggleTrackerEntryRelated: () => {},
    openTrackerEntryNoticeViewer: () => {},
    bindRelatedNoticeViewerButtons: () => {},
    claimSalesProject: () => {},
    saveSalesClaimNote: () => {},
    transferSalesClaim: () => {},
    flash: () => {},
    openSalesCloseDialog: () => {},
    closeSalesClaim: () => {},
    releaseSalesClaim: () => {},
    loadSelectedEntryDetail: () => {},
    prefetchTrackerEntryDetails: () => {},
    buildTrackerBoardMarkupFallback: () => "",
    renderTrackerEntries: () => {},
    toggleTrackerBoardBlankPriority: () => {},
    beginTrackerBoardEdit: () => {},
    saveTrackerBoardEdit: () => {},
    columns: [],
    textareaFields: new Set(["project_name", "progress_note"]),
    blankPriorityFields: new Set(["demand_contact"]),
    renderTrackerBoardHeaderCell: () => "",
    renderTrackerBoardCell: () => "",
    renderTrackerBoardEditingCell: () => "",
    sortTrackerBoardEntriesFallback: (entries) => entries,
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

test("createTrackerRenderFallbackHelpers exposes tracker-board helper functions", () => {
  const runtime = loadAppSupportRuntime();
  const helpers = createTrackerRenderFallbackHelpers(runtime);

  assert.equal(typeof helpers.renderTrackerBoardHeaderCell, "function");
  assert.equal(typeof helpers.isTrackerBoardBlankValue, "function");
  assert.equal(typeof helpers.buildTrackerBoardCellMarkupFallback, "function");
  assert.equal(typeof helpers.buildTrackerBoardEditingCellMarkupFallback, "function");
  assert.equal(typeof helpers.sortTrackerBoardEntries, "function");
});

test("sortTrackerBoardEntries keeps blank-priority fields first without changing stable order otherwise", () => {
  const runtime = loadAppSupportRuntime();
  const helpers = createTrackerRenderFallbackHelpers(runtime);
  const entries = [
    { id: "entry-1", demand_contact: "filled" },
    { id: "entry-2", demand_contact: "" },
    { id: "entry-3", demand_contact: "other" },
  ];

  assert.deepEqual(
    helpers.sortTrackerBoardEntries(entries, {
      fieldName: "demand_contact",
      blankPriorityFields: new Set(["demand_contact"]),
    }, {
      isTrackerBoardBlankValue: helpers.isTrackerBoardBlankValue,
    }).map((entry) => entry.id),
    ["entry-2", "entry-1", "entry-3"],
  );
  assert.equal(helpers.isTrackerBoardBlankValue("   "), true);
  assert.equal(helpers.isTrackerBoardBlankValue("alpha"), false);
});

test("tracker-board cell helpers preserve editable and editing selector contracts", () => {
  const runtime = loadAppSupportRuntime();
  const helpers = createTrackerRenderFallbackHelpers(runtime);

  const cellHtml = helpers.buildTrackerBoardCellMarkupFallback({
    entry: { id: "entry-1", project_name: "Alpha", overridden_fields: ["project_name"] },
    column: { key: "project_name", label: "Project name", editable: true },
    displayNo: 1,
  }, {
    escapeHtml,
  });

  assert.match(cellHtml, /data-board-edit-trigger="true"/);
  assert.match(cellHtml, /data-board-edit-entry-id="entry-1"/);
  assert.match(cellHtml, /data-board-edit-field="project_name"/);
  assert.match(cellHtml, />override<\/span>/);

  const editingHtml = helpers.buildTrackerBoardEditingCellMarkupFallback({
    entry: { id: "entry-1" },
    fieldName: "progress_note",
    label: "Progress note",
    value: 'Working note "alpha" <beta>',
    saving: false,
    errorMessage: "failed <error> & more",
  }, {
    escapeHtml,
    textareaFields: new Set(["project_name", "progress_note"]),
  });

  assert.match(editingHtml, /data-board-edit-form="true"/);
  assert.match(editingHtml, /data-board-edit-input="true"/);
  assert.match(editingHtml, /data-board-edit-active="true"/);
  assert.match(editingHtml, /tracker-board-edit-error">failed &lt;error&gt; &amp; more<\/p>/);
});
