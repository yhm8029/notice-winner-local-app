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
      return `${elapsed}일 전`;
    }
    return "오늘";
  }

  function formatRecommendationDate(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return "-";
    }
    const compact = raw.replace(/[^0-9]/g, "");
    if (compact.length >= 8) {
      return `${compact.slice(0, 4)}년 ${compact.slice(4, 6)}월 ${compact.slice(6, 8)}일`;
    }
    return raw;
  }

  function renderInternalScore(item) {
    if (!canShowInternalScore() || item?.internal_sort_score === null || item?.internal_sort_score === undefined) {
      return "";
    }
    return `<span class="sales-action-score">내부 정렬 점수 ${escapeHtml(String(item.internal_sort_score))}</span>`;
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
      demand_org_name: String(source.demand_org_name || "(수요기관 없음)"),
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

  function ensureSalesRecommendationRelatedState() {
    state.salesRecommendationRelatedPayloads = state.salesRecommendationRelatedPayloads && typeof state.salesRecommendationRelatedPayloads === "object"
      ? state.salesRecommendationRelatedPayloads
      : {};
    state.salesRecommendationRelatedItems = state.salesRecommendationRelatedItems && typeof state.salesRecommendationRelatedItems === "object"
      ? state.salesRecommendationRelatedItems
      : {};
    state.salesRecommendationRelatedErrors = state.salesRecommendationRelatedErrors && typeof state.salesRecommendationRelatedErrors === "object"
      ? state.salesRecommendationRelatedErrors
      : {};
    state.salesRecommendationRelatedAutoRecomputed = state.salesRecommendationRelatedAutoRecomputed && typeof state.salesRecommendationRelatedAutoRecomputed === "object"
      ? state.salesRecommendationRelatedAutoRecomputed
      : {};
    state.salesRecommendationRelatedPollState = state.salesRecommendationRelatedPollState && typeof state.salesRecommendationRelatedPollState === "object"
      ? state.salesRecommendationRelatedPollState
      : {};
  }

  function renderSalesRecommendationRelatedNoticeItem(item, projectId) {
    const noticeHref = String(item?.notice_detail_url || item?.notice_url || "").trim();
    const titleMarkup = noticeHref
      ? `<a class="runtime-project-related-link" href="${escapeHtml(noticeHref)}" target="_blank" rel="noreferrer">${escapeHtml(item?.project_name || "-")}</a>`
      : `<strong>${escapeHtml(item?.project_name || "-")}</strong>`;
    const viewButtonMarkup = noticeHref
      ? `<button class="ghost-button runtime-project-related-view-button" type="button" data-related-notice-project="${escapeHtml(projectId)}" data-related-notice-id="${escapeHtml(item?.id || "")}">연관 공고문</button>`
      : "";
    const adminMeta = state.uiMode === "admin"
      ? [
          item?.notice_stage ? `stage ${item.notice_stage}` : "",
          item?.sales_relevance ? `bucket ${item.sales_relevance}` : "",
          item?.exclusion_reason || "",
          ...(Array.isArray(item?.reason_codes) ? item.reason_codes : []),
        ].filter(Boolean)
      : [];
    return `
      <article class="runtime-project-related-item">
        <div class="runtime-project-related-main">
          <div>
            ${titleMarkup}
            <p>${escapeHtml(item?.issuer_name || "-")}</p>
          </div>
          ${viewButtonMarkup ? `<div class="runtime-project-related-actions">${viewButtonMarkup}</div>` : ""}
        </div>
        <div class="runtime-project-related-meta mono">
          <span>${escapeHtml(item?.announce_date || "-")}</span>
          <span>${escapeHtml(item?.bid_no || "-")} / ${escapeHtml(item?.bid_ord || "-")}</span>
          ${adminMeta.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}
        </div>
      </article>
    `;
  }

  function visibleSalesRecommendationRelatedItems(items) {
    const list = Array.isArray(items) ? items : [];
    if (state.uiMode === "admin") {
      return list;
    }
    const salesRelevant = list.filter((item) => String(item?.sales_relevance || "").trim() === "sales_relevant");
    if (salesRelevant.length) {
      return salesRelevant;
    }
    return list.filter((item) => !["excluded", "reference"].includes(String(item?.sales_relevance || "").trim()));
  }

  function renderSalesRecommendationRelatedItems(projectId, items, message = "") {
    const visibleItems = visibleSalesRecommendationRelatedItems(items);
    return `
      <div class="runtime-project-related">
        <div class="runtime-project-related-head">
          <strong>연관 공고</strong>
          <span class="mono">${escapeHtml(String(visibleItems.length))}건</span>
        </div>
        ${message ? `<div class="empty-state">${escapeHtml(message)}</div>` : ""}
        <div class="runtime-project-related-list">
          ${visibleItems.map((item) => renderSalesRecommendationRelatedNoticeItem(item, projectId)).join("")}
        </div>
      </div>
    `;
  }

  function renderSalesRecommendationRelatedPanel(projectId) {
    ensureSalesRecommendationRelatedState();
    if (!projectId || state.salesRecommendationRelatedOpenProjectId !== projectId) {
      return "";
    }
    const payload = state.salesRecommendationRelatedPayloads[projectId] || null;
    const items = state.salesRecommendationRelatedItems[projectId] || [];
    const errorMessage = state.salesRecommendationRelatedErrors[projectId] || "";
    const recomputeButton = `<button class="ghost-button sales-action-related-toggle" type="button" data-sales-action-related-recompute="${escapeHtml(projectId)}">연관공고 재계산</button>`;
    if (items.length) {
      const status = String(payload?.status || "").trim();
      const message = ["queued", "running", "pending"].includes(status)
        ? (payload?.message || "연관 공고를 검색하는 중입니다.")
        : "";
      return renderSalesRecommendationRelatedItems(projectId, items, message);
    }
    if (state.salesRecommendationRelatedLoadingProjectId === projectId) {
      return `<div class="runtime-project-related"><div class="empty-state">연관 공고를 확인하는 중입니다. ${recomputeButton}</div></div>`;
    }
    if (errorMessage && !payload && !items.length) {
      return `<div class="runtime-project-related"><div class="empty-state">연관 공고를 불러오지 못했습니다: ${escapeHtml(errorMessage)} ${recomputeButton}</div></div>`;
    }
    if (payload && ["queued", "running", "pending"].includes(String(payload.status || ""))) {
      return `<div class="runtime-project-related"><div class="empty-state">${escapeHtml(payload.message || "연관 공고 재계산이 진행 중입니다. 잠시 후 다시 열어주세요.")} ${recomputeButton}</div></div>`;
    }
    if (payload && payload.status === "missing") {
      return `<div class="runtime-project-related"><div class="empty-state">${escapeHtml(payload.message || "연관 공고 저장본이 아직 없습니다.")} ${recomputeButton}</div></div>`;
    }
    if (!items.length) {
      return `<div class="runtime-project-related"><div class="empty-state">같이 수집된 연관 공고가 없습니다. ${recomputeButton}</div></div>`;
    }
    return renderSalesRecommendationRelatedItems(projectId, items);
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
                <button class="ghost-button sales-action-related-toggle" type="button" data-sales-action-related-open="${escapeHtml(String(index))}">연관 공고 열기</button>
                <button class="ghost-button sales-action-notice-view" type="button" data-sales-action-notice-view="${escapeHtml(String(index))}">공고문 보기</button>
              </div>
            </div>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>발주처</strong> ${escapeHtml(entry.demand_org_name)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>연면적</strong> ${escapeHtml(entry.gross_area_scale)}</span>
              <span><strong>공사비</strong> ${escapeHtml(entry.construction_cost)}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>빌딩자동제어 추정금액(공사비의 1.5~2%)</strong> ${escapeHtml(entry.building_automation_estimated_amount)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>설계사무소</strong> ${escapeHtml(entry.architect_office)}</span>
              <span><strong>착공</strong> ${escapeHtml(entry.construction_start_date)}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>개찰예정일</strong> ${escapeHtml(formatRecommendationDate(entry.opening_scheduled_date))}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>담당</strong> ${escapeHtml(entry.demand_contact)}</span>
              <span><strong>현장</strong> ${escapeHtml(formatRecommendationSiteLocation(entry))}</span>
            </p>
            ${renderSalesRecommendationRelatedPanel(entry.project_id)}
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
        <p class="sales-recommendation-eyebrow">영업 추천 리스트</p>
        ${renderRecommendationProjectStatus(trackerEntry, index)}
        <div class="sales-action-labels">
          <strong>영업</strong>
          ${labelMarkup || `<span class="sales-action-label">${escapeHtml(item.primary_label || "추천")}</span>`}
          ${renderInternalScore(item)}
          <span class="sales-action-label">최근 공고 ${escapeHtml(item.latest_meaningful_notice_type || "-")}</span>
          <span class="sales-action-label">${escapeHtml(formatRecommendationElapsed(item))}</span>
        </div>
        <div class="sales-action-reasons">
          <strong>추천 이유</strong>
          ${reasonMarkup || `<p>${escapeHtml("추천 이유를 확인 중입니다.")}</p>`}
        </div>
        <div class="sales-action-next">
          <strong>추천 액션</strong>
          <p>${escapeHtml(actionText || "프로젝트 상태를 확인하세요.")}</p>
        </div>
        <div class="sales-action-buttons">
          <button class="ghost-button" type="button" data-sales-action-interest="${escapeHtml(String(index))}">관심 등록</button>
          <button class="ghost-button" type="button" data-sales-action-claim="${escapeHtml(String(index))}">담당자 배정</button>
          <button class="ghost-button" type="button" data-sales-action-done="${escapeHtml(String(index))}">확인 완료</button>
          <button class="ghost-button" type="button" data-sales-action-hold="${escapeHtml(String(index))}">보류</button>
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
      replaceSalesListHtmlIfChanged(dom.trackerSalesRecommendationList, '<div class="empty-state">영업 추천 리스트를 불러오는 중입니다.</div>');
      return;
    }
    if (state.salesActionRecommendationsError) {
      replaceSalesListHtmlIfChanged(dom.trackerSalesRecommendationList, `<div class="empty-state">${escapeHtml(state.salesActionRecommendationsError)}</div>`);
      return;
    }
    const items = visibleSalesActionRecommendations();
    const html = items.length
      ? items.map((item, index) => renderSalesActionRecommendationCard(item, index)).join("")
      : '<div class="empty-state">현재 노출할 영업 추천 리스트가 없습니다.</div>';
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
          ? target.closest("[data-sales-action-related-open], [data-sales-action-related-recompute], [data-sales-action-notice-view], [data-sales-action-interest], [data-sales-action-claim], [data-sales-action-done], [data-sales-action-hold]")
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
        flash(button.hasAttribute("data-sales-action-hold") ? "추천을 보류했습니다." : "추천을 확인 처리했습니다.");
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
          flash("담당자 배정에 필요한 프로젝트 정보가 없습니다.", "error");
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
          flash("공고문을 열 수 있는 트래커 항목 정보가 없습니다.", "warn");
          return;
        }
        const opened = appWindow?.open?.(`/api/tracker-entries/${encodeURIComponent(entryId)}/notice-file-view?embed=1`, "_blank");
        if (!opened) {
          flash("팝업이 차단되어 공고문을 열 수 없습니다.", "warn");
        }
      });
    }
    for (const button of dom.trackerSalesRecommendationList.querySelectorAll("[data-sales-action-related-open]")) {
      bindSalesActionButtonOnce(button, "related-open", (event) => {
        containSalesActionClick(event);
        keepSalesRecommendationsTab();
        const index = Number(button.getAttribute("data-sales-action-related-open") || -1);
        const item = items[index];
        const projectId = salesRecommendationProjectId(item);
        if (!projectId) {
          flash("연관 공고를 열 수 있는 프로젝트 정보가 없습니다.", "warn");
          return;
        }
        void toggleSalesRecommendationRelatedNotices(projectId);
      });
    }
    for (const button of dom.trackerSalesRecommendationList.querySelectorAll("[data-sales-action-related-recompute]")) {
      bindSalesActionButtonOnce(button, "related-recompute", (event) => {
        containSalesActionClick(event);
        keepSalesRecommendationsTab();
        const projectId = String(button.getAttribute("data-sales-action-related-recompute") || "").trim();
        void recomputeSalesRecommendationRelatedNotices(projectId);
      });
    }
    dom.trackerSalesRecommendationRefreshButton?.addEventListener("click", () => {
      void loadSalesActionRecommendations({ force: true });
    }, { once: true });
  }

  async function loadSalesRecommendationRelatedNotices(projectId, { cacheBust = false, refresh = false, quick = false } = {}) {
    const key = String(projectId || "").trim();
    if (!key) {
      return null;
    }
    keepSalesRecommendationsTab();
    state.salesRecommendationRelatedLoadingProjectId = key;
    state.salesRecommendationRelatedErrors[key] = "";
    renderSalesActionRecommendationsPanel();
    const request = (async () => {
      try {
        const params = new URLSearchParams();
        if (refresh) params.set("refresh", "true");
        if (quick) params.set("quick", "true");
        const query = params.toString() ? `?${params.toString()}` : "";
        const payload = await api(`/api/projects/${encodeURIComponent(key)}/related-notices${query}`, {
          timeoutMs: quick ? 8000 : 30000,
          cacheBust,
        });
        keepSalesRecommendationsTab();
        state.salesRecommendationRelatedPayloads[key] = payload && typeof payload === "object" ? payload : {};
        state.salesRecommendationRelatedItems[key] = Array.isArray(payload?.items) ? payload.items : [];
        return payload;
      } catch (err) {
        keepSalesRecommendationsTab();
        state.salesRecommendationRelatedPayloads[key] = null;
        state.salesRecommendationRelatedItems[key] = [];
        state.salesRecommendationRelatedErrors[key] = err.message || "연관 공고를 불러오지 못했습니다.";
        return null;
      } finally {
        keepSalesRecommendationsTab();
        if (state.salesRecommendationRelatedLoadingProjectId === key) {
          state.salesRecommendationRelatedLoadingProjectId = "";
        }
        state.salesRecommendationRelatedRequest = null;
        renderSalesActionRecommendationsPanel();
      }
    })();
    state.salesRecommendationRelatedRequest = request;
    return request;
  }

  function scheduleSalesRecommendationRelatedRefresh(projectId, { attempt = 1 } = {}) {
    const key = String(projectId || "").trim();
    const setTimeoutFn = appWindow?.setTimeout;
    if (!key || typeof setTimeoutFn !== "function") {
      return;
    }
    const nextAttempt = Number(attempt || 1);
    const delayMs = nextAttempt <= 1 ? 1500 : 2500;
    setTimeoutFn(async () => {
      if (state.salesRecommendationRelatedOpenProjectId === key && !state.salesRecommendationRelatedLoadingProjectId) {
        const payload = await loadSalesRecommendationRelatedNotices(key, { cacheBust: true, refresh: true });
        const status = String(payload?.status || "").trim();
        if (nextAttempt < 4 && ["queued", "running", "pending", "missing"].includes(status)) {
          scheduleSalesRecommendationRelatedRefresh(key, { attempt: nextAttempt + 1 });
        }
      }
    }, delayMs);
  }

  function clearSalesRecommendationRelatedProgressPoll(projectId) {
    ensureSalesRecommendationRelatedState();
    const key = String(projectId || "").trim();
    if (!key) {
      return;
    }
    const pollState = state.salesRecommendationRelatedPollState[key] || null;
    const clearTimeoutFn = appWindow?.clearTimeout;
    if (pollState?.timerId && typeof clearTimeoutFn === "function") {
      clearTimeoutFn(pollState.timerId);
    }
    delete state.salesRecommendationRelatedPollState[key];
  }

  function scheduleSalesRecommendationRelatedProgressPoll(projectId, { attempt = 1, generation = "" } = {}) {
    const key = String(projectId || "").trim();
    const setTimeoutFn = appWindow?.setTimeout;
    if (!key || typeof setTimeoutFn !== "function") {
      return;
    }
    ensureSalesRecommendationRelatedState();
    const maxAttempts = 120;
    const nextAttempt = Number(attempt || 1);
    const nextGeneration = generation || `${Date.now()}-${Math.random()}`;
    const previous = state.salesRecommendationRelatedPollState[key] || {};
    const clearTimeoutFn = appWindow?.clearTimeout;
    if (previous.timerId && typeof clearTimeoutFn === "function") {
      clearTimeoutFn(previous.timerId);
    }
    const timerId = setTimeoutFn(async () => {
      const current = state.salesRecommendationRelatedPollState?.[key] || {};
      if (current.generation !== nextGeneration || state.salesRecommendationRelatedOpenProjectId !== key) {
        return;
      }
      try {
        const payload = await api(`/api/projects/${encodeURIComponent(key)}/related-notices/progress`, {
          timeoutMs: 15000,
          cacheBust: true,
        });
        keepSalesRecommendationsTab();
        state.salesRecommendationRelatedPayloads[key] = payload && typeof payload === "object" ? payload : {};
        state.salesRecommendationRelatedItems[key] = Array.isArray(payload?.items) ? payload.items : [];
        const status = String(payload?.status || "").trim();
        renderSalesActionRecommendationsPanel();
        if (status === "ready") {
          clearSalesRecommendationRelatedProgressPoll(key);
          await loadSalesRecommendationRelatedNotices(key, { cacheBust: true, refresh: true });
          return;
        }
        if (["failed", "missing"].includes(status)) {
          clearSalesRecommendationRelatedProgressPoll(key);
          return;
        }
        if (nextAttempt < maxAttempts) {
          scheduleSalesRecommendationRelatedProgressPoll(key, { attempt: nextAttempt + 1, generation: nextGeneration });
          return;
        }
        clearSalesRecommendationRelatedProgressPoll(key);
      } catch (err) {
        if (nextAttempt < maxAttempts) {
          scheduleSalesRecommendationRelatedProgressPoll(key, { attempt: nextAttempt + 1, generation: nextGeneration });
          return;
        }
        state.salesRecommendationRelatedErrors[key] = err.message || "연관 공고 진행 상태를 확인하지 못했습니다.";
        clearSalesRecommendationRelatedProgressPoll(key);
        renderSalesActionRecommendationsPanel();
      }
    }, nextAttempt <= 1 ? 800 : 1200);
    state.salesRecommendationRelatedPollState[key] = {
      timerId,
      attempt: nextAttempt,
      generation: nextGeneration,
    };
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
        state.salesActionRecommendationsError = err.message || "영업 추천 리스트를 불러오지 못했습니다.";
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

  async function toggleSalesRecommendationRelatedNotices(projectId) {
    const key = String(projectId || "").trim();
    if (!key) {
      return;
    }
    ensureSalesRecommendationRelatedState();
    keepSalesRecommendationsTab();
    if (state.salesRecommendationRelatedOpenProjectId === key) {
      state.salesRecommendationRelatedOpenProjectId = "";
      clearSalesRecommendationRelatedProgressPoll(key);
      renderSalesActionRecommendationsPanel();
      return;
    }
    if (state.salesRecommendationRelatedOpenProjectId) {
      clearSalesRecommendationRelatedProgressPoll(state.salesRecommendationRelatedOpenProjectId);
    }
    state.salesRecommendationRelatedOpenProjectId = key;
    const existingPayload = state.salesRecommendationRelatedPayloads[key] || null;
    const existingStatus = String(existingPayload?.status || "").trim();
    if (existingPayload && !["missing", "queued", "running", "pending", "failed"].includes(existingStatus)) {
      renderSalesActionRecommendationsPanel();
      return;
    }
    renderSalesActionRecommendationsPanel();
    const request = loadSalesRecommendationRelatedNotices(key, { cacheBust: true, quick: true });
    void request.then(() => {
      if (state.salesRecommendationRelatedOpenProjectId === key) {
        void recomputeSalesRecommendationRelatedNotices(key);
      }
    });
    return request;
  }

  async function recomputeSalesRecommendationRelatedNotices(projectId) {
    const key = String(projectId || "").trim();
    if (!key) {
      return;
    }
    ensureSalesRecommendationRelatedState();
    keepSalesRecommendationsTab();
    if (
      state.salesRecommendationRelatedRecomputeRequest
      && state.salesRecommendationRelatedRecomputeProjectId === key
    ) {
      return state.salesRecommendationRelatedRecomputeRequest;
    }
    state.salesRecommendationRelatedLoadingProjectId = key;
    state.salesRecommendationRelatedRecomputeProjectId = key;
    state.salesRecommendationRelatedErrors[key] = "";
    renderSalesActionRecommendationsPanel();
    const request = (async () => {
      try {
        const payload = await api(`/api/projects/${encodeURIComponent(key)}/related-notices/recompute`, {
          method: "POST",
          timeoutMs: 30000,
          cacheBust: false,
        });
        keepSalesRecommendationsTab();
        const previousItems = Array.isArray(state.salesRecommendationRelatedItems[key])
          ? state.salesRecommendationRelatedItems[key]
          : [];
        const nextPayload = payload && typeof payload === "object" ? { ...payload } : {};
        if (previousItems.length && !Array.isArray(nextPayload.items)) {
          nextPayload.items = previousItems;
        }
        state.salesRecommendationRelatedPayloads[key] = nextPayload;
        state.salesRecommendationRelatedItems[key] = Array.isArray(nextPayload.items) ? nextPayload.items : previousItems;
        scheduleSalesRecommendationRelatedProgressPoll(key);
      } catch (err) {
        keepSalesRecommendationsTab();
        state.salesRecommendationRelatedErrors[key] = err.message || "연관 공고 재계산을 시작하지 못했습니다.";
      } finally {
        keepSalesRecommendationsTab();
        if (state.salesRecommendationRelatedLoadingProjectId === key) {
          state.salesRecommendationRelatedLoadingProjectId = "";
        }
        state.salesRecommendationRelatedRecomputeRequest = null;
        if (state.salesRecommendationRelatedRecomputeProjectId === key) {
          state.salesRecommendationRelatedRecomputeProjectId = "";
        }
        renderSalesActionRecommendationsPanel();
      }
    })();
    state.salesRecommendationRelatedRecomputeRequest = request;
    return request;
  }

  return {
    canShowSalesActionRecommendations,
    renderSalesActionRecommendationsPanel,
    loadSalesActionRecommendations,
  };
}
