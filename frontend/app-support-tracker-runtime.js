(function attachAppSupportTrackerRuntime(global) {
  function normalizeRuntimeFieldSet(values = []) {
    if (values && typeof values === "object" && typeof values.has === "function" && typeof values.add === "function") {
      return values;
    }
    if (Array.isArray(values)) {
      return new Set(values.map((value) => String(value || "").trim()).filter(Boolean));
    }
    return new Set();
  }

  function createTrackerRenderFallbackHelpers(options = {}) {
    const {
      dom = {},
      state = {},
      resetTrackerBoardEdit = () => {},
      renderTrackerBoard = () => {},
      renderSelectedEntry = () => {},
      runtimeAdapters = {},
      salesStateHelpers = {},
      renderSalesClaimSection = () => "",
      renderTrackerEntryRelatedNotices = () => "",
      syncUrlState = () => {},
      toggleTrackerEntryRelated = async () => {},
      openTrackerEntryNoticeViewer = async () => {},
      bindRelatedNoticeViewerButtons = () => {},
      claimSalesProject = async () => {},
      saveSalesClaimNote = async () => {},
      transferSalesClaim = async () => {},
      flash = () => {},
      openSalesCloseDialog = () => {},
      closeSalesClaim = async () => {},
      releaseSalesClaim = async () => {},
      loadSelectedEntryDetail = async () => {},
      prefetchTrackerEntryDetails = () => {},
      buildTrackerBoardMarkupFallback = () => "",
      renderTrackerEntries = () => {},
      toggleTrackerBoardBlankPriority = () => {},
      beginTrackerBoardEdit = () => {},
      saveTrackerBoardEdit = async () => {},
      columns = [],
      textareaFields = new Set(),
      blankPriorityFields = new Set(),
    } = options;
    const runtimeAdapterDeps =
      runtimeAdapters && typeof runtimeAdapters === "object"
        ? runtimeAdapters
        : {};
    const salesStateHelperDeps =
      salesStateHelpers && typeof salesStateHelpers === "object"
        ? salesStateHelpers
        : {};
    const {
      buildTrackerEntriesEmptyStateView = () => null,
      buildTrackerEntryCardView = () => null,
      buildTrackerEntriesListMarkup = () => "",
      formatKoreanDate = (value) => String(value ?? ""),
      formatBuildingAutomationEstimateValue = () => "",
      buildTrackerEntrySummaryDetail = () => "",
      buildTrackerBoardMarkup = () => "",
      buildTrackerBoardEmptyStateView = () => null,
    } = runtimeAdapterDeps;
    const {
      getSalesClaimForProject = () => null,
      setSalesNoteDraft = () => {},
    } = salesStateHelperDeps;

    function renderTrackerBoardHeaderCell(
      column,
      { trackerBoardBlankPriorityFields = new Set(), trackerBoardSort = { fieldName: "" }, escapeHtml = (value) => String(value ?? "") } = {},
    ) {
      if (!trackerBoardBlankPriorityFields.has(column.key)) {
        return `<th>${escapeHtml(column.label)}</th>`;
      }
      const active = trackerBoardSort.fieldName === column.key;
      return `
        <th class="tracker-board-head-cell">
          <button
            class="tracker-board-sort-trigger${active ? " is-active" : ""}"
            type="button"
            data-board-sort-field="${escapeHtml(column.key)}"
          >
            <span>${escapeHtml(column.label)}</span>
            <span class="tracker-board-sort-meta mono">${active ? "비어있는 값 우선" : "빈 값만 우선"}</span>
          </button>
        </th>
      `;
    }

    function isTrackerBoardBlankValue(value) {
      return !String(value ?? "").trim();
    }

    function buildTrackerBoardEditingCellMarkupFallback(
      { entry, fieldName, label, value, saving, errorMessage },
      { escapeHtml = (item) => String(item ?? ""), textareaFields = new Set() } = {},
    ) {
      const textareaFieldSet = normalizeRuntimeFieldSet(textareaFields);
      const textarea = textareaFieldSet.has(fieldName);
      const inputMarkup = textarea
        ? `<textarea
            class="tracker-board-edit-input tracker-board-edit-input-textarea"
            rows="${fieldName === "progress_note" ? "4" : "3"}"
            data-board-edit-input="true"
            data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
            data-board-edit-field="${escapeHtml(fieldName)}"
            data-board-edit-active="true"
            ${saving ? "disabled" : ""}
          >${escapeHtml(value || "")}</textarea>`
        : `<input
            class="tracker-board-edit-input"
            type="text"
            value="${escapeHtml(value || "")}"
            data-board-edit-input="true"
            data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
            data-board-edit-field="${escapeHtml(fieldName)}"
            data-board-edit-active="true"
            ${saving ? "disabled" : ""}
          />`;
      return `
        <td class="tracker-board-cell tracker-board-cell-editing">
          <form
            class="tracker-board-edit-form"
            data-board-edit-form="true"
            data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
            data-board-edit-field="${escapeHtml(fieldName)}"
          >
            <span class="tracker-board-edit-label">${escapeHtml(label)}</span>
            ${inputMarkup}
            <div class="tracker-board-edit-actions">
              <button class="primary-button tracker-board-edit-save" type="submit" ${saving ? "disabled" : ""}>저장</button>
              <button class="ghost-button tracker-board-edit-cancel" type="button" data-board-edit-cancel="true" ${saving ? "disabled" : ""}>취소</button>
            </div>
            <p class="tracker-board-edit-hint mono">${textarea ? "Enter 저장, Shift+Enter 줄바꿈, Esc 취소" : "Enter 저장, Esc 취소"}</p>
            ${errorMessage ? `<p class="tracker-board-edit-error">${escapeHtml(errorMessage)}</p>` : ""}
          </form>
        </td>
      `;
    }

    function buildTrackerBoardCellMarkupFallback(
      { entry, column, displayNo, trackerBoardEdit = null },
      { escapeHtml: fallbackEscapeHtml = (value) => String(value ?? ""), textareaFields = new Set() } = {},
    ) {
      if (trackerBoardEdit?.entryId === entry?.id && trackerBoardEdit?.fieldName === column?.key) {
        return buildTrackerBoardEditingCellMarkupFallback(
          {
            entry,
            fieldName: column.key,
            label: column.label,
            value: trackerBoardEdit.draftValue,
            saving: trackerBoardEdit.saving,
            errorMessage: trackerBoardEdit.errorMessage,
          },
          {
            escapeHtml: fallbackEscapeHtml,
            textareaFields,
          },
        );
      }
      if (column.key === "display_no") {
        return `<td>${displayNo}</td>`;
      }
      const value = entry?.[column.key] || "";
      if (!column.editable) {
        return `<td>${fallbackEscapeHtml(value || "-")}</td>`;
      }
      const overrideClass = Array.isArray(entry?.overridden_fields) && entry.overridden_fields.includes(column.key)
        ? " is-overridden"
        : "";
      return `
        <td class="tracker-board-cell${overrideClass}">
          <button
            class="tracker-board-edit-trigger"
            type="button"
            data-board-edit-trigger="true"
            data-board-edit-entry-id="${fallbackEscapeHtml(entry?.id || "")}"
            data-board-edit-field="${fallbackEscapeHtml(column.key)}"
          >
            <span class="tracker-board-cell-value">${fallbackEscapeHtml(value || "-")}</span>
            <span class="tracker-board-cell-meta mono">${overrideClass ? "override" : "빈값일 때 우선"}</span>
          </button>
        </td>
      `;
    }

    function renderTrackerBoardCell(payload, helpers = {}) {
      return buildTrackerBoardCellMarkupFallback(payload, helpers);
    }

    function renderTrackerBoardEditingCell(payload, helpers = {}) {
      return buildTrackerBoardEditingCellMarkupFallback(payload, helpers);
    }

    function sortTrackerBoardEntries(entries, { fieldName = "", blankPriorityFields = new Set() } = {}, helpers = {}) {
      const isBlankValue = typeof helpers.isTrackerBoardBlankValue === "function"
        ? helpers.isTrackerBoardBlankValue
        : isTrackerBoardBlankValue;
      const sourceEntries = Array.isArray(entries) ? entries : [];
      const priorityFields = normalizeRuntimeFieldSet(blankPriorityFields);
      if (!priorityFields.has(fieldName)) {
        return sourceEntries;
      }
      return sourceEntries
        .map((entry, index) => ({ entry, index }))
        .sort((left, right) => {
          const leftBlank = isBlankValue(left.entry?.[fieldName]);
          const rightBlank = isBlankValue(right.entry?.[fieldName]);
          if (leftBlank !== rightBlank) {
            return leftBlank ? -1 : 1;
          }
          return left.index - right.index;
        })
        .map(({ entry }) => entry);
    }

    function buildTrackerEntriesFallbackDeps(refreshSelectedEntry = true) {
      return {
        dom,
        state,
        resetTrackerBoardEdit,
        renderTrackerBoard,
        renderSelectedEntry,
        buildTrackerEntriesEmptyStateView,
        buildTrackerEntryCardView,
        buildTrackerEntriesListMarkup,
        renderSalesClaimSection,
        renderTrackerEntryRelatedNotices,
        formatKoreanDate,
        formatBuildingAutomationEstimateValue,
        getSalesClaimForProject,
        syncUrlState,
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
        loadSelectedEntryDetail,
        buildTrackerEntrySummaryDetail,
        prefetchTrackerEntryDetails,
        refreshSelectedEntry,
      };
    }

    function buildTrackerBoardFallbackDeps() {
      return {
        dom,
        state,
        buildTrackerBoardMarkup,
        buildTrackerBoardEmptyStateView,
        buildTrackerBoardMarkupFallback,
        renderTrackerEntries,
        toggleTrackerBoardBlankPriority,
        syncUrlState,
        resetTrackerBoardEdit,
        beginTrackerBoardEdit,
        saveTrackerBoardEdit,
        columns,
        textareaFields,
        blankPriorityFields,
        renderTrackerBoardHeaderCell,
        renderTrackerBoardCell,
        renderTrackerBoardEditingCell,
        sortTrackerBoardEntries,
        sortTrackerBoardEntriesFallback: sortTrackerBoardEntries,
      };
    }

    return {
      renderTrackerBoardHeaderCell,
      isTrackerBoardBlankValue,
      buildTrackerBoardCellMarkupFallback,
      buildTrackerBoardEditingCellMarkupFallback,
      renderTrackerBoardCell,
      renderTrackerBoardEditingCell,
      sortTrackerBoardEntries,
      sortTrackerBoardEntriesFallback: sortTrackerBoardEntries,
      buildTrackerEntriesFallbackDeps,
      buildTrackerBoardFallbackDeps,
    };
  }

  function createTrackerRenderControllerDepsHelpers(deps = {}) {
    const {
      sharedDeps = {},
      trackerBoardActions = {},
      trackerSalesActions = {},
      selectedEntryActions = {},
    } = deps;
    let cachedDeps = null;

    function buildTrackerRenderControllerDeps() {
      if (cachedDeps) {
        return cachedDeps;
      }
      cachedDeps = {
        ...sharedDeps,
        ...trackerSalesActions,
        ...selectedEntryActions,
        ...trackerBoardActions,
      };
      return cachedDeps;
    }

    return {
      buildTrackerRenderControllerDeps,
    };
  }

  global.SPMSAppSupportTrackerRuntime = {
    createTrackerRenderFallbackHelpers,
    createTrackerRenderControllerDepsHelpers,
  };
})(window);
