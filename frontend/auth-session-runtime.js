(function attachAuthSessionRuntime(global) {
  function normalizeAuthSession(session) {
    const next = session || {};
    return {
      enabled: Boolean(next.enabled),
      checked: true,
      checking: false,
      authenticated: Boolean(next.authenticated),
      authorized: Boolean(next.authorized),
      accessToken: String(next.access_token || ""),
      bootstrapEmail: String(next.bootstrap_email || ""),
      message: String(next.message || ""),
      user: next.user || null,
    };
  }

  function buildInvitationStatusViewModel(message = "", level = "") {
    const text = String(message || "").trim();
    return {
      text,
      hasMessage: Boolean(text),
      isError: level === "error",
    };
  }

  function buildProfileStatusViewModel(message = "", level = "") {
    const text = String(message || "").trim();
    return {
      text,
      hasMessage: Boolean(text),
      isError: level === "error",
    };
  }

  function shouldShowAdminModeToggle(auth = {}) {
    if (!auth?.enabled) {
      return true;
    }
    const role = String(auth?.user?.role || "").trim();
    const isAdmin = role === "platform_admin" || role === "org_admin";
    return Boolean(auth?.authenticated && auth?.authorized && isAdmin);
  }

  function buildAuthInvitationPreviewViewModel(auth = {}, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatOrgRoleLabel = (value) => String(value || ""),
      formatInvitationStatusLabel = (value) => String(value || ""),
      formatSalesDateLabel = (value) => String(value || ""),
    } = helpers;

    const hasInviteContext = Boolean(auth.inviteToken || auth.invitationPreview || auth.invitationPreviewError);
    if (!hasInviteContext) {
      return {
        visible: false,
        html: "",
      };
    }
    if (auth.invitationPreviewLoading) {
      return {
        visible: true,
        html: '<div class="auth-invite-preview-copy">초대 정보를 확인하는 중입니다.</div>',
      };
    }
    if (auth.invitationPreviewError) {
      return {
        visible: true,
        html: `
      <strong>초대 링크 확인 필요</strong>
      <p class="auth-invite-preview-copy">${escapeHtml(auth.invitationPreviewError)}</p>
    `,
      };
    }
    const preview = auth.invitationPreview;
    if (!preview) {
      return {
        visible: true,
        html: '<div class="auth-invite-preview-copy">초대 정보를 찾지 못했습니다.</div>',
      };
    }
    const detailBits = [
      `회사 ${preview.organization_name || "-"}`,
      `역할 ${formatOrgRoleLabel(preview.role || "org_member")}`,
      `이메일 ${preview.email || "-"}`,
    ];
    if (preview.team_name) {
      detailBits.push(`팀 ${preview.team_name}`);
    }
    if (preview.job_title) {
      detailBits.push(`직책 ${preview.job_title}`);
    }
    return {
      visible: true,
      html: `
    <div class="auth-invite-preview-head">
      <strong>${escapeHtml(preview.display_name || preview.email || "초대 사용자")}</strong>
      <span class="status-badge status-${escapeHtml(String(preview.status || "pending"))}">${escapeHtml(formatInvitationStatusLabel(preview.status || "pending"))}</span>
    </div>
    <p class="auth-invite-preview-copy">${escapeHtml(detailBits.join(" · "))}</p>
    <p class="auth-invite-preview-copy">만료 ${escapeHtml(preview.expires_at ? formatSalesDateLabel(preview.expires_at) : "-")}</p>
    ${preview.initial_password ? `<p class="auth-invite-preview-copy">초기 암호 ${escapeHtml(preview.initial_password)}</p>` : ""}
  `,
    };
  }

  function buildAuthFormFieldViewModel({
    auth = {},
    currentEmail = "",
    currentDisplayName = "",
    currentPassword = "",
  } = {}) {
    const preview = auth.invitationPreview || null;
    const rawEmail = String(currentEmail || "");
    const rawDisplayName = String(currentDisplayName || "");
    const rawPassword = String(currentPassword || "");
    const invitedEmail = String(preview?.email || "").trim();
    const displayNameValue = rawDisplayName.trim() ? rawDisplayName : String(preview?.display_name || "").trim();
    const shouldPrefillPassword = auth.mode === "sign_up" && !rawPassword.trim();

    return {
      emailValue: invitedEmail || rawEmail,
      emailReadOnly: Boolean(invitedEmail),
      displayNameValue,
      passwordValue: shouldPrefillPassword ? String(preview?.initial_password || "") : rawPassword,
    };
  }

  function buildAuthSessionActionViewModel(auth = {}, helpers = {}) {
    const {
      formatOrgRoleLabel = (value) => String(value || ""),
    } = helpers;

    if (!auth.user) {
      return {
        userLabel: "",
        roleLabel: "",
        sessionUserLabel: "",
      };
    }

    const displayName = auth.user.display_name || auth.user.email || "-";
    const organizationName = auth.user.organization_name || "-";

    return {
      userLabel: displayName,
      roleLabel: `${formatOrgRoleLabel(auth.user.role || "-")} | ${organizationName}`,
      sessionUserLabel: `${displayName} · ${organizationName}`,
    };
  }

  function buildAuthUiViewModel(auth = {}, helpers = {}) {
    const {
      shouldShowSignUpMode = () => true,
      formatOrgRoleLabel = (value) => String(value || ""),
    } = helpers;

    const authEnabled = Boolean(auth.enabled);
    const authorized = Boolean(auth.authenticated && auth.authorized);
    const checking = Boolean(auth.checking);
    const signUpAllowed = Boolean(shouldShowSignUpMode());
    const isSignUp = signUpAllowed && auth.mode === "sign_up";
    const previewStatus = String(auth?.invitationPreview?.status || "");
    const inviteActionBlocked = Boolean(auth.invitationPreviewError) || ["revoked", "expired"].includes(previewStatus);
    const authCopyText = checking
      ? "현재 인증 세션과 초대 정보를 확인하는 중입니다."
      : auth.inviteToken
      ? "초대받은 이메일로 가입하거나 로그인하면 초대가 자동 수락됩니다."
      : isSignUp
      ? "초대받은 이메일 또는 초기 운영자 계정으로 계정 등록할 수 있습니다."
      : "";
    const authHintText = auth.inviteToken
      ? previewStatus === "accepted"
        ? "이미 수락된 초대입니다. 같은 이메일 계정으로 로그인하면 됩니다."
        : "초대 링크 사용자는 첫 비밀번호 설정과 프로필 입력을 바로 이어서 할 수 있습니다."
      : auth.bootstrapEmail
      ? "초대 메일 클릭 후 이 화면이 보이면 초대받은 이메일을 입력하고 '계정 등록'으로 진행하세요."
      : "초기 운영자 계정이 설정되면 최초 운영자 등록을 진행할 수 있습니다.";
    const status = buildInvitationStatusViewModel(auth.message || "", auth.message && !authorized && auth.authenticated ? "error" : "");
    const sessionActions = buildAuthSessionActionViewModel(auth, { formatOrgRoleLabel });
    const blockedMessage = auth.message || "이 계정은 아직 초대되지 않았습니다.";

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
      showBlocked: authEnabled && auth.authenticated && !auth.authorized,
      blockedMessage,
      ...sessionActions,
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
  }

  function buildProfileDialogViewModel(auth = {}, helpers = {}) {
    const {
      formatOrgRoleLabel = (value) => String(value || ""),
      formatMembershipStatusLabel = (value) => String(value || ""),
    } = helpers;
    const user = auth.user || null;
    const inviteSetupAllowed = Boolean(
      auth.inviteToken
      && auth.invitationPreview
      && String(auth.invitationPreview.status || "") === "accepted",
    );
    return {
      emailValue: user?.email || "",
      displayNameValue: user?.display_name || user?.email || "",
      roleValue: formatOrgRoleLabel(user?.role || "-"),
      organizationValue: user?.organization_name || "-",
      statusValue: formatMembershipStatusLabel(user?.membership_status || user?.status || "active"),
      mobilePhoneValue: user?.mobile_phone || "",
      officePhoneValue: user?.office_phone || "",
      currentPasswordValue: "",
      currentPasswordRequired: !inviteSetupAllowed,
      currentPasswordPlaceholder: inviteSetupAllowed
        ? "초대 링크 첫 비밀번호 설정이면 비워둘 수 있습니다."
        : "회원정보 수정 전에 현재 비밀번호를 입력하세요.",
      passwordValue: "",
      passwordConfirmValue: "",
    };
  }

  function createAuthSessionRefreshController({ cooldownMs = 60_000, nowFn = () => Date.now() } = {}) {
    let inFlightPromise = null;
    let lastCompletedAt = 0;

    return {
      async run(refreshFn, { force = false } = {}) {
        if (typeof refreshFn !== "function") {
          throw new TypeError("refreshFn must be a function");
        }
        if (inFlightPromise) {
          return inFlightPromise;
        }
        const now = Number(nowFn()) || 0;
        if (!force && lastCompletedAt && now - lastCompletedAt < cooldownMs) {
          return null;
        }
        inFlightPromise = (async () => {
          try {
            return await refreshFn();
          } finally {
            lastCompletedAt = Number(nowFn()) || 0;
            inFlightPromise = null;
          }
        })();
        return inFlightPromise;
      },
    };
  }

  global.SPMSAuthSessionRuntime = {
    buildAuthFormFieldViewModel,
    buildAuthInvitationPreviewViewModel,
    buildAuthSessionActionViewModel,
    buildAuthUiViewModel,
    buildInvitationStatusViewModel,
    buildProfileDialogViewModel,
    buildProfileStatusViewModel,
    createAuthSessionRefreshController,
    normalizeAuthSession,
    shouldShowAdminModeToggle,
  };
})(window);
