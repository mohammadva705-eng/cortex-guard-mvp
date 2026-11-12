"""Service interfaces for CORTEX-GUARD MVP v1."""

from typing import Protocol

from backend.app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ContextEvent,
    ContextResult,
    ExplanationResult,
    FeatureResult,
    FusionResult,
    NormalizedEvent,
    RawInputEvent,
    RiskResult,
)


class InputNormalizerInterface(Protocol):
    def normalize(self, raw_input: RawInputEvent | dict[str, str]) -> NormalizedEvent:
        ...


class FeatureExtractorInterface(Protocol):
    def extract(self, event: NormalizedEvent) -> FeatureResult:
        ...


class RiskEngineInterface(Protocol):
    def evaluate(self, features: FeatureResult) -> RiskResult:
        ...


class ContextEngineInterface(Protocol):
    def classify(self, session_id: str, event: ContextEvent) -> ContextResult:
        ...


class FusionEngineInterface(Protocol):
    def fuse(self, risk: RiskResult, context: ContextResult) -> FusionResult:
        ...


class LabelResolverInterface(Protocol):
    def resolve(self, fusion: FusionResult) -> str:
        ...


class ExplanationEngineInterface(Protocol):
    def explain(
        self,
        features: FeatureResult,
        context: ContextResult,
    ) -> ExplanationResult:
        ...
