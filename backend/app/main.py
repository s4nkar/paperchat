from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import chat, documents, eval, upload

app = FastAPI(title="paperchat")

app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(eval.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# Served only in the production container where the frontend build is copied to ./static
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
