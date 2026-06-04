import assert from "node:assert/strict";
import test from "node:test";
import { createProjectRelatedController } from "../../frontend/project-related-controller.js";

function createController(overrides = {}) {
  const openedUrls = [];
  const assignedUrls = [];
  const apiCalls = [];
  const renderedPayloads = [];
  const appendedElements = [];
  const createdIframes = [];
  const createElement = (tagName) => {
    const element = {
      tagName: String(tagName || "").toUpperCase(),
      className: "",
      textContent: "",
      attributes: {},
      children: [],
      style: {},
      closed: false,
      src: "",
      srcdoc: "",
      setAttribute(name, value) {
        this.attributes[name] = String(value);
      },
      append(...children) {
        this.children.push(...children);
      },
      appendChild(child) {
        this.children.push(child);
        return child;
      },
      addEventListener() {},
      remove() {
        this.removed = true;
      },
    };
    if (element.tagName === "IFRAME") {
      createdIframes.push(element);
    }
    return element;
  };
  const popup = {
    closed: false,
    location: {
      href: "",
      replace(url) {
        openedUrls.push(url);
        this.href = url;
      },
    },
    document: {
      open() {},
      write() {},
      close() {},
    },
  };
  const controller = createProjectRelatedController({
    state: {
      projectRelatedPayloads: {},
      projectRelatedNotices: {},
      projectRelatedErrors: {},
      projectRelatedLoadingId: null,
      uiMode: "user",
      trackerEntries: [],
      ...overrides.state,
    },
    window: {
      localStorage: null,
      location: {
        href: "",
        assign(url) {
          assignedUrls.push(url);
          this.href = url;
        },
      },
      document: {
        body: {
          appendChild(element) {
            appendedElements.push(element);
            return element;
          },
        },
        createElement,
        getElementById() {
          return null;
        },
      },
      open() {
        openedUrls.push("about:blank");
        return popup;
      },
      clearTimeout() {},
      setTimeout() {
        return 1;
      },
    },
    api: async (url) => {
      apiCalls.push(url);
      return { title: "notice", documents: [] };
    },
    flash: () => {},
    escapeHtml: (value) => String(value ?? ""),
    RELATED_NOTICE_RUNTIME: {
      buildProjectNoticeUrl() {
        return "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01434430&bidPbancOrd=000";
      },
      buildRelatedNoticePanelMarkup() {
        return "";
      },
      extractTrackerEntryBidParts() {
        return { bidNo: "", bidOrd: "" };
      },
      buildTrackerEntryNoticeUrl() {
        return "";
      },
      ...overrides.RELATED_NOTICE_RUNTIME,
    },
    PROJECT_RELATED_READY_CACHE_TTL_MS: 1,
    PROJECT_RELATED_SEED_CACHE_TTL_MS: 1,
    PROJECT_RELATED_STORAGE_KEY: "project-related",
    PROJECT_RELATED_STORAGE_MAX_ITEMS: 5,
    renderNoticeViewerWindow: () => {},
    renderNoticeViewerPayload: (...args) => renderedPayloads.push(args),
    renderNoticeViewerError: () => {},
    renderProjects: () => {},
    renderTrackerEntries: () => {},
    loadProjectRelatedNotices: async () => {},
    loadSelectedEntryDetail: async () => null,
  });
  return { controller, openedUrls, assignedUrls, apiCalls, renderedPayloads, appendedElements, createdIframes };
}

test("tracker entry notice viewer navigates the current WebView to the Synap route", async () => {
  const { controller, openedUrls, assignedUrls, createdIframes } = createController();

  await controller.openTrackerEntryNoticeViewer("entry-1");

  assert.deepEqual(openedUrls, []);
  assert.deepEqual(assignedUrls, ["/api/tracker-entries/entry-1/notice-file-view?desktop=1"]);
  assert.equal(createdIframes.length, 0);
});

test("project notice viewer uses the local notice API instead of opening a popup or raw g2b link", async () => {
  const { controller, openedUrls, apiCalls, renderedPayloads, createdIframes } = createController();

  await controller.openProjectNoticeViewer({ id: "project-1", project_name: "Project One" });

  assert.deepEqual(openedUrls, []);
  assert.deepEqual(apiCalls, ["/api/projects/project-1/notice-view"]);
  assert.equal(renderedPayloads.length, 1);
  assert.equal(createdIframes.length, 1);
});
