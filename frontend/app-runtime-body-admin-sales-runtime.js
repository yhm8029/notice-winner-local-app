(function initAppRuntimeBodyAdminSalesRuntime(global) {
  function createAppRuntimeBodyAdminSalesDelegates({
    state,
    dom,
    APP_SUPPORT,
    TRACKER_DIAGNOSTICS_RUNTIME,
    TRACKER_MISSING_REPORT_RUNTIME,
    escapeHtml,
    formatDate,
    requireConsoleDataRuntime,
    getConsoleDataRuntimeDeps,
    getTrackerDiagnosticsPanelController,
    getOrgAdminController,
    windowObject,
    SALES_VIEW_RUNTIME,
    buildSalesClaimEstimateLabel,
    formatShortDateTimeHelper,
    formatEstimatedAmountRangeFromKrwHelper,
  }) {
    function renderTrackerContactResolutionSummary(errorMessage = "") {
      return APP_SUPPORT.renderTrackerContactResolutionSummary({
        dom,
        TRACKER_DIAGNOSTICS_RUNTIME,
        renderTrackerContactResolutionSummary: (message) => getTrackerDiagnosticsPanelController().renderTrackerContactResolutionSummary(message),
      }, errorMessage);
    }
    function renderTrackerCleanupPreview(errorMessage = "") {
      return APP_SUPPORT.renderTrackerCleanupPreview({
        dom,
        TRACKER_DIAGNOSTICS_RUNTIME,
        renderTrackerCleanupPreview: (message) => getTrackerDiagnosticsPanelController().renderTrackerCleanupPreview(message),
      }, errorMessage);
    }
    function renderTrackerMissingReport(errorMessage = "") {
      return APP_SUPPORT.renderTrackerMissingReport({ state, dom, TRACKER_MISSING_REPORT_RUNTIME, escapeHtml, formatDate }, errorMessage);
    }
    async function loadVisibleSalesClaims({ silent = false } = {}) { return requireConsoleDataRuntime().loadVisibleSalesClaims(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadHomeBootstrap({ silent = false, force = false } = {}) { return requireConsoleDataRuntime().loadHomeBootstrap(getConsoleDataRuntimeDeps(), { silent, force }); }
    async function loadHomeBootstrapFromLegacy({ silent = false } = {}) { return requireConsoleDataRuntime().loadHomeBootstrapFromLegacy(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadSalesOverview({ silent = false, force = false } = {}) { return requireConsoleDataRuntime().loadSalesOverview(getConsoleDataRuntimeDeps(), { silent, force }); }
    async function loadSalesOverviewFromLegacy({ silent = false, persistCache = false } = {}) { return requireConsoleDataRuntime().loadSalesOverviewFromLegacy(getConsoleDataRuntimeDeps(), { silent, persistCache }); }
    async function loadMySalesClaims({ silent = false } = {}) { return requireConsoleDataRuntime().loadMySalesClaims(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadClosedSalesClaims({ silent = false } = {}) { return requireConsoleDataRuntime().loadClosedSalesClaims(getConsoleDataRuntimeDeps(), { silent }); }
    function refreshSalesAdminPanels({ silent = false } = {}) { return requireConsoleDataRuntime().refreshSalesAdminPanels(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadSalesClaimSummaryByUser({ silent = false } = {}) { return requireConsoleDataRuntime().loadSalesClaimSummaryByUser(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadOrganizationUsers({ silent = false } = {}) { return requireConsoleDataRuntime().loadOrganizationUsers(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadOrganizationMembers({ silent = false } = {}) { return requireConsoleDataRuntime().loadOrganizationMembers(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadOrganizationInvitations({ silent = false } = {}) { return requireConsoleDataRuntime().loadOrganizationInvitations(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadOrganizationAuditLogs({ silent = false } = {}) { return requireConsoleDataRuntime().loadOrganizationAuditLogs(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadOrganizationDownloadAuditLogs({ silent = false } = {}) { return requireConsoleDataRuntime().loadOrganizationDownloadAuditLogs(getConsoleDataRuntimeDeps(), { silent }); }
    async function loadOrganizationLoginAuditLogs({ silent = false } = {}) { return requireConsoleDataRuntime().loadOrganizationLoginAuditLogs(getConsoleDataRuntimeDeps(), { silent }); }
    function loadOrganizationAdminData({ silent = false, force = false } = {}) { return getOrgAdminController()?.loadOrganizationAdminData({ silent, force }); }
    async function handleInvitationSubmit(event) { return getOrgAdminController()?.handleInvitationSubmit(event); }
    async function handlePlatformAdminAccountSubmit(event) { return getOrgAdminController()?.handlePlatformAdminAccountSubmit(event); }
    async function copyInvitationUrl(inviteUrl, options = {}) { return getOrgAdminController()?.copyInvitationUrl(inviteUrl, options); }
    async function revokeOrganizationInvitation(invitationId) { return getOrgAdminController()?.revokeOrganizationInvitation(invitationId); }
    async function saveOrganizationMember(userId, article) { return getOrgAdminController()?.saveOrganizationMember(userId, article); }
    async function deleteOrganizationMember(userId, article) { return getOrgAdminController()?.deleteOrganizationMember(userId, article); }
    async function resetOrganizationMemberPassword(userId, article) { return getOrgAdminController()?.resetOrganizationMemberPassword(userId, article); }
    async function performResetOrganizationMemberPassword(userId, article) { return resetOrganizationMemberPassword(userId, article); }
    function normalizeSalesClaimCardViewModel(payload = {}, options = {}) {
      const normalizeSalesClaimCardViewModelFromRuntime =
        windowObject.SPMSAppControllerWiringRuntime?.normalizeSalesClaimCardViewModel
        || windowObject.APP_CONTROLLER_DEPS?.normalizeSalesClaimCardViewModel
        || SALES_VIEW_RUNTIME?.normalizeSalesClaimCardViewModel;
      if (typeof normalizeSalesClaimCardViewModelFromRuntime !== "function") {
        throw new Error("Missing sales claim card normalizer runtime");
      }
      return normalizeSalesClaimCardViewModelFromRuntime(payload, options);
    }
    function formatSalesClaimEstimateLabel(claim) { return buildSalesClaimEstimateLabel(claim); }
    function formatShortDateTime(value) { return formatShortDateTimeHelper(value); }
    function formatEstimatedAmountRangeFromKrw(low, high, fallback = "-") {
      return formatEstimatedAmountRangeFromKrwHelper(low, high, fallback);
    }
    return {
      renderTrackerContactResolutionSummary,
      renderTrackerCleanupPreview,
      renderTrackerMissingReport,
      loadVisibleSalesClaims,
      loadHomeBootstrap,
      loadHomeBootstrapFromLegacy,
      loadSalesOverview,
      loadSalesOverviewFromLegacy,
      loadMySalesClaims,
      loadClosedSalesClaims,
      refreshSalesAdminPanels,
      loadSalesClaimSummaryByUser,
      loadOrganizationUsers,
      loadOrganizationMembers,
      loadOrganizationInvitations,
      loadOrganizationAuditLogs,
      loadOrganizationDownloadAuditLogs,
      loadOrganizationLoginAuditLogs,
      loadOrganizationAdminData,
      handleInvitationSubmit,
      handlePlatformAdminAccountSubmit,
      copyInvitationUrl,
      revokeOrganizationInvitation,
      saveOrganizationMember,
      deleteOrganizationMember,
      resetOrganizationMemberPassword,
      performResetOrganizationMemberPassword,
      normalizeSalesClaimCardViewModel,
      formatSalesClaimEstimateLabel,
      formatShortDateTime,
      formatEstimatedAmountRangeFromKrw,
    };
  }

  function createAppRuntimeBodyTrackerDelegates({
    state,
    escapeHtml,
    APP_SUPPORT,
    TRACKER_BOARD_RUNTIME,
    TRACKER_BOARD_TEXTAREA_FIELDS,
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    buildSortedTrackerBoardEntries,
    getTrackerRenderFallbackRuntime,
    getTrackerRenderFallbackHelpers,
    getTrackerRenderController,
    getTrackerEntryActionsController,
    getSelectedEntryController,
    getTrackerController,
    toTrackerEntrySummary,
  }) {
    function buildTrackerEntryCardMarkupFallback(payload = {}, helpers = {}) { return getTrackerRenderFallbackRuntime()?.buildTrackerEntryCardMarkupFallback?.(payload, helpers) || ""; }
    function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) { return getTrackerRenderController()?.renderTrackerEntries?.(entries, { refreshSelectedEntry }) ?? renderTrackerEntriesFallback(entries, { refreshSelectedEntry }); }
    function renderTrackerEntriesFallback(entries, { refreshSelectedEntry = true } = {}) { return getTrackerRenderFallbackRuntime()?.renderTrackerEntriesFallback?.(entries, getTrackerRenderFallbackHelpers().buildTrackerEntriesFallbackDeps(refreshSelectedEntry), { escapeHtml }) || undefined; }
    function sortTrackerBoardEntriesFallback(entries, { fieldName = "", blankPriorityFields = TRACKER_BOARD_BLANK_PRIORITY_FIELDS } = {}, helpers = {}) {
      return getTrackerRenderFallbackRuntime()?.sortTrackerBoardEntriesFallback?.(entries, { fieldName, blankPriorityFields }, helpers) || (Array.isArray(entries) ? entries : []);
    }
    function buildTrackerBoardMarkupFallback(entries, options = {}, helpers = {}) { return getTrackerRenderFallbackRuntime()?.buildTrackerBoardMarkupFallback?.(entries, options, helpers) || ""; }
    function renderTrackerBoard(entries) { return getTrackerRenderController()?.renderTrackerBoard?.(entries) ?? renderTrackerBoardFallback(entries); }
    function renderTrackerBoardFallback(entries) { return getTrackerRenderFallbackRuntime()?.renderTrackerBoardFallback?.(entries, getTrackerRenderFallbackHelpers().buildTrackerBoardFallbackDeps(), { escapeHtml }) || undefined; }
    function toggleTrackerBoardBlankPriority(fieldName) { return getTrackerEntryActionsController().toggleTrackerBoardBlankPriority(fieldName); }
    function renderTrackerBoardHeaderCell(column) { return APP_SUPPORT.renderTrackerBoardHeaderCellBridge({ column, TRACKER_BOARD_RUNTIME, fallbackHelpers: getTrackerRenderFallbackHelpers(), trackerBoardBlankPriorityFields: TRACKER_BOARD_BLANK_PRIORITY_FIELDS, trackerBoardSort: state.trackerBoardSort, escapeHtml }); }
    function isTrackerBoardBlankValue(value) { return APP_SUPPORT.isTrackerBoardBlankValueBridge({ value, TRACKER_BOARD_RUNTIME, fallbackHelpers: getTrackerRenderFallbackHelpers() }); }
    function sortTrackerBoardEntries(entries) { return APP_SUPPORT.sortTrackerBoardEntriesBridge({ entries, TRACKER_BOARD_RUNTIME, fallbackHelpers: getTrackerRenderFallbackHelpers(), fieldName: state.trackerBoardSort.fieldName, blankPriorityFields: TRACKER_BOARD_BLANK_PRIORITY_FIELDS, buildSortedTrackerBoardEntries }); }
    function buildTrackerBoardCellMarkupFallback({ entry, column, displayNo, trackerBoardEdit = null }, { escapeHtml: fallbackEscapeHtml = escapeHtml, textareaFields = TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {
      return APP_SUPPORT.buildTrackerBoardCellMarkupFallbackBridge({ payload: { entry, column, displayNo, trackerBoardEdit }, fallbackHelpers: getTrackerRenderFallbackHelpers(), runtime: getTrackerRenderFallbackRuntime(), escapeHtml: fallbackEscapeHtml, textareaFields });
    }
    function buildTrackerBoardEditingCellMarkupFallback({ entry, fieldName, label, value, saving, errorMessage }, { escapeHtml: fallbackEscapeHtml = escapeHtml, textareaFields = TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {
      return APP_SUPPORT.buildTrackerBoardEditingCellMarkupFallbackBridge({ payload: { entry, fieldName, label, value, saving, errorMessage }, fallbackHelpers: getTrackerRenderFallbackHelpers(), runtime: getTrackerRenderFallbackRuntime(), escapeHtml: fallbackEscapeHtml, textareaFields });
    }
    function renderTrackerBoardCell({ entry, column, displayNo }) { return APP_SUPPORT.renderTrackerBoardCellBridge({ payload: { entry, column, displayNo, trackerBoardEdit: state.trackerBoardEdit }, TRACKER_BOARD_RUNTIME, fallbackHelpers: getTrackerRenderFallbackHelpers(), escapeHtml, textareaFields: TRACKER_BOARD_TEXTAREA_FIELDS, buildTrackerBoardCellMarkupFallback }); }
    function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) { return APP_SUPPORT.renderTrackerBoardEditingCellBridge({ payload: { entry, fieldName, label, value, saving, errorMessage }, TRACKER_BOARD_RUNTIME, fallbackHelpers: getTrackerRenderFallbackHelpers(), escapeHtml, textareaFields: TRACKER_BOARD_TEXTAREA_FIELDS, buildTrackerBoardEditingCellMarkupFallback }); }
    function beginTrackerBoardEdit(entryId, fieldName) { return getTrackerEntryActionsController().beginTrackerBoardEdit(entryId, fieldName); }
    function resetTrackerBoardEdit() { return getTrackerEntryActionsController().resetTrackerBoardEdit(); }
    function resolveTrackerPatchActorLabel() { return getTrackerEntryActionsController().resolveTrackerPatchActorLabel(); }
    function getEntriesTotalPages() { return getTrackerEntryActionsController().getEntriesTotalPages(); }
    function renderEntriesPagination() { return getTrackerEntryActionsController().renderEntriesPagination(); }
    function changeEntriesPage(delta) { return getTrackerEntryActionsController().changeEntriesPage(delta); }
    function changeEntriesPageTo(page) { return getTrackerEntryActionsController().changeEntriesPageTo(page); }
    function renderSelectedEntry(entry, { summaryOnly = false } = {}) { return getSelectedEntryController().renderSelectedEntry(entry, { summaryOnly }); }
    function renderEntryDiagnostics(entry, { summaryOnly = false, view = null } = {}) { return getSelectedEntryController().renderEntryDiagnostics(entry, { summaryOnly, view }); }
    function renderEntryFieldGrid(entry, { view = null } = {}) { return getSelectedEntryController().renderEntryFieldGrid(entry, { view }); }
    function renderDrawer(entry, { view = null } = {}) { return getSelectedEntryController().renderDrawer(entry, { view }); }
    function syncPatchValueFromSelectedEntry({ patchView = null } = {}) { return getSelectedEntryController().syncPatchValueFromSelectedEntry({ patchView }); }
    async function patchTrackerEntry({ entryId, fieldName, value, changeSource = "web", actorLabel = resolveTrackerPatchActorLabel(), }) { return getTrackerController().patchTrackerEntry({ entryId, fieldName, value, changeSource, actorLabel }); }
    function replaceTrackerEntryInState(updatedEntry) {
      const summary = toTrackerEntrySummary(updatedEntry);
      state.trackerEntries = state.trackerEntries.map((item) => (item.id === summary.id ? { ...item, ...summary } : item));
      state.trackerEntryDetailCache = { ...state.trackerEntryDetailCache, [updatedEntry.id]: updatedEntry };
      if (state.selectedEntryId === updatedEntry.id) state.selectedEntry = updatedEntry;
    }
    async function syncTrackerEntryAfterPatch(updatedEntry) { return getTrackerController().syncTrackerEntryAfterPatch(updatedEntry); }
    async function saveEntryPatch(event) { return getTrackerEntryActionsController().saveEntryPatch(event); }
    async function clearEntryPatch() { return getTrackerEntryActionsController().clearEntryPatch(); }
    async function saveTrackerBoardEdit({ entryId, fieldName }) { return getTrackerController().saveTrackerBoardEdit({ entryId, fieldName }); }
    async function loadSelectedEntryAudit() { return getTrackerController().loadSelectedEntryAudit(); }
    function hydratePatchFieldOptions() { return getTrackerEntryActionsController().hydratePatchFieldOptions(); }
    function handleOutOfRangePageError(error, filterState, scopeLabel) { return APP_SUPPORT.handleOutOfRangePageError(error, filterState, scopeLabel); }
    function resolveActiveTrackerRunId() { return APP_SUPPORT.resolveActiveTrackerRunId(); }
    return { buildTrackerEntryCardMarkupFallback, renderTrackerEntries, renderTrackerEntriesFallback, sortTrackerBoardEntriesFallback, buildTrackerBoardMarkupFallback, renderTrackerBoard, renderTrackerBoardFallback, toggleTrackerBoardBlankPriority, renderTrackerBoardHeaderCell, isTrackerBoardBlankValue, sortTrackerBoardEntries, buildTrackerBoardCellMarkupFallback, buildTrackerBoardEditingCellMarkupFallback, renderTrackerBoardCell, renderTrackerBoardEditingCell, beginTrackerBoardEdit, resetTrackerBoardEdit, resolveTrackerPatchActorLabel, getEntriesTotalPages, renderEntriesPagination, changeEntriesPage, changeEntriesPageTo, renderSelectedEntry, renderEntryDiagnostics, renderEntryFieldGrid, renderDrawer, syncPatchValueFromSelectedEntry, patchTrackerEntry, replaceTrackerEntryInState, syncTrackerEntryAfterPatch, saveEntryPatch, clearEntryPatch, saveTrackerBoardEdit, loadSelectedEntryAudit, hydratePatchFieldOptions, handleOutOfRangePageError, resolveActiveTrackerRunId };
  }

  global.SPMSAppRuntimeBodyAdminSalesRuntime = {
    createAppRuntimeBodyAdminSalesDelegates,
    createAppRuntimeBodyTrackerDelegates,
  };
})(typeof window !== "undefined" ? window : globalThis);
