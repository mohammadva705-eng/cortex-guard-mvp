const MAX_TEXT_LENGTH = 5000;
const URGENCY_SUBSTRINGS = [
  "urgent",
  "immediately",
  "action required",
  "limited time"
];
const OTP_SUBSTRINGS = [
  "otp",
  "one-time password",
  "one time password",
  "verification code"
];
const SUPPORTED_FILE_EXTENSIONS = [
  ".txt",
  ".pdf"
];

function extractVisibleText() {
  const bodyText = document.body ? document.body.innerText : "";

  return bodyText.trim().slice(0, MAX_TEXT_LENGTH);
}

function eventTypeForPage(url, text) {
  const cleanText = text.toLowerCase();
  const urlPath = new URL(url).pathname.toLowerCase();

  if (OTP_SUBSTRINGS.some((substring) => cleanText.includes(substring))) {
    return "otp_request";
  }

  if (URGENCY_SUBSTRINGS.some((substring) => cleanText.includes(substring))) {
    return "message";
  }

  if (SUPPORTED_FILE_EXTENSIONS.some((extension) => urlPath.endsWith(extension))) {
    return "file";
  }

  return "link";
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || message.type !== "ANALYZE_CURRENT_PAGE") {
    return false;
  }

  const text = extractVisibleText();
  const eventType = eventTypeForPage(window.location.href, text);

  sendResponse({
    url: window.location.href,
    text,
    events: [
      {
        event_type: eventType,
        timestamp: new Date().toISOString(),
        content: `${window.location.href}\n${text}`.slice(0, MAX_TEXT_LENGTH)
      }
    ]
  });

  return true;
});
