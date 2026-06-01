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
  return context.window.SPMSTrackerBoardRuntime;
}

function loadTrackerBoardRenderersWithFallbackRuntime() {
  const appSource = fs.readFileSync(path.join(__dirname, "..", "app-runtime-body.js"), "utf8");
  const runtimeSource = fs.readFileSync(path.join(__dirname, "..", "tracker-render-fallback-runtime.js"), "utf8");
  const entryRuntimeSource = fs.readFileSync(path.join(__dirname, "..", "tracker-render-fallback-entry-runtime.js"), "utf8");
  const boardRuntimeSource = fs.readFileSync(path.join(__dirname, "..", "tracker-render-fallback-board-runtime.js"), "utf8");
  const start = appSource.indexOf("function buildTrackerBoardCellMarkupFallback(");
  const end = appSource.indexOf("function beginTrackerBoardEdit(");
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate tracker board renderers in app-runtime-body.js");
  }
  const context = {
    window: {},
    TRACKER_BOARD_RUNTIME: null,
    TRACKER_RENDER_FALLBACK_RUNTIME: null,
    getTrackerRenderFallbackRuntime() {
      return context.TRACKER_RENDER_FALLBACK_RUNTIME;
    },
    getTrackerRenderFallbackHelpers() {
      return {
        renderTrackerBoardHeaderCell(column, options) {
          return context.TRACKER_RENDER_FALLBACK_RUNTIME.renderTrackerBoardHeaderCellFallback(column, options);
        },
        isTrackerBoardBlankValue(value) {
          return context.TRACKER_RENDER_FALLBACK_RUNTIME.isTrackerBoardBlankValueFallback(value);
        },
        sortTrackerBoardEntries(entries, options, helpers) {
          return context.TRACKER_RENDER_FALLBACK_RUNTIME.sortTrackerBoardEntriesFallback(entries, options, helpers);
        },
        buildTrackerBoardCellMarkupFallback(payload, helpers) {
          if (payload?.trackerBoardEdit?.entryId === payload?.entry?.id && payload?.trackerBoardEdit?.fieldName === payload?.column?.key) {
            return context.TRACKER_RENDER_FALLBACK_RUNTIME.renderTrackerBoardEditingCellFallback({
              entry: payload.entry,
              fieldName: payload.column.key,
              label: payload.column.label,
              value: payload.trackerBoardEdit.draftValue,
              saving: payload.trackerBoardEdit.saving,
              errorMessage: payload.trackerBoardEdit.errorMessage,
            }, helpers);
          }
          return context.TRACKER_RENDER_FALLBACK_RUNTIME.renderTrackerBoardCellFallback(payload, helpers);
        },
        buildTrackerBoardEditingCellMarkupFallback(payload, helpers) {
          return context.TRACKER_RENDER_FALLBACK_RUNTIME.renderTrackerBoardEditingCellFallback(payload, helpers);
        },
        renderTrackerBoardCell(payload, helpers) {
          return this.buildTrackerBoardCellMarkupFallback(payload, helpers);
        },
        renderTrackerBoardEditingCell(payload, helpers) {
          return context.TRACKER_RENDER_FALLBACK_RUNTIME.renderTrackerBoardEditingCellFallback(payload, helpers);
        },
      };
    },
    APP_SUPPORT: {
      buildTrackerBoardCellMarkupFallbackBridge({ payload, fallbackHelpers = null, runtime = null, escapeHtml, textareaFields } = {}) {
        return fallbackHelpers?.buildTrackerBoardCellMarkupFallback?.(payload, { escapeHtml, textareaFields })
          || runtime?.renderTrackerBoardCellFallback?.(payload, { escapeHtml, textareaFields })
          || "";
      },
      buildTrackerBoardEditingCellMarkupFallbackBridge({ payload, fallbackHelpers = null, runtime = null, escapeHtml, textareaFields } = {}) {
        return fallbackHelpers?.buildTrackerBoardEditingCellMarkupFallback?.(payload, { escapeHtml, textareaFields })
          || runtime?.renderTrackerBoardEditingCellFallback?.(payload, { escapeHtml, textareaFields })
          || "";
      },
      renderTrackerBoardCellBridge({ payload, TRACKER_BOARD_RUNTIME = null, fallbackHelpers = null, escapeHtml, textareaFields, buildTrackerBoardCellMarkupFallback } = {}) {
        return TRACKER_BOARD_RUNTIME?.renderTrackerBoardCell?.(payload, { escapeHtml, textareaFields })
          || fallbackHelpers?.renderTrackerBoardCell?.(payload, { escapeHtml, textareaFields })
          || buildTrackerBoardCellMarkupFallback(payload, { escapeHtml, textareaFields });
      },
      renderTrackerBoardEditingCellBridge({ payload, TRACKER_BOARD_RUNTIME = null, fallbackHelpers = null, escapeHtml, textareaFields, buildTrackerBoardEditingCellMarkupFallback } = {}) {
        return TRACKER_BOARD_RUNTIME?.renderTrackerBoardEditingCell?.(payload, { escapeHtml, textareaFields })
          || fallbackHelpers?.renderTrackerBoardEditingCell?.(payload, { escapeHtml, textareaFields })
          || buildTrackerBoardEditingCellMarkupFallback(payload, { escapeHtml, textareaFields });
      },
    },
    TRACKER_BOARD_TEXTAREA_FIELDS: new Set(["project_name", "progress_note"]),
    state: {
      trackerBoardEdit: {
        entryId: null,
        fieldName: "",
        draftValue: "Draft <value>",
        saving: false,
        errorMessage: "",
      },
    },
    escapeHtml,
  };
  vm.createContext(context);
  vm.runInContext(entryRuntimeSource, context, { filename: path.join(__dirname, "..", "tracker-render-fallback-entry-runtime.js") });
  vm.runInContext(boardRuntimeSource, context, { filename: path.join(__dirname, "..", "tracker-render-fallback-board-runtime.js") });
  vm.runInContext(runtimeSource, context, { filename: path.join(__dirname, "..", "tracker-render-fallback-runtime.js") });
  context.TRACKER_RENDER_FALLBACK_RUNTIME = context.window.SPMSTrackerRenderFallbackRuntime;
  vm.runInContext(appSource.slice(start, end), context);
  return context;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

test("buildTrackerBoardHeaderCell renders active blank-priority header", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.buildTrackerBoardHeaderCell(
    { key: "demand_contact", label: "Contact" },
    {
      trackerBoardBlankPriorityFields: new Set(["demand_contact"]),
      trackerBoardSort: { fieldName: "demand_contact" },
      escapeHtml,
    },
  );
  assert.match(html, /data-board-sort-field="demand_contact"/);
  assert.match(html, /tracker-board-sort-trigger is-active/);
});

test("isTrackerBoardBlankValue treats whitespace as blank", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  assert.equal(runtime.isTrackerBoardBlankValue("   "), true);
  assert.equal(runtime.isTrackerBoardBlankValue("alpha"), false);
});

test("buildTrackerBoardCellMarkup renders display number cells as plain td", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.buildTrackerBoardCellMarkup(
    {
      entry: { id: "entry-1", overridden_fields: [], display_no: 7 },
      column: { key: "display_no", label: "NO.", editable: false },
      displayNo: 7,
    },
    { escapeHtml },
  );
  assert.equal(html, "<td>7</td>");
});

test("buildTrackerBoardCellMarkup preserves selector contract for editable override cells", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.buildTrackerBoardCellMarkup(
    {
      entry: { id: "entry-1", project_name: "Alpha", overridden_fields: ["project_name"] },
      column: { key: "project_name", label: "Project name", editable: true },
      displayNo: 1,
    },
    { escapeHtml },
  );
  assert.match(html, /data-board-edit-trigger="true"/);
  assert.match(html, /data-board-edit-entry-id="entry-1"/);
  assert.match(html, /data-board-edit-field="project_name"/);
  assert.match(html, />override<\/span>/);
  assert.doesNotMatch(html, /data-board-edit-form="true"/);
  assert.doesNotMatch(html, /data-board-edit-input="true"/);
  assert.doesNotMatch(html, /data-board-edit-active="true"/);
});

test("buildTrackerBoardCellMarkup ignores editing-only payload fields", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.buildTrackerBoardCellMarkup(
    {
      entry: { id: "entry-2", project_name: "Alpha", overridden_fields: [] },
      column: { key: "project_name", label: "Project name", editable: true },
      displayNo: 2,
      isEditing: true,
      editingCellMarkup: "<td class=\"broken\">broken</td>",
    },
    { escapeHtml },
  );
  assert.match(html, /data-board-edit-trigger="true"/);
  assert.doesNotMatch(html, /broken/);
});

test("buildTrackerBoardEditingCellMarkup renders textarea editing state with contract markers and escaping", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.buildTrackerBoardEditingCellMarkup(
    {
      entry: { id: "entry-3" },
      fieldName: "progress_note",
      label: "Progress note",
      value: 'Working note "alpha" <beta>',
      saving: false,
      errorMessage: "failed <error> & more",
    },
    {
      escapeHtml,
      textareaFields: new Set(["project_name", "progress_note"]),
    },
  );
  assert.match(html, /<textarea[\s\S]*rows="4"/);
  assert.match(html, /data-board-edit-form="true"/);
  assert.match(html, /data-board-edit-input="true"/);
  assert.match(html, /data-board-edit-active="true"/);
  assert.match(html, /data-board-edit-entry-id="entry-3"/);
  assert.match(html, /data-board-edit-field="progress_note"/);
  assert.match(html, /Progress note/);
  assert.match(html, /Working note &quot;alpha&quot; &lt;beta&gt;/);
  assert.match(html, /tracker-board-edit-error">failed &lt;error&gt; &amp; more<\/p>/);
  assert.match(html, /tracker-board-edit-save/);
  assert.match(html, /tracker-board-edit-cancel/);
});

test("buildTrackerBoardEditingCellMarkup renders disabled text input controls while saving", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.buildTrackerBoardEditingCellMarkup(
    {
      entry: { id: "entry-4" },
      fieldName: "gross_area_scale",
      label: "Gross area",
      value: "Alpha",
      saving: true,
      errorMessage: "",
    },
    {
      escapeHtml,
      textareaFields: new Set(["project_name", "progress_note"]),
    },
  );
  assert.match(html, /<input[\s\S]*type="text"/);
  assert.match(html, /<input[\s\S]*disabled/);
  assert.match(html, /data-board-edit-form="true"/);
  assert.match(html, /data-board-edit-input="true"/);
  assert.match(html, /data-board-edit-active="true"/);
  assert.match(html, /tracker-board-edit-save" type="submit" disabled>/);
  assert.match(html, /data-board-edit-cancel="true" disabled>/);
  assert.match(html, /tracker-board-edit-hint mono">Enter .* Esc .*<\/p>/);
});

test("renderTrackerBoardHeaderCell renders the primary header cell path", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.renderTrackerBoardHeaderCell(
    { key: "demand_contact", label: "Contact" },
    {
      trackerBoardBlankPriorityFields: new Set(["demand_contact"]),
      trackerBoardSort: { fieldName: "demand_contact" },
      escapeHtml,
    },
  );
  assert.match(html, /data-board-sort-field="demand_contact"/);
  assert.match(html, /tracker-board-sort-trigger is-active/);
});

test("renderTrackerBoardCell renders the primary editable override cell path", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.renderTrackerBoardCell(
    {
      entry: { id: "entry-1", project_name: "Alpha", overridden_fields: ["project_name"] },
      column: { key: "project_name", label: "Project name", editable: true },
      displayNo: 1,
    },
    { escapeHtml },
  );
  assert.match(html, /data-board-edit-trigger="true"/);
  assert.match(html, /data-board-edit-entry-id="entry-1"/);
  assert.match(html, /data-board-edit-field="project_name"/);
  assert.match(html, />override<\/span>/);
});

test("renderTrackerBoardEditingCell renders the primary textarea editing path", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-board-runtime.js"));
  const html = runtime.renderTrackerBoardEditingCell(
    {
      entry: { id: "entry-3" },
      fieldName: "progress_note",
      label: "Progress note",
      value: 'Working note "alpha" <beta>',
      saving: false,
      errorMessage: "failed <error> & more",
    },
    {
      escapeHtml,
      textareaFields: new Set(["project_name", "progress_note"]),
    },
  );
  assert.match(html, /<textarea[\s\S]*rows="4"/);
  assert.match(html, /data-board-edit-form="true"/);
  assert.match(html, /data-board-edit-input="true"/);
  assert.match(html, /data-board-edit-active="true"/);
  assert.match(html, /data-board-edit-entry-id="entry-3"/);
  assert.match(html, /data-board-edit-field="progress_note"/);
});

test("renderTrackerBoardCell and renderTrackerBoardEditingCell fall back through the shared runtime when board runtime is null", () => {
  const context = loadTrackerBoardRenderersWithFallbackRuntime();
  const cellHtml = context.renderTrackerBoardCell({
    entry: { id: "entry-1", project_name: "Alpha", overridden_fields: [] },
    column: { key: "project_name", label: "Project name", editable: true },
    displayNo: 1,
  });
  assert.notEqual(cellHtml, "");
  assert.match(cellHtml, /data-board-edit-trigger="true"/);

  context.state.trackerBoardEdit.entryId = "entry-1";
  context.state.trackerBoardEdit.fieldName = "project_name";
  const editingHtml = context.renderTrackerBoardCell({
    entry: { id: "entry-1", project_name: "Alpha", overridden_fields: [] },
    column: { key: "project_name", label: "Project name", editable: true },
    displayNo: 1,
  });
  assert.notEqual(editingHtml, "");
  assert.match(editingHtml, /data-board-edit-form="true"/);
  assert.match(editingHtml, /data-board-edit-input="true"/);
  assert.match(editingHtml, /data-board-edit-active="true"/);

  const directEditingHtml = context.renderTrackerBoardEditingCell({
    entry: { id: "entry-1" },
    fieldName: "progress_note",
    label: "Progress note",
    value: "Draft <value>",
    saving: false,
    errorMessage: "",
  });
  assert.notEqual(directEditingHtml, "");
  assert.match(directEditingHtml, /data-board-edit-form="true"/);
});
