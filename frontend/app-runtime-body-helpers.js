(function attachAppRuntimeBodyHelpers(global) {
  function createAppRuntimeBodyHelpers(options = {}) {
    const state = options.state || null;
    const dom = options.dom || {};
    const windowObject = options.windowObject || global;
    const documentObject = options.documentObject || windowObject.document || null;
    const runTypeLabels = options.runTypeLabels || {};
    const runViewRuntime = options.runViewRuntime || null;
    const renderTrackerChangeEventsPanel = options.renderTrackerChangeEventsPanel || null;

    function normalizePlatformAdminAccountDraft(draft) {
      const source = draft && typeof draft === "object" ? draft : {};
      return {
        email: String(source.email || ""),
        display_name: String(source.display_name || ""),
        role: String(source.role || "org_member").trim() || "org_member",
        password: String(source.password || ""),
      };
    }

    function syncPlatformAdminAccountDraftFromForm(form) {
      if (typeof HTMLFormElement !== "undefined" && !(form instanceof HTMLFormElement)) {
        return;
      }
      const data = new FormData(form);
      state.platformAdminAccount.draft = normalizePlatformAdminAccountDraft({
        email: data.get("email"),
        display_name: data.get("display_name"),
        role: data.get("role"),
        password: data.get("password"),
      });
    }

    function formatContractAmountInput(rawValue) {
      const digits = String(rawValue || "").replace(/\D+/g, "");
      return digits ? digits.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "";
    }

    function formatContractAmountDisplay(rawValue, fallback = "-") {
      return formatContractAmountInput(rawValue) || String(rawValue || "").trim() || fallback;
    }

    function openTrackerChangeModal() {
      state.trackerChangeModal.open = true;
      dom.trackerChangeModal?.classList.remove("hidden");
      renderTrackerChangeEventsPanel?.();
      windowObject.setTimeout(() => {
        dom.trackerChangeModalCloseButton?.focus();
      }, 0);
    }

    function closeTrackerChangeModal() {
      state.trackerChangeModal.open = false;
      dom.trackerChangeModal?.classList.add("hidden");
    }

    function mountParityReportEnhancements() {
      const reportPanel = dom.reportSelect?.closest(".panel-report");
      if (!reportPanel || !documentObject) {
        return;
      }
      const heading = reportPanel.querySelector(".panel-heading h2");
      if (heading) {
        heading.textContent = "\uC120\uD0DD\uC801 \uAC80\uC99D";
      }
      const kicker = reportPanel.querySelector(".panel-heading .kicker");
      if (kicker) {
        kicker.textContent = "GUI \uBE44\uAD50 \uB3C4\uAD6C";
      }
      if (dom.runReportButton) {
        dom.runReportButton.textContent = "\uAC80\uC99D \uC2E4\uD589";
      }
      if (dom.refreshReportButton) {
        dom.refreshReportButton.textContent = "\uAC80\uC99D \uC0C8\uB85C\uACE0\uCE68";
      }
      let note = reportPanel.querySelector("#parity-tool-note");
      if (!note) {
        note = documentObject.createElement("div");
        note.id = "parity-tool-note";
        note.className = "tracker-context";
        note.textContent = "\uC774 \uC601\uC5ED\uC740 \uC6B4\uC601 \uD544\uC218 \uAE30\uB2A5\uC774 \uC544\uB2C8\uB77C GUI \uBE44\uAD50 \uAC80\uC99D\uC6A9 \uBCF4\uC870 \uB3C4\uAD6C\uC785\uB2C8\uB2E4.";
        reportPanel.insertBefore(note, dom.reportStatus);
      }
    }

    function renderOrgAdminRuntimeReloadFallback(target) {
      if (!target) {
        return;
      }
      target.innerHTML = '<div class="empty-state">愿由ъ옄 ?붾㈃ 由ъ냼?ㅺ? 理쒖떊 ?곹깭媛 ?꾨떃?덈떎. ?덈줈怨좎묠 ???ㅼ떆 ?뺤씤?섏꽭??</div>';
    }

    function runTypeLabel(runType) {
      return runViewRuntime?.runTypeLabel(runType, runTypeLabels)
        || runTypeLabels[String(runType || "").trim()]
        || String(runType || "-");
    }

    function isProjectTrackerRun(runType) {
      const raw = String(runType || "").trim();
      return raw === "project_tracker" || raw === "winner_pipeline";
    }

    function useGlobalTrackerEntriesScope() {
      return true;
    }

    return {
      normalizePlatformAdminAccountDraft,
      syncPlatformAdminAccountDraftFromForm,
      formatContractAmountInput,
      formatContractAmountDisplay,
      openTrackerChangeModal,
      closeTrackerChangeModal,
      mountParityReportEnhancements,
      renderOrgAdminRuntimeReloadFallback,
      runTypeLabel,
      isProjectTrackerRun,
      useGlobalTrackerEntriesScope,
    };
  }

  global.SPMSAppRuntimeBodyHelpers = {
    createAppRuntimeBodyHelpers,
  };
})(typeof window !== "undefined" ? window : globalThis);
