(function attachSelectedEntryRuntime(global) {
  function buildSelectedEntryLoadingView(entry, { errorMessage = "" } = {}) {
    const entryName = entry?.project_name || "선택한 프로젝트";
    return {
      title: entryName,
      emptyStateText: errorMessage
        ? `${entryName} 상세를 불러오지 못했습니다. ${errorMessage}`
        : `${entryName} 상세를 불러오는 중입니다.`,
      auditHtml: '<div class="empty-state">상세 정보를 불러오면 감사 로그가 표시됩니다.</div>',
      fieldGridHtml: '<div class="empty-state">상세 필드를 불러오는 중입니다.</div>',
      diagnosticsHtml: '<div class="empty-state">상세 정보를 불러오면 source와 근거가 표시됩니다.</div>',
      changeEventsHtml: '<div class="empty-state">최근 변경을 불러오는 중입니다.</div>',
      saveDisabled: true,
      clearDisabled: true,
    };
  }

  function buildSelectedEntryEmptyView() {
    return {
      emptyStateText: "Select an entry to browse fields.",
      auditHtml: '<div class="empty-state">No audit logs loaded.</div>',
      fieldGridHtml: '<div class="empty-state">Select an entry to browse fields.</div>',
      diagnosticsHtml: '<div class="empty-state">상세 정보를 불러오면 source와 근거가 표시됩니다.</div>',
      patchValue: "",
      patchCurrentValueText: "-",
      patchOverrideMetaText: "no override",
      clearDisabled: true,
    };
  }

  function buildPatchPanelView(entry, { fieldName = "" } = {}) {
    if (!entry || typeof entry !== "object") {
      return {
        patchValue: "",
        patchCurrentValueText: "-",
        patchOverrideMetaText: "no override",
        clearDisabled: true,
      };
    }
    const overriddenFields = Array.isArray(entry.overridden_fields) ? entry.overridden_fields : [];
    const hasOverride = overriddenFields.includes(fieldName);
    const currentValue = entry[fieldName] ?? "";
    return {
      patchValue: currentValue,
      patchCurrentValueText: currentValue || "(empty)",
      patchOverrideMetaText: hasOverride ? "override active" : "source value in effect",
      clearDisabled: !hasOverride,
    };
  }

  function buildSelectedEntryMeta(entry, { summaryOnly = false } = {}) {
    if (!entry || typeof entry !== "object") {
      return "";
    }
    const architectOffice = entry.architect_office || "-";
    const detailSuffix = summaryOnly ? " | 상세 보강 중" : "";
    return `${entry.entry_key} | row ${entry.row_no} | ${entry.demand_org_name} | ${architectOffice}${detailSuffix}`;
  }

  function buildEntryDiagnosticsMarkup(entry, { escapeHtml = (value) => String(value || "") } = {}) {
    const diagnostics = Array.isArray(entry?.field_diagnostics) ? entry.field_diagnostics : [];
    if (!diagnostics.length) {
      const emptyReason = entry?.source_run_id
        ? "source run은 연결돼 있지만 winner row를 역추적하지 못했습니다. 구버전 산출물이거나 source artifact 매칭이 어긋난 케이스입니다."
        : "구버전 row이거나 source_run_id가 없어 추출 진단을 구성하지 못했습니다.";
      return `<div class="empty-state">${escapeHtml(emptyReason)}</div>`;
    }
    return diagnostics
      .map((item) => {
        const sourceBits = [
          item.source_label || "source 없음",
          item.source_type_label || item.source_type || "",
          item.reason_code || "",
        ].filter(Boolean).join(" | ");
        return `
        <details class="audit-item">
          <summary>
            <strong>${escapeHtml(item.field_label || item.field_key || "-")}</strong>
            <span class="mono">${escapeHtml(sourceBits || "source 정보 없음")}</span>
          </summary>
          <p>${escapeHtml(item.source_reason || "source 설명 없음")}</p>
          <p class="mono">${escapeHtml(item.evidence_preview || "근거 미리보기 없음")}</p>
        </details>
      `;
      })
      .join("");
  }

  function buildEntryFieldGridMarkup(entry, {
    editableFields = [],
    activeField = "",
    truncate = (value) => String(value || ""),
    escapeHtml = (value) => String(value || ""),
  } = {}) {
    return (editableFields || [])
      .map((field) => {
        const activeClass = activeField === field ? " is-active" : "";
        const overrideClass = Array.isArray(entry?.overridden_fields) && entry.overridden_fields.includes(field)
          ? " is-overridden"
          : "";
        return `
      <button class="field-chip${activeClass}${overrideClass}" type="button" data-field="${escapeHtml(field)}">
        <strong>${escapeHtml(field)}</strong>
        <span>${escapeHtml(truncate(entry?.[field] || "", 60) || "(empty)")}</span>
      </button>
    `;
      })
      .join("");
  }

  function buildDrawerFieldListMarkup(entry, {
    editableFields = [],
    escapeHtml = (value) => String(value || ""),
  } = {}) {
    return (editableFields || [])
      .map((field) => {
        const overrideMeta = Array.isArray(entry?.overridden_fields) && entry.overridden_fields.includes(field)
          ? "override active"
          : "source";
        return `
      <button class="drawer-field-item" type="button" data-drawer-field="${escapeHtml(field)}">
        <strong>${escapeHtml(field)}</strong>
        <span>${escapeHtml(entry?.[field] || "(empty)")}</span>
        <span class="mono">${escapeHtml(overrideMeta)}</span>
      </button>
    `;
      })
      .join("");
  }

  function buildDrawerView(entry, {
    editableFields = [],
    escapeHtml = (value) => String(value || ""),
  } = {}) {
    return {
      title: entry?.project_name || "",
      metaText: `${entry?.entry_key || ""} | row ${entry?.row_no || ""}`,
      statusLineHtml: `
        <span class="mono">${escapeHtml((entry?.overridden_fields || []).length ? "override active" : "source values")}</span>
        <span class="mono">${escapeHtml(entry?.demand_org_name || "")}</span>
      `,
      fieldListHtml: buildDrawerFieldListMarkup(entry, { editableFields, escapeHtml }),
    };
  }

  function buildSelectedEntryDisplayView(entry, {
    summaryOnly = false,
    editableFields = [],
    activeField = "",
    truncate = (value) => String(value || ""),
    escapeHtml = (value) => String(value || ""),
  } = {}) {
    return {
      metaText: buildSelectedEntryMeta(entry, { summaryOnly }),
      fieldGridHtml: buildEntryFieldGridMarkup(entry, {
        editableFields,
        activeField,
        truncate,
        escapeHtml,
      }),
      diagnosticsHtml: summaryOnly
        ? '<div class="empty-state">상세 source와 근거를 불러오는 중입니다.</div>'
        : buildEntryDiagnosticsMarkup(entry, { escapeHtml }),
      drawerView: buildDrawerView(entry, { editableFields, escapeHtml }),
    };
  }

  global.SPMSSelectedEntryRuntime = {
    buildSelectedEntryLoadingView,
    buildSelectedEntryEmptyView,
    buildPatchPanelView,
    buildSelectedEntryMeta,
    buildEntryDiagnosticsMarkup,
    buildEntryFieldGridMarkup,
    buildDrawerFieldListMarkup,
    buildDrawerView,
    buildSelectedEntryDisplayView,
  };
})(window);
