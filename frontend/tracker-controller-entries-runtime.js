(function attachSPMSTrackerControllerEntriesRuntime(globalObject) {
  function registerTrackerControllerEntriesRuntime({
    controller,
    deps,
    readTrackerFiltersFromControlsImpl,
  } = {}) {
    controller.loadTrackerEntries = async function loadTrackerEntries(options = {}) {
      const {
        silent = false,
        trackerRunId = deps.resolveActiveTrackerRunId?.(),
        forceRefresh = false,
      } = options;

      if (!deps.canLoadProtectedConsoleData?.()) {
        deps.state.trackerEntries = [];
        deps.state.trackerEntriesTotal = 0;
        deps.state.salesClaimsByProjectId = {};
        deps.state.salesClaimDrafts = {};
        deps.state.trackerRelatedEntryId = null;
        deps.state.trackerRelatedResolvingEntryId = null;
        deps.state.selectedEntry = null;
        deps.state.selectedEntryLoadingId = null;
        deps.state.selectedEntryError = "";
        if (deps.dom?.trackerContext) {
          deps.dom.trackerContext.textContent = "로그인해야 프로젝트 현황을 확인할 수 있습니다.";
        }
        deps.renderTrackerEntries?.([], { refreshSelectedEntry: deps.state.uiMode === "admin" });
        deps.renderEntriesPagination?.();
        deps.renderSalesSummaryPanel?.();
        return;
      }

      const globalScope = deps.useGlobalTrackerEntriesScope?.();
      if (!globalScope && !trackerRunId) {
        deps.state.trackerEntries = [];
        deps.state.trackerEntriesTotal = 0;
        deps.state.salesClaimsByProjectId = {};
        deps.state.salesClaimDrafts = {};
        deps.state.trackerEntriesError = "";
        deps.state.trackerRelatedEntryId = null;
        deps.state.trackerRelatedResolvingEntryId = null;
        deps.state.selectedEntry = null;
        deps.state.selectedEntryLoadingId = null;
        deps.state.selectedEntryError = "";
        if (deps.dom?.trackerContext) {
          deps.dom.trackerContext.textContent = "트래커 보기를 선택하면 트래커 행을 확인할 수 있습니다.";
        }
        deps.closeDrawer?.();
        deps.syncUrlState?.();
        deps.renderTrackerEntries?.([], { refreshSelectedEntry: deps.state.uiMode === "admin" });
        deps.renderEntriesPagination?.();
        deps.renderSalesSummaryPanel?.();
        return;
      }

      readTrackerFiltersFromControlsImpl();
      if (!forceRefresh && deps.shouldUseHomeBootstrapTrackerSnapshot?.()) {
        if (deps.dom?.trackerContext) {
          deps.dom.trackerContext.textContent = `전체 프로젝트 현황 | ${deps.state.trackerEntriesTotal} row(s)`;
        }
        deps.syncUrlState?.();
        deps.renderTrackerEntries?.(deps.state.trackerEntries, { refreshSelectedEntry: false });
        deps.renderEntriesPagination?.();
        return;
      }

      const params = new URLSearchParams({
        page: String(deps.state.trackerFilters.page),
        page_size: String(deps.state.trackerFilters.pageSize),
      });
      if (!globalScope) {
        params.set("source_tracker_run_id", trackerRunId);
      }
      if (deps.state.trackerFilters.q) {
        params.set("q", deps.state.trackerFilters.q);
      }
      if (deps.state.trackerFilters.region) {
        params.set("region", deps.state.trackerFilters.region);
      }
      if (deps.state.trackerFilters.noticeYear) {
        params.set("notice_year", deps.state.trackerFilters.noticeYear);
      }
      if (globalScope) {
        params.set("exclude_auxiliary_titles", "true");
      }
      if (deps.state.trackerFilters.editedOnly) {
        params.set("edited_only", "true");
      }
      if (globalScope && forceRefresh) {
        params.set("refresh", "true");
      }
      const requestKey = `${deps.state.uiMode}|${globalScope ? "global" : String(trackerRunId || "")}|${params.toString()}`;
      if (deps.state.trackerEntriesRequest && !forceRefresh && deps.state.trackerEntriesRequestKey === requestKey) {
        return deps.state.trackerEntriesRequest;
      }

      const request = (async () => {
        try {
          const response = await deps.api?.(`/api/tracker-entry-summaries?${params.toString()}`, {
            timeoutMs: deps.useGlobalTrackerEntriesScope?.() ? 65000 : 20000,
          });
          if (globalScope !== deps.useGlobalTrackerEntriesScope?.()) {
            return;
          }
          if (!globalScope && trackerRunId !== deps.resolveActiveTrackerRunId?.()) {
            return;
          }
          const total = response?.total || 0;
          const totalPages = Math.max(1, Math.ceil(total / deps.state.trackerFilters.pageSize));
          if (total > 0 && deps.state.trackerFilters.page > totalPages) {
            deps.state.trackerFilters.page = totalPages;
            deps.syncUrlState?.();
            void controller.loadTrackerEntries({ silent: true, trackerRunId });
            return;
          }
          deps.state.homeBootstrapTrackerSnapshotActive = false;
          const previousEntries = new Map((deps.state.trackerEntries || []).map((entry) => [entry.id, entry]));
          deps.state.trackerEntries = (response?.items || []).map((entry) => ({
            ...(previousEntries.get(entry.id) || {}),
            ...entry,
          }));
          deps.state.trackerEntriesTotal = total;
          deps.state.trackerEntriesError = "";
          if (!deps.state.trackerEntries.some((entry) => entry.id === deps.state.trackerBoardEdit.entryId)) {
            deps.resetTrackerBoardEdit?.();
          }
          if (!deps.state.trackerEntries.some((entry) => entry.id === deps.state.trackerRelatedEntryId)) {
            deps.state.trackerRelatedEntryId = null;
            deps.state.trackerRelatedResolvingEntryId = null;
          }
          if (!deps.state.trackerEntries.some((entry) => entry.id === deps.state.selectedEntryId)) {
            deps.state.selectedEntry = null;
            deps.state.selectedEntryLoadingId = null;
            deps.state.selectedEntryError = "";
          }
          if (deps.dom?.trackerContext) {
            deps.dom.trackerContext.textContent = globalScope
              ? `전체 프로젝트 현황 | ${response?.total || 0} row(s)`
              : `트래커 보기 ${trackerRunId} | ${response?.total || 0} row(s)`;
          }
          deps.touchSyncMeta?.(`tracker synced ${new Date().toLocaleTimeString()}`);
          deps.syncUrlState?.();
          deps.renderTrackerEntries?.(deps.state.trackerEntries, { refreshSelectedEntry: deps.state.uiMode === "admin" });
          deps.renderEntriesPagination?.();
          if (globalScope) {
            void deps.warmTrackerEntriesDownload?.();
          }
          if (deps.state.uiMode === "admin") {
            void deps.loadVisibleSalesClaims?.({ silent: true });
          }
        } catch (err) {
          if (deps.handleOutOfRangePageError?.(err, deps.state.trackerFilters, "트래커")) {
            deps.syncUrlState?.();
            void controller.loadTrackerEntries({ silent, trackerRunId });
            return;
          }
          deps.state.trackerEntriesError = err.message || "프로젝트 현황을 불러오지 못했습니다.";
          if (!deps.state.trackerEntries.length) {
            deps.state.trackerEntries = [];
            deps.state.trackerEntriesTotal = 0;
            deps.state.trackerRelatedEntryId = null;
            deps.state.trackerRelatedResolvingEntryId = null;
            if (deps.dom?.trackerContext) {
              deps.dom.trackerContext.textContent = `프로젝트 현황 로드 실패 | ${deps.state.trackerEntriesError}`;
            }
            deps.renderTrackerEntries?.([], { refreshSelectedEntry: deps.state.uiMode === "admin" });
            deps.renderEntriesPagination?.();
          } else if (deps.dom?.trackerContext) {
            deps.dom.trackerContext.textContent = `프로젝트 현황 새로고침 실패 | ${deps.state.trackerEntriesError}`;
          }
          if (!silent) {
            deps.flash?.(err.message, "error");
          }
        } finally {
          if (deps.state.trackerEntriesRequestKey === requestKey) {
            deps.state.trackerEntriesRequest = null;
            deps.state.trackerEntriesRequestKey = "";
          }
        }
      })();
      deps.state.trackerEntriesRequest = request;
      deps.state.trackerEntriesRequestKey = requestKey;
      return request;
    };

    controller.patchTrackerEntry = async function patchTrackerEntry({
      entryId,
      fieldName,
      value,
      changeSource = "web",
      actorLabel = deps.resolveTrackerPatchActorLabel?.() || "웹 콘솔",
    } = {}) {
      return deps.api?.(`/api/tracker-entries/${entryId}`, {
        method: "PATCH",
        body: JSON.stringify({
          field_name: fieldName,
          value,
          actor_label: actorLabel,
          change_source: changeSource,
        }),
      });
    };

    controller.mergeTrackerEntryInState = function mergeTrackerEntryInState(entry) {
      const summary = deps.toTrackerEntrySummary?.(entry) || entry;
      deps.state.trackerEntries = deps.state.trackerEntries.map((item) => (
        item.id === summary.id ? { ...item, ...summary } : item
      ));
      deps.state.trackerEntryDetailCache = {
        ...deps.state.trackerEntryDetailCache,
        [entry.id]: entry,
      };
      if (deps.state.selectedEntryId === entry.id) {
        deps.state.selectedEntry = entry;
      }
    };

    controller.replaceTrackerEntryInState = function replaceTrackerEntryInState(updatedEntry) {
      controller.mergeTrackerEntryInState?.(updatedEntry);
    };

    controller.fetchTrackerEntryDetail = async function fetchTrackerEntryDetail(entryId, { silent = false } = {}) {
      const existingRequest = deps.state.selectedEntryDetailRequests[entryId];
      if (existingRequest) {
        return existingRequest;
      }
      const request = (async () => {
        try {
          const entry = await deps.api?.(`/api/tracker-entries/${entryId}`);
          controller.mergeTrackerEntryInState?.(entry);
          return entry;
        } catch (err) {
          if (!silent) {
            deps.flash?.(err.message, "error");
          }
          throw err;
        }
      })();
      deps.state.selectedEntryDetailRequests = { ...deps.state.selectedEntryDetailRequests, [entryId]: request };
      try {
        return await request;
      } finally {
        const nextRequests = { ...deps.state.selectedEntryDetailRequests };
        delete nextRequests[entryId];
        deps.state.selectedEntryDetailRequests = nextRequests;
      }
    };

    controller.prefetchTrackerEntryDetails = function prefetchTrackerEntryDetails(entries) {
      const seen = new Set();
      let queued = 0;
      for (const entry of entries || []) {
        const entryId = String(entry?.id || "").trim();
        if (!entryId || seen.has(entryId)) {
          continue;
        }
        seen.add(entryId);
        if (deps.state.trackerEntryDetailCache[entryId] || deps.state.selectedEntryDetailRequests[entryId]) {
          continue;
        }
        queued += 1;
        void controller.fetchTrackerEntryDetail?.(entryId, { silent: true }).catch(() => {});
        if (queued >= (deps.TRACKER_DETAIL_PREFETCH_LIMIT || 3)) {
          break;
        }
      }
    };

    controller.loadSelectedEntryDetail = async function loadSelectedEntryDetail({
      entryId = deps.state?.selectedEntryId,
      silent = false,
      background = false,
      force = false,
    } = {}) {
      if (!entryId) {
        deps.state.selectedEntry = null;
        deps.state.selectedEntryLoadingId = null;
        deps.state.selectedEntryError = "";
        deps.renderSelectedEntry?.(null);
        return null;
      }

      const summaryEntry = deps.state.trackerEntries.find((item) => item.id === entryId);
      if (!summaryEntry) {
        if (deps.state.selectedEntryId === entryId) {
          deps.state.selectedEntry = null;
          deps.state.selectedEntryLoadingId = null;
          deps.state.selectedEntryError = "";
          deps.renderSelectedEntry?.(null);
        }
        return null;
      }

      if (!force && deps.state.selectedEntry?.id === entryId) {
        if (!background && deps.state.uiMode === "admin") {
          deps.renderSelectedEntry?.(deps.state.selectedEntry);
        }
        return deps.state.selectedEntry;
      }

      const cachedEntry = !force ? deps.state.trackerEntryDetailCache[entryId] : null;
      if (cachedEntry) {
        if (deps.state.selectedEntryId === entryId) {
          deps.state.selectedEntry = cachedEntry;
          deps.state.selectedEntryLoadingId = null;
          deps.state.selectedEntryError = "";
          if (!background && deps.state.uiMode === "admin") {
            deps.renderSelectedEntry?.(cachedEntry);
          }
        }
        return cachedEntry;
      }

      if (!background && deps.state.selectedEntryId === entryId && deps.state.uiMode === "admin") {
        deps.state.selectedEntry = null;
        deps.state.selectedEntryLoadingId = entryId;
        deps.state.selectedEntryError = "";
        deps.renderSelectedEntryLoading?.(summaryEntry);
      }

      try {
        const entry = await controller.fetchTrackerEntryDetail?.(entryId, { silent });
        if (deps.state.selectedEntryId === entryId) {
          deps.state.selectedEntry = entry;
          deps.state.selectedEntryLoadingId = null;
          deps.state.selectedEntryError = "";
          if (deps.state.uiMode === "admin") {
            deps.renderSelectedEntry?.(entry);
          }
        }
        return entry;
      } catch (err) {
        if (deps.state.selectedEntryId === entryId && !background) {
          deps.state.selectedEntry = null;
          deps.state.selectedEntryLoadingId = null;
          deps.state.selectedEntryError = err.message || "상세 정보를 불러오지 못했습니다.";
          if (deps.state.uiMode === "admin") {
            deps.renderSelectedEntryLoading?.(summaryEntry, deps.state.selectedEntryError);
          }
        }
        return null;
      }
    };

    controller.syncTrackerEntryAfterPatch = async function syncTrackerEntryAfterPatch(updatedEntry) {
      if (!updatedEntry) {
        return;
      }
      controller.replaceTrackerEntryInState?.(updatedEntry);
      deps.renderTrackerEntries?.(deps.state.trackerEntries, { refreshSelectedEntry: deps.state.uiMode === "admin" });
      if (deps.state.uiMode === "admin") {
        await controller.loadTrackerMissingReport?.({ silent: true });
      }
      await controller.loadTrackerEntries({ silent: true });
      await controller.loadTrackerChangeEvents({ silent: true });
      if (deps.state.selectedEntryId === updatedEntry.id && deps.state.uiMode !== "admin") {
        await controller.loadSelectedEntryAudit?.();
      }
      if (deps.state.selectedEntryId === updatedEntry.id) {
        await controller.loadSelectedEntryChangeEvents?.({ entryId: updatedEntry.id, silent: true });
      }
    };

    controller.saveTrackerBoardEdit = async function saveTrackerBoardEdit({ entryId, fieldName }) {
      const entry = deps.state.trackerEntries.find((item) => item.id === entryId);
      if (!entry) {
        deps.resetTrackerBoardEdit?.();
        deps.renderTrackerBoard?.(deps.state.trackerEntries);
        return;
      }
      deps.state.trackerBoardEdit.saving = true;
      deps.state.trackerBoardEdit.errorMessage = "";
      deps.renderTrackerBoard?.(deps.state.trackerEntries);
      try {
        const response = await controller.patchTrackerEntry({
          entryId,
          fieldName,
          value: deps.state.trackerBoardEdit.draftValue,
          changeSource: "web",
        });
        deps.resetTrackerBoardEdit?.();
        deps.flash?.(`Saved ${fieldName} for ${entryId}`);
        await controller.syncTrackerEntryAfterPatch(response.entry);
      } catch (err) {
        deps.state.trackerBoardEdit.saving = false;
        deps.state.trackerBoardEdit.errorMessage = err.message || "저장에 실패했습니다.";
        deps.renderTrackerBoard?.(deps.state.trackerEntries);
        deps.flash?.(err.message, "error");
      }
    };
  }

  const api = { registerTrackerControllerEntriesRuntime };
  globalObject.SPMSTrackerControllerEntriesRuntime = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
