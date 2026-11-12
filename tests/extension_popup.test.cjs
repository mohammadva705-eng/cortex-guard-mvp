const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const projectRoot = path.resolve(__dirname, "..");

function createElement() {
  return {
    attributes: {},
    children: [],
    dataset: {},
    disabled: false,
    hidden: false,
    listeners: {},
    style: {},
    textContent: "",
    addEventListener(name, handler) {
      this.listeners[name] = handler;
    },
    append(element) {
      this.children.push(element);
    },
    querySelector(selector) {
      return selector === "span" ? this.buttonLabel : null;
    },
    replaceChildren() {
      this.children = [];
    },
    setAttribute(name, value) {
      this.attributes[name] = value;
    }
  };
}

function createPopupHarness(response) {
  const elementIds = [
    "analyze-button",
    "status",
    "instruction",
    "error-message",
    "result",
    "risk-score",
    "risk-label",
    "context-pattern",
    "score-fill",
    "evidence-list",
    "empty-evidence"
  ];
  const elements = Object.fromEntries(
    elementIds.map((id) => [id, createElement()])
  );
  elements["analyze-button"].buttonLabel = createElement();
  const scoreTrack = createElement();
  const messages = [];
  let context;

  const document = {
    createElement: () => createElement(),
    getElementById: (id) => elements[id],
    querySelector: (selector) => selector === ".score-track" ? scoreTrack : null
  };
  const chrome = {
    tabs: {
      query: async () => [{ id: 23 }]
    },
    runtime: {
      sendMessage: async (message) => {
        messages.push({ type: message.type, tabId: message.tabId });
        if (response === null) {
          return null;
        }

        const serialized = JSON.stringify(response);
        return vm.runInContext(`JSON.parse(${JSON.stringify(serialized)})`, context);
      }
    }
  };

  context = vm.createContext({ chrome, document });
  vm.runInContext(
    fs.readFileSync(path.join(projectRoot, "extension", "popup.js"), "utf8"),
    context
  );

  return { context, elements, messages, scoreTrack };
}

test("popup renders the API result for the active tab", async () => {
  const harness = createPopupHarness({
    risk_score: 0.6166666667,
    label: "phishing",
    context_pattern: "multi_step_attack",
    evidence_chain: [
      "Urgency language detected",
      "Suspicious URL detected",
      "OTP request detected",
      "Multi-step attack pattern matched"
    ]
  });

  await harness.elements["analyze-button"].listeners.click();

  assert.equal(harness.messages.length, 1);
  assert.equal(harness.messages[0].type, "ANALYZE_ACTIVE_TAB");
  assert.equal(harness.messages[0].tabId, 23);
  assert.equal(harness.elements["risk-score"].textContent, "62%");
  assert.equal(harness.elements["risk-label"].textContent, "تصيّد");
  assert.equal(harness.elements["evidence-list"].children.length, 4);
  assert.equal(harness.elements.result.hidden, false);
  assert.equal(harness.elements["analyze-button"].disabled, false);
});

test("popup explains when analysis is unavailable and allows retry", async () => {
  const harness = createPopupHarness(null);

  await harness.elements["analyze-button"].listeners.click();

  assert.equal(harness.elements["status"].dataset.state, "error");
  assert.equal(harness.elements["error-message"].hidden, false);
  assert.equal(harness.elements["analyze-button"].disabled, false);
});

test("background returns the analysis even if Chrome notifications fail", async () => {
  let messageListener;
  let requestBody;
  let notificationCalls = 0;
  let notificationOptions;
  const chrome = {
    runtime: {
      onMessage: {
        addListener(listener) {
          messageListener = listener;
        }
      }
    },
    tabs: {
      sendMessage: async () => ({
        events: [{ event_type: "otp_request", content: "visible text" }]
      })
    },
    scripting: {
      executeScript: async () => [{ result: null }]
    },
    action: {
      setBadgeBackgroundColor: async () => {},
      setBadgeText: async () => {},
      setTitle: async () => {}
    },
    notifications: {
      create: async (_id, options) => {
        notificationCalls += 1;
        notificationOptions = options;
        throw new Error("notifications disabled");
      }
    }
  };
  const expectedResponse = {
    risk_score: 0.7,
    label: "phishing",
    context_pattern: "multi_step_attack",
    evidence_chain: []
  };
  const worker = {
    chrome,
    fetch: async (_url, options) => {
      requestBody = JSON.parse(options.body);
      return { ok: true, json: async () => expectedResponse };
    },
    AbortController,
    setTimeout,
    clearTimeout
  };

  vm.runInNewContext(
    fs.readFileSync(path.join(projectRoot, "extension", "background.js"), "utf8"),
    worker
  );

  let response;
  const keepsChannelOpen = messageListener(
    { type: "ANALYZE_ACTIVE_TAB", tabId: 23 },
    {},
    (value) => { response = value; }
  );
  await new Promise((resolve) => setTimeout(resolve, 30));

  assert.equal(keepsChannelOpen, true);
  assert.equal(requestBody.session_id, "23");
  assert.equal(requestBody.event_type, "otp_request");
  assert.equal(response.label, "phishing");
  assert.equal(notificationCalls, 1);
  assert.equal(notificationOptions.title, "CORTEX-GUARD: تصيّد");
  assert.match(notificationOptions.message, /^الخطر 0\.70 \| هجوم متعدد الخطوات/);
});
