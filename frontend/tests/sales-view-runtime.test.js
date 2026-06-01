const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const vm = require("node:vm");

function loadRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSSalesViewRuntime;
}

function loadWiringRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {}, console };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSAppControllerWiringRuntime;
}

test("buildSalesSummaryPanelMarkup renders summary sections for admin mode", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const html = runtime.buildSalesSummaryPanelMarkup(
    {
      uiMode: "admin",
      salesSummaryLoading: false,
      salesClosedLoading: false,
      salesSummaryError: "",
      salesClosedError: "",
      salesSummaryByUser: [],
      salesClosedClaims: [],
      activeMarkup: "",
      closedMarkup: "",
    },
    { escapeHtml: (value) => String(value) },
  );
  assert.match(html, /진행 중 영업/);
  assert.match(html, /종료\/완료 정리/);
});

test("buildClosedSalesArchiveSectionMarkup groups claims by year and month", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const html = runtime.buildClosedSalesArchiveSectionMarkup(
    {
      title: "계약 완료",
      currentYear: 2025,
      claims: [
        {
          project_name: "Alpha",
          claim_status: "won",
          owner_display_name: "Kim",
          closed_at: "2025-01-10T00:00:00Z",
          sales_note: "contract:100",
        },
        {
          project_name: "Beta",
          claim_status: "won",
          owner_email: "beta@example.com",
          closed_at: "2025-02-11T00:00:00Z",
          sales_note: "contract:200",
        },
        {
          project_name: "Gamma",
          claim_status: "won",
          owner_display_name: "Lee",
          closed_at: "2024-03-12T00:00:00Z",
          sales_note: "contract:300",
        },
        {
          project_name: "Future",
          claim_status: "won",
          owner_display_name: "Park",
          closed_at: "2026-04-12T00:00:00Z",
          sales_note: "contract:400",
        },
      ],
      showContractAmount: true,
    },
    {
      escapeHtml: (value) => String(value),
      getSalesYearMonthBucket: (value) => {
        const date = new Date(value);
        return {
          year: date.getUTCFullYear(),
          month: date.getUTCMonth() + 1,
        };
      },
      formatSalesDateLabel: (value) => new Date(value).toISOString().slice(0, 10),
      getLatestSalesNoteItem: () => null,
      formatSalesNoteTextForDisplay: (value) => String(value),
      truncate: (value) => String(value),
      salesClaimStatusLabel: (value) => value,
      extractContractAmountTextFromSalesNote: (value) => value.replace("contract:", ""),
      formatContractAmountDisplay: (value) => `$${value}`,
      formatSalesClaimEstimateLabel: (claim) => `estimate:${claim.project_name}`,
    },
  );

  assert.match(html, /2024년/);
  assert.match(html, /2025년/);
  assert.ok(html.includes("3건"));
  assert.ok(html.includes("1월"));
  assert.ok(html.includes("2월"));
  assert.ok(html.includes("3월"));
  assert.match(html, /Alpha/);
  assert.match(html, /Beta/);
  assert.match(html, /Gamma/);
  assert.doesNotMatch(html, /Future/);
  assert.match(html, /계약금액 \$100/);
  assert.match(html, /계약금액 \$200/);
  assert.match(html, /계약금액 \$300/);
});

test("buildClosedSalesArchiveSectionMarkup renders empty state when no claims exist", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const html = runtime.buildClosedSalesArchiveSectionMarkup(
    {
      title: "영업 종료",
      currentYear: 2025,
      claims: [],
      showContractAmount: false,
    },
    {
      escapeHtml: (value) => String(value),
      getSalesYearMonthBucket: () => null,
      formatSalesDateLabel: (value) => String(value),
      getLatestSalesNoteItem: () => null,
      formatSalesNoteTextForDisplay: (value) => String(value),
      truncate: (value) => String(value),
      salesClaimStatusLabel: (value) => value,
      extractContractAmountTextFromSalesNote: (value) => value,
      formatContractAmountDisplay: (value) => value,
      formatSalesClaimEstimateLabel: () => "estimate",
    },
  );

  assert.match(html, /영업 종료된 영업 프로젝트가 없습니다\./);
});

test("normalizeSalesClaimCardViewModel fills shared defaults for owned and company cards", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");

  const owned = runtime.normalizeSalesClaimCardViewModel({
    claim: {
      project_id: "  P-1  ",
      claimed_at: "2024-01-02T00:00:00Z",
      current_owner_assigned_at: "2024-01-03T00:00:00Z",
    },
    noteEntries: null,
  });

  assert.equal(owned.projectId, "P-1");
  assert.equal(owned.noteEntries.length, 0);
  assert.equal(owned.showAssignedAt, true);

  const company = runtime.normalizeSalesClaimCardViewModel(
    {
      claim: {
        project_id: "P-2",
        owner_display_name: "",
        owner_email: "company@example.com",
        claimed_at: "2024-01-04T00:00:00Z",
        current_owner_assigned_at: "2024-01-05T00:00:00Z",
      },
      noteEntries: [
        { timestamp: "2024-01-04T00:00:00Z", text: "first" },
        { timestamp: "2024-01-05T00:00:00Z", text: "second" },
      ],
    },
    { includeOwnerLabel: true },
  );

  assert.equal(company.projectId, "P-2");
  assert.equal(company.ownerLabel, "company@example.com");
  assert.equal(company.latestNote.timestamp, "2024-01-05T00:00:00Z");
  assert.equal(company.latestNote.text, "second");
  assert.equal(company.showAssignedAt, true);
});

test("normalizeSalesClaimCardViewModel preserves explicit falsey company overrides", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const payload = runtime.normalizeSalesClaimCardViewModel(
    {
      claim: {
        project_id: "P-3",
        owner_display_name: "Fallback Owner",
        owner_email: "fallback@example.com",
      },
      noteEntries: [{ timestamp: "2024-01-01T00:00:00Z", text: "first" }],
      latestNote: null,
      ownerLabel: "",
    },
    { includeOwnerLabel: true },
  );

  assert.equal(payload.latestNote, null);
  assert.equal(payload.ownerLabel, "");
});

test("renderUserOwnedSalesClaimCard, renderCompanySalesClaimCard, and renderUserTrackerClaimSection delegate to the sales panel controller", () => {
  const source = fs.readFileSync("frontend/app.js", "utf8");
  const userStart = source.indexOf("function renderUserOwnedSalesClaimCard(claim, index) {");
  const companyStart = source.indexOf("function renderCompanySalesClaimCard(claim, index) {");
  const trackerStart = source.indexOf("function renderUserTrackerClaimSection(entry, {", companyStart);
  const trackerEnd = source.indexOf("\nfunction bindUserSalesSectionEvents()", trackerStart);
  assert.ok(userStart >= 0, "renderUserOwnedSalesClaimCard source not found");
  assert.ok(companyStart > userStart, "renderCompanySalesClaimCard source not found");
  assert.ok(trackerStart > companyStart, "renderUserTrackerClaimSection source not found");
  assert.ok(trackerEnd > trackerStart, "renderUserTrackerClaimSection terminator not found");

  const userSource = source.slice(userStart, companyStart);
  const companySource = source.slice(companyStart, trackerStart);
  const trackerSource = source.slice(trackerStart, trackerEnd);
  assert.match(userSource, /return getSalesPanelController\(\)\.renderUserOwnedSalesClaimCard\(claim, index\);/);
  assert.match(companySource, /return getSalesPanelController\(\)\.renderCompanySalesClaimCard\(claim, index\);/);
  assert.match(trackerSource, /return getSalesPanelController\(\)\.renderUserTrackerClaimSection\(entry, \{/);
  assert.match(trackerSource, /projectId,/);
  assert.match(trackerSource, /claim,/);
  assert.match(trackerSource, /saving,/);
  assert.doesNotMatch(userSource, /projectId = String/);
  assert.doesNotMatch(userSource, /buildUserOwnedSalesClaimCardMarkup/);
  assert.doesNotMatch(companySource, /getSalesNoteTimeline/);
  assert.doesNotMatch(companySource, /buildCompanySalesClaimCardMarkup/);
  assert.doesNotMatch(trackerSource, /buildUserTrackerClaimSectionMarkup/);
});

test("buildUserOwnedSalesClaimCardMarkup and buildCompanySalesClaimCardMarkup preserve fallback rendering when optional view model fields are missing", () => {
  const runtime = loadRuntime("frontend/sales-view-runtime.js");
  const ownedHtml = runtime.buildUserOwnedSalesClaimCardMarkup(
    {
      claim: {
        project_id: "P-1",
        project_name: "Owned Project",
        claimed_at: "2024-01-02",
        current_owner_assigned_at: "2024-01-03",
      },
      noteDraft: "",
      noteEntries: null,
      snapshot: null,
      transferTargets: [],
      organizationUsersLoading: false,
    },
    {
      escapeHtml: (value) => String(value),
      salesClaimStatusLabel: (value) => String(value || ""),
      renderUserSalesProjectFacts: () => "",
      formatSalesDateLabel: (value) => String(value || ""),
      renderSalesNoteTimelineMarkup: () => "",
    },
  );

  const companyHtml = runtime.buildCompanySalesClaimCardMarkup(
    {
      claim: {
        project_id: "P-2",
        project_name: "Company Project",
        owner_email: "company@example.com",
        claimed_at: "2024-02-02",
        current_owner_assigned_at: "2024-02-03",
        claim_status: "active",
      },
      noteEntries: null,
      snapshot: null,
    },
    {
      escapeHtml: (value) => String(value),
      salesClaimStatusLabel: (value) => String(value || ""),
      renderUserSalesProjectFacts: () => "",
      formatSalesDateLabel: (value) => String(value || ""),
      truncate: (value) => String(value || ""),
      formatSalesNoteTextForDisplay: (value) => String(value || ""),
    },
  );

  assert.match(ownedHtml, /data-user-sales-note="P-1"/);
  assert.match(ownedHtml, /Owned Project/);
  assert.match(companyHtml, /Company Project/);
  assert.match(companyHtml, /company@example.com/);
});

test("app sales claim wrappers call into the sales panel controller without rebuilding payloads", () => {
  const source = fs.readFileSync("frontend/app.js", "utf8");
  const helperStart = source.indexOf("function normalizeSalesClaimCardViewModel(payload = {}, options = {}) {");
  const userStart = source.indexOf("function renderUserOwnedSalesClaimCard(claim, index) {");
  const companyStart = source.indexOf("function renderCompanySalesClaimCard(claim, index) {");
  const trackerStart = source.indexOf("function renderUserTrackerClaimSection(entry, {", companyStart);
  const trackerEnd = source.indexOf("\nfunction bindUserSalesSectionEvents()", trackerStart);
  assert.ok(helperStart >= 0, "normalizeSalesClaimCardViewModel source not found");
  assert.ok(userStart > helperStart, "renderUserOwnedSalesClaimCard source not found");
  assert.ok(companyStart > userStart, "renderCompanySalesClaimCard source not found");
  assert.ok(trackerStart > companyStart, "renderUserTrackerClaimSection source not found");
  assert.ok(trackerEnd > trackerStart, "renderUserTrackerClaimSection terminator not found");

  const snippet = source.slice(helperStart, trackerEnd);
  const calls = [];
  const context = {
    state: {
      salesClaimSavingProjectIds: {},
      organizationUsersLoading: false,
    },
    getSalesPanelController: () => ({
      renderUserOwnedSalesClaimCard(claim, index) {
        calls.push(["owned", claim, index]);
        return "__OWNED__";
      },
      renderCompanySalesClaimCard(claim, index) {
        calls.push(["company", claim, index]);
        return "__COMPANY__";
      },
      renderUserTrackerClaimSection(entry, options) {
        calls.push(["tracker", entry, options]);
        return "__TRACKER__";
      },
    }),
    window: {
      SPMSAppControllerWiringRuntime: {
        normalizeSalesClaimCardViewModel(payload, options) {
          return { ...payload, options };
        },
      },
    },
    SALES_VIEW_RUNTIME: {
      shouldShowCurrentOwnerAssignedAt: () => true,
    },
  };
  vm.createContext(context);
  const result = vm.runInContext(
    `${snippet}\nrenderUserOwnedSalesClaimCard({ project_id: "P-1", project_name: "Owned Project", claimed_at: "2024-01-02", current_owner_assigned_at: "2024-01-03", sales_note: "Owned note" }, 0);\nrenderCompanySalesClaimCard({ project_id: "P-2", project_name: "Company Project", owner_display_name: "Company Owner", owner_email: "company@example.com", claimed_at: "2024-01-04", current_owner_assigned_at: "2024-01-05", sales_note: "Company note" }, 1);\nrenderUserTrackerClaimSection({ id: "entry-1" }, { projectId: "P-3", claim: { project_id: "P-3" }, saving: true });`,
    context,
  );

  assert.equal(result, "__TRACKER__");
  assert.deepEqual(JSON.parse(JSON.stringify(calls)), [
    ["owned", {
      project_id: "P-1",
      project_name: "Owned Project",
      claimed_at: "2024-01-02",
      current_owner_assigned_at: "2024-01-03",
      sales_note: "Owned note",
    }, 0],
    ["company", {
      project_id: "P-2",
      project_name: "Company Project",
      owner_display_name: "Company Owner",
      owner_email: "company@example.com",
      claimed_at: "2024-01-04",
      current_owner_assigned_at: "2024-01-05",
      sales_note: "Company note",
    }, 1],
    ["tracker", { id: "entry-1" }, {
      projectId: "P-3",
      claim: { project_id: "P-3" },
      saving: true,
    }],
  ]);
});

test("normalizeSalesClaimCardViewModel fallback honors shouldShowCurrentOwnerAssignedAt from a partial runtime", () => {
  const source = fs.readFileSync("frontend/app.js", "utf8");
  const helperStart = source.indexOf("function normalizeSalesClaimCardViewModel(payload = {}, options = {}) {");
  assert.ok(helperStart >= 0, "normalizeSalesClaimCardViewModel source not found");

  const helperEnd = source.indexOf("\nfunction renderUserOwnedSalesClaimCard", helperStart);
  assert.ok(helperEnd > helperStart, "normalizeSalesClaimCardViewModel terminator not found");

  const snippet = source.slice(helperStart, helperEnd);
  const context = {
    window: {
      SPMSAppControllerWiringRuntime: {},
      APP_CONTROLLER_DEPS: {
        normalizeSalesClaimCardViewModel(payload, options) {
          const shouldShowCurrentOwnerAssignedAt = options?.shouldShowCurrentOwnerAssignedAt;
          return {
            ...payload,
            noteEntries: Array.isArray(payload.noteEntries) ? payload.noteEntries : [],
            showAssignedAt: Boolean(shouldShowCurrentOwnerAssignedAt?.(payload.claim || {})),
          };
        },
      },
    },
    SALES_VIEW_RUNTIME: {},
  };
  vm.createContext(context);
  const payload = vm.runInContext(
    `${snippet}\nnormalizeSalesClaimCardViewModel({ claim: { project_id: "P-1", claimed_at: "2024-01-02" } }, { shouldShowCurrentOwnerAssignedAt: () => true });`,
    context,
  );

  assert.equal(payload.showAssignedAt, true);
});

test("shared normalizeSalesClaimCardViewModel preserves explicit falsey company overrides", () => {
  const runtime = loadWiringRuntime("frontend/app-controller-wiring-runtime.js");
  const payload = runtime.normalizeSalesClaimCardViewModel(
    {
      claim: {
        project_id: "P-9",
        owner_display_name: "Fallback Owner",
        owner_email: "fallback@example.com",
      },
      noteEntries: [{ timestamp: "2024-01-01T00:00:00Z", text: "first" }],
      latestNote: null,
      ownerLabel: "",
    },
    { includeOwnerLabel: true, shouldShowCurrentOwnerAssignedAt: () => true },
  );

  assert.equal(payload.latestNote, null);
  assert.equal(payload.ownerLabel, "");
  assert.equal(payload.showAssignedAt, true);
});

test("renderClosedSalesArchiveSection delegates through the app sales bridge at runtime", async () => {
  const bridgeUrl = pathToFileURL(path.resolve("frontend/app-sales-bridge.js")).href;
  const { createAppSalesBridge } = await import(bridgeUrl);
  const calls = [];
  const bridge = createAppSalesBridge({
    callSalesPanelController: (...args) => {
      calls.push(args);
      return "__BRIDGE__";
    },
  });

  const result = bridge.renderClosedSalesArchiveSection("계약 완료", [{ project_name: "A" }], { showContractAmount: true });
  assert.equal(result, "__BRIDGE__");
  assert.deepEqual(calls, [
    ["renderClosedSalesArchiveSection", "계약 완료", [{ project_name: "A" }], { showContractAmount: true }],
  ]);
});
