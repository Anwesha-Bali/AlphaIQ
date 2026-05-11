import React, { useState, useEffect, useRef } from "react";
import { formatScore, truncateMiddle } from "../lib/format.jsx";

const DOC_TYPE_LABELS = {
  "10-K": "Annual",
  "10-Q": "Quarterly",
  "8-K": "Material event",
  earnings_call: "Earnings call",
  news: "News",
  research: "Research",
  other: "Document",
};

export function CitationCard({ number, citation, highlighted }) {
  const [expanded, setExpanded] = useState(false);
  const ref = useRef(null);

  // Scroll into view + flash when its inline marker is clicked.
  useEffect(() => {
    if (highlighted && ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "center" });
      setExpanded(true);
    }
  }, [highlighted]);

  const scorePct = Math.round(citation.score * 100);
  const scoreColor =
    scorePct >= 60
      ? "text-signal-400"
      : scorePct >= 35
      ? "text-risk-medium"
      : "text-bone-400";

  return (
    <div
      ref={ref}
      className={`group relative panel p-3 transition-all ${
        highlighted
          ? "border-signal-500/60 shadow-[0_0_0_2px_rgba(127,227,74,0.15)]"
          : "hover:border-ink-600"
      }`}
    >
      <div className="flex items-start gap-2.5">
        {/* Citation number badge */}
        <div className="flex-shrink-0 w-6 h-6 rounded flex items-center justify-center bg-signal-500/15 text-signal-400 border border-signal-500/30 font-mono text-[11px] font-medium">
          {number}
        </div>

        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {citation.company && (
              <span className="font-display text-[13px] text-bone-50 leading-none">
                {citation.company}
              </span>
            )}
            <span className="ticker-chip">
              {DOC_TYPE_LABELS[citation.doc_type] || citation.doc_type}
            </span>
            <span className={`font-mono text-[10px] ${scoreColor} ml-auto`}>
              {formatScore(citation.score)}
            </span>
          </div>

          {/* Source path */}
          <div className="font-mono text-[10.5px] text-bone-400/80 mb-2 truncate">
            {truncateMiddle(citation.source, 60)}
          </div>

          {/* Snippet */}
          <p
            className={`text-[12.5px] leading-relaxed text-bone-200 ${
              expanded ? "" : "line-clamp-3"
            }`}
          >
            {citation.snippet}
          </p>

          {citation.snippet.length > 200 && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="mt-1.5 text-[10.5px] font-mono uppercase tracking-wider text-bone-400 hover:text-signal-400 transition"
            >
              {expanded ? "Collapse" : "Expand"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
