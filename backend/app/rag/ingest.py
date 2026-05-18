import hashlib
from pathlib import Path

from app.rag.chunker import chunk_pdf
from app.rag.chroma_store import add_chunks, find_by_hash
from app.rag.embeddings import embed_texts


async def ingest_pdf(path: Path) -> int:
    """Chunk, embed, and store a PDF. Returns the number of chunks indexed.

    Skips embedding if an identical file (same SHA-256) is already in the store.
    """
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    existing = find_by_hash(content_hash)
    if existing > 0:
        return existing

    chunks = chunk_pdf(path)
    if not chunks:
        return 0

    vectors = await embed_texts([c.text for c in chunks])
    add_chunks(chunks, vectors, content_hash=content_hash)
    return len(chunks)
