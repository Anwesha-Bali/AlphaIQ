"""
API schemas — request and response models.

These are the contract between backend and frontend. Anything that
leaves the server or arrives from a client is validated here.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ============================================================
# Documents & chunks
# ============================================================

DocType = Literal["10-K", "10-Q", "8-K", "earnings_call", "news", "research", "other"]


class DocumentMetadata(BaseModel):
    """Metadata attached to every chunk we store."""

    doc_id: str
    source: str = Field(description="Filename or URL")
    company: str | None = None
    ticker: str | None = None
    doc_type: DocType = "other"
    filing_date: str | None = None  # ISO date string if known
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class IngestResponse(BaseModel):
    doc_id: str
    source: str
    chunks_indexed: int
    metadata: DocumentMetadata


class IngestUrlRequest(BaseModel):
    url: HttpUrl
    company: str | None = None
    ticker: str | None = None
    doc_type: DocType = "news"


# ============================================================
# Q&A (RAG)
# ============================================================


class Citation(BaseModel):
    """A single source chunk used to ground an answer."""

    chunk_id: str
    doc_id: str
    source: str
    company: str | None = None
    doc_type: DocType
    score: float
    snippet: str  # truncated chunk text shown in UI


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    ticker: str | None = Field(
        default=None,
        description="Optional ticker filter; if set, only that company's docs are searched.",
    )


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    insufficient_context: bool = False
    latency_ms: int


# ============================================================
# Structured insights
# ============================================================


class RiskFactor(BaseModel):
    title: str
    description: str
    severity: Literal["low", "medium", "high"]


class CompanyInsights(BaseModel):
    """Structured company report built from retrieved filings."""

    ticker: str
    company: str | None = None
    summary: str
    revenue_trends: str
    risk_factors: list[RiskFactor]
    competitive_positioning: str
    management_commentary: str
    overall_risk: Literal["low", "medium", "high"]
    citations: list[Citation]


class InsightsRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    company: str | None = None


# ============================================================
# Comparison
# ============================================================


class ComparisonRequest(BaseModel):
    tickers: list[str] = Field(min_length=2, max_length=5)
    dimension: str = Field(
        default="risks, margins, growth, and competitive moat",
        description="What to compare across companies.",
    )


class ComparisonResponse(BaseModel):
    tickers: list[str]
    dimension: str
    analysis: str
    citations: list[Citation]


# ============================================================
# Health
# ============================================================


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    env: str
    llm_provider: str
    vector_backend: str
    indexed_chunks: int
