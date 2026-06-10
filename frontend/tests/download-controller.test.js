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
      return {
        href: "",
        download: "",
        clickCalled: false,
        click() {
          this.clickCalled = true;
        },
        remove() {},
      };
    },
  };
}

test("tracker xlsx download uses direct file endpoint instead of download job polling", async () => {
  const { createDownloadController } = await loadDownloadController();
  const fetchedUrls = [];
  const apiCalls = [];
  const controller = createDownloadController({
    state: {
      trackerFilters: { q: "", region: "", noticeYear: "2026", editedOnly: false },
      uiMode: "admin",
    },
    dom: {},
    document: createFakeDocument(),
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
    flash(message) {
      throw new Error(message);
    },
    api(url) {
      apiCalls.push(url);
      throw new Error("download job API must not be called");
    },
    fetch(url) {
      fetchedUrls.push(url);
      return Promise.resolve({
        ok: true,
        headers: {
          get(name) {
            return String(name).toLowerCase() === "content-disposition"
              ? 'attachment; filename="project_status.xlsx"'
              : "";
          },
        },
        blob() {
          return Promise.resolve(new Blob(["xlsx"]));
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
  assert.match(fetchedUrls[0], /^\/api\/tracker-entry-summaries\/download\?/);
  assert.match(fetchedUrls[0], /notice_year=2026/);
});
