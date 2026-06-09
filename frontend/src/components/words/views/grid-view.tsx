import type { WordBrief } from "@/lib/api/types";
import { WordDefinitionText } from "@/components/word-definition-text";
import { Card } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ExamLevelBadges, FamiliarityBars, FamiliarityDot } from "../word-shared";

export function WordsGridView({
  words,
  selected,
  onToggle,
}: {
  words: WordBrief[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {words.map((w) => (
        <Card
          key={w.id}
          hover
          className={cn("cursor-pointer", selected.includes(w.id) && "ring-2 ring-brand-500 ring-offset-2")}
          onClick={() => onToggle(w.id)}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <FamiliarityDot familiarity={w.familiarity} />
              <span className="truncate text-lg font-bold text-slate-900">{w.lemma}</span>
            </div>
            <ExamLevelBadges word={w} compact />
          </div>
          <div className="mt-2 line-clamp-4 text-sm text-slate-600">
            <WordDefinitionText definition={w.definitions[0]} />
          </div>
          {w.familiarity != null && w.familiarity > 0 && (
            <div className="mt-3">
              <FamiliarityBars familiarity={w.familiarity} />
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}
