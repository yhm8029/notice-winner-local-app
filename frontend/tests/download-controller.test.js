const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

async function loadDownloadController() {
  const sourcePath = path.join(__dirname, "..", "download-controller.js");
  const tempPath = path.join(os.tmpdir(), `download-controller-${Date.now()}-${Math.random()}.mjs`);
  fs.writeFileSync(tempPath, fs.readFileSync(sourcePath, "utf8"));
  try {
    return await import(pathToFileURL(tempPath).href);
  } finally {
    fs.rmSync(tempPath, { force: true });
  }
}

function createFakeDocument() {
  const bodyChildren = [];
  const anchors = [];
  const overlay = {
    id: "download-progress-overlay",
    className: "download-progress-overlay hidden",
    innerHTML: "",
    classList: {
      add() {},
      remove() {},
    },
    querySelector() {
      return { textContent: "" };
    },
  };
  return {
    body: {
      appendChild(node) {
        bodyChildren.push(node);
      },
    },
    querySelector(selector) {
      if (selector === "#download-progress-overlay") {
        return bodyChildren.find((node) => node.id === "download-progress-overlay") || null;
      }
      return null;
    },
    createElement(tagName) {
      if (tagName === "div") {
        return overlay;
      }
      const anchor = {
        href: "",
        download: "",
        clickCalled: false,
        click() {
          this.clickCalled = true;
        },
        remove() {},
      };
      anchors.push(anchor);
      return anchor;
    },
    getAnchors() {
      return anchors;
    },
  };
}

test("tracker xlsx download saves directly to local downloads folder", async () => {
  const { createDownloadController } = await loadDownloadController();
  const fetchedUrls = [];
  const fetchMethods = [];
  const apiCalls = [];
  const document = createFakeDocument();
  const flashes = [];
  const controller = createDownloadController({
    state: {
      trackerFilters: { q: "", region: "", noticeYear: "2026", editedOnly: false },
      uiMode: "admin",
    },
    dom: {},
    document,
    window: {
      URL: {
        createObjectURL() {
          return "blob:download";
        },
        revokeObjectURL() {},
      },
      requestAnimationFrame(callback) {
        callback();
      },
      setInterval() {
        return 1;
      },
      clearInterval() {},
      setTimeout(callback) {
        callback();
        return 1;
      },
      clearTimeout() {},
    },
    setBusy() {},
    flash(message, kind) {
      flashes.push([message, kind]);
    },
    api(url) {
      apiCalls.push(url);
      throw new Error("download job API must not be called");
    },
    fetch(url, options = {}) {
      fetchedUrls.push(url);
      fetchMethods.push(options.method || "GET");
      return Promise.resolve({
        ok: true,
        headers: {
          get(name) {
            return String(name).toLowerCase() === "content-type" ? "application/json" : "";
          },
        },
        json() {
          return Promise.resolve({
            file_name: "SPMS_20260610.xlsx",
            path: "C:\\Users\\user\\Downloads\\SPMS_20260610.xlsx",
            row_count: 1,
          });
        },
      });
    },
    readTrackerFiltersFromControls() {},
    useGlobalTrackerEntriesScope() {
      return true;
    },
  });

  await controller.triggerTrackerEntriesXlsxDownload();

  assert.equal(apiCalls.length, 0);
  assert.equal(fetchedUrls.length, 1);
  assert.equal(fetchMethods[0], "POST");
  assert.match(fetchedUrls[0], /^\/api\/tracker-entry-summaries\/download-local\?/);
  assert.match(fetchedUrls[0], /notice_year=2026/);
  assert.equal(document.getAnchors().length, 0);
  assert.equal(flashes.at(-1)[1], "success");
  assert.match(flashes.at(-1)[0], /SPMS_20260610\.xlsx/);
});
