const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function buildApplySalesOverviewPayloadHarness() {
  const source = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
  const start = source.indexOf("function applySalesOverviewPayload(payload) {");
  const end = source.indexOf("function shouldApplyHomeBootstrapTrackerSnapshot()", start);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("Unable to locate applySalesOverviewPayload in app.js");
  }

  const context = {
    state: {
      companySalesClaims: [],
      mySalesClaims: [],
      organizationUsers: [],
      organizationUsersError: "stale",
      salesClaimsByProjectId: {
        "project-stale": { project_id: "project-stale", is_active: true },
      },
    },
    normalizeSalesOverviewPayload: (payload) => ({
      companyItems: Array.isArray(payload?.company_items) ? payload.company_items : [],
      myItems: Array.isArray(payload?.my_items) ? payload.my_items : [],
      organizationUsers: Array.isArray(payload?.organization_users) ? payload.organization_users : [],
    }),
    mergeActiveSalesClaims: (items) => {
      for (const item of items || []) {
        context.state.salesClaimsByProjectId[String(item.project_id || "")] = item;
      }
    },
  };
  vm.createContext(context);
  vm.runInContext(`${source.slice(start, end)}\nglobalThis.__applySalesOverviewPayload = applySalesOverviewPayload;`, context);
  return context;
}

test("applySalesOverviewPayload replaces stale visible claim state with the latest company items", () => {
  const harness = buildApplySalesOverviewPayloadHarness();

  harness.__applySalesOverviewPayload({
    company_items: [],
    my_items: [],
    organization_users: [],
  });

  assert.equal(Object.keys(harness.state.salesClaimsByProjectId).length, 0);
  assert.equal(harness.state.organizationUsersError, "");
});
