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
  return context.window.SPMSTrackerChangeRuntime;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function createClassList(initial = []) {
  const set = new Set(initial);
  return {
    add(name) {
      set.add(name);
    },
    remove(name) {
      set.delete(name);
    },
    toggle(name, force) {
      if (force === undefined) {
        if (set.has(name)) {
          set.delete(name);
          return false;
        }
        set.add(name);
        return true;
      }
      if (force) {
        set.add(name);
        return true;
      }
      set.delete(name);
      return false;
    },
    contains(name) {
      return set.has(name);
    },
  };
}

function loadTrackerChangePopoverHelpers() {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("function setTrackerChangeBellPopoverOpen(");
  const end = source.indexOf("function renderTrackerChangeEventsPanel(", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate tracker change bell popover helpers in app.js");
  }
  const context = {
    state: {
      trackerChangeBellPopoverOpen: false,
      trackerChangeEventsLoading: false,
      trackerChangeEventsAvailability: "available",
      trackerChangeEvents: [],
    },
    dom: {
      trackerChangeBell: {
        attributes: {},
        setAttribute(name, value) {
          this.attributes[name] = String(value);
        },
      },
      trackerChangeBellPopover: {
        classList: createClassList(["hidden"]),
        innerHTML: "",
      },
    },
    bindTrackerChangeEventActions(target) {
      context.__boundMarkup = target.innerHTML;
    },
    buildTrackerChangeBellPopoverMarkup(items) {
      return `<div data-count="${items.length}">${items.map((item) => item.project_name).join("|")}</div>`;
    },
  };
  vm.createContext(context);
  vm.runInContext(`${source.slice(start, end)}\nglobalThis.__trackerChangePopover = { setTrackerChangeBellPopoverOpen, renderTrackerChangeBellPopover };`, context);
  return context;
}

function loadTrackerChangeBellBehaviorHelpers() {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("function syncTrackerChangeBellVisibility(");
  const end = source.indexOf("function bindTrackerChangeEventActions(", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate tracker change bell behavior helpers in app.js");
  }
  const scrolled = [];
  const context = {
    state: {
      uiMode: "admin",
      selectedEntryId: null,
      drawerOpen: false,
      trackerChangeBellPopoverOpen: true,
    },
    dom: {
      trackerChangeBellShell: {
        classList: createClassList(),
      },
      trackerChangePanel: {
        classList: createClassList(),
        scrollIntoView(options) {
          scrolled.push({ target: "trackerChangePanel", options });
        },
      },
      entryEditor: {
        scrollIntoView(options) {
          scrolled.push({ target: "entryEditor", options });
        },
      },
      trackerEntriesList: null,
      trackerBoard: null,
    },
    setTrackerChangeBellPopoverOpen(nextOpen) {
      context.__popoverClosed = nextOpen;
    },
    syncUrlState() {
      context.__synced = true;
    },
    renderTrackerEntries(entries, options) {
      context.__rendered = { entries, options };
    },
    loadSelectedEntryDetail: async (options) => {
      context.__loaded = options;
      return { id: options.entryId };
    },
    document: {
      querySelector(selector) {
        return {
          scrollIntoView(options) {
            scrolled.push({ target: selector, options });
          },
        };
      },
    },
    CSS: { escape: (value) => value },
    window: {
      setTimeout(fn) {
        context.__timeoutScheduled = true;
        context.__timeoutFn = fn;
        return 1;
      },
      clearTimeout() {},
    },
  };
  vm.createContext(context);
  vm.runInContext(
    `${source.slice(start, end)}\nglobalThis.__trackerChangeBellBehavior = { syncTrackerChangeBellVisibility, focusTrackerChangeEntry, focusTrackerChangePanel };`,
    context,
  );
  context.__scrolled = scrolled;
  return context;
}

test("buildTrackerChangeBellPopoverMarkup renders six items max with direct project actions", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "tracker-change-runtime.js"));
  const html = runtime.buildTrackerChangeBellPopoverMarkup(
    Array.from({ length: 7 }, (_, index) => ({
      id: `event-${index + 1}`,
      tracker_entry_id: `entry-${index + 1}`,
      project_name: `Project ${index + 1}`,
      event_type: index % 2 === 0 ? "field_updated_safe" : "related_notice_added",
      field_name: "demand_contact",
      created_at: `2026-04-06T10:0${index}:00Z`,
      old_value: `old-${index + 1}`,
      new_value: `new-${index + 1}`,
      is_read: index > 3,
    })),
    {
      escapeHtml,
      formatDate: (value) => `date:${value}`,
      formatTrackerChangeEventLabel: (item) => `label:${item.event_type}`,
      buildTrackerChangeEventDescription: (item) => `diff:${item.old_value}->${item.new_value}`,
    },
  );

  assert.match(html, /Project 1/);
  assert.match(html, /Project 6/);
  assert.doesNotMatch(html, /Project 7/);
  assert.match(html, /data-change-entry-id="entry-1"/);
  assert.match(html, /data-tracker-change-open-panel="true"/);
  assert.match(html, /label:field_updated_safe/);
  assert.match(html, /diff:old-1-&gt;new-1/);
});

test("tracker change bell popover helpers toggle visibility and render only six recent items", () => {
  const context = loadTrackerChangePopoverHelpers();
  context.state.trackerChangeEvents = Array.from({ length: 7 }, (_, index) => ({
    project_name: `Project ${index + 1}`,
  }));

  context.__trackerChangePopover.setTrackerChangeBellPopoverOpen(true);
  assert.equal(context.state.trackerChangeBellPopoverOpen, true);
  assert.equal(context.dom.trackerChangeBell.attributes["aria-expanded"], "true");
  assert.equal(context.dom.trackerChangeBellPopover.classList.contains("hidden"), false);

  context.__trackerChangePopover.renderTrackerChangeBellPopover();
  assert.match(context.dom.trackerChangeBellPopover.innerHTML, /data-count="6"/);
  assert.match(context.dom.trackerChangeBellPopover.innerHTML, /Project 6/);
  assert.doesNotMatch(context.dom.trackerChangeBellPopover.innerHTML, /Project 7/);
  assert.equal(context.__boundMarkup, context.dom.trackerChangeBellPopover.innerHTML);

  context.__trackerChangePopover.setTrackerChangeBellPopoverOpen(false);
  assert.equal(context.state.trackerChangeBellPopoverOpen, false);
  assert.equal(context.dom.trackerChangeBell.attributes["aria-expanded"], "false");
  assert.equal(context.dom.trackerChangeBellPopover.classList.contains("hidden"), true);
});

test("tracker change bell visibility helper only shows the bell in admin mode", () => {
  const context = loadTrackerChangeBellBehaviorHelpers();

  context.__trackerChangeBellBehavior.syncTrackerChangeBellVisibility(true);
  assert.equal(context.dom.trackerChangeBellShell.classList.contains("hidden"), false);

  context.__trackerChangeBellBehavior.syncTrackerChangeBellVisibility(false);
  assert.equal(context.dom.trackerChangeBellShell.classList.contains("hidden"), true);
  assert.equal(context.__popoverClosed, false);
});

test("focusTrackerChangeEntry selects the entry and scrolls visible admin targets", async () => {
  const context = loadTrackerChangeBellBehaviorHelpers();
  const entries = [{ id: "entry-7" }];

  await context.__trackerChangeBellBehavior.focusTrackerChangeEntry("entry-7", entries);

  assert.equal(context.state.selectedEntryId, "entry-7");
  assert.equal(context.state.drawerOpen, false);
  assert.deepEqual(JSON.parse(JSON.stringify(context.__rendered)), {
    entries,
    options: { refreshSelectedEntry: true },
  });
  assert.deepEqual(JSON.parse(JSON.stringify(context.__loaded)), {
    entryId: "entry-7",
    silent: true,
    force: true,
  });
  assert.equal(context.__scrolled.length >= 2, true);
});

test("focusTrackerChangePanel scrolls and marks the target so the movement is visible", () => {
  const context = loadTrackerChangeBellBehaviorHelpers();

  context.__trackerChangeBellBehavior.focusTrackerChangePanel();

  assert.equal(context.dom.trackerChangePanel.classList.contains("is-focused"), true);
  assert.equal(context.__timeoutScheduled, true);
  assert.deepEqual(
    JSON.parse(JSON.stringify(context.__scrolled[0])),
    { target: "trackerChangePanel", options: { behavior: "smooth", block: "start" } },
  );

  context.__timeoutFn();
  assert.equal(context.dom.trackerChangePanel.classList.contains("is-focused"), false);
});
