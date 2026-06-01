(function attachTrackerDiagnosticsRuntime(global) {
  const STATUS_LABELS = {
    resolved: "해결됨",
    review: "검토 필요",
    no_owner_candidate: "담당 후보 없음",
    missing: "미분류",
  };

  function formatStatusLabel(value) {
    const raw = String(value || "").trim();
    return STATUS_LABELS[raw] || raw || "-";
  }

  function formatReasonLabel(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return "-";
    }
    return raw.replace(/_/g, " ");
  }

  function renderSummaryChip(label, count, escapeHtml) {
    return `
      <article class="missing-report-chip">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(String(count ?? 0))}</strong>
      </article>
    `;
  }

  function filterBackfillConflictsBySourceRun(items, sourceRunId = "") {
    const scope = String(sourceRunId || "").trim();
    if (!scope) {
      return Array.isArray(items) ? [...items] : [];
    }
    return (Array.isArray(items) ? items : []).filter(
      (item) => String(item?.source_run_id || "").trim() === scope
    );
  }

  function buildBackfillConflictsView(options = {}, helpers = {}) {
    const {
      scopeLabel = "",
      sourceRunId = "",
      items = [],
      loading = false,
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      buildBackfillConflictsMarkup = () => "",
    } = helpers;

    if (loading && !items.length) {
      return {
        isEmpty: true,
        isLoading: true,
        html: '<div class="empty-state">검토 필요 항목을 불러오는 중입니다.</div>',
        bindActions: false,
      };
    }

    if (!items.length) {
      return {
        isEmpty: true,
        isLoading: false,
        html: `<div class="empty-state">${
          escapeHtml(sourceRunId ? "선택한 source run 기준 열린 충돌 항목이 없습니다." : "열린 충돌 항목이 없습니다.")
        }</div>`,
        bindActions: false,
      };
    }

    return {
      isEmpty: false,
      isLoading: false,
      html: buildBackfillConflictsMarkup(items, { escapeHtml, scopeLabel }),
      bindActions: true,
    };
  }

  function buildTrackerCleanupPreviewMarkup(options = {}, helpers = {}) {
    const {
      scopeLabel = "",
      preview = null,
      loading = false,
      applying = false,
      canApply = false,
      applyDisabledReason = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;

    if (loading && !preview) {
      return `
        <div class="empty-state">선택한 tracker run 기준 cleanup preview를 불러오는 중입니다.</div>
      `;
    }

    if (!preview) {
      return `
        <div class="empty-state">
          ${escapeHtml(scopeLabel ? `${scopeLabel} 기준 preview가 아직 없습니다.` : "선택한 tracker run이 없습니다.")}
        </div>
      `;
    }

    const cards = [
      ["tracker entries", preview.tracker_entry_count || 0],
      ["child runs", preview.child_run_count || 0],
      ["parent runs", preview.parent_run_count || 0],
      ["logs", preview.log_count || 0],
      ["artifacts", preview.artifact_count || 0],
    ];

    return `
      <div class="tracker-cleanup-preview-card">
        <div class="artifact-head">
          <div>
            <strong>${escapeHtml(scopeLabel || "선택한 tracker run")}</strong>
            <p class="mono">tracker run ${escapeHtml(preview.source_tracker_run_id || "-")} | parent ${escapeHtml(preview.parent_run_id || "-")}</p>
          </div>
        </div>
        <div class="missing-report-summary">
          ${cards.map(([label, count]) => renderSummaryChip(label, count, escapeHtml)).join("")}
        </div>
        <div class="inline-actions">
          <button
            class="danger-button"
            type="button"
            data-tracker-cleanup-apply
            ${canApply && !applying ? "" : "disabled"}
            title="${escapeHtml(applyDisabledReason || "")}"
          >${applying ? "정리 중..." : "cleanup apply"}</button>
        </div>
      </div>
    `;
  }

  function buildContactResolutionSummaryMarkup(payload = {}, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
      formatStatusLabel: statusFormatter = formatStatusLabel,
      formatReasonLabel: reasonFormatter = formatReasonLabel,
    } = helpers;
    const summary = payload && typeof payload.summary === "object" ? payload.summary : {};
    const statusCounts = Array.isArray(payload?.status_counts) ? payload.status_counts : [];
    const reasonCounts = Array.isArray(payload?.reason_counts) ? payload.reason_counts : [];
    const items = Array.isArray(payload?.items) ? payload.items : [];
    const totalEntries = Number(summary.total_entries || 0);

    const summaryHtml = [
      renderSummaryChip("전체 대상", totalEntries, escapeHtml),
      ...statusCounts.map((item) => renderSummaryChip(statusFormatter(item?.status), item?.count, escapeHtml)),
      ...reasonCounts.slice(0, 3).map((item) => renderSummaryChip(reasonFormatter(item?.reason), item?.count, escapeHtml)),
    ].join("");

    if (!items.length) {
      return {
        summaryHtml: summaryHtml || renderSummaryChip("전체 대상", totalEntries, escapeHtml),
        listHtml: '<div class="empty-state">표본으로 확인할 재추출 항목이 없습니다.</div>',
      };
    }

    const listHtml = items
      .map((item) => `
        <article class="missing-report-item tracker-contact-resolution-item">
          <div class="artifact-head">
            <div>
              <strong>${escapeHtml(item.project_name || "-")}</strong>
              <p class="mono">${escapeHtml(item.demand_org_name || "-")} | ${escapeHtml(item.demand_contact || "-")}</p>
            </div>
            <span class="mono">${escapeHtml(formatDate(item.updated_at || ""))}</span>
          </div>
          <div class="tracker-contact-resolution-meta">
            <span class="status-badge status-${escapeHtml(String(item.resolution_status || "review"))}">${escapeHtml(statusFormatter(item.resolution_status))}</span>
            <span class="status-badge status-pending">${escapeHtml(reasonFormatter(item.resolution_reason))}</span>
            <span class="mono">${escapeHtml(item.resolution_phase || "-")} / ${escapeHtml(item.resolution_role || "-")}</span>
          </div>
          <div class="missing-report-fields">
            <div class="missing-report-field">
              <strong>owner side</strong>
              <span class="missing-report-reason">${escapeHtml(item.resolution_owner_side || "-")}</span>
              <span class="missing-report-reason">${escapeHtml(item.resolution_owner_side_basis || "-")}</span>
            </div>
            <div class="missing-report-field">
              <strong>entry</strong>
              <span class="missing-report-reason">${escapeHtml(item.entry_id || "-")}</span>
            </div>
          </div>
        </article>
      `)
      .join("");

    return {
      summaryHtml: summaryHtml || renderSummaryChip("전체 대상", totalEntries, escapeHtml),
      listHtml,
    };
  }

  function ensureTrackerContactResolutionPanel(options = {}) {
    const { dom, document } = options;
    if (!dom?.panelTracker || !document || dom.trackerContactResolutionPanel) {
      return;
    }

    const panel = document.createElement("section");
    panel.id = "tracker-contact-resolution-panel";
    panel.className = "runtime-card tracker-change-panel hidden";
    panel.innerHTML = `
      <div class="runtime-card-head">
        <div>
          <strong>연락처 재추출 검증</strong>
          <p class="kicker">샘플 기준 연락처 재추출 상태와 검토 사유를 빠르게 확인합니다.</p>
        </div>
        <button id="tracker-contact-resolution-refresh-button" class="ghost-button" type="button">새로고침</button>
      </div>
      <div id="tracker-contact-resolution-summary" class="missing-report-summary empty-state">연락처 재추출 요약을 불러오는 중입니다.</div>
      <div id="tracker-contact-resolution-list" class="missing-report-list empty-state">표본 재추출 결과를 불러오는 중입니다.</div>
    `;

    if (dom.backfillConflictPanel?.parentElement) {
      dom.backfillConflictPanel.parentElement.insertBefore(panel, dom.backfillConflictPanel);
    } else if (dom.trackerChangePanel?.parentElement) {
      dom.trackerChangePanel.parentElement.insertBefore(panel, dom.trackerChangePanel.nextSibling);
    } else {
      dom.panelTracker.insertBefore(panel, dom.trackerSalesOverviewGrid || dom.trackerEntriesSectionTitle || dom.trackerEntriesList || null);
    }

    dom.trackerContactResolutionPanel = panel;
    dom.trackerContactResolutionSummary = panel.querySelector("#tracker-contact-resolution-summary");
    dom.trackerContactResolutionList = panel.querySelector("#tracker-contact-resolution-list");
    dom.trackerContactResolutionRefreshButton = panel.querySelector("#tracker-contact-resolution-refresh-button");
  }

  function ensureTrackerCleanupPanel(options = {}) {
    const { dom, document } = options;
    if (!dom?.panelTracker || !document || dom.trackerCleanupPanel) {
      return;
    }

    const panel = document.createElement("section");
    panel.id = "tracker-cleanup-panel";
    panel.className = "runtime-card tracker-change-panel hidden";
    panel.innerHTML = `
      <div class="runtime-card-head">
        <div>
          <strong>tracker cleanup preview</strong>
          <p class="kicker">선택한 tracker run 기준 정리 범위를 먼저 확인하고 필요하면 apply 합니다.</p>
        </div>
        <button id="tracker-cleanup-refresh-button" class="ghost-button" type="button">새로고침</button>
      </div>
      <div id="tracker-cleanup-preview" class="missing-report-list empty-state">선택한 tracker run 기준 preview를 기다리는 중입니다.</div>
    `;

    if (dom.trackerContactResolutionPanel?.parentElement) {
      dom.trackerContactResolutionPanel.parentElement.insertBefore(panel, dom.trackerContactResolutionPanel);
    } else if (dom.backfillConflictPanel?.parentElement) {
      dom.backfillConflictPanel.parentElement.insertBefore(panel, dom.backfillConflictPanel);
    } else {
      dom.panelTracker.insertBefore(panel, dom.trackerSalesOverviewGrid || dom.trackerEntriesSectionTitle || dom.trackerEntriesList || null);
    }

    dom.trackerCleanupPanel = panel;
    dom.trackerCleanupPreview = panel.querySelector("#tracker-cleanup-preview");
    dom.trackerCleanupRefreshButton = panel.querySelector("#tracker-cleanup-refresh-button");
  }

  global.SPMSTrackerDiagnosticsRuntime = {
    buildBackfillConflictsView,
    buildContactResolutionSummaryMarkup,
    buildTrackerCleanupPreviewMarkup,
    filterBackfillConflictsBySourceRun,
    ensureTrackerCleanupPanel,
    ensureTrackerContactResolutionPanel,
  };
})(window);
