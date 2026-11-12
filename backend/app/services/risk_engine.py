"""Deterministic risk calculation for CORTEX-GUARD MVP v1."""

from backend.app.schemas import FeatureResult, RiskResult


TEXT_TRUE_FEATURE_WEIGHT = 0.3
URL_SUSPICIOUS_KEYWORD_WEIGHT = 0.5
HTTPS_SAFETY_BONUS = 0.1
FALLBACK_RISK_VALUE = 0.1


class RiskEngine:
    def evaluate(self, features: FeatureResult) -> RiskResult:
        try:
            feature_map = features.features

            return RiskResult(
                text_risk=self._text_risk(feature_map.get("text_features", {})),
                url_risk=self._url_risk(feature_map.get("url_features", {})),
                file_risk=self._file_risk(feature_map.get("file_features", {})),
            )
        except (AttributeError, TypeError, ValueError):
            return self._fallback_result()

    def _text_risk(self, text_features: dict[str, bool | int | float | str]) -> float:
        risk = 0.0

        for value in text_features.values():
            if value is True:
                risk += TEXT_TRUE_FEATURE_WEIGHT

        return self._clamp(risk)

    def _url_risk(self, url_features: dict[str, bool | int | float | str]) -> float:
        risk = 0.0

        if url_features.get("suspicious_keywords") is True:
            risk += URL_SUSPICIOUS_KEYWORD_WEIGHT

        if url_features.get("has_https") is True:
            risk -= HTTPS_SAFETY_BONUS

        return self._clamp(risk)

    def _file_risk(self, file_features: dict[str, bool | int | float | str]) -> float:
        file_risk = file_features.get("file_risk", 0.0)

        if isinstance(file_risk, int | float):
            return self._clamp(float(file_risk))

        return 0.0

    def _fallback_result(self) -> RiskResult:
        return RiskResult(
            text_risk=FALLBACK_RISK_VALUE,
            url_risk=FALLBACK_RISK_VALUE,
            file_risk=FALLBACK_RISK_VALUE,
        )

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
