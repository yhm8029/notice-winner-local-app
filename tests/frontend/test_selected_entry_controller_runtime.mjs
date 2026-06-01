import test from "node:test";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const controllerUrl = pathToFileURL(path.resolve(__dirname, "../../frontend/selected-entry-controller.js")).href;

function createClassList() {
  const classes = new Set();
  return {
    add: (...tokens) => tokens.forEach((token) => classes.add(token)),
    remove: (...tokens) => tokens.forEach((token) => classes.delete(token)),
    contains: (token) => classes.has(token),
    toggle: (token, force) => {
      const shouldAdd = force === undefined ? !classes.has(token) : Boolean(force);
      if (shouldAdd) {
        classes.add(token);
        return true;
      }
      classes.delete(token);
      return false;
    },
  };
}

function createNode(initial = {}) {
  return {
    classList: createClassList(),
    textContent: "",
    innerHTML: "",
    value: "",
    disabled: false,
    focus: () => {},
    select: () => {},
    querySelectorAll: () => [],
    ...initial,
  };
}

async function loadControllerModule() {
  return import(controllerUrl);
}

test("selected entry controller renders and syncs with fallback helpers", async () => {
  const { createSelectedEntryController } = await loadControllerModule();
  const calls = {
    audit: 0,
    changeEvents: 0,
    openDrawer: 0,
    closeDrawer: 0,
    syncUrlState: 0,
  };
  const dom = {
    entryEmptyState: createNode(),
    entryEditor: createNode(),
    auditLogList: createNode(),
    entryFieldGrid: createNode(),
    entryDiagnosticsList: createNode(),
    selectedEntryChangeList: createNode(),
    saveEntryButton: createNode(),
    clearEntryButton: createNode(),
    patchValue: createNode({ value: "" }),
    patchCurrentValue: createNode(),
    patchOverrideMeta: createNode(),
    patchField: createNode({ value: "manager_name" }),
    entryTitle: createNode(),
    entryMeta: createNode(),
    entryJson: createNode(),
    drawerTitle: createNode(),
    drawerMeta: createNode(),
    drawerStatusLine: createNode(),
    drawerJson: createNode(),
    drawerFieldList: createNode(),
  };
  const state = {
    selectedEntry: null,
    selectedEntryId: null,
    selectedEntryChangeEvents: [],
    selectedEntryChangeEventsLoading: false,
    drawerOpen: true,
  };

  const controller = createSelectedEntryController({
    dom,
    state,
    buildSelectedEntryChangeEventsMarkup: () => "<div class=\"changes\">changes</div>",
    buildSelectedEntryMeta: (entry, { summaryOnly = false } = {}) => `${entry.project_name}|${summaryOnly}`,
    buildEntryDiagnosticsMarkup: () => "<div class=\"diagnostics\">diag</div>",
    buildEntryFieldGridMarkup: (entry, activeField) => `<div class=\"fields\">${entry.project_name}:${activeField}</div>`,
    buildDrawerFieldListMarkup: (entry) => `<div class=\"drawer-fields\">${entry.project_name}</div>`,
    truncate: (value) => String(value ?? ""),
    escapeHtml: (value) => String(value ?? ""),
    requireSelectedEntryRuntime: () => null,
    formatJson: (value) => JSON.stringify(value),
    EDITABLE_FIELDS: ["project_name", "manager_name"],
    loadSelectedEntryAudit: async () => {
      calls.audit += 1;
    },
    loadSelectedEntryChangeEvents: async () => {
      calls.changeEvents += 1;
    },
    openDrawer: () => {
      calls.openDrawer += 1;
    },
    closeDrawer: () => {
      calls.closeDrawer += 1;
    },
    syncUrlState: () => {
      calls.syncUrlState += 1;
    },
  });

  controller.renderSelectedEntryLoading({ project_name: "Alpha" }, "boom");
  assert.equal(dom.entryEmptyState.textContent, "Alpha \uC0C1\uC138\uB97C \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. boom");
  assert.equal(dom.entryEditor.classList.contains("hidden"), true);
  assert.equal(
    dom.auditLogList.innerHTML,
    '<div class="empty-state">\uC0C1\uC138 \uC815\uBCF4\uB97C \uBD88\uB7EC\uC624\uBA74 \uAC10\uC0AC \uB85C\uADF8\uAC00 \uD45C\uC2DC\uB429\uB2C8\uB2E4.</div>',
  );
  assert.equal(
    dom.entryFieldGrid.innerHTML,
    '<div class="empty-state">\uC0C1\uC138 \uD544\uB4DC\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
  );
  assert.equal(
    dom.selectedEntryChangeList.innerHTML,
    '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
  );

  state.selectedEntryId = "entry-1";
  state.selectedEntryChangeEvents = [{ id: "change-1" }];
  controller.renderSelectedEntryChangeEvents();
  assert.match(dom.selectedEntryChangeList.innerHTML, /changes/);

  state.selectedEntryId = "entry-1";
  state.selectedEntryChangeEvents = [];
  controller.renderSelectedEntryChangeEvents();
  assert.equal(
    dom.selectedEntryChangeList.innerHTML,
    '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD \uC774\uB825\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.</div>',
  );

  state.selectedEntryId = null;
  state.selectedEntryChangeEvents = [];
  controller.renderSelectedEntryChangeEvents();
  assert.equal(
    dom.selectedEntryChangeList.innerHTML,
    "\uD504\uB85C\uC81D\uD2B8\uB97C \uC120\uD0DD\uD558\uBA74 \uCD5C\uADFC \uBCC0\uACBD\uC744 \uD45C\uC2DC\uD569\uB2C8\uB2E4.",
  );

  controller.renderSelectedEntry(null);
  assert.equal(
    dom.entryEmptyState.textContent,
    "\uD504\uB85C\uC81D\uD2B8 \uD604\uD669 \uD56D\uBAA9\uC744 \uC120\uD0DD\uD558\uBA74 \uD544\uB4DC\uB97C \uD558\uB098\uC529 \uC218\uC815\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
  );
  assert.equal(dom.auditLogList.innerHTML, '<div class="empty-state">No audit logs loaded.</div>');
  assert.equal(dom.entryFieldGrid.innerHTML, '<div class="empty-state">Select an entry to browse fields.</div>');

  state.selectedEntry = {
    id: "entry-1",
    project_name: "Alpha",
    entry_key: "E-1",
    row_no: 7,
    demand_org_name: "Org",
    architect_office: "Arch",
    overridden_fields: ["manager_name"],
    manager_name: "Kim",
  };
  controller.syncPatchValueFromSelectedEntry();
  assert.equal(dom.patchValue.value, "Kim");
  assert.equal(dom.patchCurrentValue.textContent, "Kim");
  assert.equal(dom.patchOverrideMeta.textContent, "override active");
  assert.equal(dom.clearEntryButton.disabled, false);
  assert.match(dom.entryFieldGrid.innerHTML, /manager_name/);

  controller.renderSelectedEntry(state.selectedEntry, { summaryOnly: true });
  assert.equal(dom.entryTitle.textContent, "Alpha");
  assert.equal(dom.entryMeta.textContent, "Alpha|true");
  assert.equal(
    dom.auditLogList.innerHTML,
    '<div class="empty-state">\uAC10\uC0AC \uB85C\uADF8\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
  );
  assert.equal(
    dom.selectedEntryChangeList.innerHTML,
    '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
  );
  assert.equal(
    dom.entryDiagnosticsList.innerHTML,
    '<div class="empty-state">\uC0C1\uC138 source\uC640 \uADFC\uAC70\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
  );
  assert.equal(dom.drawerTitle.textContent, "Alpha");
  assert.equal(calls.audit, 0);
  assert.equal(calls.changeEvents, 0);
  assert.equal(calls.openDrawer, 1);
  assert.equal(calls.syncUrlState, 2);
});
