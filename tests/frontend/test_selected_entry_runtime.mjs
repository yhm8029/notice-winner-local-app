import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/selected-entry-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSSelectedEntryRuntime;
}

test("buildSelectedEntryLoadingView returns loading copy for summary entry", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSelectedEntryLoadingView, "function");

  const view = runtime.buildSelectedEntryLoadingView(
    { project_name: "테스트 프로젝트" },
    { errorMessage: "" },
  );

  assert.equal(view.title, "테스트 프로젝트");
  assert.match(view.emptyStateText, /상세를 불러오는 중/);
  assert.match(view.auditHtml, /감사 로그/);
  assert.match(view.fieldGridHtml, /필드를 불러오는 중/);
});

test("buildSelectedEntryEmptyView returns disabled patch panel defaults", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSelectedEntryEmptyView, "function");

  const view = runtime.buildSelectedEntryEmptyView();

  assert.match(view.emptyStateText, /Select an entry/);
  assert.equal(view.patchValue, "");
  assert.equal(view.patchCurrentValueText, "-");
  assert.equal(view.patchOverrideMetaText, "no override");
  assert.equal(view.clearDisabled, true);
});

test("buildPatchPanelView reflects override state and current field value", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildPatchPanelView, "function");

  const view = runtime.buildPatchPanelView(
    {
      project_name: "강남 개발센터",
      progress_note: "",
      overridden_fields: ["project_name"],
    },
    { fieldName: "project_name" },
  );

  assert.equal(view.patchValue, "강남 개발센터");
  assert.equal(view.patchCurrentValueText, "강남 개발센터");
  assert.equal(view.patchOverrideMetaText, "override active");
  assert.equal(view.clearDisabled, false);
});

test("buildDrawerView returns drawer metadata and field list markup", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildDrawerView, "function");

  const view = runtime.buildDrawerView(
    {
      project_name: "성수 스튜디오",
      entry_key: "entry-7",
      row_no: 14,
      demand_org_name: "테스트 발주처",
      overridden_fields: ["progress_note"],
      progress_note: "조정 중",
    },
    {
      editableFields: ["progress_note"],
      escapeHtml: (value) => String(value),
    },
  );

  assert.equal(view.title, "성수 스튜디오");
  assert.match(view.metaText, /entry-7/);
  assert.match(view.statusLineHtml, /override active/);
  assert.match(view.fieldListHtml, /progress_note/);
});

test("buildSelectedEntryDisplayView combines meta, diagnostics, field grid, and drawer view", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildSelectedEntryDisplayView, "function");

  const view = runtime.buildSelectedEntryDisplayView(
    {
      project_name: "Project Alpha",
      entry_key: "entry-9",
      row_no: 22,
      demand_org_name: "Test Org",
      architect_office: "Test Architect",
      progress_note: "In review",
      overridden_fields: ["progress_note"],
      field_diagnostics: [],
      source_run_id: "source-1",
    },
    {
      summaryOnly: false,
      editableFields: ["progress_note"],
      activeField: "progress_note",
      truncate: (value) => String(value),
      escapeHtml: (value) => String(value),
    },
  );

  assert.match(view.metaText, /entry-9/);
  assert.match(view.fieldGridHtml, /progress_note/);
  assert.match(view.diagnosticsHtml, /empty-state|audit-item/);
  assert.equal(view.drawerView.title, "Project Alpha");
  assert.match(view.drawerView.fieldListHtml, /progress_note/);
});
