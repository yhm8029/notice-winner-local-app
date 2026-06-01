(function attachSPMSReportRuntime(globalObject) {
  function reportKeyLabel(reportKey) {
    if (reportKey === "phase1-equivalence") {
      return "동등성 검증";
    }
    return "산출물 비교 검증";
  }

  function buildReportUnavailableText(errorMessage = "") {
    return errorMessage
      ? `검증 리포트를 불러오지 못했습니다: ${errorMessage}`
      : "아직 검증 리포트를 불러오지 않았습니다.";
  }

  function buildReportStatusText(report, options = {}) {
    const summary = report?.summary || {};
    const labelBuilder =
      typeof options.reportKeyLabel === "function"
        ? options.reportKeyLabel
        : reportKeyLabel;
    return [
      labelBuilder(options.reportKey),
      `일치 ${summary.matched_count ?? summary.passed ?? 0}`,
      `불일치 ${summary.mismatched_count ?? summary.failed ?? 0}`,
      `전체 일치 ${summary.all_match ?? "-"}`,
    ].join(" | ");
  }

  function buildReportViewModel(report, options = {}, helpers = {}) {
    const { formatJson = (value) => JSON.stringify(value ?? {}) } = helpers;
    if (!report) {
      return {
        statusText: buildReportUnavailableText(options.errorMessage || ""),
        summaryText: "{}",
        reportText: "{}",
      };
    }
    const summary = report.summary || {};
    return {
      statusText: buildReportStatusText(report, options),
      summaryText: formatJson(summary),
      reportText: formatJson(report),
    };
  }

  function buildReportJobsEmptyMarkup() {
    return '<div class="empty-state">불러온 검증 작업이 없습니다.</div>';
  }

  function buildReportJobsMarkup(items, options = {}, helpers = {}) {
    const { selectedReportJobId = null } = options;
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      statusBadge = (status) => String(status ?? ""),
      reportKeyLabel: labelBuilder = reportKeyLabel,
    } = helpers;
    return (items || [])
      .map(
        (job) => `
          <article class="log-item${job.id === selectedReportJobId ? " is-selected" : ""}" data-report-job-id="${escapeHtml(job.id)}">
            <div class="artifact-head">
              <strong>${escapeHtml(labelBuilder(job.report_name))}</strong>
              ${statusBadge(job.status)}
            </div>
          <p class="mono">${escapeHtml(job.id)}</p>
          <p>${escapeHtml(formatDate(job.finished_at || job.started_at || job.created_at))}</p>
        </article>
      `
      )
      .join("");
  }

  function buildReportJobUnavailableText(errorMessage = "") {
    return errorMessage
      ? `검증 작업을 불러오지 못했습니다: ${errorMessage}`
      : "아직 시작한 검증 작업이 없습니다.";
  }

  function buildReportJobStatusText(job, options = {}) {
    const summary = job?.summary || {};
    const labelBuilder =
      typeof options.reportKeyLabel === "function"
        ? options.reportKeyLabel
        : reportKeyLabel;
    return [
      labelBuilder(job?.report_name),
      job?.status,
      job?.exit_code ?? "-",
      summary.all_match === true
        ? "전체 일치 예"
        : summary.all_match === false
          ? "전체 일치 아니오"
          : `통과 ${summary.passed ?? "-"}`,
    ].join(" | ");
  }

  function buildReportJobViewModel(job, options = {}, helpers = {}) {
    const { formatJson = (value) => JSON.stringify(value ?? {}) } = helpers;
    if (!job) {
      return {
        statusText: buildReportJobUnavailableText(options.errorMessage || ""),
        detailText: "{}",
      };
    }
    return {
      statusText: buildReportJobStatusText(job, options),
      detailText: formatJson(job),
    };
  }

  globalObject.SPMSReportRuntime = {
    reportKeyLabel,
    buildReportUnavailableText,
    buildReportStatusText,
    buildReportViewModel,
    buildReportJobsEmptyMarkup,
    buildReportJobsMarkup,
    buildReportJobUnavailableText,
    buildReportJobStatusText,
    buildReportJobViewModel,
  };
})(window);
