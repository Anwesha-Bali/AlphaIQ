/**
 * AlphaIQ API client.
 *
 * In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).
 * In production, set VITE_API_BASE to point at your backend.
 */

const BASE = import.meta.env.VITE_API_BASE || "/api";

async function jsonOrThrow(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // ignore
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

export const api = {
  async health() {
    return jsonOrThrow(await fetch(`${BASE}/health`));
  },

  async query({ question, top_k = null, ticker = null }) {
    return jsonOrThrow(
      await fetch(`${BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k, ticker }),
      })
    );
  },

  /**
   * Stream answer tokens via Server-Sent Events.
   * onEvent receives parsed event objects:
   *   { type: "citations", citations: [...] }
   *   { type: "token", text: "..." }
   *   { type: "insufficient_context" }
   *   { type: "done" }
   *   { type: "error", message }
   */
  async queryStream({ question, top_k = null, ticker = null }, onEvent, signal) {
    const res = await fetch(`${BASE}/query/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k, ticker }),
      signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`Stream failed: ${res.status} ${res.statusText}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE frames are separated by \n\n
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        for (const line of frame.split("\n")) {
          if (line.startsWith("data: ")) {
            try {
              onEvent(JSON.parse(line.slice(6)));
            } catch {
              // ignore malformed line
            }
          }
        }
      }
    }
  },

  async upload({ file, company, ticker, doc_type, filing_date }) {
    const fd = new FormData();
    fd.append("file", file);
    if (company) fd.append("company", company);
    if (ticker) fd.append("ticker", ticker);
    if (doc_type) fd.append("doc_type", doc_type);
    if (filing_date) fd.append("filing_date", filing_date);
    return jsonOrThrow(
      await fetch(`${BASE}/upload`, { method: "POST", body: fd })
    );
  },

  async ingestUrl({ url, company, ticker, doc_type = "news" }) {
    return jsonOrThrow(
      await fetch(`${BASE}/ingest-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, company, ticker, doc_type }),
      })
    );
  },

  async insights({ ticker, company }) {
    return jsonOrThrow(
      await fetch(`${BASE}/insights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, company }),
      })
    );
  },

  async compare({ tickers, dimension }) {
    return jsonOrThrow(
      await fetch(`${BASE}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tickers, dimension }),
      })
    );
  },
};
