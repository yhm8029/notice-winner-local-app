(function attachAppControllerWiringAuthRuntime(root) {
  function normalizeSalesClaimCardViewModel(payload = {}, { includeOwnerLabel = false, shouldShowCurrentOwnerAssignedAt } = {}) {
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
  }

  function createAppEventBindingsDeps(context = {}) {
    return {
      dom: context.dom,
      state: context.state,
      window: context.window || root,
      document: context.document || (typeof document !== "undefined" ? document : null),
      AUTH_MODE_SIGN_IN: context.AUTH_MODE_SIGN_IN,
      AUTH_MODE_SIGN_UP: context.AUTH_MODE_SIGN_UP,
      TRACKER_REGION_OPTIONS: context.TRACKER_REGION_OPTIONS,
      handleAuthSubmit: context.handleAuthSubmit,
      setAuthMode: context.setAuthMode,
      setAdminTab: context.setAdminTab,
      handleAuthFindId: context.handleAuthFindId,
      handleAuthPasswordReset: context.handleAuthPasswordReset,
      scheduleInvitationPreviewLookup: context.scheduleInvitationPreviewLookup,
      renderAuthUi: context.renderAuthUi,
      handleAuthSignOut: context.handleAuthSignOut,
      openProfileDialog: context.openProfileDialog,
      handleProfileSubmit: context.handleProfileSubmit,
      handleInvitationSubmit: context.handleInvitationSubmit,
      loadOrganizationAdminData: context.loadOrganizationAdminData,
      closeProfileDialog: context.closeProfileDialog,
      setTrackerChangeBellPopoverOpen: context.setTrackerChangeBellPopoverOpen,
      downloadSalesWorkbook: context.downloadSalesWorkbook,
      closeSalesCloseDialog: context.closeSalesCloseDialog,
      formatContractAmountInput: context.formatContractAmountInput,
      confirmSalesCloseDialog: context.confirmSalesCloseDialog,
      refreshAuthSessionState: context.refreshAuthSessionState,
      loadDashboardSummary: context.loadDashboardSummary,
      handleRunCreate: context.handleRunCreate,
      handleRunFormReset: context.handleRunFormReset,
      refreshSelectedRun: context.refreshSelectedRun,
      loadRuns: context.loadRuns,
      loadSelectedRunLogs: context.loadSelectedRunLogs,
      runSelectedReport: context.runSelectedReport,
      refreshReportPanels: context.refreshReportPanels,
      loadSelectedRunArtifacts: context.loadSelectedRunArtifacts,
      cancelSelectedRun: context.cancelSelectedRun,
      createTrackerExportForSelectedRun: context.createTrackerExportForSelectedRun,
      toggleUiMode: context.toggleUiMode,
      renderSyncMeta: context.renderSyncMeta,
      syncUrlState: context.syncUrlState,
      loadReportJobs: context.loadReportJobs,
      loadPhaseReport: context.loadPhaseReport,
      readRunFiltersFromControls: context.readRunFiltersFromControls,
      readTrackerFiltersFromControls: context.readTrackerFiltersFromControls,
      syncFilterControlsFromState: context.syncFilterControlsFromState,
      changeRunsPage: context.changeRunsPage,
      loadTrackerEntries: context.loadTrackerEntries,
      trackerChangeEventsCacheIsFresh: context.trackerChangeEventsCacheIsFresh,
      renderTrackerChangeBellPopover: context.renderTrackerChangeBellPopover,
      loadTrackerChangeEvents: context.loadTrackerChangeEvents,
      focusTrackerChangePanel: context.focusTrackerChangePanel,
      uploadTrackerTemplate: context.uploadTrackerTemplate,
      resetTrackerTemplateOverride: context.resetTrackerTemplateOverride,
      changeEntriesPageTo: context.changeEntriesPageTo,
      changeEntriesPage: context.changeEntriesPage,
      getEntriesTotalPages: context.getEntriesTotalPages,
      normalizeTrackerRegionFilter: context.normalizeTrackerRegionFilter,
      parseTrackerRegionFilter: context.parseTrackerRegionFilter,
      saveEntryPatch: context.saveEntryPatch,
      clearEntryPatch: context.clearEntryPatch,
      loadSelectedEntryAudit: context.loadSelectedEntryAudit,
      loadTrackerMissingReport: context.loadTrackerMissingReport,
      refreshSalesAdminPanels: context.refreshSalesAdminPanels,
      getMissingReportDownloadLimit: context.getMissingReportDownloadLimit,
      syncPatchValueFromSelectedEntry: context.syncPatchValueFromSelectedEntry,
      closeDrawer: context.closeDrawer,
      loadRunPresets: context.loadRunPresets,
      applySelectedPreset: context.applySelectedPreset,
      saveCurrentFormAsPreset: context.saveCurrentFormAsPreset,
      renderRunPresetPanel: context.renderRunPresetPanel,
      loadProjects: context.loadProjects,
      changeProjectsPage: context.changeProjectsPage,
      triggerTrackerEntriesXlsxDownload: context.triggerTrackerEntriesXlsxDownload,
    };
  }

  function createAuthControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      document: context.document,
      window: context.window || root,
      api: context.api,
      flash: context.flash,
      setBusy: context.setBusy,
      escapeHtml: context.escapeHtml,
      formatOrgRoleLabel: context.formatOrgRoleLabel,
      formatInvitationStatusLabel: context.formatInvitationStatusLabel,
      formatSalesDateLabel: context.formatSalesDateLabel,
      formatMembershipStatusLabel: context.formatMembershipStatusLabel,
      requireAuthSessionRuntime: context.requireAuthSessionRuntime,
      loadOrganizationUsers: context.loadOrganizationUsers,
      loadOrganizationMembers: context.loadOrganizationMembers,
      loadSalesOverview: context.loadSalesOverview,
      loadMySalesClaims: context.loadMySalesClaims,
      refreshSalesAdminPanels: context.refreshSalesAdminPanels,
      ensureConsoleInitialized: context.ensureConsoleInitialized,
      shouldShowSignUpMode: context.shouldShowSignUpMode,
      AUTH_MODE_SIGN_IN: context.AUTH_MODE_SIGN_IN,
      AUTH_MODE_SIGN_UP: context.AUTH_MODE_SIGN_UP,
      renderAuthUi: context.renderAuthUi,
      syncUiModeChrome: context.syncUiModeChrome,
      applyUiModeTransition: context.applyUiModeTransition,
      canUseAdminMode: context.canUseAdminMode,
      canLoadProtectedConsoleData: context.canLoadProtectedConsoleData,
      loadAdminConsoleData: context.loadAdminConsoleData,
      loadBackfillConflicts: context.loadBackfillConflicts,
      renderBackfillConflictsPanel: context.renderBackfillConflictsPanel,
      renderTrackerContactResolutionSummary: context.renderTrackerContactResolutionSummary,
      renderTrackerCleanupPreview: context.renderTrackerCleanupPreview,
      closeDrawer: context.closeDrawer,
      hydrateHomeBootstrapCache: context.hydrateHomeBootstrapCache,
      clearUserModeRunSelection: context.clearUserModeRunSelection,
      loadHomeBootstrap: context.loadHomeBootstrap,
      loadTrackerEntries: context.loadTrackerEntries,
      trackerController: context.trackerController,
      renderOrganizationAdminPanel: context.renderOrganizationAdminPanel,
      renderMySalesClaimsPanel: context.renderMySalesClaimsPanel,
      renderSalesSummaryPanel: context.renderSalesSummaryPanel,
      renderRunDetail: context.renderRunDetail,
      renderTrackerEntries: context.renderTrackerEntries,
    };
  }

  function createAuthUiControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      document: context.document,
      window: context.window || root,
      api: context.api,
      flash: context.flash,
      setBusy: context.setBusy,
      escapeHtml: context.escapeHtml,
      formatOrgRoleLabel: context.formatOrgRoleLabel,
      formatInvitationStatusLabel: context.formatInvitationStatusLabel,
      formatSalesDateLabel: context.formatSalesDateLabel,
      formatMembershipStatusLabel: context.formatMembershipStatusLabel,
      requireAuthSessionRuntime: context.requireAuthSessionRuntime,
      loadOrganizationUsers: context.loadOrganizationUsers,
      loadOrganizationMembers: context.loadOrganizationMembers,
      loadSalesOverview: context.loadSalesOverview,
      loadMySalesClaims: context.loadMySalesClaims,
      refreshSalesAdminPanels: context.refreshSalesAdminPanels,
      ensureConsoleInitialized: context.ensureConsoleInitialized,
      shouldShowSignUpMode: context.shouldShowSignUpMode,
      AUTH_MODE_SIGN_IN: context.AUTH_MODE_SIGN_IN,
      AUTH_MODE_SIGN_UP: context.AUTH_MODE_SIGN_UP,
      syncUiModeChrome: context.syncUiModeChrome,
      applyUiModeTransition: context.applyUiModeTransition,
    };
  }

  function createUiModeControllerDeps(context = {}) {
    return {
      state: context.state,
      dom: context.dom,
      window: context.window || root,
      DEFAULT_ADMIN_TAB: context.DEFAULT_ADMIN_TAB,
      APP_ROOT_PATH: context.APP_ROOT_PATH,
      normalizeLocationPath: context.normalizeLocationPath,
      getAdminRoutePath: context.getAdminRoutePath,
      canUseAdminMode: context.canUseAdminMode,
      canLoadProtectedConsoleData: context.canLoadProtectedConsoleData,
      shouldShowAdminModeToggle: context.shouldShowAdminModeToggle,
      shouldShowSharedGoogleSheetsShell: context.shouldShowSharedGoogleSheetsShell,
      isPendingLegacyAdminAlias: context.isPendingLegacyAdminAlias,
      clearAdminLegacyRouteIntent: context.clearAdminLegacyRouteIntent,
      getAdminTabByPathname: context.getAdminTabByPathname,
      resolveUiModeFromLocation: context.resolveUiModeFromLocation,
      resolveLegacyAdminRoutePath: context.resolveLegacyAdminRoutePath,
      normalizeAdminTab: context.normalizeAdminTab,
      clearAdminGoogleSheetPopupStateForTab: context.clearAdminGoogleSheetPopupStateForTab,
      maybePreloadAdminGoogleSheetsBootstrap: context.maybePreloadAdminGoogleSheetsBootstrap,
      syncUrlState: context.syncUrlState,
      syncTrackerChangeBellVisibility: context.syncTrackerChangeBellVisibility,
      hydrateTrackerChangeEventsCache: context.hydrateTrackerChangeEventsCache,
      renderTrackerChangeEventUnreadCount: context.renderTrackerChangeEventUnreadCount,
      renderTrackerChangeBellPopover: context.renderTrackerChangeBellPopover,
      renderAdminTopNavigation: context.renderAdminTopNavigation,
      renderAdminEmbedPanel: context.renderAdminEmbedPanel,
      renderTrackerTemplateStatus: context.renderTrackerTemplateStatus,
      loadAdminConsoleData: context.loadAdminConsoleData,
      loadBackfillConflicts: context.loadBackfillConflicts,
      renderBackfillConflictsPanel: context.renderBackfillConflictsPanel,
      closeDrawer: context.closeDrawer,
      renderAuthUi: context.renderAuthUi,
      renderOrganizationAdminPanel: context.renderOrganizationAdminPanel,
      renderMySalesClaimsPanel: context.renderMySalesClaimsPanel,
      renderSalesSummaryPanel: context.renderSalesSummaryPanel,
      renderRunDetail: context.renderRunDetail,
      renderTrackerEntries: context.renderTrackerEntries,
      loadOrganizationUsers: context.loadOrganizationUsers,
      loadTrackerEntries: context.loadTrackerEntries,
      loadTrackerChangeEventUnreadCount: context.loadTrackerChangeEventUnreadCount,
      loadTrackerChangeEvents: context.loadTrackerChangeEvents,
      clearUserModeRunSelection: context.clearUserModeRunSelection,
      hydrateHomeBootstrapCache: context.hydrateHomeBootstrapCache,
      loadHomeBootstrap: context.loadHomeBootstrap,
      scheduleTrackerChangeEventsWarmup: context.scheduleTrackerChangeEventsWarmup,
    };
  }

  root.SPMSAppControllerWiringAuthRuntime = {
    createAppEventBindingsDeps,
    createAuthControllerDeps,
    createAuthUiControllerDeps,
    createUiModeControllerDeps,
    normalizeSalesClaimCardViewModel,
  };
}(typeof window !== "undefined" ? window : globalThis));
