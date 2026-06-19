import type { WordBrief } from "@/lib/api/types";
import { api } from "@/lib/api";
import { AudioPlayButton } from "@/components/audio-play-button";
import { Badge } from "@/components/ui";
import type { AudioPlayer } from "@/hooks/use-audio-player";
import {
  examLevelsForWord,
  familiarityDotClass,
  levelBadgeVariant,
  levelLabel,
} from "@/lib/words-display";
import { cn } from "@/lib/utils";

export function FamiliarityDot({ familiarity }: { familiarity: number | null }) {
  return (
    <span
      className={cn("inline-block h-2 w-2 shrink-0 rounded-full", familiarityDotClass(familiarity))}
      title="熟悉度"
    />
  );
}

export function ExamLevelBadges({ word, compact }: { word: WordBrief; compact?: boolean }) {
  const levels = examLevelsForWord(word);
  return (
    <div className={cn("flex flex-wrap gap-1", compact ? "justify-end" : "")}>
      {levels.map((lv) => (
        <Badge key={lv} variant={levelBadgeVariant(lv)}>
          {levelLabel(lv)}
        </Badge>
      ))}
    </div>
  );
}

export function FamiliarityBars({ familiarity }: { familiarity: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className={cn("h-1 w-3 rounded-full sm:w-4", i < familiarity ? "bg-brand-400" : "bg-slate-100")}
        />
      ))}
    </div>
  );
}

export function WordSelectCheckbox({
  checked,
  onToggle,
}: {
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => {
        e.stopPropagation();
        onToggle();
      }}
      onClick={(e) => e.stopPropagation()}
      className="h-4 w-4 shrink-0 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
      aria-label="选择单词"
    />
  );
}

export function WordSpeakButton({
  word,
  player,
}: {
  word: WordBrief;
  player: AudioPlayer;
}) {
  return (
    <AudioPlayButton
      audioKey={`word-${word.id}`}
      url={api.getWordAudioUrl(word.id)}
      player={player}
      label={`播放 ${word.lemma}`}
      onClick={(e) => e.stopPropagation()}
    />
  );
}
