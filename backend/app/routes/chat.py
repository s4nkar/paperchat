import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.config import settings
from app.rag.llm import generate
from app.rag.retriever import retrieve

_MIN_SCORE = 0.15

router = APIRouter()


class ChatRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v.strip()


class SourceChunk(BaseModel):
    text: str
    filename: str
    page: int
    section: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        chunks = await retrieve(req.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Retrieval failed: {exc}") from exc

    chunks = [c for c in chunks if c["score"] >= _MIN_SCORE][: settings.top_k_rerank]

    if not chunks:
        return ChatResponse(
            answer="No relevant content found. Please upload documents before asking questions.",
            sources=[],
        )

    try:
        answer = await generate(req.question, chunks)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc.response.text}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc

    sources = [
        SourceChunk(
            text=c["text"],
            filename=c["metadata"]["filename"],
            page=c["metadata"]["page"],
            section=c["metadata"].get("section", ""),
            score=c["score"],
        )
        for c in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)
