"""FastAPI endpoints for CORTEX-GUARD MVP v1."""

from datetime import datetime, timezone
from typing import Any

try:
    from fastapi import APIRouter, Body
except ModuleNotFoundError:
    APIRouter = None

    def Body(default: Any = ..., **_kwargs: Any) -> Any:
        return default

from backend.app.core.constants import (
    FALLBACK_CONTEXT_PATTERN,
    FALLBACK_EVIDENCE_CHAIN,
    FALLBACK_LABEL,
    FALLBACK_RISK_SCORE,
)
from backend.app.schemas import AnalyzeResponse, ContextEvent, RawInputEvent
from backend.app.services.context_engine import ContextEngine
from backend.app.services.explanation_engine import ExplanationEngine
from backend.app.services.feature_extractor import FeatureExtractor
from backend.app.services.fusion_engine import FusionEngine
from backend.app.services.label_resolver import LabelResolver
from backend.app.services.normalizer import InputNormalizer
from backend.app.services.pipeline import AnalysisPipeline
from backend.app.services.risk_engine import RiskEngine


class _FallbackRouter:
    def post(self, *_args: object, **_kwargs: object):
        return self._decorator

    def get(self, *_args: object, **_kwargs: object):
        return self._decorator

    def _decorator(self, handler):
        return handler


router = APIRouter() if APIRouter is not None else _FallbackRouter()
context_engine = ContextEngine()
pipeline = AnalysisPipeline(
    normalizer=InputNormalizer(),
    feature_extractor=FeatureExtractor(),
    risk_engine=RiskEngine(),
    context_engine=context_engine,
    fusion_engine=FusionEngine(),
    explanation_engine=ExplanationEngine(),
    label_resolver=LabelResolver(),
)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: Any = Body(...)) -> AnalyzeResponse:
    try:
        raw_input = RawInputEvent(**request)

        return pipeline.run(
            raw_input,
            _context_event_from_request(request, raw_input),
        )
    except Exception:
        return _fallback_response()


@router.get("/session/{session_id}")
def get_session(session_id: str) -> dict[str, object]:
    try:
        events = context_engine.sessions.get(session_id, [])

        return {
            "session_id": session_id,
            "events": [
                event.model_dump() if hasattr(event, "model_dump") else event.dict()
                for event in events
            ],
        }
    except Exception:
        return {
            "session_id": session_id,
            "events": [],
        }


def _context_event_from_request(
    payload: dict[str, Any],
    request: RawInputEvent,
) -> ContextEvent:
    event_type_by_request_type = {
        "text": "message",
        "url": "link",
        "file": "file",
    }
    event_type = payload.get("event_type") or event_type_by_request_type[request.type]

    return ContextEvent(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        content=request.content,
    )


def _fallback_response() -> AnalyzeResponse:
    return AnalyzeResponse(
        risk_score=FALLBACK_RISK_SCORE,
        label=FALLBACK_LABEL,
        context_pattern=FALLBACK_CONTEXT_PATTERN,
        evidence_chain=FALLBACK_EVIDENCE_CHAIN,
    )
