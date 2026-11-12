from backend.app.core.constants import MAX_SESSION_EVENTS
from backend.app.schemas import ContextEvent
from backend.app.services.context_engine import ContextEngine


def _event(event_type: str, content: str) -> ContextEvent:
    return ContextEvent(
        event_type=event_type,
        timestamp="2026-06-13T00:00:00Z",
        content=content,
    )


def test_multi_step_attack_requires_strict_order_in_same_session():
    engine = ContextEngine()

    first = engine.classify("session-1", _event("message", "urgent action required"))
    second = engine.classify("session-1", _event("link", "https://example.test"))
    third = engine.classify("session-1", _event("otp_request", "verification code"))

    assert first.pattern == "none"
    assert second.pattern == "none"
    assert third.pattern == "multi_step_attack"
    assert third.context_risk == 0.6


def test_session_overflow_removes_oldest_events_fifo():
    engine = ContextEngine()

    for index in range(MAX_SESSION_EVENTS + 1):
        engine.classify("session-1", _event("message", f"normal message {index}"))

    events = engine.sessions["session-1"]

    assert len(events) == MAX_SESSION_EVENTS
    assert events[0].content == "normal message 1"
