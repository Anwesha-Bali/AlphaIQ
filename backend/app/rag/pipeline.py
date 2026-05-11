"""
RAG pipeline.

This is the orchestration layer that the API endpoints call. It wires
together the embedder, vector store, LLM, and prompts.

Workflow (`answer`):
    1. Embed the question.
    2. Retrieve top_k chunks (optionally filtered by ticker).
    3. Filter by minimum similarity score.
    4. If nothing useful retrieved -> return insufficient_context.
    5. Build the QA prompt and call the LLM.
    6. Return answer + citations.

Insights and Comparison follow the same shape but with different
prompts and (for insights) JSON-mode output that we then validate.
"""
from __future__ import annotations

import json
import re
import time
from typing import Iterator

from app.core.config import get_settings
from app.core.logging import get_logger
from app.embeddings.embedder import Embedder
from app.models.schemas import (
    Citation,
    CompanyInsights,
    ComparisonResponse,
    QueryResponse,
    RiskFactor,
)
from app.rag.prompts import (
    build_compare_messages,
    build_insights_messages,
    build_qa_messages,
)
from app.rag.vector_store import SearchHit, VectorStore
from app.services.llm import LLM

log = get_logger(__name__)

# Maximum chars of chunk text we ship back to the UI as a citation snippet.
_SNIPPET_CHARS = 320


def _hit_to_citation(hit: SearchHit) -> Citation:
    meta = hit.metadata or {}
    snippet = hit.text[:_SNIPPET_CHARS]
    if len(hit.text) > _SNIPPET_CHARS:
        snippet += "…"
    return Citation(
        chunk_id=hit.chunk_id,
        doc_id=str(meta.get("doc_id", "")),
        source=str(meta.get("source", "unknown")),
        company=meta.get("company"),
        doc_type=meta.get("doc_type", "other"),
        score=hit.score,
        snippet=snippet,
    )


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of an LLM response, tolerating fences."""
    text = text.strip()
    # Strip ```json ... ``` fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    # Find first { ... last } if needed.
    if not text.startswith("{"):
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
    return json.loads(text)


class RagPipeline:
    def __init__(self, embedder: Embedder, store: VectorStore, llm: LLM):
        self.embedder = embedder
        self.store = store
        self.llm = llm
        self.settings = get_settings()

    # --------------------------------------------------------
    # Retrieval
    # --------------------------------------------------------
    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        ticker: str | None = None,
    ) -> list[SearchHit]:
        k = top_k or self.settings.retrieval_top_k
        vec = self.embedder.embed_one(question)
        filters = {"ticker": ticker.upper()} if ticker else None
        hits = self.store.search(query_vec=vec, top_k=k, filters=filters)
        # Drop low-confidence hits below the configured threshold.
        kept = [h for h in hits if h.score >= self.settings.retrieval_min_score]
        log.info(
            "retrieve: q=%r k=%d ticker=%s raw=%d kept=%d",
            question[:80],
            k,
            ticker,
            len(hits),
            len(kept),
        )
        return kept

    # --------------------------------------------------------
    # Q&A
    # --------------------------------------------------------
    def answer(
        self,
        question: str,
        top_k: int | None = None,
        ticker: str | None = None,
    ) -> QueryResponse:
        t0 = time.perf_counter()
        hits = self.retrieve(question, top_k=top_k, ticker=ticker)
        if not hits:
            return QueryResponse(
                answer=(
                    "Not enough context to answer confidently. "
                    "Try uploading relevant filings, news, or research first."
                ),
                citations=[],
                insufficient_context=True,
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
        messages = build_qa_messages(question, hits)
        answer_text = self.llm.complete(messages, temperature=0.2, max_tokens=900)
        return QueryResponse(
            answer=answer_text.strip(),
            citations=[_hit_to_citation(h) for h in hits],
            insufficient_context=False,
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )

    def answer_stream(
        self,
        question: str,
        top_k: int | None = None,
        ticker: str | None = None,
    ) -> Iterator[dict]:
        """Token-streaming variant. Yields dicts the API turns into SSE events.

        Event schema:
            {"type": "citations", "citations": [...]}
            {"type": "token", "text": "..."}
            {"type": "done"}
            {"type": "insufficient_context"}
        """
        hits = self.retrieve(question, top_k=top_k, ticker=ticker)
        if not hits:
            yield {"type": "insufficient_context"}
            yield {"type": "done"}
            return
        # Send citations up front so the UI can show sources while tokens stream.
        yield {
            "type": "citations",
            "citations": [_hit_to_citation(h).model_dump() for h in hits],
        }
        messages = build_qa_messages(question, hits)
        for delta in self.llm.stream(messages, temperature=0.2, max_tokens=900):
            yield {"type": "token", "text": delta}
        yield {"type": "done"}

    # --------------------------------------------------------
    # Structured insights
    # --------------------------------------------------------
    def insights(self, ticker: str, company: str | None = None) -> CompanyInsights:
        # Retrieve broadly across the company's docs via several probe queries.
        probes = [
            f"{ticker} business overview revenue products segments",
            f"{ticker} risk factors litigation regulatory",
            f"{ticker} management discussion outlook guidance",
            f"{ticker} competition market share",
        ]
        seen: dict[str, SearchHit] = {}
        for p in probes:
            for h in self.retrieve(p, top_k=4, ticker=ticker):
                seen.setdefault(h.chunk_id, h)
        hits = sorted(seen.values(), key=lambda h: h.score, reverse=True)[:10]
        if not hits:
            raise ValueError(
                f"No indexed documents found for ticker {ticker!r}. "
                "Upload filings or news for this company first."
            )

        messages = build_insights_messages(ticker, company, hits)
        raw = self.llm.complete(
            messages, temperature=0.2, max_tokens=1500, response_format_json=True
        )
        try:
            data = _extract_json(raw)
        except json.JSONDecodeError:
            log.error("Insights JSON parse failed; raw=%s", raw[:500])
            raise ValueError("Model did not return valid JSON for insights.")

        risks = [
            RiskFactor(
                title=str(r.get("title", "")).strip() or "Untitled risk",
                description=str(r.get("description", "")).strip(),
                severity=r.get("severity", "medium"),
            )
            for r in data.get("risk_factors", [])
        ]
        return CompanyInsights(
            ticker=ticker.upper(),
            company=company or data.get("company"),
            summary=data.get("summary", ""),
            revenue_trends=data.get("revenue_trends", ""),
            risk_factors=risks,
            competitive_positioning=data.get("competitive_positioning", ""),
            management_commentary=data.get("management_commentary", ""),
            overall_risk=data.get("overall_risk", "medium"),
            citations=[_hit_to_citation(h) for h in hits],
        )

    # --------------------------------------------------------
    # Multi-company comparison
    # --------------------------------------------------------
    def compare(self, tickers: list[str], dimension: str) -> ComparisonResponse:
        tickers = [t.upper() for t in tickers]
        all_hits: dict[str, SearchHit] = {}
        for t in tickers:
            probe = f"{t} {dimension}"
            for h in self.retrieve(probe, top_k=4, ticker=t):
                all_hits.setdefault(h.chunk_id, h)
        hits = sorted(all_hits.values(), key=lambda h: h.score, reverse=True)[:12]
        if not hits:
            return ComparisonResponse(
                tickers=tickers,
                dimension=dimension,
                analysis=(
                    "Not enough context to compare these companies. "
                    "Upload filings or news for each ticker first."
                ),
                citations=[],
            )
        messages = build_compare_messages(tickers, dimension, hits)
        text = self.llm.complete(messages, temperature=0.2, max_tokens=1200)
        return ComparisonResponse(
            tickers=tickers,
            dimension=dimension,
            analysis=text.strip(),
            citations=[_hit_to_citation(h) for h in hits],
        )
