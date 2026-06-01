export function createRunPanelsFormHelpers(deps = {}) {
  const state = deps.state;
  const dom = deps.dom;
  const document = deps.document || globalThis.document || null;
  const RUN_VIEW_RUNTIME = deps.RUN_VIEW_RUNTIME || null;
  const api = deps.api || (async () => {
    throw new Error("api is required");
  });
  const flash = deps.flash || (() => {});
  const setBusy = deps.setBusy || (() => {});
  const loadRuns = deps.loadRuns || (async () => {});
  const syncUrlState = deps.syncUrlState || (() => {});
  const loadRunPresets = deps.loadRunPresets || (async () => {});
  const selectRun = deps.selectRun || (async () => {});

  function syntheticDebugEnabled() {
    return Boolean((state.dashboard || {}).synthetic_debug_enabled);
  }

  function normalizeCollectMode(value) {
    const raw = String(value || "").trim().toLowerCase();
    if (raw === "synthetic" && !syntheticDebugEnabled()) {
      return "auto";
    }
    if (["auto", "native", "synthetic"].includes(raw)) {
      return raw;
    }
    return "auto";
  }

  function handleRunFormReset() {
    dom.runForm.reset();
    const defaults = {
      notice_title: "Sample project",
      demand_org: "Sample organization",
    };
    for (const [name, value] of Object.entries(defaults)) {
      const input = dom.runForm.querySelector(`[name="${name}"]`);
      if (input) {
        input.value = value;
      }
    }
  }

  function buildRunPayload({ collectModeOverride = "" } = {}) {
    const formData = new FormData(dom.runForm);
    const collectMode = normalizeCollectMode(collectModeOverride || String(formData.get("collect_mode") || "auto"));
    return {
      run_type: "project_tracker",
      params: {
        start_date: String(formData.get("start_date") || "").trim(),
        end_date: String(formData.get("end_date") || "").trim(),
        contract_date_hint: String(formData.get("contract_date_hint") || "").trim(),
        bid_no: String(formData.get("bid_no") || "").trim(),
        notice_title: String(formData.get("notice_title") || "").trim(),
        demand_org: String(formData.get("demand_org") || "").trim(),
        rows_per_page: Number(formData.get("rows_per_page") || 100),
        max_pages: Number(formData.get("max_pages") || 3),
        api_scope: String(formData.get("api_scope") || "construction"),
      },
      advanced_options: {
        collect_mode: collectMode,
        simulate_stage_delay_ms: Number(formData.get("simulate_stage_delay_ms") || 20),
        llm_correct: formData.get("llm_correct") === "on",
        llm_model: String(formData.get("llm_model") || "").trim(),
        llm_max_rows: Number(formData.get("llm_max_rows") || 20),
        export_row_workers: Number(formData.get("export_row_workers") || 8),
      },
    };
  }

  async function createWinnerRun({ collectModeOverride = "", submitButton = null, busyLabel = "" } = {}) {
    const payload = buildRunPayload({ collectModeOverride });
    const button = submitButton || dom.submitRunButton;
    const originalLabel = button.textContent || "???덈뺄 ??戮곗굚";
    setBusy(button, true, busyLabel || "???덈뺄 ??戮곗굚 繞?..");
    try {
      const response = await api("/api/runs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      flash(`???덈뺄 ?繹먮굞夷? ${response.id}`);
      state.selectedTrackerRunId = null;
      state.selectedEntryId = null;
      state.runFilters.page = 1;
      syncUrlState();
      await loadRuns({});
      await selectRun(response.id);
    } catch (err) {
      flash(err.message, "error");
    } finally {
      setBusy(button, false, originalLabel);
    }
  }

  function syncCollectModeOptions() {
    const collectModeSelect = dom.runForm?.querySelector('[name="collect_mode"]');
    if (!collectModeSelect) {
      return;
    }
    const guiOption = collectModeSelect.querySelector('option[value="gui_seed"]');
    if (guiOption) {
      guiOption.remove();
    }
    let syntheticOption = collectModeSelect.querySelector('option[value="synthetic"]');
    if (syntheticDebugEnabled()) {
      if (!syntheticOption) {
        syntheticOption = document.createElement("option");
        syntheticOption.value = "synthetic";
        syntheticOption.textContent = "??諛댁뎽";
        collectModeSelect.appendChild(syntheticOption);
      }
    } else if (syntheticOption) {
      syntheticOption.remove();
    }
    if (!syntheticDebugEnabled() && collectModeSelect.value === "synthetic") {
      collectModeSelect.value = "auto";
    }
  }

  function renderRunPresetPanel(errorMessage = "") {
    if (!dom.presetSelect || !dom.presetStatus) {
      return;
    }
    const options = RUN_VIEW_RUNTIME?.buildRunPresetOptionsMarkup(
      state.runPresets,
      { escapeHtml: deps.escapeHtml || ((value) => String(value || "")) },
    ) || ['<option value="">?熬곣뱿遊????ルㅎ臾?/option>']
      .concat(
        state.runPresets.map(
          (item) => `<option value="${(deps.escapeHtml || ((value) => String(value || "")))(item.id)}">${(deps.escapeHtml || ((value) => String(value || "")))(item.name)}</option>`,
        ),
      )
      .join("");
    dom.presetSelect.innerHTML = options;
    dom.presetSelect.value = state.selectedPresetId || "";
    dom.presetStatus.textContent = RUN_VIEW_RUNTIME?.buildRunPresetStatusText(
      state.runPresets,
      errorMessage,
    ) || (errorMessage
      ? `?熬곣뱿遊???諭??釉띾쐞???? 嶺뚮쪇沅?쭛???鍮?? ${errorMessage}`
      : state.runPresets.length
        ? `嶺뚣끉裕???熬곣뱿遊??${state.runPresets.length}??`
        : "???縕ワ쭕??熬곣뱿遊???逾???怨룸????덈펲.");
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

  async function loadRunPresetsWithApi({ silent = false } = {}) {
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
      flash("??⑤챷????熬곣뱿遊???諭???ルㅎ臾??琉얠돪??", "error");
      return;
    }
    const preset = state.runPresets.find((item) => item.id === presetId);
    if (!preset) {
      flash("??ルㅎ臾???熬곣뱿遊???諭?嶺뚢돦堉? 嶺뚮쪇沅?쭛???鍮??", "error");
      return;
    }
    state.selectedPresetId = preset.id;
    applyPresetParams(preset.params || {});
    renderRunPresetPanel();
    flash("Preset applied: " + preset.name);
  }

  async function saveCurrentFormAsPreset() {
    const defaultName = new Date().toISOString().slice(0, 10) + " Search preset";
    const name = deps.window.prompt("Preset name", defaultName);
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
    syntheticDebugEnabled,
    normalizeCollectMode,
    handleRunFormReset,
    buildRunPayload,
    createWinnerRun,
    syncCollectModeOptions,
    renderRunPresetPanel,
    applyPresetParams,
    loadRunPresets: loadRunPresetsWithApi,
    applySelectedPreset,
    saveCurrentFormAsPreset,
  };
}

export function createRunPanelsExecutionHelpers(deps = {}) {
  const state = deps.state;
  const RUN_VIEW_RUNTIME = deps.RUN_VIEW_RUNTIME || null;
  const isProjectTrackerRun = deps.isProjectTrackerRun || (() => false);

  function numericSummaryValue(...values) {
    if (typeof RUN_VIEW_RUNTIME?.numericSummaryValue === "function") {
      return RUN_VIEW_RUNTIME.numericSummaryValue(...values);
    }
    for (const value of values) {
      const parsed = Number(value || 0);
      if (Number.isFinite(parsed) && parsed >= 0) {
        return parsed;
      }
    }
    return 0;
  }

  function trackerExportStageLabel(stage) {
    if (typeof RUN_VIEW_RUNTIME?.trackerExportStageLabel === "function") {
      return RUN_VIEW_RUNTIME.trackerExportStageLabel(stage);
    }
    const labels = {
      waiting: "waiting",
      tracker_export: "tracker export",
      finalize: "finalize",
    };
    return labels[String(stage || "").trim()] || String(stage || "waiting");
  }

  function trackerExecutionTone(status) {
    if (typeof RUN_VIEW_RUNTIME?.trackerExecutionTone === "function") {
      return RUN_VIEW_RUNTIME.trackerExecutionTone(status);
    }
    if (status === "success") {
      return "ok";
    }
    if (status === "failed" || status === "cancelled") {
      return "warn";
    }
    return "";
  }

  function trackerExecutionMessage(context) {
    if (typeof RUN_VIEW_RUNTIME?.trackerExecutionMessage === "function") {
      return RUN_VIEW_RUNTIME.trackerExecutionMessage(context);
    }
    if (!context) {
      return "";
    }
    if (context.status === "success") {
      return `?筌뤾퍔?????얜???${context.trackerEntryRows}濾곌쑬???繞벿뮻???듸쭛???鍮?? ?熬곣뫁??嶺뚯빖留?????裕?????ロ깵?源놁뒭???뿉??꾩룇瑗???紐껊퉵??`;
    }
    if (context.status === "failed") {
      return "?筌뤾퍔????곌랜??뵳寃쇱쾸? ???덉넮???곕????덈펲. ???댁쾼 ??怨몃뮔???筌먦끉逾???????곕뻣 ???덈뺄???곌랜????戮곌텕.";
    }
    if (context.status === "cancelled") {
      return "?筌뤾퍔????곌랜??뵳寃쇱쾸? ???쳛???琉????鍮??";
    }
    if (context.progressStage === "finalize") {
      return `??${context.trackerEntryRows || context.estimatedRows}濾곌쑬?????얜??????裕?????ロ깵?源놁뒭???뿉??筌먲퐘遊??濡ル츎 繞벿살탳????덈펲.`;
    }
    return `raw ?롪퍒???좊ご??筌뤾퍔?????얜????筌먦끇六??怨쀬Ŧ ?筌먲퐘遊??濡ル츎 繞벿살탳????덈펲. ????쭜 ${context.estimatedRows}濾??リ옇????怨쀬Ŧ ??ｌ뫒???꾩룇瑗???紐껊퉵??`;
  }

  function normalizeTrackerExecutionContext(payload = {}) {
    if (typeof RUN_VIEW_RUNTIME?.normalizeTrackerExecutionContext === "function") {
      return RUN_VIEW_RUNTIME.normalizeTrackerExecutionContext(payload);
    }
    const summaryOutput =
      payload.summaryOutput && typeof payload.summaryOutput === "object" && !Array.isArray(payload.summaryOutput)
        ? payload.summaryOutput
        : {};
    const estimatedRows = numericSummaryValue(
      summaryOutput.estimated_tracker_entry_rows,
      summaryOutput.auto_tracker_export_estimated_rows,
      summaryOutput.tracker_candidate_rows,
      summaryOutput.winner_csv_rows,
      summaryOutput.tracker_entry_rows,
    );
    const trackerEntryRows = numericSummaryValue(
      summaryOutput.tracker_entry_rows,
      summaryOutput.auto_tracker_export_tracker_entry_rows,
    );
    return {
      title: payload.title,
      status: String(payload.status || "queued").trim() || "queued",
      progressStage: String(payload.progressStage || "").trim() || "waiting",
      progressCurrent: numericSummaryValue(payload.progressCurrent),
      progressTotal: Math.max(1, numericSummaryValue(payload.progressTotal, 2)),
      childRunId: String(payload.childRunId || "").trim(),
      parentRunId: String(payload.parentRunId || "").trim(),
      estimatedRows,
      trackerEntryRows,
      fileName: String(
        summaryOutput.tracking_excel_file_name || summaryOutput.auto_tracker_export_tracking_excel_file_name || "",
      ).trim(),
      backend: String(summaryOutput.tracker_export_backend || summaryOutput.auto_tracker_export_backend || "").trim(),
      errorMessage: String(payload.errorMessage || "").trim(),
    };
  }

  function resolveTrackerExecutionContext(run) {
    if (!run) {
      return null;
    }
    if (run.run_type === "tracker_export") {
      return normalizeTrackerExecutionContext({
        title: "Tracker export run",
        status: run.status,
        progressStage: run.progress_stage,
        progressCurrent: run.progress_current,
        progressTotal: run.progress_total,
        childRunId: run.id,
        parentRunId: run.parent_run_id || "",
        summaryOutput: ((run.summary || {}).output || {}),
        errorMessage: ((run.error || {}).message || ""),
      });
    }
    if (!isProjectTrackerRun(run.run_type)) {
      return null;
    }
    const output = ((run.summary || {}).output || {});
    const trackerRun = state.selectedTrackerRun;
    const trackerOutput = trackerRun ? (((trackerRun.summary || {}).output || {})) : {};
    const enabled = Boolean(output.auto_tracker_export_enabled || trackerRun || state.selectedTrackerRunId);
    if (!enabled) {
      return null;
    }
    return normalizeTrackerExecutionContext({
      title: "Project tracker export",
      status: trackerRun ? trackerRun.status : String(output.auto_tracker_export_status || "").trim() || "queued",
      progressStage: trackerRun ? trackerRun.progress_stage : String(output.auto_tracker_export_progress_stage || "").trim(),
      progressCurrent: trackerRun ? trackerRun.progress_current : output.auto_tracker_export_progress_current,
      progressTotal: trackerRun ? trackerRun.progress_total : output.auto_tracker_export_progress_total,
      childRunId: trackerRun ? trackerRun.id : String(output.auto_tracker_export_run_id || "").trim(),
      parentRunId: run.id,
      summaryOutput: trackerRun ? trackerOutput : output,
      errorMessage: trackerRun ? ((trackerRun.error || {}).message || "") : String(output.auto_tracker_export_error || "").trim(),
    });
  }

  return {
    numericSummaryValue,
    trackerExportStageLabel,
    trackerExecutionTone,
    trackerExecutionMessage,
    normalizeTrackerExecutionContext,
    resolveTrackerExecutionContext,
  };
}

export function createRunPanelsArtifactHelpers(deps = {}) {
  const state = deps.state;
  const window = deps.window || globalThis.window || globalThis;
  const api = deps.api || (async () => {
    throw new Error("api is required");
  });
  const flash = deps.flash || (() => {});
  const touchSyncMeta = deps.touchSyncMeta || (() => {});
  const escapeHtml = deps.escapeHtml || ((value) => String(value || ""));
  const runTypeLabel = deps.runTypeLabel || ((value) => String(value || "-"));
  const formatDate = deps.formatDate || ((value) => String(value || ""));
  const renderRunExecutionContext = deps.renderRunExecutionContext || (() => {});
  const isProjectTrackerRun = deps.isProjectTrackerRun || (() => false);
  const buildArtifactEmptyMessage = deps.buildArtifactEmptyMessage || (() => "");
  const loadSelectedRunLogs = deps.loadSelectedRunLogs || (async () => {});
  const loadTrackerEntries = deps.loadTrackerEntries || (async () => {});
  const resetTrackerBoardEdit = deps.resetTrackerBoardEdit || (() => {});

  async function fetchArtifactPreview(item) {
    const limit = item.artifact_type === "tracking_excel" ? 16 : 6;
    return api(`/api/artifacts/${item.id}/preview?limit=${limit}`);
  }

  async function ensureArtifactPreviewCached(item) {
    if (!item || state.artifactPreviewCache[item.id]) {
      return;
    }
    try {
      state.artifactPreviewCache[item.id] = await fetchArtifactPreview(item);
    } catch (err) {
      state.artifactPreviewCache[item.id] = { error: err.message || "亦껋꼶梨?怨?돦??⒱뵛 ?β돦裕녻キ????덉넮" };
    }
    if (state.openArtifactId === item.id) {
      deps.renderArtifactsList();
    }
    if (state.selectedTrackerWorkbookArtifactId === item.id) {
      renderRunExecutionContext(state.selectedRun);
    }
  }

  function resolveTrackerContextRun(runSnapshot = state.selectedRun) {
    if (!runSnapshot) {
      return null;
    }
    if (runSnapshot.run_type === "tracker_export") {
      return runSnapshot;
    }
    return state.selectedTrackerRun;
  }

  function resolveTrackerWorkbookArtifactForSelection(runSnapshot, sections) {
    const trackerRun = resolveTrackerContextRun(runSnapshot);
    if (!trackerRun) {
      return null;
    }
    for (const section of sections || []) {
      if (section.runId !== trackerRun.id) {
        continue;
      }
      const trackingExcel = (section.items || []).find((item) => item.artifact_type === "tracking_excel");
      if (trackingExcel) {
        return trackingExcel;
      }
    }
    return null;
  }

  function shouldRetryTrackerWorkbookArtifact(runSnapshot, sections) {
    const trackerRun = resolveTrackerContextRun(runSnapshot);
    if (!trackerRun || trackerRun.status !== "success") {
      return false;
    }
    return !resolveTrackerWorkbookArtifactForSelection(runSnapshot, sections);
  }

  async function fetchArtifactsForRun(runId) {
    const response = await api(`/api/runs/${runId}/artifacts`);
    return sortArtifacts(response.items || []);
  }

  function makeArtifactSection(run, relation, items) {
    const relationLabel =
      relation === "parent"
        ? "?遊붋嶺????덈뺄"
        : relation === "child"
          ? "???六????덈뺄"
          : "??ルㅎ臾????덈뺄";
    return {
      relation,
      runId: run.id,
      title: `${relationLabel} 鸚?${runTypeLabel(run.run_type)}`,
      subtitle: `${run.progress_stage || "-"} 鸚?${formatDate(run.created_at)}`,
      meta: `${run.id} | ${run.status}`,
      items,
    };
  }

  function sortArtifacts(items) {
    const order = {
      execution_manifest: 0,
      winner_csv: 1,
      candidate_csv: 2,
      internal_nav_csv: 3,
      seed_csv: 4,
      tracking_excel: 5,
    };
    return [...items].sort((left, right) => {
      const leftOrder = order[left.artifact_type] ?? 99;
      const rightOrder = order[right.artifact_type] ?? 99;
      if (leftOrder !== rightOrder) {
        return leftOrder - rightOrder;
      }
      return String(right.created_at || "").localeCompare(String(left.created_at || ""));
    });
  }

  async function buildArtifactSectionsForRun(selectedRun) {
    if (!selectedRun) {
      return { sections: [], pendingChildRunId: "" };
    }
    const sections = [];
    let pendingChildRunId = "";
    if (isProjectTrackerRun(selectedRun.run_type)) {
      const selectedItems = await fetchArtifactsForRun(selectedRun.id);
      sections.push(makeArtifactSection(selectedRun, "selected", selectedItems));
      const childResponse = await api(`/api/runs?parent_run_id=${encodeURIComponent(selectedRun.id)}&page=1&page_size=50`);
      const childRuns = [...(childResponse.items || [])].sort((left, right) => {
        if (left.id === state.selectedTrackerRunId) {
          return -1;
        }
        if (right.id === state.selectedTrackerRunId) {
          return 1;
        }
        return String(right.created_at || "").localeCompare(String(left.created_at || ""));
      });
      const childSectionResults = await Promise.allSettled(
        childRuns.map(async (run) => ({ run, section: makeArtifactSection(run, "child", await fetchArtifactsForRun(run.id)) })),
      );
      for (const result of childSectionResults) {
        if (result.status !== "fulfilled") {
          continue;
        }
        const childRun = result.value.run;
        const section = result.value.section;
        if (section.items.length > 0) {
          sections.push(section);
          continue;
        }
        if (!pendingChildRunId && ["queued", "running"].includes(childRun.status)) {
          pendingChildRunId = childRun.id;
        }
      }
    } else {
      const selectedItems = await fetchArtifactsForRun(selectedRun.id);
      sections.push(makeArtifactSection(selectedRun, "selected", selectedItems));
      if (selectedRun.parent_run_id) {
        try {
          const parentRun = await api(`/api/runs/${selectedRun.parent_run_id}`);
          const parentItems = await fetchArtifactsForRun(parentRun.id);
          sections.unshift(makeArtifactSection(parentRun, "parent", parentItems));
        } catch (_err) {
          // Parent artifacts are optional when a child tracker_export run is selected.
        }
      }
    }
    return {
      sections: sections.filter((section) => section.items.length > 0),
      pendingChildRunId,
    };
  }

  function scheduleArtifactRetry(runId) {
    window.clearTimeout(state.artifactRetryHandle);
    state.artifactRetryHandle = window.setTimeout(() => {
      if (state.selectedRunId !== runId || !state.selectedRun || state.selectedRun.status !== "success") {
        return;
      }
      void loadSelectedRunArtifacts({ silent: true, runId, runSnapshot: state.selectedRun });
    }, 1500);
  }

  async function loadSelectedRunArtifacts({ silent = false, runId = state.selectedRunId, runSnapshot = state.selectedRun } = {}) {
    if (!runId || !runSnapshot) {
      state.artifacts = [];
      state.artifactSections = [];
      state.openArtifactId = null;
      state.selectedTrackerWorkbookArtifactId = null;
      window.clearTimeout(state.artifactRetryHandle);
      state.artifactRetryHandle = null;
      deps.dom.artifactsList.innerHTML = '<div class="empty-state">No run selected.</div>';
      renderRunExecutionContext(state.selectedRun);
      return;
    }
    try {
      const artifactResult = await buildArtifactSectionsForRun(runSnapshot);
      const sections = artifactResult.sections || [];
      if (runId !== state.selectedRunId) {
        return;
      }
      state.artifactSections = sections;
      state.artifacts = sections.flatMap((section) => section.items || []);
      const trackerWorkbookArtifact = resolveTrackerWorkbookArtifactForSelection(runSnapshot, sections);
      state.selectedTrackerWorkbookArtifactId = trackerWorkbookArtifact ? trackerWorkbookArtifact.id : null;
      const trackerWorkbookRetryPending = shouldRetryTrackerWorkbookArtifact(runSnapshot, sections);
      const trackerRun = resolveTrackerContextRun(runSnapshot);
      if (
        trackerWorkbookArtifact
        && trackerRun
        && trackerRun.status === "success"
        && state.autoOpenedTrackerPreviewRunId !== trackerRun.id
      ) {
        state.autoOpenedTrackerPreviewRunId = trackerRun.id;
        state.openArtifactId = trackerWorkbookArtifact.id;
      }
      if (!state.artifacts.length) {
        state.openArtifactId = null;
        deps.dom.artifactsList.innerHTML = `<div class="empty-state">${escapeHtml(buildArtifactEmptyMessage())}</div>`;
        if (
          (runSnapshot.run_type === "tracker_export" && runSnapshot.status === "success")
          || artifactResult.pendingChildRunId
          || trackerWorkbookRetryPending
        ) {
          scheduleArtifactRetry(runId);
        }
        renderRunExecutionContext(state.selectedRun);
        return;
      }
      window.clearTimeout(state.artifactRetryHandle);
      state.artifactRetryHandle = null;
      deps.renderArtifactsList();
      renderRunExecutionContext(state.selectedRun);
      if (trackerWorkbookArtifact) {
        void ensureArtifactPreviewCached(trackerWorkbookArtifact);
      }
      touchSyncMeta(`artifacts synced ${new Date().toLocaleTimeString()}`);
      if (artifactResult.pendingChildRunId || trackerWorkbookRetryPending) {
        scheduleArtifactRetry(runId);
      }
    } catch (err) {
      if (runSnapshot.run_type === "tracker_export" && runSnapshot.status === "success") {
        scheduleArtifactRetry(runId);
      }
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  async function loadWinnerRunPanels(run) {
    await loadSelectedRunLogs({ silent: true, runId: run.id });
    await loadSelectedRunArtifacts({ silent: true, runId: run.id, runSnapshot: run });
  }

  async function loadTrackerExportPanels(run) {
    await loadSelectedRunLogs({ silent: true, runId: run.id });
    await loadSelectedRunArtifacts({ silent: true, runId: run.id, runSnapshot: run });
    if (run.status === "success") {
      scheduleArtifactRetry(run.id);
    }
    await loadTrackerEntries({ silent: true, trackerRunId: run.id });
  }

  return {
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
  };
}
