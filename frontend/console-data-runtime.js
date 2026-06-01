(function attachConsoleDataRuntime(global) {
  const ORGANIZATION_ADMIN_READ_TIMEOUT_MS = 30000;
  async function loadVisibleSalesClaims(deps, { silent = false } = {}) {
    const projectIds = deps.getVisibleSalesProjectIds();
    if (!projectIds.length) {
      deps.state.salesClaimsByProjectId = {};
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
      return;
    }

    const params = new URLSearchParams();
    for (const projectId of projectIds) {
      params.append("project_id", projectId);
    }

    try {
      const response = await deps.api(`/api/sales-claims?${params.toString()}`, {
        timeoutMs: 15000,
        cacheBust: false,
      });
      deps.replaceVisibleSalesClaims(response.items || []);
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
    } catch (err) {
      deps.replaceVisibleSalesClaims([]);
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
      if (!silent) {
        deps.flash(err.message, "error");
      }
    }
  }

  async function loadHomeBootstrap(deps, { silent = false, force = false } = {}) {
    if (!deps.state.auth.enabled) {
      return loadHomeBootstrapFromLegacy(deps, { silent });
    }
    if (!deps.state.auth.authorized || !deps.state.auth.user) {
      return null;
    }
    if (deps.state.homeBootstrapAvailability === "missing_route" && !force) {
      const hasCachedBootstrap = deps.hasCachedHomeBootstrapData();
      if (hasCachedBootstrap) {
        return null;
      }
      return loadHomeBootstrapFromLegacy(deps, { silent });
    }
    if (deps.state.homeBootstrapRequest && !force) {
      return deps.state.homeBootstrapRequest;
    }
    const request = (async () => {
      try {
        const response = await deps.api("/api/home-bootstrap", {
          timeoutMs: 15000,
          cacheBust: false,
        });
        deps.state.homeBootstrapAvailability = "available";
        deps.applyHomeBootstrapPayload(response || {});
        deps.persistHomeBootstrapCache(response || {});
        deps.persistSalesOverviewCache(response || {});
        if (!deps.state.homeBootstrapTrackerSnapshotActive) {
          await deps.loadTrackerEntries({ silent });
        }
        return response;
      } catch (err) {
        const isMissingRoute = deps.isMissingHomeBootstrapEndpointError(err);
        if (isMissingRoute) {
          deps.state.homeBootstrapAvailability = "missing_route";
          console.warn("[home-bootstrap] legacy fallback", {
            status: err?.status || 0,
            path: err?.path || "/api/home-bootstrap",
            url: err?.url || "",
            message: err?.message || String(err || ""),
            payload: err?.payload || null,
          });
        } else {
          deps.state.homeBootstrapAvailability = "error";
          if (!silent) {
            deps.flash(err.message || "홈 부트스트랩을 불러오지 못했습니다.", "error");
          }
        }
        return loadHomeBootstrapFromLegacy(deps, { silent });
      } finally {
        deps.state.homeBootstrapRequest = null;
      }
    })();
    deps.state.homeBootstrapRequest = request;
    return request;
  }

  async function loadHomeBootstrapFromLegacy(deps, { silent = false } = {}) {
    deps.state.homeBootstrapTrackerSnapshotActive = false;
    await Promise.all([
      deps.loadTrackerEntries({ silent }),
      loadSalesOverview(deps, { silent }),
    ]);
    deps.persistHomeBootstrapCache({
      my_items: deps.state.mySalesClaims,
      company_items: deps.state.companySalesClaims,
      organization_users: deps.state.organizationUsers,
      tracker_first_page: {
        items: deps.state.trackerEntries,
        page: Number(deps.state.trackerFilters.page || 1) || 1,
        page_size: Number(deps.state.trackerFilters.pageSize || 20) || 20,
        total: Number(deps.state.trackerEntriesTotal || 0),
        sort_contract: {
          mode: "default",
          order_by: ["updated_at_desc", "id_desc"],
        },
      },
      generated_at: new Date().toISOString(),
      snapshot_version: 2,
    });
    return true;
  }

  async function loadSalesOverview(deps, { silent = false, force = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.state.auth.user) {
      deps.state.mySalesClaims = [];
      deps.state.companySalesClaims = [];
      deps.state.organizationUsers = [];
      deps.state.mySalesClaimsError = "";
      deps.state.mySalesClaimsLoading = false;
      deps.renderMySalesClaimsPanel();
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
      return;
    }

    const hasCachedOverview = deps.hasCachedSalesOverviewData();
    if (deps.state.salesOverviewAvailability === "missing_route") {
      if (hasCachedOverview && !force) {
        deps.state.mySalesClaimsLoading = false;
        deps.renderMySalesClaimsPanel();
        deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
        return;
      }
      return loadSalesOverviewFromLegacy(deps, { silent, persistCache: true });
    }

    if (deps.state.salesOverviewRequest && !force) {
      return deps.state.salesOverviewRequest;
    }

    const request = (async () => {
      let usedLegacyFallback = false;
      if (!hasCachedOverview) {
        deps.state.mySalesClaimsLoading = true;
        deps.renderMySalesClaimsPanel();
      }
      try {
        const response = await deps.api("/api/sales-claims/overview", {
          timeoutMs: 15000,
          cacheBust: false,
        });
        deps.state.salesOverviewAvailability = "available";
        deps.applySalesOverviewPayload(response || {});
        deps.persistSalesOverviewCache(response || {});
        deps.state.mySalesClaimsError = "";
      } catch (err) {
        if (deps.isMissingSalesOverviewEndpointError(err)) {
          deps.state.salesOverviewAvailability = "missing_route";
          console.warn("[sales-overview] legacy fallback", {
            status: err?.status || 0,
            path: err?.path || "/api/sales-claims/overview",
            url: err?.url || "",
            message: err?.message || String(err || ""),
            payload: err?.payload || null,
          });
          usedLegacyFallback = await loadSalesOverviewFromLegacy(deps, { silent: true, persistCache: true });
          deps.state.mySalesClaimsError = "";
        } else if (!hasCachedOverview) {
          deps.state.salesOverviewAvailability = "error";
          deps.state.mySalesClaims = [];
          deps.state.companySalesClaims = [];
          deps.state.organizationUsers = [];
          deps.state.mySalesClaimsError = err.message || "영업 개요를 불러오지 못했습니다.";
        }
        if (!silent && !hasCachedOverview && !usedLegacyFallback) {
          deps.flash(err.message, "error");
        }
      } finally {
        deps.state.mySalesClaimsLoading = false;
        deps.renderMySalesClaimsPanel();
        deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
        deps.state.salesOverviewRequest = null;
      }
    })();
    deps.state.salesOverviewRequest = request;
    return request;
  }

  async function loadSalesOverviewFromLegacy(deps, { silent = false, persistCache = false } = {}) {
    await Promise.all([
      loadMySalesClaims(deps, { silent }),
      loadOrganizationUsers(deps, { silent }),
    ]);
    if (persistCache) {
      deps.persistSalesOverviewCache({
        my_items: deps.state.mySalesClaims,
        company_items: deps.state.companySalesClaims,
        organization_users: deps.state.organizationUsers,
      });
    }
    return true;
  }

  async function loadMySalesClaims(deps, { silent = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.state.auth.user) {
      deps.state.mySalesClaims = [];
      deps.state.companySalesClaims = [];
      deps.state.mySalesClaimsError = "";
      deps.renderMySalesClaimsPanel();
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
      return;
    }

    deps.state.mySalesClaimsLoading = true;
    deps.renderMySalesClaimsPanel();
    try {
      const response = await deps.api("/api/sales-claims", {
        timeoutMs: 15000,
        cacheBust: false,
      });
      const activeClaims = (response.items || []).filter((claim) => deps.isActiveSalesClaim(claim));
      deps.state.companySalesClaims = activeClaims;
      deps.state.mySalesClaims = activeClaims.filter((claim) => deps.isCurrentUserClaimOwner(claim));
      deps.mergeActiveSalesClaims(activeClaims);
      deps.state.mySalesClaimsError = "";
    } catch (err) {
      deps.state.mySalesClaims = [];
      deps.state.companySalesClaims = [];
      deps.state.mySalesClaimsError = err.message || "내 영업 목록을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.mySalesClaimsLoading = false;
      deps.renderMySalesClaimsPanel();
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
    }
  }

  async function loadClosedSalesClaims(deps, { silent = false } = {}) {
    if (deps.state.uiMode !== "admin") {
      deps.state.salesClosedClaims = [];
      deps.state.salesClosedError = "";
      deps.renderSalesSummaryPanel();
      return;
    }
    deps.state.salesClosedLoading = true;
    deps.renderSalesSummaryPanel();
    try {
      const response = await deps.api("/api/sales-claims", {
        timeoutMs: 15000,
        cacheBust: false,
      });
      deps.state.salesClosedClaims = (response.items || [])
        .filter((claim) => String(claim.claim_status || "active") !== "active")
        .sort((left, right) => {
          const leftTime = left?.closed_at ? new Date(left.closed_at).getTime() : 0;
          const rightTime = right?.closed_at ? new Date(right.closed_at).getTime() : 0;
          return rightTime - leftTime;
        });
      deps.state.salesClosedError = "";
    } catch (err) {
      deps.state.salesClosedClaims = [];
      deps.state.salesClosedError = err.message || "종료된 영업 이력을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.salesClosedLoading = false;
      deps.renderSalesSummaryPanel();
    }
  }

  function refreshSalesAdminPanels(deps, { silent = false } = {}) {
    void loadSalesClaimSummaryByUser(deps, { silent });
    void loadClosedSalesClaims(deps, { silent });
  }

  async function loadSalesClaimSummaryByUser(deps, { silent = false } = {}) {
    if (deps.state.uiMode !== "admin") {
      return;
    }
    deps.state.salesSummaryLoading = true;
    deps.renderSalesSummaryPanel();
    try {
      const response = await deps.api("/api/sales-claims/summary-by-user", {
        timeoutMs: 15000,
        cacheBust: false,
      });
      deps.state.salesSummaryByUser = response.items || [];
      deps.state.salesSummaryError = "";
      deps.renderSalesSummaryPanel();
    } catch (err) {
      deps.state.salesSummaryByUser = [];
      deps.state.salesSummaryError = err.message || "영업 집계를 불러오지 못했습니다.";
      deps.renderSalesSummaryPanel();
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.salesSummaryLoading = false;
      deps.renderSalesSummaryPanel();
    }
  }

  async function loadOrganizationUsers(deps, { silent = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authorized) {
      deps.state.organizationUsers = [];
      deps.state.organizationUsersError = "";
      return;
    }
    deps.state.organizationUsersLoading = true;
    try {
      const response = await deps.api("/api/auth/users", {
        timeoutMs: 15000,
        cacheBust: false,
      });
      deps.state.organizationUsers = response.items || [];
      deps.state.organizationUsersError = "";
    } catch (err) {
      deps.state.organizationUsers = [];
      deps.state.organizationUsersError = err.message || "사용자 목록을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.organizationUsersLoading = false;
      deps.renderTrackerEntries(deps.state.trackerEntries, { refreshSelectedEntry: false });
    }
  }

  async function loadOrganizationMembers(deps, { silent = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.canUseAdminMode()) {
      deps.state.organizationMembers = [];
      deps.state.organizationMembersError = "";
      deps.state.organizationMembersLoaded = false;
      deps.renderOrganizationAdminPanel();
      return;
    }
    if (!silent) {
      deps.state.organizationMembersLoading = true;
      deps.renderOrganizationAdminPanel();
    }
    try {
      const response = await deps.api("/api/auth/users?include_inactive=true", {
        timeoutMs: ORGANIZATION_ADMIN_READ_TIMEOUT_MS,
        cacheBust: false,
      });
      deps.state.organizationMembers = response.items || [];
      deps.state.organizationMembersError = "";
      deps.state.organizationMembersLoaded = true;
    } catch (err) {
      deps.state.organizationMembers = [];
      deps.state.organizationMembersLoaded = false;
      deps.state.organizationMembersError = err.message || "사용자 목록을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.organizationMembersLoading = false;
      deps.renderOrganizationAdminPanel();
    }
  }

  async function loadOrganizationInvitations(deps, { silent = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.canUseAdminMode()) {
      deps.state.organizationPlanSummary = null;
      deps.state.organizationInvitations = [];
      deps.state.organizationInvitationsError = "";
      deps.state.organizationInvitationsLoaded = false;
      deps.renderOrganizationAdminPanel();
      return;
    }
    if (!silent) {
      deps.state.organizationInvitationsLoading = true;
      deps.renderOrganizationAdminPanel();
    }
    try {
      const response = await deps.api("/api/auth/invitations", {
        timeoutMs: ORGANIZATION_ADMIN_READ_TIMEOUT_MS,
        cacheBust: false,
      });
      deps.state.organizationPlanSummary = response.plan_summary || null;
      deps.state.organizationInvitations = deps.mergeOrganizationInvitations(response.items || []);
      deps.state.organizationInvitationsError = "";
      deps.state.organizationInvitationsLoaded = true;
    } catch (err) {
      deps.state.organizationPlanSummary = null;
      deps.state.organizationInvitations = [];
      deps.state.organizationInvitationsLoaded = false;
      deps.state.organizationInvitationsError = err.message || "초대 목록을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.organizationInvitationsLoading = false;
      deps.renderOrganizationAdminPanel();
    }
  }

  async function loadOrganizationAuditLogs(deps, { silent = false } = {}) {
    const visibleLimit = Math.max(1, Number(deps.state.organizationAuditLogsLimit || 5) || 5);
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.canUseAdminMode()) {
      deps.state.organizationAuditLogs = [];
      deps.state.organizationAuditLogsLoading = false;
      deps.state.organizationAuditLogsError = "";
      deps.state.organizationAuditLogsLimit = 5;
      deps.state.organizationAuditLogsHasMore = false;
      deps.state.organizationAuditLogsLoaded = false;
      deps.renderOrganizationAdminPanel();
      return;
    }
    if (!silent) {
      deps.state.organizationAuditLogsLoading = true;
      deps.renderOrganizationAdminPanel();
    }
    try {
      const response = await deps.api(`/api/auth/audit-logs?limit=${encodeURIComponent(visibleLimit + 1)}`, {
        timeoutMs: ORGANIZATION_ADMIN_READ_TIMEOUT_MS,
        cacheBust: false,
      });
      const items = response.items || [];
      deps.state.organizationAuditLogs = items.slice(0, visibleLimit);
      deps.state.organizationAuditLogsHasMore = items.length > visibleLimit;
      deps.state.organizationAuditLogsError = "";
      deps.state.organizationAuditLogsLoaded = true;
    } catch (err) {
      deps.state.organizationAuditLogs = [];
      deps.state.organizationAuditLogsHasMore = false;
      deps.state.organizationAuditLogsLoaded = false;
      deps.state.organizationAuditLogsError = err.message || "조직 감사 로그를 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.organizationAuditLogsLoading = false;
      deps.renderOrganizationAdminPanel();
    }
  }

  async function loadOrganizationDownloadAuditLogs(deps, { silent = false } = {}) {
    const visibleLimit = Math.max(1, Number(deps.state.organizationDownloadAuditLogsLimit || 5) || 5);
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.canUseAdminMode()) {
      deps.state.organizationDownloadAuditLogs = [];
      deps.state.organizationDownloadAuditLogsLoading = false;
      deps.state.organizationDownloadAuditLogsError = "";
      deps.state.organizationDownloadAuditLogsLimit = 5;
      deps.state.organizationDownloadAuditLogsHasMore = false;
      deps.state.organizationDownloadAuditLogsLoaded = false;
      deps.renderOrganizationAdminPanel();
      return;
    }
    if (!silent) {
      deps.state.organizationDownloadAuditLogsLoading = true;
      deps.renderOrganizationAdminPanel();
    }
    try {
      const response = await deps.api(`/api/admin/download-audit-logs?limit=${encodeURIComponent(visibleLimit + 1)}`, {
        timeoutMs: ORGANIZATION_ADMIN_READ_TIMEOUT_MS,
        cacheBust: false,
      });
      const items = response.items || [];
      deps.state.organizationDownloadAuditLogs = items.slice(0, visibleLimit);
      deps.state.organizationDownloadAuditLogsHasMore = items.length > visibleLimit;
      deps.state.organizationDownloadAuditLogsError = "";
      deps.state.organizationDownloadAuditLogsLoaded = true;
    } catch (err) {
      deps.state.organizationDownloadAuditLogs = [];
      deps.state.organizationDownloadAuditLogsHasMore = false;
      deps.state.organizationDownloadAuditLogsLoaded = false;
      deps.state.organizationDownloadAuditLogsError = err.message || "다운로드 이력을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.organizationDownloadAuditLogsLoading = false;
      deps.renderOrganizationAdminPanel();
    }
  }

  async function loadOrganizationLoginAuditLogs(deps, { silent = false } = {}) {
    const visibleLimit = Math.max(1, Number(deps.state.organizationLoginAuditLogsLimit || 5) || 5);
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.canUseAdminMode()) {
      deps.state.organizationLoginAuditLogs = [];
      deps.state.organizationLoginAuditLogsLoading = false;
      deps.state.organizationLoginAuditLogsError = "";
      deps.state.organizationLoginAuditLogsLimit = 5;
      deps.state.organizationLoginAuditLogsHasMore = false;
      deps.state.organizationLoginAuditLogsLoaded = false;
      deps.renderOrganizationAdminPanel();
      return;
    }
    if (!silent) {
      deps.state.organizationLoginAuditLogsLoading = true;
      deps.renderOrganizationAdminPanel();
    }
    try {
      const response = await deps.api(`/api/admin/login-audit-logs?limit=${encodeURIComponent(visibleLimit + 1)}`, {
        timeoutMs: ORGANIZATION_ADMIN_READ_TIMEOUT_MS,
        cacheBust: false,
      });
      const items = response.items || [];
      deps.state.organizationLoginAuditLogs = items.slice(0, visibleLimit);
      deps.state.organizationLoginAuditLogsHasMore = items.length > visibleLimit;
      deps.state.organizationLoginAuditLogsError = "";
      deps.state.organizationLoginAuditLogsLoaded = true;
    } catch (err) {
      deps.state.organizationLoginAuditLogs = [];
      deps.state.organizationLoginAuditLogsHasMore = false;
      deps.state.organizationLoginAuditLogsLoaded = false;
      deps.state.organizationLoginAuditLogsError = err.message || "로그인 이력을 불러오지 못했습니다.";
      if (!silent) {
        deps.flash(err.message, "error");
      }
    } finally {
      deps.state.organizationLoginAuditLogsLoading = false;
      deps.renderOrganizationAdminPanel();
    }
  }

  function setOrganizationAdminLoadingState(deps, isLoading) {
    const normalized = Boolean(isLoading);
    deps.state.organizationMembersLoading = normalized;
    deps.state.organizationInvitationsLoading = normalized;
    deps.state.organizationAuditLogsLoading = normalized;
    deps.state.organizationDownloadAuditLogsLoading = normalized;
    deps.state.organizationLoginAuditLogsLoading = normalized;
  }

  function applyOrganizationAdminBootstrapPayload(deps, payload) {
    const members = Array.isArray(payload?.members) ? payload.members : [];
    const invitations = Array.isArray(payload?.invitations) ? payload.invitations : [];
    const authAuditLogs = Array.isArray(payload?.auth_audit_logs?.items) ? payload.auth_audit_logs.items : [];
    const downloadAuditLogs = Array.isArray(payload?.download_audit_logs?.items) ? payload.download_audit_logs.items : [];
    const loginAuditLogs = Array.isArray(payload?.login_audit_logs?.items) ? payload.login_audit_logs.items : [];

    deps.state.organizationMembers = members;
    deps.state.organizationMembersError = "";
    deps.state.organizationMembersLoaded = true;
    deps.state.organizationMembersLoading = false;

    deps.state.organizationPlanSummary = payload?.plan_summary || null;
    deps.state.organizationInvitations = deps.mergeOrganizationInvitations(invitations);
    deps.state.organizationInvitationsError = "";
    deps.state.organizationInvitationsLoaded = true;
    deps.state.organizationInvitationsLoading = false;

    deps.state.organizationAuditLogs = authAuditLogs;
    deps.state.organizationAuditLogsError = "";
    deps.state.organizationAuditLogsHasMore = Boolean(payload?.auth_audit_logs?.has_more);
    deps.state.organizationAuditLogsLoaded = true;
    deps.state.organizationAuditLogsLoading = false;

    deps.state.organizationDownloadAuditLogs = downloadAuditLogs;
    deps.state.organizationDownloadAuditLogsError = "";
    deps.state.organizationDownloadAuditLogsHasMore = Boolean(payload?.download_audit_logs?.has_more);
    deps.state.organizationDownloadAuditLogsLoaded = true;
    deps.state.organizationDownloadAuditLogsLoading = false;

    deps.state.organizationLoginAuditLogs = loginAuditLogs;
    deps.state.organizationLoginAuditLogsError = "";
    deps.state.organizationLoginAuditLogsHasMore = Boolean(payload?.login_audit_logs?.has_more);
    deps.state.organizationLoginAuditLogsLoaded = true;
    deps.state.organizationLoginAuditLogsLoading = false;
    deps.renderOrganizationAdminPanel();
  }

  async function loadOrganizationAdminDataSequential(deps, { silent = false } = {}) {
    await loadOrganizationMembers(deps, { silent });
    await loadOrganizationInvitations(deps, { silent });
    await loadOrganizationAuditLogs(deps, { silent });
    await loadOrganizationDownloadAuditLogs(deps, { silent });
    await loadOrganizationLoginAuditLogs(deps, { silent });
  }

  function loadOrganizationAdminData(deps, { silent = false, force = false } = {}) {
    if (!deps.state.auth.enabled || !deps.state.auth.authorized || !deps.canUseAdminMode()) {
      deps.state.organizationMembers = [];
      deps.state.organizationMembersError = "";
      deps.state.organizationMembersLoaded = false;
      deps.state.organizationPlanSummary = null;
      deps.state.organizationInvitations = [];
      deps.state.organizationInvitationsError = "";
      deps.state.organizationInvitationsLoaded = false;
      deps.state.organizationAuditLogs = [];
      deps.state.organizationAuditLogsLoading = false;
      deps.state.organizationAuditLogsError = "";
      deps.state.organizationAuditLogsLimit = 5;
      deps.state.organizationAuditLogsHasMore = false;
      deps.state.organizationAuditLogsLoaded = false;
      deps.state.organizationDownloadAuditLogs = [];
      deps.state.organizationDownloadAuditLogsLoading = false;
      deps.state.organizationDownloadAuditLogsError = "";
      deps.state.organizationDownloadAuditLogsLimit = 5;
      deps.state.organizationDownloadAuditLogsHasMore = false;
      deps.state.organizationDownloadAuditLogsLoaded = false;
      deps.state.organizationLoginAuditLogs = [];
      deps.state.organizationLoginAuditLogsLoading = false;
      deps.state.organizationLoginAuditLogsError = "";
      deps.state.organizationLoginAuditLogsLimit = 5;
      deps.state.organizationLoginAuditLogsHasMore = false;
      deps.state.organizationLoginAuditLogsLoaded = false;
      deps.state.organizationAdminDataRequest = null;
      deps.renderOrganizationAdminPanel();
      return;
    }
    if (deps.state.organizationAdminDataRequest && !force) {
      return deps.state.organizationAdminDataRequest;
    }
    const requestId = Number(deps.state.organizationAdminDataRequestId || 0) + 1;
    deps.state.organizationAdminDataRequestId = requestId;
    const request = (async () => {
      const cachedBootstrap = !force && typeof deps.readOrganizationAdminBootstrapCache === "function"
        ? deps.readOrganizationAdminBootstrapCache()
        : null;
      const hasCachedBootstrap = Boolean(cachedBootstrap && typeof cachedBootstrap === "object");
      if (hasCachedBootstrap) {
        applyOrganizationAdminBootstrapPayload(deps, cachedBootstrap);
      } else if (!silent) {
        setOrganizationAdminLoadingState(deps, true);
        deps.renderOrganizationAdminPanel();
      }

      try {
        const response = await deps.api("/api/admin/organization-panel-bootstrap", {
          timeoutMs: ORGANIZATION_ADMIN_READ_TIMEOUT_MS,
          cacheBust: false,
        });
        if (deps.state.organizationAdminDataRequestId !== requestId) {
          return;
        }
        applyOrganizationAdminBootstrapPayload(deps, response || {});
        if (typeof deps.persistOrganizationAdminBootstrapCache === "function") {
          deps.persistOrganizationAdminBootstrapCache(response || {});
        }
      } catch (err) {
        if (deps.state.organizationAdminDataRequestId !== requestId) {
          return;
        }
        if (!hasCachedBootstrap) {
          await loadOrganizationAdminDataSequential(deps, { silent });
        }
        if (!silent && !hasCachedBootstrap) {
          deps.flash(err.message, "error");
        }
      } finally {
        setOrganizationAdminLoadingState(deps, false);
        deps.renderOrganizationAdminPanel();
      }
    })().finally(() => {
      if (deps.state.organizationAdminDataRequestId === requestId) {
        deps.state.organizationAdminDataRequest = null;
      }
    });
    deps.state.organizationAdminDataRequest = request;
    return request;
  }

  global.SPMSConsoleDataRuntime = {
    loadVisibleSalesClaims,
    loadHomeBootstrap,
    loadHomeBootstrapFromLegacy,
    loadSalesOverview,
    loadSalesOverviewFromLegacy,
    loadMySalesClaims,
    loadOrganizationUsers,
    loadOrganizationMembers,
    loadOrganizationInvitations,
    loadOrganizationAuditLogs,
    loadOrganizationDownloadAuditLogs,
    loadOrganizationLoginAuditLogs,
    loadOrganizationAdminDataSequential,
    loadOrganizationAdminData,
    loadClosedSalesClaims,
    loadSalesClaimSummaryByUser,
    refreshSalesAdminPanels,
  };
})(window);
