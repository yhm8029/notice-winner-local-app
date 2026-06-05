export function createAppProjectRelatedBridge(context = {}) {
  const {
    state = null,
    callProjectRelatedController = null,
    getTrackerController = () => null,
  } = context;

  function callTrackerController(methodName, ...args) {
    return getTrackerController()?.[methodName]?.(...args);
  }

  async function openTrackerEntryNoticeViewer(entryId, entries = state?.trackerEntries) {
    return callProjectRelatedController("openTrackerEntryNoticeViewer", entryId, entries);
  }

  function renderRelatedProjectNotices(project) {
    return callProjectRelatedController("renderRelatedProjectNotices", project);
  }

  function renderTrackerEntryRelatedNotices(entry) {
    return callProjectRelatedController("renderTrackerEntryRelatedNotices", entry);
  }

  function renderRelatedNoticePanel(projectId) {
    return callProjectRelatedController("renderRelatedNoticePanel", projectId);
  }

  function bindRelatedNoticeViewerButtons(root) {
    return callProjectRelatedController("bindRelatedNoticeViewerButtons", root);
  }

  async function openRelatedNoticeViewer(item) {
    return callProjectRelatedController("openRelatedNoticeViewer", item);
  }

  async function openProjectNoticeViewer(project) {
    return callProjectRelatedController("openProjectNoticeViewer", project);
  }

  function buildProjectNoticeUrl(project) {
    return callProjectRelatedController("buildProjectNoticeUrl", project);
  }

  function extractTrackerEntryBidParts(entry) {
    return callProjectRelatedController("extractTrackerEntryBidParts", entry);
  }

  function buildTrackerEntryNoticeUrl(entry) {
    return callProjectRelatedController("buildTrackerEntryNoticeUrl", entry);
  }

  function prefetchProjectRelatedNotices(projectIds) {
    return callTrackerController("prefetchProjectRelatedNotices", projectIds);
  }

  function prefetchVisibleProjectRelatedNotices(entries) {
    return callTrackerController("prefetchVisibleProjectRelatedNotices", entries);
  }

  function toggleProjectRelated(projectId) {
    return callTrackerController("toggleProjectRelated", projectId);
  }

  function toggleTrackerEntryRelated(entryId) {
    return callTrackerController("toggleTrackerEntryRelated", entryId);
  }

  function loadProjectRelatedNotices(projectId, options = {}) {
    return callTrackerController("loadProjectRelatedNotices", projectId, options);
  }

  function resolveOpenTrackerRelatedProjectId() {
    return callProjectRelatedController("resolveOpenTrackerRelatedProjectId");
  }

  function isProjectRelatedVisible(projectId) {
    return callProjectRelatedController("isProjectRelatedVisible", projectId);
  }

  function renderProjectRelatedHosts() {
    return callProjectRelatedController("renderProjectRelatedHosts");
  }

  function clearProjectRelatedRefresh(projectId = "") {
    return callProjectRelatedController("clearProjectRelatedRefresh", projectId);
  }

  function maybeScheduleProjectRelatedRefresh(projectId) {
    return callProjectRelatedController("maybeScheduleProjectRelatedRefresh", projectId);
  }

  function canReuseProjectRelatedPayload(payload) {
    return callProjectRelatedController("canReuseProjectRelatedPayload", payload);
  }

  function cacheProjectRelatedPayload(projectId, payload) {
    return callProjectRelatedController("cacheProjectRelatedPayload", projectId, payload);
  }

  async function ensureTrackerEntryProjectId(entryId) {
    return callProjectRelatedController("ensureTrackerEntryProjectId", entryId);
  }

  function resolveTrackerEntryProjectId(entryId) {
    return callProjectRelatedController("resolveTrackerEntryProjectId", entryId);
  }

  return {
    openTrackerEntryNoticeViewer,
    renderRelatedProjectNotices,
    renderTrackerEntryRelatedNotices,
    renderRelatedNoticePanel,
    bindRelatedNoticeViewerButtons,
    openRelatedNoticeViewer,
    openProjectNoticeViewer,
    buildProjectNoticeUrl,
    extractTrackerEntryBidParts,
    buildTrackerEntryNoticeUrl,
    prefetchProjectRelatedNotices,
    prefetchVisibleProjectRelatedNotices,
    toggleProjectRelated,
    toggleTrackerEntryRelated,
    loadProjectRelatedNotices,
    resolveOpenTrackerRelatedProjectId,
    isProjectRelatedVisible,
    renderProjectRelatedHosts,
    clearProjectRelatedRefresh,
    maybeScheduleProjectRelatedRefresh,
    canReuseProjectRelatedPayload,
    cacheProjectRelatedPayload,
    ensureTrackerEntryProjectId,
    resolveTrackerEntryProjectId,
  };
}

const appProjectRelatedBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appProjectRelatedBridgeRoot.APP_PROJECT_RELATED_BRIDGE = appProjectRelatedBridgeRoot.APP_PROJECT_RELATED_BRIDGE || {};
appProjectRelatedBridgeRoot.APP_PROJECT_RELATED_BRIDGE.createAppProjectRelatedBridge = createAppProjectRelatedBridge;
