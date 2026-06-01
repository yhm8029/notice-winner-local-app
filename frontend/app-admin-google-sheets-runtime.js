(function attachAppAdminGoogleSheetsRuntime(global) {
  function createAppAdminGoogleSheetsRuntime(options) {
    const state = options?.state || {};
    const dom = options?.dom || {};
    const windowObject = options?.window || global;
    const requestRenderAdminEmbedPanel = typeof options?.renderAdminEmbedPanel === "function"
      ? options.renderAdminEmbedPanel
      : function noop() {};
    const findResolvedAdminTab = typeof options?.findResolvedAdminTab === "function"
      ? options.findResolvedAdminTab
      : function defaultFindResolvedAdminTab(tab) {
        return tab && typeof tab === "object" ? tab : null;
      };
    const escapeHtml = typeof options?.escapeHtml === "function"
      ? options.escapeHtml
      : function passthrough(value) {
        return String(value ?? "");
      };
    const createStateRuntime = options?.adminGoogleSheetsStateRuntime
      || global.SPMSAppAdminGoogleSheetsStateRuntime?.createAppAdminGoogleSheetsStateRuntime
      || null;

    if (typeof createStateRuntime !== "function") {
      throw new Error("SPMSAppAdminGoogleSheetsStateRuntime is required before app.js loads");
    }

    const stateRuntime = createStateRuntime({
      state,
      dom,
      window: windowObject,
      googleSheetsRuntime: options?.googleSheetsRuntime || global.SPMSAdminGoogleSheetsRuntime || null,
      renderAdminEmbedPanel: requestRenderAdminEmbedPanel,
      findResolvedAdminTab,
    });
    let lastAdminGoogleSheetTableHtml = null;
    let pendingAdminGoogleSheetTableHtml = null;
    let pendingAdminGoogleSheetTableRenderHandle = null;

    function buildAdminGoogleSheetsOverviewMessage(bootstrap = state.adminGoogleSheetsBootstrap || {}) {
      if (state.adminGoogleSheetsBootstrapError) {
        return state.adminGoogleSheetsBootstrapError;
      }
      if (state.adminGoogleSheetsBootstrapLoading && !state.adminGoogleSheetsBootstrap) {
        return "Google Sheets 연동 정보를 불러오는 중입니다.";
      }
      const syncStatus = String(bootstrap?.sync_status || "").trim().toLowerCase();
      const lastError = String(bootstrap?.last_error || "").trim();
      if (syncStatus === "not_configured" || bootstrap?.enabled === false) {
        return "Google Sheets 연동이 아직 설정되지 않았습니다. EC2에 GOOGLE_SHEETS_ADMIN_SPREADSHEET_ID, GOOGLE_SHEETS_ADMIN_CLIENT_ID, GOOGLE_SHEETS_ADMIN_CLIENT_SECRET, GOOGLE_SHEETS_ADMIN_REFRESH_TOKEN 환경 변수를 설정해 주세요.";
      }
      if (syncStatus === "failed") {
        return lastError
          ? `Google Sheets 동기화에 실패했습니다. ${lastError}`
          : "Google Sheets 동기화에 실패했습니다.";
      }
      if (syncStatus === "initializing") {
        return "Google Sheets 동기화를 초기화하는 중입니다. 잠시 후 다시 확인해 주세요.";
      }
      if (lastError) {
        return `Google Sheets 상태를 확인해 주세요. ${lastError}`;
      }
      return "Google Sheets 동기화는 완료됐지만 표시할 시트를 찾지 못했습니다. 스프레드시트에 동기화 가능한 시트가 있는지 확인해 주세요.";
    }

    function hasActiveTextSelection() {
      const getSelection = typeof windowObject?.getSelection === "function" ? windowObject.getSelection : null;
      const selection = getSelection ? getSelection.call(windowObject) : null;
      return Boolean(selection && (!selection.isCollapsed || String(selection.toString?.() || "").trim()));
    }

    function schedulePendingAdminGoogleSheetTableRender() {
      if (pendingAdminGoogleSheetTableRenderHandle) {
        return;
      }
      const setTimeoutFn = typeof windowObject?.setTimeout === "function" ? windowObject.setTimeout.bind(windowObject) : setTimeout;
      pendingAdminGoogleSheetTableRenderHandle = setTimeoutFn(() => {
        pendingAdminGoogleSheetTableRenderHandle = null;
        const nextHtml = pendingAdminGoogleSheetTableHtml;
        pendingAdminGoogleSheetTableHtml = null;
        if (nextHtml !== null) {
          replaceAdminGoogleSheetTableHtmlIfChanged(nextHtml);
        }
      }, 120);
    }

    function replaceAdminGoogleSheetTableHtmlIfChanged(html, { deferOnSelection = true } = {}) {
      const nextHtml = String(html || "");
      if (lastAdminGoogleSheetTableHtml === nextHtml) {
        return;
      }
      if (deferOnSelection && lastAdminGoogleSheetTableHtml !== null && hasActiveTextSelection()) {
        pendingAdminGoogleSheetTableHtml = nextHtml;
        schedulePendingAdminGoogleSheetTableRender();
        return;
      }
      pendingAdminGoogleSheetTableHtml = null;
      dom.adminGoogleSheetTable.innerHTML = nextHtml;
      lastAdminGoogleSheetTableHtml = nextHtml;
    }

    function renderAdminGoogleSheetTable(sheetKey, sheetPayload) {
      const runtime = stateRuntime.requireGoogleSheetsRuntime();
      let appliedState = stateRuntime.getAdminGoogleSheetsFilterState(sheetKey);
      const popupState = stateRuntime.getAdminGoogleSheetPopupState();
      const renderView = function renderView(minTableHeightPx) {
        return runtime.buildAdminGoogleSheetTableView(
          sheetPayload,
          {
            escapeHtml,
            sheetKey,
            sheetState: appliedState,
            popupState,
            minTableHeightPx,
          },
        );
      };
      let view = renderView(stateRuntime.getAdminGoogleSheetMinHeight(sheetKey));
      replaceAdminGoogleSheetTableHtmlIfChanged(view.html);
      if (sheetKey && !stateRuntime.adminGoogleSheetsFilterStateEqual(appliedState, view.sheetState)) {
        stateRuntime.setAdminGoogleSheetsFilterState(sheetKey, view.sheetState, { render: false });
        appliedState = stateRuntime.getAdminGoogleSheetsFilterState(sheetKey);
      }
      const minHeightSync = stateRuntime.syncAdminGoogleSheetMinHeight(sheetKey);
      if (minHeightSync.changed) {
        view = renderView(minHeightSync.value);
        replaceAdminGoogleSheetTableHtmlIfChanged(view.html);
      }
      bindAdminGoogleSheetTableInteractions(sheetKey);
    }

    function bindAdminGoogleSheetTableInteractions(sheetKey) {
      const runtime = stateRuntime.requireGoogleSheetsRuntime();
      if (!dom.adminGoogleSheetTable) {
        return;
      }

      const key = String(sheetKey || "").trim();
      if (key) {
        dom.adminGoogleSheetTable.dataset.adminGoogleSheetActiveSheetKey = key;
      }

      if (dom.adminGoogleSheetTable.dataset.adminGoogleSheetInteractionsBound === "1") {
        return;
      }

      dom.adminGoogleSheetTable.dataset.adminGoogleSheetInteractionsBound = "1";

      const resolveActiveSheetKey = function resolveActiveSheetKey() {
        return stateRuntime.getAdminGoogleSheetTableInteractionSheetKey();
      };
      const resolvePopupModel = function resolvePopupModel(activeSheetKey) {
        const resolvedKey = String(activeSheetKey || "").trim();
        if (!resolvedKey || !runtime?.buildAdminGoogleSheetFilterModel) {
          return null;
        }
        const payload = state.adminGoogleSheetPayloadByKey?.[resolvedKey];
        if (!payload) {
          return null;
        }
        return runtime.buildAdminGoogleSheetFilterModel(
          payload,
          stateRuntime.getAdminGoogleSheetsFilterState(resolvedKey),
        );
      };

      dom.adminGoogleSheetTable.addEventListener("click", function handleClick(event) {
        const trigger = event.target?.closest?.("[data-admin-google-sheet-trigger-index]");
        if (trigger) {
          const columnIndex = Number(trigger.getAttribute("data-admin-google-sheet-trigger-index"));
          stateRuntime.openAdminGoogleSheetFilterPopup(resolveActiveSheetKey(), columnIndex);
          return;
        }

        const sortButton = event.target?.closest?.("[data-admin-google-sheet-popup-sort]");
        if (sortButton) {
          stateRuntime.setAdminGoogleSheetPopupSort(sortButton.getAttribute("data-admin-google-sheet-popup-sort"));
          return;
        }

        const actionButton = event.target?.closest?.("[data-admin-google-sheet-popup-action]");
        if (actionButton) {
          const action = String(actionButton.getAttribute("data-admin-google-sheet-popup-action") || "").trim();
          if (action === "confirm") {
            stateRuntime.confirmAdminGoogleSheetPopup();
          } else if (action === "cancel") {
            stateRuntime.cancelAdminGoogleSheetPopup();
          }
        }
      });

      dom.adminGoogleSheetTable.addEventListener("input", function handleInput(event) {
        const searchInput = event.target?.closest?.("[data-admin-google-sheet-popup-search=\"1\"]");
        if (!searchInput) {
          return;
        }
        stateRuntime.setAdminGoogleSheetPopupSearch(searchInput.value);
      });

      dom.adminGoogleSheetTable.addEventListener("change", function handleChange(event) {
        const valueCheckbox = event.target?.closest?.("[data-admin-google-sheet-popup-value]");
        if (valueCheckbox) {
          stateRuntime.toggleAdminGoogleSheetPopupValue(valueCheckbox.getAttribute("data-admin-google-sheet-popup-value"), valueCheckbox.checked);
          return;
        }

        const selectAllCheckbox = event.target?.closest?.("[data-admin-google-sheet-popup-select-all=\"1\"]");
        if (!selectAllCheckbox) {
          return;
        }

        const activeSheetKey = resolveActiveSheetKey();
        const popupState = stateRuntime.getAdminGoogleSheetPopupState();
        const model = resolvePopupModel(activeSheetKey);
        const popupModel = model
          ? runtime?.buildAdminGoogleSheetPopupModel?.(model, popupState) || null
          : null;
        if (!popupState.open || !popupModel) {
          return;
        }

        const visibleValues = Array.isArray(popupModel.visibleValueKeys)
          ? popupModel.visibleValueKeys
          : (Array.isArray(popupModel.visibleValues) ? popupModel.visibleValues : []);
        const nextSelectedValues = new Set(popupState.pendingSelectedValues);
        if (selectAllCheckbox.checked) {
          visibleValues.forEach((value) => nextSelectedValues.add(value));
        } else {
          visibleValues.forEach((value) => nextSelectedValues.delete(value));
        }

        stateRuntime.setAdminGoogleSheetPopupState({
          ...popupState,
          pendingSelectedValues: Array.from(nextSelectedValues),
        });
      });

      dom.adminGoogleSheetTable.dataset.adminGoogleSheetDismissalBound = "1";
    }

    function renderAdminEmbedPanel(deps = {}) {
      if (
        !dom.adminEmbedPanel
        || !dom.adminEmbedTitle
        || !dom.adminEmbedSubtitle
        || !dom.adminGoogleSheetsSyncFeedback
        || !dom.adminGoogleSheetStatus
        || !dom.adminGoogleSheetTable
        || !dom.adminEmbedEmpty
      ) {
        return;
      }
      const runtime = options?.googleSheetsRuntime || global.SPMSAdminGoogleSheetsRuntime || null;

      const getActiveAdminTab = typeof deps.getActiveAdminTab === "function"
        ? deps.getActiveAdminTab
        : (typeof options?.getActiveAdminTab === "function" ? options.getActiveAdminTab : function fallbackActiveTab() {
          return null;
        });
      const getValidatedActiveAdminGoogleSheetTab = typeof deps.getValidatedActiveAdminGoogleSheetTab === "function"
        ? deps.getValidatedActiveAdminGoogleSheetTab
        : (typeof options?.getValidatedActiveAdminGoogleSheetTab === "function" ? options.getValidatedActiveAdminGoogleSheetTab : function fallbackValidatedTab() {
          return null;
        });
      const canLoadProtectedConsoleData = typeof deps.canLoadProtectedConsoleData === "function"
        ? deps.canLoadProtectedConsoleData
        : (typeof options?.canLoadProtectedConsoleData === "function" ? options.canLoadProtectedConsoleData : function fallbackCanLoadProtectedConsoleData() {
          return false;
        });
      const shouldShowSharedGoogleSheetsShell = typeof deps.shouldShowSharedGoogleSheetsShell === "function"
        ? deps.shouldShowSharedGoogleSheetsShell
        : (typeof options?.shouldShowSharedGoogleSheetsShell === "function" ? options.shouldShowSharedGoogleSheetsShell : function fallbackShouldShowSharedGoogleSheetsShell() {
          return false;
        });
      const shouldShowAdminGoogleSheetsOverviewPanel = typeof deps.shouldShowAdminGoogleSheetsOverviewPanel === "function"
        ? deps.shouldShowAdminGoogleSheetsOverviewPanel
        : (typeof options?.shouldShowAdminGoogleSheetsOverviewPanel === "function" ? options.shouldShowAdminGoogleSheetsOverviewPanel : function fallbackShouldShowAdminGoogleSheetsOverviewPanel() {
          return false;
        });
      const shouldShowAdminGoogleSheetsControls = typeof deps.shouldShowAdminGoogleSheetsControls === "function"
        ? deps.shouldShowAdminGoogleSheetsControls
        : (typeof options?.shouldShowAdminGoogleSheetsControls === "function" ? options.shouldShowAdminGoogleSheetsControls : function fallbackShouldShowAdminGoogleSheetsControls() {
          return false;
        });
      const loadAdminGoogleSheetsBootstrap = typeof deps.loadAdminGoogleSheetsBootstrap === "function"
        ? deps.loadAdminGoogleSheetsBootstrap
        : (typeof options?.loadAdminGoogleSheetsBootstrap === "function" ? options.loadAdminGoogleSheetsBootstrap : function noop() {});
      const loadAdminGoogleSheetPayload = typeof deps.loadAdminGoogleSheetPayload === "function"
        ? deps.loadAdminGoogleSheetPayload
        : (typeof options?.loadAdminGoogleSheetPayload === "function" ? options.loadAdminGoogleSheetPayload : function noop() {});

      const adminMode = state.uiMode === "admin";
      const activeTab = getActiveAdminTab();
      const validatedSheetTab = getValidatedActiveAdminGoogleSheetTab();
      const canLoadProtectedData = canLoadProtectedConsoleData();
      const sharedShellVisible = shouldShowSharedGoogleSheetsShell({ canLoadProtectedData });
      const showGoogleSheetsOverview = adminMode && shouldShowAdminGoogleSheetsOverviewPanel({ canLoadProtectedData });
      const pendingGoogleSheetsOverview = sharedShellVisible
        && !validatedSheetTab
        && !showGoogleSheetsOverview
        && adminMode
        && (!state.adminGoogleSheetsBootstrap || state.adminGoogleSheetsBootstrapLoading);
      const sheetTabActive = sharedShellVisible && (activeTab?.type === "google_sheet" || activeTab?.type === "google_sheet_pending");
      const panelVisible = sheetTabActive || showGoogleSheetsOverview || pendingGoogleSheetsOverview;
      const bootstrap = state.adminGoogleSheetsBootstrapError && !state.adminGoogleSheetsBootstrapLoading
        ? {
          ...(state.adminGoogleSheetsBootstrap || {}),
          sync_status: "failed",
        }
        : (state.adminGoogleSheetsBootstrap || {});
      const showAdminControls = shouldShowAdminGoogleSheetsControls({ panelVisible });
      const panelTitle = showGoogleSheetsOverview ? "Google Sheets 연동 상태" : String(activeTab?.label || "");
      const panelSubtitle = showGoogleSheetsOverview
        ? (adminMode ? "현재 관리자용 Google Sheets 연동 상태" : "")
        : (adminMode ? String(activeTab?.subtitle || "") : "");

      dom.adminEmbedTitle.textContent = panelTitle;
      dom.adminEmbedSubtitle.textContent = panelSubtitle;
      dom.adminEmbedPanel.classList.toggle("hidden", !panelVisible);

      const hasSyncFeedback = Boolean(state.adminGoogleSheetsSyncMessage);
      dom.adminGoogleSheetsSyncFeedback.classList.toggle("hidden", !showAdminControls || !hasSyncFeedback);
      dom.adminGoogleSheetsSyncFeedback.textContent = showAdminControls && hasSyncFeedback ? state.adminGoogleSheetsSyncMessage : "";

      if (canLoadProtectedData && sharedShellVisible && !state.adminGoogleSheetsBootstrap && !state.adminGoogleSheetsBootstrapLoading && !state.adminGoogleSheetsBootstrapError) {
        void loadAdminGoogleSheetsBootstrap({ silent: true });
      }

      if (dom.adminGoogleSheetsSyncButton) {
        const shouldShowSyncButton = showAdminControls;
        dom.adminGoogleSheetsSyncButton.classList.toggle("hidden", !shouldShowSyncButton);
        const syncBusy = state.adminGoogleSheetsSyncing || state.adminGoogleSheetsBootstrapLoading;
        const shouldDisableSync = !shouldShowSyncButton || !canLoadProtectedData || syncBusy;
        if (shouldDisableSync) {
          dom.adminGoogleSheetsSyncButton.setAttribute("disabled", "disabled");
        } else {
          dom.adminGoogleSheetsSyncButton.removeAttribute("disabled");
        }
        dom.adminGoogleSheetsSyncButton.textContent = syncBusy ? "Google Sheets 동기화 중..." : "Google Sheets 동기화";
      }

      if (!panelVisible) {
        dom.adminGoogleSheetStatus.classList.add("hidden");
        dom.adminGoogleSheetStatus.innerHTML = "";
        dom.adminGoogleSheetTable.classList.add("hidden");
        replaceAdminGoogleSheetTableHtmlIfChanged("", { deferOnSelection: false });
        dom.adminEmbedEmpty.classList.add("hidden");
        dom.adminEmbedEmpty.textContent = "";
        return;
      }

      if (!runtime) {
        dom.adminGoogleSheetStatus.classList.add("hidden");
        dom.adminGoogleSheetStatus.innerHTML = "";
        dom.adminGoogleSheetTable.classList.add("hidden");
        replaceAdminGoogleSheetTableHtmlIfChanged("", { deferOnSelection: false });
        dom.adminEmbedEmpty.classList.remove("hidden");
        dom.adminEmbedEmpty.textContent = "Admin Google Sheets runtime is not available.";
        return;
      }

      if (canLoadProtectedData && validatedSheetTab) {
        if (
          !state.adminGoogleSheetPayloadByKey[validatedSheetTab.key]
          && !state.adminGoogleSheetPayloadLoadingByKey[validatedSheetTab.key]
          && !state.adminGoogleSheetPayloadErrorByKey[validatedSheetTab.key]
        ) {
          void loadAdminGoogleSheetPayload(validatedSheetTab.key, { silent: true });
        }
      }

      const activeSheetKey = validatedSheetTab?.key || "";
      const sheetPayload = state.adminGoogleSheetPayloadByKey[activeSheetKey] || {};
      const sheetError = String(state.adminGoogleSheetPayloadErrorByKey[activeSheetKey] || "").trim();

      if (showGoogleSheetsOverview || adminMode) {
        dom.adminGoogleSheetStatus.classList.remove("hidden");
        dom.adminGoogleSheetStatus.innerHTML = runtime.buildAdminGoogleSheetStatusView(
          bootstrap,
          showGoogleSheetsOverview ? { label: panelTitle } : activeTab,
        ).html || "";
      } else {
        dom.adminGoogleSheetStatus.classList.add("hidden");
        dom.adminGoogleSheetStatus.innerHTML = "";
      }

      if (showGoogleSheetsOverview || pendingGoogleSheetsOverview) {
        dom.adminGoogleSheetTable.classList.add("hidden");
        replaceAdminGoogleSheetTableHtmlIfChanged("", { deferOnSelection: false });
        dom.adminEmbedEmpty.classList.remove("hidden");
        dom.adminEmbedEmpty.textContent = buildAdminGoogleSheetsOverviewMessage(bootstrap);
        return;
      }

      dom.adminGoogleSheetTable.classList.remove("hidden");
      renderAdminGoogleSheetTable(activeSheetKey, sheetPayload);

      if (sheetError) {
        dom.adminEmbedEmpty.classList.remove("hidden");
        dom.adminEmbedEmpty.textContent = sheetError;
        return;
      }
      if (state.adminGoogleSheetsBootstrapError) {
        dom.adminEmbedEmpty.classList.remove("hidden");
        dom.adminEmbedEmpty.textContent = state.adminGoogleSheetsBootstrapError;
        return;
      }
      dom.adminEmbedEmpty.classList.add("hidden");
      dom.adminEmbedEmpty.textContent = "";
    }

    return {
      ...stateRuntime,
      renderAdminEmbedPanel,
      bindAdminGoogleSheetTableInteractions,
      renderAdminGoogleSheetTable,
    };
  }

  global.SPMSAppAdminGoogleSheetsRuntime = {
    createAppAdminGoogleSheetsRuntime,
  };
})(typeof window !== "undefined" ? window : globalThis);

