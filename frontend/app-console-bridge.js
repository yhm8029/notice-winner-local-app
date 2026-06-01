export function createAppConsoleBridge(context = {}) {
  const {
    callConsolePanelsController = null,
  } = context;

  function requireConsolePanelsControllerCall() {
    if (typeof callConsolePanelsController !== "function") {
      throw new Error("callConsolePanelsController is required before app.js loads");
    }
    return callConsolePanelsController;
  }

  async function loadDashboardSummary({ silent = false } = {}) {
    return requireConsolePanelsControllerCall()("loadDashboardSummary", { silent });
  }

  function renderDashboard(summary, errorMessage = "") {
    return requireConsolePanelsControllerCall()("renderDashboard", summary, errorMessage);
  }

  function renderRunExecutionContext(run) {
    return requireConsolePanelsControllerCall()("renderRunExecutionContext", run);
  }

  async function loadProjects({ silent = false } = {}) {
    return requireConsolePanelsControllerCall()("loadProjects", { silent });
  }

  function renderProjects(errorMessage = "") {
    return requireConsolePanelsControllerCall()("renderProjects", errorMessage);
  }

  function changeProjectsPage(delta) {
    return requireConsolePanelsControllerCall()("changeProjectsPage", delta);
  }

  function handleOutOfRangePageError(error, filterState, scopeLabel) {
    return requireConsolePanelsControllerCall()("handleOutOfRangePageError", error, filterState, scopeLabel);
  }

  return {
    loadDashboardSummary,
    renderDashboard,
    renderRunExecutionContext,
    loadProjects,
    renderProjects,
    changeProjectsPage,
    handleOutOfRangePageError,
  };
}

const appConsoleBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appConsoleBridgeRoot.APP_CONSOLE_BRIDGE = appConsoleBridgeRoot.APP_CONSOLE_BRIDGE || {};
appConsoleBridgeRoot.APP_CONSOLE_BRIDGE.createAppConsoleBridge = createAppConsoleBridge;
