from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/documents")
async def list_documents():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")
