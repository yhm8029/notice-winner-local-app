export function createTrackerRenderController(deps = {}) {
  const {
    dom,
    state,
    escapeHtml,
    formatKoreanDate,
    formatBuildingAutomationEstimateValue,
    TRACKER_ENTRY_RUNTIME,
    buildTrackerEntryCardMarkupFallback,
    renderSalesClaimSection,
    renderTrackerEntryRelatedNotices,
    resetTrackerBoardEdit,
    renderSelectedEntry,
    buildTrackerEntrySummaryDetail,
    loadSelectedEntryDetail,
    toggleTrackerEntryRelated,
    openTrackerEntryNoticeViewer,
    bindRelatedNoticeViewerButtons,
    claimSalesProject,
    setSalesNoteDraft,
    saveSalesClaimNote,
    transferSalesClaim,
    flash,
    openSalesCloseDialog,
    closeSalesClaim,
    releaseSalesClaim,
    syncUrlState,
    prefetchTrackerEntryDetails,
    getSalesClaimForProject,
    getSortedTrackerBoardEntries,
    TRACKER_BOARD_COLUMNS,
    renderTrackerBoardHeaderCell,
    renderTrackerBoardCell,
    toggleTrackerBoardBlankPriority,
    beginTrackerBoardEdit,
    saveTrackerBoardEdit,
    window: appWindow = typeof window !== "undefined" ? window : null,
  } = deps;

  function hasActiveTextSelection() {
    const getSelection = typeof appWindow?.getSelection === "function" ? appWindow.getSelection : null;
    const selection = getSelection ? getSelection.call(appWindow) : null;
    return Boolean(selection && (!selection.isCollapsed || String(selection.toString?.() || "").trim()));
  }

  function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {
    const displayEntries = state.uiMode === "user"
      ? entries.filter((entry) => !getSalesClaimForProject(String(entry.project_id || "").trim()))
      : entries;

    if (!displayEntries.length) {
      resetTrackerBoardEdit();
      state.trackerRelatedEntryId = null;
      state.trackerRelatedResolvingEntryId = null;
      dom.trackerEntriesList.innerHTML = state.trackerEntriesError
        ? `<div class="empty-state">프로젝트 현황을 불러오지 못했습니다: ${escapeHtml(state.trackerEntriesError)}</div>`
        : state.uiMode === "user"
          ? '<div class="empty-state">현재 영업 대상으로 바로 가져올 수 있는 프로젝트가 없습니다.</div>'
          : '<div class="empty-state">No tracker rows loaded.</div>';
      renderTrackerBoard([]);
      if (refreshSelectedEntry) {
        renderSelectedEntry(null);
      }
      return;
    }

    if (!displayEntries.some((entry) => entry.id === state.selectedEntryId)) {
      state.selectedEntryId = displayEntries[0].id;
    }
    if (!displayEntries.some((entry) => entry.id === state.trackerRelatedEntryId)) {
      state.trackerRelatedEntryId = null;
    }

    dom.trackerEntriesList.innerHTML = displayEntries
      .map((entry, index) => {
        const displayNo = (state.trackerFilters.page - 1) * state.trackerFilters.pageSize + index + 1;
        const isSelected = entry.id === state.selectedEntryId;
        const overridden = entry.overridden_fields.length
          ? `override ${escapeHtml(entry.overridden_fields.join(", "))}`
          : "no overrides";
        const overrideMetaHtml = state.uiMode === "admin"
          ? `<p>${escapeHtml(overridden)}</p>`
          : "";
        const relatedButtonLabel = entry.id === state.trackerRelatedEntryId ? "연관 공고 닫기" : "연관 공고 열기";
        return TRACKER_ENTRY_RUNTIME?.buildTrackerEntryCardMarkup?.(
          {
            entry,
            displayNo,
            isSelected,
            relatedButtonLabel,
            salesMarkup: renderSalesClaimSection(entry),
            overrideMarkup: overrideMetaHtml,
            relatedMarkup: renderTrackerEntryRelatedNotices(entry),
          },
          {
            escapeHtml,
            formatBuildingAutomationEstimateValue,
            formatKoreanDate,
          },
        ) || buildTrackerEntryCardMarkupFallback(
          {
            entry,
            displayNo,
            isSelected,
            relatedButtonLabel,
            salesMarkup: renderSalesClaimSection(entry),
            overrideMarkup: overrideMetaHtml,
            relatedMarkup: renderTrackerEntryRelatedNotices(entry),
          },
          {
            escapeHtml,
            formatBuildingAutomationEstimateValue,
            formatKoreanDate,
          },
        );
      })
      .join("");

    for (const item of dom.trackerEntriesList.querySelectorAll("[data-entry-id]")) {
      item.addEventListener("click", (event) => {
        if (event.target.closest("button, a, textarea, input, select, label")) {
          return;
        }
        if (hasActiveTextSelection()) {
          return;
        }
        state.selectedEntryId = item.getAttribute("data-entry-id");
        state.drawerOpen = false;
        syncUrlState();
        renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: state.uiMode === "admin" });
      });
    }
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-entry-related-toggle]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entryId = button.getAttribute("data-entry-related-toggle");
        if (!entryId) {
          return;
        }
        const entry = displayEntries.find((item) => item.id === entryId);
        if (!entry) {
          return;
        }
        state.selectedEntryId = entryId;
        if (state.uiMode === "admin") {
          renderSelectedEntry(buildTrackerEntrySummaryDetail(entry), { summaryOnly: true });
          void loadSelectedEntryDetail({ entryId, silent: true, background: true });
        }
        void toggleTrackerEntryRelated(entryId);
      });
    }
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-entry-notice-view]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entryId = button.getAttribute("data-entry-notice-view");
        if (!entryId) {
          return;
        }
        void openTrackerEntryNoticeViewer(entryId, entries);
      });
    }
    bindRelatedNoticeViewerButtons(dom.trackerEntriesList);
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-claim]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entryId = button.getAttribute("data-sales-claim");
        const entry = displayEntries.find((item) => item.id === entryId);
        if (!entry) {
          return;
        }
        void claimSalesProject(entry);
      });
    }
    for (const textarea of dom.trackerEntriesList.querySelectorAll("[data-sales-note]")) {
      textarea.addEventListener("click", (event) => event.stopPropagation());
      textarea.addEventListener("input", () => {
        const projectId = textarea.getAttribute("data-sales-note");
        if (!projectId) {
          return;
        }
        setSalesNoteDraft(projectId, textarea.value);
      });
      textarea.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          const projectId = textarea.getAttribute("data-sales-note");
          if (!projectId) {
            return;
          }
          void saveSalesClaimNote(projectId);
        }
      });
    }
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-note-save]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-note-save");
        if (!projectId) {
          return;
        }
        void saveSalesClaimNote(projectId);
      });
    }
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-transfer]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-transfer");
        if (!projectId) {
          return;
        }
        const select = button.closest(".entry-sales-transfer")?.querySelector("[data-sales-transfer-select]");
        const targetUserId = select ? select.value : "";
        if (!targetUserId) {
          flash("이관 대상 사용자를 선택해라.", "warn");
          return;
        }
        void transferSalesClaim(projectId, targetUserId);
      });
    }
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-close]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-close");
        const outcome = button.getAttribute("data-sales-close-outcome");
        if (!projectId || !outcome) {
          return;
        }
        if (outcome === "won") {
          openSalesCloseDialog(projectId);
          return;
        }
        void closeSalesClaim(projectId, outcome);
      });
    }
    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-release]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-release");
        if (!projectId) {
          return;
        }
        void releaseSalesClaim(projectId);
      });
    }

    const selectedEntry = displayEntries.find((entry) => entry.id === state.selectedEntryId) || displayEntries[0];
    renderTrackerBoard(displayEntries);
    if (refreshSelectedEntry) {
      const cachedSelectedEntry =
        (state.selectedEntry?.id === selectedEntry.id ? state.selectedEntry : null)
        || state.trackerEntryDetailCache[selectedEntry.id]
        || null;
      if (cachedSelectedEntry) {
        const summaryOnly = Boolean(cachedSelectedEntry._summary_only);
        renderSelectedEntry(cachedSelectedEntry, { summaryOnly });
        if (summaryOnly) {
          void loadSelectedEntryDetail({
            entryId: selectedEntry.id,
            silent: true,
            background: true,
          });
        }
      } else {
        renderSelectedEntry(buildTrackerEntrySummaryDetail(selectedEntry), { summaryOnly: true });
        void loadSelectedEntryDetail({
          entryId: selectedEntry.id,
          silent: true,
          background: true,
        });
      }
    }
    prefetchTrackerEntryDetails(displayEntries);
  }


  function renderTrackerBoard(entries) {
    if (!dom.trackerBoard) {
      return;
    }
    if (!entries.length) {
      dom.trackerBoard.innerHTML = "트래커 행을 불러오면 여기에 표로 표시됩니다.";
      dom.trackerBoard.className = "tracker-board-content empty-state";
      return;
    }
    const boardEntries = getSortedTrackerBoardEntries(entries);
    dom.trackerBoard.className = "tracker-board-content";
    dom.trackerBoard.innerHTML = `
      <table class="tracker-board-table">
        <thead>
          <tr>
            ${TRACKER_BOARD_COLUMNS.map((column) => renderTrackerBoardHeaderCell(column)).join("")}
          </tr>
        </thead>
        <tbody>
          ${boardEntries
            .map(
              (entry, index) => {
                const displayNo = (state.trackerFilters.page - 1) * state.trackerFilters.pageSize + index + 1;
                const cells = TRACKER_BOARD_COLUMNS.map((column) =>
                  renderTrackerBoardCell({
                    entry,
                    column,
                    displayNo,
                  }),
                ).join("");
                return `
                <tr data-board-entry-id="${escapeHtml(entry.id)}" class="${entry.id === state.selectedEntryId ? "is-selected" : ""}">
                  ${cells}
                </tr>
              `;
              }
            )
            .join("")}
        </tbody>
      </table>
    `;
    for (const button of dom.trackerBoard.querySelectorAll("[data-board-sort-field]")) {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        const fieldName = button.getAttribute("data-board-sort-field");
        if (!fieldName) {
          return;
        }
        toggleTrackerBoardBlankPriority(fieldName);
      });
    }
    for (const row of dom.trackerBoard.querySelectorAll("[data-board-entry-id]")) {
      row.addEventListener("click", (event) => {
        if (event.target.closest("button, a")) {
          return;
        }
        if (hasActiveTextSelection()) {
          return;
        }
        state.selectedEntryId = row.getAttribute("data-board-entry-id");
        state.drawerOpen = false;
        syncUrlState();
        renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: state.uiMode === "admin" });
      });
    }
    for (const button of dom.trackerBoard.querySelectorAll("[data-board-edit-trigger]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entryId = button.getAttribute("data-board-edit-entry-id");
        const fieldName = button.getAttribute("data-board-edit-field");
        if (!entryId || !fieldName) {
          return;
        }
        beginTrackerBoardEdit(entryId, fieldName);
      });
    }
    for (const button of dom.trackerBoard.querySelectorAll("[data-board-edit-cancel]")) {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        resetTrackerBoardEdit();
        renderTrackerBoard(state.trackerEntries);
      });
    }
    for (const form of dom.trackerBoard.querySelectorAll("[data-board-edit-form]")) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const entryId = form.getAttribute("data-board-edit-entry-id");
        const fieldName = form.getAttribute("data-board-edit-field");
        if (!entryId || !fieldName) {
          return;
        }
        void saveTrackerBoardEdit({ entryId, fieldName });
      });
    }
    for (const input of dom.trackerBoard.querySelectorAll("[data-board-edit-input]")) {
      input.addEventListener("click", (event) => event.stopPropagation());
      input.addEventListener("input", () => {
        state.trackerBoardEdit.draftValue = input.value;
        state.trackerBoardEdit.errorMessage = "";
      });
      input.addEventListener("keydown", (event) => {
        event.stopPropagation();
        if (event.key === "Escape") {
          event.preventDefault();
          resetTrackerBoardEdit();
          renderTrackerBoard(state.trackerEntries);
          return;
        }
        if (event.key !== "Enter") {
          return;
        }
        if (input.tagName === "TEXTAREA" && event.shiftKey) {
          return;
        }
        event.preventDefault();
        const entryId = input.getAttribute("data-board-edit-entry-id");
        const fieldName = input.getAttribute("data-board-edit-field");
        if (!entryId || !fieldName) {
          return;
        }
        void saveTrackerBoardEdit({ entryId, fieldName });
      });
      if (input.getAttribute("data-board-edit-active") === "true") {
        input.focus();
        if (typeof input.select === "function") {
          input.select();
        }
      }
    }
  }


  return {
    renderTrackerEntries,
    renderTrackerBoard,
  };
}

const trackerRenderControllerRoot = typeof window !== 'undefined' ? window : globalThis;
trackerRenderControllerRoot.TRACKER_RENDER_CONTROLLER = trackerRenderControllerRoot.TRACKER_RENDER_CONTROLLER || {};
trackerRenderControllerRoot.TRACKER_RENDER_CONTROLLER.createTrackerRenderController = createTrackerRenderController;
