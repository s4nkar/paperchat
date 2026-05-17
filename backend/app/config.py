from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    jina_api_key: str = ""
    groq_api_key: str = ""
    cohere_api_key: str = ""

    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "jina-embeddings-v3"
    chroma_persist_dir: str = "/data/chroma"
    upload_dir: str = "/data/uploads"

    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_dense: int = 10
    top_k_bm25: int = 10
    top_k_rerank: int = 5


settings = Settings()
