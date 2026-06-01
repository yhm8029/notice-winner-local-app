export function createSalesPanelControllerViewModelHelpers(deps = {}) {
  const {
    state,
    escapeHtml,
    formatSalesDateLabel,
    salesClaimStatusLabel,
    formatContractAmountDisplay,
    extractContractAmountTextFromSalesNote,
    truncate,
    formatSalesNoteTextForDisplay,
    getLatestSalesNoteItem,
    getSalesNoteTimeline,
    getTrackerProjectSnapshot,
    getOrganizationTransferTargets,
    getSalesNoteDraft,
    isCurrentUserClaimOwner,
    canCurrentUserManageClaim,
    buildSalesClaimEstimateLabelMarkup,
    buildUserOwnedSalesClaimCardMarkup,
    buildCompanySalesClaimCardMarkup,
    buildUserTrackerClaimSectionMarkup,
    normalizeSalesClaimCardViewModel,
    salesViewRuntime = null,
  } = deps;

  function renderUserOwnedSalesClaimCard(claim, index) {
    const projectId = String(claim.project_id || "").trim();
    const saving = Boolean(state.salesClaimSavingProjectIds[projectId]);
    const noteDraft = getSalesNoteDraft(projectId, claim);
    const noteEntries = getSalesNoteTimeline(claim.sales_note, claim.claimed_at);
    const snapshot = getTrackerProjectSnapshot(projectId);
    const transferTargets = getOrganizationTransferTargets(claim);
    const viewModelInput = {
      claim,
      index,
      projectId,
      saving,
      noteDraft,
      noteEntries,
      snapshot,
      transferTargets,
      organizationUsersLoading: state.organizationUsersLoading,
    };
    const payload = salesViewRuntime?.buildUserOwnedSalesClaimCardViewModel?.(viewModelInput)
      || salesViewRuntime?.normalizeSalesClaimCardViewModel?.(viewModelInput)
      || normalizeSalesClaimCardViewModel(viewModelInput, {
        shouldShowCurrentOwnerAssignedAt: salesViewRuntime?.shouldShowCurrentOwnerAssignedAt,
      });
    return buildUserOwnedSalesClaimCardMarkup(payload);
  }

  function formatSalesClaimEstimateLabel(claim) {
    return buildSalesClaimEstimateLabelMarkup(claim);
  }

  function renderCompanySalesClaimCard(claim, index) {
    const noteEntries = getSalesNoteTimeline(claim.sales_note, claim.claimed_at);
    const snapshot = getTrackerProjectSnapshot(claim.project_id);
    const viewModelInput = {
      claim,
      index,
      noteEntries,
      snapshot,
    };
    const payload = salesViewRuntime?.buildCompanySalesClaimCardViewModel?.(viewModelInput)
      || salesViewRuntime?.normalizeSalesClaimCardViewModel?.(viewModelInput, { includeOwnerLabel: true })
      || normalizeSalesClaimCardViewModel(viewModelInput, {
        includeOwnerLabel: true,
        shouldShowCurrentOwnerAssignedAt: salesViewRuntime?.shouldShowCurrentOwnerAssignedAt,
      });
    return buildCompanySalesClaimCardMarkup(payload);
  }

  function renderUserTrackerClaimSection(entry, {
    projectId,
    claim,
    saving,
  }) {
    return buildUserTrackerClaimSectionMarkup({ entry, projectId, claim, saving });
  }

  function renderSalesClaimSection(entry) {
    const projectId = String(entry.project_id || "").trim();
    const claim = state.salesClaimsByProjectId[projectId] || null;
    const ownerMatch = isCurrentUserClaimOwner(claim);
    const canManage = canCurrentUserManageClaim(claim);
    const saving = Boolean(state.salesClaimSavingProjectIds[projectId]);
    const noteDraft = getSalesNoteDraft(projectId, claim);
    const noteEntries = getSalesNoteTimeline(claim?.sales_note, claim?.claimed_at);
    const claimStatus = String(claim?.claim_status || "active").trim();
    const isClosed = Boolean(claim && claimStatus !== "active");
    const transferTargets = claim ? getOrganizationTransferTargets(claim) : [];
    const showAssignedAt = salesViewRuntime?.shouldShowCurrentOwnerAssignedAt?.(claim) || Boolean(
      claim?.current_owner_assigned_at
        && claim?.claimed_at
        && String(claim.current_owner_assigned_at).trim() !== String(claim.claimed_at).trim()
    );

    if (state.uiMode === "user") {
      return renderUserTrackerClaimSection(entry, {
        projectId,
        claim,
        ownerMatch,
        saving,
        isClosed,
        showAssignedAt,
      });
    }
    const payload = salesViewRuntime?.buildAdminSalesClaimSectionViewModel?.({
      entry,
      claim,
      projectId,
      saving,
      noteDraft,
      noteEntries,
      claimStatus,
      isClosed,
      transferTargets,
      showAssignedAt,
      ownerMatch,
      canManage,
      statusText: salesClaimStatusLabel(claimStatus),
      claimedAtLabel: claim ? formatSalesDateLabel(claim.claimed_at) : "-",
      currentOwnerAssignedAtLabel: claim ? formatSalesDateLabel(claim.current_owner_assigned_at) : "-",
      closedAtLabel: claim ? formatSalesDateLabel(claim.closed_at) : "-",
      organizationUsersLoading: state.organizationUsersLoading,
    }) || {
      entry,
      claim,
      projectId,
      saving,
      noteDraft,
      noteEntries,
      claimStatus,
      isClosed,
      transferTargets,
      showAssignedAt,
      ownerMatch,
      canManage,
      statusText: salesClaimStatusLabel(claimStatus),
      claimedAtLabel: claim ? formatSalesDateLabel(claim.claimed_at) : "-",
      currentOwnerAssignedAtLabel: claim ? formatSalesDateLabel(claim.current_owner_assigned_at) : "-",
      closedAtLabel: claim ? formatSalesDateLabel(claim.closed_at) : "-",
      organizationUsersLoading: state.organizationUsersLoading,
    };
    return salesViewRuntime?.buildAdminSalesClaimSectionMarkup?.(
      payload,
      {
        escapeHtml,
        buildSalesTransferOptionsMarkup: (items, options) => salesViewRuntime?.buildSalesTransferOptionsMarkup?.(items, options, { escapeHtml }) || "",
        buildRawSalesNoteTimelineMarkup: (items) => salesViewRuntime?.buildRawSalesNoteTimelineMarkup?.(items, { escapeHtml }) || "",
      },
    ) || "";
  }

  return {
    renderUserOwnedSalesClaimCard,
    formatSalesClaimEstimateLabel,
    renderCompanySalesClaimCard,
    renderUserTrackerClaimSection,
    renderSalesClaimSection,
  };
}
