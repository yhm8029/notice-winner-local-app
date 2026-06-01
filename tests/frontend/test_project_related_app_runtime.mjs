import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/project-related-app-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8");
  const context = vm.createContext({ console, window: {} });
  vm.runInContext(source, context, { filename: runtimePath });
  return context.window.SPMSProjectRelatedAppRuntime;
}

test("project-related runtime exposes the app body helper factory", () => {
  const runtime = loadRuntime();
  assert.equal(typeof runtime?.createProjectRelatedBodyRuntime, "function");
});

test("project-related app body helper falls back to runtime notice viewer rendering", () => {
  const runtime = loadRuntime();
  const writes = [];
  const helper = runtime.createProjectRelatedBodyRuntime({
    getProjectRelatedController: () => null,
    getReportPanelsController: () => null,
    getExistingReportPanelsController: () => null,
    relatedNoticeRuntime: {
      buildNoticeViewerDocumentsMarkup() {
        return "<p>docs</p>";
      },
      buildNoticeViewerHtml({ title, meta, body }) {
        return `<html><body><h1>${title}</h1><div>${meta}</div>${body}</body></html>`;
      },
      formatNoticeViewerSourceLabel(value) {
        return String(value ?? "");
      },
    },
    escapeHtml: (value) => String(value ?? ""),
  });
  const targetWindow = {
    closed: false,
    document: {
      open() {
        writes.push("open");
      },
      write(value) {
        writes.push(value);
      },
      close() {
        writes.push("close");
      },
    },
  };

  assert.equal(
    helper.renderNoticeViewerPayload(
      targetWindow,
      { title: "notice-title", project_name: "alpha", bid_no: "B-1", bid_ord: "2", document_count: 3 },
      "fallback-title",
    ),
    undefined,
  );
  assert.match(writes[1], /notice-title/);

  writes.length = 0;
  assert.equal(
    helper.renderNoticeViewerError(targetWindow, { title: "error-title", errorMessage: "broken" }),
    undefined,
  );
  assert.match(writes[1], /error-title/);
});

test("project-related app body helper delegates project-related cache helpers to the controller", () => {
  const calls = [];
  const runtime = loadRuntime();
  const helper = runtime.createProjectRelatedBodyRuntime({
    getProjectRelatedController: () => ({
      hydrateProjectRelatedPayloadCache() {
        calls.push("hydrate");
        return "hydrate-result";
      },
      persistProjectRelatedPayloadCache() {
        calls.push("persist");
        return "persist-result";
      },
    }),
    getReportPanelsController: () => null,
    getExistingReportPanelsController: () => null,
    relatedNoticeRuntime: null,
    escapeHtml: (value) => String(value ?? ""),
  });

  assert.equal(helper.hydrateProjectRelatedPayloadCache(), "hydrate-result");
  assert.equal(helper.persistProjectRelatedPayloadCache(), "persist-result");
  assert.deepEqual(calls, ["hydrate", "persist"]);
});
