"""Project-wide constants for CORTEX-GUARD MVP v1."""

PROJECT_NAME = "CORTEX-GUARD"
PROJECT_VERSION = "1.0.0"

BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
BACKEND_BASE_URL = "http://localhost:8000"

MAX_INPUT_LENGTH = 5000
MAX_SESSION_EVENTS = 50
REQUEST_TIMEOUT_SECONDS = 2
RETRY_ATTEMPTS = 1

RISK_NOTIFICATION_THRESHOLD = 0.6

FALLBACK_RISK_SCORE = 0.1
FALLBACK_LABEL = "suspicious"
FALLBACK_CONTEXT_PATTERN = "none"
FALLBACK_EVIDENCE_CHAIN = [
    "fallback triggered due to processing error",
]

ALLOWED_INPUT_FIELDS = (
    "url",
    "visible_text",
)

ALLOWED_EVENT_TYPES = (
    "text",
    "url",
    "file",
)
