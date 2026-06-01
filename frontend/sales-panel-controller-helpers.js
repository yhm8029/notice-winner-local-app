export function createSalesPanelControllerHelpers(deps = {}) {
  const {
    state,
    escapeHtml,
    buildUserSalesProjectFactsMarkup,
    formatEokValue,
    isAdminRole,
  } = deps;

  function getVisibleSalesProjectIds(entries = state.trackerEntries) {
    return [...new Set(
      (entries || [])
        .map((entry) => String(entry.project_id || "").trim())
        .filter(Boolean)
    )];
  }

  function getSalesClaimForProject(projectId) {
    if (!projectId) {
      return null;
    }
    const key = String(projectId);
    return (
      state.salesClaimsByProjectId[key]
      || state.mySalesClaims.find((claim) => String(claim?.project_id || "") === key)
      || state.companySalesClaims.find((claim) => String(claim?.project_id || "") === key)
      || null
    );
  }

  function getTrackerProjectSnapshot(projectId) {
    const key = String(projectId || "").trim();
    if (!key) {
      return null;
    }
    const summaryEntry = state.trackerEntries.find((entry) => String(entry.project_id || "").trim() === key);
    if (summaryEntry) {
      return summaryEntry;
    }
    if (state.selectedEntry && String(state.selectedEntry.project_id || "").trim() === key) {
      return state.selectedEntry;
    }
    return null;
  }

  function renderUserSalesProjectFacts(snapshot, estimatedAmountText = "-") {
    return buildUserSalesProjectFactsMarkup(snapshot, estimatedAmountText);
  }

  function isCurrentUserClaimOwner(claim) {
    if (!claim || !state.auth.user) {
      return false;
    }
    const currentUserId = String(state.auth.user.local_user_id || "").trim();
    const currentEmail = String(state.auth.user.email || "").trim().toLowerCase();
    if (currentUserId && String(claim.owner_user_id || "").trim() === currentUserId) {
      return true;
    }
    return Boolean(currentEmail && String(claim.owner_email || "").trim().toLowerCase() === currentEmail);
  }

  function canCurrentUserForceRelease() {
    return isAdminRole(state.auth.user?.role);
  }

  function canCurrentUserManageClaim(claim) {
    return isCurrentUserClaimOwner(claim) || canCurrentUserForceRelease();
  }

  function isActiveSalesClaim(claim) {
    return Boolean(claim && claim.is_active && String(claim.claim_status || "active") === "active");
  }

  function getOrganizationTransferTargets(claim) {
    const currentUserId = String(claim?.owner_user_id || "").trim();
    const currentEmail = String(claim?.owner_email || "").trim().toLowerCase();
    return (state.organizationUsers || []).filter((item) => {
      const itemId = String(item.id || "").trim();
      const itemEmail = String(item.email || "").trim().toLowerCase();
      if (currentUserId && itemId === currentUserId) {
        return false;
      }
      if (currentEmail && itemEmail === currentEmail) {
        return false;
      }
      return String(item.status || "active") === "active";
    });
  }

  function getSalesNoteDraft(projectId) {
    const key = String(projectId || "").trim();
    if (!key) {
      return "";
    }
    if (Object.prototype.hasOwnProperty.call(state.salesClaimDrafts, key)) {
      return state.salesClaimDrafts[key];
    }
    return "";
  }

  function setSalesNoteDraft(projectId, value) {
    const key = String(projectId || "").trim();
    if (!key) {
      return;
    }
    state.salesClaimDrafts[key] = String(value || "");
  }

  function upsertSalesClaim(claim) {
    const key = String(claim?.project_id || "").trim();
    if (!key) {
      return;
    }
    if (!claim.is_active) {
      delete state.salesClaimsByProjectId[key];
      delete state.salesClaimDrafts[key];
      return;
    }
    state.salesClaimsByProjectId[key] = claim;
  }

  function replaceVisibleSalesClaims(items) {
    const previousDrafts = { ...state.salesClaimDrafts };
    const visibleKeys = new Set(getVisibleSalesProjectIds());
    for (const key of visibleKeys) {
      delete state.salesClaimsByProjectId[key];
      delete state.salesClaimDrafts[key];
    }
    for (const item of items || []) {
      upsertSalesClaim(item);
      const key = String(item?.project_id || "").trim();
      if (key && Object.prototype.hasOwnProperty.call(previousDrafts, key) && isCurrentUserClaimOwner(item)) {
        state.salesClaimDrafts[key] = previousDrafts[key];
      }
    }
  }

  function mergeActiveSalesClaims(items) {
    for (const item of items || []) {
      upsertSalesClaim(item);
    }
  }

  function formatEstimatedAmountRangeFromKrw(low, high, fallback = "-") {
    const lowValue = Number(low);
    const highValue = Number(high);
    if (!Number.isFinite(lowValue) && !Number.isFinite(highValue)) {
      return fallback;
    }
    const safeLow = Number.isFinite(lowValue) ? lowValue : highValue;
    const safeHigh = Number.isFinite(highValue) ? highValue : lowValue;
    const lowEok = formatEokValue(safeLow / 100000000);
    const highEok = formatEokValue(safeHigh / 100000000);
    if (Math.abs(safeLow - safeHigh) < 1) {
      return `${lowEok}?듭썝`;
    }
    return `${lowEok}~${highEok}?듭썝`;
  }

  return {
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
    formatEstimatedAmountRangeFromKrw,
  };
}
