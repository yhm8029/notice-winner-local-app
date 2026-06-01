(function attachArtifactRuntime(global) {
  function buildArtifactEmptyMessage(payload = {}) {
    const artifactBackend = payload.artifactBackend || "unknown";
    const persistent = Boolean(payload.persistent);
    const runStatus = String(payload.runStatus || "").trim().toLowerCase();
    if (runStatus === "success" && !persistent) {
      return `산출물이 없거나 메타데이터가 비어 있습니다. 현재 artifact backend=${artifactBackend} 이라 서버 재시작 후 목록이 사라질 수 있습니다.`;
    }
    return `No artifacts generated for this run. backend=${artifactBackend}`;
  }

  function artifactTypeLabel(artifactType) {
    const labels = {
      execution_manifest: "실행 근거 매니페스트",
      winner_csv: "최종 낙찰 CSV",
      candidate_csv: "후보 수집 CSV",
      internal_nav_csv: "내부 탐색 CSV",
      seed_csv: "시드 수집 CSV",
      tracking_excel: "트래커 엑셀",
    };
    return labels[artifactType] || artifactType;
  }

  function buildArtifactMetaBits(item, helpers = {}) {
    const { formatBytes = (value) => String(value || "") } = helpers;
    const bits = [];
    if (item.meta?.stage) {
      bits.push(`단계 ${item.meta.stage}`);
    }
    if (item.meta?.backend) {
      bits.push(`backend ${item.meta.backend}`);
    }
    if (item.meta?.requested_collect_mode) {
      bits.push(`요청 ${item.meta.requested_collect_mode}`);
    }
    if (item.meta?.runtime_profile) {
      bits.push(`프로필 ${item.meta.runtime_profile}`);
    }
    if (item.meta?.quota_fallback_used) {
      bits.push("쿼터 폴백");
    }
    bits.push(`크기 ${formatBytes(item.size_bytes || 0)}`);
    return bits.join(" | ");
  }

  function trackerColumnStyle(widths, index) {
    const width = Array.isArray(widths) ? Number(widths[index] || 0) : 0;
    if (!Number.isFinite(width) || width <= 0) {
      return "";
    }
    return `min-width:${Math.max(72, Math.round(width * 7))}px`;
  }

  function buildWorkbookTitleCells(titleRow, helpers = {}) {
    const { escapeHtml = (value) => String(value || "") } = helpers;
    if (!Array.isArray(titleRow) || !titleRow.length) {
      return '<th colspan="1">트래커 양식</th>';
    }
    const groups = [];
    let index = 0;
    while (index < titleRow.length) {
      const value = String(titleRow[index] || "").trim();
      if (value) {
        let span = 1;
        let cursor = index + 1;
        while (cursor < titleRow.length && !String(titleRow[cursor] || "").trim()) {
          span += 1;
          cursor += 1;
        }
        groups.push({ value, span, align: cursor >= titleRow.length ? "right" : "left" });
        index = cursor;
        continue;
      }
      index += 1;
    }
    if (!groups.length) {
      return `<th colspan="${titleRow.length}">트래커 양식</th>`;
    }
    return groups
      .map(
        (group) =>
          `<th colspan="${group.span}" class="tracker-title-cell tracker-title-cell-${group.align}">${escapeHtml(group.value)}</th>`,
      )
      .join("");
  }

  function canPreviewArtifact(item) {
    return ["execution_manifest", "winner_csv", "candidate_csv", "internal_nav_csv", "seed_csv", "tracking_excel"].includes(item?.artifact_type);
  }

  function buildArtifactPreviewMarkup(cached, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatJson = (value) => JSON.stringify(value, null, 2),
    } = helpers;
    if (!cached) {
      return '<div class="artifact-preview"><div class="empty-state">미리보기를 불러오는 중입니다.</div></div>';
    }
    if (cached.error) {
      return `<div class="artifact-preview"><div class="empty-state">${escapeHtml(cached.error)}</div></div>`;
    }
    if (cached.kind === "json") {
      return `<div class="artifact-preview"><pre>${escapeHtml(formatJson(cached.payload))}</pre></div>`;
    }
    if (cached.kind === "tracker_workbook") {
      const titleCells = buildWorkbookTitleCells(cached.title_row || [], { escapeHtml });
      const headerMarkup = (cached.header_row || [])
        .map((header, index) => `<th style="${trackerColumnStyle(cached.column_widths, index)}">${escapeHtml(header)}</th>`)
        .join("");
      const rowMarkup = (cached.rows || [])
        .map(
          (row) => `
            <tr>${row.map((value, index) => `<td style="${trackerColumnStyle(cached.column_widths, index)}">${escapeHtml(value || "")}</td>`).join("")}</tr>
          `,
        )
        .join("");
      return `
        <div class="artifact-preview tracker-workbook-preview">
          <div class="tracker-workbook-meta">
            <span class="mono">${escapeHtml(cached.sheet_name || "Sheet1")} | ${cached.rows.length}행 / 전체 ${cached.total_rows}행</span>
          </div>
          <p class="mono">원본 tracking_excel 산출물 미리보기입니다. 프로젝트 현황 보드의 최신 보정/보조 필터와 다를 수 있습니다.</p>
          <div class="artifact-preview-table">
            <table class="tracker-preview-table">
              <thead>
                <tr class="tracker-title-row">${titleCells}</tr>
                <tr>${headerMarkup}</tr>
              </thead>
              <tbody>${rowMarkup}</tbody>
            </table>
          </div>
        </div>
      `;
    }
    if (cached.kind === "table") {
      const headers = Array.isArray(cached.headers) ? cached.headers : [];
      const rows = Array.isArray(cached.rows) ? cached.rows : [];
      const headerMarkup = headers
        .map((header) => `<th>${escapeHtml(header)}</th>`)
        .join("");
      const rowMarkup = rows
        .map((row) => `<tr>${headers.map((header) => `<td>${escapeHtml(row?.[header] || "")}</td>`).join("")}</tr>`)
        .join("");
      return `
        <div class="artifact-preview">
          <p class="mono">${escapeHtml((cached.format || "preview").toUpperCase())} 미리보기 ${rows.length}행 / 전체 ${cached.total_rows}행</p>
          <div class="artifact-preview-table">
            <table>
              <thead><tr>${headerMarkup}</tr></thead>
              <tbody>${rowMarkup}</tbody>
            </table>
          </div>
        </div>
      `;
    }
    return '<div class="artifact-preview"><div class="empty-state">미리보기를 표시할 수 없습니다.</div></div>';
  }

  function buildArtifactCardMarkup(item, options = {}, helpers = {}) {
    const {
      openArtifactId = "",
      previewMarkup = "",
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
      artifactTypeLabel: resolveArtifactTypeLabel = artifactTypeLabel,
      buildArtifactMetaBits: resolveMetaBits = buildArtifactMetaBits,
      canPreviewArtifact: previewable = canPreviewArtifact,
    } = helpers;
    const metaBits = resolveMetaBits(item, helpers);
    const showPreview = previewable(item);
    const previewButton = showPreview
      ? `<button class="ghost-button artifact-preview-button" type="button" data-preview-artifact-id="${escapeHtml(item.id)}">${item.id === openArtifactId ? "미리보기 닫기" : "미리보기"}</button>`
      : "";
    return `
      <article class="artifact-item">
        <div class="artifact-head">
          <div>
            <strong>${escapeHtml(resolveArtifactTypeLabel(item.artifact_type))}</strong>
            <p class="mono">${escapeHtml(item.file_name)}</p>
          </div>
          <span class="mono">${escapeHtml(String(item.meta?.rows || 0))} rows</span>
        </div>
        <p>${escapeHtml(item.mime_type)}</p>
        ${metaBits ? `<p class="mono artifact-meta-line">${escapeHtml(metaBits)}</p>` : ""}
        <div class="artifact-actions">
          ${previewButton}
          <a class="artifact-link" href="${escapeHtml(item.download_url)}">다운로드</a>
        </div>
        ${previewMarkup}
      </article>
    `;
  }

  function buildArtifactSectionMarkup(section, options = {}, helpers = {}) {
    const {
      openArtifactId = "",
      renderPreview = () => "",
      renderCard = buildArtifactCardMarkup,
    } = options;
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;
    return `
      <section class="artifact-section">
        <div class="artifact-section-head">
          <div>
            <strong>${escapeHtml(section.title)}</strong>
            <p>${escapeHtml(section.subtitle)}</p>
          </div>
          <span class="mono artifact-run-meta">${escapeHtml(section.meta)}</span>
        </div>
        <div class="artifact-section-grid">
          ${(section.items || []).map((item) => renderCard(item, {
            openArtifactId,
            previewMarkup: item.id === openArtifactId ? renderPreview(item) : "",
          }, helpers)).join("")}
        </div>
      </section>
    `;
  }

  global.SPMSArtifactRuntime = {
    buildArtifactEmptyMessage,
    artifactTypeLabel,
    buildArtifactMetaBits,
    trackerColumnStyle,
    buildWorkbookTitleCells,
    canPreviewArtifact,
    buildArtifactPreviewMarkup,
    buildArtifactCardMarkup,
    buildArtifactSectionMarkup,
  };
})(window);
