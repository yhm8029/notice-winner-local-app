import test from "node:test";
import assert from "node:assert/strict";
import { createReportPanelsController } from "../../frontend/report-panels-controller.js";

function createButton(artifactId) {
  return {
    artifactId,
    listener: null,
    getAttribute(name) {
      return name === "data-preview-artifact-id" ? this.artifactId : null;
    },
    addEventListener(type, handler) {
      assert.equal(type, "click");
      this.listener = handler;
    },
  };
}

test("report panels controller can request run-side artifact preview caching", async () => {
  const button = createButton("artifact-1");
  const dom = {
    reportSelect: { value: "phase1-artifact-diff" },
    reportStatus: { textContent: "" },
    reportSummary: { textContent: "" },
    reportJson: { textContent: "" },
    reportJobsList: { innerHTML: "", querySelectorAll: () => [] },
    reportJobStatus: { textContent: "" },
    reportJobDetail: { textContent: "" },
    runReportButton: { textContent: "" },
    reportSeedLimit: { value: "3" },
    artifactsList: {
      innerHTML: "",
      querySelectorAll: (selector) => {
        assert.equal(selector, "[data-preview-artifact-id]");
        return [button];
      },
    },
  };
  const state = {
    reportKey: "phase1-artifact-diff",
    reportData: null,
    reportJobs: [],
    reportJob: null,
    selectedReportJobId: null,
    artifactPreviewCache: {},
    artifactSections: [{ title: "selected", subtitle: "sub", meta: "meta", items: [{ id: "artifact-1", artifact_type: "tracking_excel", file_name: "file.xlsx", mime_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", meta: { rows: 1 }, download_url: "/download" }] }],
    artifacts: [{ id: "artifact-1", artifact_type: "tracking_excel", file_name: "file.xlsx", mime_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", meta: { rows: 1 }, download_url: "/download" }],
    openArtifactId: null,
    selectedRun: { status: "success", id: "run-1" },
    dashboard: { repository_backends: { artifacts: "s3" }, artifact_metadata_persistent: true },
  };
  const calls = [];
  const controller = createReportPanelsController({
    state,
    dom,
    api: async () => ({ items: [] }),
    flash: () => {},
    setBusy: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    formatBytes: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    ARTIFACT_RUNTIME: {
      buildArtifactSectionMarkup: () => '<button data-preview-artifact-id="artifact-1" type="button">preview</button>',
      buildArtifactPreviewMarkup: (cached) => `<pre>${JSON.stringify(cached)}</pre>`,
      buildArtifactEmptyMessage: () => "empty",
      artifactTypeLabel: (value) => String(value ?? ""),
      buildArtifactMetaBits: () => "",
      canPreviewArtifact: () => true,
    },
    RELATED_NOTICE_RUNTIME: null,
    loadDashboardSummary: async () => {},
    touchSyncMeta: () => {},
    syncUrlState: () => {},
    callRunPanelsController: async (methodName, item) => {
      calls.push([methodName, item.id]);
      state.artifactPreviewCache[item.id] = { preview: true };
    },
  });

  controller.renderArtifactsList();
  assert.equal(typeof button.listener, "function");

  await button.listener();

  assert.deepEqual(calls, [["ensureArtifactPreviewCached", "artifact-1"]]);
  assert.equal(state.openArtifactId, "artifact-1");
  assert.deepEqual(state.artifactPreviewCache["artifact-1"], { preview: true });
});

test("report panels controller owns report rendering and artifact empty-state markup", () => {
  const dom = {
    reportSelect: { value: "phase1-artifact-diff" },
    reportStatus: { textContent: "" },
    reportSummary: { textContent: "" },
    reportJson: { textContent: "" },
    reportJobsList: { innerHTML: "" },
    reportJobStatus: { textContent: "" },
    reportJobDetail: { textContent: "" },
    runReportButton: { textContent: "" },
    reportSeedLimit: { value: "3" },
    artifactsList: { innerHTML: "" },
  };
  const state = {
    reportKey: "phase1-artifact-diff",
    reportData: null,
    reportJobs: [],
    reportJob: null,
    selectedReportJobId: null,
    artifactPreviewCache: {},
    artifactSections: [],
    artifacts: [],
    openArtifactId: null,
    selectedRun: { status: "success", id: "run-1" },
    dashboard: { repository_backends: { artifacts: "s3" }, artifact_metadata_persistent: false },
  };

  const controller = createReportPanelsController({
    state,
    dom,
    api: async () => ({ items: [] }),
    flash: () => {},
    setBusy: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    formatBytes: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    ARTIFACT_RUNTIME: {
      buildArtifactEmptyMessage: ({ artifactBackend, persistent, runStatus }) => `empty:${artifactBackend}:${persistent}:${runStatus}`,
      buildArtifactPreviewMarkup: (cached) => `<pre>${JSON.stringify(cached)}</pre>`,
      artifactTypeLabel: (value) => String(value ?? ""),
      buildArtifactMetaBits: () => "",
      canPreviewArtifact: () => true,
    },
    RELATED_NOTICE_RUNTIME: null,
    loadDashboardSummary: async () => {},
    touchSyncMeta: () => {},
    syncUrlState: () => {},
    callRunPanelsController: async () => {},
  });

  controller.renderReport(null, "boom");
  assert.match(dom.reportStatus.textContent, /boom/);
  assert.equal(dom.reportSummary.textContent, "{}");
  assert.equal(dom.reportJson.textContent, "{}");

  controller.renderReport({ summary: { matched_count: 3 } });
  assert.match(dom.reportStatus.textContent, /3/);
  assert.equal(dom.reportSummary.textContent, JSON.stringify({ matched_count: 3 }));

  controller.renderReportJobs([]);
  assert.match(dom.reportJobsList.innerHTML, /empty-state/);

  controller.renderReportJob(null, "err");
  assert.match(dom.reportJobStatus.textContent, /err/);
  assert.equal(dom.reportJobDetail.textContent, "{}");

  assert.equal(controller.buildArtifactEmptyMessage(), "empty:s3:false:success");
  assert.equal(controller.renderArtifactPreviewMarkup("artifact-1"), "<pre>undefined</pre>");
});
