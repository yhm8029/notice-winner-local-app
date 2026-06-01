(function attachAdminTabsRuntime(global) {
  const DEFAULT_ADMIN_TAB = "project-status";
  const DEFAULT_ADMIN_TAB_ROUTE_PATH = "/";
  const DEFAULT_ADMIN_GOOGLE_SHEETS_SUBTITLE = "Google Sheets read-only view";
  const ADMIN_GOOGLE_SHEET_TAB_KEY_RE = /^sheet-\d+$/;

  function isPlainObject(value) {
    if (!value || typeof value !== "object") {
      return false;
    }
    if (Array.isArray(value)) {
      return false;
    }
    return Object.prototype.toString.call(value) === "[object Object]";
  }

  function isAdminGoogleSheetTabKey(value) {
    return ADMIN_GOOGLE_SHEET_TAB_KEY_RE.test(String(value ?? "").trim());
  }

  function normalizeAdminTab(rawValue, options = {}) {
    const defaultTab = String(options.defaultTab || DEFAULT_ADMIN_TAB).trim() || DEFAULT_ADMIN_TAB;
    const isAdminGoogleSheetTabKeyFn = typeof options.isAdminGoogleSheetTabKey === "function"
      ? options.isAdminGoogleSheetTabKey
      : isAdminGoogleSheetTabKey;
    const isBuiltinAdminTabKeyFn = typeof options.isBuiltinAdminTabKey === "function"
      ? options.isBuiltinAdminTabKey
      : (value) => String(value || "").trim() === defaultTab;
    const candidate = String(rawValue || "").trim();
    if (!candidate) {
      return defaultTab;
    }
    if (isBuiltinAdminTabKeyFn(candidate)) {
      return candidate;
    }
    if (isAdminGoogleSheetTabKeyFn(candidate)) {
      return candidate;
    }
    return defaultTab;
  }

  function normalizeLocationPath(pathname) {
    const raw = String(pathname || "").trim();
    if (!raw) {
      return DEFAULT_ADMIN_TAB_ROUTE_PATH;
    }
    const normalized = raw.endsWith("/") && raw !== "/" ? raw.replace(/\/+$/, "") : raw;
    return normalized || DEFAULT_ADMIN_TAB_ROUTE_PATH;
  }

  function resolveUiModeFromLocation(pathname = DEFAULT_ADMIN_TAB_ROUTE_PATH, search = "", options = {}) {
    const canUseAdminMode = typeof options.canUseAdminMode === "function" ? options.canUseAdminMode : () => true;
    const isProjectStatusRoutePath = typeof options.isProjectStatusRoutePath === "function"
      ? options.isProjectStatusRoutePath
      : () => false;
    const isAdminModeRoutePath = typeof options.isAdminModeRoutePath === "function"
      ? options.isAdminModeRoutePath
      : isProjectStatusRoutePath;
    const resolveLegacyAdminRoutePath = typeof options.resolveLegacyAdminRoutePath === "function"
      ? options.resolveLegacyAdminRoutePath
      : () => "";

    if (!canUseAdminMode()) {
      return "user";
    }
    const params = new URLSearchParams(search);
    if (params.get("mode") === "admin") {
      return "admin";
    }
    if (isAdminModeRoutePath(pathname)) {
      return "admin";
    }
    if (resolveLegacyAdminRoutePath(pathname)) {
      return "admin";
    }
    return "user";
  }

  function normalizeResolvedAdminGoogleSheetTab(tab, fallbackKey, routePath, subtitle, sourceIndex) {
    const source = tab && typeof tab === "object" ? tab : {};
    const key = String(source.key ?? fallbackKey ?? "").trim();
    const rawTitle = String(source.rawTitle ?? source.raw_title ?? "").trim();
    const label = String(source.label ?? source.display_title ?? source.displayTitle ?? rawTitle ?? key).trim() || key;
    const sheetIdValue = source.sheetId ?? source.sheet_id ?? 0;
    const sheetOrderValue = source.sheetOrder ?? source.sheet_order ?? source.order ?? sourceIndex;
    const sheetId = Number(sheetIdValue);
    const sheetOrder = Number(sheetOrderValue);

    return {
      key,
      label,
      routePath,
      type: "google_sheet",
      subtitle,
      sheetId: Number.isFinite(sheetId) ? sheetId : 0,
      rawTitle,
      sheetOrder: Number.isFinite(sheetOrder) ? sheetOrder : sourceIndex,
    };
  }

  function buildResolvedAdminGoogleSheetTabs(tabsSource, options = {}) {
    const routePath = String(options.routePath || DEFAULT_ADMIN_TAB_ROUTE_PATH).trim() || DEFAULT_ADMIN_TAB_ROUTE_PATH;
    const subtitle = String(options.subtitle || DEFAULT_ADMIN_GOOGLE_SHEETS_SUBTITLE).trim() || DEFAULT_ADMIN_GOOGLE_SHEETS_SUBTITLE;
    const entries = Array.isArray(tabsSource)
      ? tabsSource.map((tab, index) => normalizeResolvedAdminGoogleSheetTab(tab, tab?.key, routePath, subtitle, index))
      : isPlainObject(tabsSource)
        ? Object.entries(tabsSource).map(([key, tab], index) => normalizeResolvedAdminGoogleSheetTab(tab, key, routePath, subtitle, index))
        : [];

    return entries
      .slice()
      .sort((left, right) => {
        const leftOrder = Number(left.sheetOrder || 0);
        const rightOrder = Number(right.sheetOrder || 0);
        if (leftOrder !== rightOrder) {
          return leftOrder - rightOrder;
        }
        return String(left.key || "").localeCompare(String(right.key || ""), "ko");
      })
      .map(({ sheetOrder, ...tab }) => tab)
      .filter((tab) => Boolean(tab.key));
  }

  function shouldHydrateEmptyAdminGoogleSheetsBootstrapFromCache(bootstrap, resolvedTabs) {
    const syncStatus = String(bootstrap?.sync_status || "").trim().toLowerCase();
    if (Array.isArray(resolvedTabs) && resolvedTabs.length > 0) {
      return true;
    }
    if (!bootstrap || typeof bootstrap !== "object") {
      return false;
    }
    if (bootstrap?.enabled === false) {
      return true;
    }
    if (syncStatus === "not_configured" || syncStatus === "failed" || syncStatus === "initializing") {
      return true;
    }
    if (String(bootstrap?.last_error || "").trim()) {
      return true;
    }
    return false;
  }

  function readAdminGoogleSheetsCacheSnapshot(cacheRuntime = global.SPMSAdminGoogleSheetsCacheRuntime || null) {
    if (typeof cacheRuntime?.readAdminGoogleSheetsCache !== "function") {
      return null;
    }
    const snapshot = cacheRuntime.readAdminGoogleSheetsCache();
    if (!snapshot || typeof snapshot !== "object" || !snapshot.bootstrap || typeof snapshot.bootstrap !== "object") {
      return null;
    }
    if (!snapshot.payloadsByKey || typeof snapshot.payloadsByKey !== "object") {
      return null;
    }
    return snapshot;
  }

  function hydrateAdminGoogleSheetsCacheOnFirstProtectedRender(options = {}) {
    const state = options.state && typeof options.state === "object" ? options.state : null;
    const cacheRuntime = options.cacheRuntime || global.SPMSAdminGoogleSheetsCacheRuntime || null;
    const canLoadProtectedConsoleData = typeof options.canLoadProtectedConsoleData === "function"
      ? options.canLoadProtectedConsoleData
      : null;
    const shouldShowSharedGoogleSheetsShell = typeof options.shouldShowSharedGoogleSheetsShell === "function"
      ? options.shouldShowSharedGoogleSheetsShell
      : null;
    const maybeResolveLegacyAdminAliasToSheetTab = typeof options.maybeResolveLegacyAdminAliasToSheetTab === "function"
      ? options.maybeResolveLegacyAdminAliasToSheetTab
      : null;
    const isAdminGoogleSheetTabKeyFn = typeof options.isAdminGoogleSheetTabKey === "function"
      ? options.isAdminGoogleSheetTabKey
      : isAdminGoogleSheetTabKey;
    const routePath = String(options.routePath || DEFAULT_ADMIN_TAB_ROUTE_PATH).trim() || DEFAULT_ADMIN_TAB_ROUTE_PATH;

    if (!state || !cacheRuntime || typeof cacheRuntime.readAdminGoogleSheetsCache !== "function") {
      return false;
    }
    if (state.adminGoogleSheetsCacheHydrationAttempted) {
      return Boolean(state.adminGoogleSheetsCacheHydrated);
    }
    if (canLoadProtectedConsoleData && !canLoadProtectedConsoleData()) {
      return false;
    }
    if (shouldShowSharedGoogleSheetsShell && !shouldShowSharedGoogleSheetsShell({ canLoadProtectedData: true })) {
      return false;
    }

    state.adminGoogleSheetsCacheHydrationAttempted = true;
    const snapshot = readAdminGoogleSheetsCacheSnapshot(cacheRuntime);
    if (!snapshot) {
      return false;
    }

    const bootstrap = state.adminGoogleSheetsBootstrap && typeof state.adminGoogleSheetsBootstrap === "object"
      ? state.adminGoogleSheetsBootstrap
      : snapshot.bootstrap;
    const resolvedTabs = buildResolvedAdminGoogleSheetTabs(bootstrap?.tabs, { routePath });
    const shouldHydrateBootstrap = shouldHydrateEmptyAdminGoogleSheetsBootstrapFromCache(bootstrap, resolvedTabs);

    if (shouldHydrateBootstrap && bootstrap) {
      state.adminGoogleSheetsBootstrap = bootstrap;
    }
    state.adminGoogleSheetTabs = shouldHydrateBootstrap ? resolvedTabs : [];

    const currentEpoch = Number(state.adminGoogleSheetsPayloadEpoch || 0);
    const payloadsByKey = snapshot.payloadsByKey && typeof snapshot.payloadsByKey === "object"
      ? snapshot.payloadsByKey
      : {};
    state.adminGoogleSheetPayloadByKey = state.adminGoogleSheetPayloadByKey && typeof state.adminGoogleSheetPayloadByKey === "object"
      ? state.adminGoogleSheetPayloadByKey
      : {};
    state.adminGoogleSheetPayloadEpochByKey = state.adminGoogleSheetPayloadEpochByKey && typeof state.adminGoogleSheetPayloadEpochByKey === "object"
      ? state.adminGoogleSheetPayloadEpochByKey
      : {};
    state.adminGoogleSheetPayloadErrorByKey = state.adminGoogleSheetPayloadErrorByKey && typeof state.adminGoogleSheetPayloadErrorByKey === "object"
      ? state.adminGoogleSheetPayloadErrorByKey
      : {};

    for (const [key, payload] of Object.entries(payloadsByKey)) {
      if (!isAdminGoogleSheetTabKeyFn(key) || !payload || typeof payload !== "object") {
        continue;
      }
      state.adminGoogleSheetPayloadByKey[key] = payload;
      state.adminGoogleSheetPayloadEpochByKey[key] = currentEpoch;
      state.adminGoogleSheetPayloadErrorByKey[key] = "";
    }

    state.adminGoogleSheetsCacheHydrated = shouldHydrateBootstrap;
    if (state.adminLegacyRoutePath && state.adminTab === DEFAULT_ADMIN_TAB && maybeResolveLegacyAdminAliasToSheetTab) {
      maybeResolveLegacyAdminAliasToSheetTab({ historyMode: "replace" });
    }
    return true;
  }

  function persistAdminGoogleSheetsCache(options = {}) {
    const state = options.state && typeof options.state === "object" ? options.state : null;
    const cacheRuntime = options.cacheRuntime || global.SPMSAdminGoogleSheetsCacheRuntime || null;
    const isAdminGoogleSheetTabKeyFn = typeof options.isAdminGoogleSheetTabKey === "function"
      ? options.isAdminGoogleSheetTabKey
      : isAdminGoogleSheetTabKey;

    if (!state || !cacheRuntime || typeof cacheRuntime.writeAdminGoogleSheetsCache !== "function") {
      return false;
    }
    if (!state.adminGoogleSheetsBootstrap || typeof state.adminGoogleSheetsBootstrap !== "object") {
      return false;
    }

    const payloadsByKey = {};
    const sourcePayloads = state.adminGoogleSheetPayloadByKey && typeof state.adminGoogleSheetPayloadByKey === "object"
      ? state.adminGoogleSheetPayloadByKey
      : {};
    for (const [key, payload] of Object.entries(sourcePayloads)) {
      if (!isAdminGoogleSheetTabKeyFn(key) || !payload || typeof payload !== "object") {
        continue;
      }
      payloadsByKey[key] = payload;
    }

    return cacheRuntime.writeAdminGoogleSheetsCache({
      bootstrap: state.adminGoogleSheetsBootstrap,
      payloadsByKey,
    });
  }

  global.SPMSAdminTabsRuntime = {
    DEFAULT_ADMIN_GOOGLE_SHEETS_SUBTITLE,
    DEFAULT_ADMIN_TAB,
    DEFAULT_ADMIN_TAB_ROUTE_PATH,
    buildResolvedAdminGoogleSheetTabs,
    hydrateAdminGoogleSheetsCacheOnFirstProtectedRender,
    isAdminGoogleSheetTabKey,
    normalizeAdminTab,
    readAdminGoogleSheetsCacheSnapshot,
    resolveUiModeFromLocation,
    persistAdminGoogleSheetsCache,
  };
})(window);
