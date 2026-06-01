import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/organization-admin-runtime.js");
const controllerPath = path.resolve(__dirname, "../../frontend/org-admin-controller.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSOrganizationAdminRuntime;
}

function loadController(overrides = {}) {
  const source = fs.readFileSync(controllerPath, "utf8")
    .replace("export function createOrgAdminController", "function createOrgAdminController");
  const context = vm.createContext({
    window: {},
    console,
    globalThis: {},
    ...overrides,
  });
  vm.runInContext(source, context, { filename: controllerPath });
  return context.window.ORG_ADMIN_CONTROLLER.createOrgAdminController(overrides);
}

test("buildOrganizationPlanSummaryView returns disabled submit state when upgrade is required", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildOrganizationPlanSummaryView, "function");

  const upgradeMessage = "사용자 한도를 늘리려면 업그레이드가 필요합니다.";
  const view = runtime.buildOrganizationPlanSummaryView(
    {
      planSummary: {
        plan_label: "Starter",
        plan_code: "starter",
        active_user_count: 5,
        active_user_limit: 5,
        pending_invite_count: 2,
        pending_invite_limit: 2,
        remaining_active_user_slots: 0,
        remaining_pending_invite_slots: 0,
        upgrade_required: true,
        upgrade_message: upgradeMessage,
      },
    },
    {
      escapeHtml: (value) => String(value),
    },
  );

  assert.match(view.html, /업그레이드 필요/);
  assert.equal(view.invitationSubmitDisabled, true);
  assert.equal(view.invitationSubmitTitle, upgradeMessage);
});

test("buildOrganizationInvitationListView renders hidden pending hint", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildOrganizationInvitationListView, "function");

  const view = runtime.buildOrganizationInvitationListView(
    {
      organizationInvitations: [
        { id: "inv-1", email: "one@example.com", status: "pending", role: "org_member" },
      ],
      planSummary: { pending_invite_count: 3 },
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => value,
      formatInvitationStatusLabel: (value) => value,
      formatDate: (value) => String(value || ""),
    },
  );

  assert.match(view.html, /hint-text/);
  assert.match(view.html, /현재 권한으로 관리할 수 없는 pending 초대가 있습니다\./);
  assert.match(view.html, /inv-1/);
});

test("buildOrganizationMemberViews sorts active members first and locks protected/self accounts", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildOrganizationMemberSummaryView, "function");
  assert.equal(typeof runtime.buildOrganizationMemberListView, "function");

  const members = [
    { id: "self-1", email: "self@example.com", display_name: "나", role: "org_admin", membership_status: "active", account_status: "active" },
    { id: "protected-1", email: "protected@example.com", display_name: "보호", role: "org_admin", membership_status: "active", account_status: "active" },
    { id: "member-2", email: "inactive@example.com", display_name: "비활성", role: "org_member", membership_status: "inactive", account_status: "active" },
    { id: "member-1", email: "active@example.com", display_name: "활성", role: "org_member", membership_status: "active", account_status: "active" },
  ];

  const summaryView = runtime.buildOrganizationMemberSummaryView(
    { organizationMembers: members },
    {
      escapeHtml: (value) => String(value),
      formatAccountStatusLabel: (value) => value,
      formatMembershipStatusLabel: (value) => value,
      resolveStatusClass: (value) => value,
    },
  );
  assert.match(summaryView.html, /총4명/);

  const listView = runtime.buildOrganizationMemberListView(
    {
      organizationMembers: members,
      memberSaveStateByUserId: {},
      memberDeleteStateByUserId: {},
    },
    {
      escapeHtml: (value) => String(value),
      formatAccountStatusLabel: (value) => value,
      formatMembershipStatusLabel: (value) => value,
      formatOrgRoleLabel: (value) => value,
      resolveStatusClass: (value) => value,
      membershipStatusOptions: ["active", "inactive", "deactivated"],
      getRenderableOrgRoleOptions: () => ["org_member", "org_admin"],
      isProtectedOrganizationMember: (member) => member.id === "protected-1",
      getCurrentAuthLocalUserId: () => "self-1",
    },
  );

  assert.ok(listView.html.indexOf("active@example.com") < listView.html.indexOf("inactive@example.com"));

  const selfCardMatch = listView.html.match(/<article class="org-admin-list-item org-member-card" data-member-id="self-1">[\s\S]*?<\/article>/);
  const protectedCardMatch = listView.html.match(/<article class="org-admin-list-item org-member-card" data-member-id="protected-1">[\s\S]*?<\/article>/);

  assert.ok(selfCardMatch, "self member card should be rendered");
  assert.ok(protectedCardMatch, "protected member card should be rendered");

  const selfCard = selfCardMatch[0];
  const protectedCard = protectedCardMatch[0];

  assert.match(selfCard, /data-member-field="role"[^>]*disabled/);
  assert.match(selfCard, /data-member-field="membership_status"[^>]*disabled/);
  assert.doesNotMatch(selfCard, /data-member-delete="self-1"/);

  assert.match(protectedCard, /data-member-field="role"[^>]*disabled/);
  assert.match(protectedCard, /data-member-field="membership_status"[^>]*disabled/);
  assert.doesNotMatch(protectedCard, /data-member-delete="protected-1"/);
});

test("resetOrganizationMemberPassword resets the member password and refreshes organization data", async () => {
  const calls = [];
  class HTMLElement {
    querySelector(selector) {
      calls.push(["querySelector", selector]);
      return selector === "strong" ? { textContent: "  Member One  " } : null;
    }
  }
  const state = {
    auth: { enabled: true, authorized: true, user: { role: "org_admin" } },
    platformAdminAccount: { draft: {}, saving: false, result: null, resetStateByUserId: {} },
    memberSaveStateByUserId: {},
    memberDeleteStateByUserId: {},
  };
  const controller = loadController({
    window: {
      HTMLElement,
      prompt: (message, value) => {
        calls.push(["prompt", message, value]);
        return "  new-secret  ";
      },
    },
    state,
    dom: {},
    api: async (url, options) => {
      calls.push(["api", url, options]);
      return { message: "reset ok" };
    },
    flash: (message, type = "") => {
      calls.push(["flash", message, type]);
    },
    renderOrganizationAdminPanel: () => {
      calls.push(["renderOrganizationAdminPanel", { ...state.platformAdminAccount.resetStateByUserId }]);
    },
    canManagePlatformAdminAccounts: () => true,
    requireConsoleDataRuntime: () => ({
      loadOrganizationMembers(runtimeDeps, options) {
        calls.push(["loadOrganizationMembers", runtimeDeps, options]);
      },
      loadOrganizationAuditLogs(runtimeDeps, options) {
        calls.push(["loadOrganizationAuditLogs", runtimeDeps, options]);
      },
    }),
    getConsoleDataRuntimeDeps: () => "console-runtime-deps",
  });

  await controller.resetOrganizationMemberPassword("user-1", new HTMLElement());

  assert.deepEqual(calls[0], ["querySelector", "strong"]);
  assert.deepEqual(calls[1], ["prompt", "Member One 계정의 새 비밀번호를 입력하세요.", ""]);
  assert.deepEqual(calls[2], ["renderOrganizationAdminPanel", { "user-1": true }]);
  assert.equal(calls[3][0], "api");
  assert.equal(calls[3][1], "/api/admin/accounts/user-1/password-reset");
  assert.equal(calls[3][2].method, "POST");
  assert.equal(calls[3][2].body, JSON.stringify({ password: "new-secret" }));
  assert.deepEqual(calls[4], ["flash", "reset ok", ""]);
  assert.equal(calls[5][0], "loadOrganizationMembers");
  assert.equal(calls[5][1], "console-runtime-deps");
  assert.equal(calls[5][2].silent, true);
  assert.equal(calls[6][0], "loadOrganizationAuditLogs");
  assert.equal(calls[6][1], "console-runtime-deps");
  assert.equal(calls[6][2].silent, true);
  assert.deepEqual(calls.at(-1), ["renderOrganizationAdminPanel", {}]);
  assert.equal(Object.keys(state.platformAdminAccount.resetStateByUserId).length, 0);
});

test("resetOrganizationMemberPassword rejects an empty password before calling the API", async () => {
  const calls = [];
  class HTMLElement {
    querySelector(selector) {
      calls.push(["querySelector", selector]);
      return { textContent: "Member Two" };
    }
  }
  const controller = loadController({
    window: {
      HTMLElement,
      prompt: (message, value) => {
        calls.push(["prompt", message, value]);
        return "   ";
      },
    },
    state: {
      auth: { enabled: true, authorized: true, user: { role: "org_admin" } },
      platformAdminAccount: { draft: {}, saving: false, result: null, resetStateByUserId: {} },
      memberSaveStateByUserId: {},
      memberDeleteStateByUserId: {},
    },
    dom: {},
    api: async () => {
      throw new Error("api should not be called for an empty password");
    },
    flash: (message, type = "") => {
      calls.push(["flash", message, type]);
    },
    renderOrganizationAdminPanel: () => {
      calls.push(["renderOrganizationAdminPanel"]);
    },
    canManagePlatformAdminAccounts: () => true,
    loadOrganizationMembers: async () => {
      throw new Error("loadOrganizationMembers should not run for an empty password");
    },
    loadOrganizationAuditLogs: async () => {
      throw new Error("loadOrganizationAuditLogs should not run for an empty password");
    },
  });

  await controller.resetOrganizationMemberPassword("user-2", new HTMLElement());

  assert.deepEqual(calls, [
    ["querySelector", "strong"],
    ["prompt", "Member Two 계정의 새 비밀번호를 입력하세요.", ""],
    ["flash", "비밀번호를 입력해야 합니다.", "error"],
  ]);
});

test("handlePlatformAdminAccountSubmit creates an account and refreshes org admin data", async () => {
  const calls = [];
  class HTMLFormElement {
    constructor(fields = {}) {
      this.fields = fields;
    }
  }
  class FormData {
    constructor(form) {
      this.fields = form.fields || {};
    }
    get(name) {
      return this.fields[name];
    }
  }
  const controller = loadController({
    window: { HTMLFormElement, FormData },
    state: {
      auth: { enabled: true, authorized: true, user: { role: "org_admin" } },
      platformAdminAccount: { draft: {}, saving: false, result: null, resetStateByUserId: {} },
      memberSaveStateByUserId: {},
      memberDeleteStateByUserId: {},
    },
    dom: {},
    api: async (url, options) => {
      calls.push(["api", url, options]);
      return { id: "acct-1", email: "admin@example.com" };
    },
    flash: (message, type = "") => {
      calls.push(["flash", message, type]);
    },
    renderOrganizationAdminPanel: () => {
      calls.push(["renderOrganizationAdminPanel"]);
    },
    canManagePlatformAdminAccounts: () => true,
    loadOrganizationMembers: async (options) => {
      calls.push(["loadOrganizationMembers", options]);
    },
    loadOrganizationUsers: async (options) => {
      calls.push(["loadOrganizationUsers", options]);
    },
    loadOrganizationAuditLogs: async (options) => {
      calls.push(["loadOrganizationAuditLogs", options]);
    },
  });

  const form = new HTMLFormElement({
    email: " admin@example.com ",
    display_name: "  Admin User  ",
    role: "org_member",
    password: "secret123",
  });
  const event = {
    preventDefault() {
      calls.push(["preventDefault"]);
    },
    currentTarget: form,
  };

  await controller.handlePlatformAdminAccountSubmit(event);

  assert.deepEqual(calls[0], ["preventDefault"]);
  assert.deepEqual(calls[1], ["renderOrganizationAdminPanel"]);
  assert.equal(calls[2][0], "api");
  assert.equal(calls[2][1], "/api/admin/accounts");
  assert.equal(calls[2][2].method, "POST");
  assert.equal(calls[2][2].body, JSON.stringify({
    email: "admin@example.com",
    display_name: "Admin User",
    role: "org_member",
    password: "secret123",
  }));
  assert.equal(calls[2][2].cacheBust, false);
  assert.equal(calls[2][2].timeoutMs, 20000);
  assert.deepEqual(calls[3], ["flash", "계정을 생성했습니다.", ""]);
  assert.equal(calls[4][0], "loadOrganizationMembers");
  assert.equal(calls[4][1].silent, true);
  assert.equal(calls[5][0], "loadOrganizationUsers");
  assert.equal(calls[5][1].silent, true);
  assert.equal(calls[6][0], "loadOrganizationAuditLogs");
  assert.equal(calls[6][1].silent, true);
  assert.deepEqual(calls.at(-1), ["renderOrganizationAdminPanel"]);
});

test("handlePlatformAdminAccountSubmit blocks disallowed roles before calling the API", async () => {
  const calls = [];
  class HTMLFormElement {
    constructor(fields = {}) {
      this.fields = fields;
    }
  }
  class FormData {
    constructor(form) {
      this.fields = form.fields || {};
    }
    get(name) {
      return this.fields[name];
    }
  }
  const controller = loadController({
    window: { HTMLFormElement, FormData },
    state: {
      auth: { enabled: true, authorized: true, user: { role: "org_member" } },
      platformAdminAccount: { draft: {}, saving: false, result: null, resetStateByUserId: {} },
      memberSaveStateByUserId: {},
      memberDeleteStateByUserId: {},
    },
    dom: {},
    api: async () => {
      throw new Error("api should not be called for blocked roles");
    },
    flash: (message, type = "") => {
      calls.push(["flash", message, type]);
    },
    renderOrganizationAdminPanel: () => {
      calls.push(["renderOrganizationAdminPanel"]);
    },
    canManagePlatformAdminAccounts: () => true,
    loadOrganizationMembers: async () => {
      throw new Error("loadOrganizationMembers should not run for blocked roles");
    },
    loadOrganizationUsers: async () => {
      throw new Error("loadOrganizationUsers should not run for blocked roles");
    },
    loadOrganizationAuditLogs: async () => {
      throw new Error("loadOrganizationAuditLogs should not run for blocked roles");
    },
  });

  const form = new HTMLFormElement({
    email: "blocked@example.com",
    display_name: "Blocked User",
    role: "org_admin",
    password: "secret123",
  });
  const event = {
    preventDefault() {
      calls.push(["preventDefault"]);
    },
    currentTarget: form,
  };

  await controller.handlePlatformAdminAccountSubmit(event);

  assert.deepEqual(calls[0], ["preventDefault"]);
  assert.deepEqual(calls[1], [
    "flash",
    "이 화면에서는 해당 역할 계정을 만들 수 없습니다.",
    "error",
  ]);
  assert.equal(calls.length, 2);
});
