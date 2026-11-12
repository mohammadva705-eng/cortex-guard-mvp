"""Substring-only feature extraction for CORTEX-GUARD MVP v1."""

from backend.app.schemas import FeatureResult, NormalizedEvent
from urllib.parse import urlsplit


URGENT_WORDS = (
    "urgent",
    "immediately",
    "action required",
    "limited time",
)

OTP_REQUEST_WORDS = (
    "otp",
    "one-time password",
    "one time password",
    "verification code",
)

THREAT_LANGUAGE_WORDS = (
    "suspend",
    "blocked",
    "locked",
    "terminate",
)

SUSPICIOUS_URL_KEYWORDS = (
    "login",
    "verify",
    "account",
    "secure",
    "update",
)

SUPPORTED_FILE_EXTENSIONS = (
    ".txt",
    ".pdf",
)


class FeatureExtractor:
    def extract(self, event: NormalizedEvent) -> FeatureResult:
        content = event.clean_content.lower()

        return FeatureResult(
            features={
                "text_features": self._extract_text_features(content),
                "url_features": self._extract_url_features(content),
                "file_features": self._extract_file_features(event),
            },
            evidence_chain=[],
        )

    def _extract_text_features(self, content: str) -> dict[str, bool]:
        return {
            "has_urgent_words": self._contains_any(content, URGENT_WORDS),
            "has_otp_request": self._contains_any(content, OTP_REQUEST_WORDS),
            "has_threat_language": self._contains_any(content, THREAT_LANGUAGE_WORDS),
        }

    def _extract_url_features(self, content: str) -> dict[str, bool | int]:
        return {
            "has_https": "https://" in content,
            "suspicious_keywords": self._contains_any(content, SUSPICIOUS_URL_KEYWORDS),
            "url_length": len(content),
        }

    def _extract_file_features(
        self,
        event: NormalizedEvent,
    ) -> dict[str, bool | float | str]:
        if event.type != "file":
            return {}

        try:
            if not self._is_supported_file(event.clean_content):
                return {
                    "supported": False,
                    "file_risk": 0.2,
                    "raw_text": "",
                }

            return {
                "supported": True,
                "raw_text": event.clean_content,
            }
        except (AttributeError, TypeError, ValueError):
            return {
                "supported": False,
                "file_risk": 0.2,
                "raw_text": "",
            }

    def _contains_any(self, content: str, substrings: tuple[str, ...]) -> bool:
        return any(substring in content for substring in substrings)

    def _is_supported_file(self, content: str) -> bool:
        first_line = content.splitlines()[0] if content.splitlines() else content
        file_path = urlsplit(first_line).path.lower()

        return any(
            file_path.endswith(extension)
            for extension in SUPPORTED_FILE_EXTENSIONS
        )
