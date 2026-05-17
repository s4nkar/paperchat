from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="paperchat")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# Served only in the production container where the frontend build is copied to ./static
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
