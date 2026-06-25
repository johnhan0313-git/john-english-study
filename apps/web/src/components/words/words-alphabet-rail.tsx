"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Card } from "@/components/ui";
import { cn } from "@/lib/utils";

export const ALPHABET_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export type LetterSelectOptions = { fromDrag?: boolean };

function railLetters(availableLetters: Set<string>) {
  return [...ALPHABET_LETTERS, ...(availableLetters.has("#") ? ["#"] : [])];
}

function DesktopAlphabetRail({
  letters,
  availableLetters,
  selectedLetter,
  onLetterSelect,
}: {
  letters: string[];
  availableLetters: Set<string>;
  selectedLetter: string;
  onLetterSelect: (letter: string, options?: LetterSelectOptions) => void;
}) {
  return (
    <aside className="sticky top-24 hidden h-fit max-h-[calc(100vh-8rem)] shrink-0 overflow-y-auto lg:block">
      <Card className="p-2">
        <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">A-Z</p>
        <div className="grid grid-cols-2 gap-0.5">
          {letters.map((letter) => {
            const available = availableLetters.has(letter);
            const selected = selectedLetter === letter;
            return (
              <button
                key={letter}
                type="button"
                disabled={!available && !selected}
                onClick={() => onLetterSelect(letter)}
                className={cn(
                  "rounded px-2 py-1 text-xs font-medium transition-colors",
                  selected
                    ? "bg-brand-500 text-white shadow-sm"
                    : available
                      ? "text-brand-700 hover:bg-brand-100"
                      : "cursor-not-allowed text-slate-300",
                )}
              >
                {letter}
              </button>
            );
          })}
        </div>
      </Card>
    </aside>
  );
}

function MobileAlphabetRail({
  letters,
  availableLetters,
  selectedLetter,
  onLetterSelect,
}: {
  letters: string[];
  availableLetters: Set<string>;
  selectedLetter: string;
  onLetterSelect: (letter: string, options?: LetterSelectOptions) => void;
}) {
  const railRef = useRef<HTMLElement>(null);
  const lastLetterRef = useRef<string | null>(null);
  const [touching, setTouching] = useState(false);
  const [bubbleLetter, setBubbleLetter] = useState<string | null>(null);
  const [bubbleY, setBubbleY] = useState(0);

  const letterFromClientY = useCallback(
    (clientY: number) => {
      const el = railRef.current;
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const relativeY = clientY - rect.top;
      const itemHeight = rect.height / letters.length;
      const index = Math.floor(relativeY / itemHeight);
      return letters[Math.max(0, Math.min(letters.length - 1, index))] ?? null;
    },
    [letters],
  );

  const pickLetter = useCallback(
    (clientY: number, fromDrag: boolean) => {
      const letter = letterFromClientY(clientY);
      if (!letter) return;

      setBubbleY(clientY);
      setBubbleLetter(letter);

      if (letter === lastLetterRef.current) return;
      lastLetterRef.current = letter;

      const available = availableLetters.has(letter) || selectedLetter === letter;
      if (!available) return;

      onLetterSelect(letter, { fromDrag });
      if (fromDrag && typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate(8);
      }
    },
    [availableLetters, letterFromClientY, onLetterSelect, selectedLetter],
  );

  const endTouch = useCallback(() => {
    setTouching(false);
    window.setTimeout(() => {
      setBubbleLetter(null);
      lastLetterRef.current = null;
    }, 120);
  }, []);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouching(true);
    pickLetter(e.touches[0].clientY, true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    e.preventDefault();
    pickLetter(e.touches[0].clientY, true);
  };

  const activeHighlight = touching ? bubbleLetter : selectedLetter;

  return (
    <>
      <aside
        ref={railRef}
        className="fixed right-0 top-1/2 z-20 flex max-h-[min(72vh,calc(100vh-8rem))] w-7 -translate-y-1/2 touch-none select-none flex-col items-center justify-center rounded-l-xl bg-white/90 py-2 shadow-lg ring-1 ring-surface-border/80 backdrop-blur-sm lg:hidden"
        aria-label="字母索引"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={endTouch}
        onTouchCancel={endTouch}
      >
        {letters.map((letter) => {
          const available = availableLetters.has(letter);
          const active = activeHighlight === letter;
          return (
            <span
              key={letter}
              className={cn(
                "flex h-[1.05rem] w-full items-center justify-center text-[10px] font-semibold leading-none transition-all duration-100",
                active
                  ? "scale-[1.35] text-brand-600"
                  : available
                    ? "text-brand-700/90"
                    : "text-slate-300",
              )}
            >
              {letter}
            </span>
          );
        })}
      </aside>

      {touching &&
        bubbleLetter &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            className="pointer-events-none fixed z-50 lg:hidden"
            style={{ top: bubbleY, right: "2.75rem", transform: "translateY(-50%)" }}
            aria-hidden
          >
            <div className="animate-alphabet-bubble relative flex h-[4.25rem] w-[4.25rem] items-center justify-center">
              <div className="absolute inset-0 rounded-2xl bg-brand-500/20 blur-md" />
              <div className="relative flex h-full w-full items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-[2rem] font-bold text-white shadow-[0_12px_40px_rgba(234,88,12,0.35)]">
                {bubbleLetter}
              </div>
            </div>
          </div>,
          document.body,
        )}
    </>
  );
}

export function WordsAlphabetRail({
  availableLetters,
  selectedLetter,
  onLetterSelect,
}: {
  availableLetters: Set<string>;
  selectedLetter: string;
  onLetterSelect: (letter: string, options?: LetterSelectOptions) => void;
}) {
  const letters = useMemo(() => railLetters(availableLetters), [availableLetters]);

  return (
    <>
      <DesktopAlphabetRail
        letters={letters}
        availableLetters={availableLetters}
        selectedLetter={selectedLetter}
        onLetterSelect={onLetterSelect}
      />
      <MobileAlphabetRail
        letters={letters}
        availableLetters={availableLetters}
        selectedLetter={selectedLetter}
        onLetterSelect={onLetterSelect}
      />
    </>
  );
}
