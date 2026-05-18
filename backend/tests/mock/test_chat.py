"""
Mocked tests for the chat streaming endpoint.

In a real system these would run against a live LLM and retrieval stack. Here we
mock retrieve, rerank, and stream_tokens to verify NDJSON event ordering and
input validation without API calls.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


_FAKE_CHUNKS = [
    {
        "text": "The payment policy requires 30 days notice.",
        "metadata": {"filename": "policy.pdf", "page": 1, "section": "Policy"},
        "score": 0.92,
    }
]


async def _fake_stream(*_args, **_kwargs):
    yield "30 days "
    yield "notice is required."


@pytest.fixture
def mocked_pipeline():
    with (
        patch("app.routes.chat.retrieve", new_callable=AsyncMock, return_value=_FAKE_CHUNKS),
        patch("app.routes.chat.rerank", new_callable=AsyncMock, return_value=_FAKE_CHUNKS),
        patch("app.routes.chat.stream_tokens", side_effect=_fake_stream),
    ):
        yield


@pytest.mark.usefixtures("mocked_pipeline")
def test_chat_streams_answer_and_sources(client: TestClient):
    response = client.post("/api/chat", json={"question": "What is the payment policy?"})
    assert response.status_code == 200

    events = [json.loads(line) for line in response.text.strip().splitlines()]
    types = [e["type"] for e in events]

    assert types[0] == "sources"
    assert "token" in types
    assert types[-1] == "done"

    sources = events[0]["data"]
    assert len(sources) == 1
    assert sources[0]["filename"] == "policy.pdf"
    assert sources[0]["page"] == 1
    assert sources[0]["score"] == pytest.approx(0.92)

    answer = "".join(e["data"] for e in events if e["type"] == "token")
    assert answer == "30 days notice is required."


def test_chat_empty_question(client: TestClient):
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422


def test_chat_missing_question(client: TestClient):
    response = client.post("/api/chat", json={})
    assert response.status_code == 422
