# User Mode Shared Google Sheets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let 사용자모드 land on `프로젝트 현황` and use the same Google Sheets-backed tab/navigation shell as 운영자모드, while hiding sync controls and operator-only wording from 사용자모드.

**Architecture:** Keep one shared frontend shell for `프로젝트 현황` and Google Sheets tabs, but explicitly separate `shared tab visibility` from `admin mode`. Persist mode in the URL with a dedicated query parameter so both modes can use `/app/project-status` without ambiguity, reuse the existing Google Sheets bootstrap/payload APIs, and gate sync controls and operator copy on `uiMode === "admin"` only.

**Tech Stack:** Vanilla JavaScript SPA, existing Google Sheets runtime, node test runner, existing frontend integration harnesses

---

## File Map

- Modify: `frontend/app.js`
  - separate shared project-status/tab routing from admin-only mode
  - make user mode default to `/app/project-status`
  - reuse shared top navigation and embed panel in both modes
  - hide sync controls, sync feedback, and operator subtitle/copy in user mode
- Modify: `tests/frontend/test_admin_tabs_app_integration.mjs`
  - add user-mode shared-shell and admin-regression tests using the existing harness
- Modify: `tests/frontend/test_admin_google_sheets_cache_app_integration.mjs`
  - verify stale-first/shared-cache behavior still works when the shared shell is shown in user mode

### Task 1: Add failing integration tests for shared user-mode Google Sheets behavior

**Files:**
- Modify: `tests/frontend/test_admin_tabs_app_integration.mjs`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Add the failing user-mode default landing and shared-tab tests**

```js
test("user mode defaults to project-status shared shell without switching to admin mode", async () => {
  const harness = loadAppForBehaviorTest({ pathname: "/app/", search: "" });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.equal(harness.hooks.state.adminTab, "project-status");
  assert.equal(harness.window.location.pathname, "/app/project-status");
  assert.equal(harness.elements["#admin-embed-panel"].classList.contains("hidden"), false);
});

test("user mode shows shared google sheets tabs without sync controls or admin copy", async () => {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/project-status",
    search: "?admin_tab=sheet-22",
  });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  harness.resolveBootstrap({
    sync_status: "synced",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.match(harness.elements["#admin-top-nav-list"].innerHTML, /Lost/);
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), true);
  assert.equal(harness.elements["#admin-google-sheets-sync-feedback"].textContent, "");
  assert.doesNotMatch(harness.elements["#admin-embed-subtitle"].textContent, /Google Sheets read-only view/i);
});

test("admin mode still shows sync controls on the shared google sheets shell", async () => {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/project-status",
    search: "?mode=admin&admin_tab=sheet-22",
  });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();

  harness.resolveBootstrap({
    sync_status: "queued",
    tabs: {
      "sheet-22": { sheet_order: 1, raw_title: "Lost", sheet_id: 22 },
    },
  });
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "admin");
  assert.equal(harness.elements["#admin-google-sheets-sync-button"].classList.contains("hidden"), false);
});
```

- [ ] **Step 2: Run the integration tests to verify they fail**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected:
- FAIL because `/app/` still hydrates to user mode outside the shared shell
- FAIL because `/app/project-status` still forces `uiMode === "admin"`
- FAIL because user mode does not yet render the shared tab shell and still ties it to admin mode

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "test: cover shared google sheets shell in user mode"
```

### Task 2: Implement shared routing and mode-aware Google Sheets shell behavior

**Files:**
- Modify: `frontend/app.js`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Update URL state rules so both modes can use `/app/project-status`**

```js
function buildUrlForState({ pathname = null, uiMode = state.uiMode, adminTab = state.adminTab } = {}) {
  const params = new URLSearchParams();
  // existing run/tracker/report params...

  const sharedProjectStatusRoute = adminTab && (
    adminTab === DEFAULT_ADMIN_TAB
    || isAdminGoogleSheetTabKey(adminTab)
  );

  if (uiMode === "admin") {
    params.set("mode", "admin");
  }
  if (adminTab && adminTab !== DEFAULT_ADMIN_TAB) {
    params.set("admin_tab", adminTab);
  }

  const nextPath = pathname || (
    sharedProjectStatusRoute ? getAdminRoutePath(adminTab) : APP_ROOT_PATH
  );
  return `${nextPath}${params.toString() ? `?${params.toString()}` : ""}`;
}

function hydrateStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const routeTab = getAdminTabByPathname(window.location.pathname);
  state.adminLegacyRoutePath = params.has("admin_tab") ? "" : resolveLegacyAdminRoutePath(window.location.pathname);
  state.adminTab = normalizeAdminTab(params.get("admin_tab") || routeTab?.key || DEFAULT_ADMIN_TAB);
  state.uiMode = params.get("mode") === "admin" && canUseAdminMode() ? "admin" : "user";
}
```

- [ ] **Step 2: Make user mode land on the shared `프로젝트 현황` route**

```js
function resolveStatePathname() {
  const sharedProjectStatusRoute = state.adminTab === DEFAULT_ADMIN_TAB || isAdminGoogleSheetTabKey(state.adminTab);
  if (sharedProjectStatusRoute) {
    return getAdminRoutePath(state.adminTab);
  }
  return window.location.pathname || APP_ROOT_PATH;
}

function applyUiMode() {
  // existing state syncing...
  if (state.uiMode === "user" && window.location.pathname === APP_ROOT_PATH) {
    syncUrlState({ historyMode: "replace", uiMode: "user", adminTab: DEFAULT_ADMIN_TAB });
  }
  // continue normal rendering...
}
```

- [ ] **Step 3: Split shared shell visibility from admin-only controls**

```js
function shouldShowSharedGoogleSheetsShell() {
  if (!canLoadProtectedConsoleData()) {
    return false;
  }
  return state.adminTab === DEFAULT_ADMIN_TAB || isAdminGoogleSheetTabKey(state.adminTab) || isPendingLegacyAdminAlias();
}

function shouldShowAdminGoogleSheetsControls() {
  return state.uiMode === "admin" && canLoadProtectedConsoleData();
}

function renderAdminTopNavigation() {
  if (!shouldShowSharedGoogleSheetsShell()) {
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
```

- [ ] **Step 4: Hide operator-only subtitle, sync feedback, and sync button in user mode**

```js
function getSharedGoogleSheetsSubtitle(activeTab, { adminMode, showGoogleSheetsOverview }) {
  if (!adminMode) {
    return "";
  }
  if (showGoogleSheetsOverview) {
    return "설계리스트 등 관리자 시트 연결 상태";
  }
  return activeTab.subtitle || "";
}

function renderAdminEmbedPanel() {
  const adminMode = state.uiMode === "admin";
  const panelVisible = shouldShowSharedGoogleSheetsShell() || shouldShowAdminGoogleSheetsOverviewPanel(...);
  dom.adminEmbedSubtitle.textContent = getSharedGoogleSheetsSubtitle(activeTab, { adminMode, showGoogleSheetsOverview });
  dom.adminGoogleSheetsSyncFeedback.classList.toggle("hidden", !adminMode || !panelVisible || !state.adminGoogleSheetsSyncMessage);
  dom.adminGoogleSheetsSyncFeedback.textContent = adminMode && panelVisible ? state.adminGoogleSheetsSyncMessage : "";
  dom.adminGoogleSheetsSyncButton.classList.toggle("hidden", !adminMode || !panelVisible || !ADMIN_GOOGLE_SHEETS_RUNTIME);
}
```

- [ ] **Step 5: Keep polling and sheet bootstrap behavior safe in both modes**

```js
function shouldPollAdminGoogleSheets() {
  if (!state.autoRefresh || !ADMIN_GOOGLE_SHEETS_RUNTIME || !canLoadProtectedConsoleData()) {
    return false;
  }
  return shouldShowSharedGoogleSheetsShell();
}

function syncUiModeFromLocation() {
  const params = new URLSearchParams(window.location.search);
  state.uiMode = params.get("mode") === "admin" && canUseAdminMode() ? "admin" : "user";
  const routeTab = getAdminTabByPathname(window.location.pathname);
  if (routeTab) {
    state.adminLegacyRoutePath = params.has("admin_tab") ? "" : resolveLegacyAdminRoutePath(window.location.pathname);
    state.adminTab = normalizeAdminTab(params.get("admin_tab") || routeTab.key || state.adminTab);
  }
}
```

- [ ] **Step 6: Re-run the integration tests**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 7: Commit the routing and shared-shell implementation**

```bash
git add frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "feat: share google sheets shell with user mode"
```

### Task 3: Add stale-cache regression coverage and run the focused frontend suite

**Files:**
- Modify: `tests/frontend/test_admin_google_sheets_cache_app_integration.mjs`
- Test: `tests/frontend/test_admin_google_sheets_cache_app_integration.mjs`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Add a failing stale-first user-mode regression test**

```js
test("stale-first user mode keeps cached google sheet table visible on shared project-status shell", async () => {
  const harness = loadAppForBehaviorTest({
    pathname: "/app/project-status",
    search: "?admin_tab=sheet-11",
    cacheSnapshot: {
      bootstrap: {
        sync_status: "synced",
        tabs: {
          "sheet-11": { sheet_order: 1, raw_title: "Design List", sheet_id: 11 },
        },
      },
      payloads: {
        "sheet-11": { headers: ["Name"], rows: [["Cached Alice"]] },
      },
    },
  });
  authorizeHarness(harness);

  harness.hooks.hydrateStateFromUrl();
  harness.hooks.syncUiModeFromLocation();
  harness.hooks.applyUiMode();
  await harness.flushUi();

  assert.equal(harness.hooks.state.uiMode, "user");
  assert.match(harness.elements["#admin-google-sheet-table"].innerHTML, /Cached Alice/);
});
```

- [ ] **Step 2: Run the cache regression test to verify it fails first if needed**

Run: `node --test tests/frontend/test_admin_google_sheets_cache_app_integration.mjs`
Expected: either a new failing assertion around user-mode shared shell visibility or an updated harness expectation if the shell is still admin-only

- [ ] **Step 3: Make any minimal follow-up app.js adjustments required by the cache regression**

```js
function maybePreloadAdminGoogleSheetsBootstrap() {
  if (!canLoadProtectedConsoleData()) {
    return;
  }
  if (!shouldShowSharedGoogleSheetsShell()) {
    return;
  }
  // existing preload behavior...
}
```

- [ ] **Step 4: Run the focused frontend verification suite**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_google_sheets_cache_app_integration.mjs tests/frontend/test_admin_routes_vercel_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit the regression coverage**

```bash
git add frontend/app.js tests/frontend/test_admin_google_sheets_cache_app_integration.mjs
git commit -m "test: cover shared google sheets cache behavior in user mode"
```
