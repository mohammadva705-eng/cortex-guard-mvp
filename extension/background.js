const BACKEND_URL = "http://localhost:8000/analyze";
const MAX_CONTENT_LENGTH = 5000;
const RISK_NOTIFICATION_THRESHOLD = 0.6;
const REQUEST_TIMEOUT_MS = 2000;
const RETRY_ATTEMPTS = 1;

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.id) {
    return;
  }

  try {
    const pageData = await collectPageData(tab.id);
    const analysis = await sendToBackend(pageData, tab.id);

    await updateNotificationState(analysis, tab.id);
  } catch (_error) {
    // Silent fail by specification.
  }
});

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
    title: `CORTEX-GUARD | ${scoreText} | ${analysis.label}`
  });

  if (!isHighRisk) {
    return;
  }

  const evidence = Array.isArray(analysis.evidence_chain)
    ? analysis.evidence_chain.join(" | ")
    : "";

  await chrome.notifications.create(`cortex-guard-${tabId}-${Date.now()}`, {
    type: "basic",
    iconUrl: "icons/icon128.png",
    title: `CORTEX-GUARD: ${analysis.label}`,
    message: `Risk ${scoreText} | ${analysis.context_pattern}\n${evidence}`
  });
}
