export function createAppAuthBridge(context = {}) {
  const {
    callAuthController = null,
    callAuthUiController = null,
  } = context;

  function requireAuthControllerCall() {
    if (typeof callAuthController !== "function") {
      throw new Error("callAuthController is required before app.js loads");
    }
    return callAuthController;
  }

  function requireAuthUiControllerCall() {
    if (typeof callAuthUiController !== "function") {
      throw new Error("callAuthUiController is required before app.js loads");
    }
    return callAuthUiController;
  }

  function initializeAuthGate(options = {}) {
    return requireAuthControllerCall()("initializeAuthGate", options);
  }

  function loadInvitationPreview(options = {}) {
    return requireAuthControllerCall()("loadInvitationPreview", options);
  }

  function loadInvitationPreviewByEmail(email, options = {}) {
    return requireAuthControllerCall()("loadInvitationPreviewByEmail", email, options);
  }

  function scheduleInvitationPreviewLookup(email) {
    return requireAuthControllerCall()("scheduleInvitationPreviewLookup", email);
  }

  function importAuthSessionFromLocationHash() {
    return requireAuthControllerCall()("importAuthSessionFromLocationHash");
  }

  function acceptPendingInvitationToken(options = {}) {
    return requireAuthControllerCall()("acceptPendingInvitationToken", options);
  }

  function applyAuthSession(session) {
    return requireAuthUiControllerCall()("applyAuthSession", session);
  }

  function refreshAuthSessionState({ silent = false } = {}) {
    return requireAuthControllerCall()("refreshAuthSessionState", { silent });
  }

  function syncAuthFormWithInvitationPreview() {
    return requireAuthUiControllerCall()("syncAuthFormWithInvitationPreview");
  }

  function renderAuthInvitationPreview() {
    return requireAuthUiControllerCall()("renderAuthInvitationPreview");
  }

  function renderAuthUi() {
    return requireAuthUiControllerCall()("renderAuthUi");
  }

  function renderProfileStatus(message = "", level = "") {
    return requireAuthUiControllerCall()("renderProfileStatus", message, level);
  }

  function syncProfileDialogWithSession() {
    return requireAuthUiControllerCall()("syncProfileDialogWithSession");
  }

  function openProfileDialog() {
    return requireAuthUiControllerCall()("openProfileDialog");
  }

  function closeProfileDialog() {
    return requireAuthUiControllerCall()("closeProfileDialog");
  }

  function handleProfileSubmit(event) {
    return requireAuthUiControllerCall()("handleProfileSubmit", event);
  }

  function handleAuthSubmit(event) {
    return requireAuthControllerCall()("handleAuthSubmit", event);
  }

  function handleAuthPasswordReset() {
    return requireAuthControllerCall()("handleAuthPasswordReset");
  }

  function handleAuthSignOut() {
    return requireAuthControllerCall()("handleAuthSignOut");
  }

  function setAuthMode(mode) {
    return requireAuthControllerCall()("setAuthMode", mode);
  }

  function syncUiModeChrome() {
    return requireAuthControllerCall()("syncUiModeChrome");
  }

  function applyUiModeTransition(adminMode, options = {}) {
    return requireAuthControllerCall()("applyUiModeTransition", adminMode, options);
  }

  return {
    initializeAuthGate,
    loadInvitationPreview,
    loadInvitationPreviewByEmail,
    scheduleInvitationPreviewLookup,
    importAuthSessionFromLocationHash,
    acceptPendingInvitationToken,
    applyAuthSession,
    refreshAuthSessionState,
    syncAuthFormWithInvitationPreview,
    renderAuthInvitationPreview,
    renderAuthUi,
    renderProfileStatus,
    syncProfileDialogWithSession,
    openProfileDialog,
    closeProfileDialog,
    handleProfileSubmit,
    handleAuthSubmit,
    handleAuthPasswordReset,
    handleAuthSignOut,
    setAuthMode,
    syncUiModeChrome,
    applyUiModeTransition,
  };
}

const appAuthBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appAuthBridgeRoot.APP_AUTH_BRIDGE = appAuthBridgeRoot.APP_AUTH_BRIDGE || {};
appAuthBridgeRoot.APP_AUTH_BRIDGE.createAppAuthBridge = createAppAuthBridge;
