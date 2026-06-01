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
    "/admin-google-sheets-cache-runtime.js",
    "/admin-google-sheets-runtime.js",
    "/admin-tabs-runtime.js",
    "/app-controller-deps.js",
    "/org-admin-controller.js",
    "/auth-ui-controller.js",
    "/run-panels-controller.js",
    "/tracker-controller-diagnostics-runtime.js",
    "/tracker-controller-runs-runtime.js",
    "/tracker-controller-entries-runtime.js",
    "/tracker-controller.js",
    "/admin-google-sheets-controller.js",
    "/app-admin-google-sheets-state-runtime.js",
    "/app-admin-google-sheets-runtime.js",
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

  assert.match(html, /\/app\.js\?v=20260429c/);
  assert.match(appSource, /\/app\/app-runtime-body\.js\?v=20260429c/);
});

test("index.html keeps the admin google sheets shell mount points", () => {
  const html = readHtmlSource();

  for (const selector of [
    'id="admin-header-bar"',
    'id="admin-top-nav"',
    'id="admin-top-nav-list"',
    'id="admin-embed-panel"',
    'id="admin-embed-title"',
    'id="admin-embed-subtitle"',
    'id="admin-google-sheets-sync-feedback"',
    'id="admin-google-sheet-status"',
    'id="admin-google-sheet-table"',
    'id="admin-embed-empty"',
  ]) {
    assert.match(html, new RegExp(selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});
