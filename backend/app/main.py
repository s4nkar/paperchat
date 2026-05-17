from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="paperchat")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
