import test from "node:test";
import assert from "node:assert/strict";
import { createTrackerRenderController } from "../../frontend/tracker-render-controller.js";

function createClickableElement(attributeName, attributeValue) {
  const listeners = {};
  return {
    listeners,
    disabled: false,
    textContent: "",
    dataset: {},
    addEventListener(type, handler) {
      listeners[type] = handler;
    },
    getAttribute(name) {
      return name === attributeName ? attributeValue : "";
    },
    querySelectorAll() {
      return [];
    },
  };
}

function createTrackerListElement(items) {
  const noticeButtons = [
    createClickableElement("data-entry-notice-view", "entry-1"),
    createClickableElement("data-entry-notice-view", "entry-2"),
  ];
  noticeButtons[0].textContent = "공고문 보기";
  noticeButtons[1].textContent = "공고문 보기";
  return {
    html: "",
    noticeButtons,
    set innerHTML(value) {
      this.html = String(value || "");
    },
    get innerHTML() {
      return this.html;
    },
    querySelectorAll(selector) {
      if (selector === "[data-entry-id]") {
        return items;
      }
      if (selector === "[data-entry-notice-view]") {
        return noticeButtons;
      }
      return [];
    },
  };
}

function createTrackerBoardElement(rows) {
  return {
    className: "",
    html: "",
    set innerHTML(value) {
      this.html = String(value || "");
    },
    get innerHTML() {
      return this.html;
    },
    querySelectorAll(selector) {
      if (selector === "[data-board-entry-id]") {
        return rows;
      }
      return [];
    },
  };
}

function createControllerHarness({ selectionActive = false, openTrackerEntryNoticeViewer } = {}) {
  const listItems = [
    createClickableElement("data-entry-id", "entry-1"),
    createClickableElement("data-entry-id", "entry-2"),
  ];
  const boardRows = [
    createClickableElement("data-board-entry-id", "entry-1"),
    createClickableElement("data-board-entry-id", "entry-2"),
  ];
  const state = {
    uiMode: "admin",
    selectedEntryId: "entry-1",
    trackerRelatedEntryId: null,
    trackerRelatedResolvingEntryId: null,
    trackerEntriesError: "",
    trackerEntries: [
      { id: "entry-1", project_id: "project-1", project_name: "Project One", overridden_fields: [] },
      { id: "entry-2", project_id: "project-2", project_name: "Project Two", overridden_fields: [] },
    ],
    trackerFilters: { page: 1, pageSize: 20 },
    trackerEntryDetailCache: {},
  };
  const calls = [];
  const trackerEntriesList = createTrackerListElement(listItems);
  const trackerBoard = createTrackerBoardElement(boardRows);
  const controller = createTrackerRenderController({
    dom: {
      trackerEntriesList,
      trackerBoard,
    },
    state,
    window: {
      getSelection: () => ({
        isCollapsed: !selectionActive,
        toString: () => (selectionActive ? "Project One" : ""),
      }),
    },
    escapeHtml: (value) => String(value ?? ""),
    formatKoreanDate: (value) => String(value ?? ""),
    formatBuildingAutomationEstimateValue: (_entry, fallback) => String(fallback ?? ""),
    TRACKER_ENTRY_RUNTIME: {
      buildTrackerEntryCardMarkup: ({ entry }) => `<article data-entry-id="${entry.id}">${entry.project_name}</article>`,
    },
    buildTrackerEntryCardMarkupFallback: ({ entry }) => `<article data-entry-id="${entry.id}">${entry.project_name}</article>`,
    renderSalesClaimSection: () => "",
    renderTrackerEntryRelatedNotices: () => "",
    resetTrackerBoardEdit: () => calls.push("resetTrackerBoardEdit"),
    renderSelectedEntry: (...args) => calls.push(["renderSelectedEntry", ...args]),
    buildTrackerEntrySummaryDetail: (entry) => ({ id: entry.id, _summary_only: true }),
    loadSelectedEntryDetail: (...args) => calls.push(["loadSelectedEntryDetail", ...args]),
    toggleTrackerEntryRelated: (...args) => calls.push(["toggleTrackerEntryRelated", ...args]),
    openTrackerEntryNoticeViewer: openTrackerEntryNoticeViewer || ((...args) => calls.push(["openTrackerEntryNoticeViewer", ...args])),
    bindRelatedNoticeViewerButtons: () => calls.push("bindRelatedNoticeViewerButtons"),
    claimSalesProject: (...args) => calls.push(["claimSalesProject", ...args]),
    setSalesNoteDraft: (...args) => calls.push(["setSalesNoteDraft", ...args]),
    saveSalesClaimNote: (...args) => calls.push(["saveSalesClaimNote", ...args]),
    transferSalesClaim: (...args) => calls.push(["transferSalesClaim", ...args]),
    flash: (...args) => calls.push(["flash", ...args]),
    openSalesCloseDialog: (...args) => calls.push(["openSalesCloseDialog", ...args]),
    closeSalesClaim: (...args) => calls.push(["closeSalesClaim", ...args]),
    releaseSalesClaim: (...args) => calls.push(["releaseSalesClaim", ...args]),
    syncUrlState: () => calls.push("syncUrlState"),
    prefetchTrackerEntryDetails: (...args) => calls.push(["prefetchTrackerEntryDetails", ...args]),
    getSalesClaimForProject: () => null,
    getSortedTrackerBoardEntries: (entries) => entries,
    TRACKER_BOARD_COLUMNS: [{ key: "project_name", label: "Project" }],
    renderTrackerBoardHeaderCell: () => "<th>Project</th>",
    renderTrackerBoardCell: ({ entry }) => `<td>${entry.project_name}</td>`,
    toggleTrackerBoardBlankPriority: (...args) => calls.push(["toggleTrackerBoardBlankPriority", ...args]),
    beginTrackerBoardEdit: (...args) => calls.push(["beginTrackerBoardEdit", ...args]),
    saveTrackerBoardEdit: (...args) => calls.push(["saveTrackerBoardEdit", ...args]),
  });
  return { controller, state, calls, listItems, boardRows, trackerEntriesList, trackerBoard };
}

test("tracker card click does not select or rerender while text selection is active", () => {
  const { controller, state, calls, listItems } = createControllerHarness({ selectionActive: true });

  controller.renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
  listItems[1].listeners.click({
    target: { closest: () => null },
  });

  assert.equal(state.selectedEntryId, "entry-1");
  assert.equal(calls.includes("syncUrlState"), false);
});

test("tracker board row click does not select or rerender while text selection is active", () => {
  const { controller, state, calls, boardRows } = createControllerHarness({ selectionActive: true });

  controller.renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
  boardRows[1].listeners.click({
    target: { closest: () => null },
  });

  assert.equal(state.selectedEntryId, "entry-1");
  assert.equal(calls.includes("syncUrlState"), false);
});

test("tracker render controller does not prefetch entry details on page render", () => {
  const { controller, state, calls } = createControllerHarness();

  controller.renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });

  assert.deepEqual(
    calls.filter((call) => Array.isArray(call) && call[0] === "prefetchTrackerEntryDetails"),
    [],
  );
});

test("tracker notice button shows a busy state while opening the notice", async () => {
  let resolveOpen;
  const openPromise = new Promise((resolve) => {
    resolveOpen = resolve;
  });
  const openCalls = [];
  const { controller, state, trackerEntriesList } = createControllerHarness({
    openTrackerEntryNoticeViewer: (...args) => {
      openCalls.push(args);
      return openPromise;
    },
  });

  controller.renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
  const noticeButton = trackerEntriesList.noticeButtons[0];
  noticeButton.listeners.click({
    stopPropagation() {},
  });

  assert.equal(noticeButton.disabled, true);
  assert.equal(noticeButton.textContent, "공고문 여는 중...");
  assert.equal(noticeButton.dataset.originalLabel, "공고문 보기");
  await Promise.resolve();
  assert.equal(openCalls.length, 1);
  assert.equal(openCalls[0][0], "entry-1");

  resolveOpen();
  await openPromise;
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.equal(noticeButton.disabled, false);
  assert.equal(noticeButton.textContent, "공고문 보기");
});
