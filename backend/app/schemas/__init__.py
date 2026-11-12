"""Shared schemas and contracts for CORTEX-GUARD MVP v1."""

from typing import Literal

from pydantic import BaseModel, Field

from backend.app.core.constants import MAX_INPUT_LENGTH


class AnalyzeRequest(BaseModel):
    url: str = Field(..., max_length=MAX_INPUT_LENGTH)
    visible_text: str = Field(..., max_length=MAX_INPUT_LENGTH)


class AnalyzeResponse(BaseModel):
    risk_score: float
    label: str
    context_pattern: str
    evidence_chain: list[str]


class RawInputEvent(BaseModel):
    type: Literal["text", "url", "file"]
    content: str = Field(..., max_length=MAX_INPUT_LENGTH)
    session_id: str | None = None


class NormalizedEvent(BaseModel):
    event_id: str
    type: Literal["text", "url", "file"]
    clean_content: str = Field(..., max_length=MAX_INPUT_LENGTH)
    session_id: str


class FeatureResult(BaseModel):
    features: dict[str, dict[str, bool | int | float | str]]
    evidence_chain: list[str]


class RiskResult(BaseModel):
    text_risk: float
    url_risk: float
    file_risk: float


class ContextEvent(BaseModel):
    event_type: Literal["message", "link", "otp_request", "file"]
    timestamp: str
    content: str = Field(..., max_length=MAX_INPUT_LENGTH)


class ContextResult(BaseModel):
    context_risk: float
    pattern: Literal["none", "multi_step_attack"]


class FusionResult(BaseModel):
    risk_score: float


class ExplanationResult(BaseModel):
    evidence_chain: list[str]
