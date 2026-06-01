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
  return context.window.SPMSTrackerMissingReportRuntime;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDate(value) {
  return value ? `date:${value}` : "-";
}

function normalizeMarkup(value) {
  return String(value).replace(/\s+/g, " ").trim();
}

function loadMissingReportAppContext(runtime = null) {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("function renderTrackerMissingReport(");
  const end = source.indexOf("const SALES_STATE_HELPERS =", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate missing report renderers in app.js");
  }

  const calls = [];
  const context = {
    TRACKER_MISSING_REPORT_RUNTIME: runtime,
    APP_SUPPORT: {
      renderTrackerMissingReport(options, errorMessage = "") {
        calls.push(["renderTrackerMissingReport", errorMessage]);
        if (!options.TRACKER_MISSING_REPORT_RUNTIME) {
          options.dom.missingReportSummary.innerHTML = '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>';
          options.dom.missingReportList.innerHTML = '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>';
          return undefined;
        }
        const view = options.TRACKER_MISSING_REPORT_RUNTIME.buildMissingReportViewModel(
          options.state.trackerMissingReport,
          { errorMessage },
          {
            escapeHtml: options.escapeHtml,
            formatDate: options.formatDate,
          },
        );
        if (view.summaryClassName) {
          options.dom.missingReportSummary.className = view.summaryClassName;
        }
        options.dom.missingReportSummary.innerHTML = view.summaryMarkup;
        if (view.listClassName) {
          options.dom.missingReportList.className = view.listClassName;
        }
        options.dom.missingReportList.innerHTML = view.listMarkup;
        return undefined;
      },
    },
    state: {
      trackerMissingReport: null,
    },
    dom: {
      missingReportSummary: {
        innerHTML: "",
        className: "missing-report-summary empty-state",
      },
      missingReportList: {
        innerHTML: "",
        className: "missing-report-list empty-state",
      },
    },
    escapeHtml,
    formatDate,
  };

  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  context.calls = calls;
  context.sectionSource = source.slice(start, end);
  return context;
}

test("missing report runtime builds full view model", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-missing-report-runtime.js"));
  const report = {
    summary: {
      total_entries: 8,
      missing_entries: 2,
      contact_missing: 1,
      architect_missing: 1,
      area_missing: 0,
    },
    items: [
      {
        project_name: "Alpha",
        bid_no: "BID-1",
        bid_ord: "001",
        demand_org_name: "서울시",
        updated_at: "2026-03-30T00:00:00Z",
        missing_fields: [
          {
            field_label: "담당 연락처",
            reason_group: "source_gap",
            reason_explainer: "원본에 값이 없습니다.",
            source_reason: "source 비어 있음",
          },
          {
            field_key: "architect_office",
            reason_group: "",
            reason_explainer: "",
            source_reason: "",
          },
        ],
      },
    ],
  };

  const reportView = runtime.buildMissingReportViewModel(report, {}, { escapeHtml, formatDate });
  assert.equal(reportView.summaryClassName, "missing-report-summary");
  assert.equal(reportView.listClassName, "missing-report-list");
  assert.match(reportView.summaryMarkup, /전체 공고/);
  assert.match(reportView.summaryMarkup, /누락 공고/);
  assert.match(reportView.listMarkup, /Alpha/);
  assert.match(reportView.listMarkup, /date:2026-03-30T00:00:00Z/);
  assert.match(reportView.listMarkup, /담당 연락처/);
  assert.match(reportView.listMarkup, /architect_office/);
  assert.match(reportView.listMarkup, /원인 미분류/);
  assert.match(reportView.listMarkup, /source 정보 없음/);

  const emptyView = runtime.buildMissingReportViewModel(
    { summary: report.summary, items: [] },
    {},
    { escapeHtml, formatDate },
  );
  assert.equal(emptyView.listClassName, "missing-report-list empty-state");
  assert.equal(emptyView.listMarkup, '<div class="empty-state">현재 누락 항목이 없습니다.</div>');

  const unloadedView = runtime.buildMissingReportViewModel(
    null,
    { errorMessage: "boom" },
    { escapeHtml, formatDate },
  );
  assert.equal(unloadedView.summaryClassName, "");
  assert.equal(unloadedView.listClassName, "");
  assert.equal(unloadedView.summaryMarkup, '<div class="empty-state">누락 현황을 아직 불러오지 않았습니다.</div>');
  assert.equal(unloadedView.listMarkup, '<div class="empty-state">boom</div>');
});

test("missing report runtime preserves chip and item helpers", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-missing-report-runtime.js"));

  assert.equal(
    normalizeMarkup(runtime.buildMissingReportChipMarkup("전체 공고", 12, { escapeHtml })),
    normalizeMarkup(`
      <article class="missing-report-chip">
        <span>전체 공고</span>
        <strong>12</strong>
      </article>
    `),
  );
  assert.equal(
    runtime.buildMissingReportEmptyMarkup("현재 누락 항목이 없습니다.", { escapeHtml }),
    '<div class="empty-state">현재 누락 항목이 없습니다.</div>',
  );
});

test("app missing report rendering delegates to runtime", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-missing-report-runtime.js"));
  const app = loadMissingReportAppContext(runtime);
  const report = {
    summary: {
      total_entries: 8,
      missing_entries: 2,
      contact_missing: 1,
      architect_missing: 1,
      area_missing: 0,
    },
    items: [
      {
        project_name: "Alpha",
        bid_no: "BID-1",
        bid_ord: "001",
        demand_org_name: "서울시",
        updated_at: "2026-03-30T00:00:00Z",
        missing_fields: [
          {
            field_label: "담당 연락처",
            reason_group: "source_gap",
            reason_explainer: "원본에 값이 없습니다.",
            source_reason: "source 비어 있음",
          },
        ],
      },
    ],
  };

  app.renderTrackerMissingReport();
  let expectedView = runtime.buildMissingReportViewModel(null, {}, { escapeHtml, formatDate });
  assert.deepEqual(app.calls, [["renderTrackerMissingReport", ""]]);
  assert.equal(app.dom.missingReportSummary.className, "missing-report-summary empty-state");
  assert.equal(app.dom.missingReportList.className, "missing-report-list empty-state");
  assert.equal(app.dom.missingReportSummary.innerHTML, expectedView.summaryMarkup);
  assert.equal(app.dom.missingReportList.innerHTML, expectedView.listMarkup);

  app.state.trackerMissingReport = report;
  app.renderTrackerMissingReport();
  assert.deepEqual(app.calls, [["renderTrackerMissingReport", ""], ["renderTrackerMissingReport", ""]]);
  expectedView = runtime.buildMissingReportViewModel(report, {}, { escapeHtml, formatDate });
  assert.equal(app.dom.missingReportSummary.className, expectedView.summaryClassName);
  assert.equal(app.dom.missingReportList.className, expectedView.listClassName);
  assert.equal(normalizeMarkup(app.dom.missingReportSummary.innerHTML), normalizeMarkup(expectedView.summaryMarkup));
  assert.equal(normalizeMarkup(app.dom.missingReportList.innerHTML), normalizeMarkup(expectedView.listMarkup));
});

test("app missing report rendering degrades safely when runtime is missing", () => {
  const app = loadMissingReportAppContext(null);

  app.renderTrackerMissingReport();

  assert.equal(app.dom.missingReportSummary.className, "missing-report-summary empty-state");
  assert.equal(app.dom.missingReportList.className, "missing-report-list empty-state");
  assert.equal(
    app.dom.missingReportSummary.innerHTML,
    '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>',
  );
  assert.equal(
    app.dom.missingReportList.innerHTML,
    '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>',
  );
});

test("app missing report section no longer carries duplicate fallback renderers", () => {
  const app = loadMissingReportAppContext();
  assert.doesNotMatch(app.sectionSource, /renderMissingReportChip/);
  assert.doesNotMatch(app.sectionSource, /buildMissingReportChipMarkupFallback/);
  assert.doesNotMatch(app.sectionSource, /buildMissingReportSummaryMarkupFallback/);
  assert.doesNotMatch(app.sectionSource, /buildMissingReportItemsMarkupFallback/);
  assert.doesNotMatch(app.sectionSource, /buildMissingReportEmptyMarkupFallback/);
  assert.match(app.sectionSource, /APP_SUPPORT\.renderTrackerMissingReport/);
});
