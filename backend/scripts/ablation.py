"""
Chunking ablation: sweep chunk sizes [256, 512, 1024] and measure Recall@5
using pure dense retrieval (no BM25, no reranker) to isolate chunking impact.

Usage (from backend/):
    python -m scripts.ablation
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

import chromadb

# Allow running as a script from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.rag.chunker import chunk_pdf
from app.rag.embeddings import embed_texts

_FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
_QUESTIONS_PATH = Path(__file__).parent.parent / "app" / "eval" / "questions.json"
_DOCS_PATH = Path(__file__).parent.parent.parent / "docs" / "ablation.md"
_CHUNK_SIZES = [256, 512, 1024]
_TOP_K = 5
_COLLECTION = "ablation"


def _override_chunk_size(size: int) -> None:
    settings.chunk_size = size
    settings.chunk_overlap = size // 8


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    try:
        client.delete_collection(_COLLECTION)
    except Exception:
        pass
    return client.create_collection(_COLLECTION, metadata={"hnsw:space": "cosine"})


def _recall_hit(results: list[dict], expected_sources: list[dict], k: int) -> bool:
    for chunk in results[:k]:
        meta = chunk["metadata"]
        for e in expected_sources:
            if meta.get("filename") == e["filename"] and meta.get("page") == e["page"]:
                return True
    return False


async def _run_chunk_size(size: int, questions: list[dict]) -> dict:
    _override_chunk_size(size)

    pdfs = [_FIXTURES / "A survey on sentiment analysis.pdf"]
    all_chunks = []
    for pdf in pdfs:
        all_chunks.extend(chunk_pdf(pdf))

    texts = [c.text for c in all_chunks]
    vectors = await embed_texts(texts, task="retrieval.passage")

    with tempfile.TemporaryDirectory() as tmp:
        client = chromadb.PersistentClient(path=tmp)
        col = _get_collection(client)
        col.upsert(
            ids=[f"{c.filename}__{c.chunk_index}" for c in all_chunks],
            embeddings=vectors,
            documents=texts,
            metadatas=[
                {"filename": c.filename, "page": c.page, "section": c.section}
                for c in all_chunks
            ],
        )

        hits = 0
        for q in questions:
            q_vec = await embed_texts([q["question"]], task="retrieval.query")
            count = col.count()
            results = col.query(
                query_embeddings=[q_vec[0]],
                n_results=min(_TOP_K, count),
                include=["metadatas", "distances"],
            )
            retrieved = [
                {"metadata": m, "score": 1.0 - d}
                for m, d in zip(results["metadatas"][0], results["distances"][0])
            ]
            if _recall_hit(retrieved, q["expected_sources"], _TOP_K):
                hits += 1

    avg_len = sum(len(c.text) for c in all_chunks) / len(all_chunks) if all_chunks else 0
    return {
        "chunk_size": size,
        "chunk_overlap": size // 8,
        "total_chunks": len(all_chunks),
        "avg_chunk_len": round(avg_len),
        "recall_at_5": hits / len(questions) if questions else 0.0,
    }


def _write_markdown(rows: list[dict]) -> str:
    lines = [
        "# Chunking Ablation Results",
        "",
        "Sweep over chunk sizes using pure dense retrieval (Jina v3) on a 30+ page research paper.",
        "Recall@5 measures whether the expected source page appears in the top 5 retrieved chunks.",
        "BM25 and Cohere reranker are excluded to isolate chunking impact.",
        "",
        "| Chunk size | Overlap | Total chunks | Avg chunk length | Recall@5 |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        recall_pct = f"{r['recall_at_5'] * 100:.0f}%"
        lines.append(
            f"| {r['chunk_size']} | {r['chunk_overlap']} "
            f"| {r['total_chunks']} | {r['avg_chunk_len']} chars | {recall_pct} |"
        )

    lines += [
        "",
        "## Trade-offs",
        "",
        "- **Small chunks (256):** More granular retrieval, lower risk of including irrelevant text, "
        "but key information may be split across chunk boundaries.",
        "- **Medium chunks (512):** Balanced — enough context for embeddings to capture meaning "
        "while keeping noise low. Default choice.",
        "- **Large chunks (1024):** Each chunk carries more context, which helps for multi-sentence "
        "answers, but embeddings become less discriminative and precision drops.",
    ]
    return "\n".join(lines) + "\n"


async def main() -> None:
    questions = json.loads(_QUESTIONS_PATH.read_text(encoding="utf-8"))
    print(f"Running ablation over chunk sizes {_CHUNK_SIZES} with {len(questions)} questions...\n")

    rows = []
    for size in _CHUNK_SIZES:
        print(f"  chunk_size={size} ...", end=" ", flush=True)
        result = await _run_chunk_size(size, questions)
        rows.append(result)
        print(f"Recall@5={result['recall_at_5'] * 100:.0f}%  chunks={result['total_chunks']}  avg_len={result['avg_chunk_len']}")

    md = _write_markdown(rows)
    _DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DOCS_PATH.write_text(md, encoding="utf-8")

    print(f"\nResults written to {_DOCS_PATH.relative_to(Path(__file__).parent.parent.parent)}\n")
    print(md)


if __name__ == "__main__":
    asyncio.run(main())
