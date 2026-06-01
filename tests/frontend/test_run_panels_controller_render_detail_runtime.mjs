import test from "node:test";
import assert from "node:assert/strict";
import { createRunPanelsController } from "../../frontend/run-panels-controller.js";

function makeClassList() {
  return {
    values: new Set(),
    add(value) {
      this.values.add(value);
    },
    remove(value) {
      this.values.delete(value);
    },
    contains(value) {
      return this.values.has(value);
    },
  };
}

function makeNode(overrides = {}) {
  return {
    innerHTML: "",
    textContent: "",
    dataset: {},
    disabled: false,
    value: "",
    style: {},
    classList: makeClassList(),
    ...overrides,
  };
}

test("run panels controller renders run detail without RUN_VIEW_RUNTIME", () => {
  const calls = [];
  const dom = {
    runEmptyState: makeNode(),
    runDetail: makeNode(),
    logsList: makeNode(),
    artifactsList: makeNode(),
    runEventStatus: makeNode(),
    runId: makeNode(),
    runStatusBadge: makeNode(),
    runProgress: makeNode(),
    runType: makeNode(),
    runProgressStage: makeNode(),
    runProgressMeta: makeNode(),
    runProgressBar: makeNode({ style: {} }),
    runParams: makeNode(),
    runSummary: makeNode(),
    runError: makeNode(),
    runCreatedAt: makeNode(),
    runStartedAt: makeNode(),
    runFinishedAt: makeNode(),
    runParentId: makeNode(),
    cancelRunButton: makeNode(),
    trackerExportButton: makeNode(),
    refreshRunButton: makeNode(),
    refreshLogsButton: makeNode(),
    refreshArtifactsButton: makeNode(),
    refreshEntriesButton: makeNode(),
  };

  const controller = createRunPanelsController({
    state: {
      selectedTrackerRun: null,
      pollHandle: null,
    },
    dom,
    window: {
      clearTimeout() {},
      setTimeout() {
        return 1;
      },
    },
    RUN_VIEW_RUNTIME: null,
    statusBadge: (value) => `<span>${value}</span>`,
    runTypeLabel: (value) => `type:${value}`,
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    progressPercent: () => 50,
    renderRunExecutionContext(run) {
      calls.push(["renderRunExecutionContext", run?.id || null]);
    },
    syncRunActionButtons(run) {
      calls.push(["syncRunActionButtons", run?.id || null]);
    },
    isProjectTrackerRun: (value) => value === "project_tracker",
    useGlobalTrackerEntriesScope: () => false,
  });

  controller.renderRunDetail({
    id: "run-42",
    status: "success",
    run_type: "project_tracker",
    progress_stage: "done",
    progress_current: 2,
    progress_total: 4,
    params: { q: 1 },
    summary: { rows: 10 },
    error: null,
    created_at: "2026-04-21T00:00:00Z",
    started_at: "2026-04-21T00:00:01Z",
    finished_at: "2026-04-21T00:00:02Z",
    parent_run_id: "parent-1",
  });

  assert.equal(dom.runEmptyState.classList.contains("hidden"), true);
  assert.equal(dom.runDetail.classList.contains("hidden"), false);
  assert.equal(dom.runId.textContent, "run-42");
  assert.equal(dom.runStatusBadge.innerHTML, "<span>success</span>");
  assert.equal(dom.runProgress.textContent, "2 / 4");
  assert.equal(dom.runType.textContent, "type:project_tracker");
  assert.equal(dom.runProgressStage.textContent, "done");
  assert.equal(dom.runProgressMeta.textContent, "2 / 4");
  assert.equal(dom.runProgressBar.style.width, "50%");
  assert.equal(dom.runParams.textContent, JSON.stringify({ q: 1 }));
  assert.equal(dom.runSummary.textContent, JSON.stringify({ rows: 10 }));
  assert.equal(dom.runError.textContent, "null");
  assert.equal(dom.runCreatedAt.textContent, "2026-04-21T00:00:00Z");
  assert.equal(dom.runStartedAt.textContent, "2026-04-21T00:00:01Z");
  assert.equal(dom.runFinishedAt.textContent, "2026-04-21T00:00:02Z");
  assert.equal(dom.runParentId.textContent, "parent-1");
  assert.equal(dom.cancelRunButton.disabled, true);
  assert.equal(dom.trackerExportButton.disabled, false);
  assert.equal(dom.refreshRunButton.disabled, false);
  assert.equal(dom.refreshLogsButton.disabled, false);
  assert.equal(dom.refreshArtifactsButton.disabled, false);
  assert.deepEqual(calls, [["renderRunExecutionContext", "run-42"]]);
});
