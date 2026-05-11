"""
Document loaders.

Each loader returns plain text. Higher layers handle chunking & metadata.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from app.core.logging import get_logger

log = get_logger(__name__)


# ------------------------------------------------------------
# PDF
# ------------------------------------------------------------
def load_pdf(content: bytes) -> str:
    """Extract text from a PDF byte stream using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # pragma: no cover
            log.warning("PDF page %d extraction failed: %s", i, e)
            text = ""
        pages.append(text)
    return "\n\n".join(pages)


# ------------------------------------------------------------
# Plain text
# ------------------------------------------------------------
def load_text(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


# ------------------------------------------------------------
# URL / HTML
# ------------------------------------------------------------
def load_url(url: str, timeout: float = 20.0) -> str:
    """Fetch a URL and return readable text. Strips scripts, styles, nav."""
    import httpx
    from bs4 import BeautifulSoup

    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url, headers={"User-Agent": "AlphaIQ/1.0"})
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if "pdf" in ctype.lower():
            return load_pdf(resp.content)
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form"]):
        tag.decompose()
    text = soup.get_text("\n")
    # Collapse runs of blank lines.
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


# ------------------------------------------------------------
# Dispatcher
# ------------------------------------------------------------
def load_file(filename: str, content: bytes) -> str:
    """Pick a loader based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return load_pdf(content)
    if ext in (".txt", ".md", ".html", ".htm", ".csv"):
        return load_text(content)
    # Unknown extension — try text first, fall back to PDF.
    try:
        return load_text(content)
    except Exception:  # pragma: no cover
        return load_pdf(content)
