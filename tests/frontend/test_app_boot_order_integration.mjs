import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app.js");
const appRuntimeBodyPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function readAppRuntimeBodySource() {
  return fs.readFileSync(appRuntimeBodyPath, "utf8");
}

test("app.js loads the extracted runtime body", () => {
  const source = readAppSource();
  assert.match(source, /app-runtime-body\.js/);
  assert.doesNotMatch(source, /void boot\(\);/);
});

test("boot is invoked after late-bound backfill helpers are declared", () => {
  const source = readAppRuntimeBodySource();
  const bootIndex = source.indexOf("void boot();");
  const helperIndex = source.indexOf("buildBackfillConflictsView,");

  assert.notEqual(bootIndex, -1);
  assert.notEqual(helperIndex, -1);
  assert.ok(
    bootIndex > helperIndex,
    "boot() must run after buildBackfillConflictsView is initialized so startup does not hit the TDZ",
  );
});
