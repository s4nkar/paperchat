import asyncio
from typing import Literal

import httpx

from app.config import settings

_JINA_URL = "https://api.jina.ai/v1/embeddings"
_BATCH_SIZE = 100
_MAX_RETRIES = 3
_RETRY_BASE = 2.0  # seconds; doubles per attempt (2s, 4s)


async def _embed_batch(
    client: httpx.AsyncClient,
    texts: list[str],
    task: str,
) -> list[list[float]]:
    payload = {
        "model": settings.embedding_model,
        "task": task,
        "input": texts,
        "normalized": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.jina_api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(_MAX_RETRIES):
        response = await client.post(_JINA_URL, json=payload, headers=headers, timeout=60.0)

        if response.status_code != 429:
            response.raise_for_status()
            items = sorted(response.json()["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in items]

        if attempt < _MAX_RETRIES - 1:
            await asyncio.sleep(_RETRY_BASE**attempt)
        else:
            response.raise_for_status()

    raise RuntimeError("unreachable")


async def embed_texts(
    texts: list[str],
    *,
    task: Literal["retrieval.passage", "retrieval.query"] = "retrieval.passage",
) -> list[list[float]]:
    """Embed a list of texts via Jina v3. Use task='retrieval.query' for user questions."""
    if not texts:
        return []

    async with httpx.AsyncClient() as client:
        results: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            vectors = await _embed_batch(client, batch, task)
            results.extend(vectors)

    return results
