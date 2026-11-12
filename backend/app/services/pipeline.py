"""Pipeline orchestration for CORTEX-GUARD MVP v1."""

from backend.app.core.constants import (
    FALLBACK_CONTEXT_PATTERN,
    FALLBACK_EVIDENCE_CHAIN,
    FALLBACK_LABEL,
    FALLBACK_RISK_SCORE,
)
from backend.app.schemas import AnalyzeResponse, ContextEvent, RawInputEvent
from backend.app.services import (
    ContextEngineInterface,
    ExplanationEngineInterface,
    FeatureExtractorInterface,
    FusionEngineInterface,
    InputNormalizerInterface,
    LabelResolverInterface,
    RiskEngineInterface,
)


class AnalysisPipeline:
    def __init__(
        self,
        normalizer: InputNormalizerInterface,
        feature_extractor: FeatureExtractorInterface,
        risk_engine: RiskEngineInterface,
        context_engine: ContextEngineInterface,
        fusion_engine: FusionEngineInterface,
        explanation_engine: ExplanationEngineInterface,
        label_resolver: LabelResolverInterface,
    ) -> None:
        self.normalizer = normalizer
        self.feature_extractor = feature_extractor
        self.risk_engine = risk_engine
        self.context_engine = context_engine
        self.fusion_engine = fusion_engine
        self.explanation_engine = explanation_engine
        self.label_resolver = label_resolver

    def run(
        self,
        raw_input: RawInputEvent | dict[str, str],
        context_event: ContextEvent,
    ) -> AnalyzeResponse:
        try:
            normalized_event = self.normalizer.normalize(raw_input)
            feature_result = self.feature_extractor.extract(normalized_event)
            risk_result = self.risk_engine.evaluate(feature_result)
            context_result = self.context_engine.classify(
                normalized_event.session_id,
                context_event,
            )
            fusion_result = self.fusion_engine.fuse(risk_result, context_result)
            explanation_result = self.explanation_engine.explain(
                feature_result,
                context_result,
            )
            label = self.label_resolver.resolve(fusion_result)

            return AnalyzeResponse(
                risk_score=fusion_result.risk_score,
                label=label,
                context_pattern=context_result.pattern,
                evidence_chain=explanation_result.evidence_chain,
            )
        except Exception:
            return self._fallback_response()

    def _fallback_response(self) -> AnalyzeResponse:
        return AnalyzeResponse(
            risk_score=FALLBACK_RISK_SCORE,
            label=FALLBACK_LABEL,
            context_pattern=FALLBACK_CONTEXT_PATTERN,
            evidence_chain=FALLBACK_EVIDENCE_CHAIN,
        )
