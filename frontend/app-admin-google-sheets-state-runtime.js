(function attachAppAdminGoogleSheetsStateRuntime(global) {
  function createAppAdminGoogleSheetsStateRuntime(options = {}) {
    const state = options?.state || {};
    const dom = options?.dom || {};
    const root = options?.window || global;
    const requestRenderAdminEmbedPanel = typeof options?.renderAdminEmbedPanel === "function"
      ? options.renderAdminEmbedPanel
      : function noop() {};
    const findResolvedAdminTab = typeof options?.findResolvedAdminTab === "function"
      ? options.findResolvedAdminTab
      : function defaultFindResolvedAdminTab(tab) {
        return tab && typeof tab === "object" ? tab : null;
      };

    function getGoogleSheetsRuntime() {
      return options?.googleSheetsRuntime || root.SPMSAdminGoogleSheetsRuntime || null;
    }

    function requireGoogleSheetsRuntime() {
      const runtime = getGoogleSheetsRuntime();
      if (!runtime || typeof runtime !== "object") {
        throw new Error("SPMSAdminGoogleSheetsRuntime is required before app.js loads");
      }
      return runtime;
    }

    function normalizeAdminGoogleSheetsFilterState(sheetState) {
      const runtime = getGoogleSheetsRuntime();
      if (runtime?.normalizeAdminGoogleSheetState) {
        return runtime.normalizeAdminGoogleSheetState(sheetState);
      }

      const source = sheetState && typeof sheetState === "object" ? sheetState : {};
      const columnsSource = source.columns && typeof source.columns === "object" ? source.columns : {};
      const columns = {};

      Object.entries(columnsSource).forEach(([columnKey, columnState]) => {
        const columnIndex = Number(columnKey);
        if (!Number.isInteger(columnIndex) || columnIndex < 0) {
          return;
        }

        const selectedValues = Array.from(new Set(
          (Array.isArray(columnState?.selectedValues) ? columnState.selectedValues : [])
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

    function adminGoogleSheetsFilterStateEqual(left, right) {
      const leftState = normalizeAdminGoogleSheetsFilterState(left);
      const rightState = normalizeAdminGoogleSheetsFilterState(right);
      const leftSort = leftState.sort;
      const rightSort = rightState.sort;

      if (Boolean(leftSort) !== Boolean(rightSort)) {
        return false;
      }
      if (leftSort && (leftSort.columnIndex !== rightSort.columnIndex || leftSort.direction !== rightSort.direction)) {
        return false;
      }

      const leftColumns = Object.keys(leftState.columns).map(Number).sort((a, b) => a - b);
      const rightColumns = Object.keys(rightState.columns).map(Number).sort((a, b) => a - b);
      if (leftColumns.length !== rightColumns.length) {
        return false;
      }

      return leftColumns.every((columnIndex, index) => {
        const rightColumnIndex = rightColumns[index];
        if (columnIndex !== rightColumnIndex) {
          return false;
        }
        const leftValues = Array.isArray(leftState.columns[String(columnIndex)]?.selectedValues)
          ? leftState.columns[String(columnIndex)].selectedValues
          : [];
        const rightValues = Array.isArray(rightState.columns[String(rightColumnIndex)]?.selectedValues)
          ? rightState.columns[String(rightColumnIndex)].selectedValues
          : [];
        if (leftValues.length !== rightValues.length) {
          return false;
        }
        return leftValues.every((value, valueIndex) => value === rightValues[valueIndex]);
      });
    }

    function getAdminGoogleSheetsFilterState(sheetKey) {
      const key = String(sheetKey || "").trim();
      if (!key) {
        return { sort: null, columns: {} };
      }
      return normalizeAdminGoogleSheetsFilterState(state.adminGoogleSheetsFilterStateByKey?.[key]);
    }

    function getAdminGoogleSheetMinHeight(sheetKey) {
      const key = String(sheetKey || "").trim();
      if (!key) {
        return 0;
      }
      const height = Number(state.adminGoogleSheetMinHeightByKey?.[key] || 0);
      return Number.isFinite(height) && height > 0 ? height : 0;
    }

    function measureAdminGoogleSheetTableHeight() {
      const tableWrap = dom.adminGoogleSheetTable?.querySelector?.(".admin-google-sheet-table-wrap");
      if (!tableWrap) {
        return 0;
      }
      const rectHeight = Number(tableWrap.getBoundingClientRect?.().height || 0);
      const offsetHeight = Number(tableWrap.offsetHeight || 0);
      const scrollHeight = Number(tableWrap.scrollHeight || 0);
      const measuredHeight = Math.max(rectHeight, offsetHeight, scrollHeight, 0);
      return Number.isFinite(measuredHeight) && measuredHeight > 0 ? Math.round(measuredHeight) : 0;
    }

    function syncAdminGoogleSheetMinHeight(sheetKey) {
      const key = String(sheetKey || "").trim();
      if (!key) {
        return { changed: false, value: 0 };
      }
      const measuredHeight = measureAdminGoogleSheetTableHeight();
      if (measuredHeight <= 0) {
        return { changed: false, value: getAdminGoogleSheetMinHeight(key) };
      }
      const currentHeight = getAdminGoogleSheetMinHeight(key);
      if (measuredHeight <= currentHeight) {
        return { changed: false, value: currentHeight };
      }
      state.adminGoogleSheetMinHeightByKey[key] = measuredHeight;
      return { changed: true, value: measuredHeight };
    }

    function sanitizeAdminGoogleSheetsFilterStateForSheet(sheetKey, sheetState) {
      const key = String(sheetKey || "").trim();
      const normalized = normalizeAdminGoogleSheetsFilterState(sheetState);
      const runtime = getGoogleSheetsRuntime();
      if (!key || !runtime?.buildAdminGoogleSheetFilterModel) {
        return normalized;
      }
      const payload = state.adminGoogleSheetPayloadByKey?.[key];
      if (!payload) {
        return normalized;
      }
      return runtime.buildAdminGoogleSheetFilterModel(payload, normalized).sheetState || normalized;
    }

    function setAdminGoogleSheetsFilterState(sheetKey, sheetState, nextOptions) {
      const settings = nextOptions && typeof nextOptions === "object" ? nextOptions : {};
      const key = String(sheetKey || "").trim();
      if (!key) {
        return;
      }
      const sanitized = sanitizeAdminGoogleSheetsFilterStateForSheet(key, sheetState);
      if (adminGoogleSheetsFilterStateEqual(state.adminGoogleSheetsFilterStateByKey?.[key], sanitized)) {
        if (settings.render) {
          requestRenderAdminEmbedPanel();
        }
        return;
      }
      if (!Object.keys(sanitized.columns).length && !sanitized.sort) {
        delete state.adminGoogleSheetsFilterStateByKey[key];
      } else {
        state.adminGoogleSheetsFilterStateByKey[key] = sanitized;
      }
      if (settings.render !== false) {
        requestRenderAdminEmbedPanel();
      }
    }

    function normalizeAdminGoogleSheetPopupState(popupState) {
      const source = popupState && typeof popupState === "object" ? popupState : {};
      const open = source.open === true;
      const columnIndexValue = Number(source.columnIndex);
      const pendingSelectedValuesSource = Array.isArray(source.pendingSelectedValues) ? source.pendingSelectedValues : [];
      const pendingSortDirection = String(source.pendingSortDirection ?? "").trim();

      return {
        open,
        sheetKey: open ? String(source.sheetKey ?? "").trim() : "",
        columnIndex: open && Number.isInteger(columnIndexValue) && columnIndexValue >= 0 ? columnIndexValue : -1,
        searchDraft: open ? String(source.searchDraft ?? "") : "",
        pendingSelectedValues: open
          ? Array.from(new Set(
            pendingSelectedValuesSource.map((value) => String(value ?? "").trim()).filter(Boolean),
          ))
          : [],
        pendingSortDirection: open && (pendingSortDirection === "asc" || pendingSortDirection === "desc")
          ? pendingSortDirection
          : "",
      };
    }

    function getAdminGoogleSheetPopupState() {
      return normalizeAdminGoogleSheetPopupState(state.adminGoogleSheetsPopupState);
    }

    function setAdminGoogleSheetPopupState(popupState, nextOptions) {
      state.adminGoogleSheetsPopupState = normalizeAdminGoogleSheetPopupState(popupState);
      if ((nextOptions?.render) !== false) {
        requestRenderAdminEmbedPanel();
      }
    }

    function setAdminGoogleSheetPopupSearch(searchDraft) {
      const popupState = getAdminGoogleSheetPopupState();
      if (!popupState.open) {
        return;
      }
      setAdminGoogleSheetPopupState({
        ...popupState,
        searchDraft: String(searchDraft ?? ""),
      });
    }

    function openAdminGoogleSheetFilterPopup(sheetKey, columnIndex) {
      const key = String(sheetKey || "").trim();
      const columnNumber = Number(columnIndex);
      const runtime = getGoogleSheetsRuntime();
      if (!key || !Number.isInteger(columnNumber) || columnNumber < 0) {
        return;
      }
      const payload = state.adminGoogleSheetPayloadByKey?.[key];
      if (!payload || !runtime?.buildAdminGoogleSheetFilterModel) {
        return;
      }
      const appliedState = getAdminGoogleSheetsFilterState(key);
      const model = runtime.buildAdminGoogleSheetFilterModel(payload, appliedState);
      const allValues = Array.isArray(model.optionValueLists?.[columnNumber])
        ? model.optionValueLists[columnNumber].slice()
        : (Array.isArray(model.optionLists?.[columnNumber]) ? model.optionLists[columnNumber].slice() : []);
      const appliedSelectedValues = Array.isArray(model.sheetState?.columns?.[String(columnNumber)]?.selectedValues)
        ? model.sheetState.columns[String(columnNumber)].selectedValues.slice()
        : [];
      const pendingSelectedValues = appliedSelectedValues.length > 0 ? appliedSelectedValues : allValues;
      const pendingSortDirection = model.sheetState?.sort?.columnIndex === columnNumber
        ? String(model.sheetState.sort.direction || "").trim()
        : "";

      setAdminGoogleSheetPopupState({
        open: true,
        sheetKey: key,
        columnIndex: columnNumber,
        searchDraft: "",
        pendingSelectedValues,
        pendingSortDirection,
      });
    }

    function toggleAdminGoogleSheetPopupValue(value, checked) {
      const popupState = getAdminGoogleSheetPopupState();
      if (!popupState.open) {
        return;
      }
      const nextValue = String(value ?? "").trim();
      if (!nextValue) {
        return;
      }
      const nextSelectedValues = new Set(popupState.pendingSelectedValues);
      if (checked) {
        nextSelectedValues.add(nextValue);
      } else {
        nextSelectedValues.delete(nextValue);
      }
      setAdminGoogleSheetPopupState({
        ...popupState,
        pendingSelectedValues: Array.from(nextSelectedValues),
      });
    }

    function setAdminGoogleSheetPopupSort(direction) {
      const popupState = getAdminGoogleSheetPopupState();
      if (!popupState.open) {
        return;
      }
      const normalizedDirection = String(direction ?? "").trim();
      setAdminGoogleSheetPopupState({
        ...popupState,
        pendingSortDirection: normalizedDirection === "asc" || normalizedDirection === "desc" ? normalizedDirection : "",
      });
    }

    function clearAdminGoogleSheetPopupState(nextOptions) {
      state.adminGoogleSheetsPopupState = {
        open: false,
        sheetKey: "",
        columnIndex: -1,
        searchDraft: "",
        pendingSelectedValues: [],
        pendingSortDirection: "",
      };
      if ((nextOptions?.render) !== false) {
        requestRenderAdminEmbedPanel();
      }
    }

    function clearAdminGoogleSheetPopupStateForTab(nextTab, nextOptions) {
      const popupState = getAdminGoogleSheetPopupState();
      if (!popupState.open) {
        return false;
      }
      const resolvedNextTab = findResolvedAdminTab(nextTab);
      const nextSheetKey = resolvedNextTab?.type === "google_sheet"
        ? String(resolvedNextTab.key || "").trim()
        : "";
      if (nextSheetKey === popupState.sheetKey) {
        return false;
      }
      clearAdminGoogleSheetPopupState(nextOptions);
      return true;
    }

    function confirmAdminGoogleSheetPopup() {
      const popupState = getAdminGoogleSheetPopupState();
      const runtime = getGoogleSheetsRuntime();
      if (!popupState.open) {
        return;
      }

      const key = String(popupState.sheetKey || "").trim();
      const columnIndex = Number(popupState.columnIndex);
      const payload = state.adminGoogleSheetPayloadByKey?.[key];
      if (key && Number.isInteger(columnIndex) && columnIndex >= 0 && payload && runtime?.buildAdminGoogleSheetFilterModel) {
        const appliedState = getAdminGoogleSheetsFilterState(key);
        const nextColumns = { ...(appliedState.columns || {}) };
        const nextSelectedValues = Array.from(new Set(
          popupState.pendingSelectedValues
            .map((value) => String(value ?? "").trim())
            .filter(Boolean),
        ));
        if (nextSelectedValues.length) {
          nextColumns[String(columnIndex)] = { selectedValues: nextSelectedValues };
        } else {
          delete nextColumns[String(columnIndex)];
        }

        const hasPopupSort = popupState.pendingSortDirection === "asc" || popupState.pendingSortDirection === "desc";
        let nextSort = appliedState.sort && Number.isInteger(Number(appliedState.sort.columnIndex))
          ? { columnIndex: Number(appliedState.sort.columnIndex), direction: String(appliedState.sort.direction || "").trim() }
          : null;
        if (hasPopupSort) {
          nextSort = { columnIndex, direction: popupState.pendingSortDirection };
        } else if (nextSort && nextSort.columnIndex === columnIndex) {
          nextSort = null;
        }

        const draftState = {
          sort: nextSort,
          columns: nextColumns,
        };
        const sanitizedState = runtime.buildAdminGoogleSheetFilterModel(payload, draftState).sheetState;
        setAdminGoogleSheetsFilterState(key, sanitizedState, { render: false });
      }

      clearAdminGoogleSheetPopupState({ render: false });
      requestRenderAdminEmbedPanel();
    }

    function cancelAdminGoogleSheetPopup() {
      clearAdminGoogleSheetPopupState();
    }

    function getAdminGoogleSheetTableInteractionSheetKey() {
      return String(dom.adminGoogleSheetTable?.dataset?.adminGoogleSheetActiveSheetKey || "").trim();
    }

    function handleAdminGoogleSheetPopupDismissal(event) {
      const popupState = getAdminGoogleSheetPopupState();
      if (!popupState.open) {
        return false;
      }
      const target = event?.target || null;
      if (target) {
        if (typeof target.closest === "function" && target.closest("[data-admin-google-sheet-popup-root=\"1\"]")) {
          return false;
        }
        if (typeof target.closest === "function" && target.closest("[data-admin-google-sheet-trigger-index]")) {
          return false;
        }
      }
      cancelAdminGoogleSheetPopup();
      return true;
    }

    return {
      requireGoogleSheetsRuntime,
      normalizeAdminGoogleSheetsFilterState,
      adminGoogleSheetsFilterStateEqual,
      getAdminGoogleSheetsFilterState,
      getAdminGoogleSheetMinHeight,
      measureAdminGoogleSheetTableHeight,
      syncAdminGoogleSheetMinHeight,
      sanitizeAdminGoogleSheetsFilterStateForSheet,
      setAdminGoogleSheetsFilterState,
      normalizeAdminGoogleSheetPopupState,
      getAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupState,
      setAdminGoogleSheetPopupSearch,
      openAdminGoogleSheetFilterPopup,
      toggleAdminGoogleSheetPopupValue,
      setAdminGoogleSheetPopupSort,
      clearAdminGoogleSheetPopupState,
      clearAdminGoogleSheetPopupStateForTab,
      confirmAdminGoogleSheetPopup,
      cancelAdminGoogleSheetPopup,
      getAdminGoogleSheetTableInteractionSheetKey,
      handleAdminGoogleSheetPopupDismissal,
    };
  }

  global.SPMSAppAdminGoogleSheetsStateRuntime = {
    createAppAdminGoogleSheetsStateRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
