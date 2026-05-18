# Chunking Ablation Results

Sweep over chunk sizes using pure dense retrieval (Jina v3) on a 30+ page research paper.
Recall@5 measures whether the expected source page appears in the top 5 retrieved chunks.
BM25 and Cohere reranker are excluded to isolate chunking impact.

| Chunk size | Overlap | Total chunks | Avg chunk length | Recall@5 |
|---|---|---|---|---|
| 256 | 32 | 805 | 200 chars | 100% |
| 512 | 64 | 371 | 439 chars | 100% |
| 1024 | 128 | 200 | 868 chars | 100% |

## Trade-offs

- **Small chunks (256):** More granular retrieval, lower risk of including irrelevant text, but key information may be split across chunk boundaries.
- **Medium chunks (512):** Balanced — enough context for embeddings to capture meaning while keeping noise low. Default choice.
- **Large chunks (1024):** Each chunk carries more context, which helps for multi-sentence answers, but embeddings become less discriminative and precision drops.
