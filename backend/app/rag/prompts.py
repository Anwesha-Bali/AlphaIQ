"""
Prompt templates used by the RAG pipeline.

All prompts in one file so it's easy to audit how the LLM is being
instructed. Citation discipline is enforced in the system prompt.
"""
from __future__ import annotations

from app.rag.vector_store import SearchHit


def _format_context(hits: list[SearchHit]) -> str:
    """Render retrieved chunks as numbered citation blocks."""
    blocks = []
    for i, h in enumerate(hits, start=1):
        meta = h.metadata or {}
        header_parts = [f"[{i}]"]
        if meta.get("company"):
            header_parts.append(str(meta["company"]))
        if meta.get("ticker"):
            header_parts.append(f"({meta['ticker']})")
        if meta.get("doc_type"):
            header_parts.append(str(meta["doc_type"]))
        if meta.get("filing_date"):
            header_parts.append(str(meta["filing_date"]))
        header_parts.append(f"score={h.score:.2f}")
        header = " | ".join(header_parts)
        source = meta.get("source", "unknown")
        blocks.append(f"{header}\nSource: {source}\n---\n{h.text}")
    return "\n\n".join(blocks)


# ============================================================
# QA — answer a question grounded in retrieved chunks
# ============================================================

QA_SYSTEM = """\
You are AlphaIQ, an AI investment research assistant for financial analysts.

Strict rules:
1. Use ONLY the provided context blocks to answer. Do not introduce facts,
   numbers, or quotations that do not appear in the context.
2. Every non-trivial claim must be followed by an inline citation in square
   brackets matching the context block number, e.g. "Revenue grew 8% YoY [2]".
   You may cite multiple sources like [1][3].
3. If the context is insufficient to answer, say exactly:
   "Not enough context to answer confidently." and then briefly state what
   additional documents would help.
4. Be concise. Lead with the answer, then 2-4 supporting sentences. Use a
   short bulleted list only if the question explicitly asks to enumerate.
5. Never invent ticker symbols, dollar figures, dates, or executive names.
6. Maintain a measured, analytical tone — no hype, no advice to buy or sell.
"""

QA_USER_TMPL = """\
QUESTION:
{question}

CONTEXT BLOCKS:
{context}

Answer the question following the rules above. Cite using the numeric
identifiers shown in each context block header.\
"""


def build_qa_messages(question: str, hits: list[SearchHit]) -> list[dict]:
    return [
        {"role": "system", "content": QA_SYSTEM},
        {
            "role": "user",
            "content": QA_USER_TMPL.format(
                question=question.strip(),
                context=_format_context(hits),
            ),
        },
    ]


# ============================================================
# Structured insights — JSON-only output
# ============================================================

INSIGHTS_SYSTEM = """\
You are AlphaIQ, an AI investment research assistant. Produce a structured
analyst briefing about a single company, grounded ONLY in the provided
context blocks.

Output requirements:
- Respond with valid JSON only. No markdown, no commentary, no fences.
- JSON shape:
  {
    "summary": str,
    "revenue_trends": str,
    "risk_factors": [{"title": str, "description": str, "severity": "low"|"medium"|"high"}, ...],
    "competitive_positioning": str,
    "management_commentary": str,
    "overall_risk": "low"|"medium"|"high"
  }
- 3-6 risk factors. Severity reflects materiality to the investment case.
- If a section cannot be supported by the context, set it to "Not enough
  context." Do not invent numbers or quotations.
- Be specific and analyst-grade. No hedging filler.
"""

INSIGHTS_USER_TMPL = """\
COMPANY: {company_label}

CONTEXT BLOCKS:
{context}

Produce the JSON briefing per the system instructions.\
"""


def build_insights_messages(
    ticker: str, company: str | None, hits: list[SearchHit]
) -> list[dict]:
    label = f"{company} ({ticker})" if company else ticker
    return [
        {"role": "system", "content": INSIGHTS_SYSTEM},
        {
            "role": "user",
            "content": INSIGHTS_USER_TMPL.format(
                company_label=label,
                context=_format_context(hits),
            ),
        },
    ]


# ============================================================
# Comparison — multi-company analysis
# ============================================================

COMPARE_SYSTEM = """\
You are AlphaIQ, an AI investment research assistant. Compare multiple
companies along a specified dimension, grounded ONLY in the provided
context blocks.

Rules:
- Use ONLY the context. Inline-cite with [n].
- Structure: one short intro paragraph, then a comparison per company,
  then a one-line takeaway. Keep it tight — analyst memo, not essay.
- If the context lacks data for any company, say so explicitly.
"""

COMPARE_USER_TMPL = """\
COMPANIES: {tickers}
DIMENSION: {dimension}

CONTEXT BLOCKS:
{context}

Produce the comparison memo per the system instructions.\
"""


def build_compare_messages(
    tickers: list[str], dimension: str, hits: list[SearchHit]
) -> list[dict]:
    return [
        {"role": "system", "content": COMPARE_SYSTEM},
        {
            "role": "user",
            "content": COMPARE_USER_TMPL.format(
                tickers=", ".join(tickers),
                dimension=dimension,
                context=_format_context(hits),
            ),
        },
    ]
