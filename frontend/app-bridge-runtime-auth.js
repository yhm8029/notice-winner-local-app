(function attachAppBridgeRuntimeAuth(global) {
  function requireHelpers() {
    const helpers = global.SPMSAppBridgeRuntimeHelpers;
    if (!helpers) {
      throw new Error("SPMSAppBridgeRuntimeHelpers is required before app.js loads");
    }
    return helpers;
  }

  function createAppAuthBridgeSection(options = {}) {
    const { createRequiredBridge } = requireHelpers();
    const appAuthBridge = createRequiredBridge(
      options.APP_AUTH_BRIDGE,
      "createAppAuthBridge",
      {
        callAuthController: options.callAuthController,
        callAuthUiController: options.callAuthUiController,
      },
      "APP_AUTH_BRIDGE.createAppAuthBridge is required before app.js loads",
    );

    return {
      appAuthBridge,
      initializeAuthGate: appAuthBridge.initializeAuthGate,
      loadInvitationPreview: appAuthBridge.loadInvitationPreview,
      loadInvitationPreviewByEmail: appAuthBridge.loadInvitationPreviewByEmail,
      scheduleInvitationPreviewLookup: appAuthBridge.scheduleInvitationPreviewLookup,
      importAuthSessionFromLocationHash: appAuthBridge.importAuthSessionFromLocationHash,
      acceptPendingInvitationToken: appAuthBridge.acceptPendingInvitationToken,
      applyAuthSession: appAuthBridge.applyAuthSession,
      refreshAuthSessionState: appAuthBridge.refreshAuthSessionState,
      syncAuthFormWithInvitationPreview: appAuthBridge.syncAuthFormWithInvitationPreview,
      renderAuthInvitationPreview: appAuthBridge.renderAuthInvitationPreview,
      renderAuthUi: appAuthBridge.renderAuthUi,
      renderProfileStatus: appAuthBridge.renderProfileStatus,
      syncProfileDialogWithSession: appAuthBridge.syncProfileDialogWithSession,
      openProfileDialog: appAuthBridge.openProfileDialog,
      closeProfileDialog: appAuthBridge.closeProfileDialog,
      handleProfileSubmit: appAuthBridge.handleProfileSubmit,
      handleAuthSubmit: appAuthBridge.handleAuthSubmit,
      handleAuthPasswordReset: appAuthBridge.handleAuthPasswordReset,
      handleAuthSignOut: appAuthBridge.handleAuthSignOut,
      setAuthMode: appAuthBridge.setAuthMode,
      syncUiModeChrome: appAuthBridge.syncUiModeChrome,
      applyUiModeTransition: appAuthBridge.applyUiModeTransition,
    };
  }

  global.SPMSAppBridgeRuntimeAuth = {
    createAppAuthBridgeSection,
  };
})(typeof window !== "undefined" ? window : globalThis);
