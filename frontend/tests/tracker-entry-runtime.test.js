const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime(filePath) {
  const source = fs.readFileSync(filePath, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSTrackerEntryRuntime;
}

function loadTrackerEntryFallbackContext() {
  const source = fs.readFileSync(path.join(__dirname, "..", "tracker-render-fallback-runtime.js"), "utf8");
  const context = {
    window: {},
    console,
  };
  vm.createContext(context);
  vm.runInContext(source, context, {
    filename: path.join(__dirname, "..", "tracker-render-fallback-runtime.js"),
  });
  return context.window.SPMSTrackerRenderFallbackRuntime;
}

function loadTrackerEntryHelperBindings(runtime = null) {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("const toTrackerEntrySummary = TRACKER_ENTRY_RUNTIME?.toTrackerEntrySummary");
  const end = source.indexOf("const buildSelectedEntryMeta =", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate tracker entry helper bindings in app.js");
  }
  const context = {
    TRACKER_ENTRY_RUNTIME: runtime,
    escapeHtml,
  };
  vm.createContext(context);
  vm.runInContext(
    `${source.slice(start, end)}\nglobalThis.__trackerEntryBindings = {\n  toTrackerEntrySummary,\n  buildTrackerEntrySummaryDetail,\n  formatEokValue,\n  parseTrackerCostToWon,\n  formatBuildingAutomationEstimateValue,\n};`,
    context,
  );
  return context.__trackerEntryBindings;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

test("buildTrackerEntryCardMarkup renders shell, number badge, and action selectors", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));
  const html = runtime.buildTrackerEntryCardMarkup(
    {
      entry: {
        id: "entry-1",
        project_name: "Alpha",
        entry_key: "K-1",
        demand_org_name: "Org",
        gross_area_scale: "1000",
        construction_cost: "2000",
        building_automation_estimated_amount: "3000",
        overridden_fields: [],
      },
      displayNo: 7,
      relatedButtonLabel: "연관 공고 열기",
      overrideMarkup: "",
      salesMarkup: "",
      relatedMarkup: "",
    },
    {
      escapeHtml,
      formatBuildingAutomationEstimateValue: (_entry, fallbackValue) => `estimate:${fallbackValue}`,
      formatKoreanDate: (value) => `date:${value}`,
    },
  );

  assert.match(html, /<article class="entry-item"/);
  assert.match(html, /data-entry-id="entry-1"/);
  assert.match(html, /entry-no-badge/);
  assert.match(html, /No\./);
  assert.match(html, /data-entry-related-toggle="entry-1"/);
  assert.match(html, /data-entry-notice-view="entry-1"/);
});

test("buildTrackerEntryCardMarkup renders metrics and injected sections", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));
  const html = runtime.buildTrackerEntryCardMarkup(
    {
      entry: {
        id: "entry-2",
        project_name: "Beta",
        entry_key: "K-2",
        demand_org_name: "Org",
        gross_area_scale: "1000",
        construction_cost: "2000",
        architect_office: "Architect",
        construction_start_date: "2026-03-01",
        opening_scheduled_date: "2026-03-30",
        demand_contact: "Contact",
        site_location_1: "경기도",
        site_location_2: "포천시",
        building_automation_estimated_amount: "estimate",
        overridden_fields: [],
      },
      displayNo: 2,
      relatedButtonLabel: "연관 공고 닫기",
      overrideMarkup: '<p data-test="override">override</p>',
      salesMarkup: '<section data-test="sales">sales</section>',
      relatedMarkup: '<section data-test="related">related</section>',
    },
    {
      escapeHtml,
      formatBuildingAutomationEstimateValue: (_entry, fallbackValue) => `estimate:${fallbackValue}`,
      formatKoreanDate: (value) => `date:${value}`,
    },
  );

  assert.match(html, /entry-metrics/);
  assert.match(html, /연면적/);
  assert.match(html, /공사비/);
  assert.match(html, /빌딩자동제어 추정금액\(공사비의 1.5~2%\)/);
  assert.match(html, /estimate:estimate/);
  assert.match(html, /entry-metrics entry-metrics-single/);
  assert.match(html, /<strong>발주처<\/strong> Org/);
  assert.match(html, /<p data-test="override">override<\/p>/);
  assert.match(html, /<section data-test="sales">sales<\/section>/);
  assert.match(html, /<section data-test="related">related<\/section>/);
  assert.doesNotMatch(html, /<p class="mono">K-2<\/p>/);
  assert.match(html, /현장<\/strong> 경기도 포천시/);
});

test("app-side fallback exists and returns non-empty card markup when runtime helper is missing", () => {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  assert.match(source, /TRACKER_RENDER_FALLBACK_RUNTIME/);
  assert.match(source, /runtime\?\.buildTrackerEntryCardMarkupFallback\?\./);
  assert.match(source, /function buildTrackerEntryCardMarkupFallback\(/);

  const runtime = loadTrackerEntryFallbackContext();
  const html = runtime.buildTrackerEntryCardMarkupFallback(
    {
      entry: {
        id: "entry-3",
        project_name: "Gamma",
        entry_key: "K-3",
        demand_org_name: "Org",
        gross_area_scale: "1000",
        construction_cost: "2000",
        building_automation_estimated_amount: "3000",
        overridden_fields: ["project_name"],
      },
      displayNo: 3,
      relatedButtonLabel: "연관 공고 열기",
      overrideMarkup: '<p data-test="override">override</p>',
      salesMarkup: '<section data-test="sales">sales</section>',
      relatedMarkup: '<section data-test="related">related</section>',
    },
    {
      escapeHtml,
      formatBuildingAutomationEstimateValue: (_entry, fallbackValue) => `estimate:${fallbackValue}`,
      formatKoreanDate: (value) => `date:${value}`,
    },
  );

  assert.notEqual(html, "");
  assert.match(html, /data-entry-id="entry-3"/);
  assert.match(html, /data-entry-related-toggle="entry-3"/);
  assert.match(html, /data-entry-notice-view="entry-3"/);
});

test("tracker-entry helper aliases stay functional when runtime is missing", () => {
  const bindings = loadTrackerEntryHelperBindings(null);

  assert.equal(typeof bindings.toTrackerEntrySummary, "function");
  assert.equal(typeof bindings.buildTrackerEntrySummaryDetail, "function");
  assert.equal(typeof bindings.formatEokValue, "function");
  assert.equal(typeof bindings.parseTrackerCostToWon, "function");
  assert.equal(typeof bindings.formatBuildingAutomationEstimateValue, "function");

  const summary = bindings.toTrackerEntrySummary({
    id: "entry-4",
    source_run_id: "run-1",
    source_tracker_run_id: "tracker-run-1",
    project_id: "project-1",
    source_bid_no: "B-1",
    source_bid_ord: "01",
    entry_key: "entry-key",
    row_no: "12",
    project_name: "Project",
    construction_cost: "100000000",
    building_automation_estimated_amount: "fallback-estimate",
    overridden_fields: ["project_name"],
    gross_area_scale_source: "source-a",
    demand_contact_source: "source-b",
    architect_office_source: "source-c",
    source_type: "manual",
    reason_code: "R1",
    evidence_source: "ledger",
    field_diagnostics: [{ field: "project_name" }],
  });
  assert.deepEqual(JSON.parse(JSON.stringify(summary)), {
    id: "entry-4",
    source_run_id: "run-1",
    source_tracker_run_id: "tracker-run-1",
    project_id: "project-1",
    source_bid_no: "B-1",
    source_bid_ord: "01",
    entry_key: "entry-key",
    row_no: 12,
    project_name: "Project",
    gross_area_scale: "",
    construction_cost: "100000000",
    demand_org_name: "",
    demand_contact: "",
    client_location: "",
    site_location_1: "",
    site_location_2: "",
    architect_office: "",
    opening_scheduled_date: "",
    construction_start_date: "",
    contract_date: "",
    construction_duration_days: "",
    completion_expected_date_explicit: "",
    completion_expected_date_computed: "",
    last_checked_date: "",
    progress_note: "",
    notice_date: "",
    manager_name: "",
    building_automation_estimated_amount: "fallback-estimate",
    overridden_fields: ["project_name"],
    gross_area_scale_source: "source-a",
    demand_contact_source: "source-b",
    architect_office_source: "source-c",
    source_type: "manual",
    reason_code: "R1",
    evidence_source: "ledger",
    field_diagnostics: [{ field: "project_name" }],
  });

  const detail = bindings.buildTrackerEntrySummaryDetail({
    id: "entry-5",
    overridden_fields: [],
  });
  assert.deepEqual(JSON.parse(JSON.stringify(detail)), {
    id: "entry-5",
    source_run_id: null,
    source_tracker_run_id: null,
    project_id: null,
    source_bid_no: "",
    source_bid_ord: "",
    entry_key: "",
    row_no: 0,
    project_name: "",
    gross_area_scale: "",
    construction_cost: "",
    demand_org_name: "",
    demand_contact: "",
    client_location: "",
    site_location_1: "",
    site_location_2: "",
    architect_office: "",
    opening_scheduled_date: "",
    construction_start_date: "",
    contract_date: "",
    construction_duration_days: "",
    completion_expected_date_explicit: "",
    completion_expected_date_computed: "",
    last_checked_date: "",
    progress_note: "",
    notice_date: "",
    manager_name: "",
    building_automation_estimated_amount: "",
    overridden_fields: [],
    _summary_only: true,
  });

  assert.equal(bindings.formatEokValue(3.14), "3.1");
  assert.equal(bindings.formatEokValue(4), "4");
  assert.equal(bindings.parseTrackerCostToWon("100,000,000원"), 100000000);
  assert.equal(bindings.parseTrackerCostToWon(""), 0);
  const estimate = bindings.formatBuildingAutomationEstimateValue(
    { construction_cost: "10000000000", building_automation_estimated_amount: "1.50억원~2.00억원" },
    "1.50억원~2.00억원",
  );
  assert.equal(estimate, "1.50억원~2.00억원");
});

test("tracker-entry runtime exports preserve summary and estimate helper behavior", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));

  const summary = runtime.toTrackerEntrySummary({
    id: "entry-4",
    source_run_id: "run-1",
    source_tracker_run_id: "tracker-run-1",
    project_id: "project-1",
    source_bid_no: "B-1",
    source_bid_ord: "01",
    entry_key: "entry-key",
    row_no: "12",
    project_name: "Project",
    construction_cost: "100000000",
    building_automation_estimated_amount: "fallback-estimate",
    overridden_fields: ["project_name"],
    gross_area_scale_source: "source-a",
    demand_contact_source: "source-b",
    architect_office_source: "source-c",
    source_type: "manual",
    reason_code: "R1",
    evidence_source: "ledger",
    field_diagnostics: [{ field: "project_name" }],
  });
  assert.deepEqual(JSON.parse(JSON.stringify(summary)), {
    id: "entry-4",
    source_run_id: "run-1",
    source_tracker_run_id: "tracker-run-1",
    project_id: "project-1",
    source_bid_no: "B-1",
    source_bid_ord: "01",
    entry_key: "entry-key",
    row_no: 12,
    project_name: "Project",
    gross_area_scale: "",
    construction_cost: "100000000",
    demand_org_name: "",
    demand_contact: "",
    client_location: "",
    site_location_1: "",
    site_location_2: "",
    architect_office: "",
    opening_scheduled_date: "",
    construction_start_date: "",
    contract_date: "",
    construction_duration_days: "",
    completion_expected_date_explicit: "",
    completion_expected_date_computed: "",
    last_checked_date: "",
    progress_note: "",
    notice_date: "",
    manager_name: "",
    building_automation_estimated_amount: "fallback-estimate",
    overridden_fields: ["project_name"],
    gross_area_scale_source: "source-a",
    demand_contact_source: "source-b",
    architect_office_source: "source-c",
    source_type: "manual",
    reason_code: "R1",
    evidence_source: "ledger",
    field_diagnostics: [{ field: "project_name" }],
  });

  const detail = runtime.buildTrackerEntrySummaryDetail({
    id: "entry-5",
    overridden_fields: [],
  });
  assert.deepEqual(JSON.parse(JSON.stringify(detail)), {
    id: "entry-5",
    source_run_id: null,
    source_tracker_run_id: null,
    project_id: null,
    source_bid_no: "",
    source_bid_ord: "",
    entry_key: "",
    row_no: 0,
    project_name: "",
    gross_area_scale: "",
    construction_cost: "",
    demand_org_name: "",
    demand_contact: "",
    client_location: "",
    site_location_1: "",
    site_location_2: "",
    architect_office: "",
    opening_scheduled_date: "",
    construction_start_date: "",
    contract_date: "",
    construction_duration_days: "",
    completion_expected_date_explicit: "",
    completion_expected_date_computed: "",
    last_checked_date: "",
    progress_note: "",
    notice_date: "",
    manager_name: "",
    building_automation_estimated_amount: "",
    overridden_fields: [],
    _summary_only: true,
  });

  assert.equal(runtime.formatEokValue(3.14), "3.1");
  assert.equal(runtime.formatEokValue(4), "4");
  assert.equal(runtime.parseTrackerCostToWon("100,000,000원"), 100000000);
  assert.equal(runtime.parseTrackerCostToWon(""), 0);
  assert.equal(
    runtime.formatBuildingAutomationEstimateValue(
      { construction_cost: "10000000000", building_automation_estimated_amount: "1.50억원~2.00억원" },
      "1.50억원~2.00억원",
    ),
    "1.50억원~2.00억원",
  );
});

test("tracker-entry estimate helper falls back to 1.5~2.0 percent range when stored estimate is blank", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));

  assert.equal(
    runtime.formatBuildingAutomationEstimateValue(
      { construction_cost: "10000000000", building_automation_estimated_amount: "" },
      "",
    ),
    "1.50억원~2.00억원",
  );
});

test("tracker-entry card runtime and app fallback stay aligned on key selectors and content", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-entry-runtime.js"));
  const fallbackRuntime = loadTrackerEntryFallbackContext();
  const payload = {
    entry: {
      id: "entry-6",
      project_name: "Parity Project",
      entry_key: "KEY-6",
      demand_org_name: "Org",
      gross_area_scale: "2000",
      construction_cost: "4000",
      architect_office: "Architect",
      construction_start_date: "2026-03-01",
      opening_scheduled_date: "2026-03-30",
      demand_contact: "Contact",
      site_location_1: "Site",
      building_automation_estimated_amount: "estimate",
      overridden_fields: [],
    },
    displayNo: 6,
    relatedButtonLabel: "연관 공고 열기",
    overrideMarkup: '<p data-test="override">override</p>',
    salesMarkup: '<section data-test="sales">sales</section>',
    relatedMarkup: '<section data-test="related">related</section>',
  };
  const helpers = {
    escapeHtml,
    formatBuildingAutomationEstimateValue: (_entry, fallbackValue) => `estimate:${fallbackValue}`,
    formatKoreanDate: (value) => `date:${value}`,
  };

  const runtimeHtml = runtime.buildTrackerEntryCardMarkup(payload, helpers);
  const fallbackHtml = fallbackRuntime.buildTrackerEntryCardMarkupFallback(payload, helpers);
  for (const html of [runtimeHtml, fallbackHtml]) {
    assert.match(html, /data-entry-id="entry-6"/);
    assert.match(html, /data-entry-related-toggle="entry-6"/);
    assert.match(html, /data-entry-notice-view="entry-6"/);
    assert.match(html, /<section data-test="sales">sales<\/section>/);
    assert.match(html, /<p data-test="override">override<\/p>/);
    assert.match(html, /<section data-test="related">related<\/section>/);
  }
});
