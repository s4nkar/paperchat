from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/eval")
async def run_eval():
    raise HTTPException(status_code=501, detail="Not implemented")
