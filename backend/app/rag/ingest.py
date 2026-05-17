from pathlib import Path

from app.rag.chunker import chunk_pdf
from app.rag.chroma_store import add_chunks
from app.rag.embeddings import embed_texts


async def ingest_pdf(path: Path) -> int:
    """Chunk, embed, and store a PDF. Returns the number of chunks indexed."""
    chunks = chunk_pdf(path)
    if not chunks:
        return 0

    vectors = await embed_texts([c.text for c in chunks])
    add_chunks(chunks, vectors)
    return len(chunks)
