import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const runtimePath = path.resolve(__dirname, "../../frontend/sales-action-recommendations-runtime.js");

function loadRuntime() {
  const source = fs.readFileSync(runtimePath, "utf8")
    .replace("export function createSalesActionRecommendationsRuntime", "function createSalesActionRecommendationsRuntime")
    + "\nwindow.__runtime = { createSalesActionRecommendationsRuntime };";
  const window = {};
  const context = vm.createContext({ window, console, URLSearchParams, Date });
  vm.runInContext(source, context, { filename: runtimePath });
  return window.__runtime;
}

function makeClassList() {
  return {
    hidden: false,
    toggle(token, value) {
      if (token === "hidden") {
        this.hidden = Boolean(value);
      }
    },
  };
}

function makeRecommendationList(buttonsBySelector = {}) {
  return {
    className: "",
    innerHTML: "",
    querySelectorAll(selector) {
      const key = String(selector || "");
      for (const [selectorPart, buttons] of Object.entries(buttonsBySelector)) {
        if (key.includes(selectorPart)) {
          return buttons;
        }
      }
      return [];
    },
  };
}

function makeButton(attribute, value) {
  const clickHandlers = [];
  return {
    getAttribute(name) {
      return name === attribute ? value : "";
    },
    hasAttribute(name) {
      return name === attribute;
    },
    addEventListener(eventName, handler) {
      if (eventName === "click") {
        clickHandlers.push(handler);
      }
    },
    click(event = undefined) {
      for (const handler of [...clickHandlers]) {
        handler(event);
      }
    },
    clickHandlerCount() {
      return clickHandlers.length;
    },
  };
}

function makeClickEvent() {
  return {
    defaultPrevented: false,
    propagationStopped: false,
    preventDefault() {
      this.defaultPrevented = true;
    },
    stopPropagation() {
      this.propagationStopped = true;
    },
  };
}

test("sales action recommendations render a notice viewer button for tracker entries", () => {
  const runtime = loadRuntime();
  const noticeButton = makeButton("data-sales-action-notice-view", "0");
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const state = {
    uiMode: "user",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: "project-1",
      project_name: "추천 프로젝트",
      tracker_entry: {
        id: "entry-1",
        project_id: "project-1",
        project_name: "충주삼원초 학교복합시설 건립 설계 공모",
        demand_org_name: "충청북도 충주시",
        gross_area_scale: "8,000㎡",
        construction_cost: "311.4억원",
        building_automation_estimated_amount: "4.67억원~6.23억원",
        architect_office: "",
        construction_start_date: "착수일로부터210일",
        opening_scheduled_date: "20260519",
        demand_contact: "노인복지과/043-850-6823",
        site_location_1: "충청북도",
        site_location_2: "충주시",
      },
      action_labels: ["신규 추적 대상"],
      reasons: ["최근 등록된 고액 설계공모입니다."],
      recommended_actions: ["관심 등록"],
      automation_amount_text: "2.5억원",
      latest_meaningful_notice_type: "설계공모",
    }],
  };
  const list = makeRecommendationList({
    "data-sales-action-notice-view": [noticeButton],
    "data-sales-action-related-open": [relatedButton],
  });
  const openedUrls = [];
  const flashMessages = [];
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: makeClassList() },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: {
      localStorage: { getItem: () => "{}", setItem: () => {} },
      open(url) {
        openedUrls.push(url);
        return {};
      },
    },
    flash(message) {
      flashMessages.push(message);
    },
    api: async () => ({}),
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
  });

  recommendations.renderSalesActionRecommendationsPanel();

  assert.match(list.innerHTML, />영업 추천 리스트</);
  assert.match(list.innerHTML, /No\./);
  assert.match(list.innerHTML, /충주삼원초 학교복합시설 건립 설계 공모/);
  assert.match(list.innerHTML, /발주처<\/strong> 충청북도 충주시/);
  assert.match(list.innerHTML, /연면적<\/strong> 8,000㎡/);
  assert.match(list.innerHTML, /공사비<\/strong> 311.4억원/);
  assert.match(list.innerHTML, /빌딩자동제어 추정금액\(공사비의 1\.5~2%\)<\/strong> 4.67억원~6.23억원/);
  assert.match(list.innerHTML, /착공<\/strong> 착수일로부터210일/);
  assert.match(list.innerHTML, /개찰예정일<\/strong> 2026년 05월 19일/);
  assert.match(list.innerHTML, /담당<\/strong> 노인복지과\/043-850-6823/);
  assert.match(list.innerHTML, /현장<\/strong> 충청북도 충주시/);
  assert.match(list.innerHTML, />영업</);
  assert.match(list.innerHTML, /data-sales-action-notice-view="0"/);
  assert.match(list.innerHTML, />공고문 보기<\/button>/);

  noticeButton.click();

  assert.deepEqual(openedUrls, ["/api/tracker-entries/entry-1/notice-file-view"]);
  assert.deepEqual(flashMessages, []);
});

test("sales action recommendations opens related notices with a fast read before manual recompute", async () => {
  const runtime = loadRuntime();
  const projectId = "4a74afbf-3dfc-57b5-8d08-45aa003e6ec0";
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const recomputeButton = makeButton("data-sales-action-related-recompute", projectId);
  const state = {
    uiMode: "user",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: projectId,
      project_name: "Fast related notice demo",
      tracker_entry: { id: "entry-1", project_id: projectId, project_name: "Fast related notice demo" },
      action_labels: ["label"],
      reasons: ["reason"],
      recommended_actions: ["action"],
      automation_amount_text: "2.5",
      latest_meaningful_notice_type: "design",
    }],
  };
  const list = makeRecommendationList({
    "data-sales-action-related-open": [relatedButton],
    "data-sales-action-related-recompute": [recomputeButton],
  });
  const apiCalls = [];
  const timers = [];
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: makeClassList() },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: {
      localStorage: { getItem: () => "{}", setItem: () => {} },
      setTimeout(handler, delay) {
        timers.push({ handler, delay });
      },
      open() {
        throw new Error("raw related notice json should not be opened");
      },
    },
    flash() {},
    api: async (requestPath, options = {}) => {
      apiCalls.push([requestPath, options.method || "GET", Boolean(options.cacheBust)]);
      if (requestPath === `/api/projects/${projectId}/related-notices?quick=true`) {
        return {
          status: "ready",
          source: "raw_search",
          message: "quick related notice result",
          items: [{ id: "quick-1", project_name: "quick followup notice" }],
        };
      }
      if (requestPath === `/api/projects/${projectId}/related-notices/recompute`) {
        return { status: "queued", queued: true, message: "related notice recompute started" };
      }
      if (requestPath === `/api/projects/${projectId}/related-notices/progress`) {
        const progressCalls = apiCalls.filter(([path]) => path === `/api/projects/${projectId}/related-notices/progress`).length;
        return {
          status: progressCalls > 1 ? "ready" : "running",
          message: progressCalls > 1 ? "related notice recompute finished" : "related notice recompute running",
          items: [{ id: "notice-1", project_name: "followup design notice" }],
        };
      }
      if (requestPath === `/api/projects/${projectId}/related-notices?refresh=true`) {
        return {
          status: "ready",
          source: "precomputed",
          message: "",
          items: [{ id: "notice-1", project_name: "followup design notice" }],
        };
      }
      throw new Error(`unexpected api path: ${requestPath}`);
    },
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
  });

  recommendations.renderSalesActionRecommendationsPanel();
  relatedButton.click();
  assert.match(list.innerHTML, /Fast related notice demo/);
  await state.salesRecommendationRelatedRequest;

  await state.salesRecommendationRelatedRecomputeRequest;

  assert.deepEqual(apiCalls, [
    [`/api/projects/${projectId}/related-notices?quick=true`, "GET", true],
    [`/api/projects/${projectId}/related-notices/recompute`, "POST", false],
  ]);
  assert.equal(timers.length, 1);
  assert.match(list.innerHTML, /quick followup notice/);
  assert.match(list.innerHTML, /related notice recompute started/);

  await timers.shift().handler();
  assert.deepEqual(apiCalls.map(([path]) => path), [
    `/api/projects/${projectId}/related-notices?quick=true`,
    `/api/projects/${projectId}/related-notices/recompute`,
    `/api/projects/${projectId}/related-notices/progress`,
  ]);
  assert.match(list.innerHTML, /followup design notice/);
});

test("sales action related buttons contain clicks inside the recommendation panel", async () => {
  const runtime = loadRuntime();
  const projectId = "project-contained";
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const recomputeButton = makeButton("data-sales-action-related-recompute", projectId);
  const state = {
    uiMode: "user",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesRecommendationRelatedPayloads: {
      [projectId]: { status: "missing", message: "저장된 후속공고 정보가 없습니다.", items: [] },
    },
    salesRecommendationRelatedItems: {
      [projectId]: [],
    },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: projectId,
      project_name: "Contained related notice demo",
      tracker_entry: { id: "entry-1", project_id: projectId, project_name: "Contained related notice demo" },
      action_labels: ["label"],
      reasons: ["reason"],
      recommended_actions: ["action"],
      automation_amount_text: "2.5",
      latest_meaningful_notice_type: "design",
    }],
  };
  const list = makeRecommendationList({
    "data-sales-action-related-open": [relatedButton],
    "data-sales-action-related-recompute": [recomputeButton],
  });
  const apiCalls = [];
  const syncedTabs = [];
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: makeClassList() },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: { localStorage: { getItem: () => "{}", setItem: () => {} }, open() {} },
    flash() {},
    api: async (requestPath, options = {}) => {
      apiCalls.push([requestPath, options.method || "GET"]);
      if (requestPath === `/api/projects/${projectId}/related-notices`) {
        return { status: "missing", message: "저장된 후속공고 정보가 없습니다.", items: [] };
      }
      if (requestPath === `/api/projects/${projectId}/related-notices/recompute`) {
        return { status: "queued", queued: true, message: "후속공고 갱신 요청이 등록되었습니다." };
      }
      throw new Error(`unexpected api path: ${requestPath}`);
    },
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
    syncUrlState(options = {}) {
      syncedTabs.push(options.adminTab || "");
    },
  });

  recommendations.renderSalesActionRecommendationsPanel();
  const relatedEvent = makeClickEvent();
  relatedButton.click(relatedEvent);
  await state.salesRecommendationRelatedRequest;
  const recomputeEvent = makeClickEvent();
  recomputeButton.click(recomputeEvent);
  await state.salesRecommendationRelatedRecomputeRequest;

  assert.equal(relatedEvent.defaultPrevented, true);
  assert.equal(relatedEvent.propagationStopped, true);
  assert.equal(recomputeEvent.defaultPrevented, true);
  assert.equal(recomputeEvent.propagationStopped, true);
  assert.equal(state.adminTab, "sales-recommendations");
  assert.ok(syncedTabs.length >= 2);
  assert.ok(syncedTabs.every((tab) => tab === "sales-recommendations"));
  assert.deepEqual(apiCalls, [
    [`/api/projects/${projectId}/related-notices?quick=true`, "GET"],
    [`/api/projects/${projectId}/related-notices/recompute`, "POST"],
  ]);
  assert.match(list.innerHTML, /후속공고 갱신 요청이 등록되었습니다\./);
});

test("sales action related async recompute restores the sales recommendations tab after router drift", async () => {
  const runtime = loadRuntime();
  const projectId = "project-router-drift";
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const state = {
    uiMode: "user",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: projectId,
      project_name: "Router drift demo",
      tracker_entry: { id: "entry-1", project_id: projectId, project_name: "Router drift demo" },
      action_labels: ["label"],
      reasons: ["reason"],
      recommended_actions: ["action"],
      automation_amount_text: "2.5",
      latest_meaningful_notice_type: "design",
    }],
  };
  const list = makeRecommendationList({
    "data-sales-action-related-open": [relatedButton],
  });
  const syncedTabs = [];
  const sectionClassList = makeClassList();
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: sectionClassList },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: {
      localStorage: { getItem: () => "{}", setItem: () => {} },
      setTimeout() {},
      open() {},
    },
    flash() {},
    api: async (requestPath, options = {}) => {
      if (requestPath === `/api/projects/${projectId}/related-notices?quick=true`) {
        return { status: "ready", source: "raw_search", items: [{ id: "quick-1", project_name: "quick result" }] };
      }
      if (requestPath === `/api/projects/${projectId}/related-notices/recompute` && options.method === "POST") {
        state.adminTab = "project-status";
        return { status: "queued", queued: true, message: "queued after drift" };
      }
      throw new Error(`unexpected api path: ${requestPath}`);
    },
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
    syncUrlState(options = {}) {
      syncedTabs.push(options.adminTab || "");
    },
  });

  recommendations.renderSalesActionRecommendationsPanel();
  relatedButton.click(makeClickEvent());
  await state.salesRecommendationRelatedRequest;
  await state.salesRecommendationRelatedRecomputeRequest;

  assert.equal(state.adminTab, "sales-recommendations");
  assert.equal(sectionClassList.hidden, false);
  assert.equal(syncedTabs.at(-1), "sales-recommendations");
});

test("sales action recommendations render related notices inline instead of opening raw json", async () => {
  const runtime = loadRuntime();
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const state = {
    uiMode: "user",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesRecommendationRelatedPayloads: {
      "project-1": {
        status: "ready",
        message: "",
        items: [{
          id: "notice-1",
          project_name: "추천 프로젝트 실시설계 용역",
          issuer_name: "충청북도 충주시",
          announce_date: "2026-05-20",
          bid_no: "R26BK00000001",
          bid_ord: "000",
        }],
      },
    },
    salesRecommendationRelatedItems: {
      "project-1": [{
        id: "notice-1",
        project_name: "추천 프로젝트 실시설계 용역",
        issuer_name: "충청북도 충주시",
        announce_date: "2026-05-20",
        bid_no: "R26BK00000001",
        bid_ord: "000",
      }],
    },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: "project-1",
      project_name: "추천 프로젝트",
      tracker_entry: {
        id: "entry-1",
        project_id: "project-1",
        project_name: "추천 프로젝트",
      },
      action_labels: ["단계 변화 감지"],
      reasons: ["최근 실시설계 관련 공고가 확인되었습니다."],
      recommended_actions: ["설계사무소 확인"],
      automation_amount_text: "2.5억원",
      latest_meaningful_notice_type: "실시설계 / 설계용역",
    }],
  };
  const list = makeRecommendationList({
    "data-sales-action-related-open": [relatedButton],
  });
  const openedUrls = [];
  const apiCalls = [];
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: makeClassList() },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: {
      localStorage: { getItem: () => "{}", setItem: () => {} },
      open(url) {
        openedUrls.push(url);
        return {};
      },
    },
    flash() {},
    api: async (path) => {
      apiCalls.push(path);
      throw new Error(`unexpected api path: ${path}`);
    },
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
  });

  recommendations.renderSalesActionRecommendationsPanel();
  relatedButton.click();

  assert.deepEqual(openedUrls, []);
  assert.deepEqual(apiCalls, []);
  assert.match(list.innerHTML, /연관 공고/);
  assert.match(list.innerHTML, /추천 프로젝트 실시설계 용역/);
  assert.doesNotMatch(list.innerHTML, /\"project_id\":\"project-1\"/);
});

test("sales action recommendations show sales relevant related notices by default", async () => {
  const runtime = loadRuntime();
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const state = {
    uiMode: "user",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesRecommendationRelatedPayloads: {
      "project-1": { status: "ready", message: "" },
    },
    salesRecommendationRelatedItems: {
      "project-1": [
        { id: "notice-sales", project_name: "Sales followup", sales_relevance: "sales_relevant" },
        { id: "notice-reference", project_name: "Reference result", sales_relevance: "reference" },
        { id: "notice-excluded", project_name: "Proposal evaluation", sales_relevance: "excluded" },
      ],
    },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: "project-1",
      project_name: "Demo Project",
      tracker_entry: { id: "entry-1", project_id: "project-1", project_name: "Demo Project" },
      action_labels: ["label"],
      reasons: ["reason"],
      recommended_actions: ["action"],
      automation_amount_text: "2.5",
      latest_meaningful_notice_type: "design",
    }],
  };
  const list = makeRecommendationList({ "data-sales-action-related-open": [relatedButton] });
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: makeClassList() },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: { localStorage: { getItem: () => "{}", setItem: () => {} }, open() {} },
    flash() {},
    api: async () => {
      throw new Error("cached related notices should not call api");
    },
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
  });

  recommendations.renderSalesActionRecommendationsPanel();
  relatedButton.click();

  assert.match(list.innerHTML, /Sales followup/);
  assert.doesNotMatch(list.innerHTML, /Reference result/);
  assert.doesNotMatch(list.innerHTML, /Proposal evaluation/);
});

test("sales action recommendations show reference and excluded related notices in admin mode", async () => {
  const runtime = loadRuntime();
  const relatedButton = makeButton("data-sales-action-related-open", "0");
  const state = {
    uiMode: "admin",
    adminTab: "sales-recommendations",
    auth: { enabled: true, authorized: true, user: { id: "user-1" } },
    salesRecommendationRelatedPayloads: {
      "project-1": { status: "ready", message: "" },
    },
    salesRecommendationRelatedItems: {
      "project-1": [
        { id: "notice-sales", project_name: "Sales followup", sales_relevance: "sales_relevant" },
        { id: "notice-reference", project_name: "Reference result", sales_relevance: "reference", reason_codes: ["PHASE_MATCH:CONTEST_RESULT"] },
        { id: "notice-excluded", project_name: "Proposal evaluation", sales_relevance: "excluded", exclusion_reason: "HARD_EXCLUDE:proposal_evaluation" },
      ],
    },
    salesActionRecommendations: [{
      entry_id: "entry-1",
      project_id: "project-1",
      project_name: "Demo Project",
      tracker_entry: { id: "entry-1", project_id: "project-1", project_name: "Demo Project" },
      action_labels: ["label"],
      reasons: ["reason"],
      recommended_actions: ["action"],
      automation_amount_text: "2.5",
      latest_meaningful_notice_type: "design",
    }],
  };
  const list = makeRecommendationList({ "data-sales-action-related-open": [relatedButton] });
  const recommendations = runtime.createSalesActionRecommendationsRuntime({
    state,
    dom: {
      trackerSalesRecommendationSection: { classList: makeClassList() },
      trackerSalesRecommendationList: list,
      trackerSalesRecommendationRefreshButton: null,
    },
    window: { localStorage: { getItem: () => "{}", setItem: () => {} }, open() {} },
    flash() {},
    api: async () => {
      throw new Error("cached related notices should not call api");
    },
    escapeHtml: (value) => String(value ?? ""),
    replaceSalesListHtmlIfChanged(element, html) {
      element.innerHTML = html;
      return "applied";
    },
    claimSalesProject: async () => {},
  });

  recommendations.renderSalesActionRecommendationsPanel();
  relatedButton.click();

  assert.match(list.innerHTML, /Sales followup/);
  assert.match(list.innerHTML, /Reference result/);
  assert.match(list.innerHTML, /Proposal evaluation/);
  assert.match(list.innerHTML, /HARD_EXCLUDE:proposal_evaluation/);
});
