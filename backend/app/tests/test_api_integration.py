import asyncio
import json
import uuid

from backend.app.main import app


def _asgi_request(method: str, path: str, payload=None) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    incoming = [{"type": "http.request", "body": body, "more_body": False}]
    outgoing = []

    async def receive():
        if incoming:
            return incoming.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        outgoing.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "server": ("localhost", 8000),
        "client": ("test", 1),
    }

    asyncio.run(app(scope, receive, send))
    status = next(
        message["status"]
        for message in outgoing
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in outgoing
        if message["type"] == "http.response.body"
    )

    return status, json.loads(response_body or b"{}")


def test_api_preserves_event_sequence_and_session():
    session_id = f"api-test-{uuid.uuid4()}"
    events = [
        {
            "type": "text",
            "content": "http://notice.example.test urgent action required",
            "session_id": session_id,
            "event_type": "message",
        },
        {
            "type": "url",
            "content": "http://secure-login.example.test",
            "session_id": session_id,
            "event_type": "link",
        },
        {
            "type": "text",
            "content": (
                "http://verify.example.test urgent verification code required "
                "for login account suspend blocked"
            ),
            "session_id": session_id,
            "event_type": "otp_request",
        },
    ]

    responses = [
        _asgi_request("POST", "/analyze", event)
        for event in events
    ]
    session_status, session = _asgi_request(
        "GET",
        f"/session/{session_id}",
    )

    assert all(status == 200 for status, _ in responses)
    final_response = responses[-1][1]
    assert final_response["context_pattern"] == "multi_step_attack"
    assert final_response["risk_score"] >= 0.6
    assert final_response["label"] == "phishing"
    assert "Multi-step attack pattern matched" in final_response["evidence_chain"]
    assert session_status == 200
    assert [event["event_type"] for event in session["events"]] == [
        "message",
        "link",
        "otp_request",
    ]


def test_api_invalid_body_returns_global_fallback():
    status, response = _asgi_request("POST", "/analyze", [])

    assert status == 200
    assert response == {
        "risk_score": 0.1,
        "label": "suspicious",
        "context_pattern": "none",
        "evidence_chain": ["fallback triggered due to processing error"],
    }
