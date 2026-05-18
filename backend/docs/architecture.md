# Architecture

## System Diagram

```
Browser
  │
  ├─ POST /api/upload ──────────────────────────────────────────────────────┐
  │                                                                          │
  │                                                                 FastAPI (backend)
  │                                                                          │
  │                                                              ┌───────────▼───────────┐
  │                                                              │  upload route          │
  │                                                              │  • validate magic bytes│
  │                                                              │  • safe filename       │
  │                                                              │  • ingest_pdf()        │
  │                                                              └───────────┬───────────┘
  │                                                                          │
  │                                                            ┌─────────────▼─────────────┐
  │                                                            │       ingest pipeline      │
  │                                                            │  SHA-256 → skip if cached  │
  │                                                            │  chunk_pdf() per page      │
  │                                                            │  embed_texts() Jina v3     │
  │                                                            │  Chroma upsert             │
  │                                                            │  BM25 index update         │
  │                                                            └────────────────────────────┘
  │
  ├─ POST /api/chat ────────────────────────────────────────────────────────┐
  │                                                                          │
  │                                                              ┌───────────▼───────────┐
  │                                                              │  chat route            │
  │                                                              │  question cache check  │
  │                                                              └───────────┬───────────┘
  │                                                                          │
  │                                              ┌───────────────────────────▼──────────────────────────┐
  │                                              │                 retrieval pipeline                    │
  │                                              │                                                       │
  │                                              │   embed query (Jina v3, task=retrieval.query)         │
  │                                              │        │                    │                         │
  │                                              │   Chroma top 10       BM25 top 10                    │
  │                                              │        │                    │                         │
  │                                              │        └────────┬───────────┘                         │
  │                                              │            RRF fusion                                 │
  │                                              │            Cohere rerank → top 3                      │
  │                                              │            score filter ≥ 0.2                         │
  │                                              └───────────────────────────┬──────────────────────────┘
  │                                                                          │
  │                                                              ┌───────────▼───────────┐
  │                                                              │  Groq LLM              │
  │                                                              │  Llama 3.3 70B         │
  │                                                              │  streamed SSE → NDJSON │
  │                                                              └───────────┬───────────┘
  │                                                                          │
  │◄─────────────────────── NDJSON stream ───────────────────────────────────┘
  │  {type:"sources"} → {type:"token"}* → {type:"usage"} → {type:"done"}
  │
  ├─ GET /api/documents
  ├─ DELETE /api/documents/{filename}
  └─ GET /api/eval
```

## Component Responsibilities

### Backend

| Module | Responsibility |
|---|---|
| `routes/upload.py` | Validate files (magic bytes, MIME type, path traversal), save to disk, trigger ingestion |
| `routes/chat.py` | Check question cache, run retrieval pipeline, stream NDJSON response |
| `routes/documents.py` | List documents from Chroma metadata, delete from Chroma and BM25 |
| `routes/eval.py` | Run golden question set, return Recall@5 / MRR@3 / Precision@3 |
| `rag/chunker.py` | Per-page recursive separator splitting with section heading detection |
| `rag/embeddings.py` | Jina v3 HTTP client, batched (100), retry on 429 |
| `rag/chroma_store.py` | Chroma CRUD: add, query (cosine), delete by filename, list with metadata |
| `rag/bm25_store.py` | rank-bm25 index, pickle-persisted, rebuilt on add/delete |
| `rag/retriever.py` | Parallel dense + BM25 retrieval via asyncio, RRF fusion |
| `rag/reranker.py` | Cohere rerank-v3.5 HTTP client, returns top_k_rerank chunks with new scores |
| `rag/llm.py` | Groq streaming client, parses SSE, yields tokens + total_tokens |
| `rag/ingest.py` | Orchestrates chunk → embed → store, SHA-256 content deduplication |
| `rag/question_cache.py` | SHA-256 keyed JSON file cache for full question→answer replay |
| `eval/metrics.py` | _recall, _reciprocal_rank, _precision helpers; run_eval() orchestrator |

### Frontend

| Component | Responsibility |
|---|---|
| `ChatWindow.tsx` | Message state, AbortController, calls streamChat(), auto-scroll |
| `MessageBubble.tsx` | Renders user/assistant bubbles, markdown (react-markdown), error banner, token count |
| `SourceCard.tsx` | Displays filename, page, relevance score, 2-line text preview per source |
| `DocumentList.tsx` | TanStack Query `useQuery(["documents"])`, numbered cards, delete with invalidation |
| `PdfUploader.tsx` | File input, `useMutation`, captures FileList before reset, compact result |
| `EvalPanel.tsx` | Lazy `useQuery(["eval"])`, aggregate metric cards, per-question pass/fail table |
| `lib/stream.ts` | `streamChat()` — fetch POST, line-buffered NDJSON reader, typed callbacks |
| `lib/api.ts` | REST helpers: fetchDocuments, deleteDocument, uploadPdfs |
| `types.ts` | All shared TypeScript types: Chunk, ChatMessage, StreamEvent, StreamCallbacks |

## Data Flow

### Upload

```
File bytes
  → magic byte check (%PDF header)
  → SHA-256 hash → find_by_hash() → skip if already in Chroma
  → chunk_pdf()  → list[Chunk]  (text, filename, page, section, chunk_index)
  → embed_texts() → list[vector]  (1024-dim, normalised)
  → chroma add_chunks()  (upsert by filename__chunk_index)
  → bm25_store add_chunks()  (rebuild index, repickle)
```

### Query

```
Question string
  → question_cache.get()  → cache hit: replay sources + answer, 0 tokens
  → embed_texts([question], task="retrieval.query")  → query vector
  → asyncio.gather(
        run_in_executor(query_chunks, vector, top_k=10),   # Chroma
        run_in_executor(bm25_store.query, question, top_k=10)  # BM25
    )
  → _rrf([dense, bm25])  → fused list, scored by 1/(60+rank), deduped by text
  → rerank(question, fused)  → Cohere cross-encoder, top 3
  → score filter ≥ 0.2  → drop off-topic chunks
  → stream_tokens(question, chunks)  → Groq SSE → yield token | total_tokens
  → NDJSON events: sources → token* → usage → done
  → question_cache.set()  → persist for replay
```
