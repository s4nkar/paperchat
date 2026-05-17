from dataclasses import dataclass
from pathlib import Path

import pymupdf

from app.config import settings

_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    text: str
    filename: str
    page: int
    section: str
    chunk_index: int


def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or not 3 <= len(line) <= 80:
        return False
    if line[-1] in ".,:;!?":
        return False
    if not (line[0].isupper() or line[0].isdigit()):
        return False
    if len(line.split()) > 8:
        return False
    return True


def _merge_pieces(pieces: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    """Merge small pieces into chunks with piece-boundary overlap (LangChain-style)."""
    chunks: list[str] = []
    window: list[str] = []
    window_len = 0

    for piece in pieces:
        piece_len = len(piece)
        if window and window_len + 1 + piece_len > chunk_size:
            chunks.append(" ".join(window))
            # Slide window back: drop pieces from the front until overlap fits
            while window and (window_len > chunk_overlap or window_len + 1 + piece_len > chunk_size):
                window_len -= len(window[0]) + (1 if len(window) > 1 else 0)
                window.pop(0)
        window.append(piece)
        window_len += piece_len + (1 if len(window) > 1 else 0)

    if window:
        chunks.append(" ".join(window))
    return chunks


def _split_recursive(text: str, separators: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    if not separators:
        step = max(1, chunk_size - chunk_overlap)
        return [text[i : i + chunk_size] for i in range(0, len(text), step)]

    # Find the first separator that actually appears in the text
    sep = separators[-1]
    rest: list[str] = []
    for i, s in enumerate(separators):
        if s in text:
            sep, rest = s, separators[i + 1:]
            break

    pieces: list[str] = []
    for part in text.split(sep):
        part = part.strip()
        if not part:
            continue
        if len(part) <= chunk_size:
            pieces.append(part)
        else:
            pieces.extend(_split_recursive(part, rest, chunk_size, chunk_overlap))

    return _merge_pieces(pieces, chunk_size, chunk_overlap)


def chunk_pdf(path: Path) -> list[Chunk]:
    doc = pymupdf.open(str(path))
    all_chunks: list[Chunk] = []
    chunk_index = 0
    current_section = ""

    for page_num in range(doc.page_count):
        text = doc[page_num].get_text("text")
        if not text.strip():
            continue

        for line in text.splitlines():
            if _is_heading(line):
                current_section = line.strip()
                break

        page_chunks = _split_recursive(
            text,
            _SEPARATORS,
            settings.chunk_size,
            settings.chunk_overlap,
        )

        for chunk_text in page_chunks:
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
            all_chunks.append(
                Chunk(
                    text=chunk_text,
                    filename=path.name,
                    page=page_num + 1,
                    section=current_section,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

    doc.close()
    return all_chunks
