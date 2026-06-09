import type { WordBrief } from "@/lib/api/types";
import { definitionPreview } from "@/lib/definition-format";
import { Card } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ExamLevelBadges, FamiliarityDot, WordSelectCheckbox } from "../word-shared";

export function WordsListView({
  words,
  selected,
  onToggle,
}: {
  words: WordBrief[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  return (
    <Card className="divide-y divide-surface-border p-0 overflow-hidden">
      {words.map((w) => {
        const isSelected = selected.includes(w.id);
        return (
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
              "flex cursor-pointer items-start gap-3 px-4 py-3 transition-colors hover:bg-brand-50/40",
              isSelected && "bg-brand-50/70",
            )}
          >
            <WordSelectCheckbox checked={isSelected} onToggle={() => onToggle(w.id)} />
            <FamiliarityDot familiarity={w.familiarity} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-slate-900">{w.lemma}</span>
                <ExamLevelBadges word={w} compact />
              </div>
              <p className="mt-0.5 line-clamp-2 text-sm text-slate-600">
                {definitionPreview(w.definitions[0], 96)}
              </p>
            </div>
          </div>
        );
      })}
    </Card>
  );
}
