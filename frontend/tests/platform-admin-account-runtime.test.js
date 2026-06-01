const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path, key) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window[key];
}

test("buildPlatformAdminAccountCardMarkup renders form controls for platform admins", () => {
  const runtime = loadRuntime("frontend/platform-admin-account-runtime.js", "SPMSPlatformAdminAccountRuntime");
  const html = runtime.buildPlatformAdminAccountCardMarkup(
    {
      enabled: true,
      currentUserRole: "platform_admin",
      saving: false,
      result: null,
    },
    {
      escapeHtml: (value) => String(value),
    },
  );

  assert.match(html, /platform-admin-account-form/);
  assert.match(html, /name="email"/);
  assert.match(html, /name="password"/);
  assert.match(html, /platform-admin-account-submit-button/);
});

test("buildPlatformAdminAccountCardMarkup hides the form for non-platform-admin users", () => {
  const runtime = loadRuntime("frontend/platform-admin-account-runtime.js", "SPMSPlatformAdminAccountRuntime");
  const html = runtime.buildPlatformAdminAccountCardMarkup(
    {
      enabled: true,
      currentUserRole: "org_admin",
      saving: false,
      result: null,
    },
    {
      escapeHtml: (value) => String(value),
    },
  );

  assert.doesNotMatch(html, /platform-admin-account-form/);
});

test("buildPlatformAdminAccountCardMarkup preserves form draft values across rerenders", () => {
  const runtime = loadRuntime("frontend/platform-admin-account-runtime.js", "SPMSPlatformAdminAccountRuntime");
  const html = runtime.buildPlatformAdminAccountCardMarkup(
    {
      enabled: true,
      currentUserRole: "platform_admin",
      saving: false,
      result: null,
      draft: {
        email: "draft@example.com",
        display_name: "Draft User",
        role: "org_admin",
        password: "TempPass123!",
      },
    },
    {
      escapeHtml: (value) => String(value),
    },
  );

  assert.match(html, /name="email"[^>]*value="draft@example\.com"/);
  assert.match(html, /name="display_name"[^>]*value="Draft User"/);
  assert.match(html, /option value="org_admin" selected/);
  assert.match(html, /name="password"[^>]*value="TempPass123!"/);
});

test("buildPlatformAdminAccountResultMarkup renders account details without echoing the password", () => {
  const runtime = loadRuntime("frontend/platform-admin-account-runtime.js", "SPMSPlatformAdminAccountRuntime");
  const html = runtime.buildPlatformAdminAccountResultMarkup(
    {
      email: "member@example.com",
      display_name: "Member",
      role: "org_member",
      account_status: "active",
      membership_status: "active",
      password_setup_mode: "admin_set",
      force_password_change: false,
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => String(value),
    },
  );

  assert.match(html, /member@example.com/);
  assert.match(html, /org_member/);
  assert.match(html, /active/);
  assert.doesNotMatch(html, /TempPass123!/);
});
