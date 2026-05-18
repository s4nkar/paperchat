import pytest

from app.rag.bm25_store import add_chunks, query, remove_document
from app.rag.chunker import Chunk


def _chunks(texts: list[str], filename: str = "doc.pdf") -> list[Chunk]:
    return [
        Chunk(text=t, filename=filename, page=i + 1, section="", chunk_index=i)
        for i, t in enumerate(texts)
    ]


@pytest.fixture(autouse=True)
def patch_index_path(monkeypatch, tmp_path):
    monkeypatch.setattr("app.rag.bm25_store._index_path", lambda: tmp_path / "bm25.pkl")


def test_query_returns_matching_chunk():
    add_chunks(_chunks(["council tax bill proof of address", "unrelated text about dogs"]))
    results = query("council tax", top_k=5)
    assert results[0]["text"] == "council tax bill proof of address"


def test_query_empty_index_returns_empty():
    results = query("anything", top_k=5)
    assert results == []


def test_query_top_k_respected():
    add_chunks(_chunks([f"document about topic {i}" for i in range(10)]))
    results = query("document topic", top_k=3)
    assert len(results) <= 3


def test_add_chunks_replaces_existing_document():
    add_chunks(_chunks(["old content"], filename="a.pdf"))
    add_chunks(_chunks(["new content"], filename="a.pdf"))
    results = query("content", top_k=10)
    texts = [r["text"] for r in results]
    assert "new content" in texts
    assert "old content" not in texts


def test_remove_document():
    add_chunks(_chunks(["tax bill address"], filename="a.pdf"))
    add_chunks(_chunks(["payment policy uniform"], filename="b.pdf"))
    remove_document("a.pdf")
    results = query("tax bill", top_k=5)
    assert all(r["metadata"]["filename"] != "a.pdf" for r in results)


def test_result_has_required_keys():
    add_chunks(_chunks(["some text"], filename="test.pdf"))
    results = query("text", top_k=1)
    assert len(results) == 1
    assert {"text", "metadata", "score"} <= results[0].keys()
    assert {"filename", "page", "section"} <= results[0]["metadata"].keys()
