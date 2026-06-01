import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const vercelPath = path.resolve(__dirname, "../../frontend/vercel.json");

function readVercelConfig() {
  return JSON.parse(fs.readFileSync(vercelPath, "utf8"));
}

test("vercel rewrites admin section routes and runtime assets to the SPA document", () => {
  const config = readVercelConfig();
  const rewrites = Array.isArray(config.rewrites) ? config.rewrites : [];
  const rewriteBySource = new Map(rewrites.map((entry) => [entry.source, entry]));

  assert.equal(rewriteBySource.get("/app/project-status")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/project-status/")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/sales-recommendations")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/sales-recommendations/")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/design-list")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/design-list/")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/planned-orders")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/planned-orders/")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/lost")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/lost/")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/agency-list")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/agency-list/")?.destination, "/index.html");
  assert.equal(rewriteBySource.get("/app/:path*")?.destination, "/:path*");
});
