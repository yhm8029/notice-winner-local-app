export function createDownloadController(deps = {}) {
  const {
    state,
    dom,
    window: appWindow = typeof window !== "undefined" ? window : null,
    document: appDocument = typeof document !== "undefined" ? document : null,
    setBusy,
    flash,
    api,
    readTrackerFiltersFromControls,
    useGlobalTrackerEntriesScope,
    resolveActiveTrackerRunId,
  } = deps;

  function extractDownloadFilename(response, fallbackName) {
    const disposition = String(response.headers.get("content-disposition") || "");
    const encodedMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (encodedMatch && encodedMatch[1]) {
      try {
        return decodeURIComponent(encodedMatch[1]);
      } catch (_error) {
        return encodedMatch[1];
      }
    }
    const plainMatch = disposition.match(/filename=\"?([^\";]+)\"?/i);
    if (plainMatch && plainMatch[1]) {
      return plainMatch[1];
    }
    return fallbackName;
  }

  function ensureDownloadProgressOverlay() {
    let overlay = appDocument.querySelector("#download-progress-overlay");
    if (overlay) {
      return overlay;
    }
    overlay = appDocument.createElement("div");
    overlay.id = "download-progress-overlay";
    overlay.className = "download-progress-overlay hidden";
    overlay.innerHTML = `
    <div class="download-progress-card" role="status" aria-live="polite" aria-atomic="true">
      <div class="download-progress-spinner" aria-hidden="true"></div>
      <p class="download-progress-title">엑셀 다운로드를 준비하고 있습니다.</p>
      <p class="download-progress-detail">서버에서 파일을 준비하는 중입니다.</p>
      <div class="download-progress-bar">
        <span class="download-progress-bar-fill"></span>
      </div>
    </div>
  `;
    appDocument.body.appendChild(overlay);
    return overlay;
  }

  function showDownloadProgressOverlay(
    stages = [
      "서버에서 파일을 준비하는 중입니다.",
      "엑셀 데이터를 정리하는 중입니다.",
      "엑셀 파일을 마무리하는 중입니다.",
    ],
    title = "엑셀 다운로드를 준비하고 있습니다.",
  ) {
    const overlay = ensureDownloadProgressOverlay();
    const titleNode = overlay.querySelector(".download-progress-title");
    const detailNode = overlay.querySelector(".download-progress-detail");
    const raf = typeof appWindow.requestAnimationFrame === "function"
      ? appWindow.requestAnimationFrame.bind(appWindow)
      : (callback) => callback();
    if (titleNode) {
      titleNode.textContent = title;
    }
    if (detailNode) {
      detailNode.textContent = stages[0] || "서버에서 파일을 준비하는 중입니다.";
    }
    appWindow.clearInterval(state.downloadProgressStageHandle);
    appWindow.clearTimeout(state.downloadProgressHideHandle);
    overlay.classList.remove("hidden");
    raf(() => overlay.classList.add("is-visible"));
    let stageIndex = 0;
    state.downloadProgressStageHandle = appWindow.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, Math.max(stages.length - 1, 0));
      if (detailNode) {
        detailNode.textContent = stages[stageIndex] || stages[stages.length - 1] || "";
      }
      if (stageIndex >= stages.length - 1) {
        appWindow.clearInterval(state.downloadProgressStageHandle);
        state.downloadProgressStageHandle = null;
      }
    }, 1600);
  }

  function updateDownloadProgressOverlay(message) {
    const overlay = appDocument.querySelector("#download-progress-overlay");
    const detailNode = overlay?.querySelector(".download-progress-detail");
    if (detailNode && message) {
      detailNode.textContent = message;
    }
  }

  function hideDownloadProgressOverlay() {
    const overlay = appDocument.querySelector("#download-progress-overlay");
    if (!overlay) {
      return;
    }
    appWindow.clearInterval(state.downloadProgressStageHandle);
    state.downloadProgressStageHandle = null;
    appWindow.clearTimeout(state.downloadProgressHideHandle);
    overlay.classList.remove("is-visible");
    state.downloadProgressHideHandle = appWindow.setTimeout(() => {
      overlay.classList.add("hidden");
    }, 180);
  }

  async function triggerFileDownload(
    url,
    {
      button = null,
      busyLabel = "다운로드 준비 중...",
      fallbackName = "download",
      showProgressOverlay = false,
      progressTitle = "엑셀 다운로드를 준비하고 있습니다.",
      progressStages = null,
    } = {},
  ) {
    const originalLabel = button ? button.textContent || "" : "";
    const fetchFn = typeof deps.fetch === "function" ? deps.fetch : fetch;
    if (button) {
      setBusy(button, true, busyLabel);
    }
    if (showProgressOverlay) {
      showDownloadProgressOverlay(Array.isArray(progressStages) && progressStages.length ? progressStages : undefined, progressTitle);
    }
    try {
      const response = await fetchFn(url, {
        method: "GET",
        credentials: "same-origin",
      });
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        const contentType = String(response.headers.get("content-type") || "");
        if (contentType.includes("application/json")) {
          const payload = await response.json().catch(() => null);
          errorMessage = payload?.error?.message || errorMessage;
        } else {
          const text = await response.text().catch(() => "");
          if (text) {
            errorMessage = text;
          }
        }
        throw new Error(errorMessage);
      }
      if (showProgressOverlay) {
        updateDownloadProgressOverlay("엑셀 파일을 마무리하는 중입니다.");
      }
      const blob = await response.blob();
      const fileName = extractDownloadFilename(response, fallbackName);
      if (showProgressOverlay) {
        updateDownloadProgressOverlay("브라우저 다운로드를 시작하는 중입니다.");
      }
      const objectUrl = appWindow.URL.createObjectURL(blob);
      const anchor = appDocument.createElement("a");
      anchor.href = objectUrl;
      anchor.download = fileName;
      appDocument.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      appWindow.setTimeout(() => appWindow.URL.revokeObjectURL(objectUrl), 1000);
    } catch (err) {
      flash(err.message || "다운로드에 실패했습니다.", "error");
    } finally {
      if (showProgressOverlay) {
        hideDownloadProgressOverlay();
      }
      if (button) {
        setBusy(button, false, originalLabel);
      }
    }
  }

  function downloadSalesWorkbook(scope, button = null) {
    const normalizedScope = scope === "company" ? "company" : "my";
    return triggerFileDownload(
      `/api/sales-claims/export?scope=${encodeURIComponent(normalizedScope)}`,
      {
        button,
        busyLabel: "엑셀 준비 중...",
        fallbackName: normalizedScope === "company" ? "company_active_sales.xlsx" : "my_active_sales.xlsx",
        showProgressOverlay: true,
        progressTitle: "영업 엑셀을 준비하고 있습니다.",
      },
    );
  }

  function buildTrackerEntriesDownloadUrl(format) {
    readTrackerFiltersFromControls?.();
    const normalizedFormat = String(format || "xlsx").trim().toLowerCase();
    const canUseTrackedWorkbookArtifact = (
      normalizedFormat === "xlsx"
      && state.uiMode !== "user"
      && !useGlobalTrackerEntriesScope?.()
      && !state.trackerFilters?.q
      && !state.trackerFilters?.region
      && !state.trackerFilters?.noticeYear
      && !state.trackerFilters?.editedOnly
      && state.selectedTrackerWorkbookArtifactId
    );
    if (canUseTrackedWorkbookArtifact) {
      return `/api/artifacts/${encodeURIComponent(state.selectedTrackerWorkbookArtifactId)}/download`;
    }
    const params = new URLSearchParams({
      format: normalizedFormat,
    });
    if (!useGlobalTrackerEntriesScope?.()) {
      const trackerRunId = resolveActiveTrackerRunId?.();
      if (trackerRunId) {
        params.set("source_tracker_run_id", trackerRunId);
      }
    }
    if (state.trackerFilters?.q) {
      params.set("q", state.trackerFilters.q);
    }
    if (state.trackerFilters?.region) {
      params.set("region", state.trackerFilters.region);
    }
    if (state.trackerFilters?.noticeYear) {
      params.set("notice_year", state.trackerFilters.noticeYear);
    }
    if (useGlobalTrackerEntriesScope?.()) {
      params.set("exclude_auxiliary_titles", "true");
    }
    if (state.trackerFilters?.editedOnly) {
      params.set("edited_only", "true");
    }
    if (state.uiMode === "user") {
      params.set("blank_progress_note", "true");
    }
    return `/api/tracker-entry-summaries/download?${params.toString()}`;
  }

  function buildTrackerEntriesDownloadJobPayload() {
    readTrackerFiltersFromControls?.();
    return {
      format: "xlsx",
      q: state.trackerFilters?.q || "",
      region: state.trackerFilters?.region || "",
      notice_year: state.trackerFilters?.noticeYear || "",
      exclude_auxiliary_titles: Boolean(useGlobalTrackerEntriesScope?.()),
      edited_only: Boolean(state.trackerFilters?.editedOnly),
      blank_progress_note: state.uiMode === "user",
      source_tracker_run_id: useGlobalTrackerEntriesScope?.() ? null : (resolveActiveTrackerRunId?.() || null),
      source_run_id: null,
      sheet_name: "",
      section_name: "",
    };
  }

  async function pollTrackerDownloadJob(jobId, { timeoutMs = 300000, intervalMs = 700 } = {}) {
    const startedAt = Date.now();
    let lastJob = null;
    while (Date.now() - startedAt < timeoutMs) {
      lastJob = await api(`/api/tracker-entry-summaries/download-jobs/${encodeURIComponent(jobId)}`, {
        timeoutMs: 15000,
        cacheBust: false,
      });
      if (lastJob.status === "success" || lastJob.status === "failed") {
        return lastJob;
      }
      updateDownloadProgressOverlay(
        lastJob.status === "running"
          ? "엑셀 파일을 생성하고 있습니다."
          : "엑셀 생성 작업을 대기열에 등록했습니다.",
      );
      await new Promise((resolve) => appWindow.setTimeout(resolve, intervalMs));
    }
    throw new Error("엑셀 준비가 지연되고 있습니다. 잠시 후 다시 시도해 주세요.");
  }

  async function triggerTrackerEntriesXlsxDownload(button = null) {
    const directUrl = buildTrackerEntriesDownloadUrl("xlsx");
    if (directUrl) {
      return triggerFileDownload(directUrl, {
        button,
        busyLabel: "엑셀 준비 중...",
        fallbackName: "project_tracking.xlsx",
        showProgressOverlay: true,
        progressTitle: "프로젝트 현황 엑셀을 준비하고 있습니다.",
      });
    }

    const originalLabel = button ? button.textContent || "" : "";
    if (button) {
      setBusy(button, true, "엑셀 준비 중...");
    }
    showDownloadProgressOverlay(undefined, "프로젝트 현황 엑셀을 준비하고 있습니다.");
    try {
      updateDownloadProgressOverlay("엑셀 생성 작업을 시작하고 있습니다.");
      const created = await api("/api/tracker-entry-summaries/download-jobs", {
        method: "POST",
        body: JSON.stringify(buildTrackerEntriesDownloadJobPayload()),
        timeoutMs: 15000,
        cacheBust: false,
      });
      const job = await pollTrackerDownloadJob(created.id, {});
      if (job.status !== "success" || !job.download_url) {
        throw new Error(job.error || "엑셀 다운로드 준비에 실패했습니다.");
      }
      updateDownloadProgressOverlay(job.reused_existing ? "기존 엑셀 파일을 재사용합니다." : "엑셀 파일 다운로드를 시작합니다.");
      appWindow.location.href = job.download_url;
    } catch (err) {
      flash(err.message || "다운로드에 실패했습니다.", "error");
    } finally {
      hideDownloadProgressOverlay();
      if (button) {
        setBusy(button, false, originalLabel);
      }
    }
  }

  function buildTrackerEntriesDownloadWarmUrl() {
    readTrackerFiltersFromControls?.();
    if (!useGlobalTrackerEntriesScope?.()) {
      return "";
    }
    const params = new URLSearchParams({
      format: "xlsx",
    });
    if (state.trackerFilters?.q) {
      params.set("q", state.trackerFilters.q);
    }
    if (state.trackerFilters?.region) {
      params.set("region", state.trackerFilters.region);
    }
    if (state.trackerFilters?.noticeYear) {
      params.set("notice_year", state.trackerFilters.noticeYear);
    }
    params.set("exclude_auxiliary_titles", "true");
    if (state.trackerFilters?.editedOnly) {
      params.set("edited_only", "true");
    }
    if (state.uiMode === "user") {
      params.set("blank_progress_note", "true");
    }
    return `/api/tracker-entry-summaries/download/warm?${params.toString()}`;
  }

  async function warmTrackerEntriesDownload() {
    const url = buildTrackerEntriesDownloadWarmUrl();
    if (!url || typeof api !== "function") {
      return;
    }
    const requestKey = `${state.uiMode}|${url}`;
    if (state.trackerDownloadWarmRequest && state.trackerDownloadWarmRequestKey === requestKey) {
      return state.trackerDownloadWarmRequest;
    }
    const request = (async () => {
      try {
        await api(url, {
          method: "POST",
          timeoutMs: 2000,
        });
      } catch (_err) {
        // Warm-up is optional. Ignore failures and keep the live download path.
      } finally {
        if (state.trackerDownloadWarmRequestKey === requestKey) {
          state.trackerDownloadWarmRequest = null;
          state.trackerDownloadWarmRequestKey = "";
        }
      }
    })();
    state.trackerDownloadWarmRequest = request;
    state.trackerDownloadWarmRequestKey = requestKey;
    return request;
  }

  return {
    extractDownloadFilename,
    ensureDownloadProgressOverlay,
    showDownloadProgressOverlay,
    updateDownloadProgressOverlay,
    hideDownloadProgressOverlay,
    triggerFileDownload,
    downloadSalesWorkbook,
    buildTrackerEntriesDownloadUrl,
    buildTrackerEntriesDownloadJobPayload,
    pollTrackerDownloadJob,
    triggerTrackerEntriesXlsxDownload,
    buildTrackerEntriesDownloadWarmUrl,
    warmTrackerEntriesDownload,
  };
}

const downloadControllerRoot = typeof window !== "undefined" ? window : globalThis;
downloadControllerRoot.DOWNLOAD_CONTROLLER = downloadControllerRoot.DOWNLOAD_CONTROLLER || {};
downloadControllerRoot.DOWNLOAD_CONTROLLER.createDownloadController = createDownloadController;
