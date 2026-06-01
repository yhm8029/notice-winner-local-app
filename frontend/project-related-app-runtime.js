(function attachProjectRelatedAppRuntime(global) {
  const NOTICE_VIEWER_TITLE = "\uACF5\uACE0\uBB38";
  const NOTICE_VIEWER_LOAD_ERROR = "\uACF5\uACE0\uBB38 \uBCF8\uBB38\uC744 \uC77D\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.";
  const NOTICE_VIEWER_OPEN_ERROR = "\uACF5\uACE0\uBB38\uC744 \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.";

  function createProjectRelatedBodyRuntime({
    getProjectRelatedController,
    getReportPanelsController,
    getExistingReportPanelsController,
    relatedNoticeRuntime,
    escapeHtml,
  } = {}) {
    function resolveReportPanelsController() {
      return getExistingReportPanelsController?.() || getReportPanelsController?.() || null;
    }

    function formatNoticeViewerSourceLabel(value) {
      return relatedNoticeRuntime?.formatNoticeViewerSourceLabel?.(value) || NOTICE_VIEWER_TITLE;
    }

    function renderNoticeViewerWindow(targetWindow, { title = NOTICE_VIEWER_TITLE, meta = "", body = "" } = {}) {
      const controller = resolveReportPanelsController();
      if (controller?.renderNoticeViewerWindow) {
        return controller.renderNoticeViewerWindow(targetWindow, { title, meta, body });
      }
      return renderNoticeViewerWindowFallback({
        targetWindow,
        title,
        meta,
        body,
        relatedNoticeRuntime,
        escapeHtml,
      });
    }

    function renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle = NOTICE_VIEWER_TITLE) {
      const controller = resolveReportPanelsController();
      if (controller?.renderNoticeViewerPayload) {
        return controller.renderNoticeViewerPayload(viewerWindow, payload, fallbackTitle);
      }
      return renderNoticeViewerPayloadFallback({
        viewerWindow,
        payload,
        fallbackTitle,
        renderNoticeViewerWindow,
        relatedNoticeRuntime,
        escapeHtml,
        formatNoticeViewerSourceLabel,
      });
    }

    function renderNoticeViewerError(viewerWindow, { title = NOTICE_VIEWER_TITLE, errorMessage = "", links = [] } = {}) {
      const controller = resolveReportPanelsController();
      if (controller?.renderNoticeViewerError) {
        return controller.renderNoticeViewerError(viewerWindow, { title, errorMessage, links });
      }
      return renderNoticeViewerErrorFallback({
        viewerWindow,
        title,
        errorMessage,
        links,
        renderNoticeViewerWindow,
        escapeHtml,
      });
    }

    function hydrateProjectRelatedPayloadCache() {
      return getProjectRelatedController?.()?.hydrateProjectRelatedPayloadCache?.();
    }

    function persistProjectRelatedPayloadCache() {
      return getProjectRelatedController?.()?.persistProjectRelatedPayloadCache?.();
    }

    return {
      renderNoticeViewerPayload,
      renderNoticeViewerError,
      renderNoticeViewerWindow,
      formatNoticeViewerSourceLabel,
      hydrateProjectRelatedPayloadCache,
      persistProjectRelatedPayloadCache,
    };
  }

  function renderNoticeViewerPayloadFallback({
    viewerWindow,
    payload,
    fallbackTitle = NOTICE_VIEWER_TITLE,
    renderNoticeViewerWindow,
    relatedNoticeRuntime,
    escapeHtml,
    formatNoticeViewerSourceLabel,
  } = {}) {
    if (!viewerWindow || viewerWindow.closed) return;
    const documentsMarkup = relatedNoticeRuntime?.buildNoticeViewerDocumentsMarkup?.(
      payload,
      { escapeHtml, formatNoticeViewerSourceLabel },
    ) || `<p class="notice-viewer-state">${NOTICE_VIEWER_LOAD_ERROR}</p>`;
    return renderNoticeViewerWindow(viewerWindow, {
      title: payload?.title || fallbackTitle,
      meta: [
        payload?.project_name || "",
        payload?.bid_no ? `${payload.bid_no}${payload?.bid_ord ? ` / ${payload.bid_ord}` : ""}` : "",
        payload?.document_count ? `\uBB38\uC11C ${payload.document_count}\uAC74` : "",
      ].filter(Boolean).join(" | "),
      body: documentsMarkup,
    });
  }

  function renderNoticeViewerErrorFallback({
    viewerWindow,
    title = NOTICE_VIEWER_TITLE,
    errorMessage = "",
    renderNoticeViewerWindow,
    escapeHtml,
  } = {}) {
    if (!viewerWindow || viewerWindow.closed) return;
    return renderNoticeViewerWindow(viewerWindow, {
      title,
      body: ` <p class="notice-viewer-state">${NOTICE_VIEWER_OPEN_ERROR}</p> <p class="notice-viewer-error">${escapeHtml(errorMessage || "viewer load failed")}</p> `,
    });
  }

  function renderNoticeViewerWindowFallback({
    targetWindow,
    title = NOTICE_VIEWER_TITLE,
    meta = "",
    body = "",
    relatedNoticeRuntime,
    escapeHtml,
  } = {}) {
    if (!targetWindow || targetWindow.closed) return;
    targetWindow.document.open();
    targetWindow.document.write(
      relatedNoticeRuntime?.buildNoticeViewerHtml?.({ title, meta, body }, { escapeHtml }) || "",
    );
    targetWindow.document.close();
  }

  global.SPMSProjectRelatedAppRuntime = {
    createProjectRelatedBodyRuntime,
    renderNoticeViewerPayloadFallback,
    renderNoticeViewerErrorFallback,
    renderNoticeViewerWindowFallback,
  };
})(typeof window !== "undefined" ? window : globalThis);
