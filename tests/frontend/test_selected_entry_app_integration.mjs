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

test("selected entry wrappers delegate to the selected-entry controller", () => {
  const source = readAppSource();
  const selectedEntrySection = source.slice(
    source.indexOf("function renderSelectedEntryLoading("),
    source.indexOf("async function patchTrackerEntry("),
  );
  const getterSection = source.slice(
    source.indexOf("function getSelectedEntryController() {"),
    source.indexOf("function getRunPanelsController() {"),
  );

  assert.ok(selectedEntrySection.length > 0, "selected entry render section should exist");
  assert.ok(getterSection.length > 0, "selected entry getter section should exist");
  assert.doesNotMatch(selectedEntrySection, /function legacyRender/);
  assert.match(getterSection, /createControllerWithWiringDeps\(\{/);
  assert.match(getterSection, /wiringDepsFactoryName:\s*"createSelectedEntryControllerDeps"/);
  assert.match(getterSection, /missingFactoryError:\s*"Missing selected entry controller runtime: window\.SELECTED_ENTRY_CONTROLLER\.createSelectedEntryController"/);
  assert.match(getterSection, /APP_SUPPORT\.createSelectedEntryControllerDepsHelpers\(\{/);
  assert.match(getterSection, /buildSelectedEntryControllerDeps\(\)/);
  assert.match(selectedEntrySection, /function renderSelectedEntryLoading[\s\S]*getSelectedEntryController/);
  assert.match(selectedEntrySection, /function renderSelectedEntryLoading[\s\S]*getSelectedEntryController\(\)\.renderSelectedEntryLoading/);
  assert.match(selectedEntrySection, /function renderSelectedEntryChangeEvents[\s\S]*getSelectedEntryController\(\)\.renderSelectedEntryChangeEvents/);
  assert.match(selectedEntrySection, /function getSelectedEntryDisplayView[\s\S]*getSelectedEntryController\(\)\.getSelectedEntryDisplayView/);
  assert.match(selectedEntrySection, /function renderEntryDiagnostics[\s\S]*getSelectedEntryController\(\)\.renderEntryDiagnostics/);
  assert.match(selectedEntrySection, /function renderEntryFieldGrid[\s\S]*getSelectedEntryController\(\)\.renderEntryFieldGrid/);
  assert.match(selectedEntrySection, /function renderDrawer[\s\S]*getSelectedEntryController\(\)\.renderDrawer/);
  assert.match(selectedEntrySection, /function renderSelectedEntry[\s\S]*getSelectedEntryController\(\)\.renderSelectedEntry/);
  assert.match(selectedEntrySection, /function syncPatchValueFromSelectedEntry[\s\S]*getSelectedEntryController\(\)\.syncPatchValueFromSelectedEntry/);
  assert.doesNotMatch(selectedEntrySection, /buildSelectedEntryLoadingViewFallback/);
  assert.doesNotMatch(selectedEntrySection, /buildSelectedEntryEmptyViewFallback/);
  assert.doesNotMatch(selectedEntrySection, /buildPatchPanelViewFallback/);
  assert.doesNotMatch(selectedEntrySection, /buildSelectedEntryDisplayViewFallback/);
});
