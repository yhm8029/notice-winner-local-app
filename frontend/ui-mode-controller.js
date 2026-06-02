(function attachUiModeController(global) {
  const SALES_RECOMMENDATIONS_ADMIN_TAB = "sales-recommendations";

  function createUiModeController(deps = {}) {
    function requireWindow() {
      const currentWindow = deps.window || (typeof window !== "undefined" ? window : null);
      if (!currentWindow) {
        throw new Error("ui mode controller dependency is missing: window");
      }
      return currentWindow;
    }

    function canUseAdminMode() {
      if (typeof deps.canUseAdminMode === "function") {
        return deps.canUseAdminMode();
      }
      return false;
    }

    function canLoadProtectedConsoleData() {
      if (typeof deps.canLoadProtectedConsoleData === "function") {
        return deps.canLoadProtectedConsoleData();
      }
      return false;
    }

    function shouldShowAdminModeToggle() {
      if (typeof deps.shouldShowAdminModeToggle === "function") {
        return deps.shouldShowAdminModeToggle();
      }
      return canUseAdminMode();
    }

    function shouldShowSharedGoogleSheetsShell() {
      if (typeof deps.shouldShowSharedGoogleSheetsShell === "function") {
        return deps.shouldShowSharedGoogleSheetsShell({ canLoadProtectedData: canLoadProtectedConsoleData() });
      }
      return false;
    }

    function isPendingLegacyAdminAlias() {
      if (typeof deps.isPendingLegacyAdminAlias === "function") {
        return deps.isPendingLegacyAdminAlias();
      }
      return false;
    }

    function maybePreloadAdminGoogleSheetsBootstrap() {
      if (typeof deps.maybePreloadAdminGoogleSheetsBootstrap === "function") {
        return deps.maybePreloadAdminGoogleSheetsBootstrap();
      }
      return undefined;
    }

    function normalizeLocationPath(pathname) {
      const raw = String(pathname || "").trim();
      if (!raw) {
        return String(deps.APP_ROOT_PATH || "/");
      }
      const normalized = raw.endsWith("/") && raw !== "/" ? raw.replace(/\/+$/, "") : raw;
      return normalized || String(deps.APP_ROOT_PATH || "/");
    }

    function getAdminRoutePath(tabKey) {
      if (typeof deps.getAdminRoutePath === "function") {
        return deps.getAdminRoutePath(tabKey);
      }
      return String(deps.APP_ROOT_PATH || "/");
    }

    function syncUiModeChrome() {
      if (!canUseAdminMode()) {
        deps.state.uiMode = "user";
      }
      const adminMode = deps.state.uiMode === "admin";
      const currentWindow = requireWindow();
      if (adminMode && deps.state.trackerChangeEventsWarmupHandle) {
        currentWindow.clearTimeout(deps.state.trackerChangeEventsWarmupHandle);
        deps.state.trackerChangeEventsWarmupHandle = null;
      }
      if (deps.dom?.uiModeLabel) {
        deps.dom.uiModeLabel.textContent = adminMode ? "운영자 모드" : "실사용자 모드";
      }
      if (deps.dom?.modeToggleButton) {
        deps.dom.modeToggleButton.textContent = adminMode ? "사용자 모드" : "운영자 모드";
        deps.dom.modeToggleButton.classList.toggle("hidden", !shouldShowAdminModeToggle());
      }
      if (deps.dom?.authSessionModeToggleButton) {
        deps.dom.authSessionModeToggleButton.textContent = adminMode ? "사용자 모드" : "운영자 모드";
        deps.dom.authSessionModeToggleButton.classList.toggle("hidden", !shouldShowAdminModeToggle());
      }
      deps.syncTrackerChangeBellVisibility?.(adminMode);
      if (adminMode) {
        deps.hydrateTrackerChangeEventsCache?.();
        deps.renderTrackerChangeEventUnreadCount?.();
        deps.renderTrackerChangeBellPopover?.();
      }
      const sharedShellVisible = shouldShowSharedGoogleSheetsShell();
      const showingProjectStatus = sharedShellVisible && deps.state.adminTab === deps.DEFAULT_ADMIN_TAB && !isPendingLegacyAdminAlias();
      const showingSalesRecommendations = sharedShellVisible && deps.state.adminTab === SALES_RECOMMENDATIONS_ADMIN_TAB && !isPendingLegacyAdminAlias();
      const showingBuiltinLayout = showingProjectStatus || showingSalesRecommendations;
      deps.dom?.apiMetaCard?.classList.toggle("hidden", !adminMode);
      deps.dom?.syncMetaCard?.classList.toggle("hidden", !adminMode);
      deps.dom?.adminHeaderBar?.classList.toggle("hidden", !sharedShellVisible);
      deps.dom?.adminTopNav?.classList.toggle("hidden", !sharedShellVisible);
      deps.dom?.heroCopy?.classList.toggle("hidden", false);
      deps.dom?.hero?.classList.toggle("hero-admin-nav-active", sharedShellVisible);
      deps.dom?.layoutGrid?.classList.toggle("hidden", sharedShellVisible && !showingBuiltinLayout);
      deps.dom?.panelTracker?.classList.toggle("hidden", sharedShellVisible && !showingProjectStatus);
      deps.dom?.panelSalesRecommendations?.classList.toggle("hidden", !showingSalesRecommendations);

      const showProjectStatusAdminPanels = adminMode && !showingSalesRecommendations;
      const visibleProjectStatusPanels = [
        deps.dom?.panelForm,
      ];
      for (const panel of visibleProjectStatusPanels) {
        panel?.classList.toggle("hidden", !showProjectStatusAdminPanels);
      }

      const hiddenLocalPanels = [
        deps.dom?.panelOrgAdmin,
        deps.dom?.panelDashboard,
        deps.dom?.panelStatus,
        deps.dom?.panelRuns,
        deps.dom?.panelLogs,
        deps.dom?.panelReport,
        deps.dom?.panelArtifacts,
        deps.dom?.projectPanel,
        deps.dom?.panelSalesSummary,
        deps.dom?.trackerChangePanel,
        deps.dom?.backfillConflictPanel,
      ];
      for (const panel of hiddenLocalPanels) {
        panel?.classList.add("hidden");
      }

      deps.dom?.panelEditor?.classList.add("hidden");
      deps.dom?.panelMissingReport?.classList.add("hidden");
      deps.dom?.trackerInlineEditor?.classList.add("hidden");
      deps.dom?.trackerEntriesList?.classList.toggle("hidden", showProjectStatusAdminPanels || showingSalesRecommendations);
      deps.dom?.entriesPrevButton?.closest(".pagination-row")?.classList.toggle("hidden", showProjectStatusAdminPanels || showingSalesRecommendations);
      deps.dom?.trackerBoard?.closest(".tracker-board")?.classList.toggle("hidden", !showProjectStatusAdminPanels);
      deps.dom?.trackerTemplateUploadButton?.classList.toggle("hidden", !showProjectStatusAdminPanels);
      deps.dom?.trackerTemplateResetButton?.classList.toggle("hidden", !showProjectStatusAdminPanels);
      deps.dom?.trackerTemplateStatus?.classList.toggle("hidden", !showProjectStatusAdminPanels);
      deps.dom?.trackerExportButton?.classList.add("hidden");
      deps.dom?.trackerContext?.classList.add("hidden");
      deps.dom?.presetPanel?.classList.add("hidden");
      deps.dom?.runExecutionContext?.classList.add("hidden");
      maybePreloadAdminGoogleSheetsBootstrap();
      deps.renderAdminTopNavigation?.();
      deps.renderAdminEmbedPanel?.();
      deps.renderTrackerTemplateStatus?.();
      const advancedBox = deps.dom?.runForm?.querySelector(".advanced-box");
      advancedBox?.classList.add("hidden");
      return adminMode;
    }

    function applyUiModeTransition(adminMode, { renderAuth = true } = {}) {
      if (!adminMode) {
        deps.state.backfillConflicts = [];
        deps.state.backfillConflictsLoading = false;
        deps.renderBackfillConflictsPanel?.();
        deps.closeDrawer?.();
      } else if (canLoadProtectedConsoleData()) {
        void deps.loadAdminConsoleData?.({ silent: true });
        void deps.loadBackfillConflicts?.({ silent: true });
      }
      if (renderAuth) {
        deps.renderAuthUi?.();
      }
      deps.renderOrganizationAdminPanel?.();
      deps.renderMySalesClaimsPanel?.();
      deps.renderSalesSummaryPanel?.();
      deps.renderRunDetail?.(deps.state.selectedRun);
      deps.renderTrackerEntries?.(deps.state.trackerEntries, { refreshSelectedEntry: adminMode });
      if (canLoadProtectedConsoleData()) {
        if (adminMode) {
          void deps.loadOrganizationUsers?.({ silent: true });
          void deps.loadTrackerEntries?.({ silent: true });
          void deps.loadTrackerChangeEventUnreadCount?.({ silent: true });
          void deps.loadTrackerChangeEvents?.({ silent: true });
        } else {
          deps.clearUserModeRunSelection?.({ sync: true });
          deps.hydrateHomeBootstrapCache?.();
          void deps.loadHomeBootstrap?.({ silent: true });
          deps.scheduleTrackerChangeEventsWarmup?.();
        }
      }
    }

    function applyUiMode({ renderAuth = true } = {}) {
      const currentWindow = requireWindow();
      if (typeof currentWindow !== "undefined" && currentWindow.__SPMS_TEST_MODE__ && currentWindow.__SPMS_TEST_MINIMAL_UI__) {
        if (
          deps.state.uiMode === "user"
          && canLoadProtectedConsoleData()
          && normalizeLocationPath(currentWindow.location?.pathname) === normalizeLocationPath(deps.APP_ROOT_PATH)
          && deps.state.adminTab === deps.DEFAULT_ADMIN_TAB
        ) {
          deps.syncUrlState?.({
            historyMode: "replace",
            pathname: deps.APP_ROOT_PATH || getAdminRoutePath(deps.DEFAULT_ADMIN_TAB),
            uiMode: "user",
            adminTab: deps.DEFAULT_ADMIN_TAB,
          });
        }
        const sharedShellVisible = shouldShowSharedGoogleSheetsShell();
        const showingProjectStatus = sharedShellVisible && deps.state.adminTab === deps.DEFAULT_ADMIN_TAB && !isPendingLegacyAdminAlias();
        const showingSalesRecommendations = sharedShellVisible && deps.state.adminTab === SALES_RECOMMENDATIONS_ADMIN_TAB && !isPendingLegacyAdminAlias();
        const showingBuiltinLayout = showingProjectStatus || showingSalesRecommendations;
        maybePreloadAdminGoogleSheetsBootstrap();
        deps.dom?.layoutGrid?.classList.toggle("hidden", sharedShellVisible && !showingBuiltinLayout);
        deps.dom?.panelTracker?.classList.toggle("hidden", sharedShellVisible && !showingProjectStatus);
        deps.dom?.panelSalesRecommendations?.classList.toggle("hidden", !showingSalesRecommendations);
        deps.renderAdminTopNavigation?.();
        deps.renderAdminEmbedPanel?.();
        return undefined;
      }
      if (!canUseAdminMode()) {
        deps.state.uiMode = "user";
      }
      if (
        deps.state.uiMode === "user"
        && canLoadProtectedConsoleData()
        && normalizeLocationPath(currentWindow.location?.pathname) === normalizeLocationPath(deps.APP_ROOT_PATH)
        && deps.state.adminTab === deps.DEFAULT_ADMIN_TAB
      ) {
        deps.syncUrlState?.({
          historyMode: "replace",
          pathname: deps.APP_ROOT_PATH || getAdminRoutePath(deps.DEFAULT_ADMIN_TAB),
          uiMode: "user",
          adminTab: deps.DEFAULT_ADMIN_TAB,
        });
      }
      const adminMode = syncUiModeChrome();
      return applyUiModeTransition(adminMode, { renderAuth });
    }

    function toggleUiMode() {
      if (!canUseAdminMode()) {
        deps.state.uiMode = "user";
        deps.clearAdminLegacyRouteIntent?.();
        deps.syncUrlState?.({ historyMode: "replace", uiMode: "user" });
        return applyUiMode();
      }
      deps.state.uiMode = deps.state.uiMode === "admin" ? "user" : "admin";
      if (deps.state.uiMode !== "admin") {
        deps.clearAdminLegacyRouteIntent?.();
      }
      deps.syncUrlState?.({ historyMode: "push", uiMode: deps.state.uiMode });
      return applyUiMode();
    }

    function syncUiModeFromLocation() {
      const currentWindow = requireWindow();
      const pathname = currentWindow.location?.pathname || "";
      const search = currentWindow.location?.search || "";
      const effectivePathname = deps.state.canonicalUrlStateHydrated
        ? (deps.state.canonicalLocationPathname || pathname)
        : pathname;
      const effectiveSearch = deps.state.canonicalUrlStateHydrated
        ? (deps.state.canonicalLocationSearch || search)
        : search;
      const params = new URLSearchParams(effectiveSearch);
      const routeTab = deps.getAdminTabByPathname?.(effectivePathname);
      deps.state.uiMode = deps.resolveUiModeFromLocation?.(effectivePathname, effectiveSearch) || "user";
      if (routeTab) {
        deps.state.adminLegacyRoutePath = params.has("admin_tab")
          ? ""
          : (deps.resolveLegacyAdminRoutePath?.(effectivePathname) || "");
        const nextAdminTab = deps.normalizeAdminTab?.(params.get("admin_tab") || routeTab.key || deps.state.adminTab);
        deps.clearAdminGoogleSheetPopupStateForTab?.(nextAdminTab, { render: false });
        deps.state.adminTab = nextAdminTab;
        return undefined;
      }
      deps.clearAdminLegacyRouteIntent?.();
      return undefined;
    }

    return {
      syncUiModeChrome,
      applyUiModeTransition,
      applyUiMode,
      toggleUiMode,
      syncUiModeFromLocation,
    };
  }

  global.SPMSUiModeController = global.SPMSUiModeController || {};
  global.SPMSUiModeController.createUiModeController = createUiModeController;
})(typeof window !== "undefined" ? window : globalThis);
