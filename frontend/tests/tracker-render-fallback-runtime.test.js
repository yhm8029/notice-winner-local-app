const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime() {
  const entryRuntimePath = path.join(__dirname, "..", "tracker-render-fallback-entry-runtime.js");
  const boardRuntimePath = path.join(__dirname, "..", "tracker-render-fallback-board-runtime.js");
  const runtimePath = path.join(__dirname, "..", "tracker-render-fallback-runtime.js");
  const entrySource = fs.readFileSync(entryRuntimePath, "utf8");
  const boardSource = fs.readFileSync(boardRuntimePath, "utf8");
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(entrySource, context, { filename: entryRuntimePath });
  vm.runInContext(boardSource, context, { filename: boardRuntimePath });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSTrackerRenderFallbackRuntime;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

test("tracker render fallback runtime exports the expected helpers", () => {
  const runtime = loadRuntime();

  assert.equal(typeof runtime.buildTrackerEntryCardMarkupFallback, "function");
  assert.equal(typeof runtime.renderTrackerEntriesFallback, "function");
  assert.equal(typeof runtime.buildTrackerBoardMarkupFallback, "function");
  assert.equal(typeof runtime.renderTrackerBoardFallback, "function");
  assert.equal(typeof runtime.renderTrackerBoardHeaderCellFallback, "function");
  assert.equal(typeof runtime.isTrackerBoardBlankValueFallback, "function");
  assert.equal(typeof runtime.sortTrackerBoardEntriesFallback, "function");
});

test("sortTrackerBoardEntriesFallback keeps blank-priority fields first without changing stable order otherwise", () => {
  const runtime = loadRuntime();
  const entries = [
    { id: "entry-1", demand_contact: "filled" },
    { id: "entry-2", demand_contact: "" },
    { id: "entry-3", demand_contact: "other" },
  ];

  assert.deepEqual(
    runtime.sortTrackerBoardEntriesFallback(entries, {
      fieldName: "demand_contact",
      blankPriorityFields: new Set(["demand_contact"]),
    }, {
      isTrackerBoardBlankValue: runtime.isTrackerBoardBlankValueFallback,
    }).map((entry) => entry.id),
    ["entry-2", "entry-1", "entry-3"],
  );
  assert.equal(runtime.isTrackerBoardBlankValueFallback("   "), true);
  assert.equal(runtime.isTrackerBoardBlankValueFallback("alpha"), false);
});

test("buildTrackerEntryCardMarkupFallback preserves the entry card selectors", () => {
  const runtime = loadRuntime();
  const html = runtime.buildTrackerEntryCardMarkupFallback(
    {
      entry: {
        id: "entry-1",
        project_name: "Alpha",
        demand_org_name: "Org",
        gross_area_scale: "1000",
        construction_cost: "2000",
        building_automation_estimated_amount: "3000",
        site_location_1: "서울",
        site_location_2: "강남",
        overridden_fields: [],
      },
      displayNo: 7,
      relatedButtonLabel: "연관 공고 열기",
      overrideMarkup: "<p data-test=\"override\">override</p>",
      salesMarkup: "<section data-test=\"sales\">sales</section>",
      relatedMarkup: "<section data-test=\"related\">related</section>",
    },
    {
      escapeHtml,
      formatBuildingAutomationEstimateValue: (_entry, fallbackValue) => `estimate:${fallbackValue}`,
      formatKoreanDate: (value) => `date:${value}`,
    },
  );

  assert.match(html, /<article class="entry-item"/);
  assert.match(html, /data-entry-id="entry-1"/);
  assert.match(html, /data-entry-related-toggle="entry-1"/);
  assert.match(html, /data-entry-notice-view="entry-1"/);
  assert.match(html, /entry-metrics entry-metrics-single/);
  assert.match(html, /estimate:3000/);
  assert.doesNotMatch(html, /data-test="sales"/);
  assert.doesNotMatch(html, /data-test="override"/);
  assert.match(html, /서울 강남/);
});

test("buildTrackerBoardMarkupFallback preserves sorting and edit selectors", () => {
  const runtime = loadRuntime();
  const html = runtime.buildTrackerBoardMarkupFallback(
    [
      {
        id: "entry-1",
        project_name: "Alpha",
        demand_contact: "",
        construction_start_date: "",
        overridden_fields: ["project_name"],
      },
      {
        id: "entry-2",
        project_name: "Beta",
        demand_contact: "filled",
        construction_start_date: "2024-01-01",
        overridden_fields: [],
      },
    ],
    {
      columns: [
        { key: "display_no", label: "NO.", editable: false },
        { key: "project_name", label: "프로젝트명", editable: true },
        { key: "demand_contact", label: "담당자", editable: true },
      ],
      currentSortField: "demand_contact",
      trackerBoardEdit: {
        entryId: "entry-2",
        fieldName: "demand_contact",
        draftValue: "editing",
        saving: false,
        errorMessage: "",
      },
      textareaFields: ["demand_contact"],
      blankPriorityFields: ["demand_contact"],
      page: 2,
      pageSize: 10,
      selectedEntryId: "entry-2",
    },
    { escapeHtml },
  );

  assert.match(html, /<table class="tracker-board-table">/);
  assert.match(html, /data-board-entry-id="entry-2"/);
  assert.match(html, /data-board-edit-trigger="true"/);
  assert.match(html, /data-board-edit-form="true"/);
  assert.match(html, /data-board-edit-input="true"/);
  assert.match(html, /tracker-board-edit-cancel/);
  assert.match(html, /editing/);
});

test("renderTrackerEntriesFallback still renders the entry list when tracker-entry runtime helpers are absent", () => {
  const runtime = loadRuntime();
  const dom = {
    trackerEntriesList: {
      innerHTML: "",
      querySelectorAll() {
        return [];
      },
    },
  };
  const state = {
    uiMode: "admin",
    trackerFilters: {
      page: 1,
      pageSize: 20,
    },
    trackerEntriesError: "",
    selectedEntryId: "entry-1",
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    selectedEntry: null,
    trackerEntryDetailCache: {},
    drawerOpen: false,
  };

  runtime.renderTrackerEntriesFallback(
    [
      {
        id: "entry-1",
        project_id: "project-1",
        project_name: "Fallback Alpha",
        demand_org_name: "Org",
        gross_area_scale: "1000",
        construction_cost: "2000",
        building_automation_estimated_amount: "3000",
        overridden_fields: [],
      },
    ],
    {
      dom,
      state,
      resetTrackerBoardEdit: () => {},
      renderTrackerBoard: () => {},
      renderSelectedEntry: () => {},
      renderSalesClaimSection: () => "",
      renderTrackerEntryRelatedNotices: () => "",
      getSalesClaimForProject: () => null,
      syncUrlState: () => {},
      toggleTrackerEntryRelated: () => {},
      openTrackerEntryNoticeViewer: () => {},
      bindRelatedNoticeViewerButtons: () => {},
      claimSalesProject: () => {},
      setSalesNoteDraft: () => {},
      saveSalesClaimNote: () => {},
      transferSalesClaim: () => {},
      flash: () => {},
      openSalesCloseDialog: () => {},
      closeSalesClaim: () => {},
      releaseSalesClaim: () => {},
      loadSelectedEntryDetail: () => {},
      prefetchTrackerEntryDetails: () => {},
      refreshSelectedEntry: false,
    },
    {
      escapeHtml,
      formatBuildingAutomationEstimateValue: (_entry, fallbackValue) => `estimate:${fallbackValue}`,
      formatKoreanDate: (value) => `date:${value}`,
    },
  );

  assert.match(dom.trackerEntriesList.innerHTML, /data-entry-id="entry-1"/);
  assert.match(dom.trackerEntriesList.innerHTML, /entry-item/);
  assert.match(dom.trackerEntriesList.innerHTML, /3000/);
});
