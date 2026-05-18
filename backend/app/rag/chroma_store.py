import chromadb

from app.config import settings
from app.rag.chunker import Chunk

_COLLECTION_NAME = "chunks"


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )


def add_chunks(chunks: list[Chunk], vectors: list[list[float]], content_hash: str = "") -> None:
    col = _get_collection(_client())
    col.upsert(
        ids=[f"{c.filename}__{c.chunk_index}" for c in chunks],
        embeddings=vectors,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "filename": c.filename,
                "page": c.page,
                "section": c.section,
                "chunk_index": c.chunk_index,
                "content_hash": content_hash,
            }
            for c in chunks
        ],
    )


def find_by_hash(content_hash: str) -> int:
    """Return the number of chunks already stored for this content hash, or 0 if none."""
    try:
        col = _get_collection(_client())
        result = col.get(where={"content_hash": content_hash}, include=[])
        return len(result["ids"])
    except Exception:
        return 0


def query_chunks(vector: list[float], top_k: int) -> list[dict]:
    col = _get_collection(_client())
    results = col.query(
        query_embeddings=[vector],
        n_results=min(top_k, col.count()),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {
            "text": doc,
            "metadata": meta,
            "score": 1.0 - dist,  # cosine distance → cosine similarity
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def delete_document(filename: str) -> None:
    col = _get_collection(_client())
    col.delete(where={"filename": filename})


def list_documents() -> list[dict]:
    """Return one entry per document with filename, page_count, and chunk_count."""
    col = _get_collection(_client())
    result = col.get(include=["metadatas"])
    docs: dict[str, dict] = {}
    for m in result["metadatas"]:
        name = m["filename"]
        if name not in docs:
            docs[name] = {"filename": name, "page_count": 0, "chunk_count": 0}
        docs[name]["chunk_count"] += 1
        docs[name]["page_count"] = max(docs[name]["page_count"], m.get("page", 0))
    return sorted(docs.values(), key=lambda d: d["filename"])
