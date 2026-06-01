import test from "node:test";
import assert from "node:assert/strict";
import { createConsolePanelsController } from "../../frontend/console-panels-controller.js";

function createDom() {
  return {
    dashboardMetrics: { innerHTML: "" },
    dashboardFailedRuns: { innerHTML: "" },
    dashboardReportJobs: { innerHTML: "" },
    runExecutionContext: null,
    projectList: null,
    projectPageMeta: null,
    projectPrevButton: null,
    projectNextButton: null,
  };
}

test("console panels controller loads and renders the dashboard summary", async () => {
  const dom = createDom();
  const state = { dashboard: null, projects: [], projectsTotal: 0, projectFilters: { page: 1, pageSize: 20 } };
  let apiCalls = 0;
  let touched = "";
  const controller = createConsolePanelsController({
    dom,
    state,
    api: async (path) => {
      apiCalls += 1;
      assert.equal(path, "/api/dashboard/summary");
      return {
        run_counts: { running: 2, failed: 1 },
        tracker_total: 4,
        tracker_edited_total: 1,
        artifact_metadata_persistent: true,
        repository_backends: { artifacts: "s3" },
        latest_reports: {},
        recent_failed_runs: [{ id: "run-1", run_type: "project_tracker", status: "failed", created_at: "2026-04-21T00:00:00Z" }],
        active_report_jobs: [{ id: "job-1", report_name: "phase1-artifact-diff", status: "running", started_at: "2026-04-21T00:00:00Z" }],
      };
    },
    flash: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    metricCard: (label, value) => `<article>${label}:${value}</article>`,
    PROJECT_RUNTIME: null,
    RUN_VIEW_RUNTIME: null,
    renderArtifactPreviewMarkup: () => "",
    resolveTrackerExecutionContext: () => null,
    trackerExecutionTone: () => "",
    trackerExecutionMessage: () => "",
    progressPercent: () => 0,
    trackerExportStageLabel: (value) => String(value ?? ""),
    renderRelatedProjectNotices: () => "",
    bindRelatedNoticeViewerButtons: () => {},
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: (value) => {
      touched = value;
    },
  });

  await controller.loadDashboardSummary();

  assert.equal(apiCalls, 1);
  assert.match(dom.dashboardMetrics.innerHTML, /Running:2/);
  assert.match(dom.dashboardFailedRuns.innerHTML, /run-1/);
  assert.match(dom.dashboardReportJobs.innerHTML, /job-1/);
  assert.match(touched, /dashboard synced/);
});

test("console panels controller renders the run execution context markup", () => {
  const dom = createDom();
  dom.runExecutionContext = {
    className: "",
    dataset: {},
    innerHTML: "",
    classList: {
      add() {
        throw new Error("renderRunExecutionContext should not hide the panel for a valid context");
      },
      remove() {
        dom.runExecutionContext.hiddenRemoved = true;
      },
    },
  };
  const state = {
    dashboard: null,
    projects: [],
    projectsTotal: 0,
    projectFilters: { page: 1, pageSize: 20 },
    artifacts: [{ id: "artifact-1", download_url: "/downloads/artifact-1.xlsx" }],
    selectedTrackerWorkbookArtifactId: "artifact-1",
    selectedTrackerRun: null,
    selectedTrackerRunId: null,
  };
  const controller = createConsolePanelsController({
    dom,
    state,
    api: async () => {
      throw new Error("api should not be called in renderRunExecutionContext coverage");
    },
    flash: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    metricCard: (label, value) => `<article>${label}:${value}</article>`,
    PROJECT_RUNTIME: null,
    RUN_VIEW_RUNTIME: {
      buildRunExecutionContextMarkup(context, { previewMarkup }) {
        return `<section data-title="${context.title}">${previewMarkup}</section>`;
      },
      buildTrackerExecutionDetailBits() {
        return [];
      },
    },
    renderArtifactPreviewMarkup(artifactId) {
      return `<div class="artifact-preview">${artifactId}</div>`;
    },
    resolveTrackerExecutionContext(run) {
      return {
        title: `context:${run.id}`,
        status: "success",
        progressStage: "exporting",
        progressCurrent: 2,
        progressTotal: 4,
        estimatedRows: 10,
        trackerEntryRows: 8,
        errorMessage: "",
      };
    },
    trackerExecutionTone: (status) => `tone:${status}`,
    trackerExecutionMessage: (context) => `message:${context.title}`,
    progressPercent: () => 50,
    trackerExportStageLabel: (stage) => `stage:${stage}`,
    renderRelatedProjectNotices: () => "",
    bindRelatedNoticeViewerButtons: () => {},
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: () => {},
  });

  controller.renderRunExecutionContext({ id: "run-17" });

  assert.equal(dom.runExecutionContext.hiddenRemoved, true);
  assert.equal(dom.runExecutionContext.className, "runtime-card tracker-execution-context");
  assert.equal(dom.runExecutionContext.dataset.tone, "tone:success");
  assert.match(dom.runExecutionContext.innerHTML, /context:run-17/);
  assert.match(dom.runExecutionContext.innerHTML, /artifact-preview/);
  assert.match(dom.runExecutionContext.innerHTML, /artifact-1/);
});

test("console panels controller loads and renders the projects list", async () => {
  const dom = createDom();
  const listenerCalls = [];
  const projectListNodes = [
    {
      addEventListener(type) {
        listenerCalls.push(["title", type]);
      },
      getAttribute() {
        return "project-1";
      },
    },
  ];
  dom.projectQuery = { value: "  portal  " };
  dom.projectList = {
    innerHTML: "",
    querySelectorAll(selector) {
      listenerCalls.push(["query", selector]);
      return projectListNodes;
    },
  };
  dom.projectPageMeta = { textContent: "" };
  dom.projectPrevButton = { disabled: false };
  dom.projectNextButton = { disabled: false };

  const state = { dashboard: null, projects: [], projectsTotal: 0, projectFilters: { page: 1, pageSize: 1, q: "" }, projectOpenId: "project-1" };
  let apiPath = "";
  let synced = "";
  const controller = createConsolePanelsController({
    dom,
    state,
    api: async (path) => {
      apiPath = path;
      return {
        items: [
          { id: "project-1", project_name: "Project One" },
          { id: "project-2", project_name: "Project Two" },
        ],
        total: 2,
      };
    },
    flash: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    metricCard: (label, value) => `<article>${label}:${value}</article>`,
    PROJECT_RUNTIME: {
      buildProjectPageMeta(page, totalPages, totalItems) {
        return `Page ${page}/${totalPages} | ${totalItems}`;
      },
      buildProjectListMarkup(items) {
        return `<section>${items.map((item) => item.project_name).join(",")}</section>`;
      },
    },
    RUN_VIEW_RUNTIME: null,
    renderArtifactPreviewMarkup: () => "",
    resolveTrackerExecutionContext: () => null,
    trackerExecutionTone: () => "",
    trackerExecutionMessage: () => "",
    progressPercent: () => 0,
    trackerExportStageLabel: (value) => String(value ?? ""),
    renderRelatedProjectNotices: () => "related",
    bindRelatedNoticeViewerButtons: () => {
      listenerCalls.push(["bindRelatedNoticeViewerButtons"]);
    },
    toggleProjectRelated: () => {},
    openProjectNoticeViewer: () => {},
    applyPresetParams: () => {},
    syncUrlState: () => {},
    syncCollectModeOptions: () => {},
    touchSyncMeta: (value) => {
      synced = value;
    },
  });

  await controller.loadProjects({ silent: true });

  assert.match(apiPath, /\/api\/projects\?page=1&page_size=1&q=portal/);
  assert.equal(dom.projectQuery.value, "portal");
  assert.equal(state.projectsTotal, 2);
  assert.equal(dom.projectPageMeta.textContent, "Page 1/2 | 2");
  assert.equal(dom.projectPrevButton.disabled, true);
  assert.equal(dom.projectNextButton.disabled, false);
  assert.match(dom.projectList.innerHTML, /Project One/);
  assert.match(synced, /projects synced/);
  assert.deepEqual(listenerCalls.filter(([kind]) => kind === "query").length, 5);
  assert.deepEqual(listenerCalls.filter(([kind]) => kind === "title").length, 5);
  assert.deepEqual(listenerCalls.at(-1), ["bindRelatedNoticeViewerButtons"]);
});
