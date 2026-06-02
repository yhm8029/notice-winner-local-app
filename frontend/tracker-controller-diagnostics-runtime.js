(function attachSPMSTrackerControllerDiagnosticsRuntime(globalObject) {
  function registerTrackerControllerDiagnosticsRuntime({
    controller,
    deps,
    getTrackerDiagnosticsScopeImpl,
    syncTrackerChangeEventUnreadCountBadge,
    runtimeRoot = globalObject,
  } = {}) {
    controller.refreshTrackerOperationalDiagnostics = function refreshTrackerOperationalDiagnostics({ silent = true } = {}) {
      if (deps.state.uiMode !== "admin") {
        return;
      }
      void controller.loadTrackerContactResolutionSummary?.({ silent });
      void controller.loadTrackerCleanupPreview?.({ silent });
      void controller.loadBackfillConflicts?.({ silent });
    };

    controller.loadTrackerContactResolutionSummary = async function loadTrackerContactResolutionSummary({ silent = false } = {}) {
      if (!deps.dom?.trackerContactResolutionPanel || deps.state.uiMode !== "admin") {
        return;
      }
      const scope = getTrackerDiagnosticsScopeImpl();
      deps.state.trackerContactResolutionLoading = true;
      deps.renderTrackerContactResolutionSummary?.();
      try {
        const query = new URLSearchParams({ limit: "12" });
        if (scope?.trackerRunId) {
          query.set("source_tracker_run_id", scope.trackerRunId);
        }
        const response = await deps.api?.(`/api/admin/tracker-contact-resolution-summary?${query.toString()}`, {
          timeoutMs: 90000,
        });
        if (deps.state.uiMode !== "admin") {
          return;
        }
        deps.state.trackerContactResolutionSummary = response || null;
        deps.state.trackerContactResolutionLoading = false;
        deps.renderTrackerContactResolutionSummary?.();
      } catch (err) {
        deps.state.trackerContactResolutionSummary = null;
        deps.state.trackerContactResolutionLoading = false;
        deps.renderTrackerContactResolutionSummary?.(err.message);
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      }
    };

    controller.loadTrackerTemplateStatus = async function loadTrackerTemplateStatus({ silent = false } = {}) {
      try {
        deps.state.trackerTemplateStatus = await deps.api?.("/api/tracker-template", { timeoutMs: 20000 });
        controller.renderTrackerTemplateStatus?.();
      } catch (err) {
        deps.state.trackerTemplateStatus = null;
        controller.renderTrackerTemplateStatus?.(err.message || "양식 상태 확인 실패");
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      }
    };

    controller.uploadTrackerTemplate = async function uploadTrackerTemplate(file) {
      if (!file) {
        return;
      }
      const formData = new deps.FormData();
      formData.append("file", file);
      deps.setBusy?.(deps.dom?.trackerTemplateUploadButton, true, "업로드 중...");
      try {
        deps.state.trackerTemplateStatus = await deps.api?.("/api/tracker-template", {
          method: "POST",
          body: formData,
          timeoutMs: 60000,
        });
        controller.renderTrackerTemplateStatus?.();
        deps.flash?.(`양식 업로드 완료: ${deps.state.trackerTemplateStatus.original_file_name || file.name}`);
      } catch (err) {
        controller.renderTrackerTemplateStatus?.(err.message || "양식 업로드 실패");
        deps.flash?.(err.message, "error");
      } finally {
        deps.setBusy?.(deps.dom?.trackerTemplateUploadButton, false, "양식 업로드");
      }
    };

    controller.resetTrackerTemplateOverride = async function resetTrackerTemplateOverride() {
      deps.setBusy?.(deps.dom?.trackerTemplateResetButton, true, "초기화 중...");
      try {
        deps.state.trackerTemplateStatus = await deps.api?.("/api/tracker-template", {
          method: "DELETE",
          timeoutMs: 20000,
        });
        controller.renderTrackerTemplateStatus?.();
        deps.flash?.("서버 업로드 양식을 제거하고 기본 양식으로 되돌렸습니다.");
      } catch (err) {
        controller.renderTrackerTemplateStatus?.(err.message || "양식 초기화 실패");
        deps.flash?.(err.message, "error");
      } finally {
        deps.setBusy?.(deps.dom?.trackerTemplateResetButton, false, "양식 초기화");
      }
    };

    controller.loadTrackerChangeEventUnreadCount = async function loadTrackerChangeEventUnreadCount({ silent = false } = {}) {
      if (deps.state.trackerChangeEventsAvailability === "unavailable") {
        deps.state.trackerChangeEventsUnread = 0;
        syncTrackerChangeEventUnreadCountBadge(0);
        return;
      }
      try {
        const response = await deps.api?.("/api/tracker-change-events/unread-count");
        deps.state.trackerChangeEventsAvailability = "available";
        deps.state.trackerChangeEventsUnread = Number(response?.unread_count || 0);
        syncTrackerChangeEventUnreadCountBadge(deps.state.trackerChangeEventsUnread);
      } catch (err) {
        if (Number(err?.status || 0) >= 500 || Number(err?.status || 0) === 404) {
          deps.state.trackerChangeEventsAvailability = "unavailable";
          deps.state.trackerChangeEventsUnread = 0;
          syncTrackerChangeEventUnreadCountBadge(0);
          return;
        }
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      }
    };

    controller.loadTrackerChangeEvents = async function loadTrackerChangeEvents({ silent = false, includeSilent = false } = {}) {
      if (deps.state.trackerChangeEventsAvailability === "unavailable") {
        deps.state.trackerChangeEvents = [];
        deps.state.trackerChangeEventsLoading = false;
        deps.renderTrackerChangeEventsPanel?.();
        return;
      }
      const shouldShowLoading = !(silent && deps.state.uiMode === "user" && !deps.state.trackerChangeEvents.length);
      deps.state.trackerChangeEventsLoading = shouldShowLoading;
      if (shouldShowLoading) {
        deps.renderTrackerChangeEventsPanel?.();
      }
      try {
        const query = new URLSearchParams({ limit: "20" });
        if (includeSilent) {
          query.set("include_silent", "true");
        }
        const response = await deps.api?.(`/api/tracker-change-events?${query.toString()}`);
        deps.state.trackerChangeEventsAvailability = "available";
        deps.state.trackerChangeEvents = Array.isArray(response?.items) ? response.items : [];
        await controller.loadTrackerChangeEventUnreadCount({ silent: true });
      } catch (err) {
        if (Number(err?.status || 0) >= 500 || Number(err?.status || 0) === 404) {
          deps.state.trackerChangeEventsAvailability = "unavailable";
          deps.state.trackerChangeEvents = [];
          deps.state.trackerChangeEventsUnread = 0;
          if (deps.dom?.trackerChangeBellBadge) {
            deps.dom.trackerChangeBellBadge.textContent = "0";
            deps.dom.trackerChangeBellBadge.classList.add("hidden");
          }
        } else {
          deps.state.trackerChangeEvents = [];
        }
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      } finally {
        deps.state.trackerChangeEventsLoading = false;
        deps.renderTrackerChangeEventsPanel?.();
      }
    };

    controller.renderTrackerChangeEventUnreadCount = function renderTrackerChangeEventUnreadCount() {
      syncTrackerChangeEventUnreadCountBadge(deps.state.trackerChangeEventsUnread);
    };

    controller.renderTrackerTemplateStatus = function renderTrackerTemplateStatus(errorMessage = "") {
      if (!deps.dom?.trackerTemplateStatus) {
        return;
      }
      if (deps.state?.uiMode !== "admin") {
        deps.dom.trackerTemplateStatus.classList.add("hidden");
        return;
      }
      deps.dom.trackerTemplateStatus.classList.remove("hidden");
      if (errorMessage) {
        deps.dom.trackerTemplateStatus.textContent = `양식 상태 확인 실패: ${errorMessage}`;
        return;
      }
      const template = deps.state?.trackerTemplateStatus;
      if (!template) {
        deps.dom.trackerTemplateStatus.textContent = "";
        deps.dom.trackerTemplateStatus.classList.add("hidden");
        return;
      }
      const updatedAt = template.updated_at ? (deps.formatDate?.(template.updated_at) || template.updated_at) : "-";
      const originalName = template.original_file_name || template.file_name || "-";
      deps.dom.trackerTemplateStatus.textContent =
        `현재 서버 양식: ${template.source_label || template.source} | ${originalName} | ${updatedAt}`;
    };

    controller.renderTrackerMissingReport = function renderTrackerMissingReport(errorMessage = "") {
      return deps.renderTrackerMissingReport?.(errorMessage);
    };

    controller.renderSelectedEntryChangeEvents = function renderSelectedEntryChangeEvents() {
      return deps.renderSelectedEntryChangeEvents?.();
    };

    controller.loadTrackerMissingReport = async function loadTrackerMissingReport({ silent = false } = {}) {
      if (!deps.dom?.panelMissingReport || deps.state.uiMode !== "admin") {
        return;
      }
      try {
        const response = await deps.api?.("/api/tracker-entries/missing-report?limit=40", {
          timeoutMs: 90000,
        });
        if (deps.state.uiMode !== "admin") {
          return;
        }
        deps.state.trackerMissingReport = response;
        controller.renderTrackerMissingReport?.();
      } catch (err) {
        deps.state.trackerMissingReport = null;
        controller.renderTrackerMissingReport?.(err.message);
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      }
    };

    controller.loadBackfillConflicts = async function loadBackfillConflicts({ silent = false, includeResolved = false, sourceRunId = undefined } = {}) {
      deps.state.backfillConflictsLoading = true;
      deps.renderBackfillConflictsPanel?.();
      try {
        const query = new URLSearchParams({ limit: "20" });
        const scope = getTrackerDiagnosticsScopeImpl();
        const effectiveSourceRunId = sourceRunId === undefined
          ? (scope?.sourceRunId || "")
          : String(sourceRunId || "").trim();
        if (includeResolved) {
          query.set("include_resolved", "true");
        }
        if (effectiveSourceRunId) {
          query.set("source_run_id", effectiveSourceRunId);
        }
        const response = await deps.api?.(`/api/backfill-conflicts?${query.toString()}`);
        deps.state.backfillConflicts = deps.requireTrackerDiagnosticsRuntime?.().filterBackfillConflictsBySourceRun(
          Array.isArray(response?.items) ? response.items : [],
          effectiveSourceRunId
        );
      } catch (err) {
        deps.state.backfillConflicts = [];
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      } finally {
        deps.state.backfillConflictsLoading = false;
        deps.renderBackfillConflictsPanel?.();
      }
    };

    controller.loadSelectedEntryAudit = async function loadSelectedEntryAudit() {
      if (!deps.state.selectedEntry) {
        deps.dom.auditLogList.innerHTML = '<div class="empty-state">No audit logs loaded.</div>';
        return;
      }
      try {
        const response = await deps.api?.(`/api/tracker-entries/${deps.state.selectedEntry.id}/audit-logs?limit=20`);
        if (!response.items.length) {
          deps.dom.auditLogList.innerHTML = '<div class="empty-state">No audit history for this entry.</div>';
          return;
        }
        deps.dom.auditLogList.innerHTML = deps.buildSelectedEntryAuditMarkup?.(response.items) || "";
      } catch (err) {
        deps.flash?.(err.message, "error");
      }
    };

    controller.loadSelectedEntryChangeEvents = async function loadSelectedEntryChangeEvents({ entryId = deps.state.selectedEntryId, silent = false } = {}) {
      if (!entryId) {
        deps.state.selectedEntryChangeEvents = [];
        deps.state.selectedEntryChangeEventsLoading = false;
        controller.renderSelectedEntryChangeEvents?.();
        return;
      }
      deps.state.selectedEntryChangeEventsLoading = true;
      controller.renderSelectedEntryChangeEvents?.();
      try {
        const query = new URLSearchParams({
          tracker_entry_id: entryId,
          limit: "10",
          include_silent: "true",
        });
        const response = await deps.api?.(`/api/tracker-change-events?${query.toString()}`);
        deps.state.selectedEntryChangeEvents = Array.isArray(response.items) ? response.items : [];
        await controller.markTrackerChangeEventsRead?.({ trackerEntryId: entryId, silent: true });
      } catch (err) {
        deps.state.selectedEntryChangeEvents = [];
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      } finally {
        deps.state.selectedEntryChangeEventsLoading = false;
        controller.renderSelectedEntryChangeEvents?.();
      }
    };

    controller.markTrackerChangeEventsRead = async function markTrackerChangeEventsRead({ eventIds = [], trackerEntryId = null, silent = false } = {}) {
      if (!eventIds.length && !trackerEntryId) {
        return 0;
      }
      try {
        const response = await deps.api?.("/api/tracker-change-events/mark-read", {
          method: "POST",
          body: JSON.stringify({
            event_ids: eventIds,
            tracker_entry_id: trackerEntryId,
          }),
        });
        const eventIdSet = new Set((eventIds || []).map((item) => String(item)));
        const markMatcher = (item) => (
          (trackerEntryId && String(item?.tracker_entry_id || "") === String(trackerEntryId))
          || (eventIdSet.size > 0 && eventIdSet.has(String(item?.id || "")))
        );
        const markedAt = new Date().toISOString();
        deps.state.trackerChangeEvents = deps.state.trackerChangeEvents.map((item) => (
          markMatcher(item) ? { ...item, is_read: true, read_at: markedAt } : item
        ));
        deps.state.selectedEntryChangeEvents = deps.state.selectedEntryChangeEvents.map((item) => (
          markMatcher(item) ? { ...item, is_read: true, read_at: markedAt } : item
        ));
        deps.renderTrackerChangeEventsPanel?.();
        controller.renderSelectedEntryChangeEvents?.();
        await controller.loadTrackerChangeEventUnreadCount({ silent: true });
        return Number(response.updated_count || 0);
      } catch (err) {
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
        return 0;
      }
    };

    controller.loadTrackerCleanupPreview = async function loadTrackerCleanupPreview({ silent = false } = {}) {
      if (!deps.dom?.trackerCleanupPanel || deps.state.uiMode !== "admin") {
        return;
      }
      const scope = getTrackerDiagnosticsScopeImpl();
      if (!scope?.trackerRunId) {
        deps.state.trackerCleanupPreview = null;
        deps.state.trackerCleanupLoading = false;
        deps.renderTrackerCleanupPreview?.();
        return;
      }
      deps.state.trackerCleanupLoading = true;
      deps.renderTrackerCleanupPreview?.();
      try {
        const response = await deps.api?.(
          `/api/admin/tracker-cleanup/preview?source_tracker_run_id=${encodeURIComponent(scope.trackerRunId)}`,
          { timeoutMs: 90000 }
        );
        if (deps.state.uiMode !== "admin") {
          return;
        }
        deps.state.trackerCleanupPreview = response || null;
        deps.state.trackerCleanupLoading = false;
        deps.renderTrackerCleanupPreview?.();
      } catch (err) {
        deps.state.trackerCleanupPreview = null;
        deps.state.trackerCleanupLoading = false;
        deps.renderTrackerCleanupPreview?.(err.message);
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      }
    };

    controller.applyTrackerCleanupForScope = async function applyTrackerCleanupForScope() {
      const scope = getTrackerDiagnosticsScopeImpl();
      if (!scope?.trackerRunId) {
        deps.flash?.("cleanup 대상 tracker run이 선택되지 않았습니다.", "error");
        return;
      }
      const confirmed = runtimeRoot.confirm?.(
        `${scope.scopeLabel} 기준 tracker cleanup을 실행할까요? 이 작업은 run/log/artifact/tracker entry를 삭제합니다.`
      );
      if (!confirmed) {
        return;
      }
      deps.state.trackerCleanupApplying = true;
      deps.renderTrackerCleanupPreview?.();
      try {
        const result = await deps.api?.("/api/admin/tracker-cleanup/apply", {
          method: "POST",
          body: JSON.stringify({ source_tracker_run_id: scope.trackerRunId }),
        });
        deps.flash?.(`tracker cleanup 완료 | entries ${Number(result?.deleted_tracker_entry_count || 0)} / runs ${Number(result?.deleted_run_count || 0)}`);
        deps.state.trackerCleanupPreview = null;
        deps.state.trackerCleanupApplying = false;
        await controller.loadRuns({ silent: true });
        await controller.refreshSelectedRun({ silent: true });
        controller.refreshTrackerOperationalDiagnostics?.({ silent: true });
      } catch (err) {
        deps.state.trackerCleanupApplying = false;
        deps.renderTrackerCleanupPreview?.(err.message);
        deps.flash?.(err.message, "error");
      }
    };
  }

  const api = { registerTrackerControllerDiagnosticsRuntime };
  globalObject.SPMSTrackerControllerDiagnosticsRuntime = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
