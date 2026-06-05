(function attachProjectRuntime(global) {
  function buildProjectPageMeta(page, totalPages, totalProjects) {
    return `Page ${page} / ${totalPages} | ${totalProjects} project(s)`;
  }

  function buildProjectItemMarkup(project, options = {}, helpers = {}) {
    const {
      projectOpenId = "",
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
                ? `<p class="mono runtime-project-search">?꾨줈?앺듃 寃?됰챸 | ${escapeHtml(project.project_search_name)}</p>`
                : ""
            }
          </div>
          <div class="runtime-project-actions">
            <button class="ghost-button" type="button" data-project-notice-view="${escapeHtml(project.id)}">怨듦퀬臾?蹂닿린</button>
            <button class="ghost-button" type="button" data-project-apply="${escapeHtml(project.id)}">議곌굔 ?곸슜</button>
          </div>
        </div>
      </article>
    `;
  }

  function buildProjectListMarkup(projects, options = {}, helpers = {}) {
    const {
    } = helpers;
    return (projects || [])
      .map((project) =>
        buildProjectItemMarkup(
          project,
          {
            ...options,
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
