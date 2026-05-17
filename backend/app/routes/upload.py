from pathlib import Path

import pymupdf
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class DocumentMeta(BaseModel):
    filename: str
    size: int   # bytes
    pages: int


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
        doc.close()

        results.append(
            DocumentMeta(filename=file.filename or "", size=len(contents), pages=pages)
        )

    return results
