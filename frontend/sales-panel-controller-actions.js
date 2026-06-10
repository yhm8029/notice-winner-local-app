import { createSalesActionRecommendationsRuntime } from "./sales-action-recommendations-runtime.js?v=20260604b";

export function createSalesPanelControllerActions(deps = {}) {
  const {
    state,
    dom,
    window: appWindow = typeof window !== "undefined" ? window : null,
    flash,
    api,
    renderTrackerEntries,
    loadSalesOverview,
    loadMySalesClaims,
    loadVisibleSalesClaims,
    refreshSalesAdminPanels,
    syncUrlState,
    getSalesClaimForProject,
    getSalesNoteDraft,
    setSalesNoteDraft,
    getSalesNoteEntries,
    serializeSalesNoteEntry,
    removeLatestSalesNoteEntry,
    canCurrentUserForceRelease,
    formatContractAmountInput,
    renderClosedSalesArchiveSection,
    renderUserOwnedSalesClaimCard,
    renderCompanySalesClaimCard,
    formatSalesClaimEstimateLabel,
    renderUserTrackerClaimSection,
    renderSalesNoteTimelineMarkup,
  } = deps;
  const salesListHtmlByElement = new WeakMap();
  let pendingMySalesClaimsPanelRenderHandle = null;
  let salesListSelectionAttemptActive = false;
  let salesListSelectionGuardBound = false;

  function hasActiveTextSelection() {
    if (salesListSelectionAttemptActive) {
      return true;
    }
    const getSelection = typeof appWindow?.getSelection === "function" ? appWindow.getSelection : null;
    const selection = getSelection ? getSelection.call(appWindow) : null;
    return Boolean(selection && (!selection.isCollapsed || String(selection.toString?.() || "").trim()));
  }

  function clearSalesListSelectionAttemptSoon() {
    const setTimeoutFn = typeof appWindow?.setTimeout === "function" ? appWindow.setTimeout.bind(appWindow) : setTimeout;
    setTimeoutFn(() => {
      salesListSelectionAttemptActive = false;
    }, 0);
  }

  function bindSalesListSelectionGuard() {
    if (salesListSelectionGuardBound) {
      return;
    }
    const targets = [dom.trackerUserSalesList, dom.trackerCompanySalesList].filter(Boolean);
    if (!targets.length) {
      return;
    }
    salesListSelectionGuardBound = true;
    const markSelectionAttempt = () => {
      salesListSelectionAttemptActive = true;
    };
    for (const target of targets) {
      target.addEventListener?.("pointerdown", markSelectionAttempt);
      target.addEventListener?.("mousedown", markSelectionAttempt);
      target.addEventListener?.("selectstart", markSelectionAttempt);
    }
    const clearSelectionAttempt = () => clearSalesListSelectionAttemptSoon();
    appWindow?.addEventListener?.("pointerup", clearSelectionAttempt, true);
    appWindow?.addEventListener?.("mouseup", clearSelectionAttempt, true);
    appWindow?.addEventListener?.("pointercancel", clearSelectionAttempt, true);
    appWindow?.addEventListener?.("blur", clearSelectionAttempt, true);
  }

  function scheduleMySalesClaimsPanelRender() {
    if (pendingMySalesClaimsPanelRenderHandle) {
      return;
    }
    const setTimeoutFn = typeof appWindow?.setTimeout === "function" ? appWindow.setTimeout.bind(appWindow) : setTimeout;
    pendingMySalesClaimsPanelRenderHandle = setTimeoutFn(() => {
      pendingMySalesClaimsPanelRenderHandle = null;
      renderMySalesClaimsPanel();
    }, 120);
  }

  function replaceSalesListHtmlIfChanged(element, html, { deferOnSelection = true } = {}) {
    if (!element) {
      return "missing";
    }
    const nextHtml = String(html || "");
    const lastHtml = salesListHtmlByElement.get(element) ?? null;
    if (lastHtml === nextHtml) {
      return "skipped";
    }
    if (deferOnSelection && lastHtml !== null && hasActiveTextSelection()) {
      scheduleMySalesClaimsPanelRender();
      return "deferred";
    }
    element.innerHTML = nextHtml;
    salesListHtmlByElement.set(element, nextHtml);
    return "applied";
  }

  const salesActionRecommendations = createSalesActionRecommendationsRuntime({
    state,
    dom,
    window: appWindow,
    flash,
    api,
    escapeHtml: deps.escapeHtml,
    replaceSalesListHtmlIfChanged,
    claimSalesProject,
    syncUrlState,
  });

  async function claimSalesProject(entry) {
    if (!entry || !entry.project_id) {
      flash("project_id媛 ?녿뒗 ?됱? ?곸뾽 ???吏?뺤씠 遺덇??ν빀?덈떎.", "error");
      return;
    }
    const projectId = String(entry.project_id);
    state.salesClaimSavingProjectIds[projectId] = true;
    renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    try {
      const response = await api(`/api/sales-claims/projects/${projectId}/claim`, {
        method: "POST",
        body: JSON.stringify({
          source_entry_id: entry.id,
          source_run_id: entry.source_tracker_run_id || entry.source_run_id || null,
          project_name: entry.project_name || "",
          estimated_amount_text: entry.building_automation_estimated_amount || entry.construction_cost || "",
        }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      deps.upsertSalesClaim(response.claim);
      setSalesNoteDraft(projectId, "");
      flash(response.changed ? "?곸뾽???쒖옉?덈떎." : "?대? 蹂몄씤???대떦 以묒씤 ?꾨줈?앺듃??");
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadMySalesClaims({ silent: true });
        refreshSalesAdminPanels({ silent: true });
      }
    } catch (err) {
      flash(err.message, "error");
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadVisibleSalesClaims({ silent: true });
      }
    } finally {
      delete state.salesClaimSavingProjectIds[projectId];
      renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    }
  }

  async function saveSalesClaimNote(projectId) {
    const claim = getSalesClaimForProject(projectId);
    if (!claim) {
      flash("?곸뾽 ?꾪솴????ν븷 ??곸씠 ?놁뒿?덈떎.", "error");
      return;
    }
    const key = String(projectId || "");
    const nextEntry = String(getSalesNoteDraft(key, claim) || "").trim();
    if (!nextEntry) {
      flash("?곸뾽 ?꾪솴???낅젰?대씪.", "warn");
      return;
    }
    const nextSalesNote = [...getSalesNoteEntries(claim.sales_note), serializeSalesNoteEntry(nextEntry)].join("\n");
    state.salesClaimSavingProjectIds[key] = true;
    renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    try {
      const response = await api(`/api/sales-claims/projects/${key}`, {
        method: "PATCH",
        body: JSON.stringify({
          sales_note: nextSalesNote,
        }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      deps.upsertSalesClaim(response.claim);
      setSalesNoteDraft(key, "");
      flash("?곸뾽 ?꾪솴????ν뻽??");
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadMySalesClaims({ silent: true });
        refreshSalesAdminPanels({ silent: true });
      }
    } catch (err) {
      flash(err.message, "error");
    } finally {
      delete state.salesClaimSavingProjectIds[key];
      renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    }
  }

  async function transferSalesClaim(projectId, targetUserId) {
    const key = String(projectId || "").trim();
    if (!key) {
      return;
    }
    const target = (state.organizationUsers || []).find((item) => String(item.id || "") === String(targetUserId || ""));
    if (!target) {
      flash("?닿? ????ъ슜?먮? ?좏깮?대씪.", "warn");
      return;
    }
    state.salesClaimSavingProjectIds[key] = true;
    renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    renderSalesSummaryPanel();
    try {
      const response = await api(`/api/sales-claims/projects/${key}/transfer`, {
        method: "POST",
        body: JSON.stringify({
          target_user_id: target.id,
          target_email: target.email,
          force: canCurrentUserForceRelease(),
        }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      deps.upsertSalesClaim(response.claim);
      flash(`${target.display_name || target.email}?먭쾶 ?곸뾽???닿??덈떎.`);
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadMySalesClaims({ silent: true });
        refreshSalesAdminPanels({ silent: true });
        void loadVisibleSalesClaims({ silent: true });
      }
    } catch (err) {
      flash(err.message, "error");
    } finally {
      delete state.salesClaimSavingProjectIds[key];
      renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
      renderSalesSummaryPanel();
    }
  }

  async function closeSalesClaim(projectId, outcome, { contractAmountText = "" } = {}) {
    const key = String(projectId || "").trim();
    if (!key) {
      return;
    }
    const outcomeLabel = outcome === "won" ? "怨꾩빟 ?꾨즺" : "?곸뾽 醫낅즺";
    if (outcome === "won" && !String(contractAmountText || "").trim()) {
      flash("怨꾩빟湲덉븸???낅젰?댁빞 怨꾩빟 ?꾨즺 泥섎━?????덈떎.", "warn");
      return;
    }
    state.salesClaimSavingProjectIds[key] = true;
    renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    renderSalesSummaryPanel();
    try {
      const response = await api(`/api/sales-claims/projects/${key}/close`, {
        method: "POST",
        body: JSON.stringify({
          outcome,
          contract_amount_text: contractAmountText,
          force: canCurrentUserForceRelease(),
        }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      deps.upsertSalesClaim(response.claim);
      flash(`${outcomeLabel} 泥섎━?덈떎.`);
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadMySalesClaims({ silent: true });
        refreshSalesAdminPanels({ silent: true });
        void loadVisibleSalesClaims({ silent: true });
      }
    } catch (err) {
      flash(err.message, "error");
    } finally {
      delete state.salesClaimSavingProjectIds[key];
      renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
      renderSalesSummaryPanel();
    }
  }

  function openSalesCloseDialog(projectId) {
    state.salesCloseDialog.open = true;
    state.salesCloseDialog.projectId = String(projectId || "").trim();
    if (dom.salesCloseAmountInput) {
      dom.salesCloseAmountInput.value = "";
    }
    dom.salesCloseDialog?.classList.remove("hidden");
    appWindow.setTimeout(() => {
      dom.salesCloseAmountInput?.focus();
    }, 0);
  }

  function closeSalesCloseDialog() {
    state.salesCloseDialog.open = false;
    state.salesCloseDialog.projectId = "";
    dom.salesCloseDialog?.classList.add("hidden");
    if (dom.salesCloseAmountInput) {
      dom.salesCloseAmountInput.value = "";
    }
  }

  async function confirmSalesCloseDialog() {
    if (!state.salesCloseDialog.open || !state.salesCloseDialog.projectId) {
      return;
    }
    const amount = formatContractAmountInput(dom.salesCloseAmountInput?.value || "");
    if (!amount) {
      flash("怨꾩빟湲덉븸???낅젰?댁빞 怨꾩빟 ?꾨즺 泥섎━?????덈떎.", "warn");
      dom.salesCloseAmountInput?.focus();
      return;
    }
    const projectId = state.salesCloseDialog.projectId;
    closeSalesCloseDialog();
    await closeSalesClaim(projectId, "won", { contractAmountText: amount });
  }

  async function adminDeleteLatestSalesNote(projectId, rawSalesNote) {
    const key = String(projectId || "").trim();
    const nextSalesNote = removeLatestSalesNoteEntry(rawSalesNote);
    state.salesClaimSavingProjectIds[key] = true;
    renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    renderSalesSummaryPanel();
    try {
      const response = await api(`/api/sales-claims/projects/${key}`, {
        method: "PATCH",
        body: JSON.stringify({
          sales_note: nextSalesNote,
          force_admin_override: true,
        }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      deps.upsertSalesClaim(response.claim);
      flash("愿由ъ옄 沅뚰븳?쇰줈 理쒓렐 硫붾え瑜???젣?덈떎.");
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadMySalesClaims({ silent: true });
        refreshSalesAdminPanels({ silent: true });
        void loadVisibleSalesClaims({ silent: true });
      }
    } catch (err) {
      flash(err.message, "error");
    } finally {
      delete state.salesClaimSavingProjectIds[key];
      renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
      renderSalesSummaryPanel();
    }
  }

  async function releaseSalesClaim(projectId, { force = false } = {}) {
    if (!projectId) {
      return;
    }
    const key = String(projectId);
    state.salesClaimSavingProjectIds[key] = true;
    renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    try {
      await api(`/api/sales-claims/projects/${key}/release`, {
        method: "POST",
        body: JSON.stringify({ force: Boolean(force) }),
        cacheBust: false,
        timeoutMs: 15000,
      });
      delete state.salesClaimsByProjectId[key];
      delete state.salesClaimDrafts[key];
      flash(force ? "愿由ъ옄 沅뚰븳?쇰줈 ?곸뾽???댁젣?덈떎." : "?곸뾽???댁젣?덈떎.");
      if (state.uiMode === "user") {
        void loadSalesOverview({ silent: true, force: true });
      } else {
        void loadMySalesClaims({ silent: true });
        refreshSalesAdminPanels({ silent: true });
      }
    } catch (err) {
      flash(err.message, "error");
    } finally {
      delete state.salesClaimSavingProjectIds[key];
      renderTrackerEntries(state.trackerEntries, { refreshSelectedEntry: false });
    }
  }

  function renderSalesSummaryPanel() {
    if (!dom.salesSummaryList) {
      return;
    }
    if (state.uiMode !== "admin") {
      dom.salesSummaryList.innerHTML = '<div class="empty-state">관리자 모드에서 영업 현황 지표를 확인할 수 있습니다.</div>';
      return;
    }
    if (state.salesSummaryLoading || state.salesClosedLoading) {
      dom.salesSummaryList.innerHTML = '<div class="empty-state">영업 지표를 불러오는 중입니다.</div>';
      return;
    }
    if (state.salesSummaryError || state.salesClosedError) {
      dom.salesSummaryList.innerHTML = `<div class="empty-state">${deps.escapeHtml(state.salesSummaryError || state.salesClosedError)}</div>`;
      return;
    }
    const activeMarkup = state.salesSummaryByUser.length
      ? state.salesSummaryByUser
      .map((item) => {
        const totalAmountLabel = deps.formatEstimatedAmountRangeFromKrw(item.total_low_krw, item.total_high_krw, "-");
        const projectsMarkup = (item.projects || [])
          .map((project, index) => {
            const latestNote = deps.getLatestSalesNoteItem(project.sales_note, project.claimed_at);
            const latestNoteLabel = latestNote
              ? `${latestNote.timestamp ? `${latestNote.timestamp} 夷?` : ""}${deps.truncate(deps.formatSalesNoteTextForDisplay(latestNote.text), 120)}`
              : "";
            return `
            <article class="sales-summary-project">
              <div class="sales-summary-project-copy">
                <strong>${deps.escapeHtml(String(index + 1))}. ${deps.escapeHtml(project.project_name || "-")}</strong>
                <p class="mono">${deps.escapeHtml(formatSalesClaimEstimateLabel(project))} | ${deps.escapeHtml(deps.formatSalesDateLabel(project.claimed_at))} ?곸뾽 ?쒖옉</p>
                <p>${deps.escapeHtml(project.elapsed_days)}??寃쎄낵 夷??꾩옱 ?대떦 ${deps.escapeHtml(project.owner_elapsed_days)}?쇱감${latestNoteLabel ? ` | ${deps.escapeHtml(latestNoteLabel)}` : ""}</p>
              </div>
            <div class="sales-summary-project-actions">
              ${
                canCurrentUserForceRelease() && deps.getSalesNoteEntries(project.sales_note).length
                  ? `<button class="ghost-button" type="button" data-sales-force-delete-note="${deps.escapeHtml(project.project_id)}">理쒓렐 硫붾え ??젣</button>`
                  : ""
              }
              ${
                canCurrentUserForceRelease()
                  ? `<button class="ghost-button" type="button" data-sales-force-release="${deps.escapeHtml(project.project_id)}">媛뺤젣 ?댁젣</button>`
                  : ""
              }
            </div>
          </article>
        `;
          })
          .join("");
        return `
        <article class="sales-summary-user">
          <div class="sales-summary-user-head">
            <div>
              <strong>${deps.escapeHtml(item.user_name || item.user_email || "-")}</strong>
              <p class="mono">${deps.escapeHtml(item.user_email || "-")} | ${deps.escapeHtml(String(item.active_project_count || 0))}嫄?吏꾪뻾 以?/p>
            </div>
            <div class="sales-summary-total">
              <span>珥?異붿젙湲덉븸</span>
              <strong>${deps.escapeHtml(totalAmountLabel)}</strong>
            </div>
          </div>
          <div class="sales-summary-project-list">${projectsMarkup}</div>
        </article>
      `;
      })
      .join("")
      : '<div class="empty-state">현재 진행 중인 영업 프로젝트가 없습니다.</div>';

    const wonClaims = state.salesClosedClaims.filter((claim) => String(claim.claim_status || "") === "won");
    const lostClaims = state.salesClosedClaims.filter((claim) => String(claim.claim_status || "") === "lost");
    const closedMarkup = renderClosedSalesArchiveSection("계약 완료", wonClaims, { showContractAmount: true })
      + renderClosedSalesArchiveSection("영업 종료", lostClaims, { showContractAmount: false });

    dom.salesSummaryList.innerHTML = `
    <section class="sales-summary-section">
      <div class="sales-summary-section-head">
        <strong>吏꾪뻾 以??곸뾽</strong>
        <span class="mono">${deps.escapeHtml(String(state.salesSummaryByUser.reduce((count, item) => count + Number(item.active_project_count || 0), 0)))}嫄?/span>
      </div>
      <div class="sales-summary-section-body">${activeMarkup}</div>
    </section>
    <section class="sales-summary-section">
      <div class="sales-summary-section-head">
        <strong>醫낅즺/?꾨즺 ?뺣━</strong>
        <span class="mono">${deps.escapeHtml(String(state.salesClosedClaims.length))}嫄?/span>
      </div>
      <div class="sales-summary-section-body sales-summary-archive-stack">${closedMarkup}</div>
    </section>
  `;

    for (const button of dom.salesSummaryList.querySelectorAll("[data-sales-force-release]")) {
      button.addEventListener("click", () => {
        const projectId = button.getAttribute("data-sales-force-release");
        if (!projectId) {
          return;
        }
        void releaseSalesClaim(projectId, { force: true });
      });
    }
    for (const button of dom.salesSummaryList.querySelectorAll("[data-sales-force-delete-note]")) {
      button.addEventListener("click", () => {
        const projectId = button.getAttribute("data-sales-force-delete-note");
        if (!projectId) {
          return;
        }
        const summaryProject = state.salesSummaryByUser
          .flatMap((item) => item.projects || [])
          .find((item) => String(item.project_id || "") === projectId);
        if (!summaryProject) {
          return;
        }
        void adminDeleteLatestSalesNote(projectId, summaryProject.sales_note || "");
      });
    }
  }

  function renderMySalesClaimsPanel() {
    if (
      !dom.trackerSalesOverviewGrid
      || !dom.trackerUserSalesSection
      || !dom.trackerUserSalesList
      || !dom.trackerCompanySalesSection
      || !dom.trackerCompanySalesList
      || !dom.trackerEntriesSectionTitle
    ) {
      return;
    }
    bindSalesListSelectionGuard();
    const isProjectStatusTab = state.adminTab !== "sales-recommendations";
    const showProjectWorkspace = isProjectStatusTab;
    const canShowRecommendations = salesActionRecommendations.canShowSalesActionRecommendations();
    dom.trackerSalesOverviewGrid.classList.toggle("hidden", !showProjectWorkspace);
    dom.trackerUserSalesSection.classList.toggle("hidden", !showProjectWorkspace);
    dom.trackerCompanySalesSection.classList.toggle("hidden", !showProjectWorkspace);
    dom.trackerEntriesSectionTitle.classList.toggle("hidden", !showProjectWorkspace);
    if (canShowRecommendations) {
      void salesActionRecommendations.loadSalesActionRecommendations({ silent: true });
    } else {
      salesActionRecommendations.renderSalesActionRecommendationsPanel();
    }
    if (!showProjectWorkspace) {
      return;
    }
    if (state.mySalesClaimsLoading) {
      replaceSalesListHtmlIfChanged(dom.trackerUserSalesList, '<div class="empty-state">영업 정보를 불러오는 중입니다.</div>');
      replaceSalesListHtmlIfChanged(dom.trackerCompanySalesList, '<div class="empty-state">회사 진행 영업 정보를 불러오는 중입니다.</div>');
      return;
    }
    if (state.mySalesClaimsError) {
      replaceSalesListHtmlIfChanged(dom.trackerUserSalesList, `<div class="empty-state">${deps.escapeHtml(state.mySalesClaimsError)}</div>`);
      replaceSalesListHtmlIfChanged(dom.trackerCompanySalesList, `<div class="empty-state">${deps.escapeHtml(state.mySalesClaimsError)}</div>`);
      return;
    }

    dom.trackerUserSalesList.className = "runtime-list user-sales-list";
    const userSalesListHtml = state.mySalesClaims.length
      ? state.mySalesClaims.map((claim, index) => renderUserOwnedSalesClaimCard(claim, index)).join("")
      : '<div class="empty-state">현재 내가 진행 중인 영업 프로젝트가 없습니다.</div>';
    replaceSalesListHtmlIfChanged(dom.trackerUserSalesList, userSalesListHtml);

    dom.trackerCompanySalesList.className = "runtime-list user-sales-list";
    const companySalesListHtml = state.companySalesClaims.length
      ? state.companySalesClaims.map((claim, index) => renderCompanySalesClaimCard(claim, index)).join("")
      : '<div class="empty-state">현재 회사 전체가 진행 중인 영업 프로젝트가 없습니다.</div>';
    replaceSalesListHtmlIfChanged(dom.trackerCompanySalesList, companySalesListHtml);

    bindUserSalesSectionEvents();
  }

  function bindUserSalesSectionEvents() {
    if (!dom.trackerUserSalesList) {
      return;
    }
    for (const textarea of dom.trackerUserSalesList.querySelectorAll("[data-user-sales-note]")) {
      textarea.addEventListener("input", () => {
        const projectId = textarea.getAttribute("data-user-sales-note");
        if (!projectId) {
          return;
        }
        setSalesNoteDraft(projectId, textarea.value);
      });
      textarea.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          const projectId = textarea.getAttribute("data-user-sales-note");
          if (projectId) {
            void saveSalesClaimNote(projectId);
          }
        }
      });
    }
    for (const button of dom.trackerUserSalesList.querySelectorAll("[data-user-sales-note-save]")) {
      button.addEventListener("click", () => {
        const projectId = button.getAttribute("data-user-sales-note-save");
        if (projectId) {
          void saveSalesClaimNote(projectId);
        }
      });
    }
    for (const button of dom.trackerUserSalesList.querySelectorAll("[data-user-sales-transfer]")) {
      button.addEventListener("click", () => {
        const projectId = button.getAttribute("data-user-sales-transfer");
        if (!projectId) {
          return;
        }
        const escapedProjectId = appWindow?.CSS?.escape ? appWindow.CSS.escape(projectId) : projectId;
        const select = dom.trackerUserSalesList.querySelector(`[data-user-sales-transfer-select="${escapedProjectId}"]`);
        const targetUserId = appWindow?.HTMLSelectElement && select instanceof appWindow.HTMLSelectElement ? select.value : "";
        if (!targetUserId) {
          flash("?닿? ????ъ슜?먮? ?좏깮?대씪.", "warn");
          return;
        }
        void transferSalesClaim(projectId, targetUserId);
      });
    }
    for (const button of dom.trackerUserSalesList.querySelectorAll("[data-user-sales-close]")) {
      button.addEventListener("click", () => {
        const projectId = button.getAttribute("data-user-sales-close");
        const outcome = button.getAttribute("data-user-sales-close-outcome");
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
    for (const button of dom.trackerUserSalesList.querySelectorAll("[data-user-sales-release]")) {
      button.addEventListener("click", () => {
        const projectId = button.getAttribute("data-user-sales-release");
        if (projectId) {
          void releaseSalesClaim(projectId);
        }
      });
    }
  }

  return {
    claimSalesProject,
    saveSalesClaimNote,
    transferSalesClaim,
    closeSalesClaim,
    adminDeleteLatestSalesNote,
    releaseSalesClaim,
    openSalesCloseDialog,
    closeSalesCloseDialog,
    confirmSalesCloseDialog,
    renderSalesSummaryPanel,
    renderMySalesClaimsPanel,
    bindUserSalesSectionEvents,
    renderSalesActionRecommendationsPanel: salesActionRecommendations.renderSalesActionRecommendationsPanel,
    loadSalesActionRecommendations: salesActionRecommendations.loadSalesActionRecommendations,
  };
}
