"""
Mocked tests for the PDF ingest orchestrator.

In a real system embed_texts and add_chunks would call live Jina and Chroma.
Here we mock both to verify that the orchestrator correctly pairs chunk count
with vector count and handles blank PDFs without crashing.
"""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pymupdf
import pytest

from app.rag.ingest import ingest_pdf


@pytest.mark.asyncio
async def test_ingest_returns_chunk_count(sample_pdf: Path):
    with (
        patch("app.rag.ingest.embed_texts", new_callable=AsyncMock) as mock_embed,
        patch("app.rag.ingest.add_chunks") as mock_add,
    ):
        mock_embed.side_effect = lambda texts, **_: [[0.1] * 1024] * len(texts)
        count = await ingest_pdf(sample_pdf)

    assert count > 0
    mock_embed.assert_awaited_once()
    mock_add.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_passes_matching_chunks_and_vectors(sample_pdf: Path):
    with (
        patch("app.rag.ingest.embed_texts", new_callable=AsyncMock) as mock_embed,
        patch("app.rag.ingest.add_chunks") as mock_add,
    ):
        mock_embed.side_effect = lambda texts, **_: [[0.0] * 1024] * len(texts)
        count = await ingest_pdf(sample_pdf)

        chunks_arg, vectors_arg = mock_add.call_args.args
        assert len(chunks_arg) == len(vectors_arg) == count


@pytest.mark.asyncio
async def test_ingest_empty_pdf_returns_zero(tmp_path: Path):
    empty = tmp_path / "empty.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(empty))
    doc.close()

    with (
        patch("app.rag.ingest.embed_texts", new_callable=AsyncMock),
        patch("app.rag.ingest.add_chunks"),
    ):
        count = await ingest_pdf(empty)

    assert count == 0
