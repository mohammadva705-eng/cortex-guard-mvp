const analyzeButton = document.getElementById("analyze-button");
const statusElement = document.getElementById("status");
const instructionElement = document.getElementById("instruction");
const errorElement = document.getElementById("error-message");
const resultElement = document.getElementById("result");
const riskScoreElement = document.getElementById("risk-score");
const riskLabelElement = document.getElementById("risk-label");
const contextPatternElement = document.getElementById("context-pattern");
const scoreTrack = document.querySelector(".score-track");
const scoreFill = document.getElementById("score-fill");
const evidenceList = document.getElementById("evidence-list");
const emptyEvidence = document.getElementById("empty-evidence");

const LABELS = {
  safe: "آمن",
  suspicious: "مريب",
  phishing: "تصيّد",
  critical_phishing: "تصيّد حرج"
};

const EVIDENCE = {
  "Urgency language detected": "تم رصد لغة استعجال",
  "Suspicious URL detected": "تم رصد رابط مريب",
  "OTP request detected": "تم رصد طلب رمز تحقق",
  "Multi-step attack pattern matched": "تطابق نمط هجوم متعدد الخطوات",
  "fallback triggered due to processing error": "تعذّر إكمال التحليل؛ أُعيدت نتيجة احتياطية"
};

const CONTEXT_PATTERNS = {
  none: "لا يوجد نمط متعدد الخطوات",
  multi_step_attack: "هجوم متعدد الخطوات"
};

analyzeButton.addEventListener("click", analyzeCurrentPage);

async function analyzeCurrentPage() {
  setLoading(true);
  resultElement.hidden = true;
  errorElement.hidden = true;

  try {
    const [activeTab] = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    if (!activeTab || !Number.isInteger(activeTab.id)) {
      throw new Error("No active tab");
    }

    const analysis = await chrome.runtime.sendMessage({
      type: "ANALYZE_ACTIVE_TAB",
      tabId: activeTab.id
    });

    if (!analysis || !Number.isFinite(analysis.risk_score)) {
      throw new Error("Analysis unavailable");
    }

    renderAnalysis(analysis);
    setStatus("اكتمل", "ready");
    instructionElement.textContent = "نتيجة التحليل الحالي.";
  } catch (_error) {
    setStatus("غير متاح", "error");
    instructionElement.textContent = "لم يكتمل الفحص.";
    errorElement.textContent = "التحليل غير متاح. تأكد من تشغيل الخادم المحلي ثم أعد المحاولة.";
    errorElement.hidden = false;
  } finally {
    setLoading(false);
  }
}

function renderAnalysis(analysis) {
  const riskScore = Math.max(0, Math.min(1, analysis.risk_score));
  const riskPercent = Math.round(riskScore * 100);
  const label = LABELS[analysis.label] || "نتيجة غير معروفة";
  const pattern = CONTEXT_PATTERNS[analysis.context_pattern] || "نمط غير معروف";

  riskScoreElement.textContent = `${riskPercent}%`;
  riskLabelElement.textContent = label;
  riskLabelElement.dataset.risk = analysis.label;
  contextPatternElement.textContent = pattern;
  scoreTrack.dataset.risk = analysis.label;
  scoreTrack.setAttribute("aria-valuenow", riskPercent.toString());
  scoreFill.style.width = `${riskPercent}%`;

  evidenceList.replaceChildren();
  const evidence = Array.isArray(analysis.evidence_chain)
    ? analysis.evidence_chain
    : [];

  for (const item of evidence) {
    const listItem = document.createElement("li");
    listItem.textContent = EVIDENCE[item] || item;
    evidenceList.append(listItem);
  }

  emptyEvidence.hidden = evidence.length > 0;
  resultElement.hidden = false;
}

function setLoading(isLoading) {
  analyzeButton.disabled = isLoading;
  analyzeButton.setAttribute("aria-busy", isLoading.toString());
  analyzeButton.querySelector("span").textContent = isLoading
    ? "جارٍ تحليل الصفحة..."
    : "حلّل الصفحة الحالية";

  if (isLoading) {
    setStatus("جارٍ الفحص", "loading");
    instructionElement.textContent = "جارٍ تحليل الصفحة.";
  }
}

function setStatus(label, state) {
  statusElement.textContent = label;
  statusElement.dataset.state = state;
}
