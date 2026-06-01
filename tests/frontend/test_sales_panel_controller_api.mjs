import test from "node:test";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const controllerUrl = pathToFileURL(path.resolve(__dirname, "../../frontend/sales-panel-controller.js")).href;
const helpersUrl = pathToFileURL(path.resolve(__dirname, "../../frontend/sales-panel-controller-helpers.js")).href;

async function loadControllerModule() {
  return import(controllerUrl);
}

async function loadHelpersModule() {
  return import(helpersUrl);
}

function createClassListRecorder() {
  const operations = [];
  const tokens = new Set();
  return {
    operations,
    add(...values) {
      operations.push(["add", ...values]);
      for (const value of values) {
        tokens.add(value);
      }
    },
    remove(...values) {
      operations.push(["remove", ...values]);
      for (const value of values) {
        tokens.delete(value);
      }
    },
    toggle(value, force) {
      operations.push(["toggle", value, force]);
      const next = typeof force === "boolean" ? force : !tokens.has(value);
      if (next) {
        tokens.add(value);
      } else {
        tokens.delete(value);
      }
      return next;
    },
  };
}

function createInteractiveElement({
  attributes = {},
  value = "",
  innerHTML = "",
  className = "",
  querySelectorAll = () => [],
  querySelector = () => null,
} = {}) {
  let html = String(innerHTML ?? "");
  let innerHTMLWriteCount = innerHTML ? 1 : 0;
  return {
    attributes: { ...attributes },
    value,
    get innerHTML() {
      return html;
    },
    set innerHTML(nextValue) {
      html = String(nextValue ?? "");
      innerHTMLWriteCount += 1;
    },
    getInnerHTMLWriteCount: () => innerHTMLWriteCount,
    className,
    listeners: {},
    classList: createClassListRecorder(),
    getAttribute(name) {
      return this.attributes[name] ?? null;
    },
    setAttribute(name, nextValue) {
      this.attributes[name] = String(nextValue);
    },
    addEventListener(type, handler) {
      this.listeners[type] = handler;
    },
    querySelectorAll,
    querySelector,
    focus() {
      this.focused = true;
    },
  };
}

async function createSalesControllerHarness({
  state: stateOverrides = {},
  dom: domOverrides = {},
  window: windowOverrides = {},
  deps: depsOverrides = {},
} = {}) {
  const { createSalesPanelController } = await loadControllerModule();
  const apiCalls = [];
  const flashCalls = [];
  const renderTrackerEntriesCalls = [];
  const loadSalesOverviewCalls = [];
  const loadMySalesClaimsCalls = [];
  const loadVisibleSalesClaimsCalls = [];
  const refreshSalesAdminPanelsCalls = [];
  const saveSalesClaimNoteCalls = [];
  const transferSalesClaimCalls = [];
  const closeSalesClaimCalls = [];
  const releaseSalesClaimCalls = [];
  const adminDeleteLatestSalesNoteCalls = [];
  const renderUserTrackerClaimSectionCalls = [];
  const userTrackerClaimSectionMarkupCalls = [];
  const userOwnedCardViewModelCalls = [];
  const companyCardViewModelCalls = [];
  const normalizeCardViewModelCalls = [];
  const adminSectionViewModelCalls = [];
  const adminSectionMarkupCalls = [];

  const window = {
    CSS: {
      escape: (value) => String(value ?? ""),
    },
    HTMLSelectElement: class HTMLSelectElement {},
    setTimeout() {
      return 0;
    },
    clearTimeout() {},
    ...windowOverrides,
  };

  const state = {
    auth: {
      user: {
        local_user_id: "user-1",
        email: "owner@example.com",
        role: "admin",
      },
    },
    uiMode: "user",
    trackerEntries: [],
    organizationUsers: [],
    organizationUsersLoading: false,
    salesSummaryLoading: false,
    salesClosedLoading: false,
    salesSummaryError: "",
    salesClosedError: "",
    salesSummaryByUser: [],
    salesClosedClaims: [],
    mySalesClaimsLoading: false,
    mySalesClaimsError: "",
    mySalesClaims: [],
    companySalesClaims: [],
    salesClaimSavingProjectIds: {},
    salesClaimDrafts: {},
    salesClaimsByProjectId: {},
    salesCloseDialog: {
      open: false,
      projectId: "",
    },
    ...stateOverrides,
  };

  const dom = {
    salesSummaryList: createInteractiveElement(),
    trackerSalesOverviewGrid: createInteractiveElement(),
    trackerUserSalesSection: createInteractiveElement(),
    trackerUserSalesList: createInteractiveElement(),
    trackerCompanySalesSection: createInteractiveElement(),
    trackerCompanySalesList: createInteractiveElement(),
    trackerEntriesSectionTitle: createInteractiveElement(),
    ...domOverrides,
  };

  const deps = {
    api: async (url, options = {}) => {
      apiCalls.push({ url, options });
      if (typeof depsOverrides.api === "function") {
        return depsOverrides.api(url, options, { state, dom, apiCalls });
      }
      return {
        changed: true,
        claim: state.salesClaimsByProjectId["P-1"] || null,
      };
    },
    flash: (...args) => {
      flashCalls.push(args);
      return depsOverrides.flash?.(...args);
    },
    renderTrackerEntries: (...args) => {
      renderTrackerEntriesCalls.push(args);
      return depsOverrides.renderTrackerEntries?.(...args);
    },
    loadSalesOverview: (...args) => {
      loadSalesOverviewCalls.push(args);
      return depsOverrides.loadSalesOverview?.(...args);
    },
    loadMySalesClaims: (...args) => {
      loadMySalesClaimsCalls.push(args);
      return depsOverrides.loadMySalesClaims?.(...args);
    },
    loadVisibleSalesClaims: (...args) => {
      loadVisibleSalesClaimsCalls.push(args);
      return depsOverrides.loadVisibleSalesClaims?.(...args);
    },
    refreshSalesAdminPanels: (...args) => {
      refreshSalesAdminPanelsCalls.push(args);
      return depsOverrides.refreshSalesAdminPanels?.(...args);
    },
    getSalesClaimForProject: (projectId) => state.salesClaimsByProjectId[String(projectId || "").trim()] || null,
    getSalesNoteDraft: (projectId) => state.salesClaimDrafts[String(projectId || "").trim()] || "",
    setSalesNoteDraft: (projectId, value) => {
      const key = String(projectId || "").trim();
      if (!key) {
        return;
      }
      state.salesClaimDrafts[key] = String(value ?? "");
    },
    getSalesNoteEntries: (salesNote) => String(salesNote || "").split("\n").filter(Boolean),
    serializeSalesNoteEntry: (value) => String(value),
    getSalesYearMonthBucket: (value) => {
      if (!value) {
        return null;
      }
      const [year, month] = String(value).slice(0, 7).split("-");
      return { year: Number(year), month: Number(month) };
    },
    formatContractAmountDisplay: (value, fallback = "-") => `contract:${value ?? fallback}`,
    formatSalesDateLabel: (value) => `date:${value ?? ""}`,
    formatSalesNoteTextForDisplay: (value) => `note:${value ?? ""}`,
    getLatestSalesNoteItem: (salesNote, claimedAt) => {
      const note = String(salesNote || "").trim();
      return note ? { timestamp: claimedAt ? "2026-04-01" : "", text: note } : null;
    },
    truncate: (value) => String(value ?? ""),
    salesClaimStatusLabel: (value) => `status:${value}`,
    extractContractAmountTextFromSalesNote: () => "contract-note",
    getOrganizationTransferTargets: (claim) => (state.organizationUsers || []).filter((item) => String(item.id || "") !== String(claim?.owner_user_id || "")),
    canCurrentUserForceRelease: () => true,
    canCurrentUserManageClaim: (claim) => Boolean(claim),
    isCurrentUserClaimOwner: (claim) => Boolean(claim && String(claim.owner_user_id || "") === String(state.auth.user?.local_user_id || "")),
    isActiveSalesClaim: (claim) => Boolean(claim?.is_active),
    formatEstimatedAmountRangeFromKrw: (low, high, fallback = "-") => `range:${low ?? high ?? fallback}`,
    formatContractAmountInput: (value) => String(value ?? "").replace(/\D+/g, ""),
    buildUserSalesProjectFactsMarkup: () => "",
    buildSalesClaimEstimateLabelMarkup: (claim) => `estimate:${claim?.project_id || ""}`,
    buildUserOwnedSalesClaimCardMarkup: (payload) => `owned:${payload.claim.project_id}:${payload.saving}`,
    buildCompanySalesClaimCardMarkup: (payload) => `company:${payload.claim.project_id}`,
    formatSalesClaimEstimateLabel: (claim) => `estimate:${claim?.project_id || ""}`,
    buildUserTrackerClaimSectionMarkup: (payload) => {
      userTrackerClaimSectionMarkupCalls.push(payload);
      return `user-tracker:${payload.projectId}:${Boolean(payload.saving)}`;
    },
    formatEokValue: (value) => String(value ?? ""),
    escapeHtml: (value) => String(value ?? ""),
    getSalesNoteTimeline: (salesNote, claimedAt) => (String(salesNote || "").trim() ? [{ timestamp: claimedAt || "", text: String(salesNote) }] : []),
    removeLatestSalesNoteEntry: (value) => String(value || "").split("\n").slice(0, -1).join("\n"),
    isAdminRole: (role) => role === "admin",
    normalizeSalesClaimCardViewModel: (payload, options) => {
      normalizeCardViewModelCalls.push({ payload, options });
      const noteEntries = Array.isArray(payload.noteEntries) ? payload.noteEntries : [];
      const result = {
        ...payload,
        projectId: payload.projectId || String(payload.claim?.project_id || "").trim(),
        noteEntries,
        showAssignedAt: payload.showAssignedAt ?? Boolean(options?.shouldShowCurrentOwnerAssignedAt?.(payload.claim || {})),
      };
      if (options?.includeOwnerLabel) {
        result.latestNote = Object.prototype.hasOwnProperty.call(payload, "latestNote")
          ? payload.latestNote
          : (noteEntries.length ? noteEntries[noteEntries.length - 1] : null);
        result.ownerLabel = Object.prototype.hasOwnProperty.call(payload, "ownerLabel")
          ? payload.ownerLabel
          : (payload.claim?.owner_display_name || payload.claim?.owner_email || "-");
      }
      return result;
    },
    renderTrackerEntries: (...args) => {
      renderTrackerEntriesCalls.push(args);
      return depsOverrides.renderTrackerEntries?.(...args);
    },
    loadSalesOverview: (...args) => {
      loadSalesOverviewCalls.push(args);
      return depsOverrides.loadSalesOverview?.(...args);
    },
    loadMySalesClaims: (...args) => {
      loadMySalesClaimsCalls.push(args);
      return depsOverrides.loadMySalesClaims?.(...args);
    },
    loadVisibleSalesClaims: (...args) => {
      loadVisibleSalesClaimsCalls.push(args);
      return depsOverrides.loadVisibleSalesClaims?.(...args);
    },
    refreshSalesAdminPanels: (...args) => {
      refreshSalesAdminPanelsCalls.push(args);
      return depsOverrides.refreshSalesAdminPanels?.(...args);
    },
    renderUserOwnedSalesClaimCard: (claim, index) => `user-card:${index}:${claim.project_id}`,
    renderCompanySalesClaimCard: (claim, index) => `company-card:${index}:${claim.project_id}`,
    renderUserTrackerClaimSection: (...args) => {
      renderUserTrackerClaimSectionCalls.push(args);
      return depsOverrides.renderUserTrackerClaimSection?.(...args) || `user-section:${args[1].projectId}`;
    },
    salesViewRuntime: {
      shouldShowCurrentOwnerAssignedAt: (claim) => claim?.current_owner_assigned_at === "show-me",
      buildUserOwnedSalesClaimCardViewModel: (payload) => {
        userOwnedCardViewModelCalls.push(payload);
        return payload;
      },
      buildCompanySalesClaimCardViewModel: (payload) => {
        companyCardViewModelCalls.push(payload);
        return payload;
      },
      buildAdminSalesClaimSectionViewModel: (payload) => {
        adminSectionViewModelCalls.push(payload);
        return payload;
      },
      buildAdminSalesClaimSectionMarkup: (payload, helpers) => {
        adminSectionMarkupCalls.push({ payload, helpers });
        return `admin-section:${payload.projectId}:${payload.claimStatus}`;
      },
      buildSalesTransferOptionsMarkup: () => "",
      buildRawSalesNoteTimelineMarkup: () => "",
      ...depsOverrides.salesViewRuntime,
    },
    saveSalesClaimNote: (...args) => {
      saveSalesClaimNoteCalls.push(args);
      return depsOverrides.saveSalesClaimNote?.(...args);
    },
    transferSalesClaim: (...args) => {
      transferSalesClaimCalls.push(args);
      return depsOverrides.transferSalesClaim?.(...args);
    },
    closeSalesClaim: (...args) => {
      closeSalesClaimCalls.push(args);
      return depsOverrides.closeSalesClaim?.(...args);
    },
    adminDeleteLatestSalesNote: (...args) => {
      adminDeleteLatestSalesNoteCalls.push(args);
      return depsOverrides.adminDeleteLatestSalesNote?.(...args);
    },
    releaseSalesClaim: (...args) => {
      releaseSalesClaimCalls.push(args);
      return depsOverrides.releaseSalesClaim?.(...args);
    },
    ...depsOverrides,
  };

  const controller = createSalesPanelController({
    state,
    dom,
    window,
    ...deps,
  });

  return {
    controller,
    state,
    dom,
    window,
    calls: {
      apiCalls,
      flashCalls,
      renderTrackerEntriesCalls,
      loadSalesOverviewCalls,
      loadMySalesClaimsCalls,
      loadVisibleSalesClaimsCalls,
      refreshSalesAdminPanelsCalls,
      saveSalesClaimNoteCalls,
      transferSalesClaimCalls,
      closeSalesClaimCalls,
      releaseSalesClaimCalls,
      adminDeleteLatestSalesNoteCalls,
      renderUserTrackerClaimSectionCalls,
      userTrackerClaimSectionMarkupCalls,
      userOwnedCardViewModelCalls,
      companyCardViewModelCalls,
      normalizeCardViewModelCalls,
      adminSectionViewModelCalls,
      adminSectionMarkupCalls,
    },
  };
}

test("sales panel helper state functions preserve visible claim drafts", async () => {
  const { createSalesPanelControllerHelpers } = await loadHelpersModule();
  const state = {
    auth: { user: { local_user_id: "user-1", email: "owner@example.com", role: "admin" } },
    trackerEntries: [
      { project_id: "P-1" },
      { project_id: "P-2" },
    ],
    salesClaimsByProjectId: {
      "P-1": { project_id: "P-1", is_active: true, owner_user_id: "user-1", owner_email: "owner@example.com" },
      "P-2": { project_id: "P-2", is_active: true, owner_user_id: "user-1", owner_email: "owner@example.com" },
    },
    salesClaimDrafts: {
      "P-1": "draft-1",
      "P-2": "draft-2",
    },
    mySalesClaims: [],
    companySalesClaims: [],
    organizationUsers: [],
    selectedEntry: null,
  };

  const helpers = createSalesPanelControllerHelpers({
    state,
    buildUserSalesProjectFactsMarkup: (snapshot, amountText) => `facts:${snapshot?.project_id || ""}:${amountText}`,
    formatEokValue: (value) => String(value),
    isAdminRole: (role) => role === "admin",
  });

  assert.deepEqual(helpers.getVisibleSalesProjectIds(), ["P-1", "P-2"]);
  helpers.replaceVisibleSalesClaims([
    { project_id: "P-1", is_active: true, owner_user_id: "user-1", owner_email: "owner@example.com" },
    { project_id: "P-2", is_active: true, owner_user_id: "user-1", owner_email: "owner@example.com" },
  ]);
  assert.equal(state.salesClaimDrafts["P-1"], "draft-1");
  assert.equal(state.salesClaimDrafts["P-2"], "draft-2");
  assert.equal(helpers.renderUserSalesProjectFacts({ project_id: "P-9" }, "123"), "facts:P-9:123");
  assert.match(helpers.formatEstimatedAmountRangeFromKrw(100000000, 100000000, "-"), /^1/);
});

test("claimSalesProject uses the provided api dependency", async () => {
  const { createSalesPanelController } = await loadControllerModule();
  const apiCalls = [];
  const state = {
    salesClaimSavingProjectIds: {},
    trackerEntries: [],
    uiMode: "user",
    organizationUsers: [],
    salesClaimsByProjectId: {},
    mySalesClaims: [],
    companySalesClaims: [],
  };

  const controller = createSalesPanelController({
    api: async (url, options = {}) => {
      apiCalls.push({ url, options });
      return {
        claim: {
          project_id: "P-1",
          is_active: true,
        },
        changed: true,
      };
    },
    state,
    dom: {},
    window: {},
    flash: () => {},
    renderTrackerEntries: () => {},
    loadSalesOverview: () => {},
    loadMySalesClaims: () => {},
    loadVisibleSalesClaims: () => {},
    refreshSalesAdminPanels: () => {},
    getSalesClaimForProject: () => null,
    getSalesNoteDraft: () => "",
    setSalesNoteDraft: () => {},
    getSalesNoteEntries: () => [],
    serializeSalesNoteEntry: (value) => String(value),
    getSalesYearMonthBucket: () => null,
    formatContractAmountDisplay: (value, fallback = "-") => String(value || fallback),
    formatSalesDateLabel: (value) => String(value || ""),
    formatSalesNoteTextForDisplay: (value) => String(value || ""),
    getLatestSalesNoteItem: () => null,
    truncate: (value) => String(value || ""),
    salesClaimStatusLabel: (value) => String(value || ""),
    extractContractAmountTextFromSalesNote: () => "",
    getOrganizationTransferTargets: () => [],
    canCurrentUserForceRelease: () => false,
    canCurrentUserManageClaim: () => false,
    isCurrentUserClaimOwner: () => false,
    isActiveSalesClaim: () => true,
    formatEstimatedAmountRangeFromKrw: (low, high, fallback = "-") => String(low ?? high ?? fallback),
    formatContractAmountInput: (value) => String(value || ""),
    buildUserSalesProjectFactsMarkup: () => "",
    buildSalesClaimEstimateLabelMarkup: () => "",
    buildUserOwnedSalesClaimCardMarkup: () => "",
    buildCompanySalesClaimCardMarkup: () => "",
    buildUserTrackerClaimSectionMarkup: () => "",
    formatEokValue: (value) => String(value || ""),
    getSalesClaimForProject: () => null,
    upsertSalesClaim: () => {},
    replaceVisibleSalesClaims: () => {},
    mergeActiveSalesClaims: () => {},
    claimSalesProject: null,
    saveSalesClaimNote: null,
    transferSalesClaim: null,
    closeSalesClaim: null,
    adminDeleteLatestSalesNote: null,
    releaseSalesClaim: null,
    loadSalesOverview: () => {},
    loadMySalesClaims: () => {},
    loadVisibleSalesClaims: () => {},
    refreshSalesAdminPanels: () => {},
    isAdminRole: () => false,
    getVisibleSalesProjectIds: () => [],
    getSalesClaimForProject: () => null,
    getTrackerProjectSnapshot: () => null,
    renderUserSalesProjectFacts: () => "",
    renderUserOwnedSalesClaimCard: () => "",
    formatSalesClaimEstimateLabel: () => "",
    renderCompanySalesClaimCard: () => "",
    renderUserTrackerClaimSection: () => "",
    renderSalesNoteTimelineMarkup: () => "",
    renderSalesSummaryPanel: () => {},
    renderClosedSalesArchiveSection: () => "",
    renderMySalesClaimsPanel: () => {},
    bindUserSalesSectionEvents: () => {},
    salesViewRuntime: {
      buildSalesNoteTimelineMarkup: () => "",
    },
  });

  await controller.claimSalesProject({
    id: "entry-1",
    project_id: "P-1",
    project_name: "Project",
    building_automation_estimated_amount: "123",
  });

  assert.equal(apiCalls.length, 1);
  assert.equal(apiCalls[0].url, "/api/sales-claims/projects/P-1/claim");
  assert.equal(apiCalls[0].options.method, "POST");
  assert.equal(state.salesClaimSavingProjectIds["P-1"], undefined);
});

test("renderSalesSummaryPanel renders admin summary markup and wires action buttons", async () => {
  const summaryProject = {
    project_id: "P-1",
    project_name: "Project One",
    sales_note: "First note",
    claimed_at: "2024-01-02",
    owner_elapsed_days: 3,
    elapsed_days: 7,
  };
  const releaseButton = createInteractiveElement({
    attributes: { "data-sales-force-release": "P-1" },
  });
  const deleteButton = createInteractiveElement({
    attributes: { "data-sales-force-delete-note": "P-1" },
  });
  const { controller, dom, calls } = await createSalesControllerHarness({
    state: {
      uiMode: "admin",
      salesSummaryByUser: [
        {
          user_name: "Sales Owner",
          user_email: "sales@example.com",
          active_project_count: 1,
          total_low_krw: 1000,
          total_high_krw: 2000,
          projects: [summaryProject],
        },
      ],
      salesClosedClaims: [
        {
          project_id: "P-2",
          project_name: "Closed Won",
          claim_status: "won",
          closed_at: "2024-01-11",
          sales_note: "Won note",
        },
        {
          project_id: "P-3",
          project_name: "Closed Lost",
          claim_status: "lost",
          closed_at: "2024-02-12",
          sales_note: "",
        },
      ],
    },
    dom: {
      salesSummaryList: createInteractiveElement({
        querySelectorAll(selector) {
          if (selector === "[data-sales-force-release]") {
            return [releaseButton];
          }
          if (selector === "[data-sales-force-delete-note]") {
            return [deleteButton];
          }
          return [];
        },
      }),
    },
  });

  controller.renderSalesSummaryPanel();

  assert.match(dom.salesSummaryList.innerHTML, /sales-summary-section/);
  assert.match(dom.salesSummaryList.innerHTML, /Sales Owner/);
  assert.match(dom.salesSummaryList.innerHTML, /Project One/);
  assert.match(dom.salesSummaryList.innerHTML, /sales-summary-archive-group/);
  assert.match(dom.salesSummaryList.innerHTML, /data-sales-force-release="P-1"/);
  assert.match(dom.salesSummaryList.innerHTML, /data-sales-force-delete-note="P-1"/);
  assert.equal(typeof releaseButton.listeners.click, "function");
  assert.equal(typeof deleteButton.listeners.click, "function");

  releaseButton.listeners.click();
  deleteButton.listeners.click();

  assert.equal(calls.apiCalls[0].url, "/api/sales-claims/projects/P-1/release");
  assert.equal(calls.apiCalls[0].options.method, "POST");
  assert.equal(calls.apiCalls[1].url, "/api/sales-claims/projects/P-1");
  assert.equal(calls.apiCalls[1].options.method, "PATCH");
  assert.match(String(calls.apiCalls[1].options.body || ""), /force_admin_override/);
});

test("renderMySalesClaimsPanel renders the user lists and binds sales section interactions", async () => {
  const noteTextarea = createInteractiveElement({
    attributes: { "data-user-sales-note": "P-1" },
    value: "",
  });
  const saveButton = createInteractiveElement({
    attributes: { "data-user-sales-note-save": "P-1" },
  });
  const transferButton = createInteractiveElement({
    attributes: { "data-user-sales-transfer": "P-1" },
  });
  const closeWonButton = createInteractiveElement({
    attributes: {
      "data-user-sales-close": "P-1",
      "data-user-sales-close-outcome": "won",
    },
  });
  const closeLostButton = createInteractiveElement({
    attributes: {
      "data-user-sales-close": "P-2",
      "data-user-sales-close-outcome": "lost",
    },
  });
  const releaseButton = createInteractiveElement({
    attributes: { "data-user-sales-release": "P-1" },
  });
  let transferSelect = null;

  const { controller, state, dom, calls, window: testWindow } = await createSalesControllerHarness({
    state: {
      uiMode: "user",
      mySalesClaims: [
        {
          project_id: "P-1",
          project_name: "Owned Project",
          claimed_at: "2024-01-01",
          sales_note: "Initial note",
        },
      ],
      companySalesClaims: [
        {
          project_id: "P-2",
          owner_display_name: "Company Owner",
          project_name: "Company Project",
          claimed_at: "2024-01-02",
          sales_note: "Company note",
        },
      ],
      salesClaimsByProjectId: {
        "P-1": {
          project_id: "P-1",
          owner_user_id: "user-1",
          owner_email: "owner@example.com",
          claimed_at: "2024-01-01",
          current_owner_assigned_at: "show-me",
          sales_note: "Initial note",
          claim_status: "active",
          is_active: true,
        },
        "P-2": {
          project_id: "P-2",
          owner_user_id: "user-2",
          owner_email: "other@example.com",
          claimed_at: "2024-01-02",
          claim_status: "active",
          is_active: true,
        },
      },
      organizationUsers: [
        { id: "U-2", email: "transfer@example.com", display_name: "Transfer Target", status: "active" },
      ],
    },
    dom: {
      trackerSalesOverviewGrid: createInteractiveElement(),
      trackerUserSalesSection: createInteractiveElement(),
      trackerUserSalesList: createInteractiveElement({
        querySelectorAll(selector) {
          if (selector === "[data-user-sales-note]") {
            return [noteTextarea];
          }
          if (selector === "[data-user-sales-note-save]") {
            return [saveButton];
          }
          if (selector === "[data-user-sales-transfer]") {
            return [transferButton];
          }
          if (selector === "[data-user-sales-close]") {
            return [closeWonButton, closeLostButton];
          }
          if (selector === "[data-user-sales-release]") {
            return [releaseButton];
          }
          return [];
        },
        querySelector(selector) {
          if (selector === '[data-user-sales-transfer-select="P-1"]') {
            return transferSelect;
          }
          return null;
        },
      }),
      trackerCompanySalesSection: createInteractiveElement(),
      trackerCompanySalesList: createInteractiveElement(),
      trackerEntriesSectionTitle: createInteractiveElement(),
    },
    deps: {
      buildUserOwnedSalesClaimCardMarkup: (payload) => `
        <article>
          <textarea data-user-sales-note="${payload.claim.project_id}"></textarea>
          <button data-user-sales-note-save="${payload.claim.project_id}">save</button>
          <select data-user-sales-transfer-select="${payload.claim.project_id}"></select>
          <button data-user-sales-transfer="${payload.claim.project_id}">transfer</button>
          <button data-user-sales-close="${payload.claim.project_id}" data-user-sales-close-outcome="won">close-won</button>
          <button data-user-sales-release="${payload.claim.project_id}">release</button>
        </article>
      `,
      buildCompanySalesClaimCardMarkup: (payload) => `
        <article>
          <button data-user-sales-close="${payload.claim.project_id}" data-user-sales-close-outcome="lost">close-lost</button>
        </article>
      `,
    },
  });

  controller.renderMySalesClaimsPanel();

  transferSelect = new testWindow.HTMLSelectElement();
  transferSelect.value = "U-2";

  assert.deepEqual(dom.trackerSalesOverviewGrid.classList.operations[0], ["toggle", "hidden", false]);
  assert.match(dom.trackerUserSalesList.innerHTML, /data-user-sales-note="P-1"/);
  assert.match(dom.trackerUserSalesList.innerHTML, /data-user-sales-note-save="P-1"/);
  assert.match(dom.trackerUserSalesList.innerHTML, /data-user-sales-transfer="P-1"/);
  assert.match(dom.trackerUserSalesList.innerHTML, /data-user-sales-close="P-1"/);
  assert.match(dom.trackerUserSalesList.innerHTML, /data-user-sales-release="P-1"/);
  assert.match(dom.trackerCompanySalesList.innerHTML, /data-user-sales-close="P-2"/);
  assert.equal(typeof noteTextarea.listeners.input, "function");
  assert.equal(typeof noteTextarea.listeners.keydown, "function");
  assert.equal(typeof saveButton.listeners.click, "function");
  assert.equal(typeof transferButton.listeners.click, "function");
  assert.equal(typeof closeWonButton.listeners.click, "function");
  assert.equal(typeof closeLostButton.listeners.click, "function");
  assert.equal(typeof releaseButton.listeners.click, "function");
  assert.equal(calls.userOwnedCardViewModelCalls.length, 1);
  assert.equal(calls.companyCardViewModelCalls.length, 1);
  assert.deepEqual(calls.userOwnedCardViewModelCalls[0], {
    claim: state.mySalesClaims[0],
    index: 0,
    projectId: "P-1",
    saving: false,
    noteDraft: "",
    noteEntries: [{ timestamp: "2024-01-01", text: "Initial note" }],
    snapshot: null,
    transferTargets: [
      { id: "U-2", email: "transfer@example.com", display_name: "Transfer Target", status: "active" },
    ],
    organizationUsersLoading: false,
  });
  assert.deepEqual(calls.companyCardViewModelCalls[0], {
    claim: state.companySalesClaims[0],
    index: 0,
    noteEntries: [{ timestamp: "2024-01-02", text: "Company note" }],
    snapshot: null,
  });

  noteTextarea.value = " Updated note ";
  noteTextarea.listeners.input();
  assert.equal(state.salesClaimDrafts["P-1"], " Updated note ");

  saveButton.listeners.click();
  assert.deepEqual(calls.apiCalls[0].url, "/api/sales-claims/projects/P-1");
  assert.equal(calls.apiCalls[0].options.method, "PATCH");

  noteTextarea.value = "Ctrl note";
  noteTextarea.listeners.keydown({
    key: "Enter",
    ctrlKey: true,
    metaKey: false,
    preventDefault() {},
  });
  assert.equal(calls.apiCalls[1].url, "/api/sales-claims/projects/P-1");
  assert.equal(calls.apiCalls[1].options.method, "PATCH");

  transferButton.listeners.click();
  assert.equal(calls.apiCalls[2].url, "/api/sales-claims/projects/P-1/transfer");
  assert.equal(calls.apiCalls[2].options.method, "POST");

  closeWonButton.listeners.click();
  assert.equal(state.salesCloseDialog.open, true);
  assert.equal(state.salesCloseDialog.projectId, "P-1");

  closeLostButton.listeners.click();
  assert.equal(calls.apiCalls[3].url, "/api/sales-claims/projects/P-2/close");
  assert.equal(calls.apiCalls[3].options.method, "POST");

  releaseButton.listeners.click();
  assert.equal(calls.apiCalls[4].url, "/api/sales-claims/projects/P-1/release");
  assert.equal(calls.apiCalls[4].options.method, "POST");
});

test("renderMySalesClaimsPanel preserves sales list DOM when rendered markup is unchanged", async () => {
  const { controller, dom } = await createSalesControllerHarness({
    state: {
      uiMode: "user",
      mySalesClaims: [{ project_id: "P-1", project_name: "충주삼원초 학교복합시설 건립 설계 공모" }],
      companySalesClaims: [{ project_id: "P-2", project_name: "Company Project" }],
      salesClaimsByProjectId: {
        "P-1": { project_id: "P-1", project_name: "충주삼원초 학교복합시설 건립 설계 공모", claim_status: "active", is_active: true },
        "P-2": { project_id: "P-2", project_name: "Company Project", claim_status: "active", is_active: true },
      },
    },
    deps: {
      buildUserOwnedSalesClaimCardMarkup: (payload) => `<article>${payload.claim.project_name}</article>`,
      buildCompanySalesClaimCardMarkup: (payload) => `<article>${payload.claim.project_name}</article>`,
    },
  });

  controller.renderMySalesClaimsPanel();
  const userWrites = dom.trackerUserSalesList.getInnerHTMLWriteCount();
  const companyWrites = dom.trackerCompanySalesList.getInnerHTMLWriteCount();

  controller.renderMySalesClaimsPanel();

  assert.equal(dom.trackerUserSalesList.getInnerHTMLWriteCount(), userWrites);
  assert.equal(dom.trackerCompanySalesList.getInnerHTMLWriteCount(), companyWrites);
});

test("renderMySalesClaimsPanel defers sales list replacement while text selection is active", async () => {
  let selectionActive = true;
  let deferredRender = null;
  const { controller, dom, state } = await createSalesControllerHarness({
    window: {
      getSelection: () => ({
        isCollapsed: !selectionActive,
        toString: () => (selectionActive ? "충주삼원초 학교복합시설" : ""),
      }),
      setTimeout: (handler) => {
        deferredRender = handler;
        return 1;
      },
    },
    state: {
      uiMode: "user",
      mySalesClaims: [{ project_id: "P-1", project_name: "충주삼원초 학교복합시설 건립 설계 공모" }],
      companySalesClaims: [{ project_id: "P-2", project_name: "Company Project" }],
      salesClaimsByProjectId: {
        "P-1": { project_id: "P-1", project_name: "충주삼원초 학교복합시설 건립 설계 공모", claim_status: "active", is_active: true },
        "P-2": { project_id: "P-2", project_name: "Company Project", claim_status: "active", is_active: true },
      },
    },
    deps: {
      buildUserOwnedSalesClaimCardMarkup: (payload) => `<article>${payload.claim.project_name}</article>`,
      buildCompanySalesClaimCardMarkup: (payload) => `<article>${payload.claim.project_name}</article>`,
    },
  });

  controller.renderMySalesClaimsPanel();
  const userWrites = dom.trackerUserSalesList.getInnerHTMLWriteCount();
  state.mySalesClaimsLoading = true;
  controller.renderMySalesClaimsPanel();

  assert.equal(dom.trackerUserSalesList.getInnerHTMLWriteCount(), userWrites);
  assert.match(dom.trackerUserSalesList.innerHTML, /충주삼원초 학교복합시설/);
  assert.equal(typeof deferredRender, "function");

  selectionActive = false;
  deferredRender();

  assert.equal(dom.trackerUserSalesList.getInnerHTMLWriteCount(), userWrites + 1);
  assert.match(dom.trackerUserSalesList.innerHTML, /영업 정보를 불러오는 중입니다/);
});

test("renderMySalesClaimsPanel defers sales list replacement while a sales title drag is starting", async () => {
  const timeoutHandlers = [];
  const windowListeners = {};
  const { controller, dom, state } = await createSalesControllerHarness({
    window: {
      getSelection: () => ({
        isCollapsed: true,
        toString: () => "",
      }),
      addEventListener: (type, handler) => {
        windowListeners[type] = handler;
      },
      setTimeout: (handler, delay = 0) => {
        timeoutHandlers.push({ handler, delay });
        return timeoutHandlers.length;
      },
    },
    state: {
      uiMode: "user",
      mySalesClaims: [{ project_id: "P-1", project_name: "충주삼원초 학교복합시설 건립 설계 공모" }],
      companySalesClaims: [{ project_id: "P-2", project_name: "Company Project" }],
      salesClaimsByProjectId: {
        "P-1": { project_id: "P-1", project_name: "충주삼원초 학교복합시설 건립 설계 공모", claim_status: "active", is_active: true },
        "P-2": { project_id: "P-2", project_name: "Company Project", claim_status: "active", is_active: true },
      },
    },
    deps: {
      buildUserOwnedSalesClaimCardMarkup: (payload) => `<article>${payload.claim.project_name}</article>`,
      buildCompanySalesClaimCardMarkup: (payload) => `<article>${payload.claim.project_name}</article>`,
    },
  });

  controller.renderMySalesClaimsPanel();
  const userWrites = dom.trackerUserSalesList.getInnerHTMLWriteCount();
  dom.trackerUserSalesList.listeners.pointerdown?.({});
  state.mySalesClaimsLoading = true;
  controller.renderMySalesClaimsPanel();

  assert.equal(dom.trackerUserSalesList.getInnerHTMLWriteCount(), userWrites);
  assert.match(dom.trackerUserSalesList.innerHTML, /충주삼원초 학교복합시설/);
  assert.equal(timeoutHandlers.length, 1);

  windowListeners.pointerup?.({});
  assert.equal(timeoutHandlers.length, 2);
  timeoutHandlers.sort((left, right) => left.delay - right.delay);
  timeoutHandlers.shift().handler();
  timeoutHandlers.shift().handler();

  assert.equal(dom.trackerUserSalesList.getInnerHTMLWriteCount(), userWrites + 1);
  assert.match(dom.trackerUserSalesList.innerHTML, /영업 정보를 불러오는 중입니다/);
});

test("renderMySalesClaimsPanel preserves markup fallback when sales view runtime claim helpers are missing", async () => {
  const ownedPayloads = [];
  const companyPayloads = [];
  const { controller, dom, state, calls } = await createSalesControllerHarness({
    state: {
      uiMode: "user",
      mySalesClaims: [
        {
          project_id: "P-1",
          project_name: "Owned Project",
          claimed_at: "2024-01-01",
          sales_note: "Initial note",
        },
      ],
      companySalesClaims: [
        {
          project_id: "P-2",
          project_name: "Company Project",
          owner_display_name: "Company Owner",
          claimed_at: "2024-01-02",
          sales_note: "Company note",
        },
      ],
      salesClaimsByProjectId: {
        "P-1": {
          project_id: "P-1",
          owner_user_id: "user-1",
          owner_email: "owner@example.com",
          claimed_at: "2024-01-01",
          current_owner_assigned_at: "2024-01-03",
          sales_note: "Initial note",
          claim_status: "active",
          is_active: true,
        },
        "P-2": {
          project_id: "P-2",
          owner_user_id: "user-2",
          owner_email: "other@example.com",
          claimed_at: "2024-01-02",
          current_owner_assigned_at: "2024-01-04",
          sales_note: "Company note",
          claim_status: "active",
          is_active: true,
        },
      },
    },
    deps: {
      salesViewRuntime: {
        shouldShowCurrentOwnerAssignedAt: () => true,
        buildUserOwnedSalesClaimCardViewModel: undefined,
        buildCompanySalesClaimCardViewModel: undefined,
      },
      buildUserOwnedSalesClaimCardMarkup: (payload) => {
        ownedPayloads.push(payload);
        return `owned:${payload.claim.project_id}`;
      },
      buildCompanySalesClaimCardMarkup: (payload) => {
        companyPayloads.push(payload);
        return `company:${payload.claim.project_id}`;
      },
      renderUserSalesProjectFacts: () => "",
    },
  });

  controller.renderMySalesClaimsPanel();

  assert.equal(ownedPayloads.length, 1);
  assert.equal(companyPayloads.length, 1);
  assert.deepEqual(ownedPayloads[0], {
    claim: state.mySalesClaims[0],
    index: 0,
    projectId: "P-1",
    saving: false,
    noteDraft: "",
    noteEntries: [{ timestamp: "2024-01-01", text: "Initial note" }],
    snapshot: null,
    transferTargets: [],
    organizationUsersLoading: false,
    showAssignedAt: true,
  });
  assert.deepEqual(companyPayloads[0], {
    claim: state.companySalesClaims[0],
    index: 0,
    noteEntries: [{ timestamp: "2024-01-02", text: "Company note" }],
    snapshot: null,
    projectId: "P-2",
    showAssignedAt: true,
    latestNote: { timestamp: "2024-01-02", text: "Company note" },
    ownerLabel: "Company Owner",
  });
  assert.equal(calls.normalizeCardViewModelCalls.length, 2);
  assert.equal(calls.normalizeCardViewModelCalls[0].options.includeOwnerLabel, undefined);
  assert.equal(calls.normalizeCardViewModelCalls[1].options.includeOwnerLabel, true);
  assert.equal(typeof calls.normalizeCardViewModelCalls[0].options.shouldShowCurrentOwnerAssignedAt, "function");
  assert.equal(typeof calls.normalizeCardViewModelCalls[1].options.shouldShowCurrentOwnerAssignedAt, "function");
  assert.match(dom.trackerUserSalesList.innerHTML, /owned:P-1/);
  assert.match(dom.trackerCompanySalesList.innerHTML, /company:P-2/);
});

test("renderMySalesClaimsPanel renders readable Korean empty states for user mode", async () => {
  const { controller, dom } = await createSalesControllerHarness({
    state: {
      uiMode: "user",
      mySalesClaimsLoading: false,
      mySalesClaimsError: "",
      mySalesClaims: [],
      companySalesClaims: [],
    },
  });

  controller.renderMySalesClaimsPanel();

  assert.match(dom.trackerUserSalesList.innerHTML, /현재 내가 진행 중인 영업 프로젝트가 없습니다\./);
  assert.match(dom.trackerCompanySalesList.innerHTML, /현재 회사 전체가 진행 중인 영업 프로젝트가 없습니다\./);
});

test("sales close dialog opens, resets, and confirms through controller state", async () => {
  const scheduledTimeouts = [];
  const salesCloseDialog = createInteractiveElement();
  const salesCloseAmountInput = createInteractiveElement({ value: "999999" });
  const { controller, state, calls } = await createSalesControllerHarness({
    dom: {
      salesCloseDialog,
      salesCloseAmountInput,
    },
    window: {
      setTimeout(callback) {
        scheduledTimeouts.push(callback);
        return scheduledTimeouts.length;
      },
    },
  });

  controller.openSalesCloseDialog("  P-1  ");

  assert.equal(state.salesCloseDialog.open, true);
  assert.equal(state.salesCloseDialog.projectId, "P-1");
  assert.equal(salesCloseAmountInput.value, "");
  assert.deepEqual(salesCloseDialog.classList.operations[0], ["remove", "hidden"]);
  assert.equal(scheduledTimeouts.length, 1);

  scheduledTimeouts[0]();
  assert.equal(salesCloseAmountInput.focused, true);

  salesCloseAmountInput.value = "777777";
  controller.closeSalesCloseDialog();
  assert.equal(state.salesCloseDialog.open, false);
  assert.equal(state.salesCloseDialog.projectId, "");
  assert.equal(salesCloseAmountInput.value, "");
  assert.deepEqual(salesCloseDialog.classList.operations.at(-1), ["add", "hidden"]);

  controller.openSalesCloseDialog("P-1");
  assert.equal(state.salesCloseDialog.open, true);
  assert.equal(state.salesCloseDialog.projectId, "P-1");

  salesCloseAmountInput.value = "   ";
  await controller.confirmSalesCloseDialog();
  assert.equal(state.salesCloseDialog.open, true);
  assert.equal(calls.closeSalesClaimCalls.length, 0);
  assert.equal(calls.flashCalls.at(-1)[1], "warn");
  assert.equal(salesCloseAmountInput.focused, true);

  salesCloseAmountInput.value = "123456";
  await controller.confirmSalesCloseDialog();

  assert.equal(state.salesCloseDialog.open, false);
  assert.equal(state.salesCloseDialog.projectId, "");
  assert.equal(salesCloseAmountInput.value, "");
  assert.equal(calls.apiCalls[0].url, "/api/sales-claims/projects/P-1/close");
  assert.equal(calls.apiCalls[0].options.method, "POST");
  assert.match(String(calls.apiCalls[0].options.body || ""), /"outcome":"won"/);
  assert.match(String(calls.apiCalls[0].options.body || ""), /"contract_amount_text":"123456"/);
  assert.deepEqual(salesCloseDialog.classList.operations.at(-1), ["add", "hidden"]);
});

test("renderSalesClaimSection switches between user and admin payloads", async () => {
  const { controller, state, calls } = await createSalesControllerHarness({
    state: {
      uiMode: "user",
      salesClaimsByProjectId: {
        "P-1": {
          project_id: "P-1",
          owner_user_id: "user-2",
          owner_email: "other@example.com",
          sales_note: "Note body",
          claimed_at: "2024-01-03",
          current_owner_assigned_at: "show-me",
          claim_status: "active",
          is_active: true,
        },
      },
    },
  });

  const userResult = controller.renderSalesClaimSection({ project_id: "P-1" });
  assert.equal(userResult, "user-tracker:P-1:false");
  assert.equal(calls.renderUserTrackerClaimSectionCalls.length, 0);
  assert.equal(calls.userTrackerClaimSectionMarkupCalls.length, 1);
  assert.deepEqual(calls.userTrackerClaimSectionMarkupCalls[0], {
    entry: { project_id: "P-1" },
    projectId: "P-1",
    claim: state.salesClaimsByProjectId["P-1"],
    saving: false,
  });

  state.uiMode = "admin";
  const adminResult = controller.renderSalesClaimSection({ project_id: "P-1" });
  assert.equal(adminResult, "admin-section:P-1:active");
  assert.equal(calls.adminSectionViewModelCalls.length, 1);
  assert.equal(calls.adminSectionMarkupCalls.length, 1);
  assert.equal(calls.adminSectionMarkupCalls[0].payload.projectId, "P-1");
  assert.equal(calls.adminSectionMarkupCalls[0].payload.claimStatus, "active");
  assert.equal(calls.adminSectionMarkupCalls[0].payload.showAssignedAt, true);
  assert.equal(typeof calls.adminSectionMarkupCalls[0].helpers.escapeHtml, "function");
});
