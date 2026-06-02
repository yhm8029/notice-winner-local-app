(function attachAppRuntimeBodyRuntime(global) {
  function getTrackerRenderFallbackRuntime() {
    return global.SPMSTrackerRenderFallbackRuntime || null;
  }

  function ensureProjectRelatedAppRuntimeLoaded() {
    if (global.SPMSProjectRelatedAppRuntime || typeof document === "undefined" || !document.head || typeof document.createElement !== "function") return;
    const script = document.createElement("script");
    script.src = "/app/project-related-app-runtime.js?v=20260425a";
    script.defer = false;
    script.async = false;
    script.dataset.spmsProjectRelatedAppRuntime = "true";
    script.onerror = () => console.warn("Failed to load /app/project-related-app-runtime.js");
    document.head.appendChild(script);
  }

  function normalizePlatformAdminAccountDraft(draft) {
    const source = draft && typeof draft === "object" ? draft : {};
    return {
      email: String(source.email || ""),
      display_name: String(source.display_name || ""),
      role: String(source.role || "org_member").trim() || "org_member",
      password: String(source.password || ""),
    };
  }

  function syncPlatformAdminAccountDraftFromForm(state, form) {
    if (typeof HTMLFormElement !== "undefined" && !(form instanceof HTMLFormElement)) {
      return;
    }
    const data = new FormData(form);
    state.platformAdminAccount.draft = normalizePlatformAdminAccountDraft({
      email: data.get("email"),
      display_name: data.get("display_name"),
      role: data.get("role"),
      password: data.get("password"),
    });
  }

  function formatContractAmountInput(rawValue) {
    const digits = String(rawValue || "").replace(/\D+/g, "");
    return digits ? digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "";
  }

  function formatContractAmountDisplay(rawValue, fallback = "-") {
    return formatContractAmountInput(rawValue) || String(rawValue || "").trim() || fallback;
  }

  function openTrackerChangeModal(state, dom, renderTrackerChangeEventsPanel, windowObject) {
    state.trackerChangeModal.open = true;
    dom.trackerChangeModal?.classList.remove("hidden");
    renderTrackerChangeEventsPanel?.();
    windowObject.setTimeout(() => {
      dom.trackerChangeModalCloseButton?.focus();
    }, 0);
  }

  function closeTrackerChangeModal(state, dom) {
    state.trackerChangeModal.open = false;
    dom.trackerChangeModal?.classList.add("hidden");
  }

  function mountParityReportEnhancements(dom, documentObject) {
    const reportPanel = dom.reportSelect?.closest(".panel-report");
    if (!reportPanel || !documentObject) {
      return;
    }
    const heading = reportPanel.querySelector(".panel-heading h2");
    if (heading) {
      heading.textContent = "\uC120\uD0DD\uC801 \uAC80\uC99D";
    }
    const kicker = reportPanel.querySelector(".panel-heading .kicker");
    if (kicker) {
      kicker.textContent = "GUI \uBE44\uAD50 \uB3C4\uAD6C";
    }
    if (dom.runReportButton) {
      dom.runReportButton.textContent = "\uAC80\uC99D \uC2E4\uD589";
    }
    if (dom.refreshReportButton) {
      dom.refreshReportButton.textContent = "\uAC80\uC99D \uC0C8\uB85C\uACE0\uCE68";
    }
    let note = reportPanel.querySelector("#parity-tool-note");
    if (!note) {
      note = documentObject.createElement("div");
      note.id = "parity-tool-note";
      note.className = "tracker-context";
      note.textContent = "\uC774 \uC601\uC5ED\uC740 \uC6B4\uC601 \uD544\uC218 \uAE30\uB2A5\uC774 \uC544\uB2C8\uB77C GUI \uBE44\uAD50 \uAC80\uC99D\uC6A9 \uBCF4\uC870 \uB3C4\uAD6C\uC785\uB2C8\uB2E4.";
      reportPanel.insertBefore(note, dom.reportStatus);
    }
  }

  function renderOrgAdminRuntimeReloadFallback(target) {
    if (!target) {
      return;
    }
    target.innerHTML = '<div class="empty-state">?온?귐딆쁽 ?遺얇늺 ?귐딅꺖??? 筌ㅼ뮇???怨밴묶揶쎛 ?袁⑤뻸??덈뼄. ??덉쨮?⑥쥙臾?????쇰뻻 ?類ㅼ뵥??뤾쉭??</div>';
  }

  function runTypeLabel(runType, runTypeLabels, runViewRuntime) {
    return runViewRuntime?.runTypeLabel(runType, runTypeLabels)
      || runTypeLabels[String(runType || "").trim()]
      || String(runType || "-");
  }

  function isProjectTrackerRun(runType) {
    const raw = String(runType || "").trim();
    return raw === "project_tracker" || raw === "winner_pipeline";
  }

  function useGlobalTrackerEntriesScope() {
    return true;
  }

  global.SPMSAppRuntimeBodyRuntime = {
    EDITABLE_FIELDS: ["project_name", "gross_area_scale", "construction_cost", "demand_org_name", "demand_contact", "client_location", "site_location_1", "site_location_2", "architect_office", "construction_start_date", "last_checked_date", "progress_note", "notice_date", "manager_name", "building_automation_estimated_amount"],
    RUN_TYPE_LABELS: { project_tracker: "공고 추적", winner_pipeline: "공고 추적", tracker_export: "트래커 내보내기" },
    TRACKER_REGION_OPTIONS: [{ value: "", label: "전체" }, { value: "서울", label: "서울" }, { value: "부산", label: "부산" }, { value: "대구", label: "대구" }, { value: "인천", label: "인천" }, { value: "광주", label: "광주" }, { value: "대전", label: "대전" }, { value: "울산", label: "울산" }, { value: "세종", label: "세종" }, { value: "경기", label: "경기" }, { value: "강원", label: "강원" }, { value: "충북", label: "충북" }, { value: "충남", label: "충남" }, { value: "전북", label: "전북" }, { value: "전남", label: "전남" }, { value: "경북", label: "경북" }, { value: "경남", label: "경남" }, { value: "제주", label: "제주" }],
    TRACKER_BOARD_COLUMNS: [{ key: "display_no", label: "NO.", editable: false }, { key: "project_name", label: "프로젝트명", editable: true }, { key: "gross_area_scale", label: "연면적/규모", editable: true }, { key: "construction_cost", label: "공사비", editable: true }, { key: "demand_org_name", label: "수요기관명", editable: true }, { key: "demand_contact", label: "부서/담당자", editable: true }, { key: "client_location", label: "발주처 위치", editable: true }, { key: "site_location_1", label: "현장 위치", editable: true }, { key: "architect_office", label: "설계사무소", editable: true }, { key: "construction_start_date", label: "착공일", editable: true }, { key: "last_checked_date", label: "최종점검일자", editable: true }, { key: "progress_note", label: "주요진행사항", editable: true }, { key: "notice_date", label: "공고일", editable: true }, { key: "building_automation_estimated_amount", label: "빌딩자동제어 추정 금액", editable: true }],
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS: new Set(["demand_contact", "architect_office", "construction_start_date"]),
    TRACKER_CHANGE_FIELD_LABELS: { gross_area_scale: "연면적", construction_cost: "공사비", demand_contact: "담당 연락처" },
    ORG_ROLE_OPTIONS: ["org_admin", "org_member"],
    MEMBERSHIP_STATUS_OPTIONS: ["active", "inactive", "deactivated"],
    TRACKER_BOARD_TEXTAREA_FIELDS: new Set(["project_name", "progress_note"]),
    AUTH_MODE_SIGN_IN: "sign_in",
    AUTH_MODE_SIGN_UP: "sign_up",
    AUTH_SESSION_HEARTBEAT_MS: 15 * 60 * 1000,
    AUTH_SESSION_RECHECK_COOLDOWN_MS: 60 * 1000,
    PROJECT_RELATED_PREFETCH_LIMIT: 3,
    TRACKER_DETAIL_PREFETCH_LIMIT: 3,
    PROJECT_RELATED_READY_CACHE_TTL_MS: 5 * 60 * 1000,
    PROJECT_RELATED_SEED_CACHE_TTL_MS: 60 * 1000,
    PROJECT_RELATED_STORAGE_KEY: "notice-winner-pipeline-web.projectRelatedCache.v1",
    PROJECT_RELATED_STORAGE_MAX_ITEMS: 80,
    SALES_OVERVIEW_STORAGE_KEY: "notice-winner-pipeline-web.salesOverview.v1",
    HOME_BOOTSTRAP_STORAGE_KEY: "notice-winner-pipeline-web.homeBootstrap.v6",
    ORG_ADMIN_BOOTSTRAP_STORAGE_KEY: "notice-winner-pipeline-web.orgAdminBootstrap.v1",
    TRACKER_CHANGE_EVENTS_STORAGE_KEY: "notice-winner-pipeline-web.trackerChangeEvents.v1",
    TRACKER_CHANGE_EVENTS_STORAGE_MAX_ITEMS: 6,
    TRACKER_CHANGE_EVENTS_CACHE_TTL_MS: 60 * 1000,
    APP_ROOT_PATH: "/",
    DEFAULT_ADMIN_TAB: "project-status",
    ADMIN_TABS: [
      { key: "project-status", label: "공고 추적", routePath: "/", type: "existing", subtitle: "공고 추적 실행과 결과 화면" },
    ],
    LEGACY_ADMIN_ROUTE_ALIASES: Object.freeze({ "/app/design-list": { legacyRoutePath: "/app/design-list", labelHint: "설계리스트" }, "/app/planned-orders": { legacyRoutePath: "/app/planned-orders", labelHint: "발주예정" }, "/app/lost": { legacyRoutePath: "/app/lost", labelHint: "LOST" }, "/app/agency-list": { legacyRoutePath: "/app/agency-list", labelHint: "대리점 리스트" } }),
    getTrackerRenderFallbackRuntime,
    ensureProjectRelatedAppRuntimeLoaded,
    normalizePlatformAdminAccountDraft,
    syncPlatformAdminAccountDraftFromForm,
    formatContractAmountInput,
    formatContractAmountDisplay,
    openTrackerChangeModal,
    closeTrackerChangeModal,
    mountParityReportEnhancements,
    renderOrgAdminRuntimeReloadFallback,
    runTypeLabel,
    isProjectTrackerRun,
    useGlobalTrackerEntriesScope,
  };
})(typeof window !== "undefined" ? window : globalThis);
