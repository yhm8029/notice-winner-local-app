import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

test("renderTrackerEntries is a thin wrapper around the tracker render controller", () => {
  const source = readAppSource();
  const start = source.indexOf("function renderTrackerEntries");
  const end = source.indexOf("function renderTrackerEntriesFallback", start);
  const block = source.slice(start, end);

  assert.ok(block.length > 0, "renderTrackerEntries wrapper should exist");
  assert.match(block, /getTrackerRenderController/);
  assert.match(block, /controller\?\.renderTrackerEntries/);
  assert.match(block, /renderTrackerEntriesFallback/);
  assert.doesNotMatch(block, /buildTrackerEntriesEmptyStateView/);
  assert.doesNotMatch(block, /buildTrackerEntryCardView/);
  assert.doesNotMatch(block, /buildTrackerEntriesListMarkup/);
  assert.doesNotMatch(block, /window\.getSelection\?\.\(\)|window\.getSelection\(/);
  assert.doesNotMatch(block, /!selection\.isCollapsed|selection\.toString\(\)\.trim\(\)/);
  assert.doesNotMatch(block, /dom\.trackerEntriesList\.innerHTML\s*=\s*displayEntries\s*\.map/);
  assert.doesNotMatch(block, /overridden_fields|overrideMetaHtml/);
});

test("tracker entry fallback wrappers delegate to the fallback runtime", () => {
  const source = readAppSource();

  const cardStart = source.indexOf("function buildTrackerEntryCardMarkupFallback(");
  const cardEnd = source.indexOf("function renderTrackerEntriesFallback(", cardStart);
  const cardBlock = source.slice(cardStart, cardEnd);
  assert.ok(cardBlock.length > 0, "buildTrackerEntryCardMarkupFallback wrapper should exist");
  assert.match(cardBlock, /getTrackerRenderFallbackRuntime/);
  assert.match(cardBlock, /buildTrackerEntryCardMarkupFallback/);
  assert.doesNotMatch(cardBlock, /entry-shell|entry-no-badge|siteLocationText|entry-metrics/);

  const entriesStart = source.indexOf("function renderTrackerEntriesFallback(");
  const entriesEnd = source.indexOf("function buildTrackerBoardMarkupFallback(", entriesStart);
  const entriesBlock = source.slice(entriesStart, entriesEnd);
  assert.ok(entriesBlock.length > 0, "renderTrackerEntriesFallback wrapper should exist");
  assert.match(entriesBlock, /getTrackerRenderFallbackRuntime/);
  assert.match(entriesBlock, /renderTrackerEntriesFallback/);
  assert.doesNotMatch(entriesBlock, /data-entry-related-toggle|data-sales-claim|entry-shell|entry-no-badge|entry-metrics/);
});

test("tracker entry summary detail delegates to the tracker entry runtime", () => {
  const source = readAppSource();
  const start = source.indexOf("const FRONTEND_RUNTIME_ADAPTERS =");
  const end = source.indexOf("function readConsoleCacheEnvelope(", start);
  const block = source.slice(start, end);

  assert.ok(block.length > 0, "buildTrackerEntrySummaryDetail wrapper should exist");
  assert.match(block, /APP_SUPPORT\.createFrontendRuntimeAdapters\(/);
  assert.match(block, /FRONTEND_RUNTIME_ADAPTERS/);
  assert.match(block, /TRACKER_ENTRY_RUNTIME/);
  assert.match(block, /buildTrackerEntrySummaryDetail/);
  assert.doesNotMatch(block, /_summary_only|function buildTrackerEntrySummaryDetailFallback/);
});

test("tracker entry summary alias in app.js stays runtime-only", () => {
  const source = readAppSource();
  const start = source.indexOf("const FRONTEND_RUNTIME_ADAPTERS =");
  const end = source.indexOf("function readConsoleCacheEnvelope(", start);
  const block = source.slice(start, end);

  assert.ok(block.length > 0, "toTrackerEntrySummary alias should exist");
  assert.match(block, /APP_SUPPORT\.createFrontendRuntimeAdapters\(/);
  assert.match(block, /FRONTEND_RUNTIME_ADAPTERS/);
  assert.match(block, /TRACKER_ENTRY_RUNTIME/);
  assert.match(block, /toTrackerEntrySummary/);
  assert.doesNotMatch(block, /function toTrackerEntrySummaryFallback/);
  assert.doesNotMatch(block, /source_run_id|project_id|overridden_fields|field_diagnostics/);
});
