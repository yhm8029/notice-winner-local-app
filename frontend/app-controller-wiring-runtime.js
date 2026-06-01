(function attachAppControllerWiringRuntime(root) {
  const authRuntime = root.SPMSAppControllerWiringAuthRuntime || null;
  const DEFAULT_BINDING_NAMES = [
    "createAuthControllerDeps",
    "createAuthUiControllerDeps",
    "createTrackerControllerDeps",
    "createProjectRelatedControllerDeps",
    "createTrackerEntryActionsControllerDeps",
    "createOrgAdminControllerDeps",
    "createTrackerRenderControllerDeps",
    "createRuntimeEnhancementsDeps",
    "createDownloadControllerDeps",
    "createRunPanelsControllerDeps",
    "createReportPanelsControllerDeps",
    "createConsolePanelsControllerDeps",
    "createTrackerDiagnosticsPanelControllerDeps",
    "createSalesPanelControllerDeps",
    "createAppEventBindingsDeps",
    "createSelectedEntryControllerDeps",
  ];

  function isObject(value) {
    return typeof value === "object" && value !== null;
  }

  function createAppControllerWiringRuntime(options = {}) {
    const helperSources = Array.isArray(options.helperSources) ? options.helperSources : [];
    const explicitHelpers = isObject(options.helpers) ? options.helpers : {};
    const bindingNames = Array.isArray(options.bindingNames) && options.bindingNames.length
      ? [...options.bindingNames]
      : [...DEFAULT_BINDING_NAMES];
    return {
      helperSources,
      helpers: Object.assign({}, ...helperSources, explicitHelpers),
      bindingNames,
    };
  }

  function createSalesPanelControllerDeps(context = {}) {
    return {
      dom: context.dom,
      state: context.state,
      window: context.window || root,
      api: context.api,
      escapeHtml: context.escapeHtml,
      getLatestSalesNoteItem: context.getLatestSalesNoteItem,
      truncate: context.truncate,
      formatSalesNoteTextForDisplay: context.formatSalesNoteTextForDisplay,
      formatSalesDateLabel: context.formatSalesDateLabel,
      getSalesNoteEntries: context.getSalesNoteEntries,
      getSalesYearMonthBucket: context.getSalesYearMonthBucket,
      formatContractAmountDisplay: context.formatContractAmountDisplay,
      extractContractAmountTextFromSalesNote: context.extractContractAmountTextFromSalesNote,
      salesClaimStatusLabel: context.salesClaimStatusLabel,
      getVisibleSalesProjectIds: context.getVisibleSalesProjectIds,
      getSalesClaimForProject: context.getSalesClaimForProject,
      getTrackerProjectSnapshot: context.getTrackerProjectSnapshot,
      renderUserSalesProjectFacts: context.renderUserSalesProjectFacts,
      isCurrentUserClaimOwner: context.isCurrentUserClaimOwner,
      canCurrentUserForceRelease: context.canCurrentUserForceRelease,
      canCurrentUserManageClaim: context.canCurrentUserManageClaim,
      isActiveSalesClaim: context.isActiveSalesClaim,
      getOrganizationTransferTargets: context.getOrganizationTransferTargets,
      getSalesNoteDraft: context.getSalesNoteDraft,
      setSalesNoteDraft: context.setSalesNoteDraft,
      upsertSalesClaim: context.upsertSalesClaim,
      replaceVisibleSalesClaims: context.replaceVisibleSalesClaims,
      mergeActiveSalesClaims: context.mergeActiveSalesClaims,
      renderUserOwnedSalesClaimCard: context.renderUserOwnedSalesClaimCard,
      formatSalesClaimEstimateLabel: context.formatSalesClaimEstimateLabel,
      renderCompanySalesClaimCard: context.renderCompanySalesClaimCard,
      renderUserTrackerClaimSection: context.renderUserTrackerClaimSection,
      formatEstimatedAmountRangeFromKrw: context.formatEstimatedAmountRangeFromKrw,
      claimSalesProject: context.claimSalesProject,
      saveSalesClaimNote: context.saveSalesClaimNote,
      transferSalesClaim: context.transferSalesClaim,
      closeSalesClaim: context.closeSalesClaim,
      adminDeleteLatestSalesNote: context.adminDeleteLatestSalesNote,
      releaseSalesClaim: context.releaseSalesClaim,
      formatContractAmountInput: context.formatContractAmountInput,
      buildUserSalesProjectFactsMarkup: context.buildUserSalesProjectFactsMarkup,
      buildSalesClaimEstimateLabelMarkup: context.buildSalesClaimEstimateLabelMarkup,
      buildUserOwnedSalesClaimCardMarkup: context.buildUserOwnedSalesClaimCardMarkup,
      buildCompanySalesClaimCardMarkup: context.buildCompanySalesClaimCardMarkup,
      buildUserTrackerClaimSectionMarkup: context.buildUserTrackerClaimSectionMarkup,
      formatEokValue: context.formatEokValue,
      getSalesNoteTimeline: context.getSalesNoteTimeline,
      serializeSalesNoteEntry: context.serializeSalesNoteEntry,
      removeLatestSalesNoteEntry: context.removeLatestSalesNoteEntry,
      isAdminRole: context.isAdminRole,
      normalizeSalesClaimCardViewModel: context.normalizeSalesClaimCardViewModel || function normalizeSalesClaimCardViewModel(payload = {}, { includeOwnerLabel = false, shouldShowCurrentOwnerAssignedAt } = {}) {
        const claim = payload.claim || {};
        const projectId = payload.projectId || String(claim.project_id || "").trim();
        const noteEntries = Array.isArray(payload.noteEntries) ? payload.noteEntries : [];
        const runtimeShowAssignedAt = typeof shouldShowCurrentOwnerAssignedAt === "function"
          ? shouldShowCurrentOwnerAssignedAt(claim)
          : undefined;
        const viewModel = {
          ...payload,
          claim,
          projectId,
          noteEntries,
          showAssignedAt: payload.showAssignedAt ?? Boolean(
            runtimeShowAssignedAt ?? (
              claim?.current_owner_assigned_at
                && claim?.claimed_at
                && String(claim.current_owner_assigned_at).trim() !== String(claim.claimed_at).trim()
            )
          ),
        };
        if (includeOwnerLabel) {
          viewModel.latestNote = Object.prototype.hasOwnProperty.call(payload, "latestNote")
            ? payload.latestNote
            : (noteEntries.length ? noteEntries[noteEntries.length - 1] : null);
          viewModel.ownerLabel = Object.prototype.hasOwnProperty.call(payload, "ownerLabel")
            ? payload.ownerLabel
            : (claim.owner_display_name || claim.owner_email || "-");
        }
        return viewModel;
      },
      renderTrackerEntries: context.renderTrackerEntries,
      loadSalesOverview: context.loadSalesOverview,
      loadMySalesClaims: context.loadMySalesClaims,
      loadVisibleSalesClaims: context.loadVisibleSalesClaims,
      refreshSalesAdminPanels: context.refreshSalesAdminPanels,
      syncUrlState: context.syncUrlState,
      salesViewRuntime: context.salesViewRuntime,
      flash: context.flash,
    };
  }

  function createProjectRelatedControllerDeps(context = {}) {
    return {
      state: context.state,
      window: context.window || root,
      api: context.api,
      flash: context.flash,
      escapeHtml: context.escapeHtml,
      RELATED_NOTICE_RUNTIME: context.RELATED_NOTICE_RUNTIME,
      PROJECT_RELATED_READY_CACHE_TTL_MS: context.PROJECT_RELATED_READY_CACHE_TTL_MS,
      PROJECT_RELATED_SEED_CACHE_TTL_MS: context.PROJECT_RELATED_SEED_CACHE_TTL_MS,
      PROJECT_RELATED_STORAGE_KEY: context.PROJECT_RELATED_STORAGE_KEY,
      PROJECT_RELATED_STORAGE_MAX_ITEMS: context.PROJECT_RELATED_STORAGE_MAX_ITEMS,
      renderNoticeViewerWindow: context.renderNoticeViewerWindow,
      renderNoticeViewerPayload: context.renderNoticeViewerPayload,
      renderNoticeViewerError: context.renderNoticeViewerError,
      renderProjects: context.renderProjects,
      renderTrackerEntries: context.renderTrackerEntries,
      loadProjectRelatedNotices: context.loadProjectRelatedNotices,
      loadSelectedEntryDetail: context.loadSelectedEntryDetail,
    };
  }

  function createRunPanelsControllerDeps(context = {}) {
    const {
      state,
      dom,
      window,
      document,
      RUN_VIEW_RUNTIME,
      api,
      flash,
      touchSyncMeta,
      setBusy,
      loadRuns,
      trackerController,
      resetTrackerBoardEdit,
      syncUrlState,
      refreshSelectedRun,
      escapeHtml,
      runTypeLabel,
      statusBadge,
      formatDate,
      formatJson,
      progressPercent,
      renderRunExecutionContext,
      isProjectTrackerRun,
      useGlobalTrackerEntriesScope,
      renderArtifactsList,
      buildArtifactEmptyMessage,
      loadTrackerEntries,
    } = context;

    return {
      state,
      dom,
      window,
      document,
      RUN_VIEW_RUNTIME,
      api,
      flash,
      touchSyncMeta,
      setBusy,
      loadRuns,
      trackerController,
      resetTrackerBoardEdit,
      syncUrlState,
      refreshSelectedRun,
      escapeHtml,
      runTypeLabel,
      statusBadge,
      formatDate,
      formatJson,
      progressPercent,
      renderRunExecutionContext,
      isProjectTrackerRun,
      useGlobalTrackerEntriesScope,
      renderArtifactsList,
      buildArtifactEmptyMessage,
      loadTrackerEntries,
    };
  }

  function createReportPanelsControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      api: context.api,
      flash: context.flash,
      setBusy: context.setBusy,
      escapeHtml: context.escapeHtml,
      formatDate: context.formatDate,
      formatJson: context.formatJson,
      formatBytes: context.formatBytes,
      statusBadge: context.statusBadge,
      ARTIFACT_RUNTIME: context.ARTIFACT_RUNTIME,
      RELATED_NOTICE_RUNTIME: context.RELATED_NOTICE_RUNTIME,
      loadDashboardSummary: context.loadDashboardSummary,
      touchSyncMeta: context.touchSyncMeta,
      syncUrlState: context.syncUrlState,
      callRunPanelsController: context.callRunPanelsController,
    };
  }

  function createConsolePanelsControllerDeps(context = {}) {
    return {
      dom: context.dom,
      state: context.state,
      escapeHtml: context.escapeHtml,
      formatDate: context.formatDate,
      runTypeLabel: context.runTypeLabel,
      statusBadge: context.statusBadge,
      metricCard: context.metricCard,
      PROJECT_RUNTIME: context.PROJECT_RUNTIME,
      RUN_VIEW_RUNTIME: context.RUN_VIEW_RUNTIME,
      renderArtifactPreviewMarkup: context.renderArtifactPreviewMarkup,
      resolveTrackerExecutionContext: context.resolveTrackerExecutionContext,
      trackerExecutionTone: context.trackerExecutionTone,
      trackerExecutionMessage: context.trackerExecutionMessage,
      progressPercent: context.progressPercent,
      trackerExportStageLabel: context.trackerExportStageLabel,
      renderRelatedProjectNotices: context.renderRelatedProjectNotices,
      bindRelatedNoticeViewerButtons: context.bindRelatedNoticeViewerButtons,
      toggleProjectRelated: context.toggleProjectRelated,
      openProjectNoticeViewer: context.openProjectNoticeViewer,
      applyPresetParams: context.applyPresetParams,
      api: context.api,
      syncUrlState: context.syncUrlState,
      syncCollectModeOptions: context.syncCollectModeOptions,
      touchSyncMeta: context.touchSyncMeta,
      flash: context.flash,
    };
  }

  function createDownloadControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      window: context.window || root,
      document: context.document,
      setBusy: context.setBusy,
      flash: context.flash,
      api: context.api,
      readTrackerFiltersFromControls: context.readTrackerFiltersFromControls,
      useGlobalTrackerEntriesScope: context.useGlobalTrackerEntriesScope,
      resolveActiveTrackerRunId: context.resolveActiveTrackerRunId,
    };
  }

  function createAdminGoogleSheetsControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      window: context.window || root,
      api: context.api,
      flash: context.flash,
      renderAdminTopNavigation: context.renderAdminTopNavigation,
      renderAdminEmbedPanel: context.renderAdminEmbedPanel,
      canLoadProtectedConsoleData: context.canLoadProtectedConsoleData,
      maybeResolveLegacyAdminAliasToSheetTab: context.maybeResolveLegacyAdminAliasToSheetTab,
      getValidatedActiveAdminGoogleSheetTab: context.getValidatedActiveAdminGoogleSheetTab,
      isAdminGoogleSheetTabKey: context.isAdminGoogleSheetTabKey,
      isPendingLegacyAdminAlias: context.isPendingLegacyAdminAlias,
      shouldDeferAdminGoogleSheetPayloadLoad: context.shouldDeferAdminGoogleSheetPayloadLoad,
      clearAdminGoogleSheetPopupStateForTab: context.clearAdminGoogleSheetPopupStateForTab,
      syncUrlState: context.syncUrlState,
      applyUiMode: context.applyUiMode,
      persistAdminGoogleSheetsCache: context.persistAdminGoogleSheetsCache,
      googleSheetsRuntime: context.googleSheetsRuntime,
      defaultAdminTab: context.defaultAdminTab,
    };
  }

  function createTrackerDiagnosticsPanelControllerDeps(context = {}) {
    return {
      window: context.window || root,
      dom: context.dom,
      state: context.state,
      api: context.api,
      flash: context.flash,
      trackerController: context.trackerController,
      escapeHtml: context.escapeHtml,
      formatDate: context.formatDate,
      formatContactResolutionStatusLabel: context.formatContactResolutionStatusLabel,
      formatContactResolutionReasonLabel: context.formatContactResolutionReasonLabel,
      formatBackfillConflictResolutionLabel: context.formatBackfillConflictResolutionLabel,
      getTrackerDiagnosticsScope: context.getTrackerDiagnosticsScope,
      requireTrackerDiagnosticsRuntime: context.requireTrackerDiagnosticsRuntime,
      buildTrackerChangeEventsMarkup: context.buildTrackerChangeEventsMarkup,
      buildTrackerChangeBellPopoverMarkup: context.buildTrackerChangeBellPopoverMarkup,
      buildBackfillConflictsMarkup: context.buildBackfillConflictsMarkup,
      buildBackfillConflictsView: context.buildBackfillConflictsView,
      syncUrlState: context.syncUrlState,
      renderTrackerEntries: context.renderTrackerEntries,
      loadSelectedEntryDetail: context.loadSelectedEntryDetail,
      focusTrackerChangeEntry: context.focusTrackerChangeEntry,
      closeTrackerChangeModal: context.closeTrackerChangeModal,
    };
  }

  function createTrackerEntryActionsControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      EDITABLE_FIELDS: context.EDITABLE_FIELDS,
      TRACKER_BOARD_BLANK_PRIORITY_FIELDS: context.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
      escapeHtml: context.escapeHtml,
      syncUrlState: context.syncUrlState,
      renderTrackerEntries: context.renderTrackerEntries,
      renderTrackerBoard: context.renderTrackerBoard,
      loadTrackerEntries: context.loadTrackerEntries,
      setBusy: context.setBusy,
      patchTrackerEntry: context.patchTrackerEntry,
      flash: context.flash,
      syncTrackerEntryAfterPatch: context.syncTrackerEntryAfterPatch,
    };
  }

  function createSelectedEntryControllerDeps(context = {}) {
    return {
      dom: context.dom,
      state: context.state,
      buildSelectedEntryLoadingView: context.buildSelectedEntryLoadingView,
      buildSelectedEntryEmptyView: context.buildSelectedEntryEmptyView,
      buildSelectedEntryDisplayView: context.buildSelectedEntryDisplayView,
      buildPatchPanelView: context.buildPatchPanelView,
      buildSelectedEntryMeta: context.buildSelectedEntryMeta,
      buildSelectedEntryChangeEventsMarkup: context.buildSelectedEntryChangeEventsMarkup,
      buildEntryDiagnosticsMarkup: context.buildEntryDiagnosticsMarkup,
      buildEntryFieldGridMarkup: context.buildEntryFieldGridMarkup,
      buildDrawerFieldListMarkup: context.buildDrawerFieldListMarkup,
      truncate: context.truncate,
      escapeHtml: context.escapeHtml,
      requireSelectedEntryRuntime: context.requireSelectedEntryRuntime,
      formatJson: context.formatJson,
      EDITABLE_FIELDS: context.EDITABLE_FIELDS,
      loadSelectedEntryAudit: context.loadSelectedEntryAudit,
      loadSelectedEntryChangeEvents: context.loadSelectedEntryChangeEvents,
      openDrawer: context.openDrawer,
      closeDrawer: context.closeDrawer,
      syncUrlState: context.syncUrlState,
    };
  }

  function createTrackerControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      api: context.api,
      flash: context.flash,
      setBusy: context.setBusy,
      FormData: context.FormData,
      escapeHtml: context.escapeHtml,
      formatDate: context.formatDate,
      syncUrlState: context.syncUrlState,
      readRunFiltersFromControls: context.readRunFiltersFromControls,
      renderRuns: context.renderRuns,
      renderRunsPagination: context.renderRunsPagination,
      renderRunDetail: context.renderRunDetail,
      renderRunEventStatus: context.renderRunEventStatus,
      renderLogsList: context.renderLogsList,
      upsertRunListItem: context.upsertRunListItem,
      renderTrackerEntries: context.renderTrackerEntries,
      renderEntriesPagination: context.renderEntriesPagination,
      renderSalesSummaryPanel: context.renderSalesSummaryPanel,
      renderTrackerChangeEventsPanel: context.renderTrackerChangeEventsPanel,
      renderTrackerContactResolutionSummary: context.renderTrackerContactResolutionSummary,
      renderBackfillConflictsPanel: context.renderBackfillConflictsPanel,
      renderTrackerCleanupPreview: context.renderTrackerCleanupPreview,
      renderProjectRelatedHosts: context.renderProjectRelatedHosts,
      touchSyncMeta: context.touchSyncMeta,
      persistTrackerChangeEventsCache: context.persistTrackerChangeEventsCache,
      clearTrackerChangeEventsCache: context.clearTrackerChangeEventsCache,
      handleOutOfRangePageError: context.handleOutOfRangePageError,
      canLoadProtectedConsoleData: context.canLoadProtectedConsoleData,
      TRACKER_REGION_OPTIONS: context.TRACKER_REGION_OPTIONS,
      useGlobalTrackerEntriesScope: context.useGlobalTrackerEntriesScope,
      shouldUseHomeBootstrapTrackerSnapshot: context.shouldUseHomeBootstrapTrackerSnapshot,
      isProjectTrackerRun: context.isProjectTrackerRun,
      schedulePolling: context.schedulePolling,
      loadWinnerRunPanels: context.loadWinnerRunPanels,
      loadTrackerExportPanels: context.loadTrackerExportPanels,
      loadSelectedRunLogs: context.loadSelectedRunLogs,
      loadBackfillConflicts: context.loadBackfillConflicts,
      loadVisibleSalesClaims: context.loadVisibleSalesClaims,
      requireTrackerDiagnosticsRuntime: context.requireTrackerDiagnosticsRuntime,
      clearProjectRelatedRefresh: context.clearProjectRelatedRefresh,
      maybeScheduleProjectRelatedRefresh: context.maybeScheduleProjectRelatedRefresh,
      canReuseProjectRelatedPayload: context.canReuseProjectRelatedPayload,
      cacheProjectRelatedPayload: context.cacheProjectRelatedPayload,
      isProjectRelatedVisible: context.isProjectRelatedVisible,
      resolveTrackerEntryProjectId: context.resolveTrackerEntryProjectId,
      ensureTrackerEntryProjectId: context.ensureTrackerEntryProjectId,
      TRACKER_ENTRY_RUNTIME: context.TRACKER_ENTRY_RUNTIME,
      TRACKER_DETAIL_PREFETCH_LIMIT: context.TRACKER_DETAIL_PREFETCH_LIMIT,
      warmTrackerEntriesDownload: context.warmTrackerEntriesDownload,
      closeDrawer: context.closeDrawer,
      renderTrackerBoard: context.renderTrackerBoard,
      resetTrackerBoardEdit: context.resetTrackerBoardEdit,
      loadAdminConsoleData: context.loadAdminConsoleData,
      buildSelectedEntryAuditMarkup: context.buildSelectedEntryAuditMarkup,
      loadSelectedEntryDetail: context.loadSelectedEntryDetail,
      renderTrackerMissingReport: context.renderTrackerMissingReport,
      renderSelectedEntryChangeEvents: context.renderSelectedEntryChangeEvents,
      renderSelectedEntry: context.renderSelectedEntry,
      renderSelectedEntryLoading: context.renderSelectedEntryLoading,
      resolveTrackerPatchActorLabel: context.resolveTrackerPatchActorLabel,
      runTypeLabel: context.runTypeLabel,
    };
  }

  function createTrackerRenderControllerDeps(context = {}) {
    return {
      dom: context.dom,
      state: context.state,
      escapeHtml: context.escapeHtml,
      formatKoreanDate: context.formatKoreanDate,
      formatBuildingAutomationEstimateValue: context.formatBuildingAutomationEstimateValue,
      TRACKER_ENTRY_RUNTIME: context.TRACKER_ENTRY_RUNTIME,
      buildTrackerBoardEmptyStateView: context.buildTrackerBoardEmptyStateView,
      buildTrackerBoardMarkup: context.buildTrackerBoardMarkup,
      buildTrackerEntryCardMarkupFallback: context.buildTrackerEntryCardMarkupFallback,
      renderSalesClaimSection: context.renderSalesClaimSection,
      renderTrackerEntryRelatedNotices: context.renderTrackerEntryRelatedNotices,
      resetTrackerBoardEdit: context.resetTrackerBoardEdit,
      renderSelectedEntry: context.renderSelectedEntry,
      buildTrackerEntrySummaryDetail: context.buildTrackerEntrySummaryDetail,
      loadSelectedEntryDetail: context.loadSelectedEntryDetail,
      toggleTrackerEntryRelated: context.toggleTrackerEntryRelated,
      openTrackerEntryNoticeViewer: context.openTrackerEntryNoticeViewer,
      bindRelatedNoticeViewerButtons: context.bindRelatedNoticeViewerButtons,
      claimSalesProject: context.claimSalesProject,
      setSalesNoteDraft: context.setSalesNoteDraft,
      saveSalesClaimNote: context.saveSalesClaimNote,
      transferSalesClaim: context.transferSalesClaim,
      flash: context.flash,
      openSalesCloseDialog: context.openSalesCloseDialog,
      closeSalesClaim: context.closeSalesClaim,
      releaseSalesClaim: context.releaseSalesClaim,
      syncUrlState: context.syncUrlState,
      prefetchTrackerEntryDetails: context.prefetchTrackerEntryDetails,
      getSalesClaimForProject: context.getSalesClaimForProject,
      getSortedTrackerBoardEntries: context.getSortedTrackerBoardEntries,
      TRACKER_BOARD_COLUMNS: context.TRACKER_BOARD_COLUMNS,
      renderTrackerBoardHeaderCell: context.renderTrackerBoardHeaderCell,
      renderTrackerBoardCell: context.renderTrackerBoardCell,
      toggleTrackerBoardBlankPriority: context.toggleTrackerBoardBlankPriority,
      beginTrackerBoardEdit: context.beginTrackerBoardEdit,
      saveTrackerBoardEdit: context.saveTrackerBoardEdit,
    };
  }

  function createOrgAdminControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      window: context.window || root,
      document: context.document,
      navigator: context.navigator,
      api: context.api,
      flash: context.flash,
      setBusy: context.setBusy,
      escapeHtml: context.escapeHtml,
      formatOrgRoleLabel: context.formatOrgRoleLabel,
      renderInvitationStatus: context.renderInvitationStatus,
      renderOrganizationAdminPanel: context.renderOrganizationAdminPanel,
      canUseAdminMode: context.canUseAdminMode,
      formatDate: context.formatDate,
      formatInvitationStatusLabel: context.formatInvitationStatusLabel,
      formatAccountStatusLabel: context.formatAccountStatusLabel,
      formatMembershipStatusLabel: context.formatMembershipStatusLabel,
      resolveStatusClass: context.resolveStatusClass,
      membershipStatusOptions: context.membershipStatusOptions,
      formatDownloadScopeLabel: context.formatDownloadScopeLabel,
      formatDownloadFormatLabel: context.formatDownloadFormatLabel,
      formatDownloadSourcePageLabel: context.formatDownloadSourcePageLabel,
      platformAdminAccountRuntime: context.platformAdminAccountRuntime,
      syncPlatformAdminAccountDraftFromForm: context.syncPlatformAdminAccountDraftFromForm,
      handlePlatformAdminAccountSubmit: context.handlePlatformAdminAccountSubmit,
      renderOrgAdminRuntimeReloadFallback: context.renderOrgAdminRuntimeReloadFallback,
      canManagePlatformAdminAccounts: context.canManagePlatformAdminAccounts,
      resetOrganizationMemberPassword: context.resetOrganizationMemberPassword,
      requireConsoleDataRuntime: context.requireConsoleDataRuntime,
      getConsoleDataRuntimeDeps: context.getConsoleDataRuntimeDeps,
      requireOrganizationAdminRuntime: context.requireOrganizationAdminRuntime,
      loadSalesClaimSummaryByUser: context.loadSalesClaimSummaryByUser,
      loadClosedSalesClaims: context.loadClosedSalesClaims,
    };
  }

  function createRuntimeEnhancementsDeps(context = {}) {
    return {
      dom: context.dom,
      document: context.document,
      syncCollectModeOptions: context.syncCollectModeOptions,
      RUN_VIEW_RUNTIME: context.RUN_VIEW_RUNTIME,
      renderOrganizationAdminPanel: context.renderOrganizationAdminPanel,
    };
  }

  if (typeof authRuntime?.createAppEventBindingsDeps !== "function") {
    throw new Error("SPMSAppControllerWiringAuthRuntime is required before app-controller-wiring-runtime.js loads");
  }

  const runtimeRoot = root.SPMSAppControllerWiringRuntime || {};
  runtimeRoot.DEFAULT_BINDING_NAMES = DEFAULT_BINDING_NAMES;
  runtimeRoot.createAppControllerWiringRuntime = createAppControllerWiringRuntime;
  runtimeRoot.createAuthControllerDeps = authRuntime.createAuthControllerDeps;
  runtimeRoot.createAuthUiControllerDeps = authRuntime.createAuthUiControllerDeps;
  runtimeRoot.createAppEventBindingsDeps = authRuntime.createAppEventBindingsDeps;
  runtimeRoot.createConsolePanelsControllerDeps = createConsolePanelsControllerDeps;
  runtimeRoot.createAdminGoogleSheetsControllerDeps = createAdminGoogleSheetsControllerDeps;
  runtimeRoot.createDownloadControllerDeps = createDownloadControllerDeps;
  runtimeRoot.createOrgAdminControllerDeps = createOrgAdminControllerDeps;
  runtimeRoot.createProjectRelatedControllerDeps = createProjectRelatedControllerDeps;
  runtimeRoot.createReportPanelsControllerDeps = createReportPanelsControllerDeps;
  runtimeRoot.createRunPanelsControllerDeps = createRunPanelsControllerDeps;
  runtimeRoot.createSalesPanelControllerDeps = createSalesPanelControllerDeps;
  runtimeRoot.normalizeSalesClaimCardViewModel = authRuntime.normalizeSalesClaimCardViewModel;
  runtimeRoot.createTrackerEntryActionsControllerDeps = createTrackerEntryActionsControllerDeps;
  runtimeRoot.createTrackerDiagnosticsPanelControllerDeps = createTrackerDiagnosticsPanelControllerDeps;
  runtimeRoot.createTrackerRenderControllerDeps = createTrackerRenderControllerDeps;
  runtimeRoot.createTrackerControllerDeps = createTrackerControllerDeps;
  runtimeRoot.createUiModeControllerDeps = authRuntime.createUiModeControllerDeps;
  runtimeRoot.createSelectedEntryControllerDeps = createSelectedEntryControllerDeps;
  runtimeRoot.createRuntimeEnhancementsDeps = createRuntimeEnhancementsDeps;
  root.SPMSAppControllerWiringRuntime = runtimeRoot;
}(typeof window !== "undefined" ? window : globalThis));
