import React, { useEffect } from "react";

export function Modal({ open, onClose, title, subtitle, children, maxWidth = "max-w-xl" }) {
  // Close on Escape.
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      <div
        className="absolute inset-0 bg-ink-950/80 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className={`relative ${maxWidth} w-[92vw] max-h-[88vh] overflow-y-auto panel p-6 animate-slide-up`}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="font-display text-[22px] text-bone-50 leading-none">
              {title}
            </h2>
            {subtitle && (
              <p className="text-[12px] text-bone-400 mt-1.5 leading-relaxed max-w-md">
                {subtitle}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-bone-400 hover:text-bone-50 transition p-1 -m-1"
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
