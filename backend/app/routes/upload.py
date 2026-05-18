import logging
from pathlib import Path

import pymupdf
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.rag.ingest import ingest_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

_MIN_CHARS_PER_PAGE = 50  # below this average → likely image-only
_PDF_MAGIC = b"%PDF"
_MAX_FILE_BYTES = 15 * 1024 * 1024  # 15 MB


class DocumentMeta(BaseModel):
    filename: str
    size: int   # bytes
    pages: int
    chunk_count: int = 0
    warning: str | None = None


# Module-level so tests can monkeypatch it
UPLOAD_DIR = Path(settings.upload_dir)


def _safe_filename(raw: str) -> str:
    """Strip any directory components to prevent path traversal."""
    return Path(raw).name or "upload.pdf"


async def _read_and_validate(file: UploadFile) -> tuple[str, bytes]:
    """Return (safe_filename, contents) or raise HTTPException."""
    raw_name = file.filename or ""
    if not raw_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail=f"{raw_name!r} is not a PDF")

    contents = await file.read()

    if len(contents) > _MAX_FILE_BYTES:
        mb = len(contents) / 1024 / 1024
        raise HTTPException(status_code=422, detail=f"{raw_name!r} is {mb:.1f} MB — limit is 15 MB")

    if not contents.startswith(_PDF_MAGIC):
        raise HTTPException(status_code=422, detail=f"{raw_name!r} is not a valid PDF file")

    return _safe_filename(raw_name), contents


@router.post("/upload", response_model=list[DocumentMeta])
async def upload(files: list[UploadFile] = File(...)) -> list[DocumentMeta]:
    if not files:
        raise HTTPException(status_code=422, detail="No files provided")

    # Validate and read all files before writing anything to disk
    validated: list[tuple[str, bytes]] = []
    for file in files:
        validated.append(await _read_and_validate(file))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    results: list[DocumentMeta] = []

    for safe_name, contents in validated:
        dest = UPLOAD_DIR / safe_name
        dest.write_bytes(contents)

        doc = pymupdf.open(stream=contents, filetype="pdf")
        pages = doc.page_count
        total_chars = sum(len(doc[i].get_text("text")) for i in range(pages))
        doc.close()

        warning = None
        if pages > 0 and (total_chars / pages) < _MIN_CHARS_PER_PAGE:
            warning = (
                "This PDF appears to contain scanned images with no extractable text. "
                "OCR is not supported — the document will not be searchable."
            )

        chunk_count = await ingest_pdf(dest)

        results.append(
            DocumentMeta(
                filename=safe_name,
                size=len(contents),
                pages=pages,
                chunk_count=chunk_count,
                warning=warning,
            )
        )

    return results
