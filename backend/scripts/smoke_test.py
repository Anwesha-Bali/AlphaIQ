"""End-to-end smoke test for the AlphaIQ RAG pipeline.

Runs entirely offline using MockLLM + MockEmbedder + ChromaStore. Ingests the
two sample 10-K excerpts in data/sample/, then exercises every pipeline path:
retrieval, QA with citations, streaming, insights JSON, and comparison.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_PROVIDER", "mock")
os.environ.setdefault("VECTOR_BACKEND", "chroma")
os.environ.setdefault("CHROMA_PERSIST_DIR", str(BACKEND_ROOT.parent / "data" / "chroma_smoke"))
os.environ.setdefault("EMBEDDING_DIM", "384")
# Mock embeddings produce weak signals; relax the threshold so the smoke
# test verifies plumbing end-to-end. Real embedders easily clear 0.15+.
os.environ.setdefault("RETRIEVAL_MIN_SCORE", "0.0")

from app.api.deps import ingestion_singleton, pipeline_singleton  # noqa: E402

SAMPLE_DIR = BACKEND_ROOT.parent / "data" / "sample"


def banner(title: str) -> None:
    print()
    print("=" * 72)
    print(f" {title}")
    print("=" * 72)


def main() -> int:
    banner("Bootstrapping services (mock LLM, mock embedder, Chroma)")
    ingestion = ingestion_singleton()
    pipeline = pipeline_singleton()
    print(" services ready")

    banner("Ingesting sample filings")
    samples = [
        ("AAPL_10K_2024_excerpt.txt", "Apple Inc.", "AAPL"),
        ("TSLA_10K_2024_excerpt.txt", "Tesla, Inc.", "TSLA"),
    ]
    for filename, company, ticker in samples:
        path = SAMPLE_DIR / filename
        if not path.exists():
            print(f"  ! missing sample: {path}")
            return 1
        with path.open("rb") as fh:
            result = ingestion.ingest_file(
                filename=filename,
                content=fh.read(),
                company=company,
                ticker=ticker,
                doc_type="10-K",
                filing_date="2024-09-30",
            )
        print(f"  {ticker:5s}  doc_id={result.doc_id[:8]}...  chunks={result.chunks_indexed}")

    banner("Retrieval sanity check")
    hits = pipeline.retrieve("What are the biggest risk factors?", top_k=4)
    print(f"  returned {len(hits)} hits")
    for i, h in enumerate(hits, 1):
        co = h.metadata.get("company") or "?"
        print(f"   [{i}] score={h.score:.3f}  {co}  {h.text[:80].strip()}...")

    banner("QA: 'What are Tesla's biggest risks?'")
    resp = pipeline.answer("What are Tesla's biggest risks?", top_k=5)
    print(f"  insufficient_context={resp.insufficient_context}  latency={resp.latency_ms}ms")
    print(f"  answer ({len(resp.answer)} chars):")
    print("  " + resp.answer.replace("\n", "\n  ")[:600])
    print(f"  citations: {len(resp.citations)}")
    for i, c in enumerate(resp.citations, 1):
        print(f"   [{i}] {c.company} - {c.source} (score={c.score:.3f})")

    banner("Streaming QA: 'Summarize Apple's revenue trends'")
    events = list(pipeline.answer_stream("Summarize Apple's revenue trends", top_k=5))
    types = [e["type"] for e in events]
    print(f"  event types: {types[:6]}{'...' if len(types) > 6 else ''}  total={len(events)}")
    tokens = [e["text"] for e in events if e["type"] == "token"]
    if tokens:
        print(f"  streamed text preview: {''.join(tokens)[:200]}...")

    banner("Structured insights for AAPL")
    insights = pipeline.insights(ticker="AAPL", company="Apple Inc.")
    print(f"  ticker: {insights.ticker}  overall_risk: {insights.overall_risk}")
    print(f"  summary: {insights.summary[:160]}...")
    print(f"  revenue_trends: {insights.revenue_trends[:160]}...")
    print(f"  risk factors: {len(insights.risk_factors)}")
    for r in insights.risk_factors[:3]:
        print(f"   - [{r.severity}] {r.title}")
    print(f"  competitive_positioning: {insights.competitive_positioning[:160]}...")
    print(f"  management_commentary: {insights.management_commentary[:160]}...")
    print(f"  citations: {len(insights.citations)}")

    banner("Comparison: AAPL vs TSLA - risk factors")
    cmp = pipeline.compare(tickers=["AAPL", "TSLA"], dimension="risk factors")
    print(f"  tickers={cmp.tickers}  dimension={cmp.dimension!r}")
    print(f"  analysis ({len(cmp.analysis)} chars):")
    print("  " + cmp.analysis.replace("\n", "\n  ")[:500])
    print(f"  citations: {len(cmp.citations)}")

    banner("ALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
