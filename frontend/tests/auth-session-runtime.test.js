const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime() {
  const source = fs.readFileSync("frontend/auth-session-runtime.js", "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSAuthSessionRuntime;
}

test("buildAuthUiViewModel covers sign-in, sign-up, and invite-token states", () => {
  const runtime = loadRuntime();

  const signIn = runtime.buildAuthUiViewModel(
    {
      enabled: true,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_in",
    },
    {
      shouldShowSignUpMode: () => true,
      formatOrgRoleLabel: (value) => value,
    },
  );
  assert.equal(signIn.authModeSignInActive, true);
  assert.equal(signIn.authModeSignUpActive, false);
  assert.equal(signIn.authDisplayNameHidden, true);
  assert.equal(signIn.authPasswordAutocomplete, "current-password");
  assert.equal(signIn.authShellHidden, false);
  assert.equal(signIn.previewStatus, "");

  const signUp = runtime.buildAuthUiViewModel(
    {
      enabled: true,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_up",
    },
    {
      shouldShowSignUpMode: () => true,
      formatOrgRoleLabel: (value) => value,
    },
  );
  assert.equal(signUp.authModeSignInActive, false);
  assert.equal(signUp.authModeSignUpActive, true);
  assert.equal(signUp.authDisplayNameHidden, false);
  assert.equal(signUp.authPasswordAutocomplete, "new-password");

  const inviteToken = runtime.buildAuthUiViewModel(
    {
      enabled: true,
      checking: false,
      authenticated: false,
      authorized: false,
      mode: "sign_in",
      inviteToken: "invite-1",
      invitationPreview: { status: "accepted" },
    },
    {
      shouldShowSignUpMode: () => true,
      formatOrgRoleLabel: (value) => value,
    },
  );
  assert.equal(inviteToken.previewStatus, "accepted");
  assert.equal(inviteToken.inviteActionBlocked, false);
  assert.equal(inviteToken.authModeSignUpActive, false);
  assert.notEqual(inviteToken.authCopyText, signIn.authCopyText);
  assert.notEqual(inviteToken.authHintText, signIn.authHintText);
  assert.notEqual(inviteToken.authHintText, signUp.authHintText);
});

test("buildAuthInvitationPreviewViewModel covers loading, error, and accepted states", () => {
  const runtime = loadRuntime();

  const loading = runtime.buildAuthInvitationPreviewViewModel(
    {
      inviteToken: "invite-1",
      invitationPreviewLoading: true,
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => `role:${value}`,
      formatInvitationStatusLabel: (value) => `status:${value}`,
      formatSalesDateLabel: (value) => `date:${value}`,
    },
  );
  assert.equal(loading.visible, true);
  assert.match(loading.html, /auth-invite-preview-copy/);

  const error = runtime.buildAuthInvitationPreviewViewModel(
    {
      inviteToken: "invite-1",
      invitationPreviewError: "preview failed",
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => `role:${value}`,
      formatInvitationStatusLabel: (value) => `status:${value}`,
      formatSalesDateLabel: (value) => `date:${value}`,
    },
  );
  assert.equal(error.visible, true);
  assert.match(error.html, /preview failed/);

  const accepted = runtime.buildAuthInvitationPreviewViewModel(
    {
      inviteToken: "invite-1",
      invitationPreview: {
        display_name: "Alice",
        email: "alice@example.com",
        organization_name: "Org",
        role: "org_member",
        team_name: "Team",
        job_title: "Lead",
        status: "accepted",
        expires_at: "2026-03-30T00:00:00Z",
        initial_password: "Temp1234!",
      },
    },
    {
      escapeHtml: (value) => String(value),
      formatOrgRoleLabel: (value) => `role:${value}`,
      formatInvitationStatusLabel: (value) => `status:${value}`,
      formatSalesDateLabel: (value) => `date:${value}`,
    },
  );
  assert.equal(accepted.visible, true);
  assert.match(accepted.html, /Alice/);
  assert.match(accepted.html, /alice@example.com/);
  assert.match(accepted.html, /status:accepted/);
  assert.match(accepted.html, /Temp1234!/);
});

test("buildInvitationStatusViewModel hides blank text and marks errors", () => {
  const runtime = loadRuntime();

  const hidden = runtime.buildInvitationStatusViewModel("   ", "");
  assert.deepEqual(JSON.parse(JSON.stringify(hidden)), {
    text: "",
    hasMessage: false,
    isError: false,
  });

  const error = runtime.buildInvitationStatusViewModel("Invitation failed", "error");
  assert.deepEqual(JSON.parse(JSON.stringify(error)), {
    text: "Invitation failed",
    hasMessage: true,
    isError: true,
  });
});

test("buildProfileDialogViewModel syncs fields and invite-backed password rules", () => {
  const runtime = loadRuntime();

  const regularUser = runtime.buildProfileDialogViewModel(
    {
      user: {
        email: "user@example.com",
        display_name: "User",
        role: "org_admin",
        organization_name: "Org",
        membership_status: "active",
        mobile_phone: "010-1111-2222",
        office_phone: "02-3333-4444",
      },
    },
    {
      formatOrgRoleLabel: (value) => `role:${value}`,
      formatMembershipStatusLabel: (value) => `status:${value}`,
    },
  );
  assert.deepEqual(JSON.parse(JSON.stringify(regularUser)), {
    emailValue: "user@example.com",
    displayNameValue: "User",
    roleValue: "role:org_admin",
    organizationValue: "Org",
    statusValue: "status:active",
    mobilePhoneValue: "010-1111-2222",
    officePhoneValue: "02-3333-4444",
    currentPasswordValue: "",
    currentPasswordRequired: true,
    currentPasswordPlaceholder: "회원정보 수정 전에 현재 비밀번호를 입력하세요.",
    passwordValue: "",
    passwordConfirmValue: "",
  });

  const inviteSetup = runtime.buildProfileDialogViewModel(
    {
      user: {
        email: "invited@example.com",
        display_name: "Invitee",
        role: "org_member",
        organization_name: "Org",
        status: "inactive",
      },
      inviteToken: "invite-1",
      invitationPreview: { status: "accepted" },
    },
    {
      formatOrgRoleLabel: (value) => `role:${value}`,
      formatMembershipStatusLabel: (value) => `status:${value}`,
    },
  );
  assert.equal(inviteSetup.currentPasswordRequired, false);
  assert.equal(inviteSetup.currentPasswordPlaceholder, "초대 링크 첫 비밀번호 설정이면 비워둘 수 있습니다.");
  assert.equal(inviteSetup.displayNameValue, "Invitee");
});

test("buildProfileStatusViewModel hides empty state and marks errors", () => {
  const runtime = loadRuntime();

  const hidden = runtime.buildProfileStatusViewModel("", "");
  assert.deepEqual(JSON.parse(JSON.stringify(hidden)), {
    text: "",
    hasMessage: false,
    isError: false,
  });

  const error = runtime.buildProfileStatusViewModel("saved", "error");
  assert.deepEqual(JSON.parse(JSON.stringify(error)), {
    text: "saved",
    hasMessage: true,
    isError: true,
  });
});

test("shouldShowAdminModeToggle only exposes the toggle for verified admin sessions", () => {
  const runtime = loadRuntime();

  assert.equal(
    runtime.shouldShowAdminModeToggle({
      enabled: true,
      authenticated: true,
      authorized: true,
      user: { role: "org_admin" },
    }),
    true,
  );

  assert.equal(
    runtime.shouldShowAdminModeToggle({
      enabled: true,
      authenticated: true,
      authorized: true,
      user: { role: "org_member" },
    }),
    false,
  );

  assert.equal(
    runtime.shouldShowAdminModeToggle({
      enabled: true,
      authenticated: false,
      authorized: false,
      user: { role: "org_admin" },
    }),
    false,
  );
});

test("createAuthSessionRefreshController dedupes concurrent refresh calls", async () => {
  const runtime = loadRuntime();
  let calls = 0;
  const controller = runtime.createAuthSessionRefreshController({
    cooldownMs: 60_000,
    nowFn: () => 1_000,
  });

  const request = async () => {
    calls += 1;
    return { ok: true, calls };
  };

  const first = controller.run(request, { force: false });
  const second = controller.run(request, { force: false });
  const [firstResult, secondResult] = await Promise.all([first, second]);

  assert.equal(calls, 1);
  assert.deepEqual(firstResult, secondResult);
});

test("createAuthSessionRefreshController skips repeated calls inside cooldown and allows forced refresh", async () => {
  const runtime = loadRuntime();
  let now = 1_000;
  let calls = 0;
  const controller = runtime.createAuthSessionRefreshController({
    cooldownMs: 60_000,
    nowFn: () => now,
  });

  const request = async () => {
    calls += 1;
    return { ok: true, calls };
  };

  const first = await controller.run(request, { force: false });
  const skipped = await controller.run(request, { force: false });
  now += 5_000;
  const forced = await controller.run(request, { force: true });

  assert.deepEqual(first, { ok: true, calls: 1 });
  assert.equal(skipped, null);
  assert.deepEqual(forced, { ok: true, calls: 2 });
  assert.equal(calls, 2);
});

test("normalizeAuthSession does not keep a platform admin account creation flag", () => {
  const runtime = loadRuntime();

  const session = runtime.normalizeAuthSession({
    enabled: true,
    authenticated: true,
    authorized: true,
    bootstrap_email: "ops@example.com",
    platform_admin_account_creation_enabled: true,
    user: {
      role: "platform_admin",
      email: "ops@example.com",
    },
  });

  assert.equal("platformAdminAccountCreationEnabled" in session, false);
});
