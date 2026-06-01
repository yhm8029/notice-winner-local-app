# Artifact Runtime Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the artifact list/section/card rendering seam out of `frontend/app.js` into `frontend/artifact-runtime.js` while preserving selector contracts, preview behavior, and app-side fallbacks.

**Architecture:** `frontend/artifact-runtime.js` remains the pure rendering module. `frontend/app.js` keeps state reads, preview loading, cache updates, and event wiring. The extraction should follow the same runtime-plus-fallback pattern already used for tracker board, tracker entry, org admin, and sales view helpers.

**Tech Stack:** Vanilla JavaScript, Node test runner, browser runtime helpers in `window.*`

---

### Task 1: Lock Artifact Rendering Contracts With Tests

**Files:**
- Create: `frontend/tests/artifact-runtime.test.js`
- Modify: `frontend/artifact-runtime.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: Write the failing test**

```js
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadArtifactRuntime() {
  const source = fs.readFileSync(path.join(__dirname, "..", "artifact-runtime.js"), "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSArtifactRuntime;
}

test("buildArtifactCardMarkup preserves preview selector contract", () => {
  const runtime = loadArtifactRuntime();
  const html = runtime.buildArtifactCardMarkup(
    {
      id: "artifact-1",
      artifact_type: "winner_csv",
      file_name: "winner.csv",
      mime_type: "text/csv",
      download_url: "/api/artifacts/artifact-1/download",
      meta: { rows: 12, backend: "synthetic" },
    },
    {
      openArtifactId: "artifact-1",
      previewMarkup: '<div data-test="preview">preview</div>',
    },
    {
      escapeHtml: (value) => String(value ?? ""),
    },
  );

  assert.match(html, /data-preview-artifact-id="artifact-1"/);
  assert.match(html, /artifact-preview-button/);
  assert.match(html, /href="\/api\/artifacts\/artifact-1\/download"/);
  assert.match(html, /data-test="preview"/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test frontend/tests/artifact-runtime.test.js`
Expected: FAIL because the new artifact runtime test file is missing or because the artifact fallback hooks are not implemented yet.

- [ ] **Step 3: Add parity and fallback coverage**

```js
test("app-side artifact fallback stays aligned with runtime output", () => {
  const runtime = loadArtifactRuntime();
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  assert.match(source, /ARTIFACT_RUNTIME\?\.buildArtifactSectionMarkup\?\./);
  assert.match(source, /function buildArtifactCardMarkupFallback\(/);
  assert.match(source, /function buildArtifactSectionMarkupFallback\(/);

  const fallbackStart = source.indexOf("function buildArtifactCardMarkupFallback(");
  const fallbackEnd = source.indexOf("function resolveTrackerContextRun(", fallbackStart);
  const context = {
    ARTIFACT_RUNTIME: null,
    escapeHtml: (value) => String(value ?? ""),
    artifactTypeLabel: (value) => String(value ?? ""),
    buildArtifactMetaBits: () => "rows 12",
    canPreviewArtifact: () => true,
    renderArtifactPreviewMarkup: () => '<div data-test="preview">preview</div>',
    state: { openArtifactId: "artifact-1" },
  };
  vm.createContext(context);
  vm.runInContext(source.slice(fallbackStart, fallbackEnd), context);

  const payload = {
    title: "선택 실행 · tracker_export",
    subtitle: "success",
    meta: "run-1 | success",
    items: [{
      id: "artifact-1",
      artifact_type: "winner_csv",
      file_name: "winner.csv",
      mime_type: "text/csv",
      download_url: "/api/artifacts/artifact-1/download",
      meta: { rows: 12 },
    }],
  };
  const helpers = {
    escapeHtml: (value) => String(value ?? ""),
    artifactTypeLabel: (value) => String(value ?? ""),
    buildArtifactMetaBits: () => "rows 12",
    canPreviewArtifact: () => true,
  };
  const runtimeHtml = runtime.buildArtifactSectionMarkup(payload, {
    openArtifactId: "artifact-1",
    renderPreview: () => '<div data-test="preview">preview</div>',
    renderCard: runtime.buildArtifactCardMarkup,
  }, helpers);
  const fallbackHtml = context.buildArtifactSectionMarkupFallback(payload, {
    openArtifactId: "artifact-1",
    renderPreview: () => '<div data-test="preview">preview</div>',
    renderCard: context.buildArtifactCardMarkupFallback,
  }, helpers);

  assert.equal(runtimeHtml.replace(/\s+/g, " ").trim(), fallbackHtml.replace(/\s+/g, " ").trim());
});

test("buildArtifactPreviewMarkup renders workbook preview rows", () => {
  const runtime = loadArtifactRuntime();
  const html = runtime.buildArtifactPreviewMarkup(
    {
      kind: "tracker_workbook",
      sheet_name: "Tracker",
      title_row: ["Tracking Export", ""],
      header_row: ["NO.", "Project"],
      rows: [["1", "Alpha"]],
      total_rows: 1,
      column_widths: [12, 24],
    },
    {
      escapeHtml: (value) => String(value ?? ""),
      formatJson: (value) => JSON.stringify(value),
    },
  );

  assert.match(html, /tracker-preview-table/);
  assert.match(html, /Tracking Export/);
  assert.match(html, /Alpha/);
});
```

- [ ] **Step 4: Run tests to verify the new assertions fail for the right reason**

Run: `node --test frontend/tests/artifact-runtime.test.js`
Expected: FAIL on missing fallback helpers or mismatched runtime/fallback output. The failure must point at artifact rendering behavior, not at syntax errors.

- [ ] **Step 5: Commit the red state**

```bash
git add frontend/tests/artifact-runtime.test.js
git commit -m "test: add artifact runtime rendering contracts"
```

### Task 2: Extract Artifact Card And Section Fallbacks Into app.js

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/artifact-runtime.js`
- Test: `frontend/tests/artifact-runtime.test.js`

- [ ] **Step 1: Write the minimal fallback helpers in `app.js`**

```js
function buildArtifactCardMarkupFallback(item, options = {}, helpers = {}) {
  const {
    openArtifactId = "",
    previewMarkup = "",
  } = options;
  const {
    escapeHtml = (value) => String(value ?? ""),
    artifactTypeLabel: resolveArtifactTypeLabel = artifactTypeLabel,
    buildArtifactMetaBits: resolveMetaBits = buildArtifactMetaBits,
    canPreviewArtifact: previewable = canPreviewArtifact,
  } = helpers;
  const metaBits = resolveMetaBits(item, helpers);
  const showPreview = previewable(item);
  return `
    <article class="artifact-item">
      <div class="artifact-head">
        <div>
          <strong>${escapeHtml(resolveArtifactTypeLabel(item.artifact_type))}</strong>
          <p class="mono">${escapeHtml(item.file_name)}</p>
        </div>
        <span class="mono">${escapeHtml(String(item.meta?.rows || 0))} rows</span>
      </div>
      <p>${escapeHtml(item.mime_type)}</p>
      ${metaBits ? `<p class="mono artifact-meta-line">${escapeHtml(metaBits)}</p>` : ""}
      <div class="artifact-actions">
        ${showPreview ? `<button class="ghost-button artifact-preview-button" type="button" data-preview-artifact-id="${escapeHtml(item.id)}">${item.id === openArtifactId ? "미리보기 닫기" : "미리보기"}</button>` : ""}
        <a class="artifact-link" href="${escapeHtml(item.download_url)}">다운로드</a>
      </div>
      ${previewMarkup}
    </article>
  `;
}

function buildArtifactSectionMarkupFallback(section, options = {}, helpers = {}) {
  const {
    openArtifactId = "",
    renderPreview = () => "",
    renderCard = buildArtifactCardMarkupFallback,
  } = options;
  const { escapeHtml = (value) => String(value ?? "") } = helpers;
  return `
    <section class="artifact-section">
      <div class="artifact-section-head">
        <div>
          <strong>${escapeHtml(section.title)}</strong>
          <p>${escapeHtml(section.subtitle)}</p>
        </div>
        <span class="mono artifact-run-meta">${escapeHtml(section.meta)}</span>
      </div>
      <div class="artifact-section-grid">
        ${(section.items || []).map((item) => renderCard(item, {
          openArtifactId,
          previewMarkup: item.id === openArtifactId ? renderPreview(item) : "",
        }, helpers)).join("")}
      </div>
    </section>
  `;
}
```

- [ ] **Step 2: Wire `renderArtifactsList()` and the helper seam through runtime-first, fallback-second dispatch**

```js
function buildArtifactSectionMarkup(section) {
  return ARTIFACT_RUNTIME?.buildArtifactSectionMarkup?.(
    section,
    {
      openArtifactId: state.openArtifactId,
      renderPreview: (item) => renderArtifactPreviewMarkup(item.id),
      renderCard: (item, options, helpers) =>
        ARTIFACT_RUNTIME?.buildArtifactCardMarkup?.(item, options, helpers)
        || buildArtifactCardMarkupFallback(item, options, helpers),
    },
    {
      escapeHtml,
      artifactTypeLabel,
      buildArtifactMetaBits: (item) => buildArtifactMetaBits(item),
      canPreviewArtifact,
    },
  ) || buildArtifactSectionMarkupFallback(
    section,
    {
      openArtifactId: state.openArtifactId,
      renderPreview: (item) => renderArtifactPreviewMarkup(item.id),
      renderCard: buildArtifactCardMarkupFallback,
    },
    {
      escapeHtml,
      artifactTypeLabel,
      buildArtifactMetaBits: (item) => buildArtifactMetaBits(item),
      canPreviewArtifact,
    },
  );
}
```

- [ ] **Step 3: Keep `artifact-runtime.js` pure and deterministic**

```js
global.SPMSArtifactRuntime = {
  buildArtifactEmptyMessage,
  artifactTypeLabel,
  buildArtifactMetaBits,
  trackerColumnStyle,
  buildWorkbookTitleCells,
  canPreviewArtifact,
  buildArtifactPreviewMarkup,
  buildArtifactCardMarkup,
  buildArtifactSectionMarkup,
};
```

Do not add state or DOM lookups inside `artifact-runtime.js`.

- [ ] **Step 4: Run the focused suite**

Run: `node --test frontend/tests/artifact-runtime.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/app.js frontend/artifact-runtime.js frontend/tests/artifact-runtime.test.js
git commit -m "refactor: extract artifact rendering fallbacks"
```

### Task 3: Verify Frontend Batch Against Existing Runtime Suites

**Files:**
- Modify: `frontend/tests/artifact-runtime.test.js`
- Test: `frontend/tests/tracker-board-runtime.test.js`
- Test: `frontend/tests/tracker-entry-runtime.test.js`
- Test: `frontend/tests/org-admin-runtime.test.js`
- Test: `frontend/tests/sales-view-runtime.test.js`

- [ ] **Step 1: Add one selector-focused regression assertion for preview toggling**

```js
test("artifact section markup keeps preview button targets stable", () => {
  const runtime = loadArtifactRuntime();
  const html = runtime.buildArtifactSectionMarkup(
    {
      title: "선택 실행 · tracker_export",
      subtitle: "running",
      meta: "run-1 | success",
      items: [
        {
          id: "artifact-2",
          artifact_type: "tracking_excel",
          file_name: "project_tracking.xlsx",
          mime_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          download_url: "/download",
          meta: { rows: 3 },
        },
      ],
    },
    {
      openArtifactId: "artifact-2",
      renderPreview: () => '<div data-test="preview">preview</div>',
      renderCard: runtime.buildArtifactCardMarkup,
    },
    { escapeHtml: (value) => String(value ?? "") },
  );

  assert.match(html, /artifact-section-grid/);
  assert.match(html, /data-preview-artifact-id="artifact-2"/);
  assert.match(html, /data-test="preview"/);
});
```

- [ ] **Step 2: Run the full frontend runtime verification set**

Run: `node --test frontend/tests/artifact-runtime.test.js frontend/tests/tracker-board-runtime.test.js frontend/tests/tracker-entry-runtime.test.js frontend/tests/org-admin-runtime.test.js frontend/tests/sales-view-runtime.test.js`
Expected: all tests pass, `0 fail`

- [ ] **Step 3: Run syntax verification**

Run: `node --check frontend/artifact-runtime.js frontend/app.js frontend/tracker-board-runtime.js frontend/tracker-entry-runtime.js frontend/org-admin-runtime.js frontend/sales-view-runtime.js`
Expected: exit code `0`

- [ ] **Step 4: Verify worktree and review diff**

Run: `git status --short`
Expected: only the intended frontend files are modified before commit, then clean after commit

- [ ] **Step 5: Commit final frontend cleanup**

```bash
git add frontend/app.js frontend/artifact-runtime.js frontend/tests/artifact-runtime.test.js
git commit -m "test: cover artifact runtime fallback contracts"
```
