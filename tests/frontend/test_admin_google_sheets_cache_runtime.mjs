import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/admin-google-sheets-cache-runtime.js");

function createStorage(initial = {}) {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  };
}

function loadRuntime({ localStorage } = {}) {
  const source = fs.readFileSync(runtimePath, "utf8");
  const window = { localStorage };
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.SPMSAdminGoogleSheetsCacheRuntime;
}

test("readAdminGoogleSheetsCache returns null for malformed cache payloads", () => {
  const storage = createStorage({
    "notice-winner-pipeline-web.adminGoogleSheetsCache.v1": '{"broken":true}',
  });
  const runtime = loadRuntime({ localStorage: storage });

  assert.equal(runtime.readAdminGoogleSheetsCache({ storage }), null);
});

test("writeAdminGoogleSheetsCache stores bootstrap and payloads using the versioned key", () => {
  const storage = createStorage();
  const runtime = loadRuntime({ localStorage: storage });

  runtime.writeAdminGoogleSheetsCache(
    {
      bootstrap: {
        sync_status: "ready",
        tabs: [{ key: "sheet-11", display_title: "Design List" }],
      },
      payloadsByKey: {
        "sheet-11": {
          key: "sheet-11",
          header_cells: [{ text: "Name", href: "" }],
          row_cells: [[{ text: "Cached Alice", href: "" }]],
        },
      },
    },
    { storage, nowFn: () => 1713430800000 },
  );

  assert.deepEqual(JSON.parse(JSON.stringify(runtime.readAdminGoogleSheetsCache({ storage }))), {
    savedAt: 1713430800000,
    bootstrap: {
      sync_status: "ready",
      tabs: [{ key: "sheet-11", display_title: "Design List" }],
    },
    payloadsByKey: {
      "sheet-11": {
        key: "sheet-11",
        header_cells: [{ text: "Name", href: "" }],
        row_cells: [[{ text: "Cached Alice", href: "" }]],
      },
    },
  });
});

test("writeAdminGoogleSheetsCache accepts object-map tabs and headers rows payloads", () => {
  const storage = createStorage();
  const runtime = loadRuntime({ localStorage: storage });

  runtime.writeAdminGoogleSheetsCache(
    {
      bootstrap: {
        sync_status: "ready",
        tabs: {
          "sheet-21": { key: "sheet-21", display_title: "Summary" },
        },
      },
      payloadsByKey: {
        "sheet-21": {
          key: "sheet-21",
          headers: [{ text: "Region", href: "" }],
          rows: [[{ text: "Seoul", href: "" }]],
        },
      },
    },
    { storage, nowFn: () => 1713430801234 },
  );

  assert.deepEqual(JSON.parse(JSON.stringify(runtime.readAdminGoogleSheetsCache({ storage }))), {
    savedAt: 1713430801234,
    bootstrap: {
      sync_status: "ready",
      tabs: {
        "sheet-21": { key: "sheet-21", display_title: "Summary" },
      },
    },
    payloadsByKey: {
      "sheet-21": {
        key: "sheet-21",
        headers: [{ text: "Region", href: "" }],
        rows: [[{ text: "Seoul", href: "" }]],
      },
    },
  });
});

test("clearAdminGoogleSheetsCache removes the stored envelope", () => {
  const storage = createStorage();
  const runtime = loadRuntime({ localStorage: storage });

  runtime.writeAdminGoogleSheetsCache(
    { bootstrap: { sync_status: "ready", tabs: [] }, payloadsByKey: {} },
    { storage, nowFn: () => 1 },
  );
  runtime.clearAdminGoogleSheetsCache({ storage });

  assert.equal(runtime.readAdminGoogleSheetsCache({ storage }), null);
});
