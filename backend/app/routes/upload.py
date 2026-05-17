from pathlib import Path

import pymupdf
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


_MIN_CHARS_PER_PAGE = 50  # below this average → likely image-only


class DocumentMeta(BaseModel):
    filename: str
    size: int   # bytes
    pages: int
    warning: str | None = None


# Module-level so tests can monkeypatch it
UPLOAD_DIR = Path(settings.upload_dir)


@router.post("/upload", response_model=list[DocumentMeta])
async def upload(files: list[UploadFile] = File(...)) -> list[DocumentMeta]:
    if not files:
        raise HTTPException(status_code=422, detail="No files provided")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    results: list[DocumentMeta] = []

    for file in files:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=422, detail=f"{file.filename!r} is not a PDF"
            )

        # Read once so we can write and parse from the same bytes without re-reading disk
        contents = await file.read()
        dest = UPLOAD_DIR / (file.filename or "upload.pdf")
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

        results.append(
            DocumentMeta(
                filename=file.filename or "",
                size=len(contents),
                pages=pages,
                warning=warning,
            )
        )

    return results
