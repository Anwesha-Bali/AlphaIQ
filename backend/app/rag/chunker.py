"""
Token-aware text chunking.

We aim for ~chunk_size tokens with ~overlap tokens of carry-over, but
break on sentence/paragraph boundaries when possible so retrieval
returns semantically coherent passages.

Token counting uses `tiktoken` (cl100k_base) when available; we fall
back to a 4-char-per-token heuristic so this module works even when
the LLM provider is `mock` and we never installed tiktoken.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    import tiktoken

    _ENC = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_ENC.encode(text))

except Exception:  # pragma: no cover
    log.warning("tiktoken unavailable; using char-based token estimate")

    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)


# Split on paragraph, then sentence boundaries.
_PARA_RE = re.compile(r"\n{2,}")
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"'\[])")


@dataclass
class Chunk:
    text: str
    index: int  # ordinal within the doc
    token_count: int


def _split_sentences(paragraph: str) -> list[str]:
    paragraph = paragraph.strip()
    if not paragraph:
        return []
    sents = _SENT_RE.split(paragraph)
    return [s.strip() for s in sents if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[Chunk]:
    """Greedy token-budget packer with sentence-level granularity.

    Walks sentences in order, accumulating into the current chunk until
    adding the next sentence would exceed `chunk_size`. On flush, the
    last ~`overlap` tokens worth of sentences carry into the next chunk.
    """
    if not text or not text.strip():
        return []

    # Build a flat list of (sentence, tokens) preserving order.
    sentences: list[tuple[str, int]] = []
    for para in _PARA_RE.split(text):
        for s in _split_sentences(para):
            sentences.append((s, count_tokens(s)))

    chunks: list[Chunk] = []
    current: list[tuple[str, int]] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if not current:
            return
        body = " ".join(s for s, _ in current)
        chunks.append(Chunk(text=body, index=len(chunks), token_count=current_tokens))
        # Build overlap tail.
        tail: list[tuple[str, int]] = []
        tail_tokens = 0
        for sent in reversed(current):
            if tail_tokens + sent[1] > overlap:
                break
            tail.insert(0, sent)
            tail_tokens += sent[1]
        current = tail
        current_tokens = tail_tokens

    for sent, tok in sentences:
        # An individual sentence longer than chunk_size — emit it on its own.
        if tok > chunk_size:
            flush()
            chunks.append(Chunk(text=sent, index=len(chunks), token_count=tok))
            current, current_tokens = [], 0
            continue
        if current_tokens + tok > chunk_size:
            flush()
        current.append((sent, tok))
        current_tokens += tok

    flush()
    return chunks
