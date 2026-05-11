"""
Vector store abstractions.

A `VectorStore` exposes only what the RAG layer needs:
    - upsert(chunks)
    - search(query_vec, top_k, filters)
    - count()
    - delete(doc_id)

Two backends are implemented:
    - ChromaStore   — local, zero-setup, persists to disk
    - PineconeStore — managed cloud, used when VECTOR_BACKEND=pinecone
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class StoredChunk:
    """One row in the vector store."""

    chunk_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]  # doc_id, source, company, ticker, doc_type, etc.


@dataclass
class SearchHit:
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: list[StoredChunk]) -> None: ...

    @abstractmethod
    def search(
        self,
        query_vec: list[float],
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def delete_doc(self, doc_id: str) -> int: ...


# ------------------------------------------------------------
# Chroma (default)
# ------------------------------------------------------------
class ChromaStore(VectorStore):
    """Local persistent Chroma collection. Cosine space."""

    def __init__(self, settings: Settings):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
        log.info(
            "ChromaStore ready (path=%s, collection=%s, count=%d)",
            settings.chroma_persist_dir,
            settings.chroma_collection,
            self._collection.count(),
        )

    def upsert(self, chunks: list[StoredChunk]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=[c.embedding for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[self._clean_meta(c.metadata) for c in chunks],
        )

    @staticmethod
    def _clean_meta(meta: dict[str, Any]) -> dict[str, Any]:
        """Chroma rejects non-primitive metadata values."""
        out: dict[str, Any] = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                out[k] = v
            else:
                out[k] = str(v)
        return out

    def search(
        self,
        query_vec: list[float],
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        where = filters or None
        res = self._collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            where=where,
        )
        # Chroma returns lists-of-lists (one per query); we only ever pass one.
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        hits: list[SearchHit] = []
        for cid, txt, meta, dist in zip(ids, docs, metas, dists):
            # Chroma cosine distance is in [0, 2]. Convert to similarity in [-1, 1].
            score = 1.0 - float(dist)
            hits.append(
                SearchHit(chunk_id=cid, text=txt, score=score, metadata=meta or {})
            )
        return hits

    def count(self) -> int:
        return self._collection.count()

    def delete_doc(self, doc_id: str) -> int:
        before = self._collection.count()
        self._collection.delete(where={"doc_id": doc_id})
        after = self._collection.count()
        return before - after


# ------------------------------------------------------------
# Pinecone
# ------------------------------------------------------------
class PineconeStore(VectorStore):
    """Pinecone serverless index. Cosine metric."""

    def __init__(self, settings: Settings):
        from pinecone import Pinecone, ServerlessSpec

        if not settings.pinecone_api_key:
            raise RuntimeError("PINECONE_API_KEY required for pinecone backend.")
        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        existing = {idx.name for idx in self._pc.list_indexes()}
        if settings.pinecone_index not in existing:
            self._pc.create_index(
                name=settings.pinecone_index,
                dimension=settings.embedding_dim,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
            )
        self._index = self._pc.Index(settings.pinecone_index)
        log.info("PineconeStore ready (index=%s)", settings.pinecone_index)

    def upsert(self, chunks: list[StoredChunk]) -> None:
        if not chunks:
            return
        vectors = [
            {
                "id": c.chunk_id,
                "values": c.embedding,
                "metadata": {**c.metadata, "text": c.text},
            }
            for c in chunks
        ]
        # Pinecone recommends batches of ~100.
        for i in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[i : i + 100])

    def search(
        self,
        query_vec: list[float],
        top_k: int = 6,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        res = self._index.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True,
            filter=filters or None,
        )
        hits: list[SearchHit] = []
        for m in res.matches:
            meta = dict(m.metadata or {})
            text = meta.pop("text", "")
            hits.append(
                SearchHit(chunk_id=m.id, text=text, score=float(m.score), metadata=meta)
            )
        return hits

    def count(self) -> int:
        try:
            stats = self._index.describe_index_stats()
            return int(stats.get("total_vector_count", 0))
        except Exception:  # pragma: no cover
            return 0

    def delete_doc(self, doc_id: str) -> int:
        # Pinecone serverless requires metadata-filter delete via a list-of-ids path.
        # For simplicity we use the filter API where available.
        try:
            self._index.delete(filter={"doc_id": doc_id})
            return -1  # unknown count delta
        except Exception as e:  # pragma: no cover
            log.warning("Pinecone delete failed: %s", e)
            return 0


# ------------------------------------------------------------
# Factory (singleton per process)
# ------------------------------------------------------------
_store: VectorStore | None = None


def get_vector_store(settings: Settings | None = None) -> VectorStore:
    global _store
    if _store is not None:
        return _store
    settings = settings or get_settings()
    if settings.vector_backend == "pinecone":
        _store = PineconeStore(settings)
    else:
        _store = ChromaStore(settings)
    return _store
