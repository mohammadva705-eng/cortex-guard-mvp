from backend.app.core.constants import MAX_INPUT_LENGTH
from backend.app.services.normalizer import InputNormalizer


def test_empty_input_is_normalized_without_crashing():
    result = InputNormalizer().normalize(
        {
            "type": "text",
            "content": "",
            "session_id": "",
        }
    )

    assert result.type == "text"
    assert result.clean_content == ""
    assert result.session_id
    assert result.event_id


def test_invalid_input_returns_safe_fallback_event():
    result = InputNormalizer().normalize(
        {
            "type": "invalid",
            "content": "hello",
            "session_id": "session-1",
        }
    )

    assert result.type == "text"
    assert result.clean_content == ""
    assert result.session_id
    assert result.event_id


def test_large_text_does_not_exceed_max_length():
    result = InputNormalizer().normalize(
        {
            "type": "text",
            "content": "A" * (MAX_INPUT_LENGTH + 1),
            "session_id": "session-1",
        }
    )

    assert len(result.clean_content) <= MAX_INPUT_LENGTH
