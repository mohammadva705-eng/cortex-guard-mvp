"""Risk fusion engine for CORTEX-GUARD MVP v1."""

from backend.app.schemas import ContextResult, FusionResult, RiskResult


TEXT_BASE_WEIGHT = 0.4
URL_BASE_WEIGHT = 0.3
FILE_BASE_WEIGHT = 0.1
CONTEXT_BASE_WEIGHT = 0.3
CONTEXT_ADAPTIVE_WEIGHT = 0.2
URL_ADAPTIVE_WEIGHT = 0.1
CONTEXT_ADAPTIVE_THRESHOLD = 0.7
FALLBACK_RISK_SCORE = 0.1


class FusionEngine:
    def fuse(self, risk: RiskResult, context: ContextResult) -> FusionResult:
        try:
            weights = self._normalized_weights(risk, context)
            risk_score = (
                risk.text_risk * weights["text"]
                + risk.url_risk * weights["url"]
                + risk.file_risk * weights["file"]
                + context.context_risk * weights["context"]
            )

            return FusionResult(risk_score=self._clamp(risk_score))
        except (AttributeError, TypeError, ValueError, ZeroDivisionError):
            return FusionResult(risk_score=FALLBACK_RISK_SCORE)

    def _normalized_weights(
        self,
        risk: RiskResult,
        context: ContextResult,
    ) -> dict[str, float]:
        weights = {
            "text": TEXT_BASE_WEIGHT,
            "url": URL_BASE_WEIGHT,
            "file": FILE_BASE_WEIGHT,
            "context": CONTEXT_BASE_WEIGHT,
        }

        if context.context_risk > CONTEXT_ADAPTIVE_THRESHOLD:
            weights["context"] += CONTEXT_ADAPTIVE_WEIGHT

        if risk.url_risk > 0.0:
            weights["url"] += URL_ADAPTIVE_WEIGHT

        total_weight = sum(weights.values())

        return {
            name: value / total_weight
            for name, value in weights.items()
        }

    def _clamp(self, value: float) -> float:
        if value >= 1.0 - 1e-12:
            return 1.0

        if value <= 1e-12:
            return 0.0

        return max(0.0, min(1.0, value))
