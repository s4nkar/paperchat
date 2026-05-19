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


def _api_error(service: str, exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 429:
            return f"{service} rate limit reached. Please wait a moment and try again, or upgrade your API plan."
        if code in (401, 403):
            return f"{service} API key is invalid or expired. Please check your key configuration."
        if code >= 500:
            return f"{service} is temporarily unavailable (HTTP {code}). Please try again shortly."
        return f"{service} returned an unexpected error (HTTP {code})."
    if isinstance(exc, httpx.ConnectError):
        return f"Could not reach {service}. Please check your network connection."
    return f"{service} error: {exc}"


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
        yield _event({"type": "error", "data": _api_error("Jina", exc)})
        return

    try:
        chunks = await rerank(question, chunks)
    except Exception as exc:
        yield _event({"type": "error", "data": _api_error("Cohere", exc)})
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
    except Exception as exc:
        yield _event({"type": "error", "data": _api_error("Groq", exc)})
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
