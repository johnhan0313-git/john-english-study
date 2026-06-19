"use client";

import { useMemo } from "react";

import type { WordBrief } from "@sceneenglish/api-client/types";
import { Card } from "@sceneenglish/app-core/components/ui";
import { groupWordsByLetter } from "@sceneenglish/api-client";

import { WordsAlphabetRail } from "./words-alphabet-rail";

export type WordsLetterGroup = { letter: string; words: WordBrief[] };

export function WordsLetterHeader({ letter, count }: { letter: string; count: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-100 text-xs font-bold text-brand-800">
        {letter}
      </span>
      <span className="text-xs text-slate-500">{count} 词</span>
    </div>
  );
}

export function WordsAlphabetLayout({
  words,
  total,
  availableLetters,
  selectedLetter,
  onLetterSelect,
  children,
}: {
  words: WordBrief[];
  total: number;
  availableLetters: string[];
  selectedLetter: string;
  onLetterSelect: (letter: string, options?: { fromDrag?: boolean }) => void;
  children: (groups: WordsLetterGroup[]) => React.ReactNode;
}) {
  const groups = useMemo(() => groupWordsByLetter(words), [words]);
  const letterSet = useMemo(() => new Set(availableLetters), [availableLetters]);

  if (!words.length) {
    return (
      <div className="relative flex gap-4">
        <Card className="min-w-0 flex-1 py-16 pr-7 text-center text-slate-500 lg:pr-6">
          {selectedLetter ? `字母 ${selectedLetter} 下暂无单词` : "当前筛选下暂无单词"}
        </Card>
        <WordsAlphabetRail
          availableLetters={letterSet}
          selectedLetter={selectedLetter}
          onLetterSelect={onLetterSelect}
        />
      </div>
    );
  }

  const summary = selectedLetter
    ? `字母 ${selectedLetter} · 共 ${total} 词`
    : `全库 ${total} 词 · 右侧字母可快速定位`;

  return (
    <div className="relative flex gap-4">
      <div className="min-w-0 flex-1 space-y-6 pr-7 lg:pr-0">
        <p className="text-xs text-slate-500">{summary}</p>
        {children(groups)}
      </div>
      <WordsAlphabetRail
        availableLetters={letterSet}
        selectedLetter={selectedLetter}
        onLetterSelect={onLetterSelect}
      />
    </div>
  );
}
