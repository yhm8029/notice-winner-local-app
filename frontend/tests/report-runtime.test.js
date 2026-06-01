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
  return context.window.SPMSReportRuntime;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatJson(value) {
  if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
    return "{}";
  }
  return JSON.stringify(value, null, 2);
}

function formatDate(value) {
  return value ? `date:${value}` : "-";
}

function statusBadge(status) {
  return `<span class="status-badge status-${escapeHtml(status)}">${escapeHtml(status)}</span>`;
}

function normalizeMarkup(value) {
  return String(value).replace(/\s+/g, " ").trim();
}

function createReportJobsListDom() {
  let html = "";
  let nodes = [];
  return {
    get innerHTML() {
      return html;
    },
    set innerHTML(value) {
      html = String(value);
      nodes = [...html.matchAll(/data-report-job-id="([^"]+)"/g)].map((match) => {
        const listeners = [];
        return {
          getAttribute(name) {
            return name === "data-report-job-id" ? match[1] : null;
          },
          addEventListener(type, handler) {
            if (type === "click") {
              listeners.push(handler);
            }
          },
          click() {
            for (const listener of listeners) {
              listener();
            }
          },
        };
      });
    },
    querySelectorAll(selector) {
      if (selector !== "[data-report-job-id]") {
        return [];
      }
      return nodes;
    },
  };
}

function loadReportAppContext(runtime = null) {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("function renderReport(");
  const end = source.indexOf("async function loadSelectedRunArtifacts(", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate report rendering helpers in app.js");
  }

  const syncUrlStateCalls = [];
  const loadPhaseReportCalls = [];
  const context = {
    REPORT_RUNTIME: runtime,
    requireReportRuntime() {
      if (!runtime) {
        throw new Error("SPMSReportRuntime is not available.");
      }
      return runtime;
    },
    state: {
      reportKey: "phase1-artifact-diff",
      selectedReportJobId: null,
      reportJobs: [],
      reportJob: null,
    },
    dom: {
      reportStatus: { textContent: "" },
      reportSummary: { textContent: "" },
      reportJson: { textContent: "" },
      reportJobsList: createReportJobsListDom(),
      reportJobStatus: { textContent: "" },
      reportJobDetail: { textContent: "" },
    },
    escapeHtml,
    formatJson,
    formatDate,
    statusBadge,
    syncUrlState() {
      syncUrlStateCalls.push("called");
    },
    loadPhaseReport(options) {
      loadPhaseReportCalls.push(options);
    },
  };

  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  context.syncUrlStateCalls = syncUrlStateCalls;
  context.loadPhaseReportCalls = loadPhaseReportCalls;
  context.sectionSource = source.slice(start, end);
  return context;
}

test("report runtime builds full report and job view models", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "report-runtime.js"));
  const report = {
    summary: {
      matched_count: 10,
      mismatched_count: 2,
      all_match: false,
    },
    raw: true,
  };
  const job = {
    report_name: "phase1-equivalence",
    status: "failed",
    exit_code: 12,
    summary: { all_match: false, passed: 4 },
    raw: true,
  };

  assert.equal(runtime.reportKeyLabel("phase1-equivalence"), "동등성 검증");
  assert.equal(runtime.reportKeyLabel("phase1-artifact-diff"), "산출물 비교 검증");

  const reportView = runtime.buildReportViewModel(
    report,
    { reportKey: "phase1-artifact-diff" },
    { formatJson },
  );
  assert.equal(reportView.statusText, "산출물 비교 검증 | 일치 10 | 불일치 2 | 전체 일치 false");
  assert.equal(reportView.summaryText, formatJson(report.summary));
  assert.equal(reportView.reportText, formatJson(report));

  const emptyReportView = runtime.buildReportViewModel(null, {}, { formatJson });
  assert.equal(emptyReportView.statusText, "아직 검증 리포트를 불러오지 않았습니다.");
  assert.equal(emptyReportView.summaryText, "{}");
  assert.equal(emptyReportView.reportText, "{}");

  const jobView = runtime.buildReportJobViewModel(job, {}, { formatJson });
  assert.equal(jobView.statusText, "동등성 검증 | failed | 12 | 전체 일치 아니오");
  assert.equal(jobView.detailText, formatJson(job));

  const emptyJobView = runtime.buildReportJobViewModel(null, { errorMessage: "boom" }, { formatJson });
  assert.equal(emptyJobView.statusText, "검증 작업을 불러오지 못했습니다: boom");
  assert.equal(emptyJobView.detailText, "{}");
});

test("report runtime builds stable job markup", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "report-runtime.js"));

  const jobsMarkup = runtime.buildReportJobsMarkup(
    [
      {
        id: "job-1",
        report_name: "phase1-artifact-diff",
        status: "success",
        created_at: "2026-03-30T00:00:00Z",
      },
      {
        id: "job-2",
        report_name: "phase1-equivalence",
        status: "failed",
        finished_at: "2026-03-30T01:00:00Z",
      },
    ],
    { selectedReportJobId: "job-1" },
    {
      escapeHtml,
      formatDate,
      statusBadge,
      reportKeyLabel: runtime.reportKeyLabel,
    },
  );

  assert.match(jobsMarkup, /data-report-job-id="job-1"/);
  assert.match(jobsMarkup, /data-report-job-id="job-2"/);
  assert.match(jobsMarkup, /log-item is-selected/);
  assert.match(jobsMarkup, /산출물 비교 검증/);
  assert.match(jobsMarkup, /동등성 검증/);
  assert.equal(
    runtime.buildReportJobsEmptyMarkup(),
    '<div class="empty-state">불러온 검증 작업이 없습니다.</div>',
  );
});

test("app report rendering delegates to runtime and keeps click wiring", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "report-runtime.js"));
  const app = loadReportAppContext(runtime);
  const report = {
    summary: {
      matched_count: 3,
      mismatched_count: 1,
      all_match: false,
    },
  };
  const jobs = [
    {
      id: "job-1",
      report_name: "phase1-artifact-diff",
      status: "failed",
      exit_code: 2,
      created_at: "2026-03-30T00:00:00Z",
      summary: { all_match: false, passed: 1 },
    },
    {
      id: "job-2",
      report_name: "phase1-equivalence",
      status: "success",
      exit_code: 0,
      finished_at: "2026-03-30T01:00:00Z",
      summary: { all_match: true, passed: 3 },
    },
  ];

  app.state.reportJobs = jobs.slice();
  app.state.selectedReportJobId = "job-1";

  app.renderReport(report);
  app.renderReportJobs(jobs);

  const expectedReportView = runtime.buildReportViewModel(
    report,
    { reportKey: app.state.reportKey },
    { formatJson },
  );
  assert.equal(app.dom.reportStatus.textContent, expectedReportView.statusText);
  assert.equal(app.dom.reportSummary.textContent, expectedReportView.summaryText);
  assert.equal(app.dom.reportJson.textContent, expectedReportView.reportText);
  assert.equal(
    normalizeMarkup(app.dom.reportJobsList.innerHTML),
    normalizeMarkup(
      runtime.buildReportJobsMarkup(
        jobs,
        { selectedReportJobId: "job-1" },
        {
          escapeHtml,
          formatDate,
          statusBadge,
          reportKeyLabel: runtime.reportKeyLabel,
        },
      ),
    ),
  );

  const jobNodes = app.dom.reportJobsList.querySelectorAll("[data-report-job-id]");
  assert.equal(jobNodes.length, 2);
  jobNodes[1].click();

  const expectedJobView = runtime.buildReportJobViewModel(jobs[1], {}, { formatJson });
  assert.equal(app.state.selectedReportJobId, "job-2");
  assert.equal(app.state.reportJob.id, "job-2");
  assert.equal(app.syncUrlStateCalls.length, 1);
  assert.equal(app.loadPhaseReportCalls.length, 1);
  assert.equal(app.loadPhaseReportCalls[0].silent, true);
  assert.equal(app.dom.reportJobStatus.textContent, expectedJobView.statusText);
  assert.equal(app.dom.reportJobDetail.textContent, expectedJobView.detailText);
});

test("app report rendering degrades safely when runtime is missing", () => {
  const app = loadReportAppContext(null);

  app.renderReport(null);
  app.renderReportJobs([{ id: "job-1" }]);
  app.renderReportJob(null);

  assert.equal(app.dom.reportStatus.textContent, "검증 UI 런타임을 불러오지 못했습니다.");
  assert.equal(app.dom.reportSummary.textContent, "{}");
  assert.equal(app.dom.reportJson.textContent, "{}");
  assert.equal(
    app.dom.reportJobsList.innerHTML,
    '<div class="empty-state">검증 UI 런타임을 불러오지 못했습니다.</div>',
  );
  assert.equal(app.dom.reportJobStatus.textContent, "검증 UI 런타임을 불러오지 못했습니다.");
  assert.equal(app.dom.reportJobDetail.textContent, "{}");
});

test("app report section no longer carries duplicate fallback renderers", () => {
  const app = loadReportAppContext();
  assert.doesNotMatch(app.sectionSource, /reportKeyLabelFallback/);
  assert.doesNotMatch(app.sectionSource, /buildReportUnavailableTextFallback/);
  assert.doesNotMatch(app.sectionSource, /buildReportStatusTextFallback/);
  assert.doesNotMatch(app.sectionSource, /buildReportJobsMarkupFallback/);
  assert.doesNotMatch(app.sectionSource, /buildReportJobStatusTextFallback/);
});
