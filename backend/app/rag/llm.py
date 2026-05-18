import httpx

from app.config import settings

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions strictly based on the provided context. "
    "Cite the source document and page number when you use information from it. "
    "If the answer cannot be found in the context, say so clearly."
)


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk["metadata"]
        parts.append(
            f"[{i}] (Source: {meta['filename']}, page {meta['page']})\n{chunk['text']}"
        )
    return "\n\n".join(parts)


async def generate(question: str, chunks: list[dict]) -> str:
    """Call Groq and return the answer text."""
    context = _build_context(chunks)
    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(_GROQ_URL, json=payload, headers=headers)
        response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]
