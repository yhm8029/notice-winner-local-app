export function createTrackerDiagnosticsPanelController(deps = {}) {
  const {
    window: appWindow = typeof window !== "undefined" ? window : globalThis,
    dom,
    state,
    api,
    flash,
    trackerController,
    escapeHtml,
    formatDate,
    formatContactResolutionStatusLabel,
    formatContactResolutionReasonLabel,
    formatBackfillConflictResolutionLabel,
    getTrackerDiagnosticsScope,
    requireTrackerDiagnosticsRuntime,
    buildTrackerChangeEventsMarkup,
    buildTrackerChangeBellPopoverMarkup,
    buildBackfillConflictsMarkup,
    syncUrlState,
    renderTrackerEntries,
    loadSelectedEntryDetail,
    focusTrackerChangeEntry,
    closeTrackerChangeModal,
  } = deps;

  function renderMissingReportChip(label, count) {
    return `
    <article class="missing-report-chip">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(count))}</strong>
    </article>
  `;
  }

  function renderTrackerMissingReport(errorMessage = "") {
    if (!dom.missingReportSummary || !dom.missingReportList) {
      return;
    }

    const report = state.trackerMissingReport;
    if (!report) {
      dom.missingReportSummary.innerHTML = '<div class="empty-state">누락 현황을 아직 불러오지 않았습니다.</div>';
      dom.missingReportList.innerHTML = `<div class="empty-state">${escapeHtml(errorMessage || "누락 공고를 불러오지 못했습니다.")}</div>`;
      return;
    }

    const summary = report.summary || {};
    dom.missingReportSummary.className = "missing-report-summary";
    dom.missingReportSummary.innerHTML = [
      renderMissingReportChip("전체 공고", summary.total_entries || 0),
      renderMissingReportChip("누락 공고", summary.missing_entries || 0),
      renderMissingReportChip("연락처 누락", summary.contact_missing || 0),
      renderMissingReportChip("설계사무소 누락", summary.architect_missing || 0),
      renderMissingReportChip("연면적 누락", summary.area_missing || 0),
    ].join("");

    const items = Array.isArray(report.items) ? report.items : [];
    if (!items.length) {
      dom.missingReportList.className = "missing-report-list empty-state";
      dom.missingReportList.innerHTML = '<div class="empty-state">현재 누락 항목이 없습니다.</div>';
      return;
    }

    dom.missingReportList.className = "missing-report-list";
    dom.missingReportList.innerHTML = items
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
                `,
              )
              .join("")}
          </div>
        </article>
      `,
      )
      .join("");
  }

  function renderTrackerContactResolutionSummary(errorMessage = "") {
    if (!dom.trackerContactResolutionSummary || !dom.trackerContactResolutionList) {
      return;
    }

    if (state.trackerContactResolutionLoading && !state.trackerContactResolutionSummary) {
      dom.trackerContactResolutionSummary.className = "missing-report-summary empty-state";
      dom.trackerContactResolutionSummary.innerHTML = '<div class="empty-state">연락처 검증 요약을 불러오는 중입니다.</div>';
      dom.trackerContactResolutionList.className = "missing-report-list empty-state";
      dom.trackerContactResolutionList.innerHTML = '<div class="empty-state">세부 검증 결과를 불러오는 중입니다.</div>';
      return;
    }

    const payload = state.trackerContactResolutionSummary;
    if (!payload) {
      dom.trackerContactResolutionSummary.className = "missing-report-summary empty-state";
      dom.trackerContactResolutionSummary.innerHTML = '<div class="empty-state">연락처 검증 요약을 아직 불러오지 않았습니다.</div>';
      dom.trackerContactResolutionList.className = "missing-report-list empty-state";
      dom.trackerContactResolutionList.innerHTML = `<div class="empty-state">${escapeHtml(errorMessage || "연락처 검증 결과를 불러오지 못했습니다.")}</div>`;
      return;
    }

    const view = requireTrackerDiagnosticsRuntime().buildContactResolutionSummaryMarkup(payload, {
      escapeHtml,
      formatDate,
      formatStatusLabel: formatContactResolutionStatusLabel,
      formatReasonLabel: formatContactResolutionReasonLabel,
    });
    dom.trackerContactResolutionSummary.className = "missing-report-summary";
    dom.trackerContactResolutionSummary.innerHTML = view.summaryHtml;
    const hasItems = Array.isArray(payload.items) && payload.items.length > 0;
    dom.trackerContactResolutionList.className = hasItems ? "missing-report-list" : "missing-report-list empty-state";
    dom.trackerContactResolutionList.innerHTML = view.listHtml;
  }

  function renderTrackerCleanupPreview(errorMessage = "") {
    if (!dom.trackerCleanupPreview) {
      return;
    }
    const scope = getTrackerDiagnosticsScope();
    if (!scope?.trackerRunId) {
      dom.trackerCleanupPreview.className = "missing-report-list empty-state";
      dom.trackerCleanupPreview.innerHTML = '<div class="empty-state">tracker cleanup preview는 tracker_export run 선택 시 사용할 수 있습니다.</div>';
      return;
    }
    if (state.trackerCleanupLoading && !state.trackerCleanupPreview) {
      dom.trackerCleanupPreview.className = "missing-report-list empty-state";
      dom.trackerCleanupPreview.innerHTML = '<div class="empty-state">선택한 tracker run 기준 cleanup preview를 불러오는 중입니다.</div>';
      return;
    }
    dom.trackerCleanupPreview.className = "missing-report-list";
    dom.trackerCleanupPreview.innerHTML = requireTrackerDiagnosticsRuntime().buildTrackerCleanupPreviewMarkup(
      {
        scopeLabel: scope.scopeLabel,
        preview: state.trackerCleanupPreview,
        loading: state.trackerCleanupLoading,
        applying: state.trackerCleanupApplying,
        canApply: Boolean(state.trackerCleanupPreview && !state.trackerCleanupApplying),
        applyDisabledReason: errorMessage || "",
      },
      { escapeHtml },
    );
  }

  function focusTrackerChangePanel() {
    if (!dom.trackerChangePanel) {
      return;
    }
    dom.trackerChangePanel.classList.add("is-focused");
    dom.trackerChangePanel.scrollIntoView({ behavior: "smooth", block: "start" });
    appWindow.setTimeout(() => {
      dom.trackerChangePanel?.classList.remove("is-focused");
    }, 1400);
  }

  function setTrackerChangeBellPopoverOpen(open) {
    const nextOpen = Boolean(open && dom.trackerChangeBellPopover);
    state.trackerChangeBellPopoverOpen = nextOpen;
    if (dom.trackerChangeBell) {
      dom.trackerChangeBell.setAttribute("aria-expanded", nextOpen ? "true" : "false");
    }
    dom.trackerChangeBellPopover?.classList.toggle("hidden", !nextOpen);
  }

  function renderTrackerChangeBellPopover() {
    if (!dom.trackerChangeBellPopover) {
      return;
    }
    if (state.trackerChangeEventsAvailability === "unavailable") {
      dom.trackerChangeBellPopover.innerHTML = '<div class="empty-state">최근 변경 알람을 사용할 수 없습니다.</div>';
      return;
    }
    if (state.trackerChangeEventsLoading && !state.trackerChangeEvents.length) {
      dom.trackerChangeBellPopover.innerHTML = '<div class="empty-state">최근 변경을 불러오는 중입니다.</div>';
      return;
    }
    const items = Array.isArray(state.trackerChangeEvents) ? state.trackerChangeEvents.slice(0, 6) : [];
    if (!items.length) {
      dom.trackerChangeBellPopover.innerHTML = '<div class="empty-state">표시할 최근 변경이 없습니다.</div>';
      return;
    }
    dom.trackerChangeBellPopover.innerHTML = buildTrackerChangeBellPopoverMarkup(items);
    bindTrackerChangeEventActions(dom.trackerChangeBellPopover);
  }

  function renderTrackerChangeEventsList(container) {
    if (!container) {
      return;
    }
    if (state.trackerChangeEventsLoading && !state.trackerChangeEvents.length) {
      if (state.uiMode === "user") {
        container.classList.add("empty-state");
        container.innerHTML = "표시할 최근 변경이 없습니다.";
        return;
      }
      container.classList.add("empty-state");
      container.innerHTML = "최근 변경을 불러오는 중입니다.";
      return;
    }
    if (!state.trackerChangeEvents.length) {
      container.classList.add("empty-state");
      container.innerHTML = "표시할 최근 변경이 없습니다.";
      return;
    }
    container.classList.remove("empty-state");
    container.innerHTML = buildTrackerChangeEventsMarkup(state.trackerChangeEvents);
    bindTrackerChangeEventActions(container);
  }

  function renderTrackerChangeEventUnreadCount() {
    if (!dom.trackerChangeBellBadge) {
      return;
    }
    const unreadCount = Number(state.trackerChangeEventsUnread || 0);
    dom.trackerChangeBellBadge.textContent = String(unreadCount);
    dom.trackerChangeBellBadge.classList.toggle("hidden", unreadCount <= 0);
  }

  async function resolveBackfillConflict({ conflictId, resolution } = {}) {
    try {
      const response = await api(`/api/backfill-conflicts/${encodeURIComponent(String(conflictId || "").trim())}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution }),
      });
      state.backfillConflicts = state.backfillConflicts.filter((item) => String(item.id) !== String(response.id));
      renderBackfillConflictsPanel();
      flash(`검토 항목 처리 완료 · ${formatBackfillConflictResolutionLabel(response.resolution)}`);
    } catch (err) {
      flash(err.message, "error");
    }
  }

  function bindBackfillConflictActions(container) {
    if (!container) {
      return;
    }
    for (const button of container.querySelectorAll("[data-backfill-entry-id]")) {
      button.addEventListener("click", async () => {
        const entryId = String(button.getAttribute("data-backfill-entry-id") || "").trim();
        if (!entryId) {
          return;
        }
        state.selectedEntryId = entryId;
        state.drawerOpen = state.uiMode !== "admin";
        syncUrlState?.();
        renderTrackerEntries?.(state.trackerEntries, { refreshSelectedEntry: state.uiMode === "admin" });
        await loadSelectedEntryDetail?.({ entryId, silent: true, force: true });
      });
    }
    for (const button of container.querySelectorAll("[data-backfill-resolve-id]")) {
      button.addEventListener("click", async () => {
        const conflictId = String(button.getAttribute("data-backfill-resolve-id") || "").trim();
        const resolution = String(button.getAttribute("data-backfill-resolution") || "").trim();
        if (!conflictId || !resolution) {
          return;
        }
        await resolveBackfillConflict({ conflictId, resolution });
      });
    }
  }

  function bindTrackerChangeEventActions(container) {
    if (!container) {
      return;
    }
    for (const button of container.querySelectorAll("[data-change-entry-id]")) {
      button.addEventListener("click", async () => {
        const entryId = String(button.getAttribute("data-change-entry-id") || "").trim();
        if (!entryId) {
          return;
        }
        if (state.trackerChangeModal?.open) {
          closeTrackerChangeModal?.();
        }
        if (typeof focusTrackerChangeEntry === "function") {
          await focusTrackerChangeEntry(entryId);
        } else {
          state.selectedEntryId = entryId;
          state.drawerOpen = state.uiMode !== "admin";
          syncUrlState?.();
          renderTrackerEntries?.(state.trackerEntries, { refreshSelectedEntry: state.uiMode === "admin" });
          await loadSelectedEntryDetail?.({ entryId, silent: true, force: true });
        }
        await trackerController?.markTrackerChangeEventsRead?.({ trackerEntryId: entryId, silent: true });
      });
    }
  }

  function renderTrackerChangeEventsPanel() {
    renderTrackerChangeBellPopover();
    renderTrackerChangeEventsList(dom.trackerChangeList);
    renderTrackerChangeEventsList(dom.trackerChangeModalList);
  }

  function renderBackfillConflictsPanel() {
    if (!dom.backfillConflictList) {
      return;
    }
    if (state.backfillConflictsLoading && !state.backfillConflicts.length) {
      dom.backfillConflictList.classList.add("empty-state");
      dom.backfillConflictList.innerHTML = "검토 필요 항목을 불러오는 중입니다.";
      return;
    }
    if (!state.backfillConflicts.length) {
      dom.backfillConflictList.classList.add("empty-state");
      dom.backfillConflictList.innerHTML = "열린 충돌 항목이 없습니다.";
      return;
    }
    dom.backfillConflictList.classList.remove("empty-state");
    dom.backfillConflictList.innerHTML = buildBackfillConflictsMarkup(state.backfillConflicts);
    bindBackfillConflictActions(dom.backfillConflictList);
  }

  return {
    focusTrackerChangePanel,
    setTrackerChangeBellPopoverOpen,
    renderTrackerChangeBellPopover,
    renderTrackerChangeEventsList,
    renderTrackerChangeEventUnreadCount,
    renderTrackerMissingReport,
    renderTrackerContactResolutionSummary,
    renderTrackerCleanupPreview,
    renderTrackerChangeEventsPanel,
    renderBackfillConflictsPanel,
    bindTrackerChangeEventActions,
    bindBackfillConflictActions,
    resolveBackfillConflict,
  };
}

const trackerDiagnosticsPanelControllerRoot = typeof window !== "undefined" ? window : globalThis;
trackerDiagnosticsPanelControllerRoot.TRACKER_DIAGNOSTICS_PANEL_CONTROLLER = trackerDiagnosticsPanelControllerRoot.TRACKER_DIAGNOSTICS_PANEL_CONTROLLER || {};
trackerDiagnosticsPanelControllerRoot.TRACKER_DIAGNOSTICS_PANEL_CONTROLLER.createTrackerDiagnosticsPanelController = createTrackerDiagnosticsPanelController;
