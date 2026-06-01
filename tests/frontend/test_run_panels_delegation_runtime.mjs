import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");
const wiringRuntimePath = path.resolve(__dirname, "../../frontend/app-controller-wiring-runtime.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

function readWiringRuntimeSource() {
  return fs.readFileSync(wiringRuntimePath, "utf8");
}

function extractFunction(source, startSignature, nextSignature) {
  const start = source.indexOf(startSignature);
  assert.notEqual(start, -1, `missing ${startSignature}`);
  const end = nextSignature ? source.indexOf(nextSignature, start + startSignature.length) : -1;
  assert.notEqual(end, -1, `missing ${nextSignature}`);
  return source.slice(start, end);
}

function extractRunWrapperBundle() {
  const source = readAppSource();
  return {
    createControllerWithWiringDepsSource: extractFunction(
      source,
      "function createControllerWithWiringDeps({",
      "function getAdminGoogleSheetsController() {",
    ),
    getRunPanelsControllerSource: extractFunction(
      source,
      "function getRunPanelsController() {",
      "function getReportPanelsController() {",
    ),
    callRunPanelsControllerMethodSource: extractFunction(
      source,
      "function callRunPanelsControllerMethod(methodName, fallback, ...args) {",
      "function mergeOrganizationInvitationItem(existingItem, nextItem) {",
    ),
    handleRunFormResetSource: extractFunction(
      source,
      "function handleRunFormReset() {",
      "function buildRunPayload({ collectModeOverride = \"\" } = {}) {",
    ),
    buildRunPayloadSource: extractFunction(
      source,
      "function buildRunPayload({ collectModeOverride = \"\" } = {}) {",
      "async function createWinnerRun({ collectModeOverride = \"\", submitButton = null, busyLabel = \"\" } = {}) {",
    ),
    createWinnerRunSource: extractFunction(
      source,
      "async function createWinnerRun({ collectModeOverride = \"\", submitButton = null, busyLabel = \"\" } = {}) {",
      "function hydrateStateFromUrl() {",
    ),
    changeRunsPageSource: extractFunction(
      source,
      "function changeRunsPage(delta) {",
      "async function selectRun(runId) {",
    ),
    renderRunDetailSource: extractFunction(
      source,
      "function renderRunDetail(run) {",
      "function renderRunExecutionContext(run) {",
    ),
    resolveTrackerExecutionContextSource: extractFunction(
      source,
      "function resolveTrackerExecutionContext(run) {",
      "function normalizeTrackerExecutionContext(payload = {}) {",
    ),
    normalizeTrackerExecutionContextSource: extractFunction(
      source,
      "function normalizeTrackerExecutionContext(payload = {}) {",
      "function numericSummaryValue(...values) {",
    ),
    numericSummaryValueSource: extractFunction(
      source,
      "function numericSummaryValue(...values) {",
      "function trackerExportStageLabel(stage) {",
    ),
    trackerExportStageLabelSource: extractFunction(
      source,
      "function trackerExportStageLabel(stage) {",
      "function trackerExecutionTone(status) {",
    ),
    trackerExecutionToneSource: extractFunction(
      source,
      "function trackerExecutionTone(status) {",
      "function trackerExecutionMessage(context) {",
    ),
    trackerExecutionMessageSource: extractFunction(
      source,
      "function trackerExecutionMessage(context) {",
      "function syncRunActionButtons(run) {",
    ),
    syncRunActionButtonsSource: extractFunction(
      source,
      "function syncRunActionButtons(run) {",
      "function schedulePolling(run) {",
    ),
    loadSelectedRunLogsSource: extractFunction(
      source,
      "async function loadSelectedRunLogs({ silent = false, runId = state.selectedRunId } = {}) {",
      "function renderLogsList(items) {",
    ),
    renderRunEventStatusSource: extractFunction(
      source,
      "function renderRunEventStatus(message, tone = \"\") {",
      "function disconnectRunEventStream() {",
    ),
  };
}

function createClassList() {
  return {
    values: new Set(),
    add(value) {
      this.values.add(value);
    },
    remove(value) {
      this.values.delete(value);
    },
    contains(value) {
      return this.values.has(value);
    },
  };
}

function createBaseContext(overrides = {}) {
  const overrideWindow = overrides.window || {};
  const { window: _ignoredWindow, ...restOverrides } = overrides;
  return vm.createContext({
    console,
    window: {
      SPMSAppControllerWiringRuntime: {
        createRunPanelsControllerDeps(deps) {
          return deps;
        },
      },
      clearTimeout: () => {},
      ...overrideWindow,
    },
    document: {},
    state: {
      selectedRunId: "run-current",
      selectedTrackerRun: null,
      pollHandle: 0,
      selectedTrackerRunId: null,
      runsTotal: 45,
      runFilters: {
        page: 2,
        pageSize: 10,
      },
      runLogs: [{ id: 1 }],
      runLogIds: new Set([1]),
    },
    dom: {
      runForm: {
        reset() {},
        querySelector() {
          return null;
        },
      },
      submitRunButton: {
        textContent: "실행 시작",
      },
      runEventStatus: {
        textContent: "",
        dataset: {},
      },
      runEmptyState: {
        classList: createClassList(),
      },
      runDetail: {
        classList: createClassList(),
      },
      logsList: {
        innerHTML: "",
      },
      artifactsList: {
        innerHTML: "",
      },
      runId: {
        textContent: "",
      },
      runStatusBadge: {
        innerHTML: "",
      },
      runProgress: {
        textContent: "",
      },
      runType: {
        textContent: "",
      },
      runProgressStage: {
        textContent: "",
      },
      runProgressMeta: {
        textContent: "",
      },
      runProgressBar: {
        style: {},
      },
      runParams: {
        textContent: "",
      },
      runSummary: {
        textContent: "",
      },
      runError: {
        textContent: "",
      },
      runCreatedAt: {
        textContent: "",
      },
      runStartedAt: {
        textContent: "",
      },
      runFinishedAt: {
        textContent: "",
      },
      runParentId: {
        textContent: "",
      },
      cancelRunButton: {
        disabled: false,
      },
      trackerExportButton: {
        disabled: false,
      },
      refreshRunButton: {
        disabled: false,
      },
      refreshLogsButton: {
        disabled: false,
      },
      refreshArtifactsButton: {
        disabled: false,
      },
      refreshEntriesButton: {
        disabled: false,
      },
    },
    RUN_VIEW_RUNTIME: null,
    api: async () => ({ items: [] }),
    flash: () => {},
    touchSyncMeta: () => {},
    setBusy: () => {},
    loadRuns: async () => {},
    trackerController: null,
    resetTrackerBoardEdit: () => {},
    syncUrlState: () => {},
    refreshSelectedRun: async () => {},
    disconnectRunEventStream: () => {},
    selectRun: async () => {},
    buildRunPayload: () => ({ run_type: "project_tracker", params: {} }),
    normalizeCollectMode: (value) => String(value || "").trim().toLowerCase() || "auto",
    FormData: class {
      constructor(form) {
        this.form = form;
      }
      get(name) {
        return this.form?.querySelector?.(`[name="${name}"]`)?.value ?? "";
      }
    },
    RUN_PANELS_FALLBACK_RUNTIME: null,
    escapeHtml: (value) => String(value ?? ""),
    runTypeLabel: (value) => String(value ?? ""),
    statusBadge: (value) => String(value ?? ""),
    formatDate: (value) => String(value ?? ""),
    formatJson: (value) => JSON.stringify(value),
    progressPercent: () => 0,
    renderRunExecutionContext: () => {},
    isProjectTrackerRun: () => false,
    useGlobalTrackerEntriesScope: () => false,
    renderArtifactsList: () => {},
    buildArtifactEmptyMessage: () => "",
    loadTrackerEntries: async () => {},
    renderLogsList: () => {},
    runPanelsController: null,
    APP_SUPPORT: {
      createRunPanelsControllerDepsHelpers(deps) {
        return {
          buildRunPanelsControllerDeps() {
            return deps;
          },
        };
      },
      callRunPanelsControllerFallback(payload = {}) {
        const {
          methodName,
          fallback,
          args = [],
          controller = null,
          state = {},
          dom = {},
          windowObject = {},
          RUN_PANELS_FALLBACK_RUNTIME = null,
          flash = () => {},
          setBusy = () => {},
          api = async () => ({}),
          FormData: FormDataCtor = FormData,
          isProjectTrackerRun = () => false,
          dispatch = () => undefined,
        } = payload;
        const method = controller?.[methodName];
        if (typeof method === "function") {
          return method.apply(controller, args);
        }
        if (typeof fallback === "function") {
          return fallback(...args);
        }
        switch (methodName) {
          case "syncRunActionButtons": {
            const [run] = args;
            const isRunning = run && (run.status === "queued" || run.status === "running");
            const trackerRunning = state.selectedTrackerRun && ["queued", "running"].includes(state.selectedTrackerRun.status);
            const canCancel = run && !["success", "failed", "cancelled"].includes(run.status);
            const canTrackerExport = run && isProjectTrackerRun(run.run_type) && run.status === "success";
            dom.cancelRunButton.disabled = !canCancel;
            dom.trackerExportButton.disabled = !canTrackerExport;
            dom.refreshRunButton.disabled = !run;
            dom.refreshLogsButton.disabled = !run;
            dom.refreshArtifactsButton.disabled = !run;
            if (!isRunning && !trackerRunning) {
              windowObject.clearTimeout(state.pollHandle);
              state.pollHandle = null;
            }
            return undefined;
          }
          case "resolveTrackerExecutionContext": {
            const [run] = args;
            return RUN_PANELS_FALLBACK_RUNTIME?.resolveTrackerExecutionContextFallback?.(run, {
              isProjectTrackerRun,
            }) || null;
          }
          case "normalizeTrackerExecutionContext": {
            const [context = {}] = args;
            return RUN_PANELS_FALLBACK_RUNTIME?.normalizeTrackerExecutionContextFallback?.(context) || null;
          }
          case "numericSummaryValue":
            return RUN_PANELS_FALLBACK_RUNTIME?.numericSummaryValueFallback?.(args) ?? 0;
          case "trackerExportStageLabel": {
            const [stage] = args;
            return RUN_PANELS_FALLBACK_RUNTIME?.trackerExportStageLabelFallback?.(stage) || String(stage || "waiting");
          }
          case "trackerExecutionTone": {
            const [status] = args;
            return RUN_PANELS_FALLBACK_RUNTIME?.trackerExecutionToneFallback?.(status) || "";
          }
          case "trackerExecutionMessage": {
            const [context = null] = args;
            return RUN_PANELS_FALLBACK_RUNTIME?.trackerExecutionMessageFallback?.(context) || "";
          }
          case "applyPresetParams": {
            const [params] = args;
            for (const [name, rawValue] of Object.entries(params || {})) {
              const input = dom.runForm?.querySelector?.(`[name="${name}"]`);
              if (!input) {
                continue;
              }
              input.value = rawValue == null ? "" : String(rawValue);
            }
            return undefined;
          }
          case "applySelectedPreset": {
            const presetId = dom.presetSelect?.value || state.selectedPresetId;
            if (!presetId) {
              flash("적용할 프리셋을 선택하세요.", "error");
              return undefined;
            }
            const preset = state.runPresets.find((item) => item.id === presetId);
            if (!preset) {
              flash("선택한 프리셋을 찾지 못했습니다.", "error");
              return undefined;
            }
            state.selectedPresetId = preset.id;
            dispatch("applyPresetParams", null, preset.params || {});
            dispatch("renderRunPresetPanel", null);
            flash(`프리셋 적용: ${preset.name}`);
            return undefined;
          }
          case "saveCurrentFormAsPreset": {
            const defaultName = `${new Date().toISOString().slice(0, 10)} 검색 조건`;
            const name = windowObject.prompt("프리셋 이름", defaultName);
            if (!name || !name.trim()) {
              return undefined;
            }
            const formData = new FormDataCtor(dom.runForm);
            const params = {};
            for (const [key, value] of formData.entries()) {
              params[key] = String(value ?? "");
            }
            setBusy(dom.presetSaveButton, true, "저장 중...");
            return api("/api/run-presets", {
              method: "POST",
              body: JSON.stringify({ name: name.trim(), params }),
            })
              .then(async (response) => {
                state.selectedPresetId = response.id;
                flash(`프리셋 저장: ${response.name}`);
                await dispatch("loadRunPresets", null, { silent: true });
                return response;
              })
              .catch((err) => {
                flash(err.message, "error");
                return undefined;
              })
              .finally(() => {
                setBusy(dom.presetSaveButton, false, "현재 조건 저장");
              });
          }
          default:
            return undefined;
        }
      },
    },
    ...restOverrides,
  });
}

function loadRunWrapperBundle(context) {
  const bundle = extractRunWrapperBundle();
  vm.runInContext(
    [
      bundle.createControllerWithWiringDepsSource,
      bundle.getRunPanelsControllerSource,
      bundle.callRunPanelsControllerMethodSource,
      bundle.handleRunFormResetSource,
      bundle.buildRunPayloadSource,
      bundle.createWinnerRunSource,
      bundle.changeRunsPageSource,
      bundle.renderRunDetailSource,
      bundle.resolveTrackerExecutionContextSource,
      bundle.normalizeTrackerExecutionContextSource,
      bundle.numericSummaryValueSource,
      bundle.trackerExportStageLabelSource,
      bundle.trackerExecutionToneSource,
      bundle.trackerExecutionMessageSource,
      bundle.syncRunActionButtonsSource,
      bundle.loadSelectedRunLogsSource,
      bundle.renderRunEventStatusSource,
    ].join("\n"),
    context,
    { filename: appPath },
  );
  return bundle;
}

test("run-panel wrappers delegate through app.js when controller is present", async () => {
  const calls = [];
  const wiringRuntimeSource = readWiringRuntimeSource();
  const context = createBaseContext({
    window: {
      RUN_PANELS_CONTROLLER: {
        createRunPanelsController(deps) {
          calls.push([
            "createRunPanelsController",
            Boolean(deps),
            { disconnectRunEventStream: typeof deps.trackerController?.disconnectRunEventStream === "function" },
          ]);
          return {
            changeRunsPage(delta) {
              calls.push(["changeRunsPage", delta]);
              return "page-delegated";
            },
            renderRunEventStatus(message, tone) {
              calls.push(["renderRunEventStatus", message, tone]);
              return "status-delegated";
            },
            renderRunDetail(run) {
              calls.push(["renderRunDetail", run?.id || null]);
              return "detail-delegated";
            },
            handleRunFormReset() {
              calls.push(["handleRunFormReset"]);
              return "reset-delegated";
            },
            buildRunPayload(payload) {
              calls.push(["buildRunPayload", payload]);
              return { delegated: true, payload };
            },
            createWinnerRun(options) {
              calls.push(["createWinnerRun", options]);
              return "winner-created";
            },
            resolveTrackerExecutionContext(run) {
              calls.push(["resolveTrackerExecutionContext", run?.id || null]);
              return { id: run?.id || null, delegated: true };
            },
            normalizeTrackerExecutionContext(payload) {
              calls.push(["normalizeTrackerExecutionContext", payload?.childRunId || null]);
              return { ...payload, delegated: true };
            },
            numericSummaryValue(...values) {
              calls.push(["numericSummaryValue", values]);
              return 99;
            },
            trackerExportStageLabel(stage) {
              calls.push(["trackerExportStageLabel", stage]);
              return `stage:${stage}`;
            },
            trackerExecutionTone(status) {
              calls.push(["trackerExecutionTone", status]);
              return `tone:${status}`;
            },
            trackerExecutionMessage(context) {
              calls.push(["trackerExecutionMessage", context?.status || ""]);
              return `message:${context?.status || ""}`;
            },
            syncRunActionButtons(run) {
              calls.push(["syncRunActionButtons", run?.id || null]);
              return "actions-delegated";
            },
            async loadSelectedRunLogs(options) {
              calls.push(["loadSelectedRunLogs", options]);
              return "logs-delegated";
            },
          };
        },
      },
    },
  });

  vm.runInContext(wiringRuntimeSource, context, { filename: wiringRuntimePath });
  const bundle = loadRunWrapperBundle(context);
  assert.match(bundle.getRunPanelsControllerSource, /createControllerWithWiringDeps\(\{/);
  assert.match(bundle.getRunPanelsControllerSource, /wiringDepsFactoryName:\s*"createRunPanelsControllerDeps"/);
  assert.match(bundle.getRunPanelsControllerSource, /buildRunPanelsControllerDeps\(\)/);
  assert.match(bundle.handleRunFormResetSource, /RUN_PANELS_FALLBACK_RUNTIME/);
  assert.match(bundle.buildRunPayloadSource, /RUN_PANELS_FALLBACK_RUNTIME/);
  assert.match(bundle.createWinnerRunSource, /RUN_PANELS_FALLBACK_RUNTIME/);
  assert.match(bundle.normalizeTrackerExecutionContextSource, /function normalizeTrackerExecutionContext\(payload = \{\}\)/);
  assert.match(bundle.normalizeTrackerExecutionContextSource, /callRunPanelsControllerMethod\("normalizeTrackerExecutionContext", null, payload\)/);
  assert.match(bundle.handleRunFormResetSource, /controller\?\.handleRunFormReset/);
  assert.match(bundle.buildRunPayloadSource, /controller\?\.buildRunPayload/);
  assert.match(bundle.createWinnerRunSource, /controller\?\.createWinnerRun/);
  assert.doesNotMatch(bundle.handleRunFormResetSource, /dom\.runForm\.reset|querySelector|notice_title|demand_org/);
  assert.doesNotMatch(bundle.buildRunPayloadSource, /new FormData|rows_per_page|export_row_workers/);
  assert.doesNotMatch(bundle.createWinnerRunSource, /api\(\"\x2fapi\x2fruns\"/);
  assert.doesNotMatch(bundle.normalizeTrackerExecutionContextSource, /function normalizeTrackerExecutionContext\(\{\s*title,/);
  assert.doesNotMatch(bundle.normalizeTrackerExecutionContextSource, /const estimatedRows =|const trackerEntryRows =|numericSummaryValue\(/);

  const resetResult = context.handleRunFormReset();
  const payloadResult = context.buildRunPayload({ collectModeOverride: "synthetic" });
  const createResult = await context.createWinnerRun({
    collectModeOverride: "native",
    submitButton: { textContent: "run" },
    busyLabel: "busy",
  });
  const pageResult = context.changeRunsPage(1);
  const statusResult = context.renderRunEventStatus("connected", "ok");
  const detailResult = context.renderRunDetail({ id: "run-55" });
  const contextResult = context.resolveTrackerExecutionContext({ id: "run-55" });
  const normalizedResult = context.normalizeTrackerExecutionContext({
    title: "Tracker",
    status: "running",
    progressStage: "finalize",
    progressCurrent: 1,
    progressTotal: 2,
    childRunId: "child-1",
    parentRunId: "parent-1",
    summaryOutput: {},
    errorMessage: "",
  });
  const numericResult = context.numericSummaryValue(1, 2, 3);
  const stageLabel = context.trackerExportStageLabel("finalize");
  const toneResult = context.trackerExecutionTone("success");
  const messageResult = context.trackerExecutionMessage({ status: "success" });
  const actionsResult = context.syncRunActionButtons({ id: "run-55" });
  const logsResult = await context.loadSelectedRunLogs({ silent: true, runId: "run-42" });

  assert.equal(resetResult, "reset-delegated");
  assert.equal(payloadResult.delegated, true);
  assert.equal(payloadResult.payload.collectModeOverride, "synthetic");
  assert.equal(createResult, "winner-created");
  assert.equal(pageResult, "page-delegated");
  assert.equal(statusResult, "status-delegated");
  assert.equal(detailResult, "detail-delegated");
  assert.deepEqual(contextResult, { id: "run-55", delegated: true });
  assert.deepEqual(normalizedResult, {
    title: "Tracker",
    status: "running",
    progressStage: "finalize",
    progressCurrent: 1,
    progressTotal: 2,
    childRunId: "child-1",
    parentRunId: "parent-1",
    summaryOutput: {},
    errorMessage: "",
    delegated: true,
  });
  assert.equal(numericResult, 99);
  assert.equal(stageLabel, "stage:finalize");
  assert.equal(toneResult, "tone:success");
  assert.equal(messageResult, "message:success");
  assert.equal(actionsResult, "actions-delegated");
  assert.equal(logsResult, "logs-delegated");
  assert.deepEqual(
    JSON.parse(JSON.stringify(calls)),
    [
      ["createRunPanelsController", true, { disconnectRunEventStream: true }],
      ["handleRunFormReset"],
      ["buildRunPayload", { collectModeOverride: "synthetic" }],
      ["createWinnerRun", {
        collectModeOverride: "native",
        submitButton: { textContent: "run" },
        busyLabel: "busy",
      }],
      ["changeRunsPage", 1],
      ["renderRunEventStatus", "connected", "ok"],
      ["renderRunDetail", "run-55"],
      ["resolveTrackerExecutionContext", "run-55"],
      ["normalizeTrackerExecutionContext", "child-1"],
      ["numericSummaryValue", [1, 2, 3]],
      ["trackerExportStageLabel", "finalize"],
      ["trackerExecutionTone", "success"],
      ["trackerExecutionMessage", "success"],
      ["syncRunActionButtons", "run-55"],
      ["loadSelectedRunLogs", { silent: true, runId: "run-42" }],
    ],
  );
});

test("run-panel fallback dispatch is delegated through app-support", () => {
  const context = createBaseContext();
  const fallbackCalls = [];
  context.APP_SUPPORT.callRunPanelsControllerFallback = (payload) => {
    fallbackCalls.push({
      methodName: payload.methodName,
      args: JSON.parse(JSON.stringify(payload.args)),
      hasController: Boolean(payload.controller),
      hasFallback: typeof payload.fallback === "function",
      hasDispatch: typeof payload.dispatch === "function",
    });
    return "support-fallback";
  };

  const bundle = loadRunWrapperBundle(context);

  assert.match(bundle.callRunPanelsControllerMethodSource, /APP_SUPPORT\.callRunPanelsControllerFallback\(/);

  const result = context.callRunPanelsControllerMethod("numericSummaryValue", null, 1, 2, 3);

  assert.equal(result, "support-fallback");
  assert.deepEqual(fallbackCalls, [{
    methodName: "numericSummaryValue",
    args: [1, 2, 3],
    hasController: false,
    hasFallback: false,
    hasDispatch: true,
  }]);
});

test("getRunPanelsController fails fast when the run panels wiring runtime is missing", () => {
  const bundle = extractRunWrapperBundle();
  const context = createBaseContext({
    window: {
      SPMSAppControllerWiringRuntime: {},
      RUN_PANELS_CONTROLLER: {
        createRunPanelsController() {
          return {};
        },
      },
    },
  });

  vm.runInContext(`${bundle.createControllerWithWiringDepsSource}\n${bundle.getRunPanelsControllerSource}`, context, { filename: appPath });
  assert.throws(
    () => context.getRunPanelsController(),
    /SPMSAppControllerWiringRuntime is required before app\.js loads/,
  );
});

test("run-panel wrappers fall back safely when controller asset is absent", async () => {
  const calls = {
    syncUrlState: 0,
    loadRuns: [],
    renderLogsList: [],
    setBusy: [],
    flash: [],
    selectRun: [],
    renderRunExecutionContext: [],
    runFormReset: 0,
  };
  const formInputs = {
    '[name="notice_title"]': { value: "" },
    '[name="demand_org"]': { value: "" },
  };
  const context = createBaseContext({
    api: async () => ({ id: "run-created" }),
    flash(message, tone) {
      calls.flash.push([message, tone ?? ""]);
    },
    setBusy(button, isBusy, label) {
      calls.setBusy.push([isBusy, label]);
      button.textContent = label;
    },
    syncUrlState() {
      calls.syncUrlState += 1;
    },
    async loadRuns(options) {
      calls.loadRuns.push(options);
    },
    async selectRun(runId) {
      calls.selectRun.push(runId);
    },
    renderLogsList(items) {
      calls.renderLogsList.push(items);
    },
    renderRunExecutionContext(run) {
      calls.renderRunExecutionContext.push(run ? run.id : null);
    },
    isProjectTrackerRun(runType) {
      return runType === "project_tracker";
    },
    RUN_PANELS_FALLBACK_RUNTIME: {
      handleRunFormResetFallback({ dom }) {
        dom.runForm.reset();
        dom.runForm.querySelector('[name="notice_title"]').value = "기계설비 개선";
        dom.runForm.querySelector('[name="demand_org"]').value = "도시시설사업부";
      },
      buildRunPayloadFallback({ collectModeOverride }, { dom, FormData, normalizeCollectMode }) {
        const formData = new FormData(dom.runForm);
        return {
          run_type: "project_tracker",
          params: {
            notice_title: String(formData.get("notice_title") || "").trim(),
            demand_org: String(formData.get("demand_org") || "").trim(),
          },
          advanced_options: {
            collect_mode: normalizeCollectMode(collectModeOverride || String(formData.get("collect_mode") || "auto")),
          },
        };
      },
      async createWinnerRunFallback(options, deps) {
        const payload = deps.buildRunPayload({ collectModeOverride: options.collectModeOverride || "" });
        deps.setBusy(options.submitButton, true, options.busyLabel || "실행 시작 중...");
        try {
          const response = await deps.api("/api/runs", {
            method: "POST",
            body: JSON.stringify(payload),
          });
          deps.flash(`실행 등록: ${response.id}`);
          deps.state.selectedTrackerRunId = null;
          deps.state.selectedEntryId = null;
          deps.state.runFilters.page = 1;
          deps.syncUrlState();
          await deps.loadRuns({});
          await deps.selectRun(response.id);
        } finally {
          deps.setBusy(options.submitButton, false, "실행 시작");
        }
      },
      numericSummaryValueFallback(values = []) {
        for (const value of values) {
          const parsed = Number(value || 0);
          if (Number.isFinite(parsed) && parsed >= 0) {
            return parsed;
          }
        }
        return 0;
      },
      trackerExportStageLabelFallback(stage) {
        return stage === "finalize" ? "엑셀 생성" : String(stage || "waiting");
      },
      trackerExecutionToneFallback(status) {
        return status === "failed" ? "warn" : "";
      },
      trackerExecutionMessageFallback(context = {}) {
        return context.status === "success"
          ? `트래커 작업 ${context.trackerEntryRows}건을 준비했습니다. 완료 즉시 엑셀 템플릿으로 반환합니다.`
          : "";
      },
      normalizeTrackerExecutionContextFallback(payload = {}) {
        return {
          title: payload.title,
          status: String(payload.status || "queued"),
          progressStage: String(payload.progressStage || "waiting"),
          progressCurrent: Number(payload.progressCurrent || 0),
          progressTotal: Math.max(1, Number(payload.progressTotal || 2)),
          childRunId: String(payload.childRunId || ""),
          parentRunId: String(payload.parentRunId || ""),
          estimatedRows: Number(payload.summaryOutput?.tracker_entry_rows || 0),
          trackerEntryRows: Number(payload.summaryOutput?.tracker_entry_rows || 0),
          fileName: "",
          backend: "",
          errorMessage: String(payload.errorMessage || ""),
        };
      },
      resolveTrackerExecutionContextFallback(run, deps) {
        if (!run) {
          return null;
        }
        if (run.run_type === "tracker_export") {
          return this.normalizeTrackerExecutionContextFallback({
            title: "트래커 복기 진행",
            status: run.status,
            progressStage: run.progress_stage,
            progressCurrent: run.progress_current,
            progressTotal: run.progress_total,
            childRunId: run.id,
            parentRunId: run.parent_run_id || "",
            summaryOutput: run.summary?.output || {},
            errorMessage: run.error?.message || "",
          });
        }
        if (!deps.isProjectTrackerRun(run.run_type)) {
          return null;
        }
        return this.normalizeTrackerExecutionContextFallback({
          title: "트래커 실행",
          status: run.status,
          progressStage: "waiting",
          progressCurrent: 0,
          progressTotal: 2,
          childRunId: "",
          parentRunId: run.id,
          summaryOutput: {},
          errorMessage: "",
        });
      },
    },
    dom: {
      runForm: {
        reset() {
          calls.runFormReset += 1;
        },
        querySelector(selector) {
          return formInputs[selector] || null;
        },
      },
      submitRunButton: {
        textContent: "실행 시작",
      },
      runEventStatus: {
        textContent: "",
        dataset: {},
      },
      runEmptyState: {
        classList: createClassList(),
      },
      runDetail: {
        classList: createClassList(),
      },
      logsList: {
        innerHTML: "",
      },
      artifactsList: {
        innerHTML: "",
      },
      runId: { textContent: "" },
      runStatusBadge: { innerHTML: "" },
      runProgress: { textContent: "" },
      runType: { textContent: "" },
      runProgressStage: { textContent: "" },
      runProgressMeta: { textContent: "" },
      runProgressBar: { style: {} },
      runParams: { textContent: "" },
      runSummary: { textContent: "" },
      runError: { textContent: "" },
      runCreatedAt: { textContent: "" },
      runStartedAt: { textContent: "" },
      runFinishedAt: { textContent: "" },
      runParentId: { textContent: "" },
      cancelRunButton: { disabled: false },
      trackerExportButton: { disabled: false },
      refreshRunButton: { disabled: false },
      refreshLogsButton: { disabled: false },
      refreshArtifactsButton: { disabled: false },
      refreshEntriesButton: { disabled: false },
    },
  });

  loadRunWrapperBundle(context);

  context.handleRunFormReset();
  const pageResult = context.changeRunsPage(1);
  const statusResult = context.renderRunEventStatus("fallback", "warn");
  assert.equal(context.dom.runEventStatus.textContent, "");
  assert.deepEqual(context.dom.runEventStatus.dataset, {});
  const createResult = await context.createWinnerRun({
    submitButton: context.dom.submitRunButton,
    busyLabel: "실행 중...",
  });
  const detailResult = context.renderRunDetail(null);
  const executionContext = context.resolveTrackerExecutionContext({
    id: "child-1",
    run_type: "tracker_export",
    status: "success",
    progress_stage: "finalize",
    progress_current: 1,
    progress_total: 2,
    parent_run_id: "run-parent",
    summary: { output: { tracker_entry_rows: 7 } },
    error: { message: "" },
  });
  const normalizedContext = context.normalizeTrackerExecutionContext({
    title: "Tracker",
    status: "failed",
    progressStage: "waiting",
    progressCurrent: 0,
    progressTotal: 2,
    childRunId: "child-1",
    parentRunId: "run-parent",
    summaryOutput: { tracker_entry_rows: 7 },
    errorMessage: "boom",
  });
  const numericResult = context.numericSummaryValue(undefined, "7");
  const stageLabel = context.trackerExportStageLabel("finalize");
  const toneResult = context.trackerExecutionTone("failed");
  const messageResult = context.trackerExecutionMessage({ status: "success", trackerEntryRows: 7, estimatedRows: 7 });
  const actionsResult = context.syncRunActionButtons({
    id: "run-success",
    status: "success",
    run_type: "project_tracker",
  });
  const logsResult = await context.loadSelectedRunLogs({ runId: null });

  assert.equal(pageResult, undefined);
  assert.equal(statusResult, undefined);
  assert.equal(createResult, undefined);
  assert.equal(detailResult, undefined);
  assert.equal(executionContext.childRunId, "child-1");
  assert.equal(executionContext.status, "success");
  assert.equal(normalizedContext.errorMessage, "boom");
  assert.equal(typeof numericResult, "number");
  assert.ok(stageLabel);
  assert.equal(toneResult, "warn");
  assert.match(messageResult, /7/);
  assert.equal(actionsResult, undefined);
  assert.equal(logsResult, undefined);
  assert.equal(calls.runFormReset, 1);
  assert.equal(formInputs['[name="notice_title"]'].value, "기계설비 개선");
  assert.equal(formInputs['[name="demand_org"]'].value, "도시시설사업부");
  assert.equal(context.state.runFilters.page, 1);
  assert.equal(context.state.selectedTrackerRunId, null);
  assert.equal(context.state.selectedEntryId, null);
  assert.equal(calls.syncUrlState, 1);
  assert.deepEqual(JSON.parse(JSON.stringify(calls.loadRuns)), [{}]);
  assert.deepEqual(calls.selectRun, ["run-created"]);
  assert.deepEqual(
    JSON.parse(JSON.stringify(calls.setBusy)),
    [
      [true, "실행 중..."],
      [false, "실행 시작"],
    ],
  );
  assert.equal(context.dom.logsList.innerHTML, "");
  assert.equal(context.dom.artifactsList.innerHTML, "");
  assert.equal(context.dom.cancelRunButton.disabled, true);
  assert.equal(context.dom.trackerExportButton.disabled, false);
  assert.equal(context.dom.refreshRunButton.disabled, false);
  assert.deepEqual(calls.renderRunExecutionContext, []);
  assert.deepEqual(JSON.parse(JSON.stringify(context.state.runLogs)), [{ id: 1 }]);
  assert.deepEqual([...context.state.runLogIds], [1]);
  assert.deepEqual(JSON.parse(JSON.stringify(calls.renderLogsList)), []);
});
