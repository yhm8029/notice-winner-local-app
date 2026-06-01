export function createSalesPanelControllerMarkup(deps = {}) {
  const {
    escapeHtml,
    truncate,
    formatSalesNoteTextForDisplay,
    getLatestSalesNoteItem,
    getSalesYearMonthBucket,
    formatSalesDateLabel,
    formatContractAmountDisplay,
    extractContractAmountTextFromSalesNote,
    salesClaimStatusLabel,
    formatSalesClaimEstimateLabel,
    salesViewRuntime = null,
  } = deps;

  function renderSalesNoteTimelineMarkup(noteEntries) {
    return salesViewRuntime?.buildSalesNoteTimelineMarkup?.(noteEntries, {
      escapeHtml,
      formatSalesNoteTextForDisplay,
    }) || "";
  }

  function renderClosedSalesArchiveSection(title, claims, { showContractAmount = false } = {}) {
    const currentYear = getSalesYearMonthBucket(new Date())?.year || Number(new Date().getFullYear());
    const yearGroups = new Map();

    for (const claim of claims) {
      const bucket = getSalesYearMonthBucket(claim.closed_at || claim.updated_at || claim.created_at);
      if (!bucket || !bucket.year || bucket.year > currentYear) {
        continue;
      }
      if (!yearGroups.has(bucket.year)) {
        yearGroups.set(bucket.year, new Map());
      }
      const monthGroups = yearGroups.get(bucket.year);
      if (!monthGroups.has(bucket.month)) {
        monthGroups.set(bucket.month, []);
      }
      monthGroups.get(bucket.month).push(claim);
    }

    const itemsMarkup = yearGroups.size
      ? [...yearGroups.entries()]
        .sort((left, right) => left[0] - right[0])
        .map(([year, monthGroups]) => {
          const monthMarkup = [...monthGroups.entries()]
            .sort((left, right) => left[0] - right[0])
            .map(([month, monthClaims]) => {
              const claimsMarkup = monthClaims
                .map((claim, index) => {
                  const contractAmountText = showContractAmount ? formatContractAmountDisplay(extractContractAmountTextFromSalesNote(claim.sales_note)) : "";
                  const closedDateLabel = formatSalesDateLabel(claim.closed_at || claim.updated_at || claim.created_at);
                  const ownerLabel = claim.owner_display_name || claim.owner_email || "-";
                  const latestNote = getLatestSalesNoteItem(claim.sales_note, claim.claimed_at);
                  const latestNoteLabel = latestNote
                    ? `${latestNote.timestamp ? `${latestNote.timestamp} ` : ""}${truncate(formatSalesNoteTextForDisplay(latestNote.text), 120)}`
                    : "";

                  return `
                  <article class="sales-summary-archive-item">
                    <div class="sales-summary-archive-head">
                      <strong>${escapeHtml(String(index + 1))}. ${escapeHtml(claim.project_name || "-")}</strong>
                      <span class="entry-sales-status-badge${showContractAmount ? " is-closed" : ""}">${escapeHtml(salesClaimStatusLabel(claim.claim_status))}</span>
                    </div>
                    <p class="mono">${escapeHtml(ownerLabel)} | ${escapeHtml(closedDateLabel)} closed</p>
                    <p class="mono">${showContractAmount ? `contract ${escapeHtml(contractAmountText || "-")}` : escapeHtml(formatSalesClaimEstimateLabel(claim))}</p>
                    ${latestNoteLabel ? `<p>${escapeHtml(latestNoteLabel)}</p>` : ""}
                  </article>
                `;
                })
                .join("");

              return `
              <section class="sales-summary-archive-month">
                <div class="sales-summary-archive-month-head">
                  <strong>${escapeHtml(String(month))}</strong>
                  <span class="mono">${escapeHtml(String(monthClaims.length))} items</span>
                </div>
                <div class="sales-summary-archive-list">${claimsMarkup}</div>
              </section>
            `;
            })
            .join("");

          return `
          <section class="sales-summary-archive-year">
            <div class="sales-summary-archive-year-head">
              <strong>${escapeHtml(String(year))}</strong>
              <span class="mono">${escapeHtml(String(
                [...monthGroups.values()].reduce((count, monthClaims) => count + monthClaims.length, 0)
              ))} items</span>
            </div>
            <div class="sales-summary-archive-year-list">${monthMarkup}</div>
          </section>
        `;
        })
        .join("")
      : `<div class="empty-state">${escapeHtml(`${title} archive is empty.`)}</div>`;

    return `
    <section class="sales-summary-archive-group">
      <div class="sales-summary-archive-group-head">
        <strong>${escapeHtml(title)}</strong>
        <span class="mono">${escapeHtml(String(claims.length))} items</span>
      </div>
      <div class="sales-summary-archive-list">${itemsMarkup}</div>
    </section>
  `;
  }

  return {
    renderSalesNoteTimelineMarkup,
    renderClosedSalesArchiveSection,
  };
}
