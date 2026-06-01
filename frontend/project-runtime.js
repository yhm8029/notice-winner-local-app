(function attachProjectRuntime(global) {
  function buildProjectPageMeta(page, totalPages, totalProjects) {
    return `Page ${page} / ${totalPages} | ${totalProjects} project(s)`;
  }

  function buildProjectItemMarkup(project, options = {}, helpers = {}) {
    const {
      projectOpenId = "",
      relatedNoticesMarkup = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;
    return `
      <article class="runtime-project-item${project.id === projectOpenId ? " is-expanded" : ""}" data-project-id="${escapeHtml(project.id)}">
        <div class="artifact-head runtime-project-head">
          <div class="runtime-project-copy">
            <button class="runtime-project-title-button" type="button" data-project-title="${escapeHtml(project.id)}">
              ${escapeHtml(project.project_name || "-")}
            </button>
            <p>${escapeHtml(project.issuer_name || "-")}</p>
            <p class="mono">${escapeHtml(project.latest_notice_date || "-")} | ${escapeHtml(project.latest_notice_title || "-")}</p>
            ${
              project.project_search_name
                ? `<p class="mono runtime-project-search">프로젝트 검색명 | ${escapeHtml(project.project_search_name)}</p>`
                : ""
            }
          </div>
          <div class="runtime-project-actions">
            <button class="ghost-button" type="button" data-project-notice-view="${escapeHtml(project.id)}">공고문 보기</button>
            <button class="ghost-button" type="button" data-project-toggle="${escapeHtml(project.id)}">
              ${project.id === projectOpenId ? "연관 공고 닫기" : "연관 공고 보기"}
            </button>
            <button class="ghost-button" type="button" data-project-apply="${escapeHtml(project.id)}">조건 적용</button>
          </div>
        </div>
        ${relatedNoticesMarkup}
      </article>
    `;
  }

  function buildProjectListMarkup(projects, options = {}, helpers = {}) {
    const {
      renderRelatedProjectNotices = () => "",
    } = helpers;
    return (projects || [])
      .map((project) =>
        buildProjectItemMarkup(
          project,
          {
            ...options,
            relatedNoticesMarkup: renderRelatedProjectNotices(project),
          },
          helpers,
        ),
      )
      .join("");
  }

  global.SPMSProjectRuntime = {
    buildProjectPageMeta,
    buildProjectItemMarkup,
    buildProjectListMarkup,
  };
})(window);
