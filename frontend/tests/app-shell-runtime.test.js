const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime() {
  const source = fs.readFileSync("frontend/app-shell-runtime.js", "utf8");
  const context = { window: {}, document: { querySelector: () => null } };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSAppShellRuntime;
}

test("createAppState starts in local authorized admin auth mode", () => {
  const runtime = loadRuntime();

  const state = runtime.createAppState();

  assert.equal(state.auth.localSession, true);
  assert.equal(state.auth.enabled, true);
  assert.equal(state.auth.checked, true);
  assert.equal(state.auth.checking, false);
  assert.equal(state.auth.authenticated, true);
  assert.equal(state.auth.authorized, true);
  assert.equal(state.auth.user.role, "platform_admin");
});
