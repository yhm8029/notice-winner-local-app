const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime(filePath) {
  const source = fs.readFileSync(filePath, "utf8");
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSArtifactRuntime;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatJson(value) {
  if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
    return "{}";
  }
  return JSON.stringify(value, null, 2);
}

function loadArtifactAppContext(runtime = null) {
  const source = fs.readFileSync(path.join(__dirname, "..", "app-runtime-body.js"), "utf8");
  const start = source.indexOf("function renderArtifactsList()");
  const end = source.indexOf("async function cancelSelectedRun()", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate artifact helpers in app-runtime-body.js");
  }

  const calls = [];
  const controller = {
    renderArtifactsList() {
      calls.push(["renderArtifactsList"]);
      return "render-artifacts";
    },
    buildArtifactEmptyMessage() {
      calls.push(["buildArtifactEmptyMessage"]);
      return "artifact-empty";
    },
    renderArtifactPreviewMarkup(artifactId) {
      calls.push(["renderArtifactPreviewMarkup", artifactId]);
      return `preview:${artifactId}`;
    },
  };
  const context = {
    ARTIFACT_RUNTIME: runtime,
    APP_SUPPORT: {
      trackerColumnStyle(widths, index, artifactRuntime) {
        calls.push(["trackerColumnStyle", widths, index, artifactRuntime]);
        return artifactRuntime?.trackerColumnStyle?.(widths, index) || "fallback-column-style";
      },
      buildWorkbookTitleCells(titleRow, helpers, artifactRuntime) {
        calls.push(["buildWorkbookTitleCells", titleRow, helpers, artifactRuntime]);
        return artifactRuntime?.buildWorkbookTitleCells?.(titleRow, helpers) || "fallback-title-cells";
      },
      fetchArtifactPreview(item, api) {
        calls.push(["fetchArtifactPreview", item.id]);
        return api(`/api/artifacts/${item.id}/preview?limit=${item.artifact_type === "tracking_excel" ? 16 : 6}`);
      },
      ensureArtifactPreviewCached(options) {
        calls.push(["ensureArtifactPreviewCached", options.item.id]);
        return (async () => {
          options.state.artifactPreviewCache[options.item.id] = { ok: true };
          options.renderArtifactsList();
          options.renderRunExecutionContext(options.state.selectedRun);
        })();
      },
    },
    getReportPanelsController() {
      return controller;
    },
    state: {
      artifactPreviewCache: {},
      openArtifactId: "artifact-1",
      selectedTrackerWorkbookArtifactId: "artifact-1",
      selectedRun: { id: "run-1" },
    },
    api(url) {
      calls.push(["api", url]);
      return Promise.resolve({ url });
    },
    renderRunExecutionContext(run) {
      calls.push(["renderRunExecutionContext", run.id]);
      return "run-context";
    },
    escapeHtml,
  };

  vm.createContext(context);
  vm.runInContext(source.slice(start, end), context);
  context.calls = calls;
  return context;
}

test("buildArtifactCardMarkup preserves the card selector contract", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "artifact-runtime.js"));
  const html = runtime.buildArtifactCardMarkup(
    {
      id: "artifact-1",
      artifact_type: "winner_csv",
      file_name: "winner.csv",
      mime_type: "text/csv",
      download_url: "/downloads/artifact-1",
      meta: {
        rows: 4,
      },
      size_bytes: 2048,
    },
    {
      openArtifactId: "",
      previewMarkup: "",
    },
    {
      escapeHtml,
      buildArtifactMetaBits: (item) => `meta:${item.id}`,
      canPreviewArtifact: () => true,
      artifactTypeLabel: (value) => value,
    },
  );

  assert.match(html, /<article class="artifact-item">/);
  assert.match(html, /data-preview-artifact-id="artifact-1"/);
  assert.match(html, /class="artifact-link" href="\/downloads\/artifact-1"/);
  assert.match(html, /<button class="ghost-button artifact-preview-button" type="button"/);
});

test("buildArtifactPreviewMarkup renders workbook previews", () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "artifact-runtime.js"));
  const html = runtime.buildArtifactPreviewMarkup(
    {
      kind: "tracker_workbook",
      sheet_name: "Sheet A",
      title_row: ["Overview", "", "Metrics"],
      header_row: ["Project", "Count", "Status"],
      column_widths: [12, 8, 10],
      rows: [
        ["Alpha", "3", "Done"],
        ["Beta", "1", "Queued"],
      ],
      total_rows: 2,
    },
    {
      escapeHtml,
      formatJson,
    },
  );

  assert.match(html, /tracker-workbook-preview/);
  assert.match(html, /tracker-preview-table/);
  assert.match(html, /<div class="tracker-workbook-meta">/);
  assert.match(html, /Sheet A/);
  assert.match(html, /<tr class="tracker-title-row"><th colspan="2" class="tracker-title-cell tracker-title-cell-left">Overview<\/th><th colspan="1" class="tracker-title-cell tracker-title-cell-right">Metrics<\/th><\/tr>/);
  assert.match(html, /<th[^>]*>Project<\/th>/);
  assert.match(html, /<td[^>]*>Alpha<\/td>/);
  assert.match(html, /<td[^>]*>Queued<\/td>/);
});

test("artifact wrappers delegate through report controller and app support", async () => {
  const runtime = loadRuntime(path.join(__dirname, "..", "artifact-runtime.js"));
  const app = loadArtifactAppContext(runtime);

  assert.equal(app.renderArtifactsList(), "render-artifacts");
  assert.equal(app.buildArtifactEmptyMessage(), "artifact-empty");
  assert.equal(app.renderArtifactPreviewMarkup("artifact-1"), "preview:artifact-1");
  assert.equal(app.trackerColumnStyle([12], 0), runtime.trackerColumnStyle([12], 0));
  assert.equal(
    app.buildWorkbookTitleCells(["Overview", "", "Metrics"]),
    runtime.buildWorkbookTitleCells(["Overview", "", "Metrics"], { escapeHtml }),
  );

  const preview = await app.fetchArtifactPreview({ id: "artifact-1", artifact_type: "tracking_excel" });
  assert.equal(preview.url, "/api/artifacts/artifact-1/preview?limit=16");

  await app.ensureArtifactPreviewCached({ id: "artifact-1", artifact_type: "tracking_excel" });
  assert.deepEqual(app.state.artifactPreviewCache["artifact-1"], { ok: true });
  assert.deepEqual(
    app.calls.map((entry) => entry[0]),
    [
      "renderArtifactsList",
      "buildArtifactEmptyMessage",
      "renderArtifactPreviewMarkup",
      "trackerColumnStyle",
      "buildWorkbookTitleCells",
      "fetchArtifactPreview",
      "api",
      "ensureArtifactPreviewCached",
      "renderArtifactsList",
      "renderRunExecutionContext",
    ],
  );
  assert.equal(app.calls[2][1], "artifact-1");
  assert.deepEqual(app.calls[3].slice(0, 3), ["trackerColumnStyle", [12], 0]);
  assert.deepEqual(app.calls[4].slice(0, 2), ["buildWorkbookTitleCells", ["Overview", "", "Metrics"]]);
  assert.equal(app.calls[5][1], "artifact-1");
  assert.equal(app.calls[6][1], "/api/artifacts/artifact-1/preview?limit=16");
  assert.equal(app.calls[7][1], "artifact-1");
  assert.equal(app.calls[9][1], "run-1");
});
