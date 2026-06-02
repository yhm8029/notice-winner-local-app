import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/tracker-entry-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSTrackerEntryRuntime;
}

test("buildTrackerEntriesEmptyStateView returns admin and user empty copy", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntriesEmptyStateView, "function");

  const adminView = runtime.buildTrackerEntriesEmptyStateView({
    trackerEntriesError: "",
    uiMode: "admin",
  });
  const userView = runtime.buildTrackerEntriesEmptyStateView({
    trackerEntriesError: "",
    uiMode: "user",
  });

  assert.match(adminView.html, /No tracker rows loaded/);
  assert.match(userView.html, /tracker entry/i);
});

test("buildTrackerEntryCardView returns selected state and metrics without override text", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntryCardView, "function");

  const view = runtime.buildTrackerEntryCardView(
    {
      id: "entry-1",
      project_name: "Test Project",
      entry_key: "key-1",
      demand_org_name: "Client Org",
      gross_area_scale: "1,000 sqm",
      construction_cost: "100000000",
      architect_office: "Architect Office",
      construction_start_date: "2026-05-01",
      opening_scheduled_date: "2027-01-01",
      demand_contact: "Contact Person",
      site_location_1: "Seoul",
      site_location_2: "Jung-gu",
      building_automation_estimated_amount: "3 million won",
      overridden_fields: ["project_name"],
    },
    {
      displayNo: 7,
      selectedEntryId: "entry-1",
      uiMode: "admin",
      formatOpeningScheduledDate: (value) => `open:${value}`,
      formatEstimateValue: (entry) => `estimate:${entry.building_automation_estimated_amount}`,
    },
  );

  assert.equal(view.selectedClass, " is-selected");
  assert.equal(view.displayNoText, "7");
  assert.ok(view.relatedButtonLabel.length > 0);
  assert.equal(view.overrideMetaText, "");
  assert.equal(view.overrideMetaHtml, "");
  assert.equal(view.openingScheduledDateText, "open:2027-01-01");
  assert.equal(view.estimateValueText, "estimate:3 million won");
  assert.equal(view.siteLocationText, "Seoul Jung-gu");
});

test("buildTrackerEntrySummaryDetail returns summary-only tracker entry data", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntrySummaryDetail, "function");

  const detail = runtime.buildTrackerEntrySummaryDetail({
    id: "entry-3",
    project_name: "Summary Project",
    gross_area_scale: "900 sqm",
    construction_cost: "120000000",
    demand_org_name: "Client Org",
    demand_contact: "Contact Person",
    site_location_1: "Seoul",
    site_location_2: "Gangnam",
    overridden_fields: ["project_name"],
    field_diagnostics: [{ field_name: "project_name" }],
  });

  assert.equal(detail.id, "entry-3");
  assert.equal(detail.project_name, "Summary Project");
  assert.equal(detail._summary_only, true);
  assert.deepEqual(detail.overridden_fields, ["project_name"]);
  assert.deepEqual(detail.field_diagnostics, [{ field_name: "project_name" }]);
});

test("buildTrackerEntryCardView hides empty override copy", () => {
  const runtime = loadRuntime();

  const view = runtime.buildTrackerEntryCardView(
    {
      id: "entry-2",
      project_name: "No Override Project",
      demand_org_name: "충청북도 충주시",
      overridden_fields: [],
    },
    {
      uiMode: "admin",
    },
  );

  assert.equal(view.overrideMetaText, "");
  assert.equal(view.overrideMetaHtml, "");
});

test("buildTrackerEntryCardMarkup injects related slot without sales or override chrome", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerEntryCardMarkup, "function");

  const html = runtime.buildTrackerEntryCardMarkup(
    {
      id: "entry-1",
      project_name: "Test Project",
      entry_key: "key-1",
      demandOrgNameText: "Client Org",
      grossAreaScaleText: "1,000 sqm",
      constructionCostText: "100000000",
      estimateValueText: "3 million won",
      architectOfficeText: "Architect Office",
      constructionStartDateText: "2026-05-01",
      openingScheduledDateText: "2027-01-01",
      demandContactText: "Contact Person",
      siteLocationText: "Seoul",
      selectedClass: " is-selected",
      displayNoText: "2",
      relatedButtonLabel: "Open related notice",
      overrideMetaHtml: "<p>override project_name</p>",
      salesSectionHtml: "<section>sales</section>",
      relatedNoticeHtml: "<section>related</section>",
    },
    { escapeHtml: (value) => String(value) },
  );

  assert.match(html, /<section>related<\/section>/);
  assert.doesNotMatch(html, /<section>sales<\/section>/);
  assert.doesNotMatch(html, /override project_name/);
  assert.match(html, /entry-item is-selected/);
  assert.match(html, /entry-metrics entry-metrics-single/);
  assert.match(html, /<strong>발주처<\/strong> Client Org/);
  assert.doesNotMatch(html, /key-1/);
  assert.doesNotMatch(html, /no overrides/);
});
