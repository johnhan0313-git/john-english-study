"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";

import type { WordBrief } from "@/lib/api/types";
import { WordDefinitionText } from "@/components/word-definition-text";
import { Badge, Button, Card } from "@/components/ui";
import { ExamLevelBadges } from "../word-shared";
import { cn } from "@/lib/utils";

export function WordsFlashcardView({
  words,
  selected,
  onToggle,
}: {
  words: WordBrief[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (!words.length) {
    return (
      <Card className="py-16 text-center text-slate-500">当前筛选下暂无单词</Card>
    );
  }

  const current = words[Math.min(index, words.length - 1)];
  const isSelected = selected.includes(current.id);

  const go = (next: number) => {
    setIndex(next);
    setFlipped(false);
  };

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <Card
        className={cn(
          "relative min-h-[280px] cursor-pointer select-none p-8 text-center transition-shadow",
          isSelected && "ring-2 ring-brand-500 ring-offset-2",
        )}
        onClick={() => setFlipped((f) => !f)}
      >
        <div className="absolute right-4 top-4">
          <ExamLevelBadges word={current} compact />
        </div>
        {!flipped ? (
          <div className="flex min-h-[200px] flex-col items-center justify-center gap-3">
            <p className="text-xs font-medium uppercase tracking-widest text-slate-400">点击翻面</p>
            <h2 className="text-4xl font-bold tracking-[0.02em] text-slate-900">{current.lemma}</h2>
            {current.phonetic && <p className="text-lg text-slate-500">{current.phonetic}</p>}
          </div>
        ) : (
          <div className="flex min-h-[200px] flex-col items-center justify-center gap-2 text-left">
            <p className="text-xs font-medium text-brand-600">释义</p>
            <div className="text-base leading-relaxed text-slate-700">
              <WordDefinitionText definition={current.definitions[0]} />
            </div>
          </div>
        )}
      </Card>

      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={index <= 0}
          onClick={() => go(index - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Badge variant="outline">
          {index + 1} / {words.length}
        </Badge>
        <Button
          variant="outline"
          size="sm"
          disabled={index >= words.length - 1}
          onClick={() => go(index + 1)}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setFlipped(false)}>
          <RotateCcw className="mr-1 h-3.5 w-3.5" />
          正面
        </Button>
        <Button
          variant={isSelected ? "primary" : "outline"}
          size="sm"
          onClick={() => onToggle(current.id)}
        >
          {isSelected ? "已选" : "选入场景"}
        </Button>
      </div>
      <p className="text-center text-xs text-slate-500">
        闪卡模式基于当前页单词，配合翻页浏览；选中的词可用于批量生成场景
      </p>
    </div>
  );
}
