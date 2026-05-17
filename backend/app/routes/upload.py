from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/upload")
async def upload():
    raise HTTPException(status_code=501, detail="Not implemented")
