"""Ingest the bundled sample filings (data/sample/*.txt) into the vector store.

Usage:
    python backend/scripts/ingest_samples.py

Reads configuration from your .env (or environment), so the same script works
whether you're using the mock embedder for offline demos or OpenAI embeddings
for production. Safe to re-run -- chunks are upserted by chunk_id.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.api.deps import ingestion_singleton  # noqa: E402

SAMPLE_DIR = BACKEND_ROOT.parent / "data" / "sample"

SAMPLES = [
    {
        "filename": "AAPL_10K_2024_excerpt.txt",
        "company": "Apple Inc.",
        "ticker": "AAPL",
        "doc_type": "10-K",
        "filing_date": "2024-09-30",
    },
    {
        "filename": "TSLA_10K_2024_excerpt.txt",
        "company": "Tesla, Inc.",
        "ticker": "TSLA",
        "doc_type": "10-K",
        "filing_date": "2024-09-30",
    },
]


def main() -> int:
    ingestion = ingestion_singleton()
    print(f"Ingesting {len(SAMPLES)} sample filings from {SAMPLE_DIR}\n")
    for spec in SAMPLES:
        path = SAMPLE_DIR / spec["filename"]
        if not path.exists():
            print(f"  SKIP (missing): {path}")
            continue
        with path.open("rb") as fh:
            r = ingestion.ingest_file(
                filename=spec["filename"],
                content=fh.read(),
                company=spec["company"],
                ticker=spec["ticker"],
                doc_type=spec["doc_type"],
                filing_date=spec["filing_date"],
            )
        print(
            f"  OK  {spec['ticker']:5s}  doc_id={r.doc_id[:8]}  "
            f"chunks={r.chunks_indexed:3d}  {spec['filename']}"
        )
    print("\nDone. Now start the API: uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
