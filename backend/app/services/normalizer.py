"""Input normalization service for CORTEX-GUARD MVP v1."""

from uuid import uuid4

from pydantic import ValidationError

from backend.app.core.constants import MAX_INPUT_LENGTH
from backend.app.schemas import NormalizedEvent, RawInputEvent


class InputNormalizer:
    def normalize(self, raw_input: RawInputEvent | dict[str, str]) -> NormalizedEvent:
        try:
            event = self._validate(raw_input)
            clean_content = event.content.strip().lower()[:MAX_INPUT_LENGTH]
            session_id = self._ensure_session_id(event.session_id)

            return NormalizedEvent(
                event_id=str(uuid4()),
                type=event.type,
                clean_content=clean_content,
                session_id=session_id,
            )
        except (TypeError, ValidationError, ValueError):
            return self._fallback_event()

    def _validate(self, raw_input: RawInputEvent | dict[str, str]) -> RawInputEvent:
        if isinstance(raw_input, RawInputEvent):
            return raw_input

        return RawInputEvent(**raw_input)

    def _ensure_session_id(self, session_id: str | None) -> str:
        clean_session_id = (session_id or "").strip()

        if clean_session_id:
            return clean_session_id

        return str(uuid4())

    def _fallback_event(self) -> NormalizedEvent:
        return NormalizedEvent(
            event_id=str(uuid4()),
            type="text",
            clean_content="",
            session_id=str(uuid4()),
        )
