export function createProjectRelatedController(deps = {}) {
  const {
    state,
    window,
    api,
    flash,
    escapeHtml,
    RELATED_NOTICE_RUNTIME,
    PROJECT_RELATED_READY_CACHE_TTL_MS,
    PROJECT_RELATED_SEED_CACHE_TTL_MS,
    PROJECT_RELATED_STORAGE_KEY,
    PROJECT_RELATED_STORAGE_MAX_ITEMS,
    renderNoticeViewerWindow,
    renderNoticeViewerPayload,
    renderNoticeViewerError,
    renderProjects,
    renderTrackerEntries,
    loadProjectRelatedNotices,
    loadSelectedEntryDetail,
  } = deps;

  function persistProjectRelatedPayloadCache() {
    if (typeof window === "undefined" || !window.localStorage) {
      return;
    }
    try {
      const items = Object.entries(state.projectRelatedPayloads)
        .map(([projectId, payload]) => {
          if (!projectId || !payload || payload.status !== "ready") {
            return null;
          }
          const cachedAt = Number(payload.__cachedAt || 0);
          if (cachedAt <= 0) {
            return null;
          }
          return [
            projectId,
            {
              ...payload,
              items: Array.isArray(payload.items) ? payload.items : [],
              __cachedAt: cachedAt,
            },
          ];
        })
        .filter(Boolean)
        .sort((left, right) => Number(right[1].__cachedAt || 0) - Number(left[1].__cachedAt || 0))
        .slice(0, PROJECT_RELATED_STORAGE_MAX_ITEMS);
      window.localStorage.setItem(
        PROJECT_RELATED_STORAGE_KEY,
        JSON.stringify(Object.fromEntries(items)),
      );
    } catch (_err) {
      // Ignore storage quota or serialization errors.
    }
  }

  function hydrateProjectRelatedPayloadCache() {
    if (typeof window === "undefined" || !window.localStorage) {
      return;
    }
    try {
      const raw = window.localStorage.getItem(PROJECT_RELATED_STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        return;
      }
      const nextPayloads = {};
      const nextNotices = {};
      for (const [projectId, payload] of Object.entries(parsed)) {
        if (!projectId || !payload || typeof payload !== "object" || Array.isArray(payload)) {
          continue;
        }
        const status = String(payload.status || "").trim();
        const cachedAt = Number(payload.__cachedAt || 0);
        const items = Array.isArray(payload.items) ? payload.items : [];
        if (status !== "ready" || cachedAt <= 0) {
          continue;
        }
        const normalized = {
          ...payload,
          items,
          __cachedAt: cachedAt,
        };
        nextPayloads[projectId] = normalized;
        nextNotices[projectId] = items;
      }
      state.projectRelatedPayloads = {
        ...state.projectRelatedPayloads,
        ...nextPayloads,
      };
      state.projectRelatedNotices = {
        ...state.projectRelatedNotices,
        ...nextNotices,
      };
      persistProjectRelatedPayloadCache();
    } catch (_err) {
      // Ignore malformed cache and continue with network fetches.
    }
  }

  function renderRelatedNoticePanel(projectId) {
    const payload = state.projectRelatedPayloads[projectId] || null;
    const items = state.projectRelatedNotices[projectId] || [];
    return RELATED_NOTICE_RUNTIME?.buildRelatedNoticePanelMarkup(
      {
        projectId,
        payload,
        items,
        uiMode: state.uiMode,
        loadingProjectId: state.projectRelatedLoadingId,
        errorMessage: state.projectRelatedErrors[projectId],
      },
      {
        escapeHtml,
        buildRelatedNoticeItemMarkup: RELATED_NOTICE_RUNTIME?.buildRelatedNoticeItemMarkup,
      },
    ) || '<div class="runtime-project-related"><div class="empty-state">같이 수집된 연관 공고가 없습니다.</div></div>';
  }

  function renderRelatedProjectNotices(project) {
    if (project.id !== state.projectOpenId) {
      return "";
    }
    return renderRelatedNoticePanel(project.id);
  }

  function renderTrackerEntryRelatedNotices(entry) {
    if (entry.id !== state.trackerRelatedEntryId) {
      return "";
    }
    if (entry.id === state.trackerRelatedResolvingEntryId) {
      return '<div class="runtime-project-related"><div class="empty-state">연관 공고 연결 정보를 불러오는 중입니다.</div></div>';
    }
    if (!entry.project_id) {
      return '<div class="runtime-project-related"><div class="empty-state">연관 공고를 연결할 프로젝트를 찾지 못했습니다.</div></div>';
    }
    return renderRelatedNoticePanel(entry.project_id);
  }

  function bindRelatedNoticeViewerButtons(root) {
    if (!root) {
      return;
    }
    for (const button of root.querySelectorAll("[data-related-notice-project][data-related-notice-id]")) {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const projectId = button.getAttribute("data-related-notice-project");
        const noticeId = button.getAttribute("data-related-notice-id");
        if (!projectId || !noticeId) {
          return;
        }
        const item = (state.projectRelatedNotices[projectId] || []).find((candidate) => candidate.id === noticeId);
        if (!item) {
          flash("공고문 정보를 찾지 못했습니다.", "warn");
          return;
        }
        void openRelatedNoticeViewer(item);
      });
    }
  }

  function createNoticeViewerFrame({ title = "공고문", url = "" } = {}) {
    const doc = window?.document || null;
    if (!doc?.body || typeof doc.createElement !== "function") {
      if (url && window?.location) {
        if (typeof window.location.assign === "function") {
          window.location.assign(url);
        } else {
          window.location.href = url;
        }
      }
      return null;
    }
    doc.getElementById?.("notice-viewer-overlay")?.remove?.();
    const overlay = doc.createElement("div");
    overlay.id = "notice-viewer-overlay";
    overlay.className = "notice-viewer-overlay";
    const panel = doc.createElement("section");
    panel.className = "notice-viewer-overlay-panel";
    const header = doc.createElement("header");
    header.className = "notice-viewer-overlay-header";
    const heading = doc.createElement("strong");
    heading.className = "notice-viewer-overlay-title";
    heading.textContent = String(title || "공고문");
    const closeButton = doc.createElement("button");
    closeButton.type = "button";
    closeButton.className = "notice-viewer-overlay-close";
    closeButton.setAttribute("aria-label", "닫기");
    closeButton.textContent = "×";
    const iframe = doc.createElement("iframe");
    iframe.className = "notice-viewer-overlay-frame";
    iframe.setAttribute("title", String(title || "공고문"));
    if (url) {
      iframe.src = url;
    }
    const viewerWindow = {
      closed: false,
      location: {
        href: "",
        replace(nextUrl) {
          iframe.src = nextUrl;
          this.href = nextUrl;
        },
      },
      document: {
        _buffer: "",
        open() {
          this._buffer = "";
        },
        write(markup) {
          this._buffer += String(markup || "");
        },
        close() {
          iframe.srcdoc = this._buffer;
        },
      },
      close() {
        this.closed = true;
        overlay.remove?.();
      },
    };
    closeButton.addEventListener("click", () => viewerWindow.close());
    header.append(heading, closeButton);
    panel.append(header, iframe);
    overlay.appendChild(panel);
    doc.body.appendChild(overlay);
    return viewerWindow;
  }

  function openNoticeWindow(url) {
    if (!url) {
      flash("팝업이 차단되어 공고문을 열 수 없습니다.", "warn");
      return null;
    }
    if (typeof window?.location?.assign === "function") {
      window.location.assign(url);
    } else if (window?.location) {
      window.location.href = url;
    }
    return window;
  }

  async function openRelatedNoticeViewer(item) {
    const noticeDetailUrl = String(item?.notice_detail_url || "").trim();
    const noticeUrl = String(item?.notice_url || "").trim();
    if (!noticeDetailUrl && !noticeUrl) {
      flash("공고문 URL이 없습니다.", "warn");
      return;
    }
    const viewerWindow = createNoticeViewerFrame({ title: item?.project_name || "공고문" });
    if (!viewerWindow) {
      flash("팝업이 차단되어 공고문을 열 수 없습니다.", "warn");
      return;
    }
    renderNoticeViewerWindow(viewerWindow, {
      title: item?.project_name || "공고문",
      body: '<p class="notice-viewer-state">공고문을 불러오는 중입니다.</p>',
    });
    const params = new URLSearchParams();
    if (noticeDetailUrl) {
      params.set("notice_detail_url", noticeDetailUrl);
    }
    if (noticeUrl) {
      params.set("notice_url", noticeUrl);
    }
    if (item?.project_name) {
      params.set("project_name", item.project_name);
    }
    if (item?.bid_no) {
      params.set("bid_no", item.bid_no);
    }
    if (item?.bid_ord) {
      params.set("bid_ord", item.bid_ord);
    }
    try {
      const payload = await api(`/api/notices/view?${params.toString()}`, { timeoutMs: 45000 });
      renderNoticeViewerPayload(viewerWindow, payload, item?.project_name || "공고문");
    } catch (err) {
      renderNoticeViewerError(viewerWindow, {
        title: item?.project_name || "공고문",
        errorMessage: err.message || "viewer load failed",
        links: [noticeDetailUrl || noticeUrl].filter(Boolean),
      });
    }
  }

  function buildProjectNoticeUrl(project) {
    return RELATED_NOTICE_RUNTIME?.buildProjectNoticeUrl(project) || "";
  }

  function extractTrackerEntryBidParts(entry) {
    return RELATED_NOTICE_RUNTIME?.extractTrackerEntryBidParts(entry) || { bidNo: "", bidOrd: "" };
  }

  function buildTrackerEntryNoticeUrl(entry) {
    return RELATED_NOTICE_RUNTIME?.buildTrackerEntryNoticeUrl(entry) || "";
  }

  async function openTrackerEntryNoticeViewer(entryId, _entries = state.trackerEntries) {
    if (!entryId) {
      return;
    }
    try {
      const payload = await api(`/api/tracker-entries/${encodeURIComponent(entryId)}/notice-file-open-external`, {
        method: "POST",
        timeoutMs: 45000,
      });
      if (!payload?.opened) {
        flash("공고문을 외부 브라우저로 열지 못했습니다.", "warn");
      }
    } catch (err) {
      flash(err?.message || "공고문을 외부 브라우저로 열지 못했습니다.", "warn");
    }
  }

  async function openProjectNoticeViewer(project) {
    const viewerWindow = createNoticeViewerFrame({ title: project?.project_name || "공고문" });
    if (!viewerWindow) {
      flash("팝업이 차단되어 공고문을 열 수 없습니다.", "warn");
      return;
    }
    renderNoticeViewerWindow(viewerWindow, {
      title: project?.project_name || "공고문",
      body: '<p class="notice-viewer-state">공고문을 불러오는 중입니다.</p>',
    });
    try {
      if (!project?.id) {
        throw new Error("project id is required");
      }
      const payload = await api(`/api/projects/${encodeURIComponent(project.id)}/notice-view`, { timeoutMs: 45000 });
      renderNoticeViewerPayload(viewerWindow, payload, project?.project_name || "공고문");
    } catch (err) {
      renderNoticeViewerError(viewerWindow, {
        title: project?.project_name || "공고문",
        errorMessage: err.message || "viewer load failed",
      });
    }
  }

  function resolveTrackerEntryProjectId(entryId) {
    const summaryEntry = state.trackerEntries.find((item) => item.id === entryId);
    if (summaryEntry?.project_id) {
      return summaryEntry.project_id;
    }
    if (state.selectedEntry?.id === entryId && state.selectedEntry?.project_id) {
      return state.selectedEntry.project_id;
    }
    return "";
  }

  async function ensureTrackerEntryProjectId(entryId) {
    const projectId = resolveTrackerEntryProjectId(entryId);
    if (projectId) {
      return projectId;
    }
    const detailedEntry =
      state.selectedEntry?.id === entryId
        ? state.selectedEntry
        : await loadSelectedEntryDetail?.({
          entryId,
          silent: true,
          background: true,
        });
    return detailedEntry?.project_id || "";
  }

  function resolveOpenTrackerRelatedProjectId() {
    return resolveTrackerEntryProjectId(state.trackerRelatedEntryId);
  }

  function isProjectRelatedVisible(projectId) {
    return Boolean(projectId) && (state.projectOpenId === projectId || resolveOpenTrackerRelatedProjectId() === projectId);
  }

  function renderProjectRelatedHosts() {
    renderProjects?.();
    renderTrackerEntries?.(state.trackerEntries, { refreshSelectedEntry: false });
  }

  function clearProjectRelatedRefresh(projectId = "") {
    if (!state.projectRelatedRefreshHandle) {
      return;
    }
    if (projectId && state.projectRelatedRefreshProjectId && state.projectRelatedRefreshProjectId !== projectId) {
      return;
    }
    window.clearTimeout(state.projectRelatedRefreshHandle);
    state.projectRelatedRefreshHandle = null;
    state.projectRelatedRefreshProjectId = null;
  }

  function maybeScheduleProjectRelatedRefresh(projectId) {
    const payload = state.projectRelatedPayloads[projectId] || null;
    const shouldRefresh =
      isProjectRelatedVisible(projectId) &&
      payload &&
      (payload.status === "pending" || payload.source === "seed_fallback");
    if (!shouldRefresh) {
      clearProjectRelatedRefresh(projectId);
      return;
    }
    clearProjectRelatedRefresh();
    state.projectRelatedRefreshProjectId = projectId;
    state.projectRelatedRefreshHandle = window.setTimeout(() => {
      if (!isProjectRelatedVisible(projectId)) {
        clearProjectRelatedRefresh(projectId);
        return;
      }
      void loadProjectRelatedNotices?.(projectId, { silent: true, force: true });
    }, 10000);
  }

  function canReuseProjectRelatedPayload(payload) {
    if (!payload || payload.status !== "ready") {
      return false;
    }
    const cachedAt = Number(payload.__cachedAt || 0);
    if (cachedAt <= 0) {
      return false;
    }
    const ttlMs = payload.source === "seed_fallback"
      ? PROJECT_RELATED_SEED_CACHE_TTL_MS
      : PROJECT_RELATED_READY_CACHE_TTL_MS;
    return Date.now() - cachedAt <= ttlMs;
  }

  function cacheProjectRelatedPayload(projectId, payload) {
    const cachedPayload = {
      ...payload,
      __cachedAt: Date.now(),
    };
    state.projectRelatedPayloads[projectId] = cachedPayload;
    state.projectRelatedNotices[projectId] = cachedPayload.items || [];
    persistProjectRelatedPayloadCache();
    return cachedPayload;
  }

  return {
    hydrateProjectRelatedPayloadCache,
    persistProjectRelatedPayloadCache,
    renderRelatedProjectNotices,
    renderTrackerEntryRelatedNotices,
    renderRelatedNoticePanel,
    bindRelatedNoticeViewerButtons,
    openRelatedNoticeViewer,
    openProjectNoticeViewer,
    buildProjectNoticeUrl,
    extractTrackerEntryBidParts,
    buildTrackerEntryNoticeUrl,
    openTrackerEntryNoticeViewer,
    resolveOpenTrackerRelatedProjectId,
    isProjectRelatedVisible,
    renderProjectRelatedHosts,
    clearProjectRelatedRefresh,
    maybeScheduleProjectRelatedRefresh,
    canReuseProjectRelatedPayload,
    cacheProjectRelatedPayload,
    resolveTrackerEntryProjectId,
    ensureTrackerEntryProjectId,
  };
}

const projectRelatedControllerRoot = typeof window !== "undefined" ? window : globalThis;
projectRelatedControllerRoot.PROJECT_RELATED_CONTROLLER = projectRelatedControllerRoot.PROJECT_RELATED_CONTROLLER || {};
projectRelatedControllerRoot.PROJECT_RELATED_CONTROLLER.createProjectRelatedController = createProjectRelatedController;
