(function attachSPMSTrackerMissingReportRuntime(globalObject) {
  function buildMissingReportChipMarkup(label, count, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    return `
    <article class="missing-report-chip">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(count))}</strong>
    </article>
  `;
  }

  function buildMissingReportSummaryMarkup(summary = {}, helpers = {}) {
    return [
      buildMissingReportChipMarkup("전체 공고", summary.total_entries || 0, helpers),
      buildMissingReportChipMarkup("누락 공고", summary.missing_entries || 0, helpers),
      buildMissingReportChipMarkup("연락처 누락", summary.contact_missing || 0, helpers),
      buildMissingReportChipMarkup("당선사 누락", summary.architect_missing || 0, helpers),
      buildMissingReportChipMarkup("연면적 누락", summary.area_missing || 0, helpers),
    ].join("");
  }

  function buildMissingReportItemsMarkup(items = [], helpers = {}) {
    const {
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
    } = helpers;
    return (items || [])
      .map(
        (item) => `
        <article class="missing-report-item">
          <div class="artifact-head">
            <div>
              <strong>${escapeHtml(item.project_name || "-")}</strong>
              <p class="mono">${escapeHtml(item.bid_no || "-")} / ${escapeHtml(item.bid_ord || "000")} | ${escapeHtml(item.demand_org_name || "-")}</p>
            </div>
            <span class="mono">${escapeHtml(formatDate(item.updated_at || ""))}</span>
          </div>
          <div class="missing-report-fields">
            ${(item.missing_fields || [])
              .map(
                (field) => `
                  <div class="missing-report-field">
                    <strong>${escapeHtml(field.field_label || field.field_key || "-")}</strong>
                    <span class="mono">${escapeHtml(field.reason_group || "원인 미분류")}</span>
                    <span class="missing-report-reason">${escapeHtml(field.reason_explainer || "원인 설명 없음")}</span>
                    <span class="missing-report-reason">${escapeHtml(field.source_reason || "source 정보 없음")}</span>
                  </div>
                `
              )
              .join("")}
          </div>
        </article>
      `
      )
      .join("");
  }

  function buildMissingReportEmptyMarkup(message, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    return `<div class="empty-state">${escapeHtml(message)}</div>`;
  }

  function buildMissingReportViewModel(report, options = {}, helpers = {}) {
    if (!report) {
      return {
        summaryClassName: "",
        summaryMarkup: buildMissingReportEmptyMarkup("누락 현황을 아직 불러오지 않았습니다.", helpers),
        listClassName: "",
        listMarkup: buildMissingReportEmptyMarkup(
          options.errorMessage || "누락 공고를 불러오지 못했습니다.",
          helpers,
        ),
      };
    }

    const summary = report.summary || {};
    const items = Array.isArray(report.items) ? report.items : [];
    if (!items.length) {
      return {
        summaryClassName: "missing-report-summary",
        summaryMarkup: buildMissingReportSummaryMarkup(summary, helpers),
        listClassName: "missing-report-list empty-state",
        listMarkup: buildMissingReportEmptyMarkup("현재 누락 항목이 없습니다.", helpers),
      };
    }

    return {
      summaryClassName: "missing-report-summary",
      summaryMarkup: buildMissingReportSummaryMarkup(summary, helpers),
      listClassName: "missing-report-list",
      listMarkup: buildMissingReportItemsMarkup(items, helpers),
    };
  }

  globalObject.SPMSTrackerMissingReportRuntime = {
    buildMissingReportChipMarkup,
    buildMissingReportSummaryMarkup,
    buildMissingReportItemsMarkup,
    buildMissingReportEmptyMarkup,
    buildMissingReportViewModel,
  };
})(window);
