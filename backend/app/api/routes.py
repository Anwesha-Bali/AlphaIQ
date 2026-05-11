"""
HTTP routes.

Thin layer: parse, call a service, serialize. Business logic lives in
`services/` and `rag/`.
"""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import (
    ingestion_singleton,
    pipeline_singleton,
    store_singleton,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import (
    CompanyInsights,
    ComparisonRequest,
    ComparisonResponse,
    DocType,
    HealthResponse,
    IngestResponse,
    IngestUrlRequest,
    InsightsRequest,
    QueryRequest,
    QueryResponse,
)
from app.rag.pipeline import RagPipeline
from app.services.ingestion import IngestionService

log = get_logger(__name__)
router = APIRouter()


# ============================================================
# Health
# ============================================================
@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    settings = get_settings()
    try:
        store_count = store_singleton().count()
        status = "ok"
    except Exception as e:  # pragma: no cover
        log.error("Health check store error: %s", e)
        store_count = 0
        status = "degraded"
    return HealthResponse(
        status=status,
        app=settings.app_name,
        env=settings.app_env,
        llm_provider=settings.llm_provider,
        vector_backend=settings.vector_backend,
        indexed_chunks=store_count,
    )


# ============================================================
# Ingestion — file upload
# ============================================================
@router.post("/upload", response_model=IngestResponse, tags=["ingest"])
async def upload(
    file: Annotated[UploadFile, File(description="PDF, TXT, MD, HTML, or CSV file")],
    company: Annotated[str | None, Form()] = None,
    ticker: Annotated[str | None, Form()] = None,
    doc_type: Annotated[DocType, Form()] = "other",
    filing_date: Annotated[str | None, Form()] = None,
    ingestion: IngestionService = Depends(ingestion_singleton),
) -> IngestResponse:
    settings = get_settings()
    raw = await file.read()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB; limit {settings.max_upload_mb} MB).",
        )
    try:
        return ingestion.ingest_file(
            filename=file.filename or "upload.bin",
            content=raw,
            company=company,
            ticker=ticker,
            doc_type=doc_type,
            filing_date=filing_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # pragma: no cover
        log.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e


# ============================================================
# Ingestion — URL
# ============================================================
@router.post("/ingest-url", response_model=IngestResponse, tags=["ingest"])
def ingest_url(
    req: IngestUrlRequest,
    ingestion: IngestionService = Depends(ingestion_singleton),
) -> IngestResponse:
    try:
        return ingestion.ingest_url(
            url=str(req.url),
            company=req.company,
            ticker=req.ticker,
            doc_type=req.doc_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # pragma: no cover
        log.exception("URL ingest failed")
        raise HTTPException(status_code=500, detail=f"URL ingest failed: {e}") from e


# ============================================================
# Query — synchronous answer
# ============================================================
@router.post("/query", response_model=QueryResponse, tags=["query"])
def query(
    req: QueryRequest,
    pipeline: RagPipeline = Depends(pipeline_singleton),
) -> QueryResponse:
    try:
        return pipeline.answer(
            question=req.question, top_k=req.top_k, ticker=req.ticker
        )
    except Exception as e:  # pragma: no cover
        log.exception("Query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}") from e


# ============================================================
# Query — streaming (SSE)
# ============================================================
@router.post("/query/stream", tags=["query"])
def query_stream(
    req: QueryRequest,
    pipeline: RagPipeline = Depends(pipeline_singleton),
) -> StreamingResponse:
    def event_stream():
        try:
            for event in pipeline.answer_stream(
                question=req.question, top_k=req.top_k, ticker=req.ticker
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:  # pragma: no cover
            err = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# Structured insights
# ============================================================
@router.post("/insights", response_model=CompanyInsights, tags=["insights"])
def insights(
    req: InsightsRequest,
    pipeline: RagPipeline = Depends(pipeline_singleton),
) -> CompanyInsights:
    try:
        return pipeline.insights(ticker=req.ticker, company=req.company)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:  # pragma: no cover
        log.exception("Insights failed")
        raise HTTPException(status_code=500, detail=f"Insights failed: {e}") from e


# ============================================================
# Multi-company comparison
# ============================================================
@router.post("/compare", response_model=ComparisonResponse, tags=["insights"])
def compare(
    req: ComparisonRequest,
    pipeline: RagPipeline = Depends(pipeline_singleton),
) -> ComparisonResponse:
    try:
        return pipeline.compare(tickers=req.tickers, dimension=req.dimension)
    except Exception as e:  # pragma: no cover
        log.exception("Compare failed")
        raise HTTPException(status_code=500, detail=f"Compare failed: {e}") from e
