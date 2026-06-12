"use client";

import { Card } from "@/components/ui";
import { cn } from "@/lib/utils";

export const ALPHABET_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export function WordsAlphabetRail({
  availableLetters,
  selectedLetter,
  onLetterSelect,
}: {
  availableLetters: Set<string>;
  selectedLetter: string;
  onLetterSelect: (letter: string) => void;
}) {
  const renderButton = (letter: string, variant: "desktop" | "mobile") => {
    const available = availableLetters.has(letter);
    const selected = selectedLetter === letter;
    return (
      <button
        key={letter}
        type="button"
        disabled={!available && !selected}
        onClick={() => onLetterSelect(letter)}
        className={cn(
          "font-semibold transition-colors",
          variant === "mobile"
            ? "px-1 py-0.5 text-[10px] leading-none"
            : "rounded px-2 py-1 text-xs font-medium",
          selected
            ? variant === "mobile"
              ? "rounded-sm bg-brand-500 text-white"
              : "bg-brand-500 text-white shadow-sm"
            : available
              ? "text-brand-700 hover:bg-brand-100"
              : "cursor-not-allowed text-slate-300",
        )}
      >
        {letter}
      </button>
    );
  };

  return (
    <>
      <aside className="sticky top-24 hidden h-fit max-h-[calc(100vh-8rem)] shrink-0 overflow-y-auto lg:block">
        <Card className="p-2">
          <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">A-Z</p>
          <div className="grid grid-cols-2 gap-0.5">
            {ALPHABET_LETTERS.map((letter) => renderButton(letter, "desktop"))}
            {availableLetters.has("#") && renderButton("#", "desktop")}
          </div>
        </Card>
      </aside>

      <aside
        className="fixed right-0 top-1/2 z-10 flex max-h-[min(70vh,calc(100vh-10rem))] -translate-y-1/2 flex-col items-center overflow-y-auto rounded-l-lg bg-white/95 px-0.5 py-1 shadow-md ring-1 ring-surface-border lg:hidden [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        aria-label="字母索引"
      >
        {ALPHABET_LETTERS.map((letter) => renderButton(letter, "mobile"))}
        {availableLetters.has("#") && renderButton("#", "mobile")}
      </aside>
    </>
  );
}
