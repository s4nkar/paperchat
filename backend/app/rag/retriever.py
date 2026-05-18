from app.config import settings
from app.rag.chroma_store import query_chunks
from app.rag.embeddings import embed_texts


async def retrieve(question: str) -> list[dict]:
    """Embed the question and return the top dense-retrieval chunks."""
    vectors = await embed_texts([question], task="retrieval.query")
    return query_chunks(vectors[0], top_k=settings.top_k_dense)
