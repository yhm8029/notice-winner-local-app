import assert from "node:assert/strict";
import test from "node:test";
import { createRunPanelsFormHelpers } from "../../frontend/run-panels-controller-helpers.js";

function createRunForm() {
  const values = {
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    notice_title: "테스트 공고",
    api_scope: "construction",
    collect_mode: "auto",
    simulate_stage_delay_ms: "20",
    llm_model: "",
    llm_max_rows: "20",
    export_row_workers: "8",
  };
  return {
    reset() {},
    querySelector() {
      return null;
    },
    [Symbol.iterator]: undefined,
    _values: values,
  };
}

class FakeFormData {
  constructor(form) {
    this.values = form._values || {};
  }

  get(name) {
    return this.values[name] ?? "";
  }

  entries() {
    return Object.entries(this.values);
  }
}

function createHarness({ selectRun = async () => {} } = {}) {
  const calls = [];
  const previousFormData = globalThis.FormData;
  globalThis.FormData = FakeFormData;
  const button = { textContent: "실행 시작", disabled: false };
  const helpers = createRunPanelsFormHelpers({
    state: {
      dashboard: {},
      runFilters: { page: 3 },
      selectedTrackerRunId: "old-tracker",
      selectedEntryId: "old-entry",
    },
    dom: {
      runForm: createRunForm(),
      submitRunButton: button,
    },
    document: {
      createElement() {
        return {};
      },
    },
    api: async (url, options) => {
      calls.push(["api", url, options?.method || "GET"]);
      return { id: "run-123" };
    },
    flash: (message, tone = "") => calls.push(["flash", message, tone]),
    setBusy: (target, busy, label) => {
      calls.push(["busy", busy, label]);
      target.disabled = busy;
      target.textContent = label;
    },
    loadRuns: async () => calls.push(["loadRuns"]),
    syncUrlState: () => calls.push(["syncUrlState"]),
    selectRun,
    runProgressOverlay: {
      start(runId) {
        calls.push(["overlay.start", runId]);
      },
      update(message) {
        calls.push(["overlay.update", message]);
      },
      complete(message) {
        calls.push(["overlay.complete", message]);
      },
      fail(message) {
        calls.push(["overlay.fail", message]);
      },
      watch(runId, options) {
        calls.push(["overlay.watch", runId, typeof options?.api]);
      },
    },
  });
  return {
    button,
    calls,
    helpers,
    restore() {
      globalThis.FormData = previousFormData;
    },
  };
}

test("createWinnerRun shows progress overlay and releases the button after the run is registered", async () => {
  const harness = createHarness({
    selectRun: async () => new Promise(() => {}),
  });
  try {
    const pending = harness.helpers.createWinnerRun({
      submitButton: harness.button,
      busyLabel: "실행 시작 중...",
    });
    await new Promise((resolve) => setTimeout(resolve, 0));

    assert.deepEqual(harness.calls.slice(0, 5).map((item) => item[0]), [
      "busy",
      "overlay.start",
      "api",
      "overlay.update",
      "flash",
    ]);
    assert.deepEqual(harness.calls.filter((item) => item[0] === "busy").at(-1), ["busy", false, "실행 시작"]);
    assert.deepEqual(harness.calls.filter((item) => item[0] === "overlay.watch").at(-1), ["overlay.watch", "run-123", "function"]);
    assert.equal(harness.button.disabled, false);
    assert.equal(harness.button.textContent, "실행 시작");
    assert.equal(pending instanceof Promise, true);
  } finally {
    harness.restore();
  }
});

test("createWinnerRun leaves completion to the run progress watcher", async () => {
  const harness = createHarness();
  try {
    await harness.helpers.createWinnerRun({
      submitButton: harness.button,
      busyLabel: "실행 시작 중...",
    });

    assert.equal(harness.calls.some((item) => item[0] === "overlay.complete"), false);
    assert.deepEqual(harness.calls.filter((item) => item[0] === "overlay.watch").at(-1), ["overlay.watch", "run-123", "function"]);
  } finally {
    harness.restore();
  }
});
