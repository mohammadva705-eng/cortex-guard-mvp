"""Label resolution for CORTEX-GUARD MVP v1."""

from backend.app.core.constants import FALLBACK_LABEL
from backend.app.schemas import FusionResult


class LabelResolver:
    def resolve(self, fusion: FusionResult) -> str:
        try:
            risk_score = fusion.risk_score

            if 0.0 <= risk_score <= 0.3:
                return "safe"

            if risk_score <= 0.6:
                return "suspicious"

            if risk_score <= 0.8:
                return "phishing"

            return "critical_phishing"
        except (AttributeError, TypeError, ValueError):
            return FALLBACK_LABEL
