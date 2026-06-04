import assert from "node:assert/strict";
import test from "node:test";
import { createProjectRelatedController } from "../../frontend/project-related-controller.js";

function createController(overrides = {}) {
  const openedUrls = [];
  const apiCalls = [];
  const renderedPayloads = [];
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
      open() {
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
  return { controller, openedUrls, apiCalls, renderedPayloads };
}

test("tracker entry notice viewer opens the local Synap embed route", async () => {
  const { controller, openedUrls } = createController();

  await controller.openTrackerEntryNoticeViewer("entry-1");

  assert.deepEqual(openedUrls, ["/api/tracker-entries/entry-1/notice-file-view?embed=1"]);
});

test("project notice viewer uses the local notice API instead of opening the raw g2b link", async () => {
  const { controller, openedUrls, apiCalls, renderedPayloads } = createController();

  await controller.openProjectNoticeViewer({ id: "project-1", project_name: "Project One" });

  assert.deepEqual(openedUrls, []);
  assert.deepEqual(apiCalls, ["/api/projects/project-1/notice-view"]);
  assert.equal(renderedPayloads.length, 1);
});
