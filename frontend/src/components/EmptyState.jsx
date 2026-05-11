import React from "react";

export default function EmptyState({ onOpenUpload }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 animate-fade-in">
      <div className="font-mono text-[10.5px] tracking-[0.3em] uppercase text-signal-400 mb-3">
        Grounded · Cited · Auditable
      </div>
      <h1 className="font-display text-[44px] sm:text-[58px] leading-[0.95] tracking-tight text-bone-50 max-w-2xl">
        Investment research,{" "}
        <span className="italic font-light text-bone-300">answered with</span>{" "}
        <span className="text-signal-400 italic font-light">receipts.</span>
      </h1>
      <p className="text-[14px] text-bone-300 max-w-xl mt-5 leading-relaxed">
        AlphaIQ retrieves passages from your indexed filings, transcripts, and news,
        then answers with inline citations you can click to verify. Nothing is
        invented — every claim points back to a source.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-2 mt-8">
        <button
          onClick={onOpenUpload}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-medium bg-signal-500 text-ink-950 hover:bg-signal-400 transition"
        >
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
            <path d="M6.5 9.5V2M6.5 2L3 5.5M6.5 2L10 5.5M2 11h9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Ingest your first document
        </button>
        <span className="text-bone-400 text-[12px]">or ask a question below</span>
      </div>

      {/* Capability strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-12 max-w-3xl w-full">
        {[
          ["RAG", "Vector retrieval over filings"],
          ["Citations", "Every claim, sourceable"],
          ["JSON insights", "Structured briefings"],
          ["Streaming", "Token-by-token answers"],
        ].map(([k, v]) => (
          <div
            key={k}
            className="panel p-3 text-left hover:border-ink-600 transition"
          >
            <div className="font-mono text-[10px] uppercase tracking-wider text-signal-400 mb-1">
              {k}
            </div>
            <div className="text-[12px] text-bone-300 leading-relaxed">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
