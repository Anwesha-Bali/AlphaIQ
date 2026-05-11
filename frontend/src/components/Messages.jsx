import React from "react";
import { renderWithCitations } from "../lib/format.jsx";
import { CitationCard } from "./CitationCard.jsx";

export function UserMessage({ text }) {
  return (
    <div className="animate-slide-up">
      <div className="flex items-baseline gap-3 mb-1.5">
        <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-bone-400">
          You
        </span>
        <span className="h-px flex-1 bg-ink-800/60" />
      </div>
      <div className="font-display text-[19px] leading-relaxed text-bone-50 italic font-light">
        {text}
      </div>
    </div>
  );
}

export function AssistantMessage({
  text,
  citations = [],
  insufficient = false,
  isStreaming = false,
  latency_ms = null,
  highlightedCitation,
  onCitationClick,
}) {
  return (
    <div className="animate-slide-up">
      <div className="flex items-baseline gap-3 mb-1.5">
        <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-signal-400">
          AlphaIQ
        </span>
        <span className="h-px flex-1 bg-ink-800/60" />
        {latency_ms !== null && !isStreaming && (
          <span className="font-mono text-[9.5px] tracking-wider uppercase text-bone-400/70">
            {latency_ms} ms
          </span>
        )}
      </div>

      {insufficient ? (
        <div className="panel p-4 border-risk-medium/30 bg-risk-medium/5">
          <div className="flex items-start gap-3">
            <div className="text-risk-medium mt-0.5">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 1l7 13H1L8 1z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
                <path d="M8 6v3M8 11.5v.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              </svg>
            </div>
            <div>
              <div className="font-display text-[15px] text-bone-100 mb-1">
                Not enough context
              </div>
              <p className="text-[13.5px] text-bone-300 leading-relaxed">
                {text || "Upload relevant filings or news for this question, then ask again."}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="font-sans text-[15.5px] leading-[1.75] text-bone-100 whitespace-pre-wrap">
            {renderWithCitations(text, onCitationClick)}
            {isStreaming && (
              <span className="inline-block w-[7px] h-[16px] ml-0.5 bg-signal-400 animate-pulse-dot align-middle" />
            )}
          </div>

          {/* Citations panel */}
          {citations.length > 0 && (
            <div className="mt-5">
              <div className="font-mono text-[10px] tracking-[0.2em] uppercase text-bone-400 mb-2.5">
                Sources · {citations.length}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
                {citations.map((c, i) => (
                  <CitationCard
                    key={c.chunk_id}
                    number={i + 1}
                    citation={c}
                    highlighted={highlightedCitation === i + 1}
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function ThinkingMessage() {
  return (
    <div className="animate-fade-in">
      <div className="flex items-baseline gap-3 mb-1.5">
        <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-signal-400">
          AlphaIQ
        </span>
        <span className="h-px flex-1 bg-ink-800/60" />
      </div>
      <div className="flex items-center gap-2 text-bone-300">
        <span className="inline-flex gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-signal-400 animate-pulse-dot" />
          <span className="w-1.5 h-1.5 rounded-full bg-signal-400 animate-pulse-dot" style={{ animationDelay: "0.2s" }} />
          <span className="w-1.5 h-1.5 rounded-full bg-signal-400 animate-pulse-dot" style={{ animationDelay: "0.4s" }} />
        </span>
        <span className="font-mono text-[11px] tracking-wider uppercase text-bone-400">
          Retrieving · reasoning
        </span>
      </div>
    </div>
  );
}
