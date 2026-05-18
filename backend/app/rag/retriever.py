import asyncio

from app.config import settings
from app.rag import bm25_store
from app.rag.chroma_store import query_chunks
from app.rag.embeddings import embed_texts

_RRF_K = 60  # standard constant — dampens the impact of rank differences


def _rrf(ranked_lists: list[list[dict]]) -> list[dict]:
    """Reciprocal Rank Fusion: score each chunk by 1/(k + rank) summed across lists."""
    scores: dict[str, float] = {}
    chunks: dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked, 1):
            key = chunk["text"]
            scores[key] = scores.get(key, 0.0) + 1.0 / (_RRF_K + rank)
            if key not in chunks:
                chunks[key] = chunk

    return sorted(chunks.values(), key=lambda c: scores[c["text"]], reverse=True)


async def retrieve(question: str) -> list[dict]:
    """Hybrid retrieval: dense + BM25 → RRF fusion.

    Sync store calls run in a thread-pool executor so they don't block the event loop.
    """
    vectors = await embed_texts([question], task="retrieval.query")
    loop = asyncio.get_running_loop()

    dense_results, bm25_results = await asyncio.gather(
        loop.run_in_executor(None, query_chunks, vectors[0], settings.top_k_dense),
        loop.run_in_executor(None, bm25_store.query, question, settings.top_k_bm25),
    )

    return _rrf([dense_results, bm25_results])
