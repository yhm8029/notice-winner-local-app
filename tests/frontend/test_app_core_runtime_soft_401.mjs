import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/app-core-runtime.js");

function readRuntimeSource() {
  return fs.readFileSync(runtimePath, "utf8");
}

function createBaseState() {
  return {
    auth: {
      enabled: true,
      authenticated: true,
      authorized: true,
      user: { id: "user-1" },
      message: "",
      accessToken: "",
    },
  };
}

function loadCoreApiHelper({ fetchImpl, refreshResult = null } = {}) {
  const renderCalls = [];
  const refreshCalls = [];
  const state = createBaseState();
  const context = vm.createContext({
    console,
    state,
    window: {
      setTimeout: () => 1,
      clearTimeout: () => {},
    },
    fetch: fetchImpl,
    FormData: class FakeFormData {},
    AbortController,
    Date,
  });
  vm.runInContext(readRuntimeSource(), context, { filename: runtimePath });
  const runtime = context.window.createAppCoreRuntime({
    window: context.window,
    state,
    fetch: fetchImpl,
    FormData: class FakeFormData {},
    AbortController,
    refreshAuthSessionState: async (options) => {
      refreshCalls.push(options);
      return refreshResult;
    },
    renderAuthUi: () => renderCalls.push("renderAuthUi"),
  });
  return {
    api: runtime.api,
    state,
    renderCalls,
    refreshCalls,
  };
}

test("tracker change event 401 does not clear auth state", async () => {
  const { api, state, renderCalls, refreshCalls } = loadCoreApiHelper({
    fetchImpl: async () => ({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      url: "/api/tracker-change-events?limit=15",
      headers: {
        get: () => "application/json",
      },
      json: async () => ({ error: { message: "session expired" } }),
    }),
    refreshResult: null,
  });

  await assert.rejects(
    api("/api/tracker-change-events?limit=15"),
    (error) => error?.name === "ApiRequestError" && error?.status === 401,
  );

  assert.equal(state.auth.authenticated, true);
  assert.equal(state.auth.authorized, true);
  assert.deepEqual(state.auth.user, { id: "user-1" });
  assert.equal(state.auth.message, "");
  assert.deepEqual(refreshCalls, []);
  assert.deepEqual(renderCalls, []);
});
