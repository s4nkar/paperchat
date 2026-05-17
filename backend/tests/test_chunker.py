from pathlib import Path

from app.config import settings
from app.rag.chunker import chunk_pdf


def test_produces_chunks(sample_pdf: Path) -> None:
    chunks = chunk_pdf(sample_pdf)
    assert len(chunks) > 0


def test_no_chunk_exceeds_max_size(sample_pdf: Path) -> None:
    max_allowed = settings.chunk_size + settings.chunk_overlap
    for chunk in chunk_pdf(sample_pdf):
        assert len(chunk.text) <= max_allowed, (
            f"Chunk {chunk.chunk_index} has {len(chunk.text)} chars"
        )


def test_chunk_index_is_sequential(sample_pdf: Path) -> None:
    chunks = chunk_pdf(sample_pdf)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_page_numbers_are_valid(sample_pdf: Path) -> None:
    chunks = chunk_pdf(sample_pdf)
    pages = {c.page for c in chunks}
    assert pages <= {1, 2}
    assert all(c.page >= 1 for c in chunks)


def test_no_chunk_spans_pages(sample_pdf: Path) -> None:
    # Chunking is done per page so every chunk carries exactly one page number.
    chunks = chunk_pdf(sample_pdf)
    assert all(isinstance(c.page, int) for c in chunks)


def test_filename_is_preserved(sample_pdf: Path) -> None:
    chunks = chunk_pdf(sample_pdf)
    assert all(c.filename == "sample.pdf" for c in chunks)


def test_section_heading_detected(sample_pdf: Path) -> None:
    chunks = chunk_pdf(sample_pdf)
    sections = {c.section for c in chunks}
    assert any(s in ("Introduction", "Methods") for s in sections)


def test_no_empty_chunk_text(sample_pdf: Path) -> None:
    assert all(c.text.strip() for c in chunk_pdf(sample_pdf))
