const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadHelpers() {
  const runtimePath = path.join(__dirname, "..", "app-launch-runtime-helpers.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAppLaunchRuntimeHelpers;
}

test("app launch runtime helpers expose runtime and controller access helpers", () => {
  const helpers = loadHelpers();
  assert.equal(typeof helpers.isObject, "function");
  assert.equal(typeof helpers.createControllerAccessors, "function");
  assert.equal(typeof helpers.readRuntime, "function");
  assert.equal(typeof helpers.readFactory, "function");
});

test("createControllerAccessors reads from controller state and supports overrides", () => {
  const helpers = loadHelpers();
  const controllerState = {
    authController: { id: "auth" },
    reportPanelsController: { id: "report" },
  };
  const accessors = helpers.createControllerAccessors(controllerState, {
    getReportPanelsController: () => ({ id: "override" }),
  });
  assert.deepEqual(accessors.getAuthController(), { id: "auth" });
  assert.deepEqual(accessors.getReportPanelsController(), { id: "override" });
});

test("readRuntime and readFactory enforce required runtime shape", () => {
  const helpers = loadHelpers();
  const root = {
    SPMSFooRuntime: {
      createThing() {
        return "ok";
      },
    },
  };
  const runtime = helpers.readRuntime({}, root, "FOO_RUNTIME", "SPMSFooRuntime", "missing runtime");
  assert.equal(helpers.readFactory(runtime, "createThing", "missing factory")(), "ok");
  assert.throws(() => helpers.readRuntime({}, {}, "FOO_RUNTIME", "SPMSFooRuntime", "missing runtime"), /missing runtime/);
  assert.throws(() => helpers.readFactory({}, "createThing", "missing factory"), /missing factory/);
});
