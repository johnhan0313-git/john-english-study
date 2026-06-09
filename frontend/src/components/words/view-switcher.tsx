"use client";

import { BookMarked, LayoutGrid, List, Rows3, Table2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { WORDS_VIEW_MODES, type WordsViewMode } from "@/lib/words-display";

const ICONS: Record<WordsViewMode, LucideIcon> = {
  grid: LayoutGrid,
  list: List,
  table: Table2,
  flashcard: BookMarked,
  index: Rows3,
};

export function WordsViewSwitcher({
  value,
  onChange,
}: {
  value: WordsViewMode;
  onChange: (mode: WordsViewMode) => void;
}) {
  const browse = WORDS_VIEW_MODES.filter((m) => m.group === "browse");
  const study = WORDS_VIEW_MODES.filter((m) => m.group === "study");

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
      <ModeGroup label="浏览" modes={browse} value={value} onChange={onChange} />
      <div className="hidden h-6 w-px bg-slate-200 sm:block" />
      <ModeGroup label="学习" modes={study} value={value} onChange={onChange} />
    </div>
  );
}

function ModeGroup({
  label,
  modes,
  value,
  onChange,
}: {
  label: string;
  modes: typeof WORDS_VIEW_MODES;
  value: WordsViewMode;
  onChange: (mode: WordsViewMode) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-slate-400">{label}</span>
      {modes.map((mode) => {
        const Icon = ICONS[mode.id];
        const active = value === mode.id;
        return (
          <button
            key={mode.id}
            type="button"
            title={mode.hint}
            onClick={() => onChange(mode.id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
              active
                ? "bg-brand-500 text-white shadow-sm"
                : "bg-white/80 text-slate-600 ring-1 ring-surface-border hover:bg-brand-50 hover:text-brand-700",
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {mode.label}
          </button>
        );
      })}
    </div>
  );
}
