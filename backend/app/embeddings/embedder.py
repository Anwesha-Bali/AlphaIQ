"""
Embedding providers.

Defines an abstract `Embedder` interface and concrete implementations
for OpenAI and a deterministic mock (for offline development & tests).
The rest of the app talks only to the interface.
"""
from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import Sequence

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class Embedder(ABC):
    """Abstract embedding model."""

    dim: int

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input text."""

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


# ------------------------------------------------------------
# OpenAI
# ------------------------------------------------------------
class OpenAIEmbedder(Embedder):
    """Calls the OpenAI embeddings endpoint in batches."""

    BATCH_SIZE = 100  # OpenAI accepts up to ~2048 but smaller batches are kinder

    def __init__(self, settings: Settings):
        from openai import OpenAI  # local import keeps mock-only installs lean

        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for the OpenAI embedder. "
                "Set it in .env or switch LLM_PROVIDER=mock."
            )
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model
        self.dim = settings.embedding_dim
        log.info("OpenAIEmbedder ready (model=%s, dim=%d)", self._model, self.dim)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        for i in range(0, len(texts), self.BATCH_SIZE):
            batch = list(texts[i : i + self.BATCH_SIZE])
            resp = self._client.embeddings.create(model=self._model, input=batch)
            out.extend(d.embedding for d in resp.data)
        return out


# ------------------------------------------------------------
# Mock — deterministic, no network. Useful for local dev / CI.
# ------------------------------------------------------------
class MockEmbedder(Embedder):
    """Hash-bucketed embeddings. Same text -> same vector. Not for production retrieval quality, but lets the whole pipeline run offline."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        log.warning("Using MockEmbedder (dim=%d). Retrieval quality will be low.", dim)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def _vec(self, text: str) -> list[float]:
        # Hash tokens into vector buckets, then L2-normalize.
        v = [0.0] * self.dim
        for token in text.lower().split():
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            idx = h % self.dim
            v[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]


# ------------------------------------------------------------
# Factory
# ------------------------------------------------------------
def get_embedder(settings: Settings | None = None) -> Embedder:
    settings = settings or get_settings()
    if settings.llm_provider == "mock" or not settings.openai_api_key:
        return MockEmbedder()
    return OpenAIEmbedder(settings)
