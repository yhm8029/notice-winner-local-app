const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadHelpers() {
  const runtimePath = path.join(__dirname, "..", "app-runtime-body-helpers.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const reportPanel = {
    heading: { textContent: "Original title" },
    kicker: { textContent: "Original kicker" },
    note: null,
    querySelector(selector) {
      if (selector === ".panel-heading h2") return this.heading;
      if (selector === ".panel-heading .kicker") return this.kicker;
      if (selector === "#parity-tool-note") return this.note;
      return null;
    },
    insertBefore(node) {
      this.note = node;
    },
  };
  const dom = {
    reportSelect: {
      closest(selector) {
        return selector === ".panel-report" ? reportPanel : null;
      },
    },
    runReportButton: { textContent: "Run" },
    refreshReportButton: { textContent: "Refresh" },
    reportStatus: { nodeType: 1 },
    trackerChangeModal: {
      rendered: false,
      classList: {
        removed: [],
        added: [],
        remove(token) {
          this.removed.push(token);
        },
        add(token) {
          this.added.push(token);
        },
      },
    },
    trackerChangeModalCloseButton: {
      focused: false,
      focus() {
        this.focused = true;
      },
    },
  };
  const state = {
    platformAdminAccount: { draft: null },
    trackerChangeModal: { open: false },
  };
  const document = {
    createElement(tagName) {
      return { tagName, id: "", className: "", textContent: "" };
    },
  };
  class HTMLFormElement {}
  class FormData {
    constructor(form) {
      this.form = form;
    }
    get(name) {
      return this.form?.values?.[name] ?? null;
    }
  }
  const context = vm.createContext({
    window: {
      setTimeout(fn) {
        fn();
      },
    },
    document,
    state,
    dom,
    FormData,
    HTMLFormElement,
  });
  vm.runInContext(source, context, { filename: runtimePath });
  const helpers = context.window.SPMSAppRuntimeBodyHelpers.createAppRuntimeBodyHelpers({
    state,
    dom,
    windowObject: context.window,
    documentObject: document,
    runTypeLabels: { winner_pipeline: "Winner" },
    runViewRuntime: {
      runTypeLabel(runType, labels) {
        return labels[runType] || "";
      },
    },
    renderTrackerChangeEventsPanel() {
      dom.trackerChangeModal.rendered = true;
    },
  });
  return { helpers, state, dom, reportPanel, HTMLFormElement };
}

test("app runtime body helpers normalize drafts and format amounts", () => {
  const { helpers, state, HTMLFormElement } = loadHelpers();
  assert.deepEqual(JSON.parse(JSON.stringify(helpers.normalizePlatformAdminAccountDraft(null))), {
    email: "",
    display_name: "",
    role: "org_member",
    password: "",
  });
  assert.equal(helpers.formatContractAmountInput("1200000"), "1,200,000");
  assert.equal(helpers.formatContractAmountDisplay(" 42 "), "42");
  assert.equal(helpers.formatContractAmountDisplay("", "fallback"), "fallback");
  const form = new HTMLFormElement();
  form.values = {
    email: "admin@example.com",
    display_name: "Admin",
    role: "org_admin",
    password: "secret",
  };
  helpers.syncPlatformAdminAccountDraftFromForm(form);
  assert.deepEqual(JSON.parse(JSON.stringify(state.platformAdminAccount.draft)), {
    email: "admin@example.com",
    display_name: "Admin",
    role: "org_admin",
    password: "secret",
  });
});

test("app runtime body helpers update tracker modal and parity report chrome", () => {
  const { helpers, state, dom, reportPanel } = loadHelpers();
  helpers.openTrackerChangeModal();
  assert.equal(state.trackerChangeModal.open, true);
  assert.equal(dom.trackerChangeModal.rendered, true);
  assert.equal(dom.trackerChangeModalCloseButton.focused, true);
  assert.equal(helpers.isProjectTrackerRun("winner_pipeline"), true);
  assert.equal(helpers.runTypeLabel("winner_pipeline"), "Winner");
  helpers.closeTrackerChangeModal();
  helpers.mountParityReportEnhancements();
  assert.equal(reportPanel.heading.textContent, "\uC120\uD0DD\uC801 \uAC80\uC99D");
  assert.equal(reportPanel.kicker.textContent, "GUI \uBE44\uAD50 \uB3C4\uAD6C");
  assert.equal(dom.runReportButton.textContent, "\uAC80\uC99D \uC2E4\uD589");
  assert.equal(dom.refreshReportButton.textContent, "\uAC80\uC99D \uC0C8\uB85C\uACE0\uCE68");
  assert.equal(reportPanel.note.id, "parity-tool-note");
  assert.equal(helpers.useGlobalTrackerEntriesScope(), true);
  const target = { innerHTML: "" };
  helpers.renderOrgAdminRuntimeReloadFallback(target);
  assert.match(target.innerHTML, /empty-state/);
});
