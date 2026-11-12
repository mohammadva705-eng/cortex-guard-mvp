"""Evidence chain generation for CORTEX-GUARD MVP v1."""

from backend.app.core.constants import FALLBACK_EVIDENCE_CHAIN
from backend.app.schemas import ContextResult, ExplanationResult, FeatureResult


class ExplanationEngine:
    def explain(
        self,
        features: FeatureResult,
        context: ContextResult,
    ) -> ExplanationResult:
        try:
            feature_map = features.features
            text_features = feature_map.get("text_features", {})
            url_features = feature_map.get("url_features", {})

            evidence_chain: list[str] = []

            if text_features.get("has_urgent_words") is True:
                evidence_chain.append("Urgency language detected")

            if url_features.get("suspicious_keywords") is True:
                evidence_chain.append("Suspicious URL detected")

            if text_features.get("has_otp_request") is True:
                evidence_chain.append("OTP request detected")

            if context.pattern == "multi_step_attack":
                evidence_chain.append("Multi-step attack pattern matched")

            return ExplanationResult(evidence_chain=evidence_chain)
        except (AttributeError, TypeError, ValueError):
            return ExplanationResult(evidence_chain=FALLBACK_EVIDENCE_CHAIN)
