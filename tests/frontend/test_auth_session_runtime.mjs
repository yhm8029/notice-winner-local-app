import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/auth-session-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAuthSessionRuntime;
}

test("buildAuthFormFieldViewModel locks email and pre-fills display name from invitation preview", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildAuthFormFieldViewModel, "function");

  const preview = {
    email: "invite@example.com",
    display_name: "초대 사용자",
    initial_password: "Temp1234!",
  };

  const blankView = runtime.buildAuthFormFieldViewModel({
    auth: {
      mode: "sign_up",
      inviteToken: "token-1",
      invitationPreview: preview,
    },
    currentEmail: "",
    currentDisplayName: "",
    currentPassword: "",
  });

  assert.equal(blankView.emailValue, "invite@example.com");
  assert.equal(blankView.emailReadOnly, true);
  assert.equal(blankView.displayNameValue, "초대 사용자");
  assert.equal(blankView.passwordValue, "Temp1234!");

  const typedView = runtime.buildAuthFormFieldViewModel({
    auth: {
      mode: "sign_up",
      inviteToken: "token-1",
      invitationPreview: preview,
    },
    currentEmail: "typed@example.com",
    currentDisplayName: "직접 입력한 이름",
    currentPassword: "MyTypedPass!",
  });

  assert.equal(typedView.emailValue, "invite@example.com");
  assert.equal(typedView.emailReadOnly, true);
  assert.equal(typedView.displayNameValue, "직접 입력한 이름");
  assert.equal(typedView.passwordValue, "MyTypedPass!");
});

test("buildAuthSessionActionViewModel returns authorized session labels", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildAuthSessionActionViewModel, "function");

  const view = runtime.buildAuthSessionActionViewModel({
    authorized: true,
    user: {
      display_name: "홍길동",
      email: "hong@example.com",
      organization_name: "테스트회사",
      role: "org_admin",
    },
  }, {
    formatOrgRoleLabel: (value) => value,
  });

  assert.equal(view.userLabel, "홍길동");
  assert.equal(view.roleLabel, "org_admin | 테스트회사");
  assert.equal(view.sessionUserLabel, "홍길동 · 테스트회사");
});

test("buildAuthUiViewModel returns sign-up submit text and password autocomplete", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime.buildAuthUiViewModel, "function");

  const view = runtime.buildAuthUiViewModel({
    enabled: true,
    checked: true,
    checking: false,
    authenticated: false,
    authorized: false,
    mode: "sign_up",
    inviteToken: "",
    bootstrapEmail: "admin@example.com",
    invitationPreview: null,
    invitationPreviewError: "",
    user: null,
    message: "",
  }, {
    shouldShowSignUpMode: () => true,
    formatOrgRoleLabel: (value) => value,
  });

  assert.equal(view.authSubmitText, "계정 등록");
  assert.equal(view.authPasswordAutocomplete, "new-password");
  assert.equal(view.authModeSignUpActive, true);
  assert.equal(view.authModeSignInActive, false);
  assert.equal(view.authShellHidden, false);
  assert.equal(view.consoleShellHidden, true);
  assert.equal(view.authShellActive, true);
  assert.equal(view.authMetaHidden, true);
  assert.equal(view.authSessionActionsHidden, true);
});

test("buildAuthUiViewModel leaves the default sign-in copy blank", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAuthUiViewModel({
    enabled: true,
    checked: true,
    checking: false,
    authenticated: false,
    authorized: false,
    mode: "sign_in",
    inviteToken: "",
    bootstrapEmail: "",
    invitationPreview: null,
    invitationPreviewError: "",
    user: null,
    message: "",
  }, {
    shouldShowSignUpMode: () => true,
    formatOrgRoleLabel: (value) => value,
  });

  assert.equal(view.authCopyText, "");
});

test("buildAuthUiViewModel composes session labels for authorized users", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAuthUiViewModel({
    enabled: true,
    checked: true,
    checking: false,
    authenticated: true,
    authorized: true,
    mode: "sign_in",
    user: {
      display_name: "Session User",
      email: "session@example.com",
      organization_name: "Runtime Org",
      role: "org_admin",
    },
    message: "",
  }, {
    shouldShowSignUpMode: () => true,
    formatOrgRoleLabel: (value) => `role:${value}`,
  });

  assert.equal(view.userLabel, "Session User");
  assert.equal(view.roleLabel, "role:org_admin | Runtime Org");
  assert.equal(view.sessionUserLabel, "Session User · Runtime Org");
  assert.equal(view.authShellHidden, true);
  assert.equal(view.consoleShellHidden, false);
  assert.equal(view.authShellActive, false);
  assert.equal(view.authMetaHidden, false);
  assert.equal(view.authSessionActionsHidden, false);
});
