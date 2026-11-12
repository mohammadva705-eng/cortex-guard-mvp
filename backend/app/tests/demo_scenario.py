"""Demo scenario for CORTEX-GUARD MVP v1."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.constants import (
    FALLBACK_CONTEXT_PATTERN,
    FALLBACK_EVIDENCE_CHAIN,
    FALLBACK_LABEL,
    FALLBACK_RISK_SCORE,
)
from backend.app.schemas import AnalyzeResponse, ContextEvent
from backend.app.services.context_engine import ContextEngine
from backend.app.services.explanation_engine import ExplanationEngine
from backend.app.services.feature_extractor import FeatureExtractor
from backend.app.services.fusion_engine import FusionEngine
from backend.app.services.label_resolver import LabelResolver
from backend.app.services.normalizer import InputNormalizer
from backend.app.services.pipeline import AnalysisPipeline
from backend.app.services.risk_engine import RiskEngine


SESSION_ID = "demo-session-1"


def run_demo_scenario() -> AnalyzeResponse:
    try:
        pipeline = AnalysisPipeline(
            normalizer=InputNormalizer(),
            feature_extractor=FeatureExtractor(),
            risk_engine=RiskEngine(),
            context_engine=ContextEngine(),
            fusion_engine=FusionEngine(),
            explanation_engine=ExplanationEngine(),
            label_resolver=LabelResolver(),
        )

        pipeline.run(
            {
                "type": "text",
                "content": "http://notice.example.test urgent action required",
                "session_id": SESSION_ID,
            },
            _context_event(
                "message",
                "http://notice.example.test urgent action required",
            ),
        )
        pipeline.run(
            {
                "type": "url",
                "content": "http://secure-login.example.test",
                "session_id": SESSION_ID,
            },
            _context_event("link", "http://secure-login.example.test"),
        )

        return pipeline.run(
            {
                "type": "text",
                "content": "http://verify.example.test urgent verification code required for login account suspend blocked",
                "session_id": SESSION_ID,
            },
            _context_event(
                "otp_request",
                "http://verify.example.test urgent verification code required for login account suspend blocked",
            ),
        )
    except Exception:
        return AnalyzeResponse(
            risk_score=FALLBACK_RISK_SCORE,
            label=FALLBACK_LABEL,
            context_pattern=FALLBACK_CONTEXT_PATTERN,
            evidence_chain=FALLBACK_EVIDENCE_CHAIN,
        )


def _context_event(event_type: str, content: str) -> ContextEvent:
    return ContextEvent(
        event_type=event_type,
        timestamp="2026-07-02T00:00:00Z",
        content=content,
    )


if __name__ == "__main__":
    result = run_demo_scenario()
    output = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    print(output)
