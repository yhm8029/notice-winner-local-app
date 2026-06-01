# Main Modularization Auth Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `feature/related-notice-search` 브랜치에서 `auth session` UI와 form state 계산을 [`frontend/auth-session-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/auth-session-runtime.js)로 더 분리하고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 인증 API 호출, 상태 전이, 이벤트 처리 중심으로 남긴다.

**Architecture:** 이번 차수는 `UI/view-model 우선 분리`다. runtime은 auth shell, invitation preview, form field 상태, session action label을 순수 helper로 계산하고, `app.js`는 `initializeAuthGate()` 계열 네트워크 흐름과 submit/reset/signout 실행, DOM 이벤트만 유지한다. `bootstrap-runtime.js`와 인증 네트워크 로직은 이번 범위에서 제외한다.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser global runtime pattern (`window.SPMSAuthSessionRuntime`), existing frontend shell in `frontend/app.js`

---

## File Structure

- `frontend/auth-session-runtime.js`
  - 세션 normalize, auth shell view-model, invitation preview view-model, form field view-model, session action view-model을 제공한다.
- `frontend/app.js`
  - auth API 호출, debounce/hash import/pending invite accept, submit/reset/signout 실행과 DOM 반영을 담당한다.
- `tests/frontend/test_auth_session_runtime.mjs`
  - auth-session runtime helper를 node 환경에서 직접 검증한다.
- `tests/frontend/test_auth_session_app_integration.mjs`
  - `renderAuthUi()`가 runtime 결과를 반영하는지 behavioral integration으로 검증한다.

### Task 1: Add Auth Session Runtime Tests

**Files:**
- Create: `tests/frontend/test_auth_session_runtime.mjs`

- [ ] **Step 1: Write the failing runtime tests**

```js
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

  const view = runtime.buildAuthFormFieldViewModel({
    auth: {
      mode: "sign_up",
      inviteToken: "token-1",
      invitationPreview: {
        email: "invite@example.com",
        display_name: "초대 사용자",
        initial_password: "Temp1234!",
      },
    },
    currentEmail: "",
    currentDisplayName: "",
    currentPassword: "",
  });

  assert.equal(view.emailValue, "invite@example.com");
  assert.equal(view.emailReadOnly, true);
  assert.equal(view.displayNameValue, "초대 사용자");
  assert.equal(view.passwordValue, "Temp1234!");
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

  assert.match(view.userLabel, /홍길동/);
  assert.match(view.roleLabel, /org_admin/);
  assert.match(view.sessionUserLabel, /테스트회사/);
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
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_auth_session_runtime.mjs`  
Expected: FAIL with messages like `runtime.buildAuthFormFieldViewModel is not a function`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/frontend/test_auth_session_runtime.mjs
git commit -m "test: auth session runtime helper 기대값 추가"
```

### Task 2: Implement Auth Session Runtime Helpers

**Files:**
- Modify: `frontend/auth-session-runtime.js`
- Test: `tests/frontend/test_auth_session_runtime.mjs`

- [ ] **Step 1: Add auth form field helper**

`frontend/auth-session-runtime.js`에 form field 계산 helper를 추가한다.

```js
function buildAuthFormFieldViewModel({
  auth = {},
  currentEmail = "",
  currentDisplayName = "",
  currentPassword = "",
} = {}) {
  const preview = auth.invitationPreview || null;
  const invitedEmail = String(preview?.email || "").trim();
  const isLocked = Boolean(invitedEmail);
  const isSignUp = auth.mode === "sign_up";

  return {
    emailValue: isLocked ? invitedEmail : String(currentEmail || ""),
    emailReadOnly: isLocked,
    displayNameValue:
      preview?.display_name && !String(currentDisplayName || "").trim()
        ? String(preview.display_name || "").trim()
        : String(currentDisplayName || ""),
    passwordValue:
      isSignUp && preview?.initial_password && !String(currentPassword || "").trim()
        ? String(preview.initial_password || "")
        : String(currentPassword || ""),
  };
}
```

- [ ] **Step 2: Add session action helper**

```js
function buildAuthSessionActionViewModel(auth = {}, helpers = {}) {
  const { formatOrgRoleLabel = (value) => String(value || "") } = helpers;
  const user = auth.user || null;
  if (!user) {
    return {
      userLabel: "",
      roleLabel: "",
      sessionUserLabel: "",
    };
  }
  return {
    userLabel: user.display_name || user.email || "-",
    roleLabel: `${formatOrgRoleLabel(user.role || "-")} | ${user.organization_name || "-"}`,
    sessionUserLabel: `${user.display_name || user.email || "-"} · ${user.organization_name || "-"}`,
  };
}
```

- [ ] **Step 3: Extend `buildAuthUiViewModel()` to compose helper results**

Update `buildAuthUiViewModel()` so it reuses `buildAuthSessionActionViewModel()` and keeps these contracts:

```js
const sessionLabels = buildAuthSessionActionViewModel(auth, { formatOrgRoleLabel });

return {
  authEnabled,
  authorized,
  checking,
  signUpAllowed,
  isSignUp,
  previewStatus,
  inviteActionBlocked,
  authCopyText,
  authHintText,
  status,
  showBlocked,
  blockedMessage,
  userLabel: sessionLabels.userLabel,
  roleLabel: sessionLabels.roleLabel,
  sessionUserLabel: sessionLabels.sessionUserLabel,
  authModeSignInActive: !isSignUp,
  authModeSignUpActive: isSignUp,
  authDisplayNameHidden: !isSignUp,
  authSubmitText: isSignUp ? "계정 등록" : "로그인",
  authPasswordAutocomplete: isSignUp ? "new-password" : "current-password",
  authShellHidden: !checking && (!authEnabled || authorized),
  consoleShellHidden: checking || (authEnabled && !authorized),
  authShellActive: checking || (authEnabled && !authorized),
  authMetaHidden: !authorized,
  authSessionActionsHidden: !authorized,
};
```

- [ ] **Step 4: Export the new helpers and run runtime tests**

Run: `node --test tests/frontend/test_auth_session_runtime.mjs`  
Expected: PASS

- [ ] **Step 5: Commit the runtime helper extraction**

```bash
git add frontend/auth-session-runtime.js tests/frontend/test_auth_session_runtime.mjs
git commit -m "refactor: auth session runtime helper 추가"
```

### Task 3: Wire Auth UI Rendering To Runtime Helpers

**Files:**
- Modify: `frontend/app.js`
- Create: `tests/frontend/test_auth_session_app_integration.mjs`
- Test: `tests/frontend/test_auth_session_runtime.mjs`

- [ ] **Step 1: Add behavioral integration test for `renderAuthUi()`**

Create `tests/frontend/test_auth_session_app_integration.mjs` that extracts `renderAuthUi()` from `frontend/app.js`, evaluates it in a VM, stubs its dependencies, invokes it, and asserts:

```js
assert.equal(context.dom.authSubmitButton.textContent, "계정 등록");
assert.equal(context.dom.authPassword.autocomplete, "new-password");
assert.equal(context.dom.authModeSignUp.classList.toggleCalls[0].value, true);
assert.equal(context.dom.authSessionUserLabel.textContent, "홍길동 · 테스트회사");
assert.equal(runtimeCalls.buildAuthUiViewModel, 1);
assert.equal(runtimeCalls.buildAuthInvitationPreviewViewModel, 1);
assert.equal(runtimeCalls.buildAuthFormFieldViewModel, 1);
```

Use stubs for:
- `requireAuthSessionRuntime()`
- `state`
- `dom`
- `document.body.classList`
- `renderAuthInvitationPreview()` only if absolutely necessary for isolation

- [ ] **Step 2: Run integration test to verify the current gap**

Run: `node --test tests/frontend/test_auth_session_app_integration.mjs`  
Expected: FAIL if `renderAuthUi()` and `syncAuthFormWithInvitationPreview()` still calculate auth form state inline

- [ ] **Step 3: Move app-side auth form display calculation to runtime**

In `frontend/app.js`, replace the inline field-update logic in `syncAuthFormWithInvitationPreview()` with runtime output:

```js
function syncAuthFormWithInvitationPreview() {
  const view = requireAuthSessionRuntime().buildAuthFormFieldViewModel({
    auth: state.auth,
    currentEmail: dom.authEmail?.value || "",
    currentDisplayName: dom.authDisplayName?.value || "",
    currentPassword: dom.authPassword?.value || "",
  });

  if (dom.authEmail) {
    dom.authEmail.value = view.emailValue;
    dom.authEmail.readOnly = view.emailReadOnly;
    dom.authEmail.classList.toggle("is-readonly", view.emailReadOnly);
  }
  if (dom.authDisplayName) {
    dom.authDisplayName.value = view.displayNameValue;
  }
  if (dom.authPassword) {
    dom.authPassword.value = view.passwordValue;
  }
}
```

Keep `renderAuthUi()` in runtime-composition shape and make it explicitly rely on the runtime view-model for labels and submit/autocomplete state.

- [ ] **Step 4: Run auth-focused verification**

Run:

```bash
node --test tests/frontend/test_auth_session_runtime.mjs
node --test tests/frontend/test_auth_session_app_integration.mjs
node --check frontend/app.js
node --check frontend/auth-session-runtime.js
```

Expected: all PASS

- [ ] **Step 5: Commit the app wiring**

```bash
git add frontend/app.js frontend/auth-session-runtime.js tests/frontend/test_auth_session_app_integration.mjs
git commit -m "refactor: auth session runtime 경계 정리"
```

### Task 4: Run Frontend Modularization Regression Verification

**Files:**
- Verify only: `frontend/app.js`
- Verify only: `frontend/auth-session-runtime.js`
- Verify only: `frontend/run-view-runtime.js`
- Verify only: `frontend/tracker-diagnostics-runtime.js`
- Verify only: `frontend/selected-entry-runtime.js`
- Verify only: `frontend/tracker-entry-runtime.js`
- Verify only: `frontend/organization-admin-runtime.js`

- [ ] **Step 1: Run auth session focused tests**

Run:

```bash
node --test tests/frontend/test_auth_session_runtime.mjs
node --test tests/frontend/test_auth_session_app_integration.mjs
```

Expected: all PASS

- [ ] **Step 2: Run existing modularization regression tests**

Run:

```bash
node --test tests/frontend/test_organization_admin_runtime.mjs
node --test tests/frontend/test_organization_admin_app_integration.mjs
node --test tests/frontend/test_run_view_runtime.mjs
node --test tests/frontend/test_tracker_diagnostics_runtime.mjs
node --test tests/frontend/test_selected_entry_runtime.mjs
node --test tests/frontend/test_selected_entry_app_integration.mjs
node --test tests/frontend/test_tracker_entry_runtime.mjs
node --test tests/frontend/test_tracker_entry_app_integration.mjs
node --test tests/frontend/test_tracker_board_runtime.mjs
node --test tests/frontend/test_tracker_board_app_integration.mjs
```

Expected: all PASS

- [ ] **Step 3: Run syntax and worktree checks**

Run:

```bash
node --check frontend/app.js
node --check frontend/auth-session-runtime.js
node --check frontend/run-view-runtime.js
node --check frontend/tracker-diagnostics-runtime.js
node --check frontend/selected-entry-runtime.js
node --check frontend/tracker-entry-runtime.js
node --check frontend/organization-admin-runtime.js
git status --short
```

Expected:
- all `node --check` commands exit 0
- `git status --short` shows only the expected auth-session files plus unrelated pre-existing `related notice` changes

- [ ] **Step 4: If no code changes are needed, report verification complete without creating a commit**

If all verification passes after Task 3, do not create an empty commit. Report the exact command results and note that this task was verification-only.
