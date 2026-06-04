import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const htmlPath = path.resolve(__dirname, "../../frontend/index.html");
const salesPanelControllerPath = path.resolve(__dirname, "../../frontend/sales-panel-controller.js");
const runtimeEnhancementsPath = path.resolve(__dirname, "../../frontend/runtime-enhancements.js");
const trackerDiagnosticsRuntimePath = path.resolve(__dirname, "../../frontend/tracker-controller-diagnostics-runtime.js");
const trackerControllerPath = path.resolve(__dirname, "../../frontend/tracker-controller.js");
const trackerControllerEntriesRuntimePath = path.resolve(__dirname, "../../frontend/tracker-controller-entries-runtime.js");
const appEventBindingsPath = path.resolve(__dirname, "../../frontend/app-event-bindings.js");
const bootstrapRuntimePath = path.resolve(__dirname, "../../frontend/bootstrap-runtime.js");
const orgAdminRuntimePath = path.resolve(__dirname, "../../frontend/org-admin-runtime.js");
const runtimeActivityCssPath = path.resolve(__dirname, "../../frontend/styles/runtime-activity.css");
const runPanelsControllerPath = path.resolve(__dirname, "../../frontend/run-panels-controller.js");
const runPanelsControllerHelpersPath = path.resolve(__dirname, "../../frontend/run-panels-controller-helpers.js");

function readHtmlSource() {
  return fs.readFileSync(htmlPath, "utf8");
}

function readSalesPanelControllerSource() {
  return fs.readFileSync(salesPanelControllerPath, "utf8");
}

function readRuntimeEnhancementsSource() {
  return fs.readFileSync(runtimeEnhancementsPath, "utf8");
}

function readTrackerDiagnosticsRuntimeSource() {
  return fs.readFileSync(trackerDiagnosticsRuntimePath, "utf8");
}

function readTrackerControllerSource() {
  return fs.readFileSync(trackerControllerPath, "utf8");
}

function readTrackerControllerEntriesRuntimeSource() {
  return fs.readFileSync(trackerControllerEntriesRuntimePath, "utf8");
}

function readAppEventBindingsSource() {
  return fs.readFileSync(appEventBindingsPath, "utf8");
}

function readBootstrapRuntimeSource() {
  return fs.readFileSync(bootstrapRuntimePath, "utf8");
}

function readOrgAdminRuntimeSource() {
  return fs.readFileSync(orgAdminRuntimePath, "utf8");
}

function readRuntimeActivityCssSource() {
  return fs.readFileSync(runtimeActivityCssPath, "utf8");
}

function readRunPanelsControllerSource() {
  return fs.readFileSync(runPanelsControllerPath, "utf8");
}

function readRunPanelsControllerHelpersSource() {
  return fs.readFileSync(runPanelsControllerHelpersPath, "utf8");
}

test("index.html loads the modular runtime assets before app.js", () => {
  const html = readHtmlSource();
  const runtimeScripts = [
    "/app-shell-runtime.js",
    "/app-support-runtime.js",
    "/admin-tabs-runtime.js",
    "/app-controller-deps.js",
    "/org-admin-controller.js",
    "/auth-ui-controller.js",
    "/run-panels-controller.js",
    "/tracker-controller-diagnostics-runtime.js",
    "/tracker-controller-runs-runtime.js",
    "/tracker-controller-entries-runtime.js",
    "/tracker-controller.js",
    "/app-bootstrap-bridge.js",
  ];

  const appIndex = html.indexOf("/app.js?v=");
  assert.notEqual(appIndex, -1, "app.js script tag should exist");

  for (const script of runtimeScripts) {
    const scriptIndex = html.indexOf(script);
    assert.notEqual(scriptIndex, -1, `${script} script tag should exist`);
    assert.ok(scriptIndex < appIndex, `${script} should load before app.js`);
  }
});

test("index.html loads app-bootstrap-bridge as a module before app.js", () => {
  const html = readHtmlSource();

  assert.match(
    html,
    /<script(?: defer)? type="module" src="\/app-bootstrap-bridge\.js(?:\?v=[^"]+)?"><\/script>/,
  );
});

test("sales panel controller and child action module are cache busted", () => {
  const html = readHtmlSource();
  const controllerSource = readSalesPanelControllerSource();

  assert.match(
    html,
    /<script type="module" src="\/sales-panel-controller\.js\?v=[^"]+"><\/script>/,
  );
  assert.match(
    controllerSource,
    /from "\.\/sales-panel-controller-actions\.js\?v=[^"]+"/,
  );
});

test("bootstrap and organization admin runtimes expose required bridge APIs", () => {
  const html = readHtmlSource();
  const bootstrapSource = readBootstrapRuntimeSource();
  const orgAdminSource = readOrgAdminRuntimeSource();

  assert.match(html, /\/bootstrap-runtime\.js\?v=20260602g/);
  assert.match(html, /\/org-admin-runtime\.js\?v=20260429a/);
  assert.match(bootstrapSource, /loadAdminConsoleData/);
  assert.match(bootstrapSource, /initializeConsole/);
  assert.match(bootstrapSource, /ensureConsoleInitialized/);
  assert.match(orgAdminSource, /buildInvitationRoleOptionsMarkup/);
});

test("tracker render controller is cache busted for selection guard fixes", () => {
  const html = readHtmlSource();

  assert.match(html, /\/tracker-render-controller\.js\?v=20260604a/);
  assert.match(html, /\/tracker-controller-diagnostics-runtime\.js\?v=20260602f/);
});

test("tracker entry card runtimes are cache busted for hidden sales chrome", () => {
  const html = readHtmlSource();

  assert.match(html, /\/tracker-entry-runtime\.js\?v=20260602d/);
  assert.match(html, /\/tracker-render-fallback-entry-runtime\.js\?v=20260602d/);
});

test("app runtime body is cache busted for auth submit guard fixes", () => {
  const html = readHtmlSource();
  const appSource = fs.readFileSync(path.resolve(__dirname, "../../frontend/app.js"), "utf8");

  assert.match(html, /\/app\.js\?v=20260602h/);
  assert.match(appSource, /\/app\/app-runtime-body\.js\?v=20260602g/);
});

test("index.html cache busts local console chrome runtimes", () => {
  const html = readHtmlSource();
  const appRuntimeBodySource = fs.readFileSync(path.resolve(__dirname, "../../frontend/app-runtime-body.js"), "utf8");

  assert.match(html, /\/styles\.css\?v=20260604b/);
  assert.match(html, /\/app-shell-runtime\.js\?v=20260602g/);
  assert.match(html, /\/app-event-bindings\.js\?v=20260602i/);
  assert.match(html, /\/download-controller\.js\?v=20260602g/);
  assert.match(html, /\/tracker-controller-entries-runtime\.js\?v=20260602g/);
  assert.match(html, /\/tracker-controller\.js\?v=20260602g/);
  assert.match(html, /\/app-bootstrap-bridge\.js\?v=20260602g/);
  assert.match(html, /\/ui-mode-controller\.js\?v=20260602c/);
  assert.match(html, /\/runtime-enhancements\.js\?v=20260602e/);
  assert.match(html, /\/sales-panel-controller\.js\?v=20260602c/);
  assert.match(html, /\/run-panels-controller\.js\?v=20260604a/);
  assert.match(html, /\/auth-controller\.js\?v=20260602c/);
  assert.match(appRuntimeBodySource, /\/app\/app-runtime-body-runtime\.js\?v=20260602b/);
  assert.match(appRuntimeBodySource, /\/app\/app-runtime-body-shell-runtime\.js\?v=20260602g/);
});

test("runtime enhancements do not create local sales summary cards", () => {
  const source = readRuntimeEnhancementsSource();

  assert.doesNotMatch(source, /tracker-user-sales-section/);
  assert.doesNotMatch(source, /tracker-company-sales-section/);
  assert.doesNotMatch(source, /tracker-sales-overview-grid/);
  assert.match(source, /tracker-entries-section-title/);
});

test("index.html hides local mode and sync status controls from the project workspace", () => {
  const html = readHtmlSource();

  assert.match(html, /<div class="hero-meta hidden" aria-hidden="true">/);
  assert.match(html, /id="mode-toggle-button" class="ghost-button hero-mode-button hidden"/);
  assert.match(html, /id="auth-session-mode-toggle-button" class="ghost-button hidden"/);
});

test("index.html does not render tracker template status copy by default", () => {
  const html = readHtmlSource();
  const diagnosticsSource = readTrackerDiagnosticsRuntimeSource();

  assert.match(html, /<div id="tracker-template-status" class="tracker-template-status hidden"><\/div>/);
  assert.doesNotMatch(html, /현재 서버 양식을 확인하는 중입니다/);
  assert.doesNotMatch(diagnosticsSource, /현재 서버 양식을 확인하는 중입니다/);
});

test("tracker workspace exposes a notice year filter and sends it to the tracker summary API", () => {
  const html = readHtmlSource();
  const controllerSource = readTrackerControllerSource();
  const entriesRuntimeSource = readTrackerControllerEntriesRuntimeSource();
  const appEventBindingsSource = readAppEventBindingsSource();
  const runtimeActivityCss = readRuntimeActivityCssSource();

  assert.match(html, /id="tracker-notice-year"/);
  assert.match(html, /<option value="2023">2023<\/option>/);
  assert.match(html, /<option value="2045">2045<\/option>/);
  assert.match(html, /class="tracker-filter-controls-row"[\s\S]*id="tracker-region-buttons"[\s\S]*id="tracker-notice-year"[\s\S]*id="tracker-page-size"/);
  assert.match(html, /class="compact-row tracker-year-page-size-row"[\s\S]*id="tracker-notice-year"[\s\S]*id="tracker-page-size"/);
  assert.match(html, /class="compact tracker-page-size-field"/);
  assert.match(runtimeActivityCss, /\.tracker-filter-controls-row[\s\S]*grid-column:\s*1\s*\/\s*-1/);
  assert.match(runtimeActivityCss, /\.tracker-filter-controls-row[\s\S]*display:\s*grid/);
  assert.match(runtimeActivityCss, /\.tracker-filter-controls-row[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+minmax\(0,\s*1fr\)/);
  assert.match(runtimeActivityCss, /\.tracker-year-page-size-row[\s\S]*display:\s*grid/);
  assert.match(runtimeActivityCss, /\.tracker-year-page-size-row[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+minmax\(0,\s*1fr\)/);
  assert.match(controllerSource, /trackerFilters\.noticeYear/);
  assert.match(entriesRuntimeSource, /notice_year/);
  assert.match(appEventBindingsSource, /homeBootstrapTrackerSnapshotActive\s*=\s*false/);
  assert.match(appEventBindingsSource, /loadTrackerEntries\(\{\s*forceRefresh:\s*true\s*}\)/);
});

test("project tracker create form hides fixed crawler parameters", () => {
  const html = readHtmlSource();
  const controllerSource = readRunPanelsControllerSource();
  const helpersSource = readRunPanelsControllerHelpersSource();

  assert.match(html, /<input name="contract_date_hint" type="hidden" value="" \/>/);
  assert.match(html, /<input name="bid_no" type="hidden" value="" \/>/);
  assert.match(html, /<input name="demand_org" type="hidden" value="" \/>/);
  assert.match(html, /<input name="rows_per_page" type="hidden" value="999" \/>/);
  assert.match(html, /<input name="max_pages" type="hidden" value="15" \/>/);
  assert.doesNotMatch(html, /name="contract_date_hint" type="text"/);
  assert.doesNotMatch(html, /name="bid_no" type="text"/);
  assert.doesNotMatch(html, /name="demand_org" type="text"/);
  assert.doesNotMatch(html, /name="rows_per_page" type="number"/);
  assert.doesNotMatch(html, /name="max_pages" type="number"/);
  assert.match(controllerSource, /run-panels-controller-helpers\.js\?v=20260604a/);
  assert.match(helpersSource, /contract_date_hint:\s*""/);
  assert.match(helpersSource, /bid_no:\s*""/);
  assert.match(helpersSource, /demand_org:\s*""/);
  assert.match(helpersSource, /rows_per_page:\s*999/);
  assert.match(helpersSource, /max_pages:\s*15/);
});

test("index.html does not load Google Sheets runtime assets", () => {
  const html = readHtmlSource();

  for (const removedAsset of [
    "/admin-google-sheets-cache-runtime.js",
    "/admin-google-sheets-runtime.js",
    "/admin-google-sheets-controller.js",
    "/app-admin-google-sheets-state-runtime.js",
    "/app-admin-google-sheets-runtime.js",
  ]) {
    assert.equal(html.includes(removedAsset), false, `${removedAsset} should not be loaded`);
  }

  assert.equal(html.includes("admin-google"), false);
  assert.equal(html.includes("Google Sheets"), false);
});

test("index.html starts directly in the local console instead of the login shell", () => {
  const html = readHtmlSource();

  assert.match(html, /<section id="auth-shell" class="auth-shell hidden">/);
  assert.match(html, /<div id="console-shell" class="page-shell">/);
});

test("index.html hides nonessential local operations panels by default", () => {
  const html = readHtmlSource();
  const hiddenPanelIds = [
    "panel-dashboard",
    "panel-status",
    "panel-runs",
    "panel-logs",
    "panel-report",
    "panel-artifacts",
    "panel-editor",
  ];

  for (const panelId of hiddenPanelIds) {
    assert.match(
      html,
      new RegExp(`<section id="${panelId}" class="[^"]*\\bhidden\\b[^"]*">`),
      `${panelId} should be hidden in the local console`,
    );
  }

  assert.match(html, /<section id="panel-form" class="panel panel-form">/);
  assert.match(html, /<section id="panel-tracker" class="panel panel-tracker">/);
  assert.match(html, /<h2>공고 추적<\/h2>/);
  assert.doesNotMatch(html, />프로젝트 트랙[커터]</);
});
