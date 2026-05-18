from fastapi import APIRouter, HTTPException

from app.eval.metrics import run_eval

router = APIRouter()


@router.get("/eval")
async def eval_retrieval():
    try:
        return await run_eval()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
