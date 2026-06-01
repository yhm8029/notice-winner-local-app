(function attachAppRuntimeBodyControllerRuntime(global) {
  function createControllerWithWiringDeps({
    windowObject = global,
    createController,
    wiringDepsFactoryName,
    depsFactory,
    missingFactoryError,
  } = {}) {
    if (typeof createController !== "function") {
      if (missingFactoryError) {
        throw new Error(missingFactoryError);
      }
      return null;
    }
    const createDeps = windowObject.SPMSAppControllerWiringRuntime?.[wiringDepsFactoryName];
    if (typeof createDeps !== "function") {
      throw new Error("SPMSAppControllerWiringRuntime is required before app.js loads");
    }
    return createController(createDeps(depsFactory()));
  }

  function createMethodDelegates({ getter, methods = [], strict = false } = {}) {
    const delegates = {};
    for (const methodName of methods) {
      delegates[methodName] = (...args) => {
        const target = typeof getter === "function" ? getter() : null;
        const method = target?.[methodName];
        if (typeof method !== "function") {
          if (strict) {
            throw new Error(`Missing delegated method: ${methodName}`);
          }
          return undefined;
        }
        return method.apply(target, args);
      };
    }
    return delegates;
  }

  function createAppRuntimeBodyControllerAccessors(options = {}) {
    const windowObject = options.windowObject || global;
    const documentObject = options.documentObject || windowObject.document || null;
    const navigatorObject = options.navigatorObject || windowObject.navigator || null;
    const state = options.state || null;
    const dom = options.dom || {};
    const appSupport = options.appSupport || {};
    const runtimeDeps = options.runtimeDeps || {};
    const coreDeps = options.coreDeps || {};
    const controllerDeps = options.controllerDeps || {};
    const callbacks = options.callbacks || {};

    let appRuntimeBodyHelpers = null;
    let orgAdminHelpers = null;
    let appEventBindings = null;
    let adminGoogleSheetsController = null;
    let runtimeEnhancements = null;
    let orgAdminController = null;
    let trackerRenderController = null;
    let projectRelatedController = null;
    let trackerController = null;
    let downloadController = null;
    let trackerDiagnosticsPanelController = null;
    let trackerEntryActionsController = null;
    let selectedEntryController = null;
    let runPanelsController = null;
    let reportPanelsController = null;
    let consolePanelsController = null;
    let uiModeController = null;
    let authController = null;
    let authUiController = null;
    let salesPanelController = null;

    function getAppRuntimeBodyHelpers() {
      if (appRuntimeBodyHelpers) return appRuntimeBodyHelpers;
      const createAppRuntimeBodyHelpers = windowObject.SPMSAppRuntimeBodyHelpers?.createAppRuntimeBodyHelpers;
      if (typeof createAppRuntimeBodyHelpers !== "function") return null;
      appRuntimeBodyHelpers = createAppRuntimeBodyHelpers({
        state,
        dom,
        windowObject,
        documentObject,
        runTypeLabels: runtimeDeps.RUN_TYPE_LABELS,
        runViewRuntime: runtimeDeps.RUN_VIEW_RUNTIME,
        renderTrackerChangeEventsPanel: callbacks.renderTrackerChangeEventsPanel,
      });
      return appRuntimeBodyHelpers;
    }

    function getOrgAdminHelpers() {
      if (orgAdminHelpers) return orgAdminHelpers;
      orgAdminHelpers = appSupport.createOrgAdminHelpers({
        state,
        dom,
        windowObject,
        ORG_ROLE_OPTIONS: runtimeDeps.ORG_ROLE_OPTIONS,
        formatOrgRoleLabel: callbacks.formatOrgRoleLabel,
        formatMembershipStatusLabel: callbacks.formatMembershipStatusLabel,
        escapeHtml: coreDeps.escapeHtml,
        copyInvitationUrl: callbacks.copyInvitationUrl,
        loadOrganizationInvitations: callbacks.loadOrganizationInvitations,
        getOrgAdminRuntime: callbacks.getOrgAdminRuntime,
      });
      return orgAdminHelpers;
    }

    function getAppEventBindingsDeps() {
      return windowObject.SPMSAppControllerWiringRuntime.createAppEventBindingsDeps({
        dom,
        state,
        window: windowObject,
        document: documentObject,
        ...callbacks.appEventBindingsDeps,
      });
    }

    function getAppEventBindings() {
      if (appEventBindings) return appEventBindings;
      const createAppEventBindings = windowObject.APP_EVENT_BINDINGS?.createAppEventBindings;
      if (typeof createAppEventBindings !== "function") return null;
      appEventBindings = createAppEventBindings(getAppEventBindingsDeps());
      return appEventBindings;
    }

    function getTrackerControllerDepsHelpers() {
      if (getTrackerControllerDepsHelpers.cache) return getTrackerControllerDepsHelpers.cache;
      getTrackerControllerDepsHelpers.cache = appSupport.createTrackerControllerDepsHelpers({
        state,
        dom,
        window: windowObject,
        api: coreDeps.api,
        flash: coreDeps.flash,
        setBusy: coreDeps.setBusy,
        FormData: coreDeps.FormData,
        escapeHtml: coreDeps.escapeHtml,
        formatDate: coreDeps.formatDate,
        ...controllerDeps.trackerController,
      });
      return getTrackerControllerDepsHelpers.cache;
    }

    function getAuthControllerDepsHelpers() {
      if (getAuthControllerDepsHelpers.cache) return getAuthControllerDepsHelpers.cache;
      getAuthControllerDepsHelpers.cache = appSupport.createAuthControllerDepsHelpers({
        state,
        dom,
        documentObject,
        windowObject,
        api: coreDeps.api,
        flash: coreDeps.flash,
        setBusy: coreDeps.setBusy,
        escapeHtml: coreDeps.escapeHtml,
        formatOrgRoleLabel: callbacks.formatOrgRoleLabel,
        formatInvitationStatusLabel: callbacks.formatInvitationStatusLabel,
        formatSalesDateLabel: callbacks.formatSalesDateLabel,
        formatMembershipStatusLabel: callbacks.formatMembershipStatusLabel,
        ...controllerDeps.authController,
      });
      return getAuthControllerDepsHelpers.cache;
    }

    function getTrackerControllerBaseDeps() {
      return getTrackerControllerDepsHelpers().buildTrackerControllerBaseDeps();
    }

    function getAuthControllerBaseDeps() {
      return getAuthControllerDepsHelpers().buildAuthControllerBaseDeps();
    }

    function getAdminGoogleSheetsController({ createController, missingFactoryError } = {}) {
      if (adminGoogleSheetsController) return adminGoogleSheetsController;
      adminGoogleSheetsController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createAdminGoogleSheetsControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createAdminGoogleSheetsControllerDepsHelpers({
          state,
          dom,
          window: windowObject,
          api: coreDeps.api,
          flash: coreDeps.flash,
          ...controllerDeps.adminGoogleSheets,
        }).buildAdminGoogleSheetsControllerDeps(),
      });
      return adminGoogleSheetsController;
    }

    function getRuntimeEnhancements({ createController, missingFactoryError } = {}) {
      if (runtimeEnhancements) return runtimeEnhancements;
      runtimeEnhancements = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createRuntimeEnhancementsDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createRuntimeEnhancementsDepsHelpers({
          dom,
          document: documentObject,
          ...controllerDeps.runtimeEnhancements,
        }).buildRuntimeEnhancementsDeps(),
      });
      return runtimeEnhancements;
    }

    function getOrgAdminController({ createController, missingFactoryError } = {}) {
      if (orgAdminController) return orgAdminController;
      orgAdminController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createOrgAdminControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createOrgAdminControllerDepsHelpers({
          sharedDeps: {
            state,
            dom,
            window: windowObject,
            document: documentObject,
            navigator: navigatorObject,
            api: coreDeps.api,
            flash: coreDeps.flash,
            setBusy: coreDeps.setBusy,
          },
          formattingDeps: controllerDeps.orgAdminFormatting,
          actionDeps: controllerDeps.orgAdminActions,
          runtimeDeps: controllerDeps.orgAdminRuntime,
        }).buildOrgAdminControllerDeps(),
      });
      return orgAdminController;
    }

    function getTrackerRenderController({ createController, missingFactoryError } = {}) {
      if (trackerRenderController) return trackerRenderController;
      trackerRenderController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createTrackerRenderControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createTrackerRenderControllerDepsHelpers(
          controllerDeps.trackerRender,
        ).buildTrackerRenderControllerDeps(),
      });
      return trackerRenderController;
    }

    function getProjectRelatedController({ createController, missingFactoryError } = {}) {
      if (projectRelatedController) return projectRelatedController;
      projectRelatedController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createProjectRelatedControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createProjectRelatedControllerDepsHelpers(
          controllerDeps.projectRelated,
        ).buildProjectRelatedControllerDeps(),
      });
      return projectRelatedController;
    }

    function getTrackerController({ createController, missingFactoryError } = {}) {
      if (trackerController) return trackerController;
      trackerController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createTrackerControllerDeps",
        missingFactoryError,
        depsFactory: () => getTrackerControllerDepsHelpers().buildTrackerControllerDeps(),
      });
      return trackerController;
    }

    function getDownloadController({ createController, missingFactoryError } = {}) {
      if (downloadController) return downloadController;
      downloadController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createDownloadControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createDownloadControllerDepsHelpers({
          state,
          dom,
          window: windowObject,
          document: documentObject,
          setBusy: coreDeps.setBusy,
          flash: coreDeps.flash,
          api: coreDeps.api,
          ...controllerDeps.download,
        }).buildDownloadControllerDeps(),
      });
      return downloadController;
    }

    function getTrackerDiagnosticsPanelController({ createController, missingFactoryError } = {}) {
      if (trackerDiagnosticsPanelController) return trackerDiagnosticsPanelController;
      trackerDiagnosticsPanelController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createTrackerDiagnosticsPanelControllerDeps",
        missingFactoryError,
        depsFactory: () => getTrackerControllerDepsHelpers().buildTrackerDiagnosticsPanelControllerDeps(),
      });
      return trackerDiagnosticsPanelController;
    }

    function getTrackerEntryActionsController({ createController, missingFactoryError } = {}) {
      if (trackerEntryActionsController) return trackerEntryActionsController;
      trackerEntryActionsController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createTrackerEntryActionsControllerDeps",
        missingFactoryError,
        depsFactory: () => getTrackerControllerDepsHelpers().buildTrackerEntryActionsControllerDeps(),
      });
      return trackerEntryActionsController;
    }

    function getSelectedEntryController({ createController, missingFactoryError } = {}) {
      if (selectedEntryController) return selectedEntryController;
      selectedEntryController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createSelectedEntryControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createSelectedEntryControllerDepsHelpers({
          dom,
          state,
          truncate: coreDeps.truncate,
          escapeHtml: coreDeps.escapeHtml,
          ...controllerDeps.selectedEntry,
        }).buildSelectedEntryControllerDeps(),
      });
      return selectedEntryController;
    }

    function getRunPanelsController({ createController, missingFactoryError } = {}) {
      if (runPanelsController) return runPanelsController;
      runPanelsController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createRunPanelsControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createRunPanelsControllerDepsHelpers({
          state,
          dom,
          window: windowObject,
          document: documentObject,
          RUN_VIEW_RUNTIME: runtimeDeps.RUN_VIEW_RUNTIME,
          api: coreDeps.api,
          flash: coreDeps.flash,
          setBusy: coreDeps.setBusy,
          escapeHtml: coreDeps.escapeHtml,
          statusBadge: coreDeps.statusBadge,
          formatDate: coreDeps.formatDate,
          formatJson: coreDeps.formatJson,
          progressPercent: coreDeps.progressPercent,
          ...controllerDeps.runPanels,
        }).buildRunPanelsControllerDeps(),
      });
      return runPanelsController;
    }

    function getReportPanelsController({ createController, missingFactoryError } = {}) {
      if (reportPanelsController) return reportPanelsController;
      reportPanelsController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createReportPanelsControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createReportPanelsControllerDepsHelpers({
          state,
          dom,
          api: coreDeps.api,
          flash: coreDeps.flash,
          setBusy: coreDeps.setBusy,
          escapeHtml: coreDeps.escapeHtml,
          formatDate: coreDeps.formatDate,
          formatJson: coreDeps.formatJson,
          formatBytes: coreDeps.formatBytes,
          statusBadge: coreDeps.statusBadge,
          ...controllerDeps.reportPanels,
        }).buildReportPanelsControllerDeps(),
      });
      return reportPanelsController;
    }

    function getConsolePanelsController({ createController, missingFactoryError } = {}) {
      if (consolePanelsController) return consolePanelsController;
      consolePanelsController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createConsolePanelsControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createConsolePanelsControllerDepsHelpers({
          dom,
          state,
          escapeHtml: coreDeps.escapeHtml,
          formatDate: coreDeps.formatDate,
          metricCard: coreDeps.metricCard,
          ...controllerDeps.consolePanels,
        }).buildConsolePanelsControllerDeps(),
      });
      return consolePanelsController;
    }

    function getUiModeController({ createController, missingFactoryError } = {}) {
      if (uiModeController) return uiModeController;
      uiModeController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createUiModeControllerDeps",
        missingFactoryError,
        depsFactory: () => appSupport.createUiModeControllerDepsHelpers({
          state,
          dom,
          window: windowObject,
          DEFAULT_ADMIN_TAB: runtimeDeps.DEFAULT_ADMIN_TAB,
          APP_ROOT_PATH: runtimeDeps.APP_ROOT_PATH,
          ...controllerDeps.uiMode,
        }).buildUiModeControllerDeps(),
      });
      return uiModeController;
    }

    function getAuthController({ createController, missingFactoryError } = {}) {
      if (authController) return authController;
      authController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createAuthControllerDeps",
        missingFactoryError,
        depsFactory: () => getAuthControllerDepsHelpers().buildAuthControllerDeps(),
      });
      return authController;
    }

    function getAuthUiController({ createController, missingFactoryError } = {}) {
      if (authUiController) return authUiController;
      authUiController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createAuthUiControllerDeps",
        missingFactoryError,
        depsFactory: () => getAuthControllerDepsHelpers().buildAuthUiControllerDeps(),
      });
      return authUiController;
    }

    function getSalesPanelController({ createController, missingFactoryError } = {}) {
      if (salesPanelController) return salesPanelController;
      salesPanelController = createControllerWithWiringDeps({
        windowObject,
        createController,
        wiringDepsFactoryName: "createSalesPanelControllerDeps",
        missingFactoryError,
        depsFactory: () => callbacks.getSalesPanelDepsHelpers().buildSalesPanelControllerDeps(),
      });
      return salesPanelController;
    }

    return {
      getAppRuntimeBodyHelpers,
      getOrgAdminHelpers,
      getAppEventBindingsDeps,
      getAppEventBindings,
      getTrackerControllerBaseDeps,
      getTrackerControllerDepsHelpers,
      getAuthControllerBaseDeps,
      getAuthControllerDepsHelpers,
      getAdminGoogleSheetsController,
      getRuntimeEnhancements,
      getOrgAdminController,
      getTrackerRenderController,
      getProjectRelatedController,
      getTrackerController,
      getDownloadController,
      getTrackerDiagnosticsPanelController,
      getTrackerEntryActionsController,
      getSelectedEntryController,
      getRunPanelsController,
      getReportPanelsController,
      getConsolePanelsController,
      getUiModeController,
      getAuthController,
      getAuthUiController,
      getSalesPanelController,
    };
  }

  function createTrackerRenderFallbackAccessors(options = {}) {
    const state = options.state || {};
    const appSupport = options.appSupport || {};
    const runtimeDeps = options.runtimeDeps || {};

    function getFallbackHelpers() {
      return typeof runtimeDeps.getTrackerRenderFallbackHelpers === "function"
        ? runtimeDeps.getTrackerRenderFallbackHelpers()
        : null;
    }

    function getFallbackRuntime() {
      return typeof runtimeDeps.getTrackerRenderFallbackRuntime === "function"
        ? runtimeDeps.getTrackerRenderFallbackRuntime()
        : null;
    }

    function buildTrackerEntryCardMarkupFallback(payload = {}, helpers = {}) {
      return getFallbackRuntime()?.buildTrackerEntryCardMarkupFallback?.(payload, helpers) || "";
    }

    function renderTrackerEntries(entries, { refreshSelectedEntry = true } = {}) {
      const controller = typeof runtimeDeps.getTrackerRenderController === "function"
        ? runtimeDeps.getTrackerRenderController()
        : null;
      if (controller?.renderTrackerEntries) {
        return controller.renderTrackerEntries(entries, { refreshSelectedEntry });
      }
      return renderTrackerEntriesFallback(entries, { refreshSelectedEntry });
    }

    function renderTrackerEntriesFallback(entries, { refreshSelectedEntry = true } = {}) {
      return getFallbackRuntime()?.renderTrackerEntriesFallback?.(
        entries,
        getFallbackHelpers()?.buildTrackerEntriesFallbackDeps(refreshSelectedEntry),
        { escapeHtml: runtimeDeps.escapeHtml },
      ) || undefined;
    }

    function sortTrackerBoardEntriesFallback(entries, { fieldName = "", blankPriorityFields = runtimeDeps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS } = {}, helpers = {}) {
      return getFallbackRuntime()?.sortTrackerBoardEntriesFallback?.(entries, { fieldName, blankPriorityFields }, helpers)
        || (Array.isArray(entries) ? entries : []);
    }

    function buildTrackerBoardMarkupFallback(entries, options = {}, helpers = {}) {
      return getFallbackRuntime()?.buildTrackerBoardMarkupFallback?.(entries, options, helpers) || "";
    }

    function renderTrackerBoard(entries) {
      const controller = typeof runtimeDeps.getTrackerRenderController === "function"
        ? runtimeDeps.getTrackerRenderController()
        : null;
      if (controller?.renderTrackerBoard) {
        return controller.renderTrackerBoard(entries);
      }
      return renderTrackerBoardFallback(entries);
    }

    function renderTrackerBoardFallback(entries) {
      return getFallbackRuntime()?.renderTrackerBoardFallback?.(
        entries,
        getFallbackHelpers()?.buildTrackerBoardFallbackDeps(),
        { escapeHtml: runtimeDeps.escapeHtml },
      ) || undefined;
    }

    function toggleTrackerBoardBlankPriority(fieldName) {
      return runtimeDeps.getTrackerEntryActionsController().toggleTrackerBoardBlankPriority(fieldName);
    }

    function renderTrackerBoardHeaderCell(column) {
      return appSupport.renderTrackerBoardHeaderCellBridge({
        column,
        TRACKER_BOARD_RUNTIME: runtimeDeps.TRACKER_BOARD_RUNTIME,
        fallbackHelpers: getFallbackHelpers(),
        trackerBoardBlankPriorityFields: runtimeDeps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
        trackerBoardSort: state.trackerBoardSort,
        escapeHtml: runtimeDeps.escapeHtml,
      });
    }

    function isTrackerBoardBlankValue(value) {
      return appSupport.isTrackerBoardBlankValueBridge({
        value,
        TRACKER_BOARD_RUNTIME: runtimeDeps.TRACKER_BOARD_RUNTIME,
        fallbackHelpers: getFallbackHelpers(),
      });
    }

    function sortTrackerBoardEntries(entries) {
      return appSupport.sortTrackerBoardEntriesBridge({
        entries,
        TRACKER_BOARD_RUNTIME: runtimeDeps.TRACKER_BOARD_RUNTIME,
        fallbackHelpers: getFallbackHelpers(),
        fieldName: state.trackerBoardSort.fieldName,
        blankPriorityFields: runtimeDeps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS,
        buildSortedTrackerBoardEntries: runtimeDeps.buildSortedTrackerBoardEntries,
      });
    }

    function buildTrackerBoardCellMarkupFallback({ entry, column, displayNo, trackerBoardEdit = null }, { escapeHtml: fallbackEscapeHtml = runtimeDeps.escapeHtml, textareaFields = runtimeDeps.TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {
      return appSupport.buildTrackerBoardCellMarkupFallbackBridge({
        payload: { entry, column, displayNo, trackerBoardEdit },
        fallbackHelpers: getFallbackHelpers(),
        runtime: getFallbackRuntime(),
        escapeHtml: fallbackEscapeHtml,
        textareaFields,
      });
    }

    function buildTrackerBoardEditingCellMarkupFallback({ entry, fieldName, label, value, saving, errorMessage }, { escapeHtml: fallbackEscapeHtml = runtimeDeps.escapeHtml, textareaFields = runtimeDeps.TRACKER_BOARD_TEXTAREA_FIELDS } = {}) {
      return appSupport.buildTrackerBoardEditingCellMarkupFallbackBridge({
        payload: { entry, fieldName, label, value, saving, errorMessage },
        fallbackHelpers: getFallbackHelpers(),
        runtime: getFallbackRuntime(),
        escapeHtml: fallbackEscapeHtml,
        textareaFields,
      });
    }

    function renderTrackerBoardCell({ entry, column, displayNo }) {
      return appSupport.renderTrackerBoardCellBridge({
        payload: { entry, column, displayNo, trackerBoardEdit: state.trackerBoardEdit },
        TRACKER_BOARD_RUNTIME: runtimeDeps.TRACKER_BOARD_RUNTIME,
        fallbackHelpers: getFallbackHelpers(),
        escapeHtml: runtimeDeps.escapeHtml,
        textareaFields: runtimeDeps.TRACKER_BOARD_TEXTAREA_FIELDS,
        buildTrackerBoardCellMarkupFallback,
      });
    }

    function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {
      return appSupport.renderTrackerBoardEditingCellBridge({
        payload: { entry, fieldName, label, value, saving, errorMessage },
        TRACKER_BOARD_RUNTIME: runtimeDeps.TRACKER_BOARD_RUNTIME,
        fallbackHelpers: getFallbackHelpers(),
        escapeHtml: runtimeDeps.escapeHtml,
        textareaFields: runtimeDeps.TRACKER_BOARD_TEXTAREA_FIELDS,
        buildTrackerBoardEditingCellMarkupFallback,
      });
    }

    return {
      buildTrackerEntryCardMarkupFallback,
      renderTrackerEntries,
      renderTrackerEntriesFallback,
      sortTrackerBoardEntriesFallback,
      buildTrackerBoardMarkupFallback,
      renderTrackerBoard,
      renderTrackerBoardFallback,
      toggleTrackerBoardBlankPriority,
      renderTrackerBoardHeaderCell,
      isTrackerBoardBlankValue,
      sortTrackerBoardEntries,
      buildTrackerBoardCellMarkupFallback,
      buildTrackerBoardEditingCellMarkupFallback,
      renderTrackerBoardCell,
      renderTrackerBoardEditingCell,
    };
  }

  global.SPMSAppRuntimeBodyControllerRuntime = {
    createControllerWithWiringDeps,
    createMethodDelegates,
    createAppRuntimeBodyControllerAccessors,
    createTrackerRenderFallbackAccessors,
  };
})(typeof window !== "undefined" ? window : globalThis);
