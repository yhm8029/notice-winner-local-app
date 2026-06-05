(function attachSPMSTrackerRenderFallbackEntryRuntime(globalObject) {
  function buildTrackerEntryCardMarkupFallback(payload = {}, helpers = {}) {
    const {
      entry = {},
      displayNo = "",
      isSelected = false,
    } = payload;
    const {
      escapeHtml: fallbackEscapeHtml = (value) => String(value ?? ""),
      formatBuildingAutomationEstimateValue = (_entry, fallbackValue = "") => String(fallbackValue || "-"),
      formatKoreanDate = (value) => String(value ?? ""),
    } = helpers;
    const selectedClass = isSelected ? " is-selected" : "";
    const buildingAutomationEstimate = formatBuildingAutomationEstimateValue(
      entry,
      entry.building_automation_estimated_amount || "-",
    );
    const siteRegion = String(entry.site_location_1 || "").trim();
    const siteCity = String(entry.site_location_2 || "").trim();
    const siteLocationText = siteRegion && siteCity
      ? (siteRegion.includes(siteCity) ? siteRegion : `${siteRegion} ${siteCity}`)
      : (siteCity || siteRegion || "-");
    return `
      <article class="entry-item${selectedClass}" data-entry-id="${fallbackEscapeHtml(entry.id)}">
        <div class="entry-shell">
          <div class="entry-no-badge" aria-label="No. ${fallbackEscapeHtml(String(displayNo))}">
            <span class="entry-no-label">No.</span>
            <strong>${fallbackEscapeHtml(String(displayNo))}</strong>
          </div>
          <div class="entry-body">
            <div class="entry-head">
              <div>
                <strong>${fallbackEscapeHtml(entry.project_name)}</strong>
              </div>
              <div class="entry-head-actions">
                <button class="ghost-button tracker-related-toggle" type="button" data-entry-notice-view="${fallbackEscapeHtml(entry.id)}">
                  notice viewer
                </button>
              </div>
            </div>
            <p>${fallbackEscapeHtml(entry.demand_org_name || "(no demand org)")}</p>
            <p class="entry-metrics">
              <span><strong>gross area</strong> ${fallbackEscapeHtml(entry.gross_area_scale || "-")}</span>
              <span><strong>construction cost</strong> ${fallbackEscapeHtml(entry.construction_cost || "-")}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>building automation estimate</strong> ${fallbackEscapeHtml(buildingAutomationEstimate)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>architect office</strong> ${fallbackEscapeHtml(entry.architect_office || "-")}</span>
              <span><strong>construction start</strong> ${fallbackEscapeHtml(entry.construction_start_date || "-")}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>opening scheduled</strong> ${fallbackEscapeHtml(formatKoreanDate(entry.opening_scheduled_date || ""))}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>demand contact</strong> ${fallbackEscapeHtml(entry.demand_contact || "-")}</span>
              <span><strong>site location</strong> ${fallbackEscapeHtml(siteLocationText)}</span>
            </p>
          </div>
        </div>
      </article>
    `;
  }

  function buildTrackerEntriesListMarkupFallback(entryViews = []) {
    return `
      <div class="entry-list">
        ${Array.isArray(entryViews) ? entryViews.map((view) => view?.html || "").join("") : ""}
      </div>
    `;
  }

  function buildTrackerEntriesEmptyStateViewFallback(options = {}) {
    const {
      trackerEntriesError = "",
      uiMode = "user",
      escapeHtml = (value) => String(value ?? ""),
      errorPrefix = "Project entries failed to load",
      userEmptyHtml = '<div class="empty-state">No project is ready to pull into the sales view.</div>',
      adminEmptyHtml = '<div class="empty-state">No tracker rows loaded.</div>',
    } = options;
    if (trackerEntriesError) {
      return {
        html: `<div class="empty-state">${escapeHtml(errorPrefix)}: ${escapeHtml(trackerEntriesError)}</div>`,
      };
    }
    return {
      html: uiMode === "user" ? userEmptyHtml : adminEmptyHtml,
    };
  }

  function renderTrackerEntriesFallback(entries, context = {}, helpers = {}) {
    const {
      dom = null,
      state = null,
      resetTrackerBoardEdit = () => {},
      renderTrackerBoard = () => {},
      renderSelectedEntry = () => {},
      buildTrackerEntriesEmptyStateView = buildTrackerEntriesEmptyStateViewFallback,
      buildTrackerEntryCardView = null,
      buildTrackerEntriesListMarkup = buildTrackerEntriesListMarkupFallback,
      renderSalesClaimSection = () => "",
      formatKoreanDate = (value) => String(value ?? ""),
      formatBuildingAutomationEstimateValue = (_entry, fallbackValue = "") => String(fallbackValue || "-"),
      getSalesClaimForProject = () => null,
      syncUrlState = () => {},
      openTrackerEntryNoticeViewer = () => {},
      bindRelatedNoticeViewerButtons = () => {},
      claimSalesProject = () => {},
      setSalesNoteDraft = () => {},
      saveSalesClaimNote = () => {},
      transferSalesClaim = () => {},
      flash = () => {},
      openSalesCloseDialog = () => {},
      closeSalesClaim = () => {},
      releaseSalesClaim = () => {},
      loadSelectedEntryDetail = () => {},
      buildTrackerEntrySummaryDetail = null,
      prefetchTrackerEntryDetails = () => {},
      refreshSelectedEntry = true,
    } = context;
    const {
      escapeHtml = (value) => String(value ?? ""),
    } = helpers;

    if (typeof dom === "undefined" || !dom || typeof state === "undefined" || !state || !dom.trackerEntriesList) {
      return;
    }

    const sourceEntries = Array.isArray(entries) ? entries : [];
    const displayEntries = state.uiMode === "user"
      ? sourceEntries.filter((entry) => !getSalesClaimForProject(String(entry.project_id || "").trim()))
      : sourceEntries;

    if (!displayEntries.length) {
      resetTrackerBoardEdit();
      state.trackerRelatedEntryId = null;
      state.trackerRelatedResolvingEntryId = null;
      const emptyView = buildTrackerEntriesEmptyStateView({
        trackerEntriesError: state.trackerEntriesError,
        uiMode: state.uiMode,
        escapeHtml,
        errorPrefix: "Project entries failed to load",
        userEmptyHtml: '<div class="empty-state">No project is ready to pull into the sales view.</div>',
        adminEmptyHtml: '<div class="empty-state">No tracker rows loaded.</div>',
      }) || { html: '<div class="empty-state">No tracker rows loaded.</div>' };
      dom.trackerEntriesList.innerHTML = emptyView.html;
      renderTrackerBoard([]);
      if (refreshSelectedEntry) {
        renderSelectedEntry(null);
      }
      return;
    }

    if (!displayEntries.some((entry) => entry.id === state.selectedEntryId)) {
      state.selectedEntryId = displayEntries[0].id;
    }
    if (!displayEntries.some((entry) => entry.id === state.trackerRelatedEntryId)) {
      state.trackerRelatedEntryId = null;
    }

    const entryViews = displayEntries.map((entry, index) => {
      const displayNo = (state.trackerFilters.page - 1) * state.trackerFilters.pageSize + index + 1;
      if (buildTrackerEntryCardView) {
        return buildTrackerEntryCardView(entry, {
          displayNo,
          selectedEntryId: state.selectedEntryId,
          trackerRelatedEntryId: state.trackerRelatedEntryId,
          uiMode: state.uiMode,
          formatOpeningScheduledDate: formatKoreanDate,
          formatEstimateValue: (item) => formatBuildingAutomationEstimateValue(item, item.building_automation_estimated_amount || "-"),
          noticeViewButtonLabel: "notice viewer",
          grossAreaLabel: "gross area",
          constructionCostLabel: "construction cost",
          estimateLabel: "building automation estimate",
          architectOfficeLabel: "architect office",
          constructionStartDateLabel: "construction start date",
          openingScheduledDateLabel: "opening scheduled date",
          demandContactLabel: "demand contact",
          siteLocationLabel: "site location",
          salesSectionHtml: renderSalesClaimSection(entry),
        });
      }
      return {
        html: buildTrackerEntryCardMarkupFallback(
          {
            entry,
            displayNo,
            isSelected: entry.id === state.selectedEntryId,
            overrideMarkup: state.uiMode === "admin"
              ? `<p>${escapeHtml(entry.overridden_fields?.length ? `override ${entry.overridden_fields.join(", ")}` : "no overrides")}</p>`
              : "",
            salesMarkup: renderSalesClaimSection(entry),
          },
          {
            escapeHtml,
            formatBuildingAutomationEstimateValue,
            formatKoreanDate,
          },
        ),
      };
    });

    dom.trackerEntriesList.innerHTML = buildTrackerEntriesListMarkup(entryViews, { escapeHtml });

    for (const item of dom.trackerEntriesList.querySelectorAll("[data-entry-id]")) {
      item.addEventListener("click", (event) => {
        if (event.target.closest("button, a, textarea, input, select, label")) {
          return;
        }
        const selection = typeof globalObject.getSelection === "function" ? globalObject.getSelection() : null;
        if (selection && (!selection.isCollapsed || selection.toString().trim())) {
          return;
        }
        state.selectedEntryId = item.getAttribute("data-entry-id");
        state.drawerOpen = false;
        syncUrlState();
        renderTrackerEntriesFallback(state.trackerEntries, { ...context, refreshSelectedEntry: state.uiMode === "admin" }, helpers);
      });
    }

    for (const button of dom.trackerEntriesList.querySelectorAll("[data-entry-notice-view]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entryId = button.getAttribute("data-entry-notice-view");
        if (!entryId) {
          return;
        }
        void openTrackerEntryNoticeViewer(entryId, entries);
      });
    }

    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-claim]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const entryId = button.getAttribute("data-sales-claim");
        const entry = displayEntries.find((item) => item.id === entryId);
        if (!entry) {
          return;
        }
        void claimSalesProject(entry);
      });
    }

    for (const textarea of dom.trackerEntriesList.querySelectorAll("[data-sales-note]")) {
      textarea.addEventListener("click", (event) => event.stopPropagation());
      textarea.addEventListener("input", () => {
        const projectId = textarea.getAttribute("data-sales-note");
        if (!projectId) {
          return;
        }
        setSalesNoteDraft(projectId, textarea.value);
      });
      textarea.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          const projectId = textarea.getAttribute("data-sales-note");
          if (!projectId) {
            return;
          }
          void saveSalesClaimNote(projectId);
        }
      });
    }

    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-note-save]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-note-save");
        if (!projectId) {
          return;
        }
        void saveSalesClaimNote(projectId);
      });
    }

    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-transfer]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-transfer");
        if (!projectId) {
          return;
        }
        const select = button.closest(".entry-sales-transfer")?.querySelector("[data-sales-transfer-select]");
        const targetUserId = select ? select.value : "";
        if (!targetUserId) {
          flash("Select a user to transfer.", "warn");
          return;
        }
        void transferSalesClaim(projectId, targetUserId);
      });
    }

    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-close]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-close");
        const outcome = button.getAttribute("data-sales-close-outcome");
        if (!projectId || !outcome) {
          return;
        }
        if (outcome === "won") {
          openSalesCloseDialog(projectId);
          return;
        }
        void closeSalesClaim(projectId, outcome);
      });
    }

    for (const button of dom.trackerEntriesList.querySelectorAll("[data-sales-release]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-sales-release");
        if (!projectId) {
          return;
        }
        void releaseSalesClaim(projectId);
      });
    }

    const selectedEntry = displayEntries.find((entry) => entry.id === state.selectedEntryId) || displayEntries[0];
    renderTrackerBoard(displayEntries);
    if (refreshSelectedEntry) {
      const cachedSelectedEntry =
        (state.selectedEntry?.id === selectedEntry.id ? state.selectedEntry : null)
        || state.trackerEntryDetailCache[selectedEntry.id]
        || null;
      if (cachedSelectedEntry) {
        const summaryOnly = Boolean(cachedSelectedEntry._summary_only);
        renderSelectedEntry(cachedSelectedEntry, { summaryOnly });
        if (summaryOnly) {
          void loadSelectedEntryDetail({
            entryId: selectedEntry.id,
            silent: true,
            background: true,
          });
        }
      } else {
        renderSelectedEntry(buildTrackerEntrySummaryDetail ? buildTrackerEntrySummaryDetail(selectedEntry) : selectedEntry, { summaryOnly: true });
        void loadSelectedEntryDetail({
          entryId: selectedEntry.id,
          silent: true,
          background: true,
        });
      }
    }

  }

  globalObject.SPMSTrackerRenderFallbackEntryRuntime = {
    buildTrackerEntryCardMarkupFallback,
    buildTrackerEntriesEmptyStateViewFallback,
    buildTrackerEntriesListMarkupFallback,
    renderTrackerEntriesFallback,
  };
})(window);
