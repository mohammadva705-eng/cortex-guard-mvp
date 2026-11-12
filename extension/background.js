const BACKEND_URL = "http://localhost:8000/analyze";
const MAX_CONTENT_LENGTH = 5000;
const RISK_NOTIFICATION_THRESHOLD = 0.6;
const REQUEST_TIMEOUT_MS = 2000;
const RETRY_ATTEMPTS = 1;
const DISPLAY_LABELS = {
  safe: "آمن",
  suspicious: "مريب",
  phishing: "تصيّد",
  critical_phishing: "تصيّد حرج"
};
const DISPLAY_PATTERNS = {
  none: "لا يوجد نمط متعدد الخطوات",
  multi_step_attack: "هجوم متعدد الخطوات"
};
const DISPLAY_EVIDENCE = {
  "Urgency language detected": "تم رصد لغة استعجال",
  "Suspicious URL detected": "تم رصد رابط مريب",
  "OTP request detected": "تم رصد طلب رمز تحقق",
  "Multi-step attack pattern matched": "تطابق نمط هجوم متعدد الخطوات"
};

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || message.type !== "ANALYZE_ACTIVE_TAB") {
    return false;
  }

  void analyzeTab(message.tabId).then(sendResponse, () => sendResponse(null));
  return true;
});

async function analyzeTab(tabId) {
  if (!Number.isInteger(tabId)) {
    return null;
  }

  try {
    await chrome.action.setBadgeText({ tabId, text: "" });
  } catch (_error) {
    // The popup still reports the analysis state if the badge cannot be cleared.
  }

  try {
    const pageData = await collectPageData(tabId);
    const analysis = await sendToBackend(pageData, tabId);

    if (analysis) {
      try {
        await updateNotificationState(analysis, tabId);
      } catch (_error) {
        // A notification failure must not discard the analysis result.
      }
    }

    return analysis;
  } catch (_error) {
    return null;
  }
}

async function collectPageData(tabId) {
  try {
    return await chrome.tabs.sendMessage(tabId, {
      type: "ANALYZE_CURRENT_PAGE"
    });
  } catch (_error) {
    const results = await chrome.scripting.executeScript({
      target: {
        tabId
      },
      func: () => {
        const bodyText = document.body ? document.body.innerText : "";
        const text = bodyText.trim().slice(0, 5000);
        const cleanText = text.toLowerCase();
        const urlPath = new URL(window.location.href).pathname.toLowerCase();
        const otpSubstrings = [
          "otp",
          "one-time password",
          "one time password",
          "verification code"
        ];
        const urgencySubstrings = [
          "urgent",
          "immediately",
          "action required",
          "limited time"
        ];
        const supportedFileExtensions = [
          ".txt",
          ".pdf"
        ];
        let eventType = "link";

        if (otpSubstrings.some((substring) => cleanText.includes(substring))) {
          eventType = "otp_request";
        } else if (urgencySubstrings.some((substring) => cleanText.includes(substring))) {
          eventType = "message";
        } else if (supportedFileExtensions.some((extension) => urlPath.endsWith(extension))) {
          eventType = "file";
        }

        return {
          url: window.location.href,
          text,
          events: [
            {
              event_type: eventType,
              timestamp: new Date().toISOString(),
              content: `${window.location.href}\n${text}`.slice(0, 5000)
            }
          ]
        };
      }
    });

    return results && results[0] ? results[0].result : null;
  }
}

async function sendToBackend(pageData, tabId) {
  if (!pageData) {
    return null;
  }

  try {
    const response = await fetchWithSingleRetry(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestFromPageData(pageData, tabId))
    });

    if (!response || !response.ok) {
      return null;
    }

    return await response.json();
  } catch (_error) {
    // Silent fail by specification.
    return null;
  }
}

function requestFromPageData(pageData, tabId) {
  const event = latestEvent(pageData);
  const eventType = event.event_type || "message";
  const requestTypeByEventType = {
    message: "text",
    link: "url",
    otp_request: "text",
    file: "file"
  };

  return {
    type: requestTypeByEventType[eventType] || "text",
    content: event.content.slice(0, MAX_CONTENT_LENGTH),
    session_id: String(tabId),
    event_type: eventType
  };
}

function latestEvent(pageData) {
  if (Array.isArray(pageData.events) && pageData.events.length > 0) {
    return pageData.events[pageData.events.length - 1];
  }

  return {
    event_type: "message",
    content: `${pageData.url}\n${pageData.text}`.slice(0, MAX_CONTENT_LENGTH)
  };
}

async function fetchWithSingleRetry(url, options) {
  for (let attempt = 0; attempt <= RETRY_ATTEMPTS; attempt += 1) {
    try {
      return await fetchWithTimeout(url, options);
    } catch (_error) {
      if (attempt === RETRY_ATTEMPTS) {
        throw _error;
      }
    }
  }

  return null;
}

async function fetchWithTimeout(url, options) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

async function updateNotificationState(analysis, tabId) {
  if (!analysis || !Number.isFinite(analysis.risk_score)) {
    return;
  }

  const riskScore = analysis.risk_score;
  const scoreText = riskScore.toFixed(2);
  const isHighRisk = riskScore >= RISK_NOTIFICATION_THRESHOLD;

  await chrome.action.setBadgeBackgroundColor({
    tabId,
    color: isHighRisk ? "#B00020" : "#0F766E"
  });
  await chrome.action.setBadgeText({
    tabId,
    text: scoreText
  });
  await chrome.action.setTitle({
    tabId,
    title: `CORTEX-GUARD | ${scoreText} | ${DISPLAY_LABELS[analysis.label] || analysis.label}`
  });

  if (!isHighRisk) {
    return;
  }

  const evidence = Array.isArray(analysis.evidence_chain)
    ? analysis.evidence_chain.map((item) => DISPLAY_EVIDENCE[item] || item).join(" | ")
    : "";
  const label = DISPLAY_LABELS[analysis.label] || analysis.label;
  const pattern = DISPLAY_PATTERNS[analysis.context_pattern] || analysis.context_pattern;

  await chrome.notifications.create(`cortex-guard-${tabId}-${Date.now()}`, {
    type: "basic",
    iconUrl: "icons/icon128.png",
    title: `CORTEX-GUARD: ${label}`,
    message: `الخطر ${scoreText} | ${pattern}\n${evidence}`
  });
}
