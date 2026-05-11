import React from "react";

/**
 * Replace inline citation markers like [1] or [1][3] with clickable
 * React spans, leaving the rest of the answer text untouched.
 *
 * onClickCitation(n) is called with the 1-indexed citation number.
 */
export function renderWithCitations(text, onClickCitation) {
  if (!text) return null;
  const parts = [];
  const re = /\[(\d+)\]/g;
  let lastIndex = 0;
  let m;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) {
      parts.push(
        <span key={`t-${key++}`}>{text.slice(lastIndex, m.index)}</span>
      );
    }
    const n = parseInt(m[1], 10);
    parts.push(
      <button
        key={`c-${key++}`}
        type="button"
        className="citation-mark"
        onClick={() => onClickCitation?.(n)}
        title={`Source ${n}`}
      >
        {n}
      </button>
    );
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < text.length) {
    parts.push(<span key={`t-${key++}`}>{text.slice(lastIndex)}</span>);
  }
  return parts;
}

/** Truncate a string in the middle, keeping head/tail visible. */
export function truncateMiddle(s, max = 48) {
  if (!s || s.length <= max) return s;
  const head = Math.ceil(max / 2) - 1;
  const tail = Math.floor(max / 2) - 2;
  return `${s.slice(0, head)}…${s.slice(-tail)}`;
}

export function formatScore(score) {
  return `${(score * 100).toFixed(0)}%`;
}
