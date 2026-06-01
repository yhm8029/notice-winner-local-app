(function attachSalesViewRuntime(global) {
  function buildUserSalesProjectFactsMarkup(snapshot, estimatedAmountText = "-", helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatBuildingAutomationEstimateValue = (_snapshot, fallback) => String(fallback || ""),
      formatKoreanDate = (value) => String(value || ""),
    } = helpers;
    const buildingAutomationEstimate = formatBuildingAutomationEstimateValue(snapshot, estimatedAmountText);
    if (!snapshot) {
      return `
      <p class="entry-metrics entry-metrics-single">
        <span><strong>빌딩자동제어 추정금액(공사비의 1.5~2%)</strong> ${escapeHtml(buildingAutomationEstimate)}</span>
      </p>
    `;
    }
    return `
    <p class="entry-metrics">
      <span><strong>연면적</strong> ${escapeHtml(snapshot.gross_area_scale || "-")}</span>
      <span><strong>공사비</strong> ${escapeHtml(snapshot.construction_cost || "-")}</span>
    </p>
    <p class="entry-metrics entry-metrics-single">
      <span><strong>빌딩자동제어 추정금액(공사비의 1.5~2%)</strong> ${escapeHtml(buildingAutomationEstimate)}</span>
    </p>
    <p class="entry-metrics">
      <span><strong>설계사무소</strong> ${escapeHtml(snapshot.architect_office || "-")}</span>
      <span><strong>개찰예정일</strong> ${escapeHtml(formatKoreanDate(snapshot.opening_scheduled_date || ""))}</span>
    </p>
    <p class="entry-metrics">
      <span><strong>담당</strong> ${escapeHtml(snapshot.demand_contact || "-")}</span>
      <span><strong>현장</strong> ${escapeHtml(snapshot.site_location_1 || "-")}</span>
    </p>
  `;
  }

  function buildSalesNoteTimelineMarkup(noteEntries, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatSalesNoteTextForDisplay = (value) => String(value || ""),
    } = helpers;
    if (!(noteEntries || []).length) {
      return '<div class="entry-sales-note-display is-empty">아직 등록된 영업현황이 없습니다.</div>';
    }
    return `
    <ol class="entry-sales-history">
      ${(noteEntries || []).map((item) => `
        <li class="entry-sales-history-item">
          <span class="entry-sales-history-text">${escapeHtml(formatSalesNoteTextForDisplay(item.text))}</span>
          ${item.timestamp ? `<span class="entry-sales-history-time mono">${escapeHtml(item.timestamp)}</span>` : ""}
        </li>
      `).join("")}
    </ol>
  `;
  }

  function shouldShowCurrentOwnerAssignedAt(claim) {
    return Boolean(
      claim?.current_owner_assigned_at
        && claim?.claimed_at
        && String(claim.current_owner_assigned_at).trim() !== String(claim.claimed_at).trim()
    );
  }

  function normalizeSalesClaimCardViewModel(payload = {}, { includeOwnerLabel = false } = {}) {
    const claim = payload.claim || {};
    const projectId = payload.projectId || String(claim.project_id || "").trim();
    const noteEntries = Array.isArray(payload.noteEntries) ? payload.noteEntries : [];
    const viewModel = {
      ...payload,
      claim,
      projectId,
      noteEntries,
      showAssignedAt: payload.showAssignedAt ?? shouldShowCurrentOwnerAssignedAt(claim),
    };
    if (includeOwnerLabel) {
      viewModel.latestNote = Object.prototype.hasOwnProperty.call(payload, "latestNote")
        ? payload.latestNote
        : (noteEntries.length ? noteEntries[noteEntries.length - 1] : null);
      viewModel.ownerLabel = Object.prototype.hasOwnProperty.call(payload, "ownerLabel")
        ? payload.ownerLabel
        : (claim.owner_display_name || claim.owner_email || "-");
    }
    return viewModel;
  }

  function buildUserOwnedSalesClaimCardViewModel(payload = {}) {
    return normalizeSalesClaimCardViewModel(payload);
  }

  function buildCompanySalesClaimCardViewModel(payload = {}) {
    return normalizeSalesClaimCardViewModel(payload, { includeOwnerLabel: true });
  }

  function buildSalesTransferOptionsMarkup(items, options = {}, helpers = {}) {
    const {
      loading = false,
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;
    const transferTargets = Array.isArray(items) ? items : [];
    const leadingOption = loading
      ? "사용자 불러오는 중..."
      : transferTargets.length
        ? "이관할 담당자 선택"
        : "이관 가능한 사용자가 없습니다";
    return [
      `<option value="">${escapeHtml(leadingOption)}</option>`,
      ...transferTargets.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.display_name || item.email)}${item.email ? ` (${escapeHtml(item.email)})` : ""}</option>`),
    ].join("");
  }

  function buildRawSalesNoteTimelineMarkup(noteEntries, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;
    if (!(noteEntries || []).length) {
      return '<div class="entry-sales-note-display is-empty">아직 등록된 영업현황이 없습니다.</div>';
    }
    return `
      <ol class="entry-sales-history">
        ${(noteEntries || []).map((item) => `
          <li class="entry-sales-history-item">
            <span class="entry-sales-history-text">${escapeHtml(item.text)}</span>
            ${item.timestamp ? `<span class="entry-sales-history-time mono">${escapeHtml(item.timestamp)}</span>` : ""}
          </li>
        `).join("")}
      </ol>
    `;
  }

  function buildAdminSalesClaimSectionViewModel(payload = {}) {
    const claim = payload.claim || null;
    const projectId = String(payload.projectId || claim?.project_id || "").trim();
    const claimStatus = String(payload.claimStatus || claim?.claim_status || "active").trim();
    const isClosed = payload.isClosed ?? Boolean(claim && claimStatus !== "active");
    const ownerMatch = Boolean(payload.ownerMatch);
    const canManage = Boolean(payload.canManage);
    const transferTargets = Array.isArray(payload.transferTargets) ? payload.transferTargets : [];
    const showAssignedAt = payload.showAssignedAt ?? shouldShowCurrentOwnerAssignedAt(claim);
    const ownerSummary = ownerMatch ? "나" : (claim?.owner_display_name || claim?.owner_email || "-");
    const statusLabel = claim
      ? (
        isClosed
          ? `${payload.statusText || claimStatus}${claim?.closed_at ? ` | ${payload.closedDateLabel || ""} 처리` : ""}`.trim()
          : ownerMatch
            ? "내가 담당 중"
            : `${claim?.owner_display_name || claim?.owner_email} 담당 중`
      )
      : "";
    return {
      ...payload,
      claim,
      projectId,
      claimStatus,
      isClosed,
      ownerMatch,
      canManage,
      transferTargets,
      showAssignedAt,
      ownerSummary,
      statusLabel,
    };
  }

  function buildAdminSalesClaimSectionMarkup(payload = {}, helpers = {}) {
    const {
      entry,
      claim,
      projectId,
      saving,
      noteDraft,
      noteEntries,
      claimStatus,
      isClosed,
      transferTargets,
      showAssignedAt,
      ownerMatch,
      canManage,
      ownerSummary,
      statusLabel,
      statusText,
      claimedAtLabel,
      currentOwnerAssignedAtLabel,
      closedAtLabel,
      organizationUsersLoading,
    } = payload;
    const {
      escapeHtml = (value) => String(value || ""),
      buildSalesTransferOptionsMarkup: buildOptions = buildSalesTransferOptionsMarkup,
      buildRawSalesNoteTimelineMarkup: buildTimeline = buildRawSalesNoteTimelineMarkup,
    } = helpers;

    if (!projectId) {
      return `
        <div class="entry-sales-box entry-sales-box-muted">
          <div class="entry-sales-head">
            <strong>영업현황</strong>
            <span class="mono">project_id 없음</span>
          </div>
          <p class="mono">이 항목은 프로젝트 기준 잠금을 걸 수 없어 영업 대상으로 지정할 수 없습니다.</p>
        </div>
      `;
    }

    if (!claim) {
      return `
        <div class="entry-sales-box">
          <div class="entry-sales-head">
            <strong>영업현황</strong>
            <button class="ghost-button entry-sales-claim-button" type="button" data-sales-claim="${escapeHtml(entry?.id)}" ${saving ? "disabled" : ""}>영업</button>
          </div>
          <p class="entry-sales-meta mono">아직 담당자가 지정되지 않았습니다.</p>
          <textarea class="entry-sales-note" rows="3" disabled placeholder="영업을 클릭하면 이곳에 현재 영업현황을 입력할 수 있습니다."></textarea>
        </div>
      `;
    }

    const statusBadge = `<span class="entry-sales-status-badge${isClosed ? " is-closed" : ""}">${escapeHtml(statusText || claimStatus)}</span>`;
    const transferControls = canManage && !isClosed
      ? `
        <div class="entry-sales-transfer">
          <label class="entry-sales-transfer-label" for="sales-transfer-${escapeHtml(projectId)}">담당 이관</label>
          <div class="entry-sales-transfer-controls">
            <select
              id="sales-transfer-${escapeHtml(projectId)}"
              class="entry-sales-transfer-select"
              data-sales-transfer-select="${escapeHtml(projectId)}"
              ${saving || organizationUsersLoading || !transferTargets.length ? "disabled" : ""}
            >
              ${buildOptions(transferTargets, { loading: organizationUsersLoading }, { escapeHtml })}
            </select>
            <button class="ghost-button" type="button" data-sales-transfer="${escapeHtml(projectId)}" ${saving || organizationUsersLoading || !transferTargets.length ? "disabled" : ""}>이관</button>
          </div>
        </div>
      `
      : "";

    return `
      <div class="entry-sales-box${ownerMatch ? " is-owner" : " is-locked"}${isClosed ? " is-closed" : ""}">
        <div class="entry-sales-head">
          <strong>영업현황</strong>
          ${isClosed
            ? statusBadge
            : ownerMatch
              ? `<span class="mono">영업 시작 ${escapeHtml(claimedAtLabel || "-")}</span>`
              : `<button class="ghost-button entry-sales-claim-button" type="button" disabled>영업 진행 중</button>`}
        </div>
        <div class="entry-sales-meta-group">
          <p class="entry-sales-meta mono">${escapeHtml(statusLabel || "-")}</p>
          <p class="entry-sales-meta mono">현재 담당 ${escapeHtml(ownerSummary || "-")}${claim?.owner_email ? ` · ${escapeHtml(claim.owner_email)}` : ""}</p>
          <p class="entry-sales-meta mono">영업 시작 ${escapeHtml(claimedAtLabel || "-")}</p>
          ${showAssignedAt ? `<p class="entry-sales-meta mono">현재 담당 시작 ${escapeHtml(currentOwnerAssignedAtLabel || "-")}</p>` : ""}
          ${isClosed && closedAtLabel ? `<p class="entry-sales-meta mono">종결 일자 ${escapeHtml(closedAtLabel)}</p>` : ""}
        </div>
        ${buildTimeline(noteEntries, { escapeHtml })}
        ${ownerMatch && !isClosed ? `
          <textarea class="entry-sales-note" rows="3" data-sales-note="${escapeHtml(projectId)}" placeholder="현재 영업 진행 현황을 입력하세요.">${escapeHtml(noteDraft || "")}</textarea>
        ` : ""}
        ${transferControls}
        <div class="entry-sales-actions">
          ${ownerMatch && !isClosed ? `
            <button class="primary-button entry-sales-save-button" type="button" data-sales-note-save="${escapeHtml(projectId)}" ${saving ? "disabled" : ""}>저장</button>
          ` : ""}
          ${canManage && !isClosed ? `
            <button class="ghost-button" type="button" data-sales-close="${escapeHtml(projectId)}" data-sales-close-outcome="won" ${saving ? "disabled" : ""}>계약 완료</button>
            <button class="ghost-button" type="button" data-sales-close="${escapeHtml(projectId)}" data-sales-close-outcome="lost" ${saving ? "disabled" : ""}>영업 종료</button>
          ` : ""}
          ${canManage ? `
            <button class="ghost-button entry-sales-release-button" type="button" data-sales-release="${escapeHtml(projectId)}" ${saving ? "disabled" : ""}>해제</button>
          ` : ""}
        </div>
      </div>
    `;
  }

  function buildUserOwnedSalesClaimCardMarkup(payload, helpers = {}) {
    const normalizedPayload = normalizeSalesClaimCardViewModel(payload);
    const {
      claim,
      index,
      projectId,
      saving,
      noteDraft,
      noteEntries,
      snapshot,
      transferTargets,
      organizationUsersLoading,
      showAssignedAt,
    } = normalizedPayload;
    const {
      escapeHtml = (value) => String(value || ""),
      salesClaimStatusLabel = (value) => String(value || ""),
      renderUserSalesProjectFacts = () => "",
      formatSalesDateLabel = (value) => String(value || ""),
      renderSalesNoteTimelineMarkup = () => "",
    } = helpers;
    return `
    <article class="user-sales-item user-sales-item-owned">
      <div class="user-sales-item-head">
        <strong>${escapeHtml(String((index || 0) + 1))}. ${escapeHtml(claim?.project_name || "-")}</strong>
        <span class="entry-sales-status-badge">${escapeHtml(salesClaimStatusLabel(claim?.claim_status))}</span>
      </div>
      ${renderUserSalesProjectFacts(snapshot, claim?.estimated_amount_text || "-")}
      <p class="mono">영업 시작 ${escapeHtml(formatSalesDateLabel(claim?.claimed_at))}</p>
      ${showAssignedAt ? `<p class="mono">현재 담당 시작 ${escapeHtml(formatSalesDateLabel(claim?.current_owner_assigned_at))}</p>` : ""}
      ${renderSalesNoteTimelineMarkup(noteEntries)}
      <textarea
        class="entry-sales-note"
        rows="3"
        data-user-sales-note="${escapeHtml(projectId)}"
        placeholder="현재 영업 진행 현황을 입력하세요."
      >${escapeHtml(noteDraft)}</textarea>
      <div class="entry-sales-transfer">
        <label class="entry-sales-transfer-label" for="user-sales-transfer-${escapeHtml(projectId)}">담당 이관</label>
        <div class="entry-sales-transfer-controls">
          <select
            id="user-sales-transfer-${escapeHtml(projectId)}"
            class="entry-sales-transfer-select"
            data-user-sales-transfer-select="${escapeHtml(projectId)}"
            ${saving || organizationUsersLoading || !(transferTargets || []).length ? "disabled" : ""}
          >
            <option value="">${organizationUsersLoading ? "사용자 불러오는 중..." : (transferTargets || []).length ? "이관할 담당자 선택" : "이관 가능한 사용자가 없습니다"}</option>
            ${(transferTargets || []).map((item) => `
              <option value="${escapeHtml(item.id)}">${escapeHtml(item.display_name || item.email)}${item.email ? ` (${escapeHtml(item.email)})` : ""}</option>
            `).join("")}
          </select>
          <button
            class="ghost-button"
            type="button"
            data-user-sales-transfer="${escapeHtml(projectId)}"
            ${saving || organizationUsersLoading || !(transferTargets || []).length ? "disabled" : ""}
          >
            이관
          </button>
        </div>
      </div>
      <div class="entry-sales-actions">
        <button
          class="primary-button entry-sales-save-button"
          type="button"
          data-user-sales-note-save="${escapeHtml(projectId)}"
          ${saving ? "disabled" : ""}
        >
          저장
        </button>
        <button
          class="ghost-button"
          type="button"
          data-user-sales-close="${escapeHtml(projectId)}"
          data-user-sales-close-outcome="won"
          ${saving ? "disabled" : ""}
        >
          계약 완료
        </button>
        <button
          class="ghost-button"
          type="button"
          data-user-sales-close="${escapeHtml(projectId)}"
          data-user-sales-close-outcome="lost"
          ${saving ? "disabled" : ""}
        >
          영업 종료
        </button>
        <button
          class="ghost-button entry-sales-release-button"
          type="button"
          data-user-sales-release="${escapeHtml(projectId)}"
          ${saving ? "disabled" : ""}
        >
          해제
        </button>
      </div>
    </article>
  `;
  }

  function buildCompanySalesClaimCardMarkup(payload, helpers = {}) {
    const normalizedPayload = normalizeSalesClaimCardViewModel(payload, { includeOwnerLabel: true });
    const {
      claim,
      index,
      latestNote,
      ownerLabel,
      snapshot,
      showAssignedAt,
    } = normalizedPayload;
    const {
      escapeHtml = (value) => String(value || ""),
      salesClaimStatusLabel = (value) => String(value || ""),
      renderUserSalesProjectFacts = () => "",
      formatSalesDateLabel = (value) => String(value || ""),
      truncate = (value) => String(value || ""),
      formatSalesNoteTextForDisplay = (value) => String(value || ""),
    } = helpers;
    return `
    <article class="user-sales-item user-sales-item-company">
      <div class="user-sales-item-head">
        <strong>${escapeHtml(String((index || 0) + 1))}. ${escapeHtml(claim?.project_name || "-")}</strong>
        <span class="entry-sales-status-badge">${escapeHtml(salesClaimStatusLabel(claim?.claim_status))}</span>
      </div>
      ${renderUserSalesProjectFacts(snapshot, claim?.estimated_amount_text || "-")}
      <p class="mono">${escapeHtml(ownerLabel)}${claim?.owner_email ? ` · ${escapeHtml(claim.owner_email)}` : ""}</p>
      <p class="mono">영업 시작 ${escapeHtml(formatSalesDateLabel(claim?.claimed_at))}</p>
      ${showAssignedAt ? `<p class="mono">현재 담당 시작 ${escapeHtml(formatSalesDateLabel(claim?.current_owner_assigned_at))}</p>` : ""}
      <p>${escapeHtml(latestNote ? `${latestNote.timestamp ? `${latestNote.timestamp} · ` : ""}${truncate(formatSalesNoteTextForDisplay(latestNote.text), 140)}` : "최근 영업현황이 없습니다.")}</p>
    </article>
  `;
  }

  function buildUserTrackerClaimSectionMarkup(payload, helpers = {}) {
    const { entry, projectId, claim, saving } = payload || {};
    const { escapeHtml = (value) => String(value || "") } = helpers;
    if (projectId && !claim) {
      return `
      <div class="entry-sales-actions entry-sales-actions-inline">
        <button
          class="ghost-button entry-sales-claim-button"
          type="button"
          data-sales-claim="${escapeHtml(entry?.id)}"
          ${saving ? "disabled" : ""}
        >
          영업
        </button>
      </div>
    `;
    }
    return "";
  }

  function buildSalesClaimEstimateLabel(claim, helpers = {}) {
    const {
      getTrackerProjectSnapshot = () => null,
      formatBuildingAutomationEstimateValue = (_snapshot, fallback) => String(fallback || ""),
    } = helpers;
    const snapshot = getTrackerProjectSnapshot(claim?.project_id);
    return `빌딩자동제어 추정금액(공사비의 1.5~2%) ${formatBuildingAutomationEstimateValue(
      snapshot,
      claim?.estimated_amount_text || "",
    )}`;
  }

  function buildSelectedEntryAuditMarkup(items, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
    } = helpers;
    return (items || [])
      .map((item) => `
        <article class="audit-item">
          <div class="artifact-head">
            <strong>${escapeHtml(item.field_name)}</strong>
            <span class="mono">#${escapeHtml(item.id)}</span>
          </div>
          <p>${escapeHtml(item.old_value)} -> ${escapeHtml(item.new_value)}</p>
          <p class="mono">${escapeHtml(item.actor_label || "-")} | ${escapeHtml(formatDate(item.created_at))}</p>
        </article>
      `)
      .join("");
  }

  function buildClosedSalesArchiveSectionMarkup(payload = {}, helpers = {}) {
    const {
      title = "",
      claims = [],
      showContractAmount = false,
      currentYear: payloadCurrentYear,
    } = payload;
    const {
      escapeHtml = (value) => String(value ?? ""),
      getSalesYearMonthBucket = () => null,
      formatSalesDateLabel = (value) => String(value ?? ""),
      getLatestSalesNoteItem = () => null,
      formatSalesNoteTextForDisplay = (value) => String(value ?? ""),
      truncate = (value) => String(value ?? ""),
      salesClaimStatusLabel = (value) => String(value ?? ""),
      extractContractAmountTextFromSalesNote = () => "",
      formatContractAmountDisplay = (value) => String(value ?? ""),
      formatSalesClaimEstimateLabel = (claim) => String(claim?.project_name || ""),
    } = helpers;

    const normalizeYear = (value) => {
      const year = Number(value);
      return Number.isFinite(year) ? year : null;
    };
    const currentYear = normalizeYear(payloadCurrentYear) ?? 0;
    const yearGroups = new Map();
    const eligibleClaims = [];
    for (const claim of Array.isArray(claims) ? claims : []) {
      const bucket = getSalesYearMonthBucket(claim.closed_at || claim.updated_at || claim.created_at);
      if (!bucket || !bucket.year || bucket.year > currentYear) {
        continue;
      }
      eligibleClaims.push(claim);
      if (!yearGroups.has(bucket.year)) {
        yearGroups.set(bucket.year, new Map());
      }
      const monthGroups = yearGroups.get(bucket.year);
      if (!monthGroups.has(bucket.month)) {
        monthGroups.set(bucket.month, []);
      }
      monthGroups.get(bucket.month).push(claim);
    }

    const itemsMarkup = yearGroups.size
      ? [...yearGroups.entries()]
        .sort((left, right) => left[0] - right[0])
        .map(([year, monthGroups]) => {
          const monthMarkup = [...monthGroups.entries()]
            .sort((left, right) => left[0] - right[0])
            .map(([month, monthClaims]) => {
              const claimsMarkup = monthClaims
                .map((claim, index) => {
                  const contractAmountText = showContractAmount
                    ? formatContractAmountDisplay(extractContractAmountTextFromSalesNote(claim.sales_note))
                    : "";
                  const closedDateLabel = formatSalesDateLabel(claim.closed_at || claim.updated_at || claim.created_at);
                  const ownerLabel = claim.owner_display_name || claim.owner_email || "-";
                  const latestNote = getLatestSalesNoteItem(claim.sales_note, claim.claimed_at);
                  const latestNoteLabel = latestNote
                    ? `${latestNote.timestamp ? `${latestNote.timestamp} · ` : ""}${truncate(formatSalesNoteTextForDisplay(latestNote.text), 120)}`
                    : "";
                  return `
                  <article class="sales-summary-archive-item">
                    <div class="sales-summary-archive-head">
                      <strong>${escapeHtml(String(index + 1))}. ${escapeHtml(claim.project_name || "-")}</strong>
                      <span class="entry-sales-status-badge${showContractAmount ? " is-closed" : ""}">${escapeHtml(salesClaimStatusLabel(claim.claim_status))}</span>
                    </div>
                    <p class="mono">${escapeHtml(ownerLabel)} | ${escapeHtml(closedDateLabel)} 처리</p>
                    <p class="mono">${showContractAmount ? `계약금액 ${escapeHtml(contractAmountText || "-")}` : escapeHtml(formatSalesClaimEstimateLabel(claim))}</p>
                    ${latestNoteLabel ? `<p>${escapeHtml(latestNoteLabel)}</p>` : ""}
                  </article>
                `;
                })
                .join("");
              return `
              <section class="sales-summary-archive-month">
                <div class="sales-summary-archive-month-head">
                  <strong>${escapeHtml(`${month}월`)}</strong>
                  <span class="mono">${escapeHtml(String(monthClaims.length))}건</span>
                </div>
                <div class="sales-summary-archive-list">${claimsMarkup}</div>
              </section>
            `;
            })
            .join("");
          return `
          <section class="sales-summary-archive-year">
            <div class="sales-summary-archive-year-head">
              <strong>${escapeHtml(`${year}년`)}</strong>
              <span class="mono">${escapeHtml(String(
                [...monthGroups.values()].reduce((count, monthClaims) => count + monthClaims.length, 0)
              ))}건</span>
            </div>
            <div class="sales-summary-archive-year-list">${monthMarkup}</div>
          </section>
        `;
        })
        .join("")
      : `<div class="empty-state">${escapeHtml(`${title}된 영업 프로젝트가 없습니다.`)}</div>`;

    return `
    <section class="sales-summary-archive-group">
      <div class="sales-summary-archive-group-head">
        <strong>${escapeHtml(title)}</strong>
        <span class="mono">${escapeHtml(String(eligibleClaims.length))}건</span>
      </div>
      <div class="sales-summary-archive-list">${itemsMarkup}</div>
    </section>
  `;
  }

  function buildSalesSummaryPanelMarkup(viewModel = {}, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    if (viewModel.uiMode !== "admin") {
      return '<div class="empty-state">관리자 모드에서 영업 현황 집계를 확인할 수 있습니다.</div>';
    }
    if (viewModel.salesSummaryLoading || viewModel.salesClosedLoading) {
      return '<div class="empty-state">영업 집계를 불러오는 중입니다.</div>';
    }
    if (viewModel.salesSummaryError || viewModel.salesClosedError) {
      return `<div class="empty-state">${escapeHtml(viewModel.salesSummaryError || viewModel.salesClosedError)}</div>`;
    }
    const activeProjectCount = (viewModel.salesSummaryByUser || []).reduce(
      (count, item) => count + Number(item?.active_project_count || 0),
      0,
    );
    const closedClaimCount = (viewModel.salesClosedClaims || []).length;
    return `
      <section class="sales-summary-section">
        <div class="sales-summary-section-head">
          <strong>진행 중 영업</strong>
          <span class="mono">${escapeHtml(String(activeProjectCount))}건</span>
        </div>
        <div class="sales-summary-section-body">${viewModel.activeMarkup || ""}</div>
      </section>
      <section class="sales-summary-section">
        <div class="sales-summary-section-head">
          <strong>종료/완료 정리</strong>
          <span class="mono">${escapeHtml(String(closedClaimCount))}건</span>
        </div>
        <div class="sales-summary-section-body sales-summary-archive-stack">${viewModel.closedMarkup || ""}</div>
      </section>
    `;
  }

  global.SPMSSalesViewRuntime = {
    buildUserSalesProjectFactsMarkup,
    buildSalesNoteTimelineMarkup,
    shouldShowCurrentOwnerAssignedAt,
    buildUserOwnedSalesClaimCardViewModel,
    buildCompanySalesClaimCardViewModel,
    normalizeSalesClaimCardViewModel,
    buildSalesTransferOptionsMarkup,
    buildRawSalesNoteTimelineMarkup,
    buildAdminSalesClaimSectionViewModel,
    buildAdminSalesClaimSectionMarkup,
    buildSalesClaimEstimateLabel,
    buildUserOwnedSalesClaimCardMarkup,
    buildCompanySalesClaimCardMarkup,
    buildUserTrackerClaimSectionMarkup,
    buildSelectedEntryAuditMarkup,
    buildClosedSalesArchiveSectionMarkup,
    buildSalesSummaryPanelMarkup,
  };
})(window);
