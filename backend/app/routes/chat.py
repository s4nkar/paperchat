import json
from typing import AsyncIterator

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.config import settings
from app.rag import question_cache
from app.rag.llm import stream_tokens
from app.rag.reranker import rerank
from app.rag.retriever import retrieve

router = APIRouter()


class ChatRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v.strip()


def _event(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False) + "\n"


async def _stream(question: str) -> AsyncIterator[str]:
    cached = question_cache.get(question)
    if cached:
        yield _event({"type": "sources", "data": cached["sources"]})
        yield _event({"type": "token", "data": cached["answer"]})
        yield _event({"type": "usage", "data": {"tokens": 0, "cached": True}})
        yield _event({"type": "done"})
        return

    try:
        chunks = await retrieve(question)
    except Exception as exc:
        yield _event({"type": "error", "data": f"Retrieval failed: {exc}"})
        return

    try:
        chunks = await rerank(question, chunks)
    except Exception as exc:
        yield _event({"type": "error", "data": f"Reranker error: {exc}"})
        return

    chunks = [c for c in chunks if c["score"] >= settings.min_rerank_score]

    if not chunks:
        yield _event({"type": "token", "data": "No relevant content found. Please upload documents before asking questions."})
        yield _event({"type": "done"})
        return

    sources = [
        {
            "text": c["text"],
            "filename": c["metadata"]["filename"],
            "page": c["metadata"]["page"],
            "section": c["metadata"].get("section", ""),
            "score": c["score"],
        }
        for c in chunks
    ]
    yield _event({"type": "sources", "data": sources})

    answer_parts: list[str] = []
    token_count = 0
    try:
        async for item in stream_tokens(question, chunks):
            if isinstance(item, int):
                token_count = item
            else:
                answer_parts.append(item)
                yield _event({"type": "token", "data": item})
    except httpx.HTTPStatusError as exc:
        yield _event({"type": "error", "data": f"LLM error: {exc.response.text}"})
        return
    except Exception as exc:
        yield _event({"type": "error", "data": f"LLM error: {exc}"})
        return

    yield _event({"type": "usage", "data": {"tokens": token_count, "cached": False}})
    yield _event({"type": "done"})

    question_cache.set(question, {
        "sources": sources,
        "answer": "".join(answer_parts),
        "tokens": token_count,
    })


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(_stream(req.question), media_type="application/x-ndjson")
