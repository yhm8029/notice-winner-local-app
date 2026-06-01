export function createAppRunReportBridge(context = {}) {
  const {
    state = null,
    callRunPanelsController = null,
    callReportPanelsController = null,
  } = context;

  function handleRunFormReset() {
    return callRunPanelsController("handleRunFormReset");
  }

  function buildRunPayload({ collectModeOverride = "" } = {}) {
    return callRunPanelsController("buildRunPayload", { collectModeOverride });
  }

  async function createWinnerRun({ collectModeOverride = "", submitButton = null, busyLabel = "" } = {}) {
    return callRunPanelsController("createWinnerRun", { collectModeOverride, submitButton, busyLabel });
  }

  function normalizeCollectMode(value) {
    return callRunPanelsController("normalizeCollectMode", value);
  }

  function syncCollectModeOptions() {
    return callRunPanelsController("syncCollectModeOptions");
  }

  function renderRuns() {
    return callRunPanelsController("renderRuns");
  }

  function renderRunsPagination() {
    return callRunPanelsController("renderRunsPagination");
  }

  function changeRunsPage(delta) {
    return callRunPanelsController("changeRunsPage", delta);
  }

  async function selectRun(runId) {
    return callRunPanelsController("selectRun", runId);
  }

  function renderRunDetail(run) {
    return callRunPanelsController("renderRunDetail", run);
  }

  function resolveTrackerExecutionContext(run) {
    return callRunPanelsController("resolveTrackerExecutionContext", run);
  }

  function normalizeTrackerExecutionContext(payload = {}) {
    return callRunPanelsController("normalizeTrackerExecutionContext", payload);
  }

  function numericSummaryValue(...values) {
    return callRunPanelsController("numericSummaryValue", ...values);
  }

  function trackerExportStageLabel(stage) {
    return callRunPanelsController("trackerExportStageLabel", stage);
  }

  function trackerExecutionTone(status) {
    return callRunPanelsController("trackerExecutionTone", status);
  }

  function trackerExecutionMessage(contextValue) {
    return callRunPanelsController("trackerExecutionMessage", contextValue);
  }

  function schedulePolling(run) {
    return callRunPanelsController("schedulePolling", run);
  }

  async function loadSelectedRunLogs({ silent = false, runId = state.selectedRunId } = {}) {
    return callRunPanelsController("loadSelectedRunLogs", { silent, runId });
  }

  function renderLogsList(items) {
    return callRunPanelsController("renderLogsList", items);
  }

  function renderRunEventStatus(message, tone = "") {
    return callRunPanelsController("renderRunEventStatus", message, tone);
  }

  function upsertRunListItem(run) {
    return callRunPanelsController("upsertRunListItem", run);
  }

  async function loadRunPresets({ silent = false } = {}) {
    return callRunPanelsController("loadRunPresets", { silent });
  }

  function renderRunPresetPanel(errorMessage = "") {
    return callRunPanelsController("renderRunPresetPanel", errorMessage);
  }

  function applyPresetParams(params) {
    return callRunPanelsController("applyPresetParams", params);
  }

  async function applySelectedPreset() {
    return callRunPanelsController("applySelectedPreset");
  }

  async function saveCurrentFormAsPreset() {
    return callRunPanelsController("saveCurrentFormAsPreset");
  }

  function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) {
    return callRunPanelsController("loadSelectedRunArtifacts", { silent, runId, runSnapshot });
  }

  async function loadWinnerRunPanels(run) {
    return callRunPanelsController("loadWinnerRunPanels", run);
  }

  async function loadTrackerExportPanels(run) {
    return callRunPanelsController("loadTrackerExportPanels", run);
  }

  function scheduleArtifactRetry(runId) {
    return callRunPanelsController("scheduleArtifactRetry", runId);
  }

  function resolveTrackerContextRun(runSnapshot = state.selectedRun) {
    return callRunPanelsController("resolveTrackerContextRun", runSnapshot);
  }

  async function cancelSelectedRun() {
    return callRunPanelsController("cancelSelectedRun");
  }

  async function createTrackerExportForSelectedRun() {
    return callRunPanelsController("createTrackerExportForSelectedRun");
  }

  function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = "공고문") {
    return callReportPanelsController("renderNoticeViewerPayload", viewerWindow, payload, fallbackTitle);
  }

  function renderNoticeViewerError(viewerWindow, { title = "공고문", errorMessage = "", links = [] } = {}) {
    return callReportPanelsController("renderNoticeViewerError", viewerWindow, { title, errorMessage, links });
  }

  function renderNoticeViewerWindow(targetWindow, { title = "공고문", meta = "", body = "" } = {}) {
    return callReportPanelsController("renderNoticeViewerWindow", targetWindow, { title, meta, body });
  }

  async function loadPhaseReport({ silent = false } = {}) {
    return callReportPanelsController("loadPhaseReport", { silent });
  }

  async function loadReportJobs({ silent = false } = {}) {
    return callReportPanelsController("loadReportJobs", { silent });
  }

  async function runSelectedReport() {
    return callReportPanelsController("runSelectedReport");
  }

  async function refreshReportPanels() {
    return callReportPanelsController("refreshReportPanels");
  }

  function renderReport(report, errorMessage = "") {
    return callReportPanelsController("renderReport", report, errorMessage);
  }

  function renderReportJobs(items) {
    return callReportPanelsController("renderReportJobs", items);
  }

  function renderReportJob(job, errorMessage = "") {
    return callReportPanelsController("renderReportJob", job, errorMessage);
  }

  function renderArtifactsList() {
    return callReportPanelsController("renderArtifactsList");
  }

  function buildArtifactEmptyMessage() {
    return callReportPanelsController("buildArtifactEmptyMessage");
  }

  function renderArtifactPreviewMarkup(artifactId) {
    return callReportPanelsController("renderArtifactPreviewMarkup", artifactId);
  }

  return {
    handleRunFormReset,
    buildRunPayload,
    createWinnerRun,
    normalizeCollectMode,
    syncCollectModeOptions,
    renderRuns,
    renderRunsPagination,
    changeRunsPage,
    selectRun,
    renderRunDetail,
    resolveTrackerExecutionContext,
    normalizeTrackerExecutionContext,
    numericSummaryValue,
    trackerExportStageLabel,
    trackerExecutionTone,
    trackerExecutionMessage,
    schedulePolling,
    loadSelectedRunLogs,
    renderLogsList,
    renderRunEventStatus,
    upsertRunListItem,
    loadRunPresets,
    renderRunPresetPanel,
    applyPresetParams,
    applySelectedPreset,
    saveCurrentFormAsPreset,
    loadSelectedRunArtifacts,
    loadWinnerRunPanels,
    loadTrackerExportPanels,
    scheduleArtifactRetry,
    resolveTrackerContextRun,
    cancelSelectedRun,
    createTrackerExportForSelectedRun,
    renderNoticeViewerPayload,
    renderNoticeViewerError,
    renderNoticeViewerWindow,
    loadPhaseReport,
    loadReportJobs,
    runSelectedReport,
    refreshReportPanels,
    renderReport,
    renderReportJobs,
    renderReportJob,
    renderArtifactsList,
    buildArtifactEmptyMessage,
    renderArtifactPreviewMarkup,
  };
}

const appRunReportBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appRunReportBridgeRoot.APP_RUN_REPORT_BRIDGE = appRunReportBridgeRoot.APP_RUN_REPORT_BRIDGE || {};
appRunReportBridgeRoot.APP_RUN_REPORT_BRIDGE.createAppRunReportBridge = createAppRunReportBridge;
