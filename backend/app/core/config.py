"""
Application configuration.

Centralizes all environment-driven settings so the rest of the codebase
never reads os.environ directly. Uses pydantic-settings for validation
and type coercion.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "AlphaIQ"
    app_env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # ---- LLM ----
    # Provider is pluggable. Default to OpenAI; Anthropic supported as well.
    llm_provider: Literal["openai", "anthropic", "mock"] = "openai"
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536  # must match the embedding model

    anthropic_api_key: str | None = None
    anthropic_chat_model: str = "claude-sonnet-4-5"

    # ---- Vector store ----
    # "chroma" runs locally with zero setup. "pinecone" for managed cloud.
    vector_backend: Literal["chroma", "pinecone"] = "chroma"
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "alphaiq"

    pinecone_api_key: str | None = None
    pinecone_index: str = "alphaiq"
    pinecone_environment: str = "us-east-1"

    # ---- Ingestion ----
    chunk_size_tokens: int = 700  # target tokens per chunk
    chunk_overlap_tokens: int = 100
    max_upload_mb: int = 50

    # ---- Retrieval ----
    retrieval_top_k: int = 6
    retrieval_min_score: float = 0.15  # cosine similarity threshold

    # ---- Paths ----
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def data_dir(self) -> Path:
        p = self.project_root / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
