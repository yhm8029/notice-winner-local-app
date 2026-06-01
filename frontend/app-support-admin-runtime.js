(function attachAppSupportAdminRuntime(global) {
  function createAdminTabsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      windowObject = global,
      documentObject = global?.document || null,
      APP_ROOT_PATH: appRootPath = "/app/",
      DEFAULT_ADMIN_TAB: defaultAdminTab = "project-status",
      ADMIN_TABS: adminTabs = [],
      LEGACY_ADMIN_ROUTE_ALIASES: legacyAdminRouteAliases = {},
      adminGoogleSheetsRuntime = null,
      adminGoogleSheetsAppRuntime = null,
      canLoadProtectedConsoleData = () => false,
      syncUrlState = () => {},
      applyUiMode = () => {},
      buildResolvedAdminGoogleSheetTabs = () => [],
      escapeHtml = (value) => String(value ?? ""),
      buildUrlForState = () => "",
      loadAdminGoogleSheetsBootstrap = async () => {},
      loadAdminGoogleSheetPayload = async () => {},
      syncAdminGoogleSheets = async () => {},
      setTrackerChangeBellPopoverOpen = () => {},
      closeTrackerChangeModal = () => {},
      closeProfileDialog = () => {},
    } = options;

    let globalDismissalListenersBound = false;
    const LEGACY_PROJECT_STATUS_ROUTE_PATH = "/app/project-status";

    function normalizeLocationPath(pathname) {
      const raw = String(pathname || "").trim();
      if (!raw) return appRootPath;
      const normalized = raw.endsWith("/") && raw !== "/" ? raw.replace(/\/+$/, "") : raw;
      return normalized || appRootPath;
    }

    function resolveLegacyAdminRoutePath(pathname) {
      const normalized = normalizeLocationPath(pathname);
      return legacyAdminRouteAliases[normalized] ? normalized : "";
    }

    function isAppRootRoutePath(pathname) {
      return normalizeLocationPath(pathname) === normalizeLocationPath(appRootPath);
    }

    function isLegacyProjectStatusRoutePath(pathname) {
      return normalizeLocationPath(pathname) === LEGACY_PROJECT_STATUS_ROUTE_PATH;
    }

    function getAdminTabByPathname(pathname) {
      const normalizedPath = normalizeLocationPath(pathname);
      const resolved = adminTabs.find((item) => normalizeLocationPath(item?.routePath) === normalizedPath) || null;
      if (resolved) return resolved;
      if (isLegacyProjectStatusRoutePath(normalizedPath)) return adminTabs[0] || null;
      if (legacyAdminRouteAliases[normalizedPath]) return adminTabs[0] || null;
      return null;
    }

    function isBuiltinAdminTabKey(value) {
      const key = String(value ?? "").trim();
      return Boolean(key) && adminTabs.some((item) => String(item?.key || "").trim() === key);
    }

    function isAdminRoutePath(pathname) {
      return Boolean(getAdminTabByPathname(pathname));
    }

    function getAdminRoutePath(tabKey = defaultAdminTab) {
      const key = String(tabKey || "").trim();
      const matched = adminTabs.find((item) => String(item?.key || "").trim() === key) || adminTabs[0] || null;
      return matched?.routePath || appRootPath;
    }

    function isProjectStatusRoutePath(pathname = windowObject?.location?.pathname) {
      return isAppRootRoutePath(pathname) || isLegacyProjectStatusRoutePath(pathname);
    }

    function isPendingLegacyAdminAlias() {
      return Boolean(state.adminLegacyRoutePath) && state.adminTab === defaultAdminTab;
    }

    function isAdminGoogleSheetTabKey(value) {
      const key = String(value ?? "").trim();
      if (!key) return false;
      if (typeof adminGoogleSheetsRuntime?.isAdminGoogleSheetTabKey === "function") {
        return adminGoogleSheetsRuntime.isAdminGoogleSheetTabKey(key);
      }
      return /^sheet-\d+$/.test(key);
    }

    function resolveStatePathname({
      pathname = windowObject?.location?.pathname,
      uiMode = state.uiMode,
      adminTab = state.adminTab,
    } = {}) {
      if (
        uiMode === "admin"
        || isAdminGoogleSheetTabKey(adminTab)
        || isProjectStatusRoutePath(pathname)
        || resolveLegacyAdminRoutePath(pathname)
      ) {
        return getAdminRoutePath(adminTab);
      }
      if (isAdminRoutePath(pathname)) return appRootPath;
      return pathname || appRootPath;
    }

    function getResolvedAdminTabs() {
      return [...adminTabs.filter(Boolean), ...buildResolvedAdminGoogleSheetTabs()];
    }

    function findResolvedAdminTab(tabKey) {
      const candidate = String(tabKey || "").trim();
      return getResolvedAdminTabs().find((item) => item?.key === candidate) || null;
    }

    function getValidatedActiveAdminGoogleSheetTab() {
      const resolved = findResolvedAdminTab(state.adminTab);
      return resolved && resolved.type === "google_sheet" ? resolved : null;
    }

    function getActiveAdminTab() {
      if (isPendingLegacyAdminAlias()) {
        const legacy = legacyAdminRouteAliases[state.adminLegacyRoutePath] || null;
        const legacyLabel = String(legacy?.labelHint || "").trim();
        return {
          key: state.adminLegacyRoutePath,
          label: legacyLabel || "Google Sheets",
          routePath: state.adminLegacyRoutePath,
          type: "google_sheet_pending",
          subtitle: "Google Sheets read-only view",
        };
      }
      const resolved = findResolvedAdminTab(state.adminTab);
      if (resolved) return resolved;
      if (isAdminGoogleSheetTabKey(state.adminTab)) {
        return {
          key: state.adminTab,
          label: state.adminTab,
          routePath: getAdminRoutePath(defaultAdminTab),
          type: "google_sheet",
          subtitle: "Google Sheets read-only view",
        };
      }
      return adminTabs[0];
    }

    function normalizeSheetTabMatchValue(value) {
      return String(value || "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "")
        .replace(/[^a-z0-9가-힣]/g, "");
    }

    function scoreLegacyAliasMatch(tab, hint) {
      const label = normalizeSheetTabMatchValue(tab?.label);
      const rawTitle = normalizeSheetTabMatchValue(tab?.rawTitle);
      if (!hint) return 0;
      if (label === hint || rawTitle === hint) return 300;
      if (label.startsWith(hint) || rawTitle.startsWith(hint)) return 200;
      if (label.includes(hint) || rawTitle.includes(hint)) return 100;
      return 0;
    }

    function resolveLegacyAdminGoogleSheetTabKey(legacyRoutePath) {
      const normalizedLegacyPath = resolveLegacyAdminRoutePath(legacyRoutePath);
      if (!normalizedLegacyPath) return "";
      const alias = legacyAdminRouteAliases[normalizedLegacyPath];
      const hint = normalizeSheetTabMatchValue(alias?.labelHint || "");
      if (!hint) return "";

      const tabs = Array.isArray(state.adminGoogleSheetTabs) ? state.adminGoogleSheetTabs : [];
      let bestKey = "";
      let bestScore = 0;
      for (const tab of tabs) {
        if (!tab || typeof tab !== "object") continue;
        const score = scoreLegacyAliasMatch(tab, hint);
        if (score > bestScore) {
          bestScore = score;
          bestKey = String(tab.key || "").trim();
        }
      }
      return bestKey;
    }

    function clearAdminLegacyRouteIntent() {
      state.adminLegacyRoutePath = "";
    }

    function clearAdminGoogleSheetPopupStateForTab(nextTab, { render = false } = {}) {
      return adminGoogleSheetsAppRuntime?.clearAdminGoogleSheetPopupStateForTab(nextTab, { render }) ?? false;
    }

    function maybeResolveLegacyAdminAliasToSheetTab({ historyMode = "replace" } = {}) {
      if (!state.adminLegacyRoutePath) return false;
      if (state.adminTab !== defaultAdminTab) return false;
      if (!state.adminGoogleSheetsBootstrap) return false;
      const resolvedKey = resolveLegacyAdminGoogleSheetTabKey(state.adminLegacyRoutePath);
      if (!resolvedKey) {
        state.adminLegacyRoutePath = "";
        clearAdminGoogleSheetPopupStateForTab(defaultAdminTab, { render: false });
        state.adminTab = defaultAdminTab;
        syncUrlState({ historyMode, uiMode: state.uiMode, adminTab: state.adminTab });
        applyUiMode();
        return false;
      }
      state.adminLegacyRoutePath = "";
      clearAdminGoogleSheetPopupStateForTab(resolvedKey, { render: false });
      state.adminTab = resolvedKey;
      syncUrlState({ historyMode, uiMode: state.uiMode, adminTab: state.adminTab });
      void loadAdminGoogleSheetPayload(state.adminTab, { silent: true });
      return true;
    }

    function getAdminGoogleSheetsBootstrapSyncStatus(bootstrap = state.adminGoogleSheetsBootstrap || {}) {
      return String(bootstrap?.sync_status || "").trim().toLowerCase();
    }

    function shouldDeferAdminGoogleSheetPayloadLoad(sheetKey, { force = false } = {}) {
      if (force) return false;
      if (
        !state.adminGoogleSheetsCacheHydrated
        || !state.adminGoogleSheetsCacheBootstrapRefreshRequested
        || !state.adminGoogleSheetsBootstrapLoading
      ) {
        return false;
      }
      const activeSheetTab = getValidatedActiveAdminGoogleSheetTab();
      return Boolean(activeSheetTab && activeSheetTab.key === String(sheetKey || "").trim());
    }

    function shouldShowAdminGoogleSheetsOverviewPanel({ canLoadProtectedData } = {}) {
      if (state.uiMode !== "admin" && state.uiMode !== "user") return false;
      if (isAdminGoogleSheetTabKey(state.adminTab) || isPendingLegacyAdminAlias()) return false;
      if (!adminGoogleSheetsRuntime || !canLoadProtectedData) return false;
      if (state.adminTab !== defaultAdminTab || !isProjectStatusRoutePath(windowObject?.location?.pathname)) return false;
      const hasBootstrapState = Boolean(state.adminGoogleSheetsBootstrap || state.adminGoogleSheetsBootstrapError);
      if (!hasBootstrapState) return false;
      if (state.uiMode === "user") return true;
      const hasDynamicTabs = Array.isArray(state.adminGoogleSheetTabs) && state.adminGoogleSheetTabs.length > 0;
      return Boolean(state.adminGoogleSheetsBootstrapError) || !hasDynamicTabs;
    }

    function shouldShowSharedGoogleSheetsShell({ canLoadProtectedData } = {}) {
      if (!canLoadProtectedData) return false;
      if (isPendingLegacyAdminAlias()) return true;
      if (isAdminGoogleSheetTabKey(state.adminTab)) return true;
      if (!isBuiltinAdminTabKey(state.adminTab)) return false;
      return isProjectStatusRoutePath(windowObject?.location?.pathname) || isAdminRoutePath(windowObject?.location?.pathname);
    }

    function shouldShowAdminGoogleSheetsControls({ panelVisible } = {}) {
      return Boolean(panelVisible) && state.uiMode === "admin" && Boolean(adminGoogleSheetsRuntime);
    }

    function normalizeAdminGoogleSheetsFilterState(sheetState) {
      return adminGoogleSheetsAppRuntime?.normalizeAdminGoogleSheetsFilterState(sheetState) || { sort: null, columns: {} };
    }

    function adminGoogleSheetsFilterStateEqual(left, right) {
      return adminGoogleSheetsAppRuntime?.adminGoogleSheetsFilterStateEqual(left, right) ?? false;
    }

    function getAdminGoogleSheetsFilterState(sheetKey) {
      return adminGoogleSheetsAppRuntime?.getAdminGoogleSheetsFilterState(sheetKey) || { sort: null, columns: {} };
    }

    function getAdminGoogleSheetMinHeight(sheetKey) {
      return Number(adminGoogleSheetsAppRuntime?.getAdminGoogleSheetMinHeight(sheetKey) || 0);
    }

    function measureAdminGoogleSheetTableHeight() {
      return Number(adminGoogleSheetsAppRuntime?.measureAdminGoogleSheetTableHeight() || 0);
    }

    function syncAdminGoogleSheetMinHeight(sheetKey) {
      return adminGoogleSheetsAppRuntime?.syncAdminGoogleSheetMinHeight(sheetKey) || { changed: false, value: 0 };
    }

    function sanitizeAdminGoogleSheetsFilterStateForSheet(sheetKey, sheetState) {
      return adminGoogleSheetsAppRuntime?.sanitizeAdminGoogleSheetsFilterStateForSheet(sheetKey, sheetState) || normalizeAdminGoogleSheetsFilterState(sheetState);
    }

    function setAdminGoogleSheetsFilterState(sheetKey, sheetState, { render = true } = {}) {
      return adminGoogleSheetsAppRuntime?.setAdminGoogleSheetsFilterState(sheetKey, sheetState, { render });
    }

    function normalizeAdminGoogleSheetPopupState(popupState) {
      return adminGoogleSheetsAppRuntime?.normalizeAdminGoogleSheetPopupState(popupState) || {
        open: false,
        sheetKey: "",
        columnIndex: -1,
        searchDraft: "",
        pendingSelectedValues: [],
        pendingSortDirection: "",
      };
    }

    function getAdminGoogleSheetPopupState() {
      return adminGoogleSheetsAppRuntime?.getAdminGoogleSheetPopupState() || normalizeAdminGoogleSheetPopupState(state.adminGoogleSheetsPopupState);
    }

    function setAdminGoogleSheetPopupState(popupState, { render = true } = {}) {
      return adminGoogleSheetsAppRuntime?.setAdminGoogleSheetPopupState(popupState, { render });
    }

    function setAdminGoogleSheetPopupSearch(searchDraft) {
      return adminGoogleSheetsAppRuntime?.setAdminGoogleSheetPopupSearch(searchDraft);
    }

    function openAdminGoogleSheetFilterPopup(sheetKey, columnIndex) {
      return adminGoogleSheetsAppRuntime?.openAdminGoogleSheetFilterPopup(sheetKey, columnIndex);
    }

    function toggleAdminGoogleSheetPopupValue(value, checked) {
      return adminGoogleSheetsAppRuntime?.toggleAdminGoogleSheetPopupValue(value, checked);
    }

    function setAdminGoogleSheetPopupSort(direction) {
      return adminGoogleSheetsAppRuntime?.setAdminGoogleSheetPopupSort(direction);
    }

    function clearAdminGoogleSheetPopupState({ render = true } = {}) {
      return adminGoogleSheetsAppRuntime?.clearAdminGoogleSheetPopupState({ render });
    }

    function confirmAdminGoogleSheetPopup() {
      return adminGoogleSheetsAppRuntime?.confirmAdminGoogleSheetPopup();
    }

    function cancelAdminGoogleSheetPopup() {
      return adminGoogleSheetsAppRuntime?.cancelAdminGoogleSheetPopup();
    }

    function getAdminGoogleSheetTableInteractionSheetKey() {
      return adminGoogleSheetsAppRuntime?.getAdminGoogleSheetTableInteractionSheetKey()
        || String(dom.adminGoogleSheetTable?.dataset?.adminGoogleSheetActiveSheetKey || "").trim();
    }

    function handleAdminGoogleSheetPopupDismissal(event) {
      return adminGoogleSheetsAppRuntime?.handleAdminGoogleSheetPopupDismissal(event) ?? false;
    }

    function bindAdminGoogleSheetsActions() {
      if (!dom.adminGoogleSheetsSyncButton) return;
      if (dom.adminGoogleSheetsSyncButton.dataset?.syncBound === "1") return;
      dom.adminGoogleSheetsSyncButton.dataset.syncBound = "1";
      dom.adminGoogleSheetsSyncButton.addEventListener("click", () => {
        void syncAdminGoogleSheets({});
      });
    }

    function bindGlobalDismissalListeners() {
      if (globalDismissalListenersBound) return;
      globalDismissalListenersBound = true;

      documentObject?.addEventListener?.("click", (event) => {
        handleAdminGoogleSheetPopupDismissal(event);
        const target = event?.target || null;
        if (
          state.trackerChangeBellPopoverOpen
          && (!dom.trackerChangeBellShell || !target || !dom.trackerChangeBellShell.contains(target))
        ) {
          setTrackerChangeBellPopoverOpen(false);
        }
      });
      windowObject?.addEventListener?.("keydown", (event) => {
        if (event.key === "Escape" && getAdminGoogleSheetPopupState().open) {
          cancelAdminGoogleSheetPopup();
          return;
        }
        if (event.key === "Escape" && state.trackerChangeModal.open) {
          closeTrackerChangeModal();
          return;
        }
        if (event.key === "Escape" && state.profileDialog.open) {
          closeProfileDialog();
          return;
        }
        if (event.key === "Escape" && state.trackerChangeBellPopoverOpen) {
          setTrackerChangeBellPopoverOpen(false);
        }
      });
    }

    return {
      normalizeLocationPath,
      resolveLegacyAdminRoutePath,
      getAdminTabByPathname,
      isAdminRoutePath,
      getAdminRoutePath,
      isProjectStatusRoutePath,
      resolveStatePathname,
      getActiveAdminTab,
      isPendingLegacyAdminAlias,
      isAdminGoogleSheetTabKey,
      getResolvedAdminTabs,
      findResolvedAdminTab,
      getValidatedActiveAdminGoogleSheetTab,
      normalizeSheetTabMatchValue,
      scoreLegacyAliasMatch,
      resolveLegacyAdminGoogleSheetTabKey,
      maybeResolveLegacyAdminAliasToSheetTab,
      clearAdminLegacyRouteIntent,
      getAdminGoogleSheetsBootstrapSyncStatus,
      shouldDeferAdminGoogleSheetPayloadLoad,
      shouldShowAdminGoogleSheetsOverviewPanel,
      shouldShowSharedGoogleSheetsShell,
      shouldShowAdminGoogleSheetsControls,
      normalizeAdminGoogleSheetsFilterState,
      adminGoogleSheetsFilterStateEqual,
      getAdminGoogleSheetsFilterState,
      getAdminGoogleSheetMinHeight,
      measureAdminGoogleSheetTableHeight,
      syncAdminGoogleSheetMinHeight,
      sanitizeAdminGoogleSheetsFilterStateForSheet,
      setAdminGoogleSheetsFilterState,
      normalizeAdminGoogleSheetPopupState,
      getAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupSearch,
      openAdminGoogleSheetFilterPopup,
      toggleAdminGoogleSheetPopupValue,
      setAdminGoogleSheetPopupSort,
      clearAdminGoogleSheetPopupState,
      clearAdminGoogleSheetPopupStateForTab,
      confirmAdminGoogleSheetPopup,
      cancelAdminGoogleSheetPopup,
      getAdminGoogleSheetTableInteractionSheetKey,
      handleAdminGoogleSheetPopupDismissal,
      bindAdminGoogleSheetsActions,
      bindGlobalDismissalListeners,
    };
  }

  function createAdminTabsFacade(options = {}) {
    const {
      state = {},
      dom = {},
      windowObject = global,
      APP_ROOT_PATH = "",
      DEFAULT_ADMIN_TAB = "",
      adminTabsHelpers = {},
      adminTabsRuntime = null,
      adminGoogleSheetsCacheRuntime = null,
      adminGoogleSheetsAppRuntime = null,
      canUseAdminMode = () => false,
      canLoadProtectedConsoleData = () => false,
      buildUrlForState = () => APP_ROOT_PATH,
      escapeHtml = (value) => String(value ?? ""),
      applyUiMode = () => {},
      getAdminGoogleSheetsController = () => null,
    } = options;

    const {
      normalizeLocationPath,
      resolveLegacyAdminRoutePath,
      getAdminTabByPathname,
      isAdminRoutePath,
      getAdminRoutePath,
      isProjectStatusRoutePath,
      resolveStatePathname,
      getActiveAdminTab,
      isPendingLegacyAdminAlias,
      isAdminGoogleSheetTabKey,
      getResolvedAdminTabs,
      findResolvedAdminTab,
      getValidatedActiveAdminGoogleSheetTab,
      normalizeSheetTabMatchValue,
      scoreLegacyAliasMatch,
      resolveLegacyAdminGoogleSheetTabKey,
      maybeResolveLegacyAdminAliasToSheetTab,
      clearAdminLegacyRouteIntent,
      getAdminGoogleSheetsBootstrapSyncStatus,
      shouldDeferAdminGoogleSheetPayloadLoad,
      shouldShowAdminGoogleSheetsOverviewPanel,
      shouldShowSharedGoogleSheetsShell,
      shouldShowAdminGoogleSheetsControls,
      normalizeAdminGoogleSheetsFilterState,
      adminGoogleSheetsFilterStateEqual,
      getAdminGoogleSheetsFilterState,
      getAdminGoogleSheetMinHeight,
      measureAdminGoogleSheetTableHeight,
      syncAdminGoogleSheetMinHeight,
      sanitizeAdminGoogleSheetsFilterStateForSheet,
      setAdminGoogleSheetsFilterState,
      normalizeAdminGoogleSheetPopupState,
      getAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupSearch,
      openAdminGoogleSheetFilterPopup,
      toggleAdminGoogleSheetPopupValue,
      setAdminGoogleSheetPopupSort,
      clearAdminGoogleSheetPopupState,
      clearAdminGoogleSheetPopupStateForTab,
      confirmAdminGoogleSheetPopup,
      cancelAdminGoogleSheetPopup,
      getAdminGoogleSheetTableInteractionSheetKey,
      handleAdminGoogleSheetPopupDismissal,
      bindAdminGoogleSheetsActions,
      bindGlobalDismissalListeners,
    } = adminTabsHelpers;

    function isBuiltinAdminTabKey(value) {
      const key = String(value ?? "").trim();
      if (!key) return false;
      const resolved = findResolvedAdminTab(key);
      return Boolean(resolved && resolved.type !== "google_sheet");
    }

    function normalizeAdminTab(rawValue) {
      return adminTabsRuntime?.normalizeAdminTab
        ? adminTabsRuntime.normalizeAdminTab(rawValue, { defaultTab: DEFAULT_ADMIN_TAB, isAdminGoogleSheetTabKey, isBuiltinAdminTabKey })
        : (isBuiltinAdminTabKey(rawValue) ? String(rawValue || "").trim() : DEFAULT_ADMIN_TAB);
    }

    function isLegacyProjectStatusRoutePathForFacade(pathname) {
      return normalizeLocationPath(pathname) === "/app/project-status";
    }

    function resolveUiModeFromLocation(pathname = windowObject.location.pathname, search = windowObject.location.search) {
      return adminTabsRuntime?.resolveUiModeFromLocation
        ? adminTabsRuntime.resolveUiModeFromLocation(pathname, search, {
          canUseAdminMode,
          isProjectStatusRoutePath,
          isAdminModeRoutePath: (candidate) => isLegacyProjectStatusRoutePathForFacade(candidate) || isAdminRoutePath(candidate) || Boolean(resolveLegacyAdminRoutePath(candidate)),
          resolveLegacyAdminRoutePath,
        })
        : "user";
    }

    function buildResolvedAdminGoogleSheetTabs() {
      return adminTabsRuntime?.buildResolvedAdminGoogleSheetTabs
        ? adminTabsRuntime.buildResolvedAdminGoogleSheetTabs(state.adminGoogleSheetTabs, {
          routePath: getAdminRoutePath(DEFAULT_ADMIN_TAB),
        })
        : [];
    }

    function readAdminGoogleSheetsCacheSnapshot() {
      return adminTabsRuntime?.readAdminGoogleSheetsCacheSnapshot
        ? adminTabsRuntime.readAdminGoogleSheetsCacheSnapshot(adminGoogleSheetsCacheRuntime)
        : null;
    }

    function hydrateAdminGoogleSheetsCacheOnFirstProtectedRender() {
      return adminTabsRuntime?.hydrateAdminGoogleSheetsCacheOnFirstProtectedRender
        ? adminTabsRuntime.hydrateAdminGoogleSheetsCacheOnFirstProtectedRender({
          state,
          cacheRuntime: adminGoogleSheetsCacheRuntime,
          canLoadProtectedConsoleData,
          shouldShowSharedGoogleSheetsShell,
          maybeResolveLegacyAdminAliasToSheetTab,
          isAdminGoogleSheetTabKey,
          routePath: getAdminRoutePath(DEFAULT_ADMIN_TAB),
        })
        : false;
    }

    function persistAdminGoogleSheetsCache() {
      return adminTabsRuntime?.persistAdminGoogleSheetsCache
        ? adminTabsRuntime.persistAdminGoogleSheetsCache({
          state,
          cacheRuntime: adminGoogleSheetsCacheRuntime,
          isAdminGoogleSheetTabKey,
        })
        : false;
    }

    function renderAdminTopNavigation() {
      if (!dom.adminTopNavList) return;
      if (!shouldShowSharedGoogleSheetsShell({ canLoadProtectedData: canLoadProtectedConsoleData() })) {
        dom.adminTopNavList.innerHTML = "";
        return;
      }
      dom.adminTopNavList.innerHTML = getResolvedAdminTabs().map((item) => `
        <a
          class="admin-top-nav-button${item.key === state.adminTab ? " is-active" : ""}"
          href="${escapeHtml(buildUrlForState({ pathname: item.routePath || APP_ROOT_PATH, uiMode: state.uiMode, adminTab: item.key }))}"
          data-admin-tab="${item.key}"
        >${escapeHtml(item.label)}</a>
      `).join("");
    }

    function renderAdminEmbedPanel() {
      if (
        !dom.adminEmbedPanel
        || !dom.adminEmbedTitle
        || !dom.adminEmbedSubtitle
        || !dom.adminGoogleSheetsSyncFeedback
        || !dom.adminGoogleSheetStatus
        || !dom.adminGoogleSheetTable
        || !dom.adminEmbedEmpty
      ) {
        return;
      }
      if (!adminGoogleSheetsAppRuntime?.renderAdminEmbedPanel) return;
      return adminGoogleSheetsAppRuntime.renderAdminEmbedPanel();
    }

    function loadAdminGoogleSheetsBootstrap({ silent = false, force = false } = {}) {
      return getAdminGoogleSheetsController()?.loadAdminGoogleSheetsBootstrap({ silent, force });
    }

    function loadAdminGoogleSheetPayload(sheetKey, { silent = false, force = false } = {}) {
      return getAdminGoogleSheetsController()?.loadAdminGoogleSheetPayload(sheetKey, { silent, force });
    }

    function scheduleAdminGoogleSheetsSyncFollowup() {
      return getAdminGoogleSheetsController()?.scheduleAdminGoogleSheetsSyncFollowup();
    }

    function syncAdminGoogleSheets({ silent = false } = {}) {
      return getAdminGoogleSheetsController()?.syncAdminGoogleSheets({ silent });
    }

    function setAdminTab(nextTab, { historyMode = "push" } = {}) {
      const normalized = normalizeAdminTab(nextTab);
      const clearedLegacyIntent = Boolean(state.adminLegacyRoutePath);
      clearAdminLegacyRouteIntent();
      if (state.adminTab === normalized && !clearedLegacyIntent) return;
      clearAdminGoogleSheetPopupStateForTab(normalized, { render: false });
      state.adminTab = normalized;
      options.syncUrlState?.({ historyMode, uiMode: state.uiMode, adminTab: normalized });
      const resolvedSheetTab = findResolvedAdminTab(normalized);
      if (resolvedSheetTab && resolvedSheetTab.type === "google_sheet") {
        void loadAdminGoogleSheetsBootstrap({ silent: true });
        void loadAdminGoogleSheetPayload(resolvedSheetTab.key, { silent: true });
      }
      applyUiMode();
    }

    function bindAdminGoogleSheetTableInteractions(sheetKey) {
      if (!dom.adminGoogleSheetTable || !adminGoogleSheetsAppRuntime?.bindAdminGoogleSheetTableInteractions) return;
      return adminGoogleSheetsAppRuntime.bindAdminGoogleSheetTableInteractions(sheetKey);
    }

    function renderAdminGoogleSheetTable(sheetKey, sheetPayload) {
      if (!dom.adminGoogleSheetTable || !adminGoogleSheetsAppRuntime?.renderAdminGoogleSheetTable) return;
      return adminGoogleSheetsAppRuntime.renderAdminGoogleSheetTable(sheetKey, sheetPayload);
    }

    return {
      normalizeAdminTab,
      normalizeLocationPath,
      resolveLegacyAdminRoutePath,
      getAdminTabByPathname,
      isAdminRoutePath,
      getAdminRoutePath,
      isProjectStatusRoutePath,
      resolveUiModeFromLocation,
      resolveStatePathname,
      getActiveAdminTab,
      isPendingLegacyAdminAlias,
      isAdminGoogleSheetTabKey,
      buildResolvedAdminGoogleSheetTabs,
      getResolvedAdminTabs,
      findResolvedAdminTab,
      getValidatedActiveAdminGoogleSheetTab,
      normalizeSheetTabMatchValue,
      scoreLegacyAliasMatch,
      resolveLegacyAdminGoogleSheetTabKey,
      maybeResolveLegacyAdminAliasToSheetTab,
      clearAdminLegacyRouteIntent,
      getAdminGoogleSheetsBootstrapSyncStatus,
      readAdminGoogleSheetsCacheSnapshot,
      hydrateAdminGoogleSheetsCacheOnFirstProtectedRender,
      persistAdminGoogleSheetsCache,
      shouldDeferAdminGoogleSheetPayloadLoad,
      shouldShowAdminGoogleSheetsOverviewPanel,
      shouldShowSharedGoogleSheetsShell,
      shouldShowAdminGoogleSheetsControls,
      normalizeAdminGoogleSheetsFilterState,
      adminGoogleSheetsFilterStateEqual,
      getAdminGoogleSheetsFilterState,
      getAdminGoogleSheetMinHeight,
      measureAdminGoogleSheetTableHeight,
      syncAdminGoogleSheetMinHeight,
      sanitizeAdminGoogleSheetsFilterStateForSheet,
      setAdminGoogleSheetsFilterState,
      normalizeAdminGoogleSheetPopupState,
      getAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupSearch,
      openAdminGoogleSheetFilterPopup,
      toggleAdminGoogleSheetPopupValue,
      setAdminGoogleSheetPopupSort,
      clearAdminGoogleSheetPopupState,
      clearAdminGoogleSheetPopupStateForTab,
      confirmAdminGoogleSheetPopup,
      cancelAdminGoogleSheetPopup,
      getAdminGoogleSheetTableInteractionSheetKey,
      handleAdminGoogleSheetPopupDismissal,
      bindAdminGoogleSheetTableInteractions,
      renderAdminGoogleSheetTable,
      renderAdminTopNavigation,
      renderAdminEmbedPanel,
      setAdminTab,
      loadAdminGoogleSheetsBootstrap,
      loadAdminGoogleSheetPayload,
      scheduleAdminGoogleSheetsSyncFollowup,
      syncAdminGoogleSheets,
      bindAdminGoogleSheetsActions,
      bindGlobalDismissalListeners,
    };
  }

  global.SPMSAppSupportAdminRuntime = {
    createAdminTabsHelpers,
    createAdminTabsFacade,
  };
})(typeof window !== "undefined" ? window : globalThis);
