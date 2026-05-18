from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag import bm25_store, chroma_store

router = APIRouter()


class DocumentInfo(BaseModel):
    filename: str
    page_count: int
    chunk_count: int


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents() -> list[DocumentInfo]:
    return [DocumentInfo(**d) for d in chroma_store.list_documents()]


@router.delete("/documents/{filename:path}", status_code=204)
async def delete_document(filename: str) -> None:
    existing = {d["filename"] for d in chroma_store.list_documents()}
    if filename not in existing:
        raise HTTPException(status_code=404, detail=f"{filename!r} not found")
    chroma_store.delete_document(filename)
    bm25_store.remove_document(filename)
