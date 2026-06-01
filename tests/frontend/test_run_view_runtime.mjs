import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/run-view-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSRunViewRuntime;
}

test("buildRunDetailViewModel returns stable display values", () => {
  const runtime = loadRuntime();
  assert.ok(runtime, "runtime should be attached to window");
  assert.equal(typeof runtime.buildRunDetailViewModel, "function");

  const view = runtime.buildRunDetailViewModel(
    {
      id: "run-1",
      status: "success",
      run_type: "tracker_export",
      progress_current: "02",
      progress_total: "04",
      progress_stage: "finalize",
      created_at: "2026-04-06T00:00:00Z",
      started_at: null,
      finished_at: null,
      parent_run_id: "parent-1",
      params: { a: 1 },
      summary: { b: 2 },
      error: null,
    },
    {
      runTypeLabel: (value) => `type:${value}`,
      formatDate: (value) => String(value ?? "-"),
      progressPercent: () => 50,
      formatJson: (value) => JSON.stringify(value),
    },
  );

  assert.equal(view.id, "run-1");
  assert.equal(view.status, "success");
  assert.equal(view.runTypeLabel, "type:tracker_export");
  assert.equal(view.progressText, "2 / 4");
  assert.equal(view.progressStage, "finalize");
  assert.equal(view.progressPercent, 50);
  assert.equal(view.paramsText, '{"a":1}');
  assert.equal(view.summaryText, '{"b":2}');
  assert.equal(view.errorText, "{}");
  assert.equal(view.createdAtText, "2026-04-06T00:00:00Z");
  assert.equal(view.startedAtText, "-");
  assert.equal(view.finishedAtText, "-");
  assert.equal(view.parentRunId, "parent-1");
});
