from backend.app.schemas import ContextResult, FeatureResult, RiskResult
from backend.app.services.explanation_engine import ExplanationEngine
from backend.app.services.fusion_engine import FusionEngine


def test_fusion_engine_returns_clamped_risk_score():
    risk = RiskResult(text_risk=1.0, url_risk=1.0, file_risk=1.0)
    context = ContextResult(context_risk=1.0, pattern="multi_step_attack")

    result = FusionEngine().fuse(risk, context)

    assert result.risk_score == 1.0


def test_file_risk_contributes_to_fused_score():
    engine = FusionEngine()
    context = ContextResult(context_risk=0.0, pattern="none")
    without_file_risk = RiskResult(text_risk=0.0, url_risk=0.0, file_risk=0.0)
    with_file_risk = RiskResult(text_risk=0.0, url_risk=0.0, file_risk=1.0)

    without_file_score = engine.fuse(without_file_risk, context).risk_score
    with_file_score = engine.fuse(with_file_risk, context).risk_score

    assert with_file_score > without_file_score


def test_explanation_engine_maps_detected_signals_to_evidence_chain():
    features = FeatureResult(
        features={
            "text_features": {
                "has_urgent_words": True,
                "has_otp_request": True,
            },
            "url_features": {
                "suspicious_keywords": True,
            },
            "file_features": {},
        },
        evidence_chain=[],
    )
    context = ContextResult(context_risk=0.6, pattern="multi_step_attack")

    result = ExplanationEngine().explain(features, context)

    assert result.evidence_chain == [
        "Urgency language detected",
        "Suspicious URL detected",
        "OTP request detected",
        "Multi-step attack pattern matched",
    ]
