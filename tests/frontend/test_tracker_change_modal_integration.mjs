import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readCombinedCssSource } from "./css-source.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const shellRuntimePath = path.resolve(__dirname, "../../frontend/app-shell-runtime.js");
const stylesPath = path.resolve(__dirname, "../../frontend/styles.css");
const runtimePath = path.resolve(__dirname, "../../frontend/tracker-change-runtime.js");

function read(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

test("tracker change modal selectors exist in the app shell runtime", () => {
  const source = read(shellRuntimePath);

  assert.match(source, /trackerChangeModal: query\("#tracker-change-modal"\)/);
  assert.match(source, /trackerChangeModalList: query\("#tracker-change-modal-list"\)/);
  assert.match(source, /trackerChangeModalCloseButton: query\("#tracker-change-modal-close-button"\)/);
});

test("tracker change bell opens a modal instead of scrolling to the inline panel", () => {
  const source = read(appPath);

  assert.match(source, /function openTrackerChangeModal\(/);
  assert.match(source, /function closeTrackerChangeModal\(/);
  assert.match(source, /dom\.trackerChangeBell\.addEventListener\("click"/);
  assert.match(source, /openTrackerChangeModal\(\)/);
  assert.doesNotMatch(source, /trackerChangePanel\?\.scrollIntoView/);
});

test("tracker change modal styles exist", () => {
  const source = readCombinedCssSource(stylesPath);

  assert.match(source, /\.tracker-change-modal/);
  assert.match(source, /\.tracker-change-modal-card/);
  assert.match(source, /\.tracker-change-modal-list/);
});

test("tracker change events hydrate from cache so the modal can render immediately", () => {
  const source = read(appPath);

  assert.match(source, /TRACKER_CHANGE_EVENTS_STORAGE_KEY/);
  assert.match(source, /function hydrateTrackerChangeEventsCache\(/);
  assert.match(source, /function persistTrackerChangeEventsCache\(/);
  assert.match(source, /hydrateTrackerChangeEventsCache\(\)/);
});

test("tracker change runtime no longer prints raw tracker_export source text in the list footer", () => {
  const source = read(runtimePath);

  assert.match(source, /function formatTrackerChangeSourceLabel\(/);
  assert.doesNotMatch(source, /item\.source_kind \|\| "-"/);
});
