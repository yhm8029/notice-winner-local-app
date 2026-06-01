const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

test("runtime.css imports runtime partials", () => {
  const runtimeCssPath = path.join(__dirname, "..", "styles", "runtime.css");
  const source = fs.readFileSync(runtimeCssPath, "utf8");

  assert.match(source, /@import url\("\.\/runtime-activity\.css"\);/);
  assert.match(source, /@import url\("\.\/runtime-layout\.css"\);/);
  assert.match(source, /@import url\("\.\/runtime-admin\.css"\);/);
});

test("app launch runtime internals merge startup bridge factories with runtime overrides", () => {
  const runtimePath = path.join(__dirname, "..", "app-launch-runtime-core.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const prefix = source.slice(0, source.indexOf("(function attachAppLaunchRuntimeCore(global) {"));
  const context = vm.createContext({ window: {}, console });

  vm.runInContext(
    `${prefix}\nglobalThis.__appLaunchRuntimeInternals = APP_LAUNCH_RUNTIME_INTERNALS;`,
    context,
    { filename: runtimePath },
  );

  const { coerceObject, mergeRuntimeSources } = context.__appLaunchRuntimeInternals;

  assert.equal(coerceObject("not-an-object", null), null);
  assert.deepEqual({ ...coerceObject({ ok: true }, null) }, { ok: true });
  assert.deepEqual({ ...mergeRuntimeSources(
    { bridgeFactories: { alpha: "startup", shared: "startup" } },
    { shared: "runtime", beta: "runtime" },
  ) }, {
    alpha: "startup",
    shared: "runtime",
    beta: "runtime",
  });
});
