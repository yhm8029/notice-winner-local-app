(function attachPlatformAdminAccountRuntime(globalObject) {
  function escapeAttribute(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function buildPlatformAdminAccountResultMarkup(item, helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatOrgRoleLabel = (value) => String(value ?? ""),
    } = helpers;
    if (!item || typeof item !== "object") {
      return "";
    }
    const accountStatus = String(item.account_status || "active");
    const membershipStatus = String(item.membership_status || "active");
    return `
      <article class="org-admin-list-item">
        <div class="org-admin-list-item-head">
          <div>
            <strong>${escapeHtml(item.display_name || item.email || "-")}</strong>
            <p class="mono">${escapeHtml(item.email || "-")} | ${escapeHtml(formatOrgRoleLabel(item.role || "org_member"))}</p>
          </div>
          <span class="status-badge status-${escapeHtml(accountStatus)}">${escapeHtml(accountStatus)}</span>
        </div>
        <p class="mono">멤버십 ${escapeHtml(membershipStatus)}</p>
        <p class="mono">비밀번호 설정 ${escapeHtml(String(item.password_setup_mode || "admin_set"))}</p>
      </article>
    `;
  }

  function buildPlatformAdminAccountCardMarkup(state, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    const enabled = Boolean(state?.enabled);
    const currentUserRole = String(state?.currentUserRole || "").trim();
    if (!enabled || currentUserRole !== "platform_admin") {
      return "";
    }
    const saving = Boolean(state?.saving);
    const draft = state?.draft && typeof state.draft === "object" ? state.draft : {};
    const emailValue = escapeAttribute(draft.email || "");
    const displayNameValue = escapeAttribute(draft.display_name || "");
    const passwordValue = escapeAttribute(draft.password || "");
    const roleValue = String(draft.role || "org_member").trim() || "org_member";
    const submitText = saving ? "생성 중..." : "계정 생성";
    const resultMarkup = state?.result
      ? buildPlatformAdminAccountResultMarkup(state.result, helpers)
      : '<div class="hint-text">생성한 계정은 여기서 바로 확인할 수 있습니다.</div>';
    return `
      <article class="runtime-card org-admin-card">
        <div class="runtime-card-head">
          <div>
            <strong>직접 계정 생성</strong>
            <p class="kicker">플랫폼 관리자가 초대 링크 없이 초기 비밀번호를 직접 넣어 계정을 생성합니다.</p>
          </div>
        </div>
        <form id="platform-admin-account-form" class="org-admin-form">
          <input name="email" type="email" placeholder="이메일" value="${emailValue}" required />
          <input name="display_name" type="text" placeholder="표시 이름" value="${displayNameValue}" />
          <select name="role">
            <option value="org_member" ${roleValue === "org_member" ? "selected" : ""}>사용자</option>
            <option value="org_admin" ${roleValue === "org_admin" ? "selected" : ""}>관리자</option>
          </select>
          <input name="password" type="password" placeholder="초기 비밀번호" value="${passwordValue}" required />
          <button
            id="platform-admin-account-submit-button"
            class="primary-button"
            type="submit"
            ${saving ? "disabled" : ""}
          >${escapeHtml(submitText)}</button>
        </form>
        <div id="platform-admin-account-result">${resultMarkup}</div>
      </article>
    `;
  }

  globalObject.SPMSPlatformAdminAccountRuntime = {
    buildPlatformAdminAccountCardMarkup,
    buildPlatformAdminAccountResultMarkup,
  };
})(window);
