(function attachSPMSTrackerBoardRuntime(globalObject) {
  function buildTrackerBoardHeaderCell(column, options = {}) {
    const {
      trackerBoardBlankPriorityFields = new Set(),
      trackerBoardSort = { fieldName: "" },
      escapeHtml = (value) => String(value ?? ""),
    } = options;
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
          <span class="tracker-board-sort-meta mono">${active ? "빈 값 우선" : "클릭 시 빈 값 우선"}</span>
        </button>
      </th>
    `;
  }

  function buildTrackerBoardEditingCellMarkup(payload, helpers = {}) {
    const {
      entry,
      fieldName,
      label,
      value,
      saving,
      errorMessage,
    } = payload;
    const {
      escapeHtml = (text) => String(text ?? ""),
      textareaFields = new Set(),
    } = helpers;
    const textarea = textareaFields.has(fieldName);
    const inputMarkup = textarea
      ? `<textarea
        class="tracker-board-edit-input tracker-board-edit-input-textarea"
        rows="${fieldName === "progress_note" ? "4" : "3"}"
        data-board-edit-input="true"
        data-board-edit-entry-id="${escapeHtml(entry.id)}"
        data-board-edit-field="${escapeHtml(fieldName)}"
        data-board-edit-active="true"
        ${saving ? "disabled" : ""}
      >${escapeHtml(value || "")}</textarea>`
      : `<input
        class="tracker-board-edit-input"
        type="text"
        value="${escapeHtml(value || "")}"
        data-board-edit-input="true"
        data-board-edit-entry-id="${escapeHtml(entry.id)}"
        data-board-edit-field="${escapeHtml(fieldName)}"
        data-board-edit-active="true"
        ${saving ? "disabled" : ""}
      />`;
    return `
      <td class="tracker-board-cell tracker-board-cell-editing">
        <form
          class="tracker-board-edit-form"
          data-board-edit-form="true"
          data-board-edit-entry-id="${escapeHtml(entry.id)}"
          data-board-edit-field="${escapeHtml(fieldName)}"
        >
          <span class="tracker-board-edit-label">${escapeHtml(label)}</span>
          ${inputMarkup}
          <div class="tracker-board-edit-actions">
            <button class="primary-button tracker-board-edit-save" type="submit" ${saving ? "disabled" : ""}>저장</button>
            <button class="ghost-button tracker-board-edit-cancel" type="button" data-board-edit-cancel="true" ${saving ? "disabled" : ""}>취소</button>
          </div>
          <p class="tracker-board-edit-hint mono">${textarea ? "Enter 저장 · Shift+Enter 줄바꿈 · Esc 취소" : "Enter 저장 · Esc 취소"}</p>
          ${errorMessage ? `<p class="tracker-board-edit-error">${escapeHtml(errorMessage)}</p>` : ""}
        </form>
      </td>
    `;
  }

  function buildTrackerBoardCellMarkup(payload, helpers = {}) {
    const {
      entry,
      column,
      displayNo,
    } = payload;
    const {
      escapeHtml = (text) => String(text ?? ""),
    } = helpers;
    if (column.key === "display_no") {
      return `<td>${displayNo}</td>`;
    }
    const value = entry[column.key] || "";
    if (!column.editable) {
      return `<td>${escapeHtml(value || "-")}</td>`;
    }
    const overrideClass = entry.overridden_fields.includes(column.key) ? " is-overridden" : "";
    return `
      <td class="tracker-board-cell${overrideClass}">
        <button
          class="tracker-board-edit-trigger"
          type="button"
          data-board-edit-trigger="true"
          data-board-edit-entry-id="${escapeHtml(entry.id)}"
          data-board-edit-field="${escapeHtml(column.key)}"
        >
          <span class="tracker-board-cell-value">${escapeHtml(value || "-")}</span>
          <span class="tracker-board-cell-meta mono">${entry.overridden_fields.includes(column.key) ? "override" : "클릭해 수정"}</span>
        </button>
      </td>
    `;
  }

  function renderTrackerBoardHeaderCell(column, options = {}) {
    return buildTrackerBoardHeaderCell(column, options);
  }

  function renderTrackerBoardCell(payload, helpers = {}) {
    const {
      entry,
      column,
      displayNo,
      trackerBoardEdit = null,
    } = payload;
    if (trackerBoardEdit?.entryId === entry?.id && trackerBoardEdit?.fieldName === column?.key) {
      return buildTrackerBoardEditingCellMarkup(
        {
          entry,
          fieldName: column.key,
          label: column.label,
          value: trackerBoardEdit.draftValue,
          saving: trackerBoardEdit.saving,
          errorMessage: trackerBoardEdit.errorMessage,
        },
        helpers,
      );
    }
    return buildTrackerBoardCellMarkup(
      {
        entry,
        column,
        displayNo,
      },
      helpers,
    );
  }

  function renderTrackerBoardEditingCell(payload, helpers = {}) {
    return buildTrackerBoardEditingCellMarkup(payload, helpers);
  }

  function isTrackerBoardBlankValue(value) {
    return !String(value ?? "").trim();
  }

  globalObject.SPMSTrackerBoardRuntime = {
    buildTrackerBoardCellMarkup,
    buildTrackerBoardEditingCellMarkup,
    buildTrackerBoardHeaderCell,
    renderTrackerBoardCell,
    renderTrackerBoardEditingCell,
    renderTrackerBoardHeaderCell,
    isTrackerBoardBlankValue,
  };
})(window);
