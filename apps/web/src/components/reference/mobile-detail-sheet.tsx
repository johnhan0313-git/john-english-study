"use client";

import { useEffect } from "react";

type MobileDetailSheetProps = {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
};

export function MobileDetailSheet({ open, onClose, children }: MobileDetailSheetProps) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] lg:hidden">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
        onClick={onClose}
        aria-label="关闭详情"
      />
      <div
        role="dialog"
        aria-modal="true"
        className="absolute inset-x-0 bottom-0 flex max-h-[min(88dvh,100dvh)] flex-col rounded-t-2xl border-t border-surface-border bg-white shadow-[0_-12px_40px_rgba(15,23,42,0.12)]"
      >
        <div className="flex shrink-0 justify-center pt-3 pb-1">
          <div className="h-1 w-10 rounded-full bg-slate-200" aria-hidden />
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 pb-[calc(env(safe-area-inset-bottom)+1rem)]">
          {children}
        </div>
      </div>
    </div>
  );
}
