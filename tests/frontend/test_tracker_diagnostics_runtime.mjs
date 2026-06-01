import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/tracker-diagnostics-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSTrackerDiagnosticsRuntime;
}

test("buildContactResolutionSummaryMarkup renders summary chips and review items", () => {
  const runtime = loadRuntime();
  assert.ok(runtime, "runtime should be attached to window");
  assert.equal(typeof runtime.buildContactResolutionSummaryMarkup, "function");

  const view = runtime.buildContactResolutionSummaryMarkup(
    {
      summary: {
        total_entries: 12,
      },
      status_counts: [
        { status: "resolved", count: 8 },
        { status: "review", count: 3 },
        { status: "missing", count: 1 },
      ],
      reason_counts: [
        { reason: "explicit_owner_org_match", count: 8 },
        { reason: "multiple_owner_candidates", count: 3 },
      ],
      items: [
        {
          entry_id: "entry-1",
          project_name: "Alpha Center",
          demand_org_name: "Seoul City",
          demand_contact: "02-1234-5678",
          resolution_status: "review",
          resolution_reason: "multiple_owner_candidates",
          resolution_phase: "notice",
          resolution_role: "owner_contact",
          resolution_owner_side: "uncertain",
          resolution_owner_side_basis: "manual_review",
          updated_at: "2026-04-05T00:00:00Z",
        },
      ],
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      formatDate: (value) => String(value ?? ""),
      formatStatusLabel: (value) => `status:${value}`,
      formatReasonLabel: (value) => `reason:${value}`,
    }
  );

  assert.match(view.summaryHtml, /status:resolved/);
  assert.match(view.summaryHtml, /status:review/);
  assert.match(view.summaryHtml, /reason:multiple_owner_candidates/);
  assert.match(view.summaryHtml, /12/);
  assert.match(view.listHtml, /Alpha Center/);
  assert.match(view.listHtml, /status:review/);
  assert.match(view.listHtml, /reason:multiple_owner_candidates/);
  assert.match(view.listHtml, /manual_review/);
});

test("buildContactResolutionSummaryMarkup returns empty state when no sample items exist", () => {
  const runtime = loadRuntime();
  const view = runtime.buildContactResolutionSummaryMarkup(
    {
      summary: {
        total_entries: 0,
      },
      status_counts: [],
      reason_counts: [],
      items: [],
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      formatStatusLabel: (value) => String(value ?? ""),
      formatReasonLabel: (value) => String(value ?? ""),
    }
  );

  assert.match(view.summaryHtml, /0/);
  assert.match(view.listHtml, /empty-state/);
});

test("buildTrackerCleanupPreviewMarkup renders scoped preview counts and enables apply", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerCleanupPreviewMarkup, "function");

  const html = runtime.buildTrackerCleanupPreviewMarkup(
    {
      scopeLabel: "tracker_export run-1",
      preview: {
        source_tracker_run_id: "run-1",
        parent_run_id: "parent-1",
        tracker_entry_count: 12,
        child_run_count: 1,
        parent_run_count: 1,
        log_count: 3,
        artifact_count: 2,
      },
      loading: false,
      applying: false,
      canApply: true,
      applyDisabledReason: "",
    },
    {
      escapeHtml: (value) => String(value ?? ""),
    }
  );

  assert.match(html, /tracker_export run-1/);
  assert.match(html, /tracker entries/i);
  assert.match(html, /12/);
  assert.match(html, /data-tracker-cleanup-apply/);
});

test("filterBackfillConflictsBySourceRun keeps only matching source run rows", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.filterBackfillConflictsBySourceRun, "function");

  const items = runtime.filterBackfillConflictsBySourceRun(
    [
      { id: "a", source_run_id: "run-1" },
      { id: "b", source_run_id: "run-2" },
      { id: "c", source_run_id: "run-1" },
    ],
    "run-1"
  );

  assert.deepEqual(items.map((item) => item.id), ["a", "c"]);
});

test("buildBackfillConflictsView selects loading, empty, and loaded states", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildBackfillConflictsView, "function");

  const loadingView = runtime.buildBackfillConflictsView(
    {
      scopeLabel: "tracker_export run-1",
      sourceRunId: "run-1",
      items: [],
      loading: true,
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      buildBackfillConflictsMarkup: () => "<section>loaded</section>",
    }
  );

  assert.equal(loadingView.isEmpty, true);
  assert.equal(loadingView.isLoading, true);
  assert.equal(loadingView.bindActions, false);
  assert.match(loadingView.html, /불러오는 중입니다/);

  const emptyView = runtime.buildBackfillConflictsView(
    {
      scopeLabel: "tracker_export run-1",
      sourceRunId: "run-1",
      items: [],
      loading: false,
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      buildBackfillConflictsMarkup: () => "<section>loaded</section>",
    }
  );

  assert.equal(emptyView.isEmpty, true);
  assert.equal(emptyView.isLoading, false);
  assert.equal(emptyView.bindActions, false);
  assert.match(emptyView.html, /선택한 source run 기준 열린 충돌 항목이 없습니다|열린 충돌 항목이 없습니다/);

  const loadedView = runtime.buildBackfillConflictsView(
    {
      scopeLabel: "tracker_export run-1",
      sourceRunId: "run-1",
      items: [{ id: "a" }],
      loading: false,
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      buildBackfillConflictsMarkup: () => "<section>loaded</section>",
    }
  );

  assert.equal(loadedView.isEmpty, false);
  assert.equal(loadedView.isLoading, false);
  assert.equal(loadedView.bindActions, true);
  assert.equal(loadedView.html, "<section>loaded</section>");
});
