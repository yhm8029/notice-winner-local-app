(function attachSPMSTrackerRenderFallbackBoardRuntime(globalObject) {
  function normalizeRuntimeFieldSet(values = []) {
    if (Object.prototype.toString.call(values) === "[object Set]") {
      return values;
    }
    if (Array.isArray(values)) {
      return new Set(values.map((value) => String(value || "").trim()).filter(Boolean));
    }
    return new Set();
  }

  function renderTrackerBoardHeaderCellFallback(
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
          <span class="tracker-board-sort-meta mono">${active ? "鍮?媛??곗꽑" : "?대┃ ??鍮?媛??곗꽑"}</span>
        </button>
      </th>
    `;
  }

  function isTrackerBoardBlankValueFallback(value) {
    return !String(value ?? "").trim();
  }

  function renderTrackerBoardCellFallback(
    { entry, column, displayNo },
    { escapeHtml = (value) => String(value ?? "") } = {},
  ) {
    if (column.key === "display_no") {
      return `<td>${displayNo}</td>`;
    }
    const value = entry?.[column.key] || "";
    if (!column.editable) {
      return `<td>${escapeHtml(value || "-")}</td>`;
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
          data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
          data-board-edit-field="${escapeHtml(column.key)}"
        >
          <span class="tracker-board-cell-value">${escapeHtml(value || "-")}</span>
          <span class="tracker-board-cell-meta mono">${overrideClass ? "override" : "?대┃???섏젙"}</span>
        </button>
      </td>
    `;
  }

  function renderTrackerBoardEditingCellFallback(
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
            <button class="primary-button tracker-board-edit-save" type="submit" ${saving ? "disabled" : ""}>???/button>
            <button class="ghost-button tracker-board-edit-cancel" type="button" data-board-edit-cancel="true" ${saving ? "disabled" : ""}>痍⑥냼</button>
          </div>
          <p class="tracker-board-edit-hint mono">${textarea ? "Enter ???쨌 Shift+Enter 以꾨컮轅?쨌 Esc 痍⑥냼" : "Enter ???쨌 Esc 痍⑥냼"}</p>
          ${errorMessage ? `<p class="tracker-board-edit-error">${escapeHtml(errorMessage)}</p>` : ""}
        </form>
      </td>
    `;
  }

  function sortTrackerBoardEntriesFallback(entries, { fieldName = "", blankPriorityFields = new Set() } = {}, helpers = {}) {
    const isBlankValue = typeof helpers.isTrackerBoardBlankValue === "function"
      ? helpers.isTrackerBoardBlankValue
      : isTrackerBoardBlankValueFallback;
    const sourceEntries = Array.isArray(entries) ? entries : [];
    const priorityFields = normalizeRuntimeFieldSet(blankPriorityFields);
    if (!priorityFields.has(fieldName)) {
      return sourceEntries;
    }
    return sourceEntries
      .map((entry, index) => ({ entry, index }))
      .sort((left, right) => {
        const leftBlank = isBlankValue(left.entry[fieldName]);
        const rightBlank = isBlankValue(right.entry[fieldName]);
        if (leftBlank !== rightBlank) {
          return leftBlank ? -1 : 1;
        }
        return left.index - right.index;
      })
      .map(({ entry }) => entry);
  }

  function buildTrackerBoardMarkupFallback(entries, options = {}, helpers = {}) {
    const {
      columns = [],
      currentSortField = "",
      trackerBoardEdit = null,
      textareaFields = [],
      blankPriorityFields = [],
      page = 1,
      pageSize = 20,
      selectedEntryId = "",
    } = options;
    const textareaFieldSet = normalizeRuntimeFieldSet(textareaFields);
    const blankPriorityFieldSet = normalizeRuntimeFieldSet(blankPriorityFields);
    const {
      escapeHtml: fallbackEscapeHtml = (value) => String(value ?? ""),
      renderTrackerBoardHeaderCell = renderTrackerBoardHeaderCellFallback,
      renderTrackerBoardCell = renderTrackerBoardCellFallback,
      renderTrackerBoardEditingCell = renderTrackerBoardEditingCellFallback,
      sortTrackerBoardEntriesFallback: sortEntriesFallback = sortTrackerBoardEntriesFallback,
    } = helpers;

    const sourceEntries = Array.isArray(entries) ? entries : [];
    const boardEntries = typeof sortEntriesFallback === "function"
      ? sortEntriesFallback(sourceEntries, {
        fieldName: currentSortField,
        blankPriorityFields: blankPriorityFieldSet,
      }, {
        isTrackerBoardBlankValue: isTrackerBoardBlankValueFallback,
      })
      : sourceEntries;

    if (!boardEntries.length) {
      return "";
    }

    return `
      <table class="tracker-board-table">
        <thead>
          <tr>
            ${columns.map((column) => renderTrackerBoardHeaderCell(column, {
              trackerBoardBlankPriorityFields: blankPriorityFieldSet,
              trackerBoardSort: { fieldName: currentSortField },
              escapeHtml: fallbackEscapeHtml,
            })).join("")}
          </tr>
        </thead>
        <tbody>
          ${boardEntries
            .map((entry, index) => {
              const displayNo = (page - 1) * pageSize + index + 1;
              const cells = columns.map((column) => {
                if (trackerBoardEdit?.entryId === entry.id && trackerBoardEdit?.fieldName === column.key) {
                  return renderTrackerBoardEditingCell({
                    entry,
                    fieldName: column.key,
                    label: column.label,
                    value: trackerBoardEdit.draftValue,
                    saving: trackerBoardEdit.saving,
                    errorMessage: trackerBoardEdit.errorMessage,
                  }, {
                    escapeHtml: fallbackEscapeHtml,
                    textareaFields: textareaFieldSet,
                  });
                }
                return renderTrackerBoardCell({
                  entry,
                  column,
                  displayNo,
                }, {
                  escapeHtml: fallbackEscapeHtml,
                });
              }).join("");
              return `
                <tr data-board-entry-id="${fallbackEscapeHtml(entry.id)}" class="${entry.id === selectedEntryId ? "is-selected" : ""}">
                  ${cells}
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderTrackerBoardFallback(entries, context = {}, helpers = {}) {
    const {
      dom = null,
      state = null,
      buildTrackerBoardMarkup = () => "",
      buildTrackerBoardEmptyStateView = () => null,
      buildTrackerBoardMarkupFallback: buildBoardMarkupFallback = buildTrackerBoardMarkupFallback,
      renderTrackerEntries = () => {},
      toggleTrackerBoardBlankPriority = () => {},
      syncUrlState = () => {},
      resetTrackerBoardEdit = () => {},
      beginTrackerBoardEdit = () => {},
      saveTrackerBoardEdit = () => {},
      columns = [],
      textareaFields = [],
      blankPriorityFields = [],
      renderTrackerBoardHeaderCell = renderTrackerBoardHeaderCellFallback,
      renderTrackerBoardCell = renderTrackerBoardCellFallback,
      renderTrackerBoardEditingCell = renderTrackerBoardEditingCellFallback,
      sortTrackerBoardEntriesFallback: sortEntriesFallback = sortTrackerBoardEntriesFallback,
    } = context;
    const {
      escapeHtml = (value) => String(value ?? ""),
    } = helpers;

    if (typeof dom === "undefined" || !dom || typeof state === "undefined" || !state || !dom.trackerBoard) {
      return;
    }

    const renderEntries = Array.isArray(entries) ? entries : [];
    if (!renderEntries.length) {
      const emptyView = buildTrackerBoardEmptyStateView({
        emptyHtml: "?몃옒而??됱쓣 遺덈윭?ㅻ㈃ ?ш린???쒕줈 ?쒖떆?⑸땲??",
      }) || {
        html: "?몃옒而??됱쓣 遺덈윭?ㅻ㈃ ?ш린???쒕줈 ?쒖떆?⑸땲??",
        className: "tracker-board-content empty-state",
      };
      dom.trackerBoard.innerHTML = emptyView.html;
      dom.trackerBoard.className = emptyView.className || "tracker-board-content empty-state";
      return;
    }

    dom.trackerBoard.className = "tracker-board-content";
    dom.trackerBoard.innerHTML = buildTrackerBoardMarkup(entries, {
      columns,
      currentSortField: state.trackerBoardSort?.fieldName || "",
      trackerBoardEdit: state.trackerBoardEdit,
      textareaFields,
      blankPriorityFields,
      page: state.trackerFilters?.page || 1,
      pageSize: state.trackerFilters?.pageSize || 20,
      selectedEntryId: state.selectedEntryId || "",
    }, {
      escapeHtml,
      renderTrackerBoardHeaderCell,
      renderTrackerBoardCell,
      renderTrackerBoardEditingCell,
      sortTrackerBoardEntriesFallback: sortEntriesFallback,
    }) || buildBoardMarkupFallback(entries, {
      columns,
      currentSortField: state.trackerBoardSort?.fieldName || "",
      trackerBoardEdit: state.trackerBoardEdit,
      textareaFields,
      blankPriorityFields,
      page: state.trackerFilters?.page || 1,
      pageSize: state.trackerFilters?.pageSize || 20,
      selectedEntryId: state.selectedEntryId || "",
    }, {
      escapeHtml,
      renderTrackerBoardHeaderCell,
      renderTrackerBoardCell,
      renderTrackerBoardEditingCell,
      sortTrackerBoardEntriesFallback: sortEntriesFallback,
    });

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
        renderTrackerBoardFallback(state.trackerEntries, context, helpers);
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
          renderTrackerBoardFallback(state.trackerEntries, context, helpers);
          return;
        }
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          const entryId = input.getAttribute("data-board-edit-entry-id");
          const fieldName = input.getAttribute("data-board-edit-field");
          if (!entryId || !fieldName) {
            return;
          }
          void saveTrackerBoardEdit({ entryId, fieldName });
        }
      });
    }
  }

  globalObject.SPMSTrackerRenderFallbackBoardRuntime = {
    renderTrackerBoardCellFallback,
    renderTrackerBoardEditingCellFallback,
    buildTrackerBoardMarkupFallback,
    renderTrackerBoardHeaderCellFallback,
    isTrackerBoardBlankValueFallback,
    sortTrackerBoardEntriesFallback,
    renderTrackerBoardFallback,
  };
})(window);
