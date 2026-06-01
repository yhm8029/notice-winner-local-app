# Auth UI Runtime Batch 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move more auth/profile/invitation presentation logic from `frontend/app.js` into `frontend/auth-session-runtime.js` without changing auth behavior, API calls, or selector contracts.

**Architecture:** `frontend/auth-session-runtime.js` should own deterministic auth view-model helpers for auth shell state, invitation/profile status display, and profile dialog field synchronization. `frontend/app.js` should keep DOM writes, state mutation, API calls, and event handling. This follows the same runtime-plus-app orchestration pattern already used for tracker, artifact, sales, and org-admin seams.

**Tech Stack:** Vanilla JavaScript, browser runtime helpers on `window.*`, Node test runner

---

### Task 1: Lock Current Auth UI View Behavior With Runtime Tests

**Files:**
- Create: `frontend/tests/auth-session-runtime.test.js`
- Modify: `frontend/auth-session-runtime.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: Write the failing auth runtime tests**

```js
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime() {
  const source = fs.readFileSync(path.join(__dirname, "..", "auth-session-runtime.js"), "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSAuthSessionRuntime;
}

test("buildAuthUiViewModel keeps sign-in mode hidden states and submit text stable", () => {
  const runtime = loadRuntime();
  const view = runtime.buildAuthUiViewModel(
    {
      enabled: true,
      authenticated: false,
      authorized: false,
      checking: false,
      mode: "sign_in",
      inviteToken: "",
      bootstrapEmail: "admin@example.com",
      message: "",
      user: null,
    },
    {
      shouldShowSignUpMode: () => true,
      formatOrgRoleLabel: (value) => value,
    },
  );

  assert.equal(view.authModeSignInActive, true);
  assert.equal(view.authModeSignUpActive, false);
  assert.equal(view.authDisplayNameHidden, true);
  assert.equal(view.authSubmitText, "로그인");
  assert.equal(view.authPasswordAutocomplete, "current-password");
});
```

- [ ] **Step 2: Add failing tests for invitation preview and profile dialog field sync**

```js
test("buildAuthInvitationPreviewViewModel renders accepted invitation details", () => {
  const runtime = loadRuntime();
  const view = runtime.buildAuthInvitationPreviewViewModel(
    {
      inviteToken: "invite-token",
      invitationPreviewLoading: false,
      invitationPreviewError: "",
      invitationPreview: {
        display_name: "홍길동",
        email: "member@example.com",
        organization_name: "Internal Ops",
        role: "org_member",
        status: "accepted",
        expires_at: "2026-03-31T12:00:00Z",
        initial_password: "TempPass123!",
      },
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      formatOrgRoleLabel: (value) => value,
      formatInvitationStatusLabel: (value) => value,
      formatSalesDateLabel: (value) => value,
    },
  );

  assert.equal(view.visible, true);
  assert.match(view.html, /member@example.com/);
  assert.match(view.html, /accepted/);
  assert.match(view.html, /TempPass123!/);
});

test("buildProfileDialogViewModel requires current password unless invite password setup is allowed", () => {
  const runtime = loadRuntime();
  const view = runtime.buildProfileDialogViewModel({
    user: {
      email: "member@example.com",
      display_name: "홍길동",
      role: "org_member",
      organization_name: "Internal Ops",
      membership_status: "active",
      mobile_phone: "010-1111-2222",
      office_phone: "02-123-4567",
    },
    inviteToken: "",
    invitationPreview: null,
  });

  assert.equal(view.currentPasswordRequired, true);
  assert.match(view.currentPasswordPlaceholder, /현재 비밀번호/);
  assert.equal(view.displayNameValue, "홍길동");
  assert.equal(view.mobilePhoneValue, "010-1111-2222");
});
```

- [ ] **Step 3: Run the focused test file to verify it fails**

Run: `node --test frontend/tests/auth-session-runtime.test.js`
Expected: FAIL because `buildProfileDialogViewModel` and the new auth runtime coverage do not exist yet.

- [ ] **Step 4: Commit the red state**

```bash
git add frontend/tests/auth-session-runtime.test.js
git commit -m "test: add auth session runtime coverage"
```

### Task 2: Move Profile Dialog Field Derivation Into `auth-session-runtime.js`

**Files:**
- Modify: `frontend/auth-session-runtime.js`
- Modify: `frontend/app.js`
- Test: `frontend/tests/auth-session-runtime.test.js`

- [ ] **Step 1: Add the profile dialog view-model helper**

```js
function buildProfileDialogViewModel(payload = {}, helpers = {}) {
  const {
    user = null,
    inviteToken = "",
    invitationPreview = null,
  } = payload;
  const {
    formatOrgRoleLabel = (value) => String(value || "-"),
    formatMembershipStatusLabel = (value) => String(value || "-"),
  } = helpers;
  const invitePasswordSetupAllowed = Boolean(
    inviteToken
    && invitationPreview
    && String(invitationPreview.status || "") === "accepted"
  );
  return {
    emailValue: String(user?.email || ""),
    displayNameValue: String(user?.display_name || user?.email || ""),
    roleValue: formatOrgRoleLabel(user?.role || "-"),
    organizationValue: String(user?.organization_name || "-"),
    statusValue: formatMembershipStatusLabel(user?.membership_status || user?.status || "active"),
    mobilePhoneValue: String(user?.mobile_phone || ""),
    officePhoneValue: String(user?.office_phone || ""),
    currentPasswordRequired: !invitePasswordSetupAllowed,
    currentPasswordPlaceholder: invitePasswordSetupAllowed
      ? "초대 링크 첫 비밀번호 설정이면 비워둘 수 있습니다."
      : "회원정보 수정 전에 현재 비밀번호를 입력하세요.",
  };
}
```

- [ ] **Step 2: Rewire `syncProfileDialogWithSession()` to consume the runtime helper**

```js
function syncProfileDialogWithSession() {
  const user = state.auth.user;
  if (!user) {
    return;
  }
  const view = requireAuthSessionRuntime().buildProfileDialogViewModel(
    {
      user,
      inviteToken: state.auth.inviteToken,
      invitationPreview: state.auth.invitationPreview,
    },
    {
      formatOrgRoleLabel,
      formatMembershipStatusLabel,
    },
  );
  if (dom.profileEmail) {
    dom.profileEmail.value = view.emailValue;
  }
  if (dom.profileDisplayName) {
    dom.profileDisplayName.value = view.displayNameValue;
  }
  if (dom.profileRole) {
    dom.profileRole.value = view.roleValue;
  }
  if (dom.profileOrganization) {
    dom.profileOrganization.value = view.organizationValue;
  }
  if (dom.profileStatus) {
    dom.profileStatus.value = view.statusValue;
  }
  if (dom.profileMobilePhone) {
    dom.profileMobilePhone.value = view.mobilePhoneValue;
  }
  if (dom.profileOfficePhone) {
    dom.profileOfficePhone.value = view.officePhoneValue;
  }
  if (dom.profileCurrentPassword) {
    dom.profileCurrentPassword.value = "";
    dom.profileCurrentPassword.required = view.currentPasswordRequired;
    dom.profileCurrentPassword.placeholder = view.currentPasswordPlaceholder;
  }
  if (dom.profilePassword) {
    dom.profilePassword.value = "";
  }
  if (dom.profilePasswordConfirm) {
    dom.profilePasswordConfirm.value = "";
  }
  renderProfileStatus("", "");
}
```

- [ ] **Step 3: Run the focused suite**

Run: `node --test frontend/tests/auth-session-runtime.test.js`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/auth-session-runtime.js frontend/app.js frontend/tests/auth-session-runtime.test.js
git commit -m "refactor: extract auth profile dialog view model"
```

### Task 3: Move Status Message View Logic Into `auth-session-runtime.js`

**Files:**
- Modify: `frontend/auth-session-runtime.js`
- Modify: `frontend/app.js`
- Test: `frontend/tests/auth-session-runtime.test.js`

- [ ] **Step 1: Add a profile status view-model helper beside the invitation one**

```js
function buildProfileStatusViewModel(message = "", level = "") {
  const text = String(message || "").trim();
  return {
    text,
    hasMessage: Boolean(text),
    isError: level === "error",
  };
}
```

- [ ] **Step 2: Rewire `renderProfileStatus()` and keep `renderInvitationStatus()` aligned**

```js
function renderProfileStatus(message = "", level = "") {
  if (!dom.profileStatusMessage) {
    return;
  }
  const view = requireAuthSessionRuntime().buildProfileStatusViewModel(message, level);
  dom.profileStatusMessage.textContent = view.text;
  dom.profileStatusMessage.classList.toggle("hidden", !view.hasMessage);
  dom.profileStatusMessage.classList.toggle("error", view.isError);
}

function renderInvitationStatus(message = "", level = "") {
  if (!dom.invitationStatusMessage) {
    return;
  }
  const view = requireAuthSessionRuntime().buildInvitationStatusViewModel(message, level);
  dom.invitationStatusMessage.textContent = view.text;
  dom.invitationStatusMessage.classList.toggle("hidden", !view.hasMessage);
  dom.invitationStatusMessage.classList.toggle("error", view.isError);
}
```

- [ ] **Step 3: Add tests for hidden/error states**

```js
test("buildProfileStatusViewModel mirrors invitation status semantics", () => {
  const runtime = loadRuntime();
  const hiddenView = runtime.buildProfileStatusViewModel("", "");
  const errorView = runtime.buildProfileStatusViewModel("저장 실패", "error");

  assert.equal(hiddenView.hasMessage, false);
  assert.equal(errorView.hasMessage, true);
  assert.equal(errorView.isError, true);
  assert.equal(errorView.text, "저장 실패");
});
```

- [ ] **Step 4: Run the focused suite**

Run: `node --test frontend/tests/auth-session-runtime.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/auth-session-runtime.js frontend/app.js frontend/tests/auth-session-runtime.test.js
git commit -m "refactor: extract auth status view models"
```

### Task 4: Verify Auth Shell And Invitation Preview Runtime Coverage

**Files:**
- Modify: `frontend/tests/auth-session-runtime.test.js`
- Modify: `frontend/auth-session-runtime.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: Add auth-shell state coverage for sign-up, invite-token, and blocked invitation paths**

```js
test("buildAuthUiViewModel reflects invite-token sign-up and blocked preview states", () => {
  const runtime = loadRuntime();
  const view = runtime.buildAuthUiViewModel(
    {
      enabled: true,
      authenticated: false,
      authorized: false,
      checking: false,
      mode: "sign_up",
      inviteToken: "invite-token",
      invitationPreview: { status: "revoked" },
      invitationPreviewError: "",
      bootstrapEmail: "admin@example.com",
      message: "",
      user: null,
    },
    {
      shouldShowSignUpMode: () => true,
      formatOrgRoleLabel: (value) => value,
    },
  );

  assert.equal(view.authModeSignUpActive, true);
  assert.equal(view.inviteActionBlocked, true);
  assert.match(view.authCopyText, /초대/);
});
```

- [ ] **Step 2: Add invitation-preview loading/error coverage**

```js
test("buildAuthInvitationPreviewViewModel handles loading and error states", () => {
  const runtime = loadRuntime();
  const loadingView = runtime.buildAuthInvitationPreviewViewModel(
    {
      inviteToken: "invite-token",
      invitationPreviewLoading: true,
      invitationPreviewError: "",
      invitationPreview: null,
    },
    { escapeHtml: (value) => String(value ?? "") },
  );
  const errorView = runtime.buildAuthInvitationPreviewViewModel(
    {
      inviteToken: "invite-token",
      invitationPreviewLoading: false,
      invitationPreviewError: "초대 링크 만료",
      invitationPreview: null,
    },
    { escapeHtml: (value) => String(value ?? "") },
  );

  assert.equal(loadingView.visible, true);
  assert.match(loadingView.html, /확인/);
  assert.equal(errorView.visible, true);
  assert.match(errorView.html, /초대 링크 만료/);
});
```

- [ ] **Step 3: Run the auth runtime suite and syntax checks**

Run: `node --test frontend/tests/auth-session-runtime.test.js`
Expected: PASS

Run: `node --check frontend/auth-session-runtime.js frontend/app.js`
Expected: exit code `0`

- [ ] **Step 4: Commit final auth UI batch**

```bash
git add frontend/auth-session-runtime.js frontend/app.js frontend/tests/auth-session-runtime.test.js
git commit -m "test: cover auth ui runtime batch 1"
```
