"use client";

import { useMemo } from "react";

import type { WordBrief } from "@/lib/api/types";
import { WordDefinitionText } from "@/components/word-definition-text";
import { Card } from "@/components/ui";
import { groupWordsByLetter } from "@/lib/words-display";
import { cn } from "@/lib/utils";
import { ExamLevelBadges, FamiliarityDot } from "../word-shared";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

export function WordsIndexView({
  words,
  selected,
  onToggle,
}: {
  words: WordBrief[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  const groups = useMemo(() => groupWordsByLetter(words), [words]);
  const activeLetters = new Set(groups.map((g) => g.letter));

  const scrollTo = (letter: string) => {
    document.getElementById(`words-index-${letter}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (!words.length) {
    return <Card className="py-16 text-center text-slate-500">当前筛选下暂无单词</Card>;
  }

  return (
    <div className="relative flex gap-4">
      <div className="min-w-0 flex-1 space-y-6">
        <p className="text-xs text-slate-500">
          按首字母分组（当前页 {words.length} 词）· 右侧可快速跳转
        </p>
        {groups.map(({ letter, words: groupWords }) => (
          <section key={letter} id={`words-index-${letter}`} className="scroll-mt-24">
            <div className="mb-2 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-sm font-bold text-brand-800">
                {letter}
              </span>
              <span className="text-sm text-slate-500">{groupWords.length} 词</span>
            </div>
            <Card className="divide-y divide-surface-border p-0 overflow-hidden">
              {groupWords.map((w) => (
                <div
                  key={w.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => onToggle(w.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onToggle(w.id);
                    }
                  }}
                  className={cn(
                    "flex cursor-pointer gap-3 px-4 py-2.5 transition-colors hover:bg-brand-50/40",
                    selected.includes(w.id) && "bg-brand-50/70 ring-1 ring-inset ring-brand-200",
                  )}
                >
                  <FamiliarityDot familiarity={w.familiarity} />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-medium text-slate-900">{w.lemma}</span>
                      <ExamLevelBadges word={w} compact />
                    </div>
                    <div className="mt-0.5 text-sm text-slate-600 line-clamp-2">
                      <WordDefinitionText definition={w.definitions[0]} />
                    </div>
                  </div>
                </div>
              ))}
            </Card>
          </section>
        ))}
      </div>

      <aside className="sticky top-24 hidden h-fit max-h-[calc(100vh-8rem)] shrink-0 overflow-y-auto lg:block">
        <Card className="p-2">
          <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">A-Z</p>
          <div className="grid grid-cols-2 gap-0.5">
            {LETTERS.map((letter) => (
              <button
                key={letter}
                type="button"
                disabled={!activeLetters.has(letter)}
                onClick={() => scrollTo(letter)}
                className={cn(
                  "rounded px-2 py-1 text-xs font-medium transition-colors",
                  activeLetters.has(letter)
                    ? "text-brand-700 hover:bg-brand-100"
                    : "cursor-not-allowed text-slate-300",
                )}
              >
                {letter}
              </button>
            ))}
            {activeLetters.has("#") && (
              <button
                type="button"
                onClick={() => scrollTo("#")}
                className="rounded px-2 py-1 text-xs font-medium text-brand-700 hover:bg-brand-100"
              >
                #
              </button>
            )}
          </div>
        </Card>
      </aside>

      <div className="fixed bottom-24 right-4 z-10 flex gap-1 rounded-full bg-white/95 p-1 shadow-lg ring-1 ring-surface-border lg:hidden">
        {LETTERS.filter((l) => activeLetters.has(l))
          .filter((_, i) => i % 3 === 0)
          .slice(0, 9)
          .map((letter) => (
            <button
              key={letter}
              type="button"
              onClick={() => scrollTo(letter)}
              className="rounded-full px-2 py-1 text-xs font-semibold text-brand-700"
            >
              {letter}
            </button>
          ))}
      </div>
    </div>
  );
}
