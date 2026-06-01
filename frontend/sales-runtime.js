(function attachSalesRuntime(global) {
  const SALES_NOTE_TIMESTAMP_RE = /^\[([^\]]+)\]\s*(.*)$/;
  const SALES_DISPLAY_TIMEZONE = "Asia/Seoul";

  function salesClaimStatusLabel(status) {
    switch (String(status || "").trim()) {
      case "won":
        return "계약 완료";
      case "lost":
        return "영업 종료";
      default:
        return "영업 진행 중";
    }
  }

  function getSalesNoteEntries(rawValue) {
    return String(rawValue || "")
      .split(/\r?\n+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function parseSalesDateValue(value) {
    if (value instanceof Date) {
      return Number.isNaN(value.getTime()) ? null : value;
    }
    const raw = String(value || "").trim();
    if (!raw) {
      return null;
    }
    const dayOnly = raw.match(/^([0-9]{4})-([0-9]{2})-([0-9]{2})(?:\([일월화수목금토]\))?$/);
    if (dayOnly) {
      return new Date(Number(dayOnly[1]), Number(dayOnly[2]) - 1, Number(dayOnly[3]));
    }
    const dayTime = raw.match(/^([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2})$/);
    if (dayTime) {
      return new Date(Date.UTC(
        Number(dayTime[1]),
        Number(dayTime[2]) - 1,
        Number(dayTime[3]),
        Number(dayTime[4]),
        Number(dayTime[5]),
      ));
    }
    const parsed = new Date(raw);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function getSalesDateParts(value = new Date()) {
    const parsed = parseSalesDateValue(value);
    if (!parsed || Number.isNaN(parsed.getTime())) {
      return null;
    }
    const parts = new Intl.DateTimeFormat("ko-KR", {
      timeZone: SALES_DISPLAY_TIMEZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      weekday: "short",
    }).formatToParts(parsed);
    const year = parts.find((part) => part.type === "year")?.value || "";
    const month = parts.find((part) => part.type === "month")?.value || "";
    const day = parts.find((part) => part.type === "day")?.value || "";
    const weekday = (parts.find((part) => part.type === "weekday")?.value || "").replace(".", "");
    return {
      parsed,
      year,
      month,
      day,
      weekday,
      yearNumber: Number(year) || 0,
      monthNumber: Number(month) || 0,
    };
  }

  function getSalesYearMonthBucket(value = new Date()) {
    const parts = getSalesDateParts(value);
    if (!parts) {
      return null;
    }
    return {
      year: parts.yearNumber,
      month: parts.monthNumber,
      yearLabel: parts.year,
      monthLabel: `${parts.monthNumber}월`,
    };
  }

  function formatSalesDateLabel(value = new Date()) {
    const parts = getSalesDateParts(value);
    if (!parts) {
      const fallback = String(value || "").trim();
      return fallback || "";
    }
    return `${parts.year}-${parts.month}-${parts.day}(${parts.weekday})`;
  }

  function formatSalesNoteTimestamp(value = new Date()) {
    return formatSalesDateLabel(value);
  }

  function serializeSalesNoteEntry(text, timestamp = formatSalesNoteTimestamp()) {
    const trimmed = String(text || "").trim();
    if (!trimmed) {
      return "";
    }
    return timestamp ? `[${timestamp}] ${trimmed}` : trimmed;
  }

  function parseSalesNoteEntry(rawEntry, fallbackTimestamp = "") {
    const raw = String(rawEntry || "").trim();
    if (!raw) {
      return null;
    }
    const matched = raw.match(SALES_NOTE_TIMESTAMP_RE);
    if (matched) {
      return {
        timestamp: formatSalesDateLabel(matched[1]),
        text: matched[2] || "",
        raw,
      };
    }
    return {
      timestamp: formatSalesDateLabel(fallbackTimestamp),
      text: raw,
      raw,
    };
  }

  function getSalesNoteTimeline(rawValue, claimedAt = "") {
    const fallbackClaimedAt = formatSalesNoteTimestamp(claimedAt);
    return getSalesNoteEntries(rawValue)
      .map((entry, index) => parseSalesNoteEntry(entry, index === 0 ? fallbackClaimedAt : ""))
      .filter(Boolean);
  }

  function getLatestSalesNoteEntry(rawValue) {
    const entries = getSalesNoteTimeline(rawValue);
    return entries.length ? entries[entries.length - 1].text : "";
  }

  function getLatestSalesNoteItem(rawValue, claimedAt = "") {
    const entries = getSalesNoteTimeline(rawValue, claimedAt);
    return entries.length ? entries[entries.length - 1] : null;
  }

  function extractContractAmountTextFromSalesNote(rawValue, formatContractAmountDisplay) {
    const entries = getSalesNoteTimeline(rawValue);
    for (let index = entries.length - 1; index >= 0; index -= 1) {
      const matched = String(entries[index]?.text || "").match(/계약금액\s+(.+)$/);
      if (matched && String(matched[1] || "").trim()) {
        return typeof formatContractAmountDisplay === "function"
          ? formatContractAmountDisplay(matched[1])
          : String(matched[1] || "").trim();
      }
    }
    return "";
  }

  function formatSalesNoteTextForDisplay(text, formatContractAmountDisplay) {
    const raw = String(text || "").trim();
    if (!raw) {
      return "";
    }
    if (typeof formatContractAmountDisplay !== "function") {
      return raw;
    }
    return raw.replace(/계약금액\s+([\d,\s]+)/g, (_matched, amount) => `계약금액 ${formatContractAmountDisplay(amount)}`);
  }

  function removeLatestSalesNoteEntry(rawValue) {
    const entries = getSalesNoteEntries(rawValue);
    if (!entries.length) {
      return "";
    }
    return entries.slice(0, -1).join("\n");
  }

  global.SPMSSalesRuntime = {
    salesClaimStatusLabel,
    getSalesNoteEntries,
    parseSalesDateValue,
    getSalesDateParts,
    getSalesYearMonthBucket,
    formatSalesDateLabel,
    formatSalesNoteTimestamp,
    serializeSalesNoteEntry,
    parseSalesNoteEntry,
    getSalesNoteTimeline,
    getLatestSalesNoteEntry,
    getLatestSalesNoteItem,
    extractContractAmountTextFromSalesNote,
    formatSalesNoteTextForDisplay,
    removeLatestSalesNoteEntry,
  };
})(window);
