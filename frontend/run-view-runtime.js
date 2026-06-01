(function attachRunViewRuntime(global) {
  function runTypeLabel(runType, labels = null) {
    const raw = String(runType || "").trim();
    if (labels && typeof labels === "object" && !Array.isArray(labels) && labels[raw]) {
      return labels[raw];
    }
    return raw || "-";
  }

  function buildRunCardMarkup(run, options = {}, helpers = {}) {
    const {
      selectedRunId = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      runTypeLabel: typeLabel = (value) => String(value || "-"),
      statusBadge = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
    } = helpers;
    const selectedClass = run.id === selectedRunId ? " is-selected" : "";
    const parentLine = run.parent_run_id
      ? `<p class="mono">parent ${escapeHtml(run.parent_run_id)}</p>`
      : "";
    return `
      <article class="run-card${selectedClass}" data-run-id="${escapeHtml(run.id)}">
        <div class="run-card-head">
          <div>
            <strong>${escapeHtml(typeLabel(run.run_type))}</strong>
            <p class="mono">${escapeHtml(run.id)}</p>
          </div>
          ${statusBadge(run.status)}
        </div>
        <p>stage ${escapeHtml(run.progress_stage || "-")}</p>
        ${parentLine}
        <p>created ${escapeHtml(formatDate(run.created_at))}</p>
      </article>
    `;
  }

  function buildRunsListMarkup(runs, options = {}, helpers = {}) {
    return (runs || []).map((run) => buildRunCardMarkup(run, options, helpers)).join("");
  }

  function buildRunsPageMeta(page, totalPages, totalRuns) {
    return `Page ${page} / ${totalPages} | ${totalRuns} run(s)`;
  }

  function buildRunDetailViewModel(run, helpers = {}) {
    if (!run) {
      return null;
    }
    const {
      runTypeLabel: typeLabel = (value) => String(value || "-"),
      formatDate = (value) => String(value || "-"),
      formatJson = (value) => {
        if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
          return "{}";
        }
        return JSON.stringify(value, null, 2);
      },
      progressPercent = () => 0,
    } = helpers;
    const jsonText = (value) => {
      if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
        return formatJson({});
      }
      return formatJson(value);
    };

    const progressCurrent = Number(run.progress_current || 0);
    const progressTotal = Number(run.progress_total || 0);
    const progressText = `${progressCurrent} / ${progressTotal}`;

    return {
      id: String(run.id || ""),
      status: String(run.status || ""),
      runTypeLabel: typeLabel(run.run_type),
      progressText,
      progressStage: String(run.progress_stage || "waiting"),
      progressPercent: Number(progressPercent(run) || 0),
      paramsText: jsonText(run.params),
      summaryText: jsonText(run.summary),
      errorText: jsonText(run.error),
      createdAtText: formatDate(run.created_at),
      startedAtText: formatDate(run.started_at),
      finishedAtText: formatDate(run.finished_at),
      parentRunId: String(run.parent_run_id || "-"),
    };
  }

  function buildRunLogItemMarkup(item, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
    } = helpers;
    return `
      <article class="log-item">
        <div class="artifact-head">
          <strong>${escapeHtml(item.level)}</strong>
          <span class="mono">#${item.id}</span>
        </div>
        <p>${escapeHtml(item.stage || "-")} :: ${escapeHtml(item.message)}</p>
        <p class="mono">${escapeHtml(formatDate(item.created_at))}</p>
      </article>
    `;
  }

  function buildRunLogsMarkup(items, helpers = {}) {
    return (items || []).map((item) => buildRunLogItemMarkup(item, helpers)).join("");
  }

  function buildRunPresetPanelMarkup() {
    return `
      <div class="runtime-card-head">
        <div>
          <strong>실행 프리셋</strong>
          <p class="kicker">자주 쓰는 검색 조건 저장</p>
        </div>
        <button id="preset-refresh-button" class="ghost-button" type="button">새로고침</button>
      </div>
      <div class="runtime-toolbar">
        <select id="preset-select">
          <option value="">저장된 프리셋 없음</option>
        </select>
        <button id="preset-apply-button" class="ghost-button" type="button">적용</button>
        <button id="preset-save-button" class="ghost-button" type="button">현재 조건 저장</button>
      </div>
      <p id="preset-status" class="hint-text">프리셋을 불러오는 중입니다.</p>
    `;
  }

  function buildRunPresetOptionsMarkup(runPresets, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;
    return ['<option value="">프리셋 선택</option>']
      .concat(
        (runPresets || []).map(
          (item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`,
        ),
      )
      .join("");
  }

  function buildRunPresetStatusText(runPresets, errorMessage = "") {
    if (errorMessage) {
      return `프리셋을 불러오지 못했습니다: ${errorMessage}`;
    }
    return (runPresets || []).length
      ? `최근 프리셋 ${(runPresets || []).length}개`
      : "저장된 프리셋이 없습니다.";
  }

  function numericSummaryValue(...values) {
    for (const value of values) {
      const parsed = Number(value || 0);
      if (Number.isFinite(parsed) && parsed >= 0) {
        return parsed;
      }
    }
    return 0;
  }

  function trackerExportStageLabel(stage) {
    const labels = {
      waiting: "연결 대기",
      tracker_export: "트래커 행 정리",
      finalize: "워크북 생성",
    };
    return labels[String(stage || "").trim()] || String(stage || "waiting");
  }

  function trackerExecutionTone(status) {
    if (status === "success") {
      return "ok";
    }
    if (status === "failed" || status === "cancelled") {
      return "warn";
    }
    return "";
  }

  function trackerExecutionMessage(context) {
    if (!context) {
      return "";
    }
    if (context.status === "success") {
      return `트래커 엑셀 ${context.trackerEntryRows}건을 준비했습니다. 완료 즉시 워크북을 같은 화면에 열어 둡니다.`;
    }
    if (context.status === "failed") {
      return "트래커 내보내기에 실패했습니다. 오류 내용을 확인한 뒤 다시 실행할 수 있습니다.";
    }
    if (context.status === "cancelled") {
      return "트래커 내보내기가 취소되었습니다.";
    }
    if (context.progressStage === "finalize") {
      return `행 ${context.trackerEntryRows || context.estimatedRows}건을 엑셀 워크북으로 정리하는 중입니다.`;
    }
    return `raw 결과를 트래커 양식으로 정리하는 중입니다. 예상 ${context.estimatedRows}건 기준으로 계속 반영됩니다.`;
  }

  function normalizeTrackerExecutionContext(payload = {}) {
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

  function buildTrackerExecutionDetailBits(context) {
    return [
      context?.childRunId ? `연결 실행 ${context.childRunId}` : "",
      context?.fileName ? `파일 ${context.fileName}` : "",
      context?.backend ? `backend ${context.backend}` : "",
    ].filter(Boolean);
  }

  function buildRunExecutionContextMarkup(context, options = {}, helpers = {}) {
    const {
      previewMarkup = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      statusBadge = (value) => String(value || ""),
      progressPercent = () => 0,
      metricCard = () => "",
      trackerExportStageLabel: stageLabel = trackerExportStageLabel,
      trackerExecutionMessage: executionMessage = trackerExecutionMessage,
      buildTrackerExecutionDetailBits: detailBuilder = buildTrackerExecutionDetailBits,
    } = helpers;
    const metrics = [
      metricCard("상태", context?.status || "-"),
      metricCard("현재 단계", stageLabel(context?.progressStage || "waiting")),
      metricCard("예상 row 수", context?.estimatedRows || 0),
      metricCard("확정 row 수", context?.trackerEntryRows || 0),
    ].join("");
    const detailBits = detailBuilder(context);
    return `
      <div class="runtime-card-head">
        <div>
          <strong>${escapeHtml(context?.title || "-")}</strong>
          <p>${escapeHtml(executionMessage(context))}</p>
        </div>
        ${statusBadge(context?.status || "queued")}
      </div>
      <div class="metric-grid tracker-execution-metric-grid">${metrics}</div>
      <div class="progress-block tracker-execution-progress">
        <div class="progress-head">
          <span>${escapeHtml(stageLabel(context?.progressStage || "waiting"))}</span>
          <span>${escapeHtml(`${context?.progressCurrent || 0} / ${context?.progressTotal || 1}`)}</span>
        </div>
        <div class="progress-track">
          <div class="progress-bar" style="width:${progressPercent({ progress_current: context?.progressCurrent, progress_total: context?.progressTotal })}%"></div>
        </div>
      </div>
      ${detailBits.length ? `<div class="runtime-strip-compact mono">${detailBits.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
      ${context?.errorMessage ? `<div class="empty-state">오류: ${escapeHtml(context.errorMessage)}</div>` : ""}
      ${previewMarkup}
    `;
  }

  global.SPMSRunViewRuntime = {
    runTypeLabel,
    buildRunCardMarkup,
    buildRunsListMarkup,
    buildRunsPageMeta,
    buildRunDetailViewModel,
    buildRunLogItemMarkup,
    buildRunLogsMarkup,
    buildRunPresetPanelMarkup,
    buildRunPresetOptionsMarkup,
    buildRunPresetStatusText,
    numericSummaryValue,
    trackerExportStageLabel,
    trackerExecutionTone,
    trackerExecutionMessage,
    normalizeTrackerExecutionContext,
    buildTrackerExecutionDetailBits,
    buildRunExecutionContextMarkup,
  };
})(window);
