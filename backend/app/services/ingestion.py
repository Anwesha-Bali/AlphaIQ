"""
Ingestion service.

End-to-end: raw document -> text -> chunks -> embeddings -> vector store.
Returns IngestResponse describing what was indexed.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.embeddings.embedder import Embedder
from app.models.schemas import DocType, DocumentMetadata, IngestResponse
from app.rag.chunker import chunk_text
from app.rag.loaders import load_file, load_url
from app.rag.vector_store import StoredChunk, VectorStore

log = get_logger(__name__)


class IngestionService:
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store
        self.settings = get_settings()

    # --------------------------------------------------------
    # File upload path
    # --------------------------------------------------------
    def ingest_file(
        self,
        filename: str,
        content: bytes,
        *,
        company: str | None = None,
        ticker: str | None = None,
        doc_type: DocType = "other",
        filing_date: str | None = None,
    ) -> IngestResponse:
        text = load_file(filename, content)
        return self._ingest_text(
            text=text,
            source=filename,
            company=company,
            ticker=ticker,
            doc_type=doc_type,
            filing_date=filing_date,
        )

    # --------------------------------------------------------
    # URL path
    # --------------------------------------------------------
    def ingest_url(
        self,
        url: str,
        *,
        company: str | None = None,
        ticker: str | None = None,
        doc_type: DocType = "news",
    ) -> IngestResponse:
        text = load_url(url)
        return self._ingest_text(
            text=text,
            source=url,
            company=company,
            ticker=ticker,
            doc_type=doc_type,
            filing_date=None,
        )

    # --------------------------------------------------------
    # Shared core
    # --------------------------------------------------------
    def _ingest_text(
        self,
        *,
        text: str,
        source: str,
        company: str | None,
        ticker: str | None,
        doc_type: DocType,
        filing_date: str | None,
    ) -> IngestResponse:
        if not text or len(text.strip()) < 30:
            raise ValueError(f"Document {source!r} produced no extractable text.")

        chunks = chunk_text(
            text,
            chunk_size=self.settings.chunk_size_tokens,
            overlap=self.settings.chunk_overlap_tokens,
        )
        if not chunks:
            raise ValueError(f"Document {source!r} produced no chunks.")

        doc_id = uuid.uuid4().hex[:12]
        metadata = DocumentMetadata(
            doc_id=doc_id,
            source=source,
            company=company,
            ticker=ticker.upper() if ticker else None,
            doc_type=doc_type,
            filing_date=filing_date,
            ingested_at=datetime.utcnow(),
        )

        log.info(
            "Embedding %d chunks for doc_id=%s source=%s ticker=%s",
            len(chunks),
            doc_id,
            source,
            ticker,
        )
        vectors = self.embedder.embed([c.text for c in chunks])

        stored = [
            StoredChunk(
                chunk_id=f"{doc_id}:{c.index}",
                text=c.text,
                embedding=vec,
                metadata={
                    "doc_id": doc_id,
                    "chunk_index": c.index,
                    "source": source,
                    "company": company,
                    "ticker": (ticker.upper() if ticker else None),
                    "doc_type": doc_type,
                    "filing_date": filing_date,
                    "token_count": c.token_count,
                },
            )
            for c, vec in zip(chunks, vectors)
        ]
        self.store.upsert(stored)

        log.info("Indexed doc_id=%s chunks=%d", doc_id, len(stored))
        return IngestResponse(
            doc_id=doc_id,
            source=source,
            chunks_indexed=len(stored),
            metadata=metadata,
        )
