"""
FastAPI dependency providers.

Singletons created lazily on first request, so tests can override them
and so we don't pay startup cost for code paths we never hit.
"""
from __future__ import annotations

from functools import lru_cache

from app.embeddings.embedder import Embedder, get_embedder
from app.rag.pipeline import RagPipeline
from app.rag.vector_store import VectorStore, get_vector_store
from app.services.ingestion import IngestionService
from app.services.llm import LLM, get_llm


@lru_cache
def embedder_singleton() -> Embedder:
    return get_embedder()


@lru_cache
def store_singleton() -> VectorStore:
    return get_vector_store()


@lru_cache
def llm_singleton() -> LLM:
    return get_llm()


@lru_cache
def pipeline_singleton() -> RagPipeline:
    return RagPipeline(
        embedder=embedder_singleton(),
        store=store_singleton(),
        llm=llm_singleton(),
    )


@lru_cache
def ingestion_singleton() -> IngestionService:
    return IngestionService(
        embedder=embedder_singleton(),
        store=store_singleton(),
    )
