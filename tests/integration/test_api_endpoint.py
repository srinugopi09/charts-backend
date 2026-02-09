"""Integration tests for the AG-UI SSE endpoint.

These tests call the actual FastAPI endpoint via httpx.AsyncClient
and validate SSE stream structure. Requires PostgreSQL with seed data
and a valid GOOGLE_API_KEY for Gemini.
"""

import json
import os

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport

from main import app


def _has_gemini_key() -> bool:
    from config.settings import Settings
    key = Settings().google_api_key
    return bool(key) and key != "your-gemini-api-key-here"


requires_gemini = pytest.mark.skipif(
    not _has_gemini_key(),
    reason="GOOGLE_API_KEY not set or is placeholder — skipping Gemini-dependent test",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_sse_events(text: str) -> list[dict]:
    """Parse SSE text into a list of event dicts."""
    events = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str:
                try:
                    events.append(json.loads(data_str))
                except json.JSONDecodeError:
                    pass
    return events


def make_run_input(message: str, thread_id: str = "test-thread") -> dict:
    return {
        "threadId": thread_id,
        "runId": "test-run-1",
        "messages": [{"id": "msg-1", "role": "user", "content": message}],
        "state": {},
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="module")
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_run_returns_sse(client):
    """POST to /api/agent/run should return text/event-stream."""
    resp = await client.post(
        "/api/agent/run",
        json=make_run_input("What tables are available?"),
        headers={"Accept": "text/event-stream"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_event_stream_starts_with_run_started(client):
    resp = await client.post(
        "/api/agent/run",
        json=make_run_input("Hello"),
        headers={"Accept": "text/event-stream"},
    )
    events = parse_sse_events(resp.text)
    assert len(events) > 0
    assert events[0].get("type") == "RUN_STARTED"


@pytest.mark.asyncio
async def test_event_stream_ends_with_run_finished(client):
    resp = await client.post(
        "/api/agent/run",
        json=make_run_input("Say hello"),
        headers={"Accept": "text/event-stream"},
    )
    events = parse_sse_events(resp.text)
    assert len(events) > 0
    # Last meaningful event should be RUN_FINISHED
    event_types = [e.get("type") for e in events]
    assert "RUN_FINISHED" in event_types


@requires_gemini
@pytest.mark.asyncio
async def test_text_message_events_present(client):
    """A simple question should produce text message events."""
    resp = await client.post(
        "/api/agent/run",
        json=make_run_input("What tables are available?"),
        headers={"Accept": "text/event-stream"},
    )
    events = parse_sse_events(resp.text)
    event_types = [e.get("type") for e in events]
    assert "TEXT_MESSAGE_START" in event_types
    assert "TEXT_MESSAGE_CONTENT" in event_types
    assert "TEXT_MESSAGE_END" in event_types


@requires_gemini
@pytest.mark.asyncio
async def test_tool_call_events_for_sql(client):
    """A data question should trigger tool call events."""
    resp = await client.post(
        "/api/agent/run",
        json=make_run_input("How many projects are there?"),
        headers={"Accept": "text/event-stream"},
    )
    events = parse_sse_events(resp.text)
    event_types = [e.get("type") for e in events]
    assert "TOOL_CALL_START" in event_types
    assert "TOOL_CALL_END" in event_types


@pytest.mark.asyncio
async def test_invalid_request_returns_422(client):
    """POST with missing required fields should return 422."""
    resp = await client.post(
        "/api/agent/run",
        json={"invalid": "body"},
        headers={"Accept": "text/event-stream"},
    )
    assert resp.status_code == 422


@requires_gemini
@pytest.mark.asyncio
async def test_a2ui_custom_event_emitted(client):
    """A chart question should trigger an event containing A2UI payload."""
    resp = await client.post(
        "/api/agent/run",
        json=make_run_input("Show revenue by region as a bar chart"),
        headers={"Accept": "text/event-stream"},
    )
    events = parse_sse_events(resp.text)
    # Look for events containing A2UI payload (via tool results or CUSTOM events)
    has_a2ui = any("a2ui" in json.dumps(e).lower() for e in events)
    assert has_a2ui, "No A2UI-related event found in the stream"
