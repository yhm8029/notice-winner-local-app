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

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

test("buildTrackerBoardEmptyStateView returns empty-state markup", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerBoardEmptyStateView, "function");

  const view = runtime.buildTrackerBoardEmptyStateView({
    emptyHtml: '<div class="empty-state">No board rows.</div>',
  });

  assert.match(view.html, /No board rows/);
  assert.equal(view.className, "tracker-board-content empty-state");
});

test("buildSortedTrackerBoardEntries applies blank-priority ordering", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSortedTrackerBoardEntries, "function");

  const entries = runtime.buildSortedTrackerBoardEntries(
    [
      { id: "a", demand_contact: "filled" },
      { id: "b", demand_contact: "" },
      { id: "c", demand_contact: "also filled" },
    ],
    {
      fieldName: "demand_contact",
      blankPriorityFields: ["demand_contact"],
    },
  );

  assert.deepEqual(entries.map((entry) => entry.id), ["b", "a", "c"]);
});

test("buildTrackerBoardMarkup escapes dangerous values and keeps Korean board copy", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildTrackerBoardMarkup, "function");

  const calls = [];
  const trackingEscapeHtml = (value) => {
    calls.push(value);
    return escapeHtml(value);
  };

  const html = runtime.buildTrackerBoardMarkup(
    [
      {
        id: 'entry-"1"&',
        project_name: '<img src=x onerror=alert(1)>',
        demand_contact: "",
        construction_start_date: "",
        overridden_fields: ["project_name"],
      },
      {
        id: "entry-2",
        project_name: "Safe & Sound",
        demand_contact: "filled",
        construction_start_date: "2024-01-01",
        overridden_fields: [],
      },
    ],
    {
      columns: [
        { key: "display_no", label: "NO.", editable: false },
        { key: "project_name", label: "프로젝트명", editable: true },
        { key: "demand_contact", label: "담당자", editable: true },
        { key: "construction_start_date", label: "착공일", editable: true },
      ],
      currentSortField: "demand_contact",
      trackerBoardEdit: {
        entryId: "entry-2",
        fieldName: "demand_contact",
        draftValue: 'editing <value> "danger"',
        saving: false,
        errorMessage: "",
      },
      textareaFields: ["demand_contact"],
      blankPriorityFields: ["demand_contact", "construction_start_date"],
      page: 3,
      pageSize: 10,
      selectedEntryId: "entry-2",
    },
    { escapeHtml: trackingEscapeHtml },
  );

  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.match(html, /entry-&quot;1&quot;&amp;/);
  assert.doesNotMatch(html, /<img src=x onerror=alert\(1\)>/);
  assert.match(html, /빈 값 우선/);
  assert.match(html, /클릭 시 빈 값 우선/);
  assert.match(html, /클릭해 수정/);
  assert.match(html, /저장/);
  assert.match(html, /취소/);
  assert.match(html, /Enter 저장 · Shift\+Enter 줄바꿈 · Esc 취소/);
  assert.match(html, /data-board-entry-id="entry-2"/);
  assert.ok(calls.includes('<img src=x onerror=alert(1)>'));
  assert.ok(calls.includes('entry-"1"&'));
});
