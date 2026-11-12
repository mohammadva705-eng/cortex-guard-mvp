"""FastAPI application for CORTEX-GUARD MVP v1."""

import json

try:
    from fastapi import FastAPI
except ModuleNotFoundError:
    FastAPI = None

from backend.app.core.constants import PROJECT_NAME, PROJECT_VERSION
from backend.app.routes.api import router


class FallbackASGIApp:
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return

        body = json.dumps(
            {
                "risk_score": 0.1,
                "label": "suspicious",
                "context_pattern": "none",
                "evidence_chain": ["fallback triggered due to processing error"],
            }
        ).encode("utf-8")

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


if FastAPI is None:
    app = FallbackASGIApp()
else:
    app = FastAPI(
        title=PROJECT_NAME,
        version=PROJECT_VERSION,
    )
    app.include_router(router)
