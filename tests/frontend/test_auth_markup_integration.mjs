import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const htmlPath = path.resolve(__dirname, "../../frontend/index.html");

function readHtmlSource() {
  return fs.readFileSync(htmlPath, "utf8");
}

function countMatches(source, pattern) {
  return [...source.matchAll(pattern)].length;
}

test("auth form submits with POST semantics so credentials do not fall into the query string", () => {
  const source = readHtmlSource();

  assert.match(source, /<form id="auth-form" class="auth-form" method="post">/);
});

test("hero meta cards are not duplicated in the HTML shell", () => {
  const source = readHtmlSource();

  assert.equal(countMatches(source, /id="api-meta-card"/g), 1);
  assert.equal(countMatches(source, /id="sync-meta-card"/g), 1);
});
