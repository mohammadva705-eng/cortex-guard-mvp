from backend.app.schemas import NormalizedEvent
from backend.app.services.feature_extractor import FeatureExtractor


def test_invalid_url_extracts_url_features_without_scoring():
    event = NormalizedEvent(
        event_id="event-1",
        type="url",
        clean_content="not-a-url",
        session_id="session-1",
    )

    result = FeatureExtractor().extract(event)

    assert result.features["url_features"] == {
        "has_https": False,
        "suspicious_keywords": False,
        "url_length": 9,
    }


def test_otp_attack_text_features_are_detected_by_substring():
    event = NormalizedEvent(
        event_id="event-1",
        type="text",
        clean_content="urgent verification code required",
        session_id="session-1",
    )

    result = FeatureExtractor().extract(event)

    assert result.features["text_features"]["has_urgent_words"] is True
    assert result.features["text_features"]["has_otp_request"] is True


def test_normal_message_has_no_text_signals():
    event = NormalizedEvent(
        event_id="event-1",
        type="text",
        clean_content="hello team meeting update",
        session_id="session-1",
    )

    result = FeatureExtractor().extract(event)

    assert result.features["text_features"]["has_urgent_words"] is False
    assert result.features["text_features"]["has_otp_request"] is False
    assert result.features["text_features"]["has_threat_language"] is False


def test_file_support_is_limited_to_txt_and_pdf():
    extractor = FeatureExtractor()
    supported_pdf = NormalizedEvent(
        event_id="event-pdf",
        type="file",
        clean_content="https://example.test/report.pdf?download=1\nraw text",
        session_id="session-1",
    )
    unsupported_file = NormalizedEvent(
        event_id="event-exe",
        type="file",
        clean_content="https://example.test/malware.exe\nraw text",
        session_id="session-1",
    )

    pdf_features = extractor.extract(supported_pdf).features["file_features"]
    unsupported_features = extractor.extract(unsupported_file).features["file_features"]

    assert pdf_features["supported"] is True
    assert unsupported_features == {
        "supported": False,
        "file_risk": 0.2,
        "raw_text": "",
    }
