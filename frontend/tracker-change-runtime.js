(function attachTrackerChangeRuntime(global) {
  const DEFAULT_TRACKER_CHANGE_FIELD_LABELS = {
    gross_area_scale: "연면적",
    construction_cost: "공사비",
    demand_contact: "담당 연락처",
  };

  function resolveFieldLabels(fieldLabels) {
    return fieldLabels && typeof fieldLabels === "object" && !Array.isArray(fieldLabels)
      ? fieldLabels
      : DEFAULT_TRACKER_CHANGE_FIELD_LABELS;
  }

  function getTrackerChangeFieldLabel(fieldName, fieldLabels = null) {
    const labels = resolveFieldLabels(fieldLabels);
    return labels[String(fieldName || "").trim()] || String(fieldName || "").trim() || "필드";
  }

  function formatTrackerChangeEventLabel(item, fieldLabels = null) {
    const fieldLabel = getTrackerChangeFieldLabel(item?.field_name, fieldLabels);
    const eventType = String(item?.event_type || "").trim();
    if (eventType === "related_notice_added") return "관련 공고 추가";
    if (eventType === "field_filled") return `${fieldLabel} 채워짐`;
    if (eventType === "field_updated_safe") return `${fieldLabel} 변경`;
    if (eventType === "field_conflict_detected") return `${fieldLabel} 검토 필요`;
    if (eventType === "manual_updated") return `${fieldLabel} 수동 수정`;
    return fieldLabel;
  }

  function buildTrackerChangeEventDescription(item) {
    const oldValue = String(item?.old_value || "").trim();
    const newValue = String(item?.new_value || "").trim();
    if (!oldValue && newValue) return newValue;
    if (oldValue && newValue) return `${oldValue} -> ${newValue}`;
    return newValue || oldValue || "-";
  }

  function formatTrackerChangeSourceLabel(sourceKind) {
    const value = String(sourceKind || "").trim();
    if (!value || value === "tracker_export") return "";
    return value;
  }

  function formatBackfillConflictResolutionLabel(resolution) {
    const value = String(resolution || "").trim();
    if (value === "kept_current") return "현재값 유지";
    if (value === "applied_manually") return "수동 반영";
    if (value === "applied_via_backfill") return "백필 반영";
    if (value === "dismissed") return "무시";
    return value || "-";
  }

  function buildBackfillConflictDescription(item) {
    const currentValue = String(item?.current_value || "").trim();
    const candidateValue = String(item?.candidate_value || "").trim();
    if (!currentValue && candidateValue) return candidateValue;
    if (currentValue && candidateValue) return `${currentValue} -> ${candidateValue}`;
    return candidateValue || currentValue || "-";
  }

  function buildTrackerChangeEventsMarkup(items, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
      formatTrackerChangeEventLabel: labelBuilder = formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription: descriptionBuilder = buildTrackerChangeEventDescription,
      formatTrackerChangeSourceLabel: sourceLabelBuilder = formatTrackerChangeSourceLabel,
    } = helpers;
    return (items || [])
      .map((item) => {
        const sourceLabel = sourceLabelBuilder(item?.source_kind);
        return `
      <article class="tracker-change-item${item.is_read ? " is-read" : ""}">
        <div class="tracker-change-item-head">
          <strong>${escapeHtml(labelBuilder(item))}</strong>
          <span class="mono">${escapeHtml(formatDate(item.created_at))}</span>
        </div>
        <p>${escapeHtml(item.project_name || item.entry_key || "-")}</p>
        <p class="tracker-change-item-body">${escapeHtml(descriptionBuilder(item))}</p>
        <div class="tracker-change-item-meta">
          <span class="mono">${sourceLabel ? escapeHtml(sourceLabel) : "&nbsp;"}</span>
          <button class="ghost-button" type="button" data-change-entry-id="${escapeHtml(item.tracker_entry_id)}">프로젝트 보기</button>
        </div>
      </article>
    `;
      })
      .join("");
  }

  function buildTrackerChangeBellPopoverMarkup(items, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
      formatTrackerChangeEventLabel: labelBuilder = formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription: descriptionBuilder = buildTrackerChangeEventDescription,
      formatTrackerChangeSourceLabel: sourceLabelBuilder = formatTrackerChangeSourceLabel,
    } = helpers;
    return `
      <div class="tracker-change-bell-popover-head">
        <div>
          <p class="kicker">최근 변경</p>
          <strong>확인 필요한 변경 ${Math.min((items || []).length, 6)}건</strong>
        </div>
      </div>
      <div class="tracker-change-bell-popover-list">
        ${(items || [])
          .slice(0, 6)
          .map((item) => `
            <article class="tracker-change-bell-popover-item${item.is_read ? " is-read" : ""}">
              <div class="tracker-change-bell-popover-item-head">
                <strong>${escapeHtml(labelBuilder(item))}</strong>
                <span class="mono">${escapeHtml(formatDate(item.created_at))}</span>
              </div>
              <p class="tracker-change-bell-popover-item-title">${escapeHtml(item.project_name || item.entry_key || "-")}</p>
              <p class="tracker-change-bell-popover-item-body">${escapeHtml(descriptionBuilder(item))}</p>
              <div class="tracker-change-bell-popover-item-meta">
                <span class="mono">${escapeHtml(sourceLabelBuilder(item.source_kind) || "")}</span>
                <button class="ghost-button" type="button" data-change-entry-id="${escapeHtml(item.tracker_entry_id)}">프로젝트 보기</button>
              </div>
            </article>
          `)
          .join("")}
      </div>
      <button class="ghost-button tracker-change-bell-popover-footer" type="button" data-tracker-change-open-panel="true">전체 변경 패널 보기</button>
    `;
  }

  function buildBackfillConflictsMarkup(items, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
      formatTrackerChangeEventLabel: labelBuilder = formatTrackerChangeEventLabel,
      buildBackfillConflictDescription: descriptionBuilder = buildBackfillConflictDescription,
    } = helpers;
    return (items || [])
      .map((item) => `
      <article class="tracker-change-item">
        <div class="tracker-change-item-head">
          <strong>${escapeHtml(labelBuilder({ field_name: item.field_name, event_type: "field_conflict_detected" }))}</strong>
          <span class="mono">${escapeHtml(formatDate(item.detected_at))}</span>
        </div>
        <p>${escapeHtml(item.project_name || item.entry_key || "-")}</p>
        <p class="tracker-change-item-body">${escapeHtml(descriptionBuilder(item))}</p>
        <div class="tracker-change-item-meta">
          <span class="mono">${escapeHtml(item.reason_code || "-")}</span>
          <div class="inline-button-row">
            <button class="ghost-button" type="button" data-backfill-entry-id="${escapeHtml(item.tracker_entry_id)}">프로젝트 보기</button>
            <button class="ghost-button" type="button" data-backfill-resolve-id="${escapeHtml(item.id)}" data-backfill-resolution="kept_current">유지</button>
            <button class="ghost-button" type="button" data-backfill-resolve-id="${escapeHtml(item.id)}" data-backfill-resolution="dismissed">무시</button>
          </div>
        </div>
      </article>
    `)
      .join("");
  }

  function buildSelectedEntryChangeEventsMarkup(items, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatDate = (value) => String(value || ""),
      formatTrackerChangeEventLabel: labelBuilder = formatTrackerChangeEventLabel,
      buildTrackerChangeEventDescription: descriptionBuilder = buildTrackerChangeEventDescription,
      formatTrackerChangeSourceLabel: sourceLabelBuilder = formatTrackerChangeSourceLabel,
    } = helpers;
    return (items || [])
      .map((item) => {
        const sourceLabel = sourceLabelBuilder(item?.source_kind);
        const reasonLabel = String(item?.reason_code || "").trim();
        const metaLabel = [sourceLabel, reasonLabel].filter(Boolean).join(" | ") || "-";
        return `
      <article class="audit-item">
        <div class="artifact-head">
          <strong>${escapeHtml(labelBuilder(item))}</strong>
          <span class="mono">${escapeHtml(formatDate(item.created_at))}</span>
        </div>
        <p>${escapeHtml(descriptionBuilder(item))}</p>
        <p class="mono">${escapeHtml(metaLabel)}</p>
      </article>
    `;
      })
      .join("");
  }

  global.SPMSTrackerChangeRuntime = {
    getTrackerChangeFieldLabel,
    formatTrackerChangeEventLabel,
    buildTrackerChangeEventDescription,
    formatTrackerChangeSourceLabel,
    buildTrackerChangeBellPopoverMarkup,
    formatBackfillConflictResolutionLabel,
    buildBackfillConflictDescription,
    buildTrackerChangeEventsMarkup,
    buildBackfillConflictsMarkup,
    buildSelectedEntryChangeEventsMarkup,
  };
})(window);
