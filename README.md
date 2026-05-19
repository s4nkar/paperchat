---
title: PaperChat
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# PaperChat

Upload PDFs, ask questions, get cited answers. Built with FastAPI, React, and a hybrid retrieval pipeline.

## Architecture

```
Upload PDF
  └─ PyMuPDF extracts text
  └─ Content-aware chunker  (recursive separator splitting, section heading detection)
  └─ Jina v3 embeddings     (1024-dim, normalised, task="retrieval.passage")
  └─ Chroma vector store    (cosine similarity, content-hash deduplication)
  └─ BM25 index             (rank-bm25, pickle-persisted)
  └─ PDF ingestion cache    (SHA-256 of file bytes)

Ask a question
  └─ Jina v3 query embed    (task="retrieval.query")
  └─ Dense retrieval        top 10 from Chroma
  └─ BM25 retrieval         top 10 from rank-bm25
  └─ RRF fusion             score = Σ 1/(60 + rank), dedup by text
  └─ Cohere rerank          cross-encoder, top 3 by relevance score ≥ 0.2
  └─ Groq LLM               Llama 3.3 70B, streamed NDJSON to browser
  └─ Question cache         SHA-256 keyed JSON, replays answer at 0 tokens
```

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Frontend | Vite + React + TypeScript + Tailwind + shadcn/ui |
| Vector store | Chroma (persistent, cosine similarity) |
| Lexical search | rank-bm25 (pickle-persisted) |
| Embeddings | Jina v3 (`jina-embeddings-v3`, 1024-dim) |
| Reranker | Cohere (`rerank-v3.5`) |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| PDF parsing | PyMuPDF |
| Streaming | HTTP chunked transfer, NDJSON |

## Chunking Strategy

The chunker splits per-page using recursive separator splitting, paragraph breaks first, then line breaks, then sentences, then words. This keeps semantic units intact and avoids mid-sentence cuts that degrade embedding quality.

Each chunk carries:
- `filename` and `page` (1-based) for source citations
- `section` — the nearest heading above the chunk, detected by heuristic (`_is_heading`)
- `chunk_index` — sequential ID for Chroma upsert deduplication

Default settings: `chunk_size=512`, `chunk_overlap=64`.

### Ablation Results

Sweep over chunk sizes using pure dense retrieval (Jina v3, no BM25/reranker) on a 30+ page research paper, Recall@5 on 5 golden questions:

| Chunk size | Overlap | Total chunks | Avg chunk length | Recall@5 |
|---|---|---|---|---|
| 256 | 32 | 805 | 200 chars | 100% |
| 512 | 64 | 371 | 439 chars | 100% |
| 1024 | 128 | 200 | 868 chars | 100% |

All sizes achieve 100% Recall@5 on this corpus, Jina v3's strong semantic representations are robust across chunk sizes. The choice of 512 is justified by the count/length trade-off: 256 produces 2× more chunks (higher index cost, noisier reranker input); 1024 produces fewer but broader chunks where embeddings become less discriminative on subtly different passages.

## Retrieval Pipeline

**Hybrid retrieval** combines dense vector search (captures semantic similarity) with BM25 (captures exact keyword matches). The two result lists are fused with **Reciprocal Rank Fusion** (k=60) which rewards chunks that rank highly in both lists.

**Cohere reranker** then applies a cross-encoder to the fused candidates. Unlike bi-encoder embeddings, the cross-encoder sees the question and chunk together, giving a more accurate relevance score. Chunks below 0.2 relevance are dropped before the LLM sees them.

## Evaluation

Static retrieval metrics on 5 golden questions:

- **Recall@5** — does the expected source page appear in the top 5 retriever candidates?
- **MRR@3** — mean reciprocal rank of the correct chunk in the reranker's top 3
- **Precision@3** — fraction of the 3 chunks sent to the LLM that are actually relevant

Run via the Eval panel in the UI or directly:

```bash
GET /api/eval
```

## Caching

Two independent caching layers:

| Layer | Key | Effect |
|---|---|---|
| PDF ingestion | SHA-256 of file bytes | Skip re-embedding if content already in Chroma |
| Question cache | SHA-256 of normalised question | Skip full pipeline, replay at 0 tokens |

## Deployment

The production image is a single container designed for **Hugging Face Spaces (Docker SDK)**, which exposes exactly one port (7860). A multi-stage Dockerfile compiles the Vite frontend into static assets in the build stage, then copies them into the Python image. FastAPI serves those assets via `StaticFiles` at `/` and handles all API routes under `/api/*`. One process, one port, no sidecar services — and no CORS configuration needed because the frontend and API share the same origin.

```bash
# local dev (hot reload, port 5173)
docker compose up

# production-style single container (port 7860)
docker compose -f docker-compose.prod.yml up
```

## Quick Start

```bash
cp .env.example .env    # fill in API keys
docker compose up       # http://localhost:5173
```

Required env vars: `JINA_API_KEY`, `GROQ_API_KEY`, `COHERE_API_KEY`

## Running Tests

```bash
# Real logic tests only (no API keys needed)
docker compose exec backend python -m pytest tests/

# Including mock tests
docker compose exec backend python -m pytest tests/ tests/mock/

# Full eval against live APIs (requires real keys in .env)
docker compose exec backend python -m pytest tests/test_eval_live.py
```

Tests are split into two layers:

| Layer | Path | What it tests |
|---|---|---|
| Real | `tests/` | Chunking, BM25, Chroma, RRF algorithm, metric formulas, upload validation |
| Mock | `tests/mock/` | Embeddings client, reranker client, chat endpoint, ingest orchestrator |

The mock layer exists to document the integration contract. In a production system these would hit real or containerised services.

## Running Chunking Ablation

```bash
docker compose exec backend python -m scripts.ablation
```

Results are written to `backend/docs/ablation.md`.

## Project Structure

```
backend/
  app/
    rag/          chunker, embeddings, chroma_store, bm25_store,
                  retriever, reranker, llm, ingest, question_cache
    routes/       upload, documents, chat, eval
    eval/         questions.json, metrics.py
  scripts/        ablation.py
  docs/           ablation.md  (generated by ablation script)
  tests/
    fixtures/     test PDFs for eval and ablation
frontend/
  src/
    components/   ChatWindow, MessageBubble, SourceCard,
                  DocumentList, PdfUploader, EvalPanel
    lib/          api.ts, stream.ts
    types.ts
```
