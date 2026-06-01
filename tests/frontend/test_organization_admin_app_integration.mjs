import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const salesRuntimePath = path.resolve(__dirname, "../../frontend/app-runtime-body-admin-sales-runtime.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function readSalesRuntimeSource() {
  return fs.readFileSync(salesRuntimePath, "utf8");
}

function normalizeWhitespace(source) {
  return String(source || "").replace(/\s+/g, " ").trim();
}

function extractFunction(source, startSignature, nextSignature) {
  const start = source.indexOf(startSignature);
  assert.notEqual(start, -1, `missing ${startSignature}`);
  const end = nextSignature ? source.indexOf(nextSignature, start + startSignature.length) : -1;
  assert.notEqual(end, -1, `missing ${nextSignature}`);
  return source.slice(start, end);
}

function extractFunctionBlock(source, startSignature) {
  const start = source.indexOf(startSignature);
  assert.notEqual(start, -1, `missing ${startSignature}`);
  const closeParen = source.indexOf(")", start);
  assert.notEqual(closeParen, -1, `missing closing paren for ${startSignature}`);
  const openBrace = source.indexOf("{", closeParen);
  assert.notEqual(openBrace, -1, `missing opening brace for ${startSignature}`);
  let depth = 0;
  let end = openBrace;
  for (; end < source.length; end += 1) {
    const char = source[end];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        end += 1;
        break;
      }
    }
  }
  assert.ok(depth === 0, `unterminated function block for ${startSignature}`);
  return source.slice(start, end);
}

function extractRenderOrganizationAdminPanelSource() {
  const source = readAppSource();
  const start = source.indexOf("const { renderOrganizationAdminPanel: renderOrganizationAdminPanelDelegate } = createMethodDelegates(");
  const end = source.indexOf("const { syncProfileDialogWithSession:", start);
  assert.ok(start >= 0, "renderOrganizationAdminPanel delegate should exist");
  assert.ok(end > start, "renderOrganizationAdminPanel delegate should be bounded by the next delegate block");
  return source.slice(start, end).trim();
}

function loadRenderOrganizationAdminPanel(overrides = {}) {
  const blockSource = extractRenderOrganizationAdminPanelSource();
  const contextData = {
    console,
    getOrgAdminController: () => null,
    createMethodDelegates({ getter, methods = [], strict = false } = {}) {
      const delegates = {};
      for (const methodName of methods) {
        delegates[methodName] = (...args) => {
          const target = typeof getter === "function" ? getter() : null;
          const method = target?.[methodName];
          if (typeof method !== "function") {
            if (strict) {
              throw new Error(`Missing delegated method: ${methodName}`);
            }
            return undefined;
          }
          return method.apply(target, args);
        };
      }
      return delegates;
    },
  };
  Object.assign(contextData, overrides);
  const context = vm.createContext(contextData);
  const renderOrganizationAdminPanel = vm.runInContext(
    `(function () { ${blockSource}; return renderOrganizationAdminPanel; })()`,
    context,
    { filename: appPath },
  );
  return { renderOrganizationAdminPanel, context };
}

function extractOrgAdminDelegationSources() {
  const appSource = readAppSource();
  const salesSource = readSalesRuntimeSource();
  return {
    createControllerWithWiringDepsSource: extractFunctionBlock(appSource, "function createControllerWithWiringDeps({"),
    getAppBootstrapBridgeSource: extractFunctionBlock(appSource, "function getAppBootstrapBridge() {"),
    getterSource: extractFunctionBlock(appSource, "function getOrgAdminController() {"),
    loadAdminConsoleDataSource: extractFunctionBlock(appSource, "async function loadAdminConsoleData({ silent = false, force = false } = {}) {"),
    createAppRuntimeBodyAdminSalesDelegatesSource: extractFunctionBlock(salesSource, "function createAppRuntimeBodyAdminSalesDelegates({"),
    loadOrganizationAdminDataSource: extractFunction(
      salesSource,
      "function loadOrganizationAdminData({ silent = false, force = false } = {}) {",
      "async function handleInvitationSubmit(event) {",
    ),
    handleInvitationSubmitSource: extractFunction(
      salesSource,
      "async function handleInvitationSubmit(event) {",
      "async function handlePlatformAdminAccountSubmit(event) {",
    ),
    handlePlatformAdminAccountSubmitSource: extractFunction(
      salesSource,
      "async function handlePlatformAdminAccountSubmit(event) {",
      "async function copyInvitationUrl(inviteUrl, options = {}) {",
    ),
    copyInvitationUrlSource: extractFunction(
      salesSource,
      "async function copyInvitationUrl(inviteUrl, options = {}) {",
      "async function revokeOrganizationInvitation(invitationId) {",
    ),
    revokeOrganizationInvitationSource: extractFunction(
      salesSource,
      "async function revokeOrganizationInvitation(invitationId) {",
      "async function saveOrganizationMember(userId, article) {",
    ),
    saveOrganizationMemberSource: extractFunction(
      salesSource,
      "async function saveOrganizationMember(userId, article) {",
      "async function deleteOrganizationMember(userId, article) {",
    ),
    deleteOrganizationMemberSource: extractFunction(
      salesSource,
      "async function deleteOrganizationMember(userId, article) {",
      "async function resetOrganizationMemberPassword(userId, article) {",
    ),
    resetOrganizationMemberPasswordSource: extractFunction(
      salesSource,
      "async function resetOrganizationMemberPassword(userId, article) {",
      "async function performResetOrganizationMemberPassword(userId, article) {",
    ),
  };
}

function loadOrgAdminDelegationHarness() {
  const sources = extractOrgAdminDelegationSources();
  const calls = [];
  const bridgeCalls = [];
  const bridgeFactoryCalls = [];
  const bridge = {
    loadAdminConsoleData(options) {
      bridgeCalls.push(["loadAdminConsoleData", options]);
      return "load-admin-console-data";
    },
  };
  const controller = {
    loadOrganizationAdminData(options) {
      calls.push(["loadOrganizationAdminData", options]);
      return "load-organization-admin-data";
    },
    async handleInvitationSubmit(event) {
      calls.push(["handleInvitationSubmit", event]);
      return "handle-invitation-submit";
    },
    async handlePlatformAdminAccountSubmit(event) {
      calls.push(["handlePlatformAdminAccountSubmit", event]);
      return "handle-platform-admin-account-submit";
    },
    async copyInvitationUrl(inviteUrl, options) {
      calls.push(["copyInvitationUrl", inviteUrl, options]);
      return "copy-invitation-url";
    },
    async revokeOrganizationInvitation(invitationId) {
      calls.push(["revokeOrganizationInvitation", invitationId]);
      return "revoke-organization-invitation";
    },
    async saveOrganizationMember(userId, article) {
      calls.push(["saveOrganizationMember", userId, article]);
      return "save-organization-member";
    },
    async deleteOrganizationMember(userId, article) {
      calls.push(["deleteOrganizationMember", userId, article]);
      return "delete-organization-member";
    },
    async resetOrganizationMemberPassword(userId, article) {
      calls.push(["resetOrganizationMemberPassword", userId, article]);
      return "reset-organization-member-password";
    },
  };

  const context = vm.createContext({
    console,
    state: {},
    window: {
      APP_BOOTSTRAP_BRIDGE: {
        createAppBootstrapBridge(deps) {
          bridgeFactoryCalls.push(deps);
          return bridge;
        },
      },
    },
    BOOTSTRAP_RUNTIME: {},
    clampPage: (value, fallback) => fallback,
    normalizeTrackerRegionFilter: (value) => String(value || "").trim(),
    appBootstrapBridge: null,
    getOrgAdminController: () => controller,
  });

  vm.runInContext(
    [
      sources.getAppBootstrapBridgeSource,
      sources.loadAdminConsoleDataSource,
      sources.createAppRuntimeBodyAdminSalesDelegatesSource,
    ].join("\n"),
    context,
    { filename: appPath },
  );

  const delegates = vm.runInContext(
    `createAppRuntimeBodyAdminSalesDelegates({
      state: {},
      dom: {},
      APP_SUPPORT: {},
      TRACKER_DIAGNOSTICS_RUNTIME: null,
      TRACKER_MISSING_REPORT_RUNTIME: null,
      escapeHtml: (value) => String(value ?? ""),
      formatDate: (value) => String(value ?? ""),
      requireConsoleDataRuntime: () => ({ runtime: true }),
      getConsoleDataRuntimeDeps: () => ({ runtimeDeps: true }),
      getTrackerDiagnosticsPanelController: () => ({
        renderTrackerContactResolutionSummary() {},
        renderTrackerCleanupPreview() {},
      }),
      getOrgAdminController,
      windowObject: {},
      SALES_VIEW_RUNTIME: null,
      buildSalesClaimEstimateLabel: () => "",
      formatShortDateTimeHelper: (value) => value,
      formatEstimatedAmountRangeFromKrwHelper: (low, high, fallback) => fallback,
    })`,
    context,
    { filename: salesRuntimePath },
  );

  Object.assign(context, delegates);
  return { context, calls, sources, bridgeCalls, bridgeFactoryCalls };
}

test("renderOrganizationAdminPanel is a thin wrapper around the org-admin controller delegate", () => {
  const functionSource = extractRenderOrganizationAdminPanelSource();

  assert.match(functionSource, /createMethodDelegates/);
  assert.match(functionSource, /getOrgAdminController/);
  assert.match(functionSource, /renderOrganizationAdminPanelDelegate/);
  assert.doesNotMatch(functionSource, /buildOrganizationAdminMarkup/);
  assert.doesNotMatch(functionSource, /bindOrganizationAdminActions/);
  assert.doesNotMatch(functionSource, /organizationPlanSummary\.innerHTML/);
  assert.doesNotMatch(functionSource, /platformAdminAccountPanelSlot/);
});

test("renderOrganizationAdminPanel delegates when the org-admin controller is available", () => {
  let callCount = 0;
  const { renderOrganizationAdminPanel } = loadRenderOrganizationAdminPanel({
    getOrgAdminController: () => ({
      renderOrganizationAdminPanel() {
        callCount += 1;
        return "controller-result";
      },
    }),
  });

  assert.equal(renderOrganizationAdminPanel(), "controller-result");
  assert.equal(callCount, 1);
});

test("renderOrganizationAdminPanel remains a safe no-op when the controller is absent", () => {
  const { renderOrganizationAdminPanel } = loadRenderOrganizationAdminPanel();
  assert.doesNotThrow(() => renderOrganizationAdminPanel());
});

test("getOrgAdminController returns null when the org-admin controller factory is missing", () => {
  const { getterSource, createControllerWithWiringDepsSource } = extractOrgAdminDelegationSources();
  const context = vm.createContext({
    console,
    window: {
      ORG_ADMIN_CONTROLLER: {},
    },
    orgAdminController: null,
  });

  vm.runInContext(createControllerWithWiringDepsSource, context, { filename: appPath });
  vm.runInContext(getterSource, context, { filename: appPath });
  assert.equal(context.getOrgAdminController(), null);
});

test("org-admin action wrappers stay thin and delegate through the org-admin controller", async () => {
  const { context, calls, sources, bridgeCalls, bridgeFactoryCalls } = loadOrgAdminDelegationHarness();

  assert.equal(
    normalizeWhitespace(sources.loadAdminConsoleDataSource),
    normalizeWhitespace("async function loadAdminConsoleData({ silent = false, force = false } = {}) { return getAppBootstrapBridge().loadAdminConsoleData({ silent, force }); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.getAppBootstrapBridgeSource),
    normalizeWhitespace("function getAppBootstrapBridge() { if (typeof getAppBootstrapBridgeAccessor === \"function\") return getAppBootstrapBridgeAccessor() ?? null; if (appBootstrapBridge) return appBootstrapBridge; const createAppBootstrapBridge = window.APP_BOOTSTRAP_BRIDGE?.createAppBootstrapBridge; if (typeof createAppBootstrapBridge !== \"function\") return null; appBootstrapBridge = createAppBootstrapBridge({ bootstrapRuntime: BOOTSTRAP_RUNTIME, state, window, clampPage, normalizeTrackerRegionFilter }); return appBootstrapBridge; }"),
  );
  assert.equal(
    normalizeWhitespace(sources.loadOrganizationAdminDataSource),
    normalizeWhitespace("function loadOrganizationAdminData({ silent = false, force = false } = {}) { return getOrgAdminController()?.loadOrganizationAdminData({ silent, force }); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.handleInvitationSubmitSource),
    normalizeWhitespace("async function handleInvitationSubmit(event) { return getOrgAdminController()?.handleInvitationSubmit(event); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.handlePlatformAdminAccountSubmitSource),
    normalizeWhitespace("async function handlePlatformAdminAccountSubmit(event) { return getOrgAdminController()?.handlePlatformAdminAccountSubmit(event); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.copyInvitationUrlSource),
    normalizeWhitespace("async function copyInvitationUrl(inviteUrl, options = {}) { return getOrgAdminController()?.copyInvitationUrl(inviteUrl, options); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.revokeOrganizationInvitationSource),
    normalizeWhitespace("async function revokeOrganizationInvitation(invitationId) { return getOrgAdminController()?.revokeOrganizationInvitation(invitationId); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.saveOrganizationMemberSource),
    normalizeWhitespace("async function saveOrganizationMember(userId, article) { return getOrgAdminController()?.saveOrganizationMember(userId, article); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.deleteOrganizationMemberSource),
    normalizeWhitespace("async function deleteOrganizationMember(userId, article) { return getOrgAdminController()?.deleteOrganizationMember(userId, article); }"),
  );
  assert.equal(
    normalizeWhitespace(sources.resetOrganizationMemberPasswordSource),
    normalizeWhitespace("async function resetOrganizationMemberPassword(userId, article) { return getOrgAdminController()?.resetOrganizationMemberPassword(userId, article); }"),
  );

  assert.doesNotMatch(sources.loadOrganizationAdminDataSource, /requireConsoleDataRuntime|getConsoleDataRuntimeDeps/);
  assert.doesNotMatch(sources.handleInvitationSubmitSource, /\/api\/auth\/invitations|navigator\.clipboard|copyInvitationUrl/);
  assert.doesNotMatch(sources.handlePlatformAdminAccountSubmitSource, /\/api\/admin\/accounts|normalizePlatformAdminAccountDraft|loadOrganizationAuditLogs/);
  assert.doesNotMatch(sources.copyInvitationUrlSource, /navigator\.clipboard|window\.prompt|renderInvitationStatus/);
  assert.doesNotMatch(sources.revokeOrganizationInvitationSource, /\/api\/auth\/invitations|scheduleOrganizationInvitationSync/);
  assert.doesNotMatch(sources.saveOrganizationMemberSource, /data-member-field|loadOrganizationMembers/);
  assert.doesNotMatch(sources.deleteOrganizationMemberSource, /window\.confirm|loadSalesClaimSummaryByUser/);
  assert.doesNotMatch(sources.resetOrganizationMemberPasswordSource, /window\.prompt|password-reset/);

  assert.equal(await context.loadAdminConsoleData({ silent: true, force: true }), "load-admin-console-data");
  assert.equal(context.loadOrganizationAdminData({ silent: true, force: true }), "load-organization-admin-data");
  assert.equal(await context.handleInvitationSubmit({ type: "submit" }), "handle-invitation-submit");
  assert.equal(await context.handlePlatformAdminAccountSubmit({ type: "submit" }), "handle-platform-admin-account-submit");
  assert.equal(await context.copyInvitationUrl("  https://example.test/invite  ", { renderStatusText: true }), "copy-invitation-url");
  assert.equal(await context.revokeOrganizationInvitation("invite-123"), "revoke-organization-invitation");
  assert.equal(await context.saveOrganizationMember("user-1", {}), "save-organization-member");
  assert.equal(await context.deleteOrganizationMember("user-1", {}), "delete-organization-member");
  assert.equal(await context.resetOrganizationMemberPassword("user-1", {}), "reset-organization-member-password");

  assert.equal(bridgeFactoryCalls.length, 1);
  assert.equal(bridgeCalls.length, 1);
  assert.equal(bridgeCalls[0][0], "loadAdminConsoleData");
  assert.deepEqual(JSON.parse(JSON.stringify(bridgeCalls[0][1])), { silent: true, force: true });
  assert.deepEqual(calls.map((entry) => entry[0]), [
    "loadOrganizationAdminData",
    "handleInvitationSubmit",
    "handlePlatformAdminAccountSubmit",
    "copyInvitationUrl",
    "revokeOrganizationInvitation",
    "saveOrganizationMember",
    "deleteOrganizationMember",
    "resetOrganizationMemberPassword",
  ]);
});

test("getOrgAdminController fails fast when the org admin wiring runtime is missing", () => {
  const { getterSource, createControllerWithWiringDepsSource } = extractOrgAdminDelegationSources();
  const context = vm.createContext({
    console,
    window: {
      ORG_ADMIN_CONTROLLER: {
        createOrgAdminController() {
          return {};
        },
      },
    },
    orgAdminController: null,
    state: {},
    dom: {},
    document: {},
    navigator: {},
    api: async () => {},
    flash() {},
    setBusy() {},
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: (value) => String(value ?? ""),
    renderInvitationStatus: () => {},
    renderOrganizationAdminPanel: () => {},
    canUseAdminMode: () => true,
    formatDate: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatAccountStatusLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    resolveStatusClass: (value) => String(value ?? ""),
    MEMBERSHIP_STATUS_OPTIONS: ["active"],
    formatDownloadScopeLabel: (value) => String(value ?? ""),
    formatDownloadFormatLabel: (value) => String(value ?? ""),
    formatDownloadSourcePageLabel: (value) => String(value ?? ""),
    PLATFORM_ADMIN_ACCOUNT_RUNTIME: null,
    syncPlatformAdminAccountDraftFromForm: () => {},
    handlePlatformAdminAccountSubmit: () => {},
    renderOrgAdminRuntimeReloadFallback: () => {},
    canManagePlatformAdminAccounts: () => true,
    resetOrganizationMemberPassword: () => Promise.resolve(),
    requireConsoleDataRuntime: () => ({ runtime: true }),
    getConsoleDataRuntimeDeps: () => ({ runtimeDeps: true }),
    getOrgAdminRuntime: () => ({ orgAdminRuntime: true }),
    loadSalesClaimSummaryByUser: async () => {},
    loadClosedSalesClaims: async () => {},
  });

  vm.runInContext(createControllerWithWiringDepsSource, context, { filename: appPath });
  vm.runInContext(getterSource, context, { filename: appPath });
  assert.throws(
    () => context.getOrgAdminController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});
