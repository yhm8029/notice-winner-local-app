export function createTrackerEntryActionsController(deps = {}) {
  const controller = {};

  controller.toggleTrackerBoardBlankPriority = function toggleTrackerBoardBlankPriority(fieldName) {
    if (!deps.TRACKER_BOARD_BLANK_PRIORITY_FIELDS?.has(fieldName)) {
      return;
    }
    deps.state.trackerBoardSort.fieldName = deps.state.trackerBoardSort.fieldName === fieldName ? "" : fieldName;
    deps.renderTrackerBoard?.(deps.state.trackerEntries);
  };

  controller.beginTrackerBoardEdit = function beginTrackerBoardEdit(entryId, fieldName) {
    const entry = deps.state.trackerEntries.find((item) => item.id === entryId);
    if (!entry || !deps.EDITABLE_FIELDS.includes(fieldName)) {
      return;
    }
    deps.state.selectedEntryId = entryId;
    deps.state.trackerBoardEdit = {
      entryId,
      fieldName,
      draftValue: entry[fieldName] ?? "",
      saving: false,
      errorMessage: "",
    };
    deps.syncUrlState?.();
    deps.renderTrackerEntries?.(deps.state.trackerEntries, { refreshSelectedEntry: deps.state.uiMode === "admin" });
  };

  controller.resetTrackerBoardEdit = function resetTrackerBoardEdit() {
    deps.state.trackerBoardEdit = {
      entryId: null,
      fieldName: "",
      draftValue: "",
      saving: false,
      errorMessage: "",
    };
  };

  controller.resolveTrackerPatchActorLabel = function resolveTrackerPatchActorLabel() {
    const candidate = String(deps.dom.patchActorLabel?.value || "").trim();
    if (candidate) {
      return candidate;
    }
    if (deps.state.auth.user) {
      return deps.state.auth.user.display_name || deps.state.auth.user.email || "웹 콘솔";
    }
    return "웹 콘솔";
  };

  controller.getEntriesTotalPages = function getEntriesTotalPages() {
    return Math.max(1, Math.ceil(deps.state.trackerEntriesTotal / deps.state.trackerFilters.pageSize));
  };

  controller.renderEntriesPagination = function renderEntriesPagination() {
    const totalPages = controller.getEntriesTotalPages();
    deps.dom.entriesPageMeta.textContent = `Page ${deps.state.trackerFilters.page} / ${totalPages} | ${deps.state.trackerEntriesTotal} row(s)`;
    deps.dom.entriesFirstButton.disabled = deps.state.trackerFilters.page <= 1;
    deps.dom.entriesPrevButton.disabled = deps.state.trackerFilters.page <= 1;
    deps.dom.entriesNextButton.disabled = deps.state.trackerFilters.page >= totalPages;
    deps.dom.entriesLastButton.disabled = deps.state.trackerFilters.page >= totalPages;
  };

  controller.changeEntriesPage = function changeEntriesPage(delta) {
    const totalPages = controller.getEntriesTotalPages();
    const nextPage = Math.min(totalPages, Math.max(1, deps.state.trackerFilters.page + delta));
    if (nextPage === deps.state.trackerFilters.page) {
      return;
    }
    deps.state.trackerFilters.page = nextPage;
    deps.syncUrlState?.();
    deps.loadTrackerEntries?.();
  };

  controller.changeEntriesPageTo = function changeEntriesPageTo(page) {
    const totalPages = controller.getEntriesTotalPages();
    const nextPage = Math.min(totalPages, Math.max(1, Number(page) || 1));
    if (nextPage === deps.state.trackerFilters.page) {
      return;
    }
    deps.state.trackerFilters.page = nextPage;
    deps.syncUrlState?.();
    deps.loadTrackerEntries?.();
  };

  controller.saveEntryPatch = async function saveEntryPatch(event) {
    event.preventDefault();
    if (!deps.state.selectedEntry) {
      return;
    }
    const fieldName = deps.dom.patchField.value;
    const value = deps.dom.patchValue.value;
    deps.setBusy?.(deps.dom.saveEntryButton, true, "Saving...");
    try {
      const response = await deps.patchTrackerEntry({
        entryId: deps.state.selectedEntry.id,
        fieldName,
        value,
        changeSource: "web",
        actorLabel: controller.resolveTrackerPatchActorLabel(),
      });
      deps.flash?.(`Saved ${fieldName} for ${deps.state.selectedEntry.id}`);
      await deps.syncTrackerEntryAfterPatch(response.entry);
    } catch (err) {
      deps.flash?.(err.message, "error");
    } finally {
      deps.setBusy?.(deps.dom.saveEntryButton, false, "Save override");
    }
  };

  controller.clearEntryPatch = async function clearEntryPatch() {
    if (!deps.state.selectedEntry) {
      return;
    }
    deps.setBusy?.(deps.dom.clearEntryButton, true, "Clearing...");
    try {
      const response = await deps.patchTrackerEntry({
        entryId: deps.state.selectedEntry.id,
        fieldName: deps.dom.patchField.value,
        value: null,
        changeSource: "web",
        actorLabel: controller.resolveTrackerPatchActorLabel(),
      });
      deps.flash?.(`Cleared override for ${deps.dom.patchField.value}`);
      await deps.syncTrackerEntryAfterPatch(response.entry);
    } catch (err) {
      deps.flash?.(err.message, "error");
    } finally {
      deps.setBusy?.(deps.dom.clearEntryButton, false, "Clear override");
    }
  };

  controller.hydratePatchFieldOptions = function hydratePatchFieldOptions() {
    deps.dom.patchField.innerHTML = deps.EDITABLE_FIELDS.map(
      (field) => `<option value="${deps.escapeHtml(field)}">${deps.escapeHtml(field)}</option>`
    ).join("");
    deps.dom.patchField.value = "project_name";
  };

  return controller;
}

const api = { createTrackerEntryActionsController };

const trackerEntryActionsControllerRoot = typeof window !== "undefined" ? window : globalThis;
trackerEntryActionsControllerRoot.TRACKER_ENTRY_ACTIONS_CONTROLLER = trackerEntryActionsControllerRoot.TRACKER_ENTRY_ACTIONS_CONTROLLER || {};
trackerEntryActionsControllerRoot.TRACKER_ENTRY_ACTIONS_CONTROLLER.createTrackerEntryActionsController = createTrackerEntryActionsController;

if (typeof exports !== "undefined") {
  exports.createTrackerEntryActionsController = createTrackerEntryActionsController;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = api;
}
