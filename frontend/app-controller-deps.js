import {
  createAuthControllerDeps,
  createAuthUiControllerDeps,
  createOrgAdminControllerDeps,
} from "./app-controller-deps-auth.js";
import {
  createAppEventBindingsDeps,
  createConsolePanelsControllerDeps,
  createDownloadControllerDeps,
  createProjectRelatedControllerDeps,
  createReportPanelsControllerDeps,
  createRunPanelsControllerDeps,
  createRuntimeEnhancementsDeps,
  createSalesPanelControllerDeps,
  createSelectedEntryControllerDeps,
  createTrackerControllerDeps,
  createTrackerDiagnosticsPanelControllerDeps,
  createTrackerEntryActionsControllerDeps,
  normalizeSalesClaimCardViewModel,
  resolveActiveTrackerRunIdFromState,
} from "./app-controller-deps-factories.js?v=20260503r";

export {
  createAuthControllerDeps,
  createAuthUiControllerDeps,
  createOrgAdminControllerDeps,
  createAppEventBindingsDeps,
  createConsolePanelsControllerDeps,
  createDownloadControllerDeps,
  createProjectRelatedControllerDeps,
  createReportPanelsControllerDeps,
  createRunPanelsControllerDeps,
  createRuntimeEnhancementsDeps,
  createSalesPanelControllerDeps,
  createSelectedEntryControllerDeps,
  createTrackerControllerDeps,
  createTrackerDiagnosticsPanelControllerDeps,
  createTrackerEntryActionsControllerDeps,
  normalizeSalesClaimCardViewModel,
  resolveActiveTrackerRunIdFromState,
};

const appControllerDepsRoot = typeof window !== "undefined" ? window : globalThis;
const APP_CONTROLLER_DEPS_READY_KEY = "__appControllerDepsReadyState";
const APP_CONTROLLER_DEPS_READY_EVENT = "app-controller-deps:ready";

function getAppControllerDepsReadyState() {
  const existingReadyState = appControllerDepsRoot[APP_CONTROLLER_DEPS_READY_KEY];
  if (
    existingReadyState
    && typeof existingReadyState === "object"
    && typeof existingReadyState.resolve === "function"
    && existingReadyState.promise
    && typeof existingReadyState.promise.then === "function"
  ) {
    return existingReadyState;
  }

  let resolveReady;
  const readyState = {
    resolved: false,
    promise: new Promise((resolve) => {
      resolveReady = resolve;
    }),
    resolve(value) {
      if (!readyState.resolved) {
        readyState.resolved = true;
        resolveReady(value);
      }
      return value;
    },
  };

  appControllerDepsRoot[APP_CONTROLLER_DEPS_READY_KEY] = readyState;
  return readyState;
}

function signalAppControllerDepsReady(deps) {
  const readyState = getAppControllerDepsReadyState();
  readyState.resolve(deps);
  appControllerDepsRoot.APP_CONTROLLER_DEPS_READY = readyState.promise;

  if (typeof appControllerDepsRoot.dispatchEvent === "function" && typeof Event === "function") {
    appControllerDepsRoot.dispatchEvent(new Event(APP_CONTROLLER_DEPS_READY_EVENT));
  }
}

export function createTrackerRenderControllerDeps(context = {}) {
  const {
    dom,
    state,
    escapeHtml,
    formatKoreanDate,
    formatBuildingAutomationEstimateValue,
    buildTrackerEntriesEmptyStateView,
    buildTrackerEntryCardView,
    buildTrackerEntriesListMarkup,
    buildTrackerBoardEmptyStateView,
    buildTrackerBoardMarkup,
    buildTrackerEntrySummaryDetail,
    renderSalesClaimSection,
    renderTrackerEntryRelatedNotices,
    renderSelectedEntry,
    loadSelectedEntryDetail,
    toggleTrackerEntryRelated,
    openTrackerEntryNoticeViewer,
    claimSalesProject,
    setSalesNoteDraft,
    saveSalesClaimNote,
    transferSalesClaim,
    openSalesCloseDialog,
    closeSalesClaim,
    releaseSalesClaim,
    flash,
    resetTrackerBoardEdit,
    syncUrlState,
    prefetchTrackerEntryDetails,
    toggleTrackerBoardBlankPriority,
    beginTrackerBoardEdit,
    saveTrackerBoardEdit,
    getSalesClaimForProject,
    TRACKER_BOARD_COLUMNS,
    TRACKER_BOARD_TEXTAREA_FIELDS,
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
  } = context;

  return {
    dom,
    state,
    escapeHtml,
    formatKoreanDate,
    formatBuildingAutomationEstimateValue,
    buildTrackerEntriesEmptyStateView,
    buildTrackerEntryCardView,
    buildTrackerEntriesListMarkup,
    buildTrackerBoardEmptyStateView,
    buildTrackerBoardMarkup,
    buildTrackerEntrySummaryDetail,
    renderSalesClaimSection,
    renderTrackerEntryRelatedNotices,
    renderSelectedEntry,
    loadSelectedEntryDetail,
    toggleTrackerEntryRelated,
    openTrackerEntryNoticeViewer,
    bindRelatedNoticeViewerButtons,
    claimSalesProject,
    setSalesNoteDraft,
    saveSalesClaimNote,
    transferSalesClaim,
    openSalesCloseDialog,
    closeSalesClaim,
    releaseSalesClaim,
    flash,
    resetTrackerBoardEdit,
    syncUrlState,
    prefetchTrackerEntryDetails,
    toggleTrackerBoardBlankPriority,
    beginTrackerBoardEdit,
    saveTrackerBoardEdit,
    getSalesClaimForProject,
    TRACKER_BOARD_COLUMNS,
    TRACKER_BOARD_TEXTAREA_FIELDS,
    TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
    trackerEntriesEmptyStateCopy: {
      errorPrefix: "트래커 항목을 불러오지 못했습니다.",
      userEmptyHtml: '<div class="empty-state">현재 담당자가 없는 프로젝트가 없습니다.</div>',
      adminEmptyHtml: '<div class="empty-state">No tracker rows loaded.</div>',
    },
    trackerEntryCardLabels: {
      noticeViewButtonLabel: "공고문 보기",
      grossAreaLabel: "연면적",
      constructionCostLabel: "공사비",
      estimateLabel: "빌딩자동제어 추정금액(공사비 최대 3%)",
      architectOfficeLabel: "설계사무소",
      constructionStartDateLabel: "착공",
      openingScheduledDateLabel: "개관예정일",
      demandContactLabel: "담당",
      siteLocationLabel: "현장",
    },
    trackerBoardEmptyHtml: "트래커 행을 불러오면 여기에 표로 표시됩니다.",
    trackerTransferNoTargetMessage: "이관 대상 사용자를 선택해라.",
  };
}

const APP_CONTROLLER_DEPS = {
  createAuthControllerDeps,
  createAuthUiControllerDeps,
  createTrackerControllerDeps,
  createProjectRelatedControllerDeps,
  createTrackerEntryActionsControllerDeps,
  createOrgAdminControllerDeps,
  createTrackerRenderControllerDeps,
  createRuntimeEnhancementsDeps,
  createDownloadControllerDeps,
  createRunPanelsControllerDeps,
  createReportPanelsControllerDeps,
  createConsolePanelsControllerDeps,
  createTrackerDiagnosticsPanelControllerDeps,
  createSalesPanelControllerDeps,
  createAppEventBindingsDeps,
  createSelectedEntryControllerDeps,
  normalizeSalesClaimCardViewModel,
};

appControllerDepsRoot.APP_CONTROLLER_DEPS = APP_CONTROLLER_DEPS;
signalAppControllerDepsReady(APP_CONTROLLER_DEPS);
