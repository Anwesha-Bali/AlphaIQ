import React, { useState } from "react";
import { Modal } from "./Modal.jsx";
import { CitationCard } from "./CitationCard.jsx";
import { api } from "../api/client";

export default function InsightsModal({ open, onClose }) {
  const [ticker, setTicker] = useState("");
  const [company, setCompany] = useState("");
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function run() {
    setError(null);
    setBusy(true);
    setData(null);
    try {
      const result = await api.insights({
        ticker,
        company: company || null,
      });
      setData(result);
    } catch (e) {
      setError(e.message || "Failed to generate insights.");
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
      title="Company insights"
      subtitle="Structured analyst briefing built from indexed filings: summary, revenue trends, risks, and outlook."
      maxWidth="max-w-3xl"
    >
      {/* Input row */}
      <div className="flex gap-2 mb-5">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="TICKER"
          maxLength={10}
          className="w-28 bg-ink-800/60 border border-ink-700/60 rounded px-2 py-2 text-[13px] font-mono tracking-wider text-bone-100 placeholder:text-bone-400/40 outline-none focus:border-signal-500/40 transition"
        />
        <input
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Company name (optional)"
          className="flex-1 bg-ink-800/60 border border-ink-700/60 rounded px-3 py-2 text-[13px] text-bone-100 placeholder:text-bone-400/40 outline-none focus:border-signal-500/40 transition"
        />
        <button
          onClick={run}
          disabled={busy || !ticker.trim()}
          className="px-4 rounded-md text-xs font-medium bg-signal-500 text-ink-950 hover:bg-signal-400 disabled:bg-ink-700 disabled:text-bone-400 disabled:cursor-not-allowed transition"
        >
          {busy ? "Analyzing…" : "Generate"}
        </button>
      </div>

      {error && (
        <div className="text-[12px] text-risk-high bg-risk-high/10 border border-risk-high/30 rounded px-3 py-2 mb-3">
          {error}
        </div>
      )}

      {busy && <InsightsSkeleton />}

      {data && (
        <div className="animate-slide-up">
          {/* Header band */}
          <div className="flex items-center gap-3 pb-4 border-b border-ink-800/80 mb-4">
            <div>
              <div className="font-display text-[24px] text-bone-50 leading-none">
                {data.company || data.ticker}
              </div>
              <div className="font-mono text-[11px] tracking-wider text-bone-400 mt-1">
                {data.ticker}
              </div>
            </div>
            <div className="ml-auto">
              <RiskPill severity={data.overall_risk} large />
            </div>
          </div>

          <Section title="Summary" body={data.summary} />
          <Section title="Revenue trends" body={data.revenue_trends} />

          <div className="mb-5">
            <SectionLabel>Risk factors</SectionLabel>
            <div className="space-y-2">
              {data.risk_factors.map((r, i) => (
                <div
                  key={i}
                  className="panel p-3 flex items-start gap-3 border-ink-700/60"
                >
                  <RiskPill severity={r.severity} />
                  <div>
                    <div className="font-display text-[14px] text-bone-50 mb-0.5">
                      {r.title}
                    </div>
                    <p className="text-[13px] text-bone-300 leading-relaxed">
                      {r.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Section
            title="Competitive positioning"
            body={data.competitive_positioning}
          />
          <Section
            title="Management commentary"
            body={data.management_commentary}
          />

          {/* Sources */}
          {data.citations?.length > 0 && (
            <div>
              <SectionLabel>Sources · {data.citations.length}</SectionLabel>
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

function SectionLabel({ children }) {
  return (
    <div className="font-mono text-[10px] tracking-[0.2em] uppercase text-bone-400 mb-2">
      {children}
    </div>
  );
}

function Section({ title, body }) {
  return (
    <div className="mb-5">
      <SectionLabel>{title}</SectionLabel>
      <p className="text-[13.5px] text-bone-200 leading-relaxed whitespace-pre-wrap">
        {body || "—"}
      </p>
    </div>
  );
}

function RiskPill({ severity, large = false }) {
  const cls = `severity-${severity}`;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono uppercase tracking-wider ${cls} ${
        large ? "px-3 py-1 text-[10.5px]" : "px-2 py-0.5 text-[10px]"
      }`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {severity} risk
    </span>
  );
}

function InsightsSkeleton() {
  return (
    <div className="space-y-3">
      <div className="shimmer h-6 rounded w-2/3" />
      <div className="shimmer h-4 rounded w-full" />
      <div className="shimmer h-4 rounded w-5/6" />
      <div className="shimmer h-20 rounded w-full mt-4" />
      <div className="shimmer h-20 rounded w-full" />
    </div>
  );
}
