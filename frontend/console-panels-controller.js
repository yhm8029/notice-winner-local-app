function isOutOfRangePageError(error) {
  const message = String(error && error.message ? error.message : error || "").toLowerCase();
  return message.includes("requested range not satisfiable") || message.includes("offset of");
}

function extractOutOfRangeTotalRows(error) {
  const message = String(error && error.message ? error.message : error || "");
  const match = message.match(/there are only\s+(\d+)\s+rows/i);
  return match ? Number(match[1]) || 0 : 0;
}

function handleOutOfRangePageErrorImpl(deps, error, filterState, scopeLabel) {
  if (!isOutOfRangePageError(error) || !filterState || Number(filterState.page || 1) <= 1) {
    return false;
  }
  const totalRows = extractOutOfRangeTotalRows(error);
  const pageSize = Math.max(1, Number(filterState.pageSize || 20));
  const fallbackPage = totalRows > 0 ? Math.max(1, Math.ceil(totalRows / pageSize)) : 1;
  filterState.page = fallbackPage;
  deps.flash?.(`${scopeLabel} 紐⑸줉 ?섏씠吏瑜?${fallbackPage}濡?蹂댁젙?덉뒿?덈떎.`, "warn");
  return true;
}

export function createConsolePanelsController(deps = {}) {
  const {
    dom,
    state,
    escapeHtml,
    formatDate,
    runTypeLabel,
    statusBadge,
    metricCard,
    PROJECT_RUNTIME,
    RUN_VIEW_RUNTIME,
    renderArtifactPreviewMarkup,
    resolveTrackerExecutionContext,
    trackerExecutionTone,
    trackerExecutionMessage,
    progressPercent,
    trackerExportStageLabel,
    openProjectNoticeViewer,
    applyPresetParams,
    api,
    syncUrlState,
    syncCollectModeOptions,
    touchSyncMeta,
    flash,
  } = deps;
  const controller = {};

  function renderDashboard(summary, errorMessage = "") {
    if (!summary) {
      dom.dashboardMetrics.innerHTML = `
      <article class="metric-card">
        <span class="detail-label">Dashboard</span>
        <strong>${escapeHtml(errorMessage || "unavailable")}</strong>
      </article>
    `;
      dom.dashboardFailedRuns.innerHTML = '<div class="empty-state">No dashboard data.</div>';
      dom.dashboardReportJobs.innerHTML = '<div class="empty-state">No dashboard data.</div>';
      return;
    }

    const runCounts = summary.run_counts || {};
    const totalRuns = Object.values(runCounts).reduce((sum, value) => sum + Number(value || 0), 0);
    const latestArtifact = (((summary.latest_reports || {})["phase1-artifact-diff"] || {}).summary || {});
    const latestEquivalence = (((summary.latest_reports || {})["phase1-equivalence"] || {}).summary || {});
    const repositoryBackends = summary.repository_backends || {};
    const artifactBackend = repositoryBackends.artifacts || "-";

    dom.dashboardMetrics.innerHTML = [
      metricCard("Runs", totalRuns),
      metricCard("Running", runCounts.running || 0),
      metricCard("Failed", runCounts.failed || 0),
      metricCard("Tracker Rows", summary.tracker_total || 0),
      metricCard("Edited Rows", summary.tracker_edited_total || 0),
      metricCard("Artifacts", summary.artifact_metadata_persistent ? `persistent (${artifactBackend})` : `ephemeral (${artifactBackend})`),
      metricCard("Artifact Match", latestArtifact.all_match === true ? "yes" : latestArtifact.all_match === false ? "no" : "-"),
      metricCard("Equivalence Passed", latestEquivalence.passed ?? "-"),
    ].join("");

    const failedRuns = summary.recent_failed_runs || [];
    if (!failedRuns.length) {
      dom.dashboardFailedRuns.innerHTML = '<div class="empty-state">No failed runs.</div>';
    } else {
      dom.dashboardFailedRuns.innerHTML = failedRuns
        .map(
          (run) => `
          <article class="log-item">
            <div class="artifact-head">
              <strong>${escapeHtml(runTypeLabel(run.run_type))}</strong>
              ${statusBadge(run.status)}
            </div>
            <p class="mono">${escapeHtml(run.id)}</p>
            <p>${escapeHtml(run.progress_stage || "-")} | ${escapeHtml(formatDate(run.created_at))}</p>
          </article>
        `
        )
        .join("");
    }

    const activeJobs = summary.active_report_jobs || [];
    if (!activeJobs.length) {
      dom.dashboardReportJobs.innerHTML = '<div class="empty-state">No active report jobs.</div>';
    } else {
      dom.dashboardReportJobs.innerHTML = activeJobs
        .map(
          (job) => `
          <article class="log-item">
            <div class="artifact-head">
              <strong>${escapeHtml(job.report_name)}</strong>
              ${statusBadge(job.status)}
            </div>
            <p class="mono">${escapeHtml(job.id)}</p>
            <p>${escapeHtml(formatDate(job.started_at || job.created_at))}</p>
          </article>
        `
        )
        .join("");
    }
  }

  function renderRunExecutionContext(run) {
    if (!dom.runExecutionContext) {
      return;
    }
    const context = resolveTrackerExecutionContext(run);
    if (!context) {
      dom.runExecutionContext.classList.add("hidden");
      dom.runExecutionContext.innerHTML = "";
      return;
    }
    const tone = trackerExecutionTone(context.status);
    const previewArtifact = state.artifacts.find((item) => item.id === state.selectedTrackerWorkbookArtifactId) || null;
    const downloadMarkup = previewArtifact
      ? `
      <div class="artifact-actions">
        <a class="artifact-link" href="${escapeHtml(previewArtifact.download_url)}">?몃옒而??묒? ?ㅼ슫濡쒕뱶</a>
      </div>
    `
      : "";
    let previewMarkup = "";
    if (context.status === "success") {
      if (state.selectedTrackerWorkbookArtifactId) {
        previewMarkup = `
        <div class="tracker-export-inline-preview">
          <div class="runtime-card-head">
            <div>
              <strong>?뚰겕遺?誘몃━蹂닿린</strong>
              <p>?꾨즺 利됱떆 媛숈? ?붾㈃?먯꽌 寃곌낵瑜??뺤씤?⑸땲??</p>
            </div>
          </div>
          ${renderArtifactPreviewMarkup(state.selectedTrackerWorkbookArtifactId)}
          ${downloadMarkup}
        </div>
      `;
      } else {
        previewMarkup = '<div class="empty-state">tracking_excel ?곗텧臾?硫뷀??곗씠?곕? ?뺤씤?섎뒗 以묒엯?덈떎.</div>';
      }
    }
    dom.runExecutionContext.className = "runtime-card tracker-execution-context";
    dom.runExecutionContext.dataset.tone = tone;
    dom.runExecutionContext.innerHTML = RUN_VIEW_RUNTIME?.buildRunExecutionContextMarkup(
      context,
      { previewMarkup },
      {
        escapeHtml,
        statusBadge,
        progressPercent,
        metricCard,
        trackerExportStageLabel,
        trackerExecutionMessage,
        buildTrackerExecutionDetailBits: (value) => RUN_VIEW_RUNTIME?.buildTrackerExecutionDetailBits?.(value) || [],
      },
    ) || `
    <div class="runtime-card-head">
      <div>
        <strong>${escapeHtml(context.title)}</strong>
        <p>${escapeHtml(trackerExecutionMessage(context))}</p>
      </div>
      ${statusBadge(context.status || "queued")}
    </div>
    <div class="metric-grid tracker-execution-metric-grid">
      ${metricCard("?곹깭", context.status || "-")}
      ${metricCard("?꾩옱 ?④퀎", trackerExportStageLabel(context.progressStage || "waiting"))}
      ${metricCard("?덉긽 row ??, context.estimatedRows)}
      ${metricCard("?뺤젙 row ??, context.trackerEntryRows)}
    </div>
    <div class="progress-block tracker-execution-progress">
      <div class="progress-head">
        <span>${escapeHtml(trackerExportStageLabel(context.progressStage || "waiting"))}</span>
        <span>${escapeHtml(`${context.progressCurrent} / ${context.progressTotal}`)}</span>
      </div>
      <div class="progress-track">
        <div class="progress-bar" style="width:${progressPercent({ progress_current: context.progressCurrent, progress_total: context.progressTotal })}%"></div>
      </div>
    </div>
    ${context.errorMessage ? `<div class="empty-state">?ㅻ쪟: ${escapeHtml(context.errorMessage)}</div>` : ""}
    ${previewMarkup}
  `;
    dom.runExecutionContext.classList.remove("hidden");
  }

  function renderProjects(errorMessage = "") {
    if (!dom.projectList || !dom.projectPageMeta || !dom.projectPrevButton || !dom.projectNextButton) {
      return;
    }
    const totalPages = Math.max(1, Math.ceil(state.projectsTotal / state.projectFilters.pageSize));
    dom.projectPageMeta.textContent = PROJECT_RUNTIME?.buildProjectPageMeta(
      state.projectFilters.page,
      totalPages,
      state.projectsTotal,
    ) || `Page ${state.projectFilters.page} / ${totalPages} | ${state.projectsTotal} project(s)`;
    dom.projectPrevButton.disabled = state.projectFilters.page <= 1;
    dom.projectNextButton.disabled = state.projectFilters.page >= totalPages;
    if (errorMessage) {
      dom.projectList.innerHTML = `<div class="empty-state">?꾨줈?앺듃瑜?遺덈윭?ㅼ? 紐삵뻽?듬땲?? ${escapeHtml(errorMessage)}</div>`;
      return;
    }
    if (!state.projects.length) {
      dom.projectList.innerHTML = '<div class="empty-state">吏묎퀎???꾨줈?앺듃媛 ?놁뒿?덈떎.</div>';
      return;
    }
    dom.projectList.innerHTML = PROJECT_RUNTIME?.buildProjectListMarkup(
      state.projects,
      {
        projectOpenId: state.projectOpenId,
      },
      {
        escapeHtml,
      },
    ) || "";
    for (const button of dom.projectList.querySelectorAll("[data-project-notice-view]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-project-notice-view");
        const project = state.projects.find((item) => item.id === projectId);
        if (!project) {
          flash("?먭났怨??뺣낫瑜?李얠? 紐삵뻽?듬땲??", "warn");
          return;
        }
        void openProjectNoticeViewer(project);
      });
    }
    for (const button of dom.projectList.querySelectorAll("[data-project-apply]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-project-apply");
        const project = state.projects.find((item) => item.id === projectId);
        if (!project) {
          return;
        }
        applyPresetParams({
          notice_title: project.project_search_name || project.latest_notice_title || project.project_name || "",
          demand_org: project.issuer_name || "",
          bid_no: "",
        });
        flash(`?꾨줈?앺듃 議곌굔 ?곸슜: ${project.project_name}`);
      });
    }
  }

  controller.handleOutOfRangePageError = function handleOutOfRangePageError(error, filterState, scopeLabel) {
    return handleOutOfRangePageErrorImpl(deps, error, filterState, scopeLabel);
  };

  controller.isOutOfRangePageError = function isOutOfRangePageErrorPublic(error) {
    return isOutOfRangePageError(error);
  };

  controller.extractOutOfRangeTotalRows = function extractOutOfRangeTotalRowsPublic(error) {
    return extractOutOfRangeTotalRows(error);
  };

  async function loadDashboardSummary({ silent = false } = {}) {
    try {
      const response = await api("/api/dashboard/summary");
      state.dashboard = response;
      syncCollectModeOptions();
      renderDashboard(response);
      touchSyncMeta(`dashboard synced ${new Date().toLocaleTimeString()}`);
    } catch (err) {
      state.dashboard = null;
      syncCollectModeOptions();
      renderDashboard(null, err.message);
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  async function loadProjects({ silent = false } = {}) {
    if (dom.projectQuery) {
      state.projectFilters.q = dom.projectQuery.value.trim();
      dom.projectQuery.value = state.projectFilters.q;
    }
    const params = new URLSearchParams({
      page: String(state.projectFilters.page),
      page_size: String(state.projectFilters.pageSize),
    });
    if (state.projectFilters.q) {
      params.set("q", state.projectFilters.q);
    }
    try {
      const response = await api(`/api/projects?${params.toString()}`);
      state.projects = response.items || [];
      state.projectsTotal = response.total || 0;
      renderProjects();
      touchSyncMeta(`projects synced ${new Date().toLocaleTimeString()}`);
    } catch (err) {
      if (controller.handleOutOfRangePageError?.(err, state.projectFilters, "?꾨줈?앺듃")) {
        syncUrlState();
        void loadProjects({ silent });
        return;
      }
      state.projects = [];
      state.projectsTotal = 0;
      renderProjects(err.message);
      if (!silent) {
        flash(err.message, "error");
      }
    }
  }

  function changeProjectsPage(delta) {
    const totalPages = Math.max(1, Math.ceil(state.projectsTotal / state.projectFilters.pageSize));
    const nextPage = Math.min(totalPages, Math.max(1, state.projectFilters.page + delta));
    if (nextPage === state.projectFilters.page) {
      return;
    }
    state.projectFilters.page = nextPage;
    void loadProjects({ silent: true });
  }

  return {
    handleOutOfRangePageError: controller.handleOutOfRangePageError,
    isOutOfRangePageError: controller.isOutOfRangePageError,
    extractOutOfRangeTotalRows: controller.extractOutOfRangeTotalRows,
    renderDashboard,
    loadDashboardSummary,
    renderRunExecutionContext,
    loadProjects,
    changeProjectsPage,
    renderProjects,
  };
}

const consolePanelsControllerRoot = typeof window !== "undefined" ? window : globalThis;
consolePanelsControllerRoot.CONSOLE_PANELS_CONTROLLER = consolePanelsControllerRoot.CONSOLE_PANELS_CONTROLLER || {};
consolePanelsControllerRoot.CONSOLE_PANELS_CONTROLLER.createConsolePanelsController = createConsolePanelsController;
