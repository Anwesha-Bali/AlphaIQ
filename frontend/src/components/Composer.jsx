import React, { useRef, useState, useEffect } from "react";

const SUGGESTIONS = [
  "What are Tesla's biggest risks?",
  "Summarize revenue growth trends for Apple",
  "Compare margins across last 3 years",
  "What did management say about AI investment?",
];

export default function Composer({ onSend, isBusy, ticker, onTickerChange }) {
  const [text, setText] = useState("");
  const [streamMode, setStreamMode] = useState(true);
  const taRef = useRef(null);

  // Auto-resize textarea up to 6 lines.
  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }, [text]);

  function submit() {
    const q = text.trim();
    if (!q || isBusy) return;
    onSend({ question: q, ticker: ticker || null, stream: streamMode });
    setText("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="w-full">
      {/* Suggestion chips — only show when input is empty */}
      {!text && !isBusy && (
        <div className="flex flex-wrap gap-2 mb-3 animate-fade-in">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setText(s)}
              className="text-[11.5px] px-2.5 py-1 rounded-full border border-ink-700/70 text-bone-300 hover:text-bone-50 hover:border-bone-300/40 hover:bg-ink-800/40 transition"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="panel p-3 transition-all focus-within:border-signal-500/40 focus-within:shadow-[0_0_0_4px_rgba(127,227,74,0.08)]">
        <textarea
          ref={taRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask about a company, filing, or trend…"
          disabled={isBusy}
          className="w-full bg-transparent resize-none outline-none placeholder:text-bone-400/50 text-bone-50 text-[15px] leading-relaxed font-sans"
        />

        <div className="flex items-center justify-between mt-2 pt-2 border-t border-ink-800/80">
          <div className="flex items-center gap-2">
            {/* Ticker filter */}
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-[10px] tracking-wider uppercase text-bone-400">
                Filter
              </span>
              <input
                value={ticker}
                onChange={(e) => onTickerChange(e.target.value.toUpperCase())}
                placeholder="TICKER"
                className="w-20 bg-ink-800/60 border border-ink-700/60 rounded px-2 py-1 text-[11px] font-mono tracking-wider text-bone-100 placeholder:text-bone-400/40 outline-none focus:border-signal-500/40 transition"
                maxLength={10}
              />
            </div>

            {/* Stream toggle */}
            <button
              onClick={() => setStreamMode((s) => !s)}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[10.5px] font-mono uppercase tracking-wider transition ${
                streamMode
                  ? "text-signal-400 bg-signal-500/10 border border-signal-500/30"
                  : "text-bone-400 bg-ink-800/40 border border-ink-700/60"
              }`}
              title="Toggle token streaming"
            >
              <span
                className={`inline-block w-1 h-1 rounded-full ${
                  streamMode ? "bg-signal-400" : "bg-bone-400/50"
                }`}
              />
              Stream
            </button>
          </div>

          <button
            onClick={submit}
            disabled={isBusy || !text.trim()}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-medium bg-bone-50 text-ink-950 hover:bg-signal-400 disabled:bg-ink-700 disabled:text-bone-400 disabled:cursor-not-allowed transition"
          >
            {isBusy ? "Thinking…" : "Send"}
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
              <path
                d="M2 5.5h7M6 2.5l3 3-3 3"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      <div className="text-[10.5px] font-mono uppercase tracking-wider text-bone-400/60 mt-2 text-center">
        Press <kbd className="px-1 py-0.5 rounded bg-ink-800/60 border border-ink-700/60 text-bone-300">↵</kbd> to send · <kbd className="px-1 py-0.5 rounded bg-ink-800/60 border border-ink-700/60 text-bone-300">⇧ ↵</kbd> for new line
      </div>
    </div>
  );
}
