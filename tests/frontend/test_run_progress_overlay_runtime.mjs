import assert from "node:assert/strict";
import test from "node:test";
import { createRunProgressOverlayController } from "../../frontend/run-progress-overlay-runtime.js";

function createClassList(element) {
  const values = new Set();
  return {
    add(...items) {
      for (const item of items) values.add(item);
      element.className = [...values].join(" ");
    },
    remove(...items) {
      for (const item of items) values.delete(item);
      element.className = [...values].join(" ");
    },
    contains(item) {
      return values.has(item);
    },
  };
}

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.parentNode = null;
    this.id = "";
    this.className = "";
    this.textContent = "";
    this.style = {};
    this.attributes = {};
    this.classList = createClassList(this);
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  querySelector(selector) {
    const predicate = selector.startsWith("#")
      ? (node) => node.id === selector.slice(1)
      : (node) => String(node.className || "").split(/\s+/).includes(selector.slice(1));
    const stack = [...this.children];
    while (stack.length) {
      const node = stack.shift();
      if (predicate(node)) return node;
      stack.push(...node.children);
    }
    return null;
  }
}

function createFakeDocument() {
  const body = new FakeElement("body");
  return {
    body,
    createElement(tagName) {
      return new FakeElement(tagName);
    },
    querySelector(selector) {
      if (selector === "body") return body;
      return body.querySelector(selector);
    },
  };
}

test("run progress overlay polls until success and shows the completion message", async () => {
  const document = createFakeDocument();
  const timers = [];
  const window = {
    requestAnimationFrame(callback) {
      callback();
    },
    setTimeout(callback) {
      timers.push(callback);
      return timers.length;
    },
    clearTimeout() {},
  };
  const responses = [
    { status: "running", progress_current: 1, progress_total: 3, progress_stage: "공고 수집" },
    { status: "success", progress_current: 3, progress_total: 3, progress_stage: "완료" },
  ];
  const apiCalls = [];
  const controller = createRunProgressOverlayController({ document, window });

  controller.start();
  controller.watch("run-1", {
    pollIntervalMs: 1,
    api: async (url) => {
      apiCalls.push(url);
      return responses.shift();
    },
  });
  await Promise.resolve();
  await Promise.resolve();

  assert.equal(apiCalls[0], "/api/runs/run-1");
  const overlay = document.querySelector("#run-progress-overlay");
  assert.equal(overlay.classList.contains("is-visible"), true);
  assert.match(overlay.querySelector(".download-progress-detail")?.textContent || "", /공고 수집/);

  timers.shift()();
  await Promise.resolve();
  await Promise.resolve();

  assert.equal(overlay.querySelector(".download-progress-title")?.textContent, "실행이 완료됐습니다.");
  assert.equal(overlay.querySelector(".download-progress-bar-fill")?.style.width, "100%");
});
