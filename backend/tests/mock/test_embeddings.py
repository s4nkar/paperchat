"""
Mocked tests for the Jina v3 embedding client.

In a real system these would be integration tests hitting a live or containerised
Jina endpoint. Here we mock httpx.AsyncClient to avoid network calls and API costs
while still verifying batching logic, retry behaviour, and task parameter handling.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.embeddings import _BATCH_SIZE, embed_texts


def _mock_response(texts: list[str], status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {
        "data": [{"index": i, "embedding": [0.1] * 1024} for i in range(len(texts))]
    }
    resp.raise_for_status = MagicMock(
        side_effect=None if status == 200 else Exception(f"HTTP {status}")
    )
    return resp


def _patch_client(post_fn):
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = post_fn
    return patch("httpx.AsyncClient", return_value=mock_client)


@pytest.mark.asyncio
async def test_embed_returns_correct_shape():
    texts = ["hello world"] * 10

    async def fake_post(url, **kwargs):
        return _mock_response(kwargs["json"]["input"])

    with _patch_client(fake_post):
        vectors = await embed_texts(texts)

    assert len(vectors) == 10
    assert len(vectors[0]) == 1024


@pytest.mark.asyncio
async def test_embed_batches_large_input():
    n = _BATCH_SIZE + 15
    texts = ["chunk"] * n
    call_batches: list[int] = []

    async def fake_post(url, **kwargs):
        batch = kwargs["json"]["input"]
        call_batches.append(len(batch))
        return _mock_response(batch)

    with _patch_client(fake_post):
        vectors = await embed_texts(texts)

    assert len(vectors) == n
    assert len(call_batches) == 2
    assert call_batches[0] == _BATCH_SIZE
    assert call_batches[1] == 15


@pytest.mark.asyncio
async def test_embed_retries_on_429():
    texts = ["test"]
    attempts: list[int] = []

    async def fake_post(url, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            return _mock_response([], status=429)
        return _mock_response(texts)

    with _patch_client(fake_post), patch("asyncio.sleep", new_callable=AsyncMock):
        vectors = await embed_texts(texts)

    assert len(vectors) == 1
    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_embed_empty_input():
    vectors = await embed_texts([])
    assert vectors == []


@pytest.mark.asyncio
async def test_embed_uses_query_task():
    sent_task: list[str] = []

    async def fake_post(url, **kwargs):
        sent_task.append(kwargs["json"]["task"])
        return _mock_response(kwargs["json"]["input"])

    with _patch_client(fake_post):
        await embed_texts(["what is rag?"], task="retrieval.query")

    assert sent_task[0] == "retrieval.query"
