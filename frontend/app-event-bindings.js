export function createAppEventBindings(deps = {}) {
  const {
    dom,
    state,
    AUTH_MODE_SIGN_IN,
    AUTH_MODE_SIGN_UP,
    TRACKER_REGION_OPTIONS,
    handleAuthSubmit,
    setAuthMode,
    setAdminTab,
    handleAuthFindId,
    handleAuthPasswordReset,
    scheduleInvitationPreviewLookup,
    renderAuthUi,
    handleAuthSignOut,
    openProfileDialog,
    handleProfileSubmit,
    handleInvitationSubmit,
    loadOrganizationAdminData,
    closeProfileDialog,
    setTrackerChangeBellPopoverOpen,
    downloadSalesWorkbook,
    closeSalesCloseDialog,
    formatContractAmountInput,
    confirmSalesCloseDialog,
    refreshAuthSessionState,
    loadDashboardSummary,
    handleRunCreate,
    handleRunFormReset,
    refreshSelectedRun,
    loadRuns,
    loadSelectedRunLogs,
    runSelectedReport,
    refreshReportPanels,
    loadSelectedRunArtifacts,
    cancelSelectedRun,
    createTrackerExportForSelectedRun,
    toggleUiMode,
    renderSyncMeta,
    syncUrlState,
    loadReportJobs,
    loadPhaseReport,
    readRunFiltersFromControls,
    readTrackerFiltersFromControls,
    syncFilterControlsFromState,
    changeRunsPage,
    loadTrackerEntries,
    trackerChangeEventsCacheIsFresh,
    renderTrackerChangeBellPopover,
    loadTrackerChangeEvents,
    focusTrackerChangePanel,
    uploadTrackerTemplate,
    resetTrackerTemplateOverride,
    changeEntriesPageTo,
    changeEntriesPage,
    getEntriesTotalPages,
    normalizeTrackerRegionFilter,
    parseTrackerRegionFilter,
    saveEntryPatch,
    clearEntryPatch,
    loadSelectedEntryAudit,
    loadTrackerMissingReport,
    refreshSalesAdminPanels,
    getMissingReportDownloadLimit,
    syncPatchValueFromSelectedEntry,
    closeDrawer,
    loadRunPresets,
    applySelectedPreset,
    saveCurrentFormAsPreset,
    renderRunPresetPanel,
    loadProjects,
    changeProjectsPage,
    triggerTrackerEntriesXlsxDownload,
  } = deps;
  const window = deps.window || globalThis.window || globalThis;
  const document = deps.document || globalThis.document || null;

  function bindEvents() {
    dom.authForm.addEventListener("submit", handleAuthSubmit);
    dom.authModeSignIn.addEventListener("click", () => setAuthMode(AUTH_MODE_SIGN_IN));
    dom.authModeSignUp.addEventListener("click", () => setAuthMode(AUTH_MODE_SIGN_UP));
    dom.authFindIdButton?.addEventListener("click", handleAuthFindId);
    dom.authResetPasswordButton?.addEventListener("click", () => {
      void handleAuthPasswordReset();
    });
    dom.adminTopNavList?.addEventListener("click", (event) => {
      const target = event?.target || null;
      const tabLink = target && typeof target.closest === "function"
        ? target.closest("[data-admin-tab]")
        : null;
      if (!tabLink) {
        return;
      }
      const nextTab = String(tabLink.getAttribute("data-admin-tab") || "").trim();
      if (!nextTab) {
        return;
      }
      event.preventDefault();
      setAdminTab(nextTab, { historyMode: "push" });
    });
    dom.authEmail?.addEventListener("input", () => {
      scheduleInvitationPreviewLookup(String(dom.authEmail?.value || "").trim());
      if (!state.auth.invitationPreview) {
        renderAuthUi();
      }
    });
    dom.logoutButton.addEventListener("click", handleAuthSignOut);
    dom.authProfileButton?.addEventListener("click", openProfileDialog);
    dom.authSessionProfileButton?.addEventListener("click", openProfileDialog);
    dom.authSessionLogoutButton?.addEventListener("click", handleAuthSignOut);
    dom.authBlockedLogout.addEventListener("click", handleAuthSignOut);
    dom.profileForm?.addEventListener("submit", handleProfileSubmit);
    dom.invitationForm?.addEventListener("submit", handleInvitationSubmit);
    dom.orgAdminRefreshButton?.addEventListener("click", () => {
      void loadOrganizationAdminData({});
    });
    dom.profileCloseButtons?.forEach((button) => {
      button.addEventListener("click", closeProfileDialog);
    });
    dom.profileDialog?.addEventListener("click", (event) => {
      if (event.target instanceof Element && event.target.matches("[data-profile-close]")) {
        closeProfileDialog();
      }
    });
    document.addEventListener("click", (event) => {
      if (
        state.trackerChangeBellPopoverOpen
        && event.target instanceof Element
        && dom.trackerChangeBellShell
        && !dom.trackerChangeBellShell.contains(event.target)
      ) {
        setTrackerChangeBellPopoverOpen(false);
      }
    });
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && state.profileDialog.open) {
        closeProfileDialog();
        return;
      }
      if (event.key === "Escape" && state.trackerChangeBellPopoverOpen) {
        setTrackerChangeBellPopoverOpen(false);
      }
    });
    dom.trackerUserSalesDownloadButton?.addEventListener("click", () => {
      void downloadSalesWorkbook("my", dom.trackerUserSalesDownloadButton);
    });
    dom.trackerCompanySalesDownloadButton?.addEventListener("click", () => {
      void downloadSalesWorkbook("company", dom.trackerCompanySalesDownloadButton);
    });
    dom.salesCloseDialog?.addEventListener("click", (event) => {
      if (event.target instanceof Element && event.target.closest("[data-sales-close-cancel]")) {
        closeSalesCloseDialog();
      }
    });
    dom.salesCloseAmountInput?.addEventListener("input", () => {
      dom.salesCloseAmountInput.value = formatContractAmountInput(dom.salesCloseAmountInput.value || "");
    });
    dom.salesCloseAmountInput?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        void confirmSalesCloseDialog();
      }
    });
    dom.salesCloseConfirmButton?.addEventListener("click", () => {
      void confirmSalesCloseDialog();
    });
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        void refreshAuthSessionState({ silent: true });
      }
    });
    window.addEventListener("focus", () => {
      void refreshAuthSessionState({ silent: true });
    });
    dom.refreshDashboardButton.addEventListener("click", () => loadDashboardSummary({}));
    dom.runForm.addEventListener("submit", handleRunCreate);
    dom.formResetButton.addEventListener("click", handleRunFormReset);
    dom.refreshRunButton.addEventListener("click", refreshSelectedRun);
    dom.refreshRunsButton.addEventListener("click", () => loadRuns({}));
    dom.refreshLogsButton.addEventListener("click", loadSelectedRunLogs);
    dom.runReportButton.addEventListener("click", runSelectedReport);
    dom.refreshReportButton.addEventListener("click", refreshReportPanels);
    dom.refreshArtifactsButton.addEventListener("click", loadSelectedRunArtifacts);
    dom.cancelRunButton.addEventListener("click", cancelSelectedRun);
    dom.trackerExportButton.addEventListener("click", createTrackerExportForSelectedRun);
    dom.modeToggleButton.addEventListener("click", toggleUiMode);
    dom.authSessionModeToggleButton?.addEventListener("click", toggleUiMode);
    dom.autoRefreshToggle.addEventListener("change", () => {
      state.autoRefresh = dom.autoRefreshToggle.checked;
      renderSyncMeta();
      syncUrlState();
    });
    dom.reportSelect.addEventListener("change", () => {
      state.reportKey = dom.reportSelect.value || "phase1-artifact-diff";
      syncUrlState();
      loadReportJobs({ silent: true });
      loadPhaseReport({});
    });

    dom.runFilterForm.addEventListener("submit", (event) => {
      event.preventDefault();
      readRunFiltersFromControls();
      state.runFilters.page = 1;
      syncUrlState();
      loadRuns({});
    });
    dom.runFilterReset.addEventListener("click", () => {
      state.runFilters = { status: "", runType: "", from: "", to: "", page: 1, pageSize: 20 };
      syncFilterControlsFromState();
      syncUrlState();
      loadRuns({});
    });
    dom.runPageSize.addEventListener("change", () => {
      readRunFiltersFromControls();
      state.runFilters.page = 1;
      syncUrlState();
      loadRuns({});
    });
    dom.runsPrevButton.addEventListener("click", () => changeRunsPage(-1));
    dom.runsNextButton.addEventListener("click", () => changeRunsPage(1));

    dom.trackerFilterForm.addEventListener("submit", (event) => {
      event.preventDefault();
      readTrackerFiltersFromControls();
      state.trackerFilters.page = 1;
      syncUrlState();
      loadTrackerEntries();
    });
    dom.trackerPageSize.addEventListener("change", () => {
      readTrackerFiltersFromControls();
      state.trackerFilters.page = 1;
      syncUrlState();
      loadTrackerEntries();
    });
    if (dom.trackerEntriesDownloadButton) {
      dom.trackerEntriesDownloadButton.addEventListener("click", () => {
        void triggerTrackerEntriesXlsxDownload(dom.trackerEntriesDownloadButton);
      });
    }
    if (dom.trackerChangeBell) {
      dom.trackerChangeBell.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();
        const shouldOpen = !state.trackerChangeBellPopoverOpen;
        setTrackerChangeBellPopoverOpen(shouldOpen);
        if (!shouldOpen) {
          return;
        }
        const shouldRefresh = !state.trackerChangeEvents.length || !trackerChangeEventsCacheIsFresh();
        if (!state.trackerChangeEvents.length) {
          state.trackerChangeEventsLoading = true;
          renderTrackerChangeBellPopover();
        }
        if (shouldRefresh) {
          void loadTrackerChangeEvents({ silent: true });
        }
      });
    }
    dom.trackerChangeBellPopover?.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target : null;
      if (!target) {
        return;
      }
      if (target.closest("[data-tracker-change-open-panel='true']")) {
        setTrackerChangeBellPopoverOpen(false);
        focusTrackerChangePanel();
        return;
      }
      if (target.closest("[data-change-entry-id]")) {
        setTrackerChangeBellPopoverOpen(false);
      }
    });
    if (dom.trackerTemplateUploadButton && dom.trackerTemplateFileInput) {
      dom.trackerTemplateUploadButton.addEventListener("click", () => {
        dom.trackerTemplateFileInput.value = "";
        dom.trackerTemplateFileInput.click();
      });
      dom.trackerTemplateFileInput.addEventListener("change", async () => {
        const [file] = Array.from(dom.trackerTemplateFileInput.files || []);
        if (!file) {
          return;
        }
        await uploadTrackerTemplate(file);
        dom.trackerTemplateFileInput.value = "";
      });
    }
    if (dom.trackerTemplateResetButton) {
      dom.trackerTemplateResetButton.addEventListener("click", resetTrackerTemplateOverride);
    }
    dom.entriesFirstButton.addEventListener("click", () => changeEntriesPageTo(1));
    dom.entriesPrevButton.addEventListener("click", () => changeEntriesPage(-1));
    dom.entriesNextButton.addEventListener("click", () => changeEntriesPage(1));
    dom.entriesLastButton.addEventListener("click", () => changeEntriesPageTo(getEntriesTotalPages()));
    if (dom.trackerRegionButtons) {
      dom.trackerRegionButtons.addEventListener("click", (event) => {
        const button = event.target.closest("[data-tracker-region]");
        if (!button) {
          return;
        }
        const nextRegion = normalizeTrackerRegionFilter(button.getAttribute("data-tracker-region") || "");
        if (!nextRegion) {
          if (!state.trackerFilters.region) {
            return;
          }
          state.trackerFilters.region = "";
        } else {
          const activeRegions = new Set(parseTrackerRegionFilter(state.trackerFilters.region));
          if (activeRegions.has(nextRegion)) {
            activeRegions.delete(nextRegion);
          } else {
            activeRegions.add(nextRegion);
          }
          state.trackerFilters.region = TRACKER_REGION_OPTIONS
            .map((option) => String(option.value || "").trim())
            .filter((value) => value && activeRegions.has(value))
            .join(",");
        }
        state.trackerFilters.page = 1;
        syncFilterControlsFromState();
        syncUrlState();
        loadTrackerEntries();
      });
    }

    dom.patchForm.addEventListener("submit", saveEntryPatch);
    dom.clearEntryButton.addEventListener("click", clearEntryPatch);
    dom.refreshAuditButton.addEventListener("click", loadSelectedEntryAudit);
    if (dom.missingReportRefreshButton) {
      dom.missingReportRefreshButton.addEventListener("click", () => loadTrackerMissingReport({}));
    }
    if (dom.salesSummaryRefreshButton) {
      dom.salesSummaryRefreshButton.addEventListener("click", () => refreshSalesAdminPanels({}));
    }
    if (dom.missingReportCsvButton) {
      dom.missingReportCsvButton.addEventListener("click", () => {
        window.location.href = `/api/tracker-entries/missing-report/download?format=csv&limit=${getMissingReportDownloadLimit()}`;
      });
    }
    if (dom.missingReportXlsxButton) {
      dom.missingReportXlsxButton.addEventListener("click", () => {
        window.location.href = `/api/tracker-entries/missing-report/download?format=xlsx&limit=${getMissingReportDownloadLimit()}`;
      });
    }
    dom.patchField.addEventListener("change", syncPatchValueFromSelectedEntry);
    dom.drawerBackdrop.addEventListener("click", closeDrawer);
    dom.drawerCloseButton.addEventListener("click", closeDrawer);
    if (dom.presetRefreshButton) {
      dom.presetRefreshButton.addEventListener("click", () => loadRunPresets({}));
    }
    if (dom.presetApplyButton) {
      dom.presetApplyButton.addEventListener("click", applySelectedPreset);
    }
    if (dom.presetSaveButton) {
      dom.presetSaveButton.addEventListener("click", saveCurrentFormAsPreset);
    }
    if (dom.presetSelect) {
      dom.presetSelect.addEventListener("change", () => {
        state.selectedPresetId = dom.presetSelect.value || null;
        renderRunPresetPanel();
      });
    }
    if (dom.projectSearchButton) {
      dom.projectSearchButton.addEventListener("click", () => {
        state.projectFilters.page = 1;
        void loadProjects({});
      });
    }
    if (dom.projectRefreshButton) {
      dom.projectRefreshButton.addEventListener("click", () => loadProjects({}));
    }
    if (dom.projectQuery) {
      dom.projectQuery.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          state.projectFilters.page = 1;
          void loadProjects({});
        }
      });
    }
    if (dom.projectPrevButton) {
      dom.projectPrevButton.addEventListener("click", () => changeProjectsPage(-1));
    }
    if (dom.projectNextButton) {
      dom.projectNextButton.addEventListener("click", () => changeProjectsPage(1));
    }
  }


  return {
    bindEvents,
  };
}

const appEventBindingsRoot = typeof window !== 'undefined' ? window : globalThis;
appEventBindingsRoot.APP_EVENT_BINDINGS = appEventBindingsRoot.APP_EVENT_BINDINGS || {};
appEventBindingsRoot.APP_EVENT_BINDINGS.createAppEventBindings = createAppEventBindings;
