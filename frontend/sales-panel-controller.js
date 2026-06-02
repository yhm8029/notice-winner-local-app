import { normalizeSalesClaimCardViewModel as normalizeSalesClaimCardViewModelFromDeps } from "./app-controller-deps.js";
import { createSalesPanelControllerActions } from "./sales-panel-controller-actions.js?v=20260602c";
import { createSalesPanelControllerHelpers } from "./sales-panel-controller-helpers.js";
import { createSalesPanelControllerMarkup } from "./sales-panel-controller-markup.js";
import { createSalesPanelControllerViewModelHelpers } from "./sales-panel-controller-view-model.js";

export function createSalesPanelController(deps = {}) {
  const {
    dom,
    state,
    window: appWindow = typeof window !== "undefined" ? window : null,
    escapeHtml,
    getLatestSalesNoteItem,
    truncate,
    formatSalesNoteTextForDisplay,
    formatSalesDateLabel,
    getSalesNoteEntries,
    getSalesNoteTimeline,
    getSalesYearMonthBucket,
    formatContractAmountDisplay,
    extractContractAmountTextFromSalesNote,
    salesClaimStatusLabel,
    formatEstimatedAmountRangeFromKrw,
    buildUserSalesProjectFactsMarkup,
    buildSalesClaimEstimateLabelMarkup,
    buildUserOwnedSalesClaimCardMarkup,
    buildCompanySalesClaimCardMarkup,
    buildUserTrackerClaimSectionMarkup,
    formatEokValue,
    isAdminRole,
    normalizeSalesClaimCardViewModel: normalizeSalesClaimCardViewModelFromDepsInjected = normalizeSalesClaimCardViewModelFromDeps,
    salesViewRuntime = null,
    flash,
    syncUrlState,
    upsertSalesClaim,
    serializeSalesNoteEntry,
    removeLatestSalesNoteEntry,
  } = deps;

  const helperApi = createSalesPanelControllerHelpers({
    state,
    escapeHtml,
    buildUserSalesProjectFactsMarkup,
    formatEokValue,
    isAdminRole,
  });

  const viewModelApi = createSalesPanelControllerViewModelHelpers({
    state,
    escapeHtml,
    formatSalesDateLabel,
    salesClaimStatusLabel,
    formatContractAmountDisplay,
    extractContractAmountTextFromSalesNote,
    truncate,
    formatSalesNoteTextForDisplay,
    getLatestSalesNoteItem,
    getSalesNoteTimeline: deps.getSalesNoteTimeline,
    getTrackerProjectSnapshot: helperApi.getTrackerProjectSnapshot,
    getOrganizationTransferTargets: helperApi.getOrganizationTransferTargets,
    getSalesNoteDraft: helperApi.getSalesNoteDraft,
    isCurrentUserClaimOwner: helperApi.isCurrentUserClaimOwner,
    canCurrentUserManageClaim: helperApi.canCurrentUserManageClaim,
    buildSalesClaimEstimateLabelMarkup,
    buildUserOwnedSalesClaimCardMarkup,
    buildCompanySalesClaimCardMarkup,
    buildUserTrackerClaimSectionMarkup,
    normalizeSalesClaimCardViewModel: normalizeSalesClaimCardViewModelFromDepsInjected,
    salesViewRuntime,
  });

  const markupApi = createSalesPanelControllerMarkup({
    escapeHtml,
    truncate,
    formatSalesNoteTextForDisplay,
    getLatestSalesNoteItem,
    getSalesYearMonthBucket,
    formatSalesDateLabel,
    formatContractAmountDisplay,
    extractContractAmountTextFromSalesNote,
    salesClaimStatusLabel,
    formatSalesClaimEstimateLabel: viewModelApi.formatSalesClaimEstimateLabel,
    salesViewRuntime,
  });

  const actionApi = createSalesPanelControllerActions({
    state,
    dom,
    window: appWindow,
    flash,
    api: deps.api,
    renderTrackerEntries: deps.renderTrackerEntries,
    loadSalesOverview: deps.loadSalesOverview,
    loadMySalesClaims: deps.loadMySalesClaims,
    loadVisibleSalesClaims: deps.loadVisibleSalesClaims,
    refreshSalesAdminPanels: deps.refreshSalesAdminPanels,
    syncUrlState,
    getSalesClaimForProject: helperApi.getSalesClaimForProject,
    getSalesNoteDraft: helperApi.getSalesNoteDraft,
    setSalesNoteDraft: helperApi.setSalesNoteDraft,
    getSalesNoteEntries,
    getSalesNoteTimeline,
    serializeSalesNoteEntry,
    removeLatestSalesNoteEntry,
    canCurrentUserForceRelease: helperApi.canCurrentUserForceRelease,
    formatContractAmountInput: deps.formatContractAmountInput,
    renderClosedSalesArchiveSection: markupApi.renderClosedSalesArchiveSection,
    renderUserOwnedSalesClaimCard: viewModelApi.renderUserOwnedSalesClaimCard,
    renderCompanySalesClaimCard: viewModelApi.renderCompanySalesClaimCard,
    formatSalesClaimEstimateLabel: viewModelApi.formatSalesClaimEstimateLabel,
    renderUserTrackerClaimSection: viewModelApi.renderUserTrackerClaimSection,
    renderSalesNoteTimelineMarkup: markupApi.renderSalesNoteTimelineMarkup,
    upsertSalesClaim,
    escapeHtml,
    formatEstimatedAmountRangeFromKrw,
    getLatestSalesNoteItem,
    truncate,
    formatSalesNoteTextForDisplay,
    formatSalesDateLabel,
  });

  return {
    ...helperApi,
    ...viewModelApi,
    ...markupApi,
    ...actionApi,
  };
}

const salesPanelControllerRoot = typeof window !== "undefined" ? window : globalThis;
salesPanelControllerRoot.SALES_PANEL_CONTROLLER = salesPanelControllerRoot.SALES_PANEL_CONTROLLER || {};
salesPanelControllerRoot.SALES_PANEL_CONTROLLER.createSalesPanelController = createSalesPanelController;
