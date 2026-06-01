export function createAppTrackerSupportBridge(context = {}) {
  const {
    callTrackerDiagnosticsPanelController = null,
    callTrackerRenderController = null,
    callTrackerEntryActionsController = null,
  } = context;

  function renderTrackerContactResolutionSummary(errorMessage = "") {
    return callTrackerDiagnosticsPanelController("renderTrackerContactResolutionSummary", errorMessage);
  }

  function renderTrackerCleanupPreview(errorMessage = "") {
    return callTrackerDiagnosticsPanelController("renderTrackerCleanupPreview", errorMessage);
  }

  function renderTrackerChangeEventsPanel() {
    return callTrackerDiagnosticsPanelController("renderTrackerChangeEventsPanel");
  }

  function renderBackfillConflictsPanel() {
    return callTrackerDiagnosticsPanelController("renderBackfillConflictsPanel");
  }

  function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {
    return callTrackerRenderController("renderTrackerEntries", entries, { refreshSelectedEntry });
  }

  function renderTrackerBoard(entries) {
    return callTrackerRenderController("renderTrackerBoard", entries);
  }

  function toggleTrackerBoardBlankPriority(fieldName) {
    return callTrackerEntryActionsController("toggleTrackerBoardBlankPriority", fieldName);
  }

  function beginTrackerBoardEdit(entryId, fieldName) {
    return callTrackerEntryActionsController("beginTrackerBoardEdit", entryId, fieldName);
  }

  function resetTrackerBoardEdit() {
    return callTrackerEntryActionsController("resetTrackerBoardEdit");
  }

  function resolveTrackerPatchActorLabel() {
    return callTrackerEntryActionsController("resolveTrackerPatchActorLabel");
  }

  function getEntriesTotalPages() {
    return callTrackerEntryActionsController("getEntriesTotalPages");
  }

  function renderEntriesPagination() {
    return callTrackerEntryActionsController("renderEntriesPagination");
  }

  function changeEntriesPage(delta) {
    return callTrackerEntryActionsController("changeEntriesPage", delta);
  }

  function changeEntriesPageTo(page) {
    return callTrackerEntryActionsController("changeEntriesPageTo", page);
  }

  return {
    renderTrackerContactResolutionSummary,
    renderTrackerCleanupPreview,
    renderTrackerChangeEventsPanel,
    renderBackfillConflictsPanel,
    renderTrackerEntries,
    renderTrackerBoard,
    toggleTrackerBoardBlankPriority,
    beginTrackerBoardEdit,
    resetTrackerBoardEdit,
    resolveTrackerPatchActorLabel,
    getEntriesTotalPages,
    renderEntriesPagination,
    changeEntriesPage,
    changeEntriesPageTo,
  };
}

const appTrackerSupportBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appTrackerSupportBridgeRoot.APP_TRACKER_SUPPORT_BRIDGE = appTrackerSupportBridgeRoot.APP_TRACKER_SUPPORT_BRIDGE || {};
appTrackerSupportBridgeRoot.APP_TRACKER_SUPPORT_BRIDGE.createAppTrackerSupportBridge = createAppTrackerSupportBridge;
