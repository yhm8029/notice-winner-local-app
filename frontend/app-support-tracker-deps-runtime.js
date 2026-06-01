(function attachAppSupportTrackerDepsRuntime(global) {
  const TRACKER_SUPPORT_RUNTIME = global.SPMSAppSupportTrackerRuntime || null;

  function isOutOfRangePageError(error) {
    const message = String(error && error.message ? error.message : error || "").toLowerCase();
    return message.includes("requested range not satisfiable") || message.includes("offset of");
  }

  function extractOutOfRangeTotalRows(error) {
    const message = String(error && error.message ? error.message : error || "");
    const match = message.match(/there are only\s+(\d+)\s+rows/i);
    return match ? Number(match[1]) || 0 : 0;
  }

  function createTrackerChangeEventHelpers(options = {}) {
    const {
      state = {},
      windowObject = global,
      storageKey = "",
      storageMaxItems = 0,
      cacheTtlMs = 0,
      canUseAdminMode = () => false,
      renderTrackerChangeEventsPanel = () => {},
      renderTrackerChangeEventUnreadCount = () => {},
      loadTrackerChangeEventUnreadCount = async () => {},
      loadTrackerChangeEvents = async () => {},
    } = options;

    function readTrackerChangeEventsCache() {
      try {
        const raw = windowObject.localStorage?.getItem(storageKey);
        if (!raw) {
          return null;
        }
        const parsed = JSON.parse(raw);
        if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.items)) {
          return null;
        }
        return {
          items: parsed.items.slice(0, storageMaxItems),
          unreadCount: Number(parsed.unread_count || 0),
          loadedAt: Number(parsed.loaded_at || 0),
        };
      } catch (_err) {
        return null;
      }
    }

    function persistTrackerChangeEventsCache() {
      try {
        windowObject.localStorage?.setItem(
          storageKey,
          JSON.stringify({
            items: (state.trackerChangeEvents || []).slice(0, storageMaxItems),
            unread_count: Number(state.trackerChangeEventsUnread || 0),
            loaded_at: Number(state.trackerChangeEventsLoadedAt || Date.now()),
          }),
        );
      } catch (_err) {
        // Ignore storage write failures.
      }
    }

    function clearTrackerChangeEventsCache() {
      state.trackerChangeEventsLoadedAt = 0;
      try {
        windowObject.localStorage?.removeItem(storageKey);
      } catch (_err) {
        // Ignore storage delete failures.
      }
    }

    function hydrateTrackerChangeEventsCache() {
      const cached = readTrackerChangeEventsCache();
      if (!cached) {
        return false;
      }
      if (!state.trackerChangeEvents.length && cached.items.length) {
        state.trackerChangeEvents = cached.items;
      }
      if (!state.trackerChangeEventsUnread && cached.unreadCount > 0) {
        state.trackerChangeEventsUnread = cached.unreadCount;
      }
      if (cached.loadedAt > state.trackerChangeEventsLoadedAt) {
        state.trackerChangeEventsLoadedAt = cached.loadedAt;
      }
      return cached.items.length > 0 || cached.unreadCount > 0;
    }

    function trackerChangeEventsCacheIsFresh() {
      const loadedAt = Number(state.trackerChangeEventsLoadedAt || 0);
      if (!loadedAt) {
        return false;
      }
      return (Date.now() - loadedAt) < cacheTtlMs;
    }

    function scheduleTrackerChangeEventsWarmup() {
      if (!canUseAdminMode()) {
        return;
      }
      state.trackerChangeEventsLoading = false;
      renderTrackerChangeEventsPanel();
      renderTrackerChangeEventUnreadCount();
      if (state.trackerChangeEventsWarmupHandle) {
        windowObject.clearTimeout(state.trackerChangeEventsWarmupHandle);
      }
      state.trackerChangeEventsWarmupHandle = windowObject.setTimeout(() => {
        state.trackerChangeEventsWarmupHandle = null;
        void loadTrackerChangeEventUnreadCount({ silent: true });
        void loadTrackerChangeEvents({ silent: true });
      }, 1500);
    }

    return {
      readTrackerChangeEventsCache,
      persistTrackerChangeEventsCache,
      clearTrackerChangeEventsCache,
      hydrateTrackerChangeEventsCache,
      trackerChangeEventsCacheIsFresh,
      scheduleTrackerChangeEventsWarmup,
    };
  }

  function createTrackerRenderFallbackHelpers(options = {}) {
    const factory = TRACKER_SUPPORT_RUNTIME?.createTrackerRenderFallbackHelpers;
    if (typeof factory === "function") {
      return factory(options);
    }
    throw new Error("SPMSAppSupportTrackerRuntime.createTrackerRenderFallbackHelpers is required");
  }

  function renderTrackerBoardHeaderCellBridge(options = {}) {
    const {
      column = {},
      TRACKER_BOARD_RUNTIME = null,
      fallbackHelpers = null,
      trackerBoardBlankPriorityFields = new Set(),
      trackerBoardSort = { fieldName: "" },
      escapeHtml = (value) => String(value ?? ""),
    } = options;
    return TRACKER_BOARD_RUNTIME?.renderTrackerBoardHeaderCell?.(column, {
      trackerBoardBlankPriorityFields,
      trackerBoardSort,
      escapeHtml,
    }) || fallbackHelpers?.renderTrackerBoardHeaderCell?.(column, {
      trackerBoardBlankPriorityFields,
      trackerBoardSort,
      escapeHtml,
    }) || `<th>${escapeHtml(column?.label || "")}</th>`;
  }

  function isTrackerBoardBlankValueBridge(options = {}) {
    const {
      value,
      TRACKER_BOARD_RUNTIME = null,
      fallbackHelpers = null,
    } = options;
    return TRACKER_BOARD_RUNTIME?.isTrackerBoardBlankValue?.(value)
      ?? fallbackHelpers?.isTrackerBoardBlankValue?.(value)
      ?? !String(value ?? "").trim();
  }

  function sortTrackerBoardEntriesBridge(options = {}) {
    const {
      entries = [],
      TRACKER_BOARD_RUNTIME = null,
      fallbackHelpers = null,
      fieldName = "",
      blankPriorityFields = new Set(),
      buildSortedTrackerBoardEntries = (items) => items,
    } = options;
    const blankValueHelpers = {
      isTrackerBoardBlankValue(value) {
        return isTrackerBoardBlankValueBridge({
          value,
          TRACKER_BOARD_RUNTIME,
          fallbackHelpers,
        });
      },
    };
    return fallbackHelpers?.sortTrackerBoardEntries?.(entries, {
      fieldName,
      blankPriorityFields,
    }, blankValueHelpers) || buildSortedTrackerBoardEntries(entries, {
      fieldName,
      blankPriorityFields,
    }, blankValueHelpers);
  }

  function buildTrackerBoardCellMarkupFallbackBridge(options = {}) {
    const {
      payload = {},
      fallbackHelpers = null,
      runtime = null,
      escapeHtml = (value) => String(value ?? ""),
      textareaFields = new Set(),
    } = options;
    return fallbackHelpers?.buildTrackerBoardCellMarkupFallback?.(payload, {
      escapeHtml,
      textareaFields,
    }) || runtime?.renderTrackerBoardCellFallback?.(payload, {
      escapeHtml,
      textareaFields,
    }) || "";
  }

  function buildTrackerBoardEditingCellMarkupFallbackBridge(options = {}) {
    const {
      payload = {},
      fallbackHelpers = null,
      runtime = null,
      escapeHtml = (value) => String(value ?? ""),
      textareaFields = new Set(),
    } = options;
    return fallbackHelpers?.buildTrackerBoardEditingCellMarkupFallback?.(payload, {
      escapeHtml,
      textareaFields,
    }) || runtime?.renderTrackerBoardEditingCellFallback?.(payload, {
      escapeHtml,
      textareaFields,
    }) || "";
  }

  function renderTrackerBoardCellBridge(options = {}) {
    const {
      payload = {},
      TRACKER_BOARD_RUNTIME = null,
      fallbackHelpers = null,
      escapeHtml = (value) => String(value ?? ""),
      textareaFields = new Set(),
      buildTrackerBoardCellMarkupFallback = () => "",
    } = options;
    return TRACKER_BOARD_RUNTIME?.renderTrackerBoardCell?.(payload, {
      escapeHtml,
      textareaFields,
    }) || fallbackHelpers?.renderTrackerBoardCell?.(payload, {
      escapeHtml,
      textareaFields,
    }) || buildTrackerBoardCellMarkupFallback(payload, {
      escapeHtml,
      textareaFields,
    });
  }

  function renderTrackerBoardEditingCellBridge(options = {}) {
    const {
      payload = {},
      TRACKER_BOARD_RUNTIME = null,
      fallbackHelpers = null,
      escapeHtml = (value) => String(value ?? ""),
      textareaFields = new Set(),
      buildTrackerBoardEditingCellMarkupFallback = () => "",
    } = options;
    return TRACKER_BOARD_RUNTIME?.renderTrackerBoardEditingCell?.(payload, {
      escapeHtml,
      textareaFields,
    }) || fallbackHelpers?.renderTrackerBoardEditingCell?.(payload, {
      escapeHtml,
      textareaFields,
    }) || buildTrackerBoardEditingCellMarkupFallback(payload, {
      escapeHtml,
      textareaFields,
    });
  }

  function createTrackerControllerDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      window = global,
      api = async () => ({}),
      flash = () => {},
      setBusy = () => {},
      FormData: FormDataCtor = null,
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      syncUrlState = () => {},
      renderTrackerEntries = () => {},
      EDITABLE_FIELDS = [],
      TRACKER_BOARD_BLANK_PRIORITY_FIELDS = new Set(),
      patchTrackerEntry = async () => {},
      syncTrackerEntryAfterPatch = async () => {},
      readRunFiltersFromControls = () => {},
      renderRuns = () => {},
      renderRunsPagination = () => {},
      renderRunDetail = () => {},
      renderRunEventStatus = () => {},
      renderLogsList = () => {},
      upsertRunListItem = () => {},
      renderEntriesPagination = () => {},
      renderSalesSummaryPanel = () => {},
      renderTrackerChangeEventsPanel = () => {},
      renderTrackerContactResolutionSummary = () => {},
      renderBackfillConflictsPanel = () => {},
      renderTrackerCleanupPreview = () => {},
      renderProjectRelatedHosts = () => {},
      touchSyncMeta = () => {},
      persistTrackerChangeEventsCache = () => {},
      clearTrackerChangeEventsCache = () => {},
      handleOutOfRangePageError = () => false,
      canLoadProtectedConsoleData = () => false,
      TRACKER_REGION_OPTIONS = [],
      useGlobalTrackerEntriesScope = () => false,
      shouldUseHomeBootstrapTrackerSnapshot = () => false,
      isProjectTrackerRun = () => false,
      loadTrackerEntries = async () => {},
      schedulePolling = () => {},
      loadWinnerRunPanels = async () => {},
      loadTrackerExportPanels = async () => {},
      loadSelectedRunLogs = async () => {},
      loadBackfillConflicts = async () => {},
      loadVisibleSalesClaims = async () => {},
      requireTrackerDiagnosticsRuntime = () => null,
      getTrackerController = () => null,
      formatContactResolutionStatusLabel = (value) => String(value ?? ""),
      formatContactResolutionReasonLabel = (value) => String(value ?? ""),
      formatBackfillConflictResolutionLabel = (value) => String(value ?? ""),
      getTrackerDiagnosticsScope = () => null,
      buildTrackerChangeEventsMarkup = () => "",
      buildTrackerChangeBellPopoverMarkup = () => "",
      buildBackfillConflictsMarkup = () => "",
      buildBackfillConflictsView = () => null,
      focusTrackerChangeEntry = async () => {},
      closeTrackerChangeModal = () => {},
      clearProjectRelatedRefresh = () => {},
      maybeScheduleProjectRelatedRefresh = () => {},
      canReuseProjectRelatedPayload = () => false,
      cacheProjectRelatedPayload = () => {},
      isProjectRelatedVisible = () => false,
      resolveTrackerEntryProjectId = () => "",
      ensureTrackerEntryProjectId = async () => "",
      TRACKER_ENTRY_RUNTIME = null,
      TRACKER_DETAIL_PREFETCH_LIMIT = 0,
      warmTrackerEntriesDownload = () => {},
      closeDrawer = () => {},
      renderTrackerBoard = () => {},
      resetTrackerBoardEdit = () => {},
      loadAdminConsoleData = async () => {},
      buildSelectedEntryAuditMarkup = () => "",
      loadSelectedEntryDetail = async () => {},
      renderTrackerMissingReport = () => {},
      renderSelectedEntryChangeEvents = () => {},
      renderSelectedEntry = () => {},
      renderSelectedEntryLoading = () => {},
      resolveTrackerPatchActorLabel = () => "",
      runTypeLabel = () => "",
    } = options;

    function buildTrackerControllerBaseDeps() {
      return {
        state,
        dom,
        flash,
        escapeHtml,
        syncUrlState,
        renderTrackerEntries,
      };
    }

    function buildTrackerControllerDeps() {
      return {
        ...buildTrackerControllerBaseDeps(),
        api,
        setBusy,
        FormData: FormDataCtor,
        formatDate,
        readRunFiltersFromControls,
        renderRuns,
        renderRunsPagination,
        renderRunDetail,
        renderRunEventStatus,
        renderLogsList,
        upsertRunListItem,
        renderEntriesPagination,
        renderSalesSummaryPanel,
        renderTrackerChangeEventsPanel,
        renderTrackerContactResolutionSummary,
        renderBackfillConflictsPanel,
        renderTrackerCleanupPreview,
        renderProjectRelatedHosts,
        touchSyncMeta,
        persistTrackerChangeEventsCache,
        clearTrackerChangeEventsCache,
        handleOutOfRangePageError,
        canLoadProtectedConsoleData,
        TRACKER_REGION_OPTIONS,
        useGlobalTrackerEntriesScope,
        shouldUseHomeBootstrapTrackerSnapshot,
        isProjectTrackerRun,
        loadTrackerEntries,
        schedulePolling,
        loadWinnerRunPanels,
        loadTrackerExportPanels,
        loadSelectedRunLogs,
        loadBackfillConflicts,
        loadVisibleSalesClaims,
        requireTrackerDiagnosticsRuntime,
        clearProjectRelatedRefresh,
        maybeScheduleProjectRelatedRefresh,
        canReuseProjectRelatedPayload,
        cacheProjectRelatedPayload,
        isProjectRelatedVisible,
        resolveTrackerEntryProjectId,
        ensureTrackerEntryProjectId,
        TRACKER_ENTRY_RUNTIME,
        TRACKER_DETAIL_PREFETCH_LIMIT,
        warmTrackerEntriesDownload,
        closeDrawer,
        renderTrackerBoard,
        resetTrackerBoardEdit,
        loadAdminConsoleData,
        buildSelectedEntryAuditMarkup,
        loadSelectedEntryDetail,
        renderTrackerMissingReport,
        renderSelectedEntryChangeEvents,
        renderSelectedEntry,
        renderSelectedEntryLoading,
        resolveTrackerPatchActorLabel,
        runTypeLabel,
      };
    }

    function buildTrackerEntryActionsControllerDeps() {
      return {
        ...buildTrackerControllerBaseDeps(),
        EDITABLE_FIELDS,
        TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
        renderTrackerBoard,
        loadTrackerEntries,
        setBusy,
        patchTrackerEntry,
        syncTrackerEntryAfterPatch,
      };
    }

    function buildTrackerDiagnosticsPanelControllerDeps() {
      return {
        ...buildTrackerControllerBaseDeps(),
        window,
        api,
        trackerController: getTrackerController(),
        formatDate,
        formatContactResolutionStatusLabel,
        formatContactResolutionReasonLabel,
        formatBackfillConflictResolutionLabel,
        getTrackerDiagnosticsScope,
        requireTrackerDiagnosticsRuntime,
        buildTrackerChangeEventsMarkup,
        buildTrackerChangeBellPopoverMarkup,
        buildBackfillConflictsMarkup,
        buildBackfillConflictsView,
        loadSelectedEntryDetail,
        focusTrackerChangeEntry,
        closeTrackerChangeModal,
      };
    }

    return {
      buildTrackerControllerBaseDeps,
      buildTrackerControllerDeps,
      buildTrackerEntryActionsControllerDeps,
      buildTrackerDiagnosticsPanelControllerDeps,
    };
  }

  function createTrackerControllerDepsHelpersFromApp(options = {}) {
    const {
      core = {},
      trackerCore = {},
      trackerActions = {},
      runPanels = {},
      diagnostics = {},
      trackerChange = {},
      projectRelated = {},
      adminData = {},
      constants = {},
    } = options;
    return createTrackerControllerDepsHelpers({
      state: core.state,
      dom: core.dom,
      window: core.window,
      api: core.api,
      flash: core.flash,
      setBusy: core.setBusy,
      FormData: core.FormData,
      escapeHtml: core.escapeHtml,
      formatDate: core.formatDate,
      syncUrlState: trackerCore.syncUrlState,
      renderTrackerEntries: trackerCore.renderTrackerEntries,
      EDITABLE_FIELDS: constants.EDITABLE_FIELDS,
      TRACKER_BOARD_BLANK_PRIORITY_FIELDS: constants.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
      patchTrackerEntry: trackerActions.patchTrackerEntry,
      syncTrackerEntryAfterPatch: trackerActions.syncTrackerEntryAfterPatch,
      readRunFiltersFromControls: runPanels.readRunFiltersFromControls,
      renderRuns: runPanels.renderRuns,
      renderRunsPagination: runPanels.renderRunsPagination,
      renderRunDetail: runPanels.renderRunDetail,
      renderRunEventStatus: runPanels.renderRunEventStatus,
      renderLogsList: runPanels.renderLogsList,
      upsertRunListItem: runPanels.upsertRunListItem,
      renderEntriesPagination: trackerCore.renderEntriesPagination,
      renderSalesSummaryPanel: diagnostics.renderSalesSummaryPanel,
      renderTrackerChangeEventsPanel: diagnostics.renderTrackerChangeEventsPanel,
      renderTrackerContactResolutionSummary: diagnostics.renderTrackerContactResolutionSummary,
      renderBackfillConflictsPanel: diagnostics.renderBackfillConflictsPanel,
      renderTrackerCleanupPreview: diagnostics.renderTrackerCleanupPreview,
      renderProjectRelatedHosts: projectRelated.renderProjectRelatedHosts,
      touchSyncMeta: trackerChange.touchSyncMeta,
      persistTrackerChangeEventsCache: trackerChange.persistTrackerChangeEventsCache,
      clearTrackerChangeEventsCache: trackerChange.clearTrackerChangeEventsCache,
      handleOutOfRangePageError: trackerCore.handleOutOfRangePageError,
      canLoadProtectedConsoleData: adminData.canLoadProtectedConsoleData,
      TRACKER_REGION_OPTIONS: constants.TRACKER_REGION_OPTIONS,
      useGlobalTrackerEntriesScope: trackerCore.useGlobalTrackerEntriesScope,
      shouldUseHomeBootstrapTrackerSnapshot: trackerCore.shouldUseHomeBootstrapTrackerSnapshot,
      isProjectTrackerRun: runPanels.isProjectTrackerRun,
      loadTrackerEntries: trackerCore.loadTrackerEntries,
      schedulePolling: runPanels.schedulePolling,
      loadWinnerRunPanels: runPanels.loadWinnerRunPanels,
      loadTrackerExportPanels: runPanels.loadTrackerExportPanels,
      loadSelectedRunLogs: runPanels.loadSelectedRunLogs,
      loadBackfillConflicts: diagnostics.loadBackfillConflicts,
      loadVisibleSalesClaims: diagnostics.loadVisibleSalesClaims,
      requireTrackerDiagnosticsRuntime: diagnostics.requireTrackerDiagnosticsRuntime,
      getTrackerController: trackerCore.getTrackerController,
      formatContactResolutionStatusLabel: diagnostics.formatContactResolutionStatusLabel,
      formatContactResolutionReasonLabel: diagnostics.formatContactResolutionReasonLabel,
      formatBackfillConflictResolutionLabel: diagnostics.formatBackfillConflictResolutionLabel,
      getTrackerDiagnosticsScope: diagnostics.getTrackerDiagnosticsScope,
      buildTrackerChangeEventsMarkup: diagnostics.buildTrackerChangeEventsMarkup,
      buildTrackerChangeBellPopoverMarkup: diagnostics.buildTrackerChangeBellPopoverMarkup,
      buildBackfillConflictsMarkup: diagnostics.buildBackfillConflictsMarkup,
      buildBackfillConflictsView: diagnostics.buildBackfillConflictsView,
      focusTrackerChangeEntry: trackerChange.focusTrackerChangeEntry,
      closeTrackerChangeModal: trackerChange.closeTrackerChangeModal,
      clearProjectRelatedRefresh: projectRelated.clearProjectRelatedRefresh,
      maybeScheduleProjectRelatedRefresh: projectRelated.maybeScheduleProjectRelatedRefresh,
      canReuseProjectRelatedPayload: projectRelated.canReuseProjectRelatedPayload,
      cacheProjectRelatedPayload: projectRelated.cacheProjectRelatedPayload,
      isProjectRelatedVisible: projectRelated.isProjectRelatedVisible,
      resolveTrackerEntryProjectId: projectRelated.resolveTrackerEntryProjectId,
      ensureTrackerEntryProjectId: projectRelated.ensureTrackerEntryProjectId,
      TRACKER_ENTRY_RUNTIME: constants.TRACKER_ENTRY_RUNTIME,
      TRACKER_DETAIL_PREFETCH_LIMIT: constants.TRACKER_DETAIL_PREFETCH_LIMIT,
      warmTrackerEntriesDownload: trackerActions.warmTrackerEntriesDownload,
      closeDrawer: trackerActions.closeDrawer,
      renderTrackerBoard: trackerActions.renderTrackerBoard,
      resetTrackerBoardEdit: trackerActions.resetTrackerBoardEdit,
      loadAdminConsoleData: adminData.loadAdminConsoleData,
      buildSelectedEntryAuditMarkup: trackerActions.buildSelectedEntryAuditMarkup,
      loadSelectedEntryDetail: trackerActions.loadSelectedEntryDetail,
      renderTrackerMissingReport: diagnostics.renderTrackerMissingReport,
      renderSelectedEntryChangeEvents: trackerActions.renderSelectedEntryChangeEvents,
      renderSelectedEntry: trackerActions.renderSelectedEntry,
      renderSelectedEntryLoading: trackerActions.renderSelectedEntryLoading,
      resolveTrackerPatchActorLabel: trackerActions.resolveTrackerPatchActorLabel,
      runTypeLabel: runPanels.runTypeLabel,
    });
  }

  function createTrackerRenderControllerDepsHelpers(deps = {}) {
    const factory = TRACKER_SUPPORT_RUNTIME?.createTrackerRenderControllerDepsHelpers;
    if (typeof factory === "function") {
      return factory(deps);
    }
    throw new Error("SPMSAppSupportTrackerRuntime.createTrackerRenderControllerDepsHelpers is required");
  }

  function createProjectRelatedControllerDepsHelpers(deps = {}) {
    const {
      sharedDeps = {},
      projectRelatedConfig = {},
      noticeViewerRenderers = {},
      projectRelatedActions = {},
    } = deps;
    let cachedDeps = null;

    function buildProjectRelatedControllerDeps() {
      if (cachedDeps) {
        return cachedDeps;
      }
      cachedDeps = {
        ...sharedDeps,
        ...projectRelatedConfig,
        ...noticeViewerRenderers,
        ...projectRelatedActions,
      };
      return cachedDeps;
    }

    return {
      buildProjectRelatedControllerDeps,
    };
  }

  function resolveActiveTrackerRunIdFromState(state = {}) {
    if (state.selectedRun && state.selectedRun.run_type === "tracker_export") {
      return state.selectedRun.id || null;
    }
    return state.selectedTrackerRunId || null;
  }

  function handleOutOfRangePageErrorFallback(state, flash, error, filterState, scopeLabel) {
    if (!isOutOfRangePageError(error) || !filterState || Number(filterState.page || 1) <= 1) {
      return false;
    }
    const totalRows = extractOutOfRangeTotalRows(error);
    const pageSize = Math.max(1, Number(filterState.pageSize || 20));
    const fallbackPage = totalRows > 0 ? Math.max(1, Math.ceil(totalRows / pageSize)) : 1;
    filterState.page = fallbackPage;
    flash?.(`${scopeLabel} 목록 페이지를 ${fallbackPage}로 보정했습니다.`, "warn");
    return true;
  }

  function focusTrackerChangeEntryFallback(deps, entryId, entries = deps.state?.trackerEntries) {
    const nextEntryId = String(entryId || "").trim();
    if (!nextEntryId) {
      return Promise.resolve(null);
    }
    const state = deps.state;
    const dom = deps.dom || {};
    state.selectedEntryId = nextEntryId;
    state.drawerOpen = state.uiMode !== "admin";
    deps.syncUrlState?.();
    deps.renderTrackerEntries?.(entries, { refreshSelectedEntry: state.uiMode === "admin" });
    const escapedEntryId = deps.windowObject?.CSS?.escape ? deps.windowObject.CSS.escape(nextEntryId) : nextEntryId;
    deps.documentObject?.querySelector?.(`[data-board-entry-id="${escapedEntryId}"], [data-entry-id="${escapedEntryId}"]`)
      ?.scrollIntoView?.({ behavior: "smooth", block: "center" });
    const detailPromise = deps.loadSelectedEntryDetail?.({ entryId: nextEntryId, silent: true, force: true });
    if (!detailPromise || typeof detailPromise.finally !== "function") {
      if (state.uiMode === "admin") {
        dom.entryEditor?.scrollIntoView?.({ behavior: "smooth", block: "start" });
      }
      return Promise.resolve(detailPromise ?? null);
    }
    return detailPromise.finally(() => {
      if (state.uiMode === "admin") {
        dom.entryEditor?.scrollIntoView?.({ behavior: "smooth", block: "start" });
      }
    });
  }

  function createAppSupportTrackerDepsRuntime(options = {}) {
    const state = options.state || null;
    const flash = options.flash || null;
    const windowObject = options.windowObject || global;
    const documentObject = options.documentObject || windowObject?.document || null;
    const syncUrlState = options.syncUrlState || null;
    const renderTrackerEntries = options.renderTrackerEntries || null;
    const loadSelectedEntryDetail = options.loadSelectedEntryDetail || null;
    const dom = options.dom || {};

    return {
      isOutOfRangePageError,
      extractOutOfRangeTotalRows,
      resolveActiveTrackerRunId() {
        return resolveActiveTrackerRunIdFromState(state);
      },
      handleOutOfRangePageError(error, filterState, scopeLabel) {
        return handleOutOfRangePageErrorFallback(state, flash, error, filterState, scopeLabel);
      },
      focusTrackerChangeEntry(entryId, entries = state?.trackerEntries) {
        return focusTrackerChangeEntryFallback({
          state,
          dom,
          documentObject,
          windowObject,
          syncUrlState,
          renderTrackerEntries,
          loadSelectedEntryDetail,
        }, entryId, entries);
      },
      createTrackerChangeEventHelpers,
      createTrackerRenderFallbackHelpers,
      renderTrackerBoardHeaderCellBridge,
      isTrackerBoardBlankValueBridge,
      sortTrackerBoardEntriesBridge,
      buildTrackerBoardCellMarkupFallbackBridge,
      buildTrackerBoardEditingCellMarkupFallbackBridge,
      renderTrackerBoardCellBridge,
      renderTrackerBoardEditingCellBridge,
      createTrackerControllerDepsHelpers,
      createTrackerControllerDepsHelpersFromApp,
      createTrackerRenderControllerDepsHelpers,
      createProjectRelatedControllerDepsHelpers,
    };
  }

  global.SPMSAppSupportTrackerDepsRuntime = {
    createAppSupportTrackerDepsRuntime,
  };
})(window);
