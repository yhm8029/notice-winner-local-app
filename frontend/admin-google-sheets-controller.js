function createAdminGoogleSheetsController(deps = {}) {
  const state = deps.state || {};
  const windowObject = deps.window || (typeof window !== "undefined" ? window : globalThis);
  const defaultNoop = function noop() {};
  const api = typeof deps.api === "function" ? deps.api : async function missingApi() {
    throw new Error("api is required");
  };
  const flash = typeof deps.flash === "function" ? deps.flash : defaultNoop;
  const renderAdminTopNavigation = typeof deps.renderAdminTopNavigation === "function" ? deps.renderAdminTopNavigation : defaultNoop;
  const renderAdminEmbedPanel = typeof deps.renderAdminEmbedPanel === "function" ? deps.renderAdminEmbedPanel : defaultNoop;
  const canLoadProtectedConsoleData = typeof deps.canLoadProtectedConsoleData === "function"
    ? deps.canLoadProtectedConsoleData
    : function defaultCanLoadProtectedConsoleData() {
      return true;
    };
  const maybeResolveLegacyAdminAliasToSheetTab = typeof deps.maybeResolveLegacyAdminAliasToSheetTab === "function"
    ? deps.maybeResolveLegacyAdminAliasToSheetTab
    : defaultNoop;
  const getValidatedActiveAdminGoogleSheetTab = typeof deps.getValidatedActiveAdminGoogleSheetTab === "function"
    ? deps.getValidatedActiveAdminGoogleSheetTab
    : function defaultGetValidatedActiveAdminGoogleSheetTab() {
      return null;
    };
  const isAdminGoogleSheetTabKey = typeof deps.isAdminGoogleSheetTabKey === "function"
    ? deps.isAdminGoogleSheetTabKey
    : function defaultIsAdminGoogleSheetTabKey(value) {
      return String(value || "").trim().startsWith("sheet-");
    };
  const isPendingLegacyAdminAlias = typeof deps.isPendingLegacyAdminAlias === "function"
    ? deps.isPendingLegacyAdminAlias
    : function defaultIsPendingLegacyAdminAlias() {
      return false;
    };
  const clearAdminGoogleSheetPopupStateForTab = typeof deps.clearAdminGoogleSheetPopupStateForTab === "function"
    ? deps.clearAdminGoogleSheetPopupStateForTab
    : defaultNoop;
  const syncUrlState = typeof deps.syncUrlState === "function" ? deps.syncUrlState : defaultNoop;
  const applyUiMode = typeof deps.applyUiMode === "function" ? deps.applyUiMode : defaultNoop;
  const persistAdminGoogleSheetsCache = typeof deps.persistAdminGoogleSheetsCache === "function"
    ? deps.persistAdminGoogleSheetsCache
    : defaultNoop;
  const googleSheetsRuntime = deps.googleSheetsRuntime || null;
  const defaultAdminTab = String(deps.defaultAdminTab || "project-status").trim() || "project-status";

  function getAdminGoogleSheetsSyncFollowupDelaysMs() {
    if (typeof windowObject !== "undefined" && windowObject.__SPMS_TEST_MODE__) {
      return [5, 10, 20];
    }
    return [1500, 3000, 6000, 10000, 15000];
  }

  function cancelAdminGoogleSheetsSyncFollowup() {
    if (state.adminGoogleSheetsSyncFollowupHandle) {
      windowObject.clearTimeout(state.adminGoogleSheetsSyncFollowupHandle);
      state.adminGoogleSheetsSyncFollowupHandle = null;
    }
    state.adminGoogleSheetsSyncFollowupStep = 0;
  }

  function shouldAttemptAdminGoogleSheetsSyncFollowup() {
    if (!googleSheetsRuntime) {
      return false;
    }
    if (!canLoadProtectedConsoleData()) {
      return false;
    }
    return state.uiMode === "admin" && (isAdminGoogleSheetTabKey(state.adminTab) || isPendingLegacyAdminAlias());
  }

  async function loadAdminGoogleSheetsBootstrap({ silent = false, force = false } = {}) {
    if (!googleSheetsRuntime) {
      return;
    }
    if (!canLoadProtectedConsoleData()) {
      return;
    }
    if (state.adminGoogleSheetsBootstrapLoading) {
      return;
    }
    if (state.adminGoogleSheetsBootstrap && !force) {
      return;
    }
    state.adminGoogleSheetsBootstrapLoading = true;
    state.adminGoogleSheetsBootstrapError = "";
    try {
      const response = await api("/api/admin/google-sheets/bootstrap", { timeoutMs: 12000 });
      state.adminGoogleSheetsBootstrap = response && typeof response === "object" ? response : {};
      state.adminGoogleSheetTabs = googleSheetsRuntime.buildAdminGoogleSheetTabs(state.adminGoogleSheetsBootstrap);
      persistAdminGoogleSheetsCache();

      // A forced bootstrap refresh implies the underlying snapshot may have changed; treat prior sheet payloads as stale.
      if (force) {
        state.adminGoogleSheetsPayloadEpoch = Number(state.adminGoogleSheetsPayloadEpoch || 0) + 1;
      }

      if (state.adminLegacyRoutePath && state.adminTab === defaultAdminTab) {
        if (maybeResolveLegacyAdminAliasToSheetTab({ historyMode: "replace" })) {
          applyUiMode();
          return;
        }
      }

      const syncStatus = String(state.adminGoogleSheetsBootstrap?.sync_status || "").trim().toLowerCase();
      const bootstrapInitializing = syncStatus === "initializing";
      const shouldFallbackToProjectStatus = (
        isAdminGoogleSheetTabKey(state.adminTab)
        && !state.adminGoogleSheetTabs.some((tab) => tab.key === state.adminTab)
        && !bootstrapInitializing
      );
      if (shouldFallbackToProjectStatus) {
        clearAdminGoogleSheetPopupStateForTab(defaultAdminTab, { render: false });
        state.adminTab = defaultAdminTab;
        syncUrlState({ historyMode: "replace", uiMode: state.uiMode, adminTab: state.adminTab });
        applyUiMode();
      }
      renderAdminTopNavigation();
      renderAdminEmbedPanel();
      if (force) {
        const validatedSheetTab = getValidatedActiveAdminGoogleSheetTab();
        if (validatedSheetTab) {
          await loadAdminGoogleSheetPayload(validatedSheetTab.key, { silent, force: true });
        }
      }
    } catch (err) {
      state.adminGoogleSheetsBootstrapError = err.message || "Failed to load admin Google Sheets bootstrap.";
      if (!silent) {
        flash(state.adminGoogleSheetsBootstrapError, "error");
      }
    } finally {
      state.adminGoogleSheetsBootstrapLoading = false;
      if (state.adminGoogleSheetsBootstrapError) {
        renderAdminEmbedPanel();
      }
    }
  }

  async function loadAdminGoogleSheetPayload(sheetKey, { silent = false, force = false } = {}) {
    if (!googleSheetsRuntime) {
      return;
    }
    if (!canLoadProtectedConsoleData()) {
      return;
    }
    const key = String(sheetKey || "").trim();
    if (!isAdminGoogleSheetTabKey(key)) {
      return;
    }
    if (typeof deps.shouldDeferAdminGoogleSheetPayloadLoad === "function" && deps.shouldDeferAdminGoogleSheetPayloadLoad(key, { force })) {
      return;
    }
    if (state.adminGoogleSheetPayloadLoadingByKey[key]) {
      return;
    }
    const cachedPayload = state.adminGoogleSheetPayloadByKey[key];
    const cachedEpoch = Number(state.adminGoogleSheetPayloadEpochByKey[key] || 0);
    const currentEpoch = Number(state.adminGoogleSheetsPayloadEpoch || 0);
    if (cachedPayload && !force && cachedEpoch === currentEpoch) {
      return;
    }
    state.adminGoogleSheetPayloadLoadingByKey[key] = true;
    state.adminGoogleSheetPayloadErrorByKey[key] = "";
    try {
      const response = await api(`/api/admin/google-sheets/sheets/${encodeURIComponent(key)}`, {
        timeoutMs: 20000,
        cacheBust: false,
      });
      state.adminGoogleSheetPayloadByKey[key] = response && typeof response === "object" ? response : {};
      state.adminGoogleSheetPayloadEpochByKey[key] = currentEpoch;
      persistAdminGoogleSheetsCache();
    } catch (err) {
      state.adminGoogleSheetPayloadErrorByKey[key] = err.message || "Failed to load admin Google Sheet payload.";
      if (!silent) {
        flash(state.adminGoogleSheetPayloadErrorByKey[key], "error");
      }
    } finally {
      state.adminGoogleSheetPayloadLoadingByKey[key] = false;
      renderAdminEmbedPanel();
    }
  }

  function scheduleAdminGoogleSheetsSyncFollowup() {
    cancelAdminGoogleSheetsSyncFollowup();
    const delays = getAdminGoogleSheetsSyncFollowupDelaysMs();

    const scheduleNext = () => {
      if (state.adminGoogleSheetsSyncFollowupStep >= delays.length) {
        cancelAdminGoogleSheetsSyncFollowup();
        return;
      }
      if (!shouldAttemptAdminGoogleSheetsSyncFollowup()) {
        cancelAdminGoogleSheetsSyncFollowup();
        renderAdminEmbedPanel();
        return;
      }
      const delay = delays[state.adminGoogleSheetsSyncFollowupStep];
      state.adminGoogleSheetsSyncFollowupHandle = windowObject.setTimeout(async () => {
        state.adminGoogleSheetsSyncFollowupHandle = null;
        if (!shouldAttemptAdminGoogleSheetsSyncFollowup()) {
          cancelAdminGoogleSheetsSyncFollowup();
          renderAdminEmbedPanel();
          return;
        }
        if (state.adminGoogleSheetsBootstrapLoading) {
          // Don't burn a follow-up attempt while an earlier refresh is still in flight.
          scheduleNext();
          return;
        }
        state.adminGoogleSheetsSyncFollowupStep += 1;
        await loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
        scheduleNext();
      }, delay);
    };

    scheduleNext();
  }

  async function syncAdminGoogleSheets({ silent = false } = {}) {
    if (!googleSheetsRuntime) {
      return;
    }
    if (!canLoadProtectedConsoleData()) {
      return;
    }
    if (state.adminGoogleSheetsSyncing) {
      return;
    }
    state.adminGoogleSheetsSyncing = true;
    state.adminGoogleSheetsSyncError = "";
    state.adminGoogleSheetsSyncStatus = "";
    state.adminGoogleSheetsSyncMessage = "";
    state.adminGoogleSheetsSyncRequestedAt = Date.now();
    cancelAdminGoogleSheetsSyncFollowup();
    renderAdminEmbedPanel();
    try {
      const response = await api("/api/admin/google-sheets/sync", { method: "POST", timeoutMs: 60000 });
      const syncStatus = String(response?.sync_status || "").trim().toLowerCase();
      state.adminGoogleSheetsSyncStatus = syncStatus;
      if (syncStatus === "queued") {
        state.adminGoogleSheetsSyncMessage = "Google Sheets sync_status=queued (queued). Refreshing...";
        flash("Google Sheets 동기화를 대기열에 등록했다. 완료될 때까지 자동 갱신한다.", "info");
        scheduleAdminGoogleSheetsSyncFollowup();
      } else if (syncStatus === "already_running") {
        state.adminGoogleSheetsSyncMessage = "Google Sheets sync_status=already_running. Refreshing...";
        flash("Google Sheets 동기화가 이미 실행 중이다. 완료될 때까지 자동 갱신한다.", "info");
        scheduleAdminGoogleSheetsSyncFollowup();
      } else if (syncStatus === "not_configured") {
        state.adminGoogleSheetsSyncMessage = "Google Sheets sync_status=not_configured.";
        flash("Google Sheets 동기화 설정이 없다.", "warn");
      } else if (syncStatus) {
        state.adminGoogleSheetsSyncMessage = `Google Sheets sync_status=${syncStatus}.`;
        flash(`Google Sheets 동기화 응답: ${syncStatus}`, "info");
      } else {
        state.adminGoogleSheetsSyncMessage = "Google Sheets sync request accepted.";
        flash("Google Sheets 동기화를 요청했다.", "info");
        scheduleAdminGoogleSheetsSyncFollowup();
      }

      void loadAdminGoogleSheetsBootstrap({ silent: true, force: true });
    } catch (err) {
      state.adminGoogleSheetsSyncError = err.message || "Failed to sync Google Sheets.";
      if (!silent) {
        flash(state.adminGoogleSheetsSyncError, "error");
      }
    } finally {
      state.adminGoogleSheetsSyncing = false;
      renderAdminEmbedPanel();
    }
  }

  return {
    loadAdminGoogleSheetsBootstrap,
    loadAdminGoogleSheetPayload,
    scheduleAdminGoogleSheetsSyncFollowup,
    syncAdminGoogleSheets,
    cancelAdminGoogleSheetsSyncFollowup,
  };
}

const adminGoogleSheetsControllerRoot = typeof window !== "undefined" ? window : globalThis;
adminGoogleSheetsControllerRoot.SPMSAdminGoogleSheetsController = adminGoogleSheetsControllerRoot.SPMSAdminGoogleSheetsController || {};
adminGoogleSheetsControllerRoot.SPMSAdminGoogleSheetsController.createAdminGoogleSheetsController = createAdminGoogleSheetsController;

if (typeof exports !== "undefined") {
  exports.createAdminGoogleSheetsController = createAdminGoogleSheetsController;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createAdminGoogleSheetsController };
}
