(function attachSPMSTrackerEntryRuntime(globalObject) {
  function toTrackerEntrySummary(entry) {
    const summary = {
      id: entry.id,
      source_run_id: entry.source_run_id || null,
      source_tracker_run_id: entry.source_tracker_run_id || null,
      project_id: entry.project_id || null,
      source_bid_no: entry.source_bid_no || "",
      source_bid_ord: entry.source_bid_ord || "",
      entry_key: entry.entry_key || "",
      row_no: Number(entry.row_no || 0),
      project_name: entry.project_name || "",
      gross_area_scale: entry.gross_area_scale || "",
      construction_cost: entry.construction_cost || "",
      demand_org_name: entry.demand_org_name || "",
      demand_contact: entry.demand_contact || "",
      client_location: entry.client_location || "",
      site_location_1: entry.site_location_1 || "",
      site_location_2: entry.site_location_2 || "",
      architect_office: entry.architect_office || "",
      opening_scheduled_date: entry.opening_scheduled_date || "",
      construction_start_date: entry.construction_start_date || "",
      contract_date: entry.contract_date || "",
      construction_duration_days: entry.construction_duration_days || "",
      completion_expected_date_explicit: entry.completion_expected_date_explicit || "",
      completion_expected_date_computed: entry.completion_expected_date_computed || "",
      last_checked_date: entry.last_checked_date || "",
      progress_note: entry.progress_note || "",
      notice_date: entry.notice_date || "",
      manager_name: entry.manager_name || "",
      building_automation_estimated_amount: entry.building_automation_estimated_amount || "",
      overridden_fields: Array.isArray(entry.overridden_fields) ? entry.overridden_fields : [],
    };
    if ("gross_area_scale_source" in entry) {
      summary.gross_area_scale_source = entry.gross_area_scale_source || "";
    }
    if ("demand_contact_source" in entry) {
      summary.demand_contact_source = entry.demand_contact_source || "";
    }
    if ("architect_office_source" in entry) {
      summary.architect_office_source = entry.architect_office_source || "";
    }
    if ("source_type" in entry) {
      summary.source_type = entry.source_type || "";
    }
    if ("reason_code" in entry) {
      summary.reason_code = entry.reason_code || "";
    }
    if ("evidence_source" in entry) {
      summary.evidence_source = entry.evidence_source || "";
    }
    if ("field_diagnostics" in entry) {
      summary.field_diagnostics = Array.isArray(entry.field_diagnostics) ? entry.field_diagnostics : [];
    }
    return summary;
  }

  function buildTrackerEntrySummaryDetail(entry) {
    return {
      ...toTrackerEntrySummary(entry),
      _summary_only: true,
    };
  }

  function buildTrackerBoardEmptyStateView({
    emptyHtml = '<div class="empty-state">트래커 행을 불러오면 여기에 표로 표시됩니다.</div>',
  } = {}) {
    return {
      html: emptyHtml,
      className: "tracker-board-content empty-state",
    };
  }

  function isTrackerBoardBlankValue(value) {
    return !String(value ?? "").trim();
  }

  function normalizeBlankPriorityFields(blankPriorityFields = []) {
    if (blankPriorityFields instanceof Set) {
      return blankPriorityFields;
    }
    if (Array.isArray(blankPriorityFields)) {
      return new Set(blankPriorityFields.map((value) => String(value || "").trim()).filter(Boolean));
    }
    return new Set();
  }

  function normalizeTextareaFields(textareaFields = []) {
    if (textareaFields instanceof Set) {
      return textareaFields;
    }
    if (Array.isArray(textareaFields)) {
      return new Set(textareaFields.map((value) => String(value || "").trim()).filter(Boolean));
    }
    return new Set();
  }

  function buildSortedTrackerBoardEntries(entries, { fieldName = "", blankPriorityFields = [] } = {}, helpers = {}) {
    const sourceEntries = Array.isArray(entries) ? entries : [];
    const priorityFields = normalizeBlankPriorityFields(blankPriorityFields);
    if (!priorityFields.has(fieldName)) {
      return sourceEntries;
    }
    const blankValueChecker = typeof helpers.isTrackerBoardBlankValue === "function"
      ? helpers.isTrackerBoardBlankValue
      : isTrackerBoardBlankValue;
    return sourceEntries
      .map((entry, index) => ({ entry, index }))
      .sort((left, right) => {
        const leftBlank = blankValueChecker(left.entry?.[fieldName]);
        const rightBlank = blankValueChecker(right.entry?.[fieldName]);
        if (leftBlank !== rightBlank) {
          return leftBlank ? -1 : 1;
        }
        return left.index - right.index;
      })
      .map(({ entry }) => entry);
  }

  function buildTrackerBoardHeaderCell(column, { currentSortField = "", escapeHtml = (value) => String(value ?? "") } = {}) {
    const key = String(column?.key || "");
    const label = String(column?.label || "");
    if (!key || key === "display_no") {
      return `<th>${escapeHtml(label)}</th>`;
    }
    const activeClass = key === currentSortField ? " is-active" : "";
    return `
      <th class="tracker-board-header${activeClass}">
        <button type="button" data-board-sort-field="${escapeHtml(key)}">
          ${escapeHtml(label)}
          <span class="tracker-board-sort-meta mono">${key === currentSortField ? "빈 값 우선" : "클릭 시 빈 값 우선"}</span>
        </button>
      </th>
    `;
  }

  function buildTrackerBoardCellMarkup({ entry, column, displayNo }, { escapeHtml = (value) => String(value ?? "") } = {}) {
    if (column.key === "display_no") {
      return `<td>${displayNo}</td>`;
    }
    const value = entry?.[column.key] || "";
    if (!column.editable) {
      return `<td>${escapeHtml(value || "-")}</td>`;
    }
    const overrideClass = Array.isArray(entry?.overridden_fields) && entry.overridden_fields.includes(column.key) ? " is-overridden" : "";
    return `
      <td class="tracker-board-cell${overrideClass}">
        <button
          class="tracker-board-edit-trigger"
          type="button"
          data-board-edit-trigger="true"
          data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
          data-board-edit-field="${escapeHtml(column.key)}"
        >
          <span class="tracker-board-cell-value">${escapeHtml(value || "-")}</span>
          <span class="tracker-board-cell-meta mono">${overrideClass ? "override" : "클릭해 수정"}</span>
        </button>
      </td>
    `;
  }

  function buildTrackerBoardEditingCellMarkup(
    { entry, fieldName, label, value, saving, errorMessage },
    { escapeHtml = (item) => String(item ?? ""), textareaFields = new Set() } = {},
  ) {
    const textareaFieldSet = normalizeTextareaFields(textareaFields);
    const textarea = textareaFieldSet.has(fieldName);
    const inputMarkup = textarea
      ? `<textarea
          class="tracker-board-edit-input tracker-board-edit-input-textarea"
          rows="${fieldName === "progress_note" ? "4" : "3"}"
          data-board-edit-input="true"
          data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
          data-board-edit-field="${escapeHtml(fieldName)}"
          data-board-edit-active="true"
          ${saving ? "disabled" : ""}
        >${escapeHtml(value || "")}</textarea>`
      : `<input
          class="tracker-board-edit-input"
          type="text"
          value="${escapeHtml(value || "")}"
          data-board-edit-input="true"
          data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
          data-board-edit-field="${escapeHtml(fieldName)}"
          data-board-edit-active="true"
          ${saving ? "disabled" : ""}
        />`;
    return `
      <td class="tracker-board-cell tracker-board-cell-editing">
        <form
          class="tracker-board-edit-form"
          data-board-edit-form="true"
          data-board-edit-entry-id="${escapeHtml(entry?.id || "")}"
          data-board-edit-field="${escapeHtml(fieldName)}"
        >
          <span class="tracker-board-edit-label">${escapeHtml(label)}</span>
          ${inputMarkup}
          <div class="tracker-board-edit-actions">
            <button class="primary-button tracker-board-edit-save" type="submit" ${saving ? "disabled" : ""}>저장</button>
            <button class="ghost-button tracker-board-edit-cancel" type="button" data-board-edit-cancel="true" ${saving ? "disabled" : ""}>취소</button>
          </div>
          <p class="tracker-board-edit-hint mono">${textarea ? "Enter 저장 · Shift+Enter 줄바꿈 · Esc 취소" : "Enter 저장 · Esc 취소"}</p>
          ${errorMessage ? `<p class="tracker-board-edit-error">${escapeHtml(errorMessage)}</p>` : ""}
        </form>
      </td>
    `;
  }

  function buildTrackerBoardMarkup(entries, options = {}, helpers = {}) {
    const {
      columns = [],
      currentSortField = "",
      trackerBoardEdit = null,
      textareaFields = new Set(),
      blankPriorityFields = [],
      page = 1,
      pageSize = 20,
      selectedEntryId = "",
    } = options;
    const escapeHtml = typeof helpers.escapeHtml === "function"
      ? helpers.escapeHtml
      : (value) => String(value ?? "");
    const boardEntries = buildSortedTrackerBoardEntries(entries, {
      fieldName: currentSortField,
      blankPriorityFields,
    }, {
      isTrackerBoardBlankValue,
    });
    if (!boardEntries.length) {
      return "";
    }
    return `
      <table class="tracker-board-table">
        <thead>
          <tr>
            ${columns.map((column) => buildTrackerBoardHeaderCell(column, {
              currentSortField,
              escapeHtml,
            })).join("")}
          </tr>
        </thead>
        <tbody>
          ${boardEntries
            .map((entry, index) => {
              const displayNo = (page - 1) * pageSize + index + 1;
              const cells = columns.map((column) => {
                if (trackerBoardEdit?.entryId === entry.id && trackerBoardEdit?.fieldName === column.key) {
                  return buildTrackerBoardEditingCellMarkup({
                    entry,
                    fieldName: column.key,
                    label: column.label,
                    value: trackerBoardEdit.draftValue,
                    saving: trackerBoardEdit.saving,
                    errorMessage: trackerBoardEdit.errorMessage,
                  }, {
                    escapeHtml,
                    textareaFields,
                  });
                }
                return buildTrackerBoardCellMarkup({
                  entry,
                  column,
                  displayNo,
                }, {
                  escapeHtml,
                });
              }).join("");
              return `
                <tr data-board-entry-id="${escapeHtml(entry.id)}" class="${entry.id === selectedEntryId ? "is-selected" : ""}">
                  ${cells}
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    `;
  }

  function buildTrackerSiteLocationText(siteRegion, siteCity) {
    const region = String(siteRegion || "").trim();
    const city = String(siteCity || "").trim();
    if (region && city) {
      if (region.includes(city)) {
        return region;
      }
      return `${region} ${city}`;
    }
    return city || region || "-";
  }

  function buildTrackerEntriesEmptyStateView({
    trackerEntriesError = "",
    uiMode = "admin",
    escapeHtml = (value) => String(value || ""),
    errorPrefix = "Project entries failed to load",
    userEmptyHtml = '<div class="empty-state">No tracker entry is ready for the sales view.</div>',
    adminEmptyHtml = '<div class="empty-state">No tracker rows loaded.</div>',
  } = {}) {
    if (trackerEntriesError) {
      return {
        html: `<div class="empty-state">${escapeHtml(errorPrefix)}: ${escapeHtml(trackerEntriesError)}</div>`,
      };
    }
    return {
      html: uiMode === "user" ? userEmptyHtml : adminEmptyHtml,
    };
  }

  function buildTrackerEntryCardView(entry, options = {}) {
    const {
      displayNo = 0,
      selectedEntryId = "",
      trackerRelatedEntryId = "",
      uiMode = "admin",
      formatOpeningScheduledDate = (value) => String(value || "-"),
      formatEstimateValue = () => "-",
      relatedButtonOpenLabel = "\uC5F0\uAD00 \uACF5\uACE0 \uC5F4\uAE30",
      relatedButtonCloseLabel = "\uC5F0\uAD00 \uACF5\uACE0 \uB2EB\uAE30",
      noticeViewButtonLabel = "\uACF5\uACE0\uBB38 \uBCF4\uAE30",
      grossAreaLabel = "\uC5F0\uBA74\uC801",
      constructionCostLabel = "\uACF5\uC0AC\uBE44",
      estimateLabel = "\uBE4C\uB529\uC790\uB3D9\uC81C\uC5B4 \uCD94\uC815\uAE08\uC561(\uACF5\uC0AC\uBE44\uC758 1.5~2%)",
      architectOfficeLabel = "\uC124\uACC4\uC0AC\uBB34\uC18C",
      constructionStartDateLabel = "\uCC29\uACF5",
      openingScheduledDateLabel = "\uAC1C\uCC30\uC608\uC815\uC77C",
      demandContactLabel = "\uB2F4\uB2F9",
      siteLocationLabel = "\uD604\uC7A5",
      salesSectionHtml = "",
      relatedNoticeHtml = "",
    } = options;

    const currentEntry = entry && typeof entry === "object" ? entry : {};
    const entryId = String(currentEntry.id || "");
    const overriddenFields = Array.isArray(currentEntry.overridden_fields)
      ? currentEntry.overridden_fields
      : [];
    const overrideMetaText = overriddenFields.length
      ? `override ${overriddenFields.join(", ")}`
      : "";

    return {
      id: entryId,
      selectedClass: entryId === String(selectedEntryId || "") ? " is-selected" : "",
      displayNoText: String(displayNo || ""),
      projectNameText: String(currentEntry.project_name || ""),
      entryKeyText: "",
      demandOrgNameText: String(currentEntry.demand_org_name || "(수요기관 없음)"),
      grossAreaScaleText: String(currentEntry.gross_area_scale || "-"),
      constructionCostText: String(currentEntry.construction_cost || "-"),
      estimateValueText: String(formatEstimateValue(currentEntry) || "-"),
      architectOfficeText: String(currentEntry.architect_office || "-"),
      constructionStartDateText: String(currentEntry.construction_start_date || "-"),
      openingScheduledDateText: String(
        formatOpeningScheduledDate(currentEntry.opening_scheduled_date || "") || "-",
      ),
      demandContactText: String(currentEntry.demand_contact || "-"),
      siteLocationText: buildTrackerSiteLocationText(
        currentEntry.site_location_1,
        currentEntry.site_location_2,
      ),
      relatedButtonLabel: entryId === String(trackerRelatedEntryId || "")
        ? String(relatedButtonCloseLabel)
        : String(relatedButtonOpenLabel),
      noticeViewButtonLabel: String(noticeViewButtonLabel),
      overrideMetaText,
      overrideMetaHtml: uiMode === "admin" && overrideMetaText ? `<p>${overrideMetaText}</p>` : "",
      salesSectionHtml: String(salesSectionHtml || ""),
      relatedNoticeHtml: String(relatedNoticeHtml || ""),
      grossAreaLabel: String(grossAreaLabel),
      constructionCostLabel: String(constructionCostLabel),
      estimateLabel: String(estimateLabel),
      architectOfficeLabel: String(architectOfficeLabel),
      constructionStartDateLabel: String(constructionStartDateLabel),
      openingScheduledDateLabel: String(openingScheduledDateLabel),
      demandContactLabel: String(demandContactLabel),
      siteLocationLabel: String(siteLocationLabel),
    };
  }

  function buildLegacyTrackerEntryCardView(payload = {}, helpers = {}) {
    const {
      entry = {},
      displayNo = "",
      isSelected = false,
      relatedButtonLabel = "\uC5F0\uAD00 \uACF5\uACE0 \uC5F4\uAE30",
      noticeViewButtonLabel = "\uACF5\uACE0\uBB38 \uBCF4\uAE30",
      overrideMarkup = "",
      salesMarkup = "",
      relatedMarkup = "",
    } = payload;
    const {
      formatBuildingAutomationEstimateValue: estimateFormatter =
        (_entry, fallbackValue = "") => String(fallbackValue || "-"),
      formatKoreanDate = (value) => String(value || "-"),
    } = helpers;

    const view = buildTrackerEntryCardView(entry, {
      displayNo,
      selectedEntryId: isSelected ? entry.id : "",
      formatOpeningScheduledDate: formatKoreanDate,
      formatEstimateValue: (currentEntry) =>
        estimateFormatter(currentEntry, currentEntry.building_automation_estimated_amount || "-"),
      relatedButtonOpenLabel: relatedButtonLabel,
      relatedButtonCloseLabel: relatedButtonLabel,
      noticeViewButtonLabel,
      salesSectionHtml: salesMarkup,
      relatedNoticeHtml: relatedMarkup,
    });

    return {
      ...view,
      overrideMetaHtml: String(overrideMarkup || view.overrideMetaHtml || ""),
    };
  }

  function normalizeTrackerEntryCardView(payload = {}, helpers = {}) {
    if (payload && typeof payload === "object" && "entry" in payload) {
      return buildLegacyTrackerEntryCardView(payload, helpers);
    }

    const view = payload && typeof payload === "object" ? payload : {};
    return {
      id: String(view.id || ""),
      selectedClass: String(view.selectedClass || ""),
      displayNoText: String(view.displayNoText || ""),
      projectNameText: String(view.projectNameText || view.project_name || ""),
      entryKeyText: "",
      demandOrgNameText: String(view.demandOrgNameText || view.demand_org_name || "(수요기관 없음)"),
      grossAreaScaleText: String(view.grossAreaScaleText || view.gross_area_scale || "-"),
      constructionCostText: String(view.constructionCostText || view.construction_cost || "-"),
      estimateValueText: String(
        view.estimateValueText || view.building_automation_estimated_amount || "-"
      ),
      architectOfficeText: String(view.architectOfficeText || view.architect_office || "-"),
      constructionStartDateText: String(
        view.constructionStartDateText || view.construction_start_date || "-"
      ),
      openingScheduledDateText: String(
        view.openingScheduledDateText || view.opening_scheduled_date || "-"
      ),
      demandContactText: String(view.demandContactText || view.demand_contact || "-"),
      siteLocationText: String(
        view.siteLocationText
        || buildTrackerSiteLocationText(view.site_location_1, view.site_location_2)
      ),
      relatedButtonLabel: String(view.relatedButtonLabel || "\uC5F0\uAD00 \uACF5\uACE0 \uC5F4\uAE30"),
      noticeViewButtonLabel: String(view.noticeViewButtonLabel || "\uACF5\uACE0\uBB38 \uBCF4\uAE30"),
      overrideMetaText: String(view.overrideMetaText || ""),
      overrideMetaHtml: String(view.overrideMetaHtml || ""),
      salesSectionHtml: String(view.salesSectionHtml || ""),
      relatedNoticeHtml: String(view.relatedNoticeHtml || ""),
      grossAreaLabel: String(view.grossAreaLabel || "\uC5F0\uBA74\uC801"),
      constructionCostLabel: String(view.constructionCostLabel || "\uACF5\uC0AC\uBE44"),
      estimateLabel: String(view.estimateLabel || "\uBE4C\uB529\uC790\uB3D9\uC81C\uC5B4 \uCD94\uC815\uAE08\uC561(\uACF5\uC0AC\uBE44\uC758 1.5~2%)"),
      architectOfficeLabel: String(view.architectOfficeLabel || "\uC124\uACC4\uC0AC\uBB34\uC18C"),
      constructionStartDateLabel: String(view.constructionStartDateLabel || "\uCC29\uACF5"),
      openingScheduledDateLabel: String(view.openingScheduledDateLabel || "\uAC1C\uCC30\uC608\uC815\uC77C"),
      demandContactLabel: String(view.demandContactLabel || "\uB2F4\uB2F9"),
      siteLocationLabel: String(view.siteLocationLabel || "\uD604\uC7A5"),
    };
  }

  function buildTrackerEntryCardMarkup(payload = {}, helpers = {}) {
    const { escapeHtml = (value) => String(value ?? "") } = helpers;
    const view = normalizeTrackerEntryCardView(payload, helpers);
    const overrideMetaHtml = view.overrideMetaHtml
      || (view.overrideMetaText ? `<p>${escapeHtml(view.overrideMetaText)}</p>` : "");

    return `
      <article class="entry-item${view.selectedClass}" data-entry-id="${escapeHtml(view.id)}">
        <div class="entry-shell">
          <div class="entry-no-badge" aria-label="No. ${escapeHtml(view.displayNoText)}">
            <span class="entry-no-label">No.</span>
            <strong>${escapeHtml(view.displayNoText)}</strong>
          </div>
          <div class="entry-body">
            <div class="entry-head">
              <div>
                <strong>${escapeHtml(view.projectNameText)}</strong>
              </div>
              <div class="entry-head-actions">
                <button class="ghost-button tracker-related-toggle" type="button" data-entry-related-toggle="${escapeHtml(view.id)}">
                  ${escapeHtml(view.relatedButtonLabel)}
                </button>
                <button class="ghost-button tracker-related-toggle" type="button" data-entry-notice-view="${escapeHtml(view.id)}">
                  ${escapeHtml(view.noticeViewButtonLabel)}
                </button>
              </div>
            </div>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>발주처</strong> ${escapeHtml(view.demandOrgNameText)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>${escapeHtml(view.grossAreaLabel)}</strong> ${escapeHtml(view.grossAreaScaleText)}</span>
              <span><strong>${escapeHtml(view.constructionCostLabel)}</strong> ${escapeHtml(view.constructionCostText)}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>${escapeHtml(view.estimateLabel)}</strong> ${escapeHtml(view.estimateValueText)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>${escapeHtml(view.architectOfficeLabel)}</strong> ${escapeHtml(view.architectOfficeText)}</span>
              <span><strong>${escapeHtml(view.constructionStartDateLabel)}</strong> ${escapeHtml(view.constructionStartDateText)}</span>
            </p>
            <p class="entry-metrics entry-metrics-single">
              <span><strong>${escapeHtml(view.openingScheduledDateLabel)}</strong> ${escapeHtml(view.openingScheduledDateText)}</span>
            </p>
            <p class="entry-metrics">
              <span><strong>${escapeHtml(view.demandContactLabel)}</strong> ${escapeHtml(view.demandContactText)}</span>
              <span><strong>${escapeHtml(view.siteLocationLabel)}</strong> ${escapeHtml(view.siteLocationText)}</span>
            </p>
            ${view.salesSectionHtml}
            ${overrideMetaHtml}
            ${view.relatedNoticeHtml}
          </div>
        </div>
      </article>
    `;
  }

  function buildTrackerEntriesListMarkup(views, { escapeHtml = (value) => String(value ?? "") } = {}) {
    return (Array.isArray(views) ? views : [])
      .map((view) => buildTrackerEntryCardMarkup(view, { escapeHtml }))
      .join("");
  }

  function formatEokValue(value) {
    const parsed = Number(value || 0);
    if (!Number.isFinite(parsed)) {
      return "0";
    }
    const rounded = Math.round(parsed * 10) / 10;
    return Number.isInteger(rounded) ? String(Math.trunc(rounded)) : rounded.toFixed(1);
  }

  function parseTrackerCostToWon(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return 0;
    }
    const eokMatch = raw.replaceAll(" ", "").match(/([0-9][0-9,]*(?:\.\d+)?)\s*(?:eok|\uC5B5\uC6D0?)/i);
    if (eokMatch) {
      const parsed = Number(String(eokMatch[1] || "").replaceAll(",", ""));
      if (Number.isFinite(parsed) && parsed > 0) {
        return Math.round(parsed * 100000000);
      }
    }
    const digits = raw.replace(/[^0-9]/g, "");
    if (!digits) {
      return 0;
    }
    const parsed = Number(digits);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function formatBuildingAutomationEstimateValue(snapshot, fallbackValue = "") {
    const formatRangeEok = (wonValue) => (wonValue / 100000000).toFixed(2);
    const fallback = String(fallbackValue || snapshot?.building_automation_estimated_amount || "").trim();
    if (fallback) {
      const maxMatch = fallback.match(
        /(?:max|\uCD5C\uB300)\s*([0-9][0-9,]*(?:\.\d+)?)\s*(?:eok|\uC5B5\uC6D0?)/i,
      );
      if (maxMatch) {
        return `${String(maxMatch[1] || "").replaceAll(",", "")}\uC5B5\uC6D0`;
      }
      return fallback;
    }
    const constructionCostWon = parseTrackerCostToWon(snapshot?.construction_cost || "");
    if (constructionCostWon > 0) {
      return `${formatRangeEok(constructionCostWon * 0.015)}\uC5B5\uC6D0~${formatRangeEok(constructionCostWon * 0.02)}\uC5B5\uC6D0`;
    }
    return "-";
  }

  globalObject.SPMSTrackerEntryRuntime = {
    toTrackerEntrySummary,
    buildTrackerEntrySummaryDetail,
    buildTrackerBoardEmptyStateView,
    buildSortedTrackerBoardEntries,
    buildTrackerBoardMarkup,
    buildTrackerEntriesEmptyStateView,
    buildTrackerEntryCardView,
    buildTrackerEntryCardMarkup,
    buildTrackerEntriesListMarkup,
    formatEokValue,
    parseTrackerCostToWon,
    formatBuildingAutomationEstimateValue,
  };
})(window);
