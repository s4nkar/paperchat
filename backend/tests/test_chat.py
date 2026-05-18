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


@pytest.fixture
def mocked_pipeline():
    with (
        patch("app.routes.chat.retrieve", new_callable=AsyncMock, return_value=_FAKE_CHUNKS),
        patch("app.routes.chat.generate", new_callable=AsyncMock, return_value="30 days notice is required."),
    ):
        yield


@pytest.mark.usefixtures("mocked_pipeline")
def test_chat_returns_answer_and_sources(client: TestClient):
    response = client.post("/api/chat", json={"question": "What is the payment policy?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "30 days notice is required."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["filename"] == "policy.pdf"
    assert data["sources"][0]["page"] == 1
    assert data["sources"][0]["score"] == pytest.approx(0.92)


def test_chat_empty_question(client: TestClient):
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422


def test_chat_missing_question(client: TestClient):
    response = client.post("/api/chat", json={})
    assert response.status_code == 422

