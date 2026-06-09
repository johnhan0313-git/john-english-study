import type { WordBrief } from "@/lib/api/types";
import { definitionPreview } from "@/lib/definition-format";
import { Card } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ExamLevelBadges, FamiliarityBars, WordSelectCheckbox } from "../word-shared";

export function WordsTableView({
  words,
  selected,
  onToggle,
}: {
  words: WordBrief[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="border-b border-surface-border bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <th className="w-10 px-3 py-3" />
              <th className="px-3 py-3">单词</th>
              <th className="px-3 py-3">释义</th>
              <th className="px-3 py-3">词库</th>
              <th className="px-3 py-3">熟悉度</th>
            </tr>
          </thead>
          <tbody>
            {words.map((w) => {
              const isSelected = selected.includes(w.id);
              return (
                <tr
                  key={w.id}
                  onClick={() => onToggle(w.id)}
                  className={cn(
                    "cursor-pointer border-b border-surface-border/60 transition-colors hover:bg-brand-50/30",
                    isSelected && "bg-brand-50/60",
                  )}
                >
                  <td className="px-3 py-3">
                    <WordSelectCheckbox checked={isSelected} onToggle={() => onToggle(w.id)} />
                  </td>
                  <td className="whitespace-nowrap px-3 py-3 font-semibold text-slate-900">{w.lemma}</td>
                  <td className="max-w-md px-3 py-3 text-slate-600">{definitionPreview(w.definitions[0], 120)}</td>
                  <td className="px-3 py-3">
                    <ExamLevelBadges word={w} compact />
                  </td>
                  <td className="px-3 py-3">
                    {w.familiarity != null && w.familiarity > 0 ? (
                      <FamiliarityBars familiarity={w.familiarity} />
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
