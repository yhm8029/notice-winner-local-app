const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function loadRuntime(path) {
  const source = fs.readFileSync(path, "utf8");
  const context = { window: {}, URLSearchParams };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context.window.SPMSConsoleDataRuntime;
}

function createDeps(overrides = {}) {
  return {
    state: {
      auth: {
        enabled: true,
        authorized: true,
      },
      organizationMembers: [],
      organizationMembersError: "",
      organizationMembersLoaded: false,
      organizationPlanSummary: null,
      organizationInvitations: [],
      organizationInvitationsError: "",
      organizationInvitationsLoaded: false,
      organizationAuditLogs: [],
      organizationAuditLogsLoading: false,
      organizationAuditLogsError: "",
      organizationAuditLogsLimit: 5,
      organizationAuditLogsLoaded: false,
      organizationDownloadAuditLogs: [],
      organizationDownloadAuditLogsLoading: false,
      organizationDownloadAuditLogsError: "",
      organizationDownloadAuditLogsLimit: 5,
      organizationDownloadAuditLogsLoaded: false,
      organizationLoginAuditLogs: [],
      organizationLoginAuditLogsLoading: false,
      organizationLoginAuditLogsError: "",
      organizationLoginAuditLogsLimit: 5,
      organizationLoginAuditLogsLoaded: false,
      organizationAdminDataRequest: null,
      organizationAdminDataRequestId: 0,
    },
    api: async () => ({ items: [] }),
    readOrganizationAdminBootstrapCache: () => null,
    persistOrganizationAdminBootstrapCache: () => false,
    flash: () => {},
    canUseAdminMode: () => true,
    mergeOrganizationInvitations: (items) => items,
    renderOrganizationAdminPanel: () => {},
    ...overrides,
  };
}

async function flushAsyncWork() {
  await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
}

test("loadOrganizationDownloadAuditLogs fetches admin endpoint and stores items", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const requests = [];
  let renderCount = 0;
  const deps = createDeps({
    api: async (path) => {
      requests.push(path);
      return {
        items: [
          {
            file_name: "company_active_sales.xlsx",
            user_email: "admin@example.com",
          },
        ],
      };
    },
    renderOrganizationAdminPanel: () => {
      renderCount += 1;
    },
  });

  await runtime.loadOrganizationDownloadAuditLogs(deps);

  assert.deepEqual(requests, ["/api/admin/download-audit-logs?limit=6"]);
  assert.equal(deps.state.organizationDownloadAuditLogsLoading, false);
  assert.equal(deps.state.organizationDownloadAuditLogsError, "");
  assert.equal(deps.state.organizationDownloadAuditLogs.length, 1);
  assert.equal(deps.state.organizationDownloadAuditLogs[0].file_name, "company_active_sales.xlsx");
  assert.equal(renderCount, 2);
});

test("loadVisibleSalesClaims clears stale visible claims when the request fails", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const flashes = [];
  let renderCount = 0;
  const deps = {
    state: {
      auth: {
        enabled: true,
        authorized: true,
        user: { id: "user-1" },
      },
      trackerEntries: [
        { id: "entry-1", project_id: "project-1" },
        { id: "entry-2", project_id: "project-2" },
      ],
      salesClaimsByProjectId: {
        "project-1": { project_id: "project-1", is_active: true },
        "project-2": { project_id: "project-2", is_active: true },
      },
    },
    getVisibleSalesProjectIds: () => ["project-1", "project-2"],
    api: async () => {
      throw new Error("visible claims fetch failed");
    },
    replaceVisibleSalesClaims: (items) => {
      const visibleKeys = new Set(["project-1", "project-2"]);
      for (const key of visibleKeys) {
        delete deps.state.salesClaimsByProjectId[key];
      }
      for (const item of items || []) {
        deps.state.salesClaimsByProjectId[String(item.project_id || "")] = item;
      }
    },
    renderTrackerEntries: () => {
      renderCount += 1;
    },
    flash: (message) => {
      flashes.push(message);
    },
  };

  await runtime.loadVisibleSalesClaims(deps);

  assert.deepEqual(deps.state.salesClaimsByProjectId, {});
  assert.equal(renderCount, 1);
  assert.deepEqual(flashes, ["visible claims fetch failed"]);
});

test("loadHomeBootstrap loads tracker entries when the current view cannot use the snapshot page", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const calls = [];
  const deps = {
    state: {
      auth: {
        enabled: true,
        authorized: true,
        user: { id: "user-1" },
      },
      trackerFilters: {
        page: 3,
        pageSize: 20,
        q: "",
        region: "",
        editedOnly: false,
      },
      homeBootstrapAvailability: "unknown",
      homeBootstrapRequest: null,
      homeBootstrapTrackerSnapshotActive: false,
    },
    api: async (path) => {
      calls.push(path);
      return {
        tracker_first_page: {
          items: [{ id: "entry-1" }],
          total: 20,
          page: 1,
          page_size: 20,
        },
        company_items: [],
        my_items: [],
        organization_users: [],
      };
    },
    applyHomeBootstrapPayload: () => {
      calls.push("applyHomeBootstrapPayload");
      deps.state.homeBootstrapTrackerSnapshotActive = false;
    },
    persistHomeBootstrapCache: () => {
      calls.push("persistHomeBootstrapCache");
    },
    persistSalesOverviewCache: () => {
      calls.push("persistSalesOverviewCache");
    },
    loadTrackerEntries: async ({ silent }) => {
      calls.push(`loadTrackerEntries:${silent ? "silent" : "loud"}`);
    },
    hasCachedHomeBootstrapData: () => false,
    hasCachedSalesOverviewData: () => false,
    isMissingHomeBootstrapEndpointError: () => false,
    loadSalesOverview: async () => {
      throw new Error("unexpected loadSalesOverview call");
    },
    flash: () => {},
  };

  await runtime.loadHomeBootstrap(deps, { silent: true });

  assert.deepEqual(calls, [
    "/api/home-bootstrap",
    "applyHomeBootstrapPayload",
    "persistHomeBootstrapCache",
    "persistSalesOverviewCache",
    "loadTrackerEntries:silent",
  ]);
});

test("loadHomeBootstrap falls back to legacy loading when auth is disabled", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const calls = [];
  const deps = {
    state: {
      auth: {
        enabled: false,
        authorized: false,
        user: null,
      },
      homeBootstrapAvailability: "unknown",
      homeBootstrapRequest: null,
      homeBootstrapTrackerSnapshotActive: false,
      trackerEntries: [],
      trackerEntriesTotal: 0,
      trackerFilters: {
        page: 1,
        pageSize: 20,
      },
      mySalesClaims: [],
      companySalesClaims: [],
      organizationUsers: [],
    },
    api: async () => {
      calls.push("api");
      return {};
    },
    loadTrackerEntries: async ({ silent }) => {
      calls.push(`loadTrackerEntries:${silent ? "silent" : "loud"}`);
    },
    renderMySalesClaimsPanel: () => {
      calls.push("renderMySalesClaimsPanel");
    },
    renderTrackerEntries: () => {
      calls.push("renderTrackerEntries");
    },
    persistHomeBootstrapCache: (payload) => {
      calls.push(`persistHomeBootstrapCache:${payload?.tracker_first_page?.items?.length || 0}`);
    },
  };

  await runtime.loadHomeBootstrap(deps, { silent: true });

  assert.deepEqual(calls, [
    "loadTrackerEntries:silent",
    "renderMySalesClaimsPanel",
    "renderTrackerEntries",
    "persistHomeBootstrapCache:0",
  ]);
});

test("loadOrganizationDownloadAuditLogs clears state when admin mode is unavailable", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  let renderCount = 0;
  const deps = createDeps({
    canUseAdminMode: () => false,
    renderOrganizationAdminPanel: () => {
      renderCount += 1;
    },
  });
  deps.state.organizationDownloadAuditLogs = [{ file_name: "stale.xlsx" }];
  deps.state.organizationDownloadAuditLogsLoading = true;
  deps.state.organizationDownloadAuditLogsError = "stale";

  await runtime.loadOrganizationDownloadAuditLogs(deps);

  assert.equal(Array.isArray(deps.state.organizationDownloadAuditLogs), true);
  assert.equal(deps.state.organizationDownloadAuditLogs.length, 0);
  assert.equal(deps.state.organizationDownloadAuditLogsLoading, false);
  assert.equal(deps.state.organizationDownloadAuditLogsError, "");
  assert.equal(renderCount, 1);
});

test("loadOrganizationLoginAuditLogs fetches admin endpoint and stores items", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const requests = [];
  let renderCount = 0;
  const deps = createDeps({
    api: async (path) => {
      requests.push(path);
      return {
        items: [
          {
            user_email: "member@example.com",
            user_agent: "Mozilla/5.0",
          },
        ],
      };
    },
    renderOrganizationAdminPanel: () => {
      renderCount += 1;
    },
  });

  await runtime.loadOrganizationLoginAuditLogs(deps);

  assert.deepEqual(requests, ["/api/admin/login-audit-logs?limit=6"]);
  assert.equal(deps.state.organizationLoginAuditLogsLoading, false);
  assert.equal(deps.state.organizationLoginAuditLogsError, "");
  assert.equal(deps.state.organizationLoginAuditLogs.length, 1);
  assert.equal(deps.state.organizationLoginAuditLogs[0].user_email, "member@example.com");
  assert.equal(renderCount, 2);
});

test("loadOrganizationLoginAuditLogs clears state when admin mode is unavailable", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  let renderCount = 0;
  const deps = createDeps({
    canUseAdminMode: () => false,
    renderOrganizationAdminPanel: () => {
      renderCount += 1;
    },
  });
  deps.state.organizationLoginAuditLogs = [{ user_email: "stale@example.com" }];
  deps.state.organizationLoginAuditLogsLoading = true;
  deps.state.organizationLoginAuditLogsError = "stale";

  await runtime.loadOrganizationLoginAuditLogs(deps);

  assert.equal(Array.isArray(deps.state.organizationLoginAuditLogs), true);
  assert.equal(deps.state.organizationLoginAuditLogs.length, 0);
  assert.equal(deps.state.organizationLoginAuditLogsLoading, false);
  assert.equal(deps.state.organizationLoginAuditLogsError, "");
  assert.equal(deps.state.organizationLoginAuditLogsLimit, 5);
  assert.equal(renderCount, 1);
});

test("loadOrganizationAdminData resets download audit state when auth is unavailable", () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  let renderCount = 0;
  const deps = createDeps({
    renderOrganizationAdminPanel: () => {
      renderCount += 1;
    },
  });
  deps.state.auth.authorized = false;
  deps.state.organizationDownloadAuditLogs = [{ file_name: "stale.xlsx" }];
  deps.state.organizationDownloadAuditLogsLoading = true;
  deps.state.organizationDownloadAuditLogsError = "stale";
  deps.state.organizationLoginAuditLogs = [{ user_email: "stale@example.com" }];
  deps.state.organizationLoginAuditLogsLoading = true;
  deps.state.organizationLoginAuditLogsError = "stale";

  runtime.loadOrganizationAdminData(deps);

  assert.equal(Array.isArray(deps.state.organizationDownloadAuditLogs), true);
  assert.equal(deps.state.organizationDownloadAuditLogs.length, 0);
  assert.equal(deps.state.organizationDownloadAuditLogsLoading, false);
  assert.equal(deps.state.organizationDownloadAuditLogsError, "");
  assert.equal(Array.isArray(deps.state.organizationLoginAuditLogs), true);
  assert.equal(deps.state.organizationLoginAuditLogs.length, 0);
  assert.equal(deps.state.organizationLoginAuditLogsLoading, false);
  assert.equal(deps.state.organizationLoginAuditLogsError, "");
  assert.equal(renderCount, 1);
});

test("loadOrganizationAdminData fetches a single bootstrap payload for initial admin data", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const requests = [];
  const deps = createDeps({
    api: (path) => {
      requests.push(path);
      return Promise.resolve({
        members: [],
        plan_summary: null,
        invitations: [],
        auth_audit_logs: { items: [], has_more: false },
        download_audit_logs: { items: [], has_more: false },
        login_audit_logs: { items: [], has_more: false },
      });
    },
  });

  await runtime.loadOrganizationAdminData(deps);

  assert.deepEqual(requests, ["/api/admin/organization-panel-bootstrap"]);
});

test("loadOrganizationInvitations marks empty results as loaded and uses a longer timeout budget", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const requestOptions = [];
  const deps = createDeps({
    api: async (_path, options) => {
      requestOptions.push(options);
      return { items: [], plan_summary: null };
    },
  });

  await runtime.loadOrganizationInvitations(deps);

  assert.equal(requestOptions.length, 1);
  assert.equal(requestOptions[0].timeoutMs, 30000);
  assert.equal(deps.state.organizationInvitationsLoaded, true);
  assert.deepEqual(deps.state.organizationInvitations, []);
});

test("loadOrganizationAdminData applies cached bootstrap immediately before refresh", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const requests = [];
  const renders = [];
  let resolveBootstrap;
  const cachedPayload = {
    members: [{ email: "cached-admin@example.com" }],
    plan_summary: { plan_label: "Cached Plan" },
    invitations: [{ email: "cached-invite@example.com" }],
    auth_audit_logs: { items: [{ event_type: "cached-event" }], has_more: true },
    download_audit_logs: { items: [{ file_name: "cached.xlsx" }], has_more: false },
    login_audit_logs: { items: [{ user_email: "cached-admin@example.com" }], has_more: false },
  };
  const deps = createDeps({
    readOrganizationAdminBootstrapCache: () => cachedPayload,
    api: (path) => {
      requests.push(path);
      if (path === "/api/admin/organization-panel-bootstrap") {
        return new Promise((resolve) => {
          resolveBootstrap = resolve;
        });
      }
      return Promise.resolve({ items: [] });
    },
    renderOrganizationAdminPanel: () => {
      renders.push({
        members: deps.state.organizationMembers.map((item) => item.email),
        invitations: deps.state.organizationInvitations.map((item) => item.email),
        authAuditLogs: deps.state.organizationAuditLogs.map((item) => item.event_type),
      });
    },
  });

  const request = runtime.loadOrganizationAdminData(deps);
  await flushAsyncWork();

  assert.deepEqual(requests, ["/api/admin/organization-panel-bootstrap"]);
  assert.equal(deps.state.organizationMembersLoaded, true);
  assert.equal(deps.state.organizationInvitationsLoaded, true);
  assert.equal(deps.state.organizationAuditLogsLoaded, true);
  assert.deepEqual(deps.state.organizationMembers.map((item) => item.email), ["cached-admin@example.com"]);
  assert.deepEqual(deps.state.organizationInvitations.map((item) => item.email), ["cached-invite@example.com"]);
  assert.deepEqual(deps.state.organizationAuditLogs.map((item) => item.event_type), ["cached-event"]);
  assert.ok(renders.length >= 1);

  resolveBootstrap({
    members: [{ email: "fresh-admin@example.com" }],
    plan_summary: { plan_label: "Fresh Plan" },
    invitations: [{ email: "fresh-invite@example.com" }],
    auth_audit_logs: { items: [{ event_type: "fresh-event" }], has_more: false },
    download_audit_logs: { items: [{ file_name: "fresh.xlsx" }], has_more: false },
    login_audit_logs: { items: [{ user_email: "fresh-admin@example.com" }], has_more: false },
  });
  await request;

  assert.deepEqual(deps.state.organizationMembers.map((item) => item.email), ["fresh-admin@example.com"]);
  assert.deepEqual(deps.state.organizationInvitations.map((item) => item.email), ["fresh-invite@example.com"]);
  assert.deepEqual(deps.state.organizationAuditLogs.map((item) => item.event_type), ["fresh-event"]);
});

test("loadOrganizationAdminData persists fresh bootstrap payload after single request", async () => {
  const runtime = loadRuntime("frontend/console-data-runtime.js");
  const persistedPayloads = [];
  const deps = createDeps({
    persistOrganizationAdminBootstrapCache: (payload) => {
      persistedPayloads.push(payload);
      return true;
    },
    api: async (path) => {
      assert.equal(path, "/api/admin/organization-panel-bootstrap");
      return {
        members: [{ email: "admin@example.com" }],
        plan_summary: { plan_label: "Basic" },
        invitations: [{ email: "invitee@example.com" }],
        auth_audit_logs: { items: [{ event_type: "member.updated" }], has_more: true },
        download_audit_logs: { items: [{ file_name: "download.xlsx" }], has_more: false },
        login_audit_logs: { items: [{ user_email: "admin@example.com" }], has_more: false },
      };
    },
  });

  await runtime.loadOrganizationAdminData(deps);

  assert.equal(persistedPayloads.length, 1);
  assert.deepEqual(persistedPayloads[0].members.map((item) => item.email), ["admin@example.com"]);
  assert.equal(deps.state.organizationAuditLogsHasMore, true);
  assert.equal(deps.state.organizationDownloadAuditLogsHasMore, false);
  assert.equal(deps.state.organizationLoginAuditLogsHasMore, false);
});
