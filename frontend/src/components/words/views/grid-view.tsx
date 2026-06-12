import type { WordBrief } from "@/lib/api/types";
import { WordDefinitionText } from "@/components/word-definition-text";
import { Card } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ExamLevelBadges, FamiliarityBars, FamiliarityDot } from "../word-shared";
import { WordsLetterHeader, type WordsLetterGroup } from "../words-alphabet-layout";

function WordGridCard({
  word,
  selected,
  onToggle,
}: {
  word: WordBrief;
  selected: number[];
  onToggle: (id: number) => void;
}) {
  return (
    <Card
      hover
      className={cn("cursor-pointer", selected.includes(word.id) && "ring-2 ring-brand-500 ring-offset-2")}
      onClick={() => onToggle(word.id)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <FamiliarityDot familiarity={word.familiarity} />
          <span className="truncate text-lg font-bold text-slate-900">{word.lemma}</span>
        </div>
        <ExamLevelBadges word={word} compact />
      </div>
      <div className="mt-2 line-clamp-4 text-sm text-slate-600">
        <WordDefinitionText definition={word.definitions[0]} />
      </div>
      {word.familiarity != null && word.familiarity > 0 && (
        <div className="mt-3">
          <FamiliarityBars familiarity={word.familiarity} />
        </div>
      )}
    </Card>
  );
}

export function WordsGridView({
  groups,
  selected,
  onToggle,
}: {
  groups: WordsLetterGroup[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  return (
    <>
      {groups.map(({ letter, words }) => (
        <section key={letter} id={`words-letter-${letter}`} className="scroll-mt-24 space-y-3">
          <WordsLetterHeader letter={letter} count={words.length} />
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {words.map((w) => (
              <WordGridCard key={w.id} word={w} selected={selected} onToggle={onToggle} />
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
