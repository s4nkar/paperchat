"""
Mocked tests for the Cohere reranker client.

In a real system these would hit a live Cohere endpoint. Here we mock httpx to
verify score remapping and top_k truncation without incurring API calls.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.rag.reranker import rerank

_CHUNKS = [
    {"text": "council tax proof of address", "metadata": {"filename": "a.pdf", "page": 1, "section": ""}, "score": 0.9},
    {"text": "utility bill accepted as proof", "metadata": {"filename": "a.pdf", "page": 2, "section": ""}, "score": 0.7},
    {"text": "passport is an identity document", "metadata": {"filename": "b.pdf", "page": 1, "section": ""}, "score": 0.5},
]


def _fake_response(payload: dict):
    class _Resp:
        def json(self):
            return payload
        def raise_for_status(self):
            pass
    return _Resp()


@pytest.mark.asyncio
async def test_rerank_returns_top_k(monkeypatch):
    monkeypatch.setattr("app.config.settings.top_k_rerank", 2)
    monkeypatch.setattr("app.config.settings.cohere_api_key", "test-key")

    cohere_resp = {"results": [{"index": 0, "relevance_score": 0.95}, {"index": 1, "relevance_score": 0.82}]}
    mock_post = AsyncMock(return_value=_fake_response(cohere_resp))

    with patch("app.rag.reranker.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=type("C", (), {"post": mock_post})())
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        results = await rerank("proof of address", _CHUNKS)

    assert len(results) == 2
    assert results[0]["text"] == _CHUNKS[0]["text"]
    assert results[0]["score"] == pytest.approx(0.95)
    assert results[1]["text"] == _CHUNKS[1]["text"]


@pytest.mark.asyncio
async def test_rerank_empty_chunks():
    result = await rerank("anything", [])
    assert result == []


@pytest.mark.asyncio
async def test_rerank_scores_overwritten(monkeypatch):
    monkeypatch.setattr("app.config.settings.top_k_rerank", 1)
    monkeypatch.setattr("app.config.settings.cohere_api_key", "test-key")

    cohere_resp = {"results": [{"index": 2, "relevance_score": 0.99}]}
    mock_post = AsyncMock(return_value=_fake_response(cohere_resp))

    with patch("app.rag.reranker.httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=type("C", (), {"post": mock_post})())
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        results = await rerank("passport document", _CHUNKS)

    assert results[0]["text"] == _CHUNKS[2]["text"]
    assert results[0]["score"] == pytest.approx(0.99)
