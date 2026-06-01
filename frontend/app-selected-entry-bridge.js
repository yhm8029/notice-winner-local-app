export function createAppSelectedEntryBridge(context = {}) {
  const {
    state = null,
    callSelectedEntryController = null,
    callTrackerEntryActionsController = null,
    resolveTrackerPatchActorLabel = null,
    getTrackerController = () => null,
  } = context;

  function callTrackerController(methodName, ...args) {
    return getTrackerController()?.[methodName]?.(...args);
  }

  function renderSelectedEntryLoading(entry, errorMessage = "") {
    return callSelectedEntryController("renderSelectedEntryLoading", entry, errorMessage);
  }

  async function loadSelectedEntryDetail({
    entryId = state?.selectedEntryId,
    silent = false,
    background = false,
    force = false,
  } = {}) {
    return callTrackerController("loadSelectedEntryDetail", {
      entryId,
      silent,
      background,
      force,
    }) || null;
  }

  function renderSelectedEntry(entry, { summaryOnly = false } = {}) {
    return callSelectedEntryController("renderSelectedEntry", entry, { summaryOnly });
  }

  function renderEntryDiagnostics(entry, { summaryOnly = false, view = null } = {}) {
    return callSelectedEntryController("renderEntryDiagnostics", entry, { summaryOnly, view });
  }

  function renderEntryFieldGrid(entry, { view = null } = {}) {
    return callSelectedEntryController("renderEntryFieldGrid", entry, { view });
  }

  function renderDrawer(entry, { view = null } = {}) {
    return callSelectedEntryController("renderDrawer", entry, { view });
  }

  function syncPatchValueFromSelectedEntry({ patchView = null } = {}) {
    return callSelectedEntryController("syncPatchValueFromSelectedEntry", { patchView });
  }

  function getSelectedEntryDisplayView(entry, { summaryOnly = false } = {}) {
    return callSelectedEntryController("getSelectedEntryDisplayView", entry, { summaryOnly });
  }

  async function patchTrackerEntry({
    entryId,
    fieldName,
    value,
    changeSource = "web",
    actorLabel = resolveTrackerPatchActorLabel(),
  }) {
    return callTrackerController("patchTrackerEntry", {
      entryId,
      fieldName,
      value,
      changeSource,
      actorLabel,
    }) || null;
  }

  function replaceTrackerEntryInState(updatedEntry) {
    return callTrackerController("replaceTrackerEntryInState", updatedEntry) || null;
  }

  async function syncTrackerEntryAfterPatch(updatedEntry) {
    return callTrackerController("syncTrackerEntryAfterPatch", updatedEntry) || null;
  }

  async function saveEntryPatch(event) {
    return callTrackerEntryActionsController("saveEntryPatch", event);
  }

  async function clearEntryPatch() {
    return callTrackerEntryActionsController("clearEntryPatch");
  }

  async function saveTrackerBoardEdit({ entryId, fieldName }) {
    return callTrackerController("saveTrackerBoardEdit", { entryId, fieldName }) || null;
  }

  function hydratePatchFieldOptions() {
    return callTrackerEntryActionsController("hydratePatchFieldOptions");
  }

  return {
    renderSelectedEntryLoading,
    loadSelectedEntryDetail,
    renderSelectedEntry,
    renderEntryDiagnostics,
    renderEntryFieldGrid,
    renderDrawer,
    syncPatchValueFromSelectedEntry,
    getSelectedEntryDisplayView,
    patchTrackerEntry,
    replaceTrackerEntryInState,
    syncTrackerEntryAfterPatch,
    saveEntryPatch,
    clearEntryPatch,
    saveTrackerBoardEdit,
    hydratePatchFieldOptions,
  };
}

const appSelectedEntryBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appSelectedEntryBridgeRoot.APP_SELECTED_ENTRY_BRIDGE = appSelectedEntryBridgeRoot.APP_SELECTED_ENTRY_BRIDGE || {};
appSelectedEntryBridgeRoot.APP_SELECTED_ENTRY_BRIDGE.createAppSelectedEntryBridge = createAppSelectedEntryBridge;
