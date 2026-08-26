"use client";

import { LayoutGrid, List } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "../../../app-chrome/utils";
import { WORDS_VIEW_MODES, type WordsViewMode } from "../model";

const ICONS: Record<WordsViewMode, LucideIcon> = {
  grid: LayoutGrid,
  list: List,
};

export function WordsViewSwitcher({
  value,
  onChange,
}: {
  value: WordsViewMode;
  onChange: (mode: WordsViewMode) => void;
}) {
  return (
    <div
      className="inline-flex shrink-0 rounded-xl border border-surface-border/80 bg-white/80 p-1 shadow-sm"
      role="group"
      aria-label="视图模式"
    >
      {WORDS_VIEW_MODES.map((mode) => {
        const Icon = ICONS[mode.id];
        const active = value === mode.id;
        return (
          <button
            key={mode.id}
            type="button"
            title={mode.hint}
            onClick={() => onChange(mode.id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all",
              active
                ? "bg-hero-gradient text-white shadow-sm"
                : "text-slate-600 hover:bg-brand-50 hover:text-brand-700",
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{mode.label}</span>
          </button>
        );
      })}
    </div>
  );
}
