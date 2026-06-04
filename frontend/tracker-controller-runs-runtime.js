(function attachSPMSTrackerControllerRunsRuntime(globalObject) {
  function registerTrackerControllerRunsRuntime({
    controller,
    deps,
    runtimeRoot = globalObject,
  } = {}) {
    controller.disconnectRunEventStream = function disconnectRunEventStream() {
      if (deps.state?.eventSource) {
        deps.state.eventSource.close();
      }
      deps.state.eventSource = null;
      deps.state.eventSourceRunId = null;
    };

    controller.connectRunEventStream = function connectRunEventStream(runId) {
      if (!runId || typeof runtimeRoot.EventSource === "undefined") {
        deps.renderRunEventStatus?.("실시간 이벤트 미지원 브라우저");
        return;
      }
      if (deps.state?.eventSource && deps.state.eventSourceRunId === runId) {
        return;
      }
      controller.disconnectRunEventStream?.();
      const source = new runtimeRoot.EventSource(`/api/runs/${runId}/events?poll_interval_ms=1000`);
      deps.state.eventSource = source;
      deps.state.eventSourceRunId = runId;
      deps.renderRunEventStatus?.(`실시간 이벤트 연결 중: ${runId}`);
      source.onopen = () => {
        if (deps.state.eventSourceRunId === runId) {
          deps.renderRunEventStatus?.(`실시간 이벤트 연결됨: ${runId}`, "ok");
        }
      };
      source.addEventListener("run", (event) => {
        if (deps.state.selectedRunId !== runId) {
          return;
        }
        const payload = JSON.parse(event.data);
        deps.state.selectedRun = payload;
        deps.upsertRunListItem?.(payload);
        deps.renderRuns?.();
        deps.renderRunDetail?.(payload);
      });
      source.addEventListener("log", (event) => {
        if (deps.state.selectedRunId !== runId) {
          return;
        }
        const payload = JSON.parse(event.data);
        if (deps.state.runLogIds?.has(payload.id)) {
          return;
        }
        deps.state.runLogIds.add(payload.id);
        deps.state.runLogs = [payload, ...deps.state.runLogs].slice(0, 50);
        deps.renderLogsList?.(deps.state.runLogs);
      });
      source.addEventListener("complete", (event) => {
        if (deps.state.selectedRunId !== runId) {
          return;
        }
        const payload = JSON.parse(event.data);
        deps.renderRunEventStatus?.(`실시간 이벤트 종료: ${payload.status}`, payload.status === "success" ? "ok" : "warn");
        controller.disconnectRunEventStream?.();
        void controller.refreshSelectedRun?.({ silent: true });
        void controller.loadRuns?.({ silent: true, preservePage: true });
      });
      source.addEventListener("error", () => {
        if (deps.state.eventSourceRunId === runId) {
          deps.renderRunEventStatus?.(`실시간 이벤트 재연결 중: ${runId}`, "warn");
        }
      });
    };

    controller.loadRuns = async function loadRuns(options = {}) {
      const {
        initial = false,
        silent = false,
        preservePage = false,
      } = options;

      if (!preservePage) {
        deps.readRunFiltersFromControls?.();
      }

      const params = new URLSearchParams({
        page: String(deps.state?.runFilters?.page || 1),
        page_size: String(deps.state?.runFilters?.pageSize || 20),
      });
      if (deps.state?.runFilters?.status) {
        params.set("status", deps.state.runFilters.status);
      }
      if (deps.state?.runFilters?.runType) {
        params.set("run_type", deps.state.runFilters.runType);
      }
      if (deps.state?.runFilters?.from) {
        params.set("from", deps.state.runFilters.from);
      }
      if (deps.state?.runFilters?.to) {
        params.set("to", deps.state.runFilters.to);
      }

      try {
        const response = await deps.api?.(`/api/runs?${params.toString()}`);
        if (!deps.state) {
          return;
        }
        deps.state.runs = response?.items || [];
        deps.state.runsTotal = response?.total || 0;
        deps.touchSyncMeta?.(`runs synced ${new Date().toLocaleTimeString()}`);
        deps.renderRuns?.();
        deps.renderRunsPagination?.();
        deps.syncUrlState?.();

        if (!deps.state.selectedRunId && deps.state.runs.length > 0) {
          deps.state.selectedRunId = deps.state.runs[0].id;
        }
        if (deps.state.selectedRunId) {
          void controller.refreshSelectedRun({ silent: true });
        } else if (!silent) {
          deps.renderRunDetail?.(null);
        }
      } catch (err) {
        if (deps.handleOutOfRangePageError?.(err, deps.state?.runFilters, "실행")) {
          deps.syncUrlState?.();
          void controller.loadRuns({ initial, silent, preservePage: true });
          return;
        }
        if (!silent || initial) {
          deps.flash?.(err.message, "error");
        }
      }
    };

    async function listTrackerExportChildRuns(parentRunId) {
      if (!parentRunId) {
        return [];
      }
      const response = await deps.api(`/api/runs?parent_run_id=${encodeURIComponent(parentRunId)}&page=1&page_size=50`);
      return (response.items || []).filter((item) => item.run_type === "tracker_export");
    }

    function pickPreferredTrackerExportRun(childRuns, preferredRunId = "") {
      if (!childRuns.length) {
        return null;
      }
      const statusPriority = (status) => {
        if (status === "success") return 0;
        if (status === "running") return 1;
        if (status === "queued") return 2;
        if (status === "failed") return 3;
        if (status === "cancelled") return 4;
        return 5;
      };
      const preferredSuccessfulRun = childRuns.find((item) => item.id === preferredRunId && item.status === "success");
      if (preferredSuccessfulRun) {
        return preferredSuccessfulRun;
      }
      return [...childRuns].sort((left, right) => {
        const priorityGap = statusPriority(left.status) - statusPriority(right.status);
        if (priorityGap !== 0) {
          return priorityGap;
        }
        if (left.id === preferredRunId) {
          return -1;
        }
        if (right.id === preferredRunId) {
          return 1;
        }
        return String(right.created_at || "").localeCompare(String(left.created_at || ""));
      })[0];
    }

    async function resolvePreferredTrackerRunIdForRun(run) {
      if (!run) {
        return null;
      }
      if (run.run_type === "tracker_export") {
        if (run.status === "success" || run.status === "running" || run.status === "queued") {
          return run.id;
        }
        if (!run.parent_run_id) {
          return run.id;
        }
        try {
          const childRuns = await listTrackerExportChildRuns(run.parent_run_id);
          const preferredRun = pickPreferredTrackerExportRun(childRuns, run.id);
          return (preferredRun && preferredRun.id) || run.id;
        } catch (_err) {
          return run.id;
        }
      }
      if (deps.isProjectTrackerRun?.(run.run_type)) {
        const autoTrackerRunId = (((run.summary || {}).output || {}).auto_tracker_export_run_id || "").trim();
        try {
          const childRuns = await listTrackerExportChildRuns(run.id);
          const preferredRun = pickPreferredTrackerExportRun(childRuns, autoTrackerRunId || deps.state.selectedTrackerRunId || "");
          return (preferredRun && preferredRun.id) || autoTrackerRunId || deps.state.selectedTrackerRunId || null;
        } catch (_err) {
          return autoTrackerRunId || deps.state.selectedTrackerRunId || null;
        }
      }
      return null;
    }

    controller.refreshSelectedRun = async function refreshSelectedRun(options = {}) {
      const { silent = false } = options;

      if (!deps.state?.selectedRunId) {
        controller.disconnectRunEventStream?.();
        if (deps.state) {
          deps.state.selectedTrackerRun = null;
          deps.state.selectedTrackerWorkbookArtifactId = null;
        }
        deps.renderRunDetail?.(null);
        if (deps.state?.uiMode === "admin") {
          controller.refreshTrackerOperationalDiagnostics?.({ silent: true });
        }
        return;
      }

      try {
        const requestedRunId = deps.state.selectedRunId;
        const run = await deps.api?.(`/api/runs/${requestedRunId}`);
        if (!run || deps.state.selectedRunId !== requestedRunId) {
          return;
        }

        if (["queued", "running"].includes(run.status)) {
          controller.connectRunEventStream?.(run.id);
        } else {
          controller.disconnectRunEventStream?.();
          deps.renderRunEventStatus?.(`실시간 이벤트 종료: ${run.status}`, run.status === "success" ? "ok" : "warn");
        }

        const preferredTrackerRunId = await resolvePreferredTrackerRunIdForRun(run);
        if (deps.state.selectedRunId !== requestedRunId) {
          return;
        }

        let trackerRun = null;
        if (run.run_type === "tracker_export") {
          trackerRun = run;
        } else if (preferredTrackerRunId) {
          try {
            trackerRun = await deps.api?.(`/api/runs/${preferredTrackerRunId}`);
          } catch (_err) {
            trackerRun = null;
          }
          if (deps.state.selectedRunId !== requestedRunId) {
            return;
          }
        }

        const nextTrackerRunId = preferredTrackerRunId || (run.run_type === "tracker_export" ? run.id : null);
        if (nextTrackerRunId !== deps.state.selectedTrackerRunId) {
          deps.state.selectedTrackerWorkbookArtifactId = null;
        }
        deps.state.selectedRun = run;
        deps.state.selectedTrackerRunId = nextTrackerRunId;
        deps.state.selectedTrackerRun = trackerRun;
        deps.touchSyncMeta?.(`run synced ${new Date().toLocaleTimeString()}`);
        deps.syncUrlState?.();
        deps.renderRunDetail?.(run);
        if (deps.state.uiMode === "admin") {
          controller.refreshTrackerOperationalDiagnostics?.({ silent: true });
        }

        const activeTrackerRun = run.run_type === "tracker_export" ? run : trackerRun;
        const trackerExportPending = Boolean(
          activeTrackerRun
          && activeTrackerRun.run_type === "tracker_export"
          && ["queued", "running"].includes(activeTrackerRun.status)
        );
        if (trackerExportPending) {
          if (run.run_type === "tracker_export") {
            deps.state.artifacts = [];
            deps.state.artifactSections = [];
            deps.state.openArtifactId = null;
            if (deps.dom?.artifactsList) {
              deps.dom.artifactsList.innerHTML = '<div class="empty-state">트래커 내보내기가 아직 실행 중입니다. finalize 이후 산출물이 표시됩니다.</div>';
            }
          }
        }
        deps.schedulePolling?.(run);
        if (!trackerExportPending && run.run_type === "tracker_export") {
          void deps.loadTrackerExportPanels?.(run);
        } else if (trackerExportPending) {
          void deps.loadSelectedRunLogs?.({ silent: true, runId: run.id });
          if (!deps.useGlobalTrackerEntriesScope?.()) {
            deps.state.trackerEntries = [];
            deps.state.trackerEntriesTotal = 0;
            if (deps.dom?.trackerContext) {
              deps.dom.trackerContext.textContent = `${deps.runTypeLabel?.(run.run_type) || run.run_type} ${run.id} | finalize 대기 중`;
            }
            deps.renderTrackerEntries?.([]);
            deps.renderEntriesPagination?.();
          }
        } else {
          void deps.loadWinnerRunPanels?.(run);
          if (deps.useGlobalTrackerEntriesScope?.() && deps.state.uiMode === "admin") {
            void controller.loadTrackerEntries({ silent: true });
          } else if (!deps.useGlobalTrackerEntriesScope?.()) {
            deps.renderTrackerEntries?.([]);
          }
        }
      } catch (err) {
        const message = String((err && err.message) || "");
        if (message.includes("run not found")) {
          deps.state.selectedRunId = null;
          deps.state.selectedRun = null;
          deps.state.selectedTrackerRunId = null;
          deps.state.selectedTrackerRun = null;
          deps.state.selectedTrackerWorkbookArtifactId = null;
          deps.syncUrlState?.();
          deps.renderRunDetail?.(null);
          if (deps.state.uiMode === "admin") {
            controller.refreshTrackerOperationalDiagnostics?.({ silent: true });
          }
          return;
        }
        if (!silent) {
          deps.flash?.(err.message, "error");
        }
      }
    };
  }

  const api = { registerTrackerControllerRunsRuntime };
  globalObject.SPMSTrackerControllerRunsRuntime = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
