export function createReportPanelsController(deps = {}) {
  const {
    state,
    dom,
    api,
    flash,
    setBusy,
    escapeHtml,
    formatDate,
    formatJson,
    formatBytes,
    statusBadge,
    ARTIFACT_RUNTIME,
    RELATED_NOTICE_RUNTIME,
    loadDashboardSummary,
    touchSyncMeta,
    syncUrlState,
    callRunPanelsController,
  } = deps;

  function resolveReportKey() {
    return state.reportKey || dom.reportSelect?.value || "phase1-artifact-diff";
  }

  function reportKeyLabel(reportKey) {
    if (reportKey === "phase1-equivalence") {
      return "동등성 검증";
    }
    return "산출물 비교 검증";
  }

  function formatNoticeViewerSourceLabel(value) {
    return RELATED_NOTICE_RUNTIME?.formatNoticeViewerSourceLabel?.(value) || "공고문";
  }

  function renderNoticeViewerWindow(targetWindow, { title = "공고문", meta = "", body = "" } = {}) {
    if (!targetWindow || targetWindow.closed) {
      return;
    }
    targetWindow.document.open();
    targetWindow.document.write(RELATED_NOTICE_RUNTIME?.buildNoticeViewerHtml(
      { title, meta, body },
      { escapeHtml },
    ) || "");
    targetWindow.document.close();
  }

  function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = "공고문") {
    if (!viewerWindow || viewerWindow.closed) {
      return;
    }
    const documentsMarkup = RELATED_NOTICE_RUNTIME?.buildNoticeViewerDocumentsMarkup(payload, {
      escapeHtml,
      formatNoticeViewerSourceLabel,
    }) || '<p class="notice-viewer-state">공고문 본문을 읽지 못했습니다.</p>';
    renderNoticeViewerWindow(viewerWindow, {
      title: payload.title || fallbackTitle,
      meta: [
        payload.project_name || "",
        payload.bid_no ? `${payload.bid_no}${payload.bid_ord ? ` / ${payload.bid_ord}` : ""}` : "",
        payload.document_count ? `문서 ${payload.document_count}건` : "",
      ]
        .filter(Boolean)
        .join(" | "),
      body: documentsMarkup,
    });
  }

  function renderNoticeViewerError(viewerWindow, { title = "공고문", errorMessage = "", links = [] } = {}) {
    if (!viewerWindow || viewerWindow.closed) {
      return;
    }
    renderNoticeViewerWindow(viewerWindow, {
      title,
      body: `
        <p class="notice-viewer-state">공고문을 불러오지 못했습니다.</p>
        <p class="notice-viewer-error">${escapeHtml(errorMessage || "viewer load failed")}</p>
      `,
    });
  }

  function renderReport(report, errorMessage = "") {
    if (!report) {
      dom.reportStatus.textContent = errorMessage
        ? `검증 리포트를 불러오지 못했습니다: ${errorMessage}`
        : "아직 검증 리포트를 불러오지 않았습니다.";
      dom.reportSummary.textContent = "{}";
      dom.reportJson.textContent = "{}";
      return;
    }
    const summary = report.summary || {};
    const reportLabel = reportKeyLabel(state.reportKey);
    const summaryLine = [
      reportLabel,
      `일치 ${summary.matched_count ?? summary.passed ?? 0}`,
      `불일치 ${summary.mismatched_count ?? summary.failed ?? 0}`,
      `전체 일치 ${summary.all_match ?? "-"}`,
    ].join(" | ");
    dom.reportStatus.textContent = summaryLine;
    dom.reportSummary.textContent = formatJson(summary);
    dom.reportJson.textContent = formatJson(report);
  }

  function renderReportJobs(items) {
    if (!items.length) {
      dom.reportJobsList.innerHTML = '<div class="empty-state">불러온 검증 작업이 없습니다.</div>';
      return;
    }
    dom.reportJobsList.innerHTML = items
      .map(
        (job) => `
          <article class="log-item${job.id === state.selectedReportJobId ? " is-selected" : ""}" data-report-job-id="${escapeHtml(job.id)}">
            <div class="artifact-head">
              <strong>${escapeHtml(reportKeyLabel(job.report_name))}</strong>
              ${statusBadge(job.status)}
            </div>
          <p class="mono">${escapeHtml(job.id)}</p>
          <p>${escapeHtml(formatDate(job.finished_at || job.started_at || job.created_at))}</p>
        </article>
      `,
      )
      .join("");
    for (const item of dom.reportJobsList.querySelectorAll("[data-report-job-id]")) {
      item.addEventListener("click", () => {
        const nextId = item.getAttribute("data-report-job-id");
        const selected = state.reportJobs.find((job) => job.id === nextId) || null;
        state.selectedReportJobId = nextId;
        state.reportJob = selected;
        renderReportJobs(state.reportJobs);
        renderReportJob(selected);
        syncUrlState();
        if (selected && selected.status === "success") {
          loadPhaseReport({ silent: true });
        }
      });
    }
  }

  function renderReportJob(job, errorMessage = "") {
    if (!job) {
      dom.reportJobStatus.textContent = errorMessage
        ? `검증 작업을 불러오지 못했습니다: ${errorMessage}`
        : "아직 시작한 검증 작업이 없습니다.";
      dom.reportJobDetail.textContent = "{}";
      return;
    }
    const summary = job.summary || {};
    const statusBits = [
      reportKeyLabel(job.report_name),
      job.status,
      job.exit_code ?? "-",
      summary.all_match === true
        ? "전체 일치 예"
        : summary.all_match === false
          ? "전체 일치 아니오"
          : `통과 ${summary.passed ?? "-"}`,
    ];
    dom.reportJobStatus.textContent = statusBits.join(" | ");
    dom.reportJobDetail.textContent = formatJson(job);
  }

  async function loadPhaseReport({ silent = false } = {}) {
    const reportKey = resolveReportKey();
    state.reportKey = reportKey;
    if (dom.reportSelect) {
      dom.reportSelect.value = reportKey;
    }
    try {
      const response = await api(`/api/reports/${encodeURIComponent(reportKey)}`);
      state.reportData = response;
      renderReport(response);
      touchSyncMeta(`report synced ${new Date().toLocaleTimeString()}`);
    } catch (err) {
      state.reportData = null;
      renderReport(null, err.message);
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  async function loadReportJobs({ silent = false } = {}) {
    const reportKey = resolveReportKey();
    try {
      const response = await api(`/api/report-jobs?report_name=${encodeURIComponent(reportKey)}&limit=5`);
      const items = response.items || [];
      state.reportJobs = items;
      if (!items.length) {
        state.reportJob = null;
        state.selectedReportJobId = null;
        renderReportJobs([]);
        renderReportJob(null);
        syncUrlState();
        return;
      }
      const selected =
        items.find((item) => item.id === state.selectedReportJobId) ||
        items[0];
      state.selectedReportJobId = selected.id;
      state.reportJob = selected;
      renderReportJobs(items);
      renderReportJob(selected);
      syncUrlState();
      touchSyncMeta(`report jobs synced ${new Date().toLocaleTimeString()}`);
      if (selected.status === "success") {
        void loadPhaseReport({ silent: true });
      }
    } catch (err) {
      state.reportJobs = [];
      state.reportJob = null;
      state.selectedReportJobId = null;
      renderReportJobs([]);
      renderReportJob(null, err.message);
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  async function runSelectedReport() {
    const reportKey = resolveReportKey();
    const payload = {
      report_name: reportKey,
      seed_limit: Number(dom.reportSeedLimit?.value || 3),
    };
    setBusy(dom.runReportButton, true, "검증 실행 중...");
    try {
      const response = await api("/api/report-jobs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      state.reportJobs = [response, ...state.reportJobs.filter((item) => item.id !== response.id)].slice(0, 5);
      state.selectedReportJobId = response.id;
      state.reportJob = response;
      renderReportJobs(state.reportJobs);
      renderReportJob(response);
      flash(`검증 작업 등록: ${response.id}`);
      await Promise.all([
        loadDashboardSummary({ silent: true }),
        loadReportJobs({ silent: true }),
      ]);
    } catch (err) {
      flash(err.message, "error");
    } finally {
      setBusy(dom.runReportButton, false, "검증 실행");
    }
  }

  async function refreshReportPanels() {
    await Promise.all([
      loadPhaseReport({}),
      loadReportJobs({ silent: true }),
    ]);
  }

  function buildArtifactEmptyMessage() {
    const artifactBackend = ((state.dashboard || {}).repository_backends || {}).artifacts || "unknown";
    const persistent = Boolean((state.dashboard || {}).artifact_metadata_persistent);
    const run = state.selectedRun;
    return ARTIFACT_RUNTIME?.buildArtifactEmptyMessage?.({
      artifactBackend,
      persistent,
      runStatus: run?.status,
    }) || `No artifacts generated for this run. backend=${artifactBackend}`;
  }

  function artifactTypeLabel(artifactType) {
    return ARTIFACT_RUNTIME?.artifactTypeLabel(artifactType) || artifactType;
  }

  function buildArtifactMetaBits(item) {
    return ARTIFACT_RUNTIME?.buildArtifactMetaBits(item, { formatBytes }) || "";
  }

  function canPreviewArtifact(item) {
    return ARTIFACT_RUNTIME?.canPreviewArtifact?.(item) || false;
  }

  function renderArtifactPreviewMarkup(artifactId) {
    const cached = state.artifactPreviewCache[artifactId];
    return ARTIFACT_RUNTIME?.buildArtifactPreviewMarkup?.(cached, {
      escapeHtml,
      formatJson,
    }) || '<div class="artifact-preview"><div class="empty-state">미리보기를 표시할 수 없습니다.</div></div>';
  }

  function syncReportSelectFromState() {
    if (!dom.reportSelect) {
      return;
    }
    dom.reportSelect.value = state.reportKey;
  }

  function renderArtifactCardMarkup(item, options = {}, helpers = {}) {
    const {
      openArtifactId = "",
      previewMarkup = "",
    } = options;
    const {
      escapeHtml: escapeHtmlHelper = (value) => String(value || ""),
      artifactTypeLabel: resolveArtifactTypeLabel = artifactTypeLabel,
      buildArtifactMetaBits: resolveMetaBits = buildArtifactMetaBits,
      canPreviewArtifact: previewable = canPreviewArtifact,
    } = helpers;
    const metaBits = resolveMetaBits(item, helpers);
    const showPreview = previewable(item);
    const previewButton = showPreview
      ? `<button class="ghost-button artifact-preview-button" type="button" data-preview-artifact-id="${escapeHtmlHelper(item.id)}">${item.id === openArtifactId ? "미리보기 닫기" : "미리보기"}</button>`
      : "";
    return `
      <article class="artifact-item">
        <div class="artifact-head">
          <div>
            <strong>${escapeHtmlHelper(resolveArtifactTypeLabel(item.artifact_type))}</strong>
            <p class="mono">${escapeHtmlHelper(item.file_name)}</p>
          </div>
          <span class="mono">${escapeHtmlHelper(String(item.meta?.rows || 0))} rows</span>
        </div>
        <p>${escapeHtmlHelper(item.mime_type)}</p>
        ${metaBits ? `<p class="mono artifact-meta-line">${escapeHtmlHelper(metaBits)}</p>` : ""}
        <div class="artifact-actions">
          ${previewButton}
          <a class="artifact-link" href="${escapeHtmlHelper(item.download_url)}">다운로드</a>
        </div>
        ${previewMarkup}
      </article>
    `;
  }

  function buildArtifactSectionMarkup(section) {
    return ARTIFACT_RUNTIME?.buildArtifactSectionMarkup?.(
      section,
      {
        openArtifactId: state.openArtifactId,
        renderPreview: (item) => renderArtifactPreviewMarkup(item.id),
        renderCard: (item, options, helpers) => renderArtifactCardMarkup(item, options, helpers),
      },
      {
        escapeHtml,
        artifactTypeLabel,
        buildArtifactMetaBits: (item) => buildArtifactMetaBits(item),
        canPreviewArtifact,
      },
    ) || "";
  }

  async function toggleArtifactPreview(artifactId) {
    if (!artifactId) {
      return;
    }
    if (state.openArtifactId === artifactId) {
      state.openArtifactId = null;
      renderArtifactsList();
      return;
    }
    state.openArtifactId = artifactId;
    renderArtifactsList();
    if (!state.artifactPreviewCache[artifactId]) {
      const item = state.artifacts.find((artifact) => artifact.id === artifactId);
      if (!item) {
        return;
      }
      await callRunPanelsController("ensureArtifactPreviewCached", item);
    }
  }

  function renderArtifactsList() {
    if (!state.artifactSections.length || !state.artifacts.length) {
      dom.artifactsList.innerHTML = `<div class="empty-state">${escapeHtml(buildArtifactEmptyMessage())}</div>`;
      return;
    }
    dom.artifactsList.innerHTML = state.artifactSections
      .map((section) => buildArtifactSectionMarkup(section))
      .join("");
    for (const button of dom.artifactsList.querySelectorAll("[data-preview-artifact-id]")) {
      button.addEventListener("click", () => toggleArtifactPreview(button.getAttribute("data-preview-artifact-id")));
    }
  }

  return {
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
    renderArtifactPreviewMarkup,
    buildArtifactEmptyMessage,
    syncReportSelectFromState,
  };
}

const reportPanelsControllerRoot = typeof window !== "undefined" ? window : globalThis;
reportPanelsControllerRoot.REPORT_PANELS_CONTROLLER = reportPanelsControllerRoot.REPORT_PANELS_CONTROLLER || {};
reportPanelsControllerRoot.REPORT_PANELS_CONTROLLER.createReportPanelsController = createReportPanelsController;
