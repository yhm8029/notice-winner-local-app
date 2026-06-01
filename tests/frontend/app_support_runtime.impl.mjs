import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appSupportRuntimePath = path.resolve(__dirname, "../../frontend/app-support-runtime.js");
const appSupportAdminRuntimePath = path.resolve(__dirname, "../../frontend/app-support-admin-runtime.js");
const appSupportOrgRuntimePath = path.resolve(__dirname, "../../frontend/app-support-org-runtime.js");
const appSupportStartupRuntimePath = path.resolve(__dirname, "../../frontend/app-support-startup-runtime.js");
const appSupportAuthRuntimePath = path.resolve(__dirname, "../../frontend/app-support-auth-runtime.js");
const appSupportViewRuntimePath = path.resolve(__dirname, "../../frontend/app-support-view-runtime.js");
const appSupportTrackerDepsRuntimePath = path.resolve(__dirname, "../../frontend/app-support-tracker-deps-runtime.js");
const appSupportUiRuntimePath = path.resolve(__dirname, "../../frontend/app-support-ui-runtime.js");
const appSupportTrackerRuntimePath = path.resolve(__dirname, "../../frontend/app-support-tracker-runtime.js");

function readAppSupportRuntimeSource() {
  return fs.readFileSync(appSupportRuntimePath, "utf8");
}

function loadAppSupportRuntime(window, context) {
  const trackerSource = fs.readFileSync(appSupportTrackerRuntimePath, "utf8");
  vm.runInContext(trackerSource, context, { filename: appSupportTrackerRuntimePath });
  assert.ok(window.SPMSAppSupportTrackerRuntime, "expected app-support tracker runtime to load");
  const adminSource = fs.readFileSync(appSupportAdminRuntimePath, "utf8");
  vm.runInContext(adminSource, context, { filename: appSupportAdminRuntimePath });
  assert.ok(window.SPMSAppSupportAdminRuntime, "expected app-support admin runtime to load");
  const orgSource = fs.readFileSync(appSupportOrgRuntimePath, "utf8");
  vm.runInContext(orgSource, context, { filename: appSupportOrgRuntimePath });
  assert.ok(window.SPMSAppSupportOrgRuntime, "expected app-support org runtime to load");
  const startupSource = fs.readFileSync(appSupportStartupRuntimePath, "utf8");
  vm.runInContext(startupSource, context, { filename: appSupportStartupRuntimePath });
  assert.ok(window.SPMSAppSupportStartupRuntime, "expected app-support startup runtime to load");
  const authSource = fs.readFileSync(appSupportAuthRuntimePath, "utf8");
  vm.runInContext(authSource, context, { filename: appSupportAuthRuntimePath });
  assert.ok(window.SPMSAppSupportAuthRuntime, "expected app-support auth runtime to load");
  const viewSource = fs.readFileSync(appSupportViewRuntimePath, "utf8");
  vm.runInContext(viewSource, context, { filename: appSupportViewRuntimePath });
  assert.ok(window.SPMSAppSupportViewRuntime, "expected app-support view runtime to load");
  const trackerDepsSource = fs.readFileSync(appSupportTrackerDepsRuntimePath, "utf8");
  vm.runInContext(trackerDepsSource, context, { filename: appSupportTrackerDepsRuntimePath });
  assert.ok(window.SPMSAppSupportTrackerDepsRuntime, "expected app-support tracker deps runtime to load");
  const uiSource = fs.readFileSync(appSupportUiRuntimePath, "utf8");
  vm.runInContext(uiSource, context, { filename: appSupportUiRuntimePath });
  assert.ok(window.SPMSAppSupportUiRuntime, "expected app-support ui runtime to load");
  const source = fs.readFileSync(appSupportRuntimePath, "utf8");
  vm.runInContext(source, context, { filename: appSupportRuntimePath });
  assert.ok(window.SPMSAppSupportRuntime, "expected app-support runtime to load");
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

test("app-support runtime exposes shared status and download helpers", () => {
  const window = {
    SPMSAppShellRuntime: {
      ORG_ROLE_LABELS: {
        platform_admin: "platform admin",
        org_admin: "org admin",
        org_member: "org member",
      },
      INVITATION_STATUS_LABELS: {
        pending: "pending label",
        accepted: "accepted label",
      },
      CONTACT_RESOLUTION_STATUS_LABELS: {
        resolved: "resolved label",
        review: "review label",
      },
    },
  };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({
    state: {
      auth: {
        enabled: true,
        user: { role: "org_admin" },
        checking: false,
        authenticated: true,
        authorized: true,
      },
      trackerMissingReport: { summary: { missing_entries: 12 } },
    },
  });

  assert.equal(typeof runtime.formatAccountStatusLabel, "function");
  assert.equal(typeof runtime.formatMembershipStatusLabel, "function");
  assert.equal(typeof runtime.resolveStatusClass, "function");
  assert.equal(typeof runtime.formatDownloadScopeLabel, "function");
  assert.equal(typeof runtime.formatDownloadFormatLabel, "function");
  assert.equal(typeof runtime.formatDownloadSourcePageLabel, "function");
  assert.equal(typeof runtime.normalizeSalesOverviewPayload, "function");
  assert.equal(typeof runtime.buildSalesOverviewCachePayload, "function");
  assert.equal(typeof runtime.mergeSalesOverviewIntoHomeBootstrapPayload, "function");
  assert.equal(typeof runtime.buildHomeBootstrapCachePayload, "function");
  assert.equal(typeof runtime.hasCachedSalesOverviewData, "function");
  assert.equal(typeof runtime.hasCachedHomeBootstrapData, "function");
  assert.equal(typeof runtime.isMissingSalesOverviewEndpointError, "function");
  assert.equal(typeof runtime.isMissingHomeBootstrapEndpointError, "function");
  assert.equal(typeof runtime.buildStorageIdentity, "function");
  assert.equal(typeof runtime.isOutOfRangePageError, "function");
  assert.equal(typeof runtime.extractOutOfRangeTotalRows, "function");
  assert.equal(typeof runtime.resolveActiveTrackerRunId, "function");
  assert.equal(typeof runtime.handleOutOfRangePageError, "function");
  assert.equal(typeof runtime.focusTrackerChangeEntry, "function");
  assert.equal(typeof runtime.formatOrgRoleLabel, "function");
  assert.equal(typeof runtime.formatInvitationStatusLabel, "function");
  assert.equal(typeof runtime.formatContactResolutionStatusLabel, "function");
  assert.equal(typeof runtime.formatContactResolutionReasonLabel, "function");
  assert.equal(typeof runtime.isAdminRole, "function");
  assert.equal(typeof runtime.canUseAdminMode, "function");
  assert.equal(typeof runtime.canLoadProtectedConsoleData, "function");
  assert.equal(typeof runtime.getMissingReportDownloadLimit, "function");
  assert.equal(typeof runtime.createFrontendRuntimeAdapters, "function");
  assert.equal(typeof runtime.createSalesStateHelpers, "function");
  assert.equal(typeof runtime.createAdminTabsHelpers, "function");
  assert.equal(typeof runtime.createOrgAdminHelpers, "function");
  assert.equal(typeof runtime.createOrgAdminControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createAppStartupFacade, "function");
  assert.equal(typeof runtime.createBootstrapCacheHelpers, "function");
  assert.equal(typeof runtime.createTrackerChangeEventHelpers, "function");
  assert.equal(typeof runtime.createTrackerRenderFallbackHelpers, "function");
  assert.equal(typeof runtime.createSalesPanelDepsHelpers, "function");
  assert.equal(typeof runtime.createDownloadControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createSelectedEntryControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createRunPanelsControllerDepsHelpers, "function");
  assert.equal(typeof runtime.callRunPanelsControllerFallback, "function");
  assert.equal(typeof runtime.renderTrackerBoardHeaderCellBridge, "function");
  assert.equal(typeof runtime.isTrackerBoardBlankValueBridge, "function");
  assert.equal(typeof runtime.sortTrackerBoardEntriesBridge, "function");
  assert.equal(typeof runtime.buildTrackerBoardCellMarkupFallbackBridge, "function");
  assert.equal(typeof runtime.buildTrackerBoardEditingCellMarkupFallbackBridge, "function");
  assert.equal(typeof runtime.renderTrackerBoardCellBridge, "function");
  assert.equal(typeof runtime.renderTrackerBoardEditingCellBridge, "function");
  assert.equal(typeof runtime.createReportPanelsControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createConsolePanelsControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createUiModeControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createAdminGoogleSheetsControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createRuntimeEnhancementsDepsHelpers, "function");
  assert.equal(typeof runtime.createTrackerControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createTrackerRenderControllerDepsHelpers, "function");
  assert.equal(typeof runtime.createProjectRelatedControllerDepsHelpers, "function");

  assert.equal(runtime.formatAccountStatusLabel("active"), "active");
  assert.equal(runtime.formatMembershipStatusLabel("inactive"), "inactive");
  assert.equal(runtime.resolveStatusClass("inactive"), "queued");
  assert.equal(runtime.formatDownloadScopeLabel("my"), "my");
  assert.equal(runtime.formatDownloadFormatLabel("csv"), "csv");
  assert.equal(runtime.formatDownloadSourcePageLabel("tracker_entries"), "tracker_entries");
  assert.equal(runtime.formatOrgRoleLabel("org_admin"), "org admin");
  assert.equal(runtime.formatInvitationStatusLabel("pending"), "pending label");
  assert.equal(runtime.formatContactResolutionStatusLabel("resolved"), "resolved label");
  assert.equal(runtime.formatContactResolutionReasonLabel("needs_follow_up"), "needs follow up");
  assert.deepEqual(plain(runtime.normalizeSalesOverviewPayload({
    my_items: [{ id: "mine" }],
    company_items: "not-an-array",
    organization_users: [{ id: "user-1" }],
  })), {
    myItems: [{ id: "mine" }],
    companyItems: [],
    organizationUsers: [{ id: "user-1" }],
  });
  assert.deepEqual(plain(runtime.buildSalesOverviewCachePayload({
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
  })), {
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
  });
  assert.deepEqual(plain(runtime.mergeSalesOverviewIntoHomeBootstrapPayload({
    existing: true,
    tracker_first_page: { items: [{ id: "tracker-1" }] },
  }, {
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
  })), {
    existing: true,
    tracker_first_page: { items: [{ id: "tracker-1" }] },
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
  });
  assert.deepEqual(plain(runtime.buildHomeBootstrapCachePayload({
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
    tracker_first_page: { items: [{ id: "tracker-1" }], page: "2", page_size: "15", total: "3" },
    generated_at: "2026-04-07T00:00:00.000Z",
    snapshot_version: "4",
  })), {
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
    tracker_first_page: { items: [{ id: "tracker-1" }], page: "2", page_size: "15", total: "3" },
    generated_at: "2026-04-07T00:00:00.000Z",
    snapshot_version: 4,
  });
  assert.equal(runtime.hasCachedSalesOverviewData({
    mySalesClaims: [{ id: "claim-1" }],
    companySalesClaims: [],
    organizationUsers: [],
  }), true);
  assert.equal(runtime.hasCachedHomeBootstrapData({
    homeBootstrapTrackerSnapshotActive: false,
    mySalesClaims: [],
    companySalesClaims: [{ id: "claim-1" }],
    organizationUsers: [],
  }), true);
  assert.equal(runtime.isMissingSalesOverviewEndpointError({
    status: 404,
    path: "/api/sales-claims/overview",
    payload: { error: { code: "" } },
  }), true);
  assert.equal(runtime.isMissingHomeBootstrapEndpointError({
    status: 404,
    path: "/api/home-bootstrap",
  }), true);
  assert.equal(runtime.buildStorageIdentity({
    organization_id: " org-123 ",
    local_user_id: " user-456 ",
    email: " USER@Example.COM ",
  }), "org-123|user-456|user@example.com");
  assert.equal(runtime.resolveActiveTrackerRunId(), null);
  const filterState = { page: 4, pageSize: 10 };
  assert.equal(runtime.handleOutOfRangePageError({
    message: "Requested range not satisfiable. There are only 23 rows.",
  }, filterState, "트래커"), true);
  assert.equal(filterState.page, 3);
  assert.equal(runtime.isAdminRole("org_admin"), true);
  assert.equal(runtime.canUseAdminMode(), true);
  assert.equal(runtime.canLoadProtectedConsoleData(), true);
  assert.equal(runtime.getMissingReportDownloadLimit(), 12);
});

test("app-support runtime delegates tracker helper ownership to the tracker support runtime", () => {
  const source = readAppSupportRuntimeSource();

  assert.match(source, /SPMSAppSupportTrackerRuntime/);
  assert.match(source, /TRACKER_SUPPORT_RUNTIME/);
  assert.match(source, /TRACKER_SUPPORT_RUNTIME\?\.createTrackerRenderFallbackHelpers/);
  assert.match(source, /TRACKER_SUPPORT_RUNTIME\?\.createTrackerRenderControllerDepsHelpers/);
  assert.match(source, /if \(typeof factory === "function"\) \{\s*return factory\(options\);/);
  assert.match(source, /if \(typeof factory === "function"\) \{\s*return factory\(deps\);/);
});

test("app-support runtime delegates admin helper ownership to the admin support runtime", () => {
  const source = readAppSupportRuntimeSource();

  assert.match(source, /SPMSAppSupportAdminRuntime/);
  assert.match(source, /ADMIN_SUPPORT_RUNTIME/);
  assert.match(source, /ADMIN_SUPPORT_RUNTIME\?\.createAdminTabsHelpers/);
  assert.match(source, /ADMIN_SUPPORT_RUNTIME\?\.createAdminTabsFacade/);
  assert.match(source, /SPMSAppSupportAdminRuntime\.createAdminTabsHelpers is required/);
  assert.match(source, /SPMSAppSupportAdminRuntime\.createAdminTabsFacade is required/);
});

test("app-support runtime handles run panel fallback dispatch", async () => {
  const calls = [];
  const formValues = {
    '[name="notice_title"]': { value: "" },
    '[name="demand_org"]': { value: "" },
  };
  const window = { SPMSAppShellRuntime: {}, prompt: () => "저장 프리셋" };
  const context = vm.createContext({ window, console, FormData });

  loadAppSupportRuntime(window, context);

  const state = {
    selectedTrackerRun: null,
    pollHandle: 7,
    runPresets: [{ id: "preset-1", name: "기본", params: { notice_title: "테스트" } }],
    selectedPresetId: "",
  };
  const dom = {
    runForm: {
      querySelector(selector) {
        return formValues[selector] || null;
      },
    },
    presetSelect: { value: "preset-1" },
    presetSaveButton: {},
    cancelRunButton: { disabled: false },
    trackerExportButton: { disabled: false },
    refreshRunButton: { disabled: true },
    refreshLogsButton: { disabled: true },
    refreshArtifactsButton: { disabled: true },
  };
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({ state });

  const actionsResult = runtime.callRunPanelsControllerFallback({
    methodName: "syncRunActionButtons",
    args: [{ id: "run-1", status: "success", run_type: "project_tracker" }],
    state,
    dom,
    windowObject: {
      clearTimeout(handle) {
        calls.push(["clearTimeout", handle]);
      },
      prompt: () => "저장 프리셋",
    },
    isProjectTrackerRun(runType) {
      return runType === "project_tracker";
    },
  });

  assert.equal(actionsResult, undefined);
  assert.deepEqual(plain(calls), [["clearTimeout", 7]]);
  assert.equal(state.pollHandle, null);
  assert.equal(dom.cancelRunButton.disabled, true);
  assert.equal(dom.trackerExportButton.disabled, false);
  assert.equal(dom.refreshRunButton.disabled, false);

  const presetCalls = [];
  const presetResult = runtime.callRunPanelsControllerFallback({
    methodName: "applySelectedPreset",
    args: [],
    state,
    dom,
    flash(message, level = "") {
      presetCalls.push(["flash", message, level]);
    },
    dispatch(nextMethod, fallback, ...nextArgs) {
      presetCalls.push(["dispatch", nextMethod, fallback, ...plain(nextArgs)]);
      return undefined;
    },
    windowObject: window,
  });

  assert.equal(presetResult, undefined);
  assert.equal(state.selectedPresetId, "preset-1");
  assert.deepEqual(plain(presetCalls), [
    ["dispatch", "applyPresetParams", null, { notice_title: "테스트" }],
    ["dispatch", "renderRunPresetPanel", null],
    ["flash", "프리셋 적용: 기본", ""],
  ]);
});

test("app-support runtime bridges tracker board render helpers", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const helperCalls = [];
  const fallbackHelpers = {
    renderTrackerBoardHeaderCell(column, options) {
      helperCalls.push(["header", column.key, options.trackerBoardSort.fieldName]);
      return `<th>${column.label}</th>`;
    },
    isTrackerBoardBlankValue(value) {
      helperCalls.push(["blank", value]);
      return value === "";
    },
    sortTrackerBoardEntries(entries, options) {
      helperCalls.push(["sort", options.fieldName]);
      return entries.slice().reverse();
    },
    buildTrackerBoardCellMarkupFallback(payload) {
      helperCalls.push(["cell-fallback", payload.entry.id, payload.column.key]);
      return "<td>fallback-cell</td>";
    },
    buildTrackerBoardEditingCellMarkupFallback(payload) {
      helperCalls.push(["editing-fallback", payload.entry.id, payload.fieldName]);
      return "<td>fallback-editing</td>";
    },
    renderTrackerBoardCell(payload) {
      helperCalls.push(["cell", payload.entry.id, payload.column.key]);
      return "<td>cell</td>";
    },
    renderTrackerBoardEditingCell(payload) {
      helperCalls.push(["editing", payload.entry.id, payload.fieldName]);
      return "<td>editing</td>";
    },
  };

  assert.equal(runtime.renderTrackerBoardHeaderCellBridge({
    column: { key: "project_name", label: "프로젝트명" },
    fallbackHelpers,
    trackerBoardBlankPriorityFields: new Set(["project_name"]),
    trackerBoardSort: { fieldName: "project_name" },
    escapeHtml: (value) => String(value ?? ""),
  }), "<th>프로젝트명</th>");
  assert.equal(runtime.isTrackerBoardBlankValueBridge({
    value: "",
    fallbackHelpers,
  }), true);
  assert.deepEqual(plain(runtime.sortTrackerBoardEntriesBridge({
    entries: [{ id: "entry-1" }, { id: "entry-2" }],
    fallbackHelpers,
    fieldName: "project_name",
    blankPriorityFields: new Set(["project_name"]),
    buildSortedTrackerBoardEntries: (entries) => entries,
  })), [{ id: "entry-2" }, { id: "entry-1" }]);
  assert.equal(runtime.buildTrackerBoardCellMarkupFallbackBridge({
    payload: {
      entry: { id: "entry-1" },
      column: { key: "project_name" },
    },
    fallbackHelpers,
  }), "<td>fallback-cell</td>");
  assert.equal(runtime.buildTrackerBoardEditingCellMarkupFallbackBridge({
    payload: {
      entry: { id: "entry-1" },
      fieldName: "project_name",
    },
    fallbackHelpers,
  }), "<td>fallback-editing</td>");
  assert.equal(runtime.renderTrackerBoardCellBridge({
    payload: {
      entry: { id: "entry-1" },
      column: { key: "project_name" },
    },
    fallbackHelpers,
    buildTrackerBoardCellMarkupFallback: () => "<td>bridge-fallback</td>",
  }), "<td>cell</td>");
  assert.equal(runtime.renderTrackerBoardEditingCellBridge({
    payload: {
      entry: { id: "entry-1" },
      fieldName: "project_name",
    },
    fallbackHelpers,
    buildTrackerBoardEditingCellMarkupFallback: () => "<td>bridge-edit-fallback</td>",
  }), "<td>editing</td>");

  assert.deepEqual(plain(helperCalls), [
    ["header", "project_name", "project_name"],
    ["blank", ""],
    ["sort", "project_name"],
    ["cell-fallback", "entry-1", "project_name"],
    ["editing-fallback", "entry-1", "project_name"],
    ["cell", "entry-1", "project_name"],
    ["editing", "entry-1", "project_name"],
  ]);
});

test("app-support runtime focuses tracker change entries without losing state or scroll behavior", async () => {
  const scrollTargets = [];
  const scrollableEditor = {
    scrollIntoView: (options) => {
      scrollTargets.push(["editor", options]);
    },
  };
  const focusTarget = {
    scrollIntoView: (options) => {
      scrollTargets.push(["entry", options]);
    },
  };
  const state = {
    uiMode: "admin",
    trackerEntries: [{ id: "entry-1" }],
    selectedEntryId: "",
    drawerOpen: false,
  };
  const window = {
    CSS: {
      escape: (value) => `escaped:${value}`,
    },
    SPMSAppShellRuntime: {},
  };
  const context = vm.createContext({
    window,
    document: {
      querySelector: () => focusTarget,
    },
    console,
  });

  loadAppSupportRuntime(window, context);

  const renderCalls = [];
  const detailCalls = [];
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({
    state,
    windowObject: window,
    documentObject: context.document,
    dom: { entryEditor: scrollableEditor },
    syncUrlState: () => {
      renderCalls.push(["syncUrlState"]);
    },
    renderTrackerEntries: (entries, options) => {
      renderCalls.push(["renderTrackerEntries", entries, options]);
    },
    loadSelectedEntryDetail: async (options) => {
      detailCalls.push(options);
      return { ok: true };
    },
  });

  await runtime.focusTrackerChangeEntry("  entry-7  ");
  assert.equal(runtime.resolveActiveTrackerRunId(), null);
  assert.deepEqual(renderCalls[0], ["syncUrlState"]);
  assert.deepEqual(plain(renderCalls[1]), ["renderTrackerEntries", [{ id: "entry-1" }], { refreshSelectedEntry: true }]);
  assert.deepEqual(plain(detailCalls[0]), { entryId: "entry-7", silent: true, force: true });
  assert.equal(context.window.CSS.escape("value"), "escaped:value");
  assert.deepEqual(plain(scrollTargets[0]), ["entry", { behavior: "smooth", block: "center" }]);
  assert.deepEqual(plain(scrollTargets[1]), ["editor", { behavior: "smooth", block: "start" }]);
  assert.equal(state.selectedEntryId, "entry-7");
  assert.equal(state.drawerOpen, false);
});

test("app-support runtime builds admin tab helpers with state-aware behavior", async () => {
  const clickHandlers = [];
  const documentHandlers = [];
  const windowHandlers = [];
  const syncButton = {
    dataset: {},
    addEventListener: (eventName, handler) => {
      if (eventName === "click") {
        clickHandlers.push(handler);
      }
    },
  };
  const trackerChangeBellShell = {
    contains: () => false,
  };
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const state = {
    uiMode: "admin",
    adminTab: "sheet-1",
    adminLegacyRoutePath: "",
    adminGoogleSheetTabs: [{ key: "sheet-1", label: "Sheet One", routePath: "/app/project-status", type: "google_sheet" }],
    adminGoogleSheetsCacheHydrated: true,
    adminGoogleSheetsCacheBootstrapRefreshRequested: true,
    adminGoogleSheetsBootstrapLoading: true,
    adminGoogleSheetsBootstrap: { sync_status: "SYNCED" },
    trackerChangeBellPopoverOpen: true,
    trackerChangeModal: { open: false },
    profileDialog: { open: false },
  };
  let synced = 0;
  let popupClosed = 0;
  let bellClosed = 0;
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({ state });
  const helpers = runtime.createAdminTabsHelpers({
    state,
    dom: {
      adminGoogleSheetsSyncButton: syncButton,
      adminGoogleSheetTable: { dataset: { adminGoogleSheetActiveSheetKey: "sheet-1" } },
      trackerChangeBellShell,
    },
    windowObject: {
      location: { pathname: "/app/project-status" },
      addEventListener: (eventName, handler) => {
        windowHandlers.push({ eventName, handler });
      },
    },
    documentObject: {
      addEventListener: (eventName, handler) => {
        documentHandlers.push({ eventName, handler });
      },
    },
    APP_ROOT_PATH: "/app/",
    DEFAULT_ADMIN_TAB: "project-status",
    ADMIN_TABS: [
      { key: "project-status", routePath: "/app/project-status" },
      { key: "sales-recommendations", routePath: "/app/sales-recommendations", type: "existing" },
    ],
    LEGACY_ADMIN_ROUTE_ALIASES: { "/app/design-list": { labelHint: "Sheet" } },
    adminGoogleSheetsRuntime: {
      isAdminGoogleSheetTabKey: (value) => String(value || "").startsWith("sheet-"),
    },
    adminGoogleSheetsAppRuntime: {
      normalizeAdminGoogleSheetsFilterState: (sheetState) => ({ sort: sheetState?.sort || null, columns: sheetState?.columns || {} }),
      getAdminGoogleSheetsFilterState: (sheetKey) => ({ sort: `sort:${sheetKey}`, columns: {} }),
      getAdminGoogleSheetPopupState: () => ({ open: true }),
      clearAdminGoogleSheetPopupStateForTab: () => {
        popupClosed += 1;
        return true;
      },
      cancelAdminGoogleSheetPopup: () => {
        popupClosed += 1;
      },
      handleAdminGoogleSheetPopupDismissal: () => true,
    },
    canLoadProtectedConsoleData: () => true,
    syncUrlState: () => {
      synced += 1;
    },
    applyUiMode: () => {},
    buildResolvedAdminGoogleSheetTabs: () => state.adminGoogleSheetTabs,
    buildUrlForState: () => "/app/project-status?mode=admin",
    loadAdminGoogleSheetsBootstrap: async () => {},
    loadAdminGoogleSheetPayload: async () => {},
    syncAdminGoogleSheets: async () => {
      synced += 10;
    },
    setTrackerChangeBellPopoverOpen: () => {
      bellClosed += 1;
      state.trackerChangeBellPopoverOpen = false;
    },
    closeTrackerChangeModal: () => {},
    closeProfileDialog: () => {},
  });

  assert.equal(helpers.getAdminRoutePath("project-status"), "/app/project-status");
  assert.equal(helpers.getAdminRoutePath("sales-recommendations"), "/app/sales-recommendations");
  assert.equal(helpers.getAdminTabByPathname("/app/sales-recommendations")?.key, "sales-recommendations");
  assert.equal(helpers.isAdminGoogleSheetTabKey("sheet-9"), true);
  assert.equal(helpers.isProjectStatusRoutePath("/app/project-status"), true);
  assert.equal(helpers.shouldShowAdminGoogleSheetsControls({ panelVisible: true }), true);
  assert.equal(helpers.shouldDeferAdminGoogleSheetPayloadLoad("sheet-1"), true);
  assert.equal(helpers.getAdminGoogleSheetsBootstrapSyncStatus(), "synced");
  assert.deepEqual(plain(helpers.getResolvedAdminTabs()), [
    { key: "project-status", routePath: "/app/project-status" },
    { key: "sales-recommendations", routePath: "/app/sales-recommendations", type: "existing" },
    { key: "sheet-1", label: "Sheet One", routePath: "/app/project-status", type: "google_sheet" },
  ]);
  assert.deepEqual(plain(helpers.getAdminGoogleSheetsFilterState("sheet-1")), {
    sort: "sort:sheet-1",
    columns: {},
  });

  helpers.bindAdminGoogleSheetsActions();
  assert.equal(clickHandlers.length, 1);
  await clickHandlers[0]();
  assert.equal(synced, 10);

  helpers.bindGlobalDismissalListeners();
  helpers.bindGlobalDismissalListeners();
  assert.equal(documentHandlers.length, 1);
  assert.equal(windowHandlers.length, 1);
  documentHandlers[0].handler({ target: null });
  assert.equal(bellClosed, 1);
  windowHandlers[0].handler({ key: "Escape" });
  assert.equal(popupClosed > 0, true);
});

test("app-support runtime builds org admin helpers with state-aware behavior", () => {
  const clickHandlers = [];
  const root = {
    querySelectorAll: () => [{
      getAttribute: () => "https://invite.example.com",
      addEventListener: (_eventName, handler) => {
        clickHandlers.push(handler);
      },
    }],
  };
  const invitationRole = {
    value: "org_member",
    innerHTML: "",
  };
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const state = {
    auth: {
      user: { role: "platform_admin", local_user_id: "user-1" },
      bootstrapEmail: "bootstrap@example.com",
    },
    organizationInvitations: [{ id: "invite-1", invite_url: "keep-me" }],
    organizationPlanSummary: {
      plan_code: "B",
      active_user_limit: 10,
      pending_invite_limit: 3,
      active_user_count: 7,
      pending_invite_count: 2,
    },
  };
  let copiedUrl = "";
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({ state });
  const helpers = runtime.createOrgAdminHelpers({
    state,
    dom: { invitationRole },
    windowObject: {
      setTimeout: (handler) => {
        handler();
        return 1;
      },
      clearTimeout: () => {},
    },
    ORG_ROLE_OPTIONS: ["org_admin", "org_member"],
    formatOrgRoleLabel: (value) => `role:${value}`,
    formatMembershipStatusLabel: (value) => `membership:${value}`,
    escapeHtml: (value) => String(value ?? ""),
    copyInvitationUrl: async (inviteUrl) => {
      copiedUrl = inviteUrl;
    },
    loadOrganizationInvitations: async () => {},
    getOrgAdminRuntime: () => ({
      formatAuthAuditSummary: (item, helpersInput) => `${helpersInput.formatOrgRoleLabel(item.actor_role)}:${helpersInput.formatMembershipStatusLabel(item.membership_status)}`,
    }),
  });

  assert.deepEqual(plain(helpers.mergeOrganizationInvitations([{ id: "invite-1", delivery_status: "" }])), [{
    id: "invite-1",
    invite_url: "keep-me",
    delivery_status: "",
    delivery_message: "",
    initial_password: "",
  }]);
  helpers.upsertOrganizationInvitation({ id: "invite-2", invite_url: "new-url" });
  assert.equal(state.organizationInvitations[0].id, "invite-2");
  helpers.removeOrganizationInvitation("invite-1");
  assert.equal(state.organizationInvitations.some((item) => item.id === "invite-1"), false);
  helpers.bindInvitationCopyButtons(root);
  assert.equal(clickHandlers.length, 1);
  clickHandlers[0]();
  assert.equal(copiedUrl, "https://invite.example.com");
  assert.deepEqual(plain(helpers.getRenderableOrgRoleOptions("custom_role")), ["custom_role", "org_admin", "org_member"]);
  assert.equal(helpers.getCurrentAuthLocalUserId(), "user-1");
  assert.equal(helpers.isProtectedOrganizationMember({ global_role: "platform_admin" }), true);
  assert.equal(helpers.canInviteOrganizationAdmins(), true);
  assert.equal(helpers.canManagePlatformAdminAccounts(), true);
  assert.deepEqual(plain(helpers.getAllowedInvitationRoleOptions()), ["org_member", "org_admin"]);
  helpers.syncInvitationRoleOptions();
  assert.match(invitationRole.innerHTML, /role:org_admin/);
  assert.deepEqual(plain(helpers.getOrganizationPlanSummaryForDisplay()), {
    plan_code: "B",
    active_user_limit: 10,
    pending_invite_limit: 3,
    active_user_count: 7,
    pending_invite_count: 2,
    remaining_active_user_slots: 3,
    remaining_pending_invite_slots: 1,
    active_user_limit_reached: false,
    pending_invite_limit_reached: false,
    upgrade_required: false,
    upgrade_message: "",
    plan_label: "플랜 B",
  });
  assert.equal(helpers.formatAuthAuditEventLabel("invite_revoked"), "초대 철회");
  assert.equal(helpers.formatAuthAuditActorLabel({ actor_display_name: "Admin", actor_email: "admin@example.com", actor_role: "org_admin" }), "Admin · admin@example.com · role:org_admin");
  assert.equal(helpers.formatAuthAuditSummary({ actor_role: "org_admin", membership_status: "active" }), "role:org_admin:membership:active");
});

test("app-support runtime builds org admin controller deps helpers with stable references", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const sharedDeps = {
    state: { orgAdmin: true },
    dom: { orgAdmin: true },
    window: { name: "window" },
    document: { name: "document" },
    navigator: { name: "navigator" },
    api: () => Promise.resolve(),
    flash: () => {},
    setBusy: () => {},
  };
  const formattingDeps = {
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: (value) => `role:${value}`,
    renderInvitationStatus: () => {},
    renderOrganizationAdminPanel: () => {},
    canUseAdminMode: () => true,
    formatDate: (value) => `date:${value}`,
    formatInvitationStatusLabel: (value) => `invite:${value}`,
    formatAccountStatusLabel: (value) => `account:${value}`,
    formatMembershipStatusLabel: (value) => `membership:${value}`,
    resolveStatusClass: (value) => `status:${value}`,
    formatDownloadScopeLabel: (value) => `scope:${value}`,
    formatDownloadFormatLabel: (value) => `format:${value}`,
    formatDownloadSourcePageLabel: (value) => `page:${value}`,
  };
  const actionDeps = {
    syncPlatformAdminAccountDraftFromForm: () => {},
    handlePlatformAdminAccountSubmit: () => {},
    renderOrgAdminRuntimeReloadFallback: () => {},
    canManagePlatformAdminAccounts: () => true,
    resetOrganizationMemberPassword: () => Promise.resolve(),
    requireConsoleDataRuntime: () => ({ runtime: true }),
    getConsoleDataRuntimeDeps: () => ({ runtimeDeps: true }),
    requireOrganizationAdminRuntime: () => ({ orgAdminRuntime: true }),
    loadSalesClaimSummaryByUser: () => Promise.resolve(),
    loadClosedSalesClaims: () => Promise.resolve(),
  };
  const runtimeDeps = {
    membershipStatusOptions: ["active"],
    platformAdminAccountRuntime: { runtime: true },
  };
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({ state: sharedDeps.state });
  const helpers = runtime.createOrgAdminControllerDepsHelpers({
    sharedDeps,
    formattingDeps,
    actionDeps,
    runtimeDeps,
  });

  const depsA = helpers.buildOrgAdminControllerDeps();
  const depsB = helpers.buildOrgAdminControllerDeps();

  assert.strictEqual(depsA, depsB);
  assert.strictEqual(depsA.state, sharedDeps.state);
  assert.strictEqual(depsA.dom, sharedDeps.dom);
  assert.strictEqual(depsA.window, sharedDeps.window);
  assert.strictEqual(depsA.document, sharedDeps.document);
  assert.strictEqual(depsA.navigator, sharedDeps.navigator);
  assert.strictEqual(depsA.api, sharedDeps.api);
  assert.strictEqual(depsA.flash, sharedDeps.flash);
  assert.strictEqual(depsA.setBusy, sharedDeps.setBusy);
  assert.strictEqual(depsA.escapeHtml, formattingDeps.escapeHtml);
  assert.strictEqual(depsA.formatOrgRoleLabel, formattingDeps.formatOrgRoleLabel);
  assert.strictEqual(depsA.renderInvitationStatus, formattingDeps.renderInvitationStatus);
  assert.strictEqual(depsA.renderOrganizationAdminPanel, formattingDeps.renderOrganizationAdminPanel);
  assert.strictEqual(depsA.canUseAdminMode, formattingDeps.canUseAdminMode);
  assert.strictEqual(depsA.formatDate, formattingDeps.formatDate);
  assert.strictEqual(depsA.formatInvitationStatusLabel, formattingDeps.formatInvitationStatusLabel);
  assert.strictEqual(depsA.formatAccountStatusLabel, formattingDeps.formatAccountStatusLabel);
  assert.strictEqual(depsA.formatMembershipStatusLabel, formattingDeps.formatMembershipStatusLabel);
  assert.strictEqual(depsA.resolveStatusClass, formattingDeps.resolveStatusClass);
  assert.deepEqual(depsA.membershipStatusOptions, runtimeDeps.membershipStatusOptions);
  assert.strictEqual(depsA.formatDownloadScopeLabel, formattingDeps.formatDownloadScopeLabel);
  assert.strictEqual(depsA.formatDownloadFormatLabel, formattingDeps.formatDownloadFormatLabel);
  assert.strictEqual(depsA.formatDownloadSourcePageLabel, formattingDeps.formatDownloadSourcePageLabel);
  assert.strictEqual(depsA.platformAdminAccountRuntime, runtimeDeps.platformAdminAccountRuntime);
  assert.strictEqual(depsA.syncPlatformAdminAccountDraftFromForm, actionDeps.syncPlatformAdminAccountDraftFromForm);
  assert.strictEqual(depsA.handlePlatformAdminAccountSubmit, actionDeps.handlePlatformAdminAccountSubmit);
  assert.strictEqual(depsA.renderOrgAdminRuntimeReloadFallback, actionDeps.renderOrgAdminRuntimeReloadFallback);
  assert.strictEqual(depsA.canManagePlatformAdminAccounts, actionDeps.canManagePlatformAdminAccounts);
  assert.strictEqual(depsA.resetOrganizationMemberPassword, actionDeps.resetOrganizationMemberPassword);
  assert.strictEqual(depsA.requireConsoleDataRuntime, actionDeps.requireConsoleDataRuntime);
  assert.strictEqual(depsA.getConsoleDataRuntimeDeps, actionDeps.getConsoleDataRuntimeDeps);
  assert.strictEqual(depsA.requireOrganizationAdminRuntime, actionDeps.requireOrganizationAdminRuntime);
  assert.strictEqual(depsA.loadSalesClaimSummaryByUser, actionDeps.loadSalesClaimSummaryByUser);
  assert.strictEqual(depsA.loadClosedSalesClaims, actionDeps.loadClosedSalesClaims);
});

test("app-support runtime builds bootstrap cache helpers with storage-aware behavior", () => {
  const cacheCalls = [];
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({
    state: {
      auth: {
        user: {
          organization_id: "org-1",
          local_user_id: "user-1",
          email: "user@example.com",
        },
      },
    },
  });
  const helpers = runtime.createBootstrapCacheHelpers({
    state: {
      auth: {
        user: {
          organization_id: "org-1",
          local_user_id: "user-1",
          email: "user@example.com",
        },
      },
    },
    cacheRuntime: {
      DEFAULT_MAX_AGE_MS: 1234,
      readEnvelope: (storageKey, options) => {
        cacheCalls.push(["read", storageKey, options]);
        return { payload: { members: [{ id: "member-1" }] } };
      },
      writeEnvelope: (storageKey, payload) => {
        cacheCalls.push(["write", storageKey, payload]);
        return true;
      },
    },
    buildStorageIdentity: (authUser) => `${authUser.organization_id}|${authUser.local_user_id}|${authUser.email}`,
    orgAdminBootstrapStorageKey: "org-admin-key",
  });

  assert.equal(helpers.buildSalesOverviewStorageIdentity(), "org-1|user-1|user@example.com");
  assert.deepEqual(plain(helpers.readConsoleCacheEnvelope("cache-key", { allowStale: true })), {
    payload: { members: [{ id: "member-1" }] },
  });
  assert.equal(helpers.writeConsoleCacheEnvelope("cache-key", { ok: true }), true);
  assert.deepEqual(plain(helpers.buildOrganizationAdminBootstrapCachePayload({
    members: [{ id: "member-1" }],
    invitations: [{ id: "invite-1" }],
    auth_audit_logs: { items: [{ id: "audit-1" }], has_more: true },
    download_audit_logs: { items: [{ id: "download-1" }], has_more: false },
    login_audit_logs: { items: [{ id: "login-1" }], has_more: true },
    generated_at: "2026-04-23T00:00:00Z",
  })), {
    members: [{ id: "member-1" }],
    plan_summary: null,
    invitations: [{ id: "invite-1" }],
    auth_audit_logs: { items: [{ id: "audit-1" }], has_more: true },
    download_audit_logs: { items: [{ id: "download-1" }], has_more: false },
    login_audit_logs: { items: [{ id: "login-1" }], has_more: true },
    generated_at: "2026-04-23T00:00:00Z",
  });
  assert.deepEqual(plain(helpers.readOrganizationAdminBootstrapCache()), {
    members: [{ id: "member-1" }],
    plan_summary: null,
    invitations: [],
    auth_audit_logs: { items: [], has_more: false },
    download_audit_logs: { items: [], has_more: false },
    login_audit_logs: { items: [], has_more: false },
    generated_at: "",
  });
  assert.equal(helpers.persistOrganizationAdminBootstrapCache({ members: [{ id: "member-2" }] }), true);
  assert.equal(cacheCalls[0][0], "read");
  assert.equal(cacheCalls[1][0], "write");
});

test("app-support runtime builds tracker change event helpers with cache-aware behavior", async () => {
  const storage = new Map();
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const state = {
    trackerChangeEvents: [],
    trackerChangeEventsUnread: 0,
    trackerChangeEventsLoadedAt: 0,
    trackerChangeEventsWarmupHandle: null,
    trackerChangeEventsLoading: true,
  };
  let renderedPanel = 0;
  let renderedUnread = 0;
  let unreadLoads = 0;
  let eventLoads = 0;
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({ state });
  const helpers = runtime.createTrackerChangeEventHelpers({
    state,
    windowObject: {
      localStorage: {
        getItem: (key) => storage.get(key) || null,
        setItem: (key, value) => storage.set(key, value),
        removeItem: (key) => storage.delete(key),
      },
      setTimeout: (handler) => {
        handler();
        return 1;
      },
      clearTimeout: () => {},
    },
    storageKey: "tracker-change-cache",
    storageMaxItems: 2,
    cacheTtlMs: 60000,
    canUseAdminMode: () => true,
    renderTrackerChangeEventsPanel: () => {
      renderedPanel += 1;
    },
    renderTrackerChangeEventUnreadCount: () => {
      renderedUnread += 1;
    },
    loadTrackerChangeEventUnreadCount: async () => {
      unreadLoads += 1;
    },
    loadTrackerChangeEvents: async () => {
      eventLoads += 1;
    },
  });

  state.trackerChangeEvents = [{ id: "1" }, { id: "2" }, { id: "3" }];
  state.trackerChangeEventsUnread = 2;
  state.trackerChangeEventsLoadedAt = Date.now();
  helpers.persistTrackerChangeEventsCache();
  assert.deepEqual(plain(JSON.parse(storage.get("tracker-change-cache"))), {
    items: [{ id: "1" }, { id: "2" }],
    unread_count: 2,
    loaded_at: state.trackerChangeEventsLoadedAt,
  });

  storage.set("tracker-change-cache", JSON.stringify({
    items: [{ id: "10" }, { id: "20" }, { id: "30" }],
    unread_count: 3,
    loaded_at: Date.now(),
  }));
  state.trackerChangeEvents = [];
  state.trackerChangeEventsUnread = 0;
  state.trackerChangeEventsLoadedAt = 0;
  assert.equal(helpers.hydrateTrackerChangeEventsCache(), true);
  assert.deepEqual(plain(state.trackerChangeEvents), [{ id: "10" }, { id: "20" }]);
  assert.equal(state.trackerChangeEventsUnread, 3);
  assert.equal(helpers.trackerChangeEventsCacheIsFresh(), true);
  helpers.clearTrackerChangeEventsCache();
  assert.equal(storage.has("tracker-change-cache"), false);
  helpers.scheduleTrackerChangeEventsWarmup();
  assert.equal(state.trackerChangeEventsLoading, false);
  assert.equal(renderedPanel, 1);
  assert.equal(renderedUnread, 1);
  assert.equal(unreadLoads, 1);
  assert.equal(eventLoads, 1);
});

test("app-support runtime builds tracker render fallback helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    dom: { trackerList: {} },
    state: { selectedEntryId: "entry-1" },
    resetTrackerBoardEdit: () => "reset",
    renderTrackerBoard: () => "render-board",
    renderSelectedEntry: () => "render-entry",
    runtimeAdapters: {
      buildTrackerEntriesEmptyStateView: () => "empty",
      buildTrackerEntryCardView: () => "card",
      buildTrackerEntriesListMarkup: () => "list",
      formatKoreanDate: () => "date",
      formatBuildingAutomationEstimateValue: () => "estimate",
      buildTrackerEntrySummaryDetail: () => "summary",
      buildTrackerBoardMarkup: () => "board-markup",
      buildTrackerBoardEmptyStateView: () => "board-empty",
    },
    salesStateHelpers: {
      getSalesClaimForProject: () => ({ id: "claim-1" }),
      setSalesNoteDraft: () => "draft",
    },
    renderSalesClaimSection: () => "sales",
    renderTrackerEntryRelatedNotices: () => "related",
    syncUrlState: () => "sync",
    toggleTrackerEntryRelated: async () => {},
    openTrackerEntryNoticeViewer: async () => {},
    bindRelatedNoticeViewerButtons: () => "bind",
    claimSalesProject: async () => {},
    saveSalesClaimNote: async () => {},
    transferSalesClaim: async () => {},
    flash: () => "flash",
    openSalesCloseDialog: () => "dialog",
    closeSalesClaim: async () => {},
    releaseSalesClaim: async () => {},
    loadSelectedEntryDetail: async () => {},
    prefetchTrackerEntryDetails: () => "prefetch",
    buildTrackerBoardMarkupFallback: () => "board-fallback",
    renderTrackerEntries: () => "render-entries",
    toggleTrackerBoardBlankPriority: () => "toggle-blank",
    beginTrackerBoardEdit: () => "begin-edit",
    saveTrackerBoardEdit: async () => {},
    columns: [{ field: "name" }],
    textareaFields: new Set(["notes"]),
    blankPriorityFields: new Set(["city"]),
    renderTrackerBoardHeaderCell: () => "header",
    renderTrackerBoardCell: () => "cell",
    renderTrackerBoardEditingCell: () => "editing-cell",
    sortTrackerBoardEntriesFallback: (entries) => entries,
  };
  const helpers = runtime.createTrackerRenderFallbackHelpers(deps);

  assert.equal(typeof helpers.buildTrackerEntriesFallbackDeps, "function");
  assert.equal(typeof helpers.buildTrackerBoardFallbackDeps, "function");

  const entriesDeps = helpers.buildTrackerEntriesFallbackDeps(false);
  assert.equal(entriesDeps.dom, deps.dom);
  assert.equal(entriesDeps.state, deps.state);
  assert.equal(entriesDeps.renderTrackerBoard, deps.renderTrackerBoard);
  assert.equal(entriesDeps.buildTrackerEntriesListMarkup, deps.runtimeAdapters.buildTrackerEntriesListMarkup);
  assert.equal(entriesDeps.renderTrackerEntryRelatedNotices, deps.renderTrackerEntryRelatedNotices);
  assert.equal(entriesDeps.getSalesClaimForProject, deps.salesStateHelpers.getSalesClaimForProject);
  assert.equal(entriesDeps.saveSalesClaimNote, deps.saveSalesClaimNote);
  assert.equal(entriesDeps.prefetchTrackerEntryDetails, deps.prefetchTrackerEntryDetails);
  assert.equal(entriesDeps.refreshSelectedEntry, false);

  const boardDeps = helpers.buildTrackerBoardFallbackDeps();
  assert.equal(boardDeps.dom, deps.dom);
  assert.equal(boardDeps.state, deps.state);
  assert.equal(boardDeps.buildTrackerBoardMarkup, deps.runtimeAdapters.buildTrackerBoardMarkup);
  assert.equal(boardDeps.buildTrackerBoardEmptyStateView, deps.runtimeAdapters.buildTrackerBoardEmptyStateView);
  assert.equal(boardDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(boardDeps.beginTrackerBoardEdit, deps.beginTrackerBoardEdit);
  assert.equal(boardDeps.saveTrackerBoardEdit, deps.saveTrackerBoardEdit);
  assert.equal(boardDeps.columns, deps.columns);
  assert.equal(boardDeps.textareaFields, deps.textareaFields);
  assert.equal(boardDeps.blankPriorityFields, deps.blankPriorityFields);
  assert.equal(typeof boardDeps.renderTrackerBoardHeaderCell, "function");
  assert.equal(typeof boardDeps.renderTrackerBoardCell, "function");
  assert.equal(typeof boardDeps.renderTrackerBoardEditingCell, "function");
  assert.equal(boardDeps.sortTrackerBoardEntriesFallback, boardDeps.sortTrackerBoardEntries);
});

test("app-support runtime tracker render fallback helpers tolerate missing grouped helpers", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const helpers = runtime.createTrackerRenderFallbackHelpers({
    runtimeAdapters: null,
    salesStateHelpers: { getSalesClaimForProject: () => ({ id: "claim-2" }) },
  });

  assert.doesNotThrow(() => helpers.buildTrackerEntriesFallbackDeps());
  assert.doesNotThrow(() => helpers.buildTrackerBoardFallbackDeps());

  const entriesDeps = helpers.buildTrackerEntriesFallbackDeps();
  assert.equal(entriesDeps.buildTrackerEntriesEmptyStateView(), null);
  assert.equal(entriesDeps.buildTrackerEntryCardView(), null);
  assert.equal(entriesDeps.buildTrackerEntriesListMarkup(), "");
  assert.equal(entriesDeps.formatKoreanDate("2026-04-23"), "2026-04-23");
  assert.equal(entriesDeps.formatBuildingAutomationEstimateValue(), "");
  assert.deepEqual(entriesDeps.getSalesClaimForProject(), { id: "claim-2" });
  assert.equal(entriesDeps.setSalesNoteDraft("project-1", "memo"), undefined);
  assert.equal(entriesDeps.buildTrackerEntrySummaryDetail(), "");

  const boardDeps = helpers.buildTrackerBoardFallbackDeps();
  assert.equal(boardDeps.buildTrackerBoardMarkup(), "");
  assert.equal(boardDeps.buildTrackerBoardEmptyStateView(), null);
});

test("app-support runtime builds sales panel deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    dom: { salesPanel: {} },
    state: { uiMode: "admin" },
    windowObject: { location: { pathname: "/app/" } },
    api: async () => ({}),
    escapeHtml: (value) => String(value ?? ""),
    runtimeAdapters: {
      getLatestSalesNoteItem: () => null,
      truncate: (value) => String(value ?? ""),
      formatSalesNoteTextForDisplay: (value) => String(value ?? ""),
      formatSalesDateLabel: (value) => String(value ?? ""),
      getSalesNoteEntries: () => [],
      formatContractAmountDisplay: (value) => String(value ?? ""),
      extractContractAmountTextFromSalesNote: () => "",
      salesClaimStatusLabel: (value) => String(value ?? ""),
      renderUserOwnedSalesClaimCard: () => "",
      buildSalesClaimEstimateLabel: () => "estimate-label",
      renderCompanySalesClaimCard: () => "",
      renderUserTrackerClaimSection: () => "",
      buildUserSalesProjectFactsMarkup: () => "",
      buildSalesClaimEstimateLabelMarkup: () => "",
      buildUserOwnedSalesClaimCardMarkup: () => "",
      buildCompanySalesClaimCardMarkup: () => "",
      buildUserTrackerClaimSectionMarkup: () => "",
      formatEokValue: (value) => String(value ?? ""),
      getSalesNoteTimeline: () => [],
      serializeSalesNoteEntry: (value) => String(value ?? ""),
      removeLatestSalesNoteEntry: () => [],
    },
    salesStateHelpers: {
      getVisibleSalesProjectIds: () => [],
      getSalesClaimForProject: () => null,
      getTrackerProjectSnapshot: () => null,
      renderUserSalesProjectFacts: () => "",
      isCurrentUserClaimOwner: () => false,
      canCurrentUserForceRelease: () => false,
      canCurrentUserManageClaim: () => false,
      isActiveSalesClaim: () => false,
      getOrganizationTransferTargets: () => [],
      getSalesNoteDraft: () => "",
      setSalesNoteDraft: () => {},
      upsertSalesClaim: () => {},
      replaceVisibleSalesClaims: () => {},
      mergeActiveSalesClaims: () => {},
      getSalesYearMonthBucket: () => "2026-04",
      formatEstimatedAmountRangeFromKrw: () => "",
    },
    renderUserOwnedSalesClaimCard: () => "owned-card",
    renderCompanySalesClaimCard: () => "company-card",
    renderUserTrackerClaimSection: () => "tracker-section",
    claimSalesProject: async () => ({}),
    saveSalesClaimNote: async () => ({}),
    transferSalesClaim: async () => ({}),
    closeSalesClaim: async () => ({}),
    adminDeleteLatestSalesNote: async () => ({}),
    releaseSalesClaim: async () => ({}),
    formatContractAmountInput: (value) => String(value ?? ""),
    isAdminRole: () => false,
    normalizeSalesClaimCardViewModel: (payload) => payload,
    renderTrackerEntries: () => {},
    loadSalesOverview: async () => ({}),
    loadMySalesClaims: async () => ({}),
    loadVisibleSalesClaims: async () => ({}),
    refreshSalesAdminPanels: async () => ({}),
    salesViewRuntime: { runtime: true },
    flash: () => {},
  };

  const helpers = runtime.createSalesPanelDepsHelpers(deps);
  assert.equal(typeof helpers.buildSalesPanelControllerDeps, "function");

  const controllerDeps = helpers.buildSalesPanelControllerDeps();
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.window, deps.windowObject);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.getSalesClaimForProject, deps.salesStateHelpers.getSalesClaimForProject);
  assert.equal(controllerDeps.replaceVisibleSalesClaims, deps.salesStateHelpers.replaceVisibleSalesClaims);
  assert.equal(controllerDeps.renderUserOwnedSalesClaimCard, deps.renderUserOwnedSalesClaimCard);
  assert.equal(controllerDeps.renderCompanySalesClaimCard, deps.renderCompanySalesClaimCard);
  assert.equal(controllerDeps.renderUserTrackerClaimSection, deps.renderUserTrackerClaimSection);
  assert.equal(controllerDeps.claimSalesProject, deps.claimSalesProject);
  assert.equal(controllerDeps.releaseSalesClaim, deps.releaseSalesClaim);
  assert.equal(controllerDeps.buildSalesClaimEstimateLabelMarkup, deps.runtimeAdapters.buildSalesClaimEstimateLabel);
  assert.equal(controllerDeps.normalizeSalesClaimCardViewModel, deps.normalizeSalesClaimCardViewModel);
  assert.equal(controllerDeps.salesViewRuntime, deps.salesViewRuntime);
  assert.equal(controllerDeps.flash, deps.flash);
});

test("app-support runtime builds bootstrap runtime deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { uiMode: "user" },
    dom: { trackerContext: {} },
    api: async () => ({}),
    flash: () => "flash",
    salesStateHelpers: {
      getVisibleSalesProjectIds: () => ["project-1"],
      isActiveSalesClaim: () => true,
      isCurrentUserClaimOwner: () => false,
      mergeActiveSalesClaims: () => "merge-claims",
      replaceVisibleSalesClaims: () => "replace-claims",
    },
    bootstrapSupport: {
      normalizeSalesOverviewPayload: () => ({ myItems: [], companyItems: [], organizationUsers: [] }),
      buildSalesOverviewCachePayload: () => ({ my_items: [] }),
      mergeSalesOverviewIntoHomeBootstrapPayload: () => ({ merged: true }),
      buildHomeBootstrapCachePayload: () => ({ cached: true }),
      hasCachedSalesOverviewData: () => true,
      hasCachedHomeBootstrapData: () => false,
      isMissingSalesOverviewEndpointError: () => false,
      isMissingHomeBootstrapEndpointError: () => true,
    },
    canUseAdminMode: () => true,
    mergeOrganizationInvitations: () => "merge-invitations",
    loadTrackerEntries: async () => "load-tracker",
    renderMySalesClaimsPanel: () => "render-my-sales",
    renderTrackerEntries: () => "render-tracker",
    renderSalesSummaryPanel: () => "render-sales-summary",
    renderOrganizationAdminPanel: () => "render-org-admin",
    applyHomeBootstrapPayload: () => "apply-home",
    applySalesOverviewPayload: () => "apply-sales",
    persistHomeBootstrapCache: () => "persist-home-cache",
    persistSalesOverviewCache: () => "persist-sales-cache",
    resetTrackerBoardEdit: () => "reset-board-edit",
    renderEntriesPagination: () => "render-pagination",
    syncUrlState: () => "sync-url",
    useGlobalTrackerEntriesScope: () => true,
    salesOverviewStorageKey: "sales-overview-key",
    homeBootstrapStorageKey: "home-bootstrap-key",
    readConsoleCacheEnvelope: () => ({ ok: true }),
    writeConsoleCacheEnvelope: () => {},
  };

  const helpers = runtime.createBootstrapRuntimeDepsHelpers(deps);
  assert.equal(typeof helpers.buildConsoleDataRuntimeDeps, "function");
  assert.equal(typeof helpers.buildHomeBootstrapRuntimeDeps, "function");

  const consoleDeps = helpers.buildConsoleDataRuntimeDeps();
  assert.equal(consoleDeps.state, deps.state);
  assert.equal(consoleDeps.api, deps.api);
  assert.equal(consoleDeps.flash, deps.flash);
  assert.equal(consoleDeps.canUseAdminMode, deps.canUseAdminMode);
  assert.equal(consoleDeps.getVisibleSalesProjectIds, deps.salesStateHelpers.getVisibleSalesProjectIds);
  assert.equal(consoleDeps.isActiveSalesClaim, deps.salesStateHelpers.isActiveSalesClaim);
  assert.equal(consoleDeps.isCurrentUserClaimOwner, deps.salesStateHelpers.isCurrentUserClaimOwner);
  assert.equal(consoleDeps.mergeActiveSalesClaims, deps.salesStateHelpers.mergeActiveSalesClaims);
  assert.equal(consoleDeps.replaceVisibleSalesClaims, deps.salesStateHelpers.replaceVisibleSalesClaims);
  assert.equal(consoleDeps.mergeOrganizationInvitations, deps.mergeOrganizationInvitations);
  assert.equal(consoleDeps.loadTrackerEntries, deps.loadTrackerEntries);
  assert.equal(consoleDeps.renderMySalesClaimsPanel, deps.renderMySalesClaimsPanel);
  assert.equal(consoleDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(consoleDeps.renderSalesSummaryPanel, deps.renderSalesSummaryPanel);
  assert.equal(consoleDeps.renderOrganizationAdminPanel, deps.renderOrganizationAdminPanel);
  assert.equal(consoleDeps.applyHomeBootstrapPayload, deps.applyHomeBootstrapPayload);
  assert.equal(consoleDeps.applySalesOverviewPayload, deps.applySalesOverviewPayload);
  assert.equal(consoleDeps.persistHomeBootstrapCache, deps.persistHomeBootstrapCache);
  assert.equal(consoleDeps.persistSalesOverviewCache, deps.persistSalesOverviewCache);
  assert.equal(consoleDeps.hasCachedHomeBootstrapData, deps.bootstrapSupport.hasCachedHomeBootstrapData);
  assert.equal(consoleDeps.hasCachedSalesOverviewData, deps.bootstrapSupport.hasCachedSalesOverviewData);
  assert.equal(consoleDeps.isMissingHomeBootstrapEndpointError, deps.bootstrapSupport.isMissingHomeBootstrapEndpointError);
  assert.equal(consoleDeps.isMissingSalesOverviewEndpointError, deps.bootstrapSupport.isMissingSalesOverviewEndpointError);

  const homeDeps = helpers.buildHomeBootstrapRuntimeDeps();
  assert.equal(homeDeps.state, deps.state);
  assert.equal(homeDeps.dom, deps.dom);
  assert.equal(homeDeps.mergeActiveSalesClaims, deps.salesStateHelpers.mergeActiveSalesClaims);
  assert.equal(homeDeps.resetTrackerBoardEdit, deps.resetTrackerBoardEdit);
  assert.equal(homeDeps.renderEntriesPagination, deps.renderEntriesPagination);
  assert.equal(homeDeps.renderMySalesClaimsPanel, deps.renderMySalesClaimsPanel);
  assert.equal(homeDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(homeDeps.syncUrlState, deps.syncUrlState);
  assert.equal(homeDeps.useGlobalTrackerEntriesScope, deps.useGlobalTrackerEntriesScope);
  assert.equal(homeDeps.normalizeSalesOverviewPayload, deps.bootstrapSupport.normalizeSalesOverviewPayload);
  assert.equal(homeDeps.buildSalesOverviewCachePayload, deps.bootstrapSupport.buildSalesOverviewCachePayload);
  assert.equal(homeDeps.mergeSalesOverviewIntoHomeBootstrapPayload, deps.bootstrapSupport.mergeSalesOverviewIntoHomeBootstrapPayload);
  assert.equal(homeDeps.buildHomeBootstrapCachePayload, deps.bootstrapSupport.buildHomeBootstrapCachePayload);
  assert.equal(homeDeps.salesOverviewStorageKey, deps.salesOverviewStorageKey);
  assert.equal(homeDeps.homeBootstrapStorageKey, deps.homeBootstrapStorageKey);
  assert.equal(homeDeps.readConsoleCacheEnvelope, deps.readConsoleCacheEnvelope);
  assert.equal(homeDeps.writeConsoleCacheEnvelope, deps.writeConsoleCacheEnvelope);
});

test("app-support runtime builds auth controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { auth: true },
    dom: { auth: true },
    document: { title: "doc" },
    windowObject: { location: { pathname: "/app/" } },
    api: async () => ({}),
    flash: () => "flash",
    setBusy: () => "busy",
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: () => "org-role",
    formatInvitationStatusLabel: () => "invite-status",
    formatSalesDateLabel: () => "sales-date",
    formatMembershipStatusLabel: () => "membership-status",
    requireAuthSessionRuntime: () => ({ runtime: true }),
    loadOrganizationUsers: async () => "users",
    loadOrganizationMembers: async () => "members",
    loadSalesOverview: async () => "sales-overview",
    loadMySalesClaims: async () => "my-sales",
    refreshSalesAdminPanels: async () => "refresh-panels",
    ensureConsoleInitialized: async () => "console-init",
    shouldShowSignUpMode: () => true,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    syncUiModeChrome: () => "sync-ui",
    applyUiModeTransition: () => "apply-ui",
    renderAuthUi: () => "render-auth",
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => false,
    loadAdminConsoleData: async () => "load-admin",
    loadBackfillConflicts: async () => "load-backfill",
    renderBackfillConflictsPanel: () => "render-backfill",
    renderTrackerContactResolutionSummary: () => "render-contact-summary",
    renderTrackerCleanupPreview: () => "render-cleanup",
    closeDrawer: () => "close-drawer",
    hydrateHomeBootstrapCache: () => true,
    clearUserModeRunSelection: () => "clear-user-selection",
    loadHomeBootstrap: async () => "load-home",
    loadTrackerEntries: async () => "load-tracker",
    getTrackerController: () => ({ controller: true }),
    renderOrganizationAdminPanel: () => "render-org-admin",
    renderMySalesClaimsPanel: () => "render-my-sales",
    renderSalesSummaryPanel: () => "render-sales-summary",
    renderRunDetail: () => "render-run-detail",
    renderTrackerEntries: () => "render-tracker-entries",
  };

  const helpers = runtime.createAuthControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildAuthControllerBaseDeps, "function");
  assert.equal(typeof helpers.buildAuthControllerDeps, "function");
  assert.equal(typeof helpers.buildAuthUiControllerDeps, "function");

  const baseDeps = helpers.buildAuthControllerBaseDeps();
  assert.equal(baseDeps.state, deps.state);
  assert.equal(baseDeps.dom, deps.dom);
  assert.equal(baseDeps.document, deps.document);
  assert.equal(baseDeps.window, deps.windowObject);
  assert.equal(baseDeps.api, deps.api);
  assert.equal(baseDeps.flash, deps.flash);
  assert.equal(baseDeps.setBusy, deps.setBusy);
  assert.equal(baseDeps.escapeHtml, deps.escapeHtml);
  assert.equal(baseDeps.formatOrgRoleLabel, deps.formatOrgRoleLabel);
  assert.equal(baseDeps.formatInvitationStatusLabel, deps.formatInvitationStatusLabel);
  assert.equal(baseDeps.formatSalesDateLabel, deps.formatSalesDateLabel);
  assert.equal(baseDeps.formatMembershipStatusLabel, deps.formatMembershipStatusLabel);
  assert.equal(baseDeps.requireAuthSessionRuntime, deps.requireAuthSessionRuntime);
  assert.equal(baseDeps.loadOrganizationUsers, deps.loadOrganizationUsers);
  assert.equal(baseDeps.loadOrganizationMembers, deps.loadOrganizationMembers);
  assert.equal(baseDeps.loadSalesOverview, deps.loadSalesOverview);
  assert.equal(baseDeps.loadMySalesClaims, deps.loadMySalesClaims);
  assert.equal(baseDeps.refreshSalesAdminPanels, deps.refreshSalesAdminPanels);
  assert.equal(baseDeps.ensureConsoleInitialized, deps.ensureConsoleInitialized);
  assert.equal(baseDeps.shouldShowSignUpMode, deps.shouldShowSignUpMode);
  assert.equal(baseDeps.AUTH_MODE_SIGN_IN, deps.AUTH_MODE_SIGN_IN);
  assert.equal(baseDeps.AUTH_MODE_SIGN_UP, deps.AUTH_MODE_SIGN_UP);
  assert.equal(baseDeps.syncUiModeChrome, deps.syncUiModeChrome);
  assert.equal(baseDeps.applyUiModeTransition, deps.applyUiModeTransition);

  const controllerDeps = helpers.buildAuthControllerDeps();
  assert.equal(controllerDeps.renderAuthUi, deps.renderAuthUi);
  assert.equal(controllerDeps.canUseAdminMode, deps.canUseAdminMode);
  assert.equal(controllerDeps.canLoadProtectedConsoleData, deps.canLoadProtectedConsoleData);
  assert.equal(controllerDeps.loadAdminConsoleData, deps.loadAdminConsoleData);
  assert.equal(controllerDeps.loadBackfillConflicts, deps.loadBackfillConflicts);
  assert.equal(controllerDeps.renderBackfillConflictsPanel, deps.renderBackfillConflictsPanel);
  assert.equal(controllerDeps.renderTrackerContactResolutionSummary, deps.renderTrackerContactResolutionSummary);
  assert.equal(controllerDeps.renderTrackerCleanupPreview, deps.renderTrackerCleanupPreview);
  assert.equal(controllerDeps.closeDrawer, deps.closeDrawer);
  assert.equal(controllerDeps.hydrateHomeBootstrapCache, deps.hydrateHomeBootstrapCache);
  assert.equal(controllerDeps.clearUserModeRunSelection, deps.clearUserModeRunSelection);
  assert.equal(controllerDeps.loadHomeBootstrap, deps.loadHomeBootstrap);
  assert.equal(controllerDeps.loadTrackerEntries, deps.loadTrackerEntries);
  assert.deepEqual(controllerDeps.trackerController, { controller: true });
  assert.equal(controllerDeps.renderOrganizationAdminPanel, deps.renderOrganizationAdminPanel);
  assert.equal(controllerDeps.renderMySalesClaimsPanel, deps.renderMySalesClaimsPanel);
  assert.equal(controllerDeps.renderSalesSummaryPanel, deps.renderSalesSummaryPanel);
  assert.equal(controllerDeps.renderRunDetail, deps.renderRunDetail);
  assert.equal(controllerDeps.renderTrackerEntries, deps.renderTrackerEntries);

  const authUiDeps = helpers.buildAuthUiControllerDeps();
  assert.equal(authUiDeps.state, deps.state);
  assert.equal(authUiDeps.dom, deps.dom);
  assert.equal(authUiDeps.document, deps.document);
  assert.equal(authUiDeps.window, deps.windowObject);
  assert.equal(authUiDeps.api, deps.api);
  assert.equal(authUiDeps.syncUiModeChrome, deps.syncUiModeChrome);
  assert.equal(authUiDeps.applyUiModeTransition, deps.applyUiModeTransition);
});

test("app-support runtime builds tracker controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { tracker: true },
    dom: { tracker: true },
    window: { tracker: true },
    api: async () => ({}),
    flash: () => "flash",
    setBusy: () => "busy",
    FormData: function FakeFormData() {},
    escapeHtml: (value) => String(value ?? ""),
    formatDate: () => "date",
    syncUrlState: () => "sync-url",
    renderTrackerEntries: () => "render-tracker-entries",
    EDITABLE_FIELDS: ["project_name"],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact"]),
    renderTrackerBoard: () => "render-tracker-board",
    patchTrackerEntry: async () => "patch-tracker-entry",
    syncTrackerEntryAfterPatch: async () => "sync-tracker-entry-after-patch",
    readRunFiltersFromControls: () => "read-run-filters",
    renderRuns: () => "render-runs",
    renderRunsPagination: () => "render-runs-pagination",
    renderRunDetail: () => "render-run-detail",
    renderRunEventStatus: () => "render-run-event-status",
    renderLogsList: () => "render-logs-list",
    upsertRunListItem: () => "upsert-run",
    renderEntriesPagination: () => "render-entries-pagination",
    renderSalesSummaryPanel: () => "render-sales-summary",
    renderTrackerChangeEventsPanel: () => "render-change-events",
    renderTrackerContactResolutionSummary: () => "render-contact-summary",
    renderBackfillConflictsPanel: () => "render-backfill",
    renderTrackerCleanupPreview: () => "render-cleanup",
    renderProjectRelatedHosts: () => "render-project-hosts",
    touchSyncMeta: () => "touch-sync",
    persistTrackerChangeEventsCache: () => "persist-change-cache",
    clearTrackerChangeEventsCache: () => "clear-change-cache",
    handleOutOfRangePageError: () => false,
    canLoadProtectedConsoleData: () => true,
    TRACKER_REGION_OPTIONS: [{ value: "", label: "전체" }],
    useGlobalTrackerEntriesScope: () => true,
    shouldUseHomeBootstrapTrackerSnapshot: () => false,
    isProjectTrackerRun: () => true,
    loadTrackerEntries: async () => "load-tracker",
    schedulePolling: () => "schedule-polling",
    loadWinnerRunPanels: async () => "load-winner",
    loadTrackerExportPanels: async () => "load-export",
    loadSelectedRunLogs: async () => "load-logs",
    loadBackfillConflicts: async () => "load-backfill",
    loadVisibleSalesClaims: async () => "load-visible-sales",
    requireTrackerDiagnosticsRuntime: () => ({ runtime: true }),
    getTrackerController: () => ({ runtime: true }),
    formatContactResolutionStatusLabel: (value) => `contact-status:${value}`,
    formatContactResolutionReasonLabel: (value) => `contact-reason:${value}`,
    formatBackfillConflictResolutionLabel: (value) => `backfill:${value}`,
    getTrackerDiagnosticsScope: () => ({ trackerRunId: "tracker-run-1" }),
    buildTrackerChangeEventsMarkup: () => "change-events",
    buildTrackerChangeBellPopoverMarkup: () => "bell-popover",
    buildBackfillConflictsMarkup: () => "backfill-conflicts",
    buildBackfillConflictsView: () => "backfill-conflicts-view",
    focusTrackerChangeEntry: () => "focus-change-entry",
    closeTrackerChangeModal: () => "close-change-modal",
    clearProjectRelatedRefresh: () => "clear-project-related",
    maybeScheduleProjectRelatedRefresh: () => "schedule-project-related",
    canReuseProjectRelatedPayload: () => false,
    cacheProjectRelatedPayload: () => "cache-project-related",
    isProjectRelatedVisible: () => true,
    resolveTrackerEntryProjectId: () => "project-1",
    ensureTrackerEntryProjectId: async () => "project-1",
    TRACKER_ENTRY_RUNTIME: { runtime: true },
    TRACKER_DETAIL_PREFETCH_LIMIT: 3,
    warmTrackerEntriesDownload: () => "warm-download",
    closeDrawer: () => "close-drawer",
    renderTrackerBoard: () => "render-board",
    resetTrackerBoardEdit: () => "reset-board-edit",
    loadAdminConsoleData: async () => "load-admin",
    buildSelectedEntryAuditMarkup: () => "build-audit",
    loadSelectedEntryDetail: async () => "load-selected-entry",
    renderTrackerMissingReport: () => "render-missing-report",
    renderSelectedEntryChangeEvents: () => "render-selected-events",
    renderSelectedEntry: () => "render-selected-entry",
    renderSelectedEntryLoading: () => "render-selected-loading",
    resolveTrackerPatchActorLabel: () => "actor-label",
    runTypeLabel: () => "run-type",
  };

  const helpers = runtime.createTrackerControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildTrackerControllerBaseDeps, "function");
  assert.equal(typeof helpers.buildTrackerControllerDeps, "function");
  assert.equal(typeof helpers.buildTrackerEntryActionsControllerDeps, "function");
  assert.equal(typeof helpers.buildTrackerDiagnosticsPanelControllerDeps, "function");

  const baseDeps = helpers.buildTrackerControllerBaseDeps();
  assert.equal(baseDeps.state, deps.state);
  assert.equal(baseDeps.dom, deps.dom);
  assert.equal(baseDeps.flash, deps.flash);
  assert.equal(baseDeps.escapeHtml, deps.escapeHtml);
  assert.equal(baseDeps.syncUrlState, deps.syncUrlState);
  assert.equal(baseDeps.renderTrackerEntries, deps.renderTrackerEntries);

  const controllerDeps = helpers.buildTrackerControllerDeps();
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.flash, deps.flash);
  assert.equal(controllerDeps.setBusy, deps.setBusy);
  assert.equal(controllerDeps.FormData, deps.FormData);
  assert.equal(controllerDeps.escapeHtml, deps.escapeHtml);
  assert.equal(controllerDeps.formatDate, deps.formatDate);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
  assert.equal(controllerDeps.readRunFiltersFromControls, deps.readRunFiltersFromControls);
  assert.equal(controllerDeps.renderRuns, deps.renderRuns);
  assert.equal(controllerDeps.renderRunsPagination, deps.renderRunsPagination);
  assert.equal(controllerDeps.renderRunDetail, deps.renderRunDetail);
  assert.equal(controllerDeps.renderRunEventStatus, deps.renderRunEventStatus);
  assert.equal(controllerDeps.renderLogsList, deps.renderLogsList);
  assert.equal(controllerDeps.upsertRunListItem, deps.upsertRunListItem);
  assert.equal(controllerDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(controllerDeps.renderEntriesPagination, deps.renderEntriesPagination);
  assert.equal(controllerDeps.renderSalesSummaryPanel, deps.renderSalesSummaryPanel);
  assert.equal(controllerDeps.renderTrackerChangeEventsPanel, deps.renderTrackerChangeEventsPanel);
  assert.equal(controllerDeps.renderTrackerContactResolutionSummary, deps.renderTrackerContactResolutionSummary);
  assert.equal(controllerDeps.renderBackfillConflictsPanel, deps.renderBackfillConflictsPanel);
  assert.equal(controllerDeps.renderTrackerCleanupPreview, deps.renderTrackerCleanupPreview);
  assert.equal(controllerDeps.renderProjectRelatedHosts, deps.renderProjectRelatedHosts);
  assert.equal(controllerDeps.touchSyncMeta, deps.touchSyncMeta);
  assert.equal(controllerDeps.persistTrackerChangeEventsCache, deps.persistTrackerChangeEventsCache);
  assert.equal(controllerDeps.clearTrackerChangeEventsCache, deps.clearTrackerChangeEventsCache);
  assert.equal(controllerDeps.handleOutOfRangePageError, deps.handleOutOfRangePageError);
  assert.equal(controllerDeps.canLoadProtectedConsoleData, deps.canLoadProtectedConsoleData);
  assert.equal(controllerDeps.TRACKER_REGION_OPTIONS, deps.TRACKER_REGION_OPTIONS);
  assert.equal(controllerDeps.useGlobalTrackerEntriesScope, deps.useGlobalTrackerEntriesScope);
  assert.equal(controllerDeps.shouldUseHomeBootstrapTrackerSnapshot, deps.shouldUseHomeBootstrapTrackerSnapshot);
  assert.equal(controllerDeps.isProjectTrackerRun, deps.isProjectTrackerRun);
  assert.equal(controllerDeps.loadTrackerEntries, deps.loadTrackerEntries);
  assert.equal(controllerDeps.schedulePolling, deps.schedulePolling);
  assert.equal(controllerDeps.loadWinnerRunPanels, deps.loadWinnerRunPanels);
  assert.equal(controllerDeps.loadTrackerExportPanels, deps.loadTrackerExportPanels);
  assert.equal(controllerDeps.loadSelectedRunLogs, deps.loadSelectedRunLogs);
  assert.equal(controllerDeps.loadBackfillConflicts, deps.loadBackfillConflicts);
  assert.equal(controllerDeps.loadVisibleSalesClaims, deps.loadVisibleSalesClaims);
  assert.equal(controllerDeps.requireTrackerDiagnosticsRuntime, deps.requireTrackerDiagnosticsRuntime);
  assert.equal(controllerDeps.clearProjectRelatedRefresh, deps.clearProjectRelatedRefresh);
  assert.equal(controllerDeps.maybeScheduleProjectRelatedRefresh, deps.maybeScheduleProjectRelatedRefresh);
  assert.equal(controllerDeps.canReuseProjectRelatedPayload, deps.canReuseProjectRelatedPayload);
  assert.equal(controllerDeps.cacheProjectRelatedPayload, deps.cacheProjectRelatedPayload);
  assert.equal(controllerDeps.isProjectRelatedVisible, deps.isProjectRelatedVisible);
  assert.equal(controllerDeps.resolveTrackerEntryProjectId, deps.resolveTrackerEntryProjectId);
  assert.equal(controllerDeps.ensureTrackerEntryProjectId, deps.ensureTrackerEntryProjectId);
  assert.equal(controllerDeps.TRACKER_ENTRY_RUNTIME, deps.TRACKER_ENTRY_RUNTIME);
  assert.equal(controllerDeps.TRACKER_DETAIL_PREFETCH_LIMIT, deps.TRACKER_DETAIL_PREFETCH_LIMIT);
  assert.equal(controllerDeps.warmTrackerEntriesDownload, deps.warmTrackerEntriesDownload);
  assert.equal(controllerDeps.closeDrawer, deps.closeDrawer);
  assert.equal(controllerDeps.renderTrackerBoard, deps.renderTrackerBoard);
  assert.equal(controllerDeps.resetTrackerBoardEdit, deps.resetTrackerBoardEdit);
  assert.equal(controllerDeps.loadAdminConsoleData, deps.loadAdminConsoleData);
  assert.equal(controllerDeps.buildSelectedEntryAuditMarkup, deps.buildSelectedEntryAuditMarkup);
  assert.equal(controllerDeps.loadSelectedEntryDetail, deps.loadSelectedEntryDetail);
  assert.equal(controllerDeps.renderTrackerMissingReport, deps.renderTrackerMissingReport);
  assert.equal(controllerDeps.renderSelectedEntryChangeEvents, deps.renderSelectedEntryChangeEvents);
  assert.equal(controllerDeps.renderSelectedEntry, deps.renderSelectedEntry);
  assert.equal(controllerDeps.renderSelectedEntryLoading, deps.renderSelectedEntryLoading);
  assert.equal(controllerDeps.resolveTrackerPatchActorLabel, deps.resolveTrackerPatchActorLabel);
  assert.equal(controllerDeps.runTypeLabel, deps.runTypeLabel);

  const entryActionsDeps = helpers.buildTrackerEntryActionsControllerDeps();
  assert.equal(entryActionsDeps.state, deps.state);
  assert.equal(entryActionsDeps.dom, deps.dom);
  assert.equal(entryActionsDeps.EDITABLE_FIELDS, deps.EDITABLE_FIELDS);
  assert.equal(entryActionsDeps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS, deps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS);
  assert.equal(entryActionsDeps.escapeHtml, deps.escapeHtml);
  assert.equal(entryActionsDeps.syncUrlState, deps.syncUrlState);
  assert.equal(entryActionsDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(entryActionsDeps.renderTrackerBoard, deps.renderTrackerBoard);
  assert.equal(entryActionsDeps.loadTrackerEntries, deps.loadTrackerEntries);
  assert.equal(entryActionsDeps.setBusy, deps.setBusy);
  assert.equal(entryActionsDeps.patchTrackerEntry, deps.patchTrackerEntry);
  assert.equal(entryActionsDeps.flash, deps.flash);
  assert.equal(entryActionsDeps.syncTrackerEntryAfterPatch, deps.syncTrackerEntryAfterPatch);

  const diagnosticsDeps = helpers.buildTrackerDiagnosticsPanelControllerDeps();
  assert.equal(diagnosticsDeps.window, deps.window);
  assert.equal(diagnosticsDeps.dom, deps.dom);
  assert.equal(diagnosticsDeps.state, deps.state);
  assert.equal(diagnosticsDeps.api, deps.api);
  assert.equal(diagnosticsDeps.flash, deps.flash);
  assert.deepEqual(diagnosticsDeps.trackerController, deps.getTrackerController());
  assert.equal(diagnosticsDeps.escapeHtml, deps.escapeHtml);
  assert.equal(diagnosticsDeps.formatDate, deps.formatDate);
  assert.equal(diagnosticsDeps.formatContactResolutionStatusLabel, deps.formatContactResolutionStatusLabel);
  assert.equal(diagnosticsDeps.formatContactResolutionReasonLabel, deps.formatContactResolutionReasonLabel);
  assert.equal(diagnosticsDeps.formatBackfillConflictResolutionLabel, deps.formatBackfillConflictResolutionLabel);
  assert.equal(diagnosticsDeps.getTrackerDiagnosticsScope, deps.getTrackerDiagnosticsScope);
  assert.equal(diagnosticsDeps.requireTrackerDiagnosticsRuntime, deps.requireTrackerDiagnosticsRuntime);
  assert.equal(diagnosticsDeps.buildTrackerChangeEventsMarkup, deps.buildTrackerChangeEventsMarkup);
  assert.equal(diagnosticsDeps.buildTrackerChangeBellPopoverMarkup, deps.buildTrackerChangeBellPopoverMarkup);
  assert.equal(diagnosticsDeps.buildBackfillConflictsMarkup, deps.buildBackfillConflictsMarkup);
  assert.equal(diagnosticsDeps.buildBackfillConflictsView, deps.buildBackfillConflictsView);
  assert.equal(diagnosticsDeps.syncUrlState, deps.syncUrlState);
  assert.equal(diagnosticsDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(diagnosticsDeps.loadSelectedEntryDetail, deps.loadSelectedEntryDetail);
  assert.equal(diagnosticsDeps.focusTrackerChangeEntry, deps.focusTrackerChangeEntry);
  assert.equal(diagnosticsDeps.closeTrackerChangeModal, deps.closeTrackerChangeModal);

  const sortTrackerBoardEntries = (entries) => entries;
  const trackerRenderInput = {
    sharedDeps: {
      dom: deps.dom,
      state: deps.state,
      escapeHtml: deps.escapeHtml,
      formatKoreanDate: deps.formatKoreanDate,
      formatBuildingAutomationEstimateValue: deps.formatBuildingAutomationEstimateValue,
      TRACKER_ENTRY_RUNTIME: deps.TRACKER_ENTRY_RUNTIME,
      flash: deps.flash,
    },
    selectedEntryActions: {
      renderSalesClaimSection: deps.renderSalesClaimSection,
      renderTrackerEntryRelatedNotices: deps.renderTrackerEntryRelatedNotices,
      resetTrackerBoardEdit: deps.resetTrackerBoardEdit,
      renderSelectedEntry: deps.renderSelectedEntry,
      buildTrackerEntrySummaryDetail: deps.buildTrackerEntrySummaryDetail,
      loadSelectedEntryDetail: deps.loadSelectedEntryDetail,
      toggleTrackerEntryRelated: deps.toggleTrackerEntryRelated,
      openTrackerEntryNoticeViewer: deps.openTrackerEntryNoticeViewer,
      bindRelatedNoticeViewerButtons: deps.bindRelatedNoticeViewerButtons,
      prefetchTrackerEntryDetails: deps.prefetchTrackerEntryDetails,
    },
    trackerSalesActions: {
      claimSalesProject: deps.claimSalesProject,
      setSalesNoteDraft: deps.setSalesNoteDraft,
      saveSalesClaimNote: deps.saveSalesClaimNote,
      transferSalesClaim: deps.transferSalesClaim,
      openSalesCloseDialog: deps.openSalesCloseDialog,
      closeSalesClaim: deps.closeSalesClaim,
      releaseSalesClaim: deps.releaseSalesClaim,
      syncUrlState: deps.syncUrlState,
      getSalesClaimForProject: deps.getSalesClaimForProject,
    },
    trackerBoardActions: {
      buildTrackerBoardEmptyStateView: deps.buildTrackerBoardEmptyStateView,
      buildTrackerBoardMarkup: deps.buildTrackerBoardMarkup,
      buildTrackerEntryCardMarkupFallback: deps.buildTrackerEntryCardMarkupFallback,
      getSortedTrackerBoardEntries: sortTrackerBoardEntries,
      TRACKER_BOARD_COLUMNS: deps.TRACKER_BOARD_COLUMNS,
      renderTrackerBoardHeaderCell: deps.renderTrackerBoardHeaderCell,
      renderTrackerBoardCell: deps.renderTrackerBoardCell,
      toggleTrackerBoardBlankPriority: deps.toggleTrackerBoardBlankPriority,
      beginTrackerBoardEdit: deps.beginTrackerBoardEdit,
      saveTrackerBoardEdit: deps.saveTrackerBoardEdit,
    },
  };
  const trackerRenderHelpers = runtime.createTrackerRenderControllerDepsHelpers(trackerRenderInput);
  assert.equal(typeof trackerRenderHelpers.buildTrackerRenderControllerDeps, "function");
  const trackerRenderDepsA = trackerRenderHelpers.buildTrackerRenderControllerDeps();
  const trackerRenderDepsB = trackerRenderHelpers.buildTrackerRenderControllerDeps();
  assert.strictEqual(trackerRenderDepsA, trackerRenderDepsB);
  assert.notStrictEqual(trackerRenderDepsA, trackerRenderInput);
  assert.strictEqual(trackerRenderDepsA.state, trackerRenderInput.sharedDeps.state);
  assert.strictEqual(trackerRenderDepsA.dom, trackerRenderInput.sharedDeps.dom);
  assert.strictEqual(trackerRenderDepsA.escapeHtml, trackerRenderInput.sharedDeps.escapeHtml);
  assert.strictEqual(trackerRenderDepsA.formatKoreanDate, trackerRenderInput.sharedDeps.formatKoreanDate);
  assert.strictEqual(trackerRenderDepsA.formatBuildingAutomationEstimateValue, trackerRenderInput.sharedDeps.formatBuildingAutomationEstimateValue);
  assert.strictEqual(trackerRenderDepsA.getSortedTrackerBoardEntries, trackerRenderInput.trackerBoardActions.getSortedTrackerBoardEntries);
  assert.strictEqual(trackerRenderDepsA.renderSalesClaimSection, trackerRenderInput.selectedEntryActions.renderSalesClaimSection);
  assert.strictEqual(trackerRenderDepsA.claimSalesProject, trackerRenderInput.trackerSalesActions.claimSalesProject);

  const projectRelatedInput = {
    sharedDeps: {
      state: deps.state,
      window: deps.window,
      api: deps.api,
      flash: deps.flash,
      escapeHtml: deps.escapeHtml,
    },
    projectRelatedConfig: {
      RELATED_NOTICE_RUNTIME: deps.RELATED_NOTICE_RUNTIME,
      PROJECT_RELATED_READY_CACHE_TTL_MS: deps.PROJECT_RELATED_READY_CACHE_TTL_MS,
      PROJECT_RELATED_SEED_CACHE_TTL_MS: deps.PROJECT_RELATED_SEED_CACHE_TTL_MS,
      PROJECT_RELATED_STORAGE_KEY: deps.PROJECT_RELATED_STORAGE_KEY,
      PROJECT_RELATED_STORAGE_MAX_ITEMS: deps.PROJECT_RELATED_STORAGE_MAX_ITEMS,
    },
    noticeViewerRenderers: {
      renderNoticeViewerWindow: deps.renderNoticeViewerWindow,
      renderNoticeViewerPayload: deps.renderNoticeViewerPayload,
      renderNoticeViewerError: deps.renderNoticeViewerError,
      renderProjects: deps.renderProjects,
      renderTrackerEntries: deps.renderTrackerEntries,
    },
    projectRelatedActions: {
      loadProjectRelatedNotices: deps.loadProjectRelatedNotices,
      loadSelectedEntryDetail: deps.loadSelectedEntryDetail,
    },
  };
  const projectRelatedHelpers = runtime.createProjectRelatedControllerDepsHelpers(projectRelatedInput);
  assert.equal(typeof projectRelatedHelpers.buildProjectRelatedControllerDeps, "function");
  const projectRelatedDepsA = projectRelatedHelpers.buildProjectRelatedControllerDeps();
  const projectRelatedDepsB = projectRelatedHelpers.buildProjectRelatedControllerDeps();
  assert.strictEqual(projectRelatedDepsA, projectRelatedDepsB);
  assert.notStrictEqual(projectRelatedDepsA, projectRelatedInput);
  assert.strictEqual(projectRelatedDepsA.state, projectRelatedInput.sharedDeps.state);
  assert.strictEqual(projectRelatedDepsA.window, projectRelatedInput.sharedDeps.window);
  assert.strictEqual(projectRelatedDepsA.api, projectRelatedInput.sharedDeps.api);
  assert.strictEqual(projectRelatedDepsA.flash, projectRelatedInput.sharedDeps.flash);
  assert.strictEqual(projectRelatedDepsA.RELATED_NOTICE_RUNTIME, projectRelatedInput.projectRelatedConfig.RELATED_NOTICE_RUNTIME);
  assert.strictEqual(projectRelatedDepsA.renderNoticeViewerWindow, projectRelatedInput.noticeViewerRenderers.renderNoticeViewerWindow);
  assert.strictEqual(projectRelatedDepsA.loadProjectRelatedNotices, projectRelatedInput.projectRelatedActions.loadProjectRelatedNotices);
});

test("app-support runtime builds download controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { download: true },
    dom: { download: true },
    window: { download: true },
    document: { document: true },
    setBusy: () => "busy",
    flash: () => "flash",
    api: async () => ({}),
    readTrackerFiltersFromControls: () => "read-filters",
    useGlobalTrackerEntriesScope: () => true,
    resolveActiveTrackerRunId: () => "run-1",
  };

  const helpers = runtime.createDownloadControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildDownloadControllerDeps, "function");

  const controllerDeps = helpers.buildDownloadControllerDeps();
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.window, deps.window);
  assert.equal(controllerDeps.document, deps.document);
  assert.equal(controllerDeps.setBusy, deps.setBusy);
  assert.equal(controllerDeps.flash, deps.flash);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.readTrackerFiltersFromControls, deps.readTrackerFiltersFromControls);
  assert.equal(controllerDeps.useGlobalTrackerEntriesScope, deps.useGlobalTrackerEntriesScope);
  assert.equal(controllerDeps.resolveActiveTrackerRunId, deps.resolveActiveTrackerRunId);
});

test("app-support runtime builds selected entry controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    dom: { selectedEntry: true },
    state: { selectedEntry: true },
    buildSelectedEntryLoadingView: () => "loading",
    buildSelectedEntryEmptyView: () => "empty",
    buildSelectedEntryDisplayView: () => "display",
    buildPatchPanelView: () => "patch",
    buildSelectedEntryChangeEventsMarkup: () => "events",
    buildSelectedEntryMeta: () => "meta",
    buildEntryDiagnosticsMarkup: () => "diagnostics",
    buildEntryFieldGridMarkup: () => "field-grid",
    buildDrawerFieldListMarkup: () => "drawer-fields",
    truncate: () => "truncate",
    escapeHtml: () => "escape",
    SELECTED_ENTRY_RUNTIME: { runtime: true },
    formatJson: () => "json",
    EDITABLE_FIELDS: ["project_name"],
    loadSelectedEntryAudit: async () => "audit",
    loadSelectedEntryChangeEvents: async () => "change-events",
    openDrawer: () => "open-drawer",
    closeDrawer: () => "close-drawer",
    syncUrlState: () => "sync-url",
  };

  const helpers = runtime.createSelectedEntryControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildSelectedEntryControllerDeps, "function");

  const controllerDeps = helpers.buildSelectedEntryControllerDeps();
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.buildSelectedEntryLoadingView, deps.buildSelectedEntryLoadingView);
  assert.equal(controllerDeps.buildSelectedEntryEmptyView, deps.buildSelectedEntryEmptyView);
  assert.equal(controllerDeps.buildSelectedEntryDisplayView, deps.buildSelectedEntryDisplayView);
  assert.equal(controllerDeps.buildPatchPanelView, deps.buildPatchPanelView);
  assert.equal(controllerDeps.buildSelectedEntryChangeEventsMarkup, deps.buildSelectedEntryChangeEventsMarkup);
  assert.equal(controllerDeps.buildSelectedEntryMeta, deps.buildSelectedEntryMeta);
  assert.equal(controllerDeps.buildEntryDiagnosticsMarkup, deps.buildEntryDiagnosticsMarkup);
  assert.equal(controllerDeps.buildEntryFieldGridMarkup, deps.buildEntryFieldGridMarkup);
  assert.equal(controllerDeps.buildDrawerFieldListMarkup, deps.buildDrawerFieldListMarkup);
  assert.equal(controllerDeps.truncate, deps.truncate);
  assert.equal(controllerDeps.escapeHtml, deps.escapeHtml);
  assert.equal(controllerDeps.requireSelectedEntryRuntime(), deps.SELECTED_ENTRY_RUNTIME);
  assert.equal(controllerDeps.formatJson, deps.formatJson);
  assert.equal(controllerDeps.EDITABLE_FIELDS, deps.EDITABLE_FIELDS);
  assert.equal(controllerDeps.loadSelectedEntryAudit, deps.loadSelectedEntryAudit);
  assert.equal(controllerDeps.loadSelectedEntryChangeEvents, deps.loadSelectedEntryChangeEvents);
  assert.equal(controllerDeps.openDrawer, deps.openDrawer);
  assert.equal(controllerDeps.closeDrawer, deps.closeDrawer);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
});

test("app-support runtime builds run panels controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { runs: true },
    dom: { runs: true },
    window: { runs: true },
    document: { document: true },
    RUN_VIEW_RUNTIME: { runtime: true },
    api: async () => ({}),
    flash: () => "flash",
    touchSyncMeta: () => "touch-sync",
    setBusy: () => "busy",
    loadRuns: async () => "load-runs",
    trackerController: { disconnectRunEventStream: () => "disconnect" },
    resetTrackerBoardEdit: () => "reset-board-edit",
    syncUrlState: () => "sync-url",
    refreshSelectedRun: async () => "refresh-selected-run",
    escapeHtml: (value) => String(value ?? ""),
    runTypeLabel: (value) => `run:${value}`,
    statusBadge: (value) => `status:${value}`,
    formatDate: (value) => `date:${value}`,
    formatJson: (value) => JSON.stringify(value),
    progressPercent: (value) => Number(value || 0),
    renderRunExecutionContext: () => "render-run-execution-context",
    isProjectTrackerRun: () => true,
    useGlobalTrackerEntriesScope: () => false,
    renderArtifactsList: () => "render-artifacts-list",
    buildArtifactEmptyMessage: () => "build-artifact-empty-message",
    loadTrackerEntries: async () => "load-tracker-entries",
  };

  const helpers = runtime.createRunPanelsControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildRunPanelsControllerDeps, "function");

  const controllerDeps = helpers.buildRunPanelsControllerDeps();
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.window, deps.window);
  assert.equal(controllerDeps.document, deps.document);
  assert.equal(controllerDeps.RUN_VIEW_RUNTIME, deps.RUN_VIEW_RUNTIME);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.flash, deps.flash);
  assert.equal(controllerDeps.touchSyncMeta, deps.touchSyncMeta);
  assert.equal(controllerDeps.setBusy, deps.setBusy);
  assert.equal(controllerDeps.loadRuns, deps.loadRuns);
  assert.deepEqual(controllerDeps.trackerController, deps.trackerController);
  assert.equal(controllerDeps.resetTrackerBoardEdit, deps.resetTrackerBoardEdit);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
  assert.equal(controllerDeps.refreshSelectedRun, deps.refreshSelectedRun);
  assert.equal(controllerDeps.escapeHtml, deps.escapeHtml);
  assert.equal(controllerDeps.runTypeLabel, deps.runTypeLabel);
  assert.equal(controllerDeps.statusBadge, deps.statusBadge);
  assert.equal(controllerDeps.formatDate, deps.formatDate);
  assert.equal(controllerDeps.formatJson, deps.formatJson);
  assert.equal(controllerDeps.progressPercent, deps.progressPercent);
  assert.equal(controllerDeps.renderRunExecutionContext, deps.renderRunExecutionContext);
  assert.equal(controllerDeps.isProjectTrackerRun, deps.isProjectTrackerRun);
  assert.equal(controllerDeps.useGlobalTrackerEntriesScope, deps.useGlobalTrackerEntriesScope);
  assert.equal(controllerDeps.renderArtifactsList, deps.renderArtifactsList);
  assert.equal(controllerDeps.buildArtifactEmptyMessage, deps.buildArtifactEmptyMessage);
  assert.equal(controllerDeps.loadTrackerEntries, deps.loadTrackerEntries);
});

test("app-support runtime builds report panels controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { report: true },
    dom: { report: true },
    api: async () => ({}),
    flash: () => "flash",
    setBusy: () => "busy",
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => `date:${value}`,
    formatJson: (value) => JSON.stringify(value),
    formatBytes: (value) => `bytes:${value}`,
    statusBadge: (value) => `status:${value}`,
    ARTIFACT_RUNTIME: { runtime: true },
    RELATED_NOTICE_RUNTIME: { runtime: true },
    loadDashboardSummary: async () => "load-dashboard-summary",
    touchSyncMeta: () => "touch-sync",
    syncUrlState: () => "sync-url",
    callRunPanelsController: () => "call-run-panels-controller",
  };

  const helpers = runtime.createReportPanelsControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildReportPanelsControllerDeps, "function");

  const controllerDeps = helpers.buildReportPanelsControllerDeps();
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.flash, deps.flash);
  assert.equal(controllerDeps.setBusy, deps.setBusy);
  assert.equal(controllerDeps.escapeHtml, deps.escapeHtml);
  assert.equal(controllerDeps.formatDate, deps.formatDate);
  assert.equal(controllerDeps.formatJson, deps.formatJson);
  assert.equal(controllerDeps.formatBytes, deps.formatBytes);
  assert.equal(controllerDeps.statusBadge, deps.statusBadge);
  assert.deepEqual(controllerDeps.ARTIFACT_RUNTIME, deps.ARTIFACT_RUNTIME);
  assert.deepEqual(controllerDeps.RELATED_NOTICE_RUNTIME, deps.RELATED_NOTICE_RUNTIME);
  assert.equal(controllerDeps.loadDashboardSummary, deps.loadDashboardSummary);
  assert.equal(controllerDeps.touchSyncMeta, deps.touchSyncMeta);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
  assert.equal(controllerDeps.callRunPanelsController, deps.callRunPanelsController);
});

test("app-support runtime builds console panels controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    dom: { console: true },
    state: { console: true },
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => `date:${value}`,
    runTypeLabel: (value) => `run:${value}`,
    statusBadge: (value) => `status:${value}`,
    metricCard: (label, value) => `${label}:${value}`,
    PROJECT_RUNTIME: { runtime: true },
    RUN_VIEW_RUNTIME: { runtime: true },
    renderArtifactPreviewMarkup: () => "artifact-preview",
    resolveTrackerExecutionContext: () => ({ execution: true }),
    trackerExecutionTone: (value) => `tone:${value}`,
    trackerExecutionMessage: (value) => `message:${value}`,
    progressPercent: (value) => Number(value || 0),
    trackerExportStageLabel: (value) => `stage:${value}`,
    renderRelatedProjectNotices: () => "related-notices",
    bindRelatedNoticeViewerButtons: () => "bind-buttons",
    toggleProjectRelated: () => "toggle-related",
    openProjectNoticeViewer: () => "open-notice",
    applyPresetParams: () => "apply-preset",
    api: async () => ({}),
    syncUrlState: () => "sync-url",
    syncCollectModeOptions: () => "sync-collect",
    touchSyncMeta: () => "touch-sync",
    flash: () => "flash",
  };

  const helpers = runtime.createConsolePanelsControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildConsolePanelsControllerDeps, "function");

  const controllerDeps = helpers.buildConsolePanelsControllerDeps();
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.escapeHtml, deps.escapeHtml);
  assert.equal(controllerDeps.formatDate, deps.formatDate);
  assert.equal(controllerDeps.runTypeLabel, deps.runTypeLabel);
  assert.equal(controllerDeps.statusBadge, deps.statusBadge);
  assert.equal(controllerDeps.metricCard, deps.metricCard);
  assert.deepEqual(controllerDeps.PROJECT_RUNTIME, deps.PROJECT_RUNTIME);
  assert.deepEqual(controllerDeps.RUN_VIEW_RUNTIME, deps.RUN_VIEW_RUNTIME);
  assert.equal(controllerDeps.renderArtifactPreviewMarkup, deps.renderArtifactPreviewMarkup);
  assert.equal(controllerDeps.resolveTrackerExecutionContext, deps.resolveTrackerExecutionContext);
  assert.equal(controllerDeps.trackerExecutionTone, deps.trackerExecutionTone);
  assert.equal(controllerDeps.trackerExecutionMessage, deps.trackerExecutionMessage);
  assert.equal(controllerDeps.progressPercent, deps.progressPercent);
  assert.equal(controllerDeps.trackerExportStageLabel, deps.trackerExportStageLabel);
  assert.equal(controllerDeps.renderRelatedProjectNotices, deps.renderRelatedProjectNotices);
  assert.equal(controllerDeps.bindRelatedNoticeViewerButtons, deps.bindRelatedNoticeViewerButtons);
  assert.equal(controllerDeps.toggleProjectRelated, deps.toggleProjectRelated);
  assert.equal(controllerDeps.openProjectNoticeViewer, deps.openProjectNoticeViewer);
  assert.equal(controllerDeps.applyPresetParams, deps.applyPresetParams);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
  assert.equal(controllerDeps.syncCollectModeOptions, deps.syncCollectModeOptions);
  assert.equal(controllerDeps.touchSyncMeta, deps.touchSyncMeta);
  assert.equal(controllerDeps.flash, deps.flash);
});

test("app-support runtime builds ui mode controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { uiMode: "admin" },
    dom: { uiMode: true },
    window: { name: "window" },
    DEFAULT_ADMIN_TAB: "project-status",
    APP_ROOT_PATH: "/app/",
    normalizeLocationPath: (value) => String(value ?? ""),
    getAdminRoutePath: (value) => `/app/${value}`,
    canUseAdminMode: () => true,
    canLoadProtectedConsoleData: () => false,
    shouldShowAdminModeToggle: () => true,
    shouldShowSharedGoogleSheetsShell: () => false,
    isPendingLegacyAdminAlias: () => false,
    clearAdminLegacyRouteIntent: () => "clear-legacy-intent",
    getAdminTabByPathname: () => ({ key: "project-status" }),
    resolveUiModeFromLocation: () => "admin",
    resolveLegacyAdminRoutePath: () => "/app/project-status",
    normalizeAdminTab: (value) => `normalized:${value}`,
    clearAdminGoogleSheetPopupStateForTab: () => "clear-popup-for-tab",
    maybePreloadAdminGoogleSheetsBootstrap: () => "preload",
    syncUrlState: () => "sync-url",
    syncTrackerChangeBellVisibility: () => "sync-bell",
    hydrateTrackerChangeEventsCache: () => "hydrate-cache",
    renderTrackerChangeEventUnreadCount: () => "render-unread",
    renderTrackerChangeBellPopover: () => "render-bell",
    renderAdminTopNavigation: () => "render-nav",
    renderAdminEmbedPanel: () => "render-embed",
    renderTrackerTemplateStatus: () => "render-template",
    loadAdminConsoleData: async () => "load-admin",
    loadBackfillConflicts: async () => "load-backfill",
    renderBackfillConflictsPanel: () => "render-backfill",
    closeDrawer: () => "close-drawer",
    renderAuthUi: () => "render-auth-ui",
    renderOrganizationAdminPanel: () => "render-org-admin",
    renderMySalesClaimsPanel: () => "render-my-sales",
    renderSalesSummaryPanel: () => "render-sales-summary",
    renderRunDetail: () => "render-run-detail",
    renderTrackerEntries: () => "render-tracker-entries",
    loadOrganizationUsers: async () => "load-users",
    loadTrackerEntries: async () => "load-tracker-entries",
    loadTrackerChangeEventUnreadCount: async () => "load-unread",
    loadTrackerChangeEvents: async () => "load-change-events",
    clearUserModeRunSelection: () => "clear-selection",
    hydrateHomeBootstrapCache: () => "hydrate-home",
    loadHomeBootstrap: async () => "load-home",
    scheduleTrackerChangeEventsWarmup: () => "warmup",
  };

  const helpers = runtime.createUiModeControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildUiModeControllerDeps, "function");

  const controllerDeps = helpers.buildUiModeControllerDeps();
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.window, deps.window);
  assert.equal(controllerDeps.DEFAULT_ADMIN_TAB, deps.DEFAULT_ADMIN_TAB);
  assert.equal(controllerDeps.APP_ROOT_PATH, deps.APP_ROOT_PATH);
  assert.equal(controllerDeps.normalizeLocationPath, deps.normalizeLocationPath);
  assert.equal(controllerDeps.getAdminRoutePath, deps.getAdminRoutePath);
  assert.equal(controllerDeps.canUseAdminMode, deps.canUseAdminMode);
  assert.equal(controllerDeps.canLoadProtectedConsoleData, deps.canLoadProtectedConsoleData);
  assert.equal(controllerDeps.shouldShowAdminModeToggle, deps.shouldShowAdminModeToggle);
  assert.equal(controllerDeps.shouldShowSharedGoogleSheetsShell, deps.shouldShowSharedGoogleSheetsShell);
  assert.equal(controllerDeps.isPendingLegacyAdminAlias, deps.isPendingLegacyAdminAlias);
  assert.equal(controllerDeps.clearAdminLegacyRouteIntent, deps.clearAdminLegacyRouteIntent);
  assert.equal(controllerDeps.getAdminTabByPathname, deps.getAdminTabByPathname);
  assert.equal(controllerDeps.resolveUiModeFromLocation, deps.resolveUiModeFromLocation);
  assert.equal(controllerDeps.resolveLegacyAdminRoutePath, deps.resolveLegacyAdminRoutePath);
  assert.equal(controllerDeps.normalizeAdminTab, deps.normalizeAdminTab);
  assert.equal(controllerDeps.clearAdminGoogleSheetPopupStateForTab, deps.clearAdminGoogleSheetPopupStateForTab);
  assert.equal(controllerDeps.maybePreloadAdminGoogleSheetsBootstrap, deps.maybePreloadAdminGoogleSheetsBootstrap);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
  assert.equal(controllerDeps.syncTrackerChangeBellVisibility, deps.syncTrackerChangeBellVisibility);
  assert.equal(controllerDeps.hydrateTrackerChangeEventsCache, deps.hydrateTrackerChangeEventsCache);
  assert.equal(controllerDeps.renderTrackerChangeEventUnreadCount, deps.renderTrackerChangeEventUnreadCount);
  assert.equal(controllerDeps.renderTrackerChangeBellPopover, deps.renderTrackerChangeBellPopover);
  assert.equal(controllerDeps.renderAdminTopNavigation, deps.renderAdminTopNavigation);
  assert.equal(controllerDeps.renderAdminEmbedPanel, deps.renderAdminEmbedPanel);
  assert.equal(controllerDeps.renderTrackerTemplateStatus, deps.renderTrackerTemplateStatus);
  assert.equal(controllerDeps.loadAdminConsoleData, deps.loadAdminConsoleData);
  assert.equal(controllerDeps.loadBackfillConflicts, deps.loadBackfillConflicts);
  assert.equal(controllerDeps.renderBackfillConflictsPanel, deps.renderBackfillConflictsPanel);
  assert.equal(controllerDeps.closeDrawer, deps.closeDrawer);
  assert.equal(controllerDeps.renderAuthUi, deps.renderAuthUi);
  assert.equal(controllerDeps.renderOrganizationAdminPanel, deps.renderOrganizationAdminPanel);
  assert.equal(controllerDeps.renderMySalesClaimsPanel, deps.renderMySalesClaimsPanel);
  assert.equal(controllerDeps.renderSalesSummaryPanel, deps.renderSalesSummaryPanel);
  assert.equal(controllerDeps.renderRunDetail, deps.renderRunDetail);
  assert.equal(controllerDeps.renderTrackerEntries, deps.renderTrackerEntries);
  assert.equal(controllerDeps.loadOrganizationUsers, deps.loadOrganizationUsers);
  assert.equal(controllerDeps.loadTrackerEntries, deps.loadTrackerEntries);
  assert.equal(controllerDeps.loadTrackerChangeEventUnreadCount, deps.loadTrackerChangeEventUnreadCount);
  assert.equal(controllerDeps.loadTrackerChangeEvents, deps.loadTrackerChangeEvents);
  assert.equal(controllerDeps.clearUserModeRunSelection, deps.clearUserModeRunSelection);
  assert.equal(controllerDeps.hydrateHomeBootstrapCache, deps.hydrateHomeBootstrapCache);
  assert.equal(controllerDeps.loadHomeBootstrap, deps.loadHomeBootstrap);
  assert.equal(controllerDeps.scheduleTrackerChangeEventsWarmup, deps.scheduleTrackerChangeEventsWarmup);
});

test("app-support runtime builds admin google sheets controller deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    state: { adminTab: "project-status" },
    dom: { adminEmbedPanel: true },
    window: { location: { pathname: "/app/project-status" } },
    api: async () => ({}),
    flash: () => "flash",
    renderAdminTopNavigation: () => "render-admin-top-navigation",
    renderAdminEmbedPanel: () => "render-admin-embed-panel",
    canLoadProtectedConsoleData: () => true,
    maybeResolveLegacyAdminAliasToSheetTab: () => "sheet-1",
    getValidatedActiveAdminGoogleSheetTab: () => ({ key: "sheet-1" }),
    isAdminGoogleSheetTabKey: (value) => String(value || "").startsWith("sheet-"),
    isPendingLegacyAdminAlias: () => false,
    shouldDeferAdminGoogleSheetPayloadLoad: () => true,
    clearAdminGoogleSheetPopupStateForTab: () => "cleared",
    syncUrlState: () => "sync-url",
    applyUiMode: () => "apply-ui-mode",
    persistAdminGoogleSheetsCache: () => "persist-cache",
    googleSheetsRuntime: { runtime: true },
    defaultAdminTab: "project-status",
  };

  const helpers = runtime.createAdminGoogleSheetsControllerDepsHelpers(deps);
  assert.equal(typeof helpers.buildAdminGoogleSheetsControllerDeps, "function");

  const controllerDeps = helpers.buildAdminGoogleSheetsControllerDeps();
  assert.equal(controllerDeps.state, deps.state);
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.window, deps.window);
  assert.equal(controllerDeps.api, deps.api);
  assert.equal(controllerDeps.flash, deps.flash);
  assert.equal(controllerDeps.renderAdminTopNavigation, deps.renderAdminTopNavigation);
  assert.equal(controllerDeps.renderAdminEmbedPanel, deps.renderAdminEmbedPanel);
  assert.equal(controllerDeps.canLoadProtectedConsoleData, deps.canLoadProtectedConsoleData);
  assert.equal(controllerDeps.maybeResolveLegacyAdminAliasToSheetTab, deps.maybeResolveLegacyAdminAliasToSheetTab);
  assert.equal(controllerDeps.getValidatedActiveAdminGoogleSheetTab, deps.getValidatedActiveAdminGoogleSheetTab);
  assert.equal(controllerDeps.isAdminGoogleSheetTabKey, deps.isAdminGoogleSheetTabKey);
  assert.equal(controllerDeps.isPendingLegacyAdminAlias, deps.isPendingLegacyAdminAlias);
  assert.equal(controllerDeps.shouldDeferAdminGoogleSheetPayloadLoad, deps.shouldDeferAdminGoogleSheetPayloadLoad);
  assert.equal(controllerDeps.clearAdminGoogleSheetPopupStateForTab, deps.clearAdminGoogleSheetPopupStateForTab);
  assert.equal(controllerDeps.syncUrlState, deps.syncUrlState);
  assert.equal(controllerDeps.applyUiMode, deps.applyUiMode);
  assert.equal(controllerDeps.persistAdminGoogleSheetsCache, deps.persistAdminGoogleSheetsCache);
  assert.equal(controllerDeps.googleSheetsRuntime, deps.googleSheetsRuntime);
  assert.equal(controllerDeps.defaultAdminTab, deps.defaultAdminTab);
});

test("app-support runtime builds runtime enhancements deps helpers with stable deps", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const deps = {
    dom: { runtimeEnhancements: true },
    document: { name: "document" },
    syncCollectModeOptions: () => "sync-collect",
    RUN_VIEW_RUNTIME: { runtime: true },
    renderOrganizationAdminPanel: () => "render-organization-admin-panel",
  };

  const helpers = runtime.createRuntimeEnhancementsDepsHelpers(deps);
  assert.equal(typeof helpers.buildRuntimeEnhancementsDeps, "function");

  const controllerDeps = helpers.buildRuntimeEnhancementsDeps();
  assert.equal(controllerDeps.dom, deps.dom);
  assert.equal(controllerDeps.document, deps.document);
  assert.equal(controllerDeps.syncCollectModeOptions, deps.syncCollectModeOptions);
  assert.equal(controllerDeps.RUN_VIEW_RUNTIME, deps.RUN_VIEW_RUNTIME);
  assert.equal(controllerDeps.renderOrganizationAdminPanel, deps.renderOrganizationAdminPanel);
});

test("app-support runtime parses out-of-range page errors", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();

  assert.equal(runtime.isOutOfRangePageError(new Error("Requested range not satisfiable")), true);
  assert.equal(runtime.isOutOfRangePageError(new Error("offset of 2000")), true);
  assert.equal(runtime.isOutOfRangePageError(new Error("something else")), false);
  assert.equal(runtime.extractOutOfRangeTotalRows(new Error("There are only 42 rows available")), 42);
  assert.equal(runtime.extractOutOfRangeTotalRows(new Error("no row count here")), 0);
});

test("app-support runtime builds frontend runtime adapters with runtime-only aliases", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime();
  const adapters = runtime.createFrontendRuntimeAdapters({
    SALES_RUNTIME: {
      salesClaimStatusLabel: (value) => `status:${value}`,
      formatSalesDateLabel: (value) => `date:${value}`,
    },
    TRACKER_ENTRY_RUNTIME: {
      toTrackerEntrySummary: (entry) => ({ id: entry.id }),
    },
    TRACKER_CHANGE_FIELD_LABELS: {},
    EDITABLE_FIELDS: ["project_name"],
    escapeHtml: (value) => String(value ?? ""),
    formatDate: (value) => `date:${value}`,
    formatKoreanDate: (value) => `ko:${value}`,
    formatContractAmountDisplay: (value) => `won:${value}`,
    truncate: (value) => String(value ?? ""),
    getTrackerProjectSnapshot: () => null,
    sortTrackerBoardEntriesFallback: (entries) => entries,
  });

  assert.equal(typeof adapters.salesClaimStatusLabel, "function");
  assert.equal(typeof adapters.toTrackerEntrySummary, "function");
  assert.equal(typeof adapters.buildSalesClaimEstimateLabel, "function");
  assert.equal(adapters.salesClaimStatusLabel("active"), "status:active");
  assert.deepEqual(plain(adapters.toTrackerEntrySummary({ id: "tracker-1" })), { id: "tracker-1" });
});

test("app-support runtime builds sales state helpers with state-aware behavior", () => {
  const window = { SPMSAppShellRuntime: {} };
  const context = vm.createContext({ window, console });

  loadAppSupportRuntime(window, context);

  const state = {
    trackerEntries: [{ project_id: "P-1", project_name: "Tracker" }],
    selectedEntry: { project_id: "P-2", project_name: "Selected" },
    salesClaimsByProjectId: {},
    mySalesClaims: [{ project_id: "P-1", is_active: true }],
    companySalesClaims: [],
    salesClaimDrafts: {},
    organizationUsers: [{ id: "user-2", email: "teammate@example.com", status: "active" }],
    auth: { user: { role: "org_admin", local_user_id: "user-1", email: "owner@example.com" } },
  };
  const runtime = window.SPMSAppSupportRuntime.createAppSupportRuntime({ state });
  const helpers = runtime.createSalesStateHelpers({
    state,
    isAdminRole: (role) => role === "org_admin",
    buildUserSalesProjectFactsMarkup: (snapshot, estimatedAmountText) => `${snapshot?.project_name || "-"}:${estimatedAmountText}`,
    formatEokValue: (value) => String(value),
  });

  assert.deepEqual(plain(helpers.getVisibleSalesProjectIds()), ["P-1"]);
  assert.equal(helpers.getTrackerProjectSnapshot("P-1")?.project_name, "Tracker");
  assert.equal(helpers.getTrackerProjectSnapshot("P-2")?.project_name, "Selected");
  assert.equal(helpers.getSalesClaimForProject("P-1")?.project_id, "P-1");
  assert.equal(helpers.isCurrentUserClaimOwner({ owner_user_id: "user-1" }), true);
  assert.equal(helpers.canCurrentUserForceRelease(), true);
  assert.equal(helpers.canCurrentUserManageClaim({ owner_user_id: "user-1" }), true);
  assert.equal(helpers.isActiveSalesClaim({ is_active: true, claim_status: "active" }), true);
  assert.equal(helpers.getOrganizationTransferTargets({ owner_user_id: "user-1" }).length, 1);
  helpers.setSalesNoteDraft("P-1", "memo");
  assert.equal(helpers.getSalesNoteDraft("P-1"), "memo");
  helpers.mergeActiveSalesClaims([{ project_id: "P-3", is_active: true }]);
  assert.equal(state.salesClaimsByProjectId["P-3"]?.project_id, "P-3");
  assert.equal(helpers.renderUserSalesProjectFacts({ project_name: "Tracker" }, "10억원"), "Tracker:10억원");
  assert.equal(helpers.formatShortDateTime("2026-04-23T01:02:00Z").startsWith("2026-"), true);
  assert.equal(helpers.formatEstimatedAmountRangeFromKrw(100000000, 200000000), "1~2억원");
});
