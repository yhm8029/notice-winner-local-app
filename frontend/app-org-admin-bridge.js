export function createAppOrgAdminBridge(context = {}) {
  const {
    callOrgAdminController = null,
  } = context;

  function mergeOrganizationInvitationItem(existingItem, nextItem) {
    return callOrgAdminController("mergeOrganizationInvitationItem", existingItem, nextItem);
  }

  function mergeOrganizationInvitations(items, existingItems) {
    return callOrgAdminController("mergeOrganizationInvitations", items, existingItems);
  }

  function upsertOrganizationInvitation(item) {
    return callOrgAdminController("upsertOrganizationInvitation", item);
  }

  function removeOrganizationInvitation(invitationId) {
    return callOrgAdminController("removeOrganizationInvitation", invitationId);
  }

  function scheduleOrganizationInvitationSync(delayMs = 1500) {
    return callOrgAdminController("scheduleOrganizationInvitationSync", delayMs);
  }

  function getRenderableOrgRoleOptions(currentRole = "") {
    return callOrgAdminController("getRenderableOrgRoleOptions", currentRole);
  }

  function getCurrentAuthLocalUserId() {
    return callOrgAdminController("getCurrentAuthLocalUserId");
  }

  function isProtectedOrganizationMember(member) {
    return callOrgAdminController("isProtectedOrganizationMember", member);
  }

  function canInviteOrganizationAdmins() {
    return callOrgAdminController("canInviteOrganizationAdmins");
  }

  function getAllowedInvitationRoleOptions() {
    return callOrgAdminController("getAllowedInvitationRoleOptions");
  }

  function syncInvitationRoleOptions() {
    return callOrgAdminController("syncInvitationRoleOptions");
  }

  function getOrganizationPlanSummaryForDisplay() {
    return callOrgAdminController("getOrganizationPlanSummaryForDisplay");
  }

  function formatAuthAuditEventLabel(eventType) {
    return callOrgAdminController("formatAuthAuditEventLabel", eventType);
  }

  function formatAuthAuditActorLabel(item) {
    return callOrgAdminController("formatAuthAuditActorLabel", item);
  }

  function formatDownloadScopeLabel(value) {
    return callOrgAdminController("formatDownloadScopeLabel", value);
  }

  function formatDownloadFormatLabel(value) {
    return callOrgAdminController("formatDownloadFormatLabel", value);
  }

  function formatDownloadSourcePageLabel(value) {
    return callOrgAdminController("formatDownloadSourcePageLabel", value);
  }

  function bindOrganizationAdminAuditActions(options = {}) {
    return callOrgAdminController("bindOrganizationAdminAuditActions", options);
  }

  function renderOrganizationAdminPanel() {
    return callOrgAdminController("renderOrganizationAdminPanel");
  }

  async function loadOrganizationUsers({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationUsers", { silent });
  }

  async function loadOrganizationMembers({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationMembers", { silent });
  }

  async function loadOrganizationInvitations({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationInvitations", { silent });
  }

  async function loadOrganizationAuditLogs({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationAuditLogs", { silent });
  }

  async function loadOrganizationDownloadAuditLogs({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationDownloadAuditLogs", { silent });
  }

  async function loadOrganizationLoginAuditLogs({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationLoginAuditLogs", { silent });
  }

  function loadOrganizationAdminData({ silent = false } = {}) {
    return callOrgAdminController("loadOrganizationAdminData", { silent });
  }

  async function handleInvitationSubmit(event) {
    return callOrgAdminController("handleInvitationSubmit", event);
  }

  async function copyInvitationUrl(inviteUrl) {
    return callOrgAdminController("copyInvitationUrl", inviteUrl);
  }

  async function revokeOrganizationInvitation(invitationId) {
    return callOrgAdminController("revokeOrganizationInvitation", invitationId);
  }

  async function saveOrganizationMember(userId, article) {
    return callOrgAdminController("saveOrganizationMember", userId, article);
  }

  async function deleteOrganizationMember(userId, article) {
    return callOrgAdminController("deleteOrganizationMember", userId, article);
  }

  return {
    mergeOrganizationInvitationItem,
    mergeOrganizationInvitations,
    upsertOrganizationInvitation,
    removeOrganizationInvitation,
    scheduleOrganizationInvitationSync,
    getRenderableOrgRoleOptions,
    getCurrentAuthLocalUserId,
    isProtectedOrganizationMember,
    canInviteOrganizationAdmins,
    getAllowedInvitationRoleOptions,
    syncInvitationRoleOptions,
    getOrganizationPlanSummaryForDisplay,
    formatAuthAuditEventLabel,
    formatAuthAuditActorLabel,
    formatDownloadScopeLabel,
    formatDownloadFormatLabel,
    formatDownloadSourcePageLabel,
    bindOrganizationAdminAuditActions,
    renderOrganizationAdminPanel,
    loadOrganizationUsers,
    loadOrganizationMembers,
    loadOrganizationInvitations,
    loadOrganizationAuditLogs,
    loadOrganizationDownloadAuditLogs,
    loadOrganizationLoginAuditLogs,
    loadOrganizationAdminData,
    handleInvitationSubmit,
    copyInvitationUrl,
    revokeOrganizationInvitation,
    saveOrganizationMember,
    deleteOrganizationMember,
  };
}

const appOrgAdminBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appOrgAdminBridgeRoot.APP_ORG_ADMIN_BRIDGE = appOrgAdminBridgeRoot.APP_ORG_ADMIN_BRIDGE || {};
appOrgAdminBridgeRoot.APP_ORG_ADMIN_BRIDGE.createAppOrgAdminBridge = createAppOrgAdminBridge;
