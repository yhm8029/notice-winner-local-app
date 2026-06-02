import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const htmlPath = path.resolve(__dirname, "../../frontend/index.html");
const salesPanelControllerPath = path.resolve(__dirname, "../../frontend/sales-panel-controller.js");
const bootstrapRuntimePath = path.resolve(__dirname, "../../frontend/bootstrap-runtime.js");
const orgAdminRuntimePath = path.resolve(__dirname, "../../frontend/org-admin-runtime.js");

function readHtmlSource() {
  return fs.readFileSync(htmlPath, "utf8");
}

function readSalesPanelControllerSource() {
  return fs.readFileSync(salesPanelControllerPath, "utf8");
}

function readBootstrapRuntimeSource() {
  return fs.readFileSync(bootstrapRuntimePath, "utf8");
}

function readOrgAdminRuntimeSource() {
  return fs.readFileSync(orgAdminRuntimePath, "utf8");
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

  assert.match(html, /\/bootstrap-runtime\.js\?v=20260429a/);
  assert.match(html, /\/org-admin-runtime\.js\?v=20260429a/);
  assert.match(bootstrapSource, /loadAdminConsoleData/);
  assert.match(bootstrapSource, /initializeConsole/);
  assert.match(bootstrapSource, /ensureConsoleInitialized/);
  assert.match(orgAdminSource, /buildInvitationRoleOptionsMarkup/);
});

test("tracker render controller is cache busted for selection guard fixes", () => {
  const html = readHtmlSource();

  assert.match(html, /\/tracker-render-controller\.js\?v=20260429a/);
});

test("app runtime body is cache busted for auth submit guard fixes", () => {
  const html = readHtmlSource();
  const appSource = fs.readFileSync(path.resolve(__dirname, "../../frontend/app.js"), "utf8");

  assert.match(html, /\/app\.js\?v=20260602c/);
  assert.match(appSource, /\/app\/app-runtime-body\.js\?v=20260602b/);
});

test("index.html cache busts local console chrome runtimes", () => {
  const html = readHtmlSource();
  const appRuntimeBodySource = fs.readFileSync(path.resolve(__dirname, "../../frontend/app-runtime-body.js"), "utf8");

  assert.match(html, /\/app-shell-runtime\.js\?v=20260602c/);
  assert.match(html, /\/ui-mode-controller\.js\?v=20260602c/);
  assert.match(html, /\/runtime-enhancements\.js\?v=20260602c/);
  assert.match(html, /\/sales-panel-controller\.js\?v=20260602c/);
  assert.match(html, /\/auth-controller\.js\?v=20260602c/);
  assert.match(appRuntimeBodySource, /\/app\/app-runtime-body-runtime\.js\?v=20260602b/);
});

test("index.html hides local mode and sync status controls from the project workspace", () => {
  const html = readHtmlSource();

  assert.match(html, /<div class="hero-meta hidden" aria-hidden="true">/);
  assert.match(html, /id="mode-toggle-button" class="ghost-button hero-mode-button hidden"/);
  assert.match(html, /id="auth-session-mode-toggle-button" class="ghost-button hidden"/);
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
