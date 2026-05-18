from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.llm import generate
from app.rag.retriever import retrieve

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


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
    chunks = await retrieve(req.question)
    answer = await generate(req.question, chunks)

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
