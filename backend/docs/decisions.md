# Architecture Decision Records

## ADR-1: Hosted models over self-hosted

We use Jina v3 (embeddings), Cohere (reranker), and Groq (LLM) as external API services rather than running models locally. CPU inference for a 70B parameter model is impractical for a demo. Hosted APIs give access to production-grade models with no infrastructure overhead, and the entire pipeline stays reproducible from a clean clone with only a `.env` file.

## ADR-2: Hybrid retrieval over dense-only

Dense vector search alone misses exact keyword matches — a user querying "BM25" or a proper noun will get semantically similar but lexically wrong results. BM25 alone misses paraphrased or conceptually related queries. Combining both with Reciprocal Rank Fusion consistently outperforms either approach on mixed query types, and the cost is negligible: BM25 runs in-process from a pickle file with no extra API call.

## ADR-3: NDJSON over SSE for streaming

Server-Sent Events require GET requests or a unidirectional protocol; our chat endpoint is a POST (the question is in the body). NDJSON over a streaming HTTP POST response is simpler: one connection, no EventSource polyfill, no reconnection logic, and the browser's `ReadableStream` API handles it natively. Error events are just another JSON line rather than a special SSE field, which keeps the frontend parser uniform.

## ADR-4: Chroma over FAISS

Chroma is schema-aware — it stores metadata (filename, page, section, content hash) alongside vectors and supports filtered queries. FAISS is a pure vector index with no metadata layer, requiring a separate store and join at query time. Chroma's persistent client also handles serialisation automatically, whereas FAISS requires manual index save/load. For a single-node demo with moderate scale, Chroma's ergonomics outweigh FAISS's raw throughput advantage.

## ADR-5: React over Streamlit

Streamlit rerenders the entire page on every state change, which causes visible flicker during token streaming and makes fine-grained UI control (AbortController, per-token state updates, animated source cards appearing after the answer) impractical. React's component model allows surgical state updates — only the in-progress message bubble re-renders as tokens arrive.

## ADR-6: No task queue (Celery/RQ) for PDF ingestion

Celery and RQ exist to offload work from the request cycle when jobs are long, retryable, or need distribution across workers. PDF ingestion here is synchronous and user-initiated — the frontend polls a progress endpoint and the user waits for the result. Adding a broker (Redis) and worker process would triple the `docker-compose.yml` surface area with no benefit at single-user demo scale. If this were a multi-tenant service with concurrent uploads, a task queue would be the right call.

## ADR-7: Cosine similarity over dot-product or Euclidean distance

Jina v3 embeddings are L2-normalised, which makes cosine similarity and dot-product numerically identical. Chroma defaults to cosine, which is the conventional choice for semantic search — magnitude differences between short and long chunks don't inflate similarity scores. Euclidean distance penalises long vectors regardless of direction, making cross-chunk comparisons unreliable when chunk sizes vary.

## ADR-8: Async only at I/O boundaries, not throughout

Only the Jina embedding call and Cohere rerank call are truly async — they hit external HTTPS endpoints and benefit from non-blocking I/O. BM25 scoring and chunk slicing are CPU-bound in-process operations; wrapping them in `asyncio` coroutines adds overhead without throughput gain. `run_in_executor` is used for BM25 so it doesn't block the event loop, which is the correct boundary: async for network, executor for CPU.

## ADR-9: No OCR

The brief specifies text-extractable PDFs. PyMuPDF's `get_text()` covers all standard PDF text layers with zero additional dependencies. OCR (Tesseract, EasyOCR) requires image rendering per page, GPU or heavy CPU time, and introduces accuracy variance. Adding it for scanned documents would break the "no GPU" constraint and is explicitly out of scope.

## ADR-10: Single-container Docker architecture for Hugging Face Spaces

Hugging Face Spaces (Docker SDK) provisions exactly one container and exposes exactly one port (7860). Multi-container setups (separate frontend, backend, and broker services) are not possible without an external orchestrator. The Dockerfile therefore uses a multi-stage build: stage one compiles the Vite frontend into static assets, stage two installs the Python backend and copies those assets in. At runtime, FastAPI serves the built frontend from `/app/frontend/dist` via `StaticFiles` and handles all API routes under `/api/*` — one process, one port, zero sidecar dependencies. This also eliminates CORS configuration entirely, since the frontend and API share the same origin. The trade-off is that a code change to either layer requires rebuilding the full image, which is acceptable for a demo with infrequent deploys.
