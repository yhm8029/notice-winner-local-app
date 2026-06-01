(function attachAppSupportUiRuntime(global) {
  function callRunPanelsControllerFallback(options = {}) {
    const {
      methodName = "",
      fallback = null,
      args = [],
      controller = null,
      state = {},
      dom = {},
      windowObject = global,
      RUN_PANELS_FALLBACK_RUNTIME = null,
      flash = () => {},
      setBusy = () => {},
      api = async () => ({}),
      FormData: FormDataCtor = global.FormData,
      isProjectTrackerRun = () => false,
      dispatch = () => undefined,
    } = options;

    const method = controller?.[methodName];
    if (typeof method === "function") {
      return method.apply(controller, args);
    }
    if (typeof fallback === "function") {
      return fallback(...args);
    }

    switch (methodName) {
      case "syncRunActionButtons": {
        const [run] = args;
        const isRunning = run && (run.status === "queued" || run.status === "running");
        const trackerRunning = state.selectedTrackerRun && ["queued", "running"].includes(state.selectedTrackerRun.status);
        const canCancel = run && !["success", "failed", "cancelled"].includes(run.status);
        const canTrackerExport = run && isProjectTrackerRun(run.run_type) && run.status === "success";

        dom.cancelRunButton.disabled = !canCancel;
        dom.trackerExportButton.disabled = !canTrackerExport;
        dom.refreshRunButton.disabled = !run;
        dom.refreshLogsButton.disabled = !run;
        dom.refreshArtifactsButton.disabled = !run;
        if (!isRunning && !trackerRunning) {
          windowObject.clearTimeout(state.pollHandle);
          state.pollHandle = null;
        }
        return undefined;
      }
      case "resolveTrackerExecutionContext": {
        const [run] = args;
        return RUN_PANELS_FALLBACK_RUNTIME?.resolveTrackerExecutionContextFallback?.(run, {
          isProjectTrackerRun,
        }) || null;
      }
      case "normalizeTrackerExecutionContext": {
        const [payload = {}] = args;
        return RUN_PANELS_FALLBACK_RUNTIME?.normalizeTrackerExecutionContextFallback?.(payload) || null;
      }
      case "numericSummaryValue":
        return RUN_PANELS_FALLBACK_RUNTIME?.numericSummaryValueFallback?.(args) ?? 0;
      case "trackerExportStageLabel": {
        const [stage] = args;
        return RUN_PANELS_FALLBACK_RUNTIME?.trackerExportStageLabelFallback?.(stage) || String(stage || "waiting");
      }
      case "trackerExecutionTone": {
        const [status] = args;
        return RUN_PANELS_FALLBACK_RUNTIME?.trackerExecutionToneFallback?.(status) || "";
      }
      case "trackerExecutionMessage": {
        const [context = null] = args;
        return RUN_PANELS_FALLBACK_RUNTIME?.trackerExecutionMessageFallback?.(context) || "";
      }
      case "applyPresetParams": {
        const [params] = args;
        for (const [name, rawValue] of Object.entries(params || {})) {
          const input = dom.runForm?.querySelector?.(`[name="${name}"]`);
          if (!input) {
            continue;
          }
          input.value = rawValue == null ? "" : String(rawValue);
        }
        return undefined;
      }
      case "applySelectedPreset": {
        const presetId = dom.presetSelect?.value || state.selectedPresetId;
        if (!presetId) {
          flash("적용할 프리셋을 선택하세요.", "error");
          return undefined;
        }
        const preset = state.runPresets.find((item) => item.id === presetId);
        if (!preset) {
          flash("선택한 프리셋을 찾지 못했습니다.", "error");
          return undefined;
        }
        state.selectedPresetId = preset.id;
        dispatch("applyPresetParams", null, preset.params || {});
        dispatch("renderRunPresetPanel", null);
        flash(`프리셋 적용: ${preset.name}`);
        return undefined;
      }
      case "saveCurrentFormAsPreset": {
        const defaultName = `${new Date().toISOString().slice(0, 10)} 검색 조건`;
        const name = windowObject.prompt("프리셋 이름", defaultName);
        if (!name || !name.trim()) {
          return undefined;
        }
        const formData = new FormDataCtor(dom.runForm);
        const params = {};
        for (const [key, value] of formData.entries()) {
          params[key] = String(value ?? "");
        }
        setBusy(dom.presetSaveButton, true, "저장 중...");
        return api("/api/run-presets", {
          method: "POST",
          body: JSON.stringify({ name: name.trim(), params }),
        })
          .then(async (response) => {
            state.selectedPresetId = response.id;
            flash(`프리셋 저장: ${response.name}`);
            await dispatch("loadRunPresets", null, { silent: true });
            return response;
          })
          .catch((err) => {
            flash(err.message, "error");
            return undefined;
          })
          .finally(() => {
            setBusy(dom.presetSaveButton, false, "현재 조건 저장");
          });
      }
      default:
        return undefined;
    }
  }

  function createRunPanelsControllerDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      window = global,
      document = null,
      RUN_VIEW_RUNTIME = null,
      api = async () => ({}),
      flash = () => {},
      touchSyncMeta = () => {},
      setBusy = () => {},
      loadRuns = async () => {},
      trackerController = {},
      resetTrackerBoardEdit = () => {},
      syncUrlState = () => {},
      refreshSelectedRun = async () => {},
      escapeHtml = (value) => String(value ?? ""),
      runTypeLabel = (value) => String(value ?? ""),
      statusBadge = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      formatJson = (value) => JSON.stringify(value),
      progressPercent = (value) => Number(value ?? 0),
      renderRunExecutionContext = () => {},
      isProjectTrackerRun = () => false,
      useGlobalTrackerEntriesScope = () => false,
      renderArtifactsList = () => {},
      buildArtifactEmptyMessage = () => "",
      loadTrackerEntries = async () => {},
    } = options;

    function buildRunPanelsControllerDeps() {
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

    return {
      buildRunPanelsControllerDeps,
    };
  }

  function createReportPanelsControllerDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      api = async () => ({}),
      flash = () => {},
      setBusy = () => {},
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      formatJson = (value) => JSON.stringify(value),
      formatBytes = (value) => String(value ?? ""),
      statusBadge = (value) => String(value ?? ""),
      ARTIFACT_RUNTIME = null,
      RELATED_NOTICE_RUNTIME = null,
      loadDashboardSummary = async () => {},
      touchSyncMeta = () => {},
      syncUrlState = () => {},
      callRunPanelsController = () => {},
    } = options;

    function buildReportPanelsControllerDeps() {
      return {
        state,
        dom,
        api,
        flash,
        setBusy,
        escapeHtml,
        formatDate,
        formatJson,
        formatBytes,
        statusBadge,
        ARTIFACT_RUNTIME,
        RELATED_NOTICE_RUNTIME,
        loadDashboardSummary,
        touchSyncMeta,
        syncUrlState,
        callRunPanelsController,
      };
    }

    return {
      buildReportPanelsControllerDeps,
    };
  }

  function createConsolePanelsControllerDepsHelpers(options = {}) {
    const {
      dom = {},
      state = {},
      escapeHtml = (value) => String(value ?? ""),
      formatDate = (value) => String(value ?? ""),
      runTypeLabel = (value) => String(value ?? ""),
      statusBadge = (value) => String(value ?? ""),
      metricCard = (label, value) => `${label}:${value}`,
      PROJECT_RUNTIME = null,
      RUN_VIEW_RUNTIME = null,
      renderArtifactPreviewMarkup = () => "",
      resolveTrackerExecutionContext = () => null,
      trackerExecutionTone = () => "",
      trackerExecutionMessage = () => "",
      progressPercent = (value) => Number(value ?? 0),
      trackerExportStageLabel = () => "",
      renderRelatedProjectNotices = () => "",
      bindRelatedNoticeViewerButtons = () => {},
      toggleProjectRelated = () => {},
      openProjectNoticeViewer = () => {},
      applyPresetParams = () => {},
      api = async () => ({}),
      syncUrlState = () => {},
      syncCollectModeOptions = () => {},
      touchSyncMeta = () => {},
      flash = () => {},
    } = options;

    function buildConsolePanelsControllerDeps() {
      return {
        dom,
        state,
        escapeHtml,
        formatDate,
        runTypeLabel,
        statusBadge,
        metricCard,
        PROJECT_RUNTIME,
        RUN_VIEW_RUNTIME,
        renderArtifactPreviewMarkup,
        resolveTrackerExecutionContext,
        trackerExecutionTone,
        trackerExecutionMessage,
        progressPercent,
        trackerExportStageLabel,
        renderRelatedProjectNotices,
        bindRelatedNoticeViewerButtons,
        toggleProjectRelated,
        openProjectNoticeViewer,
        applyPresetParams,
        api,
        syncUrlState,
        syncCollectModeOptions,
        touchSyncMeta,
        flash,
      };
    }

    return {
      buildConsolePanelsControllerDeps,
    };
  }

  function buildAppEventBindingsDepsFromApp(options = {}) {
    const {
      core = {},
      auth = {},
      orgAdmin = {},
      sales = {},
      runs = {},
      reports = {},
      ui = {},
      tracker = {},
      downloads = {},
    } = options;
    return {
      dom: core.dom,
      state: core.state,
      window: core.window,
      document: core.document,
      AUTH_MODE_SIGN_IN: auth.AUTH_MODE_SIGN_IN,
      AUTH_MODE_SIGN_UP: auth.AUTH_MODE_SIGN_UP,
      TRACKER_REGION_OPTIONS: tracker.TRACKER_REGION_OPTIONS,
      handleAuthSubmit: auth.handleAuthSubmit,
      setAuthMode: auth.setAuthMode,
      handleAuthFindId: auth.handleAuthFindId,
      handleAuthPasswordReset: auth.handleAuthPasswordReset,
      scheduleInvitationPreviewLookup: auth.scheduleInvitationPreviewLookup,
      renderAuthUi: auth.renderAuthUi,
      handleAuthSignOut: auth.handleAuthSignOut,
      openProfileDialog: auth.openProfileDialog,
      handleProfileSubmit: auth.handleProfileSubmit,
      handleInvitationSubmit: orgAdmin.handleInvitationSubmit,
      loadOrganizationAdminData: orgAdmin.loadOrganizationAdminData,
      closeProfileDialog: auth.closeProfileDialog,
      setTrackerChangeBellPopoverOpen: tracker.setTrackerChangeBellPopoverOpen,
      downloadSalesWorkbook: downloads.downloadSalesWorkbook,
      closeSalesCloseDialog: sales.closeSalesCloseDialog,
      formatContractAmountInput: sales.formatContractAmountInput,
      confirmSalesCloseDialog: sales.confirmSalesCloseDialog,
      refreshAuthSessionState: auth.refreshAuthSessionState,
      loadDashboardSummary: reports.loadDashboardSummary,
      handleRunCreate: runs.handleRunCreate,
      handleRunFormReset: runs.handleRunFormReset,
      refreshSelectedRun: runs.refreshSelectedRun,
      loadRuns: runs.loadRuns,
      loadSelectedRunLogs: runs.loadSelectedRunLogs,
      runSelectedReport: reports.runSelectedReport,
      refreshReportPanels: reports.refreshReportPanels,
      loadSelectedRunArtifacts: runs.loadSelectedRunArtifacts,
      cancelSelectedRun: runs.cancelSelectedRun,
      createTrackerExportForSelectedRun: runs.createTrackerExportForSelectedRun,
      toggleUiMode: ui.toggleUiMode,
      renderSyncMeta: ui.renderSyncMeta,
      syncUrlState: ui.syncUrlState,
      loadReportJobs: reports.loadReportJobs,
      loadPhaseReport: reports.loadPhaseReport,
      readRunFiltersFromControls: runs.readRunFiltersFromControls,
      readTrackerFiltersFromControls: tracker.readTrackerFiltersFromControls,
      syncFilterControlsFromState: tracker.syncFilterControlsFromState,
      changeRunsPage: runs.changeRunsPage,
      loadTrackerEntries: tracker.loadTrackerEntries,
      trackerChangeEventsCacheIsFresh: tracker.trackerChangeEventsCacheIsFresh,
      renderTrackerChangeBellPopover: tracker.renderTrackerChangeBellPopover,
      loadTrackerChangeEvents: tracker.loadTrackerChangeEvents,
      focusTrackerChangePanel: tracker.focusTrackerChangePanel,
      uploadTrackerTemplate: tracker.uploadTrackerTemplate,
      resetTrackerTemplateOverride: tracker.resetTrackerTemplateOverride,
      changeEntriesPageTo: tracker.changeEntriesPageTo,
      changeEntriesPage: tracker.changeEntriesPage,
      getEntriesTotalPages: tracker.getEntriesTotalPages,
      normalizeTrackerRegionFilter: tracker.normalizeTrackerRegionFilter,
      parseTrackerRegionFilter: tracker.parseTrackerRegionFilter,
      saveEntryPatch: tracker.saveEntryPatch,
      clearEntryPatch: tracker.clearEntryPatch,
      loadSelectedEntryAudit: tracker.loadSelectedEntryAudit,
      loadTrackerMissingReport: tracker.loadTrackerMissingReport,
      refreshSalesAdminPanels: sales.refreshSalesAdminPanels,
      getMissingReportDownloadLimit: tracker.getMissingReportDownloadLimit,
      syncPatchValueFromSelectedEntry: tracker.syncPatchValueFromSelectedEntry,
      closeDrawer: tracker.closeDrawer,
      loadRunPresets: runs.loadRunPresets,
      applySelectedPreset: runs.applySelectedPreset,
      saveCurrentFormAsPreset: runs.saveCurrentFormAsPreset,
      renderRunPresetPanel: runs.renderRunPresetPanel,
      loadProjects: reports.loadProjects,
      changeProjectsPage: reports.changeProjectsPage,
      triggerTrackerEntriesXlsxDownload: downloads.triggerTrackerEntriesXlsxDownload,
    };
  }

  function createSelectedEntryControllerDepsHelpers(options = {}) {
    const {
      dom = {},
      state = {},
      buildSelectedEntryLoadingView = () => null,
      buildSelectedEntryEmptyView = () => null,
      buildSelectedEntryDisplayView = () => null,
      buildPatchPanelView = () => null,
      buildSelectedEntryChangeEventsMarkup = () => "",
      buildSelectedEntryMeta = () => "",
      buildEntryDiagnosticsMarkup = () => "",
      buildEntryFieldGridMarkup = () => "",
      buildDrawerFieldListMarkup = () => "",
      truncate = (value) => String(value ?? ""),
      escapeHtml = (value) => String(value ?? ""),
      SELECTED_ENTRY_RUNTIME = null,
      formatJson = (value) => JSON.stringify(value),
      EDITABLE_FIELDS = [],
      loadSelectedEntryAudit = async () => {},
      loadSelectedEntryChangeEvents = async () => {},
      openDrawer = () => {},
      closeDrawer = () => {},
      syncUrlState = () => {},
    } = options;

    function buildSelectedEntryControllerDeps() {
      return {
        dom,
        state,
        buildSelectedEntryLoadingView,
        buildSelectedEntryEmptyView,
        buildSelectedEntryDisplayView,
        buildPatchPanelView,
        buildSelectedEntryChangeEventsMarkup,
        buildSelectedEntryMeta,
        buildEntryDiagnosticsMarkup,
        buildEntryFieldGridMarkup,
        buildDrawerFieldListMarkup,
        truncate,
        escapeHtml,
        requireSelectedEntryRuntime: () => SELECTED_ENTRY_RUNTIME || null,
        formatJson,
        EDITABLE_FIELDS,
        loadSelectedEntryAudit,
        loadSelectedEntryChangeEvents,
        openDrawer,
        closeDrawer,
        syncUrlState,
      };
    }

    return {
      buildSelectedEntryControllerDeps,
    };
  }

  function createUiModeControllerDepsHelpers(options = {}) {
    const {
      state = {},
      dom = {},
      window = global,
      DEFAULT_ADMIN_TAB = "",
      APP_ROOT_PATH = "",
      normalizeLocationPath = (value) => String(value ?? ""),
      getAdminRoutePath = () => "",
      canUseAdminMode = () => false,
      canLoadProtectedConsoleData = () => false,
      shouldShowAdminModeToggle = () => false,
      shouldShowSharedGoogleSheetsShell = () => false,
      isPendingLegacyAdminAlias = () => false,
      clearAdminLegacyRouteIntent = () => {},
      getAdminTabByPathname = () => null,
      resolveUiModeFromLocation = () => "user",
      resolveLegacyAdminRoutePath = () => "",
      normalizeAdminTab = (value) => String(value ?? ""),
      clearAdminGoogleSheetPopupStateForTab = () => false,
      maybePreloadAdminGoogleSheetsBootstrap = () => {},
      syncUrlState = () => {},
      syncTrackerChangeBellVisibility = () => {},
      hydrateTrackerChangeEventsCache = () => {},
      renderTrackerChangeEventUnreadCount = () => {},
      renderTrackerChangeBellPopover = () => {},
      renderAdminTopNavigation = () => {},
      renderAdminEmbedPanel = () => {},
      renderTrackerTemplateStatus = () => {},
      loadAdminConsoleData = async () => {},
      loadBackfillConflicts = async () => {},
      renderBackfillConflictsPanel = () => {},
      closeDrawer = () => {},
      renderAuthUi = () => {},
      renderOrganizationAdminPanel = () => {},
      renderMySalesClaimsPanel = () => {},
      renderSalesSummaryPanel = () => {},
      renderRunDetail = () => {},
      renderTrackerEntries = () => {},
      loadOrganizationUsers = async () => {},
      loadTrackerEntries = async () => {},
      loadTrackerChangeEventUnreadCount = async () => {},
      loadTrackerChangeEvents = async () => {},
      clearUserModeRunSelection = () => {},
      hydrateHomeBootstrapCache = () => {},
      loadHomeBootstrap = async () => {},
      scheduleTrackerChangeEventsWarmup = () => {},
    } = options;

    function buildUiModeControllerDeps() {
      return {
        state,
        dom,
        window,
        DEFAULT_ADMIN_TAB,
        APP_ROOT_PATH,
        normalizeLocationPath,
        getAdminRoutePath,
        canUseAdminMode,
        canLoadProtectedConsoleData,
        shouldShowAdminModeToggle,
        shouldShowSharedGoogleSheetsShell,
        isPendingLegacyAdminAlias,
        clearAdminLegacyRouteIntent,
        getAdminTabByPathname,
        resolveUiModeFromLocation,
        resolveLegacyAdminRoutePath,
        normalizeAdminTab,
        clearAdminGoogleSheetPopupStateForTab,
        maybePreloadAdminGoogleSheetsBootstrap,
        syncUrlState,
        syncTrackerChangeBellVisibility,
        hydrateTrackerChangeEventsCache,
        renderTrackerChangeEventUnreadCount,
        renderTrackerChangeBellPopover,
        renderAdminTopNavigation,
        renderAdminEmbedPanel,
        renderTrackerTemplateStatus,
        loadAdminConsoleData,
        loadBackfillConflicts,
        renderBackfillConflictsPanel,
        closeDrawer,
        renderAuthUi,
        renderOrganizationAdminPanel,
        renderMySalesClaimsPanel,
        renderSalesSummaryPanel,
        renderRunDetail,
        renderTrackerEntries,
        loadOrganizationUsers,
        loadTrackerEntries,
        loadTrackerChangeEventUnreadCount,
        loadTrackerChangeEvents,
        clearUserModeRunSelection,
        hydrateHomeBootstrapCache,
        loadHomeBootstrap,
        scheduleTrackerChangeEventsWarmup,
      };
    }

    return {
      buildUiModeControllerDeps,
    };
  }

  function createUiModeControllerDepsHelpersFromApp(options = {}) {
    const {
      core = {},
      adminTabs = {},
      ui = {},
      trackerChange = {},
      adminData = {},
      renders = {},
      trackers = {},
      bootstrap = {},
    } = options;
    return createUiModeControllerDepsHelpers({
      state: core.state,
      dom: core.dom,
      window: core.window,
      DEFAULT_ADMIN_TAB: adminTabs.DEFAULT_ADMIN_TAB,
      APP_ROOT_PATH: adminTabs.APP_ROOT_PATH,
      normalizeLocationPath: adminTabs.normalizeLocationPath,
      getAdminRoutePath: adminTabs.getAdminRoutePath,
      canUseAdminMode: ui.canUseAdminMode,
      canLoadProtectedConsoleData: ui.canLoadProtectedConsoleData,
      shouldShowAdminModeToggle: ui.shouldShowAdminModeToggle,
      shouldShowSharedGoogleSheetsShell: ui.shouldShowSharedGoogleSheetsShell,
      isPendingLegacyAdminAlias: adminTabs.isPendingLegacyAdminAlias,
      clearAdminLegacyRouteIntent: adminTabs.clearAdminLegacyRouteIntent,
      getAdminTabByPathname: adminTabs.getAdminTabByPathname,
      resolveUiModeFromLocation: adminTabs.resolveUiModeFromLocation,
      resolveLegacyAdminRoutePath: adminTabs.resolveLegacyAdminRoutePath,
      normalizeAdminTab: adminTabs.normalizeAdminTab,
      clearAdminGoogleSheetPopupStateForTab: adminTabs.clearAdminGoogleSheetPopupStateForTab,
      maybePreloadAdminGoogleSheetsBootstrap: adminData.maybePreloadAdminGoogleSheetsBootstrap,
      syncUrlState: ui.syncUrlState,
      syncTrackerChangeBellVisibility: trackerChange.syncTrackerChangeBellVisibility,
      hydrateTrackerChangeEventsCache: trackerChange.hydrateTrackerChangeEventsCache,
      renderTrackerChangeEventUnreadCount: trackerChange.renderTrackerChangeEventUnreadCount,
      renderTrackerChangeBellPopover: trackerChange.renderTrackerChangeBellPopover,
      renderAdminTopNavigation: renders.renderAdminTopNavigation,
      renderAdminEmbedPanel: renders.renderAdminEmbedPanel,
      renderTrackerTemplateStatus: renders.renderTrackerTemplateStatus,
      loadAdminConsoleData: adminData.loadAdminConsoleData,
      loadBackfillConflicts: trackers.loadBackfillConflicts,
      renderBackfillConflictsPanel: trackers.renderBackfillConflictsPanel,
      closeDrawer: trackers.closeDrawer,
      renderAuthUi: renders.renderAuthUi,
      renderOrganizationAdminPanel: renders.renderOrganizationAdminPanel,
      renderMySalesClaimsPanel: renders.renderMySalesClaimsPanel,
      renderSalesSummaryPanel: renders.renderSalesSummaryPanel,
      renderRunDetail: renders.renderRunDetail,
      renderTrackerEntries: renders.renderTrackerEntries,
      loadOrganizationUsers: adminData.loadOrganizationUsers,
      loadTrackerEntries: trackers.loadTrackerEntries,
      loadTrackerChangeEventUnreadCount: trackerChange.loadTrackerChangeEventUnreadCount,
      loadTrackerChangeEvents: trackerChange.loadTrackerChangeEvents,
      clearUserModeRunSelection: bootstrap.clearUserModeRunSelection,
      hydrateHomeBootstrapCache: bootstrap.hydrateHomeBootstrapCache,
      loadHomeBootstrap: bootstrap.loadHomeBootstrap,
      scheduleTrackerChangeEventsWarmup: trackerChange.scheduleTrackerChangeEventsWarmup,
    });
  }

  function createAdminGoogleSheetsControllerDepsHelpers(options = {}) {
    function buildAdminGoogleSheetsControllerDeps() {
      return {
        ...options,
        window: options.window || global,
      };
    }

    return {
      buildAdminGoogleSheetsControllerDeps,
    };
  }

  function createRuntimeEnhancementsDepsHelpers(options = {}) {
    function buildRuntimeEnhancementsDeps() {
      return options;
    }

    return {
      buildRuntimeEnhancementsDeps,
    };
  }

  function createAppSupportUiRuntime() {
    return {
      callRunPanelsControllerFallback,
      createRunPanelsControllerDepsHelpers,
      createReportPanelsControllerDepsHelpers,
      createConsolePanelsControllerDepsHelpers,
      buildAppEventBindingsDepsFromApp,
      createSelectedEntryControllerDepsHelpers,
      createUiModeControllerDepsHelpers,
      createUiModeControllerDepsHelpersFromApp,
      createAdminGoogleSheetsControllerDepsHelpers,
      createRuntimeEnhancementsDepsHelpers,
    };
  }

  global.SPMSAppSupportUiRuntime = {
    createAppSupportUiRuntime,
  };
})(window);
