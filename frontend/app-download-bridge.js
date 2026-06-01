export function createAppDownloadBridge(context = {}) {
  const {
    callDownloadController = null,
  } = context;

  function requireDownloadControllerCall() {
    if (typeof callDownloadController !== "function") {
      throw new Error("callDownloadController is required before app.js loads");
    }
    return callDownloadController;
  }

  function showDownloadProgressOverlay(
    stages = [
      "서버에서 파일을 준비하는 중입니다.",
      "엑셀 데이터를 정리하는 중입니다.",
      "엑셀 파일을 마무리하는 중입니다.",
    ],
    title = "엑셀 다운로드를 준비하고 있습니다.",
  ) {
    return requireDownloadControllerCall()("showDownloadProgressOverlay", stages, title);
  }

  function updateDownloadProgressOverlay(message) {
    return requireDownloadControllerCall()("updateDownloadProgressOverlay", message);
  }

  function hideDownloadProgressOverlay() {
    return requireDownloadControllerCall()("hideDownloadProgressOverlay");
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
    return requireDownloadControllerCall()("triggerFileDownload", url, {
      button,
      busyLabel,
      fallbackName,
      showProgressOverlay,
      progressTitle,
      progressStages,
    });
  }

  function downloadSalesWorkbook(scope, button = null) {
    return requireDownloadControllerCall()("downloadSalesWorkbook", scope, button);
  }

  function buildTrackerEntriesDownloadUrl(format) {
    return requireDownloadControllerCall()("buildTrackerEntriesDownloadUrl", format);
  }

  function buildTrackerEntriesDownloadWarmUrl() {
    return requireDownloadControllerCall()("buildTrackerEntriesDownloadWarmUrl");
  }

  async function warmTrackerEntriesDownload() {
    return requireDownloadControllerCall()("warmTrackerEntriesDownload");
  }

  return {
    showDownloadProgressOverlay,
    updateDownloadProgressOverlay,
    hideDownloadProgressOverlay,
    triggerFileDownload,
    downloadSalesWorkbook,
    buildTrackerEntriesDownloadUrl,
    buildTrackerEntriesDownloadWarmUrl,
    warmTrackerEntriesDownload,
  };
}

const appDownloadBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appDownloadBridgeRoot.APP_DOWNLOAD_BRIDGE = appDownloadBridgeRoot.APP_DOWNLOAD_BRIDGE || {};
appDownloadBridgeRoot.APP_DOWNLOAD_BRIDGE.createAppDownloadBridge = createAppDownloadBridge;
