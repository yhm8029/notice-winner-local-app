import test from "node:test";
import assert from "node:assert/strict";
import { createSalesPanelControllerDeps, normalizeSalesClaimCardViewModel } from "../../frontend/app-controller-deps.js";

test("app controller deps preserves injected sales claim card normalizer override", () => {
  const override = () => ({ injected: true });
  const deps = createSalesPanelControllerDeps({
    normalizeSalesClaimCardViewModel: override,
  });

  assert.strictEqual(deps.normalizeSalesClaimCardViewModel, override);
});

test("app controller deps falls back to the shared sales claim card normalizer export", () => {
  const deps = createSalesPanelControllerDeps({});

  assert.strictEqual(deps.normalizeSalesClaimCardViewModel, normalizeSalesClaimCardViewModel);
});
