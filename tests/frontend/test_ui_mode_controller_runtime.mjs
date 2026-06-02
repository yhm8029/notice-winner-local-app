import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/ui-mode-controller.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console, URLSearchParams });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSUiModeController;
}

function makeClassList(calls, name) {
  return {
    toggle(token, value) {
      calls.push(["toggle", name, token, value]);
    },
    add(token) {
      calls.push(["add", name, token]);
    },
  };
}

function makeNode(calls, name) {
  return {
    textContent: "",
    classList: makeClassList(calls, name),
    querySelector() {
      return { classList: makeClassList(calls, `${name}.advanced-box`) };
    },
    closest() {
      return null;
    },
  };
}

test("ui mode controller preserves chrome updates and transition loading behavior", () => {
  const runtime = loadRuntime();
  const calls = [];
  const state = {
    uiMode: "admin",
    adminTab: "project-status",
    trackerChangeEventsWarmupHandle: 7,
    selectedRun: { id: "run-1" },
    trackerEntries: [{ id: "entry-1" }],
    backfillConflicts: ["stale"],
    backfillConflictsLoading: true,
  };
  const controller = runtime.createUiModeController({
    state,
    dom: {
      uiModeLabel: makeNode(calls, "uiModeLabel"),
      modeToggleButton: makeNode(calls, "modeToggleButton"),
      authSessionModeToggleButton: makeNode(calls, "authSessionModeToggleButton"),
      apiMetaCard: makeNode(calls, "apiMetaCard"),
      syncMetaCard: makeNode(calls, "syncMetaCard"),
      adminHeaderBar: makeNode(calls, "adminHeaderBar"),
      adminTopNav: makeNode(calls, "adminTopNav"),
      heroCopy: makeNode(calls, "heroCopy"),
      hero: makeNode(calls, "hero"),
      layoutGrid: makeNode(calls, "layoutGrid"),
      panelOrgAdmin: makeNode(calls, "panelOrgAdmin"),
      panelDashboard: makeNode(calls, "panelDashboard"),
      panelStatus: makeNode(calls, "panelStatus"),
      panelForm: makeNode(calls, "panelForm"),
      panelRuns: makeNode(calls, "panelRuns"),
      panelLogs: makeNode(calls, "panelLogs"),
      panelReport: makeNode(calls, "panelReport"),
      panelArtifacts: makeNode(calls, "panelArtifacts"),
      projectPanel: makeNode(calls, "projectPanel"),
      panelSalesSummary: makeNode(calls, "panelSalesSummary"),
      trackerChangePanel: makeNode(calls, "trackerChangePanel"),
      backfillConflictPanel: makeNode(calls, "backfillConflictPanel"),
      panelEditor: makeNode(calls, "panelEditor"),
      panelMissingReport: makeNode(calls, "panelMissingReport"),
      trackerInlineEditor: makeNode(calls, "trackerInlineEditor"),
      trackerEntriesList: makeNode(calls, "trackerEntriesList"),
      trackerTemplateUploadButton: makeNode(calls, "trackerTemplateUploadButton"),
      trackerTemplateResetButton: makeNode(calls, "trackerTemplateResetButton"),
      trackerTemplateStatus: makeNode(calls, "trackerTemplateStatus"),
      trackerExportButton: makeNode(calls, "trackerExportButton"),
      trackerContext: makeNode(calls, "trackerContext"),
      presetPanel: makeNode(calls, "presetPanel"),
      runExecutionContext: makeNode(calls, "runExecutionContext"),
      runForm: {
        querySelector() {
          return { classList: makeClassList(calls, "advanced-box") };
        },
      },
    },
    window: {
      clearTimeout(handle) {
        calls.push(["clearTimeout", handle]);
      },
    },
    DEFAULT_ADMIN_TAB: "project-status",
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => true,
    shouldShowAdminModeToggle: () => true,
    shouldShowSharedGoogleSheetsShell: ({ canLoadProtectedData }) => Boolean(canLoadProtectedData),
    isPendingLegacyAdminAlias: () => false,
    maybePreloadAdminGoogleSheetsBootstrap: () => {
      calls.push(["preload"]);
    },
    syncTrackerChangeBellVisibility: (adminMode) => {
      calls.push(["bell", adminMode]);
    },
    hydrateTrackerChangeEventsCache: () => {
      calls.push(["hydrate"]);
    },
    renderTrackerChangeEventUnreadCount: () => {
      calls.push(["unread"]);
    },
    renderTrackerChangeBellPopover: () => {
      calls.push(["popover"]);
    },
    renderAdminTopNavigation: () => {
      calls.push(["topnav"]);
    },
    renderAdminEmbedPanel: () => {
      calls.push(["embed"]);
    },
    renderTrackerTemplateStatus: () => {
      calls.push(["tracker-template"]);
    },
    loadAdminConsoleData: async (options) => {
      calls.push(["loadAdminConsoleData", options]);
    },
    loadBackfillConflicts: async (options) => {
      calls.push(["loadBackfillConflicts", options]);
    },
    renderBackfillConflictsPanel: () => {
      calls.push(["renderBackfillConflictsPanel"]);
    },
    closeDrawer: () => {
      calls.push(["closeDrawer"]);
    },
    renderAuthUi: () => {
      calls.push(["renderAuthUi"]);
    },
    renderOrganizationAdminPanel: () => {
      calls.push(["renderOrganizationAdminPanel"]);
    },
    renderMySalesClaimsPanel: () => {
      calls.push(["renderMySalesClaimsPanel"]);
    },
    renderSalesSummaryPanel: () => {
      calls.push(["renderSalesSummaryPanel"]);
    },
    renderRunDetail: (run) => {
      calls.push(["renderRunDetail", run]);
    },
    renderTrackerEntries: (entries, options) => {
      calls.push(["renderTrackerEntries", entries, options]);
    },
    loadOrganizationUsers: async (options) => {
      calls.push(["loadOrganizationUsers", options]);
    },
    loadTrackerEntries: async (options) => {
      calls.push(["loadTrackerEntries", options]);
    },
    loadTrackerChangeEventUnreadCount: async (options) => {
      calls.push(["loadTrackerChangeEventUnreadCount", options]);
    },
    loadTrackerChangeEvents: async (options) => {
      calls.push(["loadTrackerChangeEvents", options]);
    },
    clearUserModeRunSelection: (options) => {
      calls.push(["clearUserModeRunSelection", options]);
    },
    hydrateHomeBootstrapCache: () => {
      calls.push(["hydrateHomeBootstrapCache"]);
    },
    loadHomeBootstrap: async (options) => {
      calls.push(["loadHomeBootstrap", options]);
    },
    scheduleTrackerChangeEventsWarmup: () => {
      calls.push(["scheduleTrackerChangeEventsWarmup"]);
    },
  });

  assert.equal(controller.syncUiModeChrome(), true);
  assert.equal(controller.applyUiModeTransition(true, { renderAuth: false }), undefined);

  const functionCallsAfterAdmin = calls.filter(([name]) => name !== "toggle" && name !== "add");
  assert.deepEqual(functionCallsAfterAdmin.map(([name]) => name), [
    "clearTimeout",
    "bell",
    "hydrate",
    "unread",
    "popover",
    "preload",
    "topnav",
    "embed",
    "tracker-template",
    "loadAdminConsoleData",
    "loadBackfillConflicts",
    "renderOrganizationAdminPanel",
    "renderMySalesClaimsPanel",
    "renderSalesSummaryPanel",
    "renderRunDetail",
    "renderTrackerEntries",
    "loadOrganizationUsers",
    "loadTrackerEntries",
    "loadTrackerChangeEventUnreadCount",
    "loadTrackerChangeEvents",
  ]);
  assert.equal(functionCallsAfterAdmin[0][1], 7);
  assert.equal(functionCallsAfterAdmin[1][1], true);
  assert.equal(functionCallsAfterAdmin[9][1].silent, true);
  assert.equal(functionCallsAfterAdmin[10][1].silent, true);
  assert.equal(functionCallsAfterAdmin[15][2].refreshSelectedEntry, true);
  assert.equal(state.trackerChangeEventsWarmupHandle, null);
  assert.equal(state.backfillConflicts.length, 1);
  assert.equal(state.backfillConflictsLoading, true);
  assert.deepEqual(calls.find((call) => call[1] === "panelForm" && call[2] === "hidden"), ["toggle", "panelForm", "hidden", false]);
  for (const hiddenPanelName of [
    "panelDashboard",
    "panelStatus",
    "panelRuns",
    "panelLogs",
    "panelReport",
    "panelArtifacts",
    "panelOrgAdmin",
    "panelSalesSummary",
    "trackerChangePanel",
    "backfillConflictPanel",
    "panelMissingReport",
    "trackerInlineEditor",
  ]) {
    assert.deepEqual(
      calls.find((call) => call[0] === "add" && call[1] === hiddenPanelName && call[2] === "hidden"),
      ["add", hiddenPanelName, "hidden"],
    );
  }

  calls.length = 0;
  state.uiMode = "user";
  state.backfillConflicts = ["stale"];
  state.backfillConflictsLoading = true;
  assert.equal(controller.applyUiModeTransition(false, { renderAuth: true }), undefined);

  const functionCallsAfterUser = calls.filter(([name]) => name !== "toggle" && name !== "add");
  assert.deepEqual(functionCallsAfterUser.map(([name]) => name), [
    "renderBackfillConflictsPanel",
    "closeDrawer",
    "renderAuthUi",
    "renderOrganizationAdminPanel",
    "renderMySalesClaimsPanel",
    "renderSalesSummaryPanel",
    "renderRunDetail",
    "renderTrackerEntries",
    "clearUserModeRunSelection",
    "hydrateHomeBootstrapCache",
    "loadHomeBootstrap",
    "scheduleTrackerChangeEventsWarmup",
  ]);
  assert.equal(functionCallsAfterUser[8][1].sync, true);
  assert.equal(functionCallsAfterUser[10][1].silent, true);
  assert.equal(state.backfillConflicts.length, 0);
  assert.equal(state.backfillConflictsLoading, false);
});

test("ui mode controller shows the dedicated sales recommendations tab without the project status tracker panel", () => {
  const runtime = loadRuntime();
  const calls = [];
  const state = {
    uiMode: "admin",
    adminTab: "sales-recommendations",
    trackerEntries: [],
  };
  const controller = runtime.createUiModeController({
    state,
    dom: {
      layoutGrid: makeNode(calls, "layoutGrid"),
      adminHeaderBar: makeNode(calls, "adminHeaderBar"),
      adminTopNav: makeNode(calls, "adminTopNav"),
      heroCopy: makeNode(calls, "heroCopy"),
      hero: makeNode(calls, "hero"),
      panelTracker: makeNode(calls, "panelTracker"),
      panelSalesRecommendations: makeNode(calls, "panelSalesRecommendations"),
      panelEditor: makeNode(calls, "panelEditor"),
      runForm: {
        querySelector() {
          return { classList: makeClassList(calls, "advanced-box") };
        },
      },
    },
    window: {},
    DEFAULT_ADMIN_TAB: "project-status",
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => true,
    shouldShowAdminModeToggle: () => false,
    shouldShowSharedGoogleSheetsShell: ({ canLoadProtectedData }) => Boolean(canLoadProtectedData),
    isPendingLegacyAdminAlias: () => false,
    maybePreloadAdminGoogleSheetsBootstrap: () => {},
    renderAdminTopNavigation: () => {},
    renderAdminEmbedPanel: () => {},
    renderTrackerTemplateStatus: () => {},
    renderMySalesClaimsPanel: () => {
      calls.push(["renderMySalesClaimsPanel"]);
    },
    renderTrackerEntries: () => {},
  });

  controller.applyUiMode({ renderAuth: false });

  assert.deepEqual(calls.find((call) => call[1] === "layoutGrid" && call[2] === "hidden"), ["toggle", "layoutGrid", "hidden", false]);
  assert.deepEqual(calls.find((call) => call[1] === "panelTracker" && call[2] === "hidden"), ["toggle", "panelTracker", "hidden", true]);
  assert.deepEqual(calls.find((call) => call[1] === "panelSalesRecommendations" && call[2] === "hidden"), ["toggle", "panelSalesRecommendations", "hidden", false]);
  assert.equal(calls.some((call) => call[0] === "renderMySalesClaimsPanel"), true);
});

test("ui mode controller applies ui mode chrome orchestration and minimal-ui route guard", () => {
  const runtime = loadRuntime();
  const calls = [];
  const state = {
    uiMode: "user",
    adminTab: "project-status",
    trackerChangeEventsWarmupHandle: null,
    selectedRun: null,
    trackerEntries: [],
    backfillConflicts: [],
    backfillConflictsLoading: false,
  };
  const controller = runtime.createUiModeController({
    state,
    dom: {
      layoutGrid: makeNode(calls, "layoutGrid"),
      adminHeaderBar: makeNode(calls, "adminHeaderBar"),
      adminTopNav: makeNode(calls, "adminTopNav"),
      heroCopy: makeNode(calls, "heroCopy"),
      hero: makeNode(calls, "hero"),
      apiMetaCard: makeNode(calls, "apiMetaCard"),
      syncMetaCard: makeNode(calls, "syncMetaCard"),
      panelOrgAdmin: makeNode(calls, "panelOrgAdmin"),
      panelDashboard: makeNode(calls, "panelDashboard"),
      panelStatus: makeNode(calls, "panelStatus"),
      panelForm: makeNode(calls, "panelForm"),
      panelRuns: makeNode(calls, "panelRuns"),
      panelLogs: makeNode(calls, "panelLogs"),
      panelReport: makeNode(calls, "panelReport"),
      panelArtifacts: makeNode(calls, "panelArtifacts"),
      projectPanel: makeNode(calls, "projectPanel"),
      panelSalesSummary: makeNode(calls, "panelSalesSummary"),
      trackerChangePanel: makeNode(calls, "trackerChangePanel"),
      backfillConflictPanel: makeNode(calls, "backfillConflictPanel"),
      panelEditor: makeNode(calls, "panelEditor"),
      panelMissingReport: makeNode(calls, "panelMissingReport"),
      trackerInlineEditor: makeNode(calls, "trackerInlineEditor"),
      trackerEntriesList: makeNode(calls, "trackerEntriesList"),
      entriesPrevButton: {
        closest() {
          return { classList: makeClassList(calls, "pagination-row") };
        },
      },
      trackerBoard: {
        closest() {
          return { classList: makeClassList(calls, "tracker-board") };
        },
      },
      trackerTemplateUploadButton: makeNode(calls, "trackerTemplateUploadButton"),
      trackerTemplateResetButton: makeNode(calls, "trackerTemplateResetButton"),
      trackerTemplateStatus: makeNode(calls, "trackerTemplateStatus"),
      trackerExportButton: makeNode(calls, "trackerExportButton"),
      trackerContext: makeNode(calls, "trackerContext"),
      presetPanel: makeNode(calls, "presetPanel"),
      runExecutionContext: makeNode(calls, "runExecutionContext"),
      runForm: {
        querySelector() {
          return { classList: makeClassList(calls, "advanced-box") };
        },
      },
    },
    window: {
      clearTimeout(handle) {
        calls.push(["clearTimeout", handle]);
      },
      __SPMS_TEST_MODE__: true,
      __SPMS_TEST_MINIMAL_UI__: true,
      location: {
        pathname: "/app/",
        search: "",
      },
    },
    DEFAULT_ADMIN_TAB: "project-status",
    APP_ROOT_PATH: "/",
    normalizeLocationPath: (value) => String(value || ""),
    getAdminRoutePath: () => "/app/project-status",
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => true,
    shouldShowAdminModeToggle: () => true,
    shouldShowSharedGoogleSheetsShell: ({ canLoadProtectedData }) => Boolean(canLoadProtectedData),
    isPendingLegacyAdminAlias: () => false,
    maybePreloadAdminGoogleSheetsBootstrap: () => {
      calls.push(["preload"]);
    },
    syncTrackerChangeBellVisibility: (adminMode) => {
      calls.push(["bell", adminMode]);
    },
    hydrateTrackerChangeEventsCache: () => {
      calls.push(["hydrate"]);
    },
    renderTrackerChangeEventUnreadCount: () => {
      calls.push(["unread"]);
    },
    renderTrackerChangeBellPopover: () => {
      calls.push(["popover"]);
    },
    renderAdminTopNavigation: () => {
      calls.push(["topnav"]);
    },
    renderAdminEmbedPanel: () => {
      calls.push(["embed"]);
    },
    renderTrackerTemplateStatus: () => {
      calls.push(["tracker-template"]);
    },
    loadAdminConsoleData: async () => {
      calls.push(["loadAdminConsoleData"]);
    },
    loadBackfillConflicts: async () => {
      calls.push(["loadBackfillConflicts"]);
    },
    renderBackfillConflictsPanel: () => {
      calls.push(["renderBackfillConflictsPanel"]);
    },
    closeDrawer: () => {
      calls.push(["closeDrawer"]);
    },
    renderAuthUi: () => {
      calls.push(["renderAuthUi"]);
    },
    renderOrganizationAdminPanel: () => {
      calls.push(["renderOrganizationAdminPanel"]);
    },
    renderMySalesClaimsPanel: () => {
      calls.push(["renderMySalesClaimsPanel"]);
    },
    renderSalesSummaryPanel: () => {
      calls.push(["renderSalesSummaryPanel"]);
    },
    renderRunDetail: () => {
      calls.push(["renderRunDetail"]);
    },
    renderTrackerEntries: () => {
      calls.push(["renderTrackerEntries"]);
    },
    loadOrganizationUsers: async () => {
      calls.push(["loadOrganizationUsers"]);
    },
    loadTrackerEntries: async () => {
      calls.push(["loadTrackerEntries"]);
    },
    loadTrackerChangeEventUnreadCount: async () => {
      calls.push(["loadTrackerChangeEventUnreadCount"]);
    },
    loadTrackerChangeEvents: async () => {
      calls.push(["loadTrackerChangeEvents"]);
    },
    clearUserModeRunSelection: () => {
      calls.push(["clearUserModeRunSelection"]);
    },
    hydrateHomeBootstrapCache: () => {
      calls.push(["hydrateHomeBootstrapCache"]);
    },
    loadHomeBootstrap: async () => {
      calls.push(["loadHomeBootstrap"]);
    },
    scheduleTrackerChangeEventsWarmup: () => {
      calls.push(["scheduleTrackerChangeEventsWarmup"]);
    },
    syncUrlState: (options) => {
      calls.push(["syncUrlState", options]);
    },
  });

  assert.equal(typeof controller.applyUiMode, "function");
  assert.equal(controller.applyUiMode(), undefined);
  assert.equal(calls[0][0], "preload");
  assert.ok(calls.some(([name]) => name === "topnav"));
  assert.ok(calls.some(([name]) => name === "embed"));
  assert.equal(calls.some(([name]) => name === "syncUiModeChrome"), false);
  assert.equal(calls.some(([name]) => name === "applyUiModeTransition"), false);
  assert.equal(state.uiMode, "user");
});

test("ui mode controller handles toggle and location sync orchestration", () => {
  const runtime = loadRuntime();
  const calls = [];
  const state = {
    uiMode: "admin",
    adminTab: "project-status",
    adminLegacyRoutePath: "",
  };
  const controller = runtime.createUiModeController({
    state,
    window: {
      location: {
        pathname: "/app/project-status",
        search: "?admin_tab=sheet-1",
      },
    },
    canUseAdminMode: () => true,
    clearAdminLegacyRouteIntent: () => {
      calls.push(["clearAdminLegacyRouteIntent"]);
      state.adminLegacyRoutePath = "";
    },
    syncUrlState: (options) => {
      calls.push(["syncUrlState", options]);
    },
    applyUiMode: () => {
      calls.push(["applyUiMode"]);
    },
    getAdminTabByPathname: () => ({ key: "project-status" }),
    resolveUiModeFromLocation: () => "admin",
    resolveLegacyAdminRoutePath: () => "/app/project-status",
    normalizeAdminTab: (value) => `normalized:${value}`,
    clearAdminGoogleSheetPopupStateForTab: (tabKey, options) => {
      calls.push(["clearAdminGoogleSheetPopupStateForTab", tabKey, options]);
    },
  });

  assert.equal(typeof controller.toggleUiMode, "function");
  assert.equal(typeof controller.syncUiModeFromLocation, "function");

  controller.toggleUiMode();
  assert.equal(state.uiMode, "user");
  assert.deepEqual(calls[0], ["clearAdminLegacyRouteIntent"]);
  assert.deepEqual(JSON.parse(JSON.stringify(calls[1])), ["syncUrlState", { historyMode: "push", uiMode: "user" }]);
  assert.equal(calls.length, 2);

  calls.length = 0;
  state.uiMode = "user";
  controller.syncUiModeFromLocation();

  assert.equal(state.uiMode, "admin");
  assert.equal(state.adminLegacyRoutePath, "");
  assert.equal(state.adminTab, "normalized:sheet-1");
  assert.deepEqual(JSON.parse(JSON.stringify(calls)), [
    ["clearAdminGoogleSheetPopupStateForTab", "normalized:sheet-1", { render: false }],
  ]);
});
