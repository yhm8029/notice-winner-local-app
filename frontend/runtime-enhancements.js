export function createRuntimeEnhancements(deps = {}) {
  const {
    dom,
    syncCollectModeOptions,
    RUN_VIEW_RUNTIME,
    renderOrganizationAdminPanel,
  } = deps;
  const document = deps.document || globalThis.document || null;

  function mountRuntimeEnhancements() {
    syncCollectModeOptions();
    const collectModeSelect = dom.runForm?.querySelector('[name="collect_mode"]');
    if (collectModeSelect && !collectModeSelect.querySelector('option[value="native"]')) {
      const nativeOption = document.createElement("option");
      nativeOption.value = "native";
      nativeOption.textContent = "네이티브 API";
      collectModeSelect.insertBefore(nativeOption, collectModeSelect.firstElementChild);
    }
    syncCollectModeOptions();

    if (dom.runDetail && !dom.runExecutionContext) {
      const executionContext = document.createElement("div");
      executionContext.id = "run-execution-context";
      executionContext.className = "tracker-context hidden";
      dom.runDetail.insertBefore(executionContext, dom.runDetail.querySelector(".detail-grid"));
      dom.runExecutionContext = executionContext;
    }

    if (dom.consoleShell && !dom.authSessionActions) {
      const actionBar = document.createElement("div");
      actionBar.id = "auth-session-actions";
      actionBar.className = "auth-session-actions hidden";
      actionBar.innerHTML = `
        <span id="auth-session-user-label" class="mono">-</span>
        <button id="auth-session-mode-toggle-button" class="ghost-button" type="button">운영자 모드</button>
        <button id="auth-session-profile-button" class="ghost-button" type="button">회원정보</button>
        <button id="auth-session-logout-button" class="ghost-button" type="button">로그아웃</button>
      `;
      const hero = dom.consoleShell.querySelector(".hero");
      hero?.insertAdjacentElement("afterend", actionBar);
      dom.authSessionActions = actionBar;
      dom.authSessionUserLabel = actionBar.querySelector("#auth-session-user-label");
      dom.authSessionModeToggleButton = actionBar.querySelector("#auth-session-mode-toggle-button");
      dom.authSessionProfileButton = actionBar.querySelector("#auth-session-profile-button");
      dom.authSessionLogoutButton = actionBar.querySelector("#auth-session-logout-button");
    }

    if (dom.authSessionActions && !dom.trackerChangeBell) {
      const bellShell = document.createElement("div");
      bellShell.id = "tracker-change-bell-shell";
      bellShell.className = "tracker-change-bell-shell";
      const bellButton = document.createElement("button");
      bellButton.id = "tracker-change-bell";
      bellButton.className = "ghost-button tracker-change-bell";
      bellButton.type = "button";
      bellButton.setAttribute("aria-haspopup", "dialog");
      bellButton.setAttribute("aria-expanded", "false");
      bellButton.innerHTML = `
        <span aria-hidden="true">변경</span>
        <span id="tracker-change-bell-badge" class="tracker-change-bell-badge hidden">0</span>
      `;
      const bellPopover = document.createElement("div");
      bellPopover.id = "tracker-change-bell-popover";
      bellPopover.className = "tracker-change-bell-popover hidden";
      bellPopover.innerHTML = '<div class="empty-state">최근 변경을 불러오는 중입니다.</div>';
      bellShell.append(bellButton, bellPopover);
      dom.authSessionActions.insertBefore(bellShell, dom.authSessionProfileButton || dom.authSessionLogoutButton || null);
      dom.trackerChangeBellShell = bellShell;
      dom.trackerChangeBell = bellButton;
      dom.trackerChangeBellBadge = bellButton.querySelector("#tracker-change-bell-badge");
      dom.trackerChangeBellPopover = bellPopover;
    }

    if (dom.authMetaCard && !dom.authProfileButton) {
      const profileButton = document.createElement("button");
      profileButton.id = "auth-profile-button";
      profileButton.className = "ghost-button hero-mode-button";
      profileButton.type = "button";
      profileButton.textContent = "회원정보";
      dom.logoutButton?.insertAdjacentElement("beforebegin", profileButton);
      dom.authProfileButton = profileButton;
    }

    if (!dom.profileDialog) {
      const dialog = document.createElement("div");
      dialog.id = "profile-dialog";
      dialog.className = "profile-dialog hidden";
      dialog.innerHTML = `
        <div class="profile-dialog-backdrop" data-profile-close></div>
        <div class="profile-dialog-card" role="dialog" aria-modal="true" aria-labelledby="profile-dialog-title">
          <div class="profile-dialog-head">
            <div>
              <p class="kicker">내 계정</p>
              <strong id="profile-dialog-title">회원정보</strong>
            </div>
            <button class="ghost-button" type="button" data-profile-close>닫기</button>
          </div>
          <form id="profile-form" class="profile-form">
            <label>
              <span>이메일</span>
              <input id="profile-email" type="email" readonly />
            </label>
            <label>
              <span>표시 이름</span>
              <input id="profile-display-name" name="display_name" type="text" maxlength="80" required />
            </label>
            <label>
              <span>역할</span>
              <input id="profile-role" type="text" readonly />
            </label>
            <label>
              <span>회사</span>
              <input id="profile-organization" type="text" readonly />
            </label>
            <label>
              <span>상태</span>
              <input id="profile-status" type="text" readonly />
            </label>
            <label>
              <span>현재 비밀번호 확인</span>
              <input id="profile-current-password" name="current_password" type="password" autocomplete="current-password" placeholder="회원정보 수정 전에 현재 비밀번호를 입력하세요." />
            </label>
            <label>
              <span>휴대폰</span>
              <input id="profile-mobile-phone" name="mobile_phone" type="text" maxlength="40" />
            </label>
            <label>
              <span>회사 전화</span>
              <input id="profile-office-phone" name="office_phone" type="text" maxlength="40" />
            </label>
            <label>
              <span>새 비밀번호</span>
              <input id="profile-password" name="password" type="password" autocomplete="new-password" placeholder="변경할 때만 입력" />
            </label>
            <label>
              <span>새 비밀번호 확인</span>
              <input id="profile-password-confirm" type="password" autocomplete="new-password" placeholder="비밀번호를 다시 입력" />
            </label>
            <p class="hint-text">기본적으로 회원정보를 저장하려면 현재 로그인 비밀번호를 다시 입력해야 한다. 초대 링크를 통한 첫 비밀번호 설정은 현재 비밀번호 없이 진행할 수 있다.</p>
            <div id="profile-status-message" class="flash-message hidden" role="status" aria-live="polite"></div>
            <div class="profile-dialog-actions">
              <button id="profile-save-button" class="primary-button" type="submit">저장</button>
              <button class="ghost-button" type="button" data-profile-close>취소</button>
            </div>
          </form>
        </div>
      `;
      document.body.appendChild(dialog);
      dom.profileDialog = dialog;
      dom.profileForm = dialog.querySelector("#profile-form");
      dom.profileDisplayName = dialog.querySelector("#profile-display-name");
      dom.profileEmail = dialog.querySelector("#profile-email");
      dom.profileRole = dialog.querySelector("#profile-role");
      dom.profileOrganization = dialog.querySelector("#profile-organization");
      dom.profileStatus = dialog.querySelector("#profile-status");
      dom.profileMobilePhone = dialog.querySelector("#profile-mobile-phone");
      dom.profileOfficePhone = dialog.querySelector("#profile-office-phone");
      dom.profileCurrentPassword = dialog.querySelector("#profile-current-password");
      dom.profilePassword = dialog.querySelector("#profile-password");
      dom.profilePasswordConfirm = dialog.querySelector("#profile-password-confirm");
      dom.profileSaveButton = dialog.querySelector("#profile-save-button");
      dom.profileStatusMessage = dialog.querySelector("#profile-status-message");
      dom.profileCloseButtons = [...dialog.querySelectorAll("[data-profile-close]")];
    }

    if (dom.runForm && !dom.presetPanel) {
      const presetPanel = document.createElement("section");
      presetPanel.className = "runtime-card";
      presetPanel.innerHTML = RUN_VIEW_RUNTIME?.buildRunPresetPanelMarkup() || `
        <div class="runtime-card-head">
          <div>
            <strong>실행 프리셋</strong>
            <p class="kicker">자주 쓰는 검색 조건 저장</p>
          </div>
          <button id="preset-refresh-button" class="ghost-button" type="button">새로고침</button>
        </div>
        <div class="runtime-toolbar">
          <select id="preset-select">
            <option value="">저장된 프리셋 없음</option>
          </select>
          <button id="preset-apply-button" class="ghost-button" type="button">적용</button>
          <button id="preset-save-button" class="ghost-button" type="button">현재 조건 저장</button>
        </div>
        <p id="preset-status" class="hint-text">프리셋을 불러오는 중입니다.</p>
      `;
      const advancedBox = dom.runForm.querySelector(".advanced-box");
      dom.runForm.insertBefore(presetPanel, advancedBox || dom.runForm.firstChild);
      dom.presetPanel = presetPanel;
      dom.presetSelect = presetPanel.querySelector("#preset-select");
      dom.presetApplyButton = presetPanel.querySelector("#preset-apply-button");
      dom.presetSaveButton = presetPanel.querySelector("#preset-save-button");
      dom.presetRefreshButton = presetPanel.querySelector("#preset-refresh-button");
      dom.presetStatus = presetPanel.querySelector("#preset-status");
    }

    if (dom.logsList && !dom.runEventStatus) {
      const eventStatus = document.createElement("div");
      eventStatus.id = "run-event-status";
      eventStatus.className = "runtime-card runtime-card-compact";
      eventStatus.textContent = "실시간 이벤트 대기";
      dom.logsList.parentElement.insertBefore(eventStatus, dom.logsList);
      dom.runEventStatus = eventStatus;
    }

    if (dom.runsList && !dom.projectPanel) {
      const projectPanel = document.createElement("section");
      projectPanel.id = "panel-projects";
      projectPanel.className = "panel panel-projects";
      projectPanel.innerHTML = `
        <div class="panel-heading">
          <div>
            <p class="kicker">프로젝트 히스토리</p>
            <h2>프로젝트 집계</h2>
          </div>
          <button id="project-refresh-button" class="ghost-button" type="button">새로고침</button>
        </div>
        <div class="runtime-toolbar">
          <input id="project-query" type="text" placeholder="프로젝트명 또는 발주처 검색" />
          <button id="project-search-button" class="ghost-button" type="button">검색</button>
        </div>
        <div id="project-list" class="runtime-list empty-state">프로젝트를 불러오는 중입니다.</div>
        <div class="pagination-row runtime-pagination">
          <button id="project-prev-button" class="ghost-button" type="button">이전</button>
          <span id="project-page-meta" class="mono">Page 1 / 1</span>
          <button id="project-next-button" class="ghost-button" type="button">다음</button>
        </div>
      `;
      dom.panelStatus?.insertAdjacentElement("afterend", projectPanel);
      dom.projectPanel = projectPanel;
      dom.projectQuery = projectPanel.querySelector("#project-query");
      dom.projectSearchButton = projectPanel.querySelector("#project-search-button");
      dom.projectRefreshButton = projectPanel.querySelector("#project-refresh-button");
      dom.projectList = projectPanel.querySelector("#project-list");
      dom.projectPageMeta = projectPanel.querySelector("#project-page-meta");
      dom.projectPrevButton = projectPanel.querySelector("#project-prev-button");
      dom.projectNextButton = projectPanel.querySelector("#project-next-button");
    }

    if (!dom.panelSalesSummary) {
      const salesSummaryPanel = document.createElement("section");
      salesSummaryPanel.id = "panel-sales-summary";
      salesSummaryPanel.className = "panel panel-sales-summary hidden";
      salesSummaryPanel.innerHTML = `
        <div class="panel-heading">
          <div>
            <p class="kicker">영업 파이프라인</p>
            <h2>영업사원별 진행 현황</h2>
          </div>
          <button id="sales-summary-refresh-button" class="ghost-button" type="button">새로고침</button>
        </div>
        <div id="sales-summary-list" class="runtime-list empty-state">영업 claim 데이터를 불러오는 중입니다.</div>
      `;
      const insertionTarget = dom.projectPanel || dom.panelDashboard || dom.panelForm;
      if (insertionTarget?.parentElement) {
        insertionTarget.parentElement.insertBefore(salesSummaryPanel, insertionTarget);
      }
      dom.panelSalesSummary = salesSummaryPanel;
      dom.salesSummaryRefreshButton = salesSummaryPanel.querySelector("#sales-summary-refresh-button");
      dom.salesSummaryList = salesSummaryPanel.querySelector("#sales-summary-list");
    }

    if (!dom.panelOrgAdmin) {
      const orgAdminPanel = document.createElement("section");
      orgAdminPanel.id = "panel-org-admin";
      orgAdminPanel.className = "panel panel-org-admin hidden";
      orgAdminPanel.innerHTML = `
        <div class="panel-heading">
          <div>
            <p class="kicker">사용자 관리</p>
            <h2>사용자 초대 및 관리</h2>
          </div>
          <button id="org-admin-refresh-button" class="ghost-button" type="button">새로고침</button>
        </div>
        <div class="org-admin-grid">
          <div id="platform-admin-account-panel-slot"></div>
          <article class="runtime-card org-admin-card">
            <div class="runtime-card-head">
              <div>
                <strong>사용자 초대</strong>
                <p class="kicker">초대 메일 발송을 시도합니다. 도착하지 않으면 링크를 직접 복사해서 전달할 수도 있습니다.</p>
              </div>
            </div>
            <div id="organization-plan-summary" class="org-plan-summary empty-state">플랜 요약을 불러오는 중입니다.</div>
            <form id="invitation-form" class="org-admin-form">
              <input id="invitation-email" name="email" type="email" placeholder="이메일" required />
              <input id="invitation-display-name" name="display_name" type="text" placeholder="표시 이름" />
              <select id="invitation-role" name="role">
                <option value="org_member">사용자</option>
                <option value="org_admin">관리자</option>
              </select>
              <input id="invitation-team-name" name="team_name" type="text" placeholder="팀명" />
              <input id="invitation-job-title" name="job_title" type="text" placeholder="직책" />
              <input id="invitation-expires-in-days" name="expires_in_days" type="number" min="1" max="30" value="7" placeholder="만료일(일)" title="초대 링크 유효기간(일)" />
              <button id="invitation-submit-button" class="primary-button" type="submit">초대 링크 생성</button>
            </form>
            <div id="invitation-status-message" class="hint-text">초대 메일을 보내고, 실패하면 링크 복사로 직접 전달할 수 있습니다.</div>
            <div id="invitation-list" class="runtime-list empty-state">초대 목록을 불러오는 중입니다.</div>
          </article>
          <article class="runtime-card org-admin-card">
            <div class="runtime-card-head">
              <div>
                <strong>사용자 상태 및 목록</strong>
                <p class="kicker">역할, 계정 상태, 소속 상태, 팀/직책을 관리합니다.</p>
              </div>
            </div>
            <div id="organization-member-summary" class="org-member-summary empty-state">사용자 상태 요약을 불러오는 중입니다.</div>
            <div id="organization-member-list" class="runtime-list empty-state">사용자 목록을 불러오는 중입니다.</div>
          </article>
          <div id="organization-audit-panel-slot"></div>
          <div id="organization-download-audit-panel-slot"></div>
          <div id="organization-login-audit-panel-slot"></div>
          <div class="org-admin-empty-slot" aria-hidden="true"></div>
        </div>
      `;
      const firstAdminPanel = dom.panelSalesSummary || dom.panelDashboard || dom.panelForm;
      if (firstAdminPanel?.parentElement) {
        firstAdminPanel.parentElement.insertBefore(orgAdminPanel, firstAdminPanel);
      }
      dom.panelOrgAdmin = orgAdminPanel;
      dom.orgAdminRefreshButton = orgAdminPanel.querySelector("#org-admin-refresh-button");
      dom.platformAdminAccountPanelSlot = orgAdminPanel.querySelector("#platform-admin-account-panel-slot");
      dom.invitationForm = orgAdminPanel.querySelector("#invitation-form");
      dom.invitationEmail = orgAdminPanel.querySelector("#invitation-email");
      dom.invitationDisplayName = orgAdminPanel.querySelector("#invitation-display-name");
      dom.invitationRole = orgAdminPanel.querySelector("#invitation-role");
      dom.invitationTeamName = orgAdminPanel.querySelector("#invitation-team-name");
      dom.invitationJobTitle = orgAdminPanel.querySelector("#invitation-job-title");
      dom.invitationExpiresInDays = orgAdminPanel.querySelector("#invitation-expires-in-days");
      dom.invitationSubmitButton = orgAdminPanel.querySelector("#invitation-submit-button");
      dom.invitationStatusMessage = orgAdminPanel.querySelector("#invitation-status-message");
      dom.organizationPlanSummary = orgAdminPanel.querySelector("#organization-plan-summary");
      dom.invitationList = orgAdminPanel.querySelector("#invitation-list");
      dom.organizationMemberSummary = orgAdminPanel.querySelector("#organization-member-summary");
      dom.organizationMemberList = orgAdminPanel.querySelector("#organization-member-list");
      dom.organizationAuditPanelSlot = orgAdminPanel.querySelector("#organization-audit-panel-slot");
      dom.organizationDownloadAuditPanelSlot = orgAdminPanel.querySelector("#organization-download-audit-panel-slot");
      dom.organizationLoginAuditPanelSlot = orgAdminPanel.querySelector("#organization-login-audit-panel-slot");
    }

    if (!dom.panelMissingReport) {
      const missingReportPanel = document.createElement("section");
      missingReportPanel.id = "panel-missing-report";
      missingReportPanel.className = "panel panel-missing-report hidden";
      missingReportPanel.innerHTML = `
        <div class="panel-heading">
          <div>
            <p class="kicker">관리자 진단</p>
            <h2>누락 리포트</h2>
          </div>
          <div class="inline-actions">
            <button id="missing-report-refresh-button" class="ghost-button" type="button">새로고침</button>
            <button id="missing-report-csv-button" class="ghost-button" type="button">CSV 다운로드</button>
            <button id="missing-report-xlsx-button" class="ghost-button" type="button">엑셀 다운로드</button>
          </div>
        </div>
        <div id="missing-report-summary" class="missing-report-summary empty-state">새로고침을 눌러 누락 현황을 불러오세요.</div>
        <div id="missing-report-list" class="missing-report-list empty-state">누락 리포트는 수동 요청 시에만 계산합니다.</div>
      `;
      const firstAdminPanel = dom.panelDashboard || dom.panelForm;
      if (firstAdminPanel?.parentElement) {
        firstAdminPanel.parentElement.insertBefore(missingReportPanel, firstAdminPanel);
      }
      dom.panelMissingReport = missingReportPanel;
      dom.missingReportSummary = missingReportPanel.querySelector("#missing-report-summary");
      dom.missingReportList = missingReportPanel.querySelector("#missing-report-list");
      dom.missingReportRefreshButton = missingReportPanel.querySelector("#missing-report-refresh-button");
      dom.missingReportCsvButton = missingReportPanel.querySelector("#missing-report-csv-button");
      dom.missingReportXlsxButton = missingReportPanel.querySelector("#missing-report-xlsx-button");
    }

    if (dom.trackerEntriesList && !dom.trackerBoard) {
      const trackerBoard = document.createElement("section");
      trackerBoard.className = "runtime-card tracker-board";
      trackerBoard.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>트래커 결과 보드</strong>
            <p class="kicker">엑셀 양식 핵심 컬럼 미리 보기</p>
          </div>
        </div>
        <div id="tracker-board" class="tracker-board-content empty-state">트래커 행을 불러오면 여기에 표로 표시됩니다.</div>
      `;
      dom.trackerEntriesList.parentElement.appendChild(trackerBoard);
      dom.trackerBoard = trackerBoard.querySelector("#tracker-board");
    }

    if (dom.panelTracker && !dom.panelSalesRecommendations) {
      const recommendationSection = document.createElement("section");
      recommendationSection.id = "panel-sales-recommendations";
      recommendationSection.className = "runtime-card tracker-sales-recommendation-panel hidden";
      recommendationSection.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>영업 추천 리스트</strong>
            <p class="kicker">지금 확인할 프로젝트와 권장 액션</p>
          </div>
          <button id="tracker-sales-recommendation-refresh-button" class="ghost-button" type="button">새로고침</button>
        </div>
        <div id="tracker-sales-recommendation-list" class="runtime-list empty-state">영업 추천 리스트를 불러오는 중입니다.</div>
      `;
      dom.panelTracker.parentElement?.insertBefore(recommendationSection, dom.panelTracker.nextSibling);
      dom.panelSalesRecommendations = recommendationSection;
      dom.trackerSalesRecommendationSection = recommendationSection;
      dom.trackerSalesRecommendationList = recommendationSection.querySelector("#tracker-sales-recommendation-list");
      dom.trackerSalesRecommendationRefreshButton = recommendationSection.querySelector("#tracker-sales-recommendation-refresh-button");
    }

    if (dom.panelTracker && dom.trackerEntriesList && !dom.trackerUserSalesSection) {
      const salesOverviewGrid = document.createElement("div");
      salesOverviewGrid.id = "tracker-sales-overview-grid";
      salesOverviewGrid.className = "tracker-sales-overview-grid hidden";

      const mySalesSection = document.createElement("section");
      mySalesSection.id = "tracker-user-sales-section";
      mySalesSection.className = "runtime-card tracker-user-sales-section hidden";
      mySalesSection.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>내가 진행 중인 영업</strong>
            <p class="kicker">현재 로그인한 영업사원이 맡고 있는 프로젝트</p>
          </div>
          <button id="tracker-user-sales-download-button" class="ghost-button" type="button">엑셀 다운로드</button>
        </div>
        <div id="tracker-user-sales-list" class="runtime-list empty-state">내 영업 정보를 불러오는 중입니다.</div>
      `;
      salesOverviewGrid.appendChild(mySalesSection);
      dom.trackerUserSalesSection = mySalesSection;
      dom.trackerUserSalesList = mySalesSection.querySelector("#tracker-user-sales-list");
      dom.trackerUserSalesDownloadButton = mySalesSection.querySelector("#tracker-user-sales-download-button");

      const companySalesSection = document.createElement("section");
      companySalesSection.id = "tracker-company-sales-section";
      companySalesSection.className = "runtime-card tracker-user-sales-section hidden";
      companySalesSection.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>회사 전체 진행 중인 영업</strong>
            <p class="kicker">현재 우리 회사 전체가 맡고 있는 진행 중 영업 프로젝트</p>
          </div>
          <button id="tracker-company-sales-download-button" class="ghost-button" type="button">엑셀 다운로드</button>
        </div>
        <div id="tracker-company-sales-list" class="runtime-list empty-state">회사 진행 영업 정보를 불러오는 중입니다.</div>
      `;
      salesOverviewGrid.appendChild(companySalesSection);
      dom.panelTracker.insertBefore(salesOverviewGrid, dom.trackerEntriesList);
      dom.trackerSalesOverviewGrid = salesOverviewGrid;
      dom.trackerCompanySalesSection = companySalesSection;
      dom.trackerCompanySalesList = companySalesSection.querySelector("#tracker-company-sales-list");
      dom.trackerCompanySalesDownloadButton = companySalesSection.querySelector("#tracker-company-sales-download-button");

      const entriesTitle = document.createElement("div");
      entriesTitle.className = "tracker-user-section-title hidden";
      entriesTitle.id = "tracker-entries-section-title";
      entriesTitle.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>전체 영업 대상 프로젝트</strong>
            <p class="kicker">프로젝트 현황에 올라와 있는 전체 공고/프로젝트</p>
          </div>
          <button id="tracker-entries-download-button" class="ghost-button" type="button">엑셀 다운로드</button>
        </div>
      `;
      dom.panelTracker.insertBefore(entriesTitle, dom.trackerEntriesList);
      dom.trackerEntriesSectionTitle = entriesTitle;
      dom.trackerEntriesDownloadButton = entriesTitle.querySelector("#tracker-entries-download-button");
    }

    if (dom.panelTracker && !dom.trackerChangePanel) {
      const recentPanel = document.createElement("section");
      recentPanel.id = "tracker-change-panel";
      recentPanel.className = "runtime-card tracker-change-panel";
      recentPanel.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>최근 변경</strong>
            <p class="kicker">누락 해소와 자동 보정 내역을 최근 순으로 표시합니다.</p>
          </div>
        </div>
        <div id="tracker-change-list" class="runtime-list tracker-change-list empty-state">최근 변경을 불러오는 중입니다.</div>
      `;
      dom.panelTracker.insertBefore(recentPanel, dom.trackerSalesOverviewGrid || dom.trackerEntriesSectionTitle || dom.trackerEntriesList);
      dom.trackerChangePanel = recentPanel;
      dom.trackerChangeList = recentPanel.querySelector("#tracker-change-list");
    }

    if (dom.panelTracker && !dom.backfillConflictPanel) {
      const conflictPanel = document.createElement("section");
      conflictPanel.id = "backfill-conflict-panel";
      conflictPanel.className = "runtime-card tracker-change-panel";
      conflictPanel.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>검토 필요</strong>
            <p class="kicker">자동 백필이 보류된 충돌 항목을 확인하고 닫습니다.</p>
          </div>
        </div>
        <div id="backfill-conflict-list" class="runtime-list tracker-change-list empty-state">검토 필요 항목을 불러오는 중입니다.</div>
      `;
      const anchor = dom.trackerChangePanel ? dom.trackerChangePanel.nextSibling : null;
      dom.panelTracker.insertBefore(conflictPanel, anchor);
      dom.backfillConflictPanel = conflictPanel;
      dom.backfillConflictList = conflictPanel.querySelector("#backfill-conflict-list");
    }

    if (!dom.salesCloseDialog) {
      const dialog = document.createElement("div");
      dialog.id = "sales-close-dialog";
      dialog.className = "sales-close-dialog hidden";
      dialog.innerHTML = `
        <div class="sales-close-dialog-backdrop" data-sales-close-cancel></div>
        <div class="sales-close-dialog-card" role="dialog" aria-modal="true" aria-labelledby="sales-close-title">
          <div class="sales-close-dialog-head">
            <strong id="sales-close-title">계약금액 입력</strong>
            <button class="ghost-button" type="button" data-sales-close-cancel>닫기</button>
          </div>
          <p class="kicker">계약 완료 처리에는 계약금액 입력이 필수다.</p>
          <input id="sales-close-amount-input" class="sales-close-amount-input" type="text" inputmode="numeric" placeholder="예: 100,000,000" />
          <div class="sales-close-dialog-actions">
            <button id="sales-close-confirm-button" class="primary-button" type="button">계약 완료 저장</button>
            <button id="sales-close-cancel-button" class="ghost-button" type="button" data-sales-close-cancel>취소</button>
          </div>
        </div>
      `;
      document.body.appendChild(dialog);
      dom.salesCloseDialog = dialog;
      dom.salesCloseTitle = dialog.querySelector("#sales-close-title");
      dom.salesCloseAmountInput = dialog.querySelector("#sales-close-amount-input");
      dom.salesCloseConfirmButton = dialog.querySelector("#sales-close-confirm-button");
      dom.salesCloseCancelButton = dialog.querySelector("#sales-close-cancel-button");
    }

    if (dom.panelTracker && dom.entryEmptyState && dom.entryEditor && !dom.trackerInlineEditor) {
      const inlineEditor = document.createElement("section");
      inlineEditor.id = "tracker-inline-editor";
      inlineEditor.className = "runtime-card tracker-inline-editor hidden";
      inlineEditor.innerHTML = `
        <div class="runtime-card-head">
          <div>
            <strong>프로젝트 현황 수정</strong>
            <p class="kicker">선택한 프로젝트의 필드와 감사 이력 편집</p>
          </div>
        </div>
        <div class="tracker-inline-editor-body"></div>
      `;
      const inlineEditorBody = inlineEditor.querySelector(".tracker-inline-editor-body");
      inlineEditorBody.appendChild(dom.entryEmptyState);
      inlineEditorBody.appendChild(dom.entryEditor);
      dom.panelTracker.appendChild(inlineEditor);
      dom.trackerInlineEditor = inlineEditor;
      dom.panelEditor?.classList.add("hidden");
    }

    if (dom.entryEditor && !dom.selectedEntryChangeSection) {
      const changeSection = document.createElement("article");
      changeSection.className = "info-card";
      changeSection.id = "selected-entry-change-section";
      changeSection.innerHTML = `
        <div class="panel-heading mini">
          <div>
            <p class="kicker">최근 변경</p>
            <h3>프로젝트 변경 이력</h3>
          </div>
        </div>
        <div id="selected-entry-change-list" class="audit-list empty-state">프로젝트를 선택하면 최근 변경을 표시합니다.</div>
      `;
      const auditCard = dom.entryEditor.querySelector("#audit-log-list")?.closest(".info-card");
      if (auditCard?.parentElement) {
        auditCard.parentElement.insertBefore(changeSection, auditCard);
      } else {
        dom.entryEditor.appendChild(changeSection);
      }
      dom.selectedEntryChangeSection = changeSection;
      dom.selectedEntryChangeList = changeSection.querySelector("#selected-entry-change-list");
    }

    renderOrganizationAdminPanel();
    mountParityReportEnhancements();
  }


  return {
    mountRuntimeEnhancements,
  };
}

const runtimeEnhancementsRoot = typeof window !== 'undefined' ? window : globalThis;
runtimeEnhancementsRoot.RUNTIME_ENHANCEMENTS = runtimeEnhancementsRoot.RUNTIME_ENHANCEMENTS || {};
runtimeEnhancementsRoot.RUNTIME_ENHANCEMENTS.createRuntimeEnhancements = createRuntimeEnhancements;
