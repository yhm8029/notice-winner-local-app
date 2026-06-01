(function attachAdminGoogleSheetsRuntime(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function isAdminGoogleSheetTabKey(value) {
    return /^sheet-\d+$/.test(String(value ?? "").trim());
  }

  function normalizeTabEntry(tab, fallbackKey) {
    const source = tab && typeof tab === "object" ? tab : {};
    const key = String(source.key ?? fallbackKey ?? "").trim();
    const rawTitle = String(source.raw_title ?? source.rawTitle ?? "").trim();
    const displayTitle = String(source.display_title ?? source.displayTitle ?? "").trim();
    const label = displayTitle || rawTitle || key;
    const sheetIdValue = source.sheet_id ?? source.sheetId ?? null;
    const sheetOrderValue = source.sheet_order ?? source.sheetOrder ?? 0;
    const sheetId = Number(sheetIdValue);
    const sheetOrder = Number(sheetOrderValue);

    return {
      key,
      label,
      rawTitle,
      sheetId: Number.isFinite(sheetId) ? sheetId : 0,
      sheetOrder: Number.isFinite(sheetOrder) ? sheetOrder : 0,
    };
  }

  function normalizeCellEntry(cell) {
    if (cell && typeof cell === "object" && !Array.isArray(cell)) {
      const text = String(cell.text ?? cell.value ?? "").trim();
      const href = String(cell.href ?? cell.url ?? "").trim();
      return { text, href };
    }
    return { text: String(cell ?? "").trim(), href: "" };
  }

  function normalizeFilterText(value) {
    return String(value ?? "").trim().toLowerCase();
  }

  const ADMIN_GOOGLE_SHEET_BLANK_LABEL = "빈값";
  const ADMIN_GOOGLE_SHEET_BLANK_VALUE = "__SPMS_ADMIN_GOOGLE_SHEET_BLANK__";

  function getAdminGoogleSheetVisibleText(cell) {
    const normalized = normalizeCellEntry(cell);
    return normalized.text || normalized.href || ADMIN_GOOGLE_SHEET_BLANK_LABEL;
  }

  function getAdminGoogleSheetFilterValue(cell) {
    const normalized = normalizeCellEntry(cell);
    return normalized.text || normalized.href || ADMIN_GOOGLE_SHEET_BLANK_VALUE;
  }

  function getAdminGoogleSheetOptionLabel(value) {
    const normalizedValue = String(value ?? "").trim();
    if (normalizedValue === ADMIN_GOOGLE_SHEET_BLANK_VALUE) {
      return ADMIN_GOOGLE_SHEET_BLANK_LABEL;
    }
    if (normalizedValue === ADMIN_GOOGLE_SHEET_BLANK_LABEL) {
      return `"${ADMIN_GOOGLE_SHEET_BLANK_LABEL}"`;
    }
    return normalizedValue;
  }

  function compareAdminGoogleSheetOptionValues(left, right) {
    if (left === ADMIN_GOOGLE_SHEET_BLANK_VALUE && right !== ADMIN_GOOGLE_SHEET_BLANK_VALUE) {
      return -1;
    }
    if (right === ADMIN_GOOGLE_SHEET_BLANK_VALUE && left !== ADMIN_GOOGLE_SHEET_BLANK_VALUE) {
      return 1;
    }
    const leftLabel = getAdminGoogleSheetOptionLabel(left);
    const rightLabel = getAdminGoogleSheetOptionLabel(right);
    const labelCompare = leftLabel.localeCompare(rightLabel, "ko");
    if (labelCompare !== 0) {
      return labelCompare;
    }
    return String(left ?? "").localeCompare(String(right ?? ""), "ko");
  }

  function normalizeAdminGoogleSheetState(sheetState) {
    const source = sheetState && typeof sheetState === "object" ? sheetState : {};
    const columnsSource = source.columns && typeof source.columns === "object" ? source.columns : {};
    const columns = {};

    Object.entries(columnsSource).forEach(([columnKey, columnState]) => {
      const columnIndex = Number(columnKey);
      if (!Number.isInteger(columnIndex) || columnIndex < 0) {
        return;
      }

      const selectedValuesSource = Array.isArray(columnState?.selectedValues)
        ? columnState.selectedValues
        : Array.isArray(columnState)
          ? columnState
          : [];
      const selectedValues = Array.from(new Set(
        selectedValuesSource
          .map((value) => String(value ?? "").trim())
          .filter(Boolean),
      ));

      if (selectedValues.length) {
        columns[String(columnIndex)] = { selectedValues };
      }
    });

    const sortColumnIndex = Number(source.sort?.columnIndex);
    const sortDirection = String(source.sort?.direction ?? "").trim();
    const sort = Number.isInteger(sortColumnIndex) && sortColumnIndex >= 0 && (sortDirection === "asc" || sortDirection === "desc")
      ? { columnIndex: sortColumnIndex, direction: sortDirection }
      : null;

    return { sort, columns };
  }

  function buildAdminGoogleSheetOptionValueLists(rows, columnCount) {
    return Array.from({ length: columnCount }, (_, index) => {
      const seen = new Set();
      return rows
        .map((row) => getAdminGoogleSheetFilterValue(row[index]))
        .filter((value) => {
          if (seen.has(value)) {
            return false;
          }
          seen.add(value);
          return true;
        })
        .sort(compareAdminGoogleSheetOptionValues);
    });
  }

  function buildAdminGoogleSheetOptionLists(optionValueLists) {
    return optionValueLists.map((values) => values.map((value) => getAdminGoogleSheetOptionLabel(value)));
  }

  function sanitizeAdminGoogleSheetState(sheetState, columnCount, optionValueLists) {
    const normalizedState = normalizeAdminGoogleSheetState(sheetState);
    const columns = {};

    Object.entries(normalizedState.columns).forEach(([columnKey, columnState]) => {
      const columnIndex = Number(columnKey);
      if (!Number.isInteger(columnIndex) || columnIndex < 0 || columnIndex >= columnCount) {
        return;
      }

      const optionList = optionValueLists[columnIndex] || [];
      const optionSet = new Set(optionList);
      const selectedValues = Array.from(new Set(
        (Array.isArray(columnState?.selectedValues) ? columnState.selectedValues : [])
          .map((value) => String(value ?? "").trim())
          .filter((value) => optionSet.has(value)),
      ));

      if (selectedValues.length > 0 && selectedValues.length < optionList.length) {
        columns[String(columnIndex)] = { selectedValues };
      }
    });

    const sort = normalizedState.sort && normalizedState.sort.columnIndex < columnCount
      ? normalizedState.sort
      : null;

    return { sort, columns };
  }

  function rowMatchesAdminGoogleSheetState(row, sheetState) {
    return Object.entries(sheetState.columns).every(([columnKey, columnState]) => {
      const columnIndex = Number(columnKey);
      const selectedValues = Array.isArray(columnState?.selectedValues) ? columnState.selectedValues : [];
      if (!selectedValues.length) {
        return true;
      }
      return selectedValues.includes(getAdminGoogleSheetFilterValue(row[columnIndex]));
    });
  }

  function sortAdminGoogleSheetRows(rows, sort) {
    if (!sort) {
      return rows.slice();
    }

    const direction = sort.direction === "desc" ? -1 : 1;
    return rows
      .slice()
      .sort((left, right) => getAdminGoogleSheetVisibleText(left[sort.columnIndex])
        .localeCompare(getAdminGoogleSheetVisibleText(right[sort.columnIndex]), "ko") * direction);
  }

  function buildAdminGoogleSheetFilterModel(payload, sheetState = {}) {
    const headers = Array.isArray(payload?.header_cells)
      ? payload.header_cells.map((cell) => normalizeCellEntry(cell))
      : (Array.isArray(payload?.headers) ? payload.headers : []).map((cell) => normalizeCellEntry(cell));
    const rows = Array.isArray(payload?.row_cells)
      ? payload.row_cells.map((row) => (Array.isArray(row) ? row : []).map((cell) => normalizeCellEntry(cell)))
      : (Array.isArray(payload?.rows) ? payload.rows : []).map((row) => (Array.isArray(row) ? row : []).map((cell) => normalizeCellEntry(cell)));
    const columnCount = headers.length || Math.max(0, ...rows.map((row) => row.length));
    const optionValueLists = buildAdminGoogleSheetOptionValueLists(rows, columnCount);
    const optionLists = buildAdminGoogleSheetOptionLists(optionValueLists);
    const normalizedSheetState = sanitizeAdminGoogleSheetState(sheetState, columnCount, optionValueLists);
    const filteredRows = sortAdminGoogleSheetRows(
      rows.filter((row) => rowMatchesAdminGoogleSheetState(row, normalizedSheetState)),
      normalizedSheetState.sort,
    );

    return {
      headers,
      rows,
      filteredRows,
      optionLists,
      optionValueLists,
      columnCount,
      sheetState: normalizedSheetState,
    };
  }

  function buildAdminGoogleSheetPopupModel(model, popupState) {
    if (!popupState || popupState.open !== true) {
      return null;
    }

    const columnIndex = Number(popupState.columnIndex);
    if (!Number.isInteger(columnIndex) || columnIndex < 0 || columnIndex >= Number(model?.columnCount ?? 0)) {
      return null;
    }

    const allValueKeys = Array.isArray(model?.optionValueLists?.[columnIndex])
      ? model.optionValueLists[columnIndex].slice()
      : Array.isArray(model?.optionLists?.[columnIndex])
        ? model.optionLists[columnIndex].slice()
      : [];
    const appliedSelectedValues = Array.isArray(model?.sheetState?.columns?.[String(columnIndex)]?.selectedValues)
      ? model.sheetState.columns[String(columnIndex)].selectedValues.slice()
      : [];
    const fallbackPendingSelectedValues = appliedSelectedValues.length > 0 ? appliedSelectedValues : allValueKeys;
    const searchDraft = String(popupState.searchDraft ?? "").trim();
    const normalizedSearch = normalizeFilterText(searchDraft);
    const visibleValueKeys = normalizedSearch
      ? allValueKeys.filter((value) => normalizeFilterText(getAdminGoogleSheetOptionLabel(value)).includes(normalizedSearch))
      : allValueKeys.slice();
    const pendingSelectedSet = new Set(
      Array.isArray(popupState.pendingSelectedValues)
        ? popupState.pendingSelectedValues
          .map((value) => String(value ?? "").trim())
          .filter((value) => allValueKeys.includes(value))
        : fallbackPendingSelectedValues,
    );
    const visibleSelectedCount = visibleValueKeys.filter((value) => pendingSelectedSet.has(value)).length;

    return {
      columnIndex,
      allValues: allValueKeys.map((value) => getAdminGoogleSheetOptionLabel(value)),
      allValueKeys,
      visibleValues: visibleValueKeys.map((value) => getAdminGoogleSheetOptionLabel(value)),
      visibleValueKeys,
      searchDraft,
      allVisibleSelected: visibleValueKeys.length > 0 && visibleSelectedCount === visibleValueKeys.length,
      partiallySelected: visibleSelectedCount > 0 && visibleSelectedCount < visibleValueKeys.length,
      pendingSelectedValues: Array.from(pendingSelectedSet),
      pendingSortDirection: popupState.pendingSortDirection === "desc"
        ? "desc"
        : popupState.pendingSortDirection === "asc"
          ? "asc"
          : "",
    };
  }

  function normalizeFilterEntry(filter) {
    return {
      query: String(filter?.query ?? ""),
      selected: String(filter?.selected ?? "").trim(),
    };
  }

  function isSafeHref(value) {
    const href = String(value ?? "").trim();
    return /^https?:\/\/[^/\s?#]/i.test(href);
  }

  function renderCellHtml(cell, escapeHtmlHelper) {
    const normalized = normalizeCellEntry(cell);
    const text = normalized.text || normalized.href || "";
    if (isSafeHref(normalized.href)) {
      return `<a class="admin-google-sheet-link" href="${escapeHtmlHelper(normalized.href)}" target="_blank" rel="noreferrer">${escapeHtmlHelper(text)}</a>`;
    }
    return escapeHtmlHelper(text);
  }

  function buildAdminGoogleSheetTabs(bootstrap) {
    const tabsSource = bootstrap && typeof bootstrap === "object" ? bootstrap.tabs : null;
    const entries = Array.isArray(tabsSource)
      ? tabsSource.map((tab) => normalizeTabEntry(tab, tab?.key))
      : tabsSource && typeof tabsSource === "object"
        ? Object.entries(tabsSource).map(([key, tab]) => normalizeTabEntry(tab, key))
        : [];

    return entries
      .slice()
      .sort((left, right) => Number(left.sheetOrder || 0) - Number(right.sheetOrder || 0))
      .map(({ sheetOrder, ...tab }) => tab);
  }

  function buildAdminGoogleSheetStatusView(bootstrap, activeSheet) {
    const syncStatus = String(bootstrap?.sync_status ?? "loading").trim() || "loading";
    const syncedAt = String(
      bootstrap?.last_successful_sync_at
      ?? bootstrap?.synced_at
      ?? bootstrap?.last_synced_at
      ?? "",
    ).trim();
    const activeSheetLabel = String(
      activeSheet?.label
      ?? activeSheet?.display_title
      ?? activeSheet?.raw_title
      ?? activeSheet?.key
      ?? "",
    ).trim();

    return {
      html: `
        <div class="admin-google-sheet-status-view" data-sync-status="${escapeHtml(syncStatus)}">
          <span class="admin-google-sheet-status-badge status-${escapeHtml(syncStatus)}">${escapeHtml(syncStatus)}</span>
          <span class="admin-google-sheet-status-synced-at">${escapeHtml(syncedAt || "-")}</span>
          <span class="admin-google-sheet-status-active-sheet">${escapeHtml(activeSheetLabel)}</span>
        </div>
      `,
    };
  }

  function buildLegacyColumnOptions(rows, columnIndex) {
    return Array.from(
      new Set(
        rows
          .map((row) => normalizeCellEntry(row[columnIndex]).text)
          .filter(Boolean),
      ),
    ).sort((left, right) => left.localeCompare(right, "ko"));
  }

  function sanitizeFilters(filters, columnCount, optionSets) {
    const entries = Array.from({ length: columnCount }, (_, index) => normalizeFilterEntry(filters?.[index]));
    return entries.map((entry, index) => ({
      query: entry.query,
      selected: optionSets[index].has(entry.selected) ? entry.selected : "",
    }));
  }

  function rowMatchesFilters(row, filters) {
    return filters.every((filter, index) => {
      const entry = normalizeFilterEntry(filter);
      const cellText = normalizeCellEntry(row[index]).text;
      const normalizedCellText = normalizeFilterText(cellText);
      const query = normalizeFilterText(entry.query);
      if (query && !normalizedCellText.includes(query)) {
        return false;
      }
      if (entry.selected && cellText !== entry.selected) {
        return false;
      }
      return true;
    });
  }

  function buildLegacyAdminGoogleSheetFilterModel(payload, filters = []) {
    const headers = Array.isArray(payload?.header_cells)
      ? payload.header_cells.map((cell) => normalizeCellEntry(cell))
      : (Array.isArray(payload?.headers) ? payload.headers : []).map((cell) => normalizeCellEntry(cell));
    const rows = Array.isArray(payload?.row_cells)
      ? payload.row_cells.map((row) => (Array.isArray(row) ? row : []).map((cell) => normalizeCellEntry(cell)))
      : (Array.isArray(payload?.rows) ? payload.rows : []).map((row) => (Array.isArray(row) ? row : []).map((cell) => normalizeCellEntry(cell)));
    const columnCount = headers.length || Math.max(0, ...rows.map((row) => row.length));
    const optionLists = Array.from({ length: columnCount }, (_, index) => buildLegacyColumnOptions(rows, index));
    const optionSets = optionLists.map((items) => new Set(items));
    const normalizedFilters = sanitizeFilters(filters, columnCount, optionSets);
    const filteredRows = rows.filter((row) => rowMatchesFilters(row, normalizedFilters));

    return {
      headers,
      rows,
      filteredRows,
      filters: normalizedFilters,
      optionLists,
      columnCount,
    };
  }

  function renderFilterCell(filter, options, columnIndex, escapeHtmlHelper) {
    const normalizedFilter = normalizeFilterEntry(filter);
    const optionHtml = options.map((value) => `
      <option value="${escapeHtmlHelper(value)}"${value === normalizedFilter.selected ? " selected" : ""}>${escapeHtmlHelper(value)}</option>
    `).join("");

    return `
      <th class="admin-google-sheet-filter-cell">
        <input
          class="admin-google-sheet-filter-input"
          type="text"
          value="${escapeHtmlHelper(normalizedFilter.query)}"
          placeholder="검색"
          data-admin-google-sheet-filter-kind="query"
          data-admin-google-sheet-filter-index="${columnIndex}"
        />
        <select
          class="admin-google-sheet-filter-select"
          data-admin-google-sheet-filter-kind="selected"
          data-admin-google-sheet-filter-index="${columnIndex}"
        >
          <option value="">전체</option>
          ${optionHtml}
        </select>
      </th>
    `;
  }

  function renderAdminGoogleSheetPopup(model, popupState, escapeHtmlHelper) {
    if (!model) {
      return "";
    }

    const selectedSet = new Set(Array.isArray(model.pendingSelectedValues) ? model.pendingSelectedValues : []);
    const valueOptionsHtml = model.visibleValueKeys.map((value, index) => `
      <label class="admin-google-sheet-popup-value">
        <input
          type="checkbox"
          data-admin-google-sheet-popup-value="${escapeHtmlHelper(value)}"
          ${selectedSet.has(value) ? "checked" : ""}
        />
        <span>${escapeHtmlHelper(model.visibleValues[index] || getAdminGoogleSheetOptionLabel(value))}</span>
      </label>
    `).join("");

    return `
      <div class="admin-google-sheet-popup" data-admin-google-sheet-popup-root="1">
        <div class="admin-google-sheet-popup-actions">
          <button type="button" data-admin-google-sheet-popup-sort="asc">오름차순</button>
          <button type="button" data-admin-google-sheet-popup-sort="desc">내림차순</button>
        </div>
        <div class="admin-google-sheet-popup-search">
          <input
            type="search"
            value="${escapeHtmlHelper(popupState?.searchDraft ?? model.searchDraft ?? "")}"
            data-admin-google-sheet-popup-search="1"
          />
        </div>
        <label class="admin-google-sheet-popup-select-all">
          <input
            type="checkbox"
            data-admin-google-sheet-popup-select-all="1"
            ${model.allVisibleSelected ? "checked" : ""}
          />
          <span>전체 선택</span>
        </label>
        <div class="admin-google-sheet-popup-values">
          ${valueOptionsHtml}
        </div>
        <div class="admin-google-sheet-popup-footer">
          <button type="button" data-admin-google-sheet-popup-action="cancel">취소</button>
          <button type="button" data-admin-google-sheet-popup-action="confirm">적용</button>
        </div>
      </div>
    `;
  }

  function renderAdminGoogleSheetHeaderCell(header, columnIndex, model, popupModel, popupState, escapeHtmlHelper) {
    const normalizedSheetState = model.sheetState || { sort: null, columns: {} };
    const columnState = normalizedSheetState.columns?.[String(columnIndex)] || null;
    const isFiltered = Array.isArray(columnState?.selectedValues) && columnState.selectedValues.length > 0;
    const isSorted = normalizedSheetState.sort?.columnIndex === columnIndex;
    const isOpen = popupModel?.columnIndex === columnIndex;
    const headerEntry = normalizeCellEntry(header);
    const headerLabel = headerEntry.text || headerEntry.href || "";
    const buttonClasses = [
      "admin-google-sheet-trigger-button",
      (isFiltered || isSorted || isOpen) ? "is-active" : "",
      isFiltered ? "is-filtered" : "",
      isSorted ? "is-sorted" : "",
      isOpen ? "is-open" : "",
    ].filter(Boolean).join(" ");

    return `
      <th class="admin-google-sheet-header-cell">
        <button
          type="button"
          class="${buttonClasses}"
          data-admin-google-sheet-trigger-index="${columnIndex}"
          aria-expanded="${isOpen ? "true" : "false"}"
        >
          <span class="admin-google-sheet-trigger-label">${escapeHtmlHelper(headerLabel)}</span>
          <span class="admin-google-sheet-trigger-icon" aria-hidden="true">▾</span>
        </button>
        ${isOpen ? renderAdminGoogleSheetPopup(popupModel, popupState, escapeHtmlHelper) : ""}
      </th>
    `;
  }

  function buildAdminGoogleSheetTableView(payload, helpers = {}) {
    const {
      escapeHtml: escapeHtmlHelper = escapeHtml,
      sheetKey = "",
      filters = [],
      sheetState = null,
      popupState = null,
      minTableHeightPx = 0,
    } = helpers;

    const hasNormalizedSheetState = sheetState !== undefined && sheetState !== null;
    const hasNormalizedPopupState = popupState !== undefined && popupState !== null;
    const useLegacyFilters = Array.isArray(filters)
      && !hasNormalizedSheetState
      && !hasNormalizedPopupState;
    const model = useLegacyFilters
      ? buildLegacyAdminGoogleSheetFilterModel(payload, filters)
      : buildAdminGoogleSheetFilterModel(payload, sheetState || {});
    const normalizedSheetKey = String(sheetKey ?? "").trim();
    const popupMatchesSheet = hasNormalizedPopupState
      && popupState?.open === true
      && (!normalizedSheetKey || String(popupState?.sheetKey ?? "").trim() === normalizedSheetKey);
    const popupModel = popupMatchesSheet
      ? buildAdminGoogleSheetPopupModel(model, popupState)
      : null;
    const headerCount = useLegacyFilters ? model.headers.length : model.columnCount;
    const headerHtml = Array.from({ length: headerCount }, (_, columnIndex) => renderAdminGoogleSheetHeaderCell(
      model.headers[columnIndex] || { text: "", href: "" },
      columnIndex,
      model,
      popupModel,
      popupState,
      escapeHtmlHelper,
    )).join("");
    const modelSheetState = model.sheetState || { sort: null, columns: {} };
    const filterRowState = useLegacyFilters
      ? model.filters
      : Array.from({ length: model.columnCount }, (_, index) => ({
          query: "",
          selected: (modelSheetState.columns[String(index)]?.selectedValues || [])[0] || "",
        }));
    const filterRowHtml = Array.from({ length: model.columnCount }, (_, index) => renderFilterCell(
      filterRowState[index],
      model.optionLists[index],
      index,
      escapeHtmlHelper,
    )).join("");
    const bodyRows = model.filteredRows.length
      ? model.filteredRows.map((row) => {
          const cells = Array.from({ length: model.columnCount }, (_, index) => normalizeCellEntry(row[index]));
          return `<tr>${cells.map((cell) => `<td>${renderCellHtml(cell, escapeHtmlHelper)}</td>`).join("")}</tr>`;
        }).join("")
      : `<tr class="admin-google-sheet-empty-row"><td colspan="${Math.max(1, model.columnCount)}">조건에 맞는 데이터가 없습니다.</td></tr>`;

    const normalizedMinHeight = Number(minTableHeightPx);
    const wrapperStyle = Number.isFinite(normalizedMinHeight) && normalizedMinHeight > 0
      ? ` style="--admin-google-sheet-min-table-height: ${escapeHtmlHelper(String(Math.round(normalizedMinHeight)))}px; min-height: var(--admin-google-sheet-min-table-height);"`
      : "";

    return {
      html: `
        <div class="admin-google-sheet-table-wrap"${wrapperStyle}>
          <table class="admin-google-sheet-table">
            <thead>
              <tr>${headerHtml}</tr>
              ${useLegacyFilters ? `<tr class="admin-google-sheet-filter-row">${filterRowHtml}</tr>` : ""}
            </thead>
            <tbody>${bodyRows}</tbody>
          </table>
        </div>
      `,
      filters: model.filters || filterRowState,
      sheetState: modelSheetState,
      popupState: popupState || null,
    };
  }

  global.SPMSAdminGoogleSheetsRuntime = Object.freeze({
    isAdminGoogleSheetTabKey,
    buildAdminGoogleSheetTabs,
    buildAdminGoogleSheetStatusView,
    normalizeAdminGoogleSheetState,
    buildAdminGoogleSheetFilterModel,
    buildAdminGoogleSheetPopupModel,
    buildAdminGoogleSheetTableView,
  });
})(window);
