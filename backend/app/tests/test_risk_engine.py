from backend.app.schemas import FeatureResult
from backend.app.services.risk_engine import RiskEngine


def test_risk_engine_computes_defined_weights_only():
    features = FeatureResult(
        features={
            "text_features": {
                "has_urgent_words": True,
                "has_otp_request": True,
                "has_threat_language": False,
            },
            "url_features": {
                "has_https": True,
                "suspicious_keywords": True,
                "url_length": 100,
            },
            "file_features": {},
        },
        evidence_chain=[],
    )

    result = RiskEngine().evaluate(features)

    assert result.text_risk == 0.6
    assert result.url_risk == 0.4
    assert result.file_risk == 0.0


def test_file_fallback_risk_is_passed_through():
    features = FeatureResult(
        features={
            "text_features": {},
            "url_features": {},
            "file_features": {"file_risk": 0.2},
        },
        evidence_chain=[],
    )

    result = RiskEngine().evaluate(features)

    assert result.file_risk == 0.2
