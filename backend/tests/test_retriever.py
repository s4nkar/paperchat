from unittest.mock import AsyncMock, patch

import pytest

from app.rag.retriever import _rrf, retrieve

_CHUNK_A = {"text": "council tax proof of address", "metadata": {"filename": "a.pdf", "page": 1, "section": ""}, "score": 0.9}
_CHUNK_B = {"text": "utility bill proof of address", "metadata": {"filename": "a.pdf", "page": 1, "section": ""}, "score": 0.7}
_CHUNK_C = {"text": "passport identity document",   "metadata": {"filename": "b.pdf", "page": 2, "section": ""}, "score": 0.5}


# --- _rrf unit tests ---

def test_rrf_chunk_in_both_lists_ranks_first():
    result = _rrf([[_CHUNK_A, _CHUNK_B], [_CHUNK_A, _CHUNK_C]])
    assert result[0]["text"] == _CHUNK_A["text"]


def test_rrf_deduplicates_same_text():
    result = _rrf([[_CHUNK_A], [_CHUNK_A]])
    assert len(result) == 1


def test_rrf_includes_chunks_from_single_list():
    result = _rrf([[_CHUNK_A, _CHUNK_B], [_CHUNK_C]])
    texts = [r["text"] for r in result]
    assert _CHUNK_B["text"] in texts
    assert _CHUNK_C["text"] in texts


def test_rrf_empty_lists():
    assert _rrf([[], []]) == []


def test_rrf_one_empty_list():
    result = _rrf([[_CHUNK_A, _CHUNK_B], []])
    assert len(result) == 2


# --- retrieve integration tests ---

@pytest.mark.asyncio
async def test_retrieve_calls_both_stores():
    fake_vector = [0.1] * 1024

    with (
        patch("app.rag.retriever.embed_texts", new_callable=AsyncMock, return_value=[fake_vector]),
        patch("app.rag.retriever.query_chunks", return_value=[_CHUNK_A]) as mock_dense,
        patch("app.rag.retriever.bm25_store.query", return_value=[_CHUNK_B]) as mock_bm25,
    ):
        results = await retrieve("proof of address")

    mock_dense.assert_called_once_with(fake_vector, 10)
    mock_bm25.assert_called_once_with("proof of address", 10)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_retrieve_returns_fused_and_deduplicated():
    fake_vector = [0.1] * 1024

    with (
        patch("app.rag.retriever.embed_texts", new_callable=AsyncMock, return_value=[fake_vector]),
        patch("app.rag.retriever.query_chunks", return_value=[_CHUNK_A, _CHUNK_B]),
        patch("app.rag.retriever.bm25_store.query", return_value=[_CHUNK_A, _CHUNK_C]),
    ):
        results = await retrieve("address")

    texts = [r["text"] for r in results]
    assert texts.count(_CHUNK_A["text"]) == 1
    assert results[0]["text"] == _CHUNK_A["text"]
