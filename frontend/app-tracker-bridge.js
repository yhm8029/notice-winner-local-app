export function createAppTrackerBridge(context = {}) {
  const {
    state = null,
    getTrackerController = () => null,
  } = context;

  function callTrackerController(methodName, ...args) {
    return getTrackerController()?.[methodName]?.(...args);
  }

  function getTrackerDiagnosticsScope(runSnapshot = state.selectedRun) {
    return callTrackerController("getTrackerDiagnosticsScope", runSnapshot);
  }

  function refreshTrackerOperationalDiagnostics({ silent = true } = {}) {
    return callTrackerController("refreshTrackerOperationalDiagnostics", { silent });
  }

  function readTrackerFiltersFromControls() {
    return callTrackerController("readTrackerFiltersFromControls");
  }

  function parseTrackerRegionFilter(region) {
    return callTrackerController("parseTrackerRegionFilter", region);
  }

  function normalizeTrackerRegionFilter(region) {
    return callTrackerController("normalizeTrackerRegionFilter", region);
  }

  function renderTrackerRegionButtons() {
    return callTrackerController("renderTrackerRegionButtons");
  }

  async function loadRuns({ initial = false, silent = false, preservePage = false } = {}) {
    return callTrackerController("loadRuns", { initial, silent, preservePage });
  }

  async function refreshSelectedRun({ silent = false } = {}) {
    return callTrackerController("refreshSelectedRun", { silent });
  }

  function renderTrackerTemplateStatus(errorMessage = "") {
    return callTrackerController("renderTrackerTemplateStatus", errorMessage);
  }

  async function loadTrackerTemplateStatus({ silent = false } = {}) {
    return callTrackerController("loadTrackerTemplateStatus", { silent });
  }

  async function uploadTrackerTemplate(file) {
    return callTrackerController("uploadTrackerTemplate", file);
  }

  async function resetTrackerTemplateOverride() {
    return callTrackerController("resetTrackerTemplateOverride");
  }

  async function loadTrackerEntries({ silent = false, trackerRunId, forceRefresh = false } = {}) {
    return callTrackerController("loadTrackerEntries", { silent, trackerRunId, forceRefresh });
  }

  async function loadTrackerContactResolutionSummary({ silent = false } = {}) {
    return callTrackerController("loadTrackerContactResolutionSummary", { silent });
  }

  function loadTrackerCleanupPreview(options = {}) {
    return callTrackerController("loadTrackerCleanupPreview", options);
  }

  function applyTrackerCleanupForScope() {
    return callTrackerController("applyTrackerCleanupForScope");
  }

  function prefetchTrackerEntryDetails(entries) {
    return callTrackerController("prefetchTrackerEntryDetails", entries) || null;
  }

  async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) {
    return callTrackerController("fetchTrackerEntryDetail", entryId, { silent }) || null;
  }

  function loadBackfillConflicts(options = {}) {
    return callTrackerController("loadBackfillConflicts", options);
  }

  return {
    getTrackerDiagnosticsScope,
    refreshTrackerOperationalDiagnostics,
    readTrackerFiltersFromControls,
    parseTrackerRegionFilter,
    normalizeTrackerRegionFilter,
    renderTrackerRegionButtons,
    loadRuns,
    refreshSelectedRun,
    renderTrackerTemplateStatus,
    loadTrackerTemplateStatus,
    uploadTrackerTemplate,
    resetTrackerTemplateOverride,
    loadTrackerEntries,
    loadTrackerContactResolutionSummary,
    loadTrackerCleanupPreview,
    applyTrackerCleanupForScope,
    prefetchTrackerEntryDetails,
    fetchTrackerEntryDetail,
    loadBackfillConflicts,
  };
}

const appTrackerBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appTrackerBridgeRoot.APP_TRACKER_BRIDGE = appTrackerBridgeRoot.APP_TRACKER_BRIDGE || {};
appTrackerBridgeRoot.APP_TRACKER_BRIDGE.createAppTrackerBridge = createAppTrackerBridge;
