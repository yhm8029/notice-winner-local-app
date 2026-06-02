import {
  createRunPanelsArtifactHelpers,
  createRunPanelsExecutionHelpers,
  createRunPanelsFormHelpers,
} from "./run-panels-controller-helpers.js?v=20260602h";

export function createRunPanelsController(deps = {}) {
  const state = deps.state;
  const dom = deps.dom;
  const window = deps.window || globalThis.window || globalThis;
  const document = deps.document || globalThis.document || null;
  const RUN_VIEW_RUNTIME = deps.RUN_VIEW_RUNTIME || null;
  const api = deps.api || (async () => {
    throw new Error("api is required");
  });
  const flash = deps.flash || (() => {});
  const touchSyncMeta = deps.touchSyncMeta || (() => {});
  const setBusy = deps.setBusy || (() => {});
  const loadRuns = deps.loadRuns || (async () => {});
  const trackerController = deps.trackerController || null;
  const resetTrackerBoardEdit = deps.resetTrackerBoardEdit || (() => {});
  const syncUrlState = deps.syncUrlState || (() => {});
  const refreshSelectedRun = deps.refreshSelectedRun || (async () => {});
  const escapeHtml = deps.escapeHtml || ((value) => String(value || ""));
  const runTypeLabel = deps.runTypeLabel || ((value) => String(value || "-"));
  const statusBadge = deps.statusBadge || ((value) => String(value || ""));
  const formatDate = deps.formatDate || ((value) => String(value || ""));
  const formatJson = deps.formatJson || ((value) => {
    if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
      return "{}";
    }
    return JSON.stringify(value, null, 2);
  });
  const progressPercent = deps.progressPercent || (() => 0);
  const renderRunExecutionContext = deps.renderRunExecutionContext || (() => {});
  const isProjectTrackerRun = deps.isProjectTrackerRun || (() => false);
  const useGlobalTrackerEntriesScope = deps.useGlobalTrackerEntriesScope || (() => false);
  const renderArtifactsList = deps.renderArtifactsList || (() => {});
  const buildArtifactEmptyMessage = deps.buildArtifactEmptyMessage || (() => "");
  const loadTrackerEntries = deps.loadTrackerEntries || (async () => {});

  const {
    handleRunFormReset,
    buildRunPayload,
    createWinnerRun,
    normalizeCollectMode,
    syncCollectModeOptions,
  } = createRunPanelsFormHelpers({
    state,
    dom,
    document,
    RUN_VIEW_RUNTIME,
    api,
    flash,
    setBusy,
    loadRuns,
    syncUrlState,
    selectRun,
  });

  async function selectRun(runId) {
    trackerController?.disconnectRunEventStream?.();
    state.selectedRunId = runId;
    state.openArtifactId = null;
    state.selectedTrackerRun = null;
    state.selectedTrackerWorkbookArtifactId = null;
    resetTrackerBoardEdit();
    state.runLogs = [];
    state.runLogIds = new Set();
    dom.logsList.innerHTML = '<div class="empty-state">?癲??嶺??雅?퍔瑗?짆?⑹퀪?????⑥ル럯??????嶺뚮ㅎ????關???꾨き??熬곥룊?????????놁졄.</div>';
    renderRunEventStatus("Waiting for live events");
    window.clearTimeout(state.artifactRetryHandle);
    state.artifactRetryHandle = null;
    syncUrlState();
    renderRuns();
    state.selectedEntryId = null;
    state.selectedEntry = null;
    state.drawerOpen = false;
    await refreshSelectedRun();
  }

  function syncRunFilterControlsFromState() {
    dom.runFilterStatus.value = state.runFilters.status;
    dom.runFilterType.value = state.runFilters.runType;
    dom.runFilterFrom.value = state.runFilters.from;
    dom.runFilterTo.value = state.runFilters.to;
    dom.runPageSize.value = String(state.runFilters.pageSize);
  }

  function changeRunsPage(delta) {
    const totalPages = Math.max(1, Math.ceil(state.runsTotal / state.runFilters.pageSize));
    const nextPage = Math.min(totalPages, Math.max(1, state.runFilters.page + delta));
    if (nextPage === state.runFilters.page) {
      return;
    }
    state.runFilters.page = nextPage;
    syncUrlState();
    void loadRuns({ preservePage: true });
  }

  function schedulePolling(run) {
    window.clearTimeout(state.pollHandle);
    state.pollHandle = null;
    const trackerRunning = state.selectedTrackerRun && ["queued", "running"].includes(state.selectedTrackerRun.status);
    if (!state.autoRefresh || !run || (!["queued", "running"].includes(run.status) && !trackerRunning)) {
      return;
    }
    state.pollHandle = window.setTimeout(() => refreshSelectedRun({ silent: true }), 2000);
  }

  const {
    numericSummaryValue,
    trackerExportStageLabel,
    trackerExecutionTone,
    trackerExecutionMessage,
    normalizeTrackerExecutionContext,
    resolveTrackerExecutionContext,
  } = createRunPanelsExecutionHelpers({
    state,
    RUN_VIEW_RUNTIME,
    isProjectTrackerRun,
  });

  function renderRuns() {
    if (!state.runs.length) {
      dom.runsList.innerHTML = '<div class="empty-state">No runs match the current filters.</div>';
      return;
    }

    const runsListMarkup = RUN_VIEW_RUNTIME?.buildRunsListMarkup(
      state.runs,
      {
        selectedRunId: state.selectedRunId,
      },
      {
        escapeHtml,
        runTypeLabel,
        statusBadge,
        formatDate,
      },
    );
    dom.runsList.innerHTML = runsListMarkup || state.runs
      .map((run) => {
        const selectedClass = run.id === state.selectedRunId ? " is-selected" : "";
        const parentLine = run.parent_run_id
          ? `<p class="mono">parent ${escapeHtml(run.parent_run_id)}</p>`
          : "";
        return `
        <article class="run-card${selectedClass}" data-run-id="${escapeHtml(run.id)}">
          <div class="run-card-head">
            <div>
              <strong>${escapeHtml(runTypeLabel(run.run_type))}</strong>
              <p class="mono">${escapeHtml(run.id)}</p>
            </div>
            ${statusBadge(run.status)}
          </div>
          <p>stage ${escapeHtml(run.progress_stage || "-")}</p>
          ${parentLine}
          <p>created ${escapeHtml(formatDate(run.created_at))}</p>
        </article>
      `;
      })
      .join("");

    for (const card of dom.runsList.querySelectorAll("[data-run-id]")) {
      card.addEventListener("click", () => selectRun(card.getAttribute("data-run-id")));
    }
  }

  function renderRunsPagination() {
    const totalPages = Math.max(1, Math.ceil(state.runsTotal / state.runFilters.pageSize));
    const runsPageMeta = RUN_VIEW_RUNTIME?.buildRunsPageMeta(
      state.runFilters.page,
      totalPages,
      state.runsTotal,
    );
    dom.runsPageMeta.textContent = runsPageMeta || `Page ${state.runFilters.page} / ${totalPages} | ${state.runsTotal} run(s)`;
    dom.runsPrevButton.disabled = state.runFilters.page <= 1;
    dom.runsNextButton.disabled = state.runFilters.page >= totalPages;
  }

  function syncRunActionButtons(run) {
    const isRunning = run && (run.status === "queued" || run.status === "running");
    const trackerRunning = state.selectedTrackerRun && ["queued", "running"].includes(state.selectedTrackerRun.status);
    const canCancel = run && !["success", "failed", "cancelled"].includes(run.status);
    const canTrackerExport = run && isProjectTrackerRun(run.run_type) && run.status === "success";
    const canRefreshEntries = useGlobalTrackerEntriesScope() || Boolean(run && run.run_type === "tracker_export");

    dom.cancelRunButton.disabled = !canCancel;
    dom.trackerExportButton.disabled = !canTrackerExport;
    dom.refreshRunButton.disabled = !run;
    dom.refreshLogsButton.disabled = !run;
    dom.refreshArtifactsButton.disabled = !run;
    if (dom.refreshEntriesButton) {
      dom.refreshEntriesButton.disabled = !canRefreshEntries;
    }
    if (!isRunning && !trackerRunning) {
      window.clearTimeout(state.pollHandle);
      state.pollHandle = null;
    }
  }

  function renderRunDetail(run) {
    if (!run) {
      dom.runEmptyState.classList.remove("hidden");
      dom.runDetail.classList.add("hidden");
      dom.logsList.innerHTML = '<div class="empty-state">No run selected.</div>';
      dom.artifactsList.innerHTML = '<div class="empty-state">No run selected.</div>';
      renderRunEventStatus("Waiting for events");
      renderRunExecutionContext(null);
      syncRunActionButtons(null);
      return;
    }

    const detailView = RUN_VIEW_RUNTIME?.buildRunDetailViewModel(
      run,
      {
        runTypeLabel,
        formatDate,
        formatJson,
        progressPercent,
      },
    );
    if (!detailView) {
      dom.runEmptyState.classList.add("hidden");
      dom.runDetail.classList.remove("hidden");
      dom.runId.textContent = run.id;
      dom.runStatusBadge.innerHTML = statusBadge(run.status);
      dom.runProgress.textContent = `${run.progress_current} / ${run.progress_total}`;
      dom.runType.textContent = runTypeLabel(run.run_type);
      dom.runProgressStage.textContent = run.progress_stage || "waiting";
      dom.runProgressMeta.textContent = `${run.progress_current} / ${run.progress_total}`;
      dom.runProgressBar.style.width = `${progressPercent(run)}%`;
      dom.runParams.textContent = formatJson(run.params);
      dom.runSummary.textContent = formatJson(run.summary);
      dom.runError.textContent = formatJson(run.error);
      dom.runCreatedAt.textContent = formatDate(run.created_at);
      dom.runStartedAt.textContent = formatDate(run.started_at);
      dom.runFinishedAt.textContent = formatDate(run.finished_at);
      dom.runParentId.textContent = run.parent_run_id || "-";
      renderRunExecutionContext(run);
      syncRunActionButtons(run);
      return;
    }

    dom.runEmptyState.classList.add("hidden");
    dom.runDetail.classList.remove("hidden");
    dom.runId.textContent = detailView.id;
    dom.runStatusBadge.innerHTML = statusBadge(detailView.status);
    dom.runProgress.textContent = detailView.progressText;
    dom.runType.textContent = detailView.runTypeLabel;
    dom.runProgressStage.textContent = detailView.progressStage;
    dom.runProgressMeta.textContent = detailView.progressText;
    dom.runProgressBar.style.width = `${detailView.progressPercent}%`;
    dom.runParams.textContent = detailView.paramsText;
    dom.runSummary.textContent = detailView.summaryText;
    dom.runError.textContent = detailView.errorText;
    dom.runCreatedAt.textContent = detailView.createdAtText;
    dom.runStartedAt.textContent = detailView.startedAtText;
    dom.runFinishedAt.textContent = detailView.finishedAtText;
    dom.runParentId.textContent = detailView.parentRunId;
    renderRunExecutionContext(run);
    syncRunActionButtons(run);
  }

  function renderLogsList(items) {
    if (!items.length) {
      dom.logsList.innerHTML = '<div class="empty-state">No logs recorded yet.</div>';
      return;
    }
    dom.logsList.innerHTML = RUN_VIEW_RUNTIME?.buildRunLogsMarkup(
      items,
      {
        escapeHtml,
        formatDate,
      },
    ) || items
      .map(
        (item) => `
        <article class="log-item">
          <div class="artifact-head">
            <strong>${escapeHtml(item.level)}</strong>
            <span class="mono">#${item.id}</span>
          </div>
          <p>${escapeHtml(item.stage || "-")} :: ${escapeHtml(item.message)}</p>
          <p class="mono">${escapeHtml(formatDate(item.created_at))}</p>
        </article>
      `,
      )
      .join("");
  }

  async function loadSelectedRunLogs({ silent = false, runId = state.selectedRunId } = {}) {
    if (!runId) {
      state.runLogs = [];
      state.runLogIds = new Set();
      renderLogsList([]);
      return;
    }
    try {
      const response = await api(`/api/runs/${runId}/logs?limit=50`);
      if (runId !== state.selectedRunId) {
        return;
      }
      state.runLogs = response.items || [];
      state.runLogIds = new Set(state.runLogs.map((item) => item.id));
      renderLogsList(state.runLogs);
      touchSyncMeta(`logs synced ${new Date().toLocaleTimeString()}`);
    } catch (err) {
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  const {
    fetchArtifactPreview,
    ensureArtifactPreviewCached,
    resolveTrackerContextRun,
    resolveTrackerWorkbookArtifactForSelection,
    shouldRetryTrackerWorkbookArtifact,
    fetchArtifactsForRun,
    makeArtifactSection,
    sortArtifacts,
    buildArtifactSectionsForRun,
    scheduleArtifactRetry,
    loadSelectedRunArtifacts,
    loadWinnerRunPanels,
    loadTrackerExportPanels,
  } = createRunPanelsArtifactHelpers({
    state,
    dom,
    window,
    api,
    flash,
    touchSyncMeta,
    escapeHtml,
    runTypeLabel,
    formatDate,
    renderRunExecutionContext,
    isProjectTrackerRun,
    renderArtifactsList,
    buildArtifactEmptyMessage,
    loadSelectedRunLogs,
    loadTrackerEntries,
    resetTrackerBoardEdit,
  });

  async function cancelSelectedRun() {
    if (!state.selectedRunId) {
      return;
    }
    setBusy(dom.cancelRunButton, true, "Cancelling...");
    try {
      const response = await api(`/api/runs/${state.selectedRunId}/cancel`, { method: "POST" });
      flash(`Cancel requested for ${response.id}`);
      await refreshSelectedRun();
      await loadRuns({ silent: true, preservePage: true });
    } catch (err) {
      flash(err.message, "error");
    } finally {
      setBusy(dom.cancelRunButton, false, "Cancel run");
    }
  }

  async function createTrackerExportForSelectedRun() {
    if (!state.selectedRunId) {
      return;
    }
    setBusy(dom.trackerExportButton, true, "?饔낅떽???壤굿?戮㏐광????..");
    try {
      const response = await api(`/api/runs/${state.selectedRunId}/tracker-export`, { method: "POST" });
      flash(`??轅붽틓??????????????濚밸Ŧ援잏댆??????怨뺤르?? ${response.id}`);
      state.selectedTrackerRunId = response.id;
      state.runFilters.page = 1;
      await selectRun(response.id);
      await loadRuns({ silent: true, preservePage: true });
    } catch (err) {
      flash(err.message, "error");
    } finally {
      setBusy(dom.trackerExportButton, false, "Create tracker export");
    }
  }

  function upsertRunListItem(run) {
    const nextItem = {
      id: run.id,
      status: run.status,
      run_type: run.run_type,
      parent_run_id: run.parent_run_id,
      progress_stage: run.progress_stage,
      created_at: run.created_at,
      started_at: run.started_at,
      finished_at: run.finished_at,
    };
    const index = state.runs.findIndex((item) => item.id === run.id);
    if (index >= 0) {
      state.runs[index] = nextItem;
      return;
    }
    state.runs = [nextItem, ...state.runs].slice(0, state.runFilters.pageSize);
  }

  function renderRunEventStatus(message, tone = "") {
    if (!dom.runEventStatus) {
      return;
    }
    dom.runEventStatus.textContent = message;
    dom.runEventStatus.dataset.tone = tone;
  }

  function renderRunPresetPanel(errorMessage = "") {
    if (!dom.presetSelect || !dom.presetStatus) {
      return;
    }
    const options = RUN_VIEW_RUNTIME?.buildRunPresetOptionsMarkup(
      state.runPresets,
      { escapeHtml },
    ) || ['<option value="">Select preset</option>']
      .concat(
        state.runPresets.map(
          (item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`
        )
      )
      .join("");
    dom.presetSelect.innerHTML = options;
    dom.presetSelect.value = state.selectedPresetId || "";
    dom.presetStatus.textContent = RUN_VIEW_RUNTIME?.buildRunPresetStatusText(
      state.runPresets,
      errorMessage,
    ) || (errorMessage
      ? `Failed to load presets: ${errorMessage}`
      : state.runPresets.length
        ? `Loaded ${state.runPresets.length} presets`
        : "No saved presets.");
  }

  function applyPresetParams(params) {
    for (const [name, rawValue] of Object.entries(params || {})) {
      const input = dom.runForm?.querySelector?.(`[name="${name}"]`);
      if (!input) {
        continue;
      }
      input.value = rawValue == null ? "" : String(rawValue);
    }
  }

  async function loadRunPresets({ silent = false } = {}) {
    try {
      const response = await api("/api/run-presets?limit=12");
      state.runPresets = response.items || [];
      if (state.selectedPresetId && !state.runPresets.some((item) => item.id === state.selectedPresetId)) {
        state.selectedPresetId = null;
      }
      if (!state.selectedPresetId && state.runPresets.length) {
        state.selectedPresetId = state.runPresets[0].id;
      }
      renderRunPresetPanel();
    } catch (err) {
      state.runPresets = [];
      renderRunPresetPanel(err.message);
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  async function applySelectedPreset() {
    const presetId = dom.presetSelect?.value || state.selectedPresetId;
    if (!presetId) {
      flash("???ㅼ굣?????ш끽諭욥걡???獄????ャ뀕???筌뚯뼚???", "error");
      return;
    }
    const preset = state.runPresets.find((item) => item.id === presetId);
    if (!preset) {
      flash("???ャ뀕?????ш끽諭욥걡???獄?癲ル슓??젆???????⑤８?????덊렡.", "error");
      return;
    }
    state.selectedPresetId = preset.id;
    applyPresetParams(preset.params || {});
    renderRunPresetPanel();
    flash("Preset applied: " + preset.name);
  }

  async function saveCurrentFormAsPreset() {
    const defaultName = new Date().toISOString().slice(0, 10) + " Search preset";
    const name = window.prompt("Preset name", defaultName);
    if (!name || !name.trim()) {
      return;
    }
    const formData = new FormData(dom.runForm);
    const params = {};
    for (const [key, value] of formData.entries()) {
      params[key] = String(value ?? "");
    }
    setBusy(dom.presetSaveButton, true, "Saving...");
    try {
      const response = await api("/api/run-presets", {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), params }),
      });
      state.selectedPresetId = response.id;
      flash("Preset saved: " + response.name);
      await loadRunPresets({ silent: true });
    } catch (err) {
      flash(err.message, "error");
    } finally {
      setBusy(dom.presetSaveButton, false, "Save current filters");
    }
  }

  return {
    handleRunFormReset,
    buildRunPayload,
    createWinnerRun,
    selectRun,
    normalizeCollectMode,
    syncCollectModeOptions,
    syncRunFilterControlsFromState,
    changeRunsPage,
    renderRuns,
    renderRunsPagination,
    renderRunDetail,
    resolveTrackerExecutionContext,
    normalizeTrackerExecutionContext,
    numericSummaryValue,
    trackerExportStageLabel,
    trackerExecutionTone,
    trackerExecutionMessage,
    renderLogsList,
    loadSelectedRunLogs,
    loadSelectedRunArtifacts,
    loadWinnerRunPanels,
    loadTrackerExportPanels,
    scheduleArtifactRetry,
    ensureArtifactPreviewCached,
    cancelSelectedRun,
    createTrackerExportForSelectedRun,
    upsertRunListItem,
    renderRunEventStatus,
    renderRunPresetPanel,
    loadRunPresets,
    applyPresetParams,
    applySelectedPreset,
    saveCurrentFormAsPreset,
    syncRunActionButtons,
    schedulePolling,
    resolveTrackerContextRun,
  };
}

const runPanelsControllerRoot = typeof window !== "undefined" ? window : globalThis;
runPanelsControllerRoot.RUN_PANELS_CONTROLLER = runPanelsControllerRoot.RUN_PANELS_CONTROLLER || {};
runPanelsControllerRoot.RUN_PANELS_CONTROLLER.createRunPanelsController = createRunPanelsController;
