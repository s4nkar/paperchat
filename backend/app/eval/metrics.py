"""Retrieval evaluation metrics: Recall@K (retriever), MRR@K and Precision@K (reranker)."""

import json
from pathlib import Path

from app.rag.reranker import rerank
from app.rag.retriever import retrieve

_QUESTIONS_PATH = Path(__file__).parent / "questions.json"


def _is_match(chunk: dict, expected_sources: list[dict]) -> bool:
    meta = chunk["metadata"]
    return any(
        meta.get("filename") == e["filename"] and meta.get("page") == e["page"]
        for e in expected_sources
    )


def _recall(retrieved: list[dict], expected_sources: list[dict], k: int) -> bool:
    """True if any expected source appears in the top-k chunks."""
    return any(_is_match(c, expected_sources) for c in retrieved[:k])


def _reciprocal_rank(ranked: list[dict], expected_sources: list[dict], k: int) -> float:
    """1/rank of the first relevant chunk within top-k, or 0 if not found."""
    for rank, chunk in enumerate(ranked[:k], 1):
        if _is_match(chunk, expected_sources):
            return 1.0 / rank
    return 0.0


def _precision(ranked: list[dict], expected_sources: list[dict], k: int) -> float:
    """Fraction of top-k chunks that are relevant."""
    top_k = ranked[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for c in top_k if _is_match(c, expected_sources))
    return hits / len(top_k)


async def run_eval(retrieval_k: int = 5, rerank_k: int = 3) -> dict:
    """Run all metrics over the golden question set.

    Returns per-question results plus aggregate Recall@K, MRR@K, and Precision@K.
    """
    questions = json.loads(_QUESTIONS_PATH.read_text(encoding="utf-8"))
    results = []

    for q in questions:
        retrieved = await retrieve(q["question"])
        reranked = await rerank(q["question"], retrieved)

        expected = q["expected_sources"]
        rr = _reciprocal_rank(reranked, expected, rerank_k)
        results.append({
            "id": q["id"],
            "question": q["question"],
            "recall": _recall(retrieved, expected, retrieval_k),
            "reciprocal_rank": rr,
            "precision": _precision(reranked, expected, rerank_k),
        })

    n = len(results)
    return {
        "retrieval_k": retrieval_k,
        "rerank_k": rerank_k,
        "recall_at_k": sum(r["recall"] for r in results) / n if n else 0.0,
        "mrr": sum(r["reciprocal_rank"] for r in results) / n if n else 0.0,
        "precision_at_k": sum(r["precision"] for r in results) / n if n else 0.0,
        "results": results,
    }
