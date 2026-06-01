export function createSelectedEntryController(deps = {}) {
  const {
    dom,
    state,
    buildSelectedEntryLoadingView,
    buildSelectedEntryEmptyView,
    buildSelectedEntryChangeEventsMarkup,
    buildSelectedEntryDisplayView,
    buildPatchPanelView,
    buildSelectedEntryMeta,
    buildEntryDiagnosticsMarkup,
    buildEntryFieldGridMarkup,
    buildDrawerFieldListMarkup,
    truncate,
    escapeHtml,
    requireSelectedEntryRuntime,
    formatJson,
    EDITABLE_FIELDS,
    loadSelectedEntryAudit,
    loadSelectedEntryChangeEvents,
    openDrawer,
    closeDrawer,
    syncUrlState,
  } = deps;

  function getSelectedEntryRuntime() {
    const runtime = typeof requireSelectedEntryRuntime === "function"
      ? requireSelectedEntryRuntime()
      : null;
    return runtime && typeof runtime === "object" ? runtime : null;
  }

  function buildSelectedEntryLoadingViewFallback(entry, errorMessage = "") {
    const entryName = entry?.project_name || "\uC120\uD0DD\uB41C \uD504\uB85C\uC81D\uD2B8";
    return {
      emptyStateText: errorMessage
        ? `${entryName} \uC0C1\uC138\uB97C \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. ${errorMessage}`
        : `${entryName} \uC0C1\uC138\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.`,
      auditHtml: '<div class="empty-state">\uC0C1\uC138 \uC815\uBCF4\uB97C \uBD88\uB7EC\uC624\uBA74 \uAC10\uC0AC \uB85C\uADF8\uAC00 \uD45C\uC2DC\uB429\uB2C8\uB2E4.</div>',
      fieldGridHtml: '<div class="empty-state">\uC0C1\uC138 \uD544\uB4DC\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
      diagnosticsHtml: dom.entryDiagnosticsList
        ? '<div class="empty-state">\uC0C1\uC138 \uC815\uBCF4\uB97C \uBD88\uB7EC\uC624\uBA74 source\uC640 \uADFC\uAC70\uAC00 \uD45C\uC2DC\uB429\uB2C8\uB2E4.</div>'
        : "",
      changeEventsHtml: '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
      saveDisabled: true,
      clearDisabled: true,
    };
  }

  function buildSelectedEntryEmptyViewFallback() {
    return {
      emptyStateText: "\uD504\uB85C\uC81D\uD2B8 \uD604\uD669 \uD56D\uBAA9\uC744 \uC120\uD0DD\uD558\uBA74 \uD544\uB4DC\uB97C \uD558\uB098\uC529 \uC218\uC815\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      auditHtml: '<div class="empty-state">No audit logs loaded.</div>',
      fieldGridHtml: '<div class="empty-state">Select an entry to browse fields.</div>',
      diagnosticsHtml: dom.entryDiagnosticsList
        ? '<div class="empty-state">\uC0C1\uC138 \uC815\uBCF4\uB97C \uBD88\uB7EC\uC624\uBA74 source\uC640 \uADFC\uAC70\uAC00 \uD45C\uC2DC\uB429\uB2C8\uB2E4.</div>'
        : "",
      changeEventsHtml: '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>',
      patchValue: "",
      patchCurrentValueText: "-",
      patchOverrideMetaText: "\uC624\uBC14\uB77C\uC774\uB4DC \uC5C6\uC74C",
      clearDisabled: true,
      saveDisabled: true,
    };
  }

  function buildPatchPanelViewFallback(entry, { fieldName = "" } = {}) {
    if (!entry) {
      return buildSelectedEntryEmptyViewFallback();
    }
    const currentValue = entry?.[fieldName] ?? "";
    const hasOverride = Array.isArray(entry?.overridden_fields) && entry.overridden_fields.includes(fieldName);
    return {
      patchValue: currentValue,
      patchCurrentValueText: currentValue || "(empty)",
      patchOverrideMetaText: hasOverride ? "override active" : "source value in effect",
      clearDisabled: !hasOverride,
    };
  }

  function buildSelectedEntryDisplayViewFallback(entry, { summaryOnly = false } = {}) {
    if (!entry) {
      return {
        ...buildSelectedEntryEmptyViewFallback(),
        drawerView: null,
      };
    }
    const activeField = dom.patchField?.value || "";
    const escape = typeof escapeHtml === "function" ? escapeHtml : (value) => String(value || "");
    const fieldGridHtml = typeof buildEntryFieldGridMarkup === "function"
      ? buildEntryFieldGridMarkup(entry, activeField)
      : "";
    const diagnosticsHtml = summaryOnly
      ? '<div class="empty-state">\uC0C1\uC138 source\uC640 \uADFC\uAC70\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>'
      : (typeof buildEntryDiagnosticsMarkup === "function" ? buildEntryDiagnosticsMarkup(entry) : "");
    const drawerView = {
      title: entry.project_name || "",
      metaText: `${entry.entry_key || ""} | row ${entry.row_no || ""}`.trim(),
      statusLineHtml: `
        <span class="mono">${escape(entry.overridden_fields?.length ? "override active" : "source values")}</span>
        <span class="mono">${escape(entry.demand_org_name || "")}</span>
      `,
      fieldListHtml: typeof buildDrawerFieldListMarkup === "function"
        ? buildDrawerFieldListMarkup(entry)
        : "",
    };
    return {
      metaText: typeof buildSelectedEntryMeta === "function"
        ? buildSelectedEntryMeta(entry, { summaryOnly })
        : "",
      fieldGridHtml,
      diagnosticsHtml,
      drawerView,
      patchView: buildPatchPanelViewFallback(entry, { fieldName: activeField }),
    };
  }

  function renderSelectedEntryLoading(entry, errorMessage = "") {
    const runtime = getSelectedEntryRuntime();
    const view = (typeof buildSelectedEntryLoadingView === "function"
      ? buildSelectedEntryLoadingView(entry, { errorMessage })
      : null)
      || runtime?.buildSelectedEntryLoadingView?.(entry, { errorMessage })
      || buildSelectedEntryLoadingViewFallback(entry, errorMessage);
    dom.entryEmptyState.classList.remove("hidden");
    dom.entryEditor.classList.add("hidden");
    dom.entryEmptyState.textContent = view.emptyStateText;
    dom.auditLogList.innerHTML = view.auditHtml;
    dom.entryFieldGrid.innerHTML = view.fieldGridHtml;
    if (dom.entryDiagnosticsList) {
      dom.entryDiagnosticsList.innerHTML = view.diagnosticsHtml;
    }
    if (dom.selectedEntryChangeList) {
      dom.selectedEntryChangeList.innerHTML = view.changeEventsHtml;
    }
    dom.saveEntryButton.disabled = view.saveDisabled;
    dom.clearEntryButton.disabled = view.clearDisabled;
  }

  function renderSelectedEntryChangeEvents() {
    if (!dom.selectedEntryChangeList) {
      return;
    }
    if (!state.selectedEntryId) {
      dom.selectedEntryChangeList.classList.add("empty-state");
      dom.selectedEntryChangeList.innerHTML = "\uD504\uB85C\uC81D\uD2B8\uB97C \uC120\uD0DD\uD558\uBA74 \uCD5C\uADFC \uBCC0\uACBD\uC744 \uD45C\uC2DC\uD569\uB2C8\uB2E4.";
      return;
    }
    if (state.selectedEntryChangeEventsLoading && !state.selectedEntryChangeEvents.length) {
      dom.selectedEntryChangeList.classList.add("empty-state");
      dom.selectedEntryChangeList.innerHTML = "<div class=\"empty-state\">\uCD5C\uADFC \uBCC0\uACBD\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>";
      return;
    }
    if (!state.selectedEntryChangeEvents.length) {
      dom.selectedEntryChangeList.classList.add("empty-state");
      dom.selectedEntryChangeList.innerHTML = '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD \uC774\uB825\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.</div>';
      return;
    }
    dom.selectedEntryChangeList.classList.remove("empty-state");
    dom.selectedEntryChangeList.innerHTML = buildSelectedEntryChangeEventsMarkup(state.selectedEntryChangeEvents);
  }

  function getSelectedEntryDisplayView(entry, { summaryOnly = false } = {}) {
    const runtime = getSelectedEntryRuntime();
    const activeField = dom.patchField?.value || "";
    return (typeof buildSelectedEntryDisplayView === "function"
      ? buildSelectedEntryDisplayView(entry, {
        summaryOnly,
        editableFields: EDITABLE_FIELDS,
        activeField,
        truncate,
        escapeHtml,
      })
      : null)
      || runtime?.buildSelectedEntryDisplayView?.(entry, {
        summaryOnly,
        editableFields: EDITABLE_FIELDS,
        activeField,
        truncate,
        escapeHtml,
      })
      || buildSelectedEntryDisplayViewFallback(entry, { summaryOnly });
  }

  function renderEntryDiagnostics(entry, { summaryOnly = false, view = null } = {}) {
    if (!dom.entryDiagnosticsList) {
      return;
    }
    const displayView = view || getSelectedEntryDisplayView(entry, { summaryOnly });
    dom.entryDiagnosticsList.innerHTML = displayView.diagnosticsHtml
      || buildEntryDiagnosticsMarkup(entry);
  }

  function renderEntryFieldGrid(entry, { view = null } = {}) {
    const fieldGridHtml = view?.fieldGridHtml || getSelectedEntryDisplayView(entry).fieldGridHtml
      || buildEntryFieldGridMarkup(entry, dom.patchField.value);
    dom.entryFieldGrid.innerHTML = fieldGridHtml;

    for (const button of dom.entryFieldGrid.querySelectorAll("[data-field]")) {
      button.addEventListener("click", () => {
        dom.patchField.value = button.getAttribute("data-field");
        syncPatchValueFromSelectedEntry();
        renderEntryFieldGrid(entry);
        dom.patchValue.focus();
        dom.patchValue.select();
      });
    }
  }

  function renderDrawer(entry, { view = null } = {}) {
    const drawerView = view?.drawerView || getSelectedEntryDisplayView(entry).drawerView
      || requireSelectedEntryRuntime().buildDrawerView(entry, {
        editableFields: EDITABLE_FIELDS,
        escapeHtml,
      });
    dom.drawerTitle.textContent = drawerView.title;
    dom.drawerMeta.textContent = drawerView.metaText;
    dom.drawerStatusLine.innerHTML = drawerView.statusLineHtml;
    dom.drawerJson.textContent = formatJson(entry);
    dom.drawerFieldList.innerHTML = drawerView.fieldListHtml || buildDrawerFieldListMarkup(entry);
    for (const button of dom.drawerFieldList.querySelectorAll("[data-drawer-field]")) {
      button.addEventListener("click", () => {
        dom.patchField.value = button.getAttribute("data-drawer-field");
        syncPatchValueFromSelectedEntry();
        dom.patchValue.focus();
        dom.patchValue.select();
      });
    }
  }

  function syncPatchValueFromSelectedEntry({ patchView = null } = {}) {
    if (!state.selectedEntry) {
      const runtime = getSelectedEntryRuntime();
      const emptyView = (typeof buildSelectedEntryEmptyView === "function"
        ? buildSelectedEntryEmptyView()
        : null)
        || runtime?.buildSelectedEntryEmptyView?.()
        || buildSelectedEntryEmptyViewFallback();
      dom.patchValue.value = emptyView.patchValue;
      dom.patchCurrentValue.textContent = emptyView.patchCurrentValueText;
      dom.patchOverrideMeta.textContent = emptyView.patchOverrideMetaText;
      dom.clearEntryButton.disabled = emptyView.clearDisabled;
      return;
    }
    const runtime = getSelectedEntryRuntime();
    const fieldName = dom.patchField?.value || "";
    const view = patchView
      || (typeof buildPatchPanelView === "function"
        ? buildPatchPanelView(state.selectedEntry, {
          fieldName,
        })
        : null)
      || runtime?.buildPatchPanelView?.(state.selectedEntry, {
        fieldName,
      })
      || buildPatchPanelViewFallback(state.selectedEntry, { fieldName });
    dom.patchValue.value = view.patchValue;
    dom.patchCurrentValue.textContent = view.patchCurrentValueText;
    dom.patchOverrideMeta.textContent = view.patchOverrideMetaText;
    dom.clearEntryButton.disabled = view.clearDisabled;
    renderEntryFieldGrid(state.selectedEntry);
  }

  function renderSelectedEntry(entry, { summaryOnly = false } = {}) {
    state.selectedEntry = entry;
    if (!entry) {
      const runtime = getSelectedEntryRuntime();
      const emptyView = (typeof buildSelectedEntryEmptyView === "function"
        ? buildSelectedEntryEmptyView()
        : null)
        || runtime?.buildSelectedEntryEmptyView?.()
        || buildSelectedEntryEmptyViewFallback();
      dom.entryEmptyState.classList.remove("hidden");
      dom.entryEditor.classList.add("hidden");
      dom.entryEmptyState.textContent = emptyView.emptyStateText;
      dom.auditLogList.innerHTML = emptyView.auditHtml;
      dom.entryFieldGrid.innerHTML = emptyView.fieldGridHtml;
      if (dom.entryDiagnosticsList) {
        dom.entryDiagnosticsList.innerHTML = emptyView.diagnosticsHtml;
      }
      state.selectedEntryChangeEvents = [];
      state.selectedEntryChangeEventsLoading = false;
      renderSelectedEntryChangeEvents();
      dom.saveEntryButton.disabled = true;
      dom.patchValue.value = emptyView.patchValue;
      dom.patchCurrentValue.textContent = emptyView.patchCurrentValueText;
      dom.patchOverrideMeta.textContent = emptyView.patchOverrideMetaText;
      dom.clearEntryButton.disabled = emptyView.clearDisabled;
      closeDrawer();
      syncUrlState();
      return;
    }

    dom.entryEmptyState.classList.add("hidden");
    dom.entryEditor.classList.remove("hidden");
    dom.saveEntryButton.disabled = false;
    dom.entryTitle.textContent = entry.project_name;
    if (!EDITABLE_FIELDS.includes(dom.patchField.value)) {
      dom.patchField.value = "project_name";
    }
    const displayView = getSelectedEntryDisplayView(entry, { summaryOnly });
    const patchView = (typeof buildPatchPanelView === "function"
      ? buildPatchPanelView(entry, {
        fieldName: dom.patchField.value,
      })
      : null)
      || getSelectedEntryRuntime()?.buildPatchPanelView?.(entry, {
        fieldName: dom.patchField.value,
      })
      || buildPatchPanelViewFallback(entry, { fieldName: dom.patchField.value });
    dom.entryMeta.textContent = displayView.metaText || buildSelectedEntryMeta(entry, { summaryOnly });
    dom.entryJson.textContent = formatJson(entry);
    renderEntryFieldGrid(entry, { view: displayView });
    renderEntryDiagnostics(entry, { summaryOnly, view: displayView });
    syncPatchValueFromSelectedEntry({ patchView });
    if (summaryOnly) {
      dom.auditLogList.innerHTML = '<div class="empty-state">\uAC10\uC0AC \uB85C\uADF8\uB97C \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>';
      if (dom.selectedEntryChangeList) {
        dom.selectedEntryChangeList.innerHTML = '<div class="empty-state">\uCD5C\uADFC \uBCC0\uACBD\uC744 \uBD88\uB7EC\uC624\uB294 \uC911\uC785\uB2C8\uB2E4.</div>';
      }
      renderDrawer(entry, { view: displayView });
      if (state.drawerOpen) {
        openDrawer();
      }
      syncUrlState();
      return;
    }
    loadSelectedEntryAudit();
    void loadSelectedEntryChangeEvents({ entryId: entry.id, silent: true });
    renderDrawer(entry, { view: displayView });
    if (state.drawerOpen) {
      openDrawer();
    }
    syncUrlState();
  }

  return {
    renderSelectedEntryLoading,
    renderSelectedEntryChangeEvents,
    getSelectedEntryDisplayView,
    renderEntryDiagnostics,
    renderEntryFieldGrid,
    renderDrawer,
    syncPatchValueFromSelectedEntry,
    renderSelectedEntry,
  };
}

const selectedEntryControllerRoot = typeof window !== "undefined" ? window : globalThis;
selectedEntryControllerRoot.SELECTED_ENTRY_CONTROLLER = selectedEntryControllerRoot.SELECTED_ENTRY_CONTROLLER || {};
selectedEntryControllerRoot.SELECTED_ENTRY_CONTROLLER.createSelectedEntryController = createSelectedEntryController;

