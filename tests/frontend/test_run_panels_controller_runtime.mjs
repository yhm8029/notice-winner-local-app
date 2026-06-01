import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function extractFunction(source, startSignature, nextSignature) {
  const start = source.indexOf(startSignature);
  assert.notEqual(start, -1, `missing ${startSignature}`);
  const end = nextSignature ? source.indexOf(nextSignature, start + startSignature.length) : -1;
  assert.notEqual(end, -1, `missing ${nextSignature}`);
  return source.slice(start, end);
}

function makeNode(overrides = {}) {
  return {
    innerHTML: "",
    textContent: "",
    dataset: {},
    disabled: false,
    value: "",
    style: {},
    classList: {
      add() {},
      remove() {},
      toggle() {},
    },
    querySelector() {
      return null;
    },
    querySelectorAll() {
      return [];
    },
    addEventListener() {},
    ...overrides,
  };
}

function createHarness({ controllerFactory = null } = {}) {
  const source = readAppSource();
  const helperSource = [
    extractFunction(
      source,
      "function createControllerWithWiringDeps({",
      "function getAdminGoogleSheetsController() {",
    ),
    extractFunction(
      source,
      "function getRunPanelsController() {",
      "function getReportPanelsController() {",
    ),
    extractFunction(
      source,
      "function callRunPanelsControllerMethod(methodName, fallback, ...args) {",
      "function mergeOrganizationInvitationItem(",
    ),
  ].join("\n");
  const sanitizedSource = source.replace(
    /\n\s*renderRunEventStatus\(".*?\);\r?\n\s*window\.clearTimeout/,
    '\n    renderRunEventStatus("run-event-waiting");\n    window.clearTimeout',
  );
  const runSliceSource = [
    extractFunction(sanitizedSource, "function handleRunFormReset() {", "function buildRunPayload("),
    extractFunction(sanitizedSource, "async function createWinnerRun({ collectModeOverride = \"\", submitButton = null, busyLabel = \"\" } = {}) {", "function hydrateStateFromUrl() {"),
    extractFunction(sanitizedSource, "function renderRuns() {", "function renderRunsPagination() {"),
    extractFunction(sanitizedSource, "function renderRunsPagination() {", "function changeRunsPage(delta) {"),
    extractFunction(sanitizedSource, "function changeRunsPage(delta) {", "async function selectRun(runId) {"),
    extractFunction(sanitizedSource, "async function selectRun(runId) {", "async function refreshSelectedRun({ silent = false } = {}) {"),
    extractFunction(sanitizedSource, "function renderRunDetail(run) {", "function renderRunExecutionContext(run) {"),
    extractFunction(sanitizedSource, "function syncRunActionButtons(run) {", "function schedulePolling(run) {"),
    extractFunction(sanitizedSource, "function schedulePolling(run) {", "async function loadSelectedRunLogs({ silent = false, runId = state.selectedRunId } = {}) {"),
    extractFunction(sanitizedSource, "async function loadSelectedRunLogs({ silent = false, runId = state.selectedRunId } = {}) {", "function renderLogsList(items) {"),
    extractFunction(sanitizedSource, "async function loadRunPresets({ silent = false } = {}) {", "function renderRunPresetPanel(errorMessage = \"\") {"),
    extractFunction(sanitizedSource, "function renderLogsList(items) {", "function renderRunEventStatus(message, tone = \"\") {"),
    extractFunction(sanitizedSource, "function renderRunEventStatus(message, tone = \"\") {", "function disconnectRunEventStream() {"),
    extractFunction(sanitizedSource, "function renderRunPresetPanel(errorMessage = \"\") {", "function applyPresetParams(params) {"),
    extractFunction(sanitizedSource, "function syncCollectModeOptions() {", "function renderArtifactPreviewMarkup(artifactId) {"),
  ].join("\n");

  const calls = [];
  const controllerMethods = new Map();
  const controller = {};
  const collectModeSelect = makeNode({
    value: "synthetic",
    querySelector(optionSelector) {
      if (optionSelector === 'option[value="gui_seed"]') {
        return null;
      }
      if (optionSelector === 'option[value="synthetic"]') {
        return makeNode({
          remove() {
            calls.push(["synthetic-option.remove"]);
          },
        });
      }
      return null;
    },
  });
  const methodNames = [
    "handleRunFormReset",
    "createWinnerRun",
    "renderRuns",
    "renderRunsPagination",
    "changeRunsPage",
    "selectRun",
    "renderRunDetail",
    "syncRunActionButtons",
    "schedulePolling",
    "loadSelectedRunLogs",
    "renderLogsList",
    "renderRunEventStatus",
    "loadRunPresets",
    "renderRunPresetPanel",
    "syncCollectModeOptions",
  ];
  for (const methodName of methodNames) {
    controller[methodName] = (...args) => {
      let normalizedArgs = args;
      if (methodName === "createWinnerRun") {
        normalizedArgs = [{
          collectModeOverride: args[0]?.collectModeOverride || "",
          busyLabel: args[0]?.busyLabel || "",
          hasSubmitButton: Boolean(args[0]?.submitButton),
        }];
      } else if (methodName === "renderRunDetail" || methodName === "syncRunActionButtons") {
        normalizedArgs = [args[0]?.id || null];
      } else if (methodName === "loadRunPresets") {
        normalizedArgs = [args[0] || {}];
      }
      calls.push([methodName, ...normalizedArgs]);
      return methodName === "createWinnerRun" || methodName === "selectRun" || methodName === "loadSelectedRunLogs" || methodName === "loadRunPresets"
        ? Promise.resolve(`${methodName}-result`)
        : `${methodName}-result`;
    };
    controllerMethods.set(methodName, controller[methodName]);
  }

  const runControllerFactory = controllerFactory || ((deps) => {
    calls.push(["factory", Boolean(deps.trackerController?.disconnectRunEventStream)]);
    controller.selectRun = (runId) => {
      calls.push(["selectRun", runId]);
      deps.trackerController?.disconnectRunEventStream?.();
      return Promise.resolve("selectRun-result");
    };
    return controller;
  });

  const window = {
    SPMSAppControllerWiringRuntime: {
      createRunPanelsControllerDeps(deps) {
        return deps;
      },
    },
    RUN_PANELS_CONTROLLER: {
      createRunPanelsController: runControllerFactory,
    },
    clearTimeout() {},
    setTimeout() {
      return 1;
    },
    localStorage: null,
    prompt() {
      return "preset";
    },
  };

  const dom = {
    runForm: makeNode({
      reset() {
        calls.push(["runForm.reset"]);
      },
      querySelector(selector) {
        if (selector === '[name="collect_mode"]') {
          return collectModeSelect;
        }
        return makeNode({
          value: "",
        });
      },
    }),
    submitRunButton: makeNode({ textContent: "submit" }),
    runsList: makeNode({
      querySelectorAll() {
        return [
          makeNode({
            getAttribute(name) {
              return name === "data-run-id" ? "run-1" : "";
            },
          }),
        ];
      },
    }),
    runsPageMeta: makeNode(),
    runsPrevButton: makeNode(),
    runsNextButton: makeNode(),
    logsList: makeNode(),
    runEventStatus: makeNode(),
    presetSelect: makeNode(),
    presetStatus: makeNode(),
    runEmptyState: makeNode(),
    runDetail: makeNode(),
    runId: makeNode(),
    runStatusBadge: makeNode(),
    runProgress: makeNode(),
    runType: makeNode(),
    runProgressStage: makeNode(),
    runProgressMeta: makeNode(),
    runProgressBar: makeNode({ style: {} }),
    runParams: makeNode(),
    runSummary: makeNode(),
    runError: makeNode(),
    runCreatedAt: makeNode(),
    runStartedAt: makeNode(),
    runFinishedAt: makeNode(),
    runParentId: makeNode(),
    cancelRunButton: makeNode(),
    trackerExportButton: makeNode(),
    refreshRunButton: makeNode(),
    refreshLogsButton: makeNode(),
    refreshArtifactsButton: makeNode(),
    refreshEntriesButton: makeNode(),
    artifactsList: makeNode(),
    runExecutionContext: makeNode(),
  };

  const state = {
    runs: [{ id: "run-1", run_type: "project_tracker", status: "success", created_at: "2026-04-21T00:00:00Z" }],
    runsTotal: 1,
    runFilters: { page: 1, pageSize: 20 },
    selectedRunId: null,
    selectedTrackerRunId: null,
    selectedTrackerRun: null,
    selectedTrackerWorkbookArtifactId: null,
    selectedEntryId: null,
    selectedEntry: null,
    drawerOpen: false,
    openArtifactId: null,
    runLogs: [],
    runLogIds: new Set(),
    pollHandle: null,
    artifactRetryHandle: null,
    autoRefresh: true,
    runPresets: [{ id: "preset-1", name: "Preset 1", params: { collect_mode: "auto" } }],
    selectedPresetId: "preset-1",
    dashboard: { synthetic_debug_enabled: false },
  };

  const stubs = {
    api: async (path) => {
      calls.push(["api", path]);
      return { items: [{ id: 1, level: "info", stage: "build", message: "ok", created_at: "2026-04-21T00:00:00Z" }] };
    },
    flash: (message, tone) => calls.push(["flash", message, tone]),
    touchSyncMeta: (label) => calls.push(["touchSyncMeta", label]),
    setBusy: (button, busy, label) => calls.push(["setBusy", Boolean(busy), label]),
    loadRuns: (options) => calls.push(["loadRuns", options]),
    refreshSelectedRun: async (options) => calls.push(["refreshSelectedRun", options]),
    resetTrackerBoardEdit: () => calls.push(["resetTrackerBoardEdit"]),
    syncUrlState: () => calls.push(["syncUrlState"]),
    escapeHtml: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => `<span>${String(value ?? "")}</span>`,
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    progressPercent: () => 0,
    renderRunExecutionContext: (run) => calls.push(["renderRunExecutionContext", run]),
    isProjectTrackerRun: (value) => value === "project_tracker",
    useGlobalTrackerEntriesScope: () => false,
    renderArtifactsList: () => calls.push(["renderArtifactsList"]),
    buildArtifactEmptyMessage: () => "empty",
    loadTrackerEntries: async (options) => calls.push(["loadTrackerEntries", options]),
    document: {
      createElement: (tag) => makeNode({ tagName: tag.toUpperCase() }),
    },
    FormData: class {
      constructor(form) {
        this.form = form;
      }
      entries() {
        return [];
      }
    },
    runPanelsController: null,
    syntheticDebugEnabled: () => false,
    disconnectRunEventStream: () => calls.push(["disconnectRunEventStream"]),
    selectRun: async () => calls.push(["selectRun-fallback"]),
    renderRuns: () => calls.push(["renderRuns-fallback"]),
    renderLogsList: () => calls.push(["renderLogsList-fallback"]),
    renderRunEventStatus: () => calls.push(["renderRunEventStatus-fallback"]),
  };

  const context = vm.createContext({
    window,
    dom,
    state,
    APP_SUPPORT: {
      createRunPanelsControllerDepsHelpers(deps) {
        return {
          buildRunPanelsControllerDeps() {
            return deps;
          },
        };
      },
      callRunPanelsControllerFallback({ controller = null, methodName = "", fallback = null, args = [] } = {}) {
        const method = controller?.[methodName];
        if (typeof method === "function") {
          return method.apply(controller, args);
        }
        if (typeof fallback === "function") {
          return fallback(...args);
        }
        return undefined;
      },
    },
    ...stubs,
    console,
    RUN_VIEW_RUNTIME: null,
    RUN_PANELS_FALLBACK_RUNTIME: null,
    runPanelsController: null,
    trackerController: null,
  });

  vm.runInContext(`${helperSource}\n${runSliceSource}`, context, { filename: appPath });

  return { context, calls, controllerMethods };
}

test("app.js delegates bounded run-panels methods to the controller runtime", async () => {
  const harness = createHarness();
  const { context, calls } = harness;

  await context.handleRunFormReset();
  assert.equal(await context.createWinnerRun({
    collectModeOverride: "synthetic",
    submitButton: context.dom.submitRunButton,
    busyLabel: "custom-busy",
  }), "createWinnerRun-result");
  context.renderRuns();
  context.renderRunsPagination();
  context.changeRunsPage(1);
  assert.equal(await context.selectRun("run-1"), "selectRun-result");
  context.renderRunDetail({ id: "run-1" });
  context.syncRunActionButtons({ id: "run-1", status: "success", run_type: "project_tracker" });
  context.schedulePolling(null);
  assert.equal(await context.loadSelectedRunLogs({ runId: "run-1" }), "loadSelectedRunLogs-result");
  context.renderLogsList([]);
  context.renderRunEventStatus("message", "warn");
  assert.equal(await context.loadRunPresets({ silent: true }), "loadRunPresets-result");
  context.renderRunPresetPanel("error");
  context.syncCollectModeOptions();

  const invoked = calls.filter(([name]) => name !== "factory");
  assert.deepEqual(
    invoked.map(([name]) => name),
    [
      "handleRunFormReset",
      "createWinnerRun",
      "renderRuns",
      "renderRunsPagination",
      "changeRunsPage",
      "selectRun",
      "disconnectRunEventStream",
      "renderRunDetail",
      "syncRunActionButtons",
      "schedulePolling",
      "loadSelectedRunLogs",
      "renderLogsList",
      "renderRunEventStatus",
      "loadRunPresets",
      "renderRunPresetPanel",
      "syncCollectModeOptions",
    ],
  );
  assert.equal(calls[0][0], "factory");
  assert.equal(calls[0][1], true);
  assert.deepEqual(calls[2], [
    "createWinnerRun",
    {
      collectModeOverride: "synthetic",
      busyLabel: "custom-busy",
      hasSubmitButton: true,
    },
  ]);
});

test("app.js falls back safely when the run-panels controller is absent", async () => {
  const harness = createHarness({
    controllerFactory: () => null,
  });
  const { context, calls } = harness;
  context.window.RUN_PANELS_CONTROLLER = {};
  context.runPanelsController = null;
  context.state.selectedRunId = "run-1";

  assert.doesNotThrow(() => context.renderRuns());
  assert.doesNotThrow(() => context.renderRunsPagination());
  assert.doesNotThrow(() => context.changeRunsPage(1));
  await assert.doesNotReject(context.selectRun("run-1"));
  assert.doesNotThrow(() => context.schedulePolling(null));
  await assert.doesNotReject(context.loadSelectedRunLogs({ runId: "run-1" }));
  assert.doesNotThrow(() => context.renderLogsList([]));
  assert.doesNotThrow(() => context.renderRunEventStatus("message", "warn"));
  await assert.doesNotReject(context.loadRunPresets({ silent: true }));
  assert.doesNotThrow(() => context.renderRunPresetPanel("error"));
  assert.doesNotThrow(() => context.syncCollectModeOptions());

  assert.equal(context.dom.runsList.innerHTML, "");
  assert.equal(context.dom.runEventStatus.textContent, "");
  assert.equal(context.dom.presetStatus.textContent, "");
  assert.equal(context.dom.runForm.querySelector('[name="collect_mode"]').value, "synthetic");
  assert.equal(calls.some(([name]) => name === "refreshSelectedRun"), false);
  assert.equal(calls.some(([name]) => name === "api"), false);
  assert.equal(context.state.runLogs.length, 0);
});

test("run panel wrappers stay thin and do not keep inline fallback rendering", () => {
  const source = readAppSource();
  const renderRunsSource = extractFunction(
    source,
    "function renderRuns() {",
    "function renderRunsPagination() {",
  );
  const renderRunDetailSource = extractFunction(
    source,
    "function renderRunDetail(run) {",
    "function renderRunExecutionContext(run) {",
  );
  const renderLogsListSource = extractFunction(
    source,
    "function renderLogsList(items) {",
    "function renderRunEventStatus(message, tone = \"\") {",
  );
  const renderRunEventStatusSource = extractFunction(
    source,
    "function renderRunEventStatus(message, tone = \"\") {",
    "function disconnectRunEventStream() {",
  );
  const loadRunPresetsSource = extractFunction(
    source,
    "async function loadRunPresets({ silent = false } = {}) {",
    "function renderRunPresetPanel(errorMessage = \"\") {",
  );
  const renderRunPresetPanelSource = extractFunction(
    source,
    "function renderRunPresetPanel(errorMessage = \"\") {",
    "function applyPresetParams(params) {",
  );

  assert.match(renderRunsSource, /callRunPanelsControllerMethod\("renderRuns", null\)/);
  assert.match(renderRunDetailSource, /callRunPanelsControllerMethod\("renderRunDetail", null, run\)/);
  assert.match(renderLogsListSource, /controller\?\.renderLogsList/);
  assert.match(renderRunEventStatusSource, /controller\?\.renderRunEventStatus/);
  assert.match(loadRunPresetsSource, /callRunPanelsControllerMethod\("loadRunPresets", null, \{ silent \}\)/);
  assert.match(renderRunPresetPanelSource, /callRunPanelsControllerMethod\("renderRunPresetPanel", null, errorMessage\)/);

  assert.doesNotMatch(renderRunsSource, /runsList\.innerHTML/);
  assert.doesNotMatch(renderRunDetailSource, /runEmptyState\.classList/);
  assert.doesNotMatch(renderRunDetailSource, /runStatusBadge\.innerHTML/);
  assert.doesNotMatch(renderLogsListSource, /logsList\.innerHTML/);
  assert.doesNotMatch(renderRunEventStatusSource, /runEventStatus\.textContent/);
  assert.doesNotMatch(loadRunPresetsSource, /api\("\/api\/run-presets\?limit=12"\)/);
  assert.doesNotMatch(renderRunPresetPanelSource, /presetSelect\.innerHTML/);
});
