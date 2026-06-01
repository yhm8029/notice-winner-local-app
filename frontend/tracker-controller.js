(function attachTrackerController(root) {
  function loadRuntime(globalName, modulePath) {
    if (root?.[globalName]) {
      return root[globalName];
    }
    if (typeof module !== "undefined" && module.exports && typeof require === "function") {
      try {
        return require(modulePath);
      } catch (_err) {
        return {};
      }
    }
    return {};
  }

  function createTrackerController(deps = {}) {
    const controller = {};
    const diagnosticsRuntime = loadRuntime("SPMSTrackerControllerDiagnosticsRuntime", "./tracker-controller-diagnostics-runtime.js");
    const runsRuntime = loadRuntime("SPMSTrackerControllerRunsRuntime", "./tracker-controller-runs-runtime.js");
    const entriesRuntime = loadRuntime("SPMSTrackerControllerEntriesRuntime", "./tracker-controller-entries-runtime.js");

    function syncTrackerChangeEventUnreadCountBadge(unreadCount = 0) {
      if (!deps.dom?.trackerChangeBellBadge) {
        return;
      }
      const nextUnreadCount = Number(unreadCount || 0);
      deps.dom.trackerChangeBellBadge.textContent = String(nextUnreadCount);
      deps.dom.trackerChangeBellBadge.classList.toggle("hidden", nextUnreadCount <= 0);
    }

    function parseTrackerRegionFilterImpl(region) {
      const allowed = new Set(
        (deps.TRACKER_REGION_OPTIONS || []).map((option) => String(option.value || "").trim()).filter(Boolean),
      );
      const tokens = String(region || "")
        .split(/[\n,;|/]+/)
        .map((item) => item.trim())
        .filter(Boolean);
      const selected = new Set();
      for (const token of tokens) {
        if (allowed.has(token)) {
          selected.add(token);
        }
      }
      return (deps.TRACKER_REGION_OPTIONS || [])
        .map((option) => String(option.value || "").trim())
        .filter((value) => value && selected.has(value));
    }

    function normalizeTrackerRegionFilterImpl(region) {
      return parseTrackerRegionFilterImpl(region).join(",");
    }

    function renderTrackerRegionButtonsImpl() {
      if (!deps.dom?.trackerRegionButtons) {
        return;
      }
      const activeRegions = new Set(parseTrackerRegionFilterImpl(deps.state?.trackerFilters?.region));
      deps.dom.trackerRegionButtons.innerHTML = (deps.TRACKER_REGION_OPTIONS || []).map((option) => {
        const isActive = option.value
          ? activeRegions.has(option.value)
          : activeRegions.size === 0;
        return `
      <button
        class="region-filter-chip${isActive ? " is-active" : ""}"
        type="button"
        data-tracker-region="${deps.escapeHtml?.(option.value) ?? String(option.value || "")}"
        aria-pressed="${isActive ? "true" : "false"}"
      >
        ${deps.escapeHtml?.(option.label) ?? String(option.label || "")}
      </button>
    `;
      }).join("");
    }

    function readTrackerFiltersFromControlsImpl() {
      deps.state.trackerFilters.q = deps.dom.trackerQuery.value.trim();
      deps.state.trackerFilters.region = normalizeTrackerRegionFilterImpl(deps.state.trackerFilters.region);
      if (deps.dom.trackerEditedOnly) {
        deps.state.trackerFilters.editedOnly = deps.dom.trackerEditedOnly.checked;
      }
      deps.state.trackerFilters.pageSize = Number(deps.dom.trackerPageSize.value || 20);
    }

    controller.readTrackerFiltersFromControls = function readTrackerFiltersFromControls() {
      return readTrackerFiltersFromControlsImpl();
    };

    controller.syncTrackerFilterControlsFromState = function syncTrackerFilterControlsFromState() {
      deps.dom.trackerQuery.value = deps.state.trackerFilters.q;
      renderTrackerRegionButtonsImpl();
      if (deps.dom.trackerEditedOnly) {
        deps.dom.trackerEditedOnly.checked = deps.state.trackerFilters.editedOnly;
      }
      deps.dom.trackerPageSize.value = String(deps.state.trackerFilters.pageSize);
    };

    controller.parseTrackerRegionFilter = function parseTrackerRegionFilter(region) {
      return parseTrackerRegionFilterImpl(region);
    };

    controller.normalizeTrackerRegionFilter = function normalizeTrackerRegionFilter(region) {
      return normalizeTrackerRegionFilterImpl(region);
    };

    controller.renderTrackerRegionButtons = function renderTrackerRegionButtons() {
      return renderTrackerRegionButtonsImpl();
    };

    function resolveTrackerContextRunImpl(runSnapshot = deps.state?.selectedRun) {
      if (!runSnapshot) {
        return null;
      }
      if (runSnapshot.run_type === "tracker_export") {
        return runSnapshot;
      }
      return deps.state?.selectedTrackerRun || null;
    }

    function getTrackerDiagnosticsScopeImpl(runSnapshot = deps.state?.selectedRun) {
      const trackerRun = resolveTrackerContextRunImpl(runSnapshot);
      if (!trackerRun || trackerRun.run_type !== "tracker_export") {
        return null;
      }
      const trackerRunId = String(trackerRun.id || "").trim();
      const sourceRunId = String(trackerRun.parent_run_id || "").trim();
      if (!trackerRunId) {
        return null;
      }
      return {
        trackerRunId,
        sourceRunId,
        scopeLabel: sourceRunId
          ? `tracker_export ${trackerRunId} / source ${sourceRunId}`
          : `tracker_export ${trackerRunId}`,
      };
    }

    controller.getTrackerDiagnosticsScope = function getTrackerDiagnosticsScope(runSnapshot = deps.state?.selectedRun) {
      return getTrackerDiagnosticsScopeImpl(runSnapshot);
    };

    diagnosticsRuntime.registerTrackerControllerDiagnosticsRuntime?.({
      controller,
      deps,
      getTrackerDiagnosticsScopeImpl,
      syncTrackerChangeEventUnreadCountBadge,
      runtimeRoot: root,
    });
    runsRuntime.registerTrackerControllerRunsRuntime?.({ controller, deps, runtimeRoot: root });
    entriesRuntime.registerTrackerControllerEntriesRuntime?.({
      controller,
      deps,
      readTrackerFiltersFromControlsImpl,
    });

    controller.prefetchProjectRelatedNotices = function prefetchProjectRelatedNotices(projectIds) {
      const seen = new Set();
      let queued = 0;
      for (const rawProjectId of projectIds || []) {
        const projectId = rawProjectId || "";
        if (!projectId || seen.has(projectId)) {
          continue;
        }
        seen.add(projectId);
        if (deps.canReuseProjectRelatedPayload?.(deps.state.projectRelatedPayloads[projectId]) || deps.state.projectRelatedInFlight[projectId]) {
          continue;
        }
        queued += 1;
        void controller.loadProjectRelatedNotices(projectId, { silent: true, prefetch: true });
        if (queued >= 3) {
          break;
        }
      }
    };

    controller.prefetchVisibleProjectRelatedNotices = function prefetchVisibleProjectRelatedNotices(entries) {
      controller.prefetchProjectRelatedNotices((entries || []).map((entry) => entry?.project_id || ""));
    };

    controller.toggleProjectRelated = async function toggleProjectRelated(projectId) {
      if (deps.state.projectOpenId === projectId) {
        deps.state.projectOpenId = null;
        deps.clearProjectRelatedRefresh?.(projectId);
        deps.renderProjectRelatedHosts?.();
        deps.syncUrlState?.();
        return;
      }
      deps.clearProjectRelatedRefresh?.();
      deps.state.projectOpenId = projectId;
      deps.renderProjectRelatedHosts?.();
      deps.syncUrlState?.();
      await controller.loadProjectRelatedNotices(projectId, { silent: true });
    };

    controller.toggleTrackerEntryRelated = async function toggleTrackerEntryRelated(entryId) {
      if (!entryId) {
        return;
      }
      if (deps.state.trackerRelatedEntryId === entryId) {
        deps.state.trackerRelatedEntryId = null;
        deps.state.trackerRelatedResolvingEntryId = null;
        deps.clearProjectRelatedRefresh?.(deps.resolveTrackerEntryProjectId?.(entryId));
        deps.renderProjectRelatedHosts?.();
        return;
      }
      deps.clearProjectRelatedRefresh?.();
      deps.state.trackerRelatedEntryId = entryId;
      deps.state.trackerRelatedResolvingEntryId = null;
      deps.renderProjectRelatedHosts?.();
      let projectId = deps.resolveTrackerEntryProjectId?.(entryId);
      if (!projectId) {
        deps.state.trackerRelatedResolvingEntryId = entryId;
        deps.renderProjectRelatedHosts?.();
        try {
          projectId = await deps.ensureTrackerEntryProjectId?.(entryId);
        } finally {
          if (deps.state.trackerRelatedEntryId === entryId) {
            deps.state.trackerRelatedResolvingEntryId = null;
            deps.renderProjectRelatedHosts?.();
          }
        }
      }
      if (!projectId) {
        return;
      }
      await controller.loadProjectRelatedNotices(projectId, { silent: true });
    };

    controller.loadProjectRelatedNotices = async function loadProjectRelatedNotices(projectId, { silent = false, force = false, prefetch = false } = {}) {
      if (!projectId) {
        return null;
      }
      const cachedPayload = deps.state.projectRelatedPayloads[projectId] || null;
      if (!force && deps.canReuseProjectRelatedPayload?.(cachedPayload)) {
        deps.maybeScheduleProjectRelatedRefresh?.(projectId);
        if (!prefetch) {
          deps.renderProjectRelatedHosts?.();
        }
        return cachedPayload;
      }
      if (deps.state.projectRelatedInFlight[projectId]) {
        return deps.state.projectRelatedInFlight[projectId];
      }

      const shouldShowLoading = !prefetch && (!silent || !cachedPayload);
      if (shouldShowLoading) {
        deps.state.projectRelatedLoadingId = projectId;
      }

      const request = (async () => {
        if (!prefetch) {
          delete deps.state.projectRelatedErrors[projectId];
          deps.renderProjectRelatedHosts?.();
        }
        try {
          const response = await deps.api?.(`/api/projects/${encodeURIComponent(projectId)}/related-notices`, {
            timeoutMs: 45000,
          });
          const cached = deps.cacheProjectRelatedPayload?.(projectId, response);
          delete deps.state.projectRelatedErrors[projectId];
          return cached;
        } catch (err) {
          if (!cachedPayload) {
            delete deps.state.projectRelatedPayloads[projectId];
            deps.state.projectRelatedNotices[projectId] = [];
          }
          if (!prefetch) {
            deps.state.projectRelatedErrors[projectId] = err.message;
            if (!silent) {
              deps.flash?.(err.message, "error");
            }
          }
          return cachedPayload;
        } finally {
          if (deps.state.projectRelatedInFlight[projectId] === request) {
            delete deps.state.projectRelatedInFlight[projectId];
          }
          if (shouldShowLoading && deps.state.projectRelatedLoadingId === projectId) {
            deps.state.projectRelatedLoadingId = null;
          }
          deps.maybeScheduleProjectRelatedRefresh?.(projectId);
          if (!prefetch || deps.isProjectRelatedVisible?.(projectId)) {
            deps.renderProjectRelatedHosts?.();
          }
        }
      })();
      deps.state.projectRelatedInFlight[projectId] = request;
      return request;
    };

    controller.renderTrackerEntries = (...args) => deps.renderTrackerEntriesImpl?.(...args);

    return controller;
  }

  const api = { createTrackerController };

  if (typeof root === "object" && root) {
    root.TRACKER_CONTROLLER = root.TRACKER_CONTROLLER || api;
  }

  if (typeof exports !== "undefined") {
    exports.createTrackerController = createTrackerController;
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
