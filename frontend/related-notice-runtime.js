(function attachRelatedNoticeRuntime(global) {
  function buildProjectNoticeUrl(project) {
    const source = project && typeof project === "object" ? project.source_json || {} : {};
    const bidNo = String(source.source_bid_no || "").trim().toUpperCase();
    if (!bidNo) {
      return "";
    }
    const bidOrdRaw = String(source.source_bid_ord || "").trim();
    const bidOrdDigits = bidOrdRaw.replace(/[^0-9]/g, "");
    const bidOrd = bidOrdDigits ? bidOrdDigits.padStart(3, "0").slice(-3) : "000";
    const url = new URL("https://www.g2b.go.kr/link/PNPE027_01/single/");
    url.searchParams.set("bidPbancNo", bidNo);
    url.searchParams.set("bidPbancOrd", bidOrd);
    return url.toString();
  }

  function extractTrackerEntryBidParts(entry) {
    if (!entry || typeof entry !== "object") {
      return { bidNo: "", bidOrd: "" };
    }
    const directBidNo = String(entry.source_bid_no || "").trim().toUpperCase();
    const directBidOrdRaw = String(entry.source_bid_ord || "").trim();
    const directBidOrdDigits = directBidOrdRaw.replace(/[^0-9]/g, "");
    if (directBidNo) {
      return {
        bidNo: directBidNo,
        bidOrd: directBidOrdDigits ? directBidOrdDigits.padStart(3, "0").slice(-3) : "000",
      };
    }
    const entryKey = String(entry.entry_key || "").trim();
    const match = entryKey.match(/^([^|]+)\|([^|]+)/);
    if (!match) {
      return { bidNo: "", bidOrd: "" };
    }
    const bidNo = String(match[1] || "").trim().toUpperCase();
    const bidOrdDigits = String(match[2] || "").trim().replace(/[^0-9]/g, "");
    return {
      bidNo,
      bidOrd: bidOrdDigits ? bidOrdDigits.padStart(3, "0").slice(-3) : "000",
    };
  }

  function buildTrackerEntryNoticeUrl(entry) {
    const { bidNo, bidOrd } = extractTrackerEntryBidParts(entry);
    if (!bidNo) {
      return "";
    }
    const url = new URL("https://www.g2b.go.kr/link/PNPE027_01/single/");
    url.searchParams.set("bidPbancNo", bidNo);
    url.searchParams.set("bidPbancOrd", bidOrd);
    return url.toString();
  }

  function formatNoticeViewerSourceLabel(value) {
    const key = String(value || "").trim().toLowerCase();
    if (key === "detail") {
      return "상세 공고";
    }
    if (key === "base") {
      return "기본 공고";
    }
    if (key === "attachment") {
      return "첨부 공고문";
    }
    return "공고문";
  }

  function buildRelatedNoticeItemMarkup(item, projectId, helpers = {}) {
    const { escapeHtml = (value) => String(value || ""), uiMode = "" } = helpers;
    const noticeHref = item.notice_detail_url || item.notice_url || "";
    const titleMarkup = noticeHref
      ? `<a class="runtime-project-related-link" href="${escapeHtml(noticeHref)}" target="_blank" rel="noreferrer">${escapeHtml(item.project_name || "-")}</a>`
      : `<strong>${escapeHtml(item.project_name || "-")}</strong>`;
    const viewButtonMarkup = noticeHref
      ? `<button class="ghost-button runtime-project-related-view-button" type="button" data-related-notice-project="${escapeHtml(projectId)}" data-related-notice-id="${escapeHtml(item.id)}">연관 공고문</button>`
      : "";
    const adminMeta = uiMode === "admin"
      ? [
          item.notice_stage ? `stage ${item.notice_stage}` : "",
          item.sales_relevance ? `bucket ${item.sales_relevance}` : "",
          item.exclusion_reason || "",
          ...(Array.isArray(item.reason_codes) ? item.reason_codes : []),
          `score ${String(item.match_score ?? 0)}`,
        ].filter(Boolean)
      : [];
    return `
      <article class="runtime-project-related-item">
        <div class="runtime-project-related-main">
          <div>
            ${titleMarkup}
            <p>${escapeHtml(item.issuer_name || "-")}</p>
          </div>
          ${viewButtonMarkup ? `<div class="runtime-project-related-actions">${viewButtonMarkup}</div>` : ""}
        </div>
        <div class="runtime-project-related-meta mono">
          <span>${escapeHtml(item.announce_date || "-")}</span>
          <span>${escapeHtml(item.bid_no || "-")} / ${escapeHtml(item.bid_ord || "-")}</span>
          ${adminMeta.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}
        </div>
      </article>
    `;
  }

  function visibleRelatedNoticeItems(items, uiMode = "") {
    const list = Array.isArray(items) ? items : [];
    if (uiMode === "admin") {
      return list;
    }
    const salesRelevant = list.filter((item) => String(item?.sales_relevance || "").trim() === "sales_relevant");
    if (salesRelevant.length) {
      return salesRelevant;
    }
    return list.filter((item) => !["reference", "excluded"].includes(String(item?.sales_relevance || "").trim()));
  }

  function buildRelatedNoticePanelMarkup(context, helpers = {}) {
    const {
      projectId = "",
      payload = null,
      items = [],
      uiMode = "",
      loadingProjectId = "",
      errorMessage = "",
    } = context || {};
    const {
      escapeHtml = (value) => String(value || ""),
      buildRelatedNoticeItemMarkup = () => "",
    } = helpers;
    let statusBanner = "";
    if (loadingProjectId === projectId && !payload && !items.length) {
      return '<div class="runtime-project-related"><div class="empty-state">연관 공고를 불러오는 중입니다.</div></div>';
    }
    if (errorMessage && !payload && !items.length) {
      return `<div class="runtime-project-related"><div class="empty-state">연관 공고를 불러오지 못했습니다: ${escapeHtml(errorMessage)}</div></div>`;
    }
    if (payload && payload.status === "pending") {
      if (!items.length) {
        return `<div class="runtime-project-related"><div class="empty-state">${escapeHtml(payload.message || "연관 공고를 준비 중입니다.")}</div></div>`;
      }
      statusBanner = `<div class="empty-state">${escapeHtml(payload.message || "연관 공고를 준비 중입니다.")}</div>`;
    }
    if (payload && payload.status === "failed") {
      return `<div class="runtime-project-related"><div class="empty-state">${escapeHtml(payload.message || "연관 공고 준비에 실패했습니다.")}</div></div>`;
    }
    if (payload && payload.status === "missing") {
      return `<div class="runtime-project-related"><div class="empty-state">${escapeHtml(payload.message || "연관 공고 저장본이 아직 없습니다.")}</div></div>`;
    }
    if (!statusBanner && payload && payload.source === "seed_fallback") {
      statusBanner = '<div class="empty-state">임시 연관 공고입니다. 백그라운드 계산이 끝나면 자동으로 갱신됩니다.</div>';
    }
    if (!items.length) {
      return '<div class="runtime-project-related"><div class="empty-state">같이 수집된 연관 공고가 없습니다.</div></div>';
    }
    const visibleItems = visibleRelatedNoticeItems(items, uiMode);
    return `
      <div class="runtime-project-related">
        ${statusBanner}
        <div class="runtime-project-related-head">
          <strong>연관 공고</strong>
          <span class="mono">${escapeHtml(String(visibleItems.length))}건</span>
        </div>
        <div class="runtime-project-related-list">
          ${visibleItems.map((item) => buildRelatedNoticeItemMarkup(item, projectId, { escapeHtml, uiMode })).join("")}
        </div>
      </div>
    `;
  }

  function buildNoticeViewerDocumentsMarkup(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
      formatNoticeViewerSourceLabel = (value) => String(value || ""),
    } = helpers;
    const documents = Array.isArray(payload?.documents) ? payload.documents : [];
    if (!documents.length) {
      return '<p class="notice-viewer-state">공고문 본문을 읽지 못했습니다.</p>';
    }
    return documents
      .map(
        (document) => `
          <section class="notice-viewer-section${document.is_primary ? " is-primary" : ""}">
            <div class="notice-viewer-section-head">
              <strong>${escapeHtml(formatNoticeViewerSourceLabel(document.source_label || "notice"))}</strong>
              <span class="mono">${escapeHtml(document.title || document.url || "-")}</span>
            </div>
            <pre>${escapeHtml(document.text || "본문을 읽지 못했습니다.")}</pre>
          </section>
        `,
      )
      .join("");
  }

  function buildNoticeViewerHtml(payload, helpers = {}) {
    const {
      escapeHtml = (value) => String(value || ""),
    } = helpers;
    const title = payload?.title || "공고문";
    const meta = payload?.meta || "";
    const body = payload?.body || "";
    return `<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f8f2ea;
        --panel: rgba(255, 252, 247, 0.96);
        --line: rgba(131, 101, 70, 0.18);
        --ink: #2d1b12;
        --muted: #6b5746;
        --accent: #aa4519;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        background: linear-gradient(180deg, #fbf6ef, #f3e8db);
        color: var(--ink);
        font: 15px/1.6 "Segoe UI", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
      }
      .notice-viewer-shell {
        width: min(1200px, calc(100vw - 32px));
        margin: 24px auto 40px;
      }
      .notice-viewer-head {
        position: sticky;
        top: 0;
        z-index: 10;
        margin-bottom: 16px;
        padding: 20px 22px;
        border-bottom: 1px solid var(--line);
        background: rgba(248, 242, 234, 0.94);
        backdrop-filter: blur(12px);
      }
      .notice-viewer-head h1 {
        margin: 0;
        font-size: 1.55rem;
        line-height: 1.25;
      }
      .notice-viewer-meta {
        margin-top: 8px;
        color: var(--muted);
      }
      .notice-viewer-links {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 16px;
      }
      .notice-viewer-links a {
        display: inline-flex;
        align-items: center;
        min-height: 38px;
        padding: 0 14px;
        border-radius: 999px;
        background: rgba(170, 69, 25, 0.12);
        color: var(--accent);
        font-weight: 700;
        text-decoration: none;
      }
      .notice-viewer-section {
        margin-bottom: 16px;
        padding: 18px 20px;
        border: 1px solid var(--line);
        border-radius: 18px;
        background: var(--panel);
        box-shadow: 0 10px 34px rgba(54, 31, 18, 0.08);
      }
      .notice-viewer-section.is-primary {
        border-color: rgba(170, 69, 25, 0.28);
      }
      .notice-viewer-section-head {
        display: grid;
        gap: 4px;
        margin-bottom: 12px;
      }
      .notice-viewer-section pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font: 14px/1.7 "IBM Plex Mono", "Consolas", monospace;
      }
      .notice-viewer-state,
      .notice-viewer-error {
        margin: 0 0 12px;
      }
      .notice-viewer-error {
        color: var(--accent);
        font-weight: 700;
      }
      @media (max-width: 760px) {
        .notice-viewer-shell {
          width: min(100vw - 20px, 100%);
          margin-top: 14px;
        }
        .notice-viewer-head,
        .notice-viewer-section {
          padding: 16px;
        }
      }
    </style>
  </head>
  <body>
    <main class="notice-viewer-shell">
      <header class="notice-viewer-head">
        <h1>${escapeHtml(title)}</h1>
        ${meta ? `<div class="notice-viewer-meta">${escapeHtml(meta)}</div>` : ""}
      </header>
      ${body}
    </main>
  </body>
</html>`;
  }

  global.SPMSRelatedNoticeRuntime = {
    buildProjectNoticeUrl,
    extractTrackerEntryBidParts,
    buildTrackerEntryNoticeUrl,
    formatNoticeViewerSourceLabel,
    buildRelatedNoticeItemMarkup,
    buildRelatedNoticePanelMarkup,
    buildNoticeViewerDocumentsMarkup,
    buildNoticeViewerHtml,
  };
})(window);
