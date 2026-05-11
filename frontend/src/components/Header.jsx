import React, { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Header({ onOpenUpload, onOpenInsights, onOpenCompare }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const tick = () => api.health().then(setHealth).catch(() => setHealth(null));
    tick();
    const id = setInterval(tick, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="relative z-10 border-b border-ink-800/80 bg-ink-950/80 backdrop-blur-xl">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <svg width="28" height="28" viewBox="0 0 28 28" className="text-signal-400">
              <path
                d="M4 22 L11 8 L17 18 L24 6"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="24" cy="6" r="2.5" fill="currentColor" />
            </svg>
          </div>
          <div className="leading-none">
            <div className="font-display text-[22px] tracking-tight text-bone-50">
              Alpha<span className="italic font-light">IQ</span>
            </div>
            <div className="font-mono text-[9.5px] tracking-[0.18em] uppercase text-bone-400 mt-0.5">
              Investment Research · v0.1
            </div>
          </div>
        </div>

        {/* Right cluster */}
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={onOpenCompare}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-bone-200 hover:text-bone-50 hover:bg-ink-800/80 transition"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M2 4h6M2 7h4M2 10h6M11 3v8M11 3l-2 2M11 3l2 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Compare
          </button>
          <button
            onClick={onOpenInsights}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-bone-200 hover:text-bone-50 hover:bg-ink-800/80 transition"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="2" y="2" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3"/>
              <path d="M4.5 9.5V7M7 9.5V5M9.5 9.5V8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
            </svg>
            Insights
          </button>
          <button
            onClick={onOpenUpload}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-medium bg-signal-500/15 text-signal-400 border border-signal-500/40 hover:bg-signal-500/25 hover:border-signal-500/70 transition"
          >
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
              <path d="M6.5 9.5V2M6.5 2L3 5.5M6.5 2L10 5.5M2 11h9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Ingest
          </button>

          {/* Status pill */}
          <div className="hidden md:flex items-center gap-2 pl-3 ml-1 border-l border-ink-700/60">
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                health?.status === "ok"
                  ? "bg-signal-400 animate-pulse-dot"
                  : "bg-risk-medium"
              }`}
            />
            <span className="font-mono text-[10px] uppercase tracking-wider text-bone-400">
              {health
                ? `${health.indexed_chunks.toLocaleString()} chunks · ${health.llm_provider}`
                : "offline"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
