import type { WordGroup } from "@sceneenglish/api-client/types";

export interface FilterChipOption {
  id: string;
  label: string;
}

export const LEARNING_LEVEL_OPTIONS: FilterChipOption[] = [
  { id: "cet4", label: "CET-4" },
  { id: "cet6", label: "CET-6" },
  { id: "pets1", label: "PETS-1" },
  { id: "pets2", label: "PETS-2" },
  { id: "pets3", label: "PETS-3" },
  { id: "pets4", label: "PETS-4" },
  { id: "pets5", label: "PETS-5" },
];

export const SCENARIO_KIND_OPTIONS: FilterChipOption[] = [
  { id: "daily", label: "每日场景" },
  { id: "narrative", label: "叙事短文" },
  { id: "dialogue", label: "对话场景" },
];

export const CONVERSATION_STATUS_OPTIONS: FilterChipOption[] = [
  { id: "active", label: "进行中" },
  { id: "ended", label: "已结束" },
];

/** 与词库主题 / 场景视觉资源对齐的默认标签 */
const THEME_LABEL_FALLBACK: Record<string, string> = {
  travel: "出行旅游",
  campus: "校园生活",
  business: "职场商务",
  health: "健康医疗",
  technology: "科技数码",
  environment: "环保自然",
  culture: "文化艺术",
  daily: "日常生活",
};

export function buildScenarioThemeOptions(groups?: WordGroup[]): FilterChipOption[] {
  const labels = new Map<string, string>(Object.entries(THEME_LABEL_FALLBACK));

  for (const group of groups ?? []) {
    labels.set(group.slug, group.name_zh || group.name_en || group.slug);
  }

  return [...labels.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, label]) => ({ id, label }));
}
