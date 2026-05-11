import React, { useState } from "react";
import { Modal } from "./Modal.jsx";
import { CitationCard } from "./CitationCard.jsx";
import { api } from "../api/client";
import { renderWithCitations } from "../lib/format.jsx";

export default function CompareModal({ open, onClose }) {
  const [tickersText, setTickersText] = useState("");
  const [dimension, setDimension] = useState(
    "risks, margins, growth, and competitive moat"
  );
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function run() {
    setError(null);
    setBusy(true);
    setData(null);
    try {
      const tickers = tickersText
        .split(/[,\s]+/)
        .map((t) => t.trim().toUpperCase())
        .filter(Boolean);
      if (tickers.length < 2) throw new Error("Enter at least two tickers.");
      const result = await api.compare({ tickers, dimension });
      setData(result);
    } catch (e) {
      setError(e.message || "Comparison failed.");
    } finally {
      setBusy(false);
    }
  }

  function handleClose() {
    setData(null);
    setError(null);
    onClose();
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Compare companies"
      subtitle="Side-by-side memo across multiple tickers along a dimension you choose."
      maxWidth="max-w-3xl"
    >
      <div className="space-y-3 mb-4">
        <label className="block">
          <span className="block font-mono text-[10px] uppercase tracking-wider text-bone-400 mb-1">
            Tickers (comma or space separated · 2–5)
          </span>
          <input
            value={tickersText}
            onChange={(e) => setTickersText(e.target.value)}
            placeholder="AAPL, MSFT, GOOGL"
            className="w-full bg-ink-800/60 border border-ink-700/60 rounded px-3 py-2 text-[13px] font-mono tracking-wider text-bone-100 placeholder:text-bone-400/40 outline-none focus:border-signal-500/40 transition"
          />
        </label>
        <label className="block">
          <span className="block font-mono text-[10px] uppercase tracking-wider text-bone-400 mb-1">
            Dimension
          </span>
          <input
            value={dimension}
            onChange={(e) => setDimension(e.target.value)}
            className="w-full bg-ink-800/60 border border-ink-700/60 rounded px-3 py-2 text-[13px] text-bone-100 outline-none focus:border-signal-500/40 transition"
          />
        </label>
        <button
          onClick={run}
          disabled={busy || !tickersText.trim()}
          className="px-4 py-2 rounded-md text-xs font-medium bg-signal-500 text-ink-950 hover:bg-signal-400 disabled:bg-ink-700 disabled:text-bone-400 disabled:cursor-not-allowed transition"
        >
          {busy ? "Analyzing…" : "Generate memo"}
        </button>
      </div>

      {error && (
        <div className="text-[12px] text-risk-high bg-risk-high/10 border border-risk-high/30 rounded px-3 py-2 mb-3">
          {error}
        </div>
      )}

      {data && (
        <div className="animate-slide-up pt-4 border-t border-ink-800/80">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            {data.tickers.map((t) => (
              <span key={t} className="ticker-chip text-[11px]">
                {t}
              </span>
            ))}
          </div>
          <div className="font-sans text-[14px] leading-[1.75] text-bone-100 whitespace-pre-wrap mb-5">
            {renderWithCitations(data.analysis)}
          </div>
          {data.citations?.length > 0 && (
            <div>
              <div className="font-mono text-[10px] tracking-[0.2em] uppercase text-bone-400 mb-2">
                Sources · {data.citations.length}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {data.citations.map((c, i) => (
                  <CitationCard key={c.chunk_id} number={i + 1} citation={c} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
