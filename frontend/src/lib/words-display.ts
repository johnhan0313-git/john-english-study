import type { WordBrief } from "@/lib/api/types";

export type WordsViewMode = "grid" | "list" | "table" | "flashcard" | "index";

export const WORDS_VIEW_MODES: {
  id: WordsViewMode;
  label: string;
  hint: string;
  group: "browse" | "study";
}[] = [
  { id: "grid", label: "卡片", hint: "浏览选词", group: "browse" },
  { id: "list", label: "列表", hint: "紧凑速览", group: "browse" },
  { id: "table", label: "表格", hint: "对比排序", group: "browse" },
  { id: "flashcard", label: "闪卡", hint: "背诵复习", group: "study" },
  { id: "index", label: "索引", hint: "字母定位", group: "study" },
];

const STORAGE_KEY = "words-view-mode";

export function loadWordsViewMode(): WordsViewMode {
  if (typeof window === "undefined") return "grid";
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved && WORDS_VIEW_MODES.some((m) => m.id === saved)) {
    return saved as WordsViewMode;
  }
  return "grid";
}

export function saveWordsViewMode(mode: WordsViewMode) {
  localStorage.setItem(STORAGE_KEY, mode);
}

export function pageSizeForView(mode: WordsViewMode): number {
  if (mode === "index") return 100;
  if (mode === "flashcard") return 50;
  return 30;
}

export function examLevelsForWord(word: WordBrief): string[] {
  return word.exam_levels?.length ? word.exam_levels : [word.level];
}

export function familiarityDotClass(f: number | null): string {
  if (f === null || f === 0) return "bg-slate-300";
  if (f <= 2) return "bg-amber-400";
  if (f <= 4) return "bg-brand-400";
  return "bg-emerald-500";
}

export function levelBadgeVariant(level: string): "brand" | "purple" | "success" | "warning" | "outline" {
  if (level === "cet6") return "purple";
  if (level.startsWith("pets1") || level.startsWith("pets2")) return "success";
  if (level.startsWith("pets4") || level.startsWith("pets5")) return "warning";
  if (level.startsWith("pets")) return "outline";
  return "brand";
}

export function levelLabel(level: string): string {
  const map: Record<string, string> = {
    cet4: "CET-4",
    cet6: "CET-6",
    both: "CET-4/6",
    pets1: "PETS-1",
    pets2: "PETS-2",
    pets3: "PETS-3",
    pets4: "PETS-4",
    pets5: "PETS-5",
  };
  return map[level] ?? level.toUpperCase();
}

export function indexLetter(lemma: string): string {
  const ch = lemma.trim().charAt(0).toUpperCase();
  return /[A-Z]/.test(ch) ? ch : "#";
}

export function groupWordsByLetter(words: WordBrief[]): { letter: string; words: WordBrief[] }[] {
  const map = new Map<string, WordBrief[]>();
  for (const word of words) {
    const letter = indexLetter(word.lemma);
    map.set(letter, [...(map.get(letter) ?? []), word]);
  }
  const letters = [...map.keys()].sort((a, b) => {
    if (a === "#") return 1;
    if (b === "#") return -1;
    return a.localeCompare(b);
  });
  return letters.map((letter) => ({
    letter,
    words: (map.get(letter) ?? []).sort((a, b) => a.lemma.localeCompare(b.lemma)),
  }));
}
