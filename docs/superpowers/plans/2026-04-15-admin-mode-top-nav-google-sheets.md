# Admin Mode Top Navigation With Google Sheet Tabs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin-only top navigation that keeps the current SPMS admin project-status page as the default tab and adds four Google Sheet-backed tabs with URL-backed tab state.

**Architecture:** Extend the existing single-page frontend instead of creating new routes. Keep `프로젝트 현황` on the current admin render path, and render the other four tabs through one shared embed panel driven by a small admin-tab config and the `admin_tab` query parameter.

**Tech Stack:** Vanilla JS SPA, static HTML/CSS, Node frontend source tests, Python backend unchanged

---

### Task 1: Add the admin-tab state model and URL wiring

**Files:**
- Modify: `frontend/app.js`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
test("hydrateStateFromUrl and syncUrlState support admin_tab", () => {
  const source = readAppSource();
  assert.match(source, /state\.adminTab\s*=/);
  assert.match(source, /params\.get\("admin_tab"\)/);
  assert.match(source, /params\.set\("admin_tab"/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: FAIL because the new admin-tab state and URL handling do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```javascript
const DEFAULT_ADMIN_TAB = "project-status";

const state = {
  // ...
  adminTab: DEFAULT_ADMIN_TAB,
};

function normalizeAdminTab(rawValue) {
  return ADMIN_TABS.some((item) => item.key === rawValue) ? rawValue : DEFAULT_ADMIN_TAB;
}

function hydrateStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  state.adminTab = normalizeAdminTab(params.get("admin_tab") || DEFAULT_ADMIN_TAB);
}

function syncUrlState() {
  const params = new URLSearchParams();
  if (state.adminTab !== DEFAULT_ADMIN_TAB) params.set("admin_tab", state.adminTab);
  window.history.replaceState({}, "", nextUrl);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "feat: add admin tab url state"
```

### Task 2: Render the admin-only top navigation and embed panel shell

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
test("admin tab shell markup and render helpers exist", () => {
  const source = readAppSource();
  assert.match(source, /function renderAdminTopNavigation\(/);
  assert.match(source, /function renderAdminEmbedPanel\(/);
  assert.match(source, /dom\.adminTopNav/);
  assert.match(source, /dom\.adminEmbedPanel/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: FAIL because the admin navigation render helpers and DOM bindings are missing.

- [ ] **Step 3: Write minimal implementation**

```html
<section id="admin-top-nav" class="admin-top-nav hidden">
  <div id="admin-top-nav-list" class="admin-top-nav-list"></div>
</section>

<section id="admin-embed-panel" class="panel panel-admin-embed hidden">
  <div class="panel-heading">
    <div>
      <p id="admin-embed-kicker" class="kicker">관리자 탭</p>
      <h2 id="admin-embed-title">-</h2>
    </div>
  </div>
  <p id="admin-embed-subtitle" class="hero-subcopy"></p>
  <iframe id="admin-embed-frame" class="admin-embed-frame hidden" loading="lazy"></iframe>
  <div id="admin-embed-empty" class="empty-state hidden"></div>
</section>
```

```javascript
function renderAdminTopNavigation() {
  dom.adminTopNavList.innerHTML = ADMIN_TABS.map((item) => `
    <button
      class="admin-top-nav-button${item.key === state.adminTab ? " is-active" : ""}"
      type="button"
      data-admin-tab="${item.key}"
    >${escapeHtml(item.label)}</button>
  `).join("");
}

function renderAdminEmbedPanel() {
  const activeTab = getActiveAdminTab();
  const isProjectStatus = activeTab.key === DEFAULT_ADMIN_TAB;
  dom.adminEmbedPanel.classList.toggle("hidden", !isAdminEmbedTabActive());
  dom.layoutGrid.classList.toggle("hidden", adminMode && !isProjectStatus);
}
```

```css
.admin-top-nav { margin: 0 0 18px; }
.admin-top-nav-list { display: flex; gap: 10px; flex-wrap: wrap; }
.admin-top-nav-button.is-active { background: var(--text); color: var(--panel-strong); }
.panel-admin-embed { grid-column: span 12; }
.admin-embed-frame { width: 100%; min-height: 72vh; border: 0; }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/styles.css frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "feat: add admin tab shell"
```

### Task 3: Bind admin tab clicks and preserve current admin content

**Files:**
- Modify: `frontend/app.js`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
test("applyUiMode keeps project-status on the existing admin content path and hides it for embed tabs", () => {
  const source = readAppSource();
  assert.match(source, /state\.adminTab === DEFAULT_ADMIN_TAB/);
  assert.match(source, /dom\.layoutGrid\.classList\.toggle\("hidden",/);
  assert.match(source, /data-admin-tab/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: FAIL because tab click handling and project-status/embed switching are not implemented yet.

- [ ] **Step 3: Write minimal implementation**

```javascript
function setAdminTab(nextTab) {
  const normalized = normalizeAdminTab(nextTab);
  if (state.adminTab === normalized) return;
  state.adminTab = normalized;
  syncUrlState();
  applyUiMode();
}

dom.adminTopNav?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-admin-tab]");
  if (!button) return;
  setAdminTab(button.getAttribute("data-admin-tab"));
});

function applyUiMode() {
  const adminMode = state.uiMode === "admin";
  const showingProjectStatus = adminMode && state.adminTab === DEFAULT_ADMIN_TAB;
  dom.adminTopNav?.classList.toggle("hidden", !adminMode);
  dom.layoutGrid?.classList.toggle("hidden", adminMode && !showingProjectStatus);
  dom.adminEmbedPanel?.classList.toggle("hidden", !adminMode || showingProjectStatus);
  renderAdminTopNavigation();
  renderAdminEmbedPanel();
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "feat: switch admin tabs inline"
```

### Task 4: Add sheet-tab configuration and safe placeholder embed behavior

**Files:**
- Modify: `frontend/app.js`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
test("sheet-backed admin tabs are configured with labels and placeholder metadata", () => {
  const source = readAppSource();
  assert.match(source, /설계리스트/);
  assert.match(source, /발주예정/);
  assert.match(source, /로스트/);
  assert.match(source, /대리점 리스트/);
  assert.match(source, /embedPlaceholder/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: FAIL because the new tab configuration and placeholder embed behavior are missing.

- [ ] **Step 3: Write minimal implementation**

```javascript
const ADMIN_TABS = [
  { key: "project-status", label: "프로젝트 현황", type: "existing" },
  { key: "design-list", label: "설계리스트", type: "embed", embedUrl: "", embedPlaceholder: "구글시트 URL 연결 대기" },
  { key: "planned-orders", label: "발주예정", type: "embed", embedUrl: "", embedPlaceholder: "구글시트 URL 연결 대기" },
  { key: "lost", label: "로스트", type: "embed", embedUrl: "", embedPlaceholder: "구글시트 URL 연결 대기" },
  { key: "agency-list", label: "대리점 리스트", type: "embed", embedUrl: "", embedPlaceholder: "구글시트 URL 연결 대기" },
];

function renderAdminEmbedPanel() {
  if (activeTab.embedUrl) {
    dom.adminEmbedFrame.src = activeTab.embedUrl;
  } else {
    dom.adminEmbedEmpty.textContent = `${activeTab.label} URL 미설정`;
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs
git commit -m "feat: configure admin sheet tabs"
```

### Task 5: Verify no user-mode regression

**Files:**
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`
- Test: `tests/frontend/test_tracker_entry_app_integration.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
test("admin navigation remains hidden for user mode", () => {
  const source = readAppSource();
  assert.match(source, /dom\.adminTopNav\?\.classList\.toggle\("hidden", !adminMode\)/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_tracker_entry_app_integration.mjs`
Expected: FAIL until the admin-only visibility rule is present.

- [ ] **Step 3: Write minimal implementation**

```javascript
function applyUiMode() {
  dom.adminTopNav?.classList.toggle("hidden", !adminMode);
  if (!adminMode) {
    dom.adminEmbedPanel?.classList.add("hidden");
    dom.layoutGrid?.classList.remove("hidden");
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_tracker_entry_app_integration.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_tracker_entry_app_integration.mjs
git commit -m "test: cover admin-only tab visibility"
```
