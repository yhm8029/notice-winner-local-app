const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadRuntime() {
  const runtimePath = path.join(__dirname, "..", "app-runtime-body-runtime.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console, document: undefined });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAppRuntimeBodyRuntime;
}

test("runtime body helper exposes constants and pure helpers", () => {
  const runtime = loadRuntime();

  assert.equal(runtime.APP_ROOT_PATH, "/app/");
  assert.equal(runtime.DEFAULT_ADMIN_TAB, "project-status");
  assert.deepEqual([...runtime.EDITABLE_FIELDS.slice(0, 3)], ["project_name", "gross_area_scale", "construction_cost"]);
  assert.equal(runtime.normalizePlatformAdminAccountDraft({ email: "a", role: "  ", password: 1 }).role, "org_member");
  assert.equal(runtime.formatContractAmountInput("1a234"), "1,234");
  assert.equal(runtime.formatContractAmountDisplay("  ", "fallback"), "fallback");
  assert.equal(runtime.runTypeLabel("winner_pipeline", runtime.RUN_TYPE_LABELS, null), "프로젝트 트랙커");
  assert.equal(runtime.isProjectTrackerRun("project_tracker"), true);
  assert.equal(runtime.useGlobalTrackerEntriesScope(), true);
});
