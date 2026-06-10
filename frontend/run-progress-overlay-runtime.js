export function createRunProgressOverlayController(deps = {}) {
  const appDocument = deps.document || (typeof document !== "undefined" ? document : null);
  const appWindow = deps.window || (typeof window !== "undefined" ? window : globalThis);
  const state = {
    hideHandle: null,
    pollHandle: null,
    watchedRunId: null,
  };

  function createNode(tagName, className = "", text = "") {
    const node = appDocument.createElement(tagName);
    if (className) {
      node.className = className;
      for (const item of className.split(/\s+/).filter(Boolean)) {
        node.classList?.add?.(item);
      }
    }
    if (text) {
      node.textContent = text;
    }
    return node;
  }

  function ensureOverlay() {
    if (!appDocument?.body) {
      return null;
    }
    let overlay = appDocument.querySelector("#run-progress-overlay");
    if (overlay) {
      return overlay;
    }

    overlay = createNode("div", "download-progress-overlay hidden");
    overlay.id = "run-progress-overlay";
    const card = createNode("div", "download-progress-card");
    card.setAttribute?.("role", "status");
    card.setAttribute?.("aria-live", "polite");
    card.setAttribute?.("aria-atomic", "true");
    card.appendChild(createNode("div", "download-progress-spinner"));
    card.appendChild(createNode("p", "download-progress-title", "실행을 준비하고 있습니다."));
    card.appendChild(createNode("p", "download-progress-detail", "서버에 실행 작업을 등록하는 중입니다."));
    const bar = createNode("div", "download-progress-bar");
    bar.appendChild(createNode("span", "download-progress-bar-fill"));
    card.appendChild(bar);
    overlay.appendChild(card);
    appDocument.body.appendChild(overlay);
    return overlay;
  }

  function setMessage({ title = "", detail = "", progressPercent = null, tone = "" } = {}) {
    const overlay = ensureOverlay();
    if (!overlay) {
      return null;
    }
    const titleNode = overlay.querySelector(".download-progress-title");
    const detailNode = overlay.querySelector(".download-progress-detail");
    const fillNode = overlay.querySelector(".download-progress-bar-fill");
    if (titleNode && title) {
      titleNode.textContent = title;
    }
    if (detailNode && detail) {
      detailNode.textContent = detail;
    }
    if (fillNode && progressPercent != null) {
      fillNode.style.width = `${Math.max(0, Math.min(100, Number(progressPercent) || 0))}%`;
    } else if (fillNode && tone === "active") {
      fillNode.style.width = "";
    }
    return overlay;
  }

  function show() {
    const overlay = ensureOverlay();
    if (!overlay) {
      return;
    }
    appWindow.clearTimeout?.(state.hideHandle);
    state.hideHandle = null;
    overlay.classList?.remove?.("hidden", "is-complete", "is-error");
    const raf = typeof appWindow.requestAnimationFrame === "function"
      ? appWindow.requestAnimationFrame.bind(appWindow)
      : (callback) => callback();
    raf(() => overlay.classList?.add?.("is-visible"));
  }

  function stopWatch() {
    if (state.pollHandle) {
      appWindow.clearTimeout?.(state.pollHandle);
    }
    state.pollHandle = null;
    state.watchedRunId = null;
  }

  function hideLater(delayMs = 2200) {
    const overlay = ensureOverlay();
    if (!overlay) {
      return;
    }
    appWindow.clearTimeout?.(state.hideHandle);
    state.hideHandle = appWindow.setTimeout?.(() => {
      overlay.classList?.remove?.("is-visible");
      state.hideHandle = appWindow.setTimeout?.(() => overlay.classList?.add?.("hidden"), 180);
    }, delayMs);
  }

  function start() {
    stopWatch();
    setMessage({
      title: "실행을 준비하고 있습니다.",
      detail: "서버에 실행 작업을 등록하는 중입니다.",
      tone: "active",
    });
    show();
  }

  function update(message, options = {}) {
    setMessage({
      title: options.title || "실행 중입니다.",
      detail: message || "실행 상태를 확인하고 있습니다.",
      progressPercent: options.progressPercent ?? null,
      tone: "active",
    });
    show();
  }

  function complete(message = "실행이 완료됐습니다.") {
    stopWatch();
    const overlay = setMessage({
      title: "실행이 완료됐습니다.",
      detail: message,
      progressPercent: 100,
    });
    overlay?.classList?.add?.("is-complete");
    show();
    hideLater();
  }

  function fail(message = "실행에 실패했습니다.") {
    stopWatch();
    const overlay = setMessage({
      title: "실행에 실패했습니다.",
      detail: message,
      progressPercent: 100,
    });
    overlay?.classList?.add?.("is-error");
    show();
    hideLater(4200);
  }

  function formatRunProgress(run = {}) {
    const stage = String(run.progress_stage || run.status || "진행 중").trim();
    const current = Number(run.progress_current || 0);
    const total = Number(run.progress_total || 0);
    const percent = total > 0 ? Math.round((current / total) * 100) : null;
    const suffix = total > 0 ? ` (${current} / ${total})` : "";
    return {
      detail: `${stage}${suffix}`,
      percent,
    };
  }

  function watch(runId, { api, pollIntervalMs = 1000 } = {}) {
    if (!runId || typeof api !== "function") {
      return;
    }
    stopWatch();
    state.watchedRunId = String(runId);

    const poll = async () => {
      const activeRunId = state.watchedRunId;
      if (!activeRunId) {
        return;
      }
      try {
        const run = await api(`/api/runs/${encodeURIComponent(activeRunId)}`);
        if (state.watchedRunId !== activeRunId) {
          return;
        }
        const status = String(run?.status || "").toLowerCase();
        if (status === "success") {
          complete("실행이 완료됐습니다.");
          return;
        }
        if (status === "failed") {
          fail(run?.error_message || "실행에 실패했습니다.");
          return;
        }
        if (status === "cancelled") {
          fail("실행이 취소됐습니다.");
          return;
        }
        const progress = formatRunProgress(run || {});
        update(progress.detail || "실행 상태를 확인하고 있습니다.", {
          progressPercent: progress.percent,
        });
      } catch (_err) {
        update("실행 상태를 확인하고 있습니다.");
      }
      if (state.watchedRunId === activeRunId) {
        state.pollHandle = appWindow.setTimeout?.(poll, pollIntervalMs);
      }
    };

    void poll();
  }

  return {
    start,
    update,
    complete,
    fail,
    watch,
    stopWatch,
  };
}

