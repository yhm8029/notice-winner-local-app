(function attachAppSupportViewRuntime(global) {
  const SHELL_RUNTIME = global.SPMSAppShellRuntime || null;
  const DOWNLOAD_AUDIT_SCOPE_LABELS = SHELL_RUNTIME?.DOWNLOAD_AUDIT_SCOPE_LABELS || {
    my: "my",
    company: "company",
    global: "global",
  };
  const DOWNLOAD_AUDIT_FORMAT_LABELS = SHELL_RUNTIME?.DOWNLOAD_AUDIT_FORMAT_LABELS || {
    xlsx: "xlsx",
    csv: "csv",
  };
  const DOWNLOAD_AUDIT_SOURCE_PAGE_LABELS = SHELL_RUNTIME?.DOWNLOAD_AUDIT_SOURCE_PAGE_LABELS || {
    my_active_sales: "my_active_sales",
    company_active_sales: "company_active_sales",
    tracker_entries: "tracker_entries",
  };

  function syntheticDebugEnabled(state) {
    return Boolean((state?.dashboard || {}).synthetic_debug_enabled);
  }

  function normalizeCollectMode(value, state) {
    const raw = String(value || "").trim().toLowerCase();
    if (raw === "synthetic" && !syntheticDebugEnabled(state)) {
      return "auto";
    }
    if (["auto", "native", "synthetic"].includes(raw)) {
      return raw;
    }
    return "auto";
  }

  function trackerColumnStyleFallback(widths, index) {
    const width = Array.isArray(widths) ? Number(widths[index] || 0) : 0;
    if (!Number.isFinite(width) || width <= 0) {
      return "";
    }
    return `min-width:${Math.max(72, Math.round(width * 7))}px`;
  }

  function buildWorkbookTitleCellsFallback(titleRow, helpers = {}) {
    const { escapeHtml = (value) => String(value || "") } = helpers;
    if (!Array.isArray(titleRow) || !titleRow.length) {
      return '<th colspan="1">트래커 양식</th>';
    }
    const groups = [];
    let index = 0;
    while (index < titleRow.length) {
      const value = String(titleRow[index] || "").trim();
      if (value) {
        let span = 1;
        let cursor = index + 1;
        while (cursor < titleRow.length && !String(titleRow[cursor] || "").trim()) {
          span += 1;
          cursor += 1;
        }
        groups.push({ value, span, align: cursor >= titleRow.length ? "right" : "left" });
        index = cursor;
        continue;
      }
      index += 1;
    }
    if (!groups.length) {
      return `<th colspan="${titleRow.length}">트래커 양식</th>`;
    }
    return groups
      .map(
        (group) =>
          `<th colspan="${group.span}" class="tracker-title-cell tracker-title-cell-${group.align}">${escapeHtml(group.value)}</th>`,
      )
      .join("");
  }

  function fetchArtifactPreview(api, item) {
    const limit = item?.artifact_type === "tracking_excel" ? 16 : 6;
    return api(`/api/artifacts/${item?.id}/preview?limit=${limit}`);
  }

  async function ensureArtifactPreviewCached(options = {}) {
    const {
      state = {},
      api = async () => ({}),
      item = null,
      renderArtifactsList = () => {},
      renderRunExecutionContext = () => {},
    } = options;
    if (!item || state.artifactPreviewCache?.[item.id]) {
      return;
    }
    try {
      state.artifactPreviewCache[item.id] = await fetchArtifactPreview(api, item);
    } catch (err) {
      state.artifactPreviewCache[item.id] = { error: err.message || "미리보기 로드 실패" };
    }
    if (state.openArtifactId === item.id) {
      renderArtifactsList();
    }
    if (state.selectedTrackerWorkbookArtifactId === item.id) {
      renderRunExecutionContext(state.selectedRun);
    }
  }

  function formatDownloadScopeLabel(scope) {
    const raw = String(scope || "").trim();
    return DOWNLOAD_AUDIT_SCOPE_LABELS[raw] || raw || "-";
  }

  function formatDownloadFormatLabel(format) {
    const raw = String(format || "").trim();
    return DOWNLOAD_AUDIT_FORMAT_LABELS[raw] || raw || "-";
  }

  function formatDownloadSourcePageLabel(sourcePage) {
    const raw = String(sourcePage || "").trim();
    return DOWNLOAD_AUDIT_SOURCE_PAGE_LABELS[raw] || raw || "-";
  }

  function changeProjectsPageFallback(options = {}, delta = 0) {
    const {
      state = {},
      controller = null,
      loadProjects = () => {},
    } = options;
    if (controller?.changeProjectsPage) {
      return controller.changeProjectsPage(delta);
    }
    const totalPages = Math.max(1, Math.ceil((state.projectsTotal || 0) / (state.projectFilters?.pageSize || 1)));
    const nextPage = Math.min(totalPages, Math.max(1, (state.projectFilters?.page || 1) + delta));
    if (nextPage === state.projectFilters?.page) {
      return undefined;
    }
    state.projectFilters.page = nextPage;
    void loadProjects({ silent: true });
    return undefined;
  }

  function renderTrackerContactResolutionSummaryFallback(options = {}, errorMessage = "") {
    const {
      dom = {},
      TRACKER_DIAGNOSTICS_RUNTIME = null,
      renderTrackerContactResolutionSummary = () => {},
    } = options;
    if (!dom.trackerContactResolutionSummary || !dom.trackerContactResolutionList) {
      return undefined;
    }
    if (!TRACKER_DIAGNOSTICS_RUNTIME) {
      dom.trackerContactResolutionSummary.className = "missing-report-summary empty-state";
      dom.trackerContactResolutionSummary.innerHTML = '<div class="empty-state">연락처 검증 UI 런타임을 불러오지 못했습니다.</div>';
      dom.trackerContactResolutionList.className = "missing-report-list empty-state";
      dom.trackerContactResolutionList.innerHTML = '<div class="empty-state">연락처 검증 UI 런타임을 불러오지 못했습니다.</div>';
      return undefined;
    }
    return renderTrackerContactResolutionSummary(errorMessage);
  }

  function renderTrackerCleanupPreviewFallback(options = {}, errorMessage = "") {
    const {
      dom = {},
      TRACKER_DIAGNOSTICS_RUNTIME = null,
      renderTrackerCleanupPreview = () => {},
    } = options;
    if (!dom.trackerCleanupPreview) {
      return undefined;
    }
    if (!TRACKER_DIAGNOSTICS_RUNTIME) {
      dom.trackerCleanupPreview.className = "missing-report-list empty-state";
      dom.trackerCleanupPreview.innerHTML = '<div class="empty-state">tracker cleanup UI 런타임을 불러오지 못했습니다.</div>';
      return undefined;
    }
    return renderTrackerCleanupPreview(errorMessage);
  }

  function renderTrackerMissingReportFallback(options = {}, errorMessage = "") {
    const {
      state = {},
      dom = {},
      TRACKER_MISSING_REPORT_RUNTIME = null,
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
    } = options;
    if (!dom.missingReportSummary || !dom.missingReportList) {
      return undefined;
    }
    if (!TRACKER_MISSING_REPORT_RUNTIME) {
      dom.missingReportSummary.innerHTML = '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>';
      dom.missingReportList.innerHTML = '<div class="empty-state">누락 UI 런타임을 불러오지 못했습니다.</div>';
      return undefined;
    }

    const view = TRACKER_MISSING_REPORT_RUNTIME.buildMissingReportViewModel(
      state.trackerMissingReport,
      { errorMessage },
      { escapeHtml, formatDate },
    );
    if (view.summaryClassName) {
      dom.missingReportSummary.className = view.summaryClassName;
    }
    dom.missingReportSummary.innerHTML = view.summaryMarkup;
    if (view.listClassName) {
      dom.missingReportList.className = view.listClassName;
    }
    dom.missingReportList.innerHTML = view.listMarkup;
    return undefined;
  }

  function createFrontendRuntimeAdapters(options = {}) {
    const {
      SALES_RUNTIME = null,
      TRACKER_CHANGE_RUNTIME = null,
      TRACKER_DIAGNOSTICS_RUNTIME = null,
      TRACKER_ENTRY_RUNTIME = null,
      SELECTED_ENTRY_RUNTIME = null,
      SALES_VIEW_RUNTIME = null,
      TRACKER_CHANGE_FIELD_LABELS = {},
      EDITABLE_FIELDS = [],
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      formatKoreanDate = (value) => String(value ?? ""),
      formatContractAmountDisplay = (value) => String(value ?? ""),
      truncate = (value) => String(value ?? ""),
      getTrackerProjectSnapshot = () => null,
      sortTrackerBoardEntriesFallback = (entries) => (Array.isArray(entries) ? entries : []),
    } = options;

    const salesClaimStatusLabel = SALES_RUNTIME?.salesClaimStatusLabel;
    const getSalesNoteEntries = SALES_RUNTIME?.getSalesNoteEntries;
    const parseSalesDateValue = SALES_RUNTIME?.parseSalesDateValue;
    const getSalesDateParts = SALES_RUNTIME?.getSalesDateParts;
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
    const buildTrackerChangeBellPopoverMarkup = (items) => TRACKER_CHANGE_RUNTIME?.buildTrackerChangeBellPopoverMarkup(items, {
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
    const buildBackfillConflictsView = (adapterOptions) => TRACKER_DIAGNOSTICS_RUNTIME?.buildBackfillConflictsView(adapterOptions, {
      escapeHtml,
      formatDate,
      formatTrackerChangeEventLabel,
      buildBackfillConflictDescription,
      formatBackfillConflictResolutionLabel,
    }) || {
      html: buildBackfillConflictsMarkup(adapterOptions?.items || []),
      isEmpty: !(adapterOptions?.items || []).length,
      bindActions: true,
    };
    const buildSelectedEntryChangeEventsMarkup = (items) => TRACKER_CHANGE_RUNTIME?.buildSelectedEntryChangeEventsMarkup(items, {
      escapeHtml,
      formatDate,
      formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription,
    }) || "";
    const toTrackerEntrySummary = TRACKER_ENTRY_RUNTIME?.toTrackerEntrySummary;
    const buildTrackerEntrySummaryDetail = TRACKER_ENTRY_RUNTIME?.buildTrackerEntrySummaryDetail;
    const buildTrackerEntriesEmptyStateView = (adapterOptions = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerEntriesEmptyStateView(adapterOptions) || null;
    const buildTrackerEntryCardView = (entry, adapterOptions = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerEntryCardView(entry, adapterOptions) || null;
    const buildTrackerEntriesListMarkup = (views, adapterOptions = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerEntriesListMarkup(views, adapterOptions) || "";
    const buildTrackerBoardEmptyStateView = (adapterOptions = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerBoardEmptyStateView(adapterOptions) || null;
    const buildSortedTrackerBoardEntries = (entries, adapterOptions = {}, helpers = {}) => TRACKER_ENTRY_RUNTIME?.buildSortedTrackerBoardEntries(entries, adapterOptions, helpers)
      || sortTrackerBoardEntriesFallback(entries, adapterOptions, helpers);
    const buildTrackerBoardMarkup = (entries, adapterOptions = {}, helpers = {}) => TRACKER_ENTRY_RUNTIME?.buildTrackerBoardMarkup(entries, adapterOptions, helpers) || "";
    const formatEokValue = TRACKER_ENTRY_RUNTIME?.formatEokValue || function formatEokValueFallback(value) {
      const parsed = Number(value || 0);
      if (!Number.isFinite(parsed)) {
        return "0";
      }
      const rounded = Math.round(parsed * 10) / 10;
      return Number.isInteger(rounded) ? String(Math.trunc(rounded)) : rounded.toFixed(1);
    };
    const parseTrackerCostToWon = TRACKER_ENTRY_RUNTIME?.parseTrackerCostToWon || function parseTrackerCostToWonFallback(value) {
      const raw = String(value || "").trim();
      if (!raw) {
        return 0;
      }
      const eokMatch = raw.replaceAll(" ", "").match(/([0-9][0-9,]*(?:\.\d+)?)\s*?억\s*원/);
      if (eokMatch) {
        const parsed = Number(String(eokMatch[1] || "").replaceAll(",", ""));
        if (Number.isFinite(parsed) && parsed > 0) {
          return Math.round(parsed * 100000000);
        }
      }
      const digits = raw.replace(/[^0-9]/g, "");
      if (!digits) {
        return 0;
      }
      const parsed = Number(digits);
      return Number.isFinite(parsed) ? parsed : 0;
    };
    const formatBuildingAutomationEstimateValue = TRACKER_ENTRY_RUNTIME?.formatBuildingAutomationEstimateValue || function formatBuildingAutomationEstimateValueFallback(snapshot, fallbackValue = "") {
      const formatRangeEok = (wonValue) => (wonValue / 100000000).toFixed(2);
      const fallback = String(fallbackValue || snapshot?.building_automation_estimated_amount || "").trim();
      if (fallback) {
        const maxMatch = fallback.match(/최대\s*([0-9][0-9,]*(?:\.\d+)?)\s*억원?/);
        if (maxMatch) {
          return `${String(maxMatch[1] || "").replaceAll(",", "")}억원`;
        }
        return fallback;
      }
      const constructionCostWon = parseTrackerCostToWon(snapshot?.construction_cost || "");
      if (constructionCostWon > 0) {
        return `${formatRangeEok(constructionCostWon * 0.015)}억원~${formatRangeEok(constructionCostWon * 0.02)}억원`;
      }
      return "-";
    };
    const buildSelectedEntryMeta = (entry, adapterOptions = {}) => SELECTED_ENTRY_RUNTIME?.buildSelectedEntryMeta(entry, adapterOptions) || "";
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
      buildTrackerChangeBellPopoverMarkup,
      buildBackfillConflictsMarkup,
      buildBackfillConflictsView,
      buildSelectedEntryChangeEventsMarkup,
      toTrackerEntrySummary,
      buildTrackerEntrySummaryDetail,
      buildTrackerEntriesEmptyStateView,
      buildTrackerEntryCardView,
      buildTrackerEntriesListMarkup,
      buildTrackerBoardEmptyStateView,
      buildSortedTrackerBoardEntries,
      buildTrackerBoardMarkup,
      formatEokValue,
      parseTrackerCostToWon,
      formatBuildingAutomationEstimateValue,
      buildSelectedEntryMeta,
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

  function createSalesPanelDepsHelpers(options = {}) {
    const {
      dom = {},
      state = {},
      windowObject = null,
      api = async () => ({}),
      escapeHtml = (value) => String(value ?? ""),
      runtimeAdapters = {},
      salesStateHelpers = {},
      renderUserOwnedSalesClaimCard = () => "",
      renderCompanySalesClaimCard = () => "",
      renderUserTrackerClaimSection = () => "",
      claimSalesProject = async () => ({}),
      saveSalesClaimNote = async () => ({}),
      transferSalesClaim = async () => ({}),
      closeSalesClaim = async () => ({}),
      adminDeleteLatestSalesNote = async () => ({}),
      releaseSalesClaim = async () => ({}),
      formatContractAmountInput = (value) => String(value ?? ""),
      isAdminRole = () => false,
      normalizeSalesClaimCardViewModel = (payload) => payload,
      renderTrackerEntries = () => {},
      loadSalesOverview = async () => ({}),
      loadMySalesClaims = async () => ({}),
      loadVisibleSalesClaims = async () => ({}),
      refreshSalesAdminPanels = async () => ({}),
      salesViewRuntime = null,
      flash = () => {},
    } = options;

    function buildSalesPanelControllerDeps() {
      return {
        dom,
        state,
        window: windowObject,
        api,
        escapeHtml,
        getLatestSalesNoteItem: runtimeAdapters.getLatestSalesNoteItem,
        truncate: runtimeAdapters.truncate,
        formatSalesNoteTextForDisplay: runtimeAdapters.formatSalesNoteTextForDisplay,
        formatSalesDateLabel: runtimeAdapters.formatSalesDateLabel,
        getSalesNoteEntries: runtimeAdapters.getSalesNoteEntries,
        getSalesYearMonthBucket: salesStateHelpers.getSalesYearMonthBucket,
        formatContractAmountDisplay: runtimeAdapters.formatContractAmountDisplay,
        extractContractAmountTextFromSalesNote: runtimeAdapters.extractContractAmountTextFromSalesNote,
        salesClaimStatusLabel: runtimeAdapters.salesClaimStatusLabel,
        getVisibleSalesProjectIds: salesStateHelpers.getVisibleSalesProjectIds,
        getSalesClaimForProject: salesStateHelpers.getSalesClaimForProject,
        getTrackerProjectSnapshot: salesStateHelpers.getTrackerProjectSnapshot,
        renderUserSalesProjectFacts: salesStateHelpers.renderUserSalesProjectFacts,
        isCurrentUserClaimOwner: salesStateHelpers.isCurrentUserClaimOwner,
        canCurrentUserForceRelease: salesStateHelpers.canCurrentUserForceRelease,
        canCurrentUserManageClaim: salesStateHelpers.canCurrentUserManageClaim,
        isActiveSalesClaim: salesStateHelpers.isActiveSalesClaim,
        getOrganizationTransferTargets: salesStateHelpers.getOrganizationTransferTargets,
        getSalesNoteDraft: salesStateHelpers.getSalesNoteDraft,
        setSalesNoteDraft: salesStateHelpers.setSalesNoteDraft,
        upsertSalesClaim: salesStateHelpers.upsertSalesClaim,
        replaceVisibleSalesClaims: salesStateHelpers.replaceVisibleSalesClaims,
        mergeActiveSalesClaims: salesStateHelpers.mergeActiveSalesClaims,
        renderUserOwnedSalesClaimCard,
        formatSalesClaimEstimateLabel: runtimeAdapters.buildSalesClaimEstimateLabel,
        renderCompanySalesClaimCard,
        renderUserTrackerClaimSection,
        formatEstimatedAmountRangeFromKrw: salesStateHelpers.formatEstimatedAmountRangeFromKrw,
        claimSalesProject,
        saveSalesClaimNote,
        transferSalesClaim,
        closeSalesClaim,
        adminDeleteLatestSalesNote,
        releaseSalesClaim,
        formatContractAmountInput,
        buildUserSalesProjectFactsMarkup: runtimeAdapters.buildUserSalesProjectFactsMarkup,
        buildSalesClaimEstimateLabelMarkup: runtimeAdapters.buildSalesClaimEstimateLabel,
        buildUserOwnedSalesClaimCardMarkup: runtimeAdapters.buildUserOwnedSalesClaimCardMarkup,
        buildCompanySalesClaimCardMarkup: runtimeAdapters.buildCompanySalesClaimCardMarkup,
        buildUserTrackerClaimSectionMarkup: runtimeAdapters.buildUserTrackerClaimSectionMarkup,
        formatEokValue: runtimeAdapters.formatEokValue,
        getSalesNoteTimeline: runtimeAdapters.getSalesNoteTimeline,
        serializeSalesNoteEntry: runtimeAdapters.serializeSalesNoteEntry,
        removeLatestSalesNoteEntry: runtimeAdapters.removeLatestSalesNoteEntry,
        isAdminRole,
        normalizeSalesClaimCardViewModel,
        renderTrackerEntries,
        loadSalesOverview,
        loadMySalesClaims,
        loadVisibleSalesClaims,
        refreshSalesAdminPanels,
        salesViewRuntime,
        flash,
      };
    }

    return {
      buildSalesPanelControllerDeps,
    };
  }

  function createDownloadControllerDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      window = global,
      document = null,
      setBusy = () => {},
      flash = () => {},
      api = async () => ({}),
      readTrackerFiltersFromControls = () => {},
      useGlobalTrackerEntriesScope = () => false,
      resolveActiveTrackerRunId = () => "",
    } = options;

    function buildDownloadControllerDeps() {
      return {
        state,
        dom,
        window,
        document,
        setBusy,
        flash,
        api,
        readTrackerFiltersFromControls,
        useGlobalTrackerEntriesScope,
        resolveActiveTrackerRunId,
      };
    }

    return {
      buildDownloadControllerDeps,
    };
  }

  function createAppSupportViewRuntime(options = {}) {
    const state = options.state || null;
    return {
      syntheticDebugEnabled: () => syntheticDebugEnabled(state),
      normalizeCollectMode(value) {
        return normalizeCollectMode(value, state);
      },
      trackerColumnStyle(widths, index, runtime = null) {
        return runtime?.trackerColumnStyle?.(widths, index) || trackerColumnStyleFallback(widths, index);
      },
      buildWorkbookTitleCells(titleRow, helpers = {}, runtime = null) {
        return runtime?.buildWorkbookTitleCells?.(titleRow, helpers) || buildWorkbookTitleCellsFallback(titleRow, helpers);
      },
      fetchArtifactPreview(item, apiImpl) {
        return fetchArtifactPreview(apiImpl, item);
      },
      ensureArtifactPreviewCached,
      formatDownloadScopeLabel,
      formatDownloadFormatLabel,
      formatDownloadSourcePageLabel,
      changeProjectsPage: changeProjectsPageFallback,
      renderTrackerContactResolutionSummary: renderTrackerContactResolutionSummaryFallback,
      renderTrackerCleanupPreview: renderTrackerCleanupPreviewFallback,
      renderTrackerMissingReport: renderTrackerMissingReportFallback,
      createFrontendRuntimeAdapters,
      createSalesPanelDepsHelpers,
      createDownloadControllerDepsHelpers,
    };
  }

  global.SPMSAppSupportViewRuntime = {
    createAppSupportViewRuntime,
  };
})(window);
