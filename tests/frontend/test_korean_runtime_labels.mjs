import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, "../../frontend");
const mojibakePattern = /\?ㅽ뻾|\?\?\?덈뺄|繞|戮|蹂몄씤/;

function extractBetween(source, startNeedle, endNeedle) {
  const start = source.indexOf(startNeedle);
  const end = source.indexOf(endNeedle, start);
  assert.notEqual(start, -1, `missing ${startNeedle}`);
  assert.notEqual(end, -1, `missing ${endNeedle}`);
  return source.slice(start, end);
}

test("run start busy labels are readable Korean", () => {
  const appBody = fs.readFileSync(path.join(frontendRoot, "app-runtime-body.js"), "utf8");
  const runHelpers = fs.readFileSync(path.join(frontendRoot, "run-panels-controller-helpers.js"), "utf8");

  assert.match(appBody, /busyLabel: "실행 시작 중\.\.\."/);
  assert.match(runHelpers, /busyLabel \|\| "실행 시작 중\.\.\."/);
});

test("run start flow does not contain known mojibake labels shown to users", () => {
  const appBody = fs.readFileSync(path.join(frontendRoot, "app-runtime-body.js"), "utf8");
  const runHelpers = fs.readFileSync(path.join(frontendRoot, "run-panels-controller-helpers.js"), "utf8");
  const trackerRuns = fs.readFileSync(path.join(frontendRoot, "tracker-controller-runs-runtime.js"), "utf8");

  const handleRunCreate = extractBetween(appBody, "async function handleRunCreate", "async function loadRuns");
  const createWinnerRun = extractBetween(runHelpers, "async function createWinnerRun", "function syncCollectModeOptions");

  assert.doesNotMatch(handleRunCreate, mojibakePattern);
  assert.doesNotMatch(createWinnerRun, mojibakePattern);
  assert.doesNotMatch(trackerRuns, /\?ㅽ뻾/);
});
