import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const appCoreRuntimePath = path.resolve(__dirname, "../../frontend/app-core-runtime.js");
const appBootstrapBridgePath = path.resolve(__dirname, "../../frontend/app-bootstrap-bridge.js");
const appRuntimeBodyShellRuntimePath = path.resolve(__dirname, "../../frontend/app-runtime-body-shell-runtime.js");
const CANONICAL_URL_STATE_STORAGE_KEY = "notice-winner-pipeline-web.canonicalUrlState.v1";

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function readAppCoreRuntimeSource() {
  return fs.readFileSync(appCoreRuntimePath, "utf8");
}

function readAppBootstrapBridgeSource() {
  return fs.readFileSync(appBootstrapBridgePath, "utf8");
}

function readAppRuntimeBodyShellRuntimeSource() {
  return fs.readFileSync(appRuntimeBodyShellRuntimePath, "utf8");
}

function findSourceIndex(source, patterns, fromIndex = 0) {
  for (const pattern of patterns) {
    const index = source.indexOf(pattern, fromIndex);
    if (index >= 0) {
      return index;
    }
  }
  return -1;
}

function normalizeWhitespace(source) {
  return source.replace(/\s+/g, " ").trim();
}

function extractSourceSlice(startPatterns, endPatterns) {
  const source = readAppSource();
  const start = findSourceIndex(source, startPatterns);
  const end = findSourceIndex(source, endPatterns, start);
  assert.ok(start >= 0, `slice start should exist: ${startPatterns[0]}`);
  assert.ok(end > start, `slice end should exist: ${endPatterns[0]}`);
  return source.slice(start, end).trim();
}

function createBaseState() {
  return {
    adminTab: "runs",
    uiMode: "user",
    runFilters: {
      status: "",
      runType: "",
      from: "",
      to: "",
      page: 1,
      pageSize: 20,
    },
    selectedRunId: null,
    selectedTrackerRunId: null,
    trackerFilters: {
      q: "",
      region: "",
      editedOnly: false,
      page: 1,
      pageSize: 20,
    },
    selectedEntryId: null,
    drawerOpen: false,
    autoRefresh: true,
    reportKey: "phase1-artifact-diff",
    selectedReportJobId: null,
    auth: {
      enabled: true,
      inviteToken: "",
      authenticated: true,
      authorized: true,
      user: { id: "user-1" },
      message: "",
    },
  };
}

function loadUrlStateHelpers({ search = "", pathname = "/app/" } = {}) {
  const urlSource = extractSourceSlice(
    ["function buildUrlForState({ pathname = null, uiMode = state.uiMode, adminTab = state.adminTab, persist = false } = {}) {"],
    ["function openDrawer() {"],
  );
  const hydrateSource = extractSourceSlice(
    ["function hydrateStateFromUrl() {"],
    ["function renderSyncMeta() {"],
  );
  const replaceCalls = [];
  const pushCalls = [];
  const sessionStorageMap = new Map();
  const state = createBaseState();
  const context = vm.createContext({
    console,
    state,
    window: {
      location: {
        search,
        pathname,
      },
      history: {
        replaceState: (_state, _title, url) => replaceCalls.push(url),
        pushState: (_state, _title, url) => pushCalls.push(url),
      },
      sessionStorage: {
        getItem: (key) => sessionStorageMap.has(key) ? sessionStorageMap.get(key) : null,
        setItem: (key, value) => sessionStorageMap.set(key, String(value)),
        removeItem: (key) => sessionStorageMap.delete(key),
      },
    },
    URLSearchParams,
    DEFAULT_ADMIN_TAB: "runs",
    getAdminTabByPathname: () => null,
    normalizeAdminTab: (value) => String(value || ""),
    clampPage: (value, fallback) => {
      const parsed = Number.parseInt(String(value || ""), 10);
      return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
    },
    normalizeTrackerRegionFilter: (value) => String(value || "").trim(),
    getAdminRoutePath: (adminTab) => `/app/admin/${adminTab}`,
    resolveStatePathname: () => "/app/",
  });
  const exports = vm.runInContext(
    `(function () { ${urlSource}; ${hydrateSource}; return { buildUrlForState, syncUrlState, hydrateStateFromUrl }; })()`,
    context,
    { filename: appPath },
  );
  return {
    ...exports,
    state,
    replaceCalls,
    pushCalls,
    getCanonicalUrlState: () => context.window.sessionStorage.getItem(CANONICAL_URL_STATE_STORAGE_KEY) || "",
  };
}

function loadHydrateWrapper({ bridgeHydrateImpl, search = "", pathname = "/app/" } = {}) {
  const hydrateWrapperSource = extractSourceSlice(
    ["function getAppBootstrapBridge() {"],
    ["function renderSyncMeta() {"],
  );
  const state = createBaseState();
  const bridgeCalls = [];
  const bootstrapRuntime = { hydrateStateFromUrl() {} };
  const context = vm.createContext({
    console,
    state,
    window: {
      location: {
        search,
        pathname,
      },
      APP_BOOTSTRAP_BRIDGE: {
        createAppBootstrapBridge(options) {
          bridgeCalls.push(options);
          return {
            hydrateStateFromUrl() {
              return bridgeHydrateImpl(options);
            },
          };
        },
      },
    },
    BOOTSTRAP_RUNTIME: bootstrapRuntime,
    clampPage: (value, fallback) => {
      const parsed = Number.parseInt(String(value || ""), 10);
      return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
    },
    normalizeTrackerRegionFilter: (value) => String(value || "").trim(),
    appBootstrapBridge: null,
  });
  const exports = vm.runInContext(
    `(function () { ${hydrateWrapperSource}; return { hydrateStateFromUrl, getAppBootstrapBridge }; })()`,
    context,
    { filename: appPath },
  );
  return {
    ...exports,
    state,
    bridgeCalls,
    window: context.window,
    bootstrapRuntime,
  };
}

function loadBootstrapBridgeHarness({ search = "", pathname = "/app/", bootstrapRuntimeOverrides = {} } = {}) {
  const replaceCalls = [];
  const pushCalls = [];
  const sessionStorageMap = new Map();
  const state = createBaseState();
  const context = vm.createContext({
    console,
    URLSearchParams,
    state,
    window: {
      location: {
        search,
        pathname,
      },
      history: {
        replaceState: (_state, _title, url) => replaceCalls.push(url),
        pushState: (_state, _title, url) => pushCalls.push(url),
      },
      sessionStorage: {
        getItem: (key) => sessionStorageMap.has(key) ? sessionStorageMap.get(key) : null,
        setItem: (key, value) => sessionStorageMap.set(key, String(value)),
        removeItem: (key) => sessionStorageMap.delete(key),
      },
    },
    DEFAULT_ADMIN_TAB: "runs",
    getAdminTabByPathname: () => null,
    normalizeAdminTab: (value) => String(value || ""),
    clampPage: (value, fallback) => {
      const parsed = Number.parseInt(String(value || ""), 10);
      return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
    },
    normalizeTrackerRegionFilter: (value) => String(value || "").trim(),
    resolveStatePathname: () => "/app/",
  });
  vm.runInContext(
    `${readAppBootstrapBridgeSource().replace("export function createAppBootstrapBridge", "function createAppBootstrapBridge")}
    this.__bridgeExports = window.APP_BOOTSTRAP_BRIDGE;`,
    context,
    { filename: appBootstrapBridgePath },
  );
  const bootstrapRuntime = {
    hydrateStateFromUrl({ state: runtimeState, window: runtimeWindow, clampPage, normalizeTrackerRegionFilter }) {
      const params = new URLSearchParams(runtimeWindow.location.search);
      const pathname = runtimeWindow.location.pathname;
      const normalizedPathname = pathname.replace(/\/+$/, "") || "/";
      const routeTab = context.getAdminTabByPathname(pathname);
      runtimeState.adminLegacyRoutePath = params.has("admin_tab")
        ? ""
        : ({
          "/app/design-list": "/app/design-list",
          "/app/planned-orders": "/app/planned-orders",
          "/app/lost": "/app/lost",
          "/app/agency-list": "/app/agency-list",
        })[normalizedPathname] || "";
      runtimeState.adminTab = context.normalizeAdminTab(params.get("admin_tab") || routeTab?.key || context.DEFAULT_ADMIN_TAB);
      runtimeState.uiMode = params.get("mode") === "admin" || routeTab?.key === context.DEFAULT_ADMIN_TAB
        || Boolean(runtimeState.adminLegacyRoutePath)
        ? "admin"
        : "user";
      runtimeState.runFilters.status = params.get("run_status") || "";
      runtimeState.runFilters.runType = params.get("run_type") || "";
      runtimeState.runFilters.from = params.get("run_from") || "";
      runtimeState.runFilters.to = params.get("run_to") || "";
      runtimeState.runFilters.page = clampPage(params.get("run_page"), 1);
      runtimeState.runFilters.pageSize = clampPage(params.get("run_page_size"), 20);
      runtimeState.selectedRunId = params.get("run_id") || null;
      runtimeState.selectedTrackerRunId = params.get("tracker_run_id") || null;
      runtimeState.trackerFilters.q = params.get("tracker_q") || "";
      runtimeState.trackerFilters.region = normalizeTrackerRegionFilter(params.get("tracker_region") || "");
      runtimeState.trackerFilters.editedOnly = false;
      runtimeState.trackerFilters.page = clampPage(params.get("tracker_page"), 1);
      runtimeState.trackerFilters.pageSize = clampPage(params.get("tracker_page_size"), 20);
      runtimeState.selectedEntryId = params.get("entry_id") || null;
      runtimeState.drawerOpen = Boolean(runtimeState.selectedEntryId);
      runtimeState.autoRefresh = params.get("auto_refresh") !== "0";
      runtimeState.reportKey = params.get("report_key") || "phase1-artifact-diff";
      runtimeState.selectedReportJobId = params.get("report_job_id") || null;
      runtimeState.auth.inviteToken = params.get("invite_token") || "";
      if (params.has("entry_id")) {
        const nextParams = new URLSearchParams(runtimeWindow.location.search);
        nextParams.delete("entry_id");
        const next = nextParams.toString();
        runtimeWindow.history.replaceState({}, "", `/app/${next ? `?${next}` : ""}`);
      }
    },
    ...bootstrapRuntimeOverrides,
  };
  const bridge = context.__bridgeExports.createAppBootstrapBridge({
    bootstrapRuntime,
    state,
    window: context.window,
    clampPage: context.clampPage,
    normalizeTrackerRegionFilter: context.normalizeTrackerRegionFilter,
  });
  return {
    bridge,
    state,
    replaceCalls,
    pushCalls,
    getCanonicalUrlState: () => context.window.sessionStorage.getItem(CANONICAL_URL_STATE_STORAGE_KEY) || "",
  };
}

function loadCoreApiHelper({ fetchImpl, refreshResult = null, timeoutMode = "deferred" } = {}) {
  const renderCalls = [];
  const refreshCalls = [];
  const state = createBaseState();
  const context = vm.createContext({
    console,
    state,
    window: {
      setTimeout: timeoutMode === "immediate"
        ? (callback) => {
          callback();
          return 1;
        }
        : () => 1,
      clearTimeout: () => {},
    },
    fetch: fetchImpl,
    FormData: class FakeFormData {},
    AbortController,
    Date,
  });
  vm.runInContext(readAppCoreRuntimeSource(), context, { filename: appCoreRuntimePath });
  const runtime = context.window.createAppCoreRuntime({
    window: context.window,
    state,
    fetch: fetchImpl,
    FormData: class FakeFormData {},
    AbortController,
    refreshAuthSessionState: async (options) => {
      refreshCalls.push(options);
      return refreshResult;
    },
    renderAuthUi: () => renderCalls.push("renderAuthUi"),
  });
  return {
    api: runtime.api,
    state,
    renderCalls,
    refreshCalls,
  };
}

function loadShellRuntimeHarness() {
  const replaceCalls = [];
  const pushCalls = [];
  const sessionStorageMap = new Map();
  const state = createBaseState();
  state.adminTab = "project-status";
  state.uiMode = "user";
  state.canonicalUrlStateHydrated = true;
  state.canonicalLocationPathname = "/";
  state.canonicalLocationSearch = "";
  const windowObject = {
    location: { pathname: "/" },
    history: {
      replaceState: (_state, _title, url) => replaceCalls.push(url),
      pushState: (_state, _title, url) => pushCalls.push(url),
    },
    sessionStorage: {
      getItem: (key) => sessionStorageMap.has(key) ? sessionStorageMap.get(key) : null,
      setItem: (key, value) => sessionStorageMap.set(key, String(value)),
      removeItem: (key) => sessionStorageMap.delete(key),
    },
  };
  const context = vm.createContext({
    window: windowObject,
    URLSearchParams,
    console,
  });
  vm.runInContext(readAppRuntimeBodyShellRuntimeSource(), context, { filename: appRuntimeBodyShellRuntimePath });
  return {
    runtime: context.window.SPMSAppRuntimeBodyShellRuntime,
    state,
    windowObject,
    replaceCalls,
    pushCalls,
    getCanonicalUrlState: () => windowObject.sessionStorage.getItem(CANONICAL_URL_STATE_STORAGE_KEY) || "",
  };
}

test("buildUrlForState omits entry_id even when an entry is selected", () => {
  const { buildUrlForState, syncUrlState, state, replaceCalls, getCanonicalUrlState } = loadUrlStateHelpers();
  state.selectedEntryId = "1285dc63-47b8-42ad-a603-37c4b71f20cf";
  state.trackerFilters.q = "school";

  const url = buildUrlForState();

  assert.equal(url, "/");
  assert.equal(getCanonicalUrlState(), "");

  syncUrlState();

  assert.deepEqual(replaceCalls, ["/"]);
  assert.equal(getCanonicalUrlState(), "tracker_q=school");
});

test("shell syncUrlState keeps canonical memory in sync after switching to sales recommendations", () => {
  const { runtime, state, windowObject, pushCalls, getCanonicalUrlState } = loadShellRuntimeHarness();
  state.adminTab = "sales-recommendations";

  runtime.syncUrlState({
    state,
    windowObject,
    buildUrlForStateFn: (options) => runtime.buildUrlForState({
      state,
      uiMode: "user",
      adminTab: "sales-recommendations",
      defaultAdminTab: "project-status",
      persist: options.persist,
    }),
  }, { historyMode: "push", uiMode: "user", adminTab: "sales-recommendations" });

  assert.deepEqual(pushCalls, ["/"]);
  assert.equal(getCanonicalUrlState(), "admin_tab=sales-recommendations");
  assert.equal(state.canonicalUrlStateHydrated, true);
  assert.equal(state.canonicalLocationPathname, "/");
  assert.equal(state.canonicalLocationSearch, "?admin_tab=sales-recommendations");
});

test("app.js hydrateStateFromUrl is a thin bootstrap-bridge wrapper", () => {
  const { hydrateStateFromUrl, getAppBootstrapBridge, state, bridgeCalls, window, bootstrapRuntime } = loadHydrateWrapper({
    bridgeHydrateImpl(options) {
      options.state.selectedEntryId = "wrapped-entry";
      return "bridge-result";
    },
  });

  const result = hydrateStateFromUrl();

  assert.equal(result, "bridge-result");
  assert.equal(state.selectedEntryId, "wrapped-entry");
  assert.equal(bridgeCalls.length, 1);
  assert.equal(bridgeCalls[0].bootstrapRuntime, bootstrapRuntime);
  assert.equal(bridgeCalls[0].state, state);
  assert.equal(bridgeCalls[0].window, window);
  assert.equal(typeof getAppBootstrapBridge, "function");
  assert.doesNotMatch(extractSourceSlice(["function hydrateStateFromUrl() {"], ["function renderSyncMeta() {"]), /URLSearchParams/);
});

test("bootstrap bridge hydrateStateFromUrl keeps the selected entry in state but scrubs entry_id from the address bar", () => {
  const { bridge, state, replaceCalls } = loadBootstrapBridgeHarness({
    search: "?tracker_q=school&entry_id=1285dc63-47b8-42ad-a603-37c4b71f20cf",
  });

  bridge.hydrateStateFromUrl();

  assert.equal(state.selectedEntryId, "1285dc63-47b8-42ad-a603-37c4b71f20cf");
  assert.equal(state.drawerOpen, true);
  assert.deepEqual(replaceCalls, ["/app/?tracker_q=school", "/"]);
});

test("bootstrap bridge falls back to local URL hydration when bootstrap runtime omits hydrateStateFromUrl", () => {
  const { bridge, state, replaceCalls, getCanonicalUrlState } = loadBootstrapBridgeHarness({
    pathname: "/app/project-status/",
    search: "?entry_id=entry-9&tracker_page=4&admin_tab=sheet-22",
    bootstrapRuntimeOverrides: {
      hydrateStateFromUrl: undefined,
    },
  });

  bridge.hydrateStateFromUrl();

  assert.equal(state.uiMode, "admin");
  assert.equal(state.adminTab, "sheet-22");
  assert.equal(state.selectedEntryId, "entry-9");
  assert.equal(state.drawerOpen, true);
  assert.equal(state.trackerFilters.page, 4);
  assert.deepEqual(replaceCalls, ["/"]);
  assert.equal(getCanonicalUrlState(), "tracker_page=4&admin_tab=sheet-22");
});

test("app.js delegates api creation to the shared app-core runtime", () => {
  const source = readAppSource();
  const normalized = normalizeWhitespace(source);

  assert.match(source, /createAppCoreRuntime/);
  assert.match(source, /APP_CORE_RUNTIME_FACTORY/);
  assert.match(
    normalized,
    /const \{ api, flash, setBusy, metricCard, statusBadge, progressPercent, formatJson, formatDate, formatKoreanDate, formatBytes, truncate, clampPage, escapeHtml \} = APP_CORE_RUNTIME;/,
  );
  for (const helperName of [
    "metricCard",
    "statusBadge",
    "progressPercent",
    "formatJson",
    "formatDate",
    "formatKoreanDate",
    "formatBytes",
    "flash",
    "setBusy",
    "truncate",
    "clampPage",
    "escapeHtml",
  ]) {
    assert.doesNotMatch(source, new RegExp(`function ${helperName}\\(`));
  }
  assert.doesNotMatch(source, /async function api\(path, options = \{\}\) \{/);
});

test("api aborts on timeout and preserves external abort behavior", async () => {
  const timeoutRuntime = loadCoreApiHelper({
    fetchImpl: async (_url, options) => {
      assert.equal(options.signal.aborted, true);
      throw Object.assign(new Error("aborted"), { name: "AbortError" });
    },
    timeoutMode: "immediate",
  });
  await assert.rejects(
    timeoutRuntime.api("/api/slow", { timeoutMs: 1 }),
    (error) => String(error?.message || "").startsWith("Request timed out: /api/slow?"),
  );

  const externalAbortController = new AbortController();
  const externalRuntime = loadCoreApiHelper({
    fetchImpl: (_url, options) => new Promise((resolve, reject) => {
      const abortError = Object.assign(new Error("aborted"), { name: "AbortError" });
      if (options.signal.aborted) {
        reject(abortError);
        return;
      }
      options.signal.addEventListener("abort", () => reject(abortError), { once: true });
    }),
  });
  const externalAbortPromise = externalRuntime.api("/api/external", {
    signal: externalAbortController.signal,
    timeoutMs: 5000,
  });
  externalAbortController.abort();
  await assert.rejects(
    externalAbortPromise,
    (error) => error?.name === "AbortError" && error?.message === "aborted",
  );
});

test("api retries protected 401s after refreshing auth state with a forced silent refresh", async () => {
  let callCount = 0;
  const { api, refreshCalls } = loadCoreApiHelper({
    fetchImpl: async (url) => {
      callCount += 1;
      if (callCount === 1) {
        return {
          ok: false,
          status: 401,
          statusText: "Unauthorized",
          url,
          headers: {
            get: () => "application/json",
          },
          json: async () => ({ error: { message: "session expired" } }),
        };
      }
      return {
        ok: true,
        status: 200,
        statusText: "OK",
        url,
        headers: {
          get: () => "application/json",
        },
        json: async () => ({ ok: true, retried: true }),
      };
    },
    refreshResult: { authenticated: true, authorized: true },
  });

  const payload = await api("/api/protected");

  assert.deepEqual(payload, { ok: true, retried: true });
  assert.equal(callCount, 2);
  assert.deepEqual(JSON.parse(JSON.stringify(refreshCalls)), [{ silent: true, force: true }]);
});

test("api forwards the in-memory access token on protected requests", async () => {
  let capturedHeaders = null;
  const { api, state } = loadCoreApiHelper({
    fetchImpl: async (_url, options = {}) => {
      capturedHeaders = options.headers || {};
      return {
        ok: true,
        status: 200,
        statusText: "OK",
        url: "/api/protected",
        headers: {
          get: () => "application/json",
        },
        json: async () => ({ ok: true }),
      };
    },
  });

  state.auth.accessToken = "access-token-123";
  await api("/api/protected", { cacheBust: false });

  assert.equal(capturedHeaders.Authorization, "Bearer access-token-123");
});

test("api uses a polite session-expired message when a protected request returns 401", async () => {
  const { api, state, renderCalls } = loadCoreApiHelper({
    fetchImpl: async () => ({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      url: "/api/protected",
      headers: {
        get: () => "application/json",
      },
      json: async () => ({ error: { message: "session expired" } }),
    }),
    refreshResult: null,
  });

  await assert.rejects(
    api("/api/protected"),
    (error) => error?.name === "ApiRequestError" && error?.status === 401,
  );
  assert.equal(state.auth.authenticated, false);
  assert.equal(state.auth.authorized, false);
  assert.equal(state.auth.user, null);
  assert.equal(state.auth.message, "세션이 만료되었습니다. 다시 로그인해 주세요.");
  assert.deepEqual(renderCalls, ["renderAuthUi"]);
});
