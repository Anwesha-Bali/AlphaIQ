import React, { useEffect, useRef, useState } from "react";
import Header from "./components/Header.jsx";
import Composer from "./components/Composer.jsx";
import {
  UserMessage,
  AssistantMessage,
  ThinkingMessage,
} from "./components/Messages.jsx";
import EmptyState from "./components/EmptyState.jsx";
import IngestModal from "./components/IngestModal.jsx";
import InsightsModal from "./components/InsightsModal.jsx";
import CompareModal from "./components/CompareModal.jsx";
import { api } from "./api/client.js";

export default function App() {
  // Conversation: array of { role: 'user' | 'assistant', ...payload }
  const [messages, setMessages] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [ticker, setTicker] = useState("");
  // Highlighted citation: { messageIdx, number }
  const [highlight, setHighlight] = useState(null);

  // Modals
  const [showUpload, setShowUpload] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [showCompare, setShowCompare] = useState(false);

  const scrollRef = useRef(null);

  // Auto-scroll to the latest message.
  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  async function handleSend({ question, ticker: t, stream }) {
    setIsBusy(true);

    // Append user message and a placeholder assistant slot.
    setMessages((prev) => [
      ...prev,
      { role: "user", text: question },
      stream
        ? {
            role: "assistant",
            text: "",
            citations: [],
            isStreaming: true,
            insufficient: false,
          }
        : { role: "assistant", thinking: true },
    ]);

    try {
      if (stream) {
        const start = performance.now();
        await api.queryStream({ question, ticker: t || null }, (evt) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (!last || last.role !== "assistant") return prev;
            if (evt.type === "citations") {
              last.citations = evt.citations;
            } else if (evt.type === "token") {
              last.text = (last.text || "") + evt.text;
            } else if (evt.type === "insufficient_context") {
              last.insufficient = true;
              last.text =
                "Not enough context to answer confidently. Upload relevant filings or news, then try again.";
            } else if (evt.type === "done") {
              last.isStreaming = false;
              last.latency_ms = Math.round(performance.now() - start);
            } else if (evt.type === "error") {
              last.isStreaming = false;
              last.error = evt.message;
              last.text =
                last.text || `Stream error: ${evt.message || "unknown"}`;
            }
            return next;
          });
        });
      } else {
        const res = await api.query({ question, ticker: t || null });
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            role: "assistant",
            text: res.answer,
            citations: res.citations,
            insufficient: res.insufficient_context,
            latency_ms: res.latency_ms,
          };
          return next;
        });
      }
    } catch (e) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          text: `Request failed: ${e.message}`,
          citations: [],
          insufficient: false,
          error: true,
        };
        return next;
      });
    } finally {
      setIsBusy(false);
    }
  }

  function handleCitationClick(messageIdx, number) {
    setHighlight({ messageIdx, number });
    // Auto-clear after a moment so re-clicking the same one re-triggers.
    setTimeout(() => setHighlight(null), 1500);
  }

  function clearConversation() {
    setMessages([]);
  }

  return (
    <div className="h-full flex flex-col">
      <Header
        onOpenUpload={() => setShowUpload(true)}
        onOpenInsights={() => setShowInsights(true)}
        onOpenCompare={() => setShowCompare(true)}
      />

      {/* Conversation area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-[1100px] mx-auto px-6 lg:px-10 py-8 space-y-8">
          {messages.length === 0 ? (
            <EmptyState onOpenUpload={() => setShowUpload(true)} />
          ) : (
            <>
              {messages.map((m, i) => {
                if (m.role === "user") return <UserMessage key={i} text={m.text} />;
                if (m.thinking) return <ThinkingMessage key={i} />;
                return (
                  <AssistantMessage
                    key={i}
                    text={m.text}
                    citations={m.citations || []}
                    insufficient={m.insufficient}
                    isStreaming={m.isStreaming}
                    latency_ms={m.latency_ms ?? null}
                    highlightedCitation={
                      highlight?.messageIdx === i ? highlight.number : null
                    }
                    onCitationClick={(n) => handleCitationClick(i, n)}
                  />
                );
              })}
              <div className="h-2" />
            </>
          )}
        </div>
      </div>

      {/* Composer pinned to bottom */}
      <div className="border-t border-ink-800/80 bg-ink-950/90 backdrop-blur-xl">
        <div className="max-w-[1100px] mx-auto px-6 lg:px-10 py-4">
          {messages.length > 0 && (
            <div className="flex justify-end mb-2">
              <button
                onClick={clearConversation}
                className="text-[10.5px] font-mono uppercase tracking-wider text-bone-400/70 hover:text-bone-200 transition"
              >
                Clear conversation
              </button>
            </div>
          )}
          <Composer
            onSend={handleSend}
            isBusy={isBusy}
            ticker={ticker}
            onTickerChange={setTicker}
          />
        </div>
      </div>

      {/* Modals */}
      <IngestModal
        open={showUpload}
        onClose={() => setShowUpload(false)}
        onIngested={() => {
          /* health auto-refreshes; nothing else to do */
        }}
      />
      <InsightsModal open={showInsights} onClose={() => setShowInsights(false)} />
      <CompareModal open={showCompare} onClose={() => setShowCompare(false)} />
    </div>
  );
}
