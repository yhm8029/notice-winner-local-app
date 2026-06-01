(function attachAppCoreRuntime(global) {
  function createAppCoreRuntime(context = {}) {
    const runtimeWindow = context.window || global;
    const state = context.state || runtimeWindow.state || null;
    const dom = context.dom || runtimeWindow.dom || null;
    const refreshAuthSessionState =
      context.refreshAuthSessionState
      || runtimeWindow.refreshAuthSessionState
      || null;
    const renderAuthUi = context.renderAuthUi || runtimeWindow.renderAuthUi || null;
    const fetchImpl = context.fetch || runtimeWindow.fetch || global.fetch;
    const AbortControllerImpl = context.AbortController || runtimeWindow.AbortController || global.AbortController;
    const FormDataImpl = context.FormData || runtimeWindow.FormData || global.FormData;
    const setTimeoutImpl = runtimeWindow.setTimeout || global.setTimeout;
    const clearTimeoutImpl = runtimeWindow.clearTimeout || global.clearTimeout;

    class ApiRequestError extends Error {
      constructor(message, { status = 0, path = "", url = "", payload = null } = {}) {
        super(message);
        this.name = "ApiRequestError";
        this.status = Number(status || 0);
        this.path = String(path || "");
        this.url = String(url || "");
        this.payload = payload;
      }
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function metricCard(label, value) {
      return `
    <article class="metric-card">
      <span class="detail-label">${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
    </article>
  `;
    }

    function statusBadge(status) {
      return `<span class="status-badge status-${escapeHtml(status)}">${escapeHtml(status)}</span>`;
    }

    function progressPercent(run) {
      if (!run || !run.progress_total) {
        return 8;
      }
      return Math.max(8, Math.min(100, Math.round((run.progress_current / run.progress_total) * 100)));
    }

    function formatJson(value) {
      if (!value || (typeof value === "object" && Object.keys(value).length === 0)) {
        return "{}";
      }
      return JSON.stringify(value, null, 2);
    }

    function formatDate(value) {
      if (!value) {
        return "-";
      }
      const parsed = new Date(value);
      if (Number.isNaN(parsed.getTime())) {
        return value;
      }
      return parsed.toLocaleString();
    }

    function formatKoreanDate(value) {
      const raw = String(value || "").trim();
      if (!raw) {
        return "-";
      }
      const compact = raw.replace(/[^0-9]/g, "");
      if (compact.length >= 8) {
        const year = compact.slice(0, 4);
        const month = compact.slice(4, 6);
        const day = compact.slice(6, 8);
        if (year && month && day) {
          return `${year}년 ${month}월 ${day}일`;
        }
      }
      const parsed = new Date(raw);
      if (Number.isNaN(parsed.getTime())) {
        return raw;
      }
      const year = parsed.getFullYear();
      const month = String(parsed.getMonth() + 1).padStart(2, "0");
      const day = String(parsed.getDate()).padStart(2, "0");
      return `${year}년 ${month}월 ${day}일`;
    }

    function formatBytes(value) {
      const size = Number(value || 0);
      if (!Number.isFinite(size) || size <= 0) {
        return "0 B";
      }
      if (size >= 1024 * 1024) {
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
      }
      if (size >= 1024) {
        return `${Math.round(size / 1024)} KB`;
      }
      return `${size} B`;
    }

    function flash(message, kind = "info") {
      dom.flashMessage.textContent = message;
      dom.flashMessage.classList.remove("hidden", "error");
      if (kind === "error") {
        dom.flashMessage.classList.add("error");
      }
      clearTimeoutImpl(flash.timer);
      flash.timer = setTimeoutImpl(() => dom.flashMessage.classList.add("hidden"), 4200);
    }

    function setBusy(element, busy, label) {
      if (!element) {
        return;
      }
      if (busy) {
        element.dataset.originalLabel = element.textContent;
        element.textContent = label;
      } else if (element.dataset.originalLabel) {
        element.textContent = element.dataset.originalLabel;
      }
      element.disabled = busy;
    }

    function truncate(value, maxLength) {
      const text = String(value || "");
      return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
    }

    function clampPage(value, fallback) {
      const parsed = Number(value);
      return Number.isFinite(parsed) && parsed >= 1 ? Math.floor(parsed) : fallback;
    }

    function isSoftProtected401Path(path) {
      const normalizedPath = String(path || "").trim();
      if (!normalizedPath) {
        return false;
      }
      return normalizedPath.startsWith("/api/tracker-change-events");
    }

    async function api(path, options = {}) {
      const timeoutMs = Number(options.timeoutMs || 15000);
      const requestOptions = { ...options };
      delete requestOptions.__skipAuthRetry;
      const controller = new AbortControllerImpl();
      let abortedByTimeout = false;
      const externalSignal = requestOptions.signal || null;
      let removeExternalAbortListener = null;
      const timeoutHandle = setTimeoutImpl(() => {
        abortedByTimeout = true;
        controller.abort();
      }, timeoutMs);
      const method = String(requestOptions.method || "GET").toUpperCase();
      const isFormData = typeof FormDataImpl !== "undefined" && requestOptions.body instanceof FormDataImpl;
      const { headers: optionHeaders = {}, ...restOptions } = requestOptions;
      if (externalSignal) {
        if (externalSignal.aborted) {
          controller.abort();
        } else if (typeof externalSignal.addEventListener === "function") {
          const forwardExternalAbort = () => controller.abort();
          externalSignal.addEventListener("abort", forwardExternalAbort, { once: true });
          removeExternalAbortListener = () => {
            if (typeof externalSignal.removeEventListener === "function") {
              externalSignal.removeEventListener("abort", forwardExternalAbort);
            }
          };
        }
      }
      let requestPath = path;
      if ((method === "GET" || method === "HEAD") && requestOptions.cacheBust !== false) {
        const separator = requestPath.includes("?") ? "&" : "?";
        requestPath = `${requestPath}${separator}_ts=${Date.now()}`;
      }
      let response;
      try {
        const authAccessToken = String(state?.auth?.accessToken || "").trim();
        const headers = {
          Accept: "application/json",
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
          ...(authAccessToken && !String(path || "").startsWith("/api/auth/") ? { Authorization: `Bearer ${authAccessToken}` } : {}),
          ...optionHeaders,
        };
        response = await fetchImpl(requestPath, {
          headers,
          ...restOptions,
          cache: requestOptions.cache || "no-store",
          signal: controller.signal,
        });
      } catch (err) {
        clearTimeoutImpl(timeoutHandle);
        if (removeExternalAbortListener) {
          removeExternalAbortListener();
        }
        if (err && err.name === "AbortError") {
          if (abortedByTimeout) {
            throw new Error(`Request timed out: ${requestPath}`);
          }
          throw err;
        }
        throw err;
      }
      clearTimeoutImpl(timeoutHandle);
      if (removeExternalAbortListener) {
        removeExternalAbortListener();
      }
      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json") ? await response.json() : await response.text();
      if (!response.ok) {
        const message =
          (payload && payload.error && payload.error.message) ||
          (typeof payload === "string" ? payload : response.statusText) ||
          `HTTP ${response.status}`;
        const softProtected401 = response.status === 401 && isSoftProtected401Path(path);
        if (
          response.status === 401
          && state.auth.enabled
          && !softProtected401
          && !options.__skipAuthRetry
          && !String(path || "").startsWith("/api/auth/")
        ) {
          const refreshed = await refreshAuthSessionState({ silent: true, force: true });
          if (refreshed && refreshed.authenticated && refreshed.authorized) {
            return api(path, { ...options, __skipAuthRetry: true });
          }
        }
        if (response.status === 401 && state.auth.enabled && !softProtected401) {
          state.auth.authenticated = false;
          state.auth.authorized = false;
          state.auth.user = null;
          state.auth.message = "세션이 만료되었습니다. 다시 로그인해 주세요.";
          renderAuthUi();
        }
        throw new ApiRequestError(message, {
          status: response.status,
          path,
          url: response.url || requestPath,
          payload,
        });
      }
      return payload;
    }

    return {
      ApiRequestError,
      api,
      flash,
      setBusy,
      metricCard,
      statusBadge,
      progressPercent,
      formatJson,
      formatDate,
      formatKoreanDate,
      formatBytes,
      truncate,
      clampPage,
      escapeHtml,
    };
  }

  global.createAppCoreRuntime = createAppCoreRuntime;
})(typeof window !== "undefined" ? window : globalThis);
