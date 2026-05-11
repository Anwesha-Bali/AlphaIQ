"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("=" * 60)
    log.info("AlphaIQ starting | env=%s", settings.app_env)
    log.info("LLM provider     | %s", settings.llm_provider)
    log.info("Vector backend   | %s", settings.vector_backend)
    log.info("CORS origins     | %s", settings.cors_origins)
    log.info("=" * 60)
    yield
    log.info("AlphaIQ shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "AI investment research platform. RAG over SEC filings, "
            "earnings transcripts, and news, with grounded citations."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    return app


app = create_app()
