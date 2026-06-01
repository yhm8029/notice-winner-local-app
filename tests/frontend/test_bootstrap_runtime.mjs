import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/bootstrap-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = {};
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSBootstrapRuntime;
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

test("bootstrap runtime normalizes and caches sales overview payloads", () => {
  const runtime = loadRuntime();

  assert.equal(Object.isFrozen(runtime), true);
  assert.deepEqual(Object.keys(runtime).sort(), [
    "buildHomeBootstrapCachePayload",
    "buildSalesOverviewCachePayload",
    "buildStorageIdentity",
    "canUseHomeBootstrapTrackerSnapshot",
    "hasCachedHomeBootstrapData",
    "hasCachedSalesOverviewData",
    "isMissingHomeBootstrapEndpointError",
    "isMissingSalesOverviewEndpointError",
    "mergeSalesOverviewIntoHomeBootstrapPayload",
    "mergeTrackerEntriesById",
    "normalizeSalesOverviewPayload",
    "normalizeTrackerFirstPagePayload",
  ]);

  assert.equal(typeof runtime.normalizeSalesOverviewPayload, "function");
  assert.equal(typeof runtime.buildSalesOverviewCachePayload, "function");
  assert.equal(typeof runtime.mergeSalesOverviewIntoHomeBootstrapPayload, "function");

  const normalized = runtime.normalizeSalesOverviewPayload({
    my_items: [{ id: "mine" }],
    company_items: "not-an-array",
    organization_users: [{ id: "user-1" }],
  });

  assert.deepEqual(plain(normalized), {
    myItems: [{ id: "mine" }],
    companyItems: [],
    organizationUsers: [{ id: "user-1" }],
  });

  const cachePayload = runtime.buildSalesOverviewCachePayload({
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
  });

  assert.deepEqual(plain(cachePayload), {
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
  });

  const merged = runtime.mergeSalesOverviewIntoHomeBootstrapPayload(
    {
      generated_at: "2026-04-07T00:00:00.000Z",
      snapshot_version: 2,
      tracker_first_page: { items: [{ id: "tracker-1" }] },
      my_items: [{ id: "old" }],
      company_items: [{ id: "old-company" }],
      organization_users: [{ id: "old-user" }],
      unrelated: true,
    },
    {
      my_items: [{ id: "mine" }],
      company_items: [{ id: "company" }],
      organization_users: [{ id: "user-1" }],
    }
  );

  assert.deepEqual(plain(merged), {
    generated_at: "2026-04-07T00:00:00.000Z",
    snapshot_version: 2,
    tracker_first_page: { items: [{ id: "tracker-1" }] },
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
    unrelated: true,
  });
});

test("bootstrap runtime normalizes tracker first page and home bootstrap cache payloads", () => {
  const runtime = loadRuntime();

  assert.equal(typeof runtime.normalizeTrackerFirstPagePayload, "function");
  assert.equal(typeof runtime.buildHomeBootstrapCachePayload, "function");

  const trackerFirstPage = runtime.normalizeTrackerFirstPagePayload({
    items: [{ id: "tracker-1" }],
    page: "3",
    total: "42",
    sort_contract: null,
  }, 37);

  assert.deepEqual(plain(trackerFirstPage), {
    items: [{ id: "tracker-1" }],
    page: 3,
    page_size: 37,
    total: 42,
    sort_contract: { mode: "default", order_by: [] },
  });

  const trackerFirstPageWithExplicitSize = runtime.normalizeTrackerFirstPagePayload({
    items: [{ id: "tracker-2" }],
    page: "4",
    page_size: "12",
    total: "7",
    sort_contract: null,
  }, 37);

  assert.deepEqual(plain(trackerFirstPageWithExplicitSize), {
    items: [{ id: "tracker-2" }],
    page: 4,
    page_size: 12,
    total: 7,
    sort_contract: { mode: "default", order_by: [] },
  });

  const cachePayload = runtime.buildHomeBootstrapCachePayload({
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
    tracker_first_page: {
      items: [{ id: "tracker-1" }],
      page: "2",
      page_size: "15",
      total: "3",
      sort_contract: { mode: "custom", order_by: ["updated_at_desc"] },
    },
    generated_at: "2026-04-07T00:00:00.000Z",
    snapshot_version: "4",
  });

  assert.deepEqual(plain(cachePayload), {
    my_items: [{ id: "mine" }],
    company_items: [{ id: "company" }],
    organization_users: [{ id: "user-1" }],
    tracker_first_page: {
      items: [{ id: "tracker-1" }],
      page: 2,
      page_size: 15,
      total: 3,
      sort_contract: { mode: "custom", order_by: ["updated_at_desc"] },
    },
    generated_at: "2026-04-07T00:00:00.000Z",
    snapshot_version: 4,
  });

  const defaultCachePayload = runtime.buildHomeBootstrapCachePayload({});
  assert.deepEqual(plain(defaultCachePayload.tracker_first_page), {
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    sort_contract: { mode: "default", order_by: [] },
  });
  assert.equal(defaultCachePayload.generated_at, "");
  assert.equal(defaultCachePayload.snapshot_version, 1);
});

test("bootstrap runtime builds storage identity and merges tracker entries by id", () => {
  const runtime = loadRuntime();

  assert.equal(typeof runtime.buildStorageIdentity, "function");
  assert.equal(typeof runtime.mergeTrackerEntriesById, "function");

  assert.equal(runtime.buildStorageIdentity({
    organization_id: " org-123 ",
    local_user_id: " user-456 ",
    email: " USER@Example.COM ",
  }), "org-123|user-456|user@example.com");

  assert.equal(runtime.buildStorageIdentity({
    organization_id: "",
    local_user_id: null,
    email: undefined,
  }), "||");

  assert.deepEqual(plain(runtime.mergeTrackerEntriesById([
    { id: "a", title: "old", score: 1 },
    { id: "b", archived: true },
  ], [
    { id: "a", title: "new" },
    { id: "c", title: "fresh" },
  ])), [
    { id: "a", title: "new", score: 1 },
    { id: "c", title: "fresh" },
  ]);
});

test("bootstrap runtime evaluates tracker snapshot reuse and cached data presence", () => {
  const runtime = loadRuntime();

  assert.equal(typeof runtime.canUseHomeBootstrapTrackerSnapshot, "function");
  assert.equal(typeof runtime.hasCachedSalesOverviewData, "function");
  assert.equal(typeof runtime.hasCachedHomeBootstrapData, "function");

  assert.equal(runtime.canUseHomeBootstrapTrackerSnapshot({
    uiMode: "user",
    globalScope: true,
    snapshotActive: true,
    query: "",
    region: "",
    editedOnly: false,
    page: 1,
  }), true);

  assert.equal(runtime.canUseHomeBootstrapTrackerSnapshot({
    uiMode: "admin",
    globalScope: true,
    snapshotActive: true,
    query: "",
    region: "",
    editedOnly: false,
    page: 1,
  }), false);

  assert.equal(runtime.canUseHomeBootstrapTrackerSnapshot({
    uiMode: "user",
    globalScope: true,
    snapshotActive: true,
    query: "abc",
    region: "",
    editedOnly: false,
    page: 1,
  }), false);

  assert.equal(runtime.hasCachedSalesOverviewData({
    mySalesClaims: [],
    companySalesClaims: [],
    organizationUsers: [],
  }), false);

  assert.equal(runtime.hasCachedSalesOverviewData({
    mySalesClaims: [{ id: "claim-1" }],
    companySalesClaims: [],
    organizationUsers: [],
  }), true);

  assert.equal(runtime.hasCachedHomeBootstrapData({
    homeBootstrapTrackerSnapshotActive: false,
    mySalesClaims: [],
    companySalesClaims: [],
    organizationUsers: [],
  }), false);

  assert.equal(runtime.hasCachedHomeBootstrapData({
    homeBootstrapTrackerSnapshotActive: true,
    mySalesClaims: [],
    companySalesClaims: [],
    organizationUsers: [],
  }), true);
});

test("bootstrap runtime detects missing endpoint errors", () => {
  const runtime = loadRuntime();

  assert.equal(typeof runtime.isMissingSalesOverviewEndpointError, "function");
  assert.equal(typeof runtime.isMissingHomeBootstrapEndpointError, "function");

  assert.equal(runtime.isMissingSalesOverviewEndpointError({
    status: 404,
    path: "/api/sales-claims/overview",
    payload: { error: { code: "" } },
  }), true);

  assert.equal(runtime.isMissingSalesOverviewEndpointError({
    status: 404,
    path: "/api/sales-claims/overview",
    payload: { error: { code: "not_found" } },
  }), false);

  assert.equal(runtime.isMissingSalesOverviewEndpointError({
    status: 500,
    path: "/api/sales-claims/overview",
    payload: null,
  }), false);

  assert.equal(runtime.isMissingHomeBootstrapEndpointError({
    status: 404,
    path: "/api/home-bootstrap",
  }), true);

  assert.equal(runtime.isMissingHomeBootstrapEndpointError({
    status: 404,
    path: "/api/home-bootstrap/v2",
  }), true);

  assert.equal(runtime.isMissingHomeBootstrapEndpointError({
    status: 404,
    path: "/api/other-route",
  }), false);
});
