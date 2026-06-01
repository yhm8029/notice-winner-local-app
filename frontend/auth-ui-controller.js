export function createAuthUiController(deps = {}) {
  const AUTH_MODE_SIGN_IN = deps.AUTH_MODE_SIGN_IN || "sign_in";
  const AUTH_MODE_SIGN_UP = deps.AUTH_MODE_SIGN_UP || "sign_up";

  function requireFunction(name) {
    const fn = deps[name];
    if (typeof fn !== "function") {
      throw new Error(`auth ui controller dependency is missing: ${name}`);
    }
    return fn;
  }

  function requireAuthSessionRuntime() {
    return requireFunction("requireAuthSessionRuntime")();
  }

  function isBootstrapEmail(email) {
    const bootstrapEmail = String(deps.state.auth.bootstrapEmail || "").trim().toLowerCase();
    const normalizedEmail = String(email || "").trim().toLowerCase();
    return Boolean(bootstrapEmail && normalizedEmail && bootstrapEmail === normalizedEmail);
  }

  function normalizeAuthErrorMessage(rawMessage, { isSignUp = false, email = "" } = {}) {
    const message = String(rawMessage || "").trim();
    const lowered = message.toLowerCase();
    if (lowered.includes("invalid_credentials")) {
      if (isSignUp && isBootstrapEmail(email)) {
        return "이미 생성된 운영자 계정입니다. 비밀번호 재설정을 사용하거나 기존 비밀번호로 로그인하세요.";
      }
      return "이메일 또는 비밀번호가 올바르지 않습니다.";
    }
    return message || "인증에 실패했습니다.";
  }

  function syncAuthFormWithInvitationPreview() {
    const fieldView = requireAuthSessionRuntime().buildAuthFormFieldViewModel({
      auth: deps.state.auth,
      currentEmail: deps.dom.authEmail?.value || "",
      currentDisplayName: deps.dom.authDisplayName?.value || "",
      currentPassword: deps.dom.authPassword?.value || "",
    });
    if (deps.dom.authEmail) {
      deps.dom.authEmail.readOnly = fieldView.emailReadOnly;
      deps.dom.authEmail.classList.toggle("is-readonly", fieldView.emailReadOnly);
      if (fieldView.emailReadOnly && deps.dom.authEmail.value !== fieldView.emailValue) {
        deps.dom.authEmail.value = fieldView.emailValue;
      }
    }
    if (deps.dom.authDisplayName && !String(deps.dom.authDisplayName.value || "").trim() && fieldView.displayNameValue) {
      deps.dom.authDisplayName.value = fieldView.displayNameValue;
    }
    if (deps.dom.authPassword && !String(deps.dom.authPassword.value || "").trim() && fieldView.passwordValue) {
      deps.dom.authPassword.value = fieldView.passwordValue;
    }
  }

  function renderAuthInvitationPreview() {
    if (!deps.dom.authInvitePreview) {
      return;
    }
    const preview = requireAuthSessionRuntime().buildAuthInvitationPreviewViewModel(deps.state.auth, {
      escapeHtml: deps.escapeHtml,
      formatOrgRoleLabel: deps.formatOrgRoleLabel,
      formatInvitationStatusLabel: deps.formatInvitationStatusLabel,
      formatSalesDateLabel: deps.formatSalesDateLabel,
    });
    if (!preview.visible) {
      deps.dom.authInvitePreview.classList.add("hidden");
      deps.dom.authInvitePreview.innerHTML = "";
      return;
    }
    deps.dom.authInvitePreview.classList.remove("hidden");
    deps.dom.authInvitePreview.innerHTML = preview.html;
  }

  function renderAuthUi() {
    const authView = requireAuthSessionRuntime().buildAuthUiViewModel(deps.state.auth, {
      shouldShowSignUpMode: deps.shouldShowSignUpMode,
      formatOrgRoleLabel: deps.formatOrgRoleLabel,
    });
    deps.document.body.classList.toggle("auth-shell-active", authView.authShellActive);
    deps.dom.authShell.classList.toggle("hidden", authView.authShellHidden);
    deps.dom.consoleShell.classList.toggle("hidden", authView.consoleShellHidden);

    if (!authView.authEnabled) {
      deps.dom.authMetaCard.classList.add("hidden");
      deps.dom.authSessionActions?.classList.add("hidden");
      return;
    }

    if (!authView.signUpAllowed && deps.state.auth.mode === AUTH_MODE_SIGN_UP) {
      deps.state.auth.mode = AUTH_MODE_SIGN_IN;
    }
    syncAuthFormWithInvitationPreview();
    deps.dom.authModeSignIn.classList.toggle("is-active", authView.authModeSignInActive);
    deps.dom.authModeSignUp.classList.toggle("is-active", authView.authModeSignUpActive);
    deps.dom.authModeSignUp.classList.toggle("hidden", !authView.signUpAllowed);
    if (deps.dom.authModeSignUp) {
      deps.dom.authModeSignUp.textContent = "계정 등록";
    }
    deps.dom.authDisplayNameField.classList.toggle("hidden", authView.authDisplayNameHidden);
    deps.dom.authSubmitButton.textContent = authView.authSubmitText;
    deps.dom.authSubmitButton.disabled = authView.checking || authView.inviteActionBlocked;
    deps.dom.authPassword.autocomplete = authView.authPasswordAutocomplete;
    deps.dom.authCopy.textContent = authView.authCopyText;
    deps.dom.authHint.textContent = authView.authHintText;
    renderAuthInvitationPreview();

    if (authView.status.hasMessage) {
      deps.dom.authStatus.textContent = authView.status.text;
      deps.dom.authStatus.classList.remove("hidden", "error");
      if (authView.status.isError) {
        deps.dom.authStatus.classList.add("error");
      }
    } else {
      deps.dom.authStatus.classList.add("hidden");
    }

    deps.dom.authUserBlocked.classList.toggle("hidden", !authView.showBlocked);
    deps.dom.authBlockedMessage.textContent = authView.blockedMessage;

    deps.dom.authMetaCard.classList.toggle("hidden", authView.authMetaHidden);
    deps.dom.authSessionActions?.classList.toggle("hidden", authView.authSessionActionsHidden);
    if (authView.authorized && deps.state.auth.user) {
      deps.dom.authUserLabel.textContent = authView.userLabel || "-";
      deps.dom.authRoleLabel.textContent = authView.roleLabel || "-";
      if (deps.dom.authSessionUserLabel) {
        deps.dom.authSessionUserLabel.textContent = authView.sessionUserLabel || "-";
      }
    }
  }

  function renderProfileStatus(message = "", level = "") {
    if (!deps.dom.profileStatusMessage) {
      return;
    }
    const statusView = requireAuthSessionRuntime().buildProfileStatusViewModel(message, level);
    deps.dom.profileStatusMessage.textContent = statusView.text;
    deps.dom.profileStatusMessage.classList.toggle("hidden", !statusView.hasMessage);
    deps.dom.profileStatusMessage.classList.toggle("error", statusView.isError);
  }

  function syncProfileDialogWithSession() {
    if (!deps.state.auth.user) {
      return;
    }
    const profileView = requireAuthSessionRuntime().buildProfileDialogViewModel(deps.state.auth, {
      formatOrgRoleLabel: deps.formatOrgRoleLabel,
      formatMembershipStatusLabel: deps.formatMembershipStatusLabel,
    });
    if (deps.dom.profileEmail) {
      deps.dom.profileEmail.value = profileView.emailValue;
    }
    if (deps.dom.profileDisplayName) {
      deps.dom.profileDisplayName.value = profileView.displayNameValue;
    }
    if (deps.dom.profileRole) {
      deps.dom.profileRole.value = profileView.roleValue;
    }
    if (deps.dom.profileOrganization) {
      deps.dom.profileOrganization.value = profileView.organizationValue;
    }
    if (deps.dom.profileStatus) {
      deps.dom.profileStatus.value = profileView.statusValue;
    }
    if (deps.dom.profileMobilePhone) {
      deps.dom.profileMobilePhone.value = profileView.mobilePhoneValue;
    }
    if (deps.dom.profileOfficePhone) {
      deps.dom.profileOfficePhone.value = profileView.officePhoneValue;
    }
    if (deps.dom.profileCurrentPassword) {
      deps.dom.profileCurrentPassword.value = profileView.currentPasswordValue;
      deps.dom.profileCurrentPassword.required = profileView.currentPasswordRequired;
      deps.dom.profileCurrentPassword.placeholder = profileView.currentPasswordPlaceholder;
    }
    if (deps.dom.profilePassword) {
      deps.dom.profilePassword.value = profileView.passwordValue;
    }
    if (deps.dom.profilePasswordConfirm) {
      deps.dom.profilePasswordConfirm.value = profileView.passwordConfirmValue;
    }
    renderProfileStatus("", "");
  }

  function openProfileDialog() {
    if (!deps.state.auth.authenticated || !deps.state.auth.authorized || !deps.state.auth.user || !deps.dom.profileDialog) {
      return;
    }
    deps.state.profileDialog.open = true;
    syncProfileDialogWithSession();
    deps.dom.profileDialog.classList.remove("hidden");
    deps.window.setTimeout(() => {
      deps.dom.profileCurrentPassword?.focus();
    }, 0);
  }

  function closeProfileDialog() {
    deps.state.profileDialog.open = false;
    deps.state.profileDialog.saving = false;
    deps.dom.profileDialog?.classList.add("hidden");
    if (deps.dom.profileForm) {
      deps.dom.profileForm.reset();
    }
    renderProfileStatus("", "");
  }

  async function handleProfileSubmit(event) {
    event.preventDefault();
    if (!deps.state.auth.authenticated || !deps.state.auth.authorized || !deps.state.auth.user) {
      return;
    }
    const setBusy = requireFunction("setBusy");
    const api = requireFunction("api");
    const flash = requireFunction("flash");
    const loadOrganizationUsers = requireFunction("loadOrganizationUsers");
    const loadOrganizationMembers = requireFunction("loadOrganizationMembers");
    const loadSalesOverview = requireFunction("loadSalesOverview");
    const loadMySalesClaims = requireFunction("loadMySalesClaims");
    const refreshSalesAdminPanels = requireFunction("refreshSalesAdminPanels");
    const displayName = String(deps.dom.profileDisplayName?.value || "").trim();
    const mobilePhone = String(deps.dom.profileMobilePhone?.value || "").trim();
    const officePhone = String(deps.dom.profileOfficePhone?.value || "").trim();
    const currentPassword = String(deps.dom.profileCurrentPassword?.value || "");
    const password = String(deps.dom.profilePassword?.value || "");
    const passwordConfirm = String(deps.dom.profilePasswordConfirm?.value || "");
    const invitePasswordSetupAllowed = Boolean(deps.state.auth.inviteToken && deps.state.auth.invitationPreview && String(deps.state.auth.invitationPreview.status || "") === "accepted");
    if (!currentPassword && !invitePasswordSetupAllowed) {
      renderProfileStatus("회원정보를 수정하려면 현재 비밀번호를 입력해야 한다.", "error");
      deps.dom.profileCurrentPassword?.focus();
      return;
    }
    if (!displayName) {
      renderProfileStatus("표시 이름을 입력해야 한다.", "error");
      deps.dom.profileDisplayName?.focus();
      return;
    }
    if (password || passwordConfirm) {
      if (password !== passwordConfirm) {
        renderProfileStatus("새 비밀번호와 확인 값이 다르다.", "error");
        deps.dom.profilePasswordConfirm?.focus();
        return;
      }
      if (password.length < 8) {
        renderProfileStatus("새 비밀번호는 8자 이상이어야 한다.", "error");
        deps.dom.profilePassword?.focus();
        return;
      }
    }

    deps.state.profileDialog.saving = true;
    renderProfileStatus("", "");
    setBusy(deps.dom.profileSaveButton, true, "저장 중...");
    try {
      const session = await api("/api/auth/profile", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: displayName,
          mobile_phone: mobilePhone,
          office_phone: officePhone,
          current_password: currentPassword,
          password,
          invite_token: deps.state.auth.inviteToken || "",
        }),
        cacheBust: false,
        timeoutMs: 20000,
      });
      applyAuthSession(session);
      if (deps.state.consoleInitialized) {
        if (deps.state.uiMode === "admin") {
          void loadOrganizationUsers({ silent: true });
        }
        void loadOrganizationMembers({ silent: true });
        if (deps.state.uiMode === "user") {
          void loadSalesOverview({ silent: true, force: true });
        } else {
          void loadMySalesClaims({ silent: true });
        }
        if (deps.state.uiMode === "admin") {
          void refreshSalesAdminPanels({ silent: true });
        }
      }
      closeProfileDialog();
      flash("회원정보를 저장했습니다.");
    } catch (err) {
      renderProfileStatus(err.message || "회원정보를 저장하지 못했습니다.", "error");
    } finally {
      deps.state.profileDialog.saving = false;
      setBusy(deps.dom.profileSaveButton, false, "저장");
    }
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    if (deps.state.auth.mode === AUTH_MODE_SIGN_UP && !deps.shouldShowSignUpMode()) {
      deps.state.auth.message = "초대 링크가 있거나 초기 운영자 계정일 때만 계정 등록할 수 있습니다.";
      renderAuthUi();
      return;
    }
    const payload = {
      email: String(deps.dom.authEmail.value || "").trim(),
      password: String(deps.dom.authPassword.value || "").trim(),
      display_name: String(deps.dom.authDisplayName.value || "").trim(),
      invite_token: deps.state.auth.inviteToken || "",
    };
    const isSignUp = deps.state.auth.mode === AUTH_MODE_SIGN_UP;
    const endpoint = isSignUp ? "/api/auth/sign-up" : "/api/auth/sign-in";
    const originalLabel = deps.dom.authSubmitButton.textContent || "로그인";
    deps.setBusy(deps.dom.authSubmitButton, true, isSignUp ? "등록 중..." : "로그인 중...");
    try {
      const session = await deps.api(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
        cacheBust: false,
        timeoutMs: 20000,
      });
      applyAuthSession(session);
      if (deps.state.auth.authenticated && deps.state.auth.authorized) {
        await requireFunction("ensureConsoleInitialized")();
      }
    } catch (err) {
      const errorMessage = normalizeAuthErrorMessage(err.message, {
        isSignUp,
        email: payload.email,
      });
      if (!isSignUp && isBootstrapEmail(payload.email) && errorMessage.includes("bootstrap")) {
        deps.state.auth.message = "초기 운영자 계정 비밀번호가 맞지 않습니다. '계정 등록' 탭에서 같은 이메일로 새 비밀번호를 다시 설정하세요.";
      } else {
        deps.state.auth.message = errorMessage;
      }
      renderAuthUi();
    } finally {
      deps.setBusy(deps.dom.authSubmitButton, false, originalLabel);
    }
  }

  function handleAuthFindId() {
    deps.state.auth.message = "로그인 아이디는 초대 또는 계정 등록에 사용한 이메일입니다. 기억나지 않으면 회사 관리자에게 확인하세요.";
    renderAuthUi();
  }

  async function handleAuthPasswordReset() {
    const email = String(deps.dom.authEmail?.value || "").trim();
    if (!email) {
      deps.state.auth.message = "비밀번호 재설정 메일을 받을 이메일을 먼저 입력하세요.";
      renderAuthUi();
      return;
    }
    const originalLabel = deps.dom.authResetPasswordButton?.textContent || "비밀번호 재설정";
    if (deps.dom.authResetPasswordButton) {
      deps.setBusy(deps.dom.authResetPasswordButton, true, "전송 중...");
    }
    try {
      const result = await deps.api("/api/auth/password-reset", {
        method: "POST",
        body: JSON.stringify({ email }),
        cacheBust: false,
        timeoutMs: 20000,
      });
      deps.state.auth.message = result.message || "비밀번호 재설정 안내를 전송했습니다.";
    } catch (err) {
      deps.state.auth.message = err.message || "비밀번호 재설정을 시작하지 못했습니다.";
    } finally {
      if (deps.dom.authResetPasswordButton) {
        deps.setBusy(deps.dom.authResetPasswordButton, false, originalLabel);
      }
      renderAuthUi();
    }
  }

  async function handleAuthSignOut() {
    closeProfileDialog();
    try {
      await deps.api("/api/auth/sign-out", {
        method: "POST",
        body: JSON.stringify({}),
        cacheBust: false,
        timeoutMs: 10000,
      });
    } catch (_err) {
      // Ignore logout failures and reset the local shell anyway.
    }
    deps.state.auth.authenticated = false;
    deps.state.auth.authorized = false;
    deps.state.auth.user = null;
    deps.state.auth.message = "";
    deps.state.organizationUsers = [];
    deps.state.organizationUsersError = "";
    deps.state.organizationMembers = [];
    deps.state.organizationMembersError = "";
    deps.state.organizationPlanSummary = null;
    deps.state.organizationInvitations = [];
    deps.state.organizationInvitationsError = "";
    deps.state.organizationAuditLogs = [];
    deps.state.organizationAuditLogsLoading = false;
    deps.state.organizationAuditLogsError = "";
    deps.state.organizationAuditLogsLimit = 5;
    deps.state.organizationAuditLogsHasMore = false;
    deps.state.organizationDownloadAuditLogs = [];
    deps.state.organizationDownloadAuditLogsLoading = false;
    deps.state.organizationDownloadAuditLogsError = "";
    deps.state.organizationDownloadAuditLogsLimit = 5;
    deps.state.organizationDownloadAuditLogsHasMore = false;
    deps.state.organizationLoginAuditLogs = [];
    deps.state.organizationLoginAuditLogsLoading = false;
    deps.state.organizationLoginAuditLogsError = "";
    deps.state.organizationLoginAuditLogsLimit = 5;
    deps.state.organizationLoginAuditLogsHasMore = false;
    deps.state.platformAdminAccount = {
      saving: false,
      result: null,
      draft: {
        email: "",
        display_name: "",
        role: "org_member",
        password: "",
      },
      resetStateByUserId: {},
    };
    deps.state.memberSaveStateByUserId = {};
    deps.state.mySalesClaims = [];
    deps.state.companySalesClaims = [];
    deps.state.mySalesClaimsError = "";
    deps.state.salesSummaryByUser = [];
    deps.state.salesSummaryError = "";
    deps.state.salesClosedClaims = [];
    deps.state.salesClosedError = "";
    deps.state.consoleInitialized = false;
    if (deps.state.runsHandle) {
      deps.window.clearInterval(deps.state.runsHandle);
      deps.state.runsHandle = null;
    }
    if (deps.state.authSessionHandle) {
      deps.window.clearInterval(deps.state.authSessionHandle);
      deps.state.authSessionHandle = null;
    }
    deps.window.location.reload();
  }

  function applyAuthSession(session) {
    const previousUiMode = deps.state.uiMode;
    const normalized = requireAuthSessionRuntime().normalizeAuthSession(session);
    deps.state.auth.enabled = normalized.enabled;
    deps.state.auth.checked = normalized.checked;
    deps.state.auth.checking = normalized.checking;
    deps.state.auth.authenticated = normalized.authenticated;
    deps.state.auth.authorized = normalized.authorized;
    deps.state.auth.accessToken = normalized.accessToken;
    deps.state.auth.bootstrapEmail = normalized.bootstrapEmail;
    deps.state.auth.message = normalized.message;
    deps.state.auth.user = normalized.user;
    if (deps.state.auth.user && deps.state.auth.user.display_name && deps.dom.patchActorLabel) {
      deps.dom.patchActorLabel.value = deps.state.auth.user.display_name;
    }
    if (typeof deps.syncUiModeFromLocation === "function") {
      deps.syncUiModeFromLocation();
    }
    renderAuthUi();
    const adminMode = requireFunction("syncUiModeChrome")();
    if (deps.state.consoleInitialized && previousUiMode === "admin" && !adminMode) {
      requireFunction("applyUiModeTransition")(adminMode, { renderAuth: false });
    }
  }

  return {
    applyAuthSession,
    renderAuthInvitationPreview,
    renderAuthUi,
    renderProfileStatus,
    syncAuthFormWithInvitationPreview,
    syncProfileDialogWithSession,
    openProfileDialog,
    closeProfileDialog,
    handleProfileSubmit,
    handleAuthSubmit,
    handleAuthFindId,
    handleAuthPasswordReset,
    handleAuthSignOut,
  };
}

const authUiControllerRoot = typeof window !== "undefined" ? window : globalThis;
authUiControllerRoot.AUTH_UI_CONTROLLER = authUiControllerRoot.AUTH_UI_CONTROLLER || {};
authUiControllerRoot.AUTH_UI_CONTROLLER.createAuthUiController = createAuthUiController;
