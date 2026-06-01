import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const controllerPath = path.resolve(__dirname, "../../frontend/auth-ui-controller.js");
const authControllerPath = path.resolve(__dirname, "../../frontend/auth-controller.js");

function readControllerSource() {
  return fs.readFileSync(controllerPath, "utf8");
}

function loadCreateAuthUiController() {
  const source = readControllerSource()
    .replace("export function createAuthUiController", "function createAuthUiController");
  const context = vm.createContext({ console, window: {}, globalThis: {} });
  return vm.runInContext(
    `(function () { ${source}; return createAuthUiController; })()`,
    context,
    { filename: controllerPath },
  );
}

function loadCreateAuthController() {
  const source = fs.readFileSync(authControllerPath, "utf8")
    .replace("export function createAuthController", "function createAuthController");
  const context = vm.createContext({ console, window: {}, globalThis: {} });
  return vm.runInContext(
    `(function () { ${source}; return createAuthController; })()`,
    context,
    { filename: authControllerPath },
  );
}

function createClassList() {
  const tokens = new Set();
  return {
    add: (...names) => {
      for (const name of names) {
        tokens.add(name);
      }
    },
    remove: (...names) => {
      for (const name of names) {
        tokens.delete(name);
      }
    },
    toggle: (name, force) => {
      if (force === undefined) {
        if (tokens.has(name)) {
          tokens.delete(name);
          return false;
        }
        tokens.add(name);
        return true;
      }
      if (force) {
        tokens.add(name);
      } else {
        tokens.delete(name);
      }
      return force;
    },
    contains: (name) => tokens.has(name),
  };
}

function createElement(overrides = {}) {
  return {
    value: "",
    readOnly: false,
    textContent: "",
    innerHTML: "",
    disabled: false,
    autocomplete: "",
    classList: createClassList(),
    ...overrides,
  };
}

function createTrackedValueElement(initialValue = "") {
  let value = initialValue;
  let writes = 0;
  return {
    get value() {
      return value;
    },
    set value(nextValue) {
      writes += 1;
      value = nextValue;
    },
    get valueWrites() {
      return writes;
    },
    resetValueWrites() {
      writes = 0;
    },
    readOnly: false,
    textContent: "",
    innerHTML: "",
    disabled: false,
    autocomplete: "",
    classList: createClassList(),
  };
}

function loadAuthUi(overrides = {}) {
  const createAuthUiController = loadCreateAuthUiController();
  const contextData = {
    console,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    state: {
      auth: {
        enabled: true,
        checked: true,
        checking: false,
        authenticated: true,
        authorized: true,
        mode: "sign_up",
        inviteToken: "invite-token",
        invitationPreview: {
          email: "invite@example.com",
          display_name: "Invited Name",
          initial_password: "InviteTemp123!",
          organization_name: "Invite Org",
          role: "org_admin",
          status: "pending",
        },
        invitationPreviewError: "",
        user: {
          display_name: "Runtime User",
          email: "runtime@example.com",
          organization_name: "Runtime Org",
          role: "org_admin",
        },
        message: "",
      },
    },
    dom: {
      authShell: createElement(),
      consoleShell: createElement(),
      authMetaCard: createElement(),
      authSessionActions: createElement(),
      authModeSignIn: createElement(),
      authModeSignUp: createElement(),
      authDisplayNameField: createElement(),
      authSubmitButton: createElement(),
      authPassword: createElement({ value: "TypedPassword!" }),
      authCopy: createElement(),
      authHint: createElement(),
      authStatus: createElement(),
      authUserBlocked: createElement(),
      authBlockedMessage: createElement(),
      authUserLabel: createElement(),
      authRoleLabel: createElement(),
      authSessionUserLabel: createElement(),
      authInvitePreview: createElement(),
      authEmail: createElement({ value: "typed@example.com" }),
      authDisplayName: createElement({ value: "" }),
    },
    document: {
      body: createElement(),
    },
    escapeHtml: (value) => `escaped:${String(value || "")}`,
    formatOrgRoleLabel: (value) => `role:${value}`,
    formatInvitationStatusLabel: (value) => `status:${value}`,
    formatSalesDateLabel: (value) => `date:${value}`,
    shouldShowSignUpMode: () => true,
    requireAuthSessionRuntime: null,
  };

  Object.assign(contextData, overrides);
  const controller = createAuthUiController(contextData);
  return { ...controller, context: contextData };
}

function loadAuthController(overrides = {}) {
  const createAuthController = loadCreateAuthController();
  const renderCalls = [];
  const apiCalls = [];
  const contextData = {
    console,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    state: {
      uiMode: "user",
      consoleInitialized: false,
      auth: {
        enabled: true,
        checked: false,
        checking: false,
        authenticated: false,
        authorized: false,
        mode: "sign_up",
        inviteToken: "invite-token",
        invitationPreview: null,
        invitationPreviewLoading: false,
        invitationPreviewError: "",
        user: null,
        message: "",
        bootstrapEmail: "",
      },
    },
    dom: {
      patchActorLabel: createElement(),
      authEmail: createElement({ value: "typed@example.com" }),
      authPassword: createElement({ value: "" }),
      authDisplayName: createElement({ value: "" }),
      authSubmitButton: createElement(),
      authResetPasswordButton: createElement(),
    },
    window: {
      location: {
        hash: "",
        pathname: "/app/",
        search: "",
      },
      history: {
        replaceState: () => {},
      },
      setTimeout,
      clearTimeout,
    },
    document: {
      body: createElement(),
    },
    api: async (endpoint, options) => {
      apiCalls.push([endpoint, options]);
      if (endpoint === "/api/auth/session") {
        return {
          enabled: true,
          checked: true,
          checking: false,
          authenticated: true,
          authorized: false,
          bootstrapEmail: "bootstrap@example.com",
          message: "",
          user: {
            display_name: "Runtime User",
            email: "runtime@example.com",
            organization_name: "Runtime Org",
            role: "org_admin",
          },
        };
      }
      if (endpoint === "/api/auth/invitations/preview?invite_token=invite-token") {
        return {
          email: "invite@example.com",
          display_name: "Invited Name",
          initial_password: "InviteTemp123!",
          organization_name: "Invite Org",
          role: "org_admin",
          status: "pending",
        };
      }
      if (endpoint === "/api/auth/invitations/accept") {
        return {
          enabled: true,
          checked: true,
          checking: false,
          authenticated: true,
          authorized: true,
          bootstrapEmail: "bootstrap@example.com",
          message: "",
          user: {
            display_name: "Accepted User",
            email: "accepted@example.com",
            organization_name: "Accepted Org",
            role: "org_admin",
          },
        };
      }
      throw new Error(`unexpected endpoint: ${endpoint}`);
    },
    flash: (message, level) => {
      renderCalls.push(["flash", message, level]);
    },
    setBusy: () => {},
    escapeHtml: (value) => String(value ?? ""),
    formatOrgRoleLabel: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    requireAuthSessionRuntime: () => ({
      normalizeAuthSession(session) {
        return {
          enabled: true,
          checked: true,
          checking: false,
          authenticated: Boolean(session?.authenticated),
          authorized: Boolean(session?.authorized),
          accessToken: String(session?.access_token || ""),
          bootstrapEmail: String(session?.bootstrapEmail || ""),
          message: String(session?.message || ""),
          user: session?.user || null,
        };
      },
    }),
    loadOrganizationUsers: async () => {},
    loadOrganizationMembers: async () => {},
    loadSalesOverview: async () => {},
    loadMySalesClaims: async () => {},
    refreshSalesAdminPanels: async () => {},
    ensureConsoleInitialized: async () => {},
    shouldShowSignUpMode: () => true,
    renderAuthUi: () => {
      renderCalls.push(["renderAuthUi"]);
    },
    syncUiModeChrome: () => false,
    syncUiModeFromLocation: () => {},
    applyUiModeTransition: () => {
      renderCalls.push(["applyUiModeTransition"]);
    },
    canUseAdminMode: () => false,
    canLoadProtectedConsoleData: () => true,
    loadAdminConsoleData: async () => {},
    loadBackfillConflicts: async () => {},
    renderBackfillConflictsPanel: () => {},
    renderTrackerContactResolutionSummary: () => {},
    renderTrackerCleanupPreview: () => {},
    closeDrawer: () => {},
    hydrateHomeBootstrapCache: () => {},
    clearUserModeRunSelection: () => {},
    loadHomeBootstrap: async () => {},
    loadTrackerEntries: async () => {},
    renderOrganizationAdminPanel: () => {},
    renderMySalesClaimsPanel: () => {},
    renderSalesSummaryPanel: () => {},
    renderRunDetail: () => {},
    renderTrackerEntries: () => {},
    trackerController: {
      loadTrackerChangeEventUnreadCount: async () => {},
      loadTrackerChangeEvents: async () => {},
    },
  };

  Object.assign(contextData, overrides);
  const controller = createAuthController(contextData);
  return { ...controller, context: contextData, apiCalls, renderCalls };
}

test("renderAuthUi composes auth runtime helpers and pre-fills blank password from the invitation preview", () => {
  const runtimeCalls = [];
  const authViewModel = {
    authEnabled: true,
    authorized: true,
    checking: false,
    signUpAllowed: true,
    inviteActionBlocked: false,
    authModeSignInActive: false,
    authModeSignUpActive: true,
    authDisplayNameHidden: false,
    authSubmitText: "Runtime Submit",
    authPasswordAutocomplete: "runtime-password",
    authCopyText: "Runtime copy",
    authHintText: "Runtime hint",
    status: {
      hasMessage: false,
      text: "",
      isError: false,
    },
    showBlocked: false,
    blockedMessage: "",
    userLabel: "Runtime User",
    roleLabel: "role:org_admin | Runtime Org",
    sessionUserLabel: "Runtime User @ Runtime Org",
    authShellHidden: true,
    consoleShellHidden: false,
    authShellActive: false,
  };
  const formFieldViewModel = {
    emailValue: "invite@example.com",
    emailReadOnly: true,
    displayNameValue: "Invited Name",
    passwordValue: "RuntimePassword!",
  };
  const previewViewModel = {
    visible: true,
    html: "<div>runtime invite preview</div>",
  };
  const runtime = {
    buildAuthUiViewModel: (auth, helpers) => {
      runtimeCalls.push({ name: "buildAuthUiViewModel", auth, helpers });
      return authViewModel;
    },
    buildAuthFormFieldViewModel: (options) => {
      runtimeCalls.push({ name: "buildAuthFormFieldViewModel", options });
      return formFieldViewModel;
    },
    buildAuthInvitationPreviewViewModel: (auth, helpers) => {
      runtimeCalls.push({ name: "buildAuthInvitationPreviewViewModel", auth, helpers });
      return previewViewModel;
    },
  };

  const { renderAuthUi, context } = loadAuthUi({
    requireAuthSessionRuntime: () => runtime,
    dom: {
      authShell: createElement(),
      consoleShell: createElement(),
      authMetaCard: createElement(),
      authSessionActions: createElement(),
      authModeSignIn: createElement(),
      authModeSignUp: createElement(),
      authDisplayNameField: createElement(),
      authSubmitButton: createElement(),
      authPassword: createElement({ value: "" }),
      authCopy: createElement(),
      authHint: createElement(),
      authStatus: createElement(),
      authUserBlocked: createElement(),
      authBlockedMessage: createElement(),
      authUserLabel: createElement(),
      authRoleLabel: createElement(),
      authSessionUserLabel: createElement(),
      authInvitePreview: createElement(),
      authEmail: createElement({ value: "typed@example.com" }),
      authDisplayName: createElement({ value: "" }),
    },
  });

  renderAuthUi();

  assert.deepEqual(runtimeCalls.map((entry) => entry.name), [
    "buildAuthUiViewModel",
    "buildAuthFormFieldViewModel",
    "buildAuthInvitationPreviewViewModel",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(runtimeCalls[1].options)), {
    auth: JSON.parse(JSON.stringify(context.state.auth)),
    currentEmail: "typed@example.com",
    currentDisplayName: "",
    currentPassword: "",
  });
  assert.equal(context.dom.authSubmitButton.textContent, "Runtime Submit");
  assert.equal(context.dom.authPassword.autocomplete, "runtime-password");
  assert.equal(context.dom.authModeSignIn.classList.contains("is-active"), false);
  assert.equal(context.dom.authModeSignUp.classList.contains("is-active"), true);
  assert.equal(context.dom.authModeSignUp.classList.contains("hidden"), false);
  assert.equal(context.dom.authDisplayNameField.classList.contains("hidden"), false);
  assert.equal(context.dom.authEmail.value, "invite@example.com");
  assert.equal(context.dom.authEmail.readOnly, true);
  assert.equal(context.dom.authEmail.classList.contains("is-readonly"), true);
  assert.equal(context.dom.authDisplayName.value, "Invited Name");
  assert.equal(context.dom.authPassword.value, "RuntimePassword!");
  assert.equal(context.dom.authInvitePreview.innerHTML, "<div>runtime invite preview</div>");
  assert.equal(context.dom.authInvitePreview.classList.contains("hidden"), false);
  assert.equal(context.dom.authUserLabel.textContent, "Runtime User");
  assert.equal(context.dom.authRoleLabel.textContent, "role:org_admin | Runtime Org");
  assert.equal(context.dom.authSessionUserLabel.textContent, "Runtime User @ Runtime Org");
});

test("renderAuthUi forwards non-empty currentPassword and does not overwrite it", () => {
  const runtimeCalls = [];
  const authViewModel = {
    authEnabled: true,
    authorized: true,
    checking: false,
    signUpAllowed: true,
    inviteActionBlocked: false,
    authModeSignInActive: false,
    authModeSignUpActive: true,
    authDisplayNameHidden: false,
    authSubmitText: "Runtime Submit",
    authPasswordAutocomplete: "runtime-password",
    authCopyText: "Runtime copy",
    authHintText: "Runtime hint",
    status: {
      hasMessage: false,
      text: "",
      isError: false,
    },
    showBlocked: false,
    blockedMessage: "",
    userLabel: "Runtime User",
    roleLabel: "role:org_admin | Runtime Org",
    sessionUserLabel: "Runtime User @ Runtime Org",
    authShellHidden: true,
    consoleShellHidden: false,
    authShellActive: false,
  };
  const runtime = {
    buildAuthUiViewModel: (auth, helpers) => {
      runtimeCalls.push({ name: "buildAuthUiViewModel", auth, helpers });
      return authViewModel;
    },
    buildAuthFormFieldViewModel: (options) => {
      runtimeCalls.push({ name: "buildAuthFormFieldViewModel", options });
      return {
        emailValue: "invite@example.com",
        emailReadOnly: true,
        displayNameValue: "Invited Name",
        passwordValue: "RuntimePassword!",
      };
    },
    buildAuthInvitationPreviewViewModel: (auth, helpers) => {
      runtimeCalls.push({ name: "buildAuthInvitationPreviewViewModel", auth, helpers });
      return {
        visible: true,
        html: "<div>runtime invite preview</div>",
      };
    },
  };

  const { renderAuthUi, context } = loadAuthUi({
    requireAuthSessionRuntime: () => runtime,
    dom: {
      authShell: createElement(),
      consoleShell: createElement(),
      authMetaCard: createElement(),
      authSessionActions: createElement(),
      authModeSignIn: createElement(),
      authModeSignUp: createElement(),
      authDisplayNameField: createElement(),
      authSubmitButton: createElement(),
      authPassword: createElement({ value: "TypedPassword!" }),
      authCopy: createElement(),
      authHint: createElement(),
      authStatus: createElement(),
      authUserBlocked: createElement(),
      authBlockedMessage: createElement(),
      authUserLabel: createElement(),
      authRoleLabel: createElement(),
      authSessionUserLabel: createElement(),
      authInvitePreview: createElement(),
      authEmail: createElement({ value: "typed@example.com" }),
      authDisplayName: createElement({ value: "" }),
    },
  });

  renderAuthUi();

  assert.deepEqual(runtimeCalls.map((entry) => entry.name), [
    "buildAuthUiViewModel",
    "buildAuthFormFieldViewModel",
    "buildAuthInvitationPreviewViewModel",
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(runtimeCalls[1].options)), {
    auth: JSON.parse(JSON.stringify(context.state.auth)),
    currentEmail: "typed@example.com",
    currentDisplayName: "",
    currentPassword: "TypedPassword!",
  });
  assert.equal(context.dom.authPassword.value, "TypedPassword!");
  assert.equal(context.dom.authEmail.value, "invite@example.com");
  assert.equal(context.dom.authEmail.readOnly, true);
  assert.equal(context.dom.authDisplayName.value, "Invited Name");
  assert.equal(context.dom.authInvitePreview.innerHTML, "<div>runtime invite preview</div>");
});

test("renderAuthUi does not rewrite unlocked auth fields on rerender when no invitation applies", () => {
  const authViewModel = {
    authEnabled: true,
    authorized: false,
    checking: false,
    signUpAllowed: true,
    inviteActionBlocked: false,
    authModeSignInActive: false,
    authModeSignUpActive: true,
    authDisplayNameHidden: false,
    authSubmitText: "Runtime Submit",
    authPasswordAutocomplete: "runtime-password",
    authCopyText: "Runtime copy",
    authHintText: "Runtime hint",
    status: {
      hasMessage: false,
      text: "",
      isError: false,
    },
    showBlocked: false,
    blockedMessage: "",
    userLabel: "",
    roleLabel: "",
    sessionUserLabel: "",
    authShellHidden: false,
    consoleShellHidden: true,
    authShellActive: true,
  };
  const runtime = {
    buildAuthUiViewModel: () => authViewModel,
    buildAuthFormFieldViewModel: (options) => ({
      emailValue: options.currentEmail,
      emailReadOnly: false,
      displayNameValue: options.currentDisplayName,
      passwordValue: options.currentPassword,
    }),
    buildAuthInvitationPreviewViewModel: () => ({
      visible: false,
      html: "",
    }),
  };

  const { renderAuthUi, context } = loadAuthUi({
    requireAuthSessionRuntime: () => runtime,
    state: {
      auth: {
        enabled: true,
        checked: true,
        checking: false,
        authenticated: false,
        authorized: false,
        mode: "sign_up",
        inviteToken: "",
        invitationPreview: null,
        invitationPreviewLoading: false,
        invitationPreviewError: "",
        user: null,
        message: "",
      },
    },
    dom: {
      authShell: createElement(),
      consoleShell: createElement(),
      authMetaCard: createElement(),
      authSessionActions: createElement(),
      authModeSignIn: createElement(),
      authModeSignUp: createElement(),
      authDisplayNameField: createElement(),
      authSubmitButton: createElement(),
      authPassword: createTrackedValueElement("typed password"),
      authCopy: createElement(),
      authHint: createElement(),
      authStatus: createElement(),
      authUserBlocked: createElement(),
      authBlockedMessage: createElement(),
      authUserLabel: createElement(),
      authRoleLabel: createElement(),
      authSessionUserLabel: createElement(),
      authInvitePreview: createElement(),
      authEmail: createTrackedValueElement("typed@example.com"),
      authDisplayName: createTrackedValueElement("typed display name"),
    },
    document: {
      body: createElement(),
    },
  });

  renderAuthUi();
  context.dom.authEmail.resetValueWrites();
  context.dom.authDisplayName.resetValueWrites();
  context.dom.authPassword.resetValueWrites();

  renderAuthUi();

  assert.equal(context.dom.authEmail.valueWrites, 0);
  assert.equal(context.dom.authDisplayName.valueWrites, 0);
  assert.equal(context.dom.authPassword.valueWrites, 0);
  assert.equal(context.dom.authEmail.value, "typed@example.com");
  assert.equal(context.dom.authDisplayName.value, "typed display name");
  assert.equal(context.dom.authPassword.value, "typed password");
});

test("handleAuthSignOut closes the profile dialog, resets auth shell state, and reloads the window", async () => {
  const clearIntervalCalls = [];
  let reloadCalls = 0;
  const apiCalls = [];
  const { handleAuthSignOut, context } = loadAuthUi({
    api: async (path, options) => {
      apiCalls.push([path, options]);
      return {};
    },
    window: {
      clearInterval(handle) {
        clearIntervalCalls.push(handle);
      },
      location: {
        reload() {
          reloadCalls += 1;
        },
      },
    },
    state: {
      profileDialog: {
        open: true,
        saving: true,
      },
      auth: {
        authenticated: true,
        authorized: true,
        user: { display_name: "Runtime User" },
        message: "keep me",
      },
      organizationUsers: [{ id: "u-1" }],
      organizationUsersError: "users error",
      organizationMembers: [{ id: "m-1" }],
      organizationMembersError: "members error",
      organizationPlanSummary: { plan: "pro" },
      organizationInvitations: [{ id: "i-1" }],
      organizationInvitationsError: "invitations error",
      organizationAuditLogs: [{ id: "a-1" }],
      organizationAuditLogsLoading: true,
      organizationAuditLogsError: "audit error",
      organizationAuditLogsLimit: 9,
      organizationAuditLogsHasMore: true,
      organizationDownloadAuditLogs: [{ id: "d-1" }],
      organizationDownloadAuditLogsLoading: true,
      organizationDownloadAuditLogsError: "download error",
      organizationDownloadAuditLogsLimit: 9,
      organizationDownloadAuditLogsHasMore: true,
      organizationLoginAuditLogs: [{ id: "l-1" }],
      organizationLoginAuditLogsLoading: true,
      organizationLoginAuditLogsError: "login error",
      organizationLoginAuditLogsLimit: 9,
      organizationLoginAuditLogsHasMore: true,
      platformAdminAccount: {
        saving: true,
        result: { ok: true },
        draft: { email: "admin@example.com", display_name: "Admin", role: "platform_admin", password: "secret" },
        resetStateByUserId: { user1: true },
      },
      memberSaveStateByUserId: { user1: true },
      mySalesClaims: [{ id: "c-1" }],
      companySalesClaims: [{ id: "c-2" }],
      mySalesClaimsError: "claims error",
      salesSummaryByUser: [{ id: "s-1" }],
      salesSummaryError: "summary error",
      salesClosedClaims: [{ id: "s-2" }],
      salesClosedError: "closed error",
      consoleInitialized: true,
      runsHandle: 11,
      authSessionHandle: 22,
    },
  });

  await handleAuthSignOut();

  assert.deepEqual(JSON.parse(JSON.stringify(apiCalls)), [[
    "/api/auth/sign-out",
    {
      method: "POST",
      body: "{}",
      cacheBust: false,
      timeoutMs: 10000,
    },
  ]]);
  assert.equal(context.state.profileDialog.open, false);
  assert.equal(context.state.profileDialog.saving, false);
  assert.deepEqual(clearIntervalCalls, [11, 22]);
  assert.equal(reloadCalls, 1);
  assert.equal(context.state.auth.authenticated, false);
  assert.equal(context.state.auth.authorized, false);
  assert.equal(context.state.auth.user, null);
  assert.equal(context.state.auth.message, "");
  assert.equal(context.state.organizationUsers.length, 0);
  assert.equal(context.state.organizationMembers.length, 0);
  assert.equal(context.state.organizationPlanSummary, null);
  assert.equal(context.state.organizationInvitations.length, 0);
  assert.equal(context.state.organizationAuditLogs.length, 0);
  assert.equal(context.state.organizationAuditLogsLoading, false);
  assert.equal(context.state.organizationAuditLogsLimit, 5);
  assert.equal(context.state.organizationAuditLogsHasMore, false);
  assert.equal(context.state.organizationDownloadAuditLogs.length, 0);
  assert.equal(context.state.organizationDownloadAuditLogsLoading, false);
  assert.equal(context.state.organizationDownloadAuditLogsLimit, 5);
  assert.equal(context.state.organizationDownloadAuditLogsHasMore, false);
  assert.equal(context.state.organizationLoginAuditLogs.length, 0);
  assert.equal(context.state.organizationLoginAuditLogsLoading, false);
  assert.equal(context.state.organizationLoginAuditLogsLimit, 5);
  assert.equal(context.state.organizationLoginAuditLogsHasMore, false);
  assert.deepEqual(JSON.parse(JSON.stringify(context.state.platformAdminAccount)), {
    saving: false,
    result: null,
    draft: {
      email: "",
      display_name: "",
      role: "org_member",
      password: "",
    },
    resetStateByUserId: {},
  });
  assert.equal(Object.keys(context.state.memberSaveStateByUserId).length, 0);
  assert.equal(context.state.mySalesClaims.length, 0);
  assert.equal(context.state.companySalesClaims.length, 0);
  assert.equal(context.state.mySalesClaimsError, "");
  assert.equal(context.state.salesSummaryByUser.length, 0);
  assert.equal(context.state.salesSummaryError, "");
  assert.equal(context.state.salesClosedClaims.length, 0);
  assert.equal(context.state.salesClosedError, "");
  assert.equal(context.state.consoleInitialized, false);
});

test("auth ui applyAuthSession preserves the session access token for protected follow-up requests", () => {
  const { applyAuthSession, context } = loadAuthUi({
    state: {
      auth: {
        enabled: true,
        checked: false,
        checking: false,
        authenticated: false,
        authorized: false,
        mode: "sign_in",
        inviteToken: "",
        invitationPreview: null,
        invitationPreviewLoading: false,
        invitationPreviewError: "",
        user: null,
        message: "",
        bootstrapEmail: "",
        accessToken: "",
      },
      uiMode: "user",
      consoleInitialized: false,
    },
    dom: {
      authShell: createElement(),
      consoleShell: createElement(),
      authMetaCard: createElement(),
      authSessionActions: createElement(),
      authModeSignIn: createElement(),
      authModeSignUp: createElement(),
      authDisplayNameField: createElement(),
      authSubmitButton: createElement(),
      authPassword: createElement({ value: "" }),
      authCopy: createElement(),
      authHint: createElement(),
      authStatus: createElement(),
      authUserBlocked: createElement(),
      authBlockedMessage: createElement(),
      authUserLabel: createElement(),
      authRoleLabel: createElement(),
      authSessionUserLabel: createElement(),
      authInvitePreview: createElement(),
      authEmail: createElement({ value: "runtime@example.com" }),
      authDisplayName: createElement({ value: "" }),
      patchActorLabel: createElement(),
    },
    requireAuthSessionRuntime: () => ({
      normalizeAuthSession(session) {
        return {
          enabled: true,
          checked: true,
          checking: false,
          authenticated: Boolean(session?.authenticated),
          authorized: Boolean(session?.authorized),
          accessToken: String(session?.access_token || ""),
          bootstrapEmail: String(session?.bootstrap_email || ""),
          message: String(session?.message || ""),
          user: session?.user || null,
        };
      },
      buildAuthUiViewModel: () => ({
        authEnabled: true,
        authorized: true,
        checking: false,
        signUpAllowed: true,
        inviteActionBlocked: false,
        authModeSignInActive: true,
        authModeSignUpActive: false,
        authDisplayNameHidden: true,
        authSubmitText: "로그인",
        authPasswordAutocomplete: "current-password",
        authCopyText: "",
        authHintText: "",
        status: { hasMessage: false, text: "", isError: false },
        showBlocked: false,
        blockedMessage: "",
        userLabel: "Runtime User",
        roleLabel: "role:org_admin",
        sessionUserLabel: "Runtime User",
        authShellHidden: true,
        consoleShellHidden: false,
        authShellActive: false,
        authMetaHidden: false,
        authSessionActionsHidden: false,
      }),
      buildAuthFormFieldViewModel: () => ({
        emailValue: "runtime@example.com",
        emailReadOnly: false,
        displayNameValue: "",
        passwordValue: "",
      }),
      buildAuthInvitationPreviewViewModel: () => ({ visible: false, html: "" }),
      buildProfileStatusViewModel: () => ({ text: "", hasMessage: false, isError: false }),
    }),
    syncUiModeFromLocation: () => {},
    syncUiModeChrome: () => false,
    applyUiModeTransition: () => {},
  });

  applyAuthSession({
    enabled: true,
    checked: true,
    checking: false,
    authenticated: true,
    authorized: true,
    access_token: "ui-session-token-123",
    bootstrap_email: "bootstrap@example.com",
    message: "",
    user: {
      display_name: "Runtime User",
      email: "runtime@example.com",
      organization_name: "Runtime Org",
      role: "org_admin",
    },
  });

  assert.equal(context.state.auth.accessToken, "ui-session-token-123");
});

test("createAuthController owns the auth bootstrap and invitation acceptance flow", async () => {
  const { initializeAuthGate, context, apiCalls, renderCalls } = loadAuthController();

  await initializeAuthGate();

  assert.deepEqual(apiCalls.map(([endpoint]) => endpoint), [
    "/api/auth/session",
    "/api/auth/invitations/preview?invite_token=invite-token",
    "/api/auth/invitations/accept",
  ]);
  assert.equal(context.state.auth.enabled, true);
  assert.equal(context.state.auth.checked, true);
  assert.equal(context.state.auth.checking, false);
  assert.equal(context.state.auth.authenticated, true);
  assert.equal(context.state.auth.authorized, true);
  assert.equal(context.state.auth.bootstrapEmail, "bootstrap@example.com");
  assert.equal(context.state.auth.user.display_name, "Accepted User");
  assert.deepEqual(context.state.auth.invitationPreview, {
    email: "invite@example.com",
    display_name: "Invited Name",
    initial_password: "InviteTemp123!",
    organization_name: "Invite Org",
    role: "org_admin",
    status: "pending",
  });
  assert.deepEqual(renderCalls, [
    ["renderAuthUi"],
    ["renderAuthUi"],
    ["renderAuthUi"],
    ["renderAuthUi"],
    ["renderAuthUi"],
  ]);
});

test("applyAuthSession triggers a renderAuth=false transition when the ui mode changes", () => {
  const transitionCalls = [];
  const stateRef = {
    uiMode: "user",
    consoleInitialized: false,
    auth: {
      enabled: true,
      checked: false,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_in",
      inviteToken: "",
      invitationPreview: null,
      invitationPreviewLoading: false,
      invitationPreviewError: "",
      user: null,
      message: "",
      bootstrapEmail: "",
      accessToken: "",
    },
  };
  const { applyAuthSession, context } = loadAuthController({
    state: stateRef,
    syncUiModeChrome: () => {
      stateRef.uiMode = "admin";
      return true;
    },
    applyUiModeTransition: (adminMode, options = {}) => {
      transitionCalls.push([adminMode, options]);
    },
  });

  applyAuthSession({
    enabled: true,
    checked: true,
    checking: false,
    authenticated: true,
    authorized: true,
    access_token: "session-token-123",
    bootstrap_email: "bootstrap@example.com",
    message: "",
    user: {
      display_name: "Promoted User",
      email: "promoted@example.com",
      organization_name: "Promoted Org",
      role: "org_admin",
    },
  });

  assert.equal(context.state.uiMode, "admin");
  assert.equal(transitionCalls.length, 1);
  assert.equal(transitionCalls[0][0], true);
  assert.equal(transitionCalls[0][1]?.renderAuth, false);
  assert.equal(context.state.auth.accessToken, "session-token-123");
});

test("applyAuthSession rehydrates admin mode from the project-status route after login", () => {
  const transitionCalls = [];
  const syncCalls = [];
  const stateRef = {
    uiMode: "user",
    consoleInitialized: false,
    auth: {
      enabled: true,
      checked: false,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_in",
      inviteToken: "",
      invitationPreview: null,
      invitationPreviewLoading: false,
      invitationPreviewError: "",
      user: null,
      message: "",
      bootstrapEmail: "",
    },
  };
  const { applyAuthSession } = loadAuthController({
    state: stateRef,
    window: {
      location: {
        hash: "",
        pathname: "/app/project-status",
        search: "",
      },
      history: {
        replaceState: () => {},
      },
      setTimeout,
      clearTimeout,
    },
    syncUiModeFromLocation: () => {
      syncCalls.push("sync");
      stateRef.uiMode = "admin";
    },
    syncUiModeChrome: () => stateRef.uiMode === "admin",
    applyUiModeTransition: (adminMode, options = {}) => {
      transitionCalls.push([adminMode, options]);
    },
  });

  applyAuthSession({
    enabled: true,
    checked: true,
    checking: false,
    authenticated: true,
    authorized: true,
    bootstrap_email: "bootstrap@example.com",
    message: "",
    user: {
      display_name: "Admin User",
      email: "admin@example.com",
      organization_name: "Promoted Org",
      role: "org_admin",
    },
  });

  assert.deepEqual(syncCalls, ["sync"]);
  assert.equal(stateRef.uiMode, "admin");
  assert.equal(transitionCalls.length, 1);
  assert.equal(transitionCalls[0][0], true);
  assert.equal(transitionCalls[0][1]?.renderAuth, false);
});

test("handleAuthPasswordReset uses the reset API for the bootstrap email", async () => {
  const apiCalls = [];
  const createAuthUiController = loadCreateAuthUiController();
  const stateRef = {
    auth: {
      enabled: true,
      checked: true,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_in",
      inviteToken: "",
      invitationPreview: null,
      invitationPreviewError: "",
      bootstrapEmail: "bootstrap@example.com",
      user: null,
      message: "",
    },
  };
  const dom = {
    authEmail: createElement({ value: "bootstrap@example.com" }),
    authResetPasswordButton: createElement({ textContent: "비밀번호 재설정" }),
    authShell: createElement(),
    consoleShell: createElement(),
    authMetaCard: createElement(),
    authSessionActions: createElement(),
    authModeSignIn: createElement(),
    authModeSignUp: createElement(),
    authDisplayNameField: createElement(),
    authSubmitButton: createElement(),
    authPassword: createElement({ value: "" }),
    authCopy: createElement(),
    authHint: createElement(),
    authStatus: createElement(),
    authUserBlocked: createElement(),
    authBlockedMessage: createElement(),
    authUserLabel: createElement(),
    authRoleLabel: createElement(),
    authSessionUserLabel: createElement(),
    authInvitePreview: createElement(),
    authDisplayName: createElement({ value: "" }),
  };
  const controller = createAuthUiController({
    console,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    state: stateRef,
    dom,
    document: { body: createElement() },
    shouldShowSignUpMode: () => true,
    requireAuthSessionRuntime: () => ({
      buildAuthUiViewModel: () => ({
        authEnabled: true,
        authorized: false,
        checking: false,
        signUpAllowed: true,
        inviteActionBlocked: false,
        authModeSignInActive: true,
        authModeSignUpActive: false,
        authDisplayNameHidden: true,
        authSubmitText: "로그인",
        authPasswordAutocomplete: "current-password",
        authCopyText: "",
        authHintText: "",
        status: { hasMessage: false, text: "", isError: false },
        showBlocked: false,
        blockedMessage: "",
        userLabel: "",
        roleLabel: "",
        sessionUserLabel: "",
        authShellHidden: false,
        consoleShellHidden: true,
        authShellActive: true,
        authMetaHidden: true,
        authSessionActionsHidden: true,
      }),
      buildAuthFormFieldViewModel: () => ({
        emailValue: "bootstrap@example.com",
        emailReadOnly: false,
        displayNameValue: "",
        passwordValue: "",
      }),
      buildAuthInvitationPreviewViewModel: () => ({ visible: false, html: "" }),
      buildProfileStatusViewModel: () => ({ text: "", hasMessage: false, isError: false }),
    }),
    api: async (endpoint, options) => {
      apiCalls.push([endpoint, options]);
      return { message: "reset sent" };
    },
    setBusy: () => {},
    renderAuthUi: () => {},
    formatOrgRoleLabel: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    escapeHtml: (value) => String(value ?? ""),
  });

  await controller.handleAuthPasswordReset();

  assert.equal(stateRef.auth.mode, "sign_in");
  assert.equal(stateRef.auth.message, "reset sent");
  assert.deepEqual(apiCalls.map(([endpoint]) => endpoint), ["/api/auth/password-reset"]);
});

test("handleAuthSubmit maps bootstrap sign-up invalid credentials to reset guidance", async () => {
  const createAuthUiController = loadCreateAuthUiController();
  const stateRef = {
    auth: {
      enabled: true,
      checked: true,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_up",
      inviteToken: "",
      invitationPreview: null,
      invitationPreviewError: "",
      bootstrapEmail: "bootstrap@example.com",
      user: null,
      message: "",
    },
  };
  const dom = {
    authEmail: createElement({ value: "bootstrap@example.com" }),
    authPassword: createElement({ value: "NewPassword123!" }),
    authDisplayName: createElement({ value: "Bootstrap User" }),
    authSubmitButton: createElement({ textContent: "계정 등록" }),
    authShell: createElement(),
    consoleShell: createElement(),
    authMetaCard: createElement(),
    authSessionActions: createElement(),
    authModeSignIn: createElement(),
    authModeSignUp: createElement(),
    authDisplayNameField: createElement(),
    authCopy: createElement(),
    authHint: createElement(),
    authStatus: createElement(),
    authUserBlocked: createElement(),
    authBlockedMessage: createElement(),
    authUserLabel: createElement(),
    authRoleLabel: createElement(),
    authSessionUserLabel: createElement(),
    authInvitePreview: createElement(),
  };
  const controller = createAuthUiController({
    console,
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    state: stateRef,
    dom,
    document: { body: createElement() },
    shouldShowSignUpMode: () => true,
    requireAuthSessionRuntime: () => ({
      buildAuthUiViewModel: () => ({
        authEnabled: true,
        authorized: false,
        checking: false,
        signUpAllowed: true,
        inviteActionBlocked: false,
        authModeSignInActive: false,
        authModeSignUpActive: true,
        authDisplayNameHidden: false,
        authSubmitText: "계정 등록",
        authPasswordAutocomplete: "new-password",
        authCopyText: "",
        authHintText: "",
        status: { hasMessage: false, text: "", isError: false },
        showBlocked: false,
        blockedMessage: "",
        userLabel: "",
        roleLabel: "",
        sessionUserLabel: "",
        authShellHidden: false,
        consoleShellHidden: true,
        authShellActive: true,
        authMetaHidden: true,
        authSessionActionsHidden: true,
      }),
      buildAuthFormFieldViewModel: () => ({
        emailValue: "bootstrap@example.com",
        emailReadOnly: false,
        displayNameValue: "",
        passwordValue: "",
      }),
      buildAuthInvitationPreviewViewModel: () => ({ visible: false, html: "" }),
      buildProfileStatusViewModel: () => ({ text: "", hasMessage: false, isError: false }),
    }),
    api: async () => {
      throw new Error('{"code":400,"error_code":"invalid_credentials","msg":"Invalid login credentials"}');
    },
    setBusy: () => {},
    renderAuthUi: () => {},
    ensureConsoleInitialized: async () => {},
    formatOrgRoleLabel: (value) => String(value ?? ""),
    formatInvitationStatusLabel: (value) => String(value ?? ""),
    formatSalesDateLabel: (value) => String(value ?? ""),
    formatMembershipStatusLabel: (value) => String(value ?? ""),
    escapeHtml: (value) => String(value ?? ""),
  });

  await controller.handleAuthSubmit({ preventDefault() {} });

  assert.equal(
    stateRef.auth.message,
    "이미 생성된 운영자 계정입니다. 비밀번호 재설정을 사용하거나 기존 비밀번호로 로그인하세요.",
  );
});
