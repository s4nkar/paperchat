from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env is optional; env vars always override (Docker Compose and HF Spaces inject secrets this way)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # API keys default to empty so the app starts without .env; routes fail at call time if missing
    jina_api_key: str = ""
    groq_api_key: str = ""
    cohere_api_key: str = ""

    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "jina-embeddings-v3"

    # Absolute paths inside the container; override in .env for local non-Docker dev
    chroma_persist_dir: str = "/data/chroma"
    upload_dir: str = "/data/uploads"

    # Changing these requires re-ingesting because existing embeddings were computed with the old chunk text
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Retrieval cascade: dense (10) + BM25 (10) → RRF → rerank top 3
    top_k_dense: int = 10
    top_k_bm25: int = 10
    top_k_rerank: int = 3


settings = Settings()
