const SALES_ACTION_RECOMMENDATION_SEEN_STORAGE_KEY = "notice-winner-pipeline-web.salesActionRecommendations.seen.v1";
const SALES_RECOMMENDATIONS_ADMIN_TAB = "sales-recommendations";

export function createSalesActionRecommendationsRuntime(deps = {}) {
  const {
    state,
    dom,
    window: appWindow = typeof window !== "undefined" ? window : null,
    flash,
    api,
    escapeHtml,
    replaceSalesListHtmlIfChanged,
    claimSalesProject,
    syncUrlState,
  } = deps;
  const boundSalesActionButtons = new WeakMap();
  let salesActionPanelGuardBound = false;

  function bindSalesActionButtonOnce(button, key, handler) {
    if (!button || typeof button.addEventListener !== "function") {
      return;
    }
    const boundKeys = boundSalesActionButtons.get(button) || new Set();
    if (boundKeys.has(key)) {
      return;
    }
    boundKeys.add(key);
    boundSalesActionButtons.set(button, boundKeys);
    button.addEventListener("click", handler);
  }

  function containSalesActionClick(event) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
  }

  function openNoticeViewerFrame(url, title = "怨듦퀬臾?) {
    const doc = appWindow?.document || null;
    if (!doc?.body || typeof doc.createElement !== "function") {
      if (url && appWindow?.location) {
        if (typeof appWindow.location.assign === "function") {
          appWindow.location.assign(url);
        } else {
          appWindow.location.href = url;
        }
        return true;
      }
      return false;
    }
    doc.getElementById?.("notice-viewer-overlay")?.remove?.();
    const overlay = doc.createElement("div");
    overlay.id = "notice-viewer-overlay";
    overlay.className = "notice-viewer-overlay";
    const panel = doc.createElement("section");
    panel.className = "notice-viewer-overlay-panel";
    const header = doc.createElement("header");
    header.className = "notice-viewer-overlay-header";
    const heading = doc.createElement("strong");
    heading.className = "notice-viewer-overlay-title";
    heading.textContent = String(title || "怨듦퀬臾?);
    const closeButton = doc.createElement("button");
    closeButton.type = "button";
    closeButton.className = "notice-viewer-overlay-close";
    closeButton.setAttribute("aria-label", "?リ린");
    closeButton.textContent = "횞";
    const iframe = doc.createElement("iframe");
    iframe.className = "notice-viewer-overlay-frame";
    iframe.setAttribute("title", String(title || "怨듦퀬臾?));
    iframe.src = url;
    closeButton.addEventListener("click", () => overlay.remove?.());
    header.append(heading, closeButton);
    panel.append(header, iframe);
    overlay.appendChild(panel);
    doc.body.appendChild(overlay);
    return true;
  }

  function keepSalesRecommendationsTab({ historyMode = "replace" } = {}) {
    state.adminTab = SALES_RECOMMENDATIONS_ADMIN_TAB;
    if (typeof syncUrlState === "function") {
      syncUrlState({
        historyMode,
        uiMode: state.uiMode,
        adminTab: SALES_RECOMMENDATIONS_ADMIN_TAB,
      });
    }
  }

  function canShowSalesActionRecommendations() {
    return (state.uiMode === "user" || state.uiMode === "admin") && state.adminTab === SALES_RECOMMENDATIONS_ADMIN_TAB;
  }

  function canShowInternalScore() {
    return state.uiMode === "admin";
  }

  function readSalesRecommendationSeenMap() {
    try {
      const raw = appWindow?.localStorage?.getItem(SALES_ACTION_RECOMMENDATION_SEEN_STORAGE_KEY) || "{}";
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_err) {
      return {};
    }
  }

  function writeSalesRecommendationSeenMap(nextMap) {
    try {
      appWindow?.localStorage?.setItem(SALES_ACTION_RECOMMENDATION_SEEN_STORAGE_KEY, JSON.stringify(nextMap || {}));
    } catch (_err) {
      // localStorage is best-effort only; recommendations still render without it.
    }
  }

  function salesRecommendationProjectKey(item) {
    return String(item?.project_id || item?.entry_id || item?.project_name || "").trim();
  }

  function salesRecommendationSeenKey(projectKey, label) {
    return `${projectKey}::${String(label || "").trim()}`;
  }

  function isSalesRecommendationRecentlySeen(item) {
    const projectKey = salesRecommendationProjectKey(item);
    if (!projectKey) {
      return false;
    }
    const seenMap = readSalesRecommendationSeenMap();
    const labels = Array.isArray(item?.action_labels) ? item.action_labels : [item?.primary_label].filter(Boolean);
    const now = Date.now();
    const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
    return labels.some((label) => {
      const raw = seenMap[salesRecommendationSeenKey(projectKey, label)];
      const seenAt = raw ? new Date(raw).getTime() : 0;
      return seenAt && Number.isFinite(seenAt) && now - seenAt >= 0 && now - seenAt < sevenDaysMs;
    });
  }

  function markSalesRecommendationSeen(item) {
    const projectKey = salesRecommendationProjectKey(item);
    if (!projectKey) {
      return;
    }
    const seenMap = readSalesRecommendationSeenMap();
    const labels = Array.isArray(item?.action_labels) ? item.action_labels : [item?.primary_label].filter(Boolean);
    const today = new Date().toISOString();
    for (const label of labels) {
      seenMap[salesRecommendationSeenKey(projectKey, label)] = today;
    }
    writeSalesRecommendationSeenMap(seenMap);
    state.salesActionRecommendations = (state.salesActionRecommendations || []).filter((candidate) => !isSalesRecommendationRecentlySeen(candidate));
    renderSalesActionRecommendationsPanel();
  }

  function formatRecommendationElapsed(item) {
    const elapsed = Number(item?.elapsed_days || 0);
    if (elapsed > 0) {
      return `${elapsed}????;
    }
    return "?ㅻ뒛";
  }

  function formatRecommendationDate(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return "-";
    }
    const compact = raw.replace(/[^0-9]/g, "");
    if (compact.length >= 8) {
      return `${compact.slice(0, 4)}??${compact.slice(4, 6)}??${compact.slice(6, 8)}??;
    }
    return raw;
  }

  function renderInternalScore(item) {
    if (!canShowInternalScore() || item?.internal_sort_score === null || item?.internal_sort_score === undefined) {
      return "";
    }
    return `<span class="sales-action-score">?대? ?뺣젹 ?먯닔 ${escapeHtml(String(item.internal_sort_score))}</span>`;
  }

  function salesRecommendationEntryId(item) {
    return String(item?.entry_id || item?.claim_payload?.id || "").trim();
  }

  function salesRecommendationProjectId(item) {
    return String(item?.project_id || item?.tracker_entry?.project_id || item?.claim_payload?.project_id || "").trim();
  }

  function salesRecommendationTrackerEntry(item) {
    const source = item?.tracker_entry && typeof item.tracker_entry === "object" ? item.tracker_entry : {};
    return {
      id: salesRecommendationEntryId(item),
      project_id: salesRecommendationProjectId(item),
      project_name: String(source.project_name || item?.project_name || "-"),
      demand_org_name: String(source.demand_org_name || "(?섏슂湲곌? ?놁쓬)"),
      gross_area_scale: String(source.gross_area_scale || "-"),
      construction_cost: String(source.construction_cost || "-"),
      building_automation_estimated_amount: String(source.building_automation_estimated_amount || item?.automation_amount_text || "-"),
      architect_office: String(source.architect_office || "-"),
      construction_start_date: String(source.construction_start_date || "-"),
      opening_scheduled_date: String(source.opening_scheduled_date || ""),
      demand_contact: String(source.demand_contact || "-"),
      site_location_1: String(source.site_location_1 || ""),
      site_location_2: String(source.site_location_2 || ""),
    };
  }

  function formatRecommendationSiteLocation(entry) {
    const parts = [entry.site_location_1, entry.site_location_2]
      .map((value) => String(value || "").trim())
      .filter(Boolean);
    return parts.length ? [...new Set(parts)].join(" ") : "-";
  }

  function renderRecommendationProjectStatus(entry, index) {
    return `
      <div class="sales-recommendation-entry">
        <div class="entry-shell">
          <div class="entry-no-badge" aria-label="No. ${escapeHtml(String(index + 1))}">
            <span class="entry-no-label">No.</span>
            <strong>${escapeHtml(String(index + 1))}</strong>
          </div>
          <div class="entry-body">
            <div class="entry-head">
              <div>
                <strong>${escapeHtml(entry.project_name)}</strong>
              </div>
              <div class="entry-head-actions">
                <button class="ghost-button sales-action-notice-view" type="button" data-sales-action-notice-view="${escapeHtml(String(index))}">怨듦퀬臾?蹂닿린</button>
              </div>
            </div>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>諛쒖＜泥?/strong> ${escapeHtml(entry.demand_org_name)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>?곕㈃??/strong> ${escapeHtml(entry.gross_area_scale)}</span>
              <span><strong>怨듭궗鍮?/strong> ${escapeHtml(entry.construction_cost)}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>鍮뚮뵫?먮룞?쒖뼱 異붿젙湲덉븸(怨듭궗鍮꾩쓽 1.5~2%)</strong> ${escapeHtml(entry.building_automation_estimated_amount)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>?ㅺ퀎?щТ??/strong> ${escapeHtml(entry.architect_office)}</span>
              <span><strong>李⑷났</strong> ${escapeHtml(entry.construction_start_date)}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>媛쒖같?덉젙??/strong> ${escapeHtml(formatRecommendationDate(entry.opening_scheduled_date))}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>?대떦</strong> ${escapeHtml(entry.demand_contact)}</span>
              <span><strong>?꾩옣</strong> ${escapeHtml(formatRecommendationSiteLocation(entry))}</span>
            </p>
          </div>
        </div>
      </div>
    `;
  }

  function renderSalesActionRecommendationCard(item, index) {
    const labels = Array.isArray(item.action_labels) ? item.action_labels : [];
    const reasons = Array.isArray(item.reasons) ? item.reasons : [];
    const actions = Array.isArray(item.recommended_actions) ? item.recommended_actions : [];
    const labelMarkup = labels
      .map((label) => `<span class="sales-action-label">${escapeHtml(label)}</span>`)
      .join("");
    const reasonMarkup = reasons.length
      ? `<ul>${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>`
      : "";
    const actionText = actions.join(" / ");
    const trackerEntry = salesRecommendationTrackerEntry(item);
    return `
      <article class="sales-action-card" data-sales-action-index="${escapeHtml(String(index))}">
        <p class="sales-recommendation-eyebrow">?곸뾽 異붿쿇 由ъ뒪??/p>
        ${renderRecommendationProjectStatus(trackerEntry, index)}
        <div class="sales-action-labels">
          <strong>?곸뾽</strong>
          ${labelMarkup || `<span class="sales-action-label">${escapeHtml(item.primary_label || "異붿쿇")}</span>`}
          ${renderInternalScore(item)}
          <span class="sales-action-label">理쒓렐 怨듦퀬 ${escapeHtml(item.latest_meaningful_notice_type || "-")}</span>
          <span class="sales-action-label">${escapeHtml(formatRecommendationElapsed(item))}</span>
        </div>
        <div class="sales-action-reasons">
          <strong>異붿쿇 ?댁쑀</strong>
          ${reasonMarkup || `<p>${escapeHtml("異붿쿇 ?댁쑀瑜??뺤씤 以묒엯?덈떎.")}</p>`}
        </div>
        <div class="sales-action-next">
          <strong>異붿쿇 ?≪뀡</strong>
          <p>${escapeHtml(actionText || "?꾨줈?앺듃 ?곹깭瑜??뺤씤?섏꽭??")}</p>
        </div>
        <div class="sales-action-buttons">
          <button class="ghost-button" type="button" data-sales-action-interest="${escapeHtml(String(index))}">愿???깅줉</button>
          <button class="ghost-button" type="button" data-sales-action-claim="${escapeHtml(String(index))}">?대떦??諛곗젙</button>
          <button class="ghost-button" type="button" data-sales-action-done="${escapeHtml(String(index))}">?뺤씤 ?꾨즺</button>
          <button class="ghost-button" type="button" data-sales-action-hold="${escapeHtml(String(index))}">蹂대쪟</button>
        </div>
      </article>
    `;
  }

  function visibleSalesActionRecommendations() {
    return (state.salesActionRecommendations || []).filter((item) => !isSalesRecommendationRecentlySeen(item));
  }

  function renderSalesActionRecommendationsPanel() {
    if (!dom.trackerSalesRecommendationSection || !dom.trackerSalesRecommendationList) {
      return;
    }
    const isVisibleMode = canShowSalesActionRecommendations();
    dom.trackerSalesRecommendationSection.classList.toggle("hidden", !isVisibleMode);
    if (!isVisibleMode) {
      return;
    }
    if (state.salesActionRecommendationsLoading) {
      replaceSalesListHtmlIfChanged(dom.trackerSalesRecommendationList, '<div class="empty-state">?곸뾽 異붿쿇 由ъ뒪?몃? 遺덈윭?ㅻ뒗 以묒엯?덈떎.</div>');
      return;
    }
    if (state.salesActionRecommendationsError) {
      replaceSalesListHtmlIfChanged(dom.trackerSalesRecommendationList, `<div class="empty-state">${escapeHtml(state.salesActionRecommendationsError)}</div>`);
      return;
    }
    const items = visibleSalesActionRecommendations();
    const html = items.length
      ? items.map((item, index) => renderSalesActionRecommendationCard(item, index)).join("")
      : '<div class="empty-state">?꾩옱 ?몄텧???곸뾽 異붿쿇 由ъ뒪?멸? ?놁뒿?덈떎.</div>';
    dom.trackerSalesRecommendationList.className = "runtime-list sales-action-recommendation-list";
    replaceSalesListHtmlIfChanged(dom.trackerSalesRecommendationList, html);
    bindSalesActionRecommendationEvents(items);
  }

  function bindSalesActionRecommendationEvents(items) {
    if (!dom.trackerSalesRecommendationList) {
      return;
    }
    if (!salesActionPanelGuardBound && typeof dom.trackerSalesRecommendationList.addEventListener === "function") {
      salesActionPanelGuardBound = true;
      dom.trackerSalesRecommendationList.addEventListener("click", (event) => {
        const target = event?.target || null;
        const actionTarget = target && typeof target.closest === "function"
          : null;
        if (!actionTarget) {
          return;
        }
        event?.preventDefault?.();
        keepSalesRecommendationsTab();
      }, true);
    }
    for (const button of dom.trackerSalesRecommendationList.querySelectorAll("[data-sales-action-interest], [data-sales-action-done], [data-sales-action-hold]")) {
      bindSalesActionButtonOnce(button, "mark-seen", (event) => {
        containSalesActionClick(event);
        keepSalesRecommendationsTab();
        const index = Number(button.getAttribute("data-sales-action-interest") || button.getAttribute("data-sales-action-done") || button.getAttribute("data-sales-action-hold") || -1);
        const item = items[index];
        if (!item) {
          return;
        }
        markSalesRecommendationSeen(item);
        flash(button.hasAttribute("data-sales-action-hold") ? "異붿쿇??蹂대쪟?덉뒿?덈떎." : "異붿쿇???뺤씤 泥섎━?덉뒿?덈떎.");
      });
    }
    for (const button of dom.trackerSalesRecommendationList.querySelectorAll("[data-sales-action-claim]")) {
      bindSalesActionButtonOnce(button, "claim", (event) => {
        containSalesActionClick(event);
        keepSalesRecommendationsTab();
        const index = Number(button.getAttribute("data-sales-action-claim") || -1);
        const item = items[index];
        const claimPayload = item?.claim_payload || null;
        if (!claimPayload || !claimPayload.project_id) {
          flash("?대떦??諛곗젙???꾩슂???꾨줈?앺듃 ?뺣낫媛 ?놁뒿?덈떎.", "error");
          return;
        }
        markSalesRecommendationSeen(item);
        void claimSalesProject(claimPayload);
      });
    }
    for (const button of dom.trackerSalesRecommendationList.querySelectorAll("[data-sales-action-notice-view]")) {
      bindSalesActionButtonOnce(button, "notice-view", (event) => {
        containSalesActionClick(event);
        keepSalesRecommendationsTab();
        const index = Number(button.getAttribute("data-sales-action-notice-view") || -1);
        const item = items[index];
        const entryId = salesRecommendationEntryId(item);
        if (!entryId) {
          flash("怨듦퀬臾몄쓣 ?????덈뒗 ?몃옒而???ぉ ?뺣낫媛 ?놁뒿?덈떎.", "warn");
          return;
        }
        void api(`/api/tracker-entries/${encodeURIComponent(entryId)}/notice-file-open-external`, {
          method: "POST",
          timeoutMs: 45000,
        })
          .then((payload) => {
            if (!payload?.opened) {
              flash("怨듦퀬臾몄쓣 ?몃? 釉뚮씪?곗?濡??댁? 紐삵뻽?듬땲??", "warn");
            }
          })
          .catch((err) => {
            flash(err?.message || "怨듦퀬臾몄쓣 ?몃? 釉뚮씪?곗?濡??댁? 紐삵뻽?듬땲??", "warn");
          });
      });
    }
    dom.trackerSalesRecommendationRefreshButton?.addEventListener("click", () => {
      void loadSalesActionRecommendations({ force: true });
    }, { once: true });
  }

  async function loadSalesActionRecommendations({ silent = false, force = false } = {}) {
    if (!state.auth?.enabled || !state.auth?.authorized || !state.auth?.user) {
      state.salesActionRecommendations = [];
      state.salesActionRecommendationsError = "";
      state.salesActionRecommendationsLoading = false;
      renderSalesActionRecommendationsPanel();
      return;
    }
    const filterKey = JSON.stringify({
      q: String(state.trackerFilters?.q || ""),
      region: String(state.trackerFilters?.region || ""),
    });
    if (state.salesActionRecommendationsRequest && !force) {
      return state.salesActionRecommendationsRequest;
    }
    if (state.salesActionRecommendationsLoadedAt && state.salesActionRecommendationsFilterKey === filterKey && !force) {
      renderSalesActionRecommendationsPanel();
      return;
    }
    const request = (async () => {
      state.salesActionRecommendationsLoading = true;
      state.salesActionRecommendationsError = "";
      renderSalesActionRecommendationsPanel();
      try {
        const params = new URLSearchParams();
        if (state.trackerFilters?.q) params.set("q", state.trackerFilters.q);
        if (state.trackerFilters?.region) params.set("region", state.trackerFilters.region);
        if (force) params.set("refresh", "true");
        const path = `/api/sales-claims/action-recommendations${params.toString() ? `?${params.toString()}` : ""}`;
        const response = await api(path, {
          timeoutMs: 20000,
          cacheBust: false,
        });
        state.salesActionRecommendations = Array.isArray(response.items) ? response.items : [];
        state.salesActionRecommendationsError = "";
        state.salesActionRecommendationsLoadedAt = Date.now();
        state.salesActionRecommendationsFilterKey = filterKey;
      } catch (err) {
        state.salesActionRecommendations = [];
        state.salesActionRecommendationsError = err.message || "?곸뾽 異붿쿇 由ъ뒪?몃? 遺덈윭?ㅼ? 紐삵뻽?듬땲??";
        if (!silent) {
          flash(state.salesActionRecommendationsError, "error");
        }
      } finally {
        state.salesActionRecommendationsLoading = false;
        state.salesActionRecommendationsRequest = null;
        renderSalesActionRecommendationsPanel();
      }
    })();
    state.salesActionRecommendationsRequest = request;
    return request;
  }

  return {
    canShowSalesActionRecommendations,
    renderSalesActionRecommendationsPanel,
    loadSalesActionRecommendations,
  };
}
