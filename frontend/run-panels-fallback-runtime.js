(function attachSPMSRunPanelsFallbackRuntime(globalObject) {
  function handleRunFormResetFallback(context = {}) {
    const { dom = null } = context;
    const runForm = dom?.runForm;
    if (!runForm || typeof runForm.reset !== "function") {
      return;
    }
    runForm.reset();
    const defaults = {
      notice_title: "기계설비 개선",
      demand_org: "도시시설사업부",
    };
    for (const [name, value] of Object.entries(defaults)) {
      const input = runForm.querySelector?.(`[name="${name}"]`);
      if (input) {
        input.value = value;
      }
    }
  }

  function buildRunPayloadFallback(options = {}, context = {}) {
    const { collectModeOverride = "" } = options;
    const {
      dom = null,
      FormData: FormDataCtor = globalObject.FormData,
      normalizeCollectMode = (value) => String(value || "").trim().toLowerCase() || "auto",
    } = context;
    if (!dom?.runForm || typeof FormDataCtor !== "function") {
      return null;
    }
    const formData = new FormDataCtor(dom.runForm);
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

  async function createWinnerRunFallback(options = {}, context = {}) {
    const {
      collectModeOverride = "",
      submitButton = null,
      busyLabel = "",
    } = options;
    const {
      dom = null,
      state = null,
      api = async () => {
        throw new Error("api is required");
      },
      flash = () => {},
      setBusy = () => {},
      syncUrlState = () => {},
      loadRuns = async () => {},
      selectRun = async () => {},
      buildRunPayload = () => null,
    } = context;
    const payload = buildRunPayload({ collectModeOverride });
    if (!payload) {
      return;
    }
    const button = submitButton || dom?.submitRunButton || null;
    const originalLabel = button?.textContent || "실행 시작";
    if (button) {
      setBusy(button, true, busyLabel || "실행 시작 중...");
    }
    try {
      const response = await api("/api/runs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      flash(`실행 등록: ${response.id}`);
      if (state) {
        state.selectedTrackerRunId = null;
        state.selectedEntryId = null;
        if (state.runFilters) {
          state.runFilters.page = 1;
        }
      }
      syncUrlState();
      await loadRuns({});
      await selectRun(response.id);
    } catch (err) {
      flash(err?.message || "실행 생성에 실패했습니다.", "error");
    } finally {
      if (button) {
        setBusy(button, false, originalLabel);
      }
    }
  }

  function numericSummaryValueFallback(values = []) {
    for (const value of values) {
      const parsed = Number(value || 0);
      if (Number.isFinite(parsed) && parsed >= 0) {
        return parsed;
      }
    }
    return 0;
  }

  function trackerExportStageLabelFallback(stage) {
    const labels = {
      waiting: "대기",
      tracker_export: "트래커 정리",
      finalize: "엑셀 생성",
    };
    return labels[String(stage || "").trim()] || String(stage || "waiting");
  }

  function trackerExecutionToneFallback(status) {
    if (status === "success") {
      return "ok";
    }
    if (status === "failed" || status === "cancelled") {
      return "warn";
    }
    return "";
  }

  function trackerExecutionMessageFallback(context = {}) {
    if (!context) {
      return "";
    }
    if (context.status === "success") {
      return `트래커 작업 ${context.trackerEntryRows}건을 준비했습니다. 완료 즉시 엑셀 템플릿으로 반환합니다.`;
    }
    if (context.status === "failed") {
      return "트래커 보기가 실패했습니다. 오류 내용을 확인한 뒤 다시 실행해 보세요.";
    }
    if (context.status === "cancelled") {
      return "트래커 보기가 취소되었습니다.";
    }
    if (context.progressStage === "finalize") {
      return `약 ${context.trackerEntryRows || context.estimatedRows}건을 엑셀 템플릿으로 정리하는 중입니다.`;
    }
    return `raw 결과를 트래커 작업 형식으로 정리하는 중입니다. 예상 ${context.estimatedRows}건 기준으로 계속 반영합니다.`;
  }

  function normalizeTrackerExecutionContextFallback(payload = {}) {
    const summaryOutput =
      payload.summaryOutput && typeof payload.summaryOutput === "object" && !Array.isArray(payload.summaryOutput)
        ? payload.summaryOutput
        : {};
    const estimatedRows = numericSummaryValueFallback([
      summaryOutput.estimated_tracker_entry_rows,
      summaryOutput.auto_tracker_export_estimated_rows,
      summaryOutput.tracker_candidate_rows,
      summaryOutput.winner_csv_rows,
      summaryOutput.tracker_entry_rows,
    ]);
    const trackerEntryRows = numericSummaryValueFallback([
      summaryOutput.tracker_entry_rows,
      summaryOutput.auto_tracker_export_tracker_entry_rows,
    ]);
    return {
      title: payload.title,
      status: String(payload.status || "queued").trim() || "queued",
      progressStage: String(payload.progressStage || "").trim() || "waiting",
      progressCurrent: numericSummaryValueFallback([payload.progressCurrent]),
      progressTotal: Math.max(1, numericSummaryValueFallback([payload.progressTotal, 2])),
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

  function resolveTrackerExecutionContextFallback(run, context = {}) {
    const { isProjectTrackerRun = () => false } = context;
    if (!run) {
      return null;
    }
    if (run.run_type === "tracker_export") {
      return normalizeTrackerExecutionContextFallback({
        title: "트래커 복기 진행",
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
    const childRun = Array.isArray(run.child_runs)
      ? run.child_runs.find((item) => item?.run_type === "tracker_export")
      : null;
    return normalizeTrackerExecutionContextFallback({
      title: "트래커 실행",
      status: childRun?.status || run.status,
      progressStage: childRun?.progress_stage || "waiting",
      progressCurrent: childRun?.progress_current,
      progressTotal: childRun?.progress_total,
      childRunId: childRun?.id || "",
      parentRunId: run.id,
      summaryOutput: ((childRun?.summary || {}).output || {}),
      errorMessage: ((childRun?.error || {}).message || ""),
    });
  }

  globalObject.SPMSRunPanelsFallbackRuntime = {
    handleRunFormResetFallback,
    buildRunPayloadFallback,
    createWinnerRunFallback,
    numericSummaryValueFallback,
    trackerExportStageLabelFallback,
    trackerExecutionToneFallback,
    trackerExecutionMessageFallback,
    normalizeTrackerExecutionContextFallback,
    resolveTrackerExecutionContextFallback,
  };
})(typeof window !== "undefined" ? window : globalThis);
