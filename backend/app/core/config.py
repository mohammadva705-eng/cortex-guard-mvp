"""Shared project-level configuration for CORTEX-GUARD MVP v1."""

from dataclasses import dataclass

from backend.app.core.constants import (
    BACKEND_BASE_URL,
    BACKEND_HOST,
    BACKEND_PORT,
    MAX_INPUT_LENGTH,
    MAX_SESSION_EVENTS,
    PROJECT_NAME,
    PROJECT_VERSION,
    REQUEST_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    RISK_NOTIFICATION_THRESHOLD,
)


@dataclass(frozen=True)
class ProjectConfig:
    project_name: str = PROJECT_NAME
    project_version: str = PROJECT_VERSION
    backend_host: str = BACKEND_HOST
    backend_port: int = BACKEND_PORT
    backend_base_url: str = BACKEND_BASE_URL
    max_input_length: int = MAX_INPUT_LENGTH
    max_session_events: int = MAX_SESSION_EVENTS
    request_timeout_seconds: int = REQUEST_TIMEOUT_SECONDS
    retry_attempts: int = RETRY_ATTEMPTS
    risk_notification_threshold: float = RISK_NOTIFICATION_THRESHOLD


CONFIG = ProjectConfig()
