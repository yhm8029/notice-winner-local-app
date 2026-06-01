(function attachAppEntryRuntime(global) {
  const CONTROLLER_INITIALIZERS = [
    ["authUiController", "AUTH_UI_CONTROLLER", "createAuthUiController", "createAuthUiControllerDeps"],
    ["projectRelatedController", "PROJECT_RELATED_CONTROLLER", "createProjectRelatedController", "createProjectRelatedControllerDeps"],
    ["trackerController", "TRACKER_CONTROLLER", "createTrackerController", "createTrackerControllerDeps"],
    ["authController", "AUTH_CONTROLLER", "createAuthController", "createAuthControllerDeps"],
    ["orgAdminController", "ORG_ADMIN_CONTROLLER", "createOrgAdminController", "createOrgAdminControllerDeps"],
    ["runtimeEnhancements", "RUNTIME_ENHANCEMENTS", "createRuntimeEnhancements", "createRuntimeEnhancementsDeps"],
    ["reportPanelsController", "REPORT_PANELS_CONTROLLER", "createReportPanelsController", "createReportPanelsControllerDeps"],
    ["runPanelsController", "RUN_PANELS_CONTROLLER", "createRunPanelsController", "createRunPanelsControllerDeps"],
    ["trackerEntryActionsController", "TRACKER_ENTRY_ACTIONS_CONTROLLER", "createTrackerEntryActionsController", "createTrackerEntryActionsControllerDeps"],
    ["trackerRenderController", "TRACKER_RENDER_CONTROLLER", "createTrackerRenderController", "createTrackerRenderControllerDeps"],
    ["consolePanelsController", "CONSOLE_PANELS_CONTROLLER", "createConsolePanelsController", "createConsolePanelsControllerDeps"],
    ["downloadController", "DOWNLOAD_CONTROLLER", "createDownloadController", "createDownloadControllerDeps"],
    ["trackerDiagnosticsPanelController", "TRACKER_DIAGNOSTICS_PANEL_CONTROLLER", "createTrackerDiagnosticsPanelController", "createTrackerDiagnosticsPanelControllerDeps"],
    ["salesPanelController", "SALES_PANEL_CONTROLLER", "createSalesPanelController", "createSalesPanelControllerDeps"],
    ["appEventBindings", "APP_EVENT_BINDINGS", "createAppEventBindings", "createAppEventBindingsDeps"],
    ["selectedEntryController", "SELECTED_ENTRY_CONTROLLER", "createSelectedEntryController", "createSelectedEntryControllerDeps"],
  ];

  function createAppControllerState() {
    return {
      authUiController: null,
      projectRelatedController: null,
      trackerController: null,
      authController: null,
      orgAdminController: null,
      runtimeEnhancements: null,
      reportPanelsController: null,
      runPanelsController: null,
      trackerEntryActionsController: null,
      trackerRenderController: null,
      consolePanelsController: null,
      downloadController: null,
      trackerDiagnosticsPanelController: null,
      salesPanelController: null,
      appEventBindings: null,
      selectedEntryController: null,
    };
  }

  function createAppEntryRuntime(options = {}) {
    const createAppViewBindings = options.createAppViewBindings;
    if (typeof createAppViewBindings !== "function") {
      throw new Error("SPMSAppViewBindingsRuntime.createAppViewBindings is required before app.js loads");
    }

    const createAppControllerBootstrapRuntime = options.createAppControllerBootstrapRuntime;
    if (typeof createAppControllerBootstrapRuntime !== "function") {
      throw new Error("SPMSAppControllerBootstrapRuntime.createAppControllerBootstrapRuntime is required before app.js loads");
    }

    const controllerState = options.controllerState && typeof options.controllerState === "object"
      ? options.controllerState
      : createAppControllerState();
    const appStartupRuntime = options.appStartupRuntime && typeof options.appStartupRuntime === "object"
      ? options.appStartupRuntime
      : null;
    if (appStartupRuntime === null) {
      throw new Error("appStartupRuntime is required before app.js loads");
    }

    const boot = options.boot;
    if (typeof boot !== "function") {
      throw new Error("boot is required before app.js loads");
    }

    const createWinnerRun = options.createWinnerRun;
    if (typeof createWinnerRun !== "function") {
      throw new Error("createWinnerRun is required before app.js loads");
    }

    const dom = options.dom && typeof options.dom === "object" ? options.dom : null;
    if (dom === null) {
      throw new Error("dom is required before app.js loads");
    }

    const appViewBindings = createAppViewBindings(options.viewBindings || {});
    const {
      waitForAppControllerDepsReady,
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
    } = createAppControllerBootstrapRuntime({
      APP_CONTROLLER_CONTEXT_RUNTIME: options.APP_CONTROLLER_CONTEXT_RUNTIME,
      APP_CONTROLLER_DEPS: options.APP_CONTROLLER_DEPS,
      root: options.root,
      locals: options.locals,
      coreRuntime: options.coreRuntime,
      shellRuntime: options.shellRuntime,
      runtimes: options.runtimes,
      bridges: options.bridges,
      helperSources: [
        appStartupRuntime,
        appViewBindings,
      ],
      helpers: {
        ...options.helpers,
        renderReportPanels() {
          return appStartupRuntime.refreshReportPanels();
        },
        renderSalesNoteTimelineMarkup(noteEntries) {
          return appViewBindings.buildSalesNoteTimelineMarkup(noteEntries);
        },
        buildSalesClaimEstimateLabelMarkup(claim) {
          return appViewBindings.buildSalesClaimEstimateLabel(claim);
        },
        async handleRunCreate(event) {
          event.preventDefault();
          await createWinnerRun({
            submitButton: dom.submitRunButton,
            busyLabel: "\uc2e4\ud589 \uc2dc\uc791 \uc911...",
          });
        },
      },
      dynamic: options.dynamic,
    });

    const controllerDeps = {
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
    };

    function initializeControllers() {
      const controllerFactories = options.controllerFactories && typeof options.controllerFactories === "object"
        ? options.controllerFactories
        : {};

      for (const [stateKey, controllerKey, createKey, depsKey] of CONTROLLER_INITIALIZERS) {
        const controllerFactory = controllerFactories[controllerKey];
        const createDeps = controllerDeps[depsKey];
        controllerState[stateKey] = controllerFactory?.[createKey]?.(createDeps()) || null;
      }
    }

    async function startApp() {
      await waitForAppControllerDepsReady();
      initializeControllers();
      await boot();
    }

    function launchApp() {
      void startApp();
    }

    return {
      appViewBindings,
      controllerState,
      initializeControllers,
      startApp,
      launchApp,
      waitForAppControllerDepsReady,
    };
  }

  global.SPMSAppEntryRuntime = {
    createAppControllerState,
    createAppEntryRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);
