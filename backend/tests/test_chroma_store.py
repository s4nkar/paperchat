import chromadb
import pytest

from app.rag.chunker import Chunk
from app.rag.chroma_store import add_chunks, delete_document, list_documents, query_chunks

_DIM = 8  # small vectors for tests


def _chunks(n: int, filename: str = "doc.pdf") -> list[Chunk]:
    return [
        Chunk(text=f"chunk {i}", filename=filename, page=1, section="Intro", chunk_index=i)
        for i in range(n)
    ]


def _vectors(n: int) -> list[list[float]]:
    # Unit vectors along first axis — all identical, so every query returns them all
    v = [1.0] + [0.0] * (_DIM - 1)
    return [v] * n


@pytest.fixture(autouse=True)
def ephemeral_client(monkeypatch, tmp_path):
    """Give each test its own isolated Chroma directory."""
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    monkeypatch.setattr("app.rag.chroma_store._client", lambda: client)
    yield client


def test_add_and_query():
    chunks = _chunks(5)
    add_chunks(chunks, _vectors(5))

    results = query_chunks([1.0] + [0.0] * (_DIM - 1), top_k=5)
    assert len(results) == 5
    assert all("text" in r and "metadata" in r and "score" in r for r in results)


def test_query_top_k_respected():
    add_chunks(_chunks(10), _vectors(10))
    results = query_chunks([1.0] + [0.0] * (_DIM - 1), top_k=3)
    assert len(results) == 3


def test_upsert_deduplicates():
    chunks = _chunks(3)
    add_chunks(chunks, _vectors(3))
    add_chunks(chunks, _vectors(3))  # same IDs — should upsert, not duplicate

    results = query_chunks([1.0] + [0.0] * (_DIM - 1), top_k=10)
    assert len(results) == 3


def test_delete_document():
    add_chunks(_chunks(4, "a.pdf"), _vectors(4))
    add_chunks(_chunks(3, "b.pdf"), _vectors(3))

    delete_document("a.pdf")
    remaining = list_documents()
    assert remaining == ["b.pdf"]


def test_list_documents():
    add_chunks(_chunks(2, "x.pdf"), _vectors(2))
    add_chunks(_chunks(2, "y.pdf"), _vectors(2))
    assert list_documents() == ["x.pdf", "y.pdf"]


def test_score_is_similarity_not_distance():
    add_chunks(_chunks(1), _vectors(1))
    results = query_chunks([1.0] + [0.0] * (_DIM - 1), top_k=1)
    # Identical unit vectors → cosine distance ≈ 0 → score ≈ 1.0
    assert results[0]["score"] > 0.99
