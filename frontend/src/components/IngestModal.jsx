import React, { useRef, useState } from "react";
import { Modal } from "./Modal.jsx";
import { api } from "../api/client";

const DOC_TYPES = [
  ["10-K", "Annual report"],
  ["10-Q", "Quarterly report"],
  ["8-K", "Material event"],
  ["earnings_call", "Earnings call"],
  ["news", "News article"],
  ["research", "Research report"],
  ["other", "Other"],
];

export default function IngestModal({ open, onClose, onIngested }) {
  const [mode, setMode] = useState("file"); // "file" | "url"
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [company, setCompany] = useState("");
  const [ticker, setTicker] = useState("");
  const [docType, setDocType] = useState("other");
  const [filingDate, setFilingDate] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  function reset() {
    setFile(null);
    setUrl("");
    setCompany("");
    setTicker("");
    setDocType("other");
    setFilingDate("");
    setError(null);
    setSuccess(null);
  }

  function handleClose() {
    if (busy) return;
    reset();
    onClose();
  }

  async function submit() {
    setError(null);
    setSuccess(null);
    setBusy(true);
    try {
      let result;
      if (mode === "file") {
        if (!file) throw new Error("Choose a file first.");
        result = await api.upload({
          file,
          company: company || null,
          ticker: ticker || null,
          doc_type: docType,
          filing_date: filingDate || null,
        });
      } else {
        if (!url) throw new Error("Enter a URL.");
        result = await api.ingestUrl({
          url,
          company: company || null,
          ticker: ticker || null,
          doc_type: docType,
        });
      }
      setSuccess(
        `Indexed ${result.chunks_indexed} chunks from ${result.source}.`
      );
      onIngested?.(result);
      // Clear inputs but leave the success message visible.
      setFile(null);
      setUrl("");
    } catch (e) {
      setError(e.message || "Ingestion failed.");
    } finally {
      setBusy(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Ingest a document"
      subtitle="Upload an SEC filing, transcript, or article. AlphaIQ chunks, embeds, and indexes it for retrieval."
    >
      {/* Mode tabs */}
      <div className="flex gap-1 p-1 rounded-md bg-ink-800/60 border border-ink-700/60 mb-5 w-fit">
        {["file", "url"].map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-3 py-1 rounded text-[11px] font-mono uppercase tracking-wider transition ${
              mode === m
                ? "bg-bone-50 text-ink-950"
                : "text-bone-300 hover:text-bone-50"
            }`}
          >
            {m === "file" ? "File" : "URL"}
          </button>
        ))}
      </div>

      {/* Source input */}
      {mode === "file" ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-6 mb-4 text-center cursor-pointer transition ${
            dragOver
              ? "border-signal-500/60 bg-signal-500/5"
              : "border-ink-700 hover:border-ink-600 hover:bg-ink-800/30"
          }`}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.md,.html,.htm,.csv"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          {file ? (
            <div>
              <div className="font-mono text-[12px] text-signal-400">
                {file.name}
              </div>
              <div className="text-[11px] text-bone-400 mt-1">
                {(file.size / 1024).toFixed(1)} KB · click to change
              </div>
            </div>
          ) : (
            <div>
              <div className="font-display text-[15px] text-bone-100 mb-1">
                Drop a file here
              </div>
              <div className="text-[12px] text-bone-400">
                PDF, TXT, MD, HTML, CSV · up to 50 MB
              </div>
            </div>
          )}
        </div>
      ) : (
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article-or-filing"
          className="w-full bg-ink-800/60 border border-ink-700/60 rounded px-3 py-2.5 text-[13px] font-mono text-bone-100 placeholder:text-bone-400/40 outline-none focus:border-signal-500/40 transition mb-4"
        />
      )}

      {/* Metadata fields */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <Field label="Company">
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Apple Inc."
            className="field-input"
          />
        </Field>
        <Field label="Ticker">
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
            maxLength={10}
            className="field-input font-mono"
          />
        </Field>
        <Field label="Document type">
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="field-input"
          >
            {DOC_TYPES.map(([v, label]) => (
              <option key={v} value={v}>
                {label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Filing date (optional)">
          <input
            type="date"
            value={filingDate}
            onChange={(e) => setFilingDate(e.target.value)}
            className="field-input"
          />
        </Field>
      </div>

      {error && (
        <div className="text-[12px] text-risk-high bg-risk-high/10 border border-risk-high/30 rounded px-3 py-2 mb-3">
          {error}
        </div>
      )}
      {success && (
        <div className="text-[12px] text-signal-400 bg-signal-500/10 border border-signal-500/30 rounded px-3 py-2 mb-3">
          {success}
        </div>
      )}

      <div className="flex justify-end gap-2 pt-3 border-t border-ink-800/80">
        <button
          onClick={handleClose}
          disabled={busy}
          className="px-3.5 py-1.5 rounded-md text-xs text-bone-300 hover:text-bone-50 transition"
        >
          Close
        </button>
        <button
          onClick={submit}
          disabled={busy || (mode === "file" ? !file : !url)}
          className="px-4 py-1.5 rounded-md text-xs font-medium bg-signal-500 text-ink-950 hover:bg-signal-400 disabled:bg-ink-700 disabled:text-bone-400 disabled:cursor-not-allowed transition"
        >
          {busy ? "Indexing…" : "Ingest"}
        </button>
      </div>

      <style>{`
        .field-input {
          width: 100%;
          background: rgba(29, 29, 34, 0.6);
          border: 1px solid rgba(58, 58, 67, 0.6);
          border-radius: 4px;
          padding: 8px 10px;
          font-size: 12.5px;
          color: #f4f1e8;
          outline: none;
          transition: border-color .15s;
        }
        .field-input:focus { border-color: rgba(127, 227, 74, 0.4); }
        .field-input::placeholder { color: rgba(154, 149, 135, 0.4); }
      `}</style>
    </Modal>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block font-mono text-[10px] uppercase tracking-wider text-bone-400 mb-1">
        {label}
      </span>
      {children}
    </label>
  );
}
