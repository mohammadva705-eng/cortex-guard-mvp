from backend.app.schemas import ContextEvent
from backend.app.services.context_engine import ContextEngine
from backend.app.services.explanation_engine import ExplanationEngine
from backend.app.services.feature_extractor import FeatureExtractor
from backend.app.services.fusion_engine import FusionEngine
from backend.app.services.label_resolver import LabelResolver
from backend.app.services.normalizer import InputNormalizer
from backend.app.services.pipeline import AnalysisPipeline
from backend.app.services.risk_engine import RiskEngine


def _pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(
        normalizer=InputNormalizer(),
        feature_extractor=FeatureExtractor(),
        risk_engine=RiskEngine(),
        context_engine=ContextEngine(),
        fusion_engine=FusionEngine(),
        explanation_engine=ExplanationEngine(),
        label_resolver=LabelResolver(),
    )


def _event(event_type: str, content: str) -> ContextEvent:
    return ContextEvent(
        event_type=event_type,
        timestamp="2026-06-13T00:00:00Z",
        content=content,
    )


def test_full_pipeline_handles_normal_message():
    result = _pipeline().run(
        {
            "type": "text",
            "content": "hello team",
            "session_id": "session-1",
        },
        _event("message", "hello team"),
    )

    assert result.risk_score == 0.0
    assert result.label == "safe"
    assert result.context_pattern == "none"
    assert result.evidence_chain == []


def test_full_pipeline_handles_otp_attack_sequence():
    pipeline = _pipeline()
    session_id = "session-attack"

    pipeline.run(
        {
            "type": "text",
            "content": "urgent action required",
            "session_id": session_id,
        },
        _event("message", "urgent action required"),
    )
    pipeline.run(
        {
            "type": "url",
            "content": "https://example.test/login",
            "session_id": session_id,
        },
        _event("link", "https://example.test/login"),
    )
    result = pipeline.run(
        {
            "type": "text",
            "content": "verification code",
            "session_id": session_id,
        },
        _event("otp_request", "verification code"),
    )

    assert result.context_pattern == "multi_step_attack"
    assert "OTP request detected" in result.evidence_chain
    assert "Multi-step attack pattern matched" in result.evidence_chain


class FailingNormalizer:
    def normalize(self, raw_input):
        raise ValueError("normalizer failure")


def test_full_pipeline_module_failure_uses_fallback_response():
    pipeline = AnalysisPipeline(
        normalizer=FailingNormalizer(),
        feature_extractor=FeatureExtractor(),
        risk_engine=RiskEngine(),
        context_engine=ContextEngine(),
        fusion_engine=FusionEngine(),
        explanation_engine=ExplanationEngine(),
        label_resolver=LabelResolver(),
    )

    result = pipeline.run(
        {
            "type": "text",
            "content": "hello",
            "session_id": "session-1",
        },
        _event("message", "hello"),
    )

    assert result.risk_score == 0.1
    assert result.label == "suspicious"
    assert result.context_pattern == "none"
    assert result.evidence_chain == ["fallback triggered due to processing error"]
