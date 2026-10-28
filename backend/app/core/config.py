import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "sqlite:///./knowledgepilot.db"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    upload_dir: Path = Path("uploads")
    jwt_secret_key: str = secrets.token_urlsafe(48)
    access_token_expire_minutes: int = 60
    max_upload_size_bytes: int = 10 * 1024 * 1024
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    retrieval_similarity_threshold: float = 0.2
    cors_origins: str = "http://localhost:5173"


settings = Settings()
