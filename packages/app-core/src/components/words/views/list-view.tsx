import type { WordBrief } from "@sceneenglish/api-client/types";
import { definitionPreview } from "@sceneenglish/api-client";
import { Card } from "@sceneenglish/app-core/components/ui";
import { cn } from "@sceneenglish/app-core/lib/utils";
import type { AudioPlayer } from "@sceneenglish/app-core/hooks/use-audio-player";
import { ExamLevelBadges, FamiliarityDot, WordSelectCheckbox, WordSpeakButton } from "../word-shared";
import { WordsLetterHeader, type WordsLetterGroup } from "../words-alphabet-layout";

function WordListRow({
  word,
  selected,
  onToggle,
  player,
}: {
  word: WordBrief;
  selected: number[];
  onToggle: (id: number) => void;
  player: AudioPlayer;
}) {
  const isSelected = selected.includes(word.id);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onToggle(word.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onToggle(word.id);
        }
      }}
      className={cn(
        "flex cursor-pointer items-start gap-3 px-4 py-3 transition-colors hover:bg-brand-50/40",
        isSelected && "bg-brand-50/70",
      )}
    >
      <WordSelectCheckbox checked={isSelected} onToggle={() => onToggle(word.id)} />
      <FamiliarityDot familiarity={word.familiarity} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-900">{word.lemma}</span>
            <WordSpeakButton word={word} player={player} />
          </div>
          <ExamLevelBadges word={word} compact />
        </div>
        <p className="mt-0.5 line-clamp-2 text-sm text-slate-600">
          {definitionPreview(word.definitions[0], 96)}
        </p>
      </div>
    </div>
  );
}

export function WordsListView({
  groups,
  selected,
  onToggle,
  player,
}: {
  groups: WordsLetterGroup[];
  selected: number[];
  onToggle: (id: number) => void;
  player: AudioPlayer;
}) {
  return (
    <>
      {groups.map(({ letter, words }) => (
        <section key={letter} id={`words-letter-${letter}`} className="scroll-mt-24 space-y-3">
          <WordsLetterHeader letter={letter} count={words.length} />
          <Card className="divide-y divide-surface-border overflow-hidden p-0">
            {words.map((w) => (
              <WordListRow key={w.id} word={w} selected={selected} onToggle={onToggle} player={player} />
            ))}
          </Card>
        </section>
      ))}
    </>
  );
}
