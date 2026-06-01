(function attachAppViewBindingsRuntime(global) {
  function createAppViewBindings(options = {}) {
    const SALES_RUNTIME = options.SALES_RUNTIME || null;
    const SALES_VIEW_RUNTIME = options.SALES_VIEW_RUNTIME || null;
    const TRACKER_CHANGE_RUNTIME = options.TRACKER_CHANGE_RUNTIME || null;
    const TRACKER_DIAGNOSTICS_RUNTIME = options.TRACKER_DIAGNOSTICS_RUNTIME || null;
    const TRACKER_ENTRY_RUNTIME = options.TRACKER_ENTRY_RUNTIME || null;
    const SELECTED_ENTRY_RUNTIME = options.SELECTED_ENTRY_RUNTIME || null;
    const TRACKER_CHANGE_FIELD_LABELS = options.TRACKER_CHANGE_FIELD_LABELS;
    const EDITABLE_FIELDS = options.EDITABLE_FIELDS;
    const formatContractAmountDisplay = options.formatContractAmountDisplay;
    const escapeHtml = options.escapeHtml;
    const formatDate = options.formatDate;
    const truncate = options.truncate;
    const formatKoreanDate = options.formatKoreanDate;
    const getTrackerProjectSnapshot = options.getTrackerProjectSnapshot;

    const salesClaimStatusLabel = SALES_RUNTIME?.salesClaimStatusLabel;
    const getSalesNoteEntries = SALES_RUNTIME?.getSalesNoteEntries;
    const parseSalesDateValue = SALES_RUNTIME?.parseSalesDateValue;
    const getSalesDateParts = SALES_RUNTIME?.getSalesDateParts;
    const getSalesYearMonthBucket = SALES_RUNTIME?.getSalesYearMonthBucket;
    const formatSalesDateLabel = SALES_RUNTIME?.formatSalesDateLabel;
    const formatSalesNoteTimestamp = SALES_RUNTIME?.formatSalesNoteTimestamp;
    const serializeSalesNoteEntry = SALES_RUNTIME?.serializeSalesNoteEntry;
    const parseSalesNoteEntry = SALES_RUNTIME?.parseSalesNoteEntry;
    const getSalesNoteTimeline = SALES_RUNTIME?.getSalesNoteTimeline;
    const getLatestSalesNoteEntry = SALES_RUNTIME?.getLatestSalesNoteEntry;
    const getLatestSalesNoteItem = SALES_RUNTIME?.getLatestSalesNoteItem;
    const extractContractAmountTextFromSalesNote = (rawValue) => SALES_RUNTIME?.extractContractAmountTextFromSalesNote(
      rawValue,
      formatContractAmountDisplay,
    ) || "";
    const formatSalesNoteTextForDisplay = (text) => SALES_RUNTIME?.formatSalesNoteTextForDisplay(
      text,
      formatContractAmountDisplay,
    ) || "";
    const removeLatestSalesNoteEntry = SALES_RUNTIME?.removeLatestSalesNoteEntry;
    const getTrackerChangeFieldLabel = (fieldName) => TRACKER_CHANGE_RUNTIME?.getTrackerChangeFieldLabel(
      fieldName,
      TRACKER_CHANGE_FIELD_LABELS,
    ) || String(fieldName || "").trim() || "필드";
    const formatTrackerChangeEventLabel = (item) => TRACKER_CHANGE_RUNTIME?.formatTrackerChangeEventLabel(
      item,
      TRACKER_CHANGE_FIELD_LABELS,
    ) || getTrackerChangeFieldLabel(item?.field_name);
    const buildTrackerChangeEventDescription = TRACKER_CHANGE_RUNTIME?.buildTrackerChangeEventDescription;
    const formatBackfillConflictResolutionLabel = TRACKER_CHANGE_RUNTIME?.formatBackfillConflictResolutionLabel;
    const buildBackfillConflictDescription = TRACKER_CHANGE_RUNTIME?.buildBackfillConflictDescription;
    const buildTrackerChangeEventsMarkup = (items) => TRACKER_CHANGE_RUNTIME?.buildTrackerChangeEventsMarkup(items, {
      escapeHtml,
      formatDate,
      formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription,
    }) || "";
    const buildBackfillConflictsMarkup = (items) => TRACKER_CHANGE_RUNTIME?.buildBackfillConflictsMarkup(items, {
      escapeHtml,
      formatDate,
      formatTrackerChangeEventLabel,
      buildBackfillConflictDescription,
    }) || "";
    const buildBackfillConflictsView = (options) => TRACKER_DIAGNOSTICS_RUNTIME?.buildBackfillConflictsView(options, {
      escapeHtml,
      buildBackfillConflictsMarkup: (items) => buildBackfillConflictsMarkup(items),
    }) || {
      className: "missing-report-list empty-state",
      html: "",
      bindActions: false,
    };
    const buildSelectedEntryChangeEventsMarkup = (items) => TRACKER_CHANGE_RUNTIME?.buildSelectedEntryChangeEventsMarkup(items, {
      escapeHtml,
      formatDate,
      formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription,
    }) || "";
    const toTrackerEntrySummary = TRACKER_ENTRY_RUNTIME?.toTrackerEntrySummary;
    const buildTrackerEntrySummaryDetail = TRACKER_ENTRY_RUNTIME?.buildTrackerEntrySummaryDetail;
    const buildTrackerEntriesEmptyStateView = (options = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerEntriesEmptyStateView(options) || null;
    const buildTrackerEntryCardView = (entry, options = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerEntryCardView(entry, options) || null;
    const buildTrackerEntriesListMarkup = (views, options = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerEntriesListMarkup(views, options) || "";
    const buildTrackerBoardEmptyStateView = (options = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerBoardEmptyStateView(options) || null;
    const buildTrackerBoardMarkup = (entries, options = {}, helpers = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerBoardMarkup(entries, options, helpers) || "";
    const formatEokValue = TRACKER_ENTRY_RUNTIME?.formatEokValue;
    const parseTrackerCostToWon = TRACKER_ENTRY_RUNTIME?.parseTrackerCostToWon;
    const formatBuildingAutomationEstimateValue = TRACKER_ENTRY_RUNTIME?.formatBuildingAutomationEstimateValue;
    const buildSelectedEntryLoadingView = (entry, options = {}) => SELECTED_ENTRY_RUNTIME?.buildSelectedEntryLoadingView(entry, options) || null;
    const buildSelectedEntryEmptyView = () => SELECTED_ENTRY_RUNTIME?.buildSelectedEntryEmptyView() || null;
    const buildPatchPanelView = (entry, options = {}) => SELECTED_ENTRY_RUNTIME?.buildPatchPanelView(entry, options) || null;
    const buildSelectedEntryMeta = (entry, options = {}) => SELECTED_ENTRY_RUNTIME?.buildSelectedEntryMeta(entry, options) || "";
    const buildSelectedEntryDisplayView = (entry, options = {}) => SELECTED_ENTRY_RUNTIME?.buildSelectedEntryDisplayView(entry, options) || null;
    const buildEntryDiagnosticsMarkup = (entry) => SELECTED_ENTRY_RUNTIME?.buildEntryDiagnosticsMarkup(entry, {
      escapeHtml,
    }) || "";
    const buildEntryFieldGridMarkup = (entry, activeField) => SELECTED_ENTRY_RUNTIME?.buildEntryFieldGridMarkup(entry, {
      editableFields: EDITABLE_FIELDS,
      activeField,
      truncate,
      escapeHtml,
    }) || "";
    const buildDrawerFieldListMarkup = (entry) => SELECTED_ENTRY_RUNTIME?.buildDrawerFieldListMarkup(entry, {
      editableFields: EDITABLE_FIELDS,
      escapeHtml,
    }) || "";
    const buildUserSalesProjectFactsMarkup = (snapshot, estimatedAmountText = "-") => SALES_VIEW_RUNTIME?.buildUserSalesProjectFactsMarkup(
      snapshot,
      estimatedAmountText,
      {
        escapeHtml,
        formatBuildingAutomationEstimateValue,
        formatKoreanDate,
      },
    ) || "";
    const buildSalesNoteTimelineMarkup = (noteEntries) => SALES_VIEW_RUNTIME?.buildSalesNoteTimelineMarkup(noteEntries, {
      escapeHtml,
      formatSalesNoteTextForDisplay,
    }) || "";
    const buildSalesClaimEstimateLabel = (claim) => SALES_VIEW_RUNTIME?.buildSalesClaimEstimateLabel(claim, {
      getTrackerProjectSnapshot,
      formatBuildingAutomationEstimateValue,
    }) || "";
    const buildUserOwnedSalesClaimCardMarkup = (params) => SALES_VIEW_RUNTIME?.buildUserOwnedSalesClaimCardMarkup(params, {
      escapeHtml,
      salesClaimStatusLabel,
      formatSalesDateLabel,
      buildUserSalesProjectFactsMarkup,
      buildSalesNoteTimelineMarkup,
    }) || "";
    const buildCompanySalesClaimCardMarkup = (params) => SALES_VIEW_RUNTIME?.buildCompanySalesClaimCardMarkup(params, {
      escapeHtml,
      salesClaimStatusLabel,
      formatSalesDateLabel,
      buildUserSalesProjectFactsMarkup,
      truncate,
      formatSalesNoteTextForDisplay,
    }) || "";
    const buildUserTrackerClaimSectionMarkup = (params) => SALES_VIEW_RUNTIME?.buildUserTrackerClaimSectionMarkup(params, {
      escapeHtml,
    }) || "";
    const buildSelectedEntryAuditMarkup = (items) => SALES_VIEW_RUNTIME?.buildSelectedEntryAuditMarkup(items, {
      escapeHtml,
      formatDate,
    }) || "";

    return {
      salesClaimStatusLabel,
      getSalesNoteEntries,
      parseSalesDateValue,
      getSalesDateParts,
      getSalesYearMonthBucket,
      formatSalesDateLabel,
      formatSalesNoteTimestamp,
      serializeSalesNoteEntry,
      parseSalesNoteEntry,
      getSalesNoteTimeline,
      getLatestSalesNoteEntry,
      getLatestSalesNoteItem,
      extractContractAmountTextFromSalesNote,
      formatSalesNoteTextForDisplay,
      removeLatestSalesNoteEntry,
      getTrackerChangeFieldLabel,
      formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription,
      formatBackfillConflictResolutionLabel,
      buildBackfillConflictDescription,
      buildTrackerChangeEventsMarkup,
      buildBackfillConflictsMarkup,
      buildBackfillConflictsView,
      buildSelectedEntryChangeEventsMarkup,
      toTrackerEntrySummary,
      buildTrackerEntrySummaryDetail,
      buildTrackerEntriesEmptyStateView,
      buildTrackerEntryCardView,
      buildTrackerEntriesListMarkup,
      buildTrackerBoardEmptyStateView,
      buildTrackerBoardMarkup,
      formatEokValue,
      parseTrackerCostToWon,
      formatBuildingAutomationEstimateValue,
      buildSelectedEntryLoadingView,
      buildSelectedEntryEmptyView,
      buildPatchPanelView,
      buildSelectedEntryMeta,
      buildSelectedEntryDisplayView,
      buildEntryDiagnosticsMarkup,
      buildEntryFieldGridMarkup,
      buildDrawerFieldListMarkup,
      buildUserSalesProjectFactsMarkup,
      buildSalesNoteTimelineMarkup,
      buildSalesClaimEstimateLabel,
      buildUserOwnedSalesClaimCardMarkup,
      buildCompanySalesClaimCardMarkup,
      buildUserTrackerClaimSectionMarkup,
      buildSelectedEntryAuditMarkup,
    };
  }

  global.SPMSAppViewBindingsRuntime = {
    createAppViewBindings,
  };
})(typeof window !== "undefined" ? window : globalThis);
