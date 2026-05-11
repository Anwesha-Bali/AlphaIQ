# AlphaIQ — AI Investment Research Platform

> Citation-grounded RAG over SEC filings, earnings calls, and news. Ask investment questions, get structured insights, compare companies side-by-side. Built like a hedge-fund internal tool, not a demo.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688.svg)]()
[![React](https://img.shields.io/badge/react-18.3-61dafb.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## What it does

AlphaIQ is a full-stack retrieval-augmented generation (RAG) platform for financial research analysts:

- **Ingest** PDFs, plain-text filings, and live URLs into a vector store
- **Ask** questions in natural language ("What are Tesla's biggest risks?", "Compare margins between Apple and Microsoft")
- **Get** answers grounded in retrieved chunks, with inline `[1]` `[2]` citations that link to expandable source cards
- **Generate** structured company reports (summary, revenue trends, risk factors with severity scoring, competitive positioning, management commentary)
- **Compare** any set of companies along any dimension you specify
- **Stream** responses token-by-token over Server-Sent Events for that ChatGPT-feel

Every answer ships with its receipts. If retrieval comes back empty, the system says "Not enough context" instead of inventing numbers.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Frontend (Vite + React)                  │
│   Chat composer → /api/query/stream → SSE → inline citations     │
│   Insights modal · Compare modal · Ingest modal · Source cards   │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼  (REST + SSE)
┌──────────────────────────────────────────────────────────────────┐
│                       Backend (FastAPI)                          │
│                                                                  │
│   ┌────────────┐   ┌──────────────┐   ┌────────────────────┐     │
│   │ Ingestion  │──▶│  Chunker     │──▶│ Embedder           │     │
│   │ (PDF/URL/  │   │ (tiktoken,   │   │ (OpenAI / mock)    │     │
│   │  text)     │   │  overlap)    │   │                    │     │
│   └────────────┘   └──────────────┘   └─────────┬──────────┘     │
│                                                 ▼                │
│                              ┌──────────────────────────┐        │
│                              │  Vector Store            │        │
│                              │  (Chroma / Pinecone)     │        │
│                              └──────────┬───────────────┘        │
│                                         │                        │
│   ┌─────────────────────────────────────▼──────────────────┐     │
│   │            RAG Pipeline                                │     │
│   │  retrieve → rerank by score → build prompt with        │     │
│   │  numbered context → LLM (OpenAI / Anthropic / mock)    │     │
│   │  → enforce citations → return QueryResponse            │     │
│   └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **Provider-agnostic abstractions.** `LLM`, `Embedder`, and `VectorStore` are ABCs. Swap OpenAI → Anthropic, Chroma → Pinecone, or run fully offline with `mock` providers, all via `.env`. No code changes.
- **Citation discipline lives in the prompt, not as wishful thinking.** The QA system prompt has six numbered rules including an "insufficient context" fallback. Below a configurable similarity threshold, the pipeline refuses to answer rather than guess.
- **Structured insights use JSON mode.** The insights endpoint runs four probe queries to cast a wide retrieval net, then asks the LLM for strict JSON (parsed fence-tolerantly).
- **Streaming is real.** SSE frames flow from the LLM through FastAPI through nginx (with `proxy_buffering off`) to React, where citation cards appear before the first token.
- **Mock providers ship by default.** You can run the entire stack with zero API keys. Set `LLM_PROVIDER=openai` when you're ready.

---

## Project layout

```
alphaIQ/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory
│   │   ├── api/
│   │   │   ├── routes.py            # /health /upload /ingest-url /query /query/stream /insights /compare
│   │   │   └── deps.py              # Singleton providers
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings (env-driven)
│   │   │   └── logging.py
│   │   ├── models/schemas.py        # All request/response Pydantic models
│   │   ├── embeddings/embedder.py   # OpenAIEmbedder · MockEmbedder
│   │   ├── rag/
│   │   │   ├── loaders.py           # PDF · URL · text loaders
│   │   │   ├── chunker.py           # Token-aware sentence-boundary chunker
│   │   │   ├── vector_store.py      # ChromaStore · PineconeStore
│   │   │   ├── prompts.py           # QA · INSIGHTS · COMPARE system prompts
│   │   │   └── pipeline.py          # RagPipeline.{retrieve,answer,answer_stream,insights,compare}
│   │   └── services/
│   │       ├── ingestion.py         # File/URL → chunks → embeddings → store
│   │       └── llm.py               # OpenAILLM · AnthropicLLM · MockLLM
│   ├── scripts/
│   │   ├── ingest_samples.py        # Bulk-ingest data/sample/*.txt
│   │   └── smoke_test.py            # End-to-end pipeline test (no API keys needed)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Top-level state, message stream wiring
│   │   ├── api/client.js            # REST + SSE client
│   │   ├── components/
│   │   │   ├── Header.jsx           # Brand, health pill, modal triggers
│   │   │   ├── Composer.jsx         # Textarea, ticker filter, stream toggle
│   │   │   ├── Messages.jsx         # User / assistant / streaming bubbles
│   │   │   ├── CitationCard.jsx     # Expandable source card with scroll-to-highlight
│   │   │   ├── IngestModal.jsx
│   │   │   ├── InsightsModal.jsx
│   │   │   ├── CompareModal.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   └── Modal.jsx
│   │   ├── lib/format.jsx           # Inline-citation renderer
│   │   ├── index.css                # Tailwind + custom palette
│   │   ├── main.jsx
│   │   └── App.jsx
│   ├── tailwind.config.js           # ink-950..bone-50 palette, signal-green accent
│   ├── vite.config.js               # Dev proxy → backend
│   ├── Dockerfile                   # Multi-stage → nginx
│   ├── nginx.conf                   # SPA fallback + SSE-friendly proxy
│   └── package.json
├── data/
│   └── sample/
│       ├── AAPL_10K_2024_excerpt.txt
│       └── TSLA_10K_2024_excerpt.txt
├── docker/
│   └── docker-compose.yml
└── README.md
```

---

## Quick start (offline, no API keys)

The fastest way to see it working:

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # defaults to mock providers

# 2. Smoke-test the whole pipeline (no server needed)
python scripts/smoke_test.py

# 3. Ingest sample filings and start the API
python scripts/ingest_samples.py
uvicorn app.main:app --reload --port 8000

# 4. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev                            # http://localhost:5173
```

Open `http://localhost:5173`, click the **Ingest** button to add more filings or URLs, or just start asking questions.

---

## Going to production

Edit `.env`:

```bash
# Use real embeddings + LLM
LLM_PROVIDER=openai                    # or "anthropic"
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini               # or "gpt-4o"
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536                     # MUST match the model above

# Or scale out the vector store
VECTOR_BACKEND=pinecone
PINECONE_API_KEY=...
PINECONE_INDEX=alphaiq-prod

# Retrieval knobs
RETRIEVAL_TOP_K=8
RETRIEVAL_MIN_SCORE=0.25               # raise to be stricter about citations
```

> **Important:** `EMBEDDING_DIM` must match your embedding model's actual dimension. Mismatches cause silent retrieval failures.

---

## Docker

```bash
cd docker
docker compose up --build
# Backend  → http://localhost:8000/api/health
# Frontend → http://localhost:8080
```

The compose file mounts `../data` so your vector store persists across container restarts.

---

## API reference

| Endpoint                  | Method | Purpose                                                 |
|---------------------------|--------|---------------------------------------------------------|
| `/api/health`             | GET    | Service status + indexed chunk count                    |
| `/api/upload`             | POST   | Multipart file upload (PDF / TXT)                       |
| `/api/ingest-url`         | POST   | Fetch and ingest a URL (news, press release, etc.)      |
| `/api/query`              | POST   | RAG question → answer + citations (blocking)            |
| `/api/query/stream`       | POST   | Same, but Server-Sent Events token stream               |
| `/api/insights`           | POST   | Structured `CompanyInsights` JSON for one ticker        |
| `/api/compare`            | POST   | Multi-ticker comparison memo along a chosen dimension   |

Example `curl`:

```bash
# Ask a question
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are Tesla'\''s biggest risks?", "top_k": 5}'

# Generate structured insights
curl -X POST http://localhost:8000/api/insights \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "company": "Apple Inc."}'

# Compare companies
curl -X POST http://localhost:8000/api/compare \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "TSLA"], "dimension": "operating margins"}'
```

Full OpenAPI spec available at `http://localhost:8000/docs`.

---

## Example queries to try

After running `python scripts/ingest_samples.py`:

- *"What are Tesla's biggest risk factors?"*
- *"Summarize Apple's revenue trends and what's driving them"*
- *"How do Apple's and Tesla's operating margins compare?"*  → use the Compare modal
- *"Give me a full report on AAPL"*  → use the Insights modal
- *"What is management saying about the outlook?"* with ticker filter set to `AAPL`

---

## Configuration reference

All settings live in `.env`. See `backend/.env.example` for the full annotated list.

| Variable                  | Default            | Notes                                                         |
|---------------------------|--------------------|---------------------------------------------------------------|
| `LLM_PROVIDER`            | `mock`             | `openai` · `anthropic` · `mock`                               |
| `OPENAI_API_KEY`          | —                  | Required if `LLM_PROVIDER=openai`                             |
| `ANTHROPIC_API_KEY`       | —                  | Required if `LLM_PROVIDER=anthropic`                          |
| `OPENAI_MODEL`            | `gpt-4o-mini`      | Any chat-completion model                                     |
| `ANTHROPIC_MODEL`         | `claude-sonnet-4-5`| Any Claude model                                              |
| `EMBEDDING_PROVIDER`      | `mock`             | `openai` · `mock`                                             |
| `EMBEDDING_MODEL`         | `text-embedding-3-small` | OpenAI embedding model                                  |
| `EMBEDDING_DIM`           | `1536`             | **Must match** the embedding model                            |
| `VECTOR_BACKEND`          | `chroma`           | `chroma` · `pinecone`                                         |
| `CHROMA_PERSIST_DIR`      | `./data/chroma`    | Local Chroma path                                             |
| `PINECONE_API_KEY`        | —                  | Required if `VECTOR_BACKEND=pinecone`                         |
| `PINECONE_INDEX`          | `alphaiq`          | Index name (serverless)                                       |
| `CHUNK_SIZE`              | `700`              | Target tokens per chunk                                       |
| `CHUNK_OVERLAP`           | `120`              | Overlap tokens between adjacent chunks                        |
| `RETRIEVAL_TOP_K`         | `6`                | Chunks returned per query                                     |
| `RETRIEVAL_MIN_SCORE`     | `0.15`             | Below this cosine score, "insufficient context"               |
| `CORS_ORIGINS`            | `http://localhost:5173,http://localhost:8080` | Comma-separated     |

---

## What's intentionally not here

This is an MVP designed to be extended, not feature-complete. Things you might want to add next:

- **Auth.** Wire JWT + per-user vector namespaces if you go multi-tenant. The pipeline already accepts a `ticker` filter — extend to `user_id`.
- **Reranking.** Add a cross-encoder reranker (e.g., Cohere rerank) between retrieval and prompt construction.
- **Evals.** A `tests/evals/` harness with golden Q/A pairs would catch regressions when you swap models.
- **LangGraph workflow.** The current pipeline is procedural for clarity. For complex agents (multi-hop questions, tool-using research bots), refactor `RagPipeline` into a LangGraph state machine.
- **Ingestion queue.** For thousands of documents, move ingestion behind a queue (Celery / RQ) and stream progress over WebSocket.

---

## License

MIT.
