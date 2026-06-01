export function createAppSalesBridge(context = {}) {
  const {
    state = null,
    callSalesPanelController = null,
  } = context;

  function openSalesCloseDialog(projectId) {
    return callSalesPanelController("openSalesCloseDialog", projectId);
  }

  function closeSalesCloseDialog() {
    return callSalesPanelController("closeSalesCloseDialog");
  }

  async function confirmSalesCloseDialog() {
    return callSalesPanelController("confirmSalesCloseDialog");
  }

  function getVisibleSalesProjectIds(entries = state.trackerEntries) {
    return callSalesPanelController("getVisibleSalesProjectIds", entries);
  }

  function getSalesClaimForProject(projectId) {
    return callSalesPanelController("getSalesClaimForProject", projectId);
  }

  function getTrackerProjectSnapshot(projectId) {
    return callSalesPanelController("getTrackerProjectSnapshot", projectId);
  }

  function renderUserSalesProjectFacts(snapshot, estimatedAmountText = "-") {
    return callSalesPanelController("renderUserSalesProjectFacts", snapshot, estimatedAmountText);
  }

  function isCurrentUserClaimOwner(claim) {
    return callSalesPanelController("isCurrentUserClaimOwner", claim);
  }

  function canCurrentUserForceRelease() {
    return callSalesPanelController("canCurrentUserForceRelease");
  }

  function canCurrentUserManageClaim(claim) {
    return callSalesPanelController("canCurrentUserManageClaim", claim);
  }

  function isActiveSalesClaim(claim) {
    return callSalesPanelController("isActiveSalesClaim", claim);
  }

  function getOrganizationTransferTargets(claim) {
    return callSalesPanelController("getOrganizationTransferTargets", claim);
  }

  function getSalesNoteDraft(projectId, claim) {
    return callSalesPanelController("getSalesNoteDraft", projectId, claim);
  }

  function setSalesNoteDraft(projectId, value) {
    return callSalesPanelController("setSalesNoteDraft", projectId, value);
  }

  function upsertSalesClaim(claim) {
    return callSalesPanelController("upsertSalesClaim", claim);
  }

  function replaceVisibleSalesClaims(items) {
    return callSalesPanelController("replaceVisibleSalesClaims", items);
  }

  function mergeActiveSalesClaims(items) {
    return callSalesPanelController("mergeActiveSalesClaims", items);
  }

  function renderSalesSummaryPanel() {
    return callSalesPanelController("renderSalesSummaryPanel");
  }

  function renderClosedSalesArchiveSection(title, claims, { showContractAmount = false } = {}) {
    return callSalesPanelController("renderClosedSalesArchiveSection", title, claims, { showContractAmount });
  }

  function renderMySalesClaimsPanel() {
    return callSalesPanelController("renderMySalesClaimsPanel");
  }

  function renderUserOwnedSalesClaimCard(claim, index) {
    return callSalesPanelController("renderUserOwnedSalesClaimCard", claim, index);
  }

  function formatSalesClaimEstimateLabel(claim) {
    return callSalesPanelController("formatSalesClaimEstimateLabel", claim);
  }

  function renderCompanySalesClaimCard(claim, index) {
    return callSalesPanelController("renderCompanySalesClaimCard", claim, index);
  }

  function renderUserTrackerClaimSection(entry, { projectId, claim, saving }) {
    return callSalesPanelController("renderUserTrackerClaimSection", entry, { projectId, claim, saving });
  }

  function claimSalesProject(entry) {
    return callSalesPanelController("claimSalesProject", entry);
  }

  function saveSalesClaimNote(projectId) {
    return callSalesPanelController("saveSalesClaimNote", projectId);
  }

  function transferSalesClaim(projectId, targetUserId) {
    return callSalesPanelController("transferSalesClaim", projectId, targetUserId);
  }

  function closeSalesClaim(projectId, outcome, options = {}) {
    return callSalesPanelController("closeSalesClaim", projectId, outcome, options);
  }

  function adminDeleteLatestSalesNote(projectId, rawSalesNote) {
    return callSalesPanelController("adminDeleteLatestSalesNote", projectId, rawSalesNote);
  }

  function releaseSalesClaim(projectId, options = {}) {
    return callSalesPanelController("releaseSalesClaim", projectId, options);
  }

  function bindUserSalesSectionEvents() {
    return callSalesPanelController("bindUserSalesSectionEvents");
  }

  function formatEstimatedAmountRangeFromKrw(low, high, fallback = "-") {
    return callSalesPanelController("formatEstimatedAmountRangeFromKrw", low, high, fallback);
  }

  function renderSalesClaimSection(entry) {
    return callSalesPanelController("renderSalesClaimSection", entry);
  }

  return {
    openSalesCloseDialog,
    closeSalesCloseDialog,
    confirmSalesCloseDialog,
    getVisibleSalesProjectIds,
    getSalesClaimForProject,
    getTrackerProjectSnapshot,
    renderUserSalesProjectFacts,
    isCurrentUserClaimOwner,
    canCurrentUserForceRelease,
    canCurrentUserManageClaim,
    isActiveSalesClaim,
    getOrganizationTransferTargets,
    getSalesNoteDraft,
    setSalesNoteDraft,
    upsertSalesClaim,
    replaceVisibleSalesClaims,
    mergeActiveSalesClaims,
    renderSalesSummaryPanel,
    renderClosedSalesArchiveSection,
    renderMySalesClaimsPanel,
    renderUserOwnedSalesClaimCard,
    formatSalesClaimEstimateLabel,
    renderCompanySalesClaimCard,
    renderUserTrackerClaimSection,
    claimSalesProject,
    saveSalesClaimNote,
    transferSalesClaim,
    closeSalesClaim,
    adminDeleteLatestSalesNote,
    releaseSalesClaim,
    bindUserSalesSectionEvents,
    formatEstimatedAmountRangeFromKrw,
    renderSalesClaimSection,
  };
}

const appSalesBridgeRoot = typeof window !== "undefined" ? window : globalThis;
appSalesBridgeRoot.APP_SALES_BRIDGE = appSalesBridgeRoot.APP_SALES_BRIDGE || {};
appSalesBridgeRoot.APP_SALES_BRIDGE.createAppSalesBridge = createAppSalesBridge;
