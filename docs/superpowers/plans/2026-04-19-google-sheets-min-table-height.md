# Google Sheets Minimum Table Height Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Google Sheets 기반 탭에서 필터 후 행 수가 줄어들어도 각 시트의 테이블 래퍼가 최초 표시 높이 아래로 줄어들지 않게 만든다.

**Architecture:** `frontend/app.js`가 시트별 최소 높이 상태를 보관하고, `renderAdminGoogleSheetTable()` 렌더 직후 실제 wrapper 높이를 측정해 상태를 갱신한다. `frontend/admin-google-sheets-runtime.js`는 이 값을 wrapper markup에 반영하고, `frontend/styles.css`는 공통 `min-height` 스타일을 제공한다.

**Tech Stack:** vanilla JavaScript, DOM rendering in `frontend/app.js`, runtime markup helpers, Node built-in test runner

---

### Task 1: Runtime markup에 최소 높이 contract 추가

**Files:**
- Modify: `frontend/admin-google-sheets-runtime.js`
- Test: `tests/frontend/test_admin_google_sheets_runtime.mjs`
- Test: `tests/frontend/test_admin_google_sheets_filters_runtime.mjs`

- [ ] **Step 1: 최소 높이 markup 검증 테스트를 먼저 추가**

```js
test("buildAdminGoogleSheetTableView renders a min-height style when provided", () => {
  const runtime = loadRuntime();

  const view = runtime.buildAdminGoogleSheetTableView(
    {
      headers: ["Name"],
      rows: [["Alice"]],
    },
    {
      escapeHtml: (value) => String(value),
      minTableHeightPx: 512,
    },
  );

  assert.match(view.html, /admin-google-sheet-table-wrap/);
  assert.match(view.html, /--admin-google-sheet-min-table-height:\s*512px/);
  assert.match(view.html, /min-height:\s*var\(--admin-google-sheet-min-table-height\)/);
});
```

- [ ] **Step 2: 테스트를 돌려 실패를 확인**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_google_sheets_filters_runtime.mjs`

Expected: `buildAdminGoogleSheetTableView renders a min-height style when provided` 관련 assertion failure

- [ ] **Step 3: runtime helper에 최소 높이 옵션을 최소 구현으로 추가**

```js
function buildAdminGoogleSheetTableView(payload, helpers = {}) {
  const {
    escapeHtml: escapeHtmlHelper = escapeHtml,
    minTableHeightPx = 0,
  } = helpers;

  const normalizedMinHeight = Number(minTableHeightPx);
  const minHeightStyle = Number.isFinite(normalizedMinHeight) && normalizedMinHeight > 0
    ? ` style="--admin-google-sheet-min-table-height: ${escapeHtmlHelper(String(Math.round(normalizedMinHeight)))}px; min-height: var(--admin-google-sheet-min-table-height);"`
    : "";

  // ...
  return {
    html: `
      <div class="admin-google-sheet-table-wrap"${minHeightStyle}>
        <table class="admin-google-sheet-table">
          ...
        </table>
      </div>
    `,
  };
}
```

- [ ] **Step 4: 테스트를 다시 돌려 통과 확인**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_google_sheets_filters_runtime.mjs`

Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add frontend/admin-google-sheets-runtime.js tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_google_sheets_filters_runtime.mjs
git commit -m "feat: add Google Sheets min-height markup contract"
```

### Task 2: 시트별 최소 높이 상태를 app controller에 추가

**Files:**
- Modify: `frontend/app.js`
- Test: `tests/frontend/test_admin_google_sheets_filters_app_integration.mjs`

- [ ] **Step 1: app integration에 failing test 추가**

```js
test("admin google sheets preserves the measured minimum height across filtered rerenders", () => {
  const harness = seedGoogleSheetHarness();
  const table = harness.elements["#admin-google-sheet-table"];
  let measuredHeight = 540;
  table.querySelector = (selector) => {
    if (selector !== ".admin-google-sheet-table-wrap") {
      return null;
    }
    return {
      offsetHeight: measuredHeight,
      getBoundingClientRect: () => ({ height: measuredHeight }),
    };
  };

  harness.hooks.renderAdminEmbedPanel();
  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 540);
  assert.match(table.innerHTML, /540px/);

  measuredHeight = 120;
  harness.hooks.openAdminGoogleSheetFilterPopup("sheet-1", 0);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Beta", false);
  harness.hooks.toggleAdminGoogleSheetPopupValue("Gamma", false);
  harness.hooks.confirmAdminGoogleSheetPopup();

  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 540);
  assert.match(table.innerHTML, /540px/);
});
```

- [ ] **Step 2: 위 테스트를 단독 실행해 실패 확인**

Run: `node --test tests/frontend/test_admin_google_sheets_filters_app_integration.mjs`

Expected: `adminGoogleSheetMinHeightByKey`가 없거나 `540px` markup이 없어서 FAIL

- [ ] **Step 3: 상태/측정/재적용 로직을 최소 구현**

```js
function getAdminGoogleSheetMinHeight(sheetKey) {
  const key = String(sheetKey || "").trim();
  if (!key) {
    return 0;
  }
  return Number(state.adminGoogleSheetMinHeightByKey[key] || 0) || 0;
}

function measureAdminGoogleSheetTableHeight(sheetKey) {
  const key = String(sheetKey || "").trim();
  const wrap = dom.adminGoogleSheetTable?.querySelector?.(".admin-google-sheet-table-wrap");
  if (!key || !wrap) {
    return 0;
  }
  const rectHeight = Number(wrap.getBoundingClientRect?.().height || 0);
  const offsetHeight = Number(wrap.offsetHeight || 0);
  return Math.max(rectHeight, offsetHeight, 0);
}

function syncAdminGoogleSheetMinHeight(sheetKey) {
  const key = String(sheetKey || "").trim();
  const measuredHeight = Math.round(measureAdminGoogleSheetTableHeight(key));
  if (!key || measuredHeight <= 0) {
    return;
  }
  const currentHeight = getAdminGoogleSheetMinHeight(key);
  if (measuredHeight > currentHeight) {
    state.adminGoogleSheetMinHeightByKey[key] = measuredHeight;
  }
}

function renderAdminGoogleSheetTable(sheetKey, sheetPayload) {
  const minTableHeightPx = getAdminGoogleSheetMinHeight(sheetKey);
  const view = ADMIN_GOOGLE_SHEETS_RUNTIME.buildAdminGoogleSheetTableView(
    sheetPayload,
    {
      escapeHtml,
      sheetKey,
      sheetState: appliedState,
      popupState,
      minTableHeightPx,
    },
  );
  dom.adminGoogleSheetTable.innerHTML = view.html || "";
  syncAdminGoogleSheetMinHeight(sheetKey);
  // 저장 후 최초 렌더보다 큰 값이 생기면 다시 한 번 재렌더
}
```

- [ ] **Step 4: 더 큰 측정값이 생겼을 때만 한 번 재렌더하는 보정까지 넣고 테스트 통과 확인**

Run: `node --test tests/frontend/test_admin_google_sheets_filters_app_integration.mjs`

Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add frontend/app.js tests/frontend/test_admin_google_sheets_filters_app_integration.mjs
git commit -m "fix: preserve Google Sheets table height across filters"
```

### Task 3: 시트 간 독립성과 CSS contract를 마무리

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Test: `tests/frontend/test_admin_google_sheets_filters_app_integration.mjs`
- Test: `tests/frontend/test_admin_tabs_app_integration.mjs`

- [ ] **Step 1: 시트별 독립성과 더 큰 높이 갱신을 검증하는 테스트 추가**

```js
test("admin google sheets keeps measured minimum heights isolated per sheet", () => {
  const harness = seedGoogleSheetHarness();
  const table = harness.elements["#admin-google-sheet-table"];
  let measuredHeight = 480;
  table.querySelector = () => ({
    offsetHeight: measuredHeight,
    getBoundingClientRect: () => ({ height: measuredHeight }),
  });

  harness.hooks.renderAdminEmbedPanel();
  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 480);

  harness.hooks.state.adminTab = "sheet-2";
  measuredHeight = 320;
  harness.hooks.renderAdminEmbedPanel();

  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-1"], 480);
  assert.equal(harness.hooks.state.adminGoogleSheetMinHeightByKey["sheet-2"], 320);
});
```

- [ ] **Step 2: CSS custom property contract 존재 여부를 고정하는 assertion 추가**

```js
test("admin google sheet styles include the shared min-height custom property contract", () => {
  const styles = fs.readFileSync(stylesPath, "utf8");
  assert.match(styles, /--admin-google-sheet-min-table-height/);
});
```

- [ ] **Step 3: styles에 공통 fallback을 추가**

```css
.admin-google-sheet-table-wrap {
  width: 100%;
  margin-top: 16px;
  overflow: auto;
  min-height: var(--admin-google-sheet-min-table-height, 0px);
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(255, 251, 247, 0.9);
}
```

- [ ] **Step 4: 관련 테스트 묶음을 실행해 전체 통과 확인**

Run: `node --test tests/frontend/test_admin_google_sheets_runtime.mjs tests/frontend/test_admin_google_sheets_filters_runtime.mjs tests/frontend/test_admin_google_sheets_filters_app_integration.mjs tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_google_sheets_cache_app_integration.mjs`

Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add frontend/app.js frontend/styles.css tests/frontend/test_admin_google_sheets_filters_app_integration.mjs tests/frontend/test_admin_tabs_app_integration.mjs tests/frontend/test_admin_google_sheets_runtime.mjs
git commit -m "test: cover Google Sheets minimum table height behavior"
```
