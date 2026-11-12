"""Session context pattern evaluation for CORTEX-GUARD MVP v1."""

from backend.app.core.constants import MAX_SESSION_EVENTS
from backend.app.schemas import ContextEvent, ContextResult


MULTI_STEP_CONTEXT_RISK = 0.6
FALLBACK_CONTEXT_RISK = 0.1
URGENCY_SUBSTRINGS = (
    "urgent",
    "immediately",
    "action required",
    "limited time",
)


class ContextEngine:
    def __init__(self) -> None:
        self.sessions: dict[str, list[ContextEvent]] = {}

    def classify(self, session_id: str, event: ContextEvent) -> ContextResult:
        try:
            clean_session_id = session_id.strip()
            if not clean_session_id:
                return self._fallback_result()

            self._append_event(clean_session_id, event)

            if self._has_multi_step_attack(self.sessions[clean_session_id]):
                return ContextResult(
                    context_risk=MULTI_STEP_CONTEXT_RISK,
                    pattern="multi_step_attack",
                )

            return ContextResult(
                context_risk=0.0,
                pattern="none",
            )
        except (AttributeError, TypeError, ValueError):
            return self._fallback_result()

    def _append_event(self, session_id: str, event: ContextEvent) -> None:
        events = self.sessions.setdefault(session_id, [])
        events.append(event)

        if len(events) > MAX_SESSION_EVENTS:
            del events[0 : len(events) - MAX_SESSION_EVENTS]

    def _has_multi_step_attack(self, events: list[ContextEvent]) -> bool:
        if len(events) < 3:
            return False

        recent_events = events[-3:]

        return (
            self._is_urgent_message(recent_events[0])
            and recent_events[1].event_type == "link"
            and recent_events[2].event_type == "otp_request"
        )

    def _is_urgent_message(self, event: ContextEvent) -> bool:
        content = event.content.lower()

        return event.event_type == "message" and any(
            substring in content for substring in URGENCY_SUBSTRINGS
        )

    def _fallback_result(self) -> ContextResult:
        return ContextResult(
            context_risk=FALLBACK_CONTEXT_RISK,
            pattern="none",
        )
